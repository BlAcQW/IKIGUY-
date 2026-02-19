"""Organization management routes."""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from typing import List, Optional, Dict, Any
from datetime import datetime
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..models import (
    Organization, OrganizationUser, OrganizationInvitation,
    OrganizationCreate, OrganizationUpdate, OrganizationUserUpdate,
    OrganizationInviteRequest, OrganizationInviteResponse,
    OrganizationRole, InvitationStatus, OrganizationStyleSettings
)
from ..services.organization_service import organization_service
from ..auth import get_current_user_mongo

router = APIRouter(prefix="/organizations", tags=["organizations"])
limiter = Limiter(key_func=get_remote_address)


def get_user_organization_access(user: dict, org_id: str, required_permission: str = None):
    """Check if user has access to organization and optionally specific permission.

    Args:
        user: Current user from auth.
        org_id: Organization ID.
        required_permission: Optional permission to check.

    Returns:
        OrganizationUser: User's organization membership.

    Raises:
        HTTPException: If user doesn't have access.
    """
    # Get user ID from JWT token - use tenant_id (sub) as primary user identifier
    user_id = user.get("tenant_id") or user.get("account_id") or user.get("sub", "default-account")
    user_email = user.get("email", "")

    # Check if user is a universal admin - they have access to all organizations
    if organization_service.is_universal_admin(user_id, user_email):
        # For universal admins, create a virtual organization user entry
        from ..models import OrganizationUser, OrganizationRole
        virtual_org_user = OrganizationUser(
            organization_id=org_id,
            user_id=user_id,
            email=user.get("email", ""),
            role=OrganizationRole.UNIVERSAL_ADMIN,
            display_name=user.get("name", user.get("email", "Universal Admin"))
        )
        return virtual_org_user

    org_user = organization_service.get_user_in_organization(org_id, user_id)
    if not org_user:
        raise HTTPException(status_code=403, detail="Access denied to organization")

    if required_permission and not organization_service.check_user_permission(org_id, user_id, required_permission):
        raise HTTPException(status_code=403, detail=f"Permission denied: {required_permission}")

    return org_user


# Organization CRUD Operations
@router.post("/", response_model=Organization)
def create_organization(
    org_data: OrganizationCreate,
    user: dict = Depends(get_current_user_mongo)
):
    """
    Create a new organization.

    Restricted to universal_admin users only.
    """
    try:
        # Get user data from JWT token
        user_id = user.get("tenant_id") or user.get("account_id") or user.get("sub", "default-account")
        user_email = user.get("email", "user@example.com")

        # Restrict organization creation to universal_admin only
        if not organization_service.is_universal_admin(user_id, user_email):
            raise HTTPException(
                status_code=403,
                detail="Only universal administrators can create organizations"
            )

        org = organization_service.create_organization(org_data, user_id, user_email)
        return org
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/all", response_model=List[Organization])
def get_all_organizations(
    search: Optional[str] = Query(None, description="Search in name, display_name, or description"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(1000, ge=1, le=1000, description="Maximum records to return"),
    user: dict = Depends(get_current_user_mongo)
):
    """
    Get all organizations in the system with advanced search.

    Restricted to universal_admin users only.

    **Search Capabilities:**
    - `search`: Case-insensitive search across name, display_name, and description
    - `industry`: Filter by industry (case-insensitive)
    - `is_active`: Filter by active/inactive status

    **Example:**
    ```
    GET /organizations/all?search=church&industry=religious&is_active=true
    ```
    """
    user_id = user.get("tenant_id") or user.get("account_id") or user.get("sub", "default-account")
    user_email = user.get("email", "")

    # Restrict to universal_admin only
    if not organization_service.is_universal_admin(user_id, user_email):
        raise HTTPException(
            status_code=403,
            detail="Only universal administrators can view all organizations"
        )

    return organization_service.get_all_organizations_for_universal_admin(
        search=search,
        industry=industry,
        is_active=is_active,
        skip=skip,
        limit=limit
    )


@router.get("/")
@limiter.limit("30/minute")  # Stricter limit for this endpoint to prevent spam
def get_user_organizations(
    request: Request,
    user: dict = Depends(get_current_user_mongo)
):
    """
    Get all organizations for the current user with membership details.

    Returns organization memberships including role information.
    """
    user_id = user.get("tenant_id") or user.get("account_id") or user.get("sub", "default-account")
    user_email = user.get("email", "")

    # Get memberships with organization details
    memberships = organization_service.get_user_organization_memberships(user_id, user_email)

    return {
        "organizations": memberships
    }


@router.get("/{org_id}", response_model=Organization)
def get_organization(
    org_id: str,
    user: dict = Depends(get_current_user_mongo)
):
    """Get organization details."""
    # Check access
    get_user_organization_access(user, org_id)

    org = organization_service.get_organization(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    return org


@router.put("/{org_id}", response_model=Organization)
def update_organization(
    org_id: str,
    update_data: OrganizationUpdate,
    user: dict = Depends(get_current_user_mongo)
):
    """Update organization details."""
    # Check admin permission
    get_user_organization_access(user, org_id, "manage_settings")

    org = organization_service.update_organization(org_id, update_data)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    return org


@router.delete("/{org_id}")
def delete_organization(
    org_id: str,
    user: dict = Depends(get_current_user_mongo)
):
    """
    Delete organization (soft delete).

    Allowed for:
    - Universal admins (can delete any organization)
    - Organization owners (can delete their own organization)
    """
    # Get user ID and email
    user_id = user.get("tenant_id") or user.get("account_id") or user.get("sub", "default-account")
    user_email = user.get("email", "")

    # Allow universal_admin to delete any organization
    is_universal_admin = organization_service.is_universal_admin(user_id, user_email)

    if not is_universal_admin:
        # Check if user is owner of this specific organization
        org_user = get_user_organization_access(user, org_id)
        if org_user.role != OrganizationRole.OWNER:
            raise HTTPException(
                status_code=403,
                detail="Only organization owner or universal admin can delete organization"
            )

    success = organization_service.delete_organization(org_id)
    if not success:
        raise HTTPException(status_code=404, detail="Organization not found")

    return {"message": "Organization deleted successfully"}


# User Management
@router.get("/{org_id}/users", response_model=List[OrganizationUser])
def get_organization_users(
    org_id: str,
    user: dict = Depends(get_current_user_mongo)
):
    """Get all users in the organization."""
    # Check view users permission
    get_user_organization_access(user, org_id, "view_users")

    return organization_service.get_organization_users(org_id)


@router.get("/{org_id}/users/{user_id}", response_model=OrganizationUser)
def get_organization_user(
    org_id: str,
    user_id: str,
    user: dict = Depends(get_current_user_mongo)
):
    """Get specific user in organization."""
    # Check access
    get_user_organization_access(user, org_id, "view_users")

    org_user = organization_service.get_user_in_organization(org_id, user_id)
    if not org_user:
        raise HTTPException(status_code=404, detail="User not found in organization")

    return org_user


@router.put("/{org_id}/users/{user_id}", response_model=OrganizationUser)
def update_organization_user(
    org_id: str,
    user_id: str,
    update_data: OrganizationUserUpdate,
    user: dict = Depends(get_current_user_mongo)
):
    """Update user role/permissions in organization."""
    # Check manage users permission
    get_user_organization_access(user, org_id, "manage_users")

    updated_user = organization_service.update_organization_user(org_id, user_id, update_data)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found in organization")

    return updated_user


@router.delete("/{org_id}/users/{user_id}")
def remove_organization_user(
    org_id: str,
    user_id: str,
    user: dict = Depends(get_current_user_mongo)
):
    """Remove user from organization."""
    # Check manage users permission
    get_user_organization_access(user, org_id, "manage_users")

    # Prevent removing the last owner
    org_users = organization_service.get_organization_users(org_id)
    owners = [u for u in org_users if u.role == OrganizationRole.OWNER]

    user_to_remove = organization_service.get_user_in_organization(org_id, user_id)
    if user_to_remove and user_to_remove.role == OrganizationRole.OWNER and len(owners) == 1:
        raise HTTPException(status_code=400, detail="Cannot remove the last owner from organization")

    success = organization_service.remove_user_from_organization(org_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found in organization")

    return {"message": "User removed from organization"}


# Invitation System
@router.post("/{org_id}/invitations", response_model=OrganizationInvitation)
def create_invitation(
    org_id: str,
    invite_data: OrganizationInviteRequest,
    user: dict = Depends(get_current_user_mongo)
):
    """Invite a user to join the organization."""
    # Check manage users permission
    get_user_organization_access(user, org_id, "manage_users")

    # Check if user is already in organization or has pending invitation
    existing_users = organization_service.get_organization_users(org_id)
    if any(u.email.lower() == invite_data.email.lower() for u in existing_users):
        raise HTTPException(status_code=400, detail="User is already a member of this organization")

    pending_invitations = organization_service.get_organization_invitations(org_id)
    if any(
        inv.email.lower() == invite_data.email.lower() and inv.status == InvitationStatus.PENDING
        for inv in pending_invitations
    ):
        raise HTTPException(status_code=400, detail="User already has a pending invitation")

    # Create invitation
    user_id = user.get("tenant_id") or user.get("account_id") or user.get("sub", "default-account")
    user_email = user.get("email", "user@example.com")

    invitation = organization_service.create_invitation(org_id, invite_data, user_id, user_email)

    # TODO: Send invitation email

    return invitation


@router.get("/{org_id}/invitations", response_model=List[OrganizationInvitation])
def get_organization_invitations(
    org_id: str,
    user: dict = Depends(get_current_user_mongo)
):
    """Get all invitations for the organization."""
    # Check manage users permission
    get_user_organization_access(user, org_id, "manage_users")

    return organization_service.get_organization_invitations(org_id)


@router.post("/invitations/{token}/accept", response_model=OrganizationUser)
def accept_invitation(
    token: str,
    user: dict = Depends(get_current_user_mongo)
):
    """Accept an organization invitation."""
    user_id = user.get("tenant_id") or user.get("account_id") or user.get("sub", "default-account")
    user_email = user.get("email", "user@example.com")

    org_user = organization_service.accept_invitation(token, user_id, user_email)
    if not org_user:
        raise HTTPException(status_code=400, detail="Invalid or expired invitation")

    return org_user


@router.post("/invitations/{token}/decline")
def decline_invitation(
    token: str,
    message: str = Query("", description="Optional decline message")
):
    """Decline an organization invitation."""
    success = organization_service.decline_invitation(token, message)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid or expired invitation")

    return {"message": "Invitation declined"}


@router.delete("/{org_id}/invitations/{invitation_id}")
def cancel_invitation(
    org_id: str,
    invitation_id: str,
    user: dict = Depends(get_current_user_mongo)
):
    """Cancel a pending invitation."""
    # Check manage users permission
    get_user_organization_access(user, org_id, "manage_users")

    success = organization_service.cancel_invitation(invitation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Invitation not found or already responded")

    return {"message": "Invitation cancelled"}


# Style Settings
@router.get("/{org_id}/style-settings", response_model=OrganizationStyleSettings)
def get_organization_style_settings(
    org_id: str,
    user: dict = Depends(get_current_user_mongo)
):
    """Get organization style settings."""
    # Check access
    get_user_organization_access(user, org_id)

    org = organization_service.get_organization(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Convert style_settings dict to OrganizationStyleSettings model
    style_settings = OrganizationStyleSettings(**org.style_settings) if org.style_settings else OrganizationStyleSettings()
    return style_settings


@router.put("/{org_id}/style-settings", response_model=Organization)
def update_organization_style_settings(
    org_id: str,
    style_settings: OrganizationStyleSettings,
    user: dict = Depends(get_current_user_mongo)
):
    """Update organization style settings."""
    # Check manage settings permission
    get_user_organization_access(user, org_id, "manage_settings")

    updated_org = organization_service.update_organization_style_settings(
        org_id,
        style_settings.model_dump()
    )

    if not updated_org:
        raise HTTPException(status_code=404, detail="Organization not found")

    return updated_org


# Permission Checks
@router.get("/{org_id}/permissions/{permission}")
def check_user_permission(
    org_id: str,
    permission: str,
    user: dict = Depends(get_current_user_mongo)
):
    """Check if current user has specific permission in organization."""
    user_id = user.get("tenant_id") or user.get("account_id") or user.get("sub", "default-account")

    has_permission = organization_service.check_user_permission(org_id, user_id, permission)

    return {
        "permission": permission,
        "has_permission": has_permission
    }


@router.get("/{org_id}/my-role", response_model=OrganizationUser)
def get_my_organization_role(
    org_id: str,
    user: dict = Depends(get_current_user_mongo)
):
    """Get current user's role and permissions in organization."""
    user_id = user.get("tenant_id") or user.get("account_id") or user.get("sub", "default-account")

    org_user = organization_service.get_user_in_organization(org_id, user_id)
    if not org_user:
        raise HTTPException(status_code=403, detail="Not a member of this organization")

    return org_user