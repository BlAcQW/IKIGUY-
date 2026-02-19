"""
User model for EventFlow.
"""

from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field
from bson import ObjectId


class User(BaseModel):
    """User model."""

    # Phone or email must be provided
    phone: str = Field(default="", description="User phone number")
    name: str = Field(..., description="User full name")
    email: Optional[str] = Field(None, description="User email address")

    # Supabase integration
    supabase_user_id: Optional[str] = Field(None, description="Supabase user ID (for email auth)")
    auth_method: Literal["phone", "email", "both"] = Field(default="phone", description="Authentication method")

    # Organization and subscription
    organization: Optional[str] = Field(None, description="Organization name")
    wallet_id: Optional[str] = Field(None, description="Wallet service ID")
    pricing_tier: str = Field(default="free", description="Pricing tier")
    roles: List[str] = Field(
        default_factory=lambda: ["organizer"], description="User roles"
    )

    # Profile and settings
    profile_image_url: Optional[str] = Field(None, description="Profile image URL")
    fcm_token: Optional[str] = Field(None, description="Firebase Cloud Messaging token")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "phone": "+233244123456",
                "name": "John Doe",
                "email": "john@example.com",
                "supabase_user_id": "4a6252e7-3dc7-483a-92c3-59a0a814a169",
                "auth_method": "email",
                "organization": "Acme Corp",
                "pricing_tier": "free",
                "roles": ["organizer"],
            }
        }


class UserInDB(User):
    """User model with database ID."""

    id: str = Field(alias="_id")

    class Config:
        """Pydantic config."""

        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
