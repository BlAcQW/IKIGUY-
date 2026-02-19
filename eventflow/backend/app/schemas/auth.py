"""
Authentication schemas.
"""

from pydantic import BaseModel, Field
from typing import Optional


class OTPSendRequest(BaseModel):
    """OTP send request schema."""

    phone: str = Field(..., description="Phone number to send OTP to")

    class Config:
        """Pydantic config."""

        json_schema_extra = {"example": {"phone": "+233244123456"}}


class OTPVerifyRequest(BaseModel):
    """OTP verification request schema."""

    phone: str = Field(..., description="Phone number")
    otp: str = Field(..., description="OTP code")

    class Config:
        """Pydantic config."""

        json_schema_extra = {"example": {"phone": "+233244123456", "otp": "123456"}}


class UserProfile(BaseModel):
    """User profile in auth response."""

    id: str
    phone: str
    name: str
    email: Optional[str] = None
    organization: Optional[str] = None
    pricing_tier: str
    wallet_id: Optional[str] = None


class EmailLoginRequest(BaseModel):
    """Email login request schema."""

    email: str = Field(..., description="Email address")
    password: str = Field(..., description="Password")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "email": "admin@ailabsafrica.com",
                "password": "password123"
            }
        }


class AuthResponse(BaseModel):
    """Authentication response schema."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserProfile = Field(..., description="User profile")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user": {
                    "id": "507f1f77bcf86cd799439011",
                    "phone": "+233244123456",
                    "name": "John Doe",
                    "email": "john@example.com",
                    "pricing_tier": "free",
                },
            }
        }


class SupabaseAuthResponse(BaseModel):
    """Supabase authentication response schema."""

    access_token: str = Field(..., description="Supabase JWT access token")
    refresh_token: str = Field(..., description="Supabase refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserProfile = Field(..., description="User profile")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "v1.Mr7234o-jf234...",
                "token_type": "bearer",
                "user": {
                    "id": "507f1f77bcf86cd799439011",
                    "phone": "",
                    "name": "Admin User",
                    "email": "admin@ailabsafrica.com",
                    "pricing_tier": "free",
                },
            }
        }
