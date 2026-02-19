"""
Responsible Person model for EventFlow.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from bson import ObjectId


class ResponsiblePerson(BaseModel):
    """Responsible person model."""

    event_id: str = Field(..., description="Event ID")
    name: str = Field(..., description="Person's full name")
    phone: str = Field(..., description="Contact phone number")
    email: Optional[str] = Field(None, description="Contact email address")
    role: str = Field(..., description="Role/department lead")
    user_id: Optional[str] = Field(
        None, description="User ID if person is a registered user"
    )
    notes: Optional[str] = Field(None, description="Additional notes")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "event_id": "507f1f77bcf86cd799439011",
                "name": "Sarah Johnson",
                "phone": "+233244567890",
                "email": "sarah@example.com",
                "role": "Catering Lead",
                "notes": "Available on weekends",
            }
        }


class ResponsiblePersonInDB(ResponsiblePerson):
    """Responsible person model with database ID."""

    id: str = Field(alias="_id")

    class Config:
        """Pydantic config."""

        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
