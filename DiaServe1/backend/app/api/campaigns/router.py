"""
Campaign API Router for EstateFlow.

Provides endpoints for managing multi-channel marketing campaigns.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from typing import List, Optional
from datetime import datetime
import logging
import csv
import io

from app.core.database import get_database
from app.core.auth import get_current_user, get_organization_context
from app.services.campaign_service import CampaignService
from app.services.contact_service import ContactService
from app.models.campaign import (
    Campaign,
    CampaignCreate,
    CampaignUpdate,
    CampaignType,
    CampaignStatus,
    CampaignListResponse,
    Contact,
    ContactCreate,
    ContactUpdate,
    ContactListResponse,
    SegmentFilter,
    SegmentPreviewResponse
)

router = APIRouter(prefix="/campaigns", tags=["campaigns"])
logger = logging.getLogger(__name__)


# ==================== Campaign Endpoints ====================


@router.post("", response_model=Campaign, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    campaign_data: CampaignCreate,
    user=Depends(get_current_user),
    org_context=Depends(get_organization_context)
):
    """
    Create a new marketing campaign.

    Args:
        campaign_data: Campaign creation data
        user: Current authenticated user
        org_context: Organization context

    Returns:
        Created campaign
    """
    db = await get_database()
    campaign_service = CampaignService(db)

    try:
        campaign = await campaign_service.create_campaign(
            campaign_data=campaign_data,
            organization_id=org_context["organization_id"],
            user_id=user["sub"]
        )
        logger.info(
            f"Campaign {campaign.id} created by user {user['sub']} "
            f"in organization {org_context['organization_id']}"
        )
        return campaign

    except Exception as e:
        logger.error(f"Error creating campaign: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create campaign: {str(e)}"
        )


@router.get("", response_model=CampaignListResponse)
async def list_campaigns(
    campaign_type: Optional[CampaignType] = Query(None, description="Filter by campaign type"),
    status_filter: Optional[CampaignStatus] = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Number of campaigns to return"),
    offset: int = Query(0, ge=0, description="Number of campaigns to skip"),
    user=Depends(get_current_user),
    org_context=Depends(get_organization_context)
):
    """
    List campaigns for the organization.

    Args:
        campaign_type: Optional filter by campaign type
        status_filter: Optional filter by status
        limit: Maximum number of campaigns to return
        offset: Number of campaigns to skip
        user: Current authenticated user
        org_context: Organization context

    Returns:
        List of campaigns with pagination info
    """
    db = await get_database()
    campaign_service = CampaignService(db)

    try:
        campaigns, total = await campaign_service.list_campaigns(
            organization_id=org_context["organization_id"],
            campaign_type=campaign_type,
            status=status_filter,
            limit=limit,
            offset=offset
        )

        return CampaignListResponse(
            campaigns=campaigns,
            total=total,
            limit=limit,
            offset=offset
        )

    except Exception as e:
        logger.error(f"Error listing campaigns: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list campaigns: {str(e)}"
        )


# ==================== Contact Endpoints ====================
# NOTE: Contact routes MUST be defined before /{campaign_id} routes,
# otherwise FastAPI matches "/contacts" as a campaign_id parameter.


@router.post("/contacts", response_model=Contact, status_code=status.HTTP_201_CREATED)
async def create_contact(
    contact_data: ContactCreate,
    user=Depends(get_current_user),
    org_context=Depends(get_organization_context)
):
    """
    Create a new contact/lead.

    Args:
        contact_data: Contact creation data
        user: Current authenticated user
        org_context: Organization context

    Returns:
        Created contact
    """
    db = await get_database()
    contact_service = ContactService(db)

    try:
        contact = await contact_service.create_contact(
            contact_data=contact_data,
            organization_id=org_context["organization_id"],
            user_id=user["sub"]
        )

        logger.info(f"Contact {contact.id} created by user {user['sub']}")
        return contact

    except Exception as e:
        logger.error(f"Error creating contact: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create contact: {str(e)}"
        )


@router.get("/contacts", response_model=ContactListResponse)
async def list_contacts(
    limit: int = Query(50, ge=1, le=100, description="Number of contacts to return"),
    offset: int = Query(0, ge=0, description="Number of contacts to skip"),
    search: Optional[str] = Query(None, description="Search by name, email, or phone"),
    user=Depends(get_current_user),
    org_context=Depends(get_organization_context)
):
    """
    List contacts for the organization.

    Args:
        limit: Maximum number of contacts to return
        offset: Number of contacts to skip
        search: Optional search query
        user: Current authenticated user
        org_context: Organization context

    Returns:
        List of contacts with pagination info
    """
    db = await get_database()
    contact_service = ContactService(db)

    try:
        contacts, total = await contact_service.list_contacts(
            organization_id=org_context["organization_id"],
            limit=limit,
            offset=offset,
            search=search
        )

        return ContactListResponse(
            contacts=contacts,
            total=total,
            limit=limit,
            offset=offset
        )

    except Exception as e:
        logger.error(f"Error listing contacts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list contacts: {str(e)}"
        )


@router.get("/contacts/{contact_id}", response_model=Contact)
async def get_contact(
    contact_id: str,
    user=Depends(get_current_user),
    org_context=Depends(get_organization_context)
):
    """
    Get contact details by ID.

    Args:
        contact_id: Contact ID
        user: Current authenticated user
        org_context: Organization context

    Returns:
        Contact details
    """
    db = await get_database()
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


@router.put("/contacts/{contact_id}", response_model=Contact)
async def update_contact(
    contact_id: str,
    updates: ContactUpdate,
    user=Depends(get_current_user),
    org_context=Depends(get_organization_context)
):
    """
    Update a contact.

    Args:
        contact_id: Contact ID
        updates: Update data
        user: Current authenticated user
        org_context: Organization context

    Returns:
        Updated contact
    """
    db = await get_database()
    contact_service = ContactService(db)

    try:
        contact = await contact_service.update_contact(
            contact_id=contact_id,
            updates=updates,
            organization_id=org_context["organization_id"]
        )

        if not contact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contact {contact_id} not found"
            )

        logger.info(f"Contact {contact_id} updated by user {user['sub']}")
        return contact

    except Exception as e:
        logger.error(f"Error updating contact: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update contact: {str(e)}"
        )


@router.delete("/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: str,
    user=Depends(get_current_user),
    org_context=Depends(get_organization_context)
):
    """
    Delete a contact.

    Args:
        contact_id: Contact ID
        user: Current authenticated user
        org_context: Organization context
    """
    db = await get_database()
    contact_service = ContactService(db)

    deleted = await contact_service.delete_contact(
        contact_id=contact_id,
        organization_id=org_context["organization_id"]
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contact {contact_id} not found"
        )

    logger.info(f"Contact {contact_id} deleted by user {user['sub']}")


@router.post("/contacts/import")
async def bulk_import_contacts(
    file: UploadFile = File(..., description="CSV file with contact data"),
    user=Depends(get_current_user),
    org_context=Depends(get_organization_context)
):
    """
    Bulk import contacts from CSV file.

    CSV format:
    name,email,phone,property_type_preferences,location_preferences,budget_min,budget_max,tags,source

    Args:
        file: CSV file upload
        user: Current authenticated user
        org_context: Organization context

    Returns:
        Import summary with count of imported contacts
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV"
        )

    db = await get_database()
    contact_service = ContactService(db)

    try:
        # Read CSV content
        content = await file.read()
        decoded_content = content.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(decoded_content))

        # Parse contacts
        contacts_data = []
        for row in csv_reader:
            contact_dict = {
                "name": row.get("name", "").strip(),
                "email": row.get("email", "").strip() or None,
                "phone": row.get("phone", "").strip() or None,
                "property_type_preferences": [
                    p.strip() for p in row.get("property_type_preferences", "").split(",") if p.strip()
                ],
                "location_preferences": [
                    l.strip() for l in row.get("location_preferences", "").split(",") if l.strip()
                ],
                "budget_min": float(row["budget_min"]) if row.get("budget_min") else None,
                "budget_max": float(row["budget_max"]) if row.get("budget_max") else None,
                "tags": [t.strip() for t in row.get("tags", "").split(",") if t.strip()],
                "source": row.get("source", "").strip() or None
            }

            # Skip if no name
            if contact_dict["name"]:
                contacts_data.append(contact_dict)

        # Bulk import
        imported_count = await contact_service.bulk_import_contacts(
            contacts_data=contacts_data,
            organization_id=org_context["organization_id"],
            user_id=user["sub"]
        )

        logger.info(f"Imported {imported_count} contacts for organization {org_context['organization_id']}")

        return {
            "imported": imported_count,
            "total_rows": len(contacts_data)
        }

    except Exception as e:
        logger.error(f"Error importing contacts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import contacts: {str(e)}"
        )


@router.post("/contacts/segment/preview", response_model=SegmentPreviewResponse)
async def preview_segment(
    segment_filter: SegmentFilter,
    campaign_type: CampaignType = Query(..., description="Campaign type for opt-out filtering"),
    user=Depends(get_current_user),
    org_context=Depends(get_organization_context)
):
    """
    Preview contacts that would be targeted by a segment filter.

    Args:
        segment_filter: Filter criteria
        campaign_type: Campaign type for opt-out filtering
        user: Current authenticated user
        org_context: Organization context

    Returns:
        Preview data with contact count, samples, and estimated cost
    """
    db = await get_database()
    campaign_service = CampaignService(db)

    try:
        preview = await campaign_service.preview_segment(
            segment_filter=segment_filter,
            organization_id=org_context["organization_id"],
            campaign_type=campaign_type
        )

        return preview

    except Exception as e:
        logger.error(f"Error previewing segment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to preview segment: {str(e)}"
        )


# ==================== Campaign by ID Endpoints ====================
# NOTE: These /{campaign_id} routes must come AFTER /contacts routes.


@router.get("/{campaign_id}", response_model=Campaign)
async def get_campaign(
    campaign_id: str,
    user=Depends(get_current_user),
    org_context=Depends(get_organization_context)
):
    """
    Get campaign details by ID.

    Args:
        campaign_id: Campaign ID
        user: Current authenticated user
        org_context: Organization context

    Returns:
        Campaign details
    """
    db = await get_database()
    campaign_service = CampaignService(db)

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


@router.put("/{campaign_id}", response_model=Campaign)
async def update_campaign(
    campaign_id: str,
    updates: CampaignUpdate,
    user=Depends(get_current_user),
    org_context=Depends(get_organization_context)
):
    """
    Update a campaign (DRAFT only).

    Args:
        campaign_id: Campaign ID
        updates: Update data
        user: Current authenticated user
        org_context: Organization context

    Returns:
        Updated campaign
    """
    db = await get_database()
    campaign_service = CampaignService(db)

    try:
        campaign = await campaign_service.update_campaign(
            campaign_id=campaign_id,
            updates=updates,
            organization_id=org_context["organization_id"]
        )

        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Campaign {campaign_id} not found"
            )

        logger.info(f"Campaign {campaign_id} updated by user {user['sub']}")
        return campaign

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating campaign: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update campaign: {str(e)}"
        )


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(
    campaign_id: str,
    user=Depends(get_current_user),
    org_context=Depends(get_organization_context)
):
    """
    Delete a campaign (DRAFT only).

    Args:
        campaign_id: Campaign ID
        user: Current authenticated user
        org_context: Organization context
    """
    db = await get_database()
    campaign_service = CampaignService(db)

    try:
        deleted = await campaign_service.delete_campaign(
            campaign_id=campaign_id,
            organization_id=org_context["organization_id"]
        )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Campaign {campaign_id} not found"
            )

        logger.info(f"Campaign {campaign_id} deleted by user {user['sub']}")

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting campaign: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete campaign: {str(e)}"
        )


# ==================== Campaign Actions ====================


@router.post("/{campaign_id}/launch", response_model=Campaign)
async def launch_campaign(
    campaign_id: str,
    user=Depends(get_current_user),
    org_context=Depends(get_organization_context)
):
    """
    Launch a campaign to start sending messages.

    Args:
        campaign_id: Campaign ID
        user: Current authenticated user
        org_context: Organization context

    Returns:
        Updated campaign with RUNNING status
    """
    db = await get_database()
    campaign_service = CampaignService(db)

    try:
        campaign = await campaign_service.launch_campaign(
            campaign_id=campaign_id,
            organization_id=org_context["organization_id"]
        )

        logger.info(
            f"Campaign {campaign_id} launched by user {user['sub']} "
            f"targeting {campaign.target_count} contacts"
        )
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
            detail=f"Failed to launch campaign: {str(e)}"
        )


@router.post("/{campaign_id}/pause", response_model=Campaign)
async def pause_campaign(
    campaign_id: str,
    user=Depends(get_current_user),
    org_context=Depends(get_organization_context)
):
    """
    Pause a running campaign.

    Args:
        campaign_id: Campaign ID
        user: Current authenticated user
        org_context: Organization context

    Returns:
        Updated campaign with PAUSED status
    """
    db = await get_database()
    campaign_service = CampaignService(db)

    try:
        campaign = await campaign_service.pause_campaign(
            campaign_id=campaign_id,
            organization_id=org_context["organization_id"]
        )

        logger.info(f"Campaign {campaign_id} paused by user {user['sub']}")
        return campaign

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error pausing campaign: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pause campaign: {str(e)}"
        )


@router.get("/{campaign_id}/analytics")
async def get_campaign_analytics(
    campaign_id: str,
    user=Depends(get_current_user),
    org_context=Depends(get_organization_context)
):
    """
    Get campaign analytics and metrics.

    Args:
        campaign_id: Campaign ID
        user: Current authenticated user
        org_context: Organization context

    Returns:
        Campaign analytics data
    """
    db = await get_database()
    campaign_service = CampaignService(db)

    try:
        analytics = await campaign_service.get_campaign_analytics(
            campaign_id=campaign_id,
            organization_id=org_context["organization_id"]
        )

        return analytics

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting campaign analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get campaign analytics: {str(e)}"
        )
