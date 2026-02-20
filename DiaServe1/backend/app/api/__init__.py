"""
API routes package.

Main API router that includes all sub-routers.
Standalone version - no external shared dependencies.
"""

from fastapi import APIRouter

# Import routers
from app.api.properties.router import router as properties_router
from app.api.bookings.router import router as bookings_router
from app.api.search.router import router as search_router
from app.api.documents.router import router as documents_router
from app.api.invoices.router import router as invoices_router
from app.api.payments.router import router as payments_router
from app.api.organizations.router import router as organizations_router
from app.api.users.router import router as users_router
from app.api.upload.router import router as upload_router
from app.api.storage.router import router as storage_router

# Optional routers - import with error handling
try:
    from app.api.chat.router import router as chat_router
    HAS_CHAT = True
except ImportError:
    HAS_CHAT = False

try:
    from app.api.agents.router import router as agents_router
    HAS_AGENTS = True
except ImportError:
    HAS_AGENTS = False

try:
    from app.api.system.router import router as system_router
    HAS_SYSTEM = True
except ImportError:
    HAS_SYSTEM = False

try:
    from app.api.campaigns.router import router as campaigns_router
    HAS_CAMPAIGNS = True
except ImportError:
    HAS_CAMPAIGNS = False

try:
    from app.api.voice.router import router as voice_router
    HAS_VOICE = True
except ImportError:
    HAS_VOICE = False

try:
    from app.api.ai_tools.router import router as ai_tools_router
    HAS_AI_TOOLS = True
except ImportError:
    HAS_AI_TOOLS = False


api_router = APIRouter()

# Include sub-routers
api_router.include_router(properties_router, tags=["properties"])
api_router.include_router(bookings_router, tags=["bookings"])
api_router.include_router(search_router, tags=["search"])
api_router.include_router(documents_router, tags=["documents"])
api_router.include_router(invoices_router, tags=["invoices"])
api_router.include_router(payments_router, tags=["payments"])
api_router.include_router(organizations_router, tags=["organizations"])
api_router.include_router(users_router, tags=["users"])
api_router.include_router(upload_router, prefix="/upload", tags=["upload"])
api_router.include_router(storage_router, prefix="/storage", tags=["storage"])

# Optional routers
if HAS_CHAT:
    api_router.include_router(chat_router, tags=["chat"])
if HAS_AGENTS:
    api_router.include_router(agents_router, tags=["agents"])
if HAS_SYSTEM:
    api_router.include_router(system_router, tags=["system"])
if HAS_CAMPAIGNS:
    api_router.include_router(campaigns_router, tags=["campaigns"])
if HAS_VOICE:
    api_router.include_router(voice_router, tags=["voice"])
if HAS_AI_TOOLS:
    api_router.include_router(ai_tools_router, tags=["ai-tools"])


@api_router.get("/")
async def api_root():
    """
    API root endpoint.

    Returns:
        dict: API information
    """
    return {
        "message": "EstateFlow API v1",
        "endpoints": {
            "properties": "/api/v1/properties",
            "bookings": "/api/v1/bookings",
            "search": "/api/v1/search",
            "documents": "/api/v1/documents",
            "invoices": "/api/v1/invoices",
            "payments": "/api/v1/payments",
            "organizations": "/api/v1/organizations",
            "users": "/api/v1/users",
            "auth": "/api/v1/auth",
            "voice": "/api/v1/voice",
            "ai": "/api/v1/ai",
        }
    }
