"""
StudyFlow (EduMate) - Personal AI Tutoring Backend.

Mobile-first AI-powered tutoring platform with RAG-based learning.
"""

import logging
import sys
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from app.config import settings
from app.core.database import connect_databases, disconnect_databases, MongoDB
from app.core.auth import initialize_auth
from app.api import api_router
from apps.shared.middleware import OrganizationContextMiddleware
from apps.shared.services.organization_service import get_organization_service
from apps.shared.services.billing_service import get_billing_service
from apps.shared.routes.billing_routes import create_billing_router
from apps.shared.routes.tts_routes import router as tts_router
from apps.shared.routes.voice_library_routes import create_voice_library_router
from apps.shared.routes.provider_routes import router as provider_router
from apps.shared.routes.asr_routes import router as asr_router
from apps.shared.routes.llm_routes import router as llm_router
from apps.shared.routes.voice_settings_routes import create_voice_settings_router
from apps.shared.startup import initialize_default_organization
from app.core.auth import get_current_user

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting StudyFlow backend...")
    try:
        await connect_databases()
        initialize_auth()

        # Initialize organization service
        db = MongoDB.get_database()
        org_service = get_organization_service(db)
        await org_service.initialize_indexes()
        logger.info("✅ Organization service initialized")

        # Initialize default organization
        await initialize_default_organization()

        # Initialize billing service
        billing_service = get_billing_service(db)
        await billing_service.initialize_indexes()
        logger.info("✅ Billing service initialized")

        # Initialize storage file serving routes (using shared service from @shared)
        try:
            from app.api.routes.storage import create_studyflow_storage_router
            storage_router = await create_studyflow_storage_router()
            app.include_router(storage_router)
            logger.info("✅ Storage file serving routes initialized (using @shared service)")
        except Exception as e:
            logger.warning(f"⚠️  Storage routes initialization error: {e}")

        logger.info("✓ StudyFlow backend started successfully")
    except Exception as e:
        logger.error(f"✗ Startup failed: {str(e)}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down StudyFlow backend...")
    await disconnect_databases()
    logger.info("✓ StudyFlow backend stopped")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Personal AI Tutoring Platform",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS configuration
# DISABLED: nginx handles CORS headers to avoid duplicate Access-Control-Allow-Origin headers
# Duplicate headers cause browser to reject with "CORS header does not match origin"
# See: /etc/nginx/sites-available/studyflow-api.ailabsafrica.com.conf
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=settings.cors_origins_list,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# Add Organization Context Middleware
app.add_middleware(OrganizationContextMiddleware)

# Include API routes
app.include_router(api_router, prefix=settings.API_V1_STR)

# Include unified TTS routes
app.include_router(tts_router, prefix="/api/tts", tags=["TTS"])

# Include unified provider discovery routes (TTS, ASR, LLM)
app.include_router(provider_router, prefix="/api/v1", tags=["Providers"])

# Include unified ASR routes
app.include_router(asr_router, prefix="/api/asr", tags=["ASR"])

# Include ASR WebSocket routes (mounted at /ws/asr for frontend compatibility)
from apps.shared.routes.asr_routes import ws_router as asr_ws_router
app.include_router(asr_ws_router, prefix="/ws/asr", tags=["ASR WebSocket"])

# Include unified LLM routes
app.include_router(llm_router, prefix="/api/llm", tags=["LLM"])

# Include unified voice settings routes
voice_settings_router = create_voice_settings_router(
    get_current_user_func=get_current_user,
    get_database_func=lambda: MongoDB.get_database()
)
app.include_router(voice_settings_router, prefix="/api/voice-settings", tags=["Voice Settings"])

# Include voice library routes (shared across apps, uses shared MongoDB)
voice_library_router = create_voice_library_router(
    get_current_user_func=get_current_user,
    get_database_func=lambda: MongoDB.get_database()
)
app.include_router(voice_library_router, prefix="/api/voice-library", tags=["Voice Library"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "app": "StudyFlow",
        "tagline": "Your personal tutor that listens, explains, and helps you learn smarter.",
        "version": "0.1.0",
        "status": "active",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "studyflow-backend",
        "version": "0.1.0",
    }


@app.get("/api/v1/subjects")
async def list_subjects():
    """List available subjects."""
    return {
        "subjects": [],
        "total": 0,
        "message": "Subject listing functionality coming soon",
    }
