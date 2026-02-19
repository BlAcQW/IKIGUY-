"""
EventFlow - AI Event Management Backend.

Automated event planning with voice AI and intelligent workflows.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sys
import os

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from .core.config import settings
from .core.database import connect_to_mongodb, close_mongodb_connection, get_database
from .api.v1 import api_router
from apps.shared.middleware import OrganizationContextMiddleware
from apps.shared.services.organization_service import get_organization_service
from apps.shared.startup import initialize_default_organization
from apps.shared.routes.tts_routes import router as shared_tts_router
from apps.shared.routes.voice_library_routes import create_voice_library_router
from .api.dependencies import get_current_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("🚀 Starting EventFlow Backend...")
    await connect_to_mongodb()

    # Initialize organization service
    db = get_database()
    org_service = get_organization_service(db)
    await org_service.initialize_indexes()
    print("✅ Organization service initialized")

    # Initialize default organization
    await initialize_default_organization()

    yield
    # Shutdown
    print("👋 Shutting down EventFlow Backend...")
    await close_mongodb_connection()


app = FastAPI(
    title="EventFlow API",
    description="AI-powered Event Management Platform",
    version=settings.app_version,
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Organization Context Middleware
app.add_middleware(OrganizationContextMiddleware)

# Include API v1 router
app.include_router(api_router, prefix=settings.api_v1_prefix)

# Add shared TTS router at /api/tts for synthesis and providers
# (shared frontend components expect /api/tts/synthesize, /api/tts/providers)
app.include_router(shared_tts_router, prefix="/api/tts", tags=["TTS"])

# Add EventFlow-specific TTS router for task reminders and summaries
from .api.v1.tts import router as eventflow_tts_router
app.include_router(eventflow_tts_router, prefix="/api", tags=["EventFlow TTS"])

# Include voice library routes (shared across apps, uses shared MongoDB)
voice_library_router = create_voice_library_router(
    get_current_user_func=get_current_user,
    get_database_func=get_database
)
app.include_router(voice_library_router, prefix="/api/voice-library", tags=["Voice Library"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "app": settings.app_name,
        "tagline": "Plan less. Celebrate more.",
        "version": settings.app_version,
        "status": "active",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "eventflow-backend",
        "version": settings.app_version,
    }
