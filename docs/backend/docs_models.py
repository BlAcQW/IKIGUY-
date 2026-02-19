"""
Data models for KasaAI Documentation System
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """User roles for documentation access"""
    ADMIN = "admin"  # Full admin access
    INTERNAL = "internal"  # Can access internal docs
    PUBLIC = "public"  # Can only access public docs


class DocumentVisibility(str, Enum):
    """Document visibility settings"""
    PUBLIC = "public"
    INTERNAL = "internal"


class UserCreate(BaseModel):
    """Model for creating a new user"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None


class UserUpdate(BaseModel):
    """Model for updating user information"""
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class User(BaseModel):
    """User model"""
    id: str  # Supabase user ID
    email: str
    full_name: Optional[str] = None
    role: UserRole = UserRole.PUBLIC
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


class DocumentMetadata(BaseModel):
    """Document metadata model"""
    path: str  # e.g., "internal/onboarding"
    visibility: DocumentVisibility
    title: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DocumentMetadataCreate(BaseModel):
    """Model for creating document metadata"""
    path: str
    visibility: DocumentVisibility
    title: Optional[str] = None
    description: Optional[str] = None


class DocumentMetadataUpdate(BaseModel):
    """Model for updating document metadata"""
    visibility: Optional[DocumentVisibility] = None
    title: Optional[str] = None
    description: Optional[str] = None


class LoginRequest(BaseModel):
    """Login request model"""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response model"""
    access_token: str
    refresh_token: str
    user: dict
