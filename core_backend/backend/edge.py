"""Edge node synchronization endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends

from .auth import get_current_account
from .models import EdgeSyncResponse
from .services.license_service import LicenseService

router = APIRouter(prefix="/internal/edge", dependencies=[Depends(get_current_account)])

# Initialize shared license service
license_service = LicenseService()


@router.get("/sync", response_model=EdgeSyncResponse)
async def sync_edge(tenant_id: UUID) -> EdgeSyncResponse:
    """Return license and capabilities for an edge node using shared library."""

    try:
        license_info = await license_service.get_license_info(str(tenant_id))
        license_data = None
        if license_info:
            license_data = {
                "tenant_id": license_info.tenant_id,
                "is_active": license_info.is_active,
                "features": license_info.features,
                "limits": license_info.limits,
                "expires_at": license_info.expires_at.isoformat() if license_info.expires_at else None
            }
    except Exception:
        license_data = None
    
    return EdgeSyncResponse(
        license=license_data, capabilities=["usage_export", "usage_import"]
    )
