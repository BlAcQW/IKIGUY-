"""
ASR Services API v1 Endpoints

Public, versioned, stable API for ASR (Automatic Speech Recognition) operations.

**Version:** 1.0.0
**Stability:** Stable - no breaking changes allowed
**Rate Limits:** 10 requests/minute (Free tier)
**Authentication:** API Key required (X-API-Key header)

Breaking changes require releasing v2.
"""

import logging
import httpx
import base64
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile, Form
from pydantic import BaseModel, Field

# Import middleware
from ...middleware.api_key_auth import verify_api_key
from ...middleware.rate_limiter import get_rate_limit_dependency

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/asr",
    tags=["ASR Services v1"],
    responses={
        401: {"description": "Invalid API key"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"},
    }
)

# ============================================================================
# Pydantic Models
# ============================================================================

class TranscriptionRequest(BaseModel):
    """Transcription request from API (base64 audio)."""
    provider_id: str = Field(..., description="ASR provider ID (e.g., 'whisper_large_v3')")
    audio_base64: str = Field(..., description="Base64-encoded audio file")
    language: Optional[str] = Field(None, description="Language code (e.g., 'en', 'tw', 'auto')")
    task: str = Field("transcribe", description="Task type: 'transcribe' or 'translate'")
    response_format: str = Field("json", description="Response format: 'json', 'text', 'srt', 'vtt'")
    temperature: float = Field(0.0, ge=0.0, le=1.0, description="Sampling temperature")
    timestamp_granularities: Optional[List[str]] = Field(None, description="Timestamp levels: ['word', 'segment']")


class TranscriptionResponse(BaseModel):
    """Transcription response from API."""
    text: str = Field(..., description="Transcribed text")
    provider_id: str = Field(..., description="Provider used")
    language: Optional[str] = Field(None, description="Detected language")
    duration: Optional[float] = Field(None, description="Audio duration in seconds")
    cost: float = Field(..., description="Cost in USD")
    transaction_id: Optional[str] = Field(None, description="Transaction ID")
    processing_time: float = Field(..., description="Processing time in seconds")
    model_name: Optional[str] = Field(None, description="Model name used")


class CostEstimateRequest(BaseModel):
    """Request for cost estimation."""
    provider_id: str = Field(..., description="ASR provider ID")
    audio_base64: str = Field(..., description="Base64-encoded audio")


class CostEstimateResponse(BaseModel):
    """Cost estimation response."""
    estimated_cost: float = Field(..., description="Estimated cost in USD")
    estimated_duration: float = Field(..., description="Estimated audio duration in seconds")
    provider_id: str = Field(..., description="Provider ID")


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


class LanguagesResponse(BaseModel):
    """Supported languages response."""
    provider_id: str
    languages: List[str]
    count: int


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
    form_data: Optional[httpx._multipart.MultipartStream] = None,
    user_id: Optional[str] = None,
    timeout: float = 300.0
) -> Dict[str, Any]:
    """
    Call Core Backend API.

    Args:
        endpoint: API endpoint path
        method: HTTP method
        json_data: JSON payload
        form_data: Multipart form data
        user_id: User ID for authentication
        timeout: Request timeout in seconds

    Returns:
        Response data

    Raises:
        HTTPException: If request fails
    """
    base_url = await get_core_backend_url()
    url = f"{base_url}{endpoint}"

    headers = {}
    if not form_data:
        headers["Content-Type"] = "application/json"

    # If user_id is provided, pass it via custom header
    if user_id:
        headers["X-User-Id"] = user_id

    logger.info(f"Calling Core Backend: {method} {url}")

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            if method == "GET":
                response = await client.get(url, headers=headers)
            elif method == "POST":
                if form_data:
                    response = await client.post(url, data=form_data, headers=headers)
                else:
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
    "/transcribe",
    response_model=TranscriptionResponse,
    summary="Transcribe audio (base64)",
    description="""
    Transcribe audio with ASR model.

    Automatically deducts cost from your wallet based on audio duration.

    **Rate Limit:** 10 requests/minute
    **Cost:** Variable (based on provider and duration)

    **Example Request:**
    ```json
    {
        "provider_id": "whisper_large_v3",
        "audio_base64": "UklGRiQAAABXQVZFZm10...",
        "language": "en",
        "task": "transcribe"
    }
    ```

    **Example Response:**
    ```json
    {
        "text": "Hello, welcome to AI Labs Africa.",
        "provider_id": "whisper_large_v3",
        "language": "en",
        "duration": 3.5,
        "cost": 0.0035,
        "transaction_id": "txn_xyz789",
        "processing_time": 1.2,
        "model_name": "whisper-large-v3"
    }
    ```
    """,
    response_description="Transcription with cost info"
)
async def transcribe(
    request: TranscriptionRequest,
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(get_rate_limit_dependency("free", cost=1))
):
    """
    Transcribe audio with ASR model.

    This endpoint proxies to the Core Backend ASR service with automatic billing.
    """
    try:
        logger.info(f"ASR transcription request: provider={request.provider_id}, language={request.language}")

        # Get user ID from API key info
        user_id = api_key.get("tenant_id")

        # Prepare request for Core Backend
        core_request = request.dict()

        # Call Core Backend
        result = await call_core_backend(
            endpoint="/api/asr/transcribe",
            method="POST",
            json_data=core_request,
            user_id=user_id,
            timeout=300.0
        )

        logger.info(
            f"ASR transcription completed: provider={result.get('provider_id')}, "
            f"duration={result.get('duration', 0):.2f}s, "
            f"cost=${result.get('cost', 0):.4f}"
        )

        return TranscriptionResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in ASR transcription: {e}", exc_info=True)
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
    "/transcribe/upload",
    response_model=TranscriptionResponse,
    summary="Transcribe audio file",
    description="""
    Transcribe audio file (multipart form upload).

    Automatically deducts cost from your wallet based on audio duration.

    **Rate Limit:** 10 requests/minute
    **Cost:** Variable (based on provider and duration)

    **Form Parameters:**
    - `audio_file`: Audio file to transcribe (required)
    - `provider_id`: ASR provider ID (required)
    - `language`: Language code (optional)
    - `task`: Task type: 'transcribe' or 'translate' (default: 'transcribe')
    - `response_format`: Response format (default: 'json')
    - `temperature`: Sampling temperature (default: 0.0)

    **Example Response:**
    ```json
    {
        "text": "Hello, welcome to AI Labs Africa.",
        "provider_id": "whisper_large_v3",
        "language": "en",
        "duration": 3.5,
        "cost": 0.0035,
        "transaction_id": "txn_xyz789",
        "processing_time": 1.2,
        "model_name": "whisper-large-v3"
    }
    ```
    """,
    response_description="Transcription with cost info"
)
async def transcribe_upload(
    audio_file: UploadFile = File(..., description="Audio file to transcribe"),
    provider_id: str = Form(..., description="ASR provider ID"),
    language: Optional[str] = Form(None, description="Language code"),
    task: str = Form("transcribe", description="Task type: 'transcribe' or 'translate'"),
    response_format: str = Form("json", description="Response format"),
    temperature: float = Form(0.0, description="Sampling temperature"),
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(get_rate_limit_dependency("free", cost=1))
):
    """
    Transcribe audio file (multipart form upload).

    This endpoint proxies to the Core Backend ASR service with automatic billing.
    """
    try:
        logger.info(f"ASR file transcription request: provider={provider_id}, filename={audio_file.filename}")

        # Get user ID from API key info
        user_id = api_key.get("tenant_id")

        # Read audio file
        audio_bytes = await audio_file.read()

        # Prepare multipart form data for Core Backend
        files = {
            "audio_file": (audio_file.filename, audio_bytes, audio_file.content_type or "audio/wav")
        }
        data = {
            "provider_id": provider_id,
            "task": task,
            "response_format": response_format,
            "temperature": str(temperature)
        }
        if language:
            data["language"] = language

        # Build multipart request
        base_url = await get_core_backend_url()
        url = f"{base_url}/api/asr/transcribe/upload"

        headers = {}
        if user_id:
            headers["X-User-Id"] = user_id

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                url,
                files=files,
                data=data,
                headers=headers
            )

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

            result = response.json()

        logger.info(
            f"ASR file transcription completed: provider={result.get('provider_id')}, "
            f"filename={audio_file.filename}, duration={result.get('duration', 0):.2f}s, "
            f"cost=${result.get('cost', 0):.4f}"
        )

        return TranscriptionResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in ASR file transcription: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/estimate-cost",
    response_model=CostEstimateResponse,
    summary="Estimate ASR cost",
    description="""
    Estimate the cost of ASR transcription before running.

    **Rate Limit:** 10 requests/minute
    **Cost:** Free

    **Example Request:**
    ```json
    {
        "provider_id": "whisper_large_v3",
        "audio_base64": "UklGRiQAAABXQVZFZm10..."
    }
    ```

    **Example Response:**
    ```json
    {
        "estimated_cost": 0.0032,
        "estimated_duration": 3.2,
        "provider_id": "whisper_large_v3"
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
    """Estimate ASR transcription cost before running."""
    try:
        logger.info(f"Cost estimation request: provider={request.provider_id}")

        # Get user ID from API key info
        user_id = api_key.get("tenant_id")

        # Call Core Backend
        result = await call_core_backend(
            endpoint="/api/asr/estimate-cost",
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
    summary="List ASR providers",
    description="""
    List all available ASR providers with real-time status.

    **Rate Limit:** 10 requests/minute
    **Cost:** Free

    **Query Parameters:**
    - `force_refresh`: Force health check even if cached (default: False)

    **Example Response:**
    ```json
    {
        "providers": {
            "whisper_large_v3": {
                "id": "whisper_large_v3",
                "name": "Whisper Large V3",
                "endpoint": "http://whisper:8000",
                "status": "online",
                "last_check": "2025-10-26T12:00:00",
                "response_time_ms": 120.5,
                "provider_type": "asr"
            }
        },
        "count": 1,
        "online_count": 1,
        "offline_count": 0
    }
    ```
    """,
    response_description="List of ASR providers with status"
)
async def list_providers(
    force_refresh: bool = Query(False, description="Force health check refresh"),
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(get_rate_limit_dependency("free", cost=1))
):
    """List all available ASR providers with health status."""
    try:
        logger.info(f"Listing ASR providers (force_refresh={force_refresh})")

        # Call Core Backend
        result = await call_core_backend(
            endpoint=f"/api/asr/providers?force_refresh={force_refresh}",
            method="GET"
        )

        return ProvidersResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing ASR providers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/providers/{provider_id}",
    response_model=ProviderHealth,
    summary="Get ASR provider status",
    description="""
    Get status of a specific ASR provider.

    **Rate Limit:** 10 requests/minute
    **Cost:** Free

    **Path Parameters:**
    - `provider_id`: Provider identifier (e.g., 'whisper_large_v3', 'akan_whisper_giftmark')

    **Example Response:**
    ```json
    {
        "id": "whisper_large_v3",
        "name": "Whisper Large V3",
        "endpoint": "http://whisper:8000",
        "status": "online",
        "last_check": "2025-10-26T12:00:00",
        "response_time_ms": 120.5,
        "provider_type": "asr"
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
    """Get status of a specific ASR provider."""
    try:
        logger.info(f"Getting ASR provider: {provider_id}")

        # Call Core Backend
        result = await call_core_backend(
            endpoint=f"/api/asr/providers/{provider_id}",
            method="GET"
        )

        return ProviderHealth(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ASR provider: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/languages/{provider_id}",
    response_model=LanguagesResponse,
    summary="Get supported languages",
    description="""
    Get supported languages for a specific ASR provider.

    **Rate Limit:** 10 requests/minute
    **Cost:** Free

    **Path Parameters:**
    - `provider_id`: Provider identifier

    **Example Response:**
    ```json
    {
        "provider_id": "whisper_large_v3",
        "languages": ["en", "es", "fr", "de", "tw", "yo", "ig", "ha"],
        "count": 8
    }
    ```
    """,
    response_description="List of supported language codes"
)
async def get_supported_languages(
    provider_id: str,
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(get_rate_limit_dependency("free", cost=1))
):
    """Get supported languages for a specific ASR provider."""
    try:
        logger.info(f"Getting languages for ASR provider: {provider_id}")

        # Call Core Backend
        result = await call_core_backend(
            endpoint=f"/api/asr/languages/{provider_id}",
            method="GET"
        )

        return LanguagesResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting languages: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/health",
    summary="Health check for ASR services",
    description="""
    Health check for ASR services route.

    **Rate Limit:** None
    **Cost:** Free

    **Example Response:**
    ```json
    {
        "status": "healthy",
        "service": "asr-services",
        "providers_count": 2,
        "billing_enabled": true,
        "health_monitoring_enabled": true
    }
    ```
    """,
    response_description="Health status"
)
async def health_check():
    """Health check for ASR services route."""
    try:
        # Call Core Backend health endpoint
        result = await call_core_backend(
            endpoint="/api/asr/health",
            method="GET"
        )

        return result

    except HTTPException:
        # If Core Backend is down, return unhealthy
        return {
            "status": "unhealthy",
            "service": "asr-services",
            "error": "Core Backend unavailable"
        }
    except Exception as e:
        logger.error(f"ASR health check error: {e}")
        return {
            "status": "unhealthy",
            "service": "asr-services",
            "error": str(e)
        }


# Export router
__all__ = ["router"]
