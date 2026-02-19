"""
Organization Settings Routes for ERP.

Handles detailed organization settings (general, branding, integrations, API keys).
Integrated from ChurchFlow's comprehensive settings system.
"""

import logging
import secrets
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, HttpUrl

from apps.shared.services.organization_service import get_organization_service
from apps.shared.dependencies import get_current_user, require_organization_admin_role
from apps.shared.models import Organization

logger = logging.getLogger(__name__)
router = APIRouter()


# Settings Schemas
class OrganizationGeneralUpdate(BaseModel):
    """Schema for updating general organization settings."""
    display_name: Optional[str] = None
    description: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[HttpUrl] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None


class OrganizationBrandingUpdate(BaseModel):
    """Schema for updating organization branding."""
    logo_url: Optional[HttpUrl] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None


class OrganizationIntegrationsUpdate(BaseModel):
    """Schema for updating organization integrations."""
    webhook_url: Optional[HttpUrl] = None
    slack_webhook: Optional[HttpUrl] = None
    email_notifications_enabled: Optional[bool] = None
    sms_notifications_enabled: Optional[bool] = None


class APIKeyResponse(BaseModel):
    """Response schema for API key operations."""
    api_key: str
    created_at: str


@router.patch("/{organization_id}/general", response_model=Organization)
async def update_general_settings(
    organization_id: str,
    update_data: OrganizationGeneralUpdate,
    user: dict = Depends(get_current_user),
    org_id: str = Depends(require_organization_admin_role),
):
    """
    Update organization general settings.

    Requires: User must be an admin of the organization.
    """
    if organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update another organization's settings"
        )

    org_service = get_organization_service()

    # Prepare update data (exclude None values)
    update_dict = update_data.model_dump(exclude_none=True)

    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update data provided"
        )

    # Update organization
    updated_org = await org_service.update_organization(organization_id, update_dict)

    if not updated_org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    logger.info(
        f"User {user.get('email')} updated general settings for organization {organization_id}"
    )

    return updated_org


@router.patch("/{organization_id}/branding", response_model=Organization)
async def update_branding_settings(
    organization_id: str,
    branding_data: OrganizationBrandingUpdate,
    user: dict = Depends(get_current_user),
    org_id: str = Depends(require_organization_admin_role),
):
    """
    Update organization branding settings.

    Requires: User must be an admin of the organization.
    """
    if organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update another organization's branding"
        )

    org_service = get_organization_service()

    # Prepare branding updates
    branding_dict = branding_data.model_dump(exclude_none=True)

    if not branding_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No branding data provided"
        )

    # Update organization
    updated_org = await org_service.update_organization(organization_id, branding_dict)

    if not updated_org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    logger.info(
        f"User {user.get('email')} updated branding for organization {organization_id}"
    )

    return updated_org


@router.patch("/{organization_id}/integrations", response_model=Organization)
async def update_integration_settings(
    organization_id: str,
    integration_data: OrganizationIntegrationsUpdate,
    user: dict = Depends(get_current_user),
    org_id: str = Depends(require_organization_admin_role),
):
    """
    Update organization integration settings.

    Requires: User must be an admin of the organization.
    """
    if organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update another organization's integrations"
        )

    org_service = get_organization_service()

    # Get current organization to update settings dict
    org = await org_service.get_organization(organization_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Prepare integration settings
    current_settings = org.settings or {}
    integration_dict = integration_data.model_dump(exclude_none=True)

    # Merge integration settings into settings dict
    updated_settings = {**current_settings, **integration_dict}

    # Update organization
    updated_org = await org_service.update_organization(
        organization_id, {"settings": updated_settings}
    )

    logger.info(
        f"User {user.get('email')} updated integrations for organization {organization_id}"
    )

    return updated_org


@router.post("/{organization_id}/api-key/regenerate", response_model=APIKeyResponse)
async def regenerate_api_key(
    organization_id: str,
    user: dict = Depends(get_current_user),
    org_id: str = Depends(require_organization_admin_role),
):
    """
    Regenerate API key for organization.

    Requires: User must be an admin of the organization.

    WARNING: This will invalidate the old API key.
    """
    if organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot regenerate API key for another organization"
        )

    org_service = get_organization_service()

    # Generate new API key
    new_api_key = f"erp_live_{secrets.token_urlsafe(32)}"
    created_at = datetime.utcnow()

    # Get current settings
    org = await org_service.get_organization(organization_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    current_settings = org.settings or {}

    # Update settings with new API key
    updated_settings = {
        **current_settings,
        "api_key": new_api_key,
        "api_key_created_at": created_at.isoformat()
    }

    # Update organization
    await org_service.update_organization(
        organization_id, {"settings": updated_settings}
    )

    logger.warning(
        f"User {user.get('email')} regenerated API key for organization {organization_id}"
    )

    return APIKeyResponse(
        api_key=new_api_key,
        created_at=created_at.isoformat()
    )


@router.get("/{organization_id}/api-key", response_model=APIKeyResponse)
async def get_api_key(
    organization_id: str,
    user: dict = Depends(get_current_user),
    org_id: str = Depends(require_organization_admin_role),
):
    """
    Get current API key for organization.

    Requires: User must be an admin of the organization.
    """
    if organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access another organization's API key"
        )

    org_service = get_organization_service()

    org = await org_service.get_organization(organization_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    settings = org.settings or {}
    api_key = settings.get("api_key")
    api_key_created_at = settings.get("api_key_created_at")

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found. Generate one first."
        )

    return APIKeyResponse(
        api_key=api_key,
        created_at=api_key_created_at or datetime.utcnow().isoformat()
    )
