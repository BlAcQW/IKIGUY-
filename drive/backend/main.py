"""
KasaAI Drive - Google Drive-like file management system.

Main FastAPI application entry point.

Author: AI Labs Africa
Date: 2025-11-10
"""

import sys
from pathlib import Path

# Add parent directories to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from apps.shared.unified_logging import get_logger, set_environment, CorrelationIdMiddleware
from apps.drive.backend.app.core.config import settings
from apps.drive.backend.app.core.database import init_db, close_db
from apps.drive.backend.app.api.routes import files, folders, search, share

# Configure unified logging
set_environment(production=not settings.DEBUG)
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="KasaAI Drive API",
    description="Google Drive-like file management system for organizations",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Correlation ID middleware (must be first to track entire request)
app.add_middleware(CorrelationIdMiddleware)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://drive.ailabsafrica.com",
        "https://dev-drive.ailabsafrica.com",
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3005"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(files.router, prefix="/api/files", tags=["Files"])
app.include_router(folders.router, prefix="/api/folders", tags=["Folders"])
app.include_router(search.router, prefix="/api/search", tags=["Search"])
app.include_router(share.router, prefix="/api/share", tags=["Sharing"])


@app.on_event("startup")
async def startup_event():
    """Initialize database and services on startup."""
    logger.info("Starting KasaAI Drive API",
                version="1.0.0",
                debug_mode=settings.DEBUG,
                port=settings.PORT)

    # Set environment variables for shared modules
    import os
    os.environ["SUPABASE_URL"] = settings.SUPABASE_URL
    os.environ["SUPABASE_ANON_KEY"] = settings.SUPABASE_ANON_KEY
    os.environ["HETZNER_STORAGE_USERNAME"] = settings.HETZNER_STORAGE_USERNAME
    os.environ["HETZNER_STORAGE_PASSWORD"] = settings.HETZNER_STORAGE_PASSWORD
    os.environ["HETZNER_STORAGE_HOST"] = settings.HETZNER_STORAGE_HOST
    os.environ["HETZNER_STORAGE_PROTOCOL"] = settings.HETZNER_STORAGE_PROTOCOL

    logger.info("Configured external services",
                supabase_url=settings.SUPABASE_URL,
                storage_host=settings.HETZNER_STORAGE_HOST,
                storage_protocol=settings.HETZNER_STORAGE_PROTOCOL)

    await init_db()
    logger.info("KasaAI Drive API started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    logger.info("Shutting down KasaAI Drive API...")
    await close_db()
    logger.info("KasaAI Drive API shut down successfully")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "KasaAI Drive API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "kasaai-drive",
        "version": "1.0.0"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.exception("Unhandled exception",
                     path=request.url.path,
                     method=request.method,
                     error_type=type(exc).__name__)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc)
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
