"""
SMS Campaign Management Routes

This module provides API endpoints for SMS campaign operations including:
- Campaign CRUD operations
- Campaign execution (start, pause, cancel)
- Message template management
- Campaign analytics
"""

from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
import logging
import os
import asyncio
import json

from ..auth import get_current_user_mongo
from ..middleware.organization_context import (
    get_organization_context,
    validate_organization_access
)
from ..mongo import get_database

# Import SMS campaign service
import sys
sys.path.insert(0, "/opt/kasaai/apps")
from shared.services.sms_campaign_service import (
    SMSCampaignService,
    SMSCampaignStatus,
    SMSMessageStatus,
    sms_campaign_service
)
from shared.integration.sms import SMSIntegration

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sms-campaigns", tags=["sms-campaigns"])


# ==================== Request/Response Models ====================

class SMSCampaignConfigRequest(BaseModel):
    """Campaign configuration options."""
    send_rate_per_second: float = Field(default=1.0, ge=0.1, le=10.0)
    batch_size: int = Field(default=100, ge=1, le=1000)
    retry_failed: bool = True
    max_retries: int = Field(default=2, ge=0, le=5)
    sender_id: Optional[str] = None
    scheduled_time: Optional[str] = None


class SMSCampaignCreate(BaseModel):
    """Request model for creating an SMS campaign."""
    name: str = Field(..., min_length=1, max_length=255)
    template_content: str = Field(..., min_length=1, max_length=1600)
    audience_id: Optional[str] = None
    config: Optional[SMSCampaignConfigRequest] = None
    sms_provider: str = Field(default="twilio")


class SMSCampaignUpdate(BaseModel):
    """Request model for updating an SMS campaign."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    template_content: Optional[str] = Field(None, min_length=1, max_length=1600)
    audience_id: Optional[str] = None
    config: Optional[SMSCampaignConfigRequest] = None


class SMSCampaignResponse(BaseModel):
    """Response model for SMS campaign."""
    id: str
    name: str
    organization_id: str
    user_id: str
    template_content: str
    audience_id: Optional[str]
    status: str
    progress: Dict[str, Any]
    config: Dict[str, Any]
    total_cost: float
    sms_provider: str
    total_messages_sent_all_time: int = 0
    total_cost_all_time: float = 0.0
    total_runs: int = 0
    created_at: str
    updated_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    error_message: Optional[str]


class SMSCampaignListResponse(BaseModel):
    """Response model for listing campaigns."""
    campaigns: List[Dict[str, Any]]
    total: int


class SMSTemplatePreviewRequest(BaseModel):
    """Request for previewing a template."""
    template_content: str
    sample_data: Dict[str, str] = Field(default_factory=dict)


class SMSTemplatePreviewResponse(BaseModel):
    """Response for template preview."""
    rendered_content: str
    placeholders: List[str]
    character_count: int
    segment_count: int


class SMSCampaignStartRequest(BaseModel):
    """Request for starting a campaign with contacts."""
    contacts: Optional[List[Dict[str, Any]]] = None


class SMSCampaignAnalyticsResponse(BaseModel):
    """Response model for campaign analytics."""
    campaign_id: str
    name: str
    status: str
    progress: Dict[str, Any]
    cost: Dict[str, Any]
    timing: Dict[str, Any]


# ==================== Helper Functions ====================

def get_sms_service() -> SMSCampaignService:
    """Get initialized SMS campaign service."""
    # Initialize SMS provider from environment
    sms_config = {
        "providers": {
            # Primary Ghana provider: Arkesel
            "arkesel": {
                "api_key": os.getenv("ARKESEL_API_KEY", ""),
                "sender_id": os.getenv("ARKESEL_SENDER_ID", "IMPACT2025"),
            },
            # Twilio optional fallback
            "twilio": {
                "account_sid": os.getenv("TWILIO_ACCOUNT_SID", ""),
                "auth_token": os.getenv("TWILIO_AUTH_TOKEN", ""),
            },
            # Hubtel (Ghana alternative)
            "hubtel": {
                "client_id": os.getenv("HUBTEL_CLIENT_ID", ""),
                "client_secret": os.getenv("HUBTEL_CLIENT_SECRET", ""),
                "sender_id": os.getenv("HUBTEL_SENDER_ID", ""),
            },
        },
        "default_provider": "arkesel",  # Match frontend default
    }

    sms_integration = SMSIntegration(sms_config)
    sms_campaign_service.set_sms_provider(sms_integration)

    return sms_campaign_service


async def init_service_db(service: SMSCampaignService):
    """Initialize database for service if not already set."""
    if service.db is None:
        db = get_database()  # get_database() is synchronous
        service.set_database(db)


# ==================== Campaign CRUD Endpoints ====================

@router.post("/", response_model=SMSCampaignResponse)
async def create_sms_campaign(
    request: Request,
    payload: SMSCampaignCreate,
    current_user=Depends(get_current_user_mongo)
):
    """
    Create a new SMS campaign.

    Creates a campaign with message template and optional audience.
    Supports placeholders like {{name}}, {{phone}}, etc.
    """
    try:
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        organization_id = org_id or current_user.get("organization_id") or current_user.get("tenant_id")
        if not organization_id:
            raise HTTPException(status_code=400, detail="Organization ID required")

        user_id = str(current_user.get("_id", current_user.get("id", "")))

        service = get_sms_service()
        await init_service_db(service)

        config_dict = payload.config.dict() if payload.config else None

        campaign = await service.create_campaign(
            name=payload.name,
            organization_id=organization_id,
            user_id=user_id,
            template_content=payload.template_content,
            audience_id=payload.audience_id,
            config=config_dict,
            sms_provider=payload.sms_provider
        )

        logger.info(f"Created SMS campaign {campaign.id} for org {organization_id}")

        return campaign.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create SMS campaign: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create campaign: {str(e)}")


@router.get("/", response_model=SMSCampaignListResponse)
async def list_sms_campaigns(
    request: Request,
    status: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
    current_user=Depends(get_current_user_mongo)
):
    """
    List SMS campaigns for the current organization.

    Supports filtering by status and pagination.
    """
    try:
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        organization_id = org_id or current_user.get("organization_id") or current_user.get("tenant_id")
        if not organization_id:
            raise HTTPException(status_code=400, detail="Organization ID required")

        service = get_sms_service()
        await init_service_db(service)

        status_filter = SMSCampaignStatus(status) if status else None
        campaigns = await service.list_campaigns(
            organization_id=organization_id,
            status=status_filter,
            limit=limit,
            skip=skip
        )

        return {
            "campaigns": [c.to_dict() for c in campaigns],
            "total": len(campaigns)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list SMS campaigns: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list campaigns: {str(e)}")


@router.get("/{campaign_id}", response_model=SMSCampaignResponse)
async def get_sms_campaign(
    request: Request,
    campaign_id: str,
    current_user=Depends(get_current_user_mongo)
):
    """Get a specific SMS campaign by ID."""
    try:
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        service = get_sms_service()
        await init_service_db(service)

        campaign = await service.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        # Verify organization access
        organization_id = org_id or current_user.get("organization_id") or current_user.get("tenant_id")
        if campaign.organization_id != organization_id:
            raise HTTPException(status_code=403, detail="Access denied")

        return campaign.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get SMS campaign: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get campaign: {str(e)}")


@router.put("/{campaign_id}", response_model=SMSCampaignResponse)
async def update_sms_campaign(
    request: Request,
    campaign_id: str,
    payload: SMSCampaignUpdate,
    current_user=Depends(get_current_user_mongo)
):
    """Update an SMS campaign."""
    try:
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        service = get_sms_service()
        await init_service_db(service)

        campaign = await service.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        # Verify organization access
        organization_id = org_id or current_user.get("organization_id") or current_user.get("tenant_id")
        if campaign.organization_id != organization_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Cannot update running campaigns
        if campaign.status == SMSCampaignStatus.RUNNING:
            raise HTTPException(status_code=400, detail="Cannot update running campaign")

        updates = {}
        if payload.name:
            updates["name"] = payload.name
        if payload.template_content:
            updates["template_content"] = payload.template_content
        if payload.audience_id:
            updates["audience_id"] = payload.audience_id
        if payload.config:
            updates["config"] = payload.config.dict()

        updated_campaign = await service.update_campaign(campaign_id, updates)

        return updated_campaign.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update SMS campaign: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update campaign: {str(e)}")


@router.delete("/{campaign_id}")
async def delete_sms_campaign(
    request: Request,
    campaign_id: str,
    current_user=Depends(get_current_user_mongo)
):
    """Delete an SMS campaign."""
    try:
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        service = get_sms_service()
        await init_service_db(service)

        campaign = await service.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        # Verify organization access
        organization_id = org_id or current_user.get("organization_id") or current_user.get("tenant_id")
        if campaign.organization_id != organization_id:
            raise HTTPException(status_code=403, detail="Access denied")

        success = await service.delete_campaign(campaign_id)

        return {"success": success, "message": "Campaign deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete SMS campaign: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete campaign: {str(e)}")


# ==================== Campaign Execution Endpoints ====================

@router.post("/{campaign_id}/prepare")
async def prepare_campaign_messages(
    request: Request,
    campaign_id: str,
    background_tasks: BackgroundTasks,
    payload: Optional[SMSCampaignStartRequest] = None,
    current_user=Depends(get_current_user_mongo)
):
    """
    Prepare campaign messages from audience or provided contacts.

    This renders the template for each contact and stores messages.
    """
    try:
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        service = get_sms_service()
        await init_service_db(service)

        campaign = await service.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        # Verify organization access
        organization_id = org_id or current_user.get("organization_id") or current_user.get("tenant_id")
        if campaign.organization_id != organization_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Get contacts from payload or fetch from audience
        contacts = []
        if payload and payload.contacts:
            contacts = payload.contacts
        elif campaign.audience_id:
            # Fetch contacts from audience
            db = get_database()  # get_database() is synchronous
            audience_contacts_collection = db["audience_contacts"]
            cursor = audience_contacts_collection.find({"audience_id": campaign.audience_id})
            async for contact in cursor:
                contacts.append({
                    "phone": contact.get("phone", ""),
                    "name": contact.get("name", ""),
                    "email": contact.get("email", ""),
                    **contact.get("metadata", {})
                })

        if not contacts:
            raise HTTPException(status_code=400, detail="No contacts provided or audience is empty")

        message_count = await service.prepare_campaign_messages(campaign_id, contacts)

        return {
            "success": True,
            "message": f"Prepared {message_count} messages",
            "message_count": message_count
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to prepare campaign messages: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to prepare messages: {str(e)}")


@router.post("/{campaign_id}/start")
async def start_sms_campaign(
    request: Request,
    campaign_id: str,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user_mongo)
):
    """Start executing an SMS campaign."""
    try:
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        service = get_sms_service()
        await init_service_db(service)

        campaign = await service.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        # Verify organization access
        organization_id = org_id or current_user.get("organization_id") or current_user.get("tenant_id")
        if campaign.organization_id != organization_id:
            raise HTTPException(status_code=403, detail="Access denied")

        success = await service.start_campaign(campaign_id)

        return {
            "success": success,
            "message": "Campaign started",
            "campaign_id": campaign_id,
            "status": "running"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start SMS campaign: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start campaign: {str(e)}")


@router.post("/{campaign_id}/pause")
async def pause_sms_campaign(
    request: Request,
    campaign_id: str,
    current_user=Depends(get_current_user_mongo)
):
    """Pause a running SMS campaign."""
    try:
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        service = get_sms_service()
        await init_service_db(service)

        campaign = await service.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        # Verify organization access
        organization_id = org_id or current_user.get("organization_id") or current_user.get("tenant_id")
        if campaign.organization_id != organization_id:
            raise HTTPException(status_code=403, detail="Access denied")

        success = await service.pause_campaign(campaign_id)

        return {
            "success": success,
            "message": "Campaign paused",
            "campaign_id": campaign_id,
            "status": "paused"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to pause SMS campaign: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to pause campaign: {str(e)}")


@router.post("/{campaign_id}/cancel")
async def cancel_sms_campaign(
    request: Request,
    campaign_id: str,
    current_user=Depends(get_current_user_mongo)
):
    """Cancel an SMS campaign."""
    try:
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        service = get_sms_service()
        await init_service_db(service)

        campaign = await service.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        # Verify organization access
        organization_id = org_id or current_user.get("organization_id") or current_user.get("tenant_id")
        if campaign.organization_id != organization_id:
            raise HTTPException(status_code=403, detail="Access denied")

        success = await service.cancel_campaign(campaign_id)

        return {
            "success": success,
            "message": "Campaign cancelled",
            "campaign_id": campaign_id,
            "status": "cancelled"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel SMS campaign: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel campaign: {str(e)}")


@router.post("/{campaign_id}/retry-failed")
async def retry_failed_messages(
    request: Request,
    campaign_id: str,
    current_user=Depends(get_current_user_mongo)
):
    """
    Retry all failed messages in a campaign.

    This resets failed messages to pending status so they can be retried
    when the campaign is started/resumed.
    """
    try:
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        service = get_sms_service()
        await init_service_db(service)

        campaign = await service.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        # Verify organization access
        organization_id = org_id or current_user.get("organization_id") or current_user.get("tenant_id")
        if campaign.organization_id != organization_id:
            raise HTTPException(status_code=403, detail="Access denied")

        result = await service.retry_failed_messages(campaign_id)

        return result

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to retry failed messages: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retry failed messages: {str(e)}")


@router.post("/{campaign_id}/restart", response_model=SMSCampaignResponse)
async def restart_sms_campaign(
    request: Request,
    campaign_id: str,
    current_user=Depends(get_current_user_mongo)
):
    """
    Restart a completed, failed, or cancelled campaign.

    This endpoint:
    1. Archives old campaign messages (preserves history)
    2. Resets campaign status and progress to zero
    3. Re-prepares messages from the current audience
    4. Automatically starts the campaign

    Args:
        campaign_id: ID of the campaign to restart

    Returns:
        The restarted campaign with updated status

    Raises:
        404: Campaign not found
        403: Access denied
        400: Campaign cannot be restarted (wrong status)
    """
    try:
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        service = get_sms_service()
        await init_service_db(service)

        # Get campaign and verify access
        campaign = await service.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        organization_id = org_id or current_user.get("organization_id") or current_user.get("tenant_id")
        if campaign.organization_id != organization_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Rerun the campaign (archives old messages, resets, re-prepares, starts)
        await service.rerun_campaign(campaign_id)

        # Get updated campaign
        updated_campaign = await service.get_campaign(campaign_id)
        if not updated_campaign:
            raise HTTPException(status_code=500, detail="Failed to retrieve restarted campaign")

        logger.info(f"Successfully restarted campaign {campaign_id}")
        return updated_campaign.to_dict()

    except ValueError as e:
        error_msg = str(e)
        logger.error(f"ValueError in restart: {error_msg}", exc_info=True)

        # Provide actionable error messages with helpful context
        if "No contacts found" in error_msg or "audience has no contacts" in error_msg:
            raise HTTPException(
                status_code=400,
                detail="Cannot restart: The audience has no contacts. Please add contacts to the audience first."
            )
        elif "status:" in error_msg and "draft" in error_msg.lower():
            raise HTTPException(
                status_code=400,
                detail=f"{error_msg} For draft campaigns, use 'Edit Campaign' to add an audience, then use 'Start Campaign'."
            )
        elif "no audience" in error_msg.lower():
            raise HTTPException(
                status_code=400,
                detail="Cannot restart: Campaign has no audience. Edit the campaign to select an audience first."
            )
        else:
            # Pass through other ValueError messages as-is
            raise HTTPException(status_code=400, detail=error_msg)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to restart SMS campaign: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to restart campaign: {str(e)}")


@router.post("/{campaign_id}/duplicate", response_model=SMSCampaignResponse)
async def duplicate_sms_campaign(
    request: Request,
    campaign_id: str,
    current_user=Depends(get_current_user_mongo)
):
    """
    Duplicate a completed campaign to run it again.

    Creates a new draft campaign with the same settings and auto-prepares messages.
    This preserves the original campaign for record-keeping.

    DEPRECATED: Use /restart endpoint instead for better UX.
    """
    try:
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        service = get_sms_service()
        await init_service_db(service)
        db = get_database()

        # Get original campaign
        original_campaign = await service.get_campaign(campaign_id)
        if not original_campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        # Verify organization access
        organization_id = org_id or current_user.get("organization_id") or current_user.get("tenant_id")
        if original_campaign.organization_id != organization_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Get full campaign details including audience and excluded numbers
        campaign_doc = await db["sms_campaigns"].find_one({"id": campaign_id})
        if not campaign_doc:
            raise HTTPException(status_code=404, detail="Campaign not found")

        # Create new campaign with same settings
        config_dict = {
            "send_rate_per_second": original_campaign.config.send_rate_per_second,
            "batch_size": original_campaign.config.batch_size,
            "retry_failed": original_campaign.config.retry_failed,
            "max_retries": original_campaign.config.max_retries,
            "sender_id": original_campaign.config.sender_id,
            "retry_delay_seconds": original_campaign.config.retry_delay_seconds,
            "scheduled_time": None
        }

        user_id = str(current_user.get("_id", current_user.get("id", "")))

        new_campaign = await service.create_campaign(
            name=f"{original_campaign.name} (Copy)",
            organization_id=organization_id,
            user_id=user_id,
            template_content=original_campaign.template_content,
            audience_id=original_campaign.audience_id,
            config=config_dict,
            sms_provider=original_campaign.sms_provider
        )

        # Copy excluded phone numbers
        excluded_phone_numbers = campaign_doc.get("excluded_phone_numbers", [])
        if excluded_phone_numbers:
            await db["sms_campaigns"].update_one(
                {"id": new_campaign.id},
                {"$set": {"excluded_phone_numbers": excluded_phone_numbers}}
            )

        # Auto-prepare messages if campaign has audience
        if new_campaign.audience_id:
            # Fetch contacts from audience
            collection = db["audience_contacts"]
            cursor = collection.find({"audience_id": new_campaign.audience_id})

            excluded_phones = set(excluded_phone_numbers)
            contacts = []
            async for contact in cursor:
                phone = contact.get("phone", "")
                if phone and phone not in excluded_phones:
                    contacts.append({
                        "phone": phone,
                        "name": contact.get("name", ""),
                        "email": contact.get("email", ""),
                        **contact.get("metadata", {})
                    })

            if contacts:
                message_count = await service.prepare_campaign_messages(new_campaign.id, contacts)
                logger.info(f"Auto-prepared {message_count} messages for duplicated campaign {new_campaign.id}")

        # Return new campaign
        updated_campaign = await service.get_campaign(new_campaign.id)
        campaign_dict = updated_campaign.to_dict() if updated_campaign else new_campaign.to_dict()

        # Include excluded numbers in response
        campaign_doc = await db["sms_campaigns"].find_one({"id": new_campaign.id})
        if campaign_doc:
            campaign_dict["excluded_phone_numbers"] = campaign_doc.get("excluded_phone_numbers", [])

        return campaign_dict

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to duplicate SMS campaign: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to duplicate campaign: {str(e)}")


# ==================== Analytics & Messages Endpoints ====================

@router.get("/{campaign_id}/analytics", response_model=SMSCampaignAnalyticsResponse)
async def get_campaign_analytics(
    request: Request,
    campaign_id: str,
    current_user=Depends(get_current_user_mongo)
):
    """Get analytics for an SMS campaign."""
    try:
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        service = get_sms_service()
        await init_service_db(service)

        campaign = await service.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        # Verify organization access
        organization_id = org_id or current_user.get("organization_id") or current_user.get("tenant_id")
        if campaign.organization_id != organization_id:
            raise HTTPException(status_code=403, detail="Access denied")

        analytics = await service.get_campaign_analytics(campaign_id)

        return analytics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get campaign analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")


@router.get("/{campaign_id}/messages")
async def get_campaign_messages(
    request: Request,
    campaign_id: str,
    status: Optional[str] = None,
    limit: int = 100,
    skip: int = 0,
    current_user=Depends(get_current_user_mongo)
):
    """
    Get detailed message list for a campaign with recipient information.

    Query parameters:
    - status: Filter by message status (sent, failed, pending, delivered)
    - limit: Number of messages to return (max 1000)
    - skip: Number of messages to skip for pagination

    Returns:
    - messages: List of messages with recipient details
    - total: Total count of messages matching the filter
    - summary: Count by status type
    - pagination: Pagination metadata
    """
    try:
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        service = get_sms_service()
        await init_service_db(service)
        db = get_database()

        campaign = await service.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        # Verify organization access
        organization_id = org_id or current_user.get("organization_id") or current_user.get("tenant_id")
        if campaign.organization_id != organization_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Build query
        query = {"campaign_id": campaign_id}
        if status:
            query["status"] = status

        # Get total count
        total = await db["sms_campaign_messages"].count_documents(query)

        # Get messages
        cursor = db["sms_campaign_messages"].find(query).sort("created_at", -1).skip(skip).limit(min(limit, 1000))

        messages = []
        async for msg in cursor:
            messages.append({
                "id": msg.get("id"),
                "recipient_name": msg.get("recipient_name"),
                "recipient_phone": msg.get("recipient_phone"),
                "recipient_email": msg.get("recipient_email"),
                "status": msg.get("status"),
                "error_message": msg.get("error_message"),
                "sent_at": msg.get("sent_at"),
                "failed_at": msg.get("failed_at"),
                "delivered_at": msg.get("delivered_at"),
                "provider_message_id": msg.get("provider_message_id"),
                "cost": msg.get("cost", 0),
            })

        # Get summary counts
        pipeline = [
            {"$match": {"campaign_id": campaign_id}},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]

        summary = {}
        async for doc in db["sms_campaign_messages"].aggregate(pipeline):
            summary[doc["_id"]] = doc["count"]

        return {
            "messages": messages,
            "total": total,
            "summary": summary,
            "pagination": {
                "limit": limit,
                "skip": skip,
                "has_more": (skip + len(messages)) < total
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get campaign messages: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {str(e)}")


@router.get("/{campaign_id}/status-stream")
async def stream_campaign_status(
    request: Request,
    campaign_id: str,
    token: Optional[str] = None
):
    """
    Stream real-time campaign status updates using Server-Sent Events (SSE).

    Uses the shared SSE publisher service for efficient event broadcasting.
    Events are published from the campaign execution loop and streamed to all connected clients.

    Usage from frontend:
    ```javascript
    const token = getAuthToken(); // Get JWT token
    const eventSource = new EventSource(`/sms-campaigns/{id}/status-stream?token=${token}`);
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Campaign progress:', data);
    };
    ```
    """
    from shared.services.sse_publisher import sse_publisher

    async def event_generator():
        """Generate SSE events with campaign status updates."""
        try:
            # Authenticate using query parameter token
            if not token:
                yield f"data: {json.dumps({'error': 'Authentication token required'})}\n\n"
                return

            # Manually authenticate with the token
            try:
                from ..auth import get_current_user_mongo
                current_user = await get_current_user_mongo(authorization=f"Bearer {token}")
            except Exception as e:
                logger.error(f"Authentication failed for SSE: {e}")
                yield f"data: {json.dumps({'error': 'Authentication failed'})}\n\n"
                return

            org_id = get_organization_context(request)
            if org_id:
                await validate_organization_access(request, current_user, org_id)

            organization_id = org_id or current_user.get("organization_id") or current_user.get("tenant_id")
            user_id = current_user.get("sub") or current_user.get("user_id")

            service = get_sms_service()
            await init_service_db(service)

            # Verify access
            campaign = await service.get_campaign(campaign_id)
            if not campaign:
                yield f"data: {json.dumps({'error': 'Campaign not found'})}\n\n"
                return

            if campaign.organization_id != organization_id:
                yield f"data: {json.dumps({'error': 'Access denied'})}\n\n"
                return

            # Get initial campaign data to send immediately
            initial_data = {
                "id": campaign_id,
                "campaign_id": campaign_id,
                "status": campaign.status.value,
                "progress": {
                    "total_recipients": campaign.progress.total_recipients,
                    "sent": campaign.progress.sent,
                    "delivered": campaign.progress.delivered,
                    "failed": campaign.progress.failed,
                    "pending": campaign.progress.pending
                },
                "total_cost": campaign.total_cost,
                "updated_at": campaign.updated_at,
                "completed_at": campaign.completed_at,
            }

            # Subscribe to SSE events for this campaign
            async for event in sse_publisher.subscribe(campaign_id, user_id, initial_data):
                # Check for keep-alive
                if event.get("_keepalive"):
                    yield ": keepalive\n\n"
                    continue

                # Send event data
                yield f"data: {json.dumps(event)}\n\n"

        except asyncio.CancelledError:
            logger.info(f"Client disconnected from campaign {campaign_id} status stream")
        except Exception as e:
            logger.error(f"Error in status stream: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering in nginx
        }
    )


# ==================== Template Utilities ====================

@router.get("/count-recipients")
async def count_recipients(
    request: Request,
    audience_id: str,
    excluded_phone_numbers: List[str] = Query(default=[]),
    current_user=Depends(get_current_user_mongo)
):
    """
    Count recipients for a campaign based on audience and exclusions.

    Query parameters:
    - audience_id: ID of the audience to count
    - excluded_phone_numbers: List of phone numbers to exclude (can be repeated)

    Returns:
    - count: Number of recipients after exclusions
    - sample_recipients: Sample of 5 recipients (name, phone)
    """
    try:
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        db = get_database()
        collection = db["audience_contacts"]

        # Fetch all contacts from the audience
        excluded_phones = set(excluded_phone_numbers)
        contacts = []
        seen_phones = set()  # Deduplicate by phone number
        cursor = collection.find({"audience_id": audience_id})

        async for contact in cursor:
            phone = contact.get("phone", "")
            # Skip if empty, excluded, or already seen (duplicate)
            if phone and phone not in excluded_phones and phone not in seen_phones:
                seen_phones.add(phone)
                contacts.append({
                    "name": contact.get("name", ""),
                    "phone": phone
                })

        # Get sample (first 5)
        sample_recipients = contacts[:5]

        return {
            "count": len(contacts),
            "sample_recipients": sample_recipients
        }

    except Exception as e:
        logger.error(f"Failed to count recipients: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to count recipients: {str(e)}")


@router.get("/preview-recipients")
async def preview_recipients(
    request: Request,
    audience_id: str,
    excluded_phone_numbers: List[str] = Query(default=[]),
    limit: int = 100,
    current_user=Depends(get_current_user_mongo)
):
    """
    Preview recipients for a campaign.

    Query parameters:
    - audience_id: ID of the audience
    - excluded_phone_numbers: List of phone numbers to exclude
    - limit: Maximum number of recipients to return (default 100)

    Returns:
    - recipients: List of recipients (name, phone)
    """
    try:
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        db = get_database()
        collection = db["audience_contacts"]

        # Fetch contacts from the audience
        excluded_phones = set(excluded_phone_numbers)
        recipients = []
        cursor = collection.find({"audience_id": audience_id}).limit(limit)

        async for contact in cursor:
            phone = contact.get("phone", "")
            if phone and phone not in excluded_phones:
                recipients.append({
                    "name": contact.get("name", ""),
                    "phone": phone
                })

        return {
            "recipients": recipients
        }

    except Exception as e:
        logger.error(f"Failed to preview recipients: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to preview recipients: {str(e)}")


@router.post("/template/preview", response_model=SMSTemplatePreviewResponse)
async def preview_sms_template(
    request: Request,
    payload: SMSTemplatePreviewRequest,
    current_user=Depends(get_current_user_mongo)
):
    """
    Preview an SMS template with sample data.

    Shows rendered message, detected placeholders, and character count.
    """
    try:
        import re

        # Extract placeholders
        placeholders = re.findall(r'\{\{(\w+)\}\}', payload.template_content)

        # Render template
        rendered = payload.template_content
        for placeholder in placeholders:
            value = payload.sample_data.get(placeholder, f"[{placeholder}]")
            rendered = rendered.replace(f"{{{{{placeholder}}}}}", str(value))

        # Calculate SMS segments (160 chars for GSM-7, 70 for Unicode)
        char_count = len(rendered)
        # Simple check for Unicode characters
        has_unicode = any(ord(c) > 127 for c in rendered)
        segment_size = 70 if has_unicode else 160
        segment_count = (char_count + segment_size - 1) // segment_size

        return {
            "rendered_content": rendered,
            "placeholders": list(set(placeholders)),
            "character_count": char_count,
            "segment_count": segment_count
        }

    except Exception as e:
        logger.error(f"Failed to preview template: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to preview template: {str(e)}")
