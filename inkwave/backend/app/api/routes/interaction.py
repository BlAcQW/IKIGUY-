"""
Interaction routes.

API endpoints for Q&A interactions with AI voice agent.
Supports both traditional request/response and streaming SSE.
"""

from typing import List, Optional, AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from datetime import datetime
import uuid
import json

from app.core.database import Database
from app.core.auth import get_current_user
from app.services.rag_service import RAGService
from app.models.interaction import (
    Interaction,
    InteractionInDB,
    InteractionCreate,
    MessageCreate,
    Message
)
from pydantic import BaseModel

router = APIRouter(prefix="/interactions", tags=["interactions"])


# Response Models
class InteractionResponse(BaseModel):
    """Response with interaction data."""
    interaction: InteractionInDB
    message: Optional[Message] = None


# Dependency to get database
async def get_db():
    """Get database instance."""
    return Database.get_database()


async def get_rag_service() -> RAGService:
    """Get RAG service instance."""
    service = RAGService()
    await service.initialize()
    return service


@router.post("", response_model=InteractionInDB)
async def create_interaction(
    request: InteractionCreate,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Create a new interaction (Q&A session).

    Args:
        request: Interaction creation request
        current_user: Authenticated user
        db: Database instance

    Returns:
        InteractionInDB: Created interaction
    """
    user_id = current_user.user_id

    # Create interaction
    interaction = Interaction(
        interaction_id=str(uuid.uuid4()),
        session_id=request.session_id,
        user_id=user_id,
        book_id=request.book_id,
        chunk_context=request.chunk_context or []
    )

    # Insert to database
    result = await db.interactions.insert_one(
        interaction.model_dump(by_alias=True, exclude={"id"})
    )

    interaction_dict = interaction.model_dump(by_alias=True, exclude={"id"})
    interaction_dict["_id"] = str(result.inserted_id)

    return InteractionInDB(**interaction_dict)


@router.get("/{interaction_id}", response_model=InteractionInDB)
async def get_interaction(
    interaction_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get interaction by ID.

    Args:
        interaction_id: Interaction ID
        current_user: Authenticated user
        db: Database instance

    Returns:
        InteractionInDB: Interaction data
    """
    user_id = current_user.user_id

    interaction = await db.interactions.find_one({
        "interaction_id": interaction_id,
        "user_id": user_id
    })

    if not interaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interaction not found"
        )

    interaction["_id"] = str(interaction["_id"])
    return InteractionInDB(**interaction)


@router.post("/{interaction_id}/messages", response_model=InteractionResponse)
async def send_message(
    interaction_id: str,
    message_request: MessageCreate,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db),
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Send a message in an interaction and get AI response.

    This endpoint:
    1. Saves user's question
    2. Queries RAG service for relevant book passages
    3. Generates AI response using LLM
    4. Saves AI response
    5. Returns updated interaction

    Args:
        interaction_id: Interaction ID
        message_request: User's message
        current_user: Authenticated user
        db: Database instance
        rag_service: RAG service instance

    Returns:
        InteractionResponse: Updated interaction with AI response
    """
    user_id = current_user.user_id

    # Get interaction
    interaction = await db.interactions.find_one({
        "interaction_id": interaction_id,
        "user_id": user_id
    })

    if not interaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interaction not found"
        )

    # Create user message
    user_message = Message(
        role="user",
        content=message_request.content,
        timestamp=datetime.utcnow()
    )

    # Get book and user info for context
    book = await db.books.find_one({"book_id": interaction["book_id"]})
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )

    # Get user profile for personalization
    user_profile = await db.users.find_one({"user_id": user_id})

    # Build context from chunk_context
    context_chunks = []
    if interaction.get("chunk_context"):
        chunks = await db.book_chunks.find({
            "book_id": interaction["book_id"],
            "chunk_index": {"$in": interaction["chunk_context"]}
        }).to_list(length=10)
        context_chunks = [chunk["text"] for chunk in chunks]

    # Estimate cost and check balance before processing
    try:
        from apps.shared.services.usage_calculator import UsageCalculator
        from decimal import Decimal
        from apps.shared.integration.wallet import Currency, InsufficientBalanceError
        
        # Rough cost estimation for RAG query
        # Estimate: ~100 input tokens (question + context) + ~200 output tokens
        usage_calc = UsageCalculator()
        estimated_cost = usage_calc.calculate_llm_cost(
            input_tokens=len(message_request.content) // 4 + sum(len(c) for c in context_chunks) // 4,
            output_tokens=200,  # Estimated response length
            model=rag_service.default_model
        )
        
        # Check balance if billing is enabled
        if rag_service.enable_billing and estimated_cost > 0:
            try:
                from app.services.wallet_service import get_wallet_service
                from app.core.database import get_db
                
                wallet_service = await get_wallet_service(db=get_db())
                wallet = await wallet_service.shared_wallet.get_wallet_by_user(
                    user_id=user_id,
                    currency=Currency.USD
                )
                
                if wallet and wallet.available_balance < Decimal(str(estimated_cost)):
                    raise HTTPException(
                        status_code=status.HTTP_402_PAYMENT_REQUIRED,
                        detail=f"Insufficient balance. Required: ${estimated_cost:.6f}, Available: ${float(wallet.available_balance):.6f}"
                    )
            except InsufficientBalanceError:
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail="Insufficient balance for this operation"
                )
            except Exception as balance_error:
                logger.warning(f"Balance check failed (allowing request): {balance_error}")
                # Don't block request if balance check fails - billing will handle it
        
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Cost estimation/balance check failed (allowing request): {e}")
    
    # Query RAG service
    try:
        # Query RAG with context
        rag_response = await rag_service.query_book(
            book_id=interaction["book_id"],
            question=message_request.content,
            context_chunks=context_chunks,
            user_profile=user_profile
        )

        # Create assistant message
        assistant_message = Message(
            role="assistant",
            content=rag_response["answer"],
            timestamp=datetime.utcnow(),
            tokens_used=rag_response.get("tokens_used"),
            cost_cents=int(rag_response.get("cost", 0) * 100) if rag_response.get("cost") else 0
        )

        # Note: Billing is already handled by LLMProviderService when RAG service calls it
        # The cost is automatically debited from user's wallet via LLMProviderService._bill_user()
        # We just log the transaction for tracking
        if rag_response.get("cost", 0) > 0:
            logger.info(
                f"RAG interaction billed: user={user_id}, "
                f"book={interaction['book_id']}, "
                f"cost=${rag_response.get('cost', 0):.6f}, "
                f"tokens={rag_response.get('tokens_used', 0)}"
            )

    except Exception as e:
        # Handle RAG error gracefully
        assistant_message = Message(
            role="assistant",
            content=f"I'm sorry, I encountered an error processing your question. Please try again. Error: {str(e)}",
            timestamp=datetime.utcnow()
        )

    # Update interaction with both messages
    result = await db.interactions.find_one_and_update(
        {
            "interaction_id": interaction_id,
            "user_id": user_id
        },
        {
            "$push": {
                "messages": {
                    "$each": [
                        user_message.model_dump(),
                        assistant_message.model_dump()
                    ]
                }
            },
            "$set": {
                "updated_at": datetime.utcnow()
            }
        },
        return_document=True
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interaction not found"
        )

    # Convert ObjectId to string
    if "_id" in result:
        result["_id"] = str(result["_id"])

    return InteractionResponse(
        interaction=InteractionInDB(**result),
        message=assistant_message
    )


@router.post("/{interaction_id}/stream")
async def stream_conversation(
    interaction_id: str,
    message_request: MessageCreate,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db),
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Streaming conversation endpoint using Server-Sent Events (SSE).

    Provides real-time streaming of AI responses for seamless conversation flow.

    Args:
        interaction_id: Interaction ID
        message_request: User's message
        current_user: Authenticated user
        db: Database instance
        rag_service: RAG service instance

    Returns:
        StreamingResponse with SSE events containing:
        - 'message_start': AI response begins
        - 'text_chunk': Incremental text chunks
        - 'message_complete': Final complete message with metadata
        - 'audio_chunk': Optional audio chunks for TTS
        - 'error': Error information if processing fails
    """
    user_id = current_user.user_id

    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate Server-Sent Events for streaming conversation."""
        try:
            # Get interaction
            interaction = await db.interactions.find_one({
                "interaction_id": interaction_id,
                "user_id": user_id
            })

            if not interaction:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Interaction not found'})}\n\n"
                return

            # Create user message
            user_message = Message(
                role="user",
                content=message_request.content,
                timestamp=datetime.utcnow()
            )

            # Send message_start event
            yield f"data: {json.dumps({'type': 'message_start', 'role': 'assistant'})}\n\n"

            # Get book and context
            book = await db.books.find_one({"book_id": interaction["book_id"]})
            if not book:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Book not found'})}\n\n"
                return

            # Get user profile
            user_profile = await db.users.find_one({"user_id": user_id})

            # Build context chunks
            context_chunks = []
            if interaction.get("chunk_context"):
                chunks = await db.book_chunks.find({
                    "book_id": interaction["book_id"],
                    "chunk_index": {"$in": interaction["chunk_context"]}
                }).to_list(length=10)
                context_chunks = [chunk["text"] for chunk in chunks]

            # Estimate cost and check balance before streaming
            try:
                from apps.shared.services.usage_calculator import UsageCalculator
                from decimal import Decimal
                from apps.shared.integration.wallet import Currency, InsufficientBalanceError
                
                # Rough cost estimation for streaming RAG query
                usage_calc = UsageCalculator()
                estimated_cost = usage_calc.calculate_llm_cost(
                    input_tokens=len(message_request.content) // 4 + sum(len(c) for c in context_chunks) // 4,
                    output_tokens=200,  # Estimated response length
                    model=rag_service.default_model
                )
                
                # Check balance if billing is enabled
                if rag_service.enable_billing and estimated_cost > 0:
                    try:
                        from app.services.wallet_service import get_wallet_service
                        from app.core.database import get_db
                        
                        wallet_service = await get_wallet_service(db=get_db())
                        wallet = await wallet_service.shared_wallet.get_wallet_by_user(
                            user_id=user_id,
                            currency=Currency.USD
                        )
                        
                        if wallet and wallet.available_balance < Decimal(str(estimated_cost)):
                            yield f"data: {json.dumps({'type': 'error', 'message': f'Insufficient balance. Required: ${estimated_cost:.6f}, Available: ${float(wallet.available_balance):.6f}'})}\n\n"
                            return
                    except InsufficientBalanceError:
                        yield f"data: {json.dumps({'type': 'error', 'message': 'Insufficient balance for this operation'})}\n\n"
                        return
                    except Exception as balance_error:
                        logger.warning(f"Balance check failed (allowing request): {balance_error}")
                        # Don't block request if balance check fails
            except Exception as e:
                logger.warning(f"Cost estimation/balance check failed (allowing request): {e}")
            
            # Stream response from RAG service using Gemini streaming
            # Note: Billing is handled automatically by RAG service
            full_answer = ""
            async for text_chunk in rag_service.query_book_stream(
                book_id=interaction["book_id"],
                question=message_request.content,
                context_chunks=context_chunks,
                user_profile=user_profile
            ):
                full_answer += text_chunk
                yield f"data: {json.dumps({'type': 'text_chunk', 'content': text_chunk})}\n\n"

            answer = full_answer
            
            # Estimate tokens and cost (billing already handled by RAG service)
            estimated_tokens = len(answer) // 4
            # Rough cost estimate for Gemini 2.0 Flash Exp (free tier, but track for consistency)
            estimated_cost = 0.0  # Free tier model
            
            # Create complete assistant message
            assistant_message = Message(
                role="assistant",
                content=answer,
                timestamp=datetime.utcnow(),
                tokens_used=estimated_tokens,
                cost_cents=int(estimated_cost * 100)
            )
            
            # Log the interaction for tracking
            logger.info(
                f"RAG streaming interaction completed: user={user_id}, "
                f"book={interaction['book_id']}, "
                f"tokens={estimated_tokens}, "
                f"cost=${estimated_cost:.6f}"
            )
            
            # Save both messages to interaction
            await db.interactions.update_one(
                {
                    "interaction_id": interaction_id,
                    "user_id": user_id
                },
                {
                    "$push": {
                        "messages": {
                            "$each": [
                                user_message.model_dump(),
                                assistant_message.model_dump()
                            ]
                        }
                    },
                    "$set": {
                        "updated_at": datetime.utcnow()
                    }
                }
            )

            # Send completion event with metadata
            completion_data = {
                'type': 'message_complete',
                'content': answer,
                'tokens_used': estimated_tokens,
                'cost': estimated_cost,
                'timestamp': datetime.utcnow().isoformat()
            }
            yield f"data: {json.dumps(completion_data)}\n\n"

            # Save both messages to interaction
            await db.interactions.update_one(
                {
                    "interaction_id": interaction_id,
                    "user_id": user_id
                },
                {
                    "$push": {
                        "messages": {
                            "$each": [
                                user_message.model_dump(),
                                assistant_message.model_dump()
                            ]
                        }
                    },
                    "$set": {
                        "updated_at": datetime.utcnow()
                    }
                }
            )

            # Send completion event with metadata
            completion_data = {
                'type': 'message_complete',
                'content': answer,
                'tokens_used': estimated_tokens,
                'cost': estimated_cost,
                'timestamp': datetime.utcnow().isoformat()
            }
            yield f"data: {json.dumps(completion_data)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


@router.get("/session/{session_id}", response_model=List[InteractionInDB])
async def get_session_interactions(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get all interactions for a reading session.

    Args:
        session_id: Reading session ID
        current_user: Authenticated user
        db: Database instance

    Returns:
        List[InteractionInDB]: Interactions for the session
    """
    user_id = current_user.user_id

    interactions = await db.interactions.find({
        "session_id": session_id,
        "user_id": user_id
    }).to_list(length=100)

    return [InteractionInDB(**interaction) for interaction in interactions]


@router.delete("/{interaction_id}")
async def delete_interaction(
    interaction_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Delete an interaction.

    Args:
        interaction_id: Interaction ID
        current_user: Authenticated user
        db: Database instance

    Returns:
        Success message
    """
    user_id = current_user.user_id

    result = await db.interactions.delete_one({
        "interaction_id": interaction_id,
        "user_id": user_id
    })

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interaction not found"
        )

    return {"message": "Interaction deleted successfully"}


# Voice Interaction Endpoints

@router.post("/{interaction_id}/voice-question", response_model=InteractionResponse)
async def send_voice_question(
    interaction_id: str,
    audio_file: bytes,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db),
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Send a voice question to the AI.

    Transcribes audio to text, processes with RAG, and generates audio response.

    Args:
        interaction_id: Interaction ID
        audio_file: Audio file bytes (from upload)
        current_user: Authenticated user
        db: Database instance
        rag_service: RAG service instance

    Returns:
        InteractionResponse with transcribed question and AI answer

    Raises:
        HTTPException: If interaction not found or processing fails
    """
    from app.services.asr_service import ASRService
    from app.services.tts_service import TTSService

    user_id = current_user.user_id

    # Get interaction
    interaction = await db.interactions.find_one({
        "interaction_id": interaction_id,
        "user_id": user_id
    })

    if not interaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interaction not found"
        )

    try:
        # Step 1: Transcribe audio to text using ASR
        asr_service = ASRService()
        await asr_service.initialize()

        transcription = await asr_service.transcribe_audio(
            audio_data=audio_file,
            user_id=user_id,
            provider_id="whisper",
            language="en"
        )

        question_text = transcription["text"]

        if not question_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not transcribe audio"
            )

        # Step 2: Process question with RAG (same as text question)
        user_message = Message(
            role="user",
            content=question_text,
            timestamp=datetime.utcnow(),
            tokens_used=transcription.get("duration", 0),
            cost_cents=transcription.get("cost", 0) * 100  # Convert to cents
        )

        # Get book for context
        book = await db.books.find_one({"book_id": interaction["book_id"]})
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )

        # Query RAG
        rag_response = await rag_service.query_book(
            book_id=interaction["book_id"],
            question=question_text,
            context_chunks=[],
            user_profile=await db.users.find_one({"user_id": user_id})
        )

        # Step 3: Generate audio response using TTS
        tts_service = TTSService()
        await tts_service.initialize()

        # Save response text temporarily (create chunk for audio generation)
        response_text = rag_response["answer"]

        # Note: In production, you'd want to stream or cache this
        # For now, we'll just include the text and let frontend request audio separately

        assistant_message = Message(
            role="assistant",
            content=response_text,
            timestamp=datetime.utcnow(),
            tokens_used=rag_response.get("tokens_used", 0),
            cost_cents=0  # TTS cost will be charged when audio is requested
        )

        # Update interaction with both messages
        result = await db.interactions.find_one_and_update(
            {
                "interaction_id": interaction_id,
                "user_id": user_id
            },
            {
                "$push": {
                    "messages": {
                        "$each": [
                            user_message.model_dump(),
                            assistant_message.model_dump()
                        ]
                    }
                },
                "$set": {
                    "updated_at": datetime.utcnow()
                }
            },
            return_document=True
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interaction not found"
            )

        # Convert ObjectId to string
        if "_id" in result:
            result["_id"] = str(result["_id"])

        return InteractionResponse(
            interaction=InteractionInDB(**result),
            message=assistant_message
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Voice question processing failed: {str(e)}"
        )


@router.get("/{interaction_id}/messages/{message_index}/audio")
async def get_message_audio(
    interaction_id: str,
    message_index: int,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get audio for a specific message.

    Generates TTS audio for assistant messages.

    Args:
        interaction_id: Interaction ID
        message_index: Index of message in messages array
        current_user: Authenticated user
        db: Database instance

    Returns:
        Audio URL and metadata

    Raises:
        HTTPException: If interaction/message not found
    """
    from app.services.tts_service import TTSService
    import hashlib

    user_id = current_user.user_id

    # Get interaction
    interaction = await db.interactions.find_one({
        "interaction_id": interaction_id,
        "user_id": user_id
    })

    if not interaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interaction not found"
        )

    # Get message
    messages = interaction.get("messages", [])
    if message_index >= len(messages):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    message = messages[message_index]

    if message["role"] != "assistant":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only assistant messages can be converted to audio"
        )

    # Generate audio using TTS
    try:
        tts_service = TTSService()
        await tts_service.initialize()

        # Create a pseudo-chunk ID for caching
        text_hash = hashlib.md5(message["content"].encode()).hexdigest()[:8]
        pseudo_chunk_id = f"msg_{interaction_id}_{message_index}_{text_hash}"

        # Check if audio already exists
        existing_audio = message.get("audio_url")
        if existing_audio:
            return {
                "audio_url": existing_audio,
                "duration": message.get("audio_duration", 0),
                "cost": 0.0,
                "cached": True
            }

        # Create temporary "chunk" for audio generation
        # (TTS service expects chunks, but we're generating for a message)
        # We'll save to a different collection or handle differently

        # For now, generate audio without saving to chunk
        from apps.shared.services.tts_provider_service import SynthesisRequest
        result = await tts_service.tts_provider.synthesize(
            user_id=user_id,
            request=SynthesisRequest(
                provider_id="coqui_xtts",
                text=message["content"],
                language="en",
                voice_id="nova",
                speed=1.0,
                output_format="mp3"
            )
        )

        # Save audio URL to message
        audio_url = f"data:audio/mp3;base64,{result.audio_base64}"  # Base64 data URL

        # Update message with audio URL
        messages[message_index]["audio_url"] = audio_url
        messages[message_index]["audio_duration"] = result.duration

        await db.interactions.update_one(
            {"interaction_id": interaction_id},
            {"$set": {"messages": messages}}
        )

        return {
            "audio_url": audio_url,
            "duration": result.duration,
            "cost": result.cost,
            "provider_used": result.provider_id,
            "cached": False
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audio generation failed: {str(e)}"
        )
