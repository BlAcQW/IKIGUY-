"""
Organization database model.

Defines the structure and validation for church organization documents in MongoDB.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl
from bson import ObjectId


class PyObjectId(ObjectId):
    """
    Custom ObjectId type for Pydantic models.

    Allows Pydantic to validate and serialize MongoDB ObjectIds.
    """

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


class ContactInfo(BaseModel):
    """Contact information for the organization."""

    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    website: Optional[HttpUrl] = None


class Organization(BaseModel):
    """
    Organization model representing a church.

    Attributes:
        id: MongoDB document ID
        name: Organization/Church name
        slug: URL-friendly identifier
        description: Brief description of the organization
        logo_url: URL to organization logo
        contact_info: Contact information
        headquarters_branch_id: Reference to main/headquarters branch
        is_default: Whether this is the default organization
        settings: Organization-specific settings
        created_at: Timestamp of organization creation
        updated_at: Timestamp of last update
        metadata: Additional organization data
    """

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    name: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=1000)
    logo_url: Optional[HttpUrl] = None
    contact_info: ContactInfo = Field(default_factory=ContactInfo)
    headquarters_branch_id: Optional[PyObjectId] = None
    is_default: bool = Field(default=False)
    settings: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic model configuration."""

        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}
        json_schema_extra = {
            "example": {
                "name": "Action Chapel International",
                "slug": "action-chapel-international",
                "description": "A vibrant church community",
                "logo_url": "https://actionchapel.net/logo.png",
                "contact_info": {
                    "phone": "+233302123456",
                    "email": "info@actionchapel.net",
                    "address": "Accra, Ghana",
                    "website": "https://actionchapel.net"
                },
                "is_default": True,
                "settings": {
                    "enable_bus_management": True,
                    "enable_qr_checkin": True
                },
                "created_at": "2025-10-24T10:00:00",
                "updated_at": "2025-10-24T10:00:00"
            }
        }


class Branch(BaseModel):
    """
    Branch model representing a church location.

    Attributes:
        id: MongoDB document ID
        organization_id: Reference to parent organization
        name: Branch name
        slug: URL-friendly identifier
        location: Physical location/address
        contact_info: Branch contact information
        is_headquarters: Whether this is the main branch
        capacity: Maximum capacity
        pastor_name: Name of branch pastor/leader
        service_times: Schedule of service times
        created_at: Timestamp of branch creation
        updated_at: Timestamp of last update
        metadata: Additional branch data
    """

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    organization_id: PyObjectId
    name: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=1, max_length=100)
    location: Optional[str] = None
    contact_info: ContactInfo = Field(default_factory=ContactInfo)
    is_headquarters: bool = Field(default=False)
    capacity: Optional[int] = Field(default=None, ge=0)
    pastor_name: Optional[str] = None
    service_times: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic model configuration."""

        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}
        json_schema_extra = {
            "example": {
                "organization_id": "507f1f77bcf86cd799439011",
                "name": "Action Chapel - Accra",
                "slug": "action-chapel-accra",
                "location": "Accra, Ghana",
                "contact_info": {
                    "phone": "+233302123456",
                    "email": "accra@actionchapel.net"
                },
                "is_headquarters": True,
                "capacity": 5000,
                "pastor_name": "Rev. Dr. John Doe",
                "service_times": ["Sunday 8:00 AM", "Sunday 10:30 AM"],
                "created_at": "2025-10-24T10:00:00",
                "updated_at": "2025-10-24T10:00:00"
            }
        }
