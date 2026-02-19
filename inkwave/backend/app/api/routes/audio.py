"""
Audio narration routes for InkWave.

Endpoints for generating and managing audiobook narration using TTS.
"""

import logging
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, File, Form, UploadFile
from pydantic import BaseModel, Field

from app.core.auth import get_current_user
from app.services.tts_service import TTSService
from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audio", tags=["audio"])


# Request/Response Models

class AudioGenerationRequest(BaseModel):
    """Request to generate audio for a chunk."""
    provider_id: str = Field(
        default="coqui_xtts",
        description="TTS provider ID"
    )
    voice_id: str = Field(
        default="nova",
        description="Voice identifier"
    )
    speed: float = Field(
        default=1.0,
        ge=0.5,
        le=2.0,
        description="Playback speed multiplier"
    )
    language: str = Field(
        default="en",
        description="Language code"
    )
    force_regenerate: bool = Field(
        default=False,
        description="Force regeneration even if cached"
    )


class ChapterAudioRequest(BaseModel):
    """Request to generate audio for an entire chapter."""
    chapter_id: str = Field(description="Chapter identifier")
    provider_id: str = Field(default="coqui_xtts")
    voice_id: str = Field(default="nova")
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    language: str = Field(default="en")


class AudioResponse(BaseModel):
    """Response with audio metadata."""
    audio_url: str
    duration: float
    cost: float
    provider_used: str
    cached: bool
    transaction_id: Optional[str] = None


class ChapterAudioResponse(BaseModel):
    """Response for chapter audio generation."""
    total_chunks: int
    successful: int
    failed: int
    total_duration: float
    total_cost: float
    chunks: list


class CostEstimateResponse(BaseModel):
    """Cost estimate for book narration."""
    total_chunks: int
    total_characters: int
    estimated_cost: float
    estimated_duration_minutes: float
    cost_per_1000_chars: float


class ProvidersResponse(BaseModel):
    """Available TTS providers."""
    providers: dict


# Endpoints

@router.post(
    "/chunks/{chunk_id}",
    response_model=AudioResponse,
    summary="Generate audio for a chunk"
)
async def generate_chunk_audio(
    chunk_id: str,
    book_id: str,
    request: AudioGenerationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate audio narration for a book chunk.

    Args:
        chunk_id: Chunk identifier
        book_id: Book identifier
        request: Audio generation parameters
        current_user: Authenticated user

    Returns:
        AudioResponse with audio URL and metadata

    Raises:
        HTTPException: If chunk not found or generation fails
    """
    try:
        tts_service = TTSService()
        await tts_service.initialize()

        result = await tts_service.narrate_chunk(
            chunk_id=chunk_id,
            book_id=book_id,
            user_id=current_user.user_id,
            provider_id=request.provider_id,
            voice_id=request.voice_id,
            speed=request.speed,
            language=request.language,
            force_regenerate=request.force_regenerate
        )

        logger.info(
            f"Audio generated for chunk {chunk_id}: "
            f"${result['cost']:.4f}, cached={result['cached']}"
        )

        return AudioResponse(**result)

    except ValueError as e:
        logger.error(f"Invalid chunk request: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Audio generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audio generation failed: {str(e)}"
        )


@router.get(
    "/chunks/{chunk_id}",
    response_model=AudioResponse,
    summary="Get cached audio for a chunk"
)
async def get_chunk_audio(
    chunk_id: str,
    book_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get cached audio for a chunk (if available).

    Args:
        chunk_id: Chunk identifier
        book_id: Book identifier
        current_user: Authenticated user
        db: Database connection

    Returns:
        AudioResponse with cached audio metadata

    Raises:
        HTTPException: If chunk not found or no audio available
    """
    try:
        # Get chunk from database
        chunk = await db.book_chunks.find_one({
            "chunk_id": chunk_id,
            "book_id": book_id
        })

        if not chunk:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chunk not found: {chunk_id}"
            )

        if not chunk.get("audio_url"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No audio available for this chunk"
            )

        return AudioResponse(
            audio_url=chunk["audio_url"],
            duration=chunk.get("audio_duration", 0),
            cost=0.0,  # Cached, no cost
            provider_used=chunk.get("audio_provider", "unknown"),
            cached=True
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get cached audio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/books/{book_id}/chapters/{chapter_id}",
    response_model=ChapterAudioResponse,
    summary="Generate audio for entire chapter"
)
async def generate_chapter_audio(
    book_id: str,
    chapter_id: str,
    request: ChapterAudioRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate audio for all chunks in a chapter.

    This endpoint processes chunks sequentially. For large chapters,
    consider using background task processing.

    Args:
        book_id: Book identifier
        chapter_id: Chapter identifier
        request: Audio generation parameters
        background_tasks: Background task manager
        current_user: Authenticated user

    Returns:
        ChapterAudioResponse with generation results

    Raises:
        HTTPException: If chapter not found or generation fails
    """
    try:
        tts_service = TTSService()
        await tts_service.initialize()

        result = await tts_service.narrate_chapter(
            book_id=book_id,
            chapter_id=chapter_id,
            user_id=current_user.user_id,
            provider_id=request.provider_id,
            voice_id=request.voice_id,
            speed=request.speed,
            language=request.language
        )

        logger.info(
            f"Chapter audio generated: {result['successful']}/{result['total_chunks']} chunks, "
            f"${result['total_cost']:.4f}"
        )

        return ChapterAudioResponse(**result)

    except ValueError as e:
        logger.error(f"Invalid chapter request: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Chapter audio generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chapter audio generation failed: {str(e)}"
        )


@router.get(
    "/books/{book_id}/estimate",
    response_model=CostEstimateResponse,
    summary="Estimate narration cost for book"
)
async def estimate_book_narration_cost(
    book_id: str,
    provider_id: str = "coqui_xtts",
    current_user: dict = Depends(get_current_user)
):
    """
    Estimate cost to narrate entire book.

    Args:
        book_id: Book identifier
        provider_id: TTS provider to use for estimation
        current_user: Authenticated user

    Returns:
        CostEstimateResponse with estimated cost and duration

    Raises:
        HTTPException: If book not found or estimation fails
    """
    try:
        tts_service = TTSService()
        await tts_service.initialize()

        estimate = await tts_service.estimate_narration_cost(
            book_id=book_id,
            provider_id=provider_id
        )

        logger.info(
            f"Cost estimate for book {book_id}: "
            f"${estimate['estimated_cost']:.2f}, "
            f"{estimate['estimated_duration_minutes']:.1f} minutes"
        )

        return CostEstimateResponse(**estimate)

    except ValueError as e:
        logger.error(f"Invalid book for estimation: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Cost estimation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cost estimation failed: {str(e)}"
        )


@router.get(
    "/providers",
    response_model=ProvidersResponse,
    summary="Get available TTS providers"
)
async def get_available_providers(
    current_user: dict = Depends(get_current_user)
):
    """
    Get list of available TTS providers with capabilities.

    Args:
        current_user: Authenticated user

    Returns:
        ProvidersResponse with provider information

    Example response:
        {
            "providers": {
                "coqui_xtts": {
                    "name": "Coqui XTTS",
                    "status": "online",
                    "capabilities": ["voice_cloning", "multi_language"],
                    "languages": ["en", "es", "fr", ...],
                    "cost_multiplier": 1.0
                }
            }
        }
    """
    try:
        tts_service = TTSService()
        await tts_service.initialize()

        providers = await tts_service.get_available_providers()

        return ProvidersResponse(providers=providers)

    except Exception as e:
        logger.error(f"Failed to get providers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get providers: {str(e)}"
        )


@router.delete(
    "/chunks/{chunk_id}/cache",
    summary="Clear cached audio for chunk"
)
async def clear_chunk_audio_cache(
    chunk_id: str,
    book_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Clear cached audio for a chunk.

    This allows regeneration with different voice/settings.

    Args:
        chunk_id: Chunk identifier
        book_id: Book identifier
        current_user: Authenticated user
        db: Database connection

    Returns:
        Success message

    Raises:
        HTTPException: If chunk not found
    """
    try:
        # Remove audio metadata from chunk
        result = await db.book_chunks.update_one(
            {
                "chunk_id": chunk_id,
                "book_id": book_id
            },
            {
                "$unset": {
                    "audio_url": "",
                    "audio_duration": "",
                    "audio_provider": "",
                    "audio_generated_at": "",
                    "audio_cost": "",
                    "audio_voice_id": "",
                    "audio_speed": "",
                    "audio_language": ""
                }
            }
        )

        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chunk not found: {chunk_id}"
            )

        logger.info(f"Cleared audio cache for chunk: {chunk_id}")

        return {"message": "Audio cache cleared successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to clear audio cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Voice Cloning Endpoints

@router.post("/voice-clones")
async def create_voice_clone(
    audio_file: UploadFile = File(..., description="Reference audio file (WAV, MP3)"),
    voice_name: str = Form(..., description="Name for this voice clone"),
    description: Optional[str] = Form(None, description="Optional description"),
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Upload reference audio for voice cloning.

    Creates a voice clone profile that can be used for personalized narration.

    Args:
        audio_file: Reference audio file (30-60 seconds recommended)
        voice_name: Name for this voice clone
        description: Optional description for the voice clone
        current_user: Authenticated user
        db: Database connection

    Returns:
        Voice clone ID and metadata

    Raises:
        HTTPException: If upload or processing fails
    """
    import base64
    import uuid
    import os

    try:
        user_id = current_user.user_id

        # Read audio file content
        audio_bytes = await audio_file.read()

        # Create storage path for voice clones
        storage_path = "/opt/kasaai/apps/inkwave/backend/storage/voice_clones"
        os.makedirs(storage_path, exist_ok=True)

        # Generate unique ID for voice clone
        clone_id = f"voice_{uuid.uuid4().hex[:12]}"
        filename = f"{user_id}_{clone_id}.wav"
        filepath = os.path.join(storage_path, filename)

        # Save audio file
        with open(filepath, "wb") as f:
            f.write(audio_bytes)

        # Create voice clone record
        voice_clone = {
            "clone_id": clone_id,
            "user_id": user_id,
            "voice_name": voice_name,
            "description": description,
            "reference_audio_path": filepath,
            "reference_audio_url": f"https://inkwave-api.ailabsafrica.com/storage/voice_clones/{filename}",
            "created_at": datetime.utcnow(),
            "file_size_bytes": len(audio_bytes),
            "provider": "f5tts",
            "language": "en"
        }

        await db.voice_clones.insert_one(voice_clone)

        logger.info(f"Voice clone created: {clone_id} for user {user_id}")

        return {
            "clone_id": clone_id,
            "voice_name": voice_name,
            "reference_audio_url": voice_clone["reference_audio_url"],
            "message": "Voice clone created successfully"
        }

    except Exception as e:
        logger.error(f"Failed to create voice clone: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Voice clone creation failed: {str(e)}"
        )


@router.get("/voice-clones")
async def list_voice_clones(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    List user's voice clones.

    Args:
        current_user: Authenticated user
        db: Database connection

    Returns:
        List of voice clones

    Raises:
        HTTPException: If retrieval fails
    """
    try:
        user_id = current_user.user_id

        # Get user's voice clones
        clones = await db.voice_clones.find({
            "user_id": user_id
        }).to_list(length=100)

        # Remove internal fields
        for clone in clones:
            clone["_id"] = str(clone["_id"])
            clone.pop("reference_audio_path", None)  # Don't expose file paths

        return {
            "voice_clones": clones,
            "total": len(clones)
        }

    except Exception as e:
        logger.error(f"Failed to list voice clones: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/voice-clones/{clone_id}")
async def delete_voice_clone(
    clone_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Delete a voice clone.

    Args:
        clone_id: Voice clone identifier
        current_user: Authenticated user
        db: Database connection

    Returns:
        Success message

    Raises:
        HTTPException: If clone not found or deletion fails
    """
    import os

    try:
        user_id = current_user.user_id

        # Get voice clone
        clone = await db.voice_clones.find_one({
            "clone_id": clone_id,
            "user_id": user_id
        })

        if not clone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Voice clone not found"
            )

        # Delete audio file
        if os.path.exists(clone["reference_audio_path"]):
            os.remove(clone["reference_audio_path"])

        # Delete database record
        await db.voice_clones.delete_one({
            "clone_id": clone_id,
            "user_id": user_id
        })

        logger.info(f"Voice clone deleted: {clone_id}")

        return {"message": "Voice clone deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete voice clone: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/voice-clones/{clone_id}/test")
async def test_voice_clone(
    clone_id: str,
    test_text: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Test a voice clone with sample text.

    Generates audio using the cloned voice for preview.

    Args:
        clone_id: Voice clone identifier
        test_text: Text to synthesize
        current_user: Authenticated user
        db: Database connection

    Returns:
        Audio URL for preview

    Raises:
        HTTPException: If clone not found or generation fails
    """
    try:
        user_id = current_user.user_id

        # Get voice clone
        clone = await db.voice_clones.find_one({
            "clone_id": clone_id,
            "user_id": user_id
        })

        if not clone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Voice clone not found"
            )

        # Read reference audio
        with open(clone["reference_audio_path"], "rb") as f:
            reference_audio = f.read()

        # Generate audio using voice cloning
        import base64
        from apps.shared.services.tts_provider_service import (
            TTSProviderService,
            VoiceCloneRequest
        )

        tts_service = TTSProviderService(enable_billing=False)  # No charge for testing
        await tts_service.initialize()

        reference_audio_base64 = base64.b64encode(reference_audio).decode('utf-8')

        result = await tts_service.synthesize_with_voice_cloning(
            user_id=user_id,
            request=VoiceCloneRequest(
                provider_id="f5tts",  # F5-TTS supports voice cloning
                text=test_text,
                reference_audio_base64=reference_audio_base64,
                language="en",
                speed=1.0
            )
        )

        # Return base64 audio for preview
        return {
            "audio_url": f"data:audio/mp3;base64,{result.audio_base64}",
            "duration": result.duration,
            "provider_used": result.provider_id,
            "message": "Voice clone test successful"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test voice clone: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Voice clone test failed: {str(e)}"
        )


# Multi-Language Support Endpoints

@router.get("/languages")
async def get_supported_languages():
    """
    Get list of supported languages for TTS and ASR.

    Returns:
        Dict with TTS and ASR language support

    Example:
        {
            "tts": {
                "coqui_xtts": ["en", "es", "fr", "de", ...],
                "f5tts": ["en", "zh", "ja", "ko"]
            },
            "asr": {
                "whisper": ["en", "es", "fr", ...]
            }
        }
    """
    return {
        "tts": {
            "coqui_xtts": [
                "en", "es", "fr", "de", "it", "pt", "pl", "tr", "ru", "nl",
                "cs", "ar", "zh-cn", "ja", "hu", "ko", "hi"
            ],
            "f5tts": ["en", "zh", "ja", "ko"],
            "styletts2": ["en"],
            "melotts": ["en", "zh", "es", "fr", "ja", "ko"],
            "openvoice": ["en", "zh"]
        },
        "asr": {
            "whisper": [
                "en", "zh", "de", "es", "ru", "ko", "fr", "ja", "pt", "tr",
                "pl", "ca", "nl", "ar", "sv", "it", "id", "hi", "fi", "vi",
                "he", "uk", "el", "ms", "cs", "ro", "da", "hu", "ta", "no"
            ]
        },
        "supported_count": {
            "tts_max": 17,  # Coqui XTTS
            "asr_max": 30   # Whisper
        }
    }


@router.post("/chunks/{chunk_id}/translate")
async def generate_translated_audio(
    chunk_id: str,
    book_id: str,
    target_language: str,
    provider_id: str = "coqui_xtts",
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Generate audio in a different language (experimental).

    Note: This generates audio with TTS in the target language,
    it does NOT translate the text. For full translation, use
    a translation service first.

    Args:
        chunk_id: Chunk identifier
        book_id: Book identifier
        target_language: Target language code
        provider_id: TTS provider that supports the language
        current_user: Authenticated user
        db: Database connection

    Returns:
        Audio URL and metadata

    Raises:
        HTTPException: If language not supported or generation fails
    """
    try:
        tts_service = TTSService()
        await tts_service.initialize()

        result = await tts_service.narrate_chunk(
            chunk_id=chunk_id,
            book_id=book_id,
            user_id=current_user.user_id,
            provider_id=provider_id,
            language=target_language,
            force_regenerate=True  # Generate new audio for this language
        )

        return {
            "audio_url": result["audio_url"],
            "duration": result["duration"],
            "cost": result["cost"],
            "language": target_language,
            "provider_used": result["provider_used"]
        }

    except Exception as e:
        logger.error(f"Failed to generate translated audio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Translation audio generation failed: {str(e)}"
        )
