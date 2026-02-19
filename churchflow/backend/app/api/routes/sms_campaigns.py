"""
SMS Campaign Routes for ChurchFlow

Provides SMS campaign functionality for church communications.
"""

from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
import logging
import os
import sys
import asyncio
import json

# Add shared to path
sys.path.insert(0, "/opt/kasaai/apps")

from shared.services.sms_campaign_service import (  # type: ignore[import]
    SMSCampaignService,
    SMSCampaignStatus,
    SMSMessageStatus,
    sms_campaign_service,
)
from shared.integration.sms import SMSIntegration  # type: ignore[import]

from app.core.database import get_database
from app.api.dependencies import get_current_user
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== Request/Response Models ====================


class SMSCampaignConfigRequest(BaseModel):
    """
    Campaign configuration options.

    Attributes:
        send_rate_per_second: Messages per second to send.
        batch_size: Number of messages to process per batch.
        retry_failed: Whether to retry failed messages.
        max_retries: Maximum number of retry attempts.
        sender_id: Optional sender ID override.
    """

    send_rate_per_second: float = Field(default=1.0, ge=0.1, le=10.0)
    batch_size: int = Field(default=100, ge=1, le=1000)
    retry_failed: bool = True
    max_retries: int = Field(default=2, ge=0, le=5)
    sender_id: Optional[str] = None


class ManualContact(BaseModel):
    """
    Manually specified SMS recipient for testing campaigns.

    Attributes:
        phone: Recipient phone number.
        name: Optional recipient name for personalization.
    """

    phone: str = Field(..., min_length=3, max_length=32)
    name: Optional[str] = Field(default=None, max_length=255)


class SMSCampaignCreate(BaseModel):
    """
    Request model for creating an SMS campaign.

    Attributes:
        name: Campaign display name.
        template_content: SMS template content.
        audience_type: Audience selector (all, conference, branch, session, checked_in, manual).
        conference_id: Target conference for conference/session audiences.
        branch_ids: Target branches for branch audience (supports multiple).
        session_ids: Target sessions for session audience (supports multiple).
        manual_contacts: Manually entered contacts for testing.
        config: Campaign execution configuration.
        sms_provider: Logical provider name (arkesel, hubtel, custom_http, twilio, messagebird).
    """

    name: str = Field(..., min_length=1, max_length=255)
    template_content: str = Field(..., min_length=1, max_length=1600)
    audience_type: str = Field(
        default="all"
    )  # all, conference, branch, session, checked_in, manual
    conference_id: Optional[str] = None
    branch_ids: Optional[List[str]] = None  # For branch-based targeting (supports multiple)
    session_ids: Optional[List[str]] = None  # For session-based targeting
    manual_contacts: Optional[List[ManualContact]] = None
    excluded_phone_numbers: Optional[List[str]] = None  # Phone numbers to exclude from campaign
    config: Optional[SMSCampaignConfigRequest] = None
    sms_provider: str = Field(default="arkesel")


class SMSCampaignResponse(BaseModel):
    """
    Response model for SMS campaign.

    Attributes:
        id: Campaign identifier.
        name: Campaign name.
        organization_id: Owning organization ID.
        user_id: Creator user ID.
        template_content: SMS template content.
        status: Campaign status.
        progress: Progress information.
        config: Execution configuration.
        total_cost: Accumulated cost.
        sms_provider: Logical SMS provider name.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
        started_at: Start timestamp.
        completed_at: Completion timestamp.
    """

    id: str
    name: str
    organization_id: str
    user_id: str
    template_content: str
    status: str
    progress: Dict[str, Any]
    config: Dict[str, Any]
    total_cost: float
    sms_provider: str
    created_at: str
    updated_at: str
    started_at: Optional[str]
    completed_at: Optional[str]


class SMSCampaignListResponse(BaseModel):
    """
    Response model for listing campaigns.

    Attributes:
        campaigns: List of campaign dictionaries.
        total: Total number of returned campaigns.
    """

    campaigns: List[Dict[str, Any]]
    total: int


class AudiencePreviewRequest(BaseModel):
    """
    Request model for audience size preview.

    Attributes:
        audience_type: Audience selector.
        conference_id: Target conference.
        branch_id: Target branch.
        session_ids: Target sessions.
    """

    audience_type: str = Field(default="all")
    conference_id: Optional[str] = None
    branch_id: Optional[str] = None
    session_ids: Optional[List[str]] = None


class AudiencePreviewResponse(BaseModel):
    """
    Response model for audience size preview.

    Attributes:
        count: Number of matching recipients.
    """

    count: int


# ==================== Helper Functions ====================


async def _fetch_campaign_contacts(
    db,
    organization_id: str,
    audience_type: str,
    conference_id: Optional[str] = None,
    branch_ids: List[str] = [],
    session_ids: List[str] = [],
    manual_contacts: List[Dict[str, Any]] = [],
    excluded_phone_numbers: List[str] = []
) -> List[Dict[str, Any]]:
    """
    Fetch contacts based on audience targeting criteria.

    Args:
        db: Database instance
        organization_id: Organization ID
        audience_type: Type of audience (all, conference, branch, session, checked_in, manual)
        conference_id: Conference ID for conference/session audiences
        branch_ids: Branch IDs for branch audience (supports multiple)
        session_ids: Session IDs for session audience
        manual_contacts: Manual contact list
        excluded_phone_numbers: Phone numbers to exclude from campaign

    Returns:
        List of contact dictionaries
    """
    contacts: List[Dict[str, Any]] = []

    if audience_type == "manual":
        # Use manually specified contacts (typically for testing).
        contacts.extend(manual_contacts)

    elif audience_type == "session" and session_ids:
        # Get attendees who checked into specific sessions
        from bson import ObjectId

        session_object_ids = [ObjectId(sid) for sid in session_ids]

        cursor = db["session_attendance"].find(
            {
                "session_id": {"$in": session_object_ids},
            }
        )

        # Get unique registrations (users may check into multiple sessions)
        registration_ids = set()
        async for attendance in cursor:
            registration_ids.add(str(attendance.get("registration_id")))

        # Now fetch registration details
        # Note: Include registrations without status (null) or with confirmed/pending status
        if registration_ids:
            reg_cursor = db["conference_registrations"].find(
                {
                    "_id": {"$in": [ObjectId(rid) for rid in registration_ids]},
                    "$or": [
                        {"status": {"$in": ["confirmed", "pending"]}},
                        {"status": {"$exists": False}},
                        {"status": None}
                    ]
                }
            )
            async for reg in reg_cursor:
                if reg.get("user_phone"):
                    contacts.append(
                        {
                            "phone": reg["user_phone"],
                            "name": reg.get("user_name", ""),
                            "email": reg.get("user_email", ""),
                            "conference": reg.get("conference_name", ""),
                        }
                    )

    elif audience_type == "checked_in" and conference_id:
        # Get registrations that have checked in to the conference
        # Note: Include registrations without status (null) or with confirmed/pending status
        from bson import ObjectId
        cursor = db["conference_registrations"].find(
            {
                "conference_id": ObjectId(conference_id),
                "checked_in": True,
                "$or": [
                    {"status": {"$in": ["confirmed", "pending"]}},
                    {"status": {"$exists": False}},
                    {"status": None}
                ]
            }
        )
        async for reg in cursor:
            if reg.get("user_phone"):
                contacts.append(
                    {
                        "phone": reg["user_phone"],
                        "name": reg.get("user_name", ""),
                        "email": reg.get("user_email", ""),
                        "conference": reg.get("conference_name", ""),
                    }
                )

    elif audience_type == "conference" and conference_id:
        # Get registrations for specific conference
        # Note: Include registrations without status (null) or with confirmed/pending status
        from bson import ObjectId
        cursor = db["conference_registrations"].find(
            {
                "conference_id": ObjectId(conference_id),
                "$or": [
                    {"status": {"$in": ["confirmed", "pending"]}},
                    {"status": {"$exists": False}},
                    {"status": None}
                ]
            }
        )
        async for reg in cursor:
            if reg.get("user_phone"):
                contacts.append(
                    {
                        "phone": reg["user_phone"],
                        "name": reg.get("user_name", ""),
                        "email": reg.get("user_email", ""),
                        "conference": reg.get("conference_name", ""),
                    }
                )

    elif audience_type == "branch" and branch_ids:
        # Get members from specific branches (supports multiple)
        cursor = db["users"].find(
            {
                "branch_id": {"$in": branch_ids},
                "phone": {"$exists": True, "$ne": ""},
            }
        )
        async for user in cursor:
            contacts.append(
                {
                    "phone": user["phone"],
                    "name": user.get("name", ""),
                    "email": user.get("email", ""),
                    "branch": user.get("branch_name", ""),
                }
            )

    else:
        # Get all members with phone numbers
        cursor = db["users"].find(
            {
                "organization_id": organization_id,
                "phone": {"$exists": True, "$ne": ""},
            }
        )
        async for user in cursor:
            contacts.append(
                {
                    "phone": user["phone"],
                    "name": user.get("name", ""),
                    "email": user.get("email", ""),
                }
            )

    return contacts


def get_sms_service() -> SMSCampaignService:
    """
    Get initialized SMS campaign service.

    Returns:
        SMSCampaignService: Singleton service instance configured with Arkesel
        as the default provider (Hubtel/custom/Twilio available via shared
        integration if configured).
    """
    sms_config = {
        "providers": {
            # Primary Ghana provider: Arkesel
            "arkesel": {
                "api_key": settings.arkesel_api_key,
                "sender_id": settings.arkesel_sender_id,
            },
            # Twilio optional fallback (configured via environment)
            "twilio": {
                "account_sid": os.getenv("TWILIO_ACCOUNT_SID", settings.twilio_account_sid),
                "auth_token": os.getenv("TWILIO_AUTH_TOKEN", settings.twilio_auth_token),
            },
        },
        # ChurchFlow default: Arkesel (matches session management SMS)
        "default_provider": "arkesel",
    }

    sms_integration = SMSIntegration(sms_config)
    sms_campaign_service.set_sms_provider(sms_integration)

    return sms_campaign_service


async def init_service_db(service: SMSCampaignService):
    """Initialize database for service."""
    if service.db is None:
        db = get_database()  # get_database() is not async, returns database directly
        service.set_database(db)


# ==================== Campaign Endpoints ====================

@router.get("/count-recipients")
async def count_recipients(
    request: Request,
    audience_type: str = "all",
    conference_id: Optional[str] = None,
    branch_ids: List[str] = Query(default=[]),
    session_ids: List[str] = Query(default=[]),
    current_user=Depends(get_current_user)
):
    """
    Count how many recipients will receive the campaign based on audience targeting.
    Also returns the first 5 sample recipients for preview.

    Returns: {"count": number, "sample": [list of first 5 recipients]}
    """
    try:
        organization_id = current_user.get("organization_id", "")
        db = get_database()

        # Fetch contacts using helper function
        contacts = await _fetch_campaign_contacts(
            db=db,
            organization_id=organization_id,
            audience_type=audience_type,
            conference_id=conference_id,
            branch_ids=branch_ids,
            session_ids=session_ids,
            manual_contacts=[]
        )

        # Get first 5 contacts as sample
        sample = contacts[:5] if len(contacts) > 0 else []

        return {
            "count": len(contacts),
            "sample": sample
        }

    except Exception as e:
        logger.error(f"Failed to count recipients: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preview-recipients")
async def preview_recipients(
    request: Request,
    audience_type: str = "all",
    conference_id: Optional[str] = None,
    branch_ids: List[str] = Query(default=[]),
    session_ids: List[str] = Query(default=[]),
    current_user=Depends(get_current_user)
):
    """
    Get all recipients who will receive the campaign based on audience targeting.
    Used for the "View All" preview functionality.

    Returns: {"recipients": [list of all recipients with name and phone]}
    """
    try:
        organization_id = current_user.get("organization_id", "")
        db = get_database()

        # Fetch contacts using helper function
        contacts = await _fetch_campaign_contacts(
            db=db,
            organization_id=organization_id,
            audience_type=audience_type,
            conference_id=conference_id,
            branch_ids=branch_ids,
            session_ids=session_ids,
            manual_contacts=[]
        )

        # Return all recipients (name and phone only)
        recipients = [
            {"name": c.get("name", "Unknown"), "phone": c.get("phone", "")}
            for c in contacts
        ]

        return {"recipients": recipients}

    except Exception as e:
        logger.error(f"Failed to preview recipients: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=SMSCampaignResponse)
async def create_sms_campaign(
    request: Request,
    payload: SMSCampaignCreate,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user)
):
    """
    Create a new SMS campaign and automatically prepare messages.

    Supports targeting:
    - All registered members
    - Members of a specific conference
    - Members of a specific branch
    """
    try:
        organization_id = current_user.get("organization_id", "")
        user_id = str(current_user.get("_id", current_user.get("id", "")))

        service = get_sms_service()
        await init_service_db(service)
        db = get_database()

        config_dict = payload.config.dict() if payload.config else None

        # Store audience targeting info in metadata
        campaign = await service.create_campaign(
            name=payload.name,
            organization_id=organization_id,
            user_id=user_id,
            template_content=payload.template_content,
            audience_id=None,
            config=config_dict,
            sms_provider=payload.sms_provider
        )

        # Update with church-specific targeting
        await db["sms_campaigns"].update_one(
            {"id": campaign.id},
            {"$set": {
                "audience_type": payload.audience_type,
                "conference_id": payload.conference_id,
                "branch_ids": payload.branch_ids or [],
                "session_ids": payload.session_ids or [],
                # Store manual contacts on the campaign document for manual/testing audiences.
                "manual_contacts": [c.model_dump() for c in payload.manual_contacts]
                if payload.manual_contacts
                else [],
                "excluded_phone_numbers": payload.excluded_phone_numbers or [],
            }}
        )

        logger.info(f"Created SMS campaign {campaign.id} for church org {organization_id}")

        # Auto-prepare messages immediately after creation
        contacts = await _fetch_campaign_contacts(
            db=db,
            organization_id=organization_id,
            audience_type=payload.audience_type,
            conference_id=payload.conference_id,
            branch_ids=payload.branch_ids or [],
            session_ids=payload.session_ids or [],
            manual_contacts=[c.model_dump() for c in payload.manual_contacts] if payload.manual_contacts else []
        )

        if contacts:
            message_count = await service.prepare_campaign_messages(campaign.id, contacts)
            logger.info(f"Auto-prepared {message_count} messages for campaign {campaign.id}")

        # Return updated campaign with message count
        updated_campaign = await service.get_campaign(campaign.id)
        return updated_campaign.to_dict() if updated_campaign else campaign.to_dict()

    except Exception as e:
        logger.error(f"Failed to create SMS campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=SMSCampaignListResponse)
async def list_sms_campaigns(
    request: Request,
    status: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
    current_user=Depends(get_current_user)
):
    """List SMS campaigns for the church."""
    try:
        organization_id = current_user.get("organization_id", "")

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

    except Exception as e:
        logger.error(f"Failed to list SMS campaigns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{campaign_id}", response_model=SMSCampaignResponse)
async def get_sms_campaign(
    campaign_id: str,
    current_user=Depends(get_current_user)
):
    """Get a specific SMS campaign with church-specific targeting info."""
    try:
        organization_id = current_user.get("organization_id", "")

        service = get_sms_service()
        await init_service_db(service)
        db = get_database()

        campaign = await service.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        if campaign.organization_id != organization_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Get full campaign document including church-specific fields
        campaign_doc = await db["sms_campaigns"].find_one({"id": campaign_id})

        # Merge campaign data with church-specific targeting info
        campaign_dict = campaign.to_dict()
        if campaign_doc:
            campaign_dict["audience_type"] = campaign_doc.get("audience_type", "all")
            campaign_dict["conference_id"] = campaign_doc.get("conference_id")
            campaign_dict["branch_ids"] = campaign_doc.get("branch_ids", [])
            campaign_dict["session_ids"] = campaign_doc.get("session_ids", [])
            campaign_dict["manual_contacts"] = campaign_doc.get("manual_contacts", [])
            campaign_dict["excluded_phone_numbers"] = campaign_doc.get("excluded_phone_numbers", [])

        return campaign_dict

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get SMS campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{campaign_id}", response_model=SMSCampaignResponse)
async def update_sms_campaign(
    campaign_id: str,
    payload: SMSCampaignCreate,
    current_user=Depends(get_current_user)
):
    """
    Update an SMS campaign (only draft campaigns can be updated).

    Updates campaign details and re-prepares messages with new targeting.
    """
    try:
        organization_id = current_user.get("organization_id", "")

        service = get_sms_service()
        await init_service_db(service)
        db = get_database()

        # Get existing campaign
        campaign = await service.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        if campaign.organization_id != organization_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Only allow updating draft and paused campaigns
        if campaign.status not in [SMSCampaignStatus.DRAFT, SMSCampaignStatus.PAUSED]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot update campaign with status: {campaign.status.value}. Only draft and paused campaigns can be edited."
            )

        # Delete existing messages
        await db["sms_campaign_messages"].delete_many({"campaign_id": campaign_id})

        # Update campaign details
        config_dict = payload.config.dict() if payload.config else None

        await db["sms_campaigns"].update_one(
            {"id": campaign_id},
            {"$set": {
                "name": payload.name,
                "template_content": payload.template_content,
                "audience_type": payload.audience_type,
                "conference_id": payload.conference_id,
                "branch_ids": payload.branch_ids or [],
                "session_ids": payload.session_ids or [],
                "manual_contacts": [c.model_dump() for c in payload.manual_contacts]
                if payload.manual_contacts
                else [],
                "excluded_phone_numbers": payload.excluded_phone_numbers or [],
                "config": config_dict or {},
                "sms_provider": payload.sms_provider,
                "updated_at": datetime.utcnow().isoformat(),
                # Reset progress
                "progress.total_recipients": 0,
                "progress.sent": 0,
                "progress.delivered": 0,
                "progress.failed": 0,
                "progress.pending": 0,
            }}
        )

        # Re-prepare messages with new targeting
        contacts = await _fetch_campaign_contacts(
            db=db,
            organization_id=organization_id,
            audience_type=payload.audience_type,
            conference_id=payload.conference_id,
            branch_ids=payload.branch_ids or [],
            session_ids=payload.session_ids or [],
            manual_contacts=[c.model_dump() for c in payload.manual_contacts] if payload.manual_contacts else []
        )

        if contacts:
            message_count = await service.prepare_campaign_messages(campaign_id, contacts)
            logger.info(f"Re-prepared {message_count} messages for updated campaign {campaign_id}")

        # Return updated campaign with church-specific fields
        updated_campaign = await service.get_campaign(campaign_id)
        campaign_dict = updated_campaign.to_dict() if updated_campaign else {}

        # Get full campaign document including church-specific fields
        campaign_doc = await db["sms_campaigns"].find_one({"id": campaign_id})
        if campaign_doc:
            campaign_dict["audience_type"] = campaign_doc.get("audience_type", "all")
            campaign_dict["conference_id"] = campaign_doc.get("conference_id")
            campaign_dict["branch_ids"] = campaign_doc.get("branch_ids", [])
            campaign_dict["session_ids"] = campaign_doc.get("session_ids", [])
            campaign_dict["manual_contacts"] = campaign_doc.get("manual_contacts", [])

        return campaign_dict

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update SMS campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{campaign_id}/duplicate", response_model=SMSCampaignResponse)
async def duplicate_sms_campaign(
    campaign_id: str,
    current_user=Depends(get_current_user)
):
    """
    Duplicate a completed campaign to run it again.

    Creates a new draft campaign with the same settings and auto-prepares messages.
    """
    try:
        organization_id = current_user.get("organization_id", "")
        user_id = str(current_user.get("_id", current_user.get("id", "")))

        service = get_sms_service()
        await init_service_db(service)
        db = get_database()

        # Get original campaign
        original_campaign = await service.get_campaign(campaign_id)
        if not original_campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        if original_campaign.organization_id != organization_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Get full campaign details including targeting info
        campaign_doc = await db["sms_campaigns"].find_one({"id": campaign_id})
        if not campaign_doc:
            raise HTTPException(status_code=404, detail="Campaign not found")

        # Create new campaign with same settings
        config_dict = original_campaign.config.__dict__ if hasattr(original_campaign.config, '__dict__') else {
            "send_rate_per_second": original_campaign.config.send_rate_per_second,
            "batch_size": original_campaign.config.batch_size,
            "retry_failed": original_campaign.config.retry_failed,
            "max_retries": original_campaign.config.max_retries,
            "sender_id": original_campaign.config.sender_id
        }

        new_campaign = await service.create_campaign(
            name=f"{original_campaign.name} (Copy)",
            organization_id=organization_id,
            user_id=user_id,
            template_content=original_campaign.template_content,
            audience_id=None,
            config=config_dict,
            sms_provider=original_campaign.sms_provider
        )

        # Copy church-specific targeting
        audience_type = campaign_doc.get("audience_type", "all")
        conference_id = campaign_doc.get("conference_id")
        branch_ids = campaign_doc.get("branch_ids", [])
        session_ids = campaign_doc.get("session_ids", [])
        manual_contacts = campaign_doc.get("manual_contacts", [])
        excluded_phone_numbers = campaign_doc.get("excluded_phone_numbers", [])

        await db["sms_campaigns"].update_one(
            {"id": new_campaign.id},
            {"$set": {
                "audience_type": audience_type,
                "conference_id": conference_id,
                "branch_ids": branch_ids,
                "session_ids": session_ids,
                "manual_contacts": manual_contacts,
                "excluded_phone_numbers": excluded_phone_numbers,
            }}
        )

        # Auto-prepare messages
        contacts = await _fetch_campaign_contacts(
            db=db,
            organization_id=organization_id,
            audience_type=audience_type,
            conference_id=conference_id,
            branch_ids=branch_ids,
            session_ids=session_ids,
            manual_contacts=manual_contacts
        )

        if contacts:
            message_count = await service.prepare_campaign_messages(new_campaign.id, contacts)
            logger.info(f"Auto-prepared {message_count} messages for duplicated campaign {new_campaign.id}")

        # Return new campaign with church-specific fields
        updated_campaign = await service.get_campaign(new_campaign.id)
        campaign_dict = updated_campaign.to_dict() if updated_campaign else new_campaign.to_dict()

        # Get full campaign document including church-specific fields
        campaign_doc = await db["sms_campaigns"].find_one({"id": new_campaign.id})
        if campaign_doc:
            campaign_dict["audience_type"] = campaign_doc.get("audience_type", "all")
            campaign_dict["conference_id"] = campaign_doc.get("conference_id")
            campaign_dict["branch_ids"] = campaign_doc.get("branch_ids", [])
            campaign_dict["session_ids"] = campaign_doc.get("session_ids", [])
            campaign_dict["manual_contacts"] = campaign_doc.get("manual_contacts", [])
            campaign_dict["excluded_phone_numbers"] = campaign_doc.get("excluded_phone_numbers", [])

        return campaign_dict

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to duplicate SMS campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{campaign_id}")
async def delete_sms_campaign(
    campaign_id: str,
    current_user=Depends(get_current_user)
):
    """Delete an SMS campaign."""
    try:
        organization_id = current_user.get("organization_id", "")

        service = get_sms_service()
        await init_service_db(service)

        campaign = await service.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        if campaign.organization_id != organization_id:
            raise HTTPException(status_code=403, detail="Access denied")

        success = await service.delete_campaign(campaign_id)

        return {"success": success, "message": "Campaign deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete SMS campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{campaign_id}/prepare")
async def prepare_campaign(
    campaign_id: str,
    current_user=Depends(get_current_user)
):
    """
    Prepare campaign messages by fetching contacts from the database.

    Note: Campaigns are now auto-prepared on creation, but this endpoint
    allows re-preparing if needed.

    Fetches contacts based on audience_type:
    - all: All registered members
    - conference: Members registered for a specific conference
    - branch: Members belonging to a specific branch
    - session: Members who checked into specific sessions
    - checked_in: Members who checked into a specific conference
    """
    try:
        organization_id = current_user.get("organization_id", "")

        service = get_sms_service()
        await init_service_db(service)
        db = get_database()

        campaign = await service.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        if campaign.organization_id != organization_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Get campaign targeting info
        campaign_doc = await db["sms_campaigns"].find_one({"id": campaign_id})
        audience_type = campaign_doc.get("audience_type", "all")
        conference_id = campaign_doc.get("conference_id")
        branch_ids = campaign_doc.get("branch_ids", [])
        session_ids = campaign_doc.get("session_ids", [])
        manual_contacts = campaign_doc.get("manual_contacts", [])

        # Fetch contacts using helper function
        contacts = await _fetch_campaign_contacts(
            db=db,
            organization_id=organization_id,
            audience_type=audience_type,
            conference_id=conference_id,
            branch_ids=branch_ids,
            session_ids=session_ids,
            manual_contacts=manual_contacts
        )

        if not contacts:
            raise HTTPException(status_code=400, detail="No contacts found for this audience")

        message_count = await service.prepare_campaign_messages(campaign_id, contacts)

        return {
            "success": True,
            "message": f"Prepared {message_count} messages",
            "message_count": message_count
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to prepare campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{campaign_id}/start")
async def start_sms_campaign(
    campaign_id: str,
    current_user=Depends(get_current_user)
):
    """Start executing an SMS campaign."""
    try:
        organization_id = current_user.get("organization_id", "")

        service = get_sms_service()
        await init_service_db(service)

        campaign = await service.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

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
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{campaign_id}/pause")
async def pause_sms_campaign(
    campaign_id: str,
    current_user=Depends(get_current_user)
):
    """Pause a running SMS campaign."""
    try:
        organization_id = current_user.get("organization_id", "")

        service = get_sms_service()
        await init_service_db(service)

        campaign = await service.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        if campaign.organization_id != organization_id:
            raise HTTPException(status_code=403, detail="Access denied")

        success = await service.pause_campaign(campaign_id)

        return {
            "success": success,
            "message": "Campaign paused",
            "status": "paused"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to pause SMS campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{campaign_id}/cancel")
async def cancel_sms_campaign(
    campaign_id: str,
    current_user=Depends(get_current_user)
):
    """Cancel an SMS campaign."""
    try:
        organization_id = current_user.get("organization_id", "")

        service = get_sms_service()
        await init_service_db(service)

        campaign = await service.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        if campaign.organization_id != organization_id:
            raise HTTPException(status_code=403, detail="Access denied")

        success = await service.cancel_campaign(campaign_id)

        return {
            "success": success,
            "message": "Campaign cancelled",
            "status": "cancelled"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel SMS campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{campaign_id}/retry-failed")
async def retry_failed_messages(
    campaign_id: str,
    current_user=Depends(get_current_user)
):
    """
    Retry all failed messages in a campaign.

    This resets failed messages to pending status so they can be retried
    when the campaign is started/resumed.
    """
    try:
        organization_id = current_user.get("organization_id", "")

        service = get_sms_service()
        await init_service_db(service)

        campaign = await service.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

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
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{campaign_id}/analytics")
async def get_campaign_analytics(
    campaign_id: str,
    current_user=Depends(get_current_user)
):
    """Get analytics for an SMS campaign."""
    try:
        organization_id = current_user.get("organization_id", "")

        service = get_sms_service()
        await init_service_db(service)

        campaign = await service.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        if campaign.organization_id != organization_id:
            raise HTTPException(status_code=403, detail="Access denied")

        analytics = await service.get_campaign_analytics(campaign_id)

        return analytics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get campaign analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{campaign_id}/messages")
async def get_campaign_messages(
    campaign_id: str,
    status: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    skip: int = Query(default=0, ge=0),
    current_user=Depends(get_current_user)
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
    """
    try:
        organization_id = current_user.get("organization_id", "")

        service = get_sms_service()
        await init_service_db(service)
        db = get_database()

        # Verify campaign access
        campaign = await service.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        if campaign.organization_id != organization_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Build query
        query = {"campaign_id": campaign_id}
        if status:
            query["status"] = status

        # Get total count
        total = await db["sms_campaign_messages"].count_documents(query)

        # Get messages
        cursor = db["sms_campaign_messages"].find(query).sort("created_at", -1).skip(skip).limit(limit)

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
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/audience-preview", response_model=AudiencePreviewResponse)
async def preview_audience_size(
    payload: AudiencePreviewRequest,
    current_user=Depends(get_current_user),
):
    """
    Preview the number of recipients for a given audience selection.

    This does **not** create messages or modify any campaigns. It simply
    returns how many contacts match the provided filters so the admin
    can see audience size before preparing a campaign.
    """
    try:
        organization_id = current_user.get("organization_id", "")
        db = get_database()  # get_database() is not async, returns database directly

        audience_type = payload.audience_type or "all"
        conference_id = payload.conference_id
        branch_id = payload.branch_id
        session_ids = payload.session_ids or []

        count = 0

        if audience_type == "session" and session_ids:
            from bson import ObjectId

            session_object_ids = [ObjectId(sid) for sid in session_ids]

            # Count distinct registrations across selected sessions.
            pipeline = [
                {
                    "$match": {
                        "session_id": {"$in": session_object_ids},
                    }
                },
                {
                    "$group": {
                        "_id": "$registration_id",
                    }
                },
                {
                    "$count": "registration_count",
                },
            ]

            result = await db["session_attendance"].aggregate(pipeline).to_list(length=1)
            if result:
                count = int(result[0].get("registration_count", 0))

        elif audience_type == "checked_in" and conference_id:
            from bson import ObjectId
            count = await db["conference_registrations"].count_documents(
                {
                    "conference_id": ObjectId(conference_id),
                    "checked_in": True,
                    "$or": [
                        {"status": {"$in": ["confirmed", "pending"]}},
                        {"status": {"$exists": False}},
                        {"status": None}
                    ],
                    "user_phone": {"$exists": True, "$ne": ""},
                }
            )

        elif audience_type == "conference" and conference_id:
            from bson import ObjectId
            count = await db["conference_registrations"].count_documents(
                {
                    "conference_id": ObjectId(conference_id),
                    "$or": [
                        {"status": {"$in": ["confirmed", "pending"]}},
                        {"status": {"$exists": False}},
                        {"status": None}
                    ],
                    "user_phone": {"$exists": True, "$ne": ""},
                }
            )

        elif audience_type == "branch" and branch_id:
            count = await db["users"].count_documents(
                {
                    "branch_id": branch_id,
                    "phone": {"$exists": True, "$ne": ""},
                }
            )

        else:
            # "all" audience: all users in organization with phone numbers.
            count = await db["users"].count_documents(
                {
                    "organization_id": organization_id,
                    "phone": {"$exists": True, "$ne": ""},
                }
            )

        return AudiencePreviewResponse(count=count)

    except Exception as e:  # pragma: no cover - defensive
        logger.error(f"Failed to preview audience size: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/template/preview")
async def preview_template(
    template_content: str,
    sample_data: Dict[str, str] = {},
    current_user=Depends(get_current_user)
):
    """Preview an SMS template with sample data."""
    import re

    placeholders = re.findall(r'\{\{(\w+)\}\}', template_content)

    rendered = template_content
    for placeholder in placeholders:
        value = sample_data.get(placeholder, f"[{placeholder}]")
        rendered = rendered.replace(f"{{{{{placeholder}}}}}", str(value))

    char_count = len(rendered)
    has_unicode = any(ord(c) > 127 for c in rendered)
    segment_size = 70 if has_unicode else 160
    segment_count = (char_count + segment_size - 1) // segment_size

    return {
        "rendered_content": rendered,
        "placeholders": list(set(placeholders)),
        "character_count": char_count,
        "segment_count": segment_count
    }


@router.get("/{campaign_id}/status-stream")
async def stream_campaign_status(
    campaign_id: str,
    current_user=Depends(get_current_user)
):
    """
    Stream real-time campaign status updates using Server-Sent Events (SSE).

    This endpoint sends campaign progress updates every 2 seconds until the
    campaign is completed, cancelled, or failed.

    Usage from frontend:
    ```javascript
    const eventSource = new EventSource('/api/v1/sms-campaigns/{id}/status-stream');
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Campaign progress:', data);
    };
    ```
    """
    async def event_generator():
        """Generate SSE events with campaign status updates."""
        try:
            organization_id = current_user.get("organization_id", "")

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

            # Stream updates until campaign is no longer running
            while True:
                campaign = await service.get_campaign(campaign_id)
                if not campaign:
                    break

                # Send current status
                status_data = {
                    "campaign_id": campaign_id,
                    "status": campaign.status.value,
                    "progress": campaign.progress.to_dict() if hasattr(campaign.progress, 'to_dict') else {
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

                yield f"data: {json.dumps(status_data)}\n\n"

                # Stop streaming if campaign is no longer running
                if campaign.status.value in ["completed", "cancelled", "failed"]:
                    logger.info(f"Campaign {campaign_id} finished with status: {campaign.status.value}")
                    break

                # Wait 2 seconds before next update
                await asyncio.sleep(2)

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
