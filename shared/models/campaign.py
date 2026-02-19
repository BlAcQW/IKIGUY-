"""
Centralized Campaign Models

Unified models for multi-channel marketing campaigns across all applications.
Supports Voice, SMS, WhatsApp, and Email campaigns.

Used by: EstateFlow, ChurchFlow, StudyFlow, InkWave, EventFlow, etc.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


# ==================== Enums ====================


class CampaignType(str, Enum):
    """Type of marketing campaign channel."""
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


class CampaignMessageStatus(str, Enum):
    """Individual message delivery status."""
    PENDING = "pending"
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    FAILED = "failed"
    BOUNCED = "bounced"


# ==================== Message Template Models ====================


class MessageTemplate(BaseModel):
    """
    Message template for campaigns.

    Different fields are used based on campaign type:
    - Voice: voice_id (Vapi assistant ID)
    - SMS/WhatsApp: text_content
    - Email: subject + html_content
    """
    # Voice campaign fields
    voice_id: Optional[str] = None  # Vapi assistant ID

    # SMS/WhatsApp fields
    text_content: Optional[str] = None

    # Email fields
    subject: Optional[str] = None
    html_content: Optional[str] = None
    text_version: Optional[str] = None  # Plain text fallback

    # Attachments (for email/whatsapp)
    attachments: List[Dict[str, str]] = Field(default_factory=list)  # [{url, filename}]

    # Template variables for personalization
    # e.g., {{name}}, {{property_type}}, {{budget}}
    variables: List[str] = Field(default_factory=list)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ScheduleConfig(BaseModel):
    """Campaign scheduling configuration."""
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    timezone: str = "UTC"
    business_hours_only: bool = False
    business_hours_start: str = "09:00"  # HH:MM
    business_hours_end: str = "18:00"    # HH:MM
    exclude_weekends: bool = False

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DeliveryConfig(BaseModel):
    """Campaign delivery configuration."""
    # Rate limiting
    max_concurrent: int = 10  # Max simultaneous deliveries
    rate_per_second: float = 1.0  # Messages per second
    batch_size: int = 100  # Messages per batch

    # Retry settings
    max_retries: int = 2
    retry_delay_seconds: int = 60
    retry_on_statuses: List[str] = Field(default_factory=lambda: ["failed", "no_answer"])

    # Provider-specific settings
    provider_settings: Dict[str, Any] = Field(default_factory=dict)


# ==================== Segment Filter Models ====================


class SegmentFilter(BaseModel):
    """
    Filter for segmenting contacts.

    Apps can extend with their own fields.
    """
    # Common filters
    tags: Optional[List[str]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    last_contacted_after: Optional[datetime] = None
    last_contacted_before: Optional[datetime] = None

    # Channel opt-out
    exclude_opted_out: bool = True

    # Custom filters (app-specific)
    # Apps can add their own filters like:
    # - property_types, budget_min/max (EstateFlow)
    # - membership_level (ChurchFlow)
    # - grade_level (StudyFlow)
    # - event_type (EventFlow)
    custom_filters: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ==================== Campaign Models ====================


class Campaign(BaseModel):
    """
    Main campaign model.

    Represents a marketing campaign across any channel.
    """
    id: str
    organization_id: str
    user_id: str  # Creator

    # Basic Info
    name: str = Field(..., min_length=1, max_length=255)
    campaign_type: CampaignType
    status: CampaignStatus = CampaignStatus.DRAFT

    # Message Template
    message_template: MessageTemplate

    # Audience Segmentation
    segment_filter: Optional[SegmentFilter] = None
    target_count: int = 0  # Number of contacts targeted

    # Scheduling & Delivery
    schedule_config: ScheduleConfig = Field(default_factory=ScheduleConfig)
    delivery_config: DeliveryConfig = Field(default_factory=DeliveryConfig)

    # Campaign Metrics
    sent_count: int = 0
    delivered_count: int = 0
    opened_count: int = 0
    clicked_count: int = 0
    failed_count: int = 0

    # Cost Tracking
    total_cost: float = 0.0
    cost_per_message: float = 0.0
    currency: str = "GHS"

    # External Integration
    external_campaign_id: Optional[str] = None  # ID from Vapi/Arkesel/etc.

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

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
    delivery_config: Optional[DeliveryConfig] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CampaignUpdate(BaseModel):
    """Request model for updating a campaign."""
    name: Optional[str] = None
    message_template: Optional[MessageTemplate] = None
    segment_filter: Optional[SegmentFilter] = None
    schedule_config: Optional[ScheduleConfig] = None
    delivery_config: Optional[DeliveryConfig] = None
    status: Optional[CampaignStatus] = None
    metadata: Optional[Dict[str, Any]] = None


class CampaignFilters(BaseModel):
    """Filters for listing campaigns."""
    campaign_type: Optional[CampaignType] = None
    status: Optional[CampaignStatus] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    search: Optional[str] = None  # Search in name
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    sort_by: str = "created_at"
    sort_order: str = "desc"  # "asc" or "desc"

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CampaignListResponse(BaseModel):
    """Response model for campaign list."""
    campaigns: List[Campaign]
    total: int
    limit: int
    offset: int
    has_more: bool


# ==================== Campaign Message Models ====================


class CampaignMessage(BaseModel):
    """
    Individual message in a campaign.

    Tracks delivery status for each recipient.
    """
    id: str
    campaign_id: str
    organization_id: str
    contact_id: str

    # Recipient Info
    recipient_phone: Optional[str] = None  # For SMS/WhatsApp/Voice
    recipient_email: Optional[str] = None  # For Email
    recipient_name: Optional[str] = None

    # Message Content (rendered from template)
    rendered_content: str

    # Delivery Status
    status: CampaignMessageStatus = CampaignMessageStatus.PENDING
    attempts: int = 0
    last_attempt: Optional[datetime] = None

    # Delivery Tracking
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None

    # Error Info
    error_message: Optional[str] = None
    error_code: Optional[str] = None

    # External Integration
    external_message_id: Optional[str] = None  # Provider message ID

    # Cost
    cost: float = 0.0

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ==================== Analytics Models ====================


class CampaignAnalytics(BaseModel):
    """Campaign performance analytics."""
    campaign_id: str
    campaign_name: str
    campaign_type: CampaignType
    status: CampaignStatus

    # Counts
    total_recipients: int = 0
    sent: int = 0
    delivered: int = 0
    opened: int = 0
    clicked: int = 0
    failed: int = 0
    pending: int = 0

    # Rates
    delivery_rate: float = 0.0  # delivered / sent
    open_rate: float = 0.0      # opened / delivered
    click_rate: float = 0.0     # clicked / opened
    failure_rate: float = 0.0   # failed / sent

    # Cost
    total_cost: float = 0.0
    cost_per_delivery: float = 0.0
    currency: str = "GHS"

    # Timing
    average_delivery_time_seconds: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None

    # Top Errors (if any)
    top_errors: List[Dict[str, Any]] = Field(default_factory=list)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SegmentPreview(BaseModel):
    """Preview of segment matching."""
    contact_count: int
    estimated_cost: float
    currency: str = "GHS"
    sample_contacts: List[Dict[str, Any]] = Field(default_factory=list)  # First 5 contacts
