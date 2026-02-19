"""
School models for StudyFlow.

Defines school organizations that can upload materials for their students.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr, HttpUrl
from bson import ObjectId


class SchoolType(str, Enum):
    """Type of educational institution."""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    HIGH_SCHOOL = "high_school"
    UNIVERSITY = "university"
    MIXED = "mixed"


class SubscriptionTier(str, Enum):
    """School subscription tier."""
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class School(BaseModel):
    """
    School model for educational institutions.

    Attributes:
        id: MongoDB ObjectId as string
        organization_id: Organization ID for multi-tenancy
        name: School name
        short_name: Short/abbreviation name
        school_type: Type of institution
        website: School website URL
        email: School contact email
        phone: School contact phone
        address: Physical address
        city: City location
        country: Country location
        logo_url: School logo URL
        admin_user_id: Supabase user ID of school admin
        subscription_tier: Current subscription level
        max_students: Maximum number of students
        max_materials: Maximum number of materials
        allowed_subjects: List of subjects school can create
        metadata: Additional school data
        is_active: School active status
        created_at: School creation timestamp
        updated_at: Last update timestamp
    """
    id: Optional[str] = Field(default=None, alias="_id")
    organization_id: str
    name: str
    short_name: str
    school_type: SchoolType

    # Contact information
    website: Optional[HttpUrl] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

    # Location
    address: Optional[str] = None
    city: Optional[str] = None
    country: str = "Ghana"

    # Branding
    logo_url: Optional[str] = None

    # Admin
    admin_user_id: str  # Supabase ID of school admin account

    # Subscription
    subscription_tier: SubscriptionTier = SubscriptionTier.FREE
    max_students: int = 100
    max_materials: int = 50
    allowed_subjects: List[str] = Field(default_factory=list)

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic configuration."""
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: lambda v: str(v)
        }


class SchoolCreate(BaseModel):
    """
    Schema for creating a new school.

    Attributes:
        organization_id: Organization ID for multi-tenancy
        name: School name
        short_name: Short name/abbreviation
        school_type: Type of institution
        website: School website
        email: Contact email
        phone: Contact phone
        address: Physical address
        city: City
        country: Country
        admin_user_id: Admin Supabase user ID
        subscription_tier: Subscription level
        allowed_subjects: Allowed subjects
    """
    organization_id: str
    name: str
    short_name: str
    school_type: SchoolType
    website: Optional[HttpUrl] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: str = "Ghana"
    admin_user_id: str
    subscription_tier: SubscriptionTier = SubscriptionTier.FREE
    allowed_subjects: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SchoolUpdate(BaseModel):
    """
    Schema for updating school information.

    All fields optional for partial updates.
    """
    name: Optional[str] = None
    short_name: Optional[str] = None
    school_type: Optional[SchoolType] = None
    website: Optional[HttpUrl] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    logo_url: Optional[str] = None
    subscription_tier: Optional[SubscriptionTier] = None
    max_students: Optional[int] = None
    max_materials: Optional[int] = None
    allowed_subjects: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SchoolResponse(BaseModel):
    """
    School response model for API responses.
    """
    id: str
    organization_id: str
    name: str
    short_name: str
    school_type: SchoolType
    website: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    city: Optional[str]
    country: str
    logo_url: Optional[str]
    subscription_tier: SubscriptionTier
    is_active: bool
    created_at: datetime

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SchoolStats(BaseModel):
    """
    Statistics for a school.
    """
    school_id: str
    school_name: str
    total_students: int
    total_materials: int
    total_teachers: int
    materials_by_subject: Dict[str, int] = Field(default_factory=dict)
    students_by_grade: Dict[str, int] = Field(default_factory=dict)
    last_activity: Optional[datetime] = None

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
