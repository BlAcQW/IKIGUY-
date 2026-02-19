"""
User models for StudyFlow.

Defines student, parent, teacher, and admin user types.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId


class UserRole(str, Enum):
    """User role types."""
    STUDENT = "student"
    PARENT = "parent"
    TEACHER = "teacher"
    SCHOOL = "school"
    ADMIN = "admin"


class User(BaseModel):
    """
    User model for all user types.

    Attributes:
        id: MongoDB ObjectId as string
        organization_id: Organization ID for multi-tenancy
        supabase_id: Supabase auth user ID
        email: User email
        phone: User phone number
        role: User role (student, parent, teacher, admin)
        full_name: User's full name
        grade: Student grade level (for students only)
        school_id: School ID (for students/teachers)
        parent_id: Parent ID (for students)
        student_ids: List of student IDs (for parents)
        subjects: List of subjects (for teachers/students)
        metadata: Additional user data
        is_active: Account active status
        created_at: Account creation timestamp
        updated_at: Last update timestamp
    """
    id: Optional[str] = Field(default=None, alias="_id")
    organization_id: str
    supabase_id: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    role: UserRole
    full_name: str

    # Student-specific fields
    grade: Optional[int] = None  # Grade level (1-12)
    school_id: Optional[str] = None
    parent_id: Optional[str] = None

    # Parent-specific fields
    student_ids: List[str] = Field(default_factory=list)

    # Teacher-specific fields
    subjects: List[str] = Field(default_factory=list)

    # Common fields
    metadata: dict = Field(default_factory=dict)
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


class UserCreate(BaseModel):
    """
    Schema for creating a new user.

    Attributes:
        organization_id: Organization ID for multi-tenancy
        supabase_id: Supabase auth user ID
        email: User email
        phone: User phone number
        role: User role
        full_name: User's full name
        grade: Student grade level (optional)
        school_id: School ID (optional)
        parent_id: Parent ID for students (optional)
        subjects: List of subjects for teachers (optional)
    """
    organization_id: str
    supabase_id: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    role: UserRole
    full_name: str
    grade: Optional[int] = None
    school_id: Optional[str] = None
    parent_id: Optional[str] = None
    subjects: List[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class UserUpdate(BaseModel):
    """
    Schema for updating user information.

    All fields are optional to allow partial updates.
    """
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    full_name: Optional[str] = None
    grade: Optional[int] = None
    school_id: Optional[str] = None
    subjects: Optional[List[str]] = None
    metadata: Optional[dict] = None
    is_active: Optional[bool] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserResponse(BaseModel):
    """
    User response model (without sensitive data).

    Used for API responses.
    """
    id: str
    organization_id: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role: UserRole
    full_name: str
    grade: Optional[int] = None
    school_id: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
