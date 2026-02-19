"""
Centralized Campaign Router

Plug-and-play FastAPI router for complete campaign functionality.
Apps can import this router and mount it to get instant campaign capabilities.

Usage in any app:
    from shared.routers.campaign_router import get_campaign_router
    from app.core.database import get_database
    from app.core.auth import get_current_user, get_organization_context

    campaign_router = get_campaign_router(
        get_database_func=get_database,
        get_current_user_func=get_current_user,
        get_org_context_func=get_organization_context
    )

    app.include_router(campaign_router, prefix="/api/v1")
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from typing import List, Optional, Callable
import logging
import io

import sys
sys.path.insert(0, '/opt/kasaai/apps')

from shared.models.campaign import (
    Campaign,
    CampaignCreate,
    CampaignUpdate,
    CampaignListResponse,
    CampaignFilters,
    CampaignAnalytics,
    SegmentPreview,
    SegmentFilter,
    CampaignType,
    CampaignStatus
)
from shared.models.contact import (
    Contact,
    ContactCreate,
    ContactUpdate,
    ContactListResponse,
    ContactFilters,
    ContactImportResult,
    ContactStats
)
from shared.services.unified_campaign_service import UnifiedCampaignService
from shared.services.contact_service import ContactService

logger = logging.getLogger(__name__)


def get_campaign_router(
    get_database_func: Callable,
    get_current_user_func: Callable,
    get_org_context_func: Callable,
    prefix: str = "/campaigns"
) -> APIRouter:
    """
    Get a configured campaign router for an app.

    Args:
        get_database_func: Function to get database instance
        get_current_user_func: Function to get current user (auth dependency)
        get_org_context_func: Function to get organization context
        prefix: Router prefix (default: "/campaigns")

    Returns:
        Configured FastAPI router with all campaign endpoints
    """
    router = APIRouter(prefix=prefix, tags=["campaigns"])

    # ==================== Campaign Endpoints ====================

    @router.post("", response_model=Campaign, status_code=status.HTTP_201_CREATED)
    async def create_campaign(
        campaign_data: CampaignCreate,
        user=Depends(get_current_user_func),
        org_context=Depends(get_org_context_func)
    ):
        """Create a new marketing campaign."""
        db = get_database_func()
        campaign_service = UnifiedCampaignService(db)

        try:
            campaign = await campaign_service.create_campaign(
                campaign_data=campaign_data,
                organization_id=org_context["organization_id"],
                user_id=user["sub"]
            )
            logger.info(f"Campaign {campaign.id} created by user {user['sub']}")
            return campaign

        except Exception as e:
            logger.error(f"Error creating campaign: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create campaign: {str(e)}"
            )

    @router.get("", response_model=CampaignListResponse)
    async def list_campaigns(
        campaign_type: Optional[CampaignType] = Query(None),
        status_filter: Optional[CampaignStatus] = Query(None, alias="status"),
        limit: int = Query(20, ge=1, le=100),
        offset: int = Query(0, ge=0),
        user=Depends(get_current_user_func),
        org_context=Depends(get_org_context_func)
    ):
        """List campaigns for the organization."""
        db = get_database_func()
        campaign_service = UnifiedCampaignService(db)

        filters = CampaignFilters(
            campaign_type=campaign_type,
            status=status_filter,
            limit=limit,
            offset=offset
        )

        try:
            return await campaign_service.list_campaigns(
                organization_id=org_context["organization_id"],
                filters=filters
            )
        except Exception as e:
            logger.error(f"Error listing campaigns: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    @router.get("/{campaign_id}", response_model=Campaign)
    async def get_campaign(
        campaign_id: str,
        user=Depends(get_current_user_func),
        org_context=Depends(get_org_context_func)
    ):
        """Get a specific campaign."""
        db = get_database_func()
        campaign_service = UnifiedCampaignService(db)

        campaign = await campaign_service.get_campaign(
            campaign_id=campaign_id,
            organization_id=org_context["organization_id"]
        )

        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Campaign {campaign_id} not found"
            )

        return campaign

    @router.patch("/{campaign_id}", response_model=Campaign)
    async def update_campaign(
        campaign_id: str,
        updates: CampaignUpdate,
        user=Depends(get_current_user_func),
        org_context=Depends(get_org_context_func)
    ):
        """Update a campaign."""
        db = get_database_func()
        campaign_service = UnifiedCampaignService(db)

        try:
            campaign = await campaign_service.update_campaign(
                campaign_id=campaign_id,
                organization_id=org_context["organization_id"],
                updates=updates
            )

            if not campaign:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Campaign {campaign_id} not found"
                )

            return campaign

        except Exception as e:
            logger.error(f"Error updating campaign: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    @router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_campaign(
        campaign_id: str,
        user=Depends(get_current_user_func),
        org_context=Depends(get_org_context_func)
    ):
        """Delete a campaign."""
        db = get_database_func()
        campaign_service = UnifiedCampaignService(db)

        success = await campaign_service.delete_campaign(
            campaign_id=campaign_id,
            organization_id=org_context["organization_id"]
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Campaign {campaign_id} not found"
            )

    @router.post("/{campaign_id}/launch", response_model=Campaign)
    async def launch_campaign(
        campaign_id: str,
        user=Depends(get_current_user_func),
        org_context=Depends(get_org_context_func)
    ):
        """Launch a campaign."""
        db = get_database_func()
        campaign_service = UnifiedCampaignService(db)

        try:
            campaign = await campaign_service.launch_campaign(
                campaign_id=campaign_id,
                organization_id=org_context["organization_id"]
            )
            logger.info(f"Campaign {campaign_id} launched by user {user['sub']}")
            return campaign

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Error launching campaign: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    @router.post("/{campaign_id}/pause", response_model=Campaign)
    async def pause_campaign(
        campaign_id: str,
        user=Depends(get_current_user_func),
        org_context=Depends(get_org_context_func)
    ):
        """Pause a running campaign."""
        db = get_database_func()
        campaign_service = UnifiedCampaignService(db)

        try:
            campaign = await campaign_service.pause_campaign(
                campaign_id=campaign_id,
                organization_id=org_context["organization_id"]
            )
            logger.info(f"Campaign {campaign_id} paused by user {user['sub']}")
            return campaign

        except Exception as e:
            logger.error(f"Error pausing campaign: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    @router.post("/preview-segment", response_model=SegmentPreview)
    async def preview_segment(
        campaign_type: CampaignType,
        segment_filter: Optional[SegmentFilter] = None,
        user=Depends(get_current_user_func),
        org_context=Depends(get_org_context_func)
    ):
        """Preview how many contacts match a segment filter."""
        db = get_database_func()
        campaign_service = UnifiedCampaignService(db)

        try:
            preview = await campaign_service.preview_segment(
                organization_id=org_context["organization_id"],
                segment_filter=segment_filter,
                campaign_type=campaign_type
            )
            return preview

        except Exception as e:
            logger.error(f"Error previewing segment: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    @router.get("/{campaign_id}/analytics", response_model=CampaignAnalytics)
    async def get_campaign_analytics(
        campaign_id: str,
        user=Depends(get_current_user_func),
        org_context=Depends(get_org_context_func)
    ):
        """Get campaign performance analytics."""
        db = get_database_func()
        campaign_service = UnifiedCampaignService(db)

        analytics = await campaign_service.get_campaign_analytics(
            campaign_id=campaign_id,
            organization_id=org_context["organization_id"]
        )

        if not analytics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Campaign {campaign_id} not found"
            )

        return analytics

    # ==================== Contact Endpoints ====================

    @router.post("/contacts", response_model=Contact, status_code=status.HTTP_201_CREATED)
    async def create_contact(
        contact_data: ContactCreate,
        user=Depends(get_current_user_func),
        org_context=Depends(get_org_context_func)
    ):
        """Create a new contact."""
        db = get_database_func()
        contact_service = ContactService(db)

        try:
            contact = await contact_service.create_contact(
                contact_data=contact_data,
                organization_id=org_context["organization_id"]
            )
            logger.info(f"Contact {contact.id} created by user {user['sub']}")
            return contact

        except Exception as e:
            logger.error(f"Error creating contact: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    @router.get("/contacts", response_model=ContactListResponse)
    async def list_contacts(
        contact_type: Optional[str] = Query(None),
        interest_level: Optional[str] = Query(None),
        tags: Optional[str] = Query(None),
        has_email: Optional[bool] = Query(None),
        has_phone: Optional[bool] = Query(None),
        search: Optional[str] = Query(None),
        limit: int = Query(20, ge=1, le=100),
        offset: int = Query(0, ge=0),
        user=Depends(get_current_user_func),
        org_context=Depends(get_org_context_func)
    ):
        """List contacts for the organization."""
        db = get_database_func()
        contact_service = ContactService(db)

        # Parse tags if provided
        tag_list = tags.split(",") if tags else None

        filters = ContactFilters(
            contact_type=contact_type,
            interest_level=interest_level,
            tags=tag_list,
            has_email=has_email,
            has_phone=has_phone,
            search=search,
            limit=limit,
            offset=offset
        )

        try:
            return await contact_service.list_contacts(
                organization_id=org_context["organization_id"],
                filters=filters
            )
        except Exception as e:
            logger.error(f"Error listing contacts: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    @router.get("/contacts/stats", response_model=ContactStats)
    async def get_contact_stats(
        user=Depends(get_current_user_func),
        org_context=Depends(get_org_context_func)
    ):
        """Get contact database statistics."""
        db = get_database_func()
        contact_service = ContactService(db)

        try:
            return await contact_service.get_contact_stats(
                organization_id=org_context["organization_id"]
            )
        except Exception as e:
            logger.error(f"Error getting contact stats: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    @router.get("/contacts/{contact_id}", response_model=Contact)
    async def get_contact(
        contact_id: str,
        user=Depends(get_current_user_func),
        org_context=Depends(get_org_context_func)
    ):
        """Get a specific contact."""
        db = get_database_func()
        contact_service = ContactService(db)

        contact = await contact_service.get_contact(
            contact_id=contact_id,
            organization_id=org_context["organization_id"]
        )

        if not contact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contact {contact_id} not found"
            )

        return contact

    @router.patch("/contacts/{contact_id}", response_model=Contact)
    async def update_contact(
        contact_id: str,
        updates: ContactUpdate,
        user=Depends(get_current_user_func),
        org_context=Depends(get_org_context_func)
    ):
        """Update a contact."""
        db = get_database_func()
        contact_service = ContactService(db)

        try:
            contact = await contact_service.update_contact(
                contact_id=contact_id,
                organization_id=org_context["organization_id"],
                updates=updates
            )

            if not contact:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Contact {contact_id} not found"
                )

            return contact

        except Exception as e:
            logger.error(f"Error updating contact: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    @router.delete("/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_contact(
        contact_id: str,
        user=Depends(get_current_user_func),
        org_context=Depends(get_org_context_func)
    ):
        """Delete a contact."""
        db = get_database_func()
        contact_service = ContactService(db)

        success = await contact_service.delete_contact(
            contact_id=contact_id,
            organization_id=org_context["organization_id"]
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contact {contact_id} not found"
            )

    @router.post("/contacts/import", response_model=ContactImportResult)
    async def import_contacts(
        file: UploadFile = File(...),
        update_existing: bool = Query(False),
        user=Depends(get_current_user_func),
        org_context=Depends(get_org_context_func)
    ):
        """Import contacts from CSV file."""
        db = get_database_func()
        contact_service = ContactService(db)

        # Read CSV content
        content = await file.read()
        csv_content = content.decode("utf-8")

        try:
            result = await contact_service.import_contacts(
                organization_id=org_context["organization_id"],
                csv_content=csv_content,
                update_existing=update_existing
            )
            logger.info(
                f"Imported {result.imported} contacts, "
                f"updated {result.updated}, skipped {result.skipped}"
            )
            return result

        except Exception as e:
            logger.error(f"Error importing contacts: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    return router
