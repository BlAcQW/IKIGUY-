"""
Conference database models.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from bson import ObjectId
from app.models.voice_greeting import VoiceGreetingConfig


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic models."""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, handler=None):
        if isinstance(v, ObjectId):
            return v
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


class Speaker(BaseModel):
    """
    Conference speaker model.

    Attributes:
        name: Speaker full name
        title: Speaker title/position
        image_url: Speaker profile image URL
        bio: Short biography
    """

    name: str = Field(..., min_length=1, max_length=200)
    title: Optional[str] = None
    image_url: Optional[str] = None
    bio: Optional[str] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "name": "Rev. Dr. John Smith",
                "title": "Senior Pastor, Grace Chapel",
                "image_url": "https://example.com/speaker.jpg",
                "bio": "Dynamic preacher and Bible teacher."
            }
        }


class Conference(BaseModel):
    """
    Conference/event model.

    Attributes:
        id: MongoDB document ID
        name: Conference name
        description: Conference description
        theme: Conference theme
        banner_url: Banner image URL
        venue: Conference venue
        venue_latitude: Venue latitude coordinate
        venue_longitude: Venue longitude coordinate
        venue_checkin_radius: Check-in radius in meters (default: 1000m/1km)
        start_date: Conference start date
        end_date: Conference end date
        registration_open: Whether registration is open
        registration_deadline: Registration deadline
        max_attendees: Maximum number of attendees (optional)
        expected_attendance: Expected number of attendees
        current_attendees: Current number of registered attendees
        status: Conference status (upcoming, ongoing, completed, cancelled)
        speakers: List of conference speakers
        organizer_id: User ID of organizer
        contact_phone: Contact phone number
        contact_email: Contact email address
        website: Conference website URL
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    theme: Optional[str] = None
    banner_url: Optional[str] = None
    venue: str = Field(..., min_length=1, max_length=300)
    venue_latitude: Optional[float] = None
    venue_longitude: Optional[float] = None
    venue_checkin_radius: int = Field(
        default=1000,
        ge=50,
        le=5000,
        description="Check-in radius in meters (default: 1000m/1km)"
    )
    start_date: datetime = Field(...)
    end_date: datetime = Field(...)
    registration_open: bool = Field(default=True)
    registration_deadline: Optional[datetime] = None
    max_attendees: Optional[int] = None
    expected_attendance: Optional[int] = None
    current_attendees: int = Field(default=0, ge=0)
    status: str = Field(
        default="upcoming",
        pattern="^(upcoming|ongoing|completed|cancelled)$"
    )
    speakers: List[Speaker] = Field(default_factory=list)
    organizer_id: Optional[PyObjectId] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    website: Optional[str] = None
    voice_greeting: Optional[VoiceGreetingConfig] = None
    self_checkin_enabled: bool = Field(
        default=True,
        description="Allow attendees to check themselves in via QR code scan"
    )
    allow_repeat_checkin: bool = Field(
        default=True,
        description="Allow attendees to check in multiple times (greet again without error)"
    )
    location_checkin_required: bool = Field(
        default=True,
        description="Require GPS location verification for self-service check-in"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic model configuration."""

        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}
        json_schema_extra = {
            "example": {
                "name": "Impact Conference 2025",
                "description": "Annual youth conference",
                "venue": "National Theatre, Accra",
                "start_date": "2025-11-15T09:00:00",
                "end_date": "2025-11-17T18:00:00",
                "registration_open": True,
                "registration_deadline": "2025-11-10T23:59:59",
                "max_attendees": 500,
                "status": "upcoming"
            }
        }


class ConferenceRegistration(BaseModel):
    """
    Conference registration for a user.

    Attributes:
        id: MongoDB document ID
        user_id: Reference to user
        conference_id: Reference to conference
        qr_code: Unique QR code for check-in
        registration_time: When user registered
        checked_in: Whether user has checked in
        check_in_time: When user checked in
        status: Registration status (confirmed, cancelled)
    """

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    user_id: PyObjectId = Field(...)
    conference_id: PyObjectId = Field(...)
    qr_code: str = Field(..., min_length=1)
    registration_time: datetime = Field(default_factory=datetime.utcnow)
    checked_in: bool = Field(default=False)
    check_in_time: Optional[datetime] = None
    status: str = Field(
        default="confirmed",
        pattern="^(confirmed|cancelled)$"
    )

    class Config:
        """Pydantic model configuration."""

        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}
