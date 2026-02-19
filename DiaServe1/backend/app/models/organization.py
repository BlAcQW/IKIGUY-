"""
Organization models for EstateFlow.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class Organization(BaseModel):
    """Organization model."""

    id: str = Field(..., description="Organization unique identifier")
    name: str = Field(..., description="Organization name")
    description: Optional[str] = Field(None, description="Organization description")
    address: Optional[str] = Field(None, description="Physical address")
    phone: Optional[str] = Field(None, description="Contact phone")
    email: Optional[str] = Field(None, description="Contact email")
    website: Optional[str] = Field(None, description="Website URL")
    tax_id: Optional[str] = Field(None, description="Tax identification number")
    payment_info: Optional[str] = Field(None, description="Payment instructions")
    logo_url: Optional[str] = Field(None, description="Logo image URL")
    invoice_settings: Optional[Dict[str, Any]] = Field(None, description="Invoice configuration")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "org_12345",
                "name": "Premium Real Estate Ghana",
                "description": "Leading real estate agency in Greater Accra",
                "address": "Plot 123, Independence Avenue, Accra, Ghana",
                "phone": "+233 30 123 4567",
                "email": "info@premiumrealestate.com",
                "website": "www.premiumrealestate.com",
                "tax_id": "TIN-GH-87654321",
                "payment_info": "Bank: Access Bank Ghana\\nAccount: 0000123456789",
                "invoice_settings": {
                    "invoice_prefix": "PRE",
                    "next_invoice_number": 1000
                }
            }
        }


class OrganizationListResponse(BaseModel):
    """Response model for organization list."""

    organizations: List[Organization] = Field(..., description="List of organizations")
    total: int = Field(..., description="Total count of organizations")
    limit: int = Field(..., description="Page size")
    offset: int = Field(..., description="Page offset")
