"""
API routes package.

Main API router that includes all sub-routers.
"""

from fastapi import APIRouter
from app.api.properties.router import router as properties_router
from app.api.chat.router import router as chat_router
from app.api.bookings.router import router as bookings_router
from app.api.agents.router import router as agents_router
from app.api.search.router import router as search_router
from app.api.documents.router import router as documents_router
from app.api.invoices.router import router as invoices_router
from app.api.payments.router import router as payments_router
from app.api.organizations.router import router as organizations_router
from app.api.users.router import router as users_router
from app.api.upload.router import router as upload_router
from app.api.storage.router import router as storage_router
from app.api.system.router import router as system_router

# Import centralized campaign router from shared
from shared.routers.campaign_router import get_campaign_router
from app.core.database import get_database
from app.core.auth import get_current_user, get_organization_context

api_router = APIRouter()

# Get centralized campaign router (plug-and-play integration)
campaigns_router = get_campaign_router(
    get_database_func=get_database,
    get_current_user_func=get_current_user,
    get_org_context_func=get_organization_context,
    prefix="/campaigns"
)

# Include sub-routers
api_router.include_router(properties_router, tags=["properties"])
api_router.include_router(chat_router, tags=["chat"])
api_router.include_router(campaigns_router, tags=["campaigns"])  # Now using centralized router
api_router.include_router(bookings_router, tags=["bookings"])
api_router.include_router(agents_router, tags=["agents"])
api_router.include_router(search_router, tags=["search"])
api_router.include_router(documents_router, tags=["documents"])
api_router.include_router(invoices_router, tags=["invoices"])
api_router.include_router(payments_router, tags=["payments"])
api_router.include_router(organizations_router, tags=["organizations"])
api_router.include_router(users_router, tags=["users"])
api_router.include_router(upload_router, prefix="/upload", tags=["upload"])
api_router.include_router(storage_router, prefix="/storage", tags=["storage"])
api_router.include_router(system_router, tags=["system"])

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
            "chat": "/api/v1/chat/properties/{property_id}",
            "listings": "/api/v1/listings",
            "campaigns": "/api/v1/campaigns",
            "bookings": "/api/v1/bookings",
            "invoices": "/api/v1/invoices",
            "payments": "/api/v1/payments",
            "system": "/api/v1/system",
        }
    }
