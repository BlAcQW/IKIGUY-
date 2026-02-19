"""
Centralized Contact Models

Unified contact/lead management for campaign targeting across all applications.

Used by: EstateFlow, ChurchFlow, StudyFlow, InkWave, EventFlow, etc.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


# ==================== Common Enums ====================


class ContactType(str, Enum):
    """Type of contact."""
    LEAD = "lead"
    CUSTOMER = "customer"
    PROSPECT = "prospect"
    MEMBER = "member"  # For ChurchFlow
    STUDENT = "student"  # For StudyFlow
    ATTENDEE = "attendee"  # For EventFlow


class InterestLevel(str, Enum):
    """Contact interest/engagement level."""
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"
    UNQUALIFIED = "unqualified"


# ==================== Contact Models ====================


class Contact(BaseModel):
    """
    Universal contact model.

    Core fields common to all apps, with flexible custom_data for app-specific fields.
    """
    id: str
    organization_id: str

    # Basic Info
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

    # Alternative contact methods
    secondary_email: Optional[str] = None
    secondary_phone: Optional[str] = None
    whatsapp_number: Optional[str] = None

    # Classification
    contact_type: ContactType = ContactType.LEAD
    interest_level: InterestLevel = InterestLevel.WARM
    tags: List[str] = Field(default_factory=list)
    source: Optional[str] = None  # "website", "referral", "event", etc.

    # Segmentation & Marketing
    segments: List[str] = Field(default_factory=list)  # For campaign targeting
    opt_out_channels: List[str] = Field(default_factory=list)  # ["email", "sms", "whatsapp"]

    # Engagement Tracking
    last_contacted: Optional[datetime] = None
    last_email_opened: Optional[datetime] = None
    last_email_clicked: Optional[datetime] = None
    total_campaigns_sent: int = 0
    total_campaigns_opened: int = 0

    # App-Specific Data
    # Each app can store its own fields here:
    # EstateFlow: {"property_preferences": [...], "budget": 500000}
    # ChurchFlow: {"membership_status": "active", "ministry": "worship"}
    # StudyFlow: {"grade_level": 10, "subjects": ["math", "physics"]}
    # EventFlow: {"preferred_event_types": ["conference", "workshop"]}
    custom_data: Dict[str, Any] = Field(default_factory=dict)

    # Notes & History
    notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None
    is_deleted: bool = False

    @property
    def name(self) -> str:
        """Full name."""
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def has_email(self) -> bool:
        """Check if contact has email."""
        return bool(self.email)

    @property
    def has_phone(self) -> bool:
        """Check if contact has phone."""
        return bool(self.phone)

    @property
    def can_receive_email(self) -> bool:
        """Check if contact can receive email campaigns."""
        return self.has_email and "email" not in self.opt_out_channels

    @property
    def can_receive_sms(self) -> bool:
        """Check if contact can receive SMS campaigns."""
        return self.has_phone and "sms" not in self.opt_out_channels

    @property
    def can_receive_whatsapp(self) -> bool:
        """Check if contact can receive WhatsApp campaigns."""
        has_number = bool(self.whatsapp_number or self.phone)
        return has_number and "whatsapp" not in self.opt_out_channels

    @property
    def can_receive_voice(self) -> bool:
        """Check if contact can receive voice campaigns."""
        return self.has_phone and "voice" not in self.opt_out_channels

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ContactCreate(BaseModel):
    """Request model for creating a contact."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    secondary_email: Optional[str] = None
    secondary_phone: Optional[str] = None
    whatsapp_number: Optional[str] = None
    contact_type: ContactType = ContactType.LEAD
    interest_level: InterestLevel = InterestLevel.WARM
    tags: List[str] = Field(default_factory=list)
    source: Optional[str] = None
    segments: List[str] = Field(default_factory=list)
    custom_data: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None


class ContactUpdate(BaseModel):
    """Request model for updating a contact."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    secondary_email: Optional[str] = None
    secondary_phone: Optional[str] = None
    whatsapp_number: Optional[str] = None
    contact_type: Optional[ContactType] = None
    interest_level: Optional[InterestLevel] = None
    tags: Optional[List[str]] = None
    source: Optional[str] = None
    segments: Optional[List[str]] = None
    opt_out_channels: Optional[List[str]] = None
    custom_data: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class ContactFilters(BaseModel):
    """Filters for listing contacts."""
    contact_type: Optional[ContactType] = None
    interest_level: Optional[InterestLevel] = None
    tags: Optional[List[str]] = None
    segments: Optional[List[str]] = None
    has_email: Optional[bool] = None
    has_phone: Optional[bool] = None
    source: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    search: Optional[str] = None  # Search in name/email/phone
    exclude_opted_out: bool = False
    opted_out_channel: Optional[str] = None  # Filter by specific opt-out channel
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    sort_by: str = "created_at"
    sort_order: str = "desc"

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ContactListResponse(BaseModel):
    """Response model for contact list."""
    contacts: List[Contact]
    total: int
    limit: int
    offset: int
    has_more: bool


class ContactImportResult(BaseModel):
    """Result of contact import operation."""
    total_rows: int
    imported: int
    updated: int
    skipped: int
    errors: List[Dict[str, str]] = Field(default_factory=list)
    imported_ids: List[str] = Field(default_factory=list)


class ContactStats(BaseModel):
    """Contact database statistics."""
    total_contacts: int = 0
    leads: int = 0
    customers: int = 0
    prospects: int = 0
    hot: int = 0
    warm: int = 0
    cold: int = 0
    with_email: int = 0
    with_phone: int = 0
    opted_out_email: int = 0
    opted_out_sms: int = 0
    created_this_month: int = 0
    created_this_week: int = 0
