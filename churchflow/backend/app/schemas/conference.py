"""
Conference request/response schemas.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class SpeakerResponse(BaseModel):
    """Speaker response schema."""

    name: str = Field(..., description="Speaker name")
    title: Optional[str] = Field(None, description="Speaker title/position")
    image_url: Optional[str] = Field(None, description="Speaker profile image URL")
    bio: Optional[str] = Field(None, description="Speaker biography")


class ConferenceResponse(BaseModel):
    """Conference response schema."""

    id: str = Field(..., description="Conference ID")
    name: str = Field(..., description="Conference name")
    description: Optional[str] = Field(None, description="Conference description")
    theme: Optional[str] = Field(None, description="Conference theme")
    banner_url: Optional[str] = Field(None, description="Banner image URL")
    venue: str = Field(..., description="Conference venue")
    venue_latitude: Optional[float] = Field(None, description="Venue latitude")
    venue_longitude: Optional[float] = Field(None, description="Venue longitude")
    venue_checkin_radius: Optional[int] = Field(1000, description="Check-in radius in meters")
    start_date: datetime = Field(..., description="Start date")
    end_date: datetime = Field(..., description="End date")
    registration_open: bool = Field(..., description="Registration open status")
    registration_deadline: Optional[datetime] = Field(None, description="Registration deadline")
    max_attendees: Optional[int] = Field(None, description="Maximum attendees")
    expected_attendance: Optional[int] = Field(None, description="Expected attendance")
    current_attendees: int = Field(..., description="Current registered attendees")
    status: str = Field(..., description="Status (upcoming, ongoing, completed, cancelled)")
    self_checkin_enabled: bool = Field(True, description="Allow self check-in")
    allow_repeat_checkin: bool = Field(True, description="Allow repeat check-ins")
    location_checkin_required: bool = Field(True, description="Require GPS location for check-in")
    speakers: List[SpeakerResponse] = Field(default_factory=list, description="List of speakers")
    organizer_id: Optional[str] = Field(None, description="Organizer user ID")
    contact_phone: Optional[str] = Field(None, description="Contact phone number")
    contact_email: Optional[str] = Field(None, description="Contact email address")
    website: Optional[str] = Field(None, description="Conference website URL")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class CreateConferenceRequest(BaseModel):
    """Request schema for creating conference."""

    name: str = Field(..., min_length=1, max_length=200, description="Conference name")
    description: Optional[str] = Field(None, description="Conference description")
    banner_url: Optional[str] = Field(None, description="Banner image URL")
    venue: str = Field(..., min_length=1, max_length=300, description="Conference venue")
    start_date: datetime = Field(..., description="Start date")
    end_date: datetime = Field(..., description="End date")
    registration_open: bool = Field(default=True, description="Registration open status")
    registration_deadline: Optional[datetime] = Field(None, description="Registration deadline")
    max_attendees: Optional[int] = Field(None, ge=1, description="Maximum attendees")


class UpdateConferenceRequest(BaseModel):
    """Request schema for updating conference."""

    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Conference name")
    description: Optional[str] = Field(None, description="Conference description")
    banner_url: Optional[str] = Field(None, description="Banner image URL")
    venue: Optional[str] = Field(None, min_length=1, max_length=300, description="Conference venue")
    venue_latitude: Optional[float] = Field(None, ge=-90, le=90, description="Venue latitude")
    venue_longitude: Optional[float] = Field(None, ge=-180, le=180, description="Venue longitude")
    venue_checkin_radius: Optional[int] = Field(None, ge=50, le=10000, description="Check-in radius in meters")
    start_date: Optional[datetime] = Field(None, description="Start date")
    end_date: Optional[datetime] = Field(None, description="End date")
    registration_open: Optional[bool] = Field(None, description="Registration open status")
    registration_deadline: Optional[datetime] = Field(None, description="Registration deadline")
    max_attendees: Optional[int] = Field(None, ge=1, description="Maximum attendees")
    self_checkin_enabled: Optional[bool] = Field(None, description="Allow self check-in")
    allow_repeat_checkin: Optional[bool] = Field(None, description="Allow repeat check-ins")
    location_checkin_required: Optional[bool] = Field(None, description="Require GPS location for check-in")
    status: Optional[str] = Field(
        None,
        pattern="^(upcoming|ongoing|completed|cancelled)$",
        description="Status"
    )


class ConferenceRegistrationResponse(BaseModel):
    """Conference registration response schema."""

    id: str = Field(..., description="Registration ID")
    user_id: str = Field(..., description="User ID")
    conference_id: str = Field(..., description="Conference ID")
    qr_code: str = Field(..., description="Unique QR code")
    registration_time: datetime = Field(..., description="Registration timestamp")
    checked_in: bool = Field(..., description="Check-in status")
    check_in_time: Optional[datetime] = Field(None, description="Check-in timestamp")
    status: str = Field(..., description="Status (confirmed, cancelled)")


class RegisterForConferenceRequest(BaseModel):
    """Request schema for registering for conference."""

    conference_id: str = Field(..., description="Conference ID")


class CheckInRequest(BaseModel):
    """Request schema for QR check-in."""

    qr_code: str = Field(..., min_length=1, description="User's QR code")


class CheckInResponse(BaseModel):
    """Response schema for QR check-in."""

    success: bool = Field(..., description="Check-in success status")
    user_name: str = Field(..., description="User's name")
    user_phone: str = Field(..., description="User's phone")
    conference_name: str = Field(..., description="Conference name")
    check_in_time: datetime = Field(..., description="Check-in timestamp")
