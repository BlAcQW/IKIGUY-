"""
Vapi Management Routes

API endpoints for managing Vapi TTS webhook integration including:
- Webhook configuration
- Testing webhooks
- Viewing statistics
- Health monitoring

Author: AI Labs Africa
Created: November 8, 2025
"""

import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Header, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field

from apps.shared.services.vapi_tts_webhook import (
    VapiTTSWebhookService,
    VapiWebhookRequest,
    get_vapi_webhook_service
)
from apps.shared.services.tts_webui_service import TTSWebUIProvider
from apps.shared.middleware.rate_limiter import RateLimitExceeded


logger = logging.getLogger(__name__)


# Create router
router = APIRouter(prefix="/vapi", tags=["Vapi Management"])


# Pydantic models for API requests/responses
class VapiConfigRequest(BaseModel):
    """Request to update Vapi configuration."""
    default_provider: Optional[str] = Field(None, description="Default TTS provider")
    fallback_provider: Optional[str] = Field(None, description="Fallback TTS provider")
    enable_rate_limiting: Optional[bool] = Field(None, description="Enable rate limiting")
    user_rpm: Optional[int] = Field(None, description="User requests per minute")
    org_rpm: Optional[int] = Field(None, description="Organization requests per minute")


class VapiTestRequest(BaseModel):
    """Request to test Vapi webhook."""
    text: str = Field(..., description="Text to synthesize", max_length=500)
    sample_rate: int = Field(24000, description="Audio sample rate (Hz)")
    provider_id: Optional[str] = Field(None, description="Specific provider to test")


class VapiWebhookTestRequest(BaseModel):
    """Full Vapi webhook test request."""
    message: Dict[str, Any] = Field(..., description="Vapi message object")
    timestamp: int = Field(..., description="Unix timestamp")
    assistant: Optional[Dict[str, Any]] = Field(None, description="Assistant metadata")
    customer: Optional[Dict[str, Any]] = Field(None, description="Customer metadata")


# Global service instance (initialized in main.py lifespan)
_vapi_service: Optional[VapiTTSWebhookService] = None


def get_vapi_service() -> VapiTTSWebhookService:
    """Get or create Vapi service instance."""
    global _vapi_service

    if _vapi_service is None:
        _vapi_service = get_vapi_webhook_service()

    return _vapi_service


@router.get("/config")
async def get_vapi_config():
    """
    Get current Vapi configuration.

    Returns:
        Current Vapi webhook configuration including providers, rate limits, and audio settings

    Example Response:
    ```json
    {
        "tts_providers": {
            "default": "styletts2",
            "fallback": "kokoro",
            "available": ["styletts2", "kokoro", "bark", ...]
        },
        "rate_limits": {
            "user": {"requests_per_minute": 30, "requests_per_hour": 500},
            "organization": {"requests_per_minute": 100, "requests_per_hour": 2000}
        },
        "audio_formats": {
            "output": "raw_pcm",
            "supported_sample_rates": [8000, 16000, 22050, 24000],
            "bit_depth": 16,
            "channels": 1
        }
    }
    ```
    """
    try:
        service = get_vapi_service()

        providers = service.tts_service.get_providers()

        return {
            "tts_providers": {
                "default": service.default_provider.value,
                "fallback": service.fallback_provider.value,
                "available": [p.value for p in providers]
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
                "enabled": bool(service.vapi_api_key),
                "method": "bearer_token"
            },
            "timeout": service.timeout
        }

    except Exception as e:
        logger.error(f"Failed to get Vapi config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def get_vapi_health():
    """
    Get Vapi service health and statistics.

    Returns:
        Service health status and usage statistics

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
            "fallback_used": 12
        },
        "config": {
            "default_provider": "styletts2",
            "fallback_provider": "kokoro",
            "rate_limiting_enabled": true
        }
    }
    ```
    """
    try:
        service = get_vapi_service()
        stats = service.get_stats()

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
                "default_provider": service.default_provider.value,
                "fallback_provider": service.fallback_provider.value,
                "rate_limiting_enabled": service.enable_rate_limiting,
                "authentication_enabled": bool(service.vapi_api_key),
                "timeout": service.timeout
            }
        }

    except Exception as e:
        logger.error(f"Failed to get Vapi health: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers")
async def get_available_providers():
    """
    Get list of available TTS providers.

    Returns:
        List of TTS providers with metadata

    Example Response:
    ```json
    {
        "providers": [
            {"id": "styletts2", "name": "StyleTTS2", "description": "Expressive voice synthesis"},
            {"id": "kokoro", "name": "Kokoro", "description": "Fast, high-quality TTS"},
            ...
        ],
        "total": 20
    }
    ```
    """
    try:
        service = get_vapi_service()
        providers = service.tts_service.get_providers()

        provider_list = [
            {
                "id": p.value,
                "name": p.value.replace("_", " ").title(),
                "description": f"{p.value.title()} TTS provider"
            }
            for p in providers
        ]

        return {
            "providers": provider_list,
            "total": len(provider_list)
        }

    except Exception as e:
        logger.error(f"Failed to get providers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test")
async def test_vapi_webhook(
    request: VapiTestRequest,
    user_id: Optional[str] = None
):
    """
    Test Vapi webhook with custom text.

    Args:
        request: Test request with text and configuration
        user_id: Optional user ID for rate limiting

    Returns:
        Audio file (raw PCM) for download

    Example:
    ```bash
    curl -X POST http://localhost:30027/api/vapi/test \
      -H "Content-Type: application/json" \
      -d '{"text": "Hello world", "sample_rate": 24000}' \
      --output test.pcm
    ```
    """
    try:
        service = get_vapi_service()

        # Create Vapi-style request
        vapi_request = VapiWebhookRequest(
            message={
                "type": "voice-request",
                "text": request.text,
                "sampleRate": request.sample_rate
            },
            timestamp=int(__import__('time').time() * 1000),
            assistant={"organizationId": f"test_{user_id or 'default'}"}
        )

        # Process webhook
        pcm_audio = await service.process_webhook_request(
            request=vapi_request,
            auth_header=None  # Skip auth for testing
        )

        # Return audio as streaming response
        return StreamingResponse(
            iter([pcm_audio]),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename=vapi_test_{request.sample_rate}hz.pcm",
                "X-Audio-Format": "pcm",
                "X-Sample-Rate": str(request.sample_rate),
                "X-Channels": "1",
                "X-Bit-Depth": "16"
            }
        )

    except RateLimitExceeded as e:
        raise HTTPException(
            status_code=429,
            detail=e.message,
            headers={"Retry-After": str(e.retry_after)}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Webhook test failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def vapi_webhook_endpoint(
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """
    Main Vapi TTS webhook endpoint.

    This is the actual webhook that Vapi will call during phone calls.

    Args:
        request: FastAPI request object
        authorization: Authorization header (Bearer token)

    Returns:
        Raw PCM audio data

    Note:
        This endpoint is called by Vapi with the following format:
        ```json
        {
            "message": {
                "type": "voice-request",
                "text": "Text to synthesize",
                "sampleRate": 24000
            },
            "timestamp": 1234567890,
            "call": {"id": "call_123"},
            "assistant": {"organizationId": "org_abc"},
            "customer": {"number": "+1234567890"}
        }
        ```
    """
    try:
        service = get_vapi_service()

        # Parse request body
        body = await request.json()
        vapi_request = VapiWebhookRequest(**body)

        # Process webhook
        pcm_audio = await service.process_webhook_request(
            request=vapi_request,
            auth_header=authorization
        )

        # Return raw PCM
        return StreamingResponse(
            iter([pcm_audio]),
            media_type="application/octet-stream",
            headers={
                "X-Audio-Format": "pcm",
                "X-Sample-Rate": str(vapi_request.message.sampleRate),
                "X-Channels": "1",
                "X-Bit-Depth": "16"
            }
        )

    except RateLimitExceeded as e:
        raise HTTPException(
            status_code=429,
            detail=e.message,
            headers={"Retry-After": str(e.retry_after)}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Vapi webhook failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stats/reset")
async def reset_stats(
    authorization: Optional[str] = Header(None)
):
    """
    Reset Vapi service statistics.

    Requires authentication.

    Returns:
        Success confirmation
    """
    try:
        service = get_vapi_service()

        # Validate authentication
        if not service.validate_authentication(authorization):
            raise HTTPException(
                status_code=401,
                detail="Invalid or missing authentication"
            )

        # Reset stats
        service.reset_stats()

        return {
            "status": "success",
            "message": "Statistics reset successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reset stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/usage")
async def get_usage_stats(user_id: Optional[str] = None, org_id: Optional[str] = None):
    """
    Get usage statistics for user or organization.

    Args:
        user_id: User identifier
        org_id: Organization identifier

    Returns:
        Usage statistics across all scopes

    Example Response:
    ```json
    {
        "user": {
            "per_minute": [25, 30],
            "per_hour": [450, 500]
        },
        "organization": {
            "per_minute": [85, 100],
            "per_hour": [1800, 2000]
        }
    }
    ```
    """
    try:
        service = get_vapi_service()

        if not service.enable_rate_limiting:
            return {
                "message": "Rate limiting is disabled",
                "usage": {}
            }

        # Get usage from rate limiter
        usage = service.rate_limiter.get_all_usage(
            user_id=user_id,
            org_id=org_id
        )

        return {
            "usage": usage,
            "user_id": user_id,
            "org_id": org_id
        }

    except Exception as e:
        logger.error(f"Failed to get usage stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
