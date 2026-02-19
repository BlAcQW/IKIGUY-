"""
EstateFlow - Real Estate Property Management Backend.

Standalone local application - no external SaaS dependencies.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.config import settings
from app.core.database import connect_databases, disconnect_databases, MongoDB
from app.core.auth import ensure_default_admin
from app.core.scheduler import get_scheduler
from app.api import api_router
from app.api.auth.router import router as auth_router

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

        # Get database instance
        db = MongoDB.get_db()
        
        # Create default admin user if not exists
        await ensure_default_admin(db)
        logger.info("Default admin user ensured")

        # Create storage directory if not exists
        storage_path = Path(settings.UPLOAD_DIR)
        storage_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Storage directory: {storage_path}")

        # Start background scheduler for reminders
        try:
            scheduler = get_scheduler(db)
            scheduler.start()
            logger.info("Background scheduler started")
        except Exception as e:
            logger.warning(f"Scheduler not started: {e}")

        logger.info("=" * 50)
        logger.info("✓ EstateFlow backend started successfully!")
        logger.info(f"  API URL: http://localhost:{settings.PORT}")
        logger.info(f"  Docs: http://localhost:{settings.PORT}/docs")
        logger.info(f"  Admin: {settings.DEFAULT_ADMIN_EMAIL}")
        logger.info("=" * 50)
        
        yield

    except Exception as e:
        logger.error(f"Error during startup: {str(e)}", exc_info=True)
        raise
    finally:
        # Shutdown
        logger.info("Shutting down EstateFlow backend...")

        # Stop scheduler
        if scheduler:
            try:
                scheduler.shutdown()
                logger.info("Background scheduler stopped")
            except Exception as e:
                logger.warning(f"Error stopping scheduler: {e}")

        await disconnect_databases()
        logger.info("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title="EstateFlow API",
    description="Real Estate Property Management Platform - Standalone Edition",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS Configuration - Allow localhost origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS + ["*"],  # Allow all for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)


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
        "description": "Real Estate Property Management Platform",
        "docs": "/docs",
        "redoc": "/redoc",
        "default_admin": settings.DEFAULT_ADMIN_EMAIL
    }


# Include auth router (login, signup, etc.)
app.include_router(auth_router, prefix="/api/v1", tags=["Authentication"])

# Include API router (properties, bookings, etc.)
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )
