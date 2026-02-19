"""
Lead and contact models for Asenda.ai
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from enum import Enum


class LeadSource(str, Enum):
    """Source of the lead."""
    CONTACT_FORM = "contact_form"
    DEMO_REQUEST = "demo_request"
    NEWSLETTER = "newsletter"
    MEETING_SCHEDULE = "meeting_schedule"


class LeadStatus(str, Enum):
    """Status of the lead."""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    DEMO_SCHEDULED = "demo_scheduled"
    CONVERTED = "converted"
    LOST = "lost"


class LeadCreate(BaseModel):
    """Schema for creating a new lead."""
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    company: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    message: Optional[str] = Field(None, max_length=2000)
    source: LeadSource = LeadSource.CONTACT_FORM
    services_interested: Optional[List[str]] = None
    company_size: Optional[str] = None
    industry: Optional[str] = None


class DemoRequest(BaseModel):
    """Schema for demo request."""
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    company: str = Field(..., min_length=2, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    job_title: Optional[str] = Field(None, max_length=100)
    company_size: Optional[str] = None
    use_case: Optional[str] = Field(None, max_length=1000)
    preferred_date: Optional[str] = None
    preferred_time: Optional[str] = None
    timezone: Optional[str] = "UTC"


class MeetingSchedule(BaseModel):
    """Schema for meeting scheduling."""
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    company: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    meeting_type: str = Field(default="discovery_call")
    preferred_datetime: Optional[datetime] = None
    timezone: Optional[str] = "UTC"
    notes: Optional[str] = Field(None, max_length=500)


class NewsletterSubscribe(BaseModel):
    """Schema for newsletter subscription."""
    email: EmailStr
    name: Optional[str] = Field(None, max_length=100)


class LeadResponse(BaseModel):
    """Response schema for lead operations."""
    success: bool
    message: str
    lead_id: Optional[str] = None


class Lead(BaseModel):
    """Full lead model stored in database."""
    id: Optional[str] = None
    name: str
    email: str
    company: Optional[str] = None
    phone: Optional[str] = None
    message: Optional[str] = None
    source: LeadSource
    status: LeadStatus = LeadStatus.NEW
    services_interested: Optional[List[str]] = None
    company_size: Optional[str] = None
    industry: Optional[str] = None
    job_title: Optional[str] = None
    use_case: Optional[str] = None
    preferred_date: Optional[str] = None
    preferred_time: Optional[str] = None
    timezone: Optional[str] = None
    meeting_type: Optional[str] = None
    notes: Optional[str] = None
    email_sent: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
