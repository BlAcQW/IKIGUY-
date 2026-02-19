"""
Subscription models for DevotionalFlow.

Handles email, WhatsApp, and Facebook group subscriptions for drip feed content.
"""

from typing import Optional, List, Literal
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from bson import ObjectId
from app.models.user import PyObjectId


class SubscriptionChannel(BaseModel):
    """Individual subscription channel preferences."""

    email: Optional[EmailStr] = None
    whatsapp: Optional[str] = None  # Phone number in E.164 format (e.g., +233123456789)
    facebook_group: bool = False  # Just tracks preference, user joins manually


class SubscriptionCreate(BaseModel):
    """Model for creating a new subscription."""

    name: str = Field(..., min_length=1, max_length=200)
    email: Optional[EmailStr] = None
    whatsapp: Optional[str] = Field(None, pattern=r"^\+[1-9]\d{1,14}$")
    facebook_group: bool = False
    preferences: Optional[dict] = Field(default_factory=dict)


class SubscriptionUpdate(BaseModel):
    """Model for updating subscription preferences."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    email: Optional[EmailStr] = None
    whatsapp: Optional[str] = Field(None, pattern=r"^\+[1-9]\d{1,14}$")
    facebook_group: Optional[bool] = None
    preferences: Optional[dict] = None
    is_active: Optional[bool] = None


class SubscriptionInDB(BaseModel):
    """Subscription model as stored in MongoDB."""

    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str
    email: Optional[str] = None
    whatsapp: Optional[str] = None
    facebook_group: bool = False
    
    # Subscription status
    is_active: bool = True
    verified_email: bool = False
    verified_whatsapp: bool = False
    
    # Preferences
    preferences: dict = Field(default_factory=dict)
    
    # Drip feed tracking
    last_sent_at: Optional[datetime] = None
    last_sent_content_id: Optional[str] = None
    total_sent: int = 0
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    unsubscribed_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}


class SubscriptionResponse(BaseModel):
    """Subscription model for API responses."""

    id: str
    name: str
    email: Optional[str] = None
    whatsapp: Optional[str] = None
    facebook_group: bool
    is_active: bool
    verified_email: bool
    verified_whatsapp: bool
    preferences: dict
    last_sent_at: Optional[str] = None
    total_sent: int
    created_at: str
    updated_at: str


class SubscriptionListResponse(BaseModel):
    """Paginated subscription list response."""

    subscriptions: List[SubscriptionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class UnsubscribeRequest(BaseModel):
    """Model for unsubscribe request."""

    email: Optional[EmailStr] = None
    whatsapp: Optional[str] = None
    token: Optional[str] = None  # Unsubscribe token for verification

