"""
Church service database models.

This module defines models for regular church services (Sunday, midweek)
separate from special conferences/events.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, model_validator
from bson import ObjectId


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


class Service(BaseModel):
    """
    Church service model for Sunday and midweek services.

    Attributes:
        id: MongoDB document ID
        service_type: Type of service (sunday_8am, sunday_10am, midweek, special)
        branch_id: Reference to branch holding the service
        organization_id: Organization identifier for multi-tenant support

        sermon_title: Title of the sermon
        series_name: Name of the sermon series (optional)
        scripture_reference: Bible passage reference
        speaker: Name of speaker/preacher

        sermon_recording_url: URL to audio/video recording
        sermon_notes_url: URL to sermon notes PDF
        livestream_link: URL for live streaming

        service_date: Date of service
        start_time: Service start time (HH:MM format)
        end_time: Service end time (HH:MM format)

        status: Service status (upcoming, ongoing, completed, cancelled)

        expected_attendance: Expected number of attendees
        actual_attendance: Actual count calculated from check-ins

        qr_code: Unique QR code for service check-in
        venue_checkin_radius: Check-in radius in meters (default: 1000m/1km)

        is_recurring: Whether this is part of recurring series
        recurrence_rule: JSON pattern details for recurring generation

        created_at: Creation timestamp
        updated_at: Last update timestamp
        created_by: User ID of creator
    """

    id: Optional[PyObjectId] = Field(default=None, alias="_id")

    # Service Identity
    service_type: str = Field(
        ...,
        pattern="^(sunday_8am|sunday_10am|midweek|special)$",
        description="Type of service"
    )
    branch_id: PyObjectId = Field(..., description="Branch holding service")
    organization_id: str = Field(..., description="Organization ID")

    # Sermon Details
    sermon_title: Optional[str] = Field(None, max_length=300)
    series_name: Optional[str] = Field(None, max_length=200)
    scripture_reference: Optional[str] = Field(None, max_length=200)
    speaker: Optional[str] = Field(None, max_length=200)

    # Media Links
    sermon_recording_url: Optional[str] = None
    sermon_notes_url: Optional[str] = None
    livestream_link: Optional[str] = None

    # Scheduling
    service_date: datetime = Field(...)
    start_time: str = Field(..., description="HH:MM format")
    end_time: str = Field(..., description="HH:MM format")

    # Status
    status: str = Field(
        default="upcoming",
        pattern="^(upcoming|ongoing|completed|cancelled)$"
    )

    # Attendance
    expected_attendance: Optional[int] = None
    actual_attendance: int = Field(default=0, ge=0)

    # Check-in Configuration
    qr_code: Optional[str] = Field(None, description="Unique QR code for check-in")
    venue_checkin_radius: int = Field(
        default=1000,
        ge=50,
        le=5000,
        description="Check-in radius in meters (default: 1000m/1km)"
    )

    # Recurring Pattern
    is_recurring: bool = Field(default=False)
    recurrence_rule: Optional[Dict[str, Any]] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[PyObjectId] = None

    @model_validator(mode='after')
    def validate_time_format(self):
        """Validate time format is HH:MM."""
        import re
        time_pattern = re.compile(r'^([01]\d|2[0-3]):([0-5]\d)$')

        if not time_pattern.match(self.start_time):
            raise ValueError(f"Invalid start_time format: {self.start_time}. Expected HH:MM")

        if not time_pattern.match(self.end_time):
            raise ValueError(f"Invalid end_time format: {self.end_time}. Expected HH:MM")

        return self

    class Config:
        """Pydantic model configuration."""

        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}
        json_schema_extra = {
            "example": {
                "service_type": "sunday_10am",
                "branch_id": "507f1f77bcf86cd799439011",
                "organization_id": "org_12345",
                "sermon_title": "Walking in Faith",
                "series_name": "Faith Series 2025",
                "scripture_reference": "Hebrews 11:1-6",
                "speaker": "Pastor Emmanuel Mensah",
                "service_date": "2025-12-14T00:00:00",
                "start_time": "10:00",
                "end_time": "12:30",
                "status": "upcoming",
                "expected_attendance": 500,
                "qr_code": "SVC_20251214_10AM_ABC123"
            }
        }
