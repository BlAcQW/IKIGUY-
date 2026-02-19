"""
Authentication request/response schemas.
"""

from pydantic import BaseModel, Field, validator
import phonenumbers


class SendOTPRequest(BaseModel):
    """Request schema for sending OTP."""

    phone: str = Field(
        ...,
        description="Phone number in E.164 format (e.g., +233201234567)",
        example="+233201234567"
    )

    @validator("phone")
    def validate_phone(cls, v):
        """
        Validate phone number format.

        Args:
            v: Phone number string

        Returns:
            str: Validated phone number

        Raises:
            ValueError: If phone number is invalid
        """
        try:
            parsed = phonenumbers.parse(v)
            if not phonenumbers.is_valid_number(parsed):
                raise ValueError("Invalid phone number")
            return phonenumbers.format_number(
                parsed,
                phonenumbers.PhoneNumberFormat.E164
            )
        except phonenumbers.NumberParseException:
            raise ValueError("Invalid phone number format. Use E.164 format (e.g., +233201234567)")


class SendOTPResponse(BaseModel):
    """Response schema for OTP sending."""

    success: bool = Field(..., description="Whether OTP was sent successfully")
    message: str = Field(..., description="Response message")
    phone: str = Field(..., description="Phone number OTP was sent to")


class VerifyOTPRequest(BaseModel):
    """Request schema for verifying OTP."""

    phone: str = Field(
        ...,
        description="Phone number in E.164 format",
        example="+233201234567"
    )
    token: str = Field(
        ...,
        description="6-digit OTP code",
        min_length=6,
        max_length=6,
        example="123456"
    )

    @validator("phone")
    def validate_phone(cls, v):
        """Validate phone number format."""
        try:
            parsed = phonenumbers.parse(v)
            if not phonenumbers.is_valid_number(parsed):
                raise ValueError("Invalid phone number")
            return phonenumbers.format_number(
                parsed,
                phonenumbers.PhoneNumberFormat.E164
            )
        except phonenumbers.NumberParseException:
            raise ValueError("Invalid phone number format")


class VerifyOTPResponse(BaseModel):
    """Response schema for OTP verification."""

    success: bool = Field(..., description="Whether OTP was verified successfully")
    user_id: str = Field(..., description="Supabase user ID")
    phone: str = Field(..., description="User's phone number")
    access_token: str = Field(..., description="JWT access token for API")
    token_type: str = Field(default="bearer", description="Token type")


class TokenData(BaseModel):
    """Token payload data."""

    sub: str = Field(..., description="Subject (user ID)")
    phone: str = Field(..., description="User phone number")
    exp: int = Field(..., description="Expiration timestamp")
    iat: int = Field(..., description="Issued at timestamp")
