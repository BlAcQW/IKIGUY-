"""
Vapi TTS Service - Production Implementation

A production-ready microservice that provides custom TTS for Vapi voice assistants
using KasaAI's TTS-WebUI infrastructure with 20+ TTS models.

Features:
- Vapi webhook endpoints for custom TTS
- Real-time PCM audio conversion
- Rate limiting per user/organization
- Health monitoring and statistics
- Authentication via API key
- Fallback provider support

Author: AI Labs Africa
Created: November 8, 2025
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from apps.shared.routers import vapi_webhook_router
from apps.shared.services.vapi_tts_webhook import (
    VapiTTSWebhookService,
    _vapi_webhook_service
)
from apps.shared.services.tts_webui_service import TTSWebUIProvider


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle.

    Initialize services on startup, cleanup on shutdown.
    """
    global _vapi_webhook_service

    # Startup
    logger.info("=" * 80)
    logger.info("Starting Vapi TTS Service")
    logger.info("=" * 80)

    try:
        # Initialize Vapi webhook service
        logger.info("Initializing Vapi TTS webhook service...")

        # Use the global singleton from shared services
        from apps.shared.services import vapi_tts_webhook
        vapi_tts_webhook._vapi_webhook_service = VapiTTSWebhookService(
            default_provider=TTSWebUIProvider.STYLETTS2,  # Expressive, natural
            fallback_provider=TTSWebUIProvider.KOKORO,    # Fast, reliable
            enable_rate_limiting=True,
            org_rpm=int(os.getenv("VAPI_ORG_RPM", "100")),
            user_rpm=int(os.getenv("VAPI_USER_RPM", "30")),
            timeout=int(os.getenv("VAPI_TIMEOUT", "30"))
        )

        vapi_service = vapi_tts_webhook._vapi_webhook_service

        logger.info(f"✓ Default provider: {vapi_service.default_provider.value}")
        logger.info(f"✓ Fallback provider: {vapi_service.fallback_provider.value}")
        logger.info(f"✓ Rate limiting: {vapi_service.enable_rate_limiting}")
        logger.info(f"✓ Authentication: {'Enabled' if vapi_service.vapi_api_key else 'Disabled'}")

        # Get TTS-WebUI service info
        tts_service = vapi_service.tts_service
        providers = tts_service.get_providers()
        logger.info(f"✓ Available TTS providers: {len(providers)}")

        logger.info("=" * 80)
        logger.info("Vapi TTS Service ready!")
        logger.info(f"Webhook endpoint: POST /api/vapi/tts-webhook")
        logger.info(f"Health check: GET /api/vapi/health")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"Failed to initialize Vapi service: {e}", exc_info=True)
        raise

    yield  # Application runs

    # Shutdown
    logger.info("=" * 80)
    logger.info("Shutting down Vapi TTS Service")
    logger.info("=" * 80)

    try:
        # Print final statistics
        from apps.shared.services import vapi_tts_webhook
        vapi_service = vapi_tts_webhook._vapi_webhook_service

        if vapi_service:
            stats = vapi_service.get_stats()
            logger.info(f"Final statistics:")
            logger.info(f"  Total requests: {stats['total_requests']}")
            logger.info(f"  Successful: {stats['successful_requests']}")
            logger.info(f"  Failed: {stats['failed_requests']}")
            logger.info(f"  Success rate: {stats['success_rate']:.1%}")
            logger.info(f"  Fallback usage: {stats['fallback_used']}")

        # Close TTS-WebUI client
        if vapi_service and vapi_service.tts_service:
            await vapi_service.tts_service.close()
            logger.info("✓ Closed TTS-WebUI client")

        logger.info("=" * 80)
        logger.info("Shutdown complete")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)


# Create FastAPI app
app = FastAPI(
    title="Vapi TTS Service",
    description=(
        "Custom TTS webhook service for Vapi voice assistants using "
        "KasaAI's TTS-WebUI infrastructure with 20+ TTS models"
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://vapi.ai",
        "https://*.vapi.ai",
        "http://localhost:*",
        "http://127.0.0.1:*",
        "*"  # Allow all for Vapi webhooks
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include Vapi webhook router
app.include_router(
    vapi_webhook_router,
    prefix="/api/vapi",
    tags=["vapi"]
)


# Root endpoint
@app.get("/", tags=["info"])
async def root():
    """
    Service information endpoint.

    Returns basic information about the Vapi TTS service.
    """
    return {
        "service": "Vapi TTS Service",
        "version": "1.0.0",
        "description": "Custom TTS webhook for Vapi voice assistants",
        "endpoints": {
            "webhook": "POST /api/vapi/tts-webhook",
            "health": "GET /api/vapi/health",
            "config": "GET /api/vapi/config",
            "docs": "GET /docs"
        },
        "features": [
            "20+ TTS models via TTS-WebUI",
            "Real-time PCM audio conversion",
            "Rate limiting per user/organization",
            "Automatic fallback providers",
            "Health monitoring and statistics"
        ]
    }


# Health check endpoint (global)
@app.get("/health", tags=["monitoring"])
async def health_check():
    """
    Global health check endpoint.

    Checks if the service and all dependencies are healthy.
    """
    try:
        # Get Vapi service from singleton
        from apps.shared.services import vapi_tts_webhook
        vapi_service = vapi_tts_webhook._vapi_webhook_service

        # Check Vapi service
        if vapi_service is None:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "error": "Vapi service not initialized"
                }
            )

        # Get Vapi service stats
        stats = vapi_service.get_stats()

        # Check TTS-WebUI service
        tts_health = await vapi_service.tts_service.health_check()

        # Determine overall health
        if tts_health["status"] == "healthy" and stats["success_rate"] >= 0.95:
            status = "healthy"
        elif tts_health["status"] == "degraded" or stats["success_rate"] >= 0.80:
            status = "degraded"
        else:
            status = "unhealthy"

        return {
            "status": status,
            "service": "vapi-tts-service",
            "components": {
                "vapi_webhook": {
                    "status": "healthy" if stats["success_rate"] >= 0.95 else "degraded",
                    "success_rate": stats["success_rate"],
                    "total_requests": stats["total_requests"]
                },
                "tts_webui": tts_health
            },
            "uptime_stats": stats
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


# Metrics endpoint
@app.get("/metrics", tags=["monitoring"])
async def metrics():
    """
    Prometheus-compatible metrics endpoint.

    Returns metrics in Prometheus text format.
    """
    # Get Vapi service from singleton
    from apps.shared.services import vapi_tts_webhook
    vapi_service = vapi_tts_webhook._vapi_webhook_service

    if vapi_service is None:
        return JSONResponse(
            status_code=503,
            content={"error": "Service not initialized"}
        )

    stats = vapi_service.get_stats()

    # Generate Prometheus metrics
    metrics_text = f"""# HELP vapi_tts_requests_total Total number of Vapi TTS requests
# TYPE vapi_tts_requests_total counter
vapi_tts_requests_total {stats['total_requests']}

# HELP vapi_tts_requests_successful Total number of successful requests
# TYPE vapi_tts_requests_successful counter
vapi_tts_requests_successful {stats['successful_requests']}

# HELP vapi_tts_requests_failed Total number of failed requests
# TYPE vapi_tts_requests_failed counter
vapi_tts_requests_failed {stats['failed_requests']}

# HELP vapi_tts_success_rate Success rate (0.0 to 1.0)
# TYPE vapi_tts_success_rate gauge
vapi_tts_success_rate {stats['success_rate']}

# HELP vapi_tts_fallback_used Number of times fallback provider was used
# TYPE vapi_tts_fallback_used counter
vapi_tts_fallback_used {stats['fallback_used']}

# HELP vapi_tts_fallback_rate Fallback usage rate (0.0 to 1.0)
# TYPE vapi_tts_fallback_rate gauge
vapi_tts_fallback_rate {stats['fallback_rate']}
"""

    return JSONResponse(
        content={"metrics": metrics_text},
        media_type="text/plain"
    )


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle unexpected errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn

    # Run with uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "30036")),
        reload=True,
        log_level="info"
    )
