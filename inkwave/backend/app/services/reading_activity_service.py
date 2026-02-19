"""
Reading activity service for social activity feeds.

Handles:
- Create reading activities (started, completed, milestones)
- Get user activity timeline
- Get following feed (activity from followed users)
- Respect privacy settings
- Auto-create from reading session updates
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.social import ReadingActivity, ActivityType, ActivityVisibility

logger = logging.getLogger(__name__)


class ReadingActivityService:
    """Service for managing reading activities."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize reading activity service.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.activity_collection = db.reading_activity
        self.users_collection = db.users
        self.follows_collection = db.user_follows
        self.books_collection = db.books
        self.sessions_collection = db.reading_sessions

    async def create_activity(
        self,
        user_id: str,
        activity_type: str,
        book_id: str,
        progress_percentage: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a reading activity.

        Args:
            user_id: User ID
            activity_type: Type of activity (started_book, completed_book, milestone_reached)
            book_id: Book ID
            progress_percentage: Optional progress percentage for milestones

        Returns:
            Created activity or None if user disabled activity sharing
        """
        # Get user
        user = await self.users_collection.find_one({"user_id": user_id})
        if not user:
            logger.warning(f"User {user_id} not found for activity creation")
            return None

        # Check if user wants to share activity
        privacy = user.get("privacy_settings", {})
        if activity_type == "started_book" and not privacy.get("show_currently_reading", False):
            return None
        if activity_type in ["completed_book", "milestone_reached"] and not privacy.get("show_reading_history", False):
            return None

        # Get book details
        book = await self.books_collection.find_one({"book_id": book_id})
        if not book:
            logger.warning(f"Book {book_id} not found for activity creation")
            return None

        # Determine visibility based on profile visibility
        profile_visibility = privacy.get("profile_visibility", "followers_only")
        if profile_visibility == "public":
            visibility = ActivityVisibility.PUBLIC
        elif profile_visibility == "followers_only":
            visibility = ActivityVisibility.FOLLOWERS_ONLY
        else:  # private
            visibility = ActivityVisibility.PRIVATE

        # Check for duplicate recent activity (within last hour)
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        existing = await self.activity_collection.find_one({
            "user_id": user_id,
            "book_id": book_id,
            "activity_type": activity_type,
            "created_at": {"$gte": one_hour_ago}
        })

        if existing:
            logger.debug(f"Duplicate activity detected for {user_id}/{book_id}/{activity_type}")
            return existing

        # Create activity
        activity = ReadingActivity(
            user_id=user_id,
            activity_type=ActivityType(activity_type),
            book_id=book_id,
            book_title=book.get("title", "Unknown"),
            book_cover_url=book.get("cover_url"),
            book_author=book.get("author"),
            progress_percentage=progress_percentage,
            visibility=visibility
        )

        result = await self.activity_collection.insert_one(activity.dict())
        activity_dict = activity.dict()
        activity_dict["_id"] = result.inserted_id

        logger.info(
            f"Created activity: {user_id} {activity_type} {book.get('title')} "
            f"({visibility})"
        )

        return activity_dict

    async def get_user_activity(
        self,
        user_id: str,
        viewer_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get user's reading activity timeline.

        Args:
            user_id: User ID to get activity for
            viewer_id: Optional viewer user ID (for privacy checks)
            limit: Number of activities to return

        Returns:
            List of activities
        """
        # Build filter
        filter_query: Dict[str, Any] = {"user_id": user_id}

        # Apply visibility filter based on viewer
        if viewer_id != user_id:
            if viewer_id:
                # Check if viewer is following
                from app.services.social_service import get_social_service
                social_service = get_social_service(self.db)
                is_following = await social_service.is_following(viewer_id, user_id)

                if is_following:
                    # Show public and followers_only
                    filter_query["visibility"] = {
                        "$in": [
                            ActivityVisibility.PUBLIC,
                            ActivityVisibility.FOLLOWERS_ONLY
                        ]
                    }
                else:
                    # Show only public
                    filter_query["visibility"] = ActivityVisibility.PUBLIC
            else:
                # Anonymous viewer: only public
                filter_query["visibility"] = ActivityVisibility.PUBLIC

        # Get activities
        activities = await self.activity_collection.find(
            filter_query
        ).sort("created_at", -1).limit(limit).to_list(length=limit)

        return activities

    async def get_following_feed(
        self, user_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get activity feed from users this user is following.

        Args:
            user_id: User ID to get feed for
            limit: Number of activities to return

        Returns:
            List of activities from followed users
        """
        # Get list of users being followed
        follows = await self.follows_collection.find({
            "follower_user_id": user_id,
            "status": "accepted"
        }).to_list(length=None)

        following_ids = [f["following_user_id"] for f in follows]

        if not following_ids:
            return []

        # Get activities from followed users
        # Show public and followers_only activities
        activities = await self.activity_collection.find({
            "user_id": {"$in": following_ids},
            "visibility": {
                "$in": [
                    ActivityVisibility.PUBLIC,
                    ActivityVisibility.FOLLOWERS_ONLY
                ]
            }
        }).sort("created_at", -1).limit(limit).to_list(length=limit)

        # Enrich with user info
        for activity in activities:
            user = await self.users_collection.find_one(
                {"user_id": activity["user_id"]},
                {"username": 1, "display_name": 1, "avatar_url": 1}
            )
            if user:
                activity["user"] = {
                    "user_id": user["user_id"],
                    "username": user.get("username"),
                    "display_name": user.get("display_name"),
                    "avatar_url": user.get("avatar_url")
                }

        return activities

    async def update_activity_from_session(
        self, session: Dict[str, Any]
    ) -> None:
        """
        Update activities based on reading session changes.

        Creates activities for:
        - First time opening a book (started_book)
        - Completing a book (completed_book)
        - Reaching milestones (25%, 50%, 75%)

        Args:
            session: Reading session document
        """
        user_id = session.get("user_id")
        book_id = session.get("book_id")
        progress = session.get("progress_percentage", 0)
        current_chunk = session.get("current_chunk_index", 0)

        if not user_id or not book_id:
            return

        # Check if this is the first chunk (started book)
        if current_chunk == 0:
            existing_start = await self.activity_collection.find_one({
                "user_id": user_id,
                "book_id": book_id,
                "activity_type": ActivityType.STARTED_BOOK
            })

            if not existing_start:
                await self.create_activity(
                    user_id, "started_book", book_id
                )

        # Check for completion
        if progress >= 100:
            existing_complete = await self.activity_collection.find_one({
                "user_id": user_id,
                "book_id": book_id,
                "activity_type": ActivityType.COMPLETED_BOOK
            })

            if not existing_complete:
                await self.create_activity(
                    user_id, "completed_book", book_id
                )

        # Check for milestones
        milestones = [25, 50, 75]
        for milestone in milestones:
            if progress >= milestone:
                existing_milestone = await self.activity_collection.find_one({
                    "user_id": user_id,
                    "book_id": book_id,
                    "activity_type": ActivityType.MILESTONE_REACHED,
                    "progress_percentage": milestone
                })

                if not existing_milestone:
                    await self.create_activity(
                        user_id,
                        "milestone_reached",
                        book_id,
                        progress_percentage=milestone
                    )

    async def delete_user_activities(self, user_id: str) -> int:
        """
        Delete all activities for a user.

        Used for account deletion/privacy.

        Args:
            user_id: User ID

        Returns:
            Number of activities deleted
        """
        result = await self.activity_collection.delete_many({"user_id": user_id})
        logger.info(f"Deleted {result.deleted_count} activities for user {user_id}")
        return result.deleted_count


def get_reading_activity_service(db: AsyncIOMotorDatabase) -> ReadingActivityService:
    """
    Get reading activity service instance.

    Args:
        db: MongoDB database instance

    Returns:
        ReadingActivityService instance
    """
    return ReadingActivityService(db)
