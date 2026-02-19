"""
Agent Data Models

Handles real estate agent profiles, contact information, and performance metrics.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, EmailStr


class AgentStatus(str, Enum):
    """Agent account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_LEAVE = "on_leave"


class AgentSpecialization(str, Enum):
    """Agent specialization areas"""
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    LUXURY = "luxury"
    INDUSTRIAL = "industrial"
    LAND = "land"
    RENTAL = "rental"


class DaySchedule(BaseModel):
    """Schedule for a single day"""
    start: str = Field(..., description="Start time (HH:MM format)", pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    end: str = Field(..., description="End time (HH:MM format)", pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    available: bool = Field(default=True, description="Whether agent works this day")


class WorkingHours(BaseModel):
    """Agent's weekly working schedule"""
    monday: Optional[DaySchedule] = Field(None, description="Monday schedule")
    tuesday: Optional[DaySchedule] = Field(None, description="Tuesday schedule")
    wednesday: Optional[DaySchedule] = Field(None, description="Wednesday schedule")
    thursday: Optional[DaySchedule] = Field(None, description="Thursday schedule")
    friday: Optional[DaySchedule] = Field(None, description="Friday schedule")
    saturday: Optional[DaySchedule] = Field(None, description="Saturday schedule")
    sunday: Optional[DaySchedule] = Field(None, description="Sunday schedule")


class Agent(BaseModel):
    """Real estate agent profile"""
    id: str = Field(..., description="Unique agent ID")
    organization_id: str = Field(..., description="Organization ID")
    user_id: Optional[str] = Field(None, description="Linked user account ID (Supabase)")

    # Personal Information
    first_name: str = Field(..., description="First name", min_length=1, max_length=100)
    last_name: str = Field(..., description="Last name", min_length=1, max_length=100)
    email: EmailStr = Field(..., description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")

    # Professional Information
    license_number: Optional[str] = Field(None, description="Real estate license number")
    specializations: List[AgentSpecialization] = Field(
        default_factory=list,
        description="Areas of specialization"
    )
    bio: Optional[str] = Field(None, description="Agent biography", max_length=1000)
    photo_url: Optional[str] = Field(None, description="Profile photo URL")

    # Status
    status: AgentStatus = Field(default=AgentStatus.ACTIVE, description="Agent status")

    # Working Hours
    working_hours: Optional[WorkingHours] = Field(None, description="Weekly working schedule")
    timezone: str = Field(default="UTC", description="Agent timezone")

    # Booking Settings
    buffer_minutes: int = Field(default=15, ge=0, le=120, description="Buffer time between bookings")
    max_bookings_per_day: int = Field(default=10, ge=1, le=50, description="Maximum daily bookings")
    default_tour_duration: int = Field(default=30, ge=15, le=180, description="Default tour duration in minutes")

    # Performance Metrics
    total_bookings: int = Field(default=0, description="Total lifetime bookings")
    completed_tours: int = Field(default=0, description="Completed tours count")
    average_rating: float = Field(default=0.0, ge=0, le=5, description="Average customer rating")
    properties_sold: int = Field(default=0, description="Total properties sold")

    # Calendar Integration
    google_calendar_id: Optional[str] = Field(None, description="Google Calendar ID")
    outlook_calendar_id: Optional[str] = Field(None, description="Outlook Calendar ID")
    calendar_sync_enabled: bool = Field(default=False, description="Whether calendar sync is enabled")

    # Languages
    languages: List[str] = Field(default_factory=lambda: ["English"], description="Languages spoken")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Created timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Updated timestamp")
    last_active_at: Optional[datetime] = Field(None, description="Last activity timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "agent_abc123",
                "organization_id": "org_xyz789",
                "user_id": "user_123",
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "phone": "+1234567890",
                "license_number": "RE12345",
                "specializations": ["residential", "luxury"],
                "bio": "Experienced agent specializing in luxury residential properties",
                "status": "active",
                "working_hours": {
                    "monday": {"start": "09:00", "end": "17:00", "available": True},
                    "tuesday": {"start": "09:00", "end": "17:00", "available": True},
                    "wednesday": {"start": "09:00", "end": "17:00", "available": True},
                    "thursday": {"start": "09:00", "end": "17:00", "available": True},
                    "friday": {"start": "09:00", "end": "17:00", "available": True},
                },
                "timezone": "America/New_York",
                "buffer_minutes": 15,
                "max_bookings_per_day": 8,
                "languages": ["English", "Spanish"]
            }
        }


class AgentCreate(BaseModel):
    """Schema for creating a new agent"""
    user_id: Optional[str] = Field(None, description="Linked user account ID")
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = None
    license_number: Optional[str] = None
    specializations: List[AgentSpecialization] = Field(default_factory=list)
    bio: Optional[str] = Field(None, max_length=1000)
    photo_url: Optional[str] = None
    working_hours: Optional[WorkingHours] = None
    timezone: str = "UTC"
    buffer_minutes: int = 15
    max_bookings_per_day: int = 10
    languages: List[str] = Field(default_factory=lambda: ["English"])


class AgentUpdate(BaseModel):
    """Schema for updating an agent"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    license_number: Optional[str] = None
    specializations: Optional[List[AgentSpecialization]] = None
    bio: Optional[str] = Field(None, max_length=1000)
    photo_url: Optional[str] = None
    status: Optional[AgentStatus] = None
    working_hours: Optional[WorkingHours] = None
    timezone: Optional[str] = None
    buffer_minutes: Optional[int] = Field(None, ge=0, le=120)
    max_bookings_per_day: Optional[int] = Field(None, ge=1, le=50)
    default_tour_duration: Optional[int] = Field(None, ge=15, le=180)
    google_calendar_id: Optional[str] = None
    outlook_calendar_id: Optional[str] = None
    calendar_sync_enabled: Optional[bool] = None
    languages: Optional[List[str]] = None


class AgentListResponse(BaseModel):
    """Response for listing agents"""
    agents: List[Agent] = Field(..., description="List of agents")
    total: int = Field(..., description="Total count")
    limit: int = Field(..., description="Page size")
    offset: int = Field(..., description="Page offset")


class AgentStats(BaseModel):
    """Agent performance statistics"""
    agent_id: str
    total_bookings: int
    completed_tours: int
    cancelled_bookings: int
    no_shows: int
    completion_rate: float = Field(..., description="Percentage of completed tours")
    average_rating: float
    total_ratings: int
    upcoming_bookings: int
    bookings_this_week: int
    bookings_this_month: int
