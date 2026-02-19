"""
Engagement service for devotional interactions.
Handles likes, bookmarks, shares, and reading history.
"""

from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from fastapi import HTTPException, status

from app.db.mongodb import get_database
from app.models.engagement import (
    BookmarkResponse,
    ShareResponse,
    ReadingHistoryResponse,
)
from app.services import gamification_service


async def like_devotional(devotional_id: str, user_id: str) -> dict:
    """
    Like or unlike a devotional.

    Args:
        devotional_id (str): Devotional ID.
        user_id (str): User ID.

    Returns:
        dict: Like status with is_liked and likes_count.

    Raises:
        HTTPException: If devotional not found.
    """
    db = get_database()

    # Check if devotional exists
    devotional = await db.devotionals.find_one({"_id": ObjectId(devotional_id)})
    if not devotional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Devotional not found",
        )

    # Check if user already liked this devotional
    existing_like = await db.likes.find_one(
        {
            "target_id": ObjectId(devotional_id),
            "user_id": ObjectId(user_id),
            "target_type": "devotional"
        }
    )

    if existing_like:
        # Unlike: remove like
        await db.likes.delete_one({"_id": existing_like["_id"]})
        await db.devotionals.update_one(
            {"_id": ObjectId(devotional_id)}, {"$inc": {"likes_count": -1}}
        )

        # Get updated count
        updated_devotional = await db.devotionals.find_one(
            {"_id": ObjectId(devotional_id)}
        )

        return {
            "is_liked": False,
            "likes_count": updated_devotional.get("likes_count", 0),
        }
    else:
        # Like: create like
        await db.likes.insert_one(
            {
                "target_id": ObjectId(devotional_id),
                "target_type": "devotional",
                "user_id": ObjectId(user_id),
                "created_at": datetime.utcnow(),
            }
        )
        await db.devotionals.update_one(
            {"_id": ObjectId(devotional_id)}, {"$inc": {"likes_count": 1}}
        )

        # Get updated count
        updated_devotional = await db.devotionals.find_one(
            {"_id": ObjectId(devotional_id)}
        )

        # Award gamification points for liking
        await gamification_service.handle_like(user_id, devotional_id)

        return {
            "is_liked": True,
            "likes_count": updated_devotional.get("likes_count", 0),
        }


async def bookmark_devotional(devotional_id: str, user_id: str) -> dict:
    """
    Bookmark or unbookmark a devotional.

    Args:
        devotional_id (str): Devotional ID.
        user_id (str): User ID.

    Returns:
        dict: Bookmark status with is_bookmarked.

    Raises:
        HTTPException: If devotional not found.
    """
    db = get_database()

    # Check if devotional exists
    devotional = await db.devotionals.find_one({"_id": ObjectId(devotional_id)})
    if not devotional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Devotional not found",
        )

    # Check if user already bookmarked this devotional
    existing_bookmark = await db.bookmarks.find_one(
        {"devotional_id": ObjectId(devotional_id), "user_id": ObjectId(user_id)}
    )

    if existing_bookmark:
        # Remove bookmark
        await db.bookmarks.delete_one({"_id": existing_bookmark["_id"]})
        await db.devotionals.update_one(
            {"_id": ObjectId(devotional_id)}, {"$inc": {"bookmarks_count": -1}}
        )

        return {"is_bookmarked": False}
    else:
        # Add bookmark
        await db.bookmarks.insert_one(
            {
                "devotional_id": ObjectId(devotional_id),
                "user_id": ObjectId(user_id),
                "created_at": datetime.utcnow(),
            }
        )
        await db.devotionals.update_one(
            {"_id": ObjectId(devotional_id)}, {"$inc": {"bookmarks_count": 1}}
        )

        # Update gamification achievement progress for bookmarking
        await gamification_service.handle_bookmark(user_id, devotional_id)

        return {"is_bookmarked": True}


async def get_user_bookmarks(
    user_id: str,
    page: int = 1,
    page_size: int = 20,
) -> List[BookmarkResponse]:
    """
    Get user's bookmarked devotionals.

    Args:
        user_id (str): User ID.
        page (int): Page number.
        page_size (int): Items per page.

    Returns:
        List[BookmarkResponse]: List of bookmarked devotionals.
    """
    db = get_database()

    # Pagination
    skip = (page - 1) * page_size

    # Fetch bookmarks with devotional data
    cursor = (
        db.bookmarks.find({"user_id": ObjectId(user_id)})
        .sort("created_at", -1)
        .skip(skip)
        .limit(page_size)
    )

    bookmarks = []
    async for bookmark_doc in cursor:
        # Fetch devotional
        devotional = await db.devotionals.find_one(
            {"_id": bookmark_doc["devotional_id"]}
        )

        if devotional:
            # Calculate reading time
            reading_time = 5  # Default
            if devotional.get("content") and isinstance(devotional["content"], list):
                total_words = sum(
                    len(block.get("text", "").split())
                    for block in devotional["content"]
                    if isinstance(block, dict) and "text" in block
                )
                reading_time = max(1, total_words // 200)

            bookmarks.append(
                BookmarkResponse(
                    id=str(devotional["_id"]),
                    title=devotional.get("title", ""),
                    excerpt=devotional.get("excerpt", ""),
                    cover_image_url=devotional.get("cover_image_url"),
                    published_at=devotional.get("published_at", bookmark_doc["created_at"]),
                    reading_time_minutes=devotional.get("reading_time_minutes", reading_time),
                    categories=devotional.get("categories", []),
                    created_at=bookmark_doc["created_at"],
                )
            )

    return bookmarks


async def track_share(
    devotional_id: str,
    user_id: str,
    platform: str,
) -> ShareResponse:
    """
    Track a devotional share.

    Args:
        devotional_id (str): Devotional ID.
        user_id (str): User ID.
        platform (str): Share platform (whatsapp, facebook, twitter, instagram, link).

    Returns:
        ShareResponse: Share record.

    Raises:
        HTTPException: If devotional not found.
    """
    db = get_database()

    # Check if devotional exists
    devotional = await db.devotionals.find_one({"_id": ObjectId(devotional_id)})
    if not devotional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Devotional not found",
        )

    # Create share record
    share_doc = {
        "devotional_id": ObjectId(devotional_id),
        "user_id": ObjectId(user_id),
        "platform": platform,
        "created_at": datetime.utcnow(),
    }

    result = await db.shares.insert_one(share_doc)

    # Increment devotional shares count
    await db.devotionals.update_one(
        {"_id": ObjectId(devotional_id)}, {"$inc": {"shares_count": 1}}
    )

    # Award gamification points for sharing
    await gamification_service.handle_share(user_id, devotional_id, platform)

    return ShareResponse(
        id=str(result.inserted_id),
        devotional_id=devotional_id,
        platform=platform,
        created_at=share_doc["created_at"],
    )


async def track_reading(
    devotional_id: str,
    user_id: str,
    progress: float = 100.0,
    time_spent: int = 0,
) -> ReadingHistoryResponse:
    """
    Track devotional reading.

    Args:
        devotional_id (str): Devotional ID.
        user_id (str): User ID.
        progress (float): Reading progress percentage (0-100).
        time_spent (int): Time spent reading in seconds.

    Returns:
        ReadingHistoryResponse: Reading history record.

    Raises:
        HTTPException: If devotional not found.
    """
    db = get_database()

    # Check if devotional exists
    devotional = await db.devotionals.find_one({"_id": ObjectId(devotional_id)})
    if not devotional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Devotional not found",
        )

    # Check if user already has a reading record for this devotional
    existing_record = await db.reading_history.find_one(
        {"devotional_id": ObjectId(devotional_id), "user_id": ObjectId(user_id)}
    )

    if existing_record:
        # Update existing record
        await db.reading_history.update_one(
            {"_id": existing_record["_id"]},
            {
                "$set": {
                    "progress": max(existing_record.get("progress", 0), progress),
                    "time_spent": existing_record.get("time_spent", 0) + time_spent,
                    "last_read_at": datetime.utcnow(),
                }
            },
        )

        updated_record = await db.reading_history.find_one(
            {"_id": existing_record["_id"]}
        )

        return ReadingHistoryResponse(
            id=str(updated_record["_id"]),
            devotional_id=devotional_id,
            devotional_title=devotional.get("title", ""),
            progress=updated_record["progress"],
            time_spent=updated_record["time_spent"],
            last_read_at=updated_record["last_read_at"],
        )
    else:
        # Create new reading record
        reading_doc = {
            "devotional_id": ObjectId(devotional_id),
            "user_id": ObjectId(user_id),
            "progress": progress,
            "time_spent": time_spent,
            "first_read_at": datetime.utcnow(),
            "last_read_at": datetime.utcnow(),
        }

        result = await db.reading_history.insert_one(reading_doc)

        # Award gamification points/streak for reading (if completed >= 80%)
        if progress >= 80:
            await gamification_service.handle_devotional_read(
                user_id, devotional_id, datetime.utcnow()
            )

        return ReadingHistoryResponse(
            id=str(result.inserted_id),
            devotional_id=devotional_id,
            devotional_title=devotional.get("title", ""),
            progress=progress,
            time_spent=time_spent,
            last_read_at=reading_doc["last_read_at"],
        )


async def get_reading_history(
    user_id: str,
    page: int = 1,
    page_size: int = 20,
) -> List[ReadingHistoryResponse]:
    """
    Get user's reading history.

    Args:
        user_id (str): User ID.
        page (int): Page number.
        page_size (int): Items per page.

    Returns:
        List[ReadingHistoryResponse]: List of reading history records.
    """
    db = get_database()

    # Pagination
    skip = (page - 1) * page_size

    # Fetch reading history
    cursor = (
        db.reading_history.find({"user_id": ObjectId(user_id)})
        .sort("last_read_at", -1)
        .skip(skip)
        .limit(page_size)
    )

    history = []
    async for record in cursor:
        # Fetch devotional
        devotional = await db.devotionals.find_one({"_id": record["devotional_id"]})

        if devotional:
            history.append(
                ReadingHistoryResponse(
                    id=str(record["_id"]),
                    devotional_id=str(devotional["_id"]),
                    devotional_title=devotional.get("title", ""),
                    progress=record.get("progress", 0),
                    time_spent=record.get("time_spent", 0),
                    last_read_at=record["last_read_at"],
                )
            )

    return history


async def update_reading_streak(user_id: str) -> int:
    """
    Update user's reading streak.
    Called when a user reads a devotional.

    Args:
        user_id (str): User ID.

    Returns:
        int: Current streak count.
    """
    db = get_database()

    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return 0

    # Get today's date (midnight UTC)
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    # Check if user read yesterday
    last_streak_date = user.get("last_streak_date")

    if last_streak_date:
        # Calculate days difference
        days_diff = (today - last_streak_date).days

        if days_diff == 0:
            # Already read today, no change
            return user.get("reading_streak", 0)
        elif days_diff == 1:
            # Consecutive day, increment streak
            new_streak = user.get("reading_streak", 0) + 1
        else:
            # Streak broken, reset to 1
            new_streak = 1
    else:
        # First time, start streak
        new_streak = 1

    # Update user
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"reading_streak": new_streak, "last_streak_date": today}},
    )

    return new_streak
