"""
API routes for lead management.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional
import logging

from ..models.lead import (
    LeadCreate,
    LeadResponse,
    LeadSource,
    LeadStatus,
    DemoRequest,
    MeetingSchedule,
    NewsletterSubscribe,
    Lead,
)
from ..services.lead_service import LeadService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/leads", tags=["leads"])

# Global lead service instance (will be set by main app)
_lead_service: Optional[LeadService] = None


def get_lead_service() -> LeadService:
    """Get the lead service instance."""
    if _lead_service is None:
        raise HTTPException(status_code=500, detail="Lead service not initialized")
    return _lead_service


def set_lead_service(service: LeadService):
    """Set the lead service instance."""
    global _lead_service
    _lead_service = service


@router.post("/contact", response_model=LeadResponse)
async def submit_contact_form(
    lead_data: LeadCreate,
    lead_service: LeadService = Depends(get_lead_service),
):
    """
    Submit a contact form.

    Creates a new lead and sends confirmation email.
    """
    try:
        lead_id = await lead_service.create_lead(lead_data)
        return LeadResponse(
            success=True,
            message="Thank you for contacting us! We'll be in touch within 24 hours.",
            lead_id=lead_id,
        )
    except Exception as e:
        logger.error(f"Error creating contact lead: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit contact form")


@router.post("/demo", response_model=LeadResponse)
async def request_demo(
    demo_data: DemoRequest,
    lead_service: LeadService = Depends(get_lead_service),
):
    """
    Request a product demo.

    Creates a demo request and sends confirmation email.
    """
    try:
        lead_id = await lead_service.create_demo_request(demo_data)
        return LeadResponse(
            success=True,
            message="Demo request received! We'll contact you within 24 hours to confirm your time.",
            lead_id=lead_id,
        )
    except Exception as e:
        logger.error(f"Error creating demo request: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit demo request")


@router.post("/meeting", response_model=LeadResponse)
async def schedule_meeting(
    meeting_data: MeetingSchedule,
    lead_service: LeadService = Depends(get_lead_service),
):
    """
    Schedule a meeting.

    Creates a meeting request and sends confirmation email.
    """
    try:
        lead_id = await lead_service.create_meeting_schedule(meeting_data)
        return LeadResponse(
            success=True,
            message="Meeting request received! We'll send a calendar invite within 24 hours.",
            lead_id=lead_id,
        )
    except Exception as e:
        logger.error(f"Error creating meeting schedule: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to schedule meeting")


@router.post("/newsletter", response_model=LeadResponse)
async def subscribe_newsletter(
    subscribe_data: NewsletterSubscribe,
    lead_service: LeadService = Depends(get_lead_service),
):
    """
    Subscribe to the newsletter.

    Creates newsletter subscription and sends welcome email.
    """
    try:
        subscription_id = await lead_service.subscribe_newsletter(subscribe_data)
        return LeadResponse(
            success=True,
            message="You're subscribed! Check your inbox for a welcome email.",
            lead_id=subscription_id,
        )
    except Exception as e:
        logger.error(f"Error creating newsletter subscription: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to subscribe to newsletter")


# Admin routes (should be protected in production)
@router.get("/", response_model=List[Lead])
async def list_leads(
    source: Optional[LeadSource] = None,
    status: Optional[LeadStatus] = None,
    limit: int = 100,
    skip: int = 0,
    lead_service: LeadService = Depends(get_lead_service),
):
    """
    List all leads with optional filtering.

    Note: This endpoint should be protected with authentication in production.
    """
    return await lead_service.get_leads(
        source=source,
        status=status,
        limit=limit,
        skip=skip,
    )


@router.get("/{lead_id}", response_model=Lead)
async def get_lead(
    lead_id: str,
    lead_service: LeadService = Depends(get_lead_service),
):
    """
    Get a specific lead by ID.

    Note: This endpoint should be protected with authentication in production.
    """
    lead = await lead_service.get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.patch("/{lead_id}/status")
async def update_lead_status(
    lead_id: str,
    status: LeadStatus,
    lead_service: LeadService = Depends(get_lead_service),
):
    """
    Update a lead's status.

    Note: This endpoint should be protected with authentication in production.
    """
    success = await lead_service.update_lead_status(lead_id, status)
    if not success:
        raise HTTPException(status_code=404, detail="Lead not found or update failed")
    return {"success": True, "message": f"Lead status updated to {status.value}"}
