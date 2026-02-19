from __future__ import annotations

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import (
    FastAPI,
    HTTPException,
    Depends,
    WebSocket,
    WebSocketDisconnect,
    UploadFile,
    File,
    Form,
    Request,
    Query,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import WebSocketException
from uuid import UUID, uuid4
import secrets
import logging
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from typing import Dict, Any, Union, Tuple, Optional
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Configure colored logging
import sys
from logging import StreamHandler, Formatter

class ColoredFormatter(Formatter):
    """Custom formatter to add colors to log levels"""

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'          # Reset color

    def format(self, record):
        # Add color to the log level
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"

        # Format the message with colors
        formatted = super().format(record)

        # Add colors to specific message patterns
        if "📞 VAPI TOOL CALL" in formatted or "📤 VAPI TOOL RESPONSE" in formatted:
            formatted = f"\033[1;34m{formatted}\033[0m"  # Bold Blue
        elif "✅" in formatted:
            formatted = f"\033[1;32m{formatted}\033[0m"  # Bold Green
        elif "❌" in formatted:
            formatted = f"\033[1;31m{formatted}\033[0m"  # Bold Red
        elif "🔍" in formatted:
            formatted = f"\033[1;33m{formatted}\033[0m"  # Bold Yellow

        return formatted

# Configure colored logging
colored_handler = StreamHandler(sys.stdout)
colored_handler.setFormatter(ColoredFormatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))

# Configure logging with colored handler
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.handlers.clear()  # Clear any existing handlers
root_logger.addHandler(colored_handler)

# Set specific modules to DEBUG level
debug_modules = [
    'backend.routes.call_management',
    'backend.routes.premier_health',
    'backend.routes.integration_webhooks'
]

for module in debug_modules:
    logger_module = logging.getLogger(module)
    logger_module.setLevel(logging.DEBUG)

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .models import (
    Assistant,
    AssistantCreate,
    KbSource,
    KbIngestRequest,
    KbSearchRequest,
    KbSearchResult,
    ServiceAccount,
    ServiceAccountCreate,
    HandoverRequest,
    SessionStatus,
    Message,
    Campaign,
    CampaignCreate,
    Audience,
    AudienceCreate,
    AudienceContact,
    DemoDeployRequest,
)
from .auth import get_current_account, get_api_deploy_key, get_current_user_mongo
from .sessions import SessionManager
from .kb import ingest as kb_ingest, fetch_url, search as kb_search
from .edge import router as edge_router
from .events import event_bus, EventType
from .qa import router as qa_router
from .events_worker import router as events_router
from .webhooks import router as webhooks_router
from .routes.industry_modules import router as industry_modules_router
from .routes.voice_engine import router as voice_engine_router
from .routes.voice_engine.phone_numbers import router as phone_numbers_router
from .routes.voice_engine.call_webhooks import router as call_webhooks_router
from .routes.voice_engine.assistant_testing import router as assistant_testing_router
from .routes.voice_engine.sip_registration import router as sip_registration_router
from .routes.voice_engine.ant_gateways import router as ant_gateways_router
# Import WebRTC from shared module (all apps can use this!)
# FastRTC removed - using custom aiortc implementation for dynamic assistant support
# from apps.shared.integration.webrtc import setup_webrtc
# Import Speech-to-Speech comparison
from .routes.voice_engine.speech_to_speech_comparison import (
    router as speech_to_speech_router,
    # setup_fastrtc_comparison  # Disabled - using aiortc instead of FastRTC
)
from .routes.integrations_routes import router as integrations_router
from .routes.integrations import router as integrations_v2_router
from .routes.voice_creation import router as voice_creation_router
from .routes.voice_lab_routes import router as voice_lab_router
# Voice library now uses shared service layer - import shared router factory
from apps.shared.routes.voice_library_routes import create_voice_library_router
# Reference audio routes for zero-shot TTS providers (StyleTTS2, XTTS, OpenVoice, F5-TTS)
from apps.shared.routes.reference_audio_routes import create_reference_audio_router
from .routes.cloned_voices import router as cloned_voices_router
# Re-enabled after HealthMonitor fix verification
from .routes.tts_services import router as tts_services_router
# REMOVED: tts.py is redundant with tts_services.py which provides superior functionality
# TTS Provider Service for comprehensive TTS with billing and health monitoring
from apps.shared.services.tts_provider_service import TTSProviderService
# Unified TTS routes from @shared/routes (Phase 2.4 of TTS Consolidation)
from apps.shared.routes.tts_routes import router as unified_tts_router
# WebSocket ASR streaming for VAPI custom-transcriber support
from apps.shared.routes.asr_routes import ws_router as asr_ws_router
# TEMPORARILY DISABLED: batch_synthesis imports non-existent services
# from .routes.batch_synthesis_routes import router as batch_synthesis_router
from .routes.audio_conversion_routes import router as audio_conversion_router
from .routes.api_keys import router as api_keys_router
from .routes.llm_services import router as llm_services_router
from .routes.asr_services import router as asr_services_router
from .routes.asr_services_phase5 import router as asr_services_phase5_router
from .routes.campaigns import router as campaigns_router
from .routes.voice_campaigns import router as voice_campaigns_router
from .routes.sms_campaigns import router as sms_campaigns_router
from .routes.whatsapp_campaigns import router as whatsapp_campaigns_router
from .routes.vapi import router as vapi_router
from .routes.vapi_consolidated import router as vapi_consolidated_router
from .routes.freshdesk_consolidated import router as freshdesk_consolidated_router
from .routes.vonage_consolidated import router as vonage_consolidated_router
from .routes.resend_consolidated import router as resend_consolidated_router
from .routes.tavily_consolidated import router as tavily_consolidated_router
from .routes.calendly_consolidated import router as calendly_consolidated_router
from .routes.firecrawl_consolidated import router as firecrawl_consolidated_router
from .routes.brave_consolidated import router as brave_consolidated_router
from .routes.ai_prompt_generator import router as ai_prompt_generator_router
from .routes.integrations_manager import router as integrations_manager_router
from .routes.monitoring import router as monitoring_router
from .routes.vapi_management import router as vapi_management_router
from .routes.vapi_assistants import router as vapi_assistants_router
from .routes.vapi_custom_providers import router as vapi_custom_providers_router
from .routes.vapi_assistant_update import router as vapi_assistant_update_router
from .routes.vapi_test_call import router as vapi_test_call_router
from .routes.organizations import router as organizations_router
from .routes.enhanced_helpdesk import router as enhanced_helpdesk_router
from .routes.enhanced_payment_reminder import router as enhanced_payment_reminder_router
from .routes.enhanced_sales_outreach import router as enhanced_sales_outreach_router
from .routes.enhanced_lead_nurturing import router as enhanced_lead_nurturing_router
from .routes.enhanced_customer_reactivation import router as enhanced_customer_reactivation_router
from .routes.enhanced_template import router as enhanced_template_router
from .routes.premier_health import router as premier_health_router
from .routes.premier_health_transfers import router as premier_health_transfers_router
from .routes.vapi_premier_health_alias import router as vapi_premier_health_alias_router
from .routes.product_launch import router as product_launch_router
from .routes.automation_templates import router as automation_templates_router
from .routes.automation_configs import router as automation_configs_router
from .routes.n8n_templates import router as n8n_templates_router
from .routes.user_favorites import router as user_favorites_router
from .routes.custom_tools import router as custom_tools_router
from .routes.admin import router as admin_router
from .routes.invitations_public import router as invitations_public_router
from .routes.fraud_detection import router as fraud_detection_router
from .routes.cost_analytics import router as cost_analytics_router
from .routes.auth import router as auth_router
from .routes.app_settings import router as app_settings_router
from .routes.industries import router as industries_router
from .routes.migrations import router as migrations_router
from .routes.integration_categories import router as integration_categories_router
from .routes.integrations import router as integrations_main_router
from .routes.automation_orchestration import router as automation_orchestration_router
from .routes.analytics import router as analytics_router
from .routes.automation_health import router as automation_health_router
from .routes.automation_analytics import router as automation_analytics_router
from .routes.automation_settings import router as automation_settings_router
from .routes.alert_management import router as alert_management_router
from .routes.export_routes import router as export_router
from .routes.backups import router as backups_router
from .routes.deployment_tracking import router as deployment_tracking_router
from .routes.integration_webhooks import router as integration_webhooks_router
from .routes.call_management import router as call_management_router
from .routes.asterisk import router as asterisk_router
from .routes.vapi_testing import router as vapi_testing_router
from .routes.knowledge_base import router as knowledge_base_router
from .routes.call_logs import router as call_logs_router
from .routes.system_health import router as system_health_router
from .routes.service_management import router as service_management_router
from .routes.tool_calls import router as tool_calls_router
from .routes.wallet import router as wallet_router
from .routes.affiliates import router as affiliates_router
from .routes.qr_codes import router as qr_codes_router
from .routes.scraper import router as scraper_router
from .routes.internal_usage import router as internal_usage_router
from .routes.recruitment import router as recruitment_router

# Initialize scheduler BEFORE importing cron_management routes
# Reason: cron_management router needs cron_management_service which requires scheduler
# AsyncIOScheduler properly handles async functions without breaking Motor event loop

scheduler = AsyncIOScheduler(timezone=timezone.utc)
scheduler.start()

# Initialize cron management service
from .services.cron_management_service import init_cron_management_service
init_cron_management_service(scheduler)

# Initialize scheduled alert checker
from .services.scheduled_alert_checker import schedule_alert_checks
schedule_alert_checks(scheduler)

# Initialize automated billing sync (runs daily at midnight UTC)
from .tasks.billing_sync import sync_and_bill_all_automations_sync
scheduler.add_job(
    sync_and_bill_all_automations_sync,
    CronTrigger(hour=0, minute=0),  # Run at 00:00 UTC daily
    id='billing_sync',
    name='Automated Billing Sync',
    replace_existing=True
)

# Initialize wallet auto-reload (runs every 5 minutes)
from .tasks.wallet_auto_reload import check_and_reload_wallets_sync
scheduler.add_job(
    check_and_reload_wallets_sync,
    'interval',
    minutes=5,  # Check every 5 minutes
    id='wallet_auto_reload',
    name='Wallet Auto-Reload',
    replace_existing=True
)

# Initialize automated affiliate payouts (runs daily at 2 AM UTC)
from .tasks.affiliate_payouts import process_automated_payouts_sync
scheduler.add_job(
    process_automated_payouts_sync,
    CronTrigger(hour=2, minute=0),  # Run at 02:00 UTC daily
    id='affiliate_payouts',
    name='Automated Affiliate Payouts',
    replace_existing=True
)

# Initialize campaign auto-resume (runs every minute to check paused campaigns)
# AsyncIOScheduler can call async functions directly without wrapper
from .services.campaign_execution_service import check_and_resume_paused_campaigns

scheduler.add_job(
    check_and_resume_paused_campaigns,  # Direct async function call
    'interval',
    minutes=1,  # Check every minute
    id='campaign_auto_resume',
    name='Campaign Auto-Resume',
    replace_existing=True
)
# Log messages will appear when FastAPI app starts (logger not yet defined here)

# Now import cron_management router after service is initialized
from .routes.cron_management import router as cron_management_router
from .routes.feedback import router as feedback_router
from .routes.storage import router as storage_router

from .mcp import init_mcp_manager, get_mcp_manager
from .services.payment_service import PaymentService

# Import shared library services
from .services.license_service import LicenseService
from .services.usage_service import UsageService
from .services.config_service import ConfigService
from .services.monitoring_service import MonitoringService
from .services.security_service import SecurityService
from .services.module_service import ModuleService
from .services.telephony_service import TelephonyService
from .services.assistant_service import MongoDBAssistantService
from .services import campaign_service, service_account_service

# Initialize assistant service
assistant_service = MongoDBAssistantService()

logger = logging.getLogger(__name__)

# Initialize rate limiter
# Reason: Protect API from abuse and spam requests, especially on auth endpoints
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per minute"])
app = FastAPI(title="KasaAI Core Backend")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Global TTS Provider Service instance (initialized on startup)
tts_provider_service: Optional[TTSProviderService] = None

# Add validation error handler to log request body parsing errors
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import Request, status

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Log validation errors to help debug VAPI integration issues."""
    logger.error(f"❌ Validation Error for {request.method} {request.url.path}")
    logger.error(f"   Client IP: {request.client.host if request.client else 'unknown'}")
    try:
        body = await request.body()
        logger.error(f"   Request body: {body.decode('utf-8')}")
    except:
        logger.error(f"   Could not read request body")
    logger.error(f"   Validation errors: {exc.errors()}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()}
    )

# CORS is handled by nginx - commenting out to prevent duplicate headers
# # Add CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[
#         "http://localhost:8080",
#         "http://localhost:8081",
#         "http://localhost:8082",
#         "http://localhost:5173",
#         "http://localhost:3000",
#         "http://127.0.0.1:8080",
#         "http://127.0.0.1:8081",
#         "http://127.0.0.1:8082",
#         "http://127.0.0.1:5173",
#         "http://127.0.0.1:3000",
#         "https://kasaai.ailabsafrica.com",
#         "https://api.ailabsafrica.com",
#         "http://kasaai.ailabsafrica.com",
#         "http://api.ailabsafrica.com",
#         "https://language-community.ailabsafrica.com",
#         "http://language-community.ailabsafrica.com",
#         "https://flow.ailabsafrica.com",
#         "http://flow.ailabsafrica.com"
#     ],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With", "X-Service-Token"],
# )

# Add Organization Context Middleware
from .middleware.organization_context import OrganizationContextMiddleware
app.add_middleware(OrganizationContextMiddleware)

session_manager = SessionManager()

# Initialize shared library services
license_service = LicenseService()
usage_service = UsageService()
config_service = ConfigService()
monitoring_service = MonitoringService()
security_service = SecurityService()
module_service = ModuleService()
telephony_service = TelephonyService()

# Initialize payment service only if not in test environment
try:
    payment_service = PaymentService(event_bus)
except RuntimeError as e:
    if "MCP manager not initialized" in str(e):
        # In test environment, create a mock payment service
        payment_service = None
    else:
        raise

app.include_router(edge_router)
app.include_router(qa_router)
app.include_router(events_router)
app.include_router(webhooks_router)
app.include_router(industry_modules_router)
app.include_router(voice_engine_router)
app.include_router(phone_numbers_router)
app.include_router(call_webhooks_router)
app.include_router(assistant_testing_router)
app.include_router(sip_registration_router)
app.include_router(ant_gateways_router)

# WebRTC voice endpoints using custom aiortc implementation
# Supports dynamic assistant IDs with full control
# Uses aiortc (NOT FastRTC) for proper dynamic routing
from .routes.voice_engine.webrtc_aiortc import router as webrtc_aiortc_router
app.include_router(webrtc_aiortc_router)

app.include_router(voice_creation_router)
app.include_router(speech_to_speech_router)  # Speech-to-Speech comparison
# FastRTC comparison endpoint disabled - using aiortc for WebRTC
# setup_fastrtc_comparison(app, assistant_id="default-assistant")
app.include_router(integrations_router)
app.include_router(integrations_v2_router)
app.include_router(voice_lab_router)

# Create voice library router using shared service layer (consistent with other apps)
# Uses VoiceLibraryService singleton with MongoDB connection to kasaai_core
from .auth import get_current_user_mongo
voice_library_router = create_voice_library_router(
    get_current_user_func=get_current_user_mongo
)
app.include_router(voice_library_router, prefix="/api/voice-library", tags=["Voice Library"])

# Create reference audio router using shared service layer (for zero-shot TTS providers)
# Uses ReferenceAudioService singleton with MongoDB connection to kasaai_core
reference_audio_router = create_reference_audio_router(
    get_current_user_func=get_current_user_mongo,
    storage_base_path="core_backend/reference_audio"  # App-specific storage path
)
app.include_router(reference_audio_router, tags=["Reference Audio"])
app.include_router(cloned_voices_router)
# Unified TTS router from @shared/routes (now with JWT auth support)
# Provides comprehensive TTS API with JWT authentication, billing, and caching
app.include_router(unified_tts_router, prefix="/api/tts", tags=["TTS Unified"])
# DISABLED: tts_services_router - replaced by unified_tts_router for consistency across apps
# The unified router now extracts user_id from JWT tokens automatically
# app.include_router(tts_services_router)
# REMOVED: tts_router is redundant with unified_tts_router
# TEMPORARILY DISABLED: batch_synthesis imports non-existent services
# app.include_router(batch_synthesis_router)
app.include_router(audio_conversion_router)
app.include_router(api_keys_router)
app.include_router(llm_services_router)
app.include_router(asr_services_router)
app.include_router(asr_services_phase5_router)
# WebSocket ASR streaming for VAPI custom-transcriber (wss://api.ailabsafrica.com/ws/asr/stream)
app.include_router(asr_ws_router, prefix="/ws/asr", tags=["ASR WebSocket"])
app.include_router(campaigns_router)
app.include_router(voice_campaigns_router)
app.include_router(sms_campaigns_router)
app.include_router(whatsapp_campaigns_router, prefix="/api")
app.include_router(vapi_router, prefix="/api")
app.include_router(vapi_management_router, prefix="/api")
app.include_router(vapi_assistants_router, prefix="/api")
app.include_router(vapi_custom_providers_router, prefix="/api")
app.include_router(vapi_assistant_update_router, prefix="/api")
app.include_router(vapi_test_call_router, prefix="/api")
app.include_router(vapi_consolidated_router, prefix="/api")
app.include_router(freshdesk_consolidated_router)
app.include_router(vonage_consolidated_router)
app.include_router(resend_consolidated_router)
app.include_router(tavily_consolidated_router)
app.include_router(calendly_consolidated_router)
app.include_router(firecrawl_consolidated_router)
app.include_router(brave_consolidated_router)
app.include_router(ai_prompt_generator_router)
app.include_router(integrations_manager_router)
app.include_router(monitoring_router)
app.include_router(organizations_router)
app.include_router(enhanced_helpdesk_router)
app.include_router(enhanced_payment_reminder_router)
app.include_router(enhanced_sales_outreach_router)
app.include_router(enhanced_lead_nurturing_router)
app.include_router(enhanced_customer_reactivation_router)
app.include_router(enhanced_template_router)
app.include_router(vapi_premier_health_alias_router)  # Must be before premier_health_router to catch /vapi/webhooks path
app.include_router(premier_health_router)
app.include_router(premier_health_transfers_router, prefix="/premier-health", tags=["Premier Health Transfers"])
app.include_router(product_launch_router)
app.include_router(automation_templates_router)
app.include_router(automation_configs_router)
app.include_router(n8n_templates_router)
app.include_router(user_favorites_router)
app.include_router(custom_tools_router)
app.include_router(admin_router)
app.include_router(invitations_public_router)
app.include_router(fraud_detection_router)
app.include_router(cost_analytics_router)
app.include_router(auth_router)
app.include_router(app_settings_router)
app.include_router(industries_router)
app.include_router(migrations_router)
app.include_router(integration_categories_router)
app.include_router(integrations_main_router)
app.include_router(automation_orchestration_router)
app.include_router(analytics_router, prefix="/api")
app.include_router(export_router, prefix="/api/export", tags=["export"])
app.include_router(automation_health_router)
app.include_router(automation_analytics_router, prefix="/api")
app.include_router(automation_settings_router)
app.include_router(alert_management_router, prefix="/api")
app.include_router(deployment_tracking_router)
app.include_router(integration_webhooks_router)
app.include_router(call_management_router)
app.include_router(asterisk_router)
app.include_router(vapi_testing_router)
app.include_router(knowledge_base_router)
app.include_router(call_logs_router)
app.include_router(tool_calls_router)
app.include_router(wallet_router, prefix="/api")
# Unified TTS routes moved up to /api/tts prefix (see above) for proper precedence
app.include_router(affiliates_router)
app.include_router(system_health_router, prefix="/api/system", tags=["system"])
app.include_router(service_management_router, prefix="/api/services", tags=["services"])
app.include_router(cron_management_router)
app.include_router(backups_router)
app.include_router(feedback_router, prefix="/api")
app.include_router(storage_router)
app.include_router(qr_codes_router, prefix="/api")
app.include_router(scraper_router, prefix="/api")
app.include_router(internal_usage_router, prefix="/api")
app.include_router(recruitment_router)  # AI Labs Africa recruitment


@app.post("/vapi/create-assistant")
async def create_vapi_assistant_compat(request: dict, current_user: dict = Depends(get_current_user_mongo)):
    """Backwards compatibility endpoint for VAPI assistant creation."""
    try:
        # This endpoint can be implemented using the VAPI service
        return {
            "success": True,
            "assistant_id": f"vapi_assistant_{uuid4().hex[:8]}",
            "phone_number": "+1234567890",
            "status": "created"
        }
    except Exception as e:
        logger.error(f"Error in VAPI assistant creation compatibility endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Scheduler and cron service already initialized at top of file (before cron_management router import)
campaign_runs: Dict[UUID, int] = defaultdict(int)
_campaign_state: Dict[UUID, Tuple[datetime, int]] = {}
_campaign_attempts: Dict[UUID, int] = defaultdict(int)
_campaign_active: Dict[UUID, bool] = defaultdict(lambda: True)
GROUNDING_THRESHOLD = 1.0


async def _enforce_license(
    tenant_id: UUID,
    agents: int = 0,
    channels: int = 0,
    minutes: float = 0.0,
) -> None:
    """Check license limits for the tenant and raise if exceeded using shared library."""

    # Use shared license service for validation
    license_info = await license_service.get_license_info(str(tenant_id))
    if not license_info:
        return  # No license found, allow operation

    # Check if license is active
    if not license_info.is_active:
        raise HTTPException(status_code=403, detail="license expired")

    # Check feature access
    if agents > 0:
        has_access = await license_service.check_feature_access(
            str(tenant_id), "agents", agents
        )
        if not has_access:
            raise HTTPException(status_code=403, detail="agent limit exceeded")

    if channels > 0:
        has_access = await license_service.check_feature_access(
            str(tenant_id), "channels", channels
        )
        if not has_access:
            raise HTTPException(status_code=403, detail="channel limit exceeded")

    if minutes > 0:
        has_access = await license_service.check_feature_access(
            str(tenant_id), "minutes", minutes
        )
        if not has_access:
            raise HTTPException(status_code=403, detail="minute limit exceeded")


async def _record_usage(
    tenant_id: UUID,
    assistant_id: Union[UUID, None] = None,
    campaign_id: Union[UUID, None] = None,
    minutes: float = 0.0,
    messages: int = 0,
    stt_calls: int = 0,
    tts_calls: int = 0,
    telephony_cost: float = 0.0,
    stt_cost: float = 0.0,
    tts_cost: float = 0.0,
) -> None:
    """Record usage metrics using shared library."""

    await usage_service.record_usage(
        tenant_id=str(tenant_id),
        feature="core_backend",
        quantity=minutes,
        metadata={
            "assistant_id": str(assistant_id) if assistant_id else None,
            "campaign_id": str(campaign_id) if campaign_id else None,
            "messages": messages,
            "stt_calls": stt_calls,
            "tts_calls": tts_calls,
            "telephony_cost": telephony_cost,
            "stt_cost": stt_cost,
            "tts_cost": tts_cost,
        },
    )


async def run_campaign(
    campaign_id: UUID,
    pacing_per_minute: int,
    max_attempts: int,
    backoff_minutes: int,
) -> None:
    """Execute a scheduled campaign run respecting pacing and retries.

    Args:
        campaign_id (UUID): Identifier for the campaign.
        pacing_per_minute (int): Maximum executions per minute.
        max_attempts (int): Maximum retry attempts.
        backoff_minutes (int): Minutes to wait before retrying.
    """

    if not _campaign_active[campaign_id]:
        return

    now = datetime.now(timezone.utc)
    window = now.replace(second=0, microsecond=0)
    state_window, count = _campaign_state.get(campaign_id, (window, 0))
    if state_window != window:
        state_window, count = window, 0
    if count >= pacing_per_minute:
        _campaign_state[campaign_id] = (state_window, count)
        return
    _campaign_state[campaign_id] = (state_window, count + 1)
    campaign_runs[campaign_id] += 1

    attempt = _campaign_attempts[campaign_id] + 1
    _campaign_attempts[campaign_id] = attempt

    # Use shared telephony service for dialing
    try:
        call_result = await telephony_service.initiate_call(
            tenant_id=str(
                campaign_id
            ),  # Using campaign_id as tenant_id for this example
            destination="+1234567890",  # This should come from campaign configuration
            source="+0987654321",
        )

        if call_result.success:
            outcome = "answered"
            # Record successful usage
            await _record_usage(
                tenant_id=campaign_id,
                campaign_id=campaign_id,
                minutes=call_result.duration or 0.0,
                telephony_cost=call_result.cost or 0.0,
            )
        else:
            outcome = "failed"

    except Exception as e:
        logger.error(f"Campaign {campaign_id} failed: {e}")
        outcome = "failed"

    # Map outcomes to event types
    if outcome == "answered":
        event_bus.emit(
            EventType.OUTCOME_CONVERTED,
            campaign_id=str(campaign_id),
            outcome=outcome,
        )
        _campaign_active[campaign_id] = False
        return

    # Handle retryable outcomes
    retryable_outcomes = {"busy", "no_answer"}
    if outcome in retryable_outcomes and attempt < max_attempts:
        run_time = now + timedelta(minutes=backoff_minutes)
        scheduler.add_job(
            run_campaign,
            "date",
            run_date=run_time,
            args=[campaign_id, pacing_per_minute, max_attempts, backoff_minutes],
        )
        return

    _campaign_active[campaign_id] = False


def schedule_campaign(campaign: Campaign) -> None:
    """Register a campaign with the scheduler."""
    parts = campaign.cron.split()
    if len(parts) == 5:
        trigger = CronTrigger.from_crontab(campaign.cron)
    elif len(parts) == 6:
        trigger = CronTrigger(
            second=parts[0],
            minute=parts[1],
            hour=parts[2],
            day=parts[3],
            month=parts[4],
            day_of_week=parts[5],
        )
    else:
        raise ValueError("Cron expression must have 5 or 6 fields")
    _campaign_active[campaign.id] = True
    _campaign_attempts[campaign.id] = 0
    scheduler.add_job(
        run_campaign,
        trigger,
        args=[
            campaign.id,
            campaign.pacing_per_minute,
            campaign.max_attempts,
            campaign.backoff_minutes,
        ],
        id=str(campaign.id),
        replace_existing=True,
    )


def _reset_campaign_state() -> None:
    """Reset in-memory campaign state (used in tests)."""

    campaign_runs.clear()
    _campaign_state.clear()
    _campaign_attempts.clear()
    # dialer.reset() # This line is removed as per the new_code
    _campaign_active.clear()


@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}


@app.websocket("/internal/sessions/{session_id}")
async def session_ws(
    websocket: WebSocket, session_id: UUID, tenant_id: Union[UUID, None] = None
) -> None:
    """Session handler that performs grounding checks via KB search.

    The caller must supply ``X-Service-Token`` in the headers. Messages
    are stored in memory. When ``tenant_id`` is provided, the handler
    searches the tenant's knowledge base. If the top result score is below
    ``GROUNDING_THRESHOLD`` it asks for clarification.

    Args:
        websocket (WebSocket): Active websocket connection.
        session_id (UUID): Identifier for the session.
        tenant_id (Union[UUID, None]): Tenant owning the knowledge base.
    """

    token = websocket.headers.get("x-service-token")
    try:
        get_current_account(token)
    except HTTPException:
        raise WebSocketException(code=1008)
    await websocket.accept()
    session_manager.start_session(session_id)
    try:
        while True:
            data = await websocket.receive_text()
            if data.strip().lower() == "bad":
                await websocket.send_text("guardrail triggered")
                await websocket.close(code=4000)
                break
            session_manager.add_turn(session_id, "user", data)
            reply = data.upper()
            if tenant_id:
                results = kb_search(tenant_id, data, top_k=1)
                if results and results[0][1] >= GROUNDING_THRESHOLD:
                    reply = results[0][0].text
                else:
                    reply = "I'm not sure about that. Could you clarify?"
            session_manager.add_turn(session_id, "assistant", reply)
            await websocket.send_text(reply)
    except WebSocketDisconnect:
        pass
    finally:
        session_manager.end_session(session_id)
        if tenant_id:
            log = session_manager.status(session_id)
            if log.end_time and log.start_time:
                duration = (log.end_time - log.start_time).total_seconds() / 60
            else:
                duration = 0.0
            user_msgs = sum(1 for r, _ in log.messages if r == "user")
            assist_msgs = sum(1 for r, _ in log.messages if r != "user")
            await _record_usage(
                tenant_id=tenant_id,
                minutes=duration,
                messages=len(log.messages),
                stt_calls=user_msgs,
                tts_calls=assist_msgs,
            )


@app.post(
    "/internal/assistants",
    response_model=Assistant,
)
async def create_assistant(payload: AssistantCreate, current_user: dict = Depends(get_current_user_mongo)) -> Assistant:
    """Create an assistant.

    Args:
        payload (AssistantCreate): Assistant configuration.

    Returns:
        Assistant: Newly created assistant.
    """

    # Use shared license service for validation
    await _enforce_license(payload.tenant_id, agents=1)
    return assistant_service.create_assistant(payload)


@app.get(
    "/internal/assistants/{assistant_id}",
    response_model=Assistant,
)
async def get_assistant(assistant_id: UUID, current_user: dict = Depends(get_current_user_mongo)) -> Assistant:
    """Retrieve an assistant by ID.

    Args:
        assistant_id (UUID): Assistant identifier.

    Returns:
        Assistant: Requested assistant.

    Raises:
        HTTPException: If assistant does not exist.
    """

    assistant = assistant_service.get_assistant(assistant_id)
    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant not found")
    return assistant


@app.get(
    "/internal/assistants",
    response_model=list[Assistant],
)
async def list_assistants(current_user: dict = Depends(get_current_user_mongo)) -> list[Assistant]:
    """List all assistants for a tenant.

    Args:
        current_user (dict): Authenticated user with tenant_id.

    Returns:
        list[Assistant]: Assistants belonging to the tenant.
    """
    # Use get_all_assistants for now since there's no tenant-specific method
    return assistant_service.get_all_assistants()


@app.post(
    "/internal/campaigns",
    response_model=Campaign,
    dependencies=[Depends(get_current_account)],
)
async def create_campaign(payload: CampaignCreate) -> Campaign:
    """Create a campaign and schedule it.

    Args:
        payload (CampaignCreate): Campaign configuration.

    Returns:
        Campaign: Newly created campaign.
    """

    # Use shared license service for validation
    await _enforce_license(payload.tenant_id, channels=1)
    campaign = campaign_service.create_campaign(payload)
    schedule_campaign(campaign)
    return campaign


@app.get(
    "/internal/campaigns/{campaign_id}",
    response_model=Campaign,
    dependencies=[Depends(get_current_account)],
)
async def get_campaign(campaign_id: UUID) -> Campaign:
    """Retrieve a campaign by ID.
    Args:
        campaign_id (UUID): Campaign identifier.

    Returns:
        Campaign: Requested campaign.

    Raises:
        HTTPException: If campaign does not exist.
    """

    campaign = campaign_service.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@app.get(
    "/internal/campaigns",
    response_model=list[Campaign],
    dependencies=[Depends(get_current_account)],
)
async def list_campaigns(tenant_id: UUID) -> list[Campaign]:
    """List all campaigns for a tenant.

    Args:
        tenant_id (UUID): Tenant identifier.

    Returns:
        list[Campaign]: Campaigns belonging to the tenant.
    """

    return campaign_service.list_campaigns(tenant_id)



@app.post(
    "/internal/campaigns/{campaign_id}/start",
    response_model=Campaign,
    dependencies=[Depends(get_current_account)],
)
async def start_campaign(campaign_id: UUID) -> Campaign:
    """Start or restart a campaign.

    Args:
        campaign_id (UUID): Identifier of the campaign to start.

    Returns:
        Campaign: The updated campaign with running status.
    """
    
    campaign = campaign_service.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Update campaign status using the service
    campaign.status = "running"
    campaign.updated_at = datetime.now(timezone.utc)
    # Note: This would need to be implemented in campaign_service.update_campaign()
    # For now, we'll just update the local object and manage state
    
    _campaign_active[campaign_id] = True
    if not scheduler.get_job(str(campaign_id)):
        schedule_campaign(campaign)
    return campaign


@app.post(
    "/internal/campaigns/{campaign_id}/pause",
    response_model=Campaign,
    dependencies=[Depends(get_current_account)],
)
async def pause_campaign(campaign_id: UUID) -> Campaign:
    """Pause a running campaign.

    Args:
        campaign_id (UUID): Identifier of the campaign to pause.

    Returns:
        Campaign: The updated campaign with paused status.
    """
    
    campaign = campaign_service.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign.status = "paused"
    campaign.updated_at = datetime.now(timezone.utc)
    # Note: This would need to be implemented in campaign_service.update_campaign()
    
    _campaign_active[campaign_id] = False
    return campaign


@app.post(
    "/internal/campaigns/{campaign_id}/resume",
    response_model=Campaign,
    dependencies=[Depends(get_current_account)],
)
async def resume_campaign(campaign_id: UUID) -> Campaign:
    """Resume a paused campaign.

    Args:
        campaign_id (UUID): Identifier of the campaign to resume.

    Returns:
        Campaign: The updated campaign with running status.
    """
    
    campaign = campaign_service.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign.status = "running"
    campaign.updated_at = datetime.now(timezone.utc)
    # Note: This would need to be implemented in campaign_service.update_campaign()
    
    _campaign_active[campaign_id] = True
    if not scheduler.get_job(str(campaign_id)):
        schedule_campaign(campaign)
    return campaign


@app.post(
    "/internal/campaigns/{campaign_id}/stop",
    response_model=Campaign,
    dependencies=[Depends(get_current_account)],
)
async def stop_campaign(campaign_id: UUID) -> Campaign:
    """Stop a campaign and remove it from the scheduler.

    Args:
        campaign_id (UUID): Identifier of the campaign to stop.

    Returns:
        Campaign: The updated campaign with stopped status.
    """
    
    campaign = campaign_service.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign.status = "stopped"
    campaign.updated_at = datetime.now(timezone.utc)
    # Note: This would need to be implemented in campaign_service.update_campaign()
    
    _campaign_active[campaign_id] = False
    if scheduler.get_job(str(campaign_id)):
        scheduler.remove_job(str(campaign_id))
    return campaign


# Audience endpoints
@app.post(
    "/audiences/",
    response_model=Audience,
)
async def create_audience(
    payload: AudienceCreate,
    current_user: dict = Depends(get_current_user_mongo),
    request: Request = None
) -> Audience:
    """
    Create a new audience.

    Args:
        payload (AudienceCreate): Audience configuration.
        current_user: Current authenticated user
        request: Optional request object for organization context

    Returns:
        Audience: Newly created audience.
    """
    from .mongo import get_collection
    from .middleware.organization_context import get_organization_context

    audiences_collection = get_collection("audiences")
    contacts_collection = get_collection("audience_contacts")

    # Calculate size if contacts provided
    size = payload.size or (len(payload.contacts) if payload.contacts else 0)

    # Get organization ID from request header if available, otherwise use tenant_id
    org_id = get_organization_context(request) if request else None
    tenant_id = org_id or current_user.get('tenant_id') or (str(payload.tenant_id) if payload.tenant_id else str(uuid4()))
    logger.info(f"Creating audience with tenant_id: {tenant_id} (org_id from header: {org_id})")

    audience_doc = {
        "id": str(uuid4()),
        "name": payload.name,
        "description": payload.description,
        "source": payload.source,
        "tags": payload.tags or [],
        "tenant_id": tenant_id,
        "size": size,
        "status": "active",
        "metadata": {},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    
    # Insert audience
    result = await audiences_collection.insert_one(audience_doc)

    # Insert contacts if provided
    if payload.contacts:
        contact_docs = []
        for contact in payload.contacts:
            contact_doc = {
                "id": str(uuid4()),
                "audience_id": audience_doc["id"],
                "phone": contact.phone,
                "name": contact.name,
                "email": contact.email,
                "metadata": contact.metadata or {},
                "created_at": datetime.now(timezone.utc)
            }
            contact_docs.append(contact_doc)

        if contact_docs:
            await contacts_collection.insert_many(contact_docs)
    
    # Return created audience
    return Audience(**audience_doc)


@app.get(
    "/audiences/{audience_id}",
    response_model=Audience,
)
async def get_audience(
    audience_id: UUID,
    current_user: dict = Depends(get_current_user_mongo)
) -> Audience:
    """
    Get a specific audience.
    
    Args:
        audience_id (UUID): Audience identifier.
        
    Returns:
        Audience: Requested audience.
    """
    from .mongo import get_collection
    
    audiences_collection = get_collection("audiences")
    audience_doc = await audiences_collection.find_one({"id": str(audience_id)})

    if not audience_doc:
        raise HTTPException(status_code=404, detail="Audience not found")

    # Convert MongoDB _id to id and handle field types
    if '_id' in audience_doc:
        audience_doc['id'] = str(audience_doc['_id'])
        del audience_doc['_id']

    # Ensure tenant_id is a string (UUID will be converted by Pydantic)
    if 'tenant_id' in audience_doc:
        audience_doc['tenant_id'] = str(audience_doc['tenant_id'])

    return Audience(**audience_doc)


@app.get(
    "/audiences/",
    response_model=list[Audience],
)
async def list_audiences(
    request: Request,
    current_user: dict = Depends(get_current_user_mongo)
) -> list[Audience]:
    """
    List all audiences for the current organization.

    Reason: Using organization context from X-Organization-ID header
    This ensures audiences are filtered by the selected organization

    Args:
        request: FastAPI request object (contains organization context)
        current_user: Current authenticated user

    Returns:
        list[Audience]: Audiences belonging to the current organization.
    """
    from .mongo import get_collection
    from .middleware.organization_context import get_organization_context

    audiences_collection = get_collection("audiences")

    # Get organization ID from request header
    org_id = get_organization_context(request)

    # Build organization filter using tenant_id field (audiences use tenant_id)
    filter_query = {}
    if org_id:
        filter_query["tenant_id"] = org_id
        logger.info(f"Filtering audiences by organization: {org_id}")
    else:
        # Fallback: get user's primary organization or user ID
        user_tenant_id = (
            current_user.get('tenant_id') or
            current_user.get('tenantId') or
            current_user.get('id') or
            current_user.get('sub')
        )
        if user_tenant_id:
            filter_query["tenant_id"] = str(user_tenant_id)
            logger.info(f"No org context, filtering by user tenant_id: {user_tenant_id}")
        else:
            logger.warning(f"No organization or tenant context available")

    logger.info(f"Querying audiences with filter: {filter_query}")
    audience_docs = await audiences_collection.find(filter_query).sort("created_at", -1).to_list(length=None)
    logger.info(f"Found {len(audience_docs)} audience documents")

    # Convert MongoDB documents to Audience models
    audiences = []
    for doc in audience_docs:
        # Convert MongoDB _id to id and handle field types
        if '_id' in doc:
            # If there's already an 'id' field, preserve it
            if 'id' not in doc:
                doc['id'] = str(doc['_id'])
            del doc['_id']

        # Ensure tenant_id is a string (UUID will be converted by Pydantic)
        if 'tenant_id' in doc:
            doc['tenant_id'] = str(doc['tenant_id'])

        try:
            audiences.append(Audience(**doc))
            logger.debug(f"Successfully converted audience: {doc.get('id')} - {doc.get('name')}")
        except Exception as e:
            logger.warning(f"Failed to convert audience document {doc.get('id', 'unknown')}: {e}")
            logger.debug(f"Problematic document: {doc}")
            continue

    logger.info(f"Returning {len(audiences)} audiences to frontend")
    return audiences


@app.delete(
    "/audiences/{audience_id}",
)
async def delete_audience(
    audience_id: UUID,
    current_user: dict = Depends(get_current_user_mongo)
) -> Dict[str, str]:
    """
    Delete an audience and its contacts.
    
    Args:
        audience_id (UUID): Audience identifier.
        
    Returns:
        Dict[str, str]: Deletion confirmation.
    """
    from .mongo import get_collection
    
    audiences_collection = get_collection("audiences")
    contacts_collection = get_collection("audience_contacts")
    
    # Check if audience exists
    audience_doc = await audiences_collection.find_one({"id": str(audience_id)})
    if not audience_doc:
        raise HTTPException(status_code=404, detail="Audience not found")

    # Delete contacts first
    await contacts_collection.delete_many({"audience_id": str(audience_id)})

    # Delete audience
    await audiences_collection.delete_one({"id": str(audience_id)})
    
    return {"message": "Audience deleted successfully"}


@app.get(
    "/audiences/{audience_id}/contacts",
)
async def get_audience_contacts(
    audience_id: UUID,
    limit: int = Query(5, ge=1, le=100, description="Number of contacts to return"),
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get contacts from an audience.
    
    Args:
        audience_id (UUID): Audience identifier.
        limit (int): Maximum number of contacts to return (default: 5, max: 100).
        
    Returns:
        List of contact dictionaries with phone, name, and email.
    """
    from .mongo import get_collection
    
    audiences_collection = get_collection("audiences")
    contacts_collection = get_collection("audience_contacts")
    
    # Check if audience exists
    audience_doc = await audiences_collection.find_one({"id": str(audience_id)})
    if not audience_doc:
        raise HTTPException(status_code=404, detail="Audience not found")

    # Get contacts (limited to specified number)
    cursor = contacts_collection.find({"audience_id": str(audience_id)}).limit(limit)
    contacts = await cursor.to_list(length=limit)
    
    # Format contacts for response
    formatted_contacts = []
    for contact in contacts:
        formatted_contacts.append({
            "phone": contact.get("phone", ""),
            "name": contact.get("name", ""),
            "email": contact.get("email", "")
        })
    
    return {
        "contacts": formatted_contacts,
        "total": audience_doc.get("size", 0),
        "returned": len(formatted_contacts)
    }


@app.get(
    "/audiences/{audience_id}/export",
)
async def export_audience(
    audience_id: UUID,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Export audience contacts as CSV.
    
    Args:
        audience_id (UUID): Audience identifier.
        
    Returns:
        CSV file download of contacts.
    """
    from fastapi.responses import StreamingResponse
    from .mongo import get_collection
    import csv
    import io
    
    audiences_collection = get_collection("audiences")
    contacts_collection = get_collection("audience_contacts")
    
    # Check if audience exists
    audience_doc = await audiences_collection.find_one({"id": str(audience_id)})
    if not audience_doc:
        raise HTTPException(status_code=404, detail="Audience not found")

    # Get contacts
    contacts = await contacts_collection.find({"audience_id": str(audience_id)}).to_list(length=None)
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(["phone", "name", "email"])
    
    # Write contacts
    for contact in contacts:
        writer.writerow([
            contact.get("phone", ""),
            contact.get("name", ""),
            contact.get("email", "")
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=audience_{audience_id}.csv"}
    )


@app.post(
    "/audiences/upload-csv",
    response_model=Audience,
)
async def upload_csv_audience(
    request: Request,
    file: UploadFile = File(...),
    name: str = Form(...),
    description: str = Form(None),
    current_user: dict = Depends(get_current_user_mongo),
    tags: str = Form(None),
    country_code: str = Form("+233")
) -> Audience:
    """
    Create audience from CSV upload.
    
    Args:
        file: CSV file with contacts
        name: Audience name
        description: Optional description
        tags: Comma-separated tags
        
    Returns:
        Audience: Created audience with contacts.
    """
    from .mongo import get_collection
    import csv
    import io
    from typing import List

    # Read file contents once
    contents = await file.read()
    filename = (file.filename or "").lower()

    contacts: List[AudienceContact] = []

    def _format_phone_with_country_code(phone: str, country_code: str) -> str:
        """
        Format phone number with country code.

        IMPORTANT: Preserves already-formatted E.164 international numbers (e.g., +1, +44, +86).
        Only normalizes local/incomplete numbers to the specified country code.

        Examples:
        - +15551234567 (US) -> +15551234567 (preserved)
        - +447911123456 (UK) -> +447911123456 (preserved)
        - +233500603563 (Ghana) -> +233500603563 (preserved)
        - 0500603563 (local) -> +233500603563 (normalized to Ghana)
        - 233500603563 (no +) -> +233500603563 (add +)
        - 500603563 (incomplete) -> +233500603563 (add country code)
        """
        if not phone:
            return ""

        # Remove all non-digit characters except +
        normalized = "".join(c for c in phone if c.isdigit() or c == "+")

        if not normalized:
            return ""

        # Remove leading + if present for comparison
        clean_country_code = country_code.replace("+", "").strip()
        digits_only = normalized.replace("+", "")

        # PRESERVE E.164 formatted numbers (starts with + and has valid length)
        # E.164 format: + followed by 1-3 digit country code, then subscriber number
        # Total length typically 8-15 digits
        if normalized.startswith("+") and 8 <= len(digits_only) <= 15:
            # Check if it's a duplicate country code (e.g., +233+233...)
            if digits_only.startswith(clean_country_code + clean_country_code):
                # Remove duplicate country code
                return f"+{digits_only[len(clean_country_code):]}"

            # Valid E.164 format - preserve as-is
            logger.debug(f"Preserving E.164 formatted number: {normalized}")
            return normalized

        # Check if number already has the target country code (without +)
        if digits_only.startswith(clean_country_code):
            # Already has country code, just ensure it starts with +
            return f"+{digits_only}"

        # If starts with 0, it's a local number - remove 0 and add country code
        if digits_only.startswith("0"):
            return f"+{clean_country_code}{digits_only[1:]}"

        # If doesn't have any country code prefix, add the default one
        # This handles incomplete numbers like "500603563"
        return f"+{clean_country_code}{digits_only}"

    def _append_contact(phone: str, name: str | None, email: str | None) -> None:
        """Helper to normalize and append a contact if phone is non-empty."""
        phone_normalized = (phone or "").strip()
        if not phone_normalized:
            return

        # Skip 'None' string values (from Excel cells)
        if phone_normalized.lower() == 'none':
            return

        # Format phone number with country code
        phone_formatted = _format_phone_with_country_code(phone_normalized, country_code)

        # Log for debugging
        logger.info(f"Formatted phone: {phone_normalized} -> {phone_formatted}")

        contacts.append(
            AudienceContact(
                phone=phone_formatted,
                name=(name or "").strip() or None,
                email=(email or "").strip() or None,
            )
        )

    # Decide parser based on extension / content
    if filename.endswith((".xlsx", ".xls")):
        # Reason: Allow uploading Excel files directly; convert to contacts server-side.
        try:
            from io import BytesIO
            from openpyxl import load_workbook

            wb = load_workbook(BytesIO(contents), read_only=True, data_only=True)
            ws = wb.active

            rows = list(ws.iter_rows(values_only=True))
            if not rows:
                raise HTTPException(status_code=400, detail="Excel file is empty")

            headers_raw = rows[0]
            headers = [
                (str(h).strip().lower() if h is not None else "")
                for h in headers_raw
            ]

            # Map common header names
            def find_col(candidates: list[str]) -> int | None:
                for idx, header in enumerate(headers):
                    for cand in candidates:
                        if cand in header:
                            return idx
                return None

            phone_idx = find_col(["phone", "mobile", "number", "cell"])
            name_idx = find_col(["name", "full name"])
            email_idx = find_col(["email", "e-mail"])

            if phone_idx is None:
                raise HTTPException(
                    status_code=400,
                    detail="No phone number column found in Excel. Expected headers containing: phone, mobile, number, or cell.",
                )

            # Iterate data rows
            for data_row in rows[1:]:
                if not data_row:
                    continue
                phone_val = (
                    str(data_row[phone_idx]).strip()
                    if phone_idx < len(data_row) and data_row[phone_idx] is not None
                    else ""
                )
                name_val = (
                    str(data_row[name_idx]).strip()
                    if name_idx is not None
                    and name_idx < len(data_row)
                    and data_row[name_idx] is not None
                    else None
                )
                email_val = (
                    str(data_row[email_idx]).strip()
                    if email_idx is not None
                    and email_idx < len(data_row)
                    and data_row[email_idx] is not None
                    else None
                )
                _append_contact(phone_val, name_val, email_val)
        except HTTPException:
            # Re-raise structured validation errors
            raise
        except Exception as e:
            logger.error(f"Error parsing Excel audience upload: {e}")
            raise HTTPException(
                status_code=400,
                detail="Failed to parse Excel file. Please check the file format.",
            )
    else:
        # Default: treat as CSV (existing behavior)
        try:
            csv_text = contents.decode("utf-8")
        except UnicodeDecodeError:
            # Fallback for files saved with BOM or other encodings
            csv_text = contents.decode("utf-8", errors="ignore")

        csv_reader = csv.DictReader(io.StringIO(csv_text))

        # Get headers for debugging (strip whitespace and quotes)
        headers = [h.strip().strip('"').strip("'") for h in (csv_reader.fieldnames or [])]
        logger.info(f"CSV headers found: {headers}")

        row_count = 0
        for row in csv_reader:
            row_count += 1
            # Find phone field (flexible column names)
            phone_val = None
            name_val = None
            email_val = None

            # Match phone field (case-insensitive, handles quotes)
            for field in ["phone", "mobile", "number", "cell"]:
                for row_key in row.keys():
                    clean_key = row_key.strip().strip('"').strip("'").lower()
                    if field in clean_key and row[row_key]:
                        phone_val = row[row_key].strip().strip('"').strip("'")
                        break
                if phone_val:
                    break

            # Match name field (case-insensitive)
            for row_key in row.keys():
                clean_key = row_key.strip().strip('"').strip("'").lower()
                if "name" in clean_key and row[row_key]:
                    name_val = row[row_key].strip().strip('"').strip("'")
                    break

            # Match email field (case-insensitive)
            for row_key in row.keys():
                clean_key = row_key.strip().strip('"').strip("'").lower()
                if "email" in clean_key and row[row_key]:
                    email_val = row[row_key].strip().strip('"').strip("'")
                    break

            if phone_val:
                _append_contact(phone_val, name_val, email_val)

        logger.info(f"Processed {row_count} CSV rows, found {len(contacts)} valid contacts")

    if not contacts:
        # Provide helpful error message
        error_detail = "No valid contacts found in uploaded file. "
        if filename.endswith((".xlsx", ".xls")):
            error_detail += "Please ensure your Excel file has a column header containing 'phone', 'mobile', 'number', or 'cell', and that phone numbers are not empty."
        else:
            error_detail += f"CSV headers found: {headers if 'headers' in locals() else 'none'}. Please ensure your CSV has a column named 'phone', 'mobile', 'number', or 'cell' with valid phone numbers."

        logger.error(f"Audience upload failed: {error_detail}")
        raise HTTPException(
            status_code=400,
            detail=error_detail,
        )
    
    # Create audience
    tag_list = [tag.strip() for tag in tags.split(',')] if tags else []

    # Get organization ID from header (priority) or fall back to user tenant_id
    from .middleware.organization_context import get_organization_context
    org_id = get_organization_context(request)
    tenant_id = org_id or current_user.get('tenant_id', str(uuid4()))
    logger.info(f"Creating audience with tenant_id: {tenant_id} (from org_id: {org_id})")

    audience_create = AudienceCreate(
        name=name,
        description=description,
        source="csv_upload",
        tags=tag_list,
        tenant_id=UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id,
        contacts=contacts,
        size=len(contacts)
    )

    return await create_audience(audience_create, current_user, request)


@app.post(
    "/internal/kb",
    dependencies=[Depends(get_current_account)],
)
async def ingest_kb(payload: KbIngestRequest) -> Dict[str, Union[str, int]]:
    """Ingest raw text or fetch from a URL into the knowledge base."""

    if not payload.content and not payload.url:
        raise HTTPException(status_code=400, detail="content or url required")
    text = payload.content or ""
    source_type = "inline"
    uri = "inline"
    if payload.url:
        try:
            text = fetch_url(payload.url)
        except Exception as exc:  # pragma: no cover - network errors
            raise HTTPException(status_code=400, detail="failed to fetch URL") from exc
        source_type = "url"
        uri = payload.url
    source, count = kb_ingest(payload.tenant_id, text, uri, source_type)
    return {"source_id": str(source.id), "chunks": count}


@app.post(
    "/internal/kb/search",
    response_model=list[KbSearchResult],
    dependencies=[Depends(get_current_account)],
)
async def search_kb(payload: KbSearchRequest) -> list[KbSearchResult]:
    """Search knowledge base chunks using hybrid retrieval."""

    results = kb_search(payload.tenant_id, payload.query, payload.top_k)
    return [
        KbSearchResult(source_id=chunk.source_id, text=chunk.text, score=score)
        for chunk, score in results
    ]


@app.post(
    "/internal/licenses/activate",
    dependencies=[Depends(get_current_account)],
)
async def activate_license(
    tenant_id: UUID, license_key: str, features: Dict[str, Any] = None, limits: Dict[str, Any] = None
) -> Dict[str, str]:
    """Activate a license using shared library."""
    try:
        result = await license_service.activate_license(
            tenant_id=str(tenant_id),
            license_key=license_key,
            features=features or {},
            limits=limits or {},
        )
        return {"status": "activated", "license_id": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get(
    "/internal/licenses/status/{tenant_id}",
    dependencies=[Depends(get_current_account)],
)
async def license_status(tenant_id: UUID) -> dict:
    """Get license status for a tenant using shared library."""
    try:
        license_info = await license_service.get_license_info(str(tenant_id))
        if not license_info:
            raise HTTPException(status_code=404, detail="License not found")
        return {
            "tenant_id": license_info.tenant_id,
            "is_active": license_info.is_active,
            "features": license_info.features,
            "limits": license_info.limits,
            "expires_at": license_info.expires_at.isoformat()
            if license_info.expires_at
            else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/internal/licenses/verify",
    dependencies=[Depends(get_current_account)],
)
async def verify_license(
    tenant_id: UUID, agents: int = 0, channels: int = 0, minutes: float = 0.0
) -> Dict[str, Union[bool, str]]:
    """Verify if a tenant may use additional features under its license."""

    try:
        # Use shared license service for validation
        await _enforce_license(
            tenant_id,
            agents=agents,
            channels=channels,
            minutes=minutes,
        )
        return {"allowed": True}
    except HTTPException as exc:
        return {"allowed": False, "detail": exc.detail}


@app.get(
    "/internal/usage",
    dependencies=[Depends(get_current_account)],
)
async def get_usage_analytics(
    tenant_id: UUID, start_date: str = None, end_date: str = None
) -> dict:
    """Get usage analytics for a tenant using shared library."""
    try:
        # Parse dates if provided
        start_dt = None
        end_dt = None
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

        usage_data = await usage_service.get_usage(
            tenant_id=str(tenant_id), start_date=start_dt, end_date=end_dt
        )

        # Get billing records from the billing service
        from apps.shared.services.billing_service import get_billing_service
        billing_service = get_billing_service(get_database())
        billing_summary = await billing_service.get_billing_summary(
            organization_id=str(tenant_id),
            service_type="vapi"
        )

        return {
            "tenant_id": usage_data.tenant_id,
            "minutes": usage_data.minutes,
            "messages": usage_data.messages,
            "stt_calls": usage_data.stt_calls,
            "tts_calls": usage_data.tts_calls,
            "telephony_cost": usage_data.telephony_cost,
            "stt_cost": usage_data.stt_cost,
            "tts_cost": usage_data.tts_cost,
            "automation_cost": billing_summary.get("totals", {}).get("total", usage_data.automation_cost),
            "automation_calls": usage_data.automation_calls,
            "period": usage_data.period,
            "generated_at": usage_data.generated_at.isoformat()
            if usage_data.generated_at
            else None,
            # Add detailed billing breakdown
            "billing_summary": billing_summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/internal/service-accounts",
    response_model=ServiceAccount,
    dependencies=[Depends(get_current_account)],
)
async def create_service_account(payload: ServiceAccountCreate) -> ServiceAccount:
    """Create a new service account and return the token."""
    token = secrets.token_urlsafe(32)
    account = ServiceAccount(token=token, **payload.model_dump())
    return service_account_service.create_account(account)


@app.get(
    "/internal/service-accounts/{account_id}",
    response_model=ServiceAccount,
    dependencies=[Depends(get_current_account)],
)
async def get_service_account(account_id: UUID) -> ServiceAccount:
    """Retrieve a service account by ID."""
    account = service_account_service.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Service account not found")
    return account


@app.post(
    "/internal/sessions/{session_id}/handover",
    dependencies=[Depends(get_current_account)],
)
async def session_handover(
    session_id: UUID, payload: HandoverRequest
) -> Dict[str, str]:
    """Initiate a human handover for a session."""

    session_manager.handover(session_id, payload.target)
    return {"status": "transferring", "target": payload.target}


@app.get(
    "/internal/sessions/{session_id}",
    response_model=SessionStatus,
    dependencies=[Depends(get_current_account)],
)
async def session_status(session_id: UUID) -> SessionStatus:
    """Get session status."""
    log = session_manager.status(session_id)
    messages = [Message(role=r, text=t) for r, t in log.messages]
    return SessionStatus(handover_target=log.handover_target, messages=messages)


# MCP Integration Endpoints
@app.post(
    "/internal/mcp/crm/leads",
    dependencies=[Depends(get_current_account)],
)
async def create_crm_lead(tenant_id: UUID, lead_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a lead in CRM via MCP."""
    try:
        mcp_manager = get_mcp_manager()
        result = await mcp_manager.create_crm_lead(tenant_id, lead_data)

        # Emit event for analytics
        await event_bus.emit(
            EventType.CRM_LEAD_CREATED,
            {"tenant_id": str(tenant_id), "lead_data": lead_data, "result": result},
        )

        return result
    except Exception as e:
        logger.error(f"Failed to create CRM lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put(
    "/internal/mcp/crm/contacts/{contact_id}",
    dependencies=[Depends(get_current_account)],
)
async def update_crm_contact(
    tenant_id: UUID, contact_id: str, contact_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Update a contact in CRM via MCP."""
    try:
        mcp_manager = get_mcp_manager()
        result = await mcp_manager.update_crm_contact(
            tenant_id, contact_id, contact_data
        )

        # Emit event for analytics
        await event_bus.emit(
            EventType.CRM_CONTACT_UPDATED,
            {
                "tenant_id": str(tenant_id),
                "contact_id": contact_id,
                "contact_data": contact_data,
                "result": result,
            },
        )

        return result
    except Exception as e:
        logger.error(f"Failed to update CRM contact: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/internal/mcp/helpdesk/tickets",
    dependencies=[Depends(get_current_account)],
)
async def create_helpdesk_ticket(
    tenant_id: UUID, ticket_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a helpdesk ticket via MCP."""
    try:
        mcp_manager = get_mcp_manager()
        result = await mcp_manager.create_helpdesk_ticket(tenant_id, ticket_data)

        # Emit event for analytics
        await event_bus.emit(
            EventType.HELPDESK_TICKET_CREATED,
            {"tenant_id": str(tenant_id), "ticket_data": ticket_data, "result": result},
        )

        return result
    except Exception as e:
        logger.error(f"Failed to create helpdesk ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/internal/mcp/payments/process",
    dependencies=[Depends(get_current_account)],
)
async def process_payment(
    tenant_id: UUID, payment_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Process a payment via MCP."""
    try:
        mcp_manager = get_mcp_manager()
        result = await mcp_manager.process_payment(tenant_id, payment_data)

        # Emit event for analytics
        await event_bus.emit(
            EventType.PAYMENT_PROCESSED,
            {
                "tenant_id": str(tenant_id),
                "payment_data": payment_data,
                "result": result,
            },
        )

        return result
    except Exception as e:
        logger.error(f"Failed to process payment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Additional MCP Integration Endpoints
@app.post(
    "/internal/mcp/email/send",
    dependencies=[Depends(get_current_account)],
)
async def send_email(tenant_id: UUID, email_data: Dict[str, Any]) -> Dict[str, Any]:
    """Send an email via MCP."""
    try:
        mcp_manager = get_mcp_manager()
        result = await mcp_manager.send_email(tenant_id, email_data)

        # Emit event for analytics
        await event_bus.emit(
            EventType.EMAIL_SENT,
            {"tenant_id": str(tenant_id), "email_data": email_data, "result": result},
        )

        return result
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/internal/mcp/sms/send",
    dependencies=[Depends(get_current_account)],
)
async def send_sms(tenant_id: UUID, sms_data: Dict[str, Any]) -> Dict[str, Any]:
    """Send an SMS via MCP."""
    try:
        mcp_manager = get_mcp_manager()
        result = await mcp_manager.send_sms(tenant_id, sms_data)

        # Emit event for analytics
        await event_bus.emit(
            EventType.SMS_SENT,
            {"tenant_id": str(tenant_id), "sms_data": sms_data, "result": result},
        )

        return result
    except Exception as e:
        logger.error(f"Failed to send SMS: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/internal/mcp/calendar/create-event",
    dependencies=[Depends(get_current_account)],
)
async def create_calendar_event(
    tenant_id: UUID, event_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a calendar event via MCP."""
    try:
        mcp_manager = get_mcp_manager()
        result = await mcp_manager.create_calendar_event(tenant_id, event_data)

        # Emit event for analytics
        await event_bus.emit(
            EventType.CALENDAR_EVENT_CREATED,
            {"tenant_id": str(tenant_id), "event_data": event_data, "result": result},
        )

        return result
    except Exception as e:
        logger.error(f"Failed to create calendar event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/internal/mcp/calendar/events",
    dependencies=[Depends(get_current_account)],
)
async def list_calendar_events(
    tenant_id: UUID, start_date: str = None, end_date: str = None
) -> Dict[str, Any]:
    """List calendar events via MCP."""
    try:
        mcp_manager = get_mcp_manager()
        result = await mcp_manager.list_calendar_events(tenant_id, start_date, end_date)
        return result
    except Exception as e:
        logger.error(f"Failed to list calendar events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/internal/mcp/documents/upload",
    dependencies=[Depends(get_current_account)],
)
async def upload_document(
    tenant_id: UUID, document_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Upload a document via MCP."""
    try:
        mcp_manager = get_mcp_manager()
        result = await mcp_manager.upload_document(tenant_id, document_data)

        # Emit event for analytics
        await event_bus.emit(
            EventType.DOCUMENT_UPLOADED,
            {
                "tenant_id": str(tenant_id),
                "document_data": document_data,
                "result": result,
            },
        )

        return result
    except Exception as e:
        logger.error(f"Failed to upload document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/internal/mcp/documents/list",
    dependencies=[Depends(get_current_account)],
)
async def list_documents(tenant_id: UUID, folder_id: str = None) -> Dict[str, Any]:
    """List documents via MCP."""
    try:
        mcp_manager = get_mcp_manager()
        result = await mcp_manager.list_documents(tenant_id, folder_id)
        return result
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/internal/mcp/analytics/track",
    dependencies=[Depends(get_current_account)],
)
async def track_analytics(
    tenant_id: UUID, analytics_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Track analytics event via MCP."""
    try:
        mcp_manager = get_mcp_manager()
        result = await mcp_manager.track_analytics(tenant_id, analytics_data)
        return result
    except Exception as e:
        logger.error(f"Failed to track analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/internal/mcp/analytics/report",
    dependencies=[Depends(get_current_account)],
)
async def get_analytics_report(
    tenant_id: UUID, report_type: str, start_date: str = None, end_date: str = None
) -> Dict[str, Any]:
    """Get analytics report via MCP."""
    try:
        mcp_manager = get_mcp_manager()
        result = await mcp_manager.get_analytics_report(
            tenant_id, report_type, start_date, end_date
        )
        return result
    except Exception as e:
        logger.error(f"Failed to get analytics report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/internal/mcp/ai/generate",
    dependencies=[Depends(get_current_account)],
)
async def generate_ai_content(
    tenant_id: UUID, generation_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate AI content via MCP."""
    try:
        mcp_manager = get_mcp_manager()
        result = await mcp_manager.generate_ai_content(tenant_id, generation_data)

        # Emit event for analytics
        await event_bus.emit(
            EventType.AI_CONTENT_GENERATED,
            {
                "tenant_id": str(tenant_id),
                "generation_data": generation_data,
                "result": result,
            },
        )

        return result
    except Exception as e:
        logger.error(f"Failed to generate AI content: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/internal/mcp/ai/analyze",
    dependencies=[Depends(get_current_account)],
)
async def analyze_with_ai(
    tenant_id: UUID, analysis_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Analyze content with AI via MCP."""
    try:
        mcp_manager = get_mcp_manager()
        result = await mcp_manager.analyze_with_ai(tenant_id, analysis_data)
        return result
    except Exception as e:
        logger.error(f"Failed to analyze with AI: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Payment endpoints
@app.get(
    "/internal/payments/methods",
    dependencies=[Depends(get_current_account)],
)
async def get_payment_methods(tenant_id: UUID, currency: str = "USD") -> Dict[str, Any]:
    """Get available payment methods for a tenant."""
    try:
        methods = await payment_service.get_available_payment_methods(
            tenant_id, currency
        )
        return {"methods": [method.dict() for method in methods], "currency": currency}
    except Exception as e:
        logger.error(f"Failed to get payment methods: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/internal/payments/deposit",
    dependencies=[Depends(get_current_account)],
)
async def create_deposit(
    tenant_id: UUID,
    amount: float,
    currency: str,
    payment_method_id: str,
    description: str = None,
    metadata: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """Create a deposit transaction."""
    try:
        from decimal import Decimal

        transaction = await payment_service.create_deposit_transaction(
            tenant_id=tenant_id,
            amount=Decimal(str(amount)),
            currency=currency,
            payment_method_id=payment_method_id,
            description=description,
            metadata=metadata,
        )
        return transaction.dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create deposit: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/internal/payments/mobile-money",
    dependencies=[Depends(get_current_account)],
)
async def process_mobile_money_payment(
    tenant_id: UUID, transaction_id: str, phone_number: str, provider: str
) -> Dict[str, Any]:
    """Process mobile money payment."""
    try:
        # In a real implementation, you would get the transaction from the database
        from decimal import Decimal
        from .services.payment_service import Transaction

        # Mock transaction for demo
        transaction = Transaction(
            id=transaction_id,
            tenant_id=tenant_id,
            amount=Decimal("50.00"),
            currency="USD",
            payment_method="momo_ghana",
            status="pending",
            transaction_type="deposit",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        result = await payment_service.process_mobile_money_payment(
            transaction=transaction, phone_number=phone_number, provider=provider
        )
        return result
    except Exception as e:
        logger.error(f"Failed to process mobile money payment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# License Management Endpoints
@app.get(
    "/internal/licenses/status/{tenant_id}",
    dependencies=[Depends(get_current_account)],
)
async def get_license_status(tenant_id: UUID) -> Dict[str, Any]:
    """Get license status for a tenant."""
    try:
        license_info = await license_service.get_license_status(str(tenant_id))
        return {
            "tenant_id": str(tenant_id),
            "is_active": license_info.is_active,
            "features": license_info.features,
            "limits": license_info.limits,
            "expires_at": license_info.expires_at.isoformat()
            if license_info.expires_at
            else None,
        }
    except Exception as e:
        logger.error(f"Failed to get license status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get license status")


@app.post(
    "/internal/licenses/verify",
    dependencies=[Depends(get_current_account)],
)
async def verify_license(
    tenant_id: UUID, agents: int = 0, channels: int = 0, minutes: int = 0
) -> Dict[str, Any]:
    """Verify license for specific features."""
    try:
        result = await license_service.verify_license(
            tenant_id=str(tenant_id), agents=agents, channels=channels, minutes=minutes
        )
        return {"allowed": result.allowed, "detail": result.detail}
    except Exception as e:
        logger.error(f"Failed to verify license: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to verify license")


@app.post(
    "/internal/licenses/activate",
    dependencies=[Depends(get_current_account)],
)
async def activate_license(
    tenant_id: UUID,
    license_key: str,
    features: Dict[str, Any] = None,
    limits: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """Activate a license for a tenant."""
    try:
        result = await license_service.activate_license(
            tenant_id=str(tenant_id),
            license_key=license_key,
            features=features or {},
            limits=limits or {},
        )
        return {"status": "activated", "license_id": result.license_id}
    except Exception as e:
        logger.error(f"Failed to activate license: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to activate license")


@app.post(
    "/internal/payments/webhooks/{provider}",
)
async def process_payment_webhook(
    provider: str, payload: Dict[str, Any], signature: str = None
) -> Dict[str, Any]:
    """Process payment webhook from provider."""
    try:
        result = await payment_service.process_webhook(
            provider=provider, payload=payload, signature=signature
        )
        return result
    except Exception as e:
        logger.error(f"Failed to process payment webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/internal/payments/wallet/{tenant_id}",
    dependencies=[Depends(get_current_account)],
)
async def get_wallet_balance(tenant_id: UUID) -> Dict[str, Any]:
    """Get wallet balance for a tenant."""
    try:
        wallet = await payment_service.get_wallet_balance(tenant_id)
        return wallet.dict()
    except Exception as e:
        logger.error(f"Failed to get wallet balance: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get wallet balance")


@app.post(
    "/internal/payments/mobile-money",
    dependencies=[Depends(get_current_account)],
)
async def process_mobile_money_payment(
    phone_number: str,
    amount: float,
    provider: str = "momo_ghana",
    tenant_id: UUID = None,
) -> Dict[str, Any]:
    """Process mobile money payment."""
    try:
        if not payment_service:
            raise HTTPException(status_code=503, detail="Payment service not available")

        # Create transaction data
        transaction_data = {
            "phone_number": phone_number,
            "amount": amount,
            "provider": provider,
            "tenant_id": str(tenant_id) if tenant_id else None,
        }

        # Use payment service to process mobile money payment
        result = await payment_service.process_mobile_money_payment(transaction_data)

        return {
            "transaction_id": result.get("transaction_id"),
            "status": result.get("status"),
            "reference": result.get("reference"),
        }
    except Exception as e:
        logger.error(f"Failed to process mobile money payment: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to process mobile money payment"
        )


@app.post(
    "/internal/payments/stripe/checkout",
    dependencies=[Depends(get_current_account)],
)
async def create_stripe_checkout(
    minutes: int, price: float, tier: str, tenant_id: UUID = None
) -> Dict[str, Any]:
    """Create a Stripe checkout session for purchasing minutes."""
    try:
        if not payment_service:
            raise HTTPException(status_code=503, detail="Payment service not available")

        # Create checkout session data
        checkout_data = {
            "minutes": minutes,
            "price": price,
            "tier": tier,
            "tenant_id": str(tenant_id) if tenant_id else None,
        }

        # Use payment service to create checkout session
        result = await payment_service.create_stripe_checkout_session(checkout_data)

        return {
            "url": result.get("url"),
            "session_id": result.get("session_id"),
            "status": "created",
        }
    except Exception as e:
        logger.error(f"Failed to create Stripe checkout: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


# Initialize MCP manager on startup
@app.on_event("startup")
async def startup_event():
    """Initialize MCP manager and run tests on startup."""
    # These would come from environment variables in production
    dev_platform_url = "http://localhost:8001"  # Developer Platform URL
    service_token = "your-service-token"  # Service token for Core->Dev Platform

    init_mcp_manager(dev_platform_url, service_token)

    # Initialize tool call logger indexes (TTL indexes for auto-cleanup)
    # Reason: Ensure MongoDB TTL indexes are created on startup for automatic data retention
    try:
        from backend.services.tool_call_logger import tool_call_logger
        await tool_call_logger.ensure_indexes()
        logger.info("✅ Tool call logger indexes initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize tool call logger indexes: {e}")

    # Initialize alert system indexes
    # Reason: Optimize alert queries and enable TTL cleanup for old alerts
    try:
        from apps.shared.services.alert_indexes import create_alert_indexes
        from .mongo import get_database
        result = await create_alert_indexes(get_database())
        if result.get("success"):
            logger.info("✅ Alert system indexes initialized")
        else:
            logger.warning(f"⚠️  Alert indexes partially created: {result.get('error')}")
    except Exception as e:
        logger.error(f"❌ Failed to initialize alert indexes: {e}")

    # Initialize voice library indexes
    # Reason: Create MongoDB indexes for voice library collections
    try:
        from apps.shared.services.voice_library_service import get_voice_library_service
        voice_library_service = get_voice_library_service()
        await voice_library_service.initialize()
        logger.info("✅ Voice library indexes initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize voice library indexes: {e}")

    # Resume running campaigns after server restart
    # Reason: Ensure campaigns continue running even after server restarts
    try:
        from backend.services.campaign_execution_service import resume_running_campaigns
        await resume_running_campaigns()
        logger.info("✅ Running campaigns resumed")
    except Exception as e:
        logger.error(f"❌ Failed to resume running campaigns: {e}")

    # Initialize TTS Provider Service with billing and health monitoring
    # Reason: Enable comprehensive TTS service with automatic billing, health monitoring, and provider failover
    global tts_provider_service
    try:
        tts_provider_service = TTSProviderService(
            enable_billing=False,  # TODO: Enable after testing (set to True for production)
            enable_health_monitoring=True,
            enable_email_alerts=True,
            cache_ttl=30
        )
        await tts_provider_service.initialize()
        logger.info("✅ TTS Provider Service initialized (billing: disabled, health monitoring: enabled)")
    except Exception as e:
        logger.error(f"❌ Failed to initialize TTS Provider Service: {e}")
        logger.warning("⚠️  Voice Agent will not have access to comprehensive TTS service")

    # Run startup tests
    try:
        from backend.services.vapi_test_runner import test_runner
        await test_runner.run_startup_tests()
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to run startup tests: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup services on shutdown."""
    global tts_provider_service

    # Shutdown TTS Provider Service
    if tts_provider_service:
        try:
            await tts_provider_service.shutdown()
            logger.info("✅ TTS Provider Service shut down gracefully")
        except Exception as e:
            logger.error(f"❌ Error shutting down TTS Provider Service: {e}")


@app.post(
    "/deploy-demo",
)
async def deploy_demo(payload: DemoDeployRequest, current_user: dict = Depends(get_current_user_mongo)) -> Dict[str, Any]:
    """Deploy a demo HTML file to the ailabsafrica server."""
    try:
        import os
        from pathlib import Path

        # Log the demo deployment request
        user_email = current_user.get("email", "unknown")
        logger.info(f"Demo deployment requested by user: {user_email}, filename: {payload.fileName}")

        # Define the target directory
        target_dir = Path("/var/www/ailabsafrica/demos")

        # Create the directory if it doesn't exist
        target_dir.mkdir(parents=True, exist_ok=True)

        # Create the full file path
        file_path = target_dir / payload.fileName

        # Validate filename to prevent directory traversal
        if ".." in payload.fileName or "/" in payload.fileName:
            return {"success": False, "error": "Invalid filename"}

        # Write the HTML content to the file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(payload.html)

        logger.info(f"Demo deployed successfully: {file_path}")

        # Construct the demo URL
        demo_url = f"http://voice-demos.ailabsafrica.com/{payload.fileName}"

        return {"success": True, "demoUrl": demo_url, "filePath": str(file_path)}

    except PermissionError as e:
        logger.error(f"Permission denied when deploying demo: {e}")
        return {"success": False, "error": "Failed to create file: Permission denied"}
    except Exception as e:
        logger.error(f"Failed to deploy demo: {e}")
        return {"success": False, "error": f"Failed to create file: {str(e)}"}
