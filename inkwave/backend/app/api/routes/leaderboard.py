"""
Leaderboard API routes for top listeners rankings.

Endpoints:
- GET    /leaderboard                       - Get top listeners
- GET    /leaderboard/rank                  - Get current user's rank
- GET    /leaderboard/my-history            - Get current user's listening history
- GET    /leaderboard/user/{user_id}/history - Get user's listening history (admin only)
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, status, Header, Request, Query
from pydantic import BaseModel

from app.core.database import get_db
from app.services.leaderboard_service import get_leaderboard_service
from apps.shared.dependencies.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


# ============================================================================
# SCHEMAS
# ============================================================================

class LeaderboardEntry(BaseModel):
    """Leaderboard entry."""
    rank: int
    user_id: str
    username: Optional[str]
    display_name: Optional[str]
    avatar_url: Optional[str]
    listening_hours: float
    display_mode: str


class LeaderboardResponse(BaseModel):
    """Leaderboard response."""
    entries: List[LeaderboardEntry]
    period: str
    total: int


class UserRankResponse(BaseModel):
    """User rank response."""
    rank: Optional[int]
    period: str
    on_leaderboard: bool


class LeaderboardSettingsResponse(BaseModel):
    """Leaderboard settings response."""
    appear_in_leaderboard: bool
    leaderboard_display_mode: str


class LeaderboardSettingsUpdate(BaseModel):
    """Leaderboard settings update request."""
    appear_in_leaderboard: Optional[bool] = None
    leaderboard_display_mode: Optional[str] = None


class BookListeningHistory(BaseModel):
    """Book listening history entry."""
    book_id: str
    book_title: str
    listening_minutes: float
    listening_hours: float
    session_count: int
    last_listened: Optional[str]


class UserListeningHistoryResponse(BaseModel):
    """User listening history response."""
    user_id: str
    email: str
    display_name: Optional[str]
    total_listening_hours: float
    total_books: int
    books: List[BookListeningHistory]


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("", response_model=LeaderboardResponse)
async def get_leaderboard(
    period: str = Query("week", regex="^(week|month|all_time)$"),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by username or display name")
):
    """
    Get top listeners leaderboard.

    Returns users who:
    - Opted into leaderboard
    - Have listening time in the period
    - Ordered by listening hours (descending)
    - Optionally filtered by search query

    Args:
        period: Time period (week, month, all_time)
        limit: Number of results to return
        search: Optional search query for username/display name

    Returns:
        Leaderboard entries
    """
    db = get_db()
    leaderboard_service = get_leaderboard_service(db)

    try:
        if search:
            # Search mode: get filtered leaderboard
            entries = await leaderboard_service.search_leaderboard(period, search, limit)
        else:
            # Normal mode: get top listeners
            entries = await leaderboard_service.get_top_listeners(period, limit)

        return LeaderboardResponse(
            entries=[LeaderboardEntry(**entry) for entry in entries],
            period=period,
            total=len(entries)
        )
    except Exception as e:
        logger.error(f"Failed to get leaderboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get leaderboard"
        )


@router.get("/rank", response_model=UserRankResponse)
async def get_my_rank(
    period: str = Query("week", regex="^(week|month|all_time)$"),
    request: Request = None,
    authorization: Optional[str] = Header(None)
):
    """
    Get current user's rank on the leaderboard.

    Args:
        period: Time period (week, month, all_time)
        request: FastAPI request object
        authorization: Auth token

    Returns:
        User's rank or None if not on leaderboard
    """
    # Get current user
    user = await get_current_user(request, authorization)
    user_id = user.get("id") or user.get("user_id")

    db = get_db()
    leaderboard_service = get_leaderboard_service(db)

    try:
        rank = await leaderboard_service.get_user_rank(user_id, period)

        return UserRankResponse(
            rank=rank,
            period=period,
            on_leaderboard=rank is not None
        )
    except Exception as e:
        logger.error(f"Failed to get user rank: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user rank"
        )


@router.get("/my-history", response_model=UserListeningHistoryResponse)
async def get_my_listening_history(
    request: Request = None,
    authorization: Optional[str] = Header(None)
):
    """
    Get current user's detailed listening history by book.

    Shows all books the user has listened to and time spent on each.

    Args:
        request: FastAPI request object
        authorization: Auth token

    Returns:
        User's detailed listening history by book
    """
    # Get current user
    user = await get_current_user(request, authorization)
    user_id = user.get("id") or user.get("user_id")

    db = get_db()

    try:
        # Get user document
        user_doc = await db.users.find_one({"user_id": user_id})
        if not user_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Aggregate listening time by book from transactions
        pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    "metadata.duration_minutes": {"$exists": True}
                }
            },
            {
                "$group": {
                    "_id": "$metadata.book_id",
                    "book_title": {"$first": "$metadata.book_title"},
                    "total_minutes": {"$sum": "$metadata.duration_minutes"},
                    "transaction_count": {"$sum": 1},
                    "last_listened": {"$max": "$created_at"}
                }
            },
            {
                "$sort": {"total_minutes": -1}
            }
        ]

        results = await db.wallet_transactions.aggregate(pipeline).to_list(length=None)

        # Format response
        books = []
        total_minutes = 0

        for result in results:
            minutes = float(result.get("total_minutes", 0))
            total_minutes += minutes

            books.append(BookListeningHistory(
                book_id=result.get("_id", "unknown"),
                book_title=result.get("book_title", "Unknown Book"),
                listening_minutes=round(minutes, 1),
                listening_hours=round(minutes / 60, 2),
                session_count=result.get("transaction_count", 0),
                last_listened=result.get("last_listened").isoformat() if result.get("last_listened") else None
            ))

        return UserListeningHistoryResponse(
            user_id=user_id,
            email=user_doc.get("email", ""),
            display_name=user_doc.get("display_name"),
            total_listening_hours=round(total_minutes / 60, 2),
            total_books=len(books),
            books=books
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user listening history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user listening history"
        )


@router.get("/settings", response_model=LeaderboardSettingsResponse)
async def get_leaderboard_settings(
    request: Request = None,
    authorization: Optional[str] = Header(None)
):
    """
    Get current user's leaderboard privacy settings.

    Args:
        request: FastAPI request object
        authorization: Auth token

    Returns:
        User's leaderboard settings
    """
    # Get current user
    user = await get_current_user(request, authorization)
    user_id = user.get("id") or user.get("user_id")

    db = get_db()

    try:
        # Get user document
        user_doc = await db.users.find_one({"user_id": user_id})

        if not user_doc:
            # Return default settings if user not found
            return LeaderboardSettingsResponse(
                appear_in_leaderboard=True,  # Default from PrivacySettings
                leaderboard_display_mode="anonymous"
            )

        # Get privacy settings
        privacy = user_doc.get("privacy_settings", {})

        return LeaderboardSettingsResponse(
            appear_in_leaderboard=privacy.get("appear_in_leaderboard", True),
            leaderboard_display_mode=privacy.get("leaderboard_display_mode", "anonymous")
        )

    except Exception as e:
        logger.error(f"Failed to get leaderboard settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get leaderboard settings"
        )


@router.put("/settings", response_model=LeaderboardSettingsResponse)
async def update_leaderboard_settings(
    settings: LeaderboardSettingsUpdate,
    request: Request = None,
    authorization: Optional[str] = Header(None)
):
    """
    Update current user's leaderboard privacy settings.

    Args:
        settings: Updated settings
        request: FastAPI request object
        authorization: Auth token

    Returns:
        Updated leaderboard settings
    """
    # Get current user
    user = await get_current_user(request, authorization)
    user_id = user.get("id") or user.get("user_id")

    # Validate display mode if provided
    valid_modes = ["opt_out", "anonymous", "full_profile"]
    if settings.leaderboard_display_mode and settings.leaderboard_display_mode not in valid_modes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid display mode. Must be one of: {', '.join(valid_modes)}"
        )

    db = get_db()

    try:
        # Build update document
        update_doc = {}
        if settings.appear_in_leaderboard is not None:
            update_doc["privacy_settings.appear_in_leaderboard"] = settings.appear_in_leaderboard
        if settings.leaderboard_display_mode is not None:
            update_doc["privacy_settings.leaderboard_display_mode"] = settings.leaderboard_display_mode

        if not update_doc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No settings provided to update"
            )

        # Update user document
        result = await db.users.find_one_and_update(
            {"user_id": user_id},
            {"$set": update_doc},
            return_document=True
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Get updated privacy settings
        privacy = result.get("privacy_settings", {})

        logger.info(f"Updated leaderboard settings for user {user_id}: {update_doc}")

        return LeaderboardSettingsResponse(
            appear_in_leaderboard=privacy.get("appear_in_leaderboard", True),
            leaderboard_display_mode=privacy.get("leaderboard_display_mode", "anonymous")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update leaderboard settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update leaderboard settings"
        )


@router.get("/user/{user_id}/history", response_model=UserListeningHistoryResponse)
async def get_user_listening_history(
    user_id: str,
    request: Request = None,
    authorization: Optional[str] = Header(None)
):
    """
    Get detailed listening history for a specific user (ADMIN ONLY).

    Shows all books the user has listened to and time spent on each.

    Args:
        user_id: Target user ID
        request: FastAPI request object
        authorization: Auth token

    Returns:
        User's detailed listening history by book
    """
    # Get current user and verify admin
    current_user = await get_current_user(request, authorization)
    current_user_id = current_user.get("id") or current_user.get("user_id")

    db = get_db()

    try:
        # Check if current user is admin
        current_user_doc = await db.users.find_one({"user_id": current_user_id})
        if not current_user_doc or not current_user_doc.get("is_admin", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )

        # Get target user
        target_user = await db.users.find_one({"user_id": user_id})
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Aggregate listening time by book from transactions
        pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    "metadata.duration_minutes": {"$exists": True}
                }
            },
            {
                "$group": {
                    "_id": "$metadata.book_id",
                    "book_title": {"$first": "$metadata.book_title"},
                    "total_minutes": {"$sum": "$metadata.duration_minutes"},
                    "transaction_count": {"$sum": 1},
                    "last_listened": {"$max": "$created_at"}
                }
            },
            {
                "$sort": {"total_minutes": -1}
            }
        ]

        results = await db.wallet_transactions.aggregate(pipeline).to_list(length=None)

        # Format response
        books = []
        total_minutes = 0

        for result in results:
            minutes = float(result.get("total_minutes", 0))
            total_minutes += minutes

            books.append(BookListeningHistory(
                book_id=result.get("_id", "unknown"),
                book_title=result.get("book_title", "Unknown Book"),
                listening_minutes=round(minutes, 1),
                listening_hours=round(minutes / 60, 2),
                session_count=result.get("transaction_count", 0),
                last_listened=result.get("last_listened").isoformat() if result.get("last_listened") else None
            ))

        return UserListeningHistoryResponse(
            user_id=user_id,
            email=target_user.get("email", ""),
            display_name=target_user.get("display_name"),
            total_listening_hours=round(total_minutes / 60, 2),
            total_books=len(books),
            books=books
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user listening history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user listening history"
        )
