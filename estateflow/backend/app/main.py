"""
EstateFlow - Real Estate Property Management SaaS Backend.

Modern property management platform with AI agents, multi-currency support,
and integrated communication campaigns.
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
from app.core.scheduler import get_scheduler
from app.core.middleware import RateLimitMiddleware
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

# Global scheduler instance
scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    global scheduler

    # Startup
    logger.info("Starting EstateFlow backend...")
    try:
        # Initialize database connections
        await connect_databases()
        logger.info("Database connections established")

        # Initialize authentication
        await initialize_auth()
        logger.info("Authentication initialized")

        # Initialize shared services after database connection
        initialize_shared_services()
        logger.info("Shared services initialized")

        # Initialize default organization (must be after shared services)
        await initialize_default_organization()
        logger.info("Default organization initialized")

        # Start background scheduler for reminders
        db = MongoDB.get_db()
        scheduler = get_scheduler(db)
        scheduler.start()
        logger.info("Background scheduler started")

        logger.info("✓ EstateFlow backend started successfully")
        yield

    except Exception as e:
        logger.error(f"Error during startup: {str(e)}", exc_info=True)
        raise
    finally:
        # Shutdown
        logger.info("Shutting down EstateFlow backend...")

        # Stop scheduler
        if scheduler:
            scheduler.shutdown()
            logger.info("Background scheduler stopped")

        await disconnect_databases()
        logger.info("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title="EstateFlow API",
    description="Real Estate Property Management SaaS Platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://estateflow.ailabsafrica.com",
        "https://dev-estateflow.ailabsafrica.com",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Add organization context middleware
app.add_middleware(OrganizationContextMiddleware)

# Add rate limiting middleware for anonymous bookings
app.add_middleware(RateLimitMiddleware, limit=3, window_hours=1)

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        dict: Health status
    """
    return {
        "status": "healthy",
        "service": "estateflow",
        "version": "1.0.0"
    }


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint with API information.

    Returns:
        dict: API information
    """
    return {
        "name": "EstateFlow API",
        "version": "1.0.0",
        "description": "Real Estate Property Management SaaS Platform",
        "docs": "/docs",
        "redoc": "/redoc"
    }


# Include routers
app.include_router(api_router, prefix="/api/v1")

# Function to initialize shared services after database connection
def initialize_shared_services():
    """Initialize shared services with database connection."""
    from apps.shared.services.organization_service import get_organization_service
    from apps.shared.services.billing_service import get_billing_service as get_billing_service_shared

    # Get database instance
    db = MongoDB.get_db()

    # Initialize services with database
    org_service = get_organization_service(db)
    billing_service_instance = get_billing_service_shared(db)

    # Create dependency functions
    def get_billing_service_func():
        return billing_service_instance

    # Include shared service routers
    app.include_router(
        create_billing_router(get_current_user, get_billing_service_func),
        prefix="/api/v1",
        tags=["billing"]
    )

    app.include_router(
        create_voice_library_router(
            get_current_user_func=get_current_user,
            get_database_func=lambda: db
        ),
        prefix="/api/v1/voice-library",
        tags=["voice-library"]
    )

    app.include_router(
        create_voice_settings_router(
            get_current_user_func=get_current_user,
            get_database_func=lambda: db
        ),
        prefix="/api/v1/voice-settings",
        tags=["voice-settings"]
    )

# Include routers that don't require database initialization

app.include_router(
    tts_router,
    prefix="/api/v1",
    tags=["tts"]
)

app.include_router(
    provider_router,
    prefix="/api/v1",
    tags=["providers"]
)

app.include_router(
    asr_router,
    prefix="/api/v1",
    tags=["asr"]
)

app.include_router(
    llm_router,
    prefix="/api/v1",
    tags=["llm"]
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=30039,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )
