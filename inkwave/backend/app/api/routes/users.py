"""
User discovery API routes for search, profiles, and username management.

Endpoints:
- GET    /users/search                      - Search users by username/display name
- GET    /users/{user_id}/profile           - Get public profile
- GET    /users/{user_id}/currently-reading - Get currently reading books
- GET    /users/{user_id}/activity          - Get user's reading activity
- PUT    /users/username                    - Update username (30-day cooldown)
- GET    /users/username/check              - Check username availability
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, status, Header, Request, Query
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.services.user_discovery_service import get_user_discovery_service
from apps.shared.dependencies.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


# ============================================================================
# SCHEMAS
# ============================================================================

class UserSearchResponse(BaseModel):
    """User search response."""
    users: List[dict]
    total: int
    page: int
    per_page: int


class PublicProfileResponse(BaseModel):
    """Public profile response."""
    user_id: str
    username: Optional[str]
    display_name: Optional[str]
    avatar_url: Optional[str]
    bio: Optional[str]
    created_at: Optional[str]
    followers_count: Optional[int] = None
    following_count: Optional[int] = None
    listening_stats: Optional[dict] = None
    is_following: Optional[bool] = None
    is_follower: Optional[bool] = None


class UpdateUsernameRequest(BaseModel):
    """Update username request."""
    username: str = Field(..., min_length=3, max_length=30)


class UpdateUsernameResponse(BaseModel):
    """Update username response."""
    success: bool
    message: str
    username: str


class UsernameCheckResponse(BaseModel):
    """Username availability check response."""
    available: bool
    username: str


class CurrentlyReadingResponse(BaseModel):
    """Currently reading books response."""
    books: List[dict]


class ActivityResponse(BaseModel):
    """Reading activity response."""
    activities: List[dict]
    count: int


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/search", response_model=UserSearchResponse)
async def search_users(
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    request: Request = None,
    authorization: Optional[str] = Header(None)
):
    """
    Search for users by username or display name.

    Only returns users who:
    - Are discoverable by search
    - Have a username set
    - Are not blocked by/blocking viewer

    Args:
        q: Search query
        page: Page number
        per_page: Results per page
        request: FastAPI request object
        authorization: Optional auth token

    Returns:
        List of matching users
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
    discovery_service = get_user_discovery_service(db)

    users = await discovery_service.search_users(
        query=q,
        viewer_id=viewer_id,
        page=page,
        per_page=per_page
    )

    return UserSearchResponse(
        users=users,
        total=len(users),  # TODO: Get actual count from service
        page=page,
        per_page=per_page
    )


@router.get("/{user_id}/profile", response_model=PublicProfileResponse)
async def get_public_profile(
    user_id: str,
    request: Request = None,
    authorization: Optional[str] = Header(None)
):
    """
    Get public profile for a user.

    Respects privacy settings and blocking.

    Args:
        user_id: User ID to get profile for
        request: FastAPI request object
        authorization: Optional auth token

    Returns:
        Public profile

    Raises:
        HTTPException: If profile not accessible
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
    discovery_service = get_user_discovery_service(db)

    try:
        profile = await discovery_service.get_public_profile(user_id, viewer_id)
        return PublicProfileResponse(**profile)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get public profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get profile"
        )


@router.get("/{user_id}/currently-reading", response_model=CurrentlyReadingResponse)
async def get_currently_reading(
    user_id: str,
    request: Request = None,
    authorization: Optional[str] = Header(None)
):
    """
    Get books user is currently reading.

    Args:
        user_id: User ID to get books for
        request: FastAPI request object
        authorization: Optional auth token

    Returns:
        List of books with progress

    Raises:
        HTTPException: If not authorized
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
    discovery_service = get_user_discovery_service(db)

    try:
        books = await discovery_service.get_currently_reading(user_id, viewer_id)
        return CurrentlyReadingResponse(books=books)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get currently reading: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get currently reading books"
        )


@router.get("/{user_id}/activity", response_model=ActivityResponse)
async def get_user_activity(
    user_id: str,
    limit: int = Query(20, ge=1, le=100),
    request: Request = None,
    authorization: Optional[str] = Header(None)
):
    """
    Get user's reading activity.

    Args:
        user_id: User ID to get activity for
        limit: Number of activities to return
        request: FastAPI request object
        authorization: Optional auth token

    Returns:
        List of activities

    Raises:
        HTTPException: If not authorized
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
    discovery_service = get_user_discovery_service(db)

    try:
        activities = await discovery_service.get_reading_activity(
            user_id, viewer_id, limit
        )
        return ActivityResponse(
            activities=activities,
            count=len(activities)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get user activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user activity"
        )


@router.put("/username", response_model=UpdateUsernameResponse)
async def update_username(
    username_request: UpdateUsernameRequest,
    request: Request = None,
    authorization: Optional[str] = Header(None)
):
    """
    Update user's username.

    Enforces 30-day cooldown between changes.

    Args:
        username_request: New username
        request: FastAPI request object
        authorization: Auth token

    Returns:
        Update result

    Raises:
        HTTPException: If validation fails
    """
    # Get current user
    user = await get_current_user(request, authorization)
    user_id = user.get("id") or user.get("user_id")

    db = get_db()
    discovery_service = get_user_discovery_service(db)

    try:
        updated_user = await discovery_service.update_username(
            user_id, username_request.username
        )
        return UpdateUsernameResponse(
            success=True,
            message="Username updated successfully",
            username=updated_user["username"]
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to update username: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update username"
        )


@router.get("/username/check", response_model=UsernameCheckResponse)
async def check_username_availability(
    username: str = Query(..., min_length=3, max_length=30)
):
    """
    Check if username is available.

    Args:
        username: Username to check

    Returns:
        Availability status
    """
    db = get_db()
    discovery_service = get_user_discovery_service(db)

    try:
        # Validate format first
        await discovery_service.validate_username(username)

        # Check availability
        is_available = await discovery_service.is_username_available(username)

        return UsernameCheckResponse(
            available=is_available,
            username=username
        )
    except ValueError as e:
        # Format validation error
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to check username availability: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check username"
        )
