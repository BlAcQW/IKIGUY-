"""
Voice Q&A API routes.

Endpoints for voice interactions:
- POST /voice/qa - Complete voice Q&A pipeline
- POST /voice/transcribe - Audio transcription only
- POST /voice/ask - Text question with RAG
- GET /voice/history/{book_id} - Conversation history

IMPORTANT: All credit operations use atomic reservations to prevent race conditions.
Credits are reserved BEFORE doing expensive work, then finalized/refunded after.
"""

import logging
import uuid
from decimal import Decimal
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, status
from fastapi.responses import JSONResponse

from app.schemas.voice import (
    VoiceQuestionRequest,
    VoiceQAResponse,
    TranscribeResponse,
    ConversationHistoryResponse
)
from app.services.voice_service import voice_service
from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import UserInDB

# Import InsufficientBalanceError - try shared first, fallback to creating compatible exception
try:
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../..')))
    from apps.shared.integration.wallet import InsufficientBalanceError
except ImportError:
    # Fallback: create compatible exception class
    class InsufficientBalanceError(Exception):
        """Raised when wallet has insufficient balance."""
        def __init__(self, available: float = 0, required: float = 0, message: str = None):
            self.available = available
            self.required = required
            super().__init__(message or f"Insufficient balance: {available} < {required}")

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["voice"])

# Pricing constants (in credits, 100 credits = $1)
COST_STT_PER_MINUTE = 60  # $0.60/min
COST_RAG_PER_QUERY = 30   # $0.30/query
COST_TTS_PER_1K_CHARS = 150  # $1.50/1k chars

# Estimated maximum costs for reservation (we refund unused credits)
MAX_VOICE_QA_CREDITS = 300  # Max expected: STT(60) + RAG(30) + TTS(~150) + buffer
MAX_TRANSCRIBE_CREDITS = 120  # Max for ~2 minute audio
MAX_ASK_CREDITS = 50  # RAG query with buffer


async def _get_wallet_service():
    """Get initialized wallet service."""
    from app.services.wallet_service import wallet_service

    if not wallet_service.initialized:
        db = get_db()
        await wallet_service.initialize(db=db)

    return wallet_service


async def reserve_credits_atomic(
    user_id: str,
    credits: int,
    description: str,
    metadata: dict = None
) -> tuple[str, bool]:
    """
    Atomically reserve credits BEFORE doing expensive work.

    This prevents race conditions where multiple concurrent requests
    could pass a balance check before any deduction occurs.

    Args:
        user_id: User ID
        credits: Credits to reserve
        description: What the credits are for
        metadata: Additional transaction metadata

    Returns:
        Tuple of (reservation_id, success)

    Raises:
        HTTPException 402 if insufficient balance
    """
    wallet_service = await _get_wallet_service()

    # Generate unique reservation ID for idempotency
    reservation_id = str(uuid.uuid4())

    try:
        transaction = await wallet_service.reserve_credits_atomic(
            user_id=user_id,
            credits=credits,
            reservation_id=reservation_id,
            description=description,
            metadata=metadata
        )

        if transaction:
            logger.info(
                f"Reserved {credits} credits for user {user_id}, "
                f"reservation_id={reservation_id}"
            )
            return reservation_id, True
        else:
            logger.error(f"Failed to reserve {credits} credits for user {user_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reserve credits. Please try again."
            )

    except InsufficientBalanceError as e:
        logger.warning(
            f"Insufficient balance for user {user_id}: "
            f"required={credits}, available={e.available}"
        )
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error": "insufficient_balance",
                "message": "Insufficient credits. Please top up your wallet.",
                "balance_credits": int(e.available * 100),
                "required_credits": credits
            }
        )


async def finalize_credits(
    user_id: str,
    reservation_id: str,
    actual_credits: int,
    reserved_credits: int,
    description: str,
    metadata: dict = None
) -> None:
    """
    Finalize a credit reservation after work is complete.
    Refunds any excess credits that were reserved but not used.

    Args:
        user_id: User ID
        reservation_id: Original reservation ID
        actual_credits: Actual credits used
        reserved_credits: Credits that were reserved
        description: Description for the transaction
        metadata: Additional transaction metadata
    """
    wallet_service = await _get_wallet_service()

    await wallet_service.finalize_reservation(
        user_id=user_id,
        reservation_id=reservation_id,
        actual_credits=actual_credits,
        reserved_credits=reserved_credits,
        description=description,
        metadata=metadata
    )

    logger.info(
        f"Finalized reservation {reservation_id} for user {user_id}: "
        f"reserved={reserved_credits}, actual={actual_credits}"
    )


async def refund_reservation(
    user_id: str,
    reservation_id: str,
    credits: int,
    reason: str
) -> None:
    """
    Refund a reservation when the operation fails.

    Args:
        user_id: User ID
        reservation_id: Original reservation ID
        credits: Credits to refund
        reason: Reason for refund
    """
    wallet_service = await _get_wallet_service()

    await wallet_service.refund_reservation(
        user_id=user_id,
        reservation_id=reservation_id,
        credits=credits,
        reason=reason
    )

    logger.info(
        f"Refunded {credits} credits for user {user_id}, "
        f"reservation_id={reservation_id}, reason={reason}"
    )


@router.post("/qa", response_model=VoiceQAResponse)
async def voice_qa(
    audio: UploadFile = File(..., description="Voice question audio file"),
    book_id: str = Form(..., description="Book ID to query"),
    output_format: str = Form("mp3", description="Output audio format (mp3, ogg, wav, flac, m4a)"),
    bitrate: str = Form("192k", description="Audio bitrate for lossy formats (128k-320k)"),
    tts_provider: str = Form("coqui_xtts", description="TTS provider to use"),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Complete voice Q&A pipeline: STT → RAG → TTS.

    Process:
    1. ATOMICALLY reserve credits (prevents race conditions)
    2. Transcribe audio to text (Whisper)
    3. Query book content (Gemini RAG)
    4. Generate audio response (TTS with format conversion)
    5. Finalize credits (refund excess or charge additional)
    6. Save conversation history

    Audio Format Options:
    - **mp3**: Best for mobile (8x smaller, good quality) - DEFAULT
    - **ogg**: Good for web browsers (Vorbis codec)
    - **wav**: Lossless quality (large files)
    - **flac**: Lossless compressed
    - **m4a**: AAC format (Apple/web)

    Bitrate Options (lossy formats only):
    - 128k: Smaller files, acceptable quality
    - 192k: Balanced (recommended) - DEFAULT
    - 256k: High quality
    - 320k: Maximum quality

    Cost: Variable based on TTS provider and text length
    - STT: ~60 credits (~$0.60) per minute
    - RAG: ~30 credits (~$0.30) per query
    - TTS: Varies by provider and duration

    Race Condition Prevention:
    Credits are ATOMICALLY reserved before any work begins, preventing
    concurrent requests from overdrawing the wallet balance.
    """
    user_id = current_user.user_id
    reservation_id = None
    reserved_credits = MAX_VOICE_QA_CREDITS

    try:
        # Read audio file first (cheap operation before reserving credits)
        audio_bytes = await audio.read()

        if len(audio_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty audio file")

        # Extract audio format from content type or filename
        audio_format = "webm"  # Default
        if audio.content_type:
            if "webm" in audio.content_type:
                audio_format = "webm"
            elif "mp3" in audio.content_type:
                audio_format = "mp3"
            elif "wav" in audio.content_type:
                audio_format = "wav"

        # Validate output_format
        valid_formats = ["mp3", "ogg", "wav", "flac", "m4a"]
        if output_format.lower() not in valid_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid output_format. Must be one of: {', '.join(valid_formats)}"
            )

        # Validate bitrate
        valid_bitrates = ["128k", "192k", "256k", "320k"]
        if bitrate not in valid_bitrates:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid bitrate. Must be one of: {', '.join(valid_bitrates)}"
            )

        # ATOMIC: Reserve credits BEFORE doing expensive AI operations
        # This prevents race conditions where concurrent requests could
        # all pass a balance check before any deduction occurs
        reservation_id, _ = await reserve_credits_atomic(
            user_id=user_id,
            credits=reserved_credits,
            description=f"Voice Q&A for book {book_id}",
            metadata={
                "book_id": book_id,
                "type": "voice_qa",
                "operation": "reservation"
            }
        )

        # Process voice Q&A (expensive AI operations)
        result = await voice_service.complete_voice_qa(
            audio_bytes=audio_bytes,
            book_id=book_id,
            user_id=user_id,
            audio_format=audio_format,
            tts_provider=tts_provider,
            output_format=output_format.lower(),
            bitrate=bitrate
        )

        # Calculate actual cost
        costs = result.get("costs", {})
        actual_credits = (
            costs.get("stt", COST_STT_PER_MINUTE) +
            costs.get("rag", COST_RAG_PER_QUERY) +
            costs.get("tts", 0)
        )

        # Finalize: refund excess credits if actual < reserved
        await finalize_credits(
            user_id=user_id,
            reservation_id=reservation_id,
            actual_credits=actual_credits,
            reserved_credits=reserved_credits,
            description=f"Voice Q&A for book {book_id}",
            metadata={
                "book_id": book_id,
                "type": "voice_qa",
                "stt_cost": costs.get("stt", 0),
                "rag_cost": costs.get("rag", 0),
                "tts_cost": costs.get("tts", 0)
            }
        )

        # Save conversation to history
        await voice_service.save_conversation(
            user_id=user_id,
            book_id=book_id,
            question=result["question"],
            answer=result["answer"],
            audio_url=result.get("audio_url")
        )

        return VoiceQAResponse(**result)

    except HTTPException:
        # If we reserved credits but got an HTTP error, refund them
        if reservation_id:
            await refund_reservation(
                user_id=user_id,
                reservation_id=reservation_id,
                credits=reserved_credits,
                reason="HTTP error during voice Q&A"
            )
        raise
    except Exception as e:
        # If we reserved credits but got an error, refund them
        if reservation_id:
            await refund_reservation(
                user_id=user_id,
                reservation_id=reservation_id,
                credits=reserved_credits,
                reason=f"Voice Q&A failed: {str(e)[:100]}"
            )
        logger.error(f"Voice Q&A failed for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Voice Q&A processing failed. Please try again."
        )


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    audio: UploadFile = File(..., description="Audio file to transcribe"),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Transcribe audio to text using Whisper.

    Cost: ~60 credits per minute

    Race Condition Prevention:
    Credits are ATOMICALLY reserved before transcription begins.
    """
    user_id = current_user.user_id
    reservation_id = None
    reserved_credits = MAX_TRANSCRIBE_CREDITS

    try:
        # Read audio file first (cheap operation)
        audio_bytes = await audio.read()

        if len(audio_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty audio file")

        # ATOMIC: Reserve credits before expensive STT operation
        reservation_id, _ = await reserve_credits_atomic(
            user_id=user_id,
            credits=reserved_credits,
            description="Audio transcription",
            metadata={"type": "transcription", "operation": "reservation"}
        )

        # Transcribe
        transcript, duration, cost = await voice_service.transcribe_audio(
            audio_bytes=audio_bytes
        )

        # Calculate actual cost based on duration (60 credits per minute)
        actual_credits = max(int(duration / 60 * COST_STT_PER_MINUTE), 1)

        # Finalize: refund excess credits
        await finalize_credits(
            user_id=user_id,
            reservation_id=reservation_id,
            actual_credits=actual_credits,
            reserved_credits=reserved_credits,
            description=f"Audio transcription ({duration:.1f}s)",
            metadata={"type": "transcription", "duration_seconds": duration}
        )

        return TranscribeResponse(
            transcript=transcript,
            duration_seconds=duration,
            cost_credits=actual_credits
        )

    except HTTPException:
        if reservation_id:
            await refund_reservation(
                user_id=user_id,
                reservation_id=reservation_id,
                credits=reserved_credits,
                reason="HTTP error during transcription"
            )
        raise
    except Exception as e:
        if reservation_id:
            await refund_reservation(
                user_id=user_id,
                reservation_id=reservation_id,
                credits=reserved_credits,
                reason=f"Transcription failed: {str(e)[:100]}"
            )
        logger.error(f"Transcription failed for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Transcription failed. Please try again."
        )


@router.post("/ask", response_model=VoiceQAResponse)
async def ask_question(
    request: VoiceQuestionRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Ask a text question using RAG (no audio).

    Cost: ~30 credits per question

    Race Condition Prevention:
    Credits are ATOMICALLY reserved before RAG query begins.
    """
    user_id = current_user.user_id
    reservation_id = None
    reserved_credits = MAX_ASK_CREDITS

    try:
        # ATOMIC: Reserve credits before RAG query
        reservation_id, _ = await reserve_credits_atomic(
            user_id=user_id,
            credits=reserved_credits,
            description=f"Book Q&A for book {request.book_id}",
            metadata={
                "book_id": request.book_id,
                "type": "text_qa",
                "operation": "reservation"
            }
        )

        # Query book with RAG
        answer, cost = await voice_service.query_book(
            question=request.transcript,
            book_id=request.book_id
        )

        # Finalize with actual cost
        actual_credits = COST_RAG_PER_QUERY
        await finalize_credits(
            user_id=user_id,
            reservation_id=reservation_id,
            actual_credits=actual_credits,
            reserved_credits=reserved_credits,
            description=f"Book Q&A for book {request.book_id}",
            metadata={
                "book_id": request.book_id,
                "type": "text_qa",
                "question_length": len(request.transcript)
            }
        )

        # Save conversation
        await voice_service.save_conversation(
            user_id=user_id,
            book_id=request.book_id,
            question=request.transcript,
            answer=answer
        )

        return VoiceQAResponse(
            question=request.transcript,
            answer=answer,
            audio_url=None,
            costs={"rag": COST_RAG_PER_QUERY, "total": COST_RAG_PER_QUERY},
            timestamp=None
        )

    except HTTPException:
        if reservation_id:
            await refund_reservation(
                user_id=user_id,
                reservation_id=reservation_id,
                credits=reserved_credits,
                reason="HTTP error during text Q&A"
            )
        raise
    except Exception as e:
        if reservation_id:
            await refund_reservation(
                user_id=user_id,
                reservation_id=reservation_id,
                credits=reserved_credits,
                reason=f"Text Q&A failed: {str(e)[:100]}"
            )
        logger.error(f"Question processing failed for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Question processing failed. Please try again."
        )


@router.get("/history/{book_id}", response_model=ConversationHistoryResponse)
async def get_conversation_history(
    book_id: str,
    limit: int = 50,
    user_id: str = Depends(get_current_user)
):
    """
    Get conversation history for a book.

    Returns recent Q&A conversations.
    """
    try:
        conversations = await voice_service.get_conversation_history(
            user_id=user_id,
            book_id=book_id,
            limit=limit
        )

        return ConversationHistoryResponse(
            conversations=conversations,
            total=len(conversations),
            book_id=book_id
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch history: {str(e)}"
        )
