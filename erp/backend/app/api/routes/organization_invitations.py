"""
Organization Invitation Routes for ERP.

Handles organization member invitations.
Integrated from ChurchFlow's invitation system.
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.models.invitation import Invitation, InvitationCreate, InvitationAccept
from app.services.invitation_service import get_invitation_service
from apps.shared.services.organization_service import get_organization_service
from apps.shared.dependencies import get_current_user, require_organization_admin_role
from apps.shared.models import OrganizationRole

logger = logging.getLogger(__name__)
router = APIRouter()


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


@router.post("/{organization_id}/invitations/{invitation_id}/resend", response_model=dict)
async def resend_invitation_email(
    organization_id: str,
    invitation_id: str,
    user: dict = Depends(get_current_user),
    org_id: str = Depends(require_organization_admin_role),
):
    """
    Resend the invitation email for a pending invitation.

    Requires: User must be an admin of the organization.
    """
    if organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot resend invitations for another organization"
        )

    invitation_service = get_invitation_service()

    # Verify invitation belongs to this organization
    invitation = await invitation_service.get_invitation_by_id(invitation_id)
    if not invitation or invitation.organization_id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )

    try:
        result = await invitation_service.resend_invitation_email(invitation_id)

        if result.get("success"):
            logger.info(
                f"User {user.get('email')} resent invitation email for {invitation.email} "
                f"in organization {organization_id}"
            )
            return {
                "success": True,
                "message": f"Invitation email resent to {invitation.email}",
                "message_id": result.get("message_id")
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send email: {result.get('error')}"
            )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


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
