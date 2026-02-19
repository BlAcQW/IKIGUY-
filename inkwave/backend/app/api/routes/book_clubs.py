"""
Book Clubs API Routes.

Endpoints for creating and managing book clubs, memberships, invitations, and discussions.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import uuid
import secrets
import logging

from app.core.auth import verify_token
from app.core.database import Database
from app.services.email_notification_service import get_email_service
from app.models.book_club import (
    BookClub,
    BookClubInDB,
    ClubMember,
    ClubMemberInDB,
    ClubInvitation,
    ClubInvitationInDB,
    ClubDiscussion,
    ClubDiscussionInDB,
    ClubVisibility,
    MemberRole,
    MemberStatus,
    InvitationStatus,
    ClubSettings,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/book-clubs", tags=["book-clubs"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class CreateClubRequest(BaseModel):
    """Request to create a new book club."""
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    book_id: str
    visibility: ClubVisibility = ClubVisibility.PUBLIC
    settings: Optional[ClubSettings] = None


class UpdateClubRequest(BaseModel):
    """Request to update club details."""
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    visibility: Optional[ClubVisibility] = None
    settings: Optional[ClubSettings] = None
    archived: Optional[bool] = None


class SendInvitationRequest(BaseModel):
    """Request to send club invitation."""
    # Either user_id (for registered users) or email (for non-registered)
    user_id: Optional[str] = None
    email: Optional[str] = None
    message: Optional[str] = Field(None, max_length=500)


class CreateDiscussionRequest(BaseModel):
    """Request to create a discussion/comment."""
    content: str = Field(..., min_length=1, max_length=2000)
    chapter_reference: Optional[int] = None
    reply_to_discussion_id: Optional[str] = None


class UpdateDiscussionRequest(BaseModel):
    """Request to update a discussion."""
    content: str = Field(..., min_length=1, max_length=2000)


class AddReactionRequest(BaseModel):
    """Request to add a reaction to a discussion."""
    emoji: str = Field(..., min_length=1, max_length=10)


class UpdateMemberRoleRequest(BaseModel):
    """Request to update member role."""
    role: MemberRole


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


async def get_club_or_404(club_id: str) -> dict:
    """Get club by ID or raise 404."""
    db = await Database.get_db()
    club = await db.book_clubs.find_one({"club_id": club_id})
    if not club:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Club {club_id} not found"
        )
    return club


async def get_membership_or_404(club_id: str, user_id: str) -> dict:
    """Get membership or raise 404."""
    db = await Database.get_db()
    membership = await db.club_members.find_one({
        "club_id": club_id,
        "user_id": user_id,
        "status": MemberStatus.ACTIVE
    })
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership not found"
        )
    return membership


async def check_member_permission(
    club_id: str,
    user_id: str,
    required_roles: List[MemberRole]
) -> dict:
    """
    Check if user has required role in club.

    Args:
        club_id: Club ID
        user_id: User ID
        required_roles: List of allowed roles

    Returns:
        Membership document

    Raises:
        HTTPException: If user doesn't have permission
    """
    membership = await get_membership_or_404(club_id, user_id)

    if membership["role"] not in [role.value for role in required_roles]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    return membership


async def check_club_access(club_id: str, user_id: Optional[str]) -> dict:
    """
    Check if user can access club based on visibility.

    Returns club document if accessible.
    """
    club = await get_club_or_404(club_id)

    # Public clubs are accessible to all
    if club["visibility"] == ClubVisibility.PUBLIC:
        return club

    # Private/followers-only clubs require membership
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authentication required"
        )

    # Check if user is a member
    db = await Database.get_db()
    membership = await db.club_members.find_one({
        "club_id": club_id,
        "user_id": user_id,
        "status": MemberStatus.ACTIVE
    })

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Club is private"
        )

    return club


async def increment_club_stat(club_id: str, field: str, increment: int = 1):
    """Increment a club's denormalized stat counter."""
    db = await Database.get_db()
    await db.book_clubs.update_one(
        {"club_id": club_id},
        {
            "$inc": {field: increment},
            "$set": {"last_activity": datetime.utcnow()}
        }
    )


async def increment_discussion_stat(discussion_id: str, field: str, increment: int = 1):
    """Increment a discussion's denormalized stat counter."""
    db = await Database.get_db()
    await db.club_discussions.update_one(
        {"discussion_id": discussion_id},
        {"$inc": {field: increment}}
    )


# ============================================================================
# CLUB MANAGEMENT ENDPOINTS
# ============================================================================


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_club(
    request: CreateClubRequest,
    user_data: dict = Depends(verify_token)
):
    """
    Create a new book club.

    User becomes the club creator.
    """
    db = await Database.get_db()
    user_id = user_data["user_id"]

    # Get book details for denormalization
    book = await db.books.find_one({"book_id": request.book_id})
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book {request.book_id} not found"
        )

    # Create club
    club_id = str(uuid.uuid4())
    club = BookClub(
        club_id=club_id,
        name=request.name,
        description=request.description,
        book_id=request.book_id,
        book_title=book.get("title", "Unknown"),
        book_cover_url=book.get("cover_url"),
        creator_user_id=user_id,
        visibility=request.visibility,
        member_count=1,  # Creator is first member
        settings=request.settings or ClubSettings(),
    )

    # Insert club
    await db.book_clubs.insert_one(club.model_dump())

    # Add creator as first member
    membership_id = str(uuid.uuid4())
    membership = ClubMember(
        membership_id=membership_id,
        club_id=club_id,
        user_id=user_id,
        role=MemberRole.CREATOR,
        status=MemberStatus.ACTIVE,
    )
    await db.club_members.insert_one(membership.model_dump())

    return {"club_id": club_id, "message": "Club created successfully"}


@router.get("/{club_id}")
async def get_club(
    club_id: str,
    user_data: Optional[dict] = Depends(verify_token)
):
    """Get club details."""
    user_id = user_data["user_id"] if user_data else None
    club = await check_club_access(club_id, user_id)

    # Check if current user is a member
    db = await Database.get_db()
    is_member = False
    user_role = None

    if user_id:
        membership = await db.club_members.find_one({
            "club_id": club_id,
            "user_id": user_id,
            "status": MemberStatus.ACTIVE
        })
        if membership:
            is_member = True
            user_role = membership["role"]

    return {
        **club,
        "is_member": is_member,
        "user_role": user_role,
    }


@router.put("/{club_id}")
async def update_club(
    club_id: str,
    request: UpdateClubRequest,
    user_data: dict = Depends(verify_token)
):
    """Update club details (creator/moderator only)."""
    user_id = user_data["user_id"]

    # Check permissions
    await check_member_permission(
        club_id,
        user_id,
        [MemberRole.CREATOR, MemberRole.MODERATOR]
    )

    # Build update document
    update_fields = {}
    if request.name is not None:
        update_fields["name"] = request.name
    if request.description is not None:
        update_fields["description"] = request.description
    if request.visibility is not None:
        update_fields["visibility"] = request.visibility
    if request.settings is not None:
        update_fields["settings"] = request.settings.model_dump()
    if request.archived is not None:
        update_fields["archived"] = request.archived

    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )

    # Update club
    db = await Database.get_db()
    result = await db.book_clubs.update_one(
        {"club_id": club_id},
        {"$set": update_fields}
    )

    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No changes made"
        )

    return {"message": "Club updated successfully"}


@router.delete("/{club_id}")
async def delete_club(
    club_id: str,
    user_data: dict = Depends(verify_token)
):
    """Delete club (creator only). Archives instead of hard delete."""
    user_id = user_data["user_id"]

    # Only creator can delete
    await check_member_permission(club_id, user_id, [MemberRole.CREATOR])

    # Archive club
    db = await Database.get_db()
    await db.book_clubs.update_one(
        {"club_id": club_id},
        {"$set": {"archived": True}}
    )

    return {"message": "Club archived successfully"}


@router.get("/")
async def list_clubs(
    book_id: Optional[str] = None,
    visibility: Optional[ClubVisibility] = None,
    limit: int = 50,
    skip: int = 0,
    user_data: Optional[dict] = Depends(verify_token)
):
    """
    List book clubs with optional filters.

    Query params:
        - book_id: Filter by book
        - visibility: Filter by visibility
        - limit: Max results (default 50)
        - skip: Pagination offset
    """
    db = await Database.get_db()

    # Build query
    query = {"archived": False}
    if book_id:
        query["book_id"] = book_id
    if visibility:
        query["visibility"] = visibility

    # Fetch clubs
    cursor = db.book_clubs.find(query).skip(skip).limit(limit).sort("created_at", -1)
    clubs = await cursor.to_list(length=limit)

    # If user is authenticated, add membership status
    if user_data:
        user_id = user_data["user_id"]
        for club in clubs:
            membership = await db.club_members.find_one({
                "club_id": club["club_id"],
                "user_id": user_id,
                "status": MemberStatus.ACTIVE
            })
            club["is_member"] = bool(membership)
            club["user_role"] = membership["role"] if membership else None
    else:
        for club in clubs:
            club["is_member"] = False
            club["user_role"] = None

    total = await db.book_clubs.count_documents(query)

    return {
        "clubs": clubs,
        "total": total,
        "limit": limit,
        "skip": skip,
    }


# ============================================================================
# MEMBERSHIP ENDPOINTS
# ============================================================================


@router.post("/{club_id}/join")
async def join_club(
    club_id: str,
    user_data: dict = Depends(verify_token)
):
    """Join a book club."""
    user_id = user_data["user_id"]
    db = await Database.get_db()

    # Check if club exists and is accessible
    club = await get_club_or_404(club_id)

    # Check if already a member
    existing = await db.club_members.find_one({
        "club_id": club_id,
        "user_id": user_id,
        "status": MemberStatus.ACTIVE
    })
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already a member"
        )

    # Check if approval is required
    if club["settings"]["require_approval"]:
        # Create pending membership
        membership_id = str(uuid.uuid4())
        membership = ClubMember(
            membership_id=membership_id,
            club_id=club_id,
            user_id=user_id,
            role=MemberRole.MEMBER,
            status=MemberStatus.PENDING,
        )
        await db.club_members.insert_one(membership.model_dump())
        return {"message": "Join request sent, awaiting approval"}

    # Auto-join
    membership_id = str(uuid.uuid4())
    membership = ClubMember(
        membership_id=membership_id,
        club_id=club_id,
        user_id=user_id,
        role=MemberRole.MEMBER,
        status=MemberStatus.ACTIVE,
    )
    await db.club_members.insert_one(membership.model_dump())

    # Increment member count
    await increment_club_stat(club_id, "member_count", 1)

    return {"message": "Joined club successfully"}


@router.post("/{club_id}/leave")
async def leave_club(
    club_id: str,
    user_data: dict = Depends(verify_token)
):
    """Leave a book club."""
    user_id = user_data["user_id"]
    db = await Database.get_db()

    # Get membership
    membership = await get_membership_or_404(club_id, user_id)

    # Creator cannot leave (must transfer ownership first)
    if membership["role"] == MemberRole.CREATOR:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Creator cannot leave club. Transfer ownership first."
        )

    # Update membership status
    await db.club_members.update_one(
        {"membership_id": membership["membership_id"]},
        {"$set": {"status": MemberStatus.LEFT}}
    )

    # Decrement member count
    await increment_club_stat(club_id, "member_count", -1)

    return {"message": "Left club successfully"}


@router.get("/{club_id}/members")
async def list_members(
    club_id: str,
    limit: int = 100,
    skip: int = 0,
    user_data: Optional[dict] = Depends(verify_token)
):
    """List club members."""
    user_id = user_data["user_id"] if user_data else None

    # Check club access
    await check_club_access(club_id, user_id)

    db = await Database.get_db()

    # Fetch members
    cursor = db.club_members.find({
        "club_id": club_id,
        "status": MemberStatus.ACTIVE
    }).skip(skip).limit(limit).sort("joined_at", 1)

    members = await cursor.to_list(length=limit)

    # Enrich with user data
    for member in members:
        user = await db.users.find_one({"user_id": member["user_id"]})
        if user:
            member["display_name"] = user.get("display_name")
            member["avatar_url"] = user.get("avatar_url")
            member["username"] = user.get("username")

    total = await db.club_members.count_documents({
        "club_id": club_id,
        "status": MemberStatus.ACTIVE
    })

    return {
        "members": members,
        "total": total,
        "limit": limit,
        "skip": skip,
    }


@router.delete("/{club_id}/members/{member_user_id}")
async def remove_member(
    club_id: str,
    member_user_id: str,
    user_data: dict = Depends(verify_token)
):
    """Remove a member from club (moderator/creator only)."""
    user_id = user_data["user_id"]

    # Check permissions
    await check_member_permission(
        club_id,
        user_id,
        [MemberRole.CREATOR, MemberRole.MODERATOR]
    )

    # Cannot remove creator
    db = await Database.get_db()
    target_membership = await db.club_members.find_one({
        "club_id": club_id,
        "user_id": member_user_id,
        "status": MemberStatus.ACTIVE
    })

    if not target_membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )

    if target_membership["role"] == MemberRole.CREATOR:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove club creator"
        )

    # Update membership
    await db.club_members.update_one(
        {"membership_id": target_membership["membership_id"]},
        {"$set": {"status": MemberStatus.REMOVED}}
    )

    # Decrement member count
    await increment_club_stat(club_id, "member_count", -1)

    return {"message": "Member removed successfully"}


@router.put("/{club_id}/members/{member_user_id}/role")
async def update_member_role(
    club_id: str,
    member_user_id: str,
    request: UpdateMemberRoleRequest,
    user_data: dict = Depends(verify_token)
):
    """Update member role (creator only)."""
    user_id = user_data["user_id"]

    # Only creator can update roles
    await check_member_permission(club_id, user_id, [MemberRole.CREATOR])

    # Cannot change creator role
    if request.role == MemberRole.CREATOR:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use transfer ownership endpoint to change creator"
        )

    # Update role
    db = await Database.get_db()
    result = await db.club_members.update_one(
        {
            "club_id": club_id,
            "user_id": member_user_id,
            "status": MemberStatus.ACTIVE
        },
        {"$set": {"role": request.role}}
    )

    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found or no change made"
        )

    return {"message": "Role updated successfully"}


# ============================================================================
# INVITATION ENDPOINTS
# ============================================================================


@router.post("/{club_id}/invitations")
async def send_invitation(
    club_id: str,
    request: SendInvitationRequest,
    user_data: dict = Depends(verify_token)
):
    """
    Send club invitation to a user or email.

    Either user_id (for registered users) or email (for non-registered) must be provided.
    """
    user_id = user_data["user_id"]
    db = await Database.get_db()

    # Check permissions
    club = await get_club_or_404(club_id)
    membership = await get_membership_or_404(club_id, user_id)

    # Check if member can invite
    if not club["settings"]["allow_member_invites"]:
        # Only moderators/creator can invite
        if membership["role"] == MemberRole.MEMBER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only moderators can send invitations"
            )

    # Validate request
    if not request.user_id and not request.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either user_id or email must be provided"
        )

    if request.user_id and request.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide either user_id or email, not both"
        )

    # Check if user is already a member (for user_id invitations)
    if request.user_id:
        existing = await db.club_members.find_one({
            "club_id": club_id,
            "user_id": request.user_id,
            "status": MemberStatus.ACTIVE
        })
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member"
            )

    # Check for existing pending invitation
    query = {"club_id": club_id, "status": InvitationStatus.PENDING}
    if request.user_id:
        query["invited_user_id"] = request.user_id
    else:
        query["invited_email"] = request.email

    existing_invitation = await db.club_invitations.find_one(query)
    if existing_invitation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation already sent"
        )

    # Create invitation
    invitation_id = str(uuid.uuid4())
    invitation_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=7)

    invitation = ClubInvitation(
        invitation_id=invitation_id,
        club_id=club_id,
        invited_by_user_id=user_id,
        invited_user_id=request.user_id,
        invited_email=request.email,
        invitation_token=invitation_token,
        status=InvitationStatus.PENDING,
        message=request.message,
        expires_at=expires_at,
    )

    await db.club_invitations.insert_one(invitation.model_dump(exclude_none=True))

    # Send email notification for email invitations
    if request.email:
        try:
            # Get inviter details
            inviter = await db.users.find_one({"user_id": user_id})
            inviter_name = inviter.get("display_name") or inviter.get("email", "A user")

            # Get email service
            email_service = get_email_service()

            # Send invitation email
            await email_service.send_club_invitation(
                to_email=request.email,
                recipient_name=None,  # We don't know their name yet
                inviter_name=inviter_name,
                club_name=club["name"],
                book_title=club["book_title"],
                club_description=club.get("description"),
                invitation_token=invitation_token,
                invitation_message=request.message,
            )
        except Exception as e:
            # Log error but don't fail the invitation creation
            logger.error(f"Failed to send invitation email: {e}")

    return {
        "invitation_id": invitation_id,
        "message": "Invitation sent successfully",
    }


@router.get("/{club_id}/invitations")
async def list_invitations(
    club_id: str,
    limit: int = 50,
    skip: int = 0,
    user_data: dict = Depends(verify_token)
):
    """List club invitations (moderator/creator only)."""
    user_id = user_data["user_id"]

    # Check permissions
    await check_member_permission(
        club_id,
        user_id,
        [MemberRole.CREATOR, MemberRole.MODERATOR]
    )

    db = await Database.get_db()

    # Fetch invitations
    cursor = db.club_invitations.find({
        "club_id": club_id
    }).skip(skip).limit(limit).sort("created_at", -1)

    invitations = await cursor.to_list(length=limit)

    # Enrich with inviter data
    for invitation in invitations:
        inviter = await db.users.find_one({"user_id": invitation["invited_by_user_id"]})
        if inviter:
            invitation["inviter_name"] = inviter.get("display_name")

        # If invited_user_id, get user data
        if invitation.get("invited_user_id"):
            invited_user = await db.users.find_one({"user_id": invitation["invited_user_id"]})
            if invited_user:
                invitation["invited_user_name"] = invited_user.get("display_name")

    total = await db.club_invitations.count_documents({"club_id": club_id})

    return {
        "invitations": invitations,
        "total": total,
        "limit": limit,
        "skip": skip,
    }


@router.delete("/{club_id}/invitations/{invitation_id}")
async def cancel_invitation(
    club_id: str,
    invitation_id: str,
    user_data: dict = Depends(verify_token)
):
    """Cancel an invitation (sender or moderator/creator only)."""
    user_id = user_data["user_id"]
    db = await Database.get_db()

    # Get invitation
    invitation = await db.club_invitations.find_one({
        "invitation_id": invitation_id,
        "club_id": club_id
    })

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )

    # Check permissions - must be sender or moderator/creator
    if invitation["invited_by_user_id"] != user_id:
        await check_member_permission(
            club_id,
            user_id,
            [MemberRole.CREATOR, MemberRole.MODERATOR]
        )

    # Update invitation status
    await db.club_invitations.update_one(
        {"invitation_id": invitation_id},
        {"$set": {"status": InvitationStatus.EXPIRED}}
    )

    return {"message": "Invitation cancelled successfully"}


@router.post("/invitations/{invitation_id}/accept")
async def accept_invitation(
    invitation_id: str,
    user_data: dict = Depends(verify_token)
):
    """Accept a club invitation."""
    user_id = user_data["user_id"]
    db = await Database.get_db()

    # Get invitation
    invitation = await db.club_invitations.find_one({
        "invitation_id": invitation_id,
        "status": InvitationStatus.PENDING
    })

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found or expired"
        )

    # Check if expired
    if invitation["expires_at"] < datetime.utcnow():
        await db.club_invitations.update_one(
            {"invitation_id": invitation_id},
            {"$set": {"status": InvitationStatus.EXPIRED}}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation has expired"
        )

    # Verify user is the invited user
    if invitation.get("invited_user_id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This invitation is not for you"
        )

    club_id = invitation["club_id"]

    # Check if already a member
    existing = await db.club_members.find_one({
        "club_id": club_id,
        "user_id": user_id,
        "status": MemberStatus.ACTIVE
    })
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already a member"
        )

    # Create membership
    membership_id = str(uuid.uuid4())
    membership = ClubMember(
        membership_id=membership_id,
        club_id=club_id,
        user_id=user_id,
        role=MemberRole.MEMBER,
        status=MemberStatus.ACTIVE,
        invited_by=invitation["invited_by_user_id"],
    )
    await db.club_members.insert_one(membership.model_dump())

    # Update invitation status
    await db.club_invitations.update_one(
        {"invitation_id": invitation_id},
        {
            "$set": {
                "status": InvitationStatus.ACCEPTED,
                "accepted_at": datetime.utcnow()
            }
        }
    )

    # Increment member count
    await increment_club_stat(club_id, "member_count", 1)

    return {"message": "Invitation accepted, you are now a member"}


@router.post("/invitations/{invitation_id}/decline")
async def decline_invitation(
    invitation_id: str,
    user_data: dict = Depends(verify_token)
):
    """Decline a club invitation."""
    user_id = user_data["user_id"]
    db = await Database.get_db()

    # Get invitation
    invitation = await db.club_invitations.find_one({
        "invitation_id": invitation_id,
        "status": InvitationStatus.PENDING
    })

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found or already processed"
        )

    # Verify user is the invited user
    if invitation.get("invited_user_id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This invitation is not for you"
        )

    # Update invitation status
    await db.club_invitations.update_one(
        {"invitation_id": invitation_id},
        {"$set": {"status": InvitationStatus.DECLINED}}
    )

    return {"message": "Invitation declined"}


@router.get("/invitations/token/{token}")
async def get_invitation_by_token(token: str):
    """
    Get invitation details by token (for email invitation links).

    Public endpoint - no authentication required.
    """
    db = await Database.get_db()

    invitation = await db.club_invitations.find_one({
        "invitation_token": token,
        "status": InvitationStatus.PENDING
    })

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found or expired"
        )

    # Check if expired
    if invitation["expires_at"] < datetime.utcnow():
        await db.club_invitations.update_one(
            {"invitation_id": invitation["invitation_id"]},
            {"$set": {"status": InvitationStatus.EXPIRED}}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation has expired"
        )

    # Get club details
    club = await db.book_clubs.find_one({"club_id": invitation["club_id"]})

    # Get inviter details
    inviter = await db.users.find_one({"user_id": invitation["invited_by_user_id"]})

    return {
        "invitation": invitation,
        "club": {
            "club_id": club["club_id"],
            "name": club["name"],
            "description": club.get("description"),
            "book_title": club["book_title"],
            "book_cover_url": club.get("book_cover_url"),
            "member_count": club["member_count"],
        },
        "inviter": {
            "display_name": inviter.get("display_name"),
            "avatar_url": inviter.get("avatar_url"),
        } if inviter else None,
    }


# ============================================================================
# DISCUSSION ENDPOINTS
# ============================================================================


@router.post("/{club_id}/discussions", status_code=status.HTTP_201_CREATED)
async def create_discussion(
    club_id: str,
    request: CreateDiscussionRequest,
    user_data: dict = Depends(verify_token)
):
    """Create a discussion/comment in the club."""
    user_id = user_data["user_id"]
    db = await Database.get_db()

    # Check membership and club settings
    club = await get_club_or_404(club_id)
    await get_membership_or_404(club_id, user_id)

    if not club["settings"]["allow_comments"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Comments are disabled for this club"
        )

    # If replying, check parent exists
    if request.reply_to_discussion_id:
        parent = await db.club_discussions.find_one({
            "discussion_id": request.reply_to_discussion_id,
            "club_id": club_id
        })
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent discussion not found"
            )

    # Get user data for denormalization
    user = await db.users.find_one({"user_id": user_id})

    # Create discussion
    discussion_id = str(uuid.uuid4())
    discussion = ClubDiscussion(
        discussion_id=discussion_id,
        club_id=club_id,
        user_id=user_id,
        username=user.get("username", ""),
        user_avatar_url=user.get("avatar_url"),
        content=request.content,
        chapter_reference=request.chapter_reference,
        reply_to_discussion_id=request.reply_to_discussion_id,
    )

    await db.club_discussions.insert_one(discussion.model_dump(exclude_none=True))

    # Increment discussion count
    await increment_club_stat(club_id, "discussion_count", 1)

    # If reply, increment parent reply count
    if request.reply_to_discussion_id:
        await increment_discussion_stat(request.reply_to_discussion_id, "reply_count", 1)

    return {
        "discussion_id": discussion_id,
        "message": "Discussion created successfully"
    }


@router.get("/{club_id}/discussions")
async def list_discussions(
    club_id: str,
    chapter: Optional[int] = None,
    limit: int = 50,
    skip: int = 0,
    user_data: Optional[dict] = Depends(verify_token)
):
    """
    List discussions in a club.

    Query params:
        - chapter: Filter by chapter reference
        - limit: Max results (default 50)
        - skip: Pagination offset
    """
    user_id = user_data["user_id"] if user_data else None

    # Check club access
    await check_club_access(club_id, user_id)

    db = await Database.get_db()

    # Build query - only show top-level discussions (replies fetched separately)
    query = {
        "club_id": club_id,
        "reply_to_discussion_id": None,
        "deleted_at": None,
    }
    if chapter is not None:
        query["chapter_reference"] = chapter

    # Fetch discussions
    cursor = db.club_discussions.find(query).skip(skip).limit(limit).sort("created_at", -1)
    discussions = await cursor.to_list(length=limit)

    total = await db.club_discussions.count_documents(query)

    return {
        "discussions": discussions,
        "total": total,
        "limit": limit,
        "skip": skip,
    }


@router.get("/discussions/{discussion_id}/replies")
async def list_replies(
    discussion_id: str,
    limit: int = 50,
    skip: int = 0,
    user_data: Optional[dict] = Depends(verify_token)
):
    """List replies to a discussion."""
    db = await Database.get_db()

    # Get parent discussion
    parent = await db.club_discussions.find_one({"discussion_id": discussion_id})
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Discussion not found"
        )

    # Check club access
    user_id = user_data["user_id"] if user_data else None
    await check_club_access(parent["club_id"], user_id)

    # Fetch replies
    cursor = db.club_discussions.find({
        "reply_to_discussion_id": discussion_id,
        "deleted_at": None,
    }).skip(skip).limit(limit).sort("created_at", 1)

    replies = await cursor.to_list(length=limit)

    total = await db.club_discussions.count_documents({
        "reply_to_discussion_id": discussion_id,
        "deleted_at": None,
    })

    return {
        "replies": replies,
        "total": total,
        "limit": limit,
        "skip": skip,
    }


@router.put("/discussions/{discussion_id}")
async def update_discussion(
    discussion_id: str,
    request: UpdateDiscussionRequest,
    user_data: dict = Depends(verify_token)
):
    """Update a discussion (author only)."""
    user_id = user_data["user_id"]
    db = await Database.get_db()

    # Get discussion
    discussion = await db.club_discussions.find_one({"discussion_id": discussion_id})
    if not discussion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Discussion not found"
        )

    # Only author can edit
    if discussion["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own discussions"
        )

    # Update discussion
    await db.club_discussions.update_one(
        {"discussion_id": discussion_id},
        {
            "$set": {
                "content": request.content,
                "edited_at": datetime.utcnow()
            }
        }
    )

    return {"message": "Discussion updated successfully"}


@router.delete("/discussions/{discussion_id}")
async def delete_discussion(
    discussion_id: str,
    user_data: dict = Depends(verify_token)
):
    """Delete a discussion (author or moderator/creator)."""
    user_id = user_data["user_id"]
    db = await Database.get_db()

    # Get discussion
    discussion = await db.club_discussions.find_one({"discussion_id": discussion_id})
    if not discussion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Discussion not found"
        )

    club_id = discussion["club_id"]

    # Check permissions - author or moderator/creator
    if discussion["user_id"] != user_id:
        await check_member_permission(
            club_id,
            user_id,
            [MemberRole.CREATOR, MemberRole.MODERATOR]
        )

    # Soft delete
    await db.club_discussions.update_one(
        {"discussion_id": discussion_id},
        {"$set": {"deleted_at": datetime.utcnow()}}
    )

    # Decrement discussion count
    await increment_club_stat(club_id, "discussion_count", -1)

    # If reply, decrement parent reply count
    if discussion.get("reply_to_discussion_id"):
        await increment_discussion_stat(
            discussion["reply_to_discussion_id"],
            "reply_count",
            -1
        )

    return {"message": "Discussion deleted successfully"}


@router.post("/discussions/{discussion_id}/reactions")
async def add_reaction(
    discussion_id: str,
    request: AddReactionRequest,
    user_data: dict = Depends(verify_token)
):
    """Add or remove a reaction to a discussion."""
    user_id = user_data["user_id"]
    db = await Database.get_db()

    # Get discussion
    discussion = await db.club_discussions.find_one({"discussion_id": discussion_id})
    if not discussion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Discussion not found"
        )

    # Check membership
    await get_membership_or_404(discussion["club_id"], user_id)

    # Get current reactions
    reactions = discussion.get("reactions", {})
    emoji = request.emoji

    # Toggle reaction
    if emoji in reactions:
        user_list = reactions[emoji]
        if user_id in user_list:
            # Remove reaction
            user_list.remove(user_id)
            if not user_list:
                # Remove emoji key if no users left
                del reactions[emoji]
            action = "removed"
        else:
            # Add reaction
            user_list.append(user_id)
            action = "added"
    else:
        # Add new emoji with user
        reactions[emoji] = [user_id]
        action = "added"

    # Update discussion
    await db.club_discussions.update_one(
        {"discussion_id": discussion_id},
        {"$set": {"reactions": reactions}}
    )

    return {
        "message": f"Reaction {action} successfully",
        "action": action,
    }
