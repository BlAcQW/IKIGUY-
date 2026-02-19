"""
Group Invite API routes for DevotionalFlow.
Handles group invitations and acceptance.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
import logging

from app.models.invite import (
    InviteCreate,
    InviteResponse,
    InviteListResponse,
    AcceptInviteRequest,
)
from app.services.invite_service import (
    create_invite,
    get_invite_by_token,
    accept_invite,
    decline_invite,
    list_group_invites,
    revoke_invite,
)
from app.utils.auth import get_current_user
from app.models.user import TokenData

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/groups/{group_id}/invites", response_model=InviteResponse, status_code=status.HTTP_201_CREATED)
async def create_invite_endpoint(
    group_id: str,
    invite_data: InviteCreate,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Create a group invite.

    **Path Parameters:**
    - group_id: Group ID

    **Request Body:**
    - invitee_email: Email address to invite (optional if invitee_id provided)
    - invitee_id: User ID to invite (optional if invitee_email provided)

    **Auth Required:** Yes (must be creator or admin)
    """
    logger.info(f"User {current_user.user_id} creating invite for group {group_id}")
    invite = await create_invite(group_id, current_user.user_id, invite_data)
    return invite


@router.get("/groups/{group_id}/invites", response_model=InviteListResponse)
async def list_invites_endpoint(
    group_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter by status: pending, accepted, declined, expired"),
    current_user: TokenData = Depends(get_current_user),
):
    """
    List invites for a group.

    **Path Parameters:**
    - group_id: Group ID

    **Query Parameters:**
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    - status: Filter by status (optional)

    **Auth Required:** Yes (must be creator or admin)
    """
    invites = await list_group_invites(
        group_id, page=page, page_size=page_size, status_filter=status
    )
    return invites


@router.get("/invites/token/{token}", response_model=InviteResponse)
async def get_invite_by_token_endpoint(token: str):
    """
    Get invite details by token (for invite acceptance page).

    **Path Parameters:**
    - token: Invite token

    **Auth Required:** No
    """
    invite = await get_invite_by_token(token)
    if not invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite not found or expired",
        )
    return invite


@router.post("/invites/token/{token}/accept", status_code=status.HTTP_200_OK)
async def accept_invite_endpoint(
    token: str,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Accept a group invite.

    **Path Parameters:**
    - token: Invite token

    **Auth Required:** Yes
    """
    logger.info(f"User {current_user.user_id} accepting invite {token}")
    result = await accept_invite(token, current_user.user_id)
    return result


@router.post("/invites/{invite_id}/decline", status_code=status.HTTP_200_OK)
async def decline_invite_endpoint(
    invite_id: str,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Decline a group invite.

    **Path Parameters:**
    - invite_id: Invite ID

    **Auth Required:** Yes
    """
    logger.info(f"User {current_user.user_id} declining invite {invite_id}")
    await decline_invite(invite_id, current_user.user_id)
    return {"message": "Invite declined"}


@router.delete("/invites/{invite_id}", status_code=status.HTTP_200_OK)
async def revoke_invite_endpoint(
    invite_id: str,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Revoke (delete) a group invite.

    **Path Parameters:**
    - invite_id: Invite ID

    **Auth Required:** Yes (must be creator or admin)
    """
    logger.info(f"User {current_user.user_id} revoking invite {invite_id}")
    await revoke_invite(invite_id, current_user.user_id)
    return {"message": "Invite revoked successfully"}

