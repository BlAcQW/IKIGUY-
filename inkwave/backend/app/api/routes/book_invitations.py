"""
Book Invitation API Routes.

Endpoints for managing book access invitation links:
- Admin: Create, list, revoke invitations
- Public: View invitation details, redeem after signup
"""

import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends, Query, Header, Request
from pydantic import BaseModel, Field
from datetime import datetime

from app.services.book_invitation_service import book_invitation_service
from app.core.config import settings
from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/book-invitations", tags=["book-invitations"])


# ============================================================================
# SCHEMAS
# ============================================================================

class CreateInvitationRequest(BaseModel):
    """Request to create a book invitation."""

    book_id: str = Field(..., description="Book ID to grant access to")
    max_uses: Optional[int] = Field(
        None,
        ge=1,
        description="Maximum uses (None = unlimited)"
    )
    expires_in_days: Optional[int] = Field(
        None,
        ge=1,
        le=365,
        description="Days until expiration (None = never)"
    )
    welcome_message: Optional[str] = Field(
        None,
        max_length=500,
        description="Custom welcome message for signup page"
    )


class InvitationResponse(BaseModel):
    """Invitation response."""

    invitation_id: str
    book_id: str
    book_title: str
    book_cover_url: Optional[str]
    invitation_url: str
    max_uses: Optional[int]
    used_count: int
    expires_at: Optional[datetime]
    status: str
    welcome_message: Optional[str]
    created_at: datetime
    created_by_email: Optional[str]


class InvitationListResponse(BaseModel):
    """List of invitations."""

    invitations: List[InvitationResponse]
    total: int
    page: int
    per_page: int


class InvitationPublicInfo(BaseModel):
    """Public invitation info (for signup page)."""

    valid: bool
    book_title: str
    book_cover_url: Optional[str]
    book_author: Optional[str]
    welcome_message: Optional[str]
    status: str
    error_message: Optional[str] = None


class RedeemResponse(BaseModel):
    """Redemption response."""

    success: bool
    book_id: str
    book_title: str
    book_cover_url: Optional[str]
    message: str


class LibraryBookResponse(BaseModel):
    """Library book response."""

    id: str
    title: str
    author: Optional[str]
    cover_url: Optional[str]
    description: Optional[str]
    access_type: str
    granted_at: Optional[datetime]
    processing_status: str


class UserLibraryResponse(BaseModel):
    """User library response."""

    books: List[LibraryBookResponse]
    total: int


# ============================================================================
# ADMIN ENDPOINTS (require admin auth)
# ============================================================================


@router.post("", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
async def create_invitation(
    request: CreateInvitationRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Create a new book invitation link (Admin only).

    Generates a unique URL that can be shared with users. When they
    register using this link, they automatically get access to the book.

    Args:
        request: Invitation details
        authorization: Admin auth token

    Returns:
        Created invitation with shareable URL
    """
    from app.core.auth import get_current_admin_user as auth_get_admin

    # Get admin user
    admin = await auth_get_admin(authorization)

    try:
        invitation = await book_invitation_service.create_invitation(
            book_id=request.book_id,
            created_by=admin.user_id,
            created_by_email=admin.email,
            max_uses=request.max_uses,
            expires_in_days=request.expires_in_days,
            welcome_message=request.welcome_message
        )

        # Build invitation URL
        frontend_url = getattr(settings, 'FRONTEND_URL', 'https://inkwave.ailabsafrica.com')
        long_invitation_url = f"{frontend_url}/signup?invite={invitation.invitation_id}"

        # Generate short URL for cleaner sharing
        invitation_url = long_invitation_url
        try:
            # Use shared URL shortening service
            from apps.shared.services.url_shortening_service import get_url_shortening_service

            db = get_db()
            service = get_url_shortening_service(db)

            result = await service.create_short_url(
                target_url=long_invitation_url,
                expires_at=invitation.expires_at,
                metadata={
                    "type": "invitation",
                    "invitation_id": invitation.invitation_id
                },
                app_name="inkwave"
            )

            # Update invitation with short_code for reference
            await db.book_invitations.update_one(
                {"invitation_id": invitation.invitation_id},
                {"$set": {"short_code": result["short_code"]}}
            )

            invitation_url = f"{frontend_url}/s/{result['short_code']}"
            logger.info(f"Created short URL {invitation_url} for invitation {invitation.invitation_id}")
        except Exception as e:
            logger.warning(f"Failed to create short URL for invitation: {e}")
            # Fallback to long URL if short URL creation fails
            invitation_url = long_invitation_url

        return InvitationResponse(
            invitation_id=invitation.invitation_id,
            book_id=invitation.book_id,
            book_title=invitation.book_title,
            book_cover_url=invitation.book_cover_url,
            invitation_url=invitation_url,
            max_uses=invitation.max_uses,
            used_count=invitation.used_count,
            expires_at=invitation.expires_at,
            status=invitation.get_status(),
            welcome_message=invitation.welcome_message,
            created_at=invitation.created_at,
            created_by_email=invitation.created_by_email
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create invitation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create invitation: {str(e)}"
        )


@router.get("", response_model=InvitationListResponse)
async def list_invitations(
    book_id: Optional[str] = Query(None, description="Filter by book ID"),
    include_inactive: bool = Query(False, description="Include revoked/expired"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    authorization: Optional[str] = Header(None)
):
    """
    List all book invitations (Admin only).

    Args:
        book_id: Optional book filter
        include_inactive: Include revoked invitations
        page: Page number
        per_page: Items per page
        authorization: Admin auth token

    Returns:
        List of invitations with pagination
    """
    from app.core.auth import get_current_admin_user as auth_get_admin

    admin = await auth_get_admin(authorization)

    try:
        invitations, total = await book_invitation_service.list_invitations(
            book_id=book_id,
            include_inactive=include_inactive,
            page=page,
            per_page=per_page
        )

        frontend_url = getattr(settings, 'FRONTEND_URL', 'https://inkwave.ailabsafrica.com')

        return InvitationListResponse(
            invitations=[
                InvitationResponse(
                    invitation_id=inv.invitation_id,
                    book_id=inv.book_id,
                    book_title=inv.book_title,
                    book_cover_url=inv.book_cover_url,
                    invitation_url=(
                        f"{frontend_url}/s/{inv.short_code}"
                        if hasattr(inv, 'short_code') and inv.short_code
                        else f"{frontend_url}/signup?invite={inv.invitation_id}"
                    ),
                    max_uses=inv.max_uses,
                    used_count=inv.used_count,
                    expires_at=inv.expires_at,
                    status=inv.get_status(),
                    welcome_message=inv.welcome_message,
                    created_at=inv.created_at,
                    created_by_email=inv.created_by_email
                )
                for inv in invitations
            ],
            total=total,
            page=page,
            per_page=per_page
        )

    except Exception as e:
        logger.error(f"Failed to list invitations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list invitations: {str(e)}"
        )


@router.delete("/{invitation_id}")
async def revoke_invitation(
    invitation_id: str,
    authorization: Optional[str] = Header(None)
):
    """
    Revoke a book invitation (Admin only).

    The link will no longer work for new registrations.

    Args:
        invitation_id: Invitation token to revoke
        authorization: Admin auth token

    Returns:
        Success message
    """
    from app.core.auth import get_current_admin_user as auth_get_admin

    admin = await auth_get_admin(authorization)

    revoked = await book_invitation_service.revoke_invitation(invitation_id)

    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )

    logger.info(f"Admin {admin.email} revoked invitation {invitation_id}")

    return {"message": "Invitation revoked successfully"}


@router.get("/stats")
async def get_invitation_stats(
    authorization: Optional[str] = Header(None)
):
    """
    Get invitation statistics (Admin only).

    Returns:
        Stats including total invitations, redemptions, top books
    """
    from app.core.auth import get_current_admin_user as auth_get_admin

    await auth_get_admin(authorization)

    stats = await book_invitation_service.get_invitation_stats()
    return stats


# ============================================================================
# PUBLIC ENDPOINTS (no auth required)
# ============================================================================

@router.get("/public/{invitation_id}", response_model=InvitationPublicInfo)
async def get_invitation_public_info(invitation_id: str):
    """
    Get public info about an invitation (for signup page).

    This endpoint is public - it allows the signup page to display
    book information before the user registers.

    Args:
        invitation_id: Invitation token from URL

    Returns:
        Book info and invitation validity
    """
    from app.core.database import get_db

    invitation = await book_invitation_service.get_invitation(invitation_id)

    if not invitation:
        return InvitationPublicInfo(
            valid=False,
            book_title="",
            book_cover_url=None,
            book_author=None,
            welcome_message=None,
            status="not_found",
            error_message="This invitation link is not valid"
        )

    # Get additional book info
    db = get_db()
    book = await db.books.find_one({"book_id": invitation.book_id})
    book_author = book.get("author") if book else None

    if not invitation.is_valid():
        status_str = invitation.get_status()
        error_messages = {
            "expired": "This invitation has expired",
            "exhausted": "This invitation has reached its usage limit",
            "revoked": "This invitation has been revoked"
        }
        return InvitationPublicInfo(
            valid=False,
            book_title=invitation.book_title,
            book_cover_url=invitation.book_cover_url,
            book_author=book_author,
            welcome_message=invitation.welcome_message,
            status=status_str,
            error_message=error_messages.get(status_str, "This invitation is no longer valid")
        )

    return InvitationPublicInfo(
        valid=True,
        book_title=invitation.book_title,
        book_cover_url=invitation.book_cover_url,
        book_author=book_author,
        welcome_message=invitation.welcome_message,
        status="active"
    )


# ============================================================================
# AUTHENTICATED ENDPOINTS (require user auth)
# ============================================================================

@router.post("/{invitation_id}/redeem", response_model=RedeemResponse)
async def redeem_invitation(
    invitation_id: str,
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """
    Redeem a book invitation (Authenticated user).

    Adds the book to the user's library after they've registered.

    Args:
        invitation_id: Invitation token
        request: FastAPI request object
        authorization: User auth token

    Returns:
        Redemption result with book info
    """
    from apps.shared.dependencies.auth import get_current_user

    user = await get_current_user(request, authorization)
    user_id = user.get("id") or user.get("user_id")
    user_email = user.get("email", "unknown")

    try:
        result = await book_invitation_service.redeem_invitation(
            invitation_id=invitation_id,
            user_id=user_id,
            user_email=user_email
        )

        return RedeemResponse(
            success=result["success"],
            book_id=result["book_id"],
            book_title=result["book_title"],
            book_cover_url=result.get("book_cover_url"),
            message=result["message"]
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to redeem invitation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to redeem invitation: {str(e)}"
        )


@router.get("/my-library", response_model=UserLibraryResponse)
async def get_my_library(
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """
    Get current user's library (books they have access to).

    Args:
        request: FastAPI request object
        authorization: User auth token

    Returns:
        List of books in user's library
    """
    from apps.shared.dependencies.auth import get_current_user

    user = await get_current_user(request, authorization)
    user_id = user.get("id") or user.get("user_id")

    try:
        books = await book_invitation_service.get_user_library(user_id)

        return UserLibraryResponse(
            books=[
                LibraryBookResponse(
                    id=b["id"],
                    title=b["title"],
                    author=b.get("author"),
                    cover_url=b.get("cover_url"),
                    description=b.get("description"),
                    access_type=b.get("access_type", "invitation"),
                    granted_at=b.get("granted_at"),
                    processing_status=b.get("processing_status", "ready")
                )
                for b in books
            ],
            total=len(books)
        )

    except Exception as e:
        logger.error(f"Failed to get library: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get library: {str(e)}"
        )
