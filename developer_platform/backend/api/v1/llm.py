"""
LLM Services API v1 Endpoints

Public, versioned, stable API for LLM (Large Language Model) operations.

**Version:** 1.0.0
**Stability:** Stable - no breaking changes allowed
**Rate Limits:** 10 requests/minute (Free tier)
**Authentication:** API Key required (X-API-Key header)

Breaking changes require releasing v2.
"""

import logging
import httpx
import json
from datetime import datetime
from typing import Optional, List, Dict, Any, AsyncIterator
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# Import middleware
from ...middleware.api_key_auth import verify_api_key
from ...middleware.rate_limiter import get_rate_limit_dependency

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/llm",
    tags=["LLM Services v1"],
    responses={
        401: {"description": "Invalid API key"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"},
    }
)

# ============================================================================
# Pydantic Models
# ============================================================================

class ChatMessage(BaseModel):
    """Chat message in conversation."""
    role: str = Field(..., description="Message role: 'system', 'user', or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Chat request from API."""
    model_id: str = Field(..., description="LLM model ID (e.g., 'kasaai_llama_twi', 'llama_32_3b')")
    messages: List[ChatMessage] = Field(..., description="Conversation messages")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    top_p: float = Field(0.9, ge=0.0, le=1.0, description="Nucleus sampling parameter")
    stream: bool = Field(False, description="Enable streaming response")
    system_prompt: Optional[str] = Field(None, description="System prompt override")


class ChatResponse(BaseModel):
    """Chat response from API."""
    message: str = Field(..., description="Generated message")
    model_id: str = Field(..., description="Model used")
    usage: Dict[str, int] = Field(..., description="Token usage")
    finish_reason: str = Field(..., description="Completion reason")
    cost: float = Field(..., description="Cost in USD")
    transaction_id: Optional[str] = Field(None, description="Transaction ID")
    processing_time: float = Field(..., description="Processing time in seconds")


class CostEstimateRequest(BaseModel):
    """Request for cost estimation."""
    model_id: str = Field(..., description="LLM model ID")
    input_text: str = Field(..., description="Sample input text for estimation")


class CostEstimateResponse(BaseModel):
    """Cost estimation response."""
    estimated_cost: float = Field(..., description="Estimated cost in USD")
    estimated_tokens: int = Field(..., description="Estimated token count")
    model_id: str = Field(..., description="Model ID")


class ProviderHealth(BaseModel):
    """Provider health status."""
    id: str
    name: str
    endpoint: str
    status: str
    last_check: str
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    provider_type: str


class ProvidersResponse(BaseModel):
    """Response with list of providers."""
    providers: Dict[str, ProviderHealth]
    count: int
    online_count: int
    offline_count: int


# ============================================================================
# Helper Functions
# ============================================================================

async def get_core_backend_url() -> str:
    """Get Core Backend URL from environment or default."""
    import os
    return os.getenv("CORE_BACKEND_URL", "https://api.ailabsafrica.com")


async def call_core_backend(
    endpoint: str,
    method: str = "GET",
    json_data: Optional[Dict] = None,
    user_id: Optional[str] = None,
    timeout: float = 300.0
) -> Dict[str, Any]:
    """
    Call Core Backend API.

    Args:
        endpoint: API endpoint path
        method: HTTP method
        json_data: JSON payload
        user_id: User ID for authentication
        timeout: Request timeout in seconds

    Returns:
        Response data

    Raises:
        HTTPException: If request fails
    """
    base_url = await get_core_backend_url()
    url = f"{base_url}{endpoint}"

    # Note: Core Backend uses Supabase auth middleware, not API keys
    # The Developer Platform acts as a proxy with its own API key auth
    headers = {
        "Content-Type": "application/json"
    }

    # If user_id is provided, pass it via custom header for Core Backend to use
    if user_id:
        headers["X-User-Id"] = user_id

    logger.info(f"Calling Core Backend: {method} {url}")

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            if method == "GET":
                response = await client.get(url, headers=headers)
            elif method == "POST":
                response = await client.post(url, json=json_data, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            if response.status_code >= 400:
                error_text = response.text
                logger.error(f"Core Backend error: {response.status_code} - {error_text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail={
                        "error": {
                            "code": "BACKEND_ERROR",
                            "message": f"Core Backend error: {error_text}"
                        },
                        "request_id": f"req_{datetime.utcnow().timestamp()}",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )

            return response.json()

        except httpx.RequestError as e:
            logger.error(f"Core Backend request failed: {e}")
            raise HTTPException(
                status_code=503,
                detail={
                    "error": {
                        "code": "SERVICE_UNAVAILABLE",
                        "message": "Core Backend service unavailable"
                    },
                    "request_id": f"req_{datetime.utcnow().timestamp()}",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )


# ============================================================================
# API Routes
# ============================================================================

@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Chat with LLM model",
    description="""
    Generate a response from an LLM model (non-streaming).

    Automatically deducts cost from your wallet based on token usage.

    **Rate Limit:** 10 requests/minute
    **Cost:** Variable (based on model and tokens)

    **Example Request:**
    ```json
    {
        "model_id": "kasaai_llama_twi",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is the capital of Ghana?"}
        ],
        "temperature": 0.7
    }
    ```

    **Example Response:**
    ```json
    {
        "message": "The capital of Ghana is Accra.",
        "model_id": "kasaai_llama_twi",
        "usage": {
            "prompt_tokens": 25,
            "completion_tokens": 8,
            "total_tokens": 33
        },
        "finish_reason": "stop",
        "cost": 0.0012,
        "transaction_id": "txn_abc123",
        "processing_time": 1.5
    }
    ```
    """,
    response_description="Generated LLM response with cost info"
)
async def chat(
    request: ChatRequest,
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(get_rate_limit_dependency("free", cost=1))
):
    """
    Chat with LLM model (non-streaming).

    This endpoint proxies to the Core Backend LLM service with automatic billing.
    """
    try:
        logger.info(f"LLM chat request: model={request.model_id}, messages={len(request.messages)}")

        # Get user ID from API key info
        user_id = api_key.get("tenant_id")  # Tenant ID acts as user ID

        # Prepare request for Core Backend
        core_request = {
            "model_id": request.model_id,
            "messages": [msg.dict() for msg in request.messages],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "top_p": request.top_p,
            "stream": False,
            "system_prompt": request.system_prompt
        }

        # Call Core Backend
        result = await call_core_backend(
            endpoint="/api/llm/chat",
            method="POST",
            json_data=core_request,
            user_id=user_id,
            timeout=300.0
        )

        logger.info(
            f"LLM chat completed: model={result.get('model_id')}, "
            f"tokens={result.get('usage', {}).get('total_tokens')}, "
            f"cost=${result.get('cost', 0):.4f}"
        )

        return ChatResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in LLM chat: {e}", exc_info=True)
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


@router.post(
    "/chat/stream",
    summary="Chat with LLM model (streaming)",
    description="""
    Generate a streaming response from an LLM model.

    Streams tokens as they're generated using Server-Sent Events (SSE).
    Billing occurs after stream completes.

    **Rate Limit:** 10 requests/minute
    **Cost:** Variable (based on model and tokens)

    **Example Request:**
    ```json
    {
        "model_id": "kasaai_llama_twi",
        "messages": [
            {"role": "user", "content": "Tell me a story"}
        ],
        "temperature": 0.7,
        "stream": true
    }
    ```

    **Response Format:** Server-Sent Events (SSE)
    ```
    data: {"content": "Once", "done": false}
    data: {"content": " upon", "done": false}
    data: {"content": " a", "done": false}
    data: {"content": " time", "done": true}
    ```
    """,
    response_description="SSE stream of tokens"
)
async def chat_stream(
    request: ChatRequest,
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(get_rate_limit_dependency("free", cost=1))
):
    """
    Chat with LLM model (streaming).

    This endpoint proxies to the Core Backend LLM streaming service.
    """
    try:
        logger.info(f"LLM stream request: model={request.model_id}, messages={len(request.messages)}")

        # Get user ID from API key info
        user_id = api_key.get("tenant_id")

        # Prepare request for Core Backend
        core_request = {
            "model_id": request.model_id,
            "messages": [msg.dict() for msg in request.messages],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "top_p": request.top_p,
            "stream": True,
            "system_prompt": request.system_prompt
        }

        base_url = await get_core_backend_url()
        url = f"{base_url}/api/llm/chat/stream"

        # Setup headers
        headers = {
            "Content-Type": "application/json"
        }
        if user_id:
            headers["X-User-Id"] = user_id

        async def stream_generator() -> AsyncIterator[str]:
            """Generate SSE stream from Core Backend."""
            async with httpx.AsyncClient(timeout=300.0) as client:
                try:
                    async with client.stream(
                        "POST",
                        url,
                        json=core_request,
                        headers=headers
                    ) as response:
                        if response.status_code != 200:
                            error_text = await response.aread()
                            logger.error(f"Stream error: {response.status_code} - {error_text}")
                            error_data = {
                                "error": f"Backend error: {error_text.decode()}",
                                "done": True
                            }
                            yield f"data: {json.dumps(error_data)}\n\n"
                            return

                        # Forward SSE stream
                        async for line in response.aiter_lines():
                            if line:
                                yield f"{line}\n"

                except httpx.RequestError as e:
                    logger.error(f"Stream request error: {e}")
                    error_data = {"error": "Stream connection failed", "done": True}
                    yield f"data: {json.dumps(error_data)}\n\n"

        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in LLM stream: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/estimate-cost",
    response_model=CostEstimateResponse,
    summary="Estimate LLM cost",
    description="""
    Estimate the cost of an LLM inference before running.

    **Rate Limit:** 10 requests/minute
    **Cost:** Free

    **Example Request:**
    ```json
    {
        "model_id": "kasaai_llama_twi",
        "input_text": "What is the capital of Ghana?"
    }
    ```

    **Example Response:**
    ```json
    {
        "estimated_cost": 0.0008,
        "estimated_tokens": 8,
        "model_id": "kasaai_llama_twi"
    }
    ```
    """,
    response_description="Cost estimation"
)
async def estimate_cost(
    request: CostEstimateRequest,
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(get_rate_limit_dependency("free", cost=1))
):
    """Estimate LLM inference cost before running."""
    try:
        logger.info(f"Cost estimation request: model={request.model_id}")

        # Get user ID from API key info
        user_id = api_key.get("tenant_id")

        # Call Core Backend
        result = await call_core_backend(
            endpoint="/api/llm/estimate-cost",
            method="POST",
            json_data=request.dict(),
            user_id=user_id
        )

        return CostEstimateResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cost estimation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/providers",
    response_model=ProvidersResponse,
    summary="List LLM providers",
    description="""
    List all available LLM providers with real-time status.

    **Rate Limit:** 10 requests/minute
    **Cost:** Free

    **Query Parameters:**
    - `force_refresh`: Force health check even if cached (default: False)

    **Example Response:**
    ```json
    {
        "providers": {
            "kasaai_llama_twi": {
                "id": "kasaai_llama_twi",
                "name": "Kasaai Llama Twi",
                "endpoint": "http://localhost:11434",
                "status": "online",
                "last_check": "2025-10-26T12:00:00",
                "response_time_ms": 45.2,
                "provider_type": "llm"
            }
        },
        "count": 1,
        "online_count": 1,
        "offline_count": 0
    }
    ```
    """,
    response_description="List of LLM providers with status"
)
async def list_providers(
    force_refresh: bool = Query(False, description="Force health check refresh"),
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(get_rate_limit_dependency("free", cost=1))
):
    """List all available LLM providers with health status."""
    try:
        logger.info(f"Listing LLM providers (force_refresh={force_refresh})")

        # Call Core Backend
        result = await call_core_backend(
            endpoint=f"/api/llm/providers?force_refresh={force_refresh}",
            method="GET"
        )

        return ProvidersResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing LLM providers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/providers/{provider_id}",
    response_model=ProviderHealth,
    summary="Get LLM provider status",
    description="""
    Get status of a specific LLM provider.

    **Rate Limit:** 10 requests/minute
    **Cost:** Free

    **Path Parameters:**
    - `provider_id`: Provider identifier (e.g., 'kasaai_llama_twi', 'llama_32_3b')

    **Example Response:**
    ```json
    {
        "id": "kasaai_llama_twi",
        "name": "Kasaai Llama Twi",
        "endpoint": "http://localhost:11434",
        "status": "online",
        "last_check": "2025-10-26T12:00:00",
        "response_time_ms": 45.2,
        "provider_type": "llm"
    }
    ```
    """,
    response_description="Provider details with status"
)
async def get_provider(
    provider_id: str,
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(get_rate_limit_dependency("free", cost=1))
):
    """Get status of a specific LLM provider."""
    try:
        logger.info(f"Getting LLM provider: {provider_id}")

        # Call Core Backend
        result = await call_core_backend(
            endpoint=f"/api/llm/providers/{provider_id}",
            method="GET"
        )

        return ProviderHealth(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting LLM provider: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/health",
    summary="Health check for LLM services",
    description="""
    Health check for LLM services route.

    **Rate Limit:** None
    **Cost:** Free

    **Example Response:**
    ```json
    {
        "status": "healthy",
        "service": "llm-services",
        "providers_count": 3,
        "billing_enabled": true,
        "health_monitoring_enabled": true
    }
    ```
    """,
    response_description="Health status"
)
async def health_check():
    """Health check for LLM services route."""
    try:
        # Call Core Backend health endpoint
        result = await call_core_backend(
            endpoint="/api/llm/health",
            method="GET"
        )

        return result

    except HTTPException:
        # If Core Backend is down, return unhealthy
        return {
            "status": "unhealthy",
            "service": "llm-services",
            "error": "Core Backend unavailable"
        }
    except Exception as e:
        logger.error(f"LLM health check error: {e}")
        return {
            "status": "unhealthy",
            "service": "llm-services",
            "error": str(e)
        }


# Export router
__all__ = ["router"]
