"""
User Management API routes for DevotionalFlow.

Handles platform-level user invitations and management.
Admin-only endpoints for inviting users, managing invitations,
and viewing user details.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, Dict, Any
import logging

from app.models.platform_invite import (
    PlatformInviteCreate,
    PlatformInviteResponse,
    PlatformInviteListResponse,
    PlatformInviteVerifyResponse,
    PlatformInviteStats,
)
from app.models.user import TokenData, UserStatsResponse
from app.services.user_management_service import get_user_management_service
from app.utils.auth import get_current_admin

logger = logging.getLogger(__name__)

router = APIRouter()


# ============ Invitation Endpoints ============


@router.post(
    "/admin/users/invite",
    response_model=PlatformInviteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create platform invitation",
    description="Create a platform invitation and send email to the invitee. Admin only."
)
async def create_invite(
    invite_data: PlatformInviteCreate,
    current_admin: TokenData = Depends(get_current_admin),
):
    """
    Create a platform invitation and send email.

    **Requires admin role.**

    The invitation email includes:
    - A secure signup link with token
    - The assigned role (user/admin)
    - Optional custom message from the inviter
    - 7-day expiry notice

    Args:
        invite_data: Email address, role, and optional message

    Returns:
        Created invitation details

    Raises:
        400: User already exists or pending invite exists
        401: Not authenticated
        403: Not an admin
    """
    logger.info(
        f"Admin {current_admin.email} creating invite for {invite_data.email} "
        f"(role: {invite_data.role})"
    )

    service = get_user_management_service()

    # Get admin user details for the invite
    admin_user = await service.users_collection.find_one(
        {"email": current_admin.email}
    )
    admin_name = admin_user.get("name", "Admin") if admin_user else "Admin"

    return await service.create_invite(
        invite_data=invite_data,
        invited_by_id=current_admin.user_id,
        invited_by_name=admin_name,
        invited_by_email=current_admin.email
    )


@router.get(
    "/admin/users/invites",
    response_model=PlatformInviteListResponse,
    summary="List platform invitations",
    description="Get paginated list of all platform invitations with filters. Admin only."
)
async def list_invites(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(
        None,
        description="Filter by status: pending, accepted, revoked, expired"
    ),
    search: Optional[str] = Query(None, description="Search by email"),
    current_admin: TokenData = Depends(get_current_admin),
):
    """
    List all platform invitations with pagination and filters.

    **Requires admin role.**

    Returns invitations sorted by creation date (newest first).
    """
    service = get_user_management_service()
    return await service.list_invites(
        page=page,
        page_size=page_size,
        status_filter=status,
        search=search
    )


@router.get(
    "/admin/users/invites/stats",
    response_model=PlatformInviteStats,
    summary="Get invitation statistics",
    description="Get statistics about platform invitations. Admin only."
)
async def get_invite_stats(
    current_admin: TokenData = Depends(get_current_admin),
):
    """
    Get statistics about platform invitations.

    **Requires admin role.**

    Returns:
        - Total invites
        - Pending/accepted/expired/revoked counts
        - Invites this week
        - Acceptance rate
    """
    service = get_user_management_service()
    return await service.get_invite_stats()


@router.get(
    "/admin/users/invites/{invite_id}",
    response_model=PlatformInviteResponse,
    summary="Get invitation details",
    description="Get a specific invitation by ID. Admin only."
)
async def get_invite(
    invite_id: str,
    current_admin: TokenData = Depends(get_current_admin),
):
    """
    Get a specific invitation by ID.

    **Requires admin role.**
    """
    service = get_user_management_service()
    invite = await service.get_invite_by_id(invite_id)

    if not invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )

    return invite


@router.post(
    "/admin/users/invites/{invite_id}/resend",
    response_model=Dict[str, Any],
    summary="Resend invitation email",
    description="Resend invitation email and extend expiry. Admin only."
)
async def resend_invite(
    invite_id: str,
    current_admin: TokenData = Depends(get_current_admin),
):
    """
    Resend invitation email and extend expiry by 7 days.

    **Requires admin role.**

    The resend email is marked as a reminder and includes
    the extended expiry date.
    """
    logger.info(f"Admin {current_admin.email} resending invite {invite_id}")

    service = get_user_management_service()

    # Get admin name for the email
    admin_user = await service.users_collection.find_one(
        {"email": current_admin.email}
    )
    admin_name = admin_user.get("name", "Admin") if admin_user else "Admin"

    return await service.resend_invite(invite_id, admin_name)


@router.delete(
    "/admin/users/invites/{invite_id}",
    response_model=Dict[str, Any],
    summary="Revoke invitation",
    description="Revoke a pending invitation. Admin only."
)
async def revoke_invite(
    invite_id: str,
    current_admin: TokenData = Depends(get_current_admin),
):
    """
    Revoke a pending invitation.

    **Requires admin role.**

    Once revoked, the invitation token can no longer be used
    for signup. Cannot revoke already accepted invitations.
    """
    logger.info(f"Admin {current_admin.email} revoking invite {invite_id}")

    service = get_user_management_service()
    return await service.revoke_invite(invite_id)


# ============ Public Invite Verification (No Auth Required) ============


@router.get(
    "/users/invites/verify/{token}",
    response_model=PlatformInviteVerifyResponse,
    summary="Verify invitation token",
    description="Verify an invitation token for the signup page. No auth required."
)
async def verify_invite_token(token: str):
    """
    Verify an invitation token.

    **No authentication required.**

    Called from the signup page to:
    - Validate the invitation is still valid
    - Pre-fill the email field
    - Set the role for signup
    - Show any custom message from the inviter

    Returns:
        - valid: True if token is valid
        - email: Invited email (if valid)
        - role: Assigned role (if valid)
        - invited_by_name: Name of inviter
        - message: Custom message from inviter
        - expires_at: When the invitation expires
        - error: Error message (if invalid)
    """
    service = get_user_management_service()
    return await service.verify_invite_token(token)


# ============ User Detail Endpoints ============


@router.get(
    "/admin/users/{user_id}",
    response_model=UserStatsResponse,
    summary="Get user details",
    description="Get detailed user information including stats. Admin only."
)
async def get_user_detail(
    user_id: str,
    current_admin: TokenData = Depends(get_current_admin),
):
    """
    Get detailed user information.

    **Requires admin role.**

    Returns user profile along with:
    - Devotional count
    - Activity status
    - Account status (suspended, active)
    """
    service = get_user_management_service()
    user = await service.get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user
