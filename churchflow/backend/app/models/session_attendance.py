"""
Session attendance database models.

This module defines the data model for tracking per-session attendance
within conferences. Each document represents one user checking into
one session.
"""

from datetime import datetime
from typing import Optional
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


class SessionAttendance(BaseModel):
    """
    Session attendance record.

    Tracks individual attendee check-ins to specific conference sessions OR church services.
    The unique constraint on (session_id, registration_id) or (service_id, registration_id)
    prevents duplicate check-ins to the same session/service.

    Attributes:
        id: MongoDB document ID
        session_id: Reference to ConferenceSession being attended (for conferences)
        service_id: Reference to Service being attended (for church services)
        conference_id: Reference to Conference (denormalized for query efficiency)
        registration_id: Reference to ConferenceRegistration or User

        checked_in_at: Timestamp when user checked in to this session
        checked_in_by: User ID of admin who performed check-in (null for self check-in)
        check_in_method: How check-in was performed (qr_scan, manual_search, phone_lookup)

        user_name: Cached user name (denormalized for read performance)
        user_phone: Cached user phone (denormalized for read performance)
        session_name: Cached session name or service type (denormalized for read performance)
        day_number: Cached day number (denormalized for grouping)

        created_at: Record creation timestamp
    """

    id: Optional[PyObjectId] = Field(default=None, alias="_id")

    # Core references - either session_id OR service_id must be set
    session_id: Optional[PyObjectId] = Field(
        None,
        description="Reference to ConferenceSession (for conferences)"
    )
    service_id: Optional[PyObjectId] = Field(
        None,
        description="Reference to Service (for church services)"
    )
    conference_id: Optional[PyObjectId] = Field(
        None,
        description="Conference ID (denormalized for query efficiency, conferences only)"
    )
    registration_id: PyObjectId = Field(
        ...,
        description="Reference to ConferenceRegistration or User"
    )

    # Check-in metadata
    checked_in_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when user checked in to this session"
    )
    checked_in_by: Optional[PyObjectId] = Field(
        None,
        description="Admin user ID who performed check-in (null for self check-in)"
    )
    check_in_method: str = Field(
        default="qr_scan",
        description="Method used for check-in: qr_scan, manual_search, or phone_lookup"
    )

    # Denormalized fields for read performance (avoid joins on list views)
    user_name: Optional[str] = Field(
        None,
        max_length=200,
        description="Cached user name for display"
    )
    user_phone: Optional[str] = Field(
        None,
        max_length=20,
        description="Cached user phone for display"
    )
    session_name: Optional[str] = Field(
        None,
        max_length=200,
        description="Cached session name for display"
    )
    day_number: Optional[int] = Field(
        None,
        ge=1,
        description="Cached day number for grouping"
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Runtime flag (not stored in database)
    is_repeat_checkin: bool = Field(
        default=False,
        description="True if this is a repeat check-in (already checked in earlier)"
    )

    @model_validator(mode='after')
    def validate_session_or_service(self):
        """Ensure either session_id or service_id is set (but not both)."""
        if not self.session_id and not self.service_id:
            raise ValueError("Either session_id or service_id must be provided")
        if self.session_id and self.service_id:
            raise ValueError("Cannot set both session_id and service_id")
        return self

    class Config:
        """Pydantic model configuration."""

        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}
        json_schema_extra = {
            "example": {
                "session_id": "674e9a2b3f1234567890abcd",
                "conference_id": "674e9a2b3f1234567890abce",
                "registration_id": "674e9a2b3f1234567890abcf",
                "checked_in_at": "2025-11-15T09:05:00",
                "check_in_method": "qr_scan",
                "user_name": "Akosua Mensah",
                "user_phone": "+233244123456",
                "session_name": "Opening Worship & Praise",
                "day_number": 1
            }
        }
