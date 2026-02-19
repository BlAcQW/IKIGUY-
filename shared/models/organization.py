"""
Centralized Organization Models for All KasaAI Apps

This module provides shared organization, user, and role models that can be used
across all KasaAI applications (ChurchFlow, EventFlow, InkWave, StudyFlow, etc.).

Organization System:
- Every user belongs to at least one organization
- All data is scoped to an organization
- Roles: admin, user (per organization)
- Universal admin role: access to all organizations

Usage:
    from apps.shared.models.organization import Organization, OrganizationUser, OrganizationRole
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from enum import Enum


class OrganizationRole(str, Enum):
    """Organization role types."""

    UNIVERSAL_ADMIN = "universal_admin"  # Can access and manage all organizations
    ADMIN = "admin"                       # Can manage organization and all its data
    APPROVER = "approver"                # Can approve financial expenses and budgets
    USER = "user"                        # Can access organization data based on permissions


class Address(BaseModel):
    """Structured address model."""

    street: Optional[str] = Field(default="", description="Street address")
    street2: Optional[str] = Field(default="", description="Street address line 2")
    city: Optional[str] = Field(default="", description="City")
    state: Optional[str] = Field(default="", description="State/Province")
    postal_code: Optional[str] = Field(default="", description="Postal/ZIP code")
    country: Optional[str] = Field(default="", description="Country")


class InvoiceSettings(BaseModel):
    """Invoice generation and branding settings."""

    # Numbering
    invoice_prefix: str = Field(default="INV", description="Invoice number prefix")
    invoice_number_start: int = Field(default=1000, description="Starting invoice number")
    next_invoice_number: int = Field(default=1000, description="Next invoice number to use")

    # Terms
    default_payment_terms: str = Field(default="Net 30", description="Default payment terms")
    late_fee_percentage: float = Field(default=0.0, description="Late fee percentage")

    # Tax
    tax_id: Optional[str] = Field(default="", description="Tax ID / VAT number")
    tax_label: str = Field(default="Tax", description="Tax label (VAT, GST, etc.)")
    default_tax_rate: float = Field(default=0.0, description="Default tax rate percentage")

    # Header/Footer
    header_text: Optional[str] = Field(default="", description="Invoice header text")
    footer_text: Optional[str] = Field(default="Thank you for your business!", description="Invoice footer text")

    # Notes
    default_notes: Optional[str] = Field(default="", description="Default invoice notes")
    terms_and_conditions: Optional[str] = Field(default="", description="Terms and conditions text")

    # Format
    date_format: str = Field(default="YYYY-MM-DD", description="Date format")
    currency_symbol: str = Field(default="$", description="Currency symbol")
    currency_position: str = Field(default="before", description="Currency symbol position (before/after)")

    # Display
    show_logo: bool = Field(default=True, description="Show logo on invoice")
    show_payment_instructions: bool = Field(default=True, description="Show payment instructions")


class InvitationStatus(str, Enum):
    """Invitation status types."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"


class Organization(BaseModel):
    """Organization model for database storage."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., description="Organization name (unique identifier)")
    display_name: str = Field(..., description="Display name for UI")
    description: Optional[str] = Field(default="", description="Organization description")

    # Organization Info
    industry: Optional[str] = Field(default="", description="Industry sector")
    company_size: Optional[str] = Field(default="", description="Company size category")
    website: Optional[str] = Field(default="", description="Company website")
    phone: Optional[str] = Field(default="", description="Contact phone number")
    email: Optional[str] = Field(default="", description="Contact email")
    address: Optional[str] = Field(default="", description="Business address (legacy)")

    # Structured Address
    billing_address: Optional[Address] = Field(default=None, description="Structured billing address")

    # Branding
    logo_url: Optional[str] = Field(default="", description="Company logo URL")
    primary_color: Optional[str] = Field(default="#0066CC", description="Primary brand color (hex)")
    secondary_color: Optional[str] = Field(default="#666666", description="Secondary brand color (hex)")
    accent_color: Optional[str] = Field(default="#00CC66", description="Accent color (hex)")

    # Invoice Settings
    invoice_settings: InvoiceSettings = Field(default_factory=InvoiceSettings, description="Invoice generation settings")

    # Bank/Payment Details
    bank_name: Optional[str] = Field(default="", description="Bank name")
    bank_account_number: Optional[str] = Field(default="", description="Bank account number")
    bank_routing_number: Optional[str] = Field(default="", description="Bank routing/sort code")
    bank_iban: Optional[str] = Field(default="", description="IBAN")
    bank_swift: Optional[str] = Field(default="", description="SWIFT/BIC code")

    # Settings
    is_active: bool = Field(default=True, description="Whether organization is active")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Organization settings")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "org_123abc",
                "name": "acme-corp",
                "display_name": "Acme Corporation",
                "description": "Global technology company",
                "industry": "technology",
                "company_size": "50-200",
                "website": "https://acme.com",
                "phone": "+1234567890",
                "address": "123 Tech Street",
                "is_active": True,
                "settings": {},
                "created_at": "2025-01-01T00:00:00",
                "updated_at": "2025-01-01T00:00:00"
            }
        }


class OrganizationUser(BaseModel):
    """Organization user membership model."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    organization_id: str = Field(..., description="Organization ID")
    user_id: str = Field(..., description="User ID (from authentication system)")
    email: str = Field(..., description="User email")
    role: OrganizationRole = Field(default=OrganizationRole.USER, description="User role in organization")

    # User Info
    first_name: Optional[str] = Field(default="", description="User first name")
    last_name: Optional[str] = Field(default="", description="User last name")
    display_name: Optional[str] = Field(default="", description="Display name")
    avatar_url: Optional[str] = Field(default="", description="User avatar URL")

    # Permissions
    permissions: Dict[str, bool] = Field(default_factory=dict, description="Specific permissions")

    # Status
    is_active: bool = Field(default=True, description="Whether membership is active")
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: Optional[datetime] = Field(default=None, description="Last activity timestamp")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "orguser_456def",
                "organization_id": "org_123abc",
                "user_id": "user_789ghi",
                "email": "john@acme.com",
                "role": "admin",
                "first_name": "John",
                "last_name": "Doe",
                "display_name": "John Doe",
                "avatar_url": "https://example.com/avatar.jpg",
                "permissions": {"create_events": True, "delete_events": False},
                "is_active": True,
                "joined_at": "2025-01-01T00:00:00",
                "last_activity": "2025-01-15T10:30:00",
                "created_at": "2025-01-01T00:00:00",
                "updated_at": "2025-01-01T00:00:00"
            }
        }


class OrganizationInvitation(BaseModel):
    """Organization invitation model."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    organization_id: str = Field(..., description="Organization ID")
    email: str = Field(..., description="Invitee email")
    role: OrganizationRole = Field(default=OrganizationRole.USER, description="Invited role")

    # Invitation Details
    invited_by_user_id: str = Field(..., description="User ID who sent invitation")
    invited_by_email: str = Field(..., description="Email of user who sent invitation")
    invitation_token: str = Field(..., description="Unique invitation token")

    # Status
    status: InvitationStatus = Field(default=InvitationStatus.PENDING, description="Invitation status")
    expires_at: datetime = Field(..., description="Invitation expiry date")

    # Response Details
    responded_at: Optional[datetime] = Field(default=None, description="Response timestamp")
    response_message: Optional[str] = Field(default="", description="Response message")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Request/Response Models

class OrganizationCreate(BaseModel):
    """Request model for creating an organization."""

    name: Optional[str] = Field(default=None, description="Organization name (auto-generated from display_name if not provided)")
    display_name: str = Field(..., description="Display name")
    description: Optional[str] = Field(default="", description="Description")
    industry: Optional[str] = Field(default="", description="Industry")
    website: Optional[str] = Field(default="", description="Website")


class OrganizationUpdate(BaseModel):
    """Request model for updating an organization."""

    name: Optional[str] = Field(default=None, description="Organization name")
    display_name: Optional[str] = Field(default=None, description="Display name")
    description: Optional[str] = Field(default=None, description="Description")
    industry: Optional[str] = Field(default=None, description="Industry")
    company_size: Optional[str] = Field(default=None, description="Company size")
    website: Optional[str] = Field(default=None, description="Website")
    phone: Optional[str] = Field(default=None, description="Phone")
    email: Optional[str] = Field(default=None, description="Email")
    address: Optional[str] = Field(default=None, description="Address")
    billing_address: Optional[Address] = Field(default=None, description="Billing address")

    # Branding
    logo_url: Optional[str] = Field(default=None, description="Logo URL")
    primary_color: Optional[str] = Field(default=None, description="Primary color")
    secondary_color: Optional[str] = Field(default=None, description="Secondary color")
    accent_color: Optional[str] = Field(default=None, description="Accent color")

    # Invoice Settings
    invoice_settings: Optional[InvoiceSettings] = Field(default=None, description="Invoice settings")

    # Bank Details
    bank_name: Optional[str] = Field(default=None, description="Bank name")
    bank_account_number: Optional[str] = Field(default=None, description="Bank account number")
    bank_routing_number: Optional[str] = Field(default=None, description="Bank routing number")
    bank_iban: Optional[str] = Field(default=None, description="IBAN")
    bank_swift: Optional[str] = Field(default=None, description="SWIFT code")

    settings: Optional[Dict[str, Any]] = Field(default=None, description="Settings")


class OrganizationUserUpdate(BaseModel):
    """Request model for updating organization user."""

    role: Optional[OrganizationRole] = Field(default=None, description="User role")
    permissions: Optional[Dict[str, bool]] = Field(default=None, description="Permissions")
    is_active: Optional[bool] = Field(default=None, description="Active status")


class OrganizationInviteRequest(BaseModel):
    """Request model for inviting users to organization."""

    email: str = Field(..., description="Email to invite")
    role: OrganizationRole = Field(default=OrganizationRole.USER, description="Role to assign")
    message: Optional[str] = Field(default="", description="Invitation message")


class OrganizationInviteResponse(BaseModel):
    """Response model for invitation actions."""

    invitation_token: str = Field(..., description="Invitation token")
    accepted: bool = Field(..., description="Whether invitation was accepted")
    message: Optional[str] = Field(default="", description="Response message")
