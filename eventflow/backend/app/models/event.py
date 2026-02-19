"""
Event model for EventFlow.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field
from bson import ObjectId


class Event(BaseModel):
    """Event model."""

    name: str = Field(..., description="Event name")
    type: str = Field(..., description="Event type")
    date: datetime = Field(..., description="Event date")
    location: str = Field(..., description="Event location")
    num_guests: int = Field(..., description="Number of expected guests")
    budget_min: Optional[float] = Field(None, description="Minimum budget (GHS)")
    budget_max: Optional[float] = Field(None, description="Maximum budget (GHS)")
    status: str = Field(default="planning", description="Event status")
    organizer_id: str = Field(..., description="User ID of organizer")
    description: Optional[str] = Field(None, description="Event description")
    documents: List[str] = Field(
        default_factory=list, description="Document URLs"
    )
    tags: List[str] = Field(default_factory=list, description="Event tags")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "name": "Impact 2025 Conference",
                "type": "conference",
                "date": "2025-03-15T09:00:00Z",
                "location": "Accra International Conference Centre",
                "num_guests": 500,
                "budget_min": 50000,
                "budget_max": 100000,
                "status": "planning",
                "organizer_id": "507f1f77bcf86cd799439011",
                "description": "Annual youth conference",
                "tags": ["youth", "conference", "public"],
            }
        }


class EventInDB(Event):
    """Event model with database ID."""

    id: str = Field(alias="_id")

    class Config:
        """Pydantic config."""

        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
