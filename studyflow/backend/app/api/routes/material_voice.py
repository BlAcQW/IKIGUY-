"""
Material Voice Chat Routes for StudyFlow.

Provides browser-based voice interaction with study materials.
Uses the user's voice settings for TTS/ASR configuration.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel

from app.services.material_voice_service import MaterialVoiceService
from app.core.auth import get_current_user_with_org

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/material-voice", tags=["Material Voice Chat"])


# ============================================================================
# Request/Response Models
# ============================================================================

class MaterialVoiceQuestionRequest(BaseModel):
    """Request for material voice question."""
    audio_base64: str
    asr_provider_id: Optional[str] = None  # Uses voice settings if None
    tts_provider_id: Optional[str] = None  # Uses voice settings if None
    tts_voice_id: Optional[str] = None     # Uses voice settings if None
    tts_speed: Optional[float] = None      # Uses voice settings if None
    tts_pitch: Optional[float] = None      # Uses voice settings if None
    language: Optional[str] = None         # Uses voice settings if None


class MaterialVoiceQuestionResponse(BaseModel):
    """Response from material voice question."""
    chat_id: str
    transcribed_text: str
    detected_language: Optional[str]
    response_text: str
    response_audio_base64: str
    audio_duration: float
    confidence_score: float
    sources: list
    cost_breakdown: dict
    performance: dict


class ChatHistoryEntry(BaseModel):
    """Chat history entry."""
    id: str
    question_text: str
    answer_text: str
    confidence_score: float
    created_at: str


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/{material_id}/ask", response_model=MaterialVoiceQuestionResponse)
async def ask_material_voice_question(
    material_id: str,
    request: MaterialVoiceQuestionRequest,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Ask a voice question about a specific material.

    This endpoint processes the complete voice-to-voice pipeline:
    1. Transcribe user's audio question (ASR)
    2. Query material's RAG embeddings for context
    3. Generate response using LLM
    4. Synthesize response to audio (TTS)

    Uses the user's voice settings from /voice-settings/me for:
    - TTS provider and voice
    - ASR provider
    - Speed and other preferences

    Args:
        material_id: Study material ID
        request: Voice question request with audio
        user_context: User context with organization info

    Returns:
        Complete voice response with transcription, text, and audio

    Raises:
        HTTPException: If material not found or processing fails
    """
    try:
        user_id = user_context["user_id"]
        organization_id = user_context["organization_id"]

        # Initialize service
        try:
            await MaterialVoiceService.initialize()
        except Exception as e:
            logger.warning(f"MaterialVoiceService already initialized: {e}")

        # Process voice question (uses Voice Settings if params are None)
        result = await MaterialVoiceService.process_voice_question(
            material_id=material_id,
            audio_base64=request.audio_base64,
            organization_id=organization_id,
            user_id=user_id,
            asr_provider_id=request.asr_provider_id,
            tts_provider_id=request.tts_provider_id,
            tts_voice_id=request.tts_voice_id,
            tts_speed=request.tts_speed,
            tts_pitch=request.tts_pitch,
            language=request.language
        )

        logger.info(
            f"Material voice question processed: material={material_id}, "
            f"user={user_id}, cost=${result['cost_breakdown']['total']:.4f}"
        )

        return MaterialVoiceQuestionResponse(
            chat_id=result["chat_id"],
            transcribed_text=result["transcribed_text"],
            detected_language=result["detected_language"],
            response_text=result["response_text"],
            response_audio_base64=result["response_audio_base64"],
            audio_duration=result["audio_duration"],
            confidence_score=result["confidence_score"],
            sources=result["sources"],
            cost_breakdown=result["cost_breakdown"],
            performance=result["performance"]
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Material voice question error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process voice question: {str(e)}"
        )


@router.get("/{material_id}/history")
async def get_material_chat_history(
    material_id: str,
    limit: int = 20,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Get voice chat history for a material.

    Returns the user's conversation history with this material,
    ordered from oldest to newest.

    Args:
        material_id: Study material ID
        limit: Maximum entries to return (default 20)
        user_context: User context with organization info

    Returns:
        List of chat history entries
    """
    try:
        user_id = user_context["user_id"]
        organization_id = user_context["organization_id"]

        history = await MaterialVoiceService.get_chat_history(
            material_id=material_id,
            organization_id=organization_id,
            user_id=user_id,
            limit=limit
        )

        return {
            "material_id": material_id,
            "count": len(history),
            "history": history
        }

    except Exception as e:
        logger.error(f"Failed to get chat history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get chat history: {str(e)}"
        )


@router.delete("/{material_id}/history")
async def clear_material_chat_history(
    material_id: str,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Clear voice chat history for a material.

    Deletes all conversation history for this material and user.

    Args:
        material_id: Study material ID
        user_context: User context with organization info

    Returns:
        Number of entries deleted
    """
    try:
        user_id = user_context["user_id"]
        organization_id = user_context["organization_id"]

        deleted_count = await MaterialVoiceService.clear_chat_history(
            material_id=material_id,
            organization_id=organization_id,
            user_id=user_id
        )

        return {
            "material_id": material_id,
            "deleted_count": deleted_count,
            "message": f"Cleared {deleted_count} chat history entries"
        }

    except Exception as e:
        logger.error(f"Failed to clear chat history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear chat history: {str(e)}"
        )


@router.get("/{material_id}/check")
async def check_material_voice_ready(
    material_id: str,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Check if a material is ready for voice chat.

    Verifies that the material exists and has been processed
    (has RAG embeddings available).

    Args:
        material_id: Study material ID
        user_context: User context with organization info

    Returns:
        Material readiness status
    """
    try:
        organization_id = user_context["organization_id"]

        material = await MaterialVoiceService.get_material(
            material_id=material_id,
            organization_id=organization_id
        )

        if not material:
            return {
                "ready": False,
                "material_id": material_id,
                "reason": "Material not found"
            }

        embedding_collection = material.get("embedding_collection")
        if not embedding_collection:
            return {
                "ready": False,
                "material_id": material_id,
                "title": material.get("title"),
                "status": material.get("status"),
                "reason": "Material has not been processed yet"
            }

        return {
            "ready": True,
            "material_id": material_id,
            "title": material.get("title"),
            "subject": material.get("subject"),
            "topics": material.get("topics", []),
            "embedding_collection": embedding_collection
        }

    except Exception as e:
        logger.error(f"Failed to check material: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check material: {str(e)}"
        )
