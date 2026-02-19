"""
Partnership schemas for API requests and responses.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr

from app.models.partnerships import PartnershipType, PartnershipStage, InteractionType


# Partnership Schemas
class PartnershipCreate(BaseModel):
    """Schema for creating a partnership."""

    partner_name: str
    partnership_type: PartnershipType
    stage: Optional[PartnershipStage] = PartnershipStage.PROSPECT

    # Contact information
    primary_contact_name: Optional[str] = None
    primary_contact_email: Optional[EmailStr] = None
    primary_contact_phone: Optional[str] = None
    primary_contact_title: Optional[str] = None

    secondary_contact_name: Optional[str] = None
    secondary_contact_email: Optional[EmailStr] = None
    secondary_contact_phone: Optional[str] = None

    # Partner details
    website: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    location: Optional[str] = None

    # Address
    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None

    # Partnership details
    description: Optional[str] = None
    value_proposition: Optional[str] = None
    expected_revenue: Optional[float] = None

    # Dates
    first_contact_date: Optional[datetime] = None
    agreement_start_date: Optional[datetime] = None
    agreement_end_date: Optional[datetime] = None

    # Proposal
    proposal_title: Optional[str] = None
    proposal_content: Optional[str] = None

    # Financial terms
    payment_terms: Optional[str] = None
    revenue_share_percentage: Optional[float] = None
    annual_fee: Optional[float] = None

    # Management
    assigned_to: Optional[str] = None
    status_notes: Optional[str] = None
    next_action: Optional[str] = None
    next_action_date: Optional[datetime] = None

    # Tags
    tags: Optional[List[str]] = []
    custom_fields: Optional[dict] = {}


class PartnershipUpdate(BaseModel):
    """Schema for updating a partnership."""

    partner_name: Optional[str] = None
    partnership_type: Optional[PartnershipType] = None
    stage: Optional[PartnershipStage] = None

    # Contact information
    primary_contact_name: Optional[str] = None
    primary_contact_email: Optional[EmailStr] = None
    primary_contact_phone: Optional[str] = None
    primary_contact_title: Optional[str] = None

    secondary_contact_name: Optional[str] = None
    secondary_contact_email: Optional[EmailStr] = None
    secondary_contact_phone: Optional[str] = None

    # Partner details
    website: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    location: Optional[str] = None

    # Address
    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None

    # Partnership details
    description: Optional[str] = None
    value_proposition: Optional[str] = None
    expected_revenue: Optional[float] = None
    actual_revenue: Optional[float] = None

    # Dates
    first_contact_date: Optional[datetime] = None
    proposal_sent_date: Optional[datetime] = None
    agreement_signed_date: Optional[datetime] = None
    agreement_start_date: Optional[datetime] = None
    agreement_end_date: Optional[datetime] = None
    renewal_date: Optional[datetime] = None

    # Proposal
    proposal_title: Optional[str] = None
    proposal_content: Optional[str] = None

    # Financial terms
    payment_terms: Optional[str] = None
    revenue_share_percentage: Optional[float] = None
    annual_fee: Optional[float] = None

    # Management
    assigned_to: Optional[str] = None
    status_notes: Optional[str] = None
    next_action: Optional[str] = None
    next_action_date: Optional[datetime] = None

    # Tags
    tags: Optional[List[str]] = None
    custom_fields: Optional[dict] = None


# Partnership Interaction Schemas
class PartnershipInteractionCreate(BaseModel):
    """Schema for creating a partnership interaction."""

    partnership_id: str
    interaction_type: InteractionType
    subject: str
    description: Optional[str] = None
    interaction_date: Optional[datetime] = None
    participants: Optional[List[str]] = []
    follow_up_required: bool = False
    follow_up_date: Optional[datetime] = None
    notes: Optional[str] = None


class PartnershipInteractionUpdate(BaseModel):
    """Schema for updating a partnership interaction."""

    interaction_type: Optional[InteractionType] = None
    subject: Optional[str] = None
    description: Optional[str] = None
    interaction_date: Optional[datetime] = None
    participants: Optional[List[str]] = None
    follow_up_required: Optional[bool] = None
    follow_up_date: Optional[datetime] = None
    notes: Optional[str] = None
