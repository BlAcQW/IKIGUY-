"""
KasaAI Developer Platform v1 API

Clean implementation with:
- Rate limiting middleware (with Redis persistence)
- Usage tracking middleware
- v1 API routers only
- No legacy endpoints

This is a production-ready API focused on the v1 public developer interface.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import logging
import uuid
import os
import redis
from pymongo import MongoClient

try:
    from .settings import settings
except ImportError:
    # Fallback settings if settings module doesn't exist
    class Settings:
        CORS_ORIGINS = "*"
        DEBUG = False
    settings = Settings()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Redis client for rate limiter persistence
try:
    redis_url = os.getenv("DEV_REDIS_URL", "redis://inspireadmin:aawwER444444@localhost:6379/1")
    redis_client = redis.from_url(
        redis_url,
        encoding="utf-8",
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5
    )
    # Test connection
    redis_client.ping()
    logger.info(f"✅ Redis connected successfully: {redis_url.split('@')[1]}")
except Exception as e:
    logger.warning(f"⚠️  Redis connection failed: {e}")
    logger.warning("⚠️  Rate limiter will run in memory-only mode")
    redis_client = None

# Initialize MongoDB for usage tracker persistence
try:
    mongo_url = os.getenv("MONGODB_URL", "mongodb://admin:aawwER4444%25@127.0.0.1:27017/kasaai_core?authSource=admin")
    mongo_client = MongoClient(
        mongo_url,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000
    )
    # Test connection
    mongo_client.admin.command('ping')
    mongo_db = mongo_client.kasaai_dev  # Use kasaai_dev database for developer platform
    logger.info(f"✅ MongoDB connected successfully: kasaai_dev database")
except Exception as e:
    logger.warning(f"⚠️  MongoDB connection failed: {e}")
    logger.warning("⚠️  Usage tracker will run in memory-only mode")
    mongo_db = None

# Create FastAPI app
app = FastAPI(
    title="KasaAI Developer Platform v1",
    description="Public API for voice + chat automation platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(",") if hasattr(settings, 'CORS_ORIGINS') and settings.CORS_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting and usage tracking middleware
from .middleware import (
    rate_limit_middleware,
    usage_tracking_middleware,
    set_redis_client,
    set_mongo_db
)

# Enable Redis persistence for rate limiter if Redis is available
if redis_client is not None:
    set_redis_client(redis_client)

# Enable MongoDB persistence for usage tracker if MongoDB is available
if mongo_db is not None:
    set_mongo_db(mongo_db)

app.middleware("http")(usage_tracking_middleware)
app.middleware("http")(rate_limit_middleware)

logger.info("✅ Middleware registered: rate_limit_middleware, usage_tracking_middleware")


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for standardized error responses."""
    request_id = str(uuid.uuid4())

    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": "HTTP_ERROR",
                    "message": exc.detail,
                    "field": None
                },
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            },
        )

    # Handle other exceptions
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal error occurred",
                "field": None
            },
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        },
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    redis_status = "connected"
    if redis_client is not None:
        try:
            redis_client.ping()
        except:
            redis_status = "disconnected"
    else:
        redis_status = "not configured"

    mongo_status = "connected"
    if mongo_db is not None:
        try:
            mongo_db.client.admin.command('ping')
        except:
            mongo_status = "disconnected"
    else:
        mongo_status = "not configured"

    return {
        "status": "ok",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "middleware": {
            "rate_limiting": "enabled",
            "usage_tracking": "enabled"
        },
        "persistence": {
            "redis": redis_status,
            "mongodb": mongo_status,
            "rate_limiter_persistence": "enabled" if redis_client is not None else "memory-only",
            "usage_tracker_persistence": "enabled" if mongo_db is not None else "memory-only"
        }
    }


# ============================================================================
# API v1 ROUTES - Public Developer API
# ============================================================================

# Import v1 routers
try:
    from .api.v1.vapi import router as vapi_router, calls_router as vapi_calls_router
    from .api.v1.n8n import router as n8n_router, executions_router as n8n_executions_router
    from .api.v1.usage import router as usage_router

    # Register v1 routers (routers already have /api/v1 prefix in their definition)
    app.include_router(
        vapi_router,
        tags=["Voice Assistants (v1)"]
    )
    app.include_router(
        vapi_calls_router,
        tags=["Voice Calls (v1)"]
    )
    app.include_router(
        n8n_router,
        tags=["Workflows (v1)"]
    )
    app.include_router(
        n8n_executions_router,
        tags=["Workflow Executions (v1)"]
    )
    app.include_router(
        usage_router,
        tags=["Usage & Analytics (v1)"]
    )

    logger.info("✅ v1 API routers registered successfully")

except ImportError as e:
    logger.error(f"❌ Failed to import v1 routers: {e}")
    logger.warning("⚠️  Server will start but v1 endpoints won't be available")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "KasaAI Developer Platform",
        "version": "1.0.0",
        "description": "Public API for voice + chat automation",
        "docs": "/docs",
        "health": "/health",
        "api_v1": {
            "assistants": "/api/v1/assistants",
            "calls": "/api/v1/calls",
            "workflows": "/api/v1/workflows",
            "executions": "/api/v1/executions",
            "usage": "/api/v1/usage"
        }
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Log startup information."""
    logger.info("=" * 60)
    logger.info("🚀 KasaAI Developer Platform v1 API Starting...")
    logger.info("=" * 60)
    logger.info(f"Version: 1.0.0")
    logger.info(f"Docs: /docs")
    logger.info(f"Health: /health")
    logger.info("Middleware: Rate Limiting + Usage Tracking")
    logger.info("=" * 60)


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Log shutdown information."""
    logger.info("🛑 KasaAI Developer Platform v1 API Shutting Down...")
