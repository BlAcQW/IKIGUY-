"""
ChurchFlow FastAPI Application

Main application entry point with startup/shutdown events,
middleware configuration, and route registration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import sys
import os

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from app.core.config import settings
from app.core.database import connect_to_mongodb, close_mongodb_connection, init_indexes, get_database
from apps.shared.middleware import OrganizationContextMiddleware
from apps.shared.services.organization_service import get_organization_service
from apps.shared.startup import initialize_default_organization
from apps.shared.routes.tts_routes import router as shared_tts_router
from apps.shared.routes.url_shortening_routes import create_url_shortening_router

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


async def resume_running_campaigns():
    """
    Resume any campaigns that were running when the server was restarted.

    This function is called on startup to ensure campaigns don't get stuck
    if the server restarts while they're running.

    Note: Only campaigns with status "running" are resumed. Paused campaigns
    remain paused and must be manually restarted.
    """
    try:
        from apps.shared.services.sms_campaign_service import sms_campaign_service, SMSCampaignStatus
        from apps.shared.integration.sms import SMSIntegration
        import os

        print("   🔍 [RESUME] Checking for running campaigns to resume...")
        logger.info("🔍 Checking for running campaigns to resume...")

        # Initialize SMS service
        sms_config = {
            "providers": {
                "arkesel": {
                    "api_key": settings.arkesel_api_key,
                    "sender_id": settings.arkesel_sender_id,
                },
                "twilio": {
                    "account_sid": os.getenv("TWILIO_ACCOUNT_SID", settings.twilio_account_sid),
                    "auth_token": os.getenv("TWILIO_AUTH_TOKEN", settings.twilio_auth_token),
                },
            },
            "default_provider": "arkesel",
        }

        sms_integration = SMSIntegration(sms_config)
        sms_campaign_service.set_sms_provider(sms_integration)

        db = get_database()
        sms_campaign_service.set_database(db)

        # Find all campaigns with status "running"
        # Note: We pass status=None to get all campaigns, then filter for running
        all_campaigns = await sms_campaign_service.list_campaigns(
            organization_id="",  # Get all organizations
            status=None,
            limit=1000
        )

        running_campaigns = [c for c in all_campaigns if c.status == SMSCampaignStatus.RUNNING]

        if not running_campaigns:
            print("   ✅ [RESUME] No running campaigns to resume")
            logger.info("✅ No running campaigns to resume")
            return

        print(f"   📊 [RESUME] Found {len(running_campaigns)} running campaign(s) to resume")
        logger.info(f"Found {len(running_campaigns)} running campaign(s) to resume")

        resumed_count = 0
        failed_count = 0

        for campaign in running_campaigns:
            print(f"   📤 [RESUME] Resuming: {campaign.name} ({campaign.progress.sent}/{campaign.progress.total_recipients})")
            logger.info(f"📤 Resuming campaign: {campaign.id} - '{campaign.name}' (Sent: {campaign.progress.sent}/{campaign.progress.total_recipients})")
            try:
                # Use force_resume=True to restart even if status is "running"
                await sms_campaign_service.start_campaign(campaign.id, force_resume=True)
                resumed_count += 1
                print(f"   ✅ [RESUME] Successfully resumed: {campaign.name}")
                logger.info(f"✅ Successfully resumed campaign: {campaign.id}")
            except Exception as e:
                failed_count += 1
                print(f"   ❌ [RESUME] Failed to resume: {campaign.name} - {e}")
                logger.error(f"❌ Failed to resume campaign {campaign.id}: {e}")

        print(f"   🎉 [RESUME] Complete - Success: {resumed_count}, Failed: {failed_count}")
        logger.info(f"Campaign resume complete - Success: {resumed_count}, Failed: {failed_count}")

    except Exception as e:
        print(f"   ❌ [RESUME] Error in resume_running_campaigns: {e}")
        logger.error(f"❌ Error in resume_running_campaigns: {e}")
        import traceback
        traceback.print_exc()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events for the application.

    Args:
        app: FastAPI application instance
    """
    # Startup
    print("🚀 [LIFESPAN] Starting ChurchFlow API...")
    logger.info("Starting ChurchFlow API...")
    await connect_to_mongodb()
    await init_indexes()

    # Initialize organization service
    print("🚀 [LIFESPAN] Initializing organization service...")
    db = get_database()
    org_service = get_organization_service(db)
    await org_service.initialize_indexes()
    logger.info("Organization service initialized")

    # Initialize default organization
    print("🚀 [LIFESPAN] Initializing default organization...")
    await initialize_default_organization()

    # Resume any running SMS campaigns
    print("🚀 [LIFESPAN] Resuming running SMS campaigns...")
    await resume_running_campaigns()

    # Initialize and start scheduler service
    print("🚀 [LIFESPAN] Initializing scheduler service...")
    from app.scheduler.scheduler_service import scheduler_service
    from app.core.database import mongodb_client

    scheduler_service.mongo_client = mongodb_client
    await scheduler_service.initialize()
    await scheduler_service.start()
    logger.info("Scheduler service started")

    print("✅ [LIFESPAN] ChurchFlow API started successfully")
    logger.info("ChurchFlow API started successfully")

    yield

    # Shutdown
    logger.info("Shutting down ChurchFlow API...")

    # Shutdown scheduler service
    logger.info("Shutting down scheduler service...")
    await scheduler_service.shutdown()
    logger.info("Scheduler service shut down")

    await close_mongodb_connection()
    logger.info("ChurchFlow API shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Mobile-first church management and event coordination platform",
    docs_url=f"{settings.api_prefix}/docs",
    redoc_url=f"{settings.api_prefix}/redoc",
    openapi_url=f"{settings.api_prefix}/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Organization-ID"],
)

# Add Organization Context Middleware
app.add_middleware(OrganizationContextMiddleware)


@app.get("/")
async def root():
    """
    Root endpoint.

    Returns:
        dict: API information
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": f"{settings.api_prefix}/docs",
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        dict: Health status
    """
    return {"status": "healthy"}


# Register API routes
from app.api.routes import auth, users, buses, conferences, registrations, wallet, analytics, church_analytics, member_analytics, organizations, feedback, voice_greetings, voice_library, geocoding, tts, sessions, session_attendance, sms_campaigns, whatsapp_campaigns, dashboard, conference_analytics, visitors, journey, leadership, member_enrichment, journey_communications, conference_materials, billing, onboarding, platform_admin, integrations, automation, giving, member_portal, services, proximity_checkin, gamification, groups, first_timers, announcements
from app.api.routes import branches_crud

app.include_router(
    auth.router,
    prefix=f"{settings.api_prefix}/auth",
    tags=["Authentication"]
)

app.include_router(
    users.router,
    prefix=f"{settings.api_prefix}/users",
    tags=["Users"]
)

app.include_router(
    organizations.router,
    prefix=f"{settings.api_prefix}/organizations",
    tags=["Organizations"]
)

app.include_router(
    buses.router,
    prefix=f"{settings.api_prefix}/buses",
    tags=["Bus Routes"]
)

app.include_router(
    conferences.router,
    prefix=f"{settings.api_prefix}/conferences",
    tags=["Conferences"]
)

app.include_router(
    branches_crud.router,
    prefix=f"{settings.api_prefix}",
    tags=["Branches"]
)

app.include_router(
    registrations.router,
    prefix=f"{settings.api_prefix}/registrations",
    tags=["Registrations"]
)

app.include_router(
    wallet.router,
    prefix=settings.api_prefix,
    tags=["Wallet"]
)

app.include_router(
    analytics.router,
    prefix=settings.api_prefix,
    tags=["Analytics"]
)

app.include_router(
    church_analytics.router,
    prefix=settings.api_prefix,
    tags=["Church Analytics"]
)

app.include_router(
    member_analytics.router,
    prefix=f"{settings.api_prefix}/member-analytics",
    tags=["Member Analytics"]
)

app.include_router(
    feedback.router,
    prefix=settings.api_prefix,
    tags=["Feedback"]
)

app.include_router(
    voice_greetings.router,
    prefix=f"{settings.api_prefix}/voice-greetings",
    tags=["Voice Greetings"]
)

app.include_router(
    voice_library.router,
    prefix=f"{settings.api_prefix}/voice-library",
    tags=["Voice Library"]
)

app.include_router(
    geocoding.router,
    prefix=settings.api_prefix,
    tags=["Geocoding"]
)

# Add shared TTS router at /api/tts for synthesis and providers
# (shared frontend components expect /api/tts/synthesize, /api/tts/providers)
app.include_router(shared_tts_router, prefix="/api/tts", tags=["TTS"])

# Add ChurchFlow-specific TTS router (provides additional provider endpoints)
app.include_router(
    tts.router,
    prefix=settings.api_prefix,
    tags=["ChurchFlow TTS"]
)

app.include_router(
    sessions.router,
    prefix=settings.api_prefix,
    tags=["Sessions"]
)

app.include_router(
    session_attendance.router,
    prefix=settings.api_prefix,
    tags=["Session Attendance"]
)

app.include_router(
    sms_campaigns.router,
    prefix=f"{settings.api_prefix}/sms-campaigns",
    tags=["SMS Campaigns"]
)

app.include_router(
    whatsapp_campaigns.router,
    prefix=f"{settings.api_prefix}/whatsapp-campaigns",
    tags=["WhatsApp Campaigns"]
)

app.include_router(
    dashboard.router,
    prefix=f"{settings.api_prefix}/dashboard",
    tags=["Dashboard"]
)

app.include_router(
    conference_analytics.router,
    prefix=settings.api_prefix,
    tags=["Conference Analytics"]
)

# Visitor Tracking & Discipleship System Routes
app.include_router(
    visitors.router,
    prefix=f"{settings.api_prefix}/visitors",
    tags=["Visitors"]
)

app.include_router(
    journey.router,
    prefix=f"{settings.api_prefix}/journey",
    tags=["Journey"]
)

app.include_router(
    leadership.router,
    prefix=f"{settings.api_prefix}",
    tags=["Leadership"]
)

app.include_router(
    groups.router,
    prefix=f"{settings.api_prefix}/groups",
    tags=["Groups"]
)

app.include_router(
    first_timers.router,
    prefix=f"{settings.api_prefix}/first-timers",
    tags=["First Timers"]
)

app.include_router(
    announcements.router,
    prefix=f"{settings.api_prefix}/announcements",
    tags=["Announcements"]
)

app.include_router(
    member_enrichment.router,
    prefix=f"{settings.api_prefix}/members",
    tags=["Member Enrichment"]
)

app.include_router(
    journey_communications.router,
    prefix=f"{settings.api_prefix}/journey/communications",
    tags=["Journey Communications"]
)

app.include_router(
    conference_materials.router,
    prefix=settings.api_prefix,
    tags=["Conference Materials"]
)

app.include_router(
    billing.router,
    prefix=settings.api_prefix,
    tags=["Billing & Subscriptions"]
)

app.include_router(
    onboarding.router,
    prefix=settings.api_prefix,
    tags=["Onboarding"]
)

app.include_router(
    platform_admin.router,
    prefix=settings.api_prefix,
    tags=["Platform Admin"]
)

app.include_router(
    integrations.router,
    prefix=settings.api_prefix,
    tags=["Integrations"]
)

app.include_router(
    automation.router,
    prefix=f"{settings.api_prefix}/automation",
    tags=["Automation"]
)

app.include_router(
    giving.router,
    prefix=f"{settings.api_prefix}/giving",
    tags=["Online Giving"]
)

app.include_router(
    member_portal.router,
    prefix=f"{settings.api_prefix}/member-portal",
    tags=["Member Portal"]
)

app.include_router(
    services.router,
    prefix=f"{settings.api_prefix}/services",
    tags=["Services"]
)

# Proximity Check-In & Gamification
app.include_router(
    proximity_checkin.router,
    prefix=settings.api_prefix,
    tags=["Proximity Check-In"]
)

app.include_router(
    gamification.router,
    prefix=settings.api_prefix,
    tags=["Gamification"]
)

# URL Shortening - using shared service (both API endpoints and redirect)
url_shortening_router = create_url_shortening_router(
    get_database_func=get_database,
    base_url="https://churchflow.ailabsafrica.com",
    app_name="churchflow"
)
app.include_router(url_shortening_router, prefix=settings.api_prefix, tags=["Short URLs"])  # /api/v1/short-urls/*
app.include_router(url_shortening_router, tags=["Short URLs"])  # /s/{short_code} redirect

# TODO: Add more routes as they are implemented
# from app.api.routes import notifications
# app.include_router(notifications.router, prefix=f"{settings.api_prefix}/notifications", tags=["Notifications"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
