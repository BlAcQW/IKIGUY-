"""
Group Invite service for DevotionalFlow.
Handles group invitations, invite links, and acceptance.
"""

from typing import Optional, List
from datetime import datetime, timedelta
from bson import ObjectId
from fastapi import HTTPException, status
import secrets

from app.db.mongodb import get_database
from app.models.invite import (
    InviteCreate,
    InviteResponse,
    InviteListResponse,
)
import logging

logger = logging.getLogger(__name__)

# Invite tokens expire after 7 days
INVITE_EXPIRY_DAYS = 7


def generate_invite_token() -> str:
    """
    Generate a secure invite token.

    Returns:
        str: Unique invite token.
    """
    return secrets.token_urlsafe(32)


async def create_invite(
    group_id: str, inviter_id: str, invite_data: InviteCreate
) -> InviteResponse:
    """
    Create a group invite.

    Args:
        group_id: Group ID.
        inviter_id: User ID creating the invite.
        invite_data: Invite creation data.

    Returns:
        InviteResponse: Created invite.
    """
    db = get_database()

    if not ObjectId.is_valid(group_id) or not ObjectId.is_valid(inviter_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid group or user ID",
        )

    # Check if group exists
    group_doc = await db.groups.find_one({"_id": ObjectId(group_id)})
    if not group_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    # Check if inviter is creator or admin
    is_creator = str(group_doc["creator_id"]) == inviter_id
    is_admin = any(
        str(member["user_id"]) == inviter_id and member.get("role") == "admin"
        for member in group_doc.get("members", [])
    )

    if not (is_creator or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only group creator or admins can create invites",
        )

    # Check if invitee_email or invitee_id is provided
    if not invite_data.invitee_email and not invite_data.invitee_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either invitee_email or invitee_id must be provided",
        )

    # If invitee_id is provided, check if user exists and is already a member
    if invite_data.invitee_id:
        if not ObjectId.is_valid(invite_data.invitee_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid invitee ID",
            )

        # Check if already a member
        is_member = any(
            str(member["user_id"]) == invite_data.invitee_id
            for member in group_doc.get("members", [])
        )
        if is_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member of this group",
            )

    # Check for existing pending invite
    existing_query = {"group_id": ObjectId(group_id), "status": "pending"}
    if invite_data.invitee_email:
        existing_query["invitee_email"] = invite_data.invitee_email
    if invite_data.invitee_id:
        existing_query["invitee_id"] = ObjectId(invite_data.invitee_id)

    existing_invite = await db.group_invites.find_one(existing_query)
    if existing_invite:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pending invite already exists for this user",
        )

    # Get inviter info
    inviter = await db.users.find_one({"_id": ObjectId(inviter_id)})
    if not inviter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inviter not found",
        )

    # Generate invite token
    invite_token = generate_invite_token()
    expires_at = datetime.utcnow() + timedelta(days=INVITE_EXPIRY_DAYS)

    # Create invite document
    invite_dict = {
        "group_id": ObjectId(group_id),
        "inviter_id": ObjectId(inviter_id),
        "invitee_email": invite_data.invitee_email,
        "invitee_id": ObjectId(invite_data.invitee_id) if invite_data.invitee_id else None,
        "invite_token": invite_token,
        "status": "pending",
        "expires_at": expires_at,
        "created_at": datetime.utcnow(),
        "accepted_at": None,
    }

    result = await db.group_invites.insert_one(invite_dict)
    invite_dict["_id"] = result.inserted_id

    return InviteResponse(
        id=str(invite_dict["_id"]),
        group_id=group_id,
        inviter_id=inviter_id,
        inviter_name=inviter.get("name", "Unknown"),
        invitee_email=invite_data.invitee_email,
        invitee_id=invite_data.invitee_id,
        invite_token=invite_token,
        status="pending",
        expires_at=expires_at,
        created_at=invite_dict["created_at"],
        accepted_at=None,
    )


async def get_invite_by_token(token: str) -> Optional[InviteResponse]:
    """
    Get an invite by token.

    Args:
        token: Invite token.

    Returns:
        InviteResponse or None if not found.
    """
    db = get_database()

    invite_doc = await db.group_invites.find_one({"invite_token": token})
    if not invite_doc:
        return None

    # Check if expired
    if invite_doc.get("expires_at") < datetime.utcnow():
        # Mark as expired
        await db.group_invites.update_one(
            {"_id": invite_doc["_id"]}, {"$set": {"status": "expired"}}
        )
        return None

    # Get inviter info
    inviter = await db.users.find_one({"_id": invite_doc["inviter_id"]})
    if not inviter:
        inviter = {"name": "Unknown"}

    return InviteResponse(
        id=str(invite_doc["_id"]),
        group_id=str(invite_doc["group_id"]),
        inviter_id=str(invite_doc["inviter_id"]),
        inviter_name=inviter.get("name", "Unknown"),
        invitee_email=invite_doc.get("invitee_email"),
        invitee_id=str(invite_doc["invitee_id"]) if invite_doc.get("invitee_id") else None,
        invite_token=invite_doc["invite_token"],
        status=invite_doc.get("status", "pending"),
        expires_at=invite_doc.get("expires_at"),
        created_at=invite_doc.get("created_at", datetime.utcnow()),
        accepted_at=invite_doc.get("accepted_at"),
    )


async def accept_invite(token: str, user_id: str) -> dict:
    """
    Accept a group invite.

    Args:
        token: Invite token.
        user_id: User ID accepting the invite.

    Returns:
        dict: Success message and group ID.
    """
    db = get_database()

    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID",
        )

    # Get invite
    invite_doc = await db.group_invites.find_one({"invite_token": token})
    if not invite_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite not found",
        )

    # Check if already accepted or declined
    if invite_doc.get("status") != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invite has already been {invite_doc.get('status')}",
        )

    # Check if expired
    if invite_doc.get("expires_at") < datetime.utcnow():
        await db.group_invites.update_one(
            {"_id": invite_doc["_id"]}, {"$set": {"status": "expired"}}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invite has expired",
        )

    # Check if invitee matches (if invitee_id or invitee_email is set)
    if invite_doc.get("invitee_id"):
        if str(invite_doc["invitee_id"]) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This invite is for a different user",
            )

    # Get user to verify email match if invitee_email is set
    if invite_doc.get("invitee_email"):
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        if user.get("email") != invite_doc["invitee_email"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This invite is for a different email address",
            )

    group_id = str(invite_doc["group_id"])

    # Check if already a member
    group_doc = await db.groups.find_one({"_id": invite_doc["group_id"]})
    if not group_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    is_member = any(
        str(member["user_id"]) == user_id for member in group_doc.get("members", [])
    )
    if is_member:
        # Mark invite as accepted anyway
        await db.group_invites.update_one(
            {"_id": invite_doc["_id"]},
            {
                "$set": {
                    "status": "accepted",
                    "accepted_at": datetime.utcnow(),
                }
            },
        )
        return {"message": "Already a member", "group_id": group_id}

    # Add user to group (reuse join_group logic)
    from app.services.group_service import join_group

    try:
        await join_group(group_id, user_id)
    except HTTPException as e:
        # If join fails, don't mark invite as accepted
        raise e

    # Mark invite as accepted
    await db.group_invites.update_one(
        {"_id": invite_doc["_id"]},
        {
            "$set": {
                "status": "accepted",
                "accepted_at": datetime.utcnow(),
            }
        },
    )

    logger.info(f"User {user_id} accepted invite to group {group_id}")

    return {"message": "Invite accepted successfully", "group_id": group_id}


async def decline_invite(invite_id: str, user_id: str) -> None:
    """
    Decline a group invite.

    Args:
        invite_id: Invite ID.
        user_id: User ID declining the invite.
    """
    db = get_database()

    if not ObjectId.is_valid(invite_id) or not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid invite or user ID",
        )

    invite_doc = await db.group_invites.find_one({"_id": ObjectId(invite_id)})
    if not invite_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite not found",
        )

    # Check if user is the invitee
    if invite_doc.get("invitee_id") and str(invite_doc["invitee_id"]) != user_id:
        # Check email match
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user or user.get("email") != invite_doc.get("invitee_email"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only decline your own invites",
            )

    if invite_doc.get("status") != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invite is not pending",
        )

    await db.group_invites.update_one(
        {"_id": ObjectId(invite_id)},
        {"$set": {"status": "declined"}},
    )


async def list_group_invites(
    group_id: str, page: int = 1, page_size: int = 20, status_filter: Optional[str] = None
) -> InviteListResponse:
    """
    List invites for a group.

    Args:
        group_id: Group ID.
        page: Page number.
        page_size: Items per page.
        status_filter: Filter by status (pending, accepted, declined, expired).

    Returns:
        InviteListResponse: Paginated list of invites.
    """
    db = get_database()

    if not ObjectId.is_valid(group_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid group ID",
        )

    query = {"group_id": ObjectId(group_id)}
    if status_filter:
        query["status"] = status_filter

    # Count total
    total = await db.group_invites.count_documents(query)

    # Get invites
    skip = (page - 1) * page_size
    cursor = (
        db.group_invites.find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(page_size)
    )

    invites = []
    async for invite_doc in cursor:
        inviter = await db.users.find_one({"_id": invite_doc["inviter_id"]})
        if not inviter:
            inviter = {"name": "Unknown"}

        invites.append(
            InviteResponse(
                id=str(invite_doc["_id"]),
                group_id=str(invite_doc["group_id"]),
                inviter_id=str(invite_doc["inviter_id"]),
                inviter_name=inviter.get("name", "Unknown"),
                invitee_email=invite_doc.get("invitee_email"),
                invitee_id=str(invite_doc["invitee_id"]) if invite_doc.get("invitee_id") else None,
                invite_token=invite_doc["invite_token"],
                status=invite_doc.get("status", "pending"),
                expires_at=invite_doc.get("expires_at"),
                created_at=invite_doc.get("created_at", datetime.utcnow()),
                accepted_at=invite_doc.get("accepted_at"),
            )
        )

    total_pages = (total + page_size - 1) // page_size

    return InviteListResponse(
        items=invites,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


async def revoke_invite(invite_id: str, user_id: str) -> None:
    """
    Revoke (delete) a group invite. Only creator or admin can revoke.

    Args:
        invite_id: Invite ID.
        user_id: User ID revoking the invite.
    """
    db = get_database()

    if not ObjectId.is_valid(invite_id) or not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid invite or user ID",
        )

    invite_doc = await db.group_invites.find_one({"_id": ObjectId(invite_id)})
    if not invite_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite not found",
        )

    # Check if user is creator or admin of the group
    group_doc = await db.groups.find_one({"_id": invite_doc["group_id"]})
    if not group_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    is_creator = str(group_doc["creator_id"]) == user_id
    is_admin = any(
        str(member["user_id"]) == user_id and member.get("role") == "admin"
        for member in group_doc.get("members", [])
    )

    if not (is_creator or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only group creator or admins can revoke invites",
        )

    await db.group_invites.delete_one({"_id": ObjectId(invite_id)})

