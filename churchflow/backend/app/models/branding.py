"""
Branding settings model for white-label customization.

Allows churches to customize their ChurchFlow instance with
custom branding (logo, colors, domain, etc.).
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl


class BrandingSettings(BaseModel):
    """
    Branding settings for an organization.

    Enables white-label customization per church.

    Attributes:
        organization_id: Organization ID
        custom_subdomain: Custom subdomain (e.g., 'actionchapel' for actionchapel.churchflow.com)
        logo_url: URL to church logo (header)
        favicon_url: URL to favicon
        email_logo_url: URL to logo for emails
        primary_color: Primary brand color (hex)
        secondary_color: Secondary brand color (hex)
        accent_color: Accent color (hex)
        font_family: Font family name
        email_sender_name: Custom email sender name
        email_reply_to: Email reply-to address
        sms_sender_name: SMS sender name
        social_media_links: Social media URLs
        custom_css: Custom CSS overrides
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    organization_id: str = Field(..., description="Organization ID")
    custom_subdomain: Optional[str] = Field(None, description="Custom subdomain")
    logo_url: Optional[str] = Field(None, description="Logo URL")
    favicon_url: Optional[str] = Field(None, description="Favicon URL")
    email_logo_url: Optional[str] = Field(None, description="Email logo URL")
    primary_color: str = Field(default="#4F46E5", description="Primary color (hex)")
    secondary_color: str = Field(default="#10B981", description="Secondary color (hex)")
    accent_color: str = Field(default="#F59E0B", description="Accent color (hex)")
    font_family: str = Field(default="Inter", description="Font family")
    email_sender_name: Optional[str] = Field(None, description="Email sender name")
    email_reply_to: Optional[str] = Field(None, description="Email reply-to")
    sms_sender_name: Optional[str] = Field(None, description="SMS sender name")
    social_media_links: dict = Field(default_factory=dict, description="Social media URLs")
    custom_css: Optional[str] = Field(None, description="Custom CSS")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "organization_id": "org_123",
                "custom_subdomain": "actionchapel",
                "logo_url": "https://cdn.churchflow.com/logos/actionchapel.png",
                "favicon_url": "https://cdn.churchflow.com/favicons/actionchapel.ico",
                "primary_color": "#4F46E5",
                "secondary_color": "#10B981",
                "accent_color": "#F59E0B",
                "font_family": "Inter",
                "email_sender_name": "Action Chapel International",
                "email_reply_to": "info@actionchapel.org",
                "sms_sender_name": "ACI",
                "social_media_links": {
                    "facebook": "https://facebook.com/actionchapel",
                    "twitter": "https://twitter.com/actionchapel",
                    "instagram": "https://instagram.com/actionchapel",
                    "youtube": "https://youtube.com/@actionchapel"
                }
            }
        }


class BrandingSettingsUpdate(BaseModel):
    """
    Schema for updating branding settings.

    All fields are optional to support partial updates.
    """
    custom_subdomain: Optional[str] = None
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    email_logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    font_family: Optional[str] = None
    email_sender_name: Optional[str] = None
    email_reply_to: Optional[str] = None
    sms_sender_name: Optional[str] = None
    social_media_links: Optional[dict] = None
    custom_css: Optional[str] = None


class BrandingSettingsResponse(BaseModel):
    """
    Response schema for branding settings.

    Returns complete branding configuration for frontend.
    """
    organization_id: str
    custom_subdomain: Optional[str]
    logo_url: Optional[str]
    favicon_url: Optional[str]
    primary_color: str
    secondary_color: str
    accent_color: str
    font_family: str
    email_sender_name: Optional[str]
    sms_sender_name: Optional[str]
    social_media_links: dict
    has_custom_branding: bool  # True if any customization is set
