"""
Campaign models for EstateFlow.

Handles multi-channel marketing campaigns (Voice, SMS, WhatsApp, Email).
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class CampaignType(str, Enum):
    """Type of marketing campaign."""
    VOICE = "voice"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    EMAIL = "email"


class CampaignStatus(str, Enum):
    """Campaign execution status."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class InterestStatus(str, Enum):
    """Lead interest level."""
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"
    UNQUALIFIED = "unqualified"


class LeadStatus(str, Enum):
    """Lead progression status."""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    NEGOTIATING = "negotiating"
    CONVERTED = "converted"
    LOST = "lost"


# ==================== Contact Models ====================


class Contact(BaseModel):
    """
    Contact/Lead for campaigns.

    Represents potential buyers, renters, or investors.
    """
    id: str
    organization_id: str

    # Basic Info
    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[str] = None
    phone: Optional[str] = None

    # Segmentation Fields
    property_type_preferences: List[str] = Field(default_factory=list)  # ["apartment", "villa"]
    location_preferences: List[str] = Field(default_factory=list)  # ["Accra", "Kumasi"]
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    bedrooms_min: Optional[int] = None
    bedrooms_max: Optional[int] = None

    # Lead Tracking
    interest_status: InterestStatus = InterestStatus.WARM
    lead_status: LeadStatus = LeadStatus.NEW
    tags: List[str] = Field(default_factory=list)  # ["investor", "first_time_buyer"]
    source: Optional[str] = None  # "website", "referral", "open_house"

    # Opt-out Management
    opt_out_channels: List[str] = Field(default_factory=list)  # ["sms", "email"]

    # Custom Fields
    notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_contacted: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ContactCreate(BaseModel):
    """Request model for creating a contact."""
    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[str] = None
    phone: Optional[str] = None
    property_type_preferences: List[str] = Field(default_factory=list)
    location_preferences: List[str] = Field(default_factory=list)
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    bedrooms_min: Optional[int] = None
    bedrooms_max: Optional[int] = None
    interest_status: InterestStatus = InterestStatus.WARM
    lead_status: LeadStatus = LeadStatus.NEW
    tags: List[str] = Field(default_factory=list)
    source: Optional[str] = None
    notes: Optional[str] = None


class ContactUpdate(BaseModel):
    """Request model for updating a contact."""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    property_type_preferences: Optional[List[str]] = None
    location_preferences: Optional[List[str]] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    bedrooms_min: Optional[int] = None
    bedrooms_max: Optional[int] = None
    interest_status: Optional[InterestStatus] = None
    lead_status: Optional[LeadStatus] = None
    tags: Optional[List[str]] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    opt_out_channels: Optional[List[str]] = None


# ==================== Segment/Filter Models ====================


class SegmentFilter(BaseModel):
    """
    Filter for segmenting contacts.

    Used to select campaign recipients based on criteria.
    """
    property_types: Optional[List[str]] = None  # ["apartment", "villa"]
    locations: Optional[List[str]] = None  # ["Accra", "Kumasi"]
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    bedrooms_min: Optional[int] = None
    bedrooms_max: Optional[int] = None
    interest_statuses: Optional[List[InterestStatus]] = None
    lead_statuses: Optional[List[LeadStatus]] = None
    tags: Optional[List[str]] = None  # All tags must match (AND logic)
    exclude_opted_out: bool = True  # Exclude contacts opted out of campaign channel


# ==================== Campaign Models ====================


class MessageTemplate(BaseModel):
    """Message template for campaigns."""
    # For Voice
    tts_text: Optional[str] = None
    voice_provider: Optional[str] = "kokoro"  # "kokoro", "elevenlabs", etc.
    voice_id: Optional[str] = None

    # For SMS/WhatsApp
    text_content: Optional[str] = None

    # For Email
    subject: Optional[str] = None
    html_content: Optional[str] = None

    # Template variables (e.g., {{name}}, {{property_address}})
    variables: Dict[str, str] = Field(default_factory=dict)


class ScheduleConfig(BaseModel):
    """Campaign scheduling configuration."""
    scheduled_time: Optional[datetime] = None  # None = immediate
    time_zone: str = "UTC"

    # Drip campaign support
    is_drip: bool = False
    drip_delay_hours: Optional[int] = None  # Delay between messages in drip
    drip_message_count: Optional[int] = None


class Campaign(BaseModel):
    """Marketing campaign."""
    id: str
    organization_id: str
    user_id: str

    # Basic Info
    name: str = Field(..., min_length=1, max_length=255)
    campaign_type: CampaignType
    status: CampaignStatus = CampaignStatus.DRAFT

    # Message Configuration
    message_template: MessageTemplate

    # Targeting
    segment_filter: Optional[SegmentFilter] = None  # None = all contacts

    # Scheduling
    schedule_config: ScheduleConfig = Field(default_factory=ScheduleConfig)

    # Analytics Counters
    target_count: int = 0
    sent_count: int = 0
    delivered_count: int = 0
    opened_count: int = 0  # Email/WhatsApp only
    clicked_count: int = 0  # Email only
    failed_count: int = 0

    # Cost Tracking
    total_cost: float = 0.0

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Reference to external campaign IDs (SMS service, WhatsApp service, etc.)
    external_campaign_id: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CampaignCreate(BaseModel):
    """Request model for creating a campaign."""
    name: str = Field(..., min_length=1, max_length=255)
    campaign_type: CampaignType
    message_template: MessageTemplate
    segment_filter: Optional[SegmentFilter] = None
    schedule_config: Optional[ScheduleConfig] = None


class CampaignUpdate(BaseModel):
    """Request model for updating a campaign (DRAFT only)."""
    name: Optional[str] = None
    message_template: Optional[MessageTemplate] = None
    segment_filter: Optional[SegmentFilter] = None
    schedule_config: Optional[ScheduleConfig] = None


# ==================== Campaign Message Models ====================


class CampaignMessageStatus(str, Enum):
    """Individual message status within a campaign."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    FAILED = "failed"


class CampaignMessage(BaseModel):
    """Individual message sent as part of a campaign."""
    id: str
    campaign_id: str
    contact_id: str
    organization_id: str

    # Message Details
    to_address: str  # Phone number or email
    message_content: str

    # Status Tracking
    status: CampaignMessageStatus = CampaignMessageStatus.PENDING
    error_message: Optional[str] = None

    # External References
    provider_message_id: Optional[str] = None  # ID from SMS/Email provider

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ==================== Response Models ====================


class ContactListResponse(BaseModel):
    """Response for contact list endpoint."""
    contacts: List[Contact]
    total: int
    limit: int
    offset: int


class CampaignListResponse(BaseModel):
    """Response for campaign list endpoint."""
    campaigns: List[Campaign]
    total: int
    limit: int
    offset: int


class SegmentPreviewResponse(BaseModel):
    """Response for segment preview endpoint."""
    contact_count: int
    sample_contacts: List[Contact]
    estimated_cost: float
