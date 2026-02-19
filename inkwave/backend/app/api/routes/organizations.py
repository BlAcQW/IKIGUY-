"""Organization Management Routes for InkWave"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List
import logging
import sys
import os

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../..")))

from apps.shared.models import (
    Organization, OrganizationCreate, OrganizationUpdate,
    OrganizationInvitation, OrganizationInviteRequest, InvitationStatus
)
from apps.shared.services.organization_service import get_organization_service
from app.core.auth import get_current_user
from datetime import datetime, timedelta
import secrets

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.post("", response_model=Organization)
async def create_organization(
    org_data: OrganizationCreate,
    user: dict = Depends(get_current_user)
):
    """Create a new audiobook organization."""
    try:
        org_service = get_organization_service()
        user_id = user.user_id
        user_email = user.email
        
        organization = await org_service.create_organization(
            org_data, user_id, user_email
        )
        logger.info(f"Created organization {organization.id} by user {user_email}")
        return organization
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating organization: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create organization")


@router.get("", response_model=List[dict])
async def list_organizations(user: dict = Depends(get_current_user)):
    """List all organizations the current user belongs to."""
    try:
        org_service = get_organization_service()
        user_orgs = await org_service.get_organizations_for_user(user.user_id)
        
        organizations = []
        for user_org in user_orgs:
            org = await org_service.get_organization(user_org.organization_id)
            if org:
                organizations.append({
                    "organization": org.model_dump(),
                    "role": user_org.role.value,
                    "joined_at": user_org.joined_at.isoformat() if user_org.joined_at else None,
                })
        return organizations
    except Exception as e:
        logger.error(f"Error listing organizations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list organizations")


@router.get("/{organization_id}", response_model=Organization)
async def get_organization(
    organization_id: str,
    user: dict = Depends(get_current_user)
):
    """Get organization details."""
    try:
        org_service = get_organization_service()

        # Check access
        has_access = await org_service.has_access_to_organization(
            organization_id, user.user_id, user.email
        )
        if not has_access:
            raise HTTPException(status_code=403, detail="Access denied")

        org = await org_service.get_organization(organization_id)
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        return org
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting organization: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get organization")


@router.put("/{organization_id}", response_model=Organization)
async def update_organization(
    organization_id: str,
    org_data: OrganizationUpdate,
    user: dict = Depends(get_current_user)
):
    """Update organization details."""
    try:
        org_service = get_organization_service()

        # Check if user is admin
        is_admin = await org_service.is_admin(organization_id, user.user_id)
        is_universal_admin = org_service.is_universal_admin(user.user_id, user.email)

        if not is_admin and not is_universal_admin:
            raise HTTPException(status_code=403, detail="Only admins can update organization")

        updated_org = await org_service.update_organization(organization_id, org_data)
        if not updated_org:
            raise HTTPException(status_code=404, detail="Organization not found")

        logger.info(f"Updated organization {organization_id} by user {user.email}")
        return updated_org
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating organization: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update organization")


@router.delete("/{organization_id}")
async def delete_organization(
    organization_id: str,
    user: dict = Depends(get_current_user)
):
    """Delete (deactivate) organization."""
    try:
        org_service = get_organization_service()

        # Check if user is admin
        is_admin = await org_service.is_admin(organization_id, user.user_id)
        is_universal_admin = org_service.is_universal_admin(user.user_id, user.email)

        if not is_admin and not is_universal_admin:
            raise HTTPException(status_code=403, detail="Only admins can delete organization")

        success = await org_service.delete_organization(organization_id)
        if not success:
            raise HTTPException(status_code=404, detail="Organization not found")

        logger.info(f"Deleted organization {organization_id} by user {user.email}")
        return {"success": True, "message": "Organization deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting organization: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete organization")


@router.get("/{organization_id}/users", response_model=List[dict])
async def list_organization_users(
    organization_id: str,
    user: dict = Depends(get_current_user)
):
    """List all users in an organization - returns full OrganizationUser objects."""
    try:
        org_service = get_organization_service()

        # Check access
        has_access = await org_service.has_access_to_organization(
            organization_id, user.user_id, user.email
        )
        if not has_access:
            raise HTTPException(status_code=403, detail="Access denied")

        users = await org_service.get_users_in_organization(organization_id)
        return [user_obj.model_dump() for user_obj in users]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing organization users: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list organization users")


@router.put("/{organization_id}/members/{user_id}")
async def update_organization_member(
    organization_id: str,
    user_id: str,
    update_data: dict,
    user: dict = Depends(get_current_user)
):
    """Update organization member role or permissions."""
    try:
        org_service = get_organization_service()

        # Check if user is admin
        is_admin = await org_service.is_admin(organization_id, user.user_id)
        is_universal_admin = org_service.is_universal_admin(user.user_id, user.email)

        if not is_admin and not is_universal_admin:
            raise HTTPException(status_code=403, detail="Only admins can update members")

        from apps.shared.models import OrganizationUserUpdate
        org_user_update = OrganizationUserUpdate(**update_data)

        updated_member = await org_service.update_organization_user(
            organization_id, user_id, org_user_update
        )
        if not updated_member:
            raise HTTPException(status_code=404, detail="Member not found")

        logger.info(f"Updated member {user_id} in organization {organization_id} by {user.email}")
        return updated_member.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating organization member: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update organization member")


@router.delete("/{organization_id}/members/{user_id}")
async def remove_organization_member(
    organization_id: str,
    user_id: str,
    user: dict = Depends(get_current_user)
):
    """Remove member from organization."""
    try:
        org_service = get_organization_service()

        # Check if user is admin
        is_admin = await org_service.is_admin(organization_id, user.user_id)
        is_universal_admin = org_service.is_universal_admin(user.user_id, user.email)

        if not is_admin and not is_universal_admin:
            raise HTTPException(status_code=403, detail="Only admins can remove members")

        # Prevent removing self if last admin
        if user.user_id == user_id:
            admins = await org_service.get_users_in_organization(
                organization_id,
                role="admin"
            )
            if len(admins) <= 1:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot remove yourself as the last admin"
                )

        success = await org_service.remove_user_from_organization(organization_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Member not found")

        logger.info(f"Removed member {user_id} from organization {organization_id} by {user.email}")
        return {"success": True, "message": "Member removed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing organization member: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to remove organization member")


@router.get("/{organization_id}/invitations", response_model=List[dict])
async def list_organization_invitations(
    organization_id: str,
    user: dict = Depends(get_current_user)
):
    """List all invitations for an organization."""
    try:
        org_service = get_organization_service()

        # Check if user is admin
        is_admin = await org_service.is_admin(organization_id, user.user_id)
        is_universal_admin = org_service.is_universal_admin(user.user_id, user.email)

        if not is_admin and not is_universal_admin:
            raise HTTPException(status_code=403, detail="Only admins can view invitations")

        # Get invitations from database
        from app.core.database import get_db
        db = get_db()
        cursor = db.organization_invitations.find({"organization_id": organization_id})
        invitations = await cursor.to_list(length=100)

        # Convert to response format
        result = []
        for inv in invitations:
            result.append({
                "id": inv.get("id"),
                "email": inv.get("email"),
                "role": inv.get("role"),
                "status": inv.get("status"),
                "invited_at": inv.get("created_at").isoformat() if inv.get("created_at") else None,
                "invited_by": inv.get("invited_by_email"),
                "expires_at": inv.get("expires_at").isoformat() if inv.get("expires_at") else None
            })

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing organization invitations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list organization invitations")


@router.post("/{organization_id}/invitations")
async def create_organization_invitation(
    organization_id: str,
    invite_data: OrganizationInviteRequest,
    user: dict = Depends(get_current_user)
):
    """Send an invitation to join organization."""
    try:
        org_service = get_organization_service()

        # Check if user is admin
        is_admin = await org_service.is_admin(organization_id, user.user_id)
        is_universal_admin = org_service.is_universal_admin(user.user_id, user.email)

        if not is_admin and not is_universal_admin:
            raise HTTPException(status_code=403, detail="Only admins can send invitations")

        # Check if user is already a member
        existing_member = await org_service.get_organization_user(organization_id, invite_data.email)
        if existing_member:
            raise HTTPException(status_code=400, detail="User is already a member of this organization")

        # Check if invitation already exists
        from app.core.database import get_db
        db = get_db()
        existing_inv = await db.organization_invitations.find_one({
            "organization_id": organization_id,
            "email": invite_data.email,
            "status": InvitationStatus.PENDING
        })
        if existing_inv:
            raise HTTPException(status_code=400, detail="Invitation already sent to this email")

        # Create invitation
        invitation_token = secrets.token_urlsafe(32)
        invitation = OrganizationInvitation(
            organization_id=organization_id,
            email=invite_data.email,
            role=invite_data.role,
            invited_by_user_id=user.user_id,
            invited_by_email=user.email,
            invitation_token=invitation_token,
            status=InvitationStatus.PENDING,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )

        await db.organization_invitations.insert_one(invitation.model_dump())

        logger.info(f"Created invitation for {invite_data.email} to organization {organization_id}")
        return {
            "success": True,
            "message": "Invitation sent successfully",
            "invitation": {
                "id": invitation.id,
                "email": invitation.email,
                "role": invitation.role.value,
                "status": invitation.status.value,
                "expires_at": invitation.expires_at.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating organization invitation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create organization invitation")


@router.delete("/{organization_id}/invitations/{invitation_id}")
async def cancel_organization_invitation(
    organization_id: str,
    invitation_id: str,
    user: dict = Depends(get_current_user)
):
    """Cancel an organization invitation."""
    try:
        org_service = get_organization_service()

        # Check if user is admin
        is_admin = await org_service.is_admin(organization_id, user.user_id)
        is_universal_admin = org_service.is_universal_admin(user.user_id, user.email)

        if not is_admin and not is_universal_admin:
            raise HTTPException(status_code=403, detail="Only admins can cancel invitations")

        # Update invitation status
        from app.core.database import get_db
        db = get_db()
        result = await db.organization_invitations.update_one(
            {
                "id": invitation_id,
                "organization_id": organization_id
            },
            {
                "$set": {
                    "status": InvitationStatus.EXPIRED,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Invitation not found")

        logger.info(f"Cancelled invitation {invitation_id} for organization {organization_id}")
        return {"success": True, "message": "Invitation cancelled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling organization invitation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to cancel organization invitation")
