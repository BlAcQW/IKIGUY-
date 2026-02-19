"""
Social API routes for follow/unfollow and blocking functionality.

Endpoints:
- POST   /social/follow/{user_id}           - Follow a user
- DELETE /social/follow/{user_id}           - Unfollow a user
- GET    /social/followers/{user_id}        - Get user's followers
- GET    /social/following/{user_id}        - Get user's following
- GET    /social/suggestions                - Get follow suggestions
- GET    /social/feed                       - Get activity feed from followed users
- POST   /social/block/{user_id}            - Block a user
- DELETE /social/unblock/{user_id}          - Unblock a user
- POST   /social/report/{user_id}           - Report a user
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, status, Header, Request, Query
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.services.social_service import get_social_service
from app.services.reading_activity_service import get_reading_activity_service
from app.models.social import ReportType
from apps.shared.dependencies.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/social", tags=["social"])


# ============================================================================
# SCHEMAS
# ============================================================================

class FollowResponse(BaseModel):
    """Follow action response."""
    success: bool
    message: str
    following_user_id: str


class UserListResponse(BaseModel):
    """User list response."""
    users: List[dict]
    total: int
    page: int
    per_page: int


class ReportUserRequest(BaseModel):
    """Report user request."""
    report_type: ReportType
    description: str = Field(..., max_length=1000)
    evidence_urls: List[str] = Field(default_factory=list)


class ReportUserResponse(BaseModel):
    """Report user response."""
    success: bool
    message: str
    report_id: str


class BlockResponse(BaseModel):
    """Block action response."""
    success: bool
    message: str


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/follow/{user_id}", response_model=FollowResponse)
async def follow_user(
    user_id: str,
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """
    Follow a user.

    Allows the current user to follow another user. Creates an asymmetric
    relationship (does not require mutual following).

    Args:
        user_id: User ID to follow
        request: FastAPI request object
        authorization: Auth token

    Returns:
        Follow result

    Raises:
        HTTPException: If validation fails
    """
    # Get current user
    user = await get_current_user(request, authorization)
    follower_id = user.get("id") or user.get("user_id")

    db = get_db()
    social_service = get_social_service(db)

    try:
        result = await social_service.follow_user(follower_id, user_id)
        return FollowResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to follow user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to follow user"
        )


@router.delete("/follow/{user_id}")
async def unfollow_user(
    user_id: str,
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """
    Unfollow a user.

    Args:
        user_id: User ID to unfollow
        request: FastAPI request object
        authorization: Auth token

    Returns:
        Success message
    """
    # Get current user
    user = await get_current_user(request, authorization)
    follower_id = user.get("id") or user.get("user_id")

    db = get_db()
    social_service = get_social_service(db)

    success = await social_service.unfollow_user(follower_id, user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not following this user"
        )

    return {"message": "Successfully unfollowed user"}


@router.get("/followers/{user_id}", response_model=UserListResponse)
async def get_followers(
    user_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    request: Request = None,
    authorization: Optional[str] = Header(None)
):
    """
    Get list of users following this user.

    Args:
        user_id: User ID to get followers for
        page: Page number
        per_page: Results per page
        request: FastAPI request object
        authorization: Optional auth token

    Returns:
        List of follower users
    """
    # Get viewer ID if authenticated
    viewer_id = None
    if authorization:
        try:
            user = await get_current_user(request, authorization)
            viewer_id = user.get("id") or user.get("user_id")
        except:
            pass  # Anonymous viewer

    db = get_db()
    social_service = get_social_service(db)

    # Check if viewer can see followers list
    target_user = await db.users.find_one({"user_id": user_id})
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    privacy = target_user.get("privacy_settings", {})
    if not privacy.get("show_followers_list", False):
        # Only owner can see
        if viewer_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This user has disabled followers list visibility"
            )

    users = await social_service.get_followers(user_id, page, per_page)

    # Count total followers
    total = target_user.get("social_stats", {}).get("followers_count", 0)

    return UserListResponse(
        users=users,
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/following/{user_id}", response_model=UserListResponse)
async def get_following(
    user_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    request: Request = None,
    authorization: Optional[str] = Header(None)
):
    """
    Get list of users this user is following.

    Args:
        user_id: User ID to get following for
        page: Page number
        per_page: Results per page
        request: FastAPI request object
        authorization: Optional auth token

    Returns:
        List of following users
    """
    # Get viewer ID if authenticated
    viewer_id = None
    if authorization:
        try:
            user = await get_current_user(request, authorization)
            viewer_id = user.get("id") or user.get("user_id")
        except:
            pass  # Anonymous viewer

    db = get_db()
    social_service = get_social_service(db)

    # Check if viewer can see following list
    target_user = await db.users.find_one({"user_id": user_id})
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    privacy = target_user.get("privacy_settings", {})
    if not privacy.get("show_following_list", False):
        # Only owner can see
        if viewer_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This user has disabled following list visibility"
            )

    users = await social_service.get_following(user_id, page, per_page)

    # Count total following
    total = target_user.get("social_stats", {}).get("following_count", 0)

    return UserListResponse(
        users=users,
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/suggestions")
async def get_follow_suggestions(
    limit: int = Query(10, ge=1, le=50),
    request: Request = None,
    authorization: Optional[str] = Header(None)
):
    """
    Get follow suggestions for the current user.

    Returns users with:
    - Most followers
    - Most listening hours
    - Not already following
    - Not blocked

    Args:
        limit: Number of suggestions
        request: FastAPI request object
        authorization: Auth token

    Returns:
        List of suggested users
    """
    # Get current user
    user = await get_current_user(request, authorization)
    user_id = user.get("id") or user.get("user_id")

    db = get_db()
    social_service = get_social_service(db)

    suggestions = await social_service.get_follow_suggestions(user_id, limit)

    return {"suggestions": suggestions}


@router.get("/feed")
async def get_following_feed(
    limit: int = Query(50, ge=1, le=100),
    request: Request = None,
    authorization: Optional[str] = Header(None)
):
    """
    Get activity feed from users the current user is following.

    Args:
        limit: Number of activities to return
        request: FastAPI request object
        authorization: Auth token

    Returns:
        List of reading activities
    """
    # Get current user
    user = await get_current_user(request, authorization)
    user_id = user.get("id") or user.get("user_id")

    db = get_db()
    activity_service = get_reading_activity_service(db)

    activities = await activity_service.get_following_feed(user_id, limit)

    return {"activities": activities, "count": len(activities)}


@router.post("/block/{user_id}", response_model=BlockResponse)
async def block_user(
    user_id: str,
    reason: Optional[str] = None,
    request: Request = None,
    authorization: Optional[str] = Header(None)
):
    """
    Block a user.

    Removes existing follow relationships in both directions.

    Args:
        user_id: User ID to block
        reason: Optional reason for blocking
        request: FastAPI request object
        authorization: Auth token

    Returns:
        Block result
    """
    # Get current user
    user = await get_current_user(request, authorization)
    blocker_id = user.get("id") or user.get("user_id")

    db = get_db()
    social_service = get_social_service(db)

    try:
        success = await social_service.block_user(blocker_id, user_id, reason)
        return BlockResponse(
            success=success,
            message="User blocked successfully"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to block user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to block user"
        )


@router.delete("/unblock/{user_id}")
async def unblock_user(
    user_id: str,
    request: Request = None,
    authorization: Optional[str] = Header(None)
):
    """
    Unblock a user.

    Args:
        user_id: User ID to unblock
        request: FastAPI request object
        authorization: Auth token

    Returns:
        Success message
    """
    # Get current user
    user = await get_current_user(request, authorization)
    blocker_id = user.get("id") or user.get("user_id")

    db = get_db()
    social_service = get_social_service(db)

    success = await social_service.unblock_user(blocker_id, user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not blocked"
        )

    return {"message": "User unblocked successfully"}


@router.post("/report/{user_id}", response_model=ReportUserResponse)
async def report_user(
    user_id: str,
    report_request: ReportUserRequest,
    request: Request = None,
    authorization: Optional[str] = Header(None)
):
    """
    Report a user for violations.

    Args:
        user_id: User ID to report
        report_request: Report details
        request: FastAPI request object
        authorization: Auth token

    Returns:
        Report result
    """
    # Get current user
    user = await get_current_user(request, authorization)
    reporter_id = user.get("id") or user.get("user_id")

    if reporter_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot report yourself"
        )

    db = get_db()

    # Create report
    from app.models.social import UserReport
    report = UserReport(
        reporter_user_id=reporter_id,
        reported_user_id=user_id,
        report_type=report_request.report_type,
        description=report_request.description,
        evidence_urls=report_request.evidence_urls
    )

    result = await db.user_reports.insert_one(report.dict())

    logger.info(
        f"User report created: {reporter_id} reported {user_id} "
        f"for {report_request.report_type}"
    )

    return ReportUserResponse(
        success=True,
        message="Report submitted successfully. Our team will review it.",
        report_id=report.report_id
    )
