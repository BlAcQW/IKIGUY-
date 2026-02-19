"""
FastAPI Router for Vapi TTS Webhook

Provides ready-to-use FastAPI routes for Vapi custom TTS integration.
Import this router into any FastAPI app to add Vapi webhook support.

Usage:
    from apps.shared.routers.vapi_webhook_router import router as vapi_router

    app = FastAPI()
    app.include_router(vapi_router, prefix="/api/vapi", tags=["vapi"])

Author: AI Labs Africa
Created: November 8, 2025
"""

import logging
from typing import Optional

from fastapi import APIRouter, Request, Response, HTTPException, Header, Depends
from fastapi.responses import Response as FastAPIResponse

from ..services.vapi_tts_webhook import (
    VapiTTSWebhookService,
    VapiWebhookRequest,
    get_vapi_webhook_service
)
from ..middleware.rate_limiter import RateLimitExceeded


logger = logging.getLogger(__name__)


# Create router
router = APIRouter()


# Dependency function for service injection
def get_vapi_service() -> VapiTTSWebhookService:
    """
    Dependency function to get Vapi webhook service instance.

    Returns:
        VapiTTSWebhookService instance
    """
    return get_vapi_webhook_service()


@router.post("/tts-webhook")
async def vapi_tts_webhook(
    request: VapiWebhookRequest,
    authorization: Optional[str] = Header(None),
    vapi_service: VapiTTSWebhookService = Depends(get_vapi_service)
) -> FastAPIResponse:
    """
    Vapi TTS webhook endpoint.

    Receives text from Vapi and returns raw PCM audio in real-time.

    **Request Format:**
    ```json
    {
        "message": {
            "type": "voice-request",
            "text": "Hello, welcome to KasaAI!",
            "sampleRate": 24000
        },
        "timestamp": 1234567890,
        "call": {"id": "call_123"},
        "assistant": {"organizationId": "org_abc"},
        "customer": {"number": "+1234567890"}
    }
    ```

    **Response:**
    - Content-Type: application/octet-stream
    - Body: Raw PCM audio data (16-bit, mono, little-endian)

    **Authentication:**
    - Header: Authorization: Bearer <VAPI_API_KEY>

    **Rate Limits:**
    - Per User: 30 req/min, 500 req/hour
    - Per Organization: 100 req/min, 2000 req/hour

    Args:
        request: Vapi webhook request
        authorization: Authorization header (Bearer token)
        vapi_service: Vapi webhook service (injected)

    Returns:
        Raw PCM audio data with application/octet-stream content type

    Raises:
        HTTPException: 400 for invalid request, 401 for auth failure,
                      429 for rate limit, 500 for synthesis failure
    """
    try:
        # Process webhook request
        pcm_audio = await vapi_service.process_webhook_request(
            request=request,
            auth_header=authorization
        )

        # Return raw PCM audio
        return FastAPIResponse(
            content=pcm_audio,
            media_type="application/octet-stream",
            headers={
                "X-Audio-Format": "pcm",
                "X-Sample-Rate": str(request.message.sampleRate),
                "X-Channels": "1",
                "X-Bit-Depth": "16"
            }
        )

    except ValueError as e:
        logger.warning(f"Invalid Vapi webhook request: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except RateLimitExceeded as e:
        logger.warning(f"Rate limit exceeded: {e}")
        raise HTTPException(
            status_code=429,
            detail=e.message,
            headers={"Retry-After": str(e.retry_after)}
        )

    except Exception as e:
        logger.error(f"Vapi webhook request failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"TTS synthesis failed: {str(e)}"
        )


@router.get("/health")
async def vapi_health_check(
    vapi_service: VapiTTSWebhookService = Depends(get_vapi_service)
) -> dict:
    """
    Health check endpoint for Vapi webhook service.

    Returns service status and statistics.

    Returns:
        Service health information including:
        - status: Service status (healthy/degraded)
        - stats: Request statistics
        - config: Service configuration

    Example Response:
    ```json
    {
        "status": "healthy",
        "service": "vapi-tts-webhook",
        "stats": {
            "total_requests": 1234,
            "successful_requests": 1200,
            "failed_requests": 34,
            "success_rate": 0.972,
            "fallback_used": 12,
            "fallback_rate": 0.01
        },
        "config": {
            "default_provider": "styletts2",
            "fallback_provider": "kokoro",
            "rate_limiting_enabled": true,
            "authentication_enabled": true
        }
    }
    ```
    """
    try:
        stats = vapi_service.get_stats()

        # Determine health status
        success_rate = stats.get("success_rate", 0.0)
        if success_rate >= 0.95:
            status = "healthy"
        elif success_rate >= 0.80:
            status = "degraded"
        else:
            status = "unhealthy"

        return {
            "status": status,
            "service": "vapi-tts-webhook",
            "stats": stats,
            "config": {
                "default_provider": vapi_service.default_provider.value,
                "fallback_provider": vapi_service.fallback_provider.value,
                "rate_limiting_enabled": vapi_service.enable_rate_limiting,
                "authentication_enabled": bool(vapi_service.vapi_api_key),
                "timeout": vapi_service.timeout
            }
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.post("/stats/reset")
async def reset_stats(
    authorization: Optional[str] = Header(None),
    vapi_service: VapiTTSWebhookService = Depends(get_vapi_service)
) -> dict:
    """
    Reset service statistics.

    Requires authentication.

    Args:
        authorization: Authorization header (Bearer token)
        vapi_service: Vapi webhook service (injected)

    Returns:
        Confirmation message

    Raises:
        HTTPException: 401 for auth failure
    """
    # Validate authentication
    if not vapi_service.validate_authentication(authorization):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing authentication"
        )

    vapi_service.reset_stats()

    return {
        "status": "success",
        "message": "Statistics reset successfully"
    }


@router.get("/config")
async def get_config(
    vapi_service: VapiTTSWebhookService = Depends(get_vapi_service)
) -> dict:
    """
    Get service configuration.

    Returns current service configuration including providers,
    rate limits, and authentication status.

    Returns:
        Service configuration

    Example Response:
    ```json
    {
        "tts_providers": {
            "default": "styletts2",
            "fallback": "kokoro",
            "available": [
                "styletts2", "kokoro", "chatterbox", "bark",
                "tortoise", "maha_tts", "mms", "vall_e_x", ...
            ]
        },
        "rate_limits": {
            "user": {
                "requests_per_minute": 30,
                "requests_per_hour": 500
            },
            "organization": {
                "requests_per_minute": 100,
                "requests_per_hour": 2000
            }
        },
        "audio_formats": {
            "output": "raw_pcm",
            "supported_sample_rates": [8000, 16000, 22050, 24000],
            "bit_depth": 16,
            "channels": 1
        },
        "authentication": {
            "enabled": true,
            "method": "bearer_token"
        }
    }
    ```
    """
    return {
        "tts_providers": {
            "default": vapi_service.default_provider.value,
            "fallback": vapi_service.fallback_provider.value,
            "available": [provider.value for provider in vapi_service.tts_service.get_providers()]
        },
        "rate_limits": {
            "user": {
                "requests_per_minute": 30,
                "requests_per_hour": 500
            },
            "organization": {
                "requests_per_minute": 100,
                "requests_per_hour": 2000
            }
        },
        "audio_formats": {
            "output": "raw_pcm",
            "supported_sample_rates": [8000, 16000, 22050, 24000],
            "bit_depth": 16,
            "channels": 1,
            "byte_order": "little_endian"
        },
        "authentication": {
            "enabled": bool(vapi_service.vapi_api_key),
            "method": "bearer_token"
        },
        "timeout": vapi_service.timeout
    }
