"""
Vapi API v1 Endpoints

Public, versioned, stable API for Vapi voice assistant operations.

**Version:** 1.0.0
**Stability:** Stable - no breaking changes allowed
**Rate Limits:** 10 requests/minute (Free tier)
**Authentication:** API Key required (X-API-Key header)

Breaking changes require releasing v2.
"""

import sys
import os
import logging
import httpx
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from fastapi.responses import JSONResponse

# Add shared to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../shared'))
from integration.vapi import VAPIService, VAPIAgent

# Import v1 models
from ...models.v1 import (
    CreateAssistantRequest,
    UpdateAssistantRequest,
    InitiateCallRequest,
    AssistantResponse,
    CallResponse,
    ListAssistantsResponse,
    ListCallsResponse,
    ErrorResponse,
    ErrorDetail,
)

# Import middleware
from ...middleware.api_key_auth import verify_api_key
from ...middleware.rate_limiter import get_rate_limit_dependency
from ...middleware.usage_tracker import usage_tracker

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/assistants",
    tags=["Assistants v1"],
    responses={
        401: {"description": "Invalid API key"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"},
    }
)

# Helper function to get Vapi config
def get_vapi_config() -> dict:
    """Get Vapi configuration from environment."""
    return {
        "VAPI_API_KEY": os.getenv("VAPI_API_KEY"),
        "VAPI_US_PHONE_ID": os.getenv("VAPI_US_PHONE_ID"),
        "webhook_url": os.getenv("VAPI_WEBHOOK_URL", "https://developer.ailabsafrica.com/webhooks/vapi")
    }


@router.post(
    "/",
    response_model=AssistantResponse,
    status_code=201,
    summary="Create voice assistant",
    description="""
    Create a new voice assistant with specified configuration.

    The assistant can handle inbound calls, make outbound calls, or both depending on configuration.

    **Rate Limit:** 10 requests/minute
    **Cost:** 1 credit per assistant

    **Example Request:**
    ```json
    {
        "name": "Customer Support Assistant",
        "system_prompt": "You are a helpful customer support representative...",
        "voice": "alloy",
        "language": "en"
    }
    ```

    **Example Response:**
    ```json
    {
        "id": "asst_123abc",
        "name": "Customer Support Assistant",
        "status": "active",
        "voice": "alloy",
        "language": "en",
        "created_at": "2025-10-23T12:00:00Z"
    }
    ```

    **Error Codes:**
    - `400` - Invalid request (e.g., name too short, invalid voice)
    - `401` - Invalid API key
    - `429` - Rate limit exceeded or quota exceeded
    - `500` - Internal server error
    """,
    response_description="Successfully created assistant"
)
async def create_assistant(
    request: CreateAssistantRequest,
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(get_rate_limit_dependency("free", cost=1))
):
    """
    Create a new voice assistant.

    This endpoint creates a Vapi-powered voice assistant with the specified
    configuration. The assistant will be ready to handle calls immediately
    upon creation.
    """
    try:
        logger.info(f"Creating assistant: {request.name}")

        # Usage tracking handled automatically by middleware
        # (or could manually record here for granular tracking)

        # Initialize Vapi service with shared library
        vapi_service = VAPIService(config=get_vapi_config())

        # Convert request to VAPIAgent model (from shared library)
        agent = VAPIAgent(
            name=request.name,
            system_prompt=request.system_prompt,
            voice=request.voice,
            language=request.language,
            speed=request.speed,
            call_type=request.call_type.value,
            max_duration=request.max_duration,
            silence_timeout=request.silence_timeout,
            record_calls=request.record_calls,
            metadata=request.metadata or {}
        )

        # Create assistant using shared service
        result = await vapi_service.create_agent(agent)

        if not result.get("success"):
            error_msg = result.get("error", "Failed to create assistant")
            logger.error(f"Assistant creation failed: {error_msg}")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "CREATION_FAILED",
                        "message": error_msg
                    },
                    "request_id": f"req_{datetime.utcnow().timestamp()}",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

        # Convert to stable v1 response
        response = AssistantResponse.from_vapi_response(result)

        logger.info(f"Assistant created successfully: {response.id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating assistant: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An internal error occurred"
                },
                "request_id": f"req_{datetime.utcnow().timestamp()}",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get(
    "/",
    response_model=ListAssistantsResponse,
    summary="List assistants",
    description="""
    Retrieve a list of your voice assistants with pagination.

    **Rate Limit:** 10 requests/minute
    **Cost:** Free

    **Query Parameters:**
    - `limit`: Maximum number of assistants to return (1-100, default: 10)
    - `offset`: Number of assistants to skip (default: 0)

    **Example Response:**
    ```json
    {
        "assistants": [
            {
                "id": "asst_123",
                "name": "Sales Assistant",
                "status": "active",
                "voice": "alloy",
                "language": "en",
                "created_at": "2025-10-23T12:00:00Z"
            }
        ],
        "total": 1,
        "limit": 10,
        "offset": 0
    }
    ```
    """,
    response_description="List of assistants"
)
async def list_assistants(
    limit: int = Query(10, ge=1, le=100, description="Maximum number of assistants to return"),
    offset: int = Query(0, ge=0, description="Number of assistants to skip"),
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(get_rate_limit_dependency("free", cost=1))
):
    """List all assistants with pagination."""
    try:
        logger.info(f"Listing assistants (limit: {limit}, offset: {offset})")

        # Initialize Vapi service
        vapi_service = VAPIService(config=get_vapi_config())

        # Get assistants from shared service
        result = await vapi_service.list_agents(limit=limit, offset=offset)

        if not result.get("success"):
            error_msg = result.get("error", "Failed to list assistants")
            logger.error(f"List assistants failed: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)

        # Convert to stable v1 response
        assistants = []
        for agent_data in result.get("agents", []):
            assistants.append(AssistantResponse.from_vapi_response(agent_data))

        return ListAssistantsResponse(
            assistants=assistants,
            total=result.get("total", len(assistants)),
            limit=limit,
            offset=offset
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error listing assistants: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/{assistant_id}",
    response_model=AssistantResponse,
    summary="Get assistant",
    description="""
    Retrieve details of a specific assistant by ID.

    **Rate Limit:** 10 requests/minute
    **Cost:** Free

    **Path Parameters:**
    - `assistant_id`: The assistant ID to retrieve

    **Example Response:**
    ```json
    {
        "id": "asst_123abc",
        "name": "Sales Assistant",
        "status": "active",
        "voice": "alloy",
        "language": "en",
        "created_at": "2025-10-23T12:00:00Z"
    }
    ```
    """,
    response_description="Assistant details"
)
async def get_assistant(
    assistant_id: str = Path(..., description="Assistant ID"),
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(get_rate_limit_dependency("free", cost=1))
):
    """Get assistant details by ID."""
    try:
        logger.info(f"Getting assistant: {assistant_id}")

        # Initialize Vapi service
        vapi_service = VAPIService(config=get_vapi_config())

        # Get assistant from shared service
        result = await vapi_service.get_assistant(assistant_id)

        if not result.get("success"):
            error_msg = result.get("error", "Assistant not found")
            logger.error(f"Get assistant failed: {error_msg}")
            raise HTTPException(status_code=404, detail=error_msg)

        # Convert to stable v1 response
        assistant_data = result.get("assistant", {})
        return AssistantResponse.from_vapi_response(assistant_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting assistant: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch(
    "/{assistant_id}",
    response_model=AssistantResponse,
    summary="Update assistant",
    description="""
    Update an existing assistant's configuration.

    Only provided fields will be updated. Omitted fields remain unchanged.

    **Rate Limit:** 10 requests/minute
    **Cost:** 1 credit per update

    **Example Request:**
    ```json
    {
        "name": "Updated Sales Assistant",
        "system_prompt": "You are an updated sales assistant..."
    }
    ```
    """,
    response_description="Updated assistant"
)
async def update_assistant(
    assistant_id: str = Path(..., description="Assistant ID"),
    request: UpdateAssistantRequest = Body(...),
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(get_rate_limit_dependency("free", cost=1))
):
    """Update assistant configuration."""
    try:
        logger.info(f"Updating assistant: {assistant_id}")

        # Usage tracking handled automatically by middleware

        # Get Vapi API key
        vapi_api_key = os.getenv("VAPI_API_KEY")
        if not vapi_api_key:
            logger.error("VAPI_API_KEY not configured")
            raise HTTPException(status_code=500, detail="Vapi API key not configured")

        # Build update payload with only provided fields
        update_data = {}
        if request.name is not None:
            update_data["name"] = request.name
        if request.system_prompt is not None:
            update_data["model"] = {"messages": [{"role": "system", "content": request.system_prompt}]}
        if request.voice is not None:
            update_data["voice"] = {"provider": "openai", "voiceId": request.voice}
        if request.first_message is not None:
            update_data["firstMessage"] = request.first_message
        if request.language is not None:
            # Language would be part of transcriber configuration
            update_data["transcriber"] = {"provider": "deepgram", "language": request.language}

        if not update_data:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "NO_UPDATE_FIELDS",
                        "message": "No update fields provided"
                    },
                    "request_id": f"req_{datetime.utcnow().timestamp()}",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

        # Call Vapi API to update assistant
        headers = {
            "Authorization": f"Bearer {vapi_api_key}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.patch(
                f"https://api.vapi.ai/assistant/{assistant_id}",
                json=update_data,
                headers=headers
            )

            if response.status_code == 200:
                assistant_data = response.json()
                logger.info(f"Assistant updated successfully: {assistant_id}")
                return AssistantResponse.from_vapi_response(assistant_data)
            elif response.status_code == 404:
                logger.error(f"Assistant not found: {assistant_id}")
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error": {
                            "code": "NOT_FOUND",
                            "message": "Assistant not found"
                        },
                        "request_id": f"req_{datetime.utcnow().timestamp()}",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
            else:
                error_text = response.text
                logger.error(f"Failed to update assistant: {response.status_code} - {error_text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail={
                        "error": {
                            "code": "UPDATE_FAILED",
                            "message": f"Failed to update assistant: {error_text}"
                        },
                        "request_id": f"req_{datetime.utcnow().timestamp()}",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating assistant: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete(
    "/{assistant_id}",
    status_code=204,
    summary="Delete assistant",
    description="""
    Delete an assistant permanently.

    **Warning:** This action cannot be undone.

    **Rate Limit:** 10 requests/minute
    **Cost:** Free

    **Response:** 204 No Content on success
    """,
    response_description="Assistant deleted successfully"
)
async def delete_assistant(
    assistant_id: str = Path(..., description="Assistant ID"),
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(get_rate_limit_dependency("free", cost=1))
):
    """Delete assistant by ID."""
    try:
        logger.info(f"Deleting assistant: {assistant_id}")

        # Get Vapi API key
        vapi_api_key = os.getenv("VAPI_API_KEY")
        if not vapi_api_key:
            logger.error("VAPI_API_KEY not configured")
            raise HTTPException(status_code=500, detail="Vapi API key not configured")

        # Call Vapi API to delete assistant
        headers = {
            "Authorization": f"Bearer {vapi_api_key}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.delete(
                f"https://api.vapi.ai/assistant/{assistant_id}",
                headers=headers
            )

            if response.status_code in [200, 204]:
                logger.info(f"Assistant deleted successfully: {assistant_id}")
                return JSONResponse(status_code=204, content=None)
            elif response.status_code == 404:
                logger.error(f"Assistant not found: {assistant_id}")
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error": {
                            "code": "NOT_FOUND",
                            "message": "Assistant not found"
                        },
                        "request_id": f"req_{datetime.utcnow().timestamp()}",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
            else:
                error_text = response.text
                logger.error(f"Failed to delete assistant: {response.status_code} - {error_text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail={
                        "error": {
                            "code": "DELETE_FAILED",
                            "message": f"Failed to delete assistant: {error_text}"
                        },
                        "request_id": f"req_{datetime.utcnow().timestamp()}",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error deleting assistant: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# CALLS ENDPOINTS
# ============================================================================

calls_router = APIRouter(
    prefix="/api/v1/calls",
    tags=["Calls v1"],
    responses={
        401: {"description": "Invalid API key"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"},
    }
)


@calls_router.post(
    "/",
    response_model=CallResponse,
    status_code=201,
    summary="Initiate outbound call",
    description="""
    Initiate an outbound voice call using a specified assistant.

    **Rate Limit:** 10 requests/minute
    **Cost:** Variable (based on call duration + destination)

    **Example Request:**
    ```json
    {
        "assistant_id": "asst_123abc",
        "to_number": "+14155551234",
        "from_number": "+14155559999",
        "metadata": {
            "campaign": "summer_sale",
            "customer_id": "cust_456"
        }
    }
    ```

    **Example Response:**
    ```json
    {
        "id": "call_789xyz",
        "assistant_id": "asst_123abc",
        "to_number": "+14155551234",
        "from_number": "+14155559999",
        "status": "initiated",
        "started_at": "2025-10-23T12:05:00Z"
    }
    ```
    """,
    response_description="Call initiated successfully"
)
async def initiate_call(
    request: InitiateCallRequest,
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(get_rate_limit_dependency("free", cost=10))
):
    """Initiate an outbound call."""
    try:
        logger.info(f"Initiating call to {request.to_number}")

        # Usage tracking handled automatically by middleware (with higher cost for calls)

        # Initialize Vapi service
        vapi_service = VAPIService(config=get_vapi_config())

        # Initiate call using shared service
        result = await vapi_service.initiate_call(
            to_number=request.to_number,
            assistant_id=request.assistant_id,
            from_number=request.from_number,
            metadata=request.metadata
        )

        if not result.get("success"):
            error_msg = result.get("error", "Failed to initiate call")
            logger.error(f"Call initiation failed: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)

        # Convert to stable v1 response
        response = CallResponse.from_vapi_response(result)

        logger.info(f"Call initiated successfully: {response.id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error initiating call: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@calls_router.get(
    "/",
    response_model=ListCallsResponse,
    summary="List calls",
    description="""
    Retrieve call history with pagination.

    **Rate Limit:** 10 requests/minute
    **Cost:** Free

    **Query Parameters:**
    - `limit`: Maximum number of calls to return (1-100, default: 10)
    - `offset`: Number of calls to skip (default: 0)
    """,
    response_description="List of calls"
)
async def list_calls(
    limit: int = Query(10, ge=1, le=100, description="Maximum number of calls to return"),
    offset: int = Query(0, ge=0, description="Number of calls to skip"),
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(get_rate_limit_dependency("free", cost=1))
):
    """List call history with pagination."""
    try:
        logger.info(f"Listing calls (limit: {limit}, offset: {offset})")

        # Initialize Vapi service
        vapi_service = VAPIService(config=get_vapi_config())

        # Get calls from shared service
        result = await vapi_service.get_calls()

        if not result.get("success"):
            error_msg = result.get("error", "Failed to list calls")
            logger.error(f"List calls failed: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)

        # Convert to stable v1 response
        calls = []
        calls_data = result.get("data", [])

        # Apply pagination
        paginated_calls = calls_data[offset:offset + limit]

        for call_data in paginated_calls:
            calls.append(CallResponse.from_vapi_response(call_data))

        return ListCallsResponse(
            calls=calls,
            total=len(calls_data),
            limit=limit,
            offset=offset
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error listing calls: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@calls_router.get(
    "/{call_id}",
    response_model=CallResponse,
    summary="Get call details",
    description="""
    Retrieve details of a specific call by ID.

    **Rate Limit:** 10 requests/minute
    **Cost:** Free
    """,
    response_description="Call details"
)
async def get_call(
    call_id: str = Path(..., description="Call ID"),
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(get_rate_limit_dependency("free", cost=1))
):
    """Get call details by ID."""
    try:
        logger.info(f"Getting call: {call_id}")

        # Initialize Vapi service
        vapi_service = VAPIService(config=get_vapi_config())

        # Get call status from shared service
        result = await vapi_service.get_call_status(call_id)

        if not result.get("success"):
            error_msg = result.get("error", "Call not found")
            logger.error(f"Get call failed: {error_msg}")
            raise HTTPException(status_code=404, detail=error_msg)

        # Convert to stable v1 response
        call_data = result.get("call", {})
        return CallResponse.from_vapi_response(call_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting call: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# Export both routers
__all__ = ["router", "calls_router"]
