"""
QuickBooks Online integration models.

Handles QBO credential storage, customer mapping, and sync tracking.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class QBOCredential(BaseModel):
    """
    QuickBooks Online OAuth credential stored per organization.

    Stored in `qbo_credentials` collection with unique index on organization_id.
    Access and refresh tokens are Fernet-encrypted before storage.
    """

    id: str = Field(..., description="Credential ID (UUID)")
    organization_id: str = Field(..., description="Organization ID (unique)")
    realm_id: str = Field(..., description="QBO company/realm ID")
    access_token: str = Field(..., description="Encrypted access token")
    refresh_token: str = Field(..., description="Encrypted refresh token")
    access_token_expires_at: datetime = Field(..., description="Access token expiry")
    refresh_token_expires_at: datetime = Field(..., description="Refresh token expiry")
    company_name: Optional[str] = Field(default=None, description="QBO company name")
    is_active: bool = Field(default=True, description="Whether connection is active")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class QBOCustomerMapping(BaseModel):
    """
    Maps a DiaServe contact to a QBO customer.

    Stored in `qbo_customer_mappings` with compound unique index
    on (organization_id, diaserve_contact_id).
    """

    id: str = Field(..., description="Mapping ID (UUID)")
    organization_id: str = Field(..., description="Organization ID")
    diaserve_contact_id: str = Field(..., description="DiaServe contact ID")
    qbo_customer_id: str = Field(..., description="QBO customer ID")
    qbo_customer_name: str = Field(..., description="QBO customer display name")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class QBOConnectionStatus(BaseModel):
    """API response model for QBO connection status."""

    is_connected: bool = Field(..., description="Whether QBO is connected")
    company_name: Optional[str] = Field(default=None, description="Connected company name")
    realm_id: Optional[str] = Field(default=None, description="QBO realm ID")
    connected_at: Optional[datetime] = Field(default=None, description="Connection timestamp")


class QBOSyncResult(BaseModel):
    """API response model for sync operation results."""

    total_invoices: int = Field(..., description="Total invoices attempted")
    synced: int = Field(..., description="Successfully synced count")
    failed: int = Field(..., description="Failed sync count")
    errors: List[str] = Field(default_factory=list, description="Error messages")
