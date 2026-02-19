"""
Main voice engine router that combines all voice-related route modules.
"""

import logging
from fastapi import APIRouter

# Import all route modules
from .core_routes import router as core_router
from .llm_routes import router as llm_router
from .voice_routes import voice_management_routers
from .assistant_routes import router as assistant_router
from .chat_routes import router as chat_router
from .websocket_chat import router as websocket_router
from .websocket_v2 import router as websocket_v2_router  # Phase 3: VoicePipeline-based WebSocket
from .pstn_routes import router as pstn_router
from .sip_routes import router as sip_router
from .training_routes import router as training_router
from .vapi_integration import router as vapi_router
from .phone_numbers import router as phone_numbers_router

logger = logging.getLogger(__name__)

# Create main voice engine router
router = APIRouter(prefix="/voice", tags=["voice"])

# Include all sub-routers
router.include_router(core_router)
router.include_router(llm_router)
router.include_router(assistant_router)
router.include_router(chat_router)
router.include_router(websocket_router)
router.include_router(websocket_v2_router)  # Phase 3: VoicePipeline-based WebSocket v2
router.include_router(pstn_router)
router.include_router(sip_router)
router.include_router(training_router)
router.include_router(vapi_router)
router.include_router(phone_numbers_router)

# Include voice management routers (providers and voices)
for voice_router in voice_management_routers:
    router.include_router(voice_router)

logger.info("Voice engine router initialized with all sub-modules")