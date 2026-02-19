"""
Unified Conversation Routes

Provides HTTP API for multi-turn voice conversations.
Exposes conversation pipeline functionality via REST endpoints.

Author: KasaAI Team
Date: 2025-11-26
"""

import logging
from typing import Optional, Callable, List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Header, Query, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# Request/Response Models
class CreateConversationRequest(BaseModel):
    """Request to create a new conversation."""
    organization_id: str = Field(default="default")
    title: Optional[str] = Field(None, description="Optional conversation title")
    asr_provider: str = Field(default="faster_whisper_large")
    llm_model: str = Field(default="gemini-2.5-flash")
    tts_provider: str = Field(default="coqui_xtts")
    tts_voice: Optional[str] = None
    system_prompt: Optional[str] = None
    cultural_context: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ConversationResponse(BaseModel):
    """Response for conversation operations."""
    id: str
    user_id: str
    organization_id: str
    title: Optional[str]
    status: str
    total_turns: int
    total_cost_usd: float
    created_at: str
    updated_at: str
    config: Dict[str, Any]


class VoiceTurnRequest(BaseModel):
    """Request to process a voice turn."""
    audio_base64: str = Field(..., description="Base64-encoded audio input")
    audio_format: str = Field(default="wav", description="Audio format")
    generate_audio: bool = Field(default=True, description="Generate TTS response")


class TextTurnRequest(BaseModel):
    """Request to process a text turn."""
    text: str = Field(..., description="User's text input")
    generate_audio: bool = Field(default=False, description="Generate TTS response")


class TurnResponse(BaseModel):
    """Response from processing a turn."""
    conversation_id: str
    turn_id: str
    user_text: str
    detected_language: Optional[str]
    assistant_text: str
    audio_base64: Optional[str]
    audio_format: str = "wav"
    audio_duration: Optional[float]
    costs: Dict[str, float]
    timing: Dict[str, float]
    providers_used: Dict[str, Optional[str]]


class ConversationListResponse(BaseModel):
    """Response for listing conversations."""
    conversations: List[ConversationResponse]
    total: int
    limit: int
    offset: int


class UserStatsResponse(BaseModel):
    """Response for user statistics."""
    total_conversations: int
    total_turns: int
    total_cost: float
    active_conversations: int


def create_conversation_router(
    get_current_user_func: Callable,
    get_database_func: Callable,
) -> APIRouter:
    """
    Create conversation router with dependency injection.

    Args:
        get_current_user_func: Function to get current authenticated user
        get_database_func: Function to get database instance

    Returns:
        Configured APIRouter
    """
    router = APIRouter()

    # Import here to avoid circular imports
    from apps.shared.conversation import (
        ConversationPipeline,
        ConversationManager,
        ConversationConfig,
    )

    async def get_pipeline():
        """Get conversation pipeline instance."""
        db = get_database_func()
        manager = ConversationManager(db)
        # Note: ASR, LLM, TTS services would be injected in production
        # For now, pipeline handles missing services gracefully
        return ConversationPipeline(conversation_manager=manager)

    async def get_manager():
        """Get conversation manager instance."""
        db = get_database_func()
        return ConversationManager(db)

    @router.post("/conversations", response_model=ConversationResponse)
    async def create_conversation(
        request: CreateConversationRequest,
        authorization: str = Header(None),
    ):
        """
        Create a new conversation.

        Creates a new multi-turn conversation with the specified configuration.
        """
        try:
            # Get user ID from auth
            try:
                user = await get_current_user_func(authorization)
                user_id = user.get("sub") or user.get("id") or "anonymous"
            except Exception:
                user_id = "anonymous"

            manager = await get_manager()

            config = ConversationConfig(
                asr_provider=request.asr_provider,
                llm_model=request.llm_model,
                tts_provider=request.tts_provider,
                tts_voice=request.tts_voice,
                system_prompt=request.system_prompt,
                cultural_context=request.cultural_context,
            )

            conversation = await manager.create_conversation(
                user_id=user_id,
                organization_id=request.organization_id,
                config=config,
                title=request.title,
                metadata=request.metadata,
            )

            return ConversationResponse(
                id=conversation.id,
                user_id=conversation.user_id,
                organization_id=conversation.organization_id,
                title=conversation.title,
                status=conversation.status.value,
                total_turns=conversation.total_turns,
                total_cost_usd=conversation.total_cost_usd,
                created_at=conversation.created_at.isoformat(),
                updated_at=conversation.updated_at.isoformat(),
                config={
                    "asr_provider": conversation.config.asr_provider,
                    "llm_model": conversation.config.llm_model,
                    "tts_provider": conversation.config.tts_provider,
                },
            )

        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/conversations", response_model=ConversationListResponse)
    async def list_conversations(
        authorization: str = Header(None),
        organization_id: Optional[str] = Query(None),
        status: Optional[str] = Query(None),
        limit: int = Query(20, ge=1, le=100),
        offset: int = Query(0, ge=0),
    ):
        """
        List user's conversations.

        Returns paginated list of conversations for the authenticated user.
        """
        try:
            # Get user ID from auth
            try:
                user = await get_current_user_func(authorization)
                user_id = user.get("sub") or user.get("id") or "anonymous"
            except Exception:
                user_id = "anonymous"

            manager = await get_manager()

            # Convert status string to enum if provided
            from apps.shared.conversation.models import ConversationStatus
            status_enum = None
            if status:
                try:
                    status_enum = ConversationStatus(status)
                except ValueError:
                    pass

            conversations = await manager.list_conversations(
                user_id=user_id,
                organization_id=organization_id,
                status=status_enum,
                limit=limit,
                skip=offset,
            )

            return ConversationListResponse(
                conversations=[
                    ConversationResponse(
                        id=c.id,
                        user_id=c.user_id,
                        organization_id=c.organization_id,
                        title=c.title,
                        status=c.status.value,
                        total_turns=c.total_turns,
                        total_cost_usd=c.total_cost_usd,
                        created_at=c.created_at.isoformat(),
                        updated_at=c.updated_at.isoformat(),
                        config={
                            "asr_provider": c.config.asr_provider,
                            "llm_model": c.config.llm_model,
                            "tts_provider": c.config.tts_provider,
                        },
                    )
                    for c in conversations
                ],
                total=len(conversations),
                limit=limit,
                offset=offset,
            )

        except Exception as e:
            logger.error(f"Error listing conversations: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
    async def get_conversation(
        conversation_id: str,
        authorization: str = Header(None),
    ):
        """
        Get a specific conversation.

        Returns conversation details including history.
        """
        try:
            # Get user ID from auth
            try:
                user = await get_current_user_func(authorization)
                user_id = user.get("sub") or user.get("id") or "anonymous"
            except Exception:
                user_id = "anonymous"

            manager = await get_manager()
            conversation = await manager.get_conversation(
                conversation_id, user_id
            )

            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")

            return ConversationResponse(
                id=conversation.id,
                user_id=conversation.user_id,
                organization_id=conversation.organization_id,
                title=conversation.title,
                status=conversation.status.value,
                total_turns=conversation.total_turns,
                total_cost_usd=conversation.total_cost_usd,
                created_at=conversation.created_at.isoformat(),
                updated_at=conversation.updated_at.isoformat(),
                config={
                    "asr_provider": conversation.config.asr_provider,
                    "llm_model": conversation.config.llm_model,
                    "tts_provider": conversation.config.tts_provider,
                },
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting conversation: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.delete("/conversations/{conversation_id}")
    async def delete_conversation(
        conversation_id: str,
        authorization: str = Header(None),
    ):
        """
        Delete a conversation.

        Permanently removes the conversation and all its turns.
        """
        try:
            # Get user ID from auth
            try:
                user = await get_current_user_func(authorization)
                user_id = user.get("sub") or user.get("id") or "anonymous"
            except Exception:
                user_id = "anonymous"

            manager = await get_manager()
            deleted = await manager.delete_conversation(conversation_id, user_id)

            if not deleted:
                raise HTTPException(status_code=404, detail="Conversation not found")

            return {"message": "Conversation deleted", "conversation_id": conversation_id}

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting conversation: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/conversations/{conversation_id}/end", response_model=ConversationResponse)
    async def end_conversation(
        conversation_id: str,
        authorization: str = Header(None),
    ):
        """
        End/complete a conversation.

        Marks the conversation as completed.
        """
        try:
            # Get user ID from auth
            try:
                user = await get_current_user_func(authorization)
                user_id = user.get("sub") or user.get("id") or "anonymous"
            except Exception:
                user_id = "anonymous"

            manager = await get_manager()
            conversation = await manager.end_conversation(conversation_id, user_id)

            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")

            return ConversationResponse(
                id=conversation.id,
                user_id=conversation.user_id,
                organization_id=conversation.organization_id,
                title=conversation.title,
                status=conversation.status.value,
                total_turns=conversation.total_turns,
                total_cost_usd=conversation.total_cost_usd,
                created_at=conversation.created_at.isoformat(),
                updated_at=conversation.updated_at.isoformat(),
                config={
                    "asr_provider": conversation.config.asr_provider,
                    "llm_model": conversation.config.llm_model,
                    "tts_provider": conversation.config.tts_provider,
                },
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error ending conversation: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/conversations/{conversation_id}/voice", response_model=TurnResponse)
    async def process_voice_turn(
        conversation_id: str,
        request: VoiceTurnRequest,
        authorization: str = Header(None),
    ):
        """
        Process a voice turn.

        Pipeline: Audio -> ASR -> LLM -> TTS -> Audio Response
        """
        try:
            # Get user ID from auth
            try:
                user = await get_current_user_func(authorization)
                user_id = user.get("sub") or user.get("id") or "anonymous"
            except Exception:
                user_id = "anonymous"

            pipeline = await get_pipeline()

            result = await pipeline.process_voice_turn(
                conversation_id=conversation_id,
                audio_base64=request.audio_base64,
                user_id=user_id,
                audio_format=request.audio_format,
                generate_audio=request.generate_audio,
            )

            return TurnResponse(
                conversation_id=result.conversation_id,
                turn_id=result.turn_id,
                user_text=result.user_text,
                detected_language=result.detected_language,
                assistant_text=result.assistant_text,
                audio_base64=result.audio_base64,
                audio_format=result.audio_format,
                audio_duration=result.audio_duration,
                costs={
                    "asr": result.asr_cost,
                    "llm": result.llm_cost,
                    "tts": result.tts_cost,
                    "total": result.total_cost,
                },
                timing={
                    "asr_ms": result.asr_time_ms or 0,
                    "llm_ms": result.llm_time_ms or 0,
                    "tts_ms": result.tts_time_ms or 0,
                    "total_ms": result.processing_time_ms,
                },
                providers_used=result.providers_used,
            )

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error processing voice turn: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/conversations/{conversation_id}/text", response_model=TurnResponse)
    async def process_text_turn(
        conversation_id: str,
        request: TextTurnRequest,
        authorization: str = Header(None),
    ):
        """
        Process a text turn.

        Pipeline: Text -> LLM -> Optional TTS
        """
        try:
            # Get user ID from auth
            try:
                user = await get_current_user_func(authorization)
                user_id = user.get("sub") or user.get("id") or "anonymous"
            except Exception:
                user_id = "anonymous"

            pipeline = await get_pipeline()

            result = await pipeline.process_text_turn(
                conversation_id=conversation_id,
                user_text=request.text,
                user_id=user_id,
                generate_audio=request.generate_audio,
            )

            return TurnResponse(
                conversation_id=result.conversation_id,
                turn_id=result.turn_id,
                user_text=result.user_text,
                detected_language=result.detected_language,
                assistant_text=result.assistant_text,
                audio_base64=result.audio_base64,
                audio_format=result.audio_format,
                audio_duration=result.audio_duration,
                costs={
                    "asr": result.asr_cost,
                    "llm": result.llm_cost,
                    "tts": result.tts_cost,
                    "total": result.total_cost,
                },
                timing={
                    "asr_ms": result.asr_time_ms or 0,
                    "llm_ms": result.llm_time_ms or 0,
                    "tts_ms": result.tts_time_ms or 0,
                    "total_ms": result.processing_time_ms,
                },
                providers_used=result.providers_used,
            )

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error processing text turn: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/conversations/{conversation_id}/stream")
    async def stream_response(
        conversation_id: str,
        text: str = Query(..., description="User input text"),
        authorization: str = Header(None),
    ):
        """
        Stream LLM response in real-time.

        Returns Server-Sent Events (SSE) stream of response chunks.
        """
        try:
            # Get user ID from auth
            try:
                user = await get_current_user_func(authorization)
                user_id = user.get("sub") or user.get("id") or "anonymous"
            except Exception:
                user_id = "anonymous"

            pipeline = await get_pipeline()

            async def event_generator():
                try:
                    async for chunk in pipeline.stream_response(
                        conversation_id=conversation_id,
                        user_text=text,
                        user_id=user_id,
                    ):
                        yield f"data: {chunk}\n\n"
                    yield "data: [DONE]\n\n"
                except Exception as e:
                    yield f"data: [ERROR] {str(e)}\n\n"

            return StreamingResponse(
                event_generator(),
                media_type="text/event-stream",
            )

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error streaming response: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/stats", response_model=UserStatsResponse)
    async def get_user_stats(
        authorization: str = Header(None),
    ):
        """
        Get user conversation statistics.

        Returns aggregated stats for the authenticated user.
        """
        try:
            # Get user ID from auth
            try:
                user = await get_current_user_func(authorization)
                user_id = user.get("sub") or user.get("id") or "anonymous"
            except Exception:
                user_id = "anonymous"

            manager = await get_manager()
            stats = await manager.get_user_stats(user_id)

            return UserStatsResponse(
                total_conversations=stats.get("total_conversations", 0),
                total_turns=stats.get("total_turns", 0),
                total_cost=stats.get("total_cost", 0.0),
                active_conversations=stats.get("active_conversations", 0),
            )

        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/conversations/search")
    async def search_conversations(
        q: str = Query(..., min_length=1, description="Search query"),
        authorization: str = Header(None),
        limit: int = Query(10, ge=1, le=50),
    ):
        """
        Search conversations by content.

        Searches conversation titles and turn content.
        """
        try:
            # Get user ID from auth
            try:
                user = await get_current_user_func(authorization)
                user_id = user.get("sub") or user.get("id") or "anonymous"
            except Exception:
                user_id = "anonymous"

            manager = await get_manager()
            conversations = await manager.search_conversations(
                user_id=user_id,
                query_text=q,
                limit=limit,
            )

            return {
                "query": q,
                "results": [
                    {
                        "id": c.id,
                        "title": c.title,
                        "status": c.status.value,
                        "total_turns": c.total_turns,
                        "updated_at": c.updated_at.isoformat(),
                    }
                    for c in conversations
                ],
                "total": len(conversations),
            }

        except Exception as e:
            logger.error(f"Error searching conversations: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    return router
