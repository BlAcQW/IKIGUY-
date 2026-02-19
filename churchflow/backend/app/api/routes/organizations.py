"""
Organization Management Routes for ChurchFlow.

Handles organization CRUD, user management, and invitations.
Integrated from shared organization system with ChurchFlow-specific features.
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from apps.shared.models import (
    Organization,
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationUser,
    OrganizationUserUpdate,
    OrganizationRole,
)
from apps.shared.services.organization_service import get_organization_service
from app.api.dependencies import (
    get_current_user,  # Use local ChurchFlow JWT auth
)
from apps.shared.dependencies import (
    require_organization_access,
    require_organization_admin_role,
)
from app.models.invitation import Invitation, InvitationCreate, InvitationAccept
from app.services.invitation_service import get_invitation_service

logger = logging.getLogger(__name__)
router = APIRouter()


# ================== Organization CRUD ==================

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
        logger.info(f"Universal admin {user_email} fetching all organizations")
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
        user_orgs = await org_service.get_organizations_for_user(user_id, user_email)
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


# ================== Member Management ==================

@router.get("/{organization_id}/users", response_model=List[OrganizationUser])
async def list_organization_users(
    organization_id: str,
    org_id: str = Depends(require_organization_access),
):
    """
    List all users in the organization.

    Requires access to the organization.
    Returns full OrganizationUser objects with email, role, is_active, etc.
    """
    if organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access another organization's users",
        )

    org_service = get_organization_service()
    users = await org_service.get_users_in_organization(organization_id)
    logger.info(f"Listed {len(users)} users in organization {organization_id}")
    return users


@router.patch("/{organization_id}/members/{user_id}", response_model=OrganizationUser)
async def update_organization_member(
    organization_id: str,
    user_id: str,
    update_data: OrganizationUserUpdate,
    org_id: str = Depends(require_organization_admin_role),
):
    """
    Update organization member (admin only).

    Can change user role, permissions, etc.
    """
    if organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update members in another organization",
        )

    org_service = get_organization_service()
    org_user = await org_service.update_organization_user(
        organization_id, user_id, update_data
    )

    if not org_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization member not found",
        )

    logger.info(f"User {user_id} updated in organization {organization_id}")
    return org_user


@router.delete("/{organization_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member_from_organization(
    organization_id: str,
    user_id: str,
    org_id: str = Depends(require_organization_admin_role),
):
    """
    Remove member from organization (admin only).

    Soft delete - sets user as inactive.
    """
    if organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot remove members from another organization",
        )

    org_service = get_organization_service()
    removed = await org_service.remove_user_from_organization(organization_id, user_id)

    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in organization",
        )

    logger.info(f"User {user_id} removed from organization {organization_id}")
    return None


# ================== Invitation Management ==================

@router.post("/{organization_id}/invitations", response_model=Invitation, status_code=status.HTTP_201_CREATED)
async def create_invitation(
    organization_id: str,
    invitation_data: InvitationCreate,
    user: dict = Depends(get_current_user),
    org_id: str = Depends(require_organization_admin_role),
):
    """
    Send an invitation to join an organization.

    Requires: User must be an admin of the organization.
    """
    if organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create invitations for another organization"
        )

    org_service = get_organization_service()
    invitation_service = get_invitation_service()

    user_id = user.get("id") or user.get("sub")
    user_email = user.get("email")

    # Verify organization exists
    org = await org_service.get_organization(organization_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    try:
        # Create invitation
        invitation = await invitation_service.create_invitation(
            organization_id=organization_id,
            email=invitation_data.email,
            role=invitation_data.role,
            invited_by=user_id,
            invited_by_email=user_email,
            display_name=invitation_data.display_name,
            message=invitation_data.message
        )

        logger.info(
            f"User {user_email} sent invitation to {invitation_data.email} "
            f"for organization {organization_id}"
        )

        return invitation
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{organization_id}/invitations", response_model=List[Invitation])
async def list_invitations(
    organization_id: str,
    status: str = "pending",
    user: dict = Depends(get_current_user),
    org_id: str = Depends(require_organization_admin_role),
):
    """
    List all invitations for an organization.

    Requires: User must be an admin of the organization.
    """
    try:
        if organization_id != org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot view invitations for another organization"
            )

        invitation_service = get_invitation_service()

        # Get invitations
        invitations = await invitation_service.list_invitations(organization_id, status)

        logger.info(
            f"User {user.get('email')} listed {len(invitations)} invitations "
            f"for organization {organization_id}"
        )

        return invitations
    except Exception as e:
        logger.error(f"Error listing invitations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list invitations: {str(e)}"
        )


@router.delete("/{organization_id}/invitations/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_invitation(
    organization_id: str,
    invitation_id: str,
    user: dict = Depends(get_current_user),
    org_id: str = Depends(require_organization_admin_role),
):
    """
    Cancel a pending invitation.

    Requires: User must be an admin of the organization.
    """
    if organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot cancel invitations for another organization"
        )

    invitation_service = get_invitation_service()

    # Verify invitation belongs to this organization
    invitation = await invitation_service.get_invitation_by_id(invitation_id)
    if not invitation or invitation.organization_id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )

    # Cancel invitation
    success = await invitation_service.cancel_invitation(invitation_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to cancel invitation"
        )

    logger.info(
        f"User {user.get('email')} cancelled invitation {invitation_id} "
        f"for organization {organization_id}"
    )

    return None


@router.post("/invitations/{token}/accept", response_model=dict)
async def accept_invitation(
    token: str,
    accept_data: InvitationAccept,
    user: dict = Depends(get_current_user),
):
    """
    Accept an organization invitation (public endpoint).

    Any authenticated user can accept an invitation if they have the token.
    """
    org_service = get_organization_service()
    invitation_service = get_invitation_service()

    user_id = accept_data.user_id
    user_email = user.get("email")

    # Verify the user_id matches the authenticated user
    auth_user_id = user.get("id") or user.get("sub")
    if user_id != auth_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User ID mismatch"
        )

    try:
        # Accept invitation
        invitation = await invitation_service.accept_invitation(
            token=token,
            user_id=user_id,
            display_name=accept_data.display_name
        )

        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to accept invitation"
            )

        # Add user to organization
        await org_service.add_user_to_organization(
            organization_id=invitation.organization_id,
            user_id=user_id,
            email=invitation.email,
            display_name=accept_data.display_name,
            role=OrganizationRole(invitation.role)
        )

        logger.info(
            f"User {user_email} accepted invitation {invitation.id} "
            f"for organization {invitation.organization_id}"
        )

        return {
            "success": True,
            "message": "Invitation accepted successfully",
            "organization_id": invitation.organization_id
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
