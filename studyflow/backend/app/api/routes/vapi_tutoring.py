"""
VAPI Voice Tutoring Routes for StudyFlow.

Provides REST endpoints for VAPI-based conversational voice tutoring on documents.
Students can have natural voice conversations about their study materials.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status, Request, Body
from pydantic import BaseModel

from app.services.vapi_document_tutoring_service import VAPIDocumentTutoringService
from app.core.auth import get_current_user_with_org
from app.core.database import mongodb

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vapi-tutoring", tags=["VAPI Voice Tutoring"])


# ============================================================================
# Request/Response Models
# ============================================================================

class CreateAssistantRequest(BaseModel):
    """Request to create VAPI assistant for a document."""
    material_id: str
    voice_id: str = "jennifer"  # Warm, patient voice
    language: str = "en"


class CreateAssistantResponse(BaseModel):
    """Response from creating VAPI assistant."""
    success: bool
    assistant_id: str
    material: dict
    voice: str
    language: str


class StartSessionRequest(BaseModel):
    """Request to start voice tutoring session."""
    material_id: str
    phone_number: str


class StartSessionResponse(BaseModel):
    """Response from starting voice session."""
    success: bool
    session_id: str
    call_id: str
    status: str
    material: dict


class WebhookEvent(BaseModel):
    """VAPI webhook event."""
    event: str
    call_id: Optional[str] = None
    assistant_id: Optional[str] = None
    function_call: Optional[dict] = None
    metadata: Optional[dict] = None
    transcript: Optional[str] = None
    recording_url: Optional[str] = None
    duration: Optional[int] = None
    ended_reason: Optional[str] = None


# ============================================================================
# REST Endpoints
# ============================================================================

@router.post("/assistants", response_model=CreateAssistantResponse)
async def create_document_assistant(
    request: CreateAssistantRequest,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Create a VAPI assistant for a specific document.

    The assistant will be able to:
    - Answer questions about the document content
    - Generate practice exercises
    - Evaluate student responses
    - Provide explanations and examples

    Args:
        request: Assistant creation request
        user_context: User context with organization info

    Returns:
        Created assistant details

    Raises:
        HTTPException: If material not found or assistant creation fails
    """
    try:
        user_id = user_context["user_id"]
        organization_id = user_context["organization_id"]

        result = await VAPIDocumentTutoringService.create_document_assistant(
            material_id=request.material_id,
            organization_id=organization_id,
            user_id=user_id,
            voice_id=request.voice_id,
            language=request.language
        )

        logger.info(
            f"VAPI assistant created: assistant_id={result['assistant_id']}, "
            f"material={request.material_id}, user={user_id}"
        )

        return CreateAssistantResponse(
            success=result["success"],
            assistant_id=result["assistant_id"],
            material=result["material"],
            voice=result["voice"],
            language=result["language"]
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Assistant creation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create assistant: {str(e)}"
        )


@router.post("/sessions/start", response_model=StartSessionResponse)
async def start_voice_session(
    request: StartSessionRequest,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Start a VAPI voice tutoring session for a document.

    Initiates an outbound call to the student's phone number.
    The VAPI assistant will have a natural conversation about the study material.

    Args:
        request: Session start request with material ID and phone number
        user_context: User context with organization info

    Returns:
        Session and call details

    Raises:
        HTTPException: If material/assistant not found or call fails
    """
    try:
        student_id = user_context["user_id"]
        organization_id = user_context["organization_id"]

        result = await VAPIDocumentTutoringService.start_voice_session(
            material_id=request.material_id,
            student_id=student_id,
            organization_id=organization_id,
            phone_number=request.phone_number
        )

        logger.info(
            f"Voice session started: session_id={result['session_id']}, "
            f"call_id={result['call_id']}, student={student_id}"
        )

        return StartSessionResponse(
            success=result["success"],
            session_id=result["session_id"],
            call_id=result["call_id"],
            status=result["status"],
            material=result["material"]
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Session start error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start session: {str(e)}"
        )


# ============================================================================
# Webhook Endpoint
# ============================================================================

@router.post("/webhook")
async def vapi_webhook(
    request: Request,
    event: WebhookEvent = Body(...)
):
    """
    Handle VAPI webhook events.

    Processes events from VAPI including:
    - call.started: Call initiated
    - call.ended: Call completed
    - function-call: Assistant requesting function execution
    - transcript: Real-time transcription
    - message: Assistant message

    Args:
        request: FastAPI request object
        event: Webhook event data

    Returns:
        Function call results or acknowledgment

    Note:
        For function calls, returns the function result directly to VAPI
        so the assistant can continue the conversation.
    """
    try:
        logger.info(f"VAPI webhook event: {event.event}")

        # Handle function calls
        if event.event == "function-call" and event.function_call:
            function_name = event.function_call.get("name")
            arguments = event.function_call.get("arguments", {})

            # Get session ID from metadata
            session_id = event.metadata.get("session_id") if event.metadata else None
            organization_id = event.metadata.get("organization_id") if event.metadata else None

            if not session_id or not organization_id:
                logger.error("Missing session_id or organization_id in webhook metadata")
                return {
                    "success": False,
                    "error": "Missing required metadata"
                }

            # Execute function
            result = await VAPIDocumentTutoringService.handle_function_call(
                function_name=function_name,
                arguments=arguments,
                session_id=session_id,
                organization_id=organization_id
            )

            logger.info(
                f"Function call executed: {function_name}, "
                f"session={session_id}, success={result.get('success')}"
            )

            # Return result to VAPI
            return result

        # Handle call started
        elif event.event == "call.started":
            logger.info(f"Call started: call_id={event.call_id}")

            # Could update session status here
            return {
                "success": True,
                "event": "call_started",
                "call_id": event.call_id
            }

        # Handle call ended
        elif event.event == "call.ended":
            logger.info(
                f"Call ended: call_id={event.call_id}, "
                f"duration={event.duration}s, reason={event.ended_reason}"
            )

            # Get session ID from metadata and end session
            if event.metadata:
                session_id = event.metadata.get("session_id")
                organization_id = event.metadata.get("organization_id")

                if session_id and organization_id:
                    from app.services.tutoring_service import TutoringService
                    await TutoringService.end_session(session_id, organization_id)
                    logger.info(f"Session ended: {session_id}")

            return {
                "success": True,
                "event": "call_ended",
                "call_id": event.call_id,
                "duration": event.duration
            }

        # Handle transcript
        elif event.event == "transcript":
            logger.debug(f"Transcript: {event.transcript}")
            return {
                "success": True,
                "event": "transcript_received"
            }

        # Handle other events
        else:
            logger.info(f"Unhandled webhook event: {event.event}")
            return {
                "success": True,
                "event": event.event,
                "message": "Event received"
            }

    except Exception as e:
        logger.error(f"Webhook error: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/voices")
async def list_available_voices(
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    List available VAPI voices for tutoring.

    Returns a curated list of warm, patient voices suitable for educational contexts.

    Args:
        user_context: User context with organization info

    Returns:
        List of available voices with descriptions
    """
    # Curated voices for educational tutoring
    voices = [
        {
            "id": "jennifer",
            "name": "Jennifer",
            "description": "Warm, patient, encouraging - ideal for tutoring",
            "language": "en",
            "gender": "female",
            "recommended": True
        },
        {
            "id": "mark",
            "name": "Mark",
            "description": "Clear, professional, supportive",
            "language": "en",
            "gender": "male",
            "recommended": True
        },
        {
            "id": "sarah",
            "name": "Sarah",
            "description": "Friendly, energetic, motivating",
            "language": "en",
            "gender": "female",
            "recommended": False
        },
        {
            "id": "david",
            "name": "David",
            "description": "Calm, steady, reassuring",
            "language": "en",
            "gender": "male",
            "recommended": False
        }
    ]

    return {
        "success": True,
        "voices": voices,
        "total": len(voices)
    }


@router.get("/materials/{material_id}/assistant")
async def get_material_assistant(
    material_id: str,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Check if a material has a VAPI assistant configured.

    Args:
        material_id: Material ID
        user_context: User context with organization info

    Returns:
        Assistant information if exists

    Raises:
        HTTPException: If material not found
    """
    try:
        from app.services.material_service import MaterialService

        organization_id = user_context["organization_id"]

        material = await MaterialService.get_material_by_id(material_id, organization_id)
        if not material:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Material not found: {material_id}"
            )

        assistant_id = material.metadata.get("vapi_assistant_id") if material.metadata else None

        if assistant_id:
            return {
                "success": True,
                "has_assistant": True,
                "assistant_id": assistant_id,
                "created_at": material.metadata.get("vapi_assistant_created_at"),
                "material": {
                    "id": material.id,
                    "title": material.title,
                    "subject": material.subject
                }
            }
        else:
            return {
                "success": True,
                "has_assistant": False,
                "material": {
                    "id": material.id,
                    "title": material.title,
                    "subject": material.subject
                }
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking assistant: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check assistant: {str(e)}"
        )
