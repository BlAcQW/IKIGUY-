"""
TTS Services API v1 Endpoints

Public, versioned, stable API for TTS (Text-to-Speech) operations.

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
    prefix="/api/v1/tts",
    tags=["TTS Services v1"],
    responses={
        401: {"description": "Invalid API key"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"},
    }
)

# ============================================================================
# Pydantic Models
# ============================================================================

class SynthesisRequest(BaseModel):
    """Synthesis request from API."""
    provider_id: str = Field(..., description="TTS provider ID (e.g., 'coqui_xtts', 'melotts')")
    text: str = Field(..., description="Text to synthesize")
    language: str = Field("en", description="Language code (e.g., 'en', 'tw')")
    voice_id: Optional[str] = Field(None, description="Voice ID or speaker")
    speed: float = Field(1.0, ge=0.5, le=2.0, description="Speech speed (0.5-2.0)")
    pitch: float = Field(0.0, description="Pitch adjustment")
    remove_silence: bool = Field(False, description="Remove silence from output")
    output_format: str = Field("wav", description="Output format (wav, mp3)")


class VoiceCloneRequest(BaseModel):
    """Voice cloning request from API (base64 audio)."""
    provider_id: str = Field(..., description="TTS provider ID")
    text: str = Field(..., description="Text to synthesize")
    reference_audio_base64: str = Field(..., description="Base64-encoded reference audio")
    language: str = Field("en", description="Language code")
    speed: float = Field(1.0, ge=0.5, le=2.0, description="Speech speed")
    remove_silence: bool = Field(False, description="Remove silence")


class SynthesisResponse(BaseModel):
    """Synthesis response from API."""
    audio_base64: str = Field(..., description="Generated audio in base64")
    text: str = Field(..., description="Input text")
    provider_id: str = Field(..., description="Provider used")
    voice_id: Optional[str] = Field(None, description="Voice ID used")
    duration: float = Field(..., description="Audio duration in seconds")
    processing_time: float = Field(..., description="Processing time in seconds")
    cost: float = Field(..., description="Cost in USD")
    transaction_id: Optional[str] = Field(None, description="Transaction ID")
    format: str = Field("wav", description="Audio format")


class CostEstimateRequest(BaseModel):
    """Request for cost estimation."""
    provider_id: str = Field(..., description="TTS provider ID")
    text: str = Field(..., description="Sample text")
    voice_cloning: bool = Field(False, description="Whether voice cloning will be used")


class CostEstimateResponse(BaseModel):
    """Cost estimation response."""
    estimated_cost: float = Field(..., description="Estimated cost in USD")
    character_count: int = Field(..., description="Character count")
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
    form_data: Optional[Dict] = None,
    files: Optional[Dict] = None,
    user_id: Optional[str] = None,
    timeout: float = 120.0
) -> Dict[str, Any]:
    """
    Call Core Backend API.

    Args:
        endpoint: API endpoint path
        method: HTTP method
        json_data: JSON payload
        form_data: Form data
        files: Files to upload
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
    if not form_data and not files:
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
                if files:
                    response = await client.post(url, data=form_data, files=files, headers=headers)
                elif form_data:
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
    "/synthesize",
    response_model=SynthesisResponse,
    summary="Synthesize speech",
    description="""
    Synthesize speech from text.

    Automatically deducts cost from your wallet based on character count.

    **Rate Limit:** 10 requests/minute
    **Cost:** Variable (based on provider and text length)

    **Example Request:**
    ```json
    {
        "provider_id": "coqui_xtts",
        "text": "Hello, welcome to AI Labs Africa.",
        "language": "en",
        "speed": 1.0
    }
    ```

    **Example Response:**
    ```json
    {
        "audio_base64": "UklGRiQAAABXQVZFZm10...",
        "text": "Hello, welcome to AI Labs Africa.",
        "provider_id": "coqui_xtts",
        "duration": 3.5,
        "processing_time": 1.2,
        "cost": 0.00023,
        "transaction_id": "txn_xyz789",
        "format": "wav"
    }
    ```
    """,
    response_description="Synthesized audio with cost info"
)
async def synthesize(
    request: SynthesisRequest,
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(get_rate_limit_dependency("free", cost=1))
):
    """
    Synthesize speech from text.

    This endpoint proxies to the Core Backend TTS service with automatic billing.
    """
    try:
        logger.info(f"TTS synthesis request: provider={request.provider_id}, chars={len(request.text)}")

        # Get user ID from API key info
        user_id = api_key.get("tenant_id")

        # Prepare request for Core Backend
        core_request = request.dict()

        # Call Core Backend
        result = await call_core_backend(
            endpoint="/api/tts/synthesize",
            method="POST",
            json_data=core_request,
            user_id=user_id,
            timeout=120.0
        )

        logger.info(
            f"TTS synthesis completed: provider={result.get('provider_id')}, "
            f"duration={result.get('duration', 0):.2f}s, "
            f"cost=${result.get('cost', 0):.4f}"
        )

        return SynthesisResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in TTS synthesis: {e}", exc_info=True)
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
    "/synthesize/upload",
    response_model=SynthesisResponse,
    summary="Synthesize with voice cloning (file upload)",
    description="""
    Synthesize speech with voice cloning using file upload.

    Automatically deducts cost from your wallet.

    **Rate Limit:** 10 requests/minute
    **Cost:** Variable (higher for voice cloning)

    **Form Parameters:**
    - `audio_file`: Reference audio file for cloning (required)
    - `provider_id`: TTS provider ID (required)
    - `text`: Text to synthesize (required)
    - `language`: Language code (default: 'en')
    - `speed`: Speech speed (default: 1.0)
    - `remove_silence`: Remove silence flag (default: false)

    **Example Response:**
    ```json
    {
        "audio_base64": "UklGRiQAAABXQVZFZm10...",
        "text": "This is cloned voice speech.",
        "provider_id": "f5tts",
        "duration": 4.2,
        "processing_time": 3.1,
        "cost": 0.055,
        "transaction_id": "txn_xyz789",
        "format": "wav"
    }
    ```
    """,
    response_description="Synthesized audio with cloned voice"
)
async def synthesize_upload(
    audio_file: UploadFile = File(..., description="Reference audio file"),
    provider_id: str = Form(..., description="TTS provider ID"),
    text: str = Form(..., description="Text to synthesize"),
    language: str = Form("en", description="Language code"),
    speed: float = Form(1.0, description="Speech speed"),
    remove_silence: bool = Form(False, description="Remove silence"),
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(get_rate_limit_dependency("free", cost=1))
):
    """
    Synthesize speech with voice cloning (file upload).

    This endpoint proxies to the Core Backend TTS service with automatic billing.
    """
    try:
        logger.info(f"Voice cloning request: provider={provider_id}, filename={audio_file.filename}")

        # Get user ID from API key info
        user_id = api_key.get("tenant_id")

        # Read audio file
        audio_bytes = await audio_file.read()

        # Prepare multipart form data for Core Backend
        files_data = {
            "audio_file": (audio_file.filename, audio_bytes, audio_file.content_type or "audio/wav")
        }
        form_data = {
            "provider_id": provider_id,
            "text": text,
            "language": language,
            "speed": str(speed),
            "remove_silence": str(remove_silence).lower()
        }

        # Build multipart request
        base_url = await get_core_backend_url()
        url = f"{base_url}/api/tts/synthesize/upload"

        headers = {}
        if user_id:
            headers["X-User-Id"] = user_id

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                url,
                files=files_data,
                data=form_data,
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
            f"Voice cloning completed: provider={result.get('provider_id')}, "
            f"filename={audio_file.filename}, duration={result.get('duration', 0):.2f}s, "
            f"cost=${result.get('cost', 0):.4f}"
        )

        return SynthesisResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in voice cloning: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/clone",
    response_model=SynthesisResponse,
    summary="Synthesize with voice cloning (base64)",
    description="""
    Synthesize speech with voice cloning using base64-encoded audio.

    Automatically deducts cost from your wallet.

    **Rate Limit:** 10 requests/minute
    **Cost:** Variable (higher for voice cloning)

    **Example Request:**
    ```json
    {
        "provider_id": "f5tts",
        "text": "This is cloned voice speech.",
        "reference_audio_base64": "UklGRiQAAABXQVZFZm10...",
        "language": "en",
        "speed": 1.0
    }
    ```
    """,
    response_description="Synthesized audio with cloned voice"
)
async def voice_clone(
    request: VoiceCloneRequest,
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(get_rate_limit_dependency("free", cost=1))
):
    """Synthesize speech with voice cloning (base64 audio)."""
    try:
        logger.info(f"Voice cloning (base64) request: provider={request.provider_id}")

        # Get user ID from API key info
        user_id = api_key.get("tenant_id")

        # Call Core Backend
        result = await call_core_backend(
            endpoint="/api/tts/clone",
            method="POST",
            json_data=request.dict(),
            user_id=user_id,
            timeout=120.0
        )

        logger.info(
            f"Voice cloning (base64) completed: provider={result.get('provider_id')}, "
            f"cost=${result.get('cost', 0):.4f}"
        )

        return SynthesisResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice cloning error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/estimate-cost",
    response_model=CostEstimateResponse,
    summary="Estimate TTS cost",
    description="""
    Estimate the cost of TTS synthesis before running.

    **Rate Limit:** 10 requests/minute
    **Cost:** Free

    **Example Request:**
    ```json
    {
        "provider_id": "coqui_xtts",
        "text": "Hello, this is a test.",
        "voice_cloning": false
    }
    ```

    **Example Response:**
    ```json
    {
        "estimated_cost": 0.00023,
        "character_count": 22,
        "provider_id": "coqui_xtts"
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
    """Estimate TTS synthesis cost before running."""
    try:
        logger.info(f"Cost estimation request: provider={request.provider_id}")

        # Get user ID from API key info
        user_id = api_key.get("tenant_id")

        # Call Core Backend
        result = await call_core_backend(
            endpoint="/api/tts/estimate-cost",
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
    summary="List TTS providers",
    description="""
    List all available TTS providers with real-time status.

    **Rate Limit:** 10 requests/minute
    **Cost:** Free

    **Query Parameters:**
    - `force_refresh`: Force health check even if cached (default: False)

    **Example Response:**
    ```json
    {
        "providers": {
            "coqui_xtts": {
                "id": "coqui_xtts",
                "name": "Coqui XTTS",
                "endpoint": "http://coqui:5000",
                "status": "online",
                "last_check": "2025-10-26T12:00:00",
                "response_time_ms": 85.3,
                "provider_type": "tts"
            }
        },
        "count": 1,
        "online_count": 1,
        "offline_count": 0
    }
    ```
    """,
    response_description="List of TTS providers with status"
)
async def list_providers(
    force_refresh: bool = Query(False, description="Force health check refresh"),
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(get_rate_limit_dependency("free", cost=1))
):
    """List all available TTS providers with health status."""
    try:
        logger.info(f"Listing TTS providers (force_refresh={force_refresh})")

        # Call Core Backend
        result = await call_core_backend(
            endpoint=f"/api/tts/providers?force_refresh={force_refresh}",
            method="GET"
        )

        return ProvidersResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing TTS providers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/providers/{provider_id}",
    response_model=ProviderHealth,
    summary="Get TTS provider status",
    description="""
    Get status of a specific TTS provider.

    **Rate Limit:** 10 requests/minute
    **Cost:** Free

    **Path Parameters:**
    - `provider_id`: Provider identifier (e.g., 'coqui_xtts', 'melotts')

    **Example Response:**
    ```json
    {
        "id": "coqui_xtts",
        "name": "Coqui XTTS",
        "endpoint": "http://coqui:5000",
        "status": "online",
        "last_check": "2025-10-26T12:00:00",
        "response_time_ms": 85.3,
        "provider_type": "tts"
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
    """Get status of a specific TTS provider."""
    try:
        logger.info(f"Getting TTS provider: {provider_id}")

        # Call Core Backend
        result = await call_core_backend(
            endpoint=f"/api/tts/providers/{provider_id}",
            method="GET"
        )

        return ProviderHealth(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting TTS provider: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/health",
    summary="Health check for TTS services",
    description="""
    Health check for TTS services route.

    **Rate Limit:** None
    **Cost:** Free

    **Example Response:**
    ```json
    {
        "status": "healthy",
        "service": "tts-services",
        "providers_count": 5,
        "billing_enabled": true,
        "health_monitoring_enabled": true
    }
    ```
    """,
    response_description="Health status"
)
async def health_check():
    """Health check for TTS services route."""
    try:
        # Call Core Backend health endpoint
        result = await call_core_backend(
            endpoint="/api/tts/health",
            method="GET"
        )

        return result

    except HTTPException:
        # If Core Backend is down, return unhealthy
        return {
            "status": "unhealthy",
            "service": "tts-services",
            "error": "Core Backend unavailable"
        }
    except Exception as e:
        logger.error(f"TTS health check error: {e}")
        return {
            "status": "unhealthy",
            "service": "tts-services",
            "error": str(e)
        }


# Export router
__all__ = ["router"]
