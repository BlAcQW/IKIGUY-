"""
DevotionalFlow Backend API - Main Application Entry Point.

This is the FastAPI application that serves the DevotionalFlow backend API.
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.config import settings
from app.db.mongodb import connect_to_mongo, close_mongo_connection
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Holy Spirit Inspired Mobile-First Devotional Platform",
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to catch all unhandled exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": f"Internal server error: {str(exc)}",
            "type": type(exc).__name__,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed messages."""
    logger.error(f"Validation error: {exc.errors()}")

    # Don't include body for multipart/form-data requests (file uploads)
    # as FormData objects are not JSON serializable
    body = exc.body
    if isinstance(body, (bytes, str)):
        try:
            # Try to include body for debugging, but skip if not serializable
            import json
            json.dumps(body)  # Test if serializable
        except (TypeError, ValueError):
            body = None
    else:
        # For FormData and other non-serializable types
        body = None

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )

# CORS middleware - DISABLED: nginx handles CORS to avoid duplicate headers
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=settings.CORS_ORIGINS,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


@app.on_event("startup")
async def startup_event():
    """Application startup: Connect to MongoDB and initialize services."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")
    await connect_to_mongo()
    
    # Initialize scheduler for drip feed
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.cron import CronTrigger
        from app.services.drip_feed_service import get_drip_feed_service
        from app.services.settings_service import SettingsService
        
        scheduler = AsyncIOScheduler()
        settings_service = SettingsService()
        
        async def send_daily_drip_feed():
            """Send daily devotional to all subscribers."""
            try:
                # Check if drip feed is enabled
                settings = await settings_service.get_settings()
                if not settings.notifications.enable_subscription_drip_feed:
                    logger.info("Subscription drip feed is disabled in settings")
                    return
                
                service = get_drip_feed_service()
                result = await service.send_daily_devotional_to_subscribers()
                logger.info(f"Daily drip feed completed: {result}")
            except Exception as e:
                logger.error(f"Error in daily drip feed: {e}", exc_info=True)
        
        async def schedule_drip_feed():
            """Schedule drip feed based on platform settings."""
            try:
                settings = await settings_service.get_settings()
                
                if not settings.notifications.enable_subscription_drip_feed:
                    logger.info("Subscription drip feed is disabled")
                    return
                
                # Parse time from settings (format: HH:MM)
                drip_feed_time = settings.notifications.subscription_drip_feed_time
                hour, minute = map(int, drip_feed_time.split(":"))
                
                # Remove existing job if it exists
                try:
                    scheduler.remove_job('daily_drip_feed')
                except:
                    pass
                
                # Add new job with configured time
                scheduler.add_job(
                    send_daily_drip_feed,
                    CronTrigger(hour=hour, minute=minute),  # Use time from settings
                    id='daily_drip_feed',
                    name='Daily Drip Feed to Subscribers',
                    replace_existing=True
                )
                
                logger.info(f"✅ Drip feed scheduled for {drip_feed_time} UTC")
            except Exception as e:
                logger.error(f"Failed to schedule drip feed: {e}", exc_info=True)
        
        # Schedule initial drip feed
        await schedule_drip_feed()
        
        scheduler.start()
        logger.info("✅ Drip feed scheduler started")
    except ImportError:
        logger.warning("APScheduler not installed - drip feed scheduler disabled. Install with: pip install apscheduler")
    except Exception as e:
        logger.error(f"Failed to start drip feed scheduler: {e}", exc_info=True)
    
    logger.info("Application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown: Close database connections."""
    logger.info("Shutting down application")
    await close_mongo_connection()
    logger.info("Application shutdown complete")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint - API status."""
    return {
        "message": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "ok",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "database": "connected",
    }


# Import and include routers
from app.routes import auth, devotionals, ai, comments, engagement, admin, author, platform_settings, moderation, calendar, devotional_daily, gamification, media, groups, invites, notifications, series, analytics, push_notifications, discussions, user_management, subscriptions
from fastapi.staticfiles import StaticFiles
import os

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
# Register daily routes BEFORE devotionals to avoid /{devotional_id} catch-all conflict
app.include_router(devotional_daily.router, prefix="/api/v1/devotionals", tags=["Daily Devotionals"])
app.include_router(devotionals.router, prefix="/api/v1/devotionals", tags=["Devotionals"])
app.include_router(ai.router, prefix="/api/v1/ai", tags=["AI"])
app.include_router(comments.router, prefix="/api/v1", tags=["Comments"])
app.include_router(engagement.router, prefix="/api/v1", tags=["Engagement"])
app.include_router(gamification.router, prefix="/api/v1/gamification", tags=["Gamification"])
app.include_router(admin.router, prefix="/api/v1", tags=["Admin"])
app.include_router(author.router, prefix="/api/v1", tags=["Author"])
app.include_router(platform_settings.router, prefix="/api/v1/admin", tags=["Platform Settings"])
app.include_router(moderation.router, prefix="/api/v1", tags=["Moderation"])
app.include_router(calendar.router, prefix="/api/v1", tags=["Calendar"])
app.include_router(media.router, prefix="/api/v1/media", tags=["Media"])
app.include_router(groups.router, prefix="/api/v1/groups", tags=["Bible Study Groups"])
app.include_router(invites.router, prefix="/api/v1", tags=["Group Invites"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["Notifications"])
app.include_router(series.router, prefix="/api/v1/series", tags=["Series"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(push_notifications.router, prefix="/api/v1/push", tags=["Push Notifications"])
app.include_router(discussions.router, prefix="/api/v1/discussions", tags=["Discussions"])
app.include_router(user_management.router, prefix="/api/v1", tags=["User Management"])
app.include_router(subscriptions.router, prefix="/api/v1", tags=["Subscriptions"])

# Serve static audio files
storage_path = os.path.join(os.path.dirname(__file__), "..", "storage", "audio")
os.makedirs(storage_path, exist_ok=True)
app.mount("/storage/audio", StaticFiles(directory=storage_path), name="audio")

# Will be added as we create them:
# from app.routes import comments, engagement, analytics, media, users, search
# app.include_router(comments.router, prefix="/api/v1", tags=["Comments"])
# app.include_router(engagement.router, prefix="/api/v1", tags=["Engagement"])
# app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
# app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
# app.include_router(ai.router, prefix="/api/v1/ai", tags=["AI"])
# app.include_router(media.router, prefix="/api/v1/media", tags=["Media"])
# app.include_router(search.router, prefix="/api/v1/search", tags=["Search"])
