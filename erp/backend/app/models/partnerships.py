"""
Partnership Management Models.

Handles partnership tracking, proposals, and interactions.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import Field, EmailStr
from enum import Enum

from .base import BaseModel


class PartnershipType(str, Enum):
    """Partnership type enumeration."""

    VENDOR = "vendor"
    TECHNOLOGY = "technology"
    STRATEGIC = "strategic"
    RESELLER = "reseller"
    DISTRIBUTOR = "distributor"
    AFFILIATE = "affiliate"
    CONSULTING = "consulting"
    OTHER = "other"


class PartnershipStage(str, Enum):
    """Partnership stage enumeration."""

    PROSPECT = "prospect"
    INITIAL_CONTACT = "initial_contact"
    DISCUSSION = "discussion"
    PROPOSAL_SENT = "proposal_sent"
    NEGOTIATION = "negotiation"
    AGREEMENT_SIGNED = "agreement_signed"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    INACTIVE = "inactive"
    TERMINATED = "terminated"


class InteractionType(str, Enum):
    """Interaction type enumeration."""

    EMAIL = "email"
    PHONE_CALL = "phone_call"
    MEETING = "meeting"
    VIDEO_CALL = "video_call"
    PROPOSAL_SENT = "proposal_sent"
    PROPOSAL_RECEIVED = "proposal_received"
    CONTRACT_REVIEW = "contract_review"
    OTHER = "other"


class PartnershipInteraction(BaseModel):
    """
    Partnership interaction model.

    Tracks individual interactions with a partner.
    """

    partnership_id: str = Field(..., description="Partnership ID this interaction belongs to")
    interaction_type: InteractionType = Field(..., description="Type of interaction")
    subject: str = Field(..., description="Interaction subject/title")
    description: Optional[str] = Field(None, description="Detailed description")
    interaction_date: datetime = Field(default_factory=datetime.utcnow, description="When interaction occurred")
    participants: Optional[List[str]] = Field(default=[], description="List of participant names/emails")
    attachments: Optional[List[str]] = Field(default=[], description="File paths to attachments")
    follow_up_required: bool = Field(default=False, description="Whether follow-up is needed")
    follow_up_date: Optional[datetime] = Field(None, description="When to follow up")
    notes: Optional[str] = Field(None, description="Additional notes")


class Partnership(BaseModel):
    """
    Partnership model.

    Central record for all partnership information.
    """

    # Partner information
    partner_name: str = Field(..., description="Partner organization name")
    partnership_type: PartnershipType = Field(..., description="Type of partnership")
    stage: PartnershipStage = Field(default=PartnershipStage.PROSPECT, description="Current stage")

    # Contact information
    primary_contact_name: Optional[str] = Field(None, description="Primary contact person")
    primary_contact_email: Optional[EmailStr] = Field(None, description="Primary contact email")
    primary_contact_phone: Optional[str] = Field(None, description="Primary contact phone")
    primary_contact_title: Optional[str] = Field(None, description="Primary contact job title")

    # Secondary contact (optional)
    secondary_contact_name: Optional[str] = Field(None, description="Secondary contact person")
    secondary_contact_email: Optional[EmailStr] = Field(None, description="Secondary contact email")
    secondary_contact_phone: Optional[str] = Field(None, description="Secondary contact phone")

    # Partner details
    website: Optional[str] = Field(None, description="Partner website URL")
    industry: Optional[str] = Field(None, description="Partner industry")
    company_size: Optional[str] = Field(None, description="Partner company size")
    location: Optional[str] = Field(None, description="Partner location/headquarters")

    # Address
    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None

    # Partnership details
    description: Optional[str] = Field(None, description="Partnership description")
    value_proposition: Optional[str] = Field(None, description="What value this partnership brings")
    expected_revenue: Optional[float] = Field(None, description="Expected annual revenue from partnership")
    actual_revenue: Optional[float] = Field(None, description="Actual revenue from partnership")

    # Dates
    first_contact_date: Optional[datetime] = Field(None, description="When first contacted")
    proposal_sent_date: Optional[datetime] = Field(None, description="When proposal was sent")
    agreement_signed_date: Optional[datetime] = Field(None, description="When agreement was signed")
    agreement_start_date: Optional[datetime] = Field(None, description="Partnership start date")
    agreement_end_date: Optional[datetime] = Field(None, description="Partnership end date")
    renewal_date: Optional[datetime] = Field(None, description="Next renewal date")

    # Proposal and documents
    proposal_title: Optional[str] = Field(None, description="Proposal title")
    proposal_content: Optional[str] = Field(None, description="Proposal content (rich text/markdown)")
    proposal_files: Optional[List[str]] = Field(default=[], description="Uploaded proposal file paths")
    contract_files: Optional[List[str]] = Field(default=[], description="Contract file paths")
    other_documents: Optional[List[str]] = Field(default=[], description="Other document file paths")

    # Financial terms
    payment_terms: Optional[str] = Field(None, description="Payment terms")
    revenue_share_percentage: Optional[float] = Field(None, description="Revenue share percentage if applicable")
    annual_fee: Optional[float] = Field(None, description="Annual partnership fee if applicable")

    # Management
    assigned_to: Optional[str] = Field(None, description="User ID responsible for this partnership")
    status_notes: Optional[str] = Field(None, description="Current status notes")
    next_action: Optional[str] = Field(None, description="Next action to take")
    next_action_date: Optional[datetime] = Field(None, description="When to take next action")

    # Metrics
    interaction_count: int = Field(default=0, description="Number of interactions recorded")
    last_interaction_date: Optional[datetime] = Field(None, description="Date of last interaction")

    # Tags and categorization
    tags: Optional[List[str]] = Field(default=[], description="Tags for categorization")
    custom_fields: Optional[dict] = Field(default={}, description="Custom fields for extensibility")
