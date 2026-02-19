"""
Voice chat routes for StudyFlow.

Provides both REST and WebSocket endpoints for voice-based tutoring.
"""

import logging
import json
from typing import Optional, Any
from fastapi import APIRouter, HTTPException, Depends, status, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from app.services.voice_tutoring_service import VoiceTutoringService
from app.services.tutoring_service import TutoringService
from app.core.auth import get_current_user_with_org, SupabaseAuth
from app.core.database import mongodb
from app.services.user_service import UserService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice-chat", tags=["Voice Chat"])


# ============================================================================
# Request/Response Models
# ============================================================================

class VoiceQuestionRequest(BaseModel):
    """
    Request for voice question processing.

    All voice settings (TTS, ASR, language) are optional.
    If not provided, the user's Voice Settings page preferences are used.
    """
    session_id: str
    audio_base64: str
    asr_provider_id: Optional[str] = Field(
        default=None,
        description="ASR provider override. Uses Voice Settings if None."
    )
    tts_provider_id: Optional[str] = Field(
        default=None,
        description="TTS provider override. Uses Voice Settings if None."
    )
    tts_voice_id: Optional[str] = Field(
        default=None,
        description="TTS voice ID override. Uses Voice Settings if None."
    )
    tts_speed: Optional[float] = Field(
        default=None,
        description="TTS speed override (0.5-2.0). Uses Voice Settings if None."
    )
    tts_pitch: Optional[float] = Field(
        default=None,
        description="TTS pitch override (-1.0 to 1.0). Uses Voice Settings if None."
    )
    language: Optional[str] = Field(
        default=None,
        description="Language code override. Uses Voice Settings if None."
    )


class VoiceQuestionResponse(BaseModel):
    """Response from voice question processing."""
    question_id: str
    transcribed_text: str
    detected_language: Optional[str]
    response_text: str
    response_audio_base64: str
    audio_duration: float
    confidence_score: float
    sources: list
    cost_breakdown: dict
    performance: dict


class WebSocketMessage(BaseModel):
    """WebSocket message format."""
    type: str  # "audio_chunk", "text", "status", "error"
    data: dict


# ============================================================================
# REST Endpoints
# ============================================================================

@router.post("/ask", response_model=VoiceQuestionResponse)
async def ask_voice_question(
    request: VoiceQuestionRequest,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Process a voice question in a tutoring session.

    Handles the complete voice-to-voice pipeline:
    1. Transcribe user's audio question (ASR)
    2. Query knowledge base and generate response (RAG + LLM)
    3. Synthesize response to audio (TTS)

    Args:
        request: Voice question request with audio and session info
        user_context: User context with organization info

    Returns:
        Complete voice response with transcription, text, and audio

    Raises:
        HTTPException: If session not found or processing fails
    """
    try:
        user_id = user_context["user_id"]
        organization_id = user_context["organization_id"]

        # Initialize voice service if needed
        try:
            await VoiceTutoringService.initialize()
        except Exception as e:
            logger.warning(f"Voice service already initialized or initialization failed: {e}")

        # Process voice question (uses Voice Settings if params are None)
        result = await VoiceTutoringService.process_voice_question(
            session_id=request.session_id,
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
            f"Voice question processed: session={request.session_id}, "
            f"user={user_id}, cost=${result['cost_breakdown']['total']:.4f}"
        )

        return VoiceQuestionResponse(
            question_id=result["question_id"],
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
        logger.error(f"Voice question error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process voice question: {str(e)}"
        )


@router.get("/providers")
async def get_voice_providers(
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Get available ASR and TTS providers for voice chat.

    Returns provider health status, capabilities, and supported languages.

    Args:
        user_context: User context with organization info

    Returns:
        Dict with ASR and TTS provider information
    """
    try:
        # Initialize voice service if needed
        try:
            await VoiceTutoringService.initialize()
        except Exception as e:
            logger.warning(f"Voice service initialization: {e}")

        providers = await VoiceTutoringService.get_available_voice_providers()
        return providers

    except Exception as e:
        logger.error(f"Failed to get providers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve providers: {str(e)}"
        )


@router.post("/estimate-cost")
async def estimate_voice_cost(
    audio_duration: float,
    response_length: int = 500,
    asr_provider: str = "whisper_large_v3",  # Self-hosted at whisper.ailabsafrica.com
    tts_provider: str = "coqui_xtts",
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Estimate cost for a voice interaction.

    Useful for showing users expected costs before they use voice features.

    Args:
        audio_duration: Audio duration in seconds
        response_length: Expected response character count
        asr_provider: ASR provider ID
        tts_provider: TTS provider ID
        user_context: User context with organization info

    Returns:
        Cost estimate breakdown
    """
    try:
        # Initialize voice service if needed
        try:
            await VoiceTutoringService.initialize()
        except Exception as e:
            logger.warning(f"Voice service initialization: {e}")

        estimate = await VoiceTutoringService.estimate_voice_cost(
            audio_duration,
            response_length,
            asr_provider,
            tts_provider
        )

        return estimate

    except Exception as e:
        logger.error(f"Cost estimation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to estimate cost: {str(e)}"
        )


# ============================================================================
# WebSocket Endpoint for Real-Time Voice Chat
# ============================================================================

@router.websocket("/ws/{session_id}")
async def voice_chat_websocket(
    websocket: WebSocket,
    session_id: str,
    token: str  # JWT token passed as query parameter
):
    """
    WebSocket endpoint for real-time voice chat.

    Protocol:
    1. Client connects with JWT token
    2. Server sends "connected" status
    3. Client streams audio chunks → Server transcribes
    4. Server processes question → Sends response chunks
    5. Client receives text + audio response

    Message Format (Client → Server):
    {
        "type": "audio_chunk",
        "data": {
            "audio_base64": "...",
            "sequence": 0,
            "is_final": false
        }
    }

    Message Format (Server → Client):
    {
        "type": "status" | "transcript" | "response" | "audio_chunk" | "error",
        "data": { ... }
    }

    Args:
        websocket: WebSocket connection
        session_id: Study session ID
        token: JWT authentication token
    """
    # Accept connection
    await websocket.accept()

    try:
        # Authenticate using JWT token
        try:
            supabase_auth = SupabaseAuth()
            token_payload = supabase_auth.verify_token(token)
            supabase_user_id = token_payload.get("sub")

            if not supabase_user_id:
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": "Invalid authentication token"}
                })
                await websocket.close(code=1008)  # Policy violation
                return

            # Get user with organization context
            user = await UserService.get_user_by_supabase_id(supabase_user_id)
            if not user:
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": "User not found"}
                })
                await websocket.close(code=1008)
                return

            user_id = user.id
            organization_id = user.organization_id

            logger.info(
                f"WebSocket authenticated: user={user_id}, org={organization_id}, "
                f"session={session_id}"
            )

        except Exception as e:
            logger.error(f"WebSocket authentication failed: {str(e)}")
            await websocket.send_json({
                "type": "error",
                "data": {"message": f"Authentication failed: {str(e)}"}
            })
            await websocket.close(code=1008)  # Policy violation
            return

        # Send connected status
        await websocket.send_json({
            "type": "status",
            "data": {
                "status": "connected",
                "session_id": session_id,
                "organization_id": organization_id,
                "message": "Voice chat ready"
            }
        })

        # Initialize voice service
        try:
            await VoiceTutoringService.initialize()
        except Exception as e:
            logger.warning(f"Voice service already initialized: {e}")

        # Message handling loop
        while True:
            try:
                # Receive message from client
                message_raw = await websocket.receive_text()
                message = json.loads(message_raw)

                message_type = message.get("type")
                message_data = message.get("data", {})

                if message_type == "audio_chunk":
                    # Handle audio chunk
                    audio_base64 = message_data.get("audio_base64")
                    is_final = message_data.get("is_final", False)

                    if is_final:
                        # Process complete audio
                        logger.info(f"Processing final audio chunk for session {session_id}")

                        # Send processing status
                        await websocket.send_json({
                            "type": "status",
                            "data": {"status": "processing", "message": "Transcribing audio..."}
                        })

                        try:
                            # Process voice question (uses Voice Settings if params are None)
                            result = await VoiceTutoringService.process_voice_question(
                                session_id=session_id,
                                audio_base64=audio_base64,
                                organization_id=organization_id,
                                user_id=user_id,
                                asr_provider_id=message_data.get("asr_provider"),  # None uses Voice Settings
                                tts_provider_id=message_data.get("tts_provider"),  # None uses Voice Settings
                                tts_voice_id=message_data.get("tts_voice_id"),  # None uses Voice Settings
                                tts_speed=message_data.get("tts_speed"),  # None uses Voice Settings
                                tts_pitch=message_data.get("tts_pitch"),  # None uses Voice Settings
                                language=message_data.get("language")  # None uses Voice Settings
                            )

                            # Send transcript
                            await websocket.send_json({
                                "type": "transcript",
                                "data": {
                                    "text": result["transcribed_text"],
                                    "language": result["detected_language"]
                                }
                            })

                            # Send response text
                            await websocket.send_json({
                                "type": "response",
                                "data": {
                                    "text": result["response_text"],
                                    "confidence": result["confidence_score"],
                                    "sources": result["sources"]
                                }
                            })

                            # Send audio response
                            await websocket.send_json({
                                "type": "audio_chunk",
                                "data": {
                                    "audio_base64": result["response_audio_base64"],
                                    "duration": result["audio_duration"],
                                    "is_final": True
                                }
                            })

                            # Send cost and performance info
                            await websocket.send_json({
                                "type": "status",
                                "data": {
                                    "status": "completed",
                                    "question_id": result["question_id"],
                                    "cost": result["cost_breakdown"],
                                    "performance": result["performance"]
                                }
                            })

                        except Exception as e:
                            logger.error(f"Voice processing error: {str(e)}", exc_info=True)
                            await websocket.send_json({
                                "type": "error",
                                "data": {
                                    "error": str(e),
                                    "message": "Failed to process voice message"
                                }
                            })

                elif message_type == "ping":
                    # Heartbeat
                    await websocket.send_json({
                        "type": "pong",
                        "data": {"timestamp": message_data.get("timestamp")}
                    })

                else:
                    logger.warning(f"Unknown message type: {message_type}")

            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for session: {session_id}")
                break

            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "data": {"error": "Invalid JSON format"}
                })

            except Exception as e:
                logger.error(f"WebSocket error: {str(e)}", exc_info=True)
                await websocket.send_json({
                    "type": "error",
                    "data": {"error": str(e)}
                })

    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}", exc_info=True)
    finally:
        logger.info(f"WebSocket connection closed for session: {session_id}")
