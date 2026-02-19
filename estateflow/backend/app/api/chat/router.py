"""
Chat API Router for EstateFlow.

Provides endpoints for AI-powered property chat interactions.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Optional
import logging

from app.models.chat import ChatRequest, ChatResponse
from app.services.chat_service import PropertyChatService
from app.services.property_service import PropertyService
from app.core.auth import get_current_user, get_optional_user
from app.core.database import get_database

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

# Initialize chat service
chat_service = PropertyChatService()


@router.on_event("startup")
async def startup_event():
    """Initialize chat service on startup."""
    try:
        await chat_service.initialize()
        logger.info("Chat service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize chat service: {e}")


@router.post(
    "/properties/{property_id}",
    response_model=ChatResponse,
    summary="Chat about a property",
    description="""
    Send a message about a specific property and receive an AI-powered response.

    The AI assistant can answer questions about:
    - Property features (bedrooms, bathrooms, amenities)
    - Location and neighborhood (schools, shops, safety)
    - Pet policies
    - Pricing and costs
    - Mortgage estimates
    - And more...

    The response includes:
    - AI-generated reply
    - Source attribution
    - Confidence score
    - Question category
    - Suggested follow-up questions
    """
)
async def chat_about_property(
    property_id: str,
    request: ChatRequest,
    current_user: Optional[dict] = Depends(get_optional_user),
    database = Depends(get_database)
) -> ChatResponse:
    """
    Chat about a property with AI assistant.

    Args:
        property_id: ID of the property to chat about
        request: Chat request with message and conversation history
        current_user: Current authenticated user (optional, uses mock auth if not provided)
        database: Database dependency

    Returns:
        ChatResponse with AI reply and metadata

    Raises:
        HTTPException: If property not found or chat service fails
    """
    try:
        # Ensure property_id in request matches URL parameter
        request.property_id = property_id

        # Use mock auth if no user authenticated (for public property pages)
        if not current_user:
            current_user = {
                "id": "4a6252e7-3dc7-483a-92c3-59a0a814a169",
                "email": "admin@ailabsafrica.com",
                "organization_id": "68cc21d968f3a4c4d6847bc0",
                "role": "admin"
            }

        # Extract organization ID and user ID
        organization_id = current_user.get("organization_id")
        user_id = current_user.get("sub") or current_user.get("id")

        if not organization_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization ID not found in user data"
            )

        # Get property data
        property_service = PropertyService(database)
        property_data = await property_service.get_property(
            property_id=property_id,
            organization_id=organization_id
        )

        if not property_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Property {property_id} not found"
            )

        # Process chat request
        response = await chat_service.chat(
            request=request,
            property_data=property_data,
            organization_id=organization_id,
            user_id=user_id
        )

        logger.info(
            f"Chat processed for property {property_id}, "
            f"category: {response.question_category}, "
            f"confidence: {response.confidence:.2f}, "
            f"time: {response.processing_time_ms:.1f}ms"
        )

        return response

    except ValueError as e:
        logger.error(f"Property not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Chat service error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat request. Please try again."
        )


@router.get(
    "/health",
    summary="Check chat service health",
    description="Health check endpoint for chat service"
)
async def health_check():
    """
    Check if chat service is healthy.

    Returns:
        Status information about the chat service
    """
    try:
        # Basic health check
        return {
            "status": "healthy",
            "service": "property_chat",
            "llm_service": "initialized"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chat service is unhealthy"
        )
