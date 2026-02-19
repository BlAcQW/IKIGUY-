"""
Engagement API routes for DevotionalFlow.
Handles likes, bookmarks, shares, and reading history.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import logging

from app.services.engagement_service import (
    like_devotional,
    bookmark_devotional,
    get_user_bookmarks,
    track_share,
    track_reading,
    get_reading_history,
    update_reading_streak,
)
from app.models.engagement import (
    ShareCreate,
    ShareResponse,
    BookmarkResponse,
    ReadingHistoryResponse,
    ReadingHistoryCreate,
)
from app.utils.auth import get_current_user
from app.models.user import TokenData

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== LIKES ====================


@router.post("/devotionals/{devotional_id}/like")
async def toggle_devotional_like(
    devotional_id: str,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Like or unlike a devotional.

    **Path Parameters:**
    - devotional_id: Devotional ID

    **Returns:**
    - is_liked: Whether user currently likes the devotional
    - likes_count: Total likes count

    **Auth Required:** Yes
    """
    logger.info(
        f"User {current_user.user_id} toggling like on devotional {devotional_id}"
    )

    result = await like_devotional(
        devotional_id=devotional_id, user_id=current_user.user_id
    )

    return result


# ==================== BOOKMARKS ====================


@router.post("/devotionals/{devotional_id}/bookmark")
async def toggle_devotional_bookmark(
    devotional_id: str,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Bookmark or unbookmark a devotional.

    **Path Parameters:**
    - devotional_id: Devotional ID

    **Returns:**
    - is_bookmarked: Whether devotional is currently bookmarked

    **Auth Required:** Yes
    """
    logger.info(
        f"User {current_user.user_id} toggling bookmark on devotional {devotional_id}"
    )

    result = await bookmark_devotional(
        devotional_id=devotional_id, user_id=current_user.user_id
    )

    return result


@router.get("/users/me/bookmarks", response_model=List[BookmarkResponse])
async def list_my_bookmarks(
    page: int = 1,
    page_size: int = 20,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Get current user's bookmarked devotionals.

    **Query Parameters:**
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20)

    **Returns:**
    - List of bookmarked devotionals with titles and excerpts

    **Auth Required:** Yes
    """
    logger.info(f"User {current_user.user_id} fetching bookmarks")

    bookmarks = await get_user_bookmarks(
        user_id=current_user.user_id, page=page, page_size=page_size
    )

    return bookmarks


# ==================== SHARES ====================


@router.post("/devotionals/{devotional_id}/share", response_model=ShareResponse)
async def share_devotional(
    devotional_id: str,
    share_data: ShareCreate,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Track a devotional share.

    **Path Parameters:**
    - devotional_id: Devotional ID

    **Request Body:**
    - platform: Share platform (whatsapp, facebook, twitter, instagram, copy_link)

    **Returns:**
    - Share record with platform and timestamp

    **Auth Required:** Yes

    **Note:**
    - This endpoint tracks shares for analytics
    - WhatsApp shares are particularly important for African market
    """
    logger.info(
        f"User {current_user.user_id} sharing devotional {devotional_id} on {share_data.platform}"
    )

    share = await track_share(
        devotional_id=devotional_id,
        user_id=current_user.user_id,
        platform=share_data.platform,
    )

    return share


# ==================== READING HISTORY ====================


@router.post("/devotionals/{devotional_id}/read", response_model=ReadingHistoryResponse)
async def record_reading(
    devotional_id: str,
    reading_data: ReadingHistoryCreate,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Track devotional reading.

    **Path Parameters:**
    - devotional_id: Devotional ID

    **Request Body:**
    - reading_progress: Reading progress percentage (0-100)
    - listening_progress: Audio listening progress percentage (0-100)
    - time_spent_seconds: Time spent reading in seconds

    **Returns:**
    - Reading history record with progress and time spent

    **Auth Required:** Yes

    **Note:**
    - This endpoint also updates the user's reading streak when progress >= 80%
    - Gamification points are awarded for completing devotionals
    """
    progress = reading_data.reading_progress
    time_spent = reading_data.time_spent_seconds

    logger.info(
        f"User {current_user.user_id} reading devotional {devotional_id} ({progress}% complete, {time_spent}s)"
    )

    # Track reading
    reading = await track_reading(
        devotional_id=devotional_id,
        user_id=current_user.user_id,
        progress=progress,
        time_spent=time_spent,
    )

    # Update reading streak if they completed the devotional
    if progress >= 100:
        await update_reading_streak(user_id=current_user.user_id)

    return reading


@router.get("/users/me/history", response_model=List[ReadingHistoryResponse])
async def get_my_reading_history(
    page: int = 1,
    page_size: int = 20,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Get current user's reading history.

    **Query Parameters:**
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20)

    **Returns:**
    - List of reading history records with progress and time spent

    **Auth Required:** Yes
    """
    logger.info(f"User {current_user.user_id} fetching reading history")

    history = await get_reading_history(
        user_id=current_user.user_id, page=page, page_size=page_size
    )

    return history
