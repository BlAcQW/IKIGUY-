"""
QuickBooks Online API endpoints.

Handles OAuth flow, connection management, and invoice sync.
"""

import logging
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import settings
from app.core.auth import get_organization_context
from app.core.database import get_database
from app.models.quickbooks import QBOConnectionStatus, QBOSyncResult
from app.services.qbo_sync_service import QBOSyncService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/quickbooks", tags=["quickbooks"])

# Frontend URL for OAuth redirects
FRONTEND_URL = "http://localhost:5173"


def get_qbo_service(
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> QBOSyncService:
    """Dependency to get QBO sync service."""
    return QBOSyncService(db)


@router.get("/auth-url")
async def get_auth_url(
    org_context: Dict[str, str] = Depends(get_organization_context),
    qbo_service: QBOSyncService = Depends(get_qbo_service),
) -> Dict[str, str]:
    """
    Get QBO OAuth authorization URL.

    Returns the URL to redirect the user to for QBO authorization.
    """
    try:
        auth_url = qbo_service.get_auth_url(org_context["organization_id"])
        return {"auth_url": auth_url}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/callback")
async def oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    realmId: str = Query(...),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> RedirectResponse:
    """
    OAuth callback from Intuit.

    No JWT auth — security comes from HMAC-signed state parameter.
    Redirects to frontend Settings page with success/error query param.
    """
    qbo_service = QBOSyncService(db)
    try:
        await qbo_service.handle_callback(code, state, realmId)
        return RedirectResponse(
            url=f"{FRONTEND_URL}/settings?qbo=connected",
            status_code=status.HTTP_302_FOUND,
        )
    except ValueError as e:
        logger.error("QBO OAuth callback failed: %s", e)
        return RedirectResponse(
            url=f"{FRONTEND_URL}/settings?qbo=error",
            status_code=status.HTTP_302_FOUND,
        )
    except Exception as e:
        logger.exception("QBO OAuth callback error")
        return RedirectResponse(
            url=f"{FRONTEND_URL}/settings?qbo=error",
            status_code=status.HTTP_302_FOUND,
        )


@router.get("/status", response_model=QBOConnectionStatus)
async def get_connection_status(
    org_context: Dict[str, str] = Depends(get_organization_context),
    qbo_service: QBOSyncService = Depends(get_qbo_service),
) -> QBOConnectionStatus:
    """Get QBO connection status for the current organization."""
    return await qbo_service.get_connection_status(
        org_context["organization_id"]
    )


@router.post("/disconnect")
async def disconnect_qbo(
    org_context: Dict[str, str] = Depends(get_organization_context),
    qbo_service: QBOSyncService = Depends(get_qbo_service),
) -> Dict[str, str]:
    """Disconnect QBO for the current organization."""
    try:
        await qbo_service.disconnect(org_context["organization_id"])
        return {"message": "QuickBooks disconnected successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/sync", response_model=QBOSyncResult)
async def sync_all_invoices(
    org_context: Dict[str, str] = Depends(get_organization_context),
    qbo_service: QBOSyncService = Depends(get_qbo_service),
) -> QBOSyncResult:
    """Sync all unsynced invoices to QBO."""
    try:
        return await qbo_service.sync_all_unsynced(
            org_context["organization_id"]
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/sync/{invoice_id}")
async def sync_single_invoice(
    invoice_id: str,
    org_context: Dict[str, str] = Depends(get_organization_context),
    qbo_service: QBOSyncService = Depends(get_qbo_service),
) -> Dict[str, str]:
    """Sync a single invoice to QBO."""
    try:
        result = await qbo_service.sync_invoice(
            org_context["organization_id"], invoice_id
        )
        return {
            "message": "Invoice synced to QuickBooks",
            "qbo_invoice_id": result["qbo_invoice_id"],
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}",
        )
