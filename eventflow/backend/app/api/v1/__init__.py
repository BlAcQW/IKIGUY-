"""
API v1 router.
"""

from fastapi import APIRouter
from .auth import router as auth_router
from .events import router as events_router
from .tasks import router as tasks_router
from .responsible_persons import router as persons_router
from .wallet import router as wallet_router
from .voice import router as voice_router
from .notifications import router as notifications_router
from .analytics import router as analytics_router
from .organizations import router as organizations_router
from .feedback import router as feedback_router
from .tts import router as tts_router
from .asr import router as asr_router
from .voice_settings import router as voice_settings_router
from .llm import router as llm_router
from .dashboard import router as dashboard_router
from ..routes.voice_library import router as voice_library_router

# Create main v1 router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(auth_router)
api_router.include_router(dashboard_router)
api_router.include_router(organizations_router)
api_router.include_router(events_router)
api_router.include_router(tasks_router)
api_router.include_router(persons_router)
api_router.include_router(wallet_router)
api_router.include_router(voice_router)
api_router.include_router(tts_router)
api_router.include_router(asr_router)
api_router.include_router(voice_settings_router)
api_router.include_router(voice_library_router, prefix="/voice-library", tags=["Voice Library"])
api_router.include_router(llm_router)
api_router.include_router(notifications_router)
api_router.include_router(analytics_router)
api_router.include_router(feedback_router)
