"""
WhatsApp Campaign Management Routes

This module provides API endpoints for WhatsApp campaign operations including:
- Campaign CRUD operations
- Campaign execution (start, pause, cancel)
- WhatsApp template management
- Media upload and management
- Interactive button configuration
- Campaign analytics and delivery tracking
"""

from fastapi import APIRouter, HTTPException, Depends, Request, UploadFile, File
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

# Import WhatsApp campaign service
import sys
sys.path.insert(0, "/opt/kasaai/apps")
from shared.services.whatsapp_campaign_service import (
    WhatsAppCampaignService,
    WhatsAppCampaignStatus,
    WhatsAppMessageStatus,
    whatsapp_campaign_service
)
from shared.integration.whatsapp_business import (
    WhatsAppBusinessIntegration,
    WhatsAppBusinessConfig
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/whatsapp-campaigns", tags=["whatsapp-campaigns"])


# ==================== Request/Response Models ====================

class WhatsAppButtonRequest(BaseModel):
    """WhatsApp button configuration."""
    type: str = Field(default="reply", description="Button type: reply, url, phone_number")
    title: str = Field(..., min_length=1, max_length=20, description="Button title")
    payload: Optional[str] = Field(None, description="Button payload for reply buttons")
    url: Optional[str] = Field(None, description="URL for URL buttons")
    phone_number: Optional[str] = Field(None, description="Phone number for call buttons")


class WhatsAppCampaignConfigRequest(BaseModel):
    """Campaign configuration options."""
    send_rate_per_second: float = Field(default=1.0, ge=0.1, le=10.0)
    batch_size: int = Field(default=100, ge=1, le=1000)
    retry_failed: bool = True
    max_retries: int = Field(default=2, ge=0, le=5)
    scheduled_time: Optional[str] = None

    # WhatsApp-specific
    template_name: str = Field(..., min_length=1, description="WhatsApp template name")
    enable_media: bool = False
    media_url: Optional[str] = None
    media_type: Optional[str] = Field(None, description="Media type: image, video, audio, document")
    media_caption: Optional[str] = Field(None, max_length=1024)
    enable_buttons: bool = False
    buttons: List[WhatsAppButtonRequest] = Field(default_factory=list, max_items=3)
    phone_number_id: str = Field(..., description="WhatsApp Business phone number ID")


class WhatsAppCampaignCreate(BaseModel):
    """Request model for creating a WhatsApp campaign."""
    name: str = Field(..., min_length=1, max_length=255)
    template_name: str = Field(..., min_length=1, description="WhatsApp template name")
    audience_id: Optional[str] = None
    config: WhatsAppCampaignConfigRequest


class WhatsAppCampaignUpdate(BaseModel):
    """Request model for updating a WhatsApp campaign."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    template_name: Optional[str] = None
    audience_id: Optional[str] = None
    config: Optional[WhatsAppCampaignConfigRequest] = None


class WhatsAppCampaignResponse(BaseModel):
    """Response model for WhatsApp campaign."""
    id: str
    name: str
    organization_id: str
    user_id: str
    template_name: Optional[str]
    template_content: str
    audience_id: Optional[str]
    status: str
    progress: Dict[str, Any]
    config: Dict[str, Any]
    total_cost: float
    cost_per_message: float
    created_at: str
    updated_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    error_message: Optional[str]
    phone_number_id: str


class WhatsAppCampaignListResponse(BaseModel):
    """Response model for listing campaigns."""
    campaigns: List[Dict[str, Any]]
    total: int


class WhatsAppTemplateResponse(BaseModel):
    """Response model for WhatsApp template."""
    id: str
    name: str
    language: str
    category: str
    status: str
    components: List[Dict[str, Any]]
    placeholders: List[str]


class WhatsAppTemplateListResponse(BaseModel):
    """Response model for listing templates."""
    templates: List[Dict[str, Any]]
    total: int


class WhatsAppCampaignStartRequest(BaseModel):
    """Request for starting a campaign with contacts."""
    contacts: Optional[List[Dict[str, Any]]] = None


class WhatsAppCampaignAnalyticsResponse(BaseModel):
    """Response model for campaign analytics."""
    campaign_id: str
    name: str
    status: str
    progress: Dict[str, Any]
    cost: Dict[str, Any]
    timing: Dict[str, Any]


class WhatsAppMediaUploadResponse(BaseModel):
    """Response model for media upload."""
    media_id: str
    media_url: str
    mime_type: str


class WhatsAppWebhookRequest(BaseModel):
    """Request model for WhatsApp webhooks."""
    object: str
    entry: List[Dict[str, Any]]


# ==================== Helper Functions ====================

def get_whatsapp_service() -> WhatsAppCampaignService:
    """Get initialized WhatsApp campaign service."""
    # Initialize WhatsApp Business API provider from environment
    whatsapp_config = WhatsAppBusinessConfig(
        access_token=os.getenv("WHATSAPP_ACCESS_TOKEN", ""),
        phone_number_id=os.getenv("WHATSAPP_PHONE_NUMBER_ID", ""),
        business_account_id=os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID", ""),
        webhook_verify_token=os.getenv("WHATSAPP_VERIFY_TOKEN", ""),
        webhook_secret=os.getenv("WHATSAPP_WEBHOOK_SECRET", "")
    )

    whatsapp_integration = WhatsAppBusinessIntegration(whatsapp_config)
    whatsapp_campaign_service.set_whatsapp_provider(whatsapp_integration)

    return whatsapp_campaign_service


async def init_service_db(service: WhatsAppCampaignService):
    """Initialize database for service if not already set."""
    if service.db is None:
        db = get_database()
        service.set_database(db)


# ==================== Campaign CRUD Endpoints ====================

@router.post("/", response_model=WhatsAppCampaignResponse)
async def create_whatsapp_campaign(
    request: Request,
    payload: WhatsAppCampaignCreate,
    current_user=Depends(get_current_user_mongo)
):
    """
    Create a new WhatsApp campaign.

    Creates a campaign with WhatsApp Business API template.
    Supports media, buttons, and variable substitution.
    """
    try:
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        organization_id = org_id or current_user.get("organization_id") or current_user.get("tenant_id")
        if not organization_id:
            raise HTTPException(status_code=400, detail="Organization ID required")

        user_id = str(current_user.get("_id", current_user.get("id", "")))

        service = get_whatsapp_service()
        await init_service_db(service)

        config_dict = payload.config.dict() if payload.config else None

        campaign = await service.create_campaign(
            name=payload.name,
            organization_id=organization_id,
            user_id=user_id,
            template_name=payload.template_name,
            audience_id=payload.audience_id,
            config=config_dict,
            phone_number_id=payload.config.phone_number_id
        )

        logger.info(f"Created WhatsApp campaign {campaign.id} for org {organization_id}")

        return campaign.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create WhatsApp campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=WhatsAppCampaignListResponse)
async def list_whatsapp_campaigns(
    request: Request,
    status: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
    current_user=Depends(get_current_user_mongo)
):
    """
    List WhatsApp campaigns for the current organization.

    Optionally filter by status.
    """
    try:
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        organization_id = org_id or current_user.get("organization_id") or current_user.get("tenant_id")
        if not organization_id:
            raise HTTPException(status_code=400, detail="Organization ID required")

        service = get_whatsapp_service()
        await init_service_db(service)

        status_filter = None
        if status:
            try:
                status_filter = WhatsAppCampaignStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

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
        logger.error(f"Failed to list WhatsApp campaigns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{campaign_id}", response_model=WhatsAppCampaignResponse)
async def get_whatsapp_campaign(
    request: Request,
    campaign_id: str,
    current_user=Depends(get_current_user_mongo)
):
    """Get a specific WhatsApp campaign by ID."""
    try:
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        service = get_whatsapp_service()
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
        logger.error(f"Failed to get WhatsApp campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{campaign_id}", response_model=WhatsAppCampaignResponse)
async def update_whatsapp_campaign(
    request: Request,
    campaign_id: str,
    payload: WhatsAppCampaignUpdate,
    current_user=Depends(get_current_user_mongo)
):
    """Update a WhatsApp campaign."""
    try:
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        service = get_whatsapp_service()
        await init_service_db(service)

        # Verify campaign exists and user has access
        campaign = await service.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        organization_id = org_id or current_user.get("organization_id") or current_user.get("tenant_id")
        if campaign.organization_id != organization_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Cannot update running campaigns
        if campaign.status == WhatsAppCampaignStatus.RUNNING:
            raise HTTPException(status_code=400, detail="Cannot update running campaign")

        # Prepare updates
        updates = {}
        if payload.name:
            updates["name"] = payload.name
        if payload.template_name:
            updates["template_name"] = payload.template_name
        if payload.audience_id is not None:
            updates["audience_id"] = payload.audience_id
        if payload.config:
            updates["config"] = payload.config.dict()

        updated_campaign = await service.update_campaign(campaign_id, updates)
        if not updated_campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        return updated_campaign.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update WhatsApp campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{campaign_id}")
async def delete_whatsapp_campaign(
    request: Request,
    campaign_id: str,
    current_user=Depends(get_current_user_mongo)
):
    """Delete a WhatsApp campaign."""
    try:
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        service = get_whatsapp_service()
        await init_service_db(service)

        # Verify campaign exists and user has access
        campaign = await service.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        organization_id = org_id or current_user.get("organization_id") or current_user.get("tenant_id")
        if campaign.organization_id != organization_id:
            raise HTTPException(status_code=403, detail="Access denied")

        success = await service.delete_campaign(campaign_id)
        if not success:
            raise HTTPException(status_code=404, detail="Campaign not found")

        return {"success": True, "message": "Campaign deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete WhatsApp campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Campaign Operations ====================

@router.post("/{campaign_id}/start")
async def start_whatsapp_campaign(
    request: Request,
    campaign_id: str,
    payload: WhatsAppCampaignStartRequest,
    current_user=Depends(get_current_user_mongo)
):
    """Start executing a WhatsApp campaign."""
    try:
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        service = get_whatsapp_service()
        await init_service_db(service)

        # Verify campaign exists and user has access
        campaign = await service.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        organization_id = org_id or current_user.get("organization_id") or current_user.get("tenant_id")
        if campaign.organization_id != organization_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # If contacts provided, prepare messages
        if payload.contacts:
            await service.prepare_campaign_messages(campaign_id, payload.contacts)

        # Start campaign
        success = await service.start_campaign(campaign_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to start campaign")

        return {
            "success": True,
            "message": "Campaign started successfully",
            "campaign_id": campaign_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start WhatsApp campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{campaign_id}/pause")
async def pause_whatsapp_campaign(
    request: Request,
    campaign_id: str,
    current_user=Depends(get_current_user_mongo)
):
    """Pause a running WhatsApp campaign."""
    try:
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        service = get_whatsapp_service()
        await init_service_db(service)

        # Verify campaign exists and user has access
        campaign = await service.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        organization_id = org_id or current_user.get("organization_id") or current_user.get("tenant_id")
        if campaign.organization_id != organization_id:
            raise HTTPException(status_code=403, detail="Access denied")

        success = await service.pause_campaign(campaign_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to pause campaign")

        return {
            "success": True,
            "message": "Campaign paused successfully",
            "campaign_id": campaign_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to pause WhatsApp campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{campaign_id}/cancel")
async def cancel_whatsapp_campaign(
    request: Request,
    campaign_id: str,
    current_user=Depends(get_current_user_mongo)
):
    """Cancel a WhatsApp campaign."""
    try:
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        service = get_whatsapp_service()
        await init_service_db(service)

        # Verify campaign exists and user has access
        campaign = await service.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        organization_id = org_id or current_user.get("organization_id") or current_user.get("tenant_id")
        if campaign.organization_id != organization_id:
            raise HTTPException(status_code=403, detail="Access denied")

        success = await service.cancel_campaign(campaign_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to cancel campaign")

        return {
            "success": True,
            "message": "Campaign cancelled successfully",
            "campaign_id": campaign_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel WhatsApp campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Template Management ====================

@router.get("/templates/list", response_model=WhatsAppTemplateListResponse)
async def list_whatsapp_templates(
    request: Request,
    current_user=Depends(get_current_user_mongo)
):
    """List approved WhatsApp templates."""
    try:
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        service = get_whatsapp_service()
        await init_service_db(service)

        templates = await service.get_templates()

        return {
            "templates": [
                {
                    "id": t.id,
                    "name": t.name,
                    "language": t.language,
                    "category": t.category,
                    "status": t.status,
                    "components": t.components,
                    "placeholders": t.placeholders
                }
                for t in templates
            ],
            "total": len(templates)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list WhatsApp templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/templates/sync")
async def sync_whatsapp_templates(
    request: Request,
    current_user=Depends(get_current_user_mongo)
):
    """Sync templates from WhatsApp Business API."""
    try:
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        service = get_whatsapp_service()
        await init_service_db(service)

        count = await service.sync_templates()

        return {
            "success": True,
            "message": f"Synced {count} templates",
            "count": count
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync WhatsApp templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Analytics ====================

@router.get("/{campaign_id}/analytics", response_model=WhatsAppCampaignAnalyticsResponse)
async def get_whatsapp_campaign_analytics(
    request: Request,
    campaign_id: str,
    current_user=Depends(get_current_user_mongo)
):
    """Get analytics for a WhatsApp campaign."""
    try:
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        service = get_whatsapp_service()
        await init_service_db(service)

        # Verify campaign exists and user has access
        campaign = await service.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        organization_id = org_id or current_user.get("organization_id") or current_user.get("tenant_id")
        if campaign.organization_id != organization_id:
            raise HTTPException(status_code=403, detail="Access denied")

        analytics = await service.get_campaign_analytics(campaign_id)

        return analytics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get WhatsApp campaign analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{campaign_id}/messages")
async def get_whatsapp_campaign_messages(
    request: Request,
    campaign_id: str,
    status: Optional[str] = None,
    limit: int = 100,
    skip: int = 0,
    current_user=Depends(get_current_user_mongo)
):
    """Get messages for a WhatsApp campaign."""
    try:
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        service = get_whatsapp_service()
        await init_service_db(service)

        # Verify campaign exists and user has access
        campaign = await service.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        organization_id = org_id or current_user.get("organization_id") or current_user.get("tenant_id")
        if campaign.organization_id != organization_id:
            raise HTTPException(status_code=403, detail="Access denied")

        status_filter = None
        if status:
            try:
                status_filter = WhatsAppMessageStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

        messages = await service.get_campaign_messages(
            campaign_id=campaign_id,
            status=status_filter,
            limit=limit,
            skip=skip
        )

        return {
            "messages": messages,
            "total": len(messages),
            "campaign_id": campaign_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get WhatsApp campaign messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Webhooks ====================

@router.get("/webhooks/verify")
async def verify_whatsapp_webhook(
    hub_mode: str = None,
    hub_verify_token: str = None,
    hub_challenge: str = None
):
    """Verify WhatsApp webhook."""
    try:
        verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "")

        if hub_mode == "subscribe" and hub_verify_token == verify_token:
            logger.info("WhatsApp webhook verified successfully")
            return int(hub_challenge)
        else:
            logger.warning("WhatsApp webhook verification failed")
            raise HTTPException(status_code=403, detail="Verification failed")

    except Exception as e:
        logger.error(f"Webhook verification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhooks/status")
async def whatsapp_status_webhook(payload: WhatsAppWebhookRequest):
    """Receive WhatsApp delivery status updates."""
    try:
        service = get_whatsapp_service()
        await init_service_db(service)

        success = await service.process_delivery_status(payload.dict())

        return {"success": success}

    except Exception as e:
        logger.error(f"Failed to process WhatsApp webhook: {e}")
        # Return 200 to acknowledge receipt even on error
        return {"success": False, "error": str(e)}
