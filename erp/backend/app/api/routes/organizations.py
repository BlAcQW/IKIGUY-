"""
Organization Management Routes.

Handles organization CRUD and user management.
Universal admins can switch between organizations.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import MongoDB
from apps.shared.models import (
    Organization,
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationUser,
    OrganizationUserUpdate,
    OrganizationRole,
)
from apps.shared.services.organization_service import get_organization_service
from apps.shared.dependencies import (
    get_current_user,
    require_organization_access,
    require_organization_admin_role,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=Organization, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_data: OrganizationCreate,
    user: dict = Depends(get_current_user),
):
    """
    Create a new organization.

    The current user becomes the admin of the new organization.
    """
    org_service = get_organization_service()
    user_id = user.get("id") or user.get("sub")
    user_email = user.get("email")

    try:
        organization = await org_service.create_organization(
            org_data, user_id, user_email
        )
        logger.info(f"Organization {organization.id} created by user {user_id}")
        return organization
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=List[dict])
async def list_user_organizations(user: dict = Depends(get_current_user)):
    """
    List all organizations the current user belongs to.

    Returns organization details along with user's role in each.
    """
    org_service = get_organization_service()
    user_id = user.get("id") or user.get("sub")
    user_email = user.get("email")

    # Check if universal admin
    is_universal = org_service.is_universal_admin(user_id, user_email)

    if is_universal:
        # Universal admins can see all organizations
        organizations = await org_service.list_organizations(limit=1000)
        return [
            {
                "organization": org.model_dump(),
                "role": "universal_admin",
                "is_universal_admin": True,
            }
            for org in organizations
        ]
    else:
        # Regular users see only their organizations
        user_orgs = await org_service.get_organizations_for_user(user_id)
        result = []
        for user_org in user_orgs:
            org = await org_service.get_organization(user_org.organization_id)
            if org:
                result.append({
                    "organization": org.model_dump(),
                    "role": user_org.role,
                    "joined_at": user_org.joined_at,
                    "is_universal_admin": False,
                })
        return result


@router.get("/{organization_id}", response_model=Organization)
async def get_organization(
    organization_id: str,
    org_id: str = Depends(require_organization_access),
):
    """
    Get organization details.

    User must have access to the organization.
    """
    if organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access another organization's details",
        )

    org_service = get_organization_service()
    org = await org_service.get_organization(organization_id)

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    return org


@router.patch("/{organization_id}", response_model=Organization)
async def update_organization(
    organization_id: str,
    update_data: OrganizationUpdate,
    org_id: str = Depends(require_organization_admin_role),
):
    """
    Update organization details (admin only).

    Only organization admins can update organization settings.
    """
    if organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update another organization",
        )

    org_service = get_organization_service()
    org = await org_service.update_organization(organization_id, update_data)

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    logger.info(f"Organization {organization_id} updated")
    return org


@router.delete("/{organization_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    organization_id: str,
    org_id: str = Depends(require_organization_admin_role),
):
    """
    Delete organization (admin only).

    Soft delete - sets organization as inactive.
    Only organization admins can delete their own organization.
    """
    if organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete another organization",
        )

    org_service = get_organization_service()
    deleted = await org_service.delete_organization(organization_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    logger.info(f"Organization {organization_id} deleted")
    return None


@router.get("/{organization_id}/users", response_model=List[OrganizationUser])
async def list_organization_users(
    organization_id: str,
    org_id: str = Depends(require_organization_access),
):
    """
    List all users in the organization.

    Requires access to the organization.
    """
    if organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access another organization's users",
        )

    org_service = get_organization_service()
    users = await org_service.get_users_in_organization(organization_id)
    return users


@router.patch("/{organization_id}/users/{user_id}", response_model=OrganizationUser)
async def update_organization_user(
    organization_id: str,
    user_id: str,
    update_data: OrganizationUserUpdate,
    org_id: str = Depends(require_organization_admin_role),
):
    """
    Update organization user (admin only).

    Can change user role, permissions, etc.
    """
    if organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update users in another organization",
        )

    org_service = get_organization_service()
    org_user = await org_service.update_organization_user(
        organization_id, user_id, update_data
    )

    if not org_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization user not found",
        )

    logger.info(f"User {user_id} updated in organization {organization_id}")
    return org_user


@router.delete("/{organization_id}/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_user_from_organization(
    organization_id: str,
    user_id: str,
    org_id: str = Depends(require_organization_admin_role),
):
    """
    Remove user from organization (admin only).

    Soft delete - sets user as inactive.
    """
    if organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot remove users from another organization",
        )

    org_service = get_organization_service()
    removed = await org_service.remove_user_from_organization(organization_id, user_id)

    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in organization",
        )

    logger.info(f"User {user_id} removed from organization {organization_id}")
    return None
