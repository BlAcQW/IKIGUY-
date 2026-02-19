"""
Conference session database models.

This module defines the data models for conference sessions.
Sessions represent scheduled activities/talks within a conference,
organized by day.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
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


class ConferenceSession(BaseModel):
    """
    Conference session model.

    A session represents a scheduled activity or talk within a conference.
    Sessions are organized by day and can have a specific location.

    Attributes:
        id: MongoDB document ID
        conference_id: Reference to parent conference
        name: Session name/title
        description: Session description/details
        location: Session location/room (e.g., "Main Auditorium", "Room 101")
        day_number: Day number within conference (1, 2, 3, etc.)
        day_label: User-friendly day label (e.g., "Day 1", "Opening Day")
        session_date: Specific date for this session
        order: Display order within the day (for sorting)
        created_by: User ID of creator (conference admin)
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    conference_id: PyObjectId = Field(..., description="Parent conference ID")
    name: str = Field(..., min_length=1, max_length=200, description="Session name")
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Session description"
    )
    location: Optional[str] = Field(
        None,
        max_length=200,
        description="Session location/room"
    )
    day_number: int = Field(..., ge=1, description="Day number (1, 2, 3...)")
    day_label: str = Field(..., description="Day label (e.g., 'Day 1', 'Opening Day')")
    session_date: datetime = Field(..., description="Specific date for this session")
    start_time: Optional[str] = Field(None, description="Session start time (HH:MM format)")
    end_time: Optional[str] = Field(None, description="Session end time (HH:MM format)")
    order: int = Field(default=0, ge=0, description="Display order within the day")

    # SMS confirmation settings
    sms_confirmation_enabled: bool = Field(
        default=False,
        description="Send SMS confirmation when attendee checks in"
    )
    sms_confirmation_template: Optional[str] = Field(
        None,
        max_length=500,
        description="SMS template with placeholders: {name}, {session_name}, {day_label}"
    )

    created_by: Optional[PyObjectId] = Field(None, description="Creator user ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic model configuration."""

        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}
        json_schema_extra = {
            "example": {
                "conference_id": "674e9a2b3f1234567890abcd",
                "name": "Opening Worship & Praise",
                "description": "Join us for powerful worship as we kick off the conference",
                "location": "Main Auditorium",
                "day_number": 1,
                "day_label": "Day 1 - Opening",
                "session_date": "2025-11-15T09:00:00",
                "order": 1,
                "sms_confirmation_enabled": True,
                "sms_confirmation_template": "Hi {name}, you're checked in to {session_name}. Welcome to {day_label}!"
            }
        }
