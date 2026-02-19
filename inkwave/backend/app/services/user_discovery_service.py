"""
User discovery service for search, profiles, and username management.

Handles:
- User search (with privacy filters)
- Public profile visibility
- Username validation and updates
- Reading activity visibility
- Currently reading books
"""

import logging
import re
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.user import User

logger = logging.getLogger(__name__)


class UserDiscoveryService:
    """Service for user discovery and profile visibility."""

    # Username change cooldown (30 days)
    USERNAME_CHANGE_COOLDOWN_DAYS = 30

    # Username reservation period (90 days after change)
    USERNAME_RESERVATION_DAYS = 90

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize user discovery service.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.users_collection = db.users
        self.blocks_collection = db.user_blocks
        self.follows_collection = db.user_follows
        self.reading_sessions_collection = db.reading_sessions
        self.reading_activity_collection = db.reading_activity
        self.books_collection = db.books

    async def search_users(
        self,
        query: str,
        viewer_id: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for users by username or display name.

        Only returns users who:
        - Are discoverable by search
        - Have a username set
        - Are not blocked by/blocking viewer

        Args:
            query: Search query
            viewer_id: Optional user ID of the searcher
            page: Page number (1-indexed)
            per_page: Results per page

        Returns:
            List of user dictionaries
        """
        skip = (page - 1) * per_page

        # Build filter
        search_filter: Dict[str, Any] = {
            "username": {"$ne": None},
            "privacy_settings.discoverable_by_search": True
        }

        # Exclude blocked users if viewer is provided
        if viewer_id:
            # Get blocked user IDs
            blocks = await self.blocks_collection.find({
                "$or": [
                    {"blocker_user_id": viewer_id},
                    {"blocked_user_id": viewer_id}
                ]
            }).to_list(length=None)

            blocked_ids = set()
            for block in blocks:
                blocked_ids.add(block["blocker_user_id"])
                blocked_ids.add(block["blocked_user_id"])

            if blocked_ids:
                search_filter["user_id"] = {"$nin": list(blocked_ids)}

        # Text search on username and display_name
        if query:
            # Use regex for flexible matching
            search_regex = {"$regex": query, "$options": "i"}
            search_filter["$or"] = [
                {"username": search_regex},
                {"display_name": search_regex}
            ]

        # Execute search
        users = await self.users_collection.find(search_filter).sort([
            ("social_stats.followers_count", -1),
            ("username", 1)
        ]).skip(skip).limit(per_page).to_list(length=per_page)

        return users

    async def get_public_profile(
        self, user_id: str, viewer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get public profile for a user.

        Respects privacy settings and blocking.

        Args:
            user_id: User ID to get profile for
            viewer_id: Optional user ID of the viewer

        Returns:
            Public profile dictionary

        Raises:
            ValueError: If profile not accessible
        """
        # Get user
        user = await self.users_collection.find_one({"user_id": user_id})
        if not user:
            raise ValueError("User not found")

        # Check if blocked
        if viewer_id:
            from app.services.social_service import get_social_service
            social_service = get_social_service(self.db)
            is_blocked = await social_service.is_blocked(viewer_id, user_id)
            if is_blocked:
                raise ValueError("User not found")  # Don't reveal block status

        # Check profile visibility
        can_view = await self.can_view_profile(user, viewer_id)
        if not can_view:
            raise ValueError("This profile is private")

        # Build public profile
        profile = {
            "user_id": user["user_id"],
            "username": user.get("username"),
            "display_name": user.get("display_name"),
            "avatar_url": user.get("avatar_url"),
            "bio": user.get("bio"),
            "created_at": user.get("created_at")
        }

        # Privacy settings for what to show
        privacy = user.get("privacy_settings", {})

        # Social stats
        if privacy.get("show_follower_count", True):
            profile["followers_count"] = user.get("social_stats", {}).get("followers_count", 0)

        if privacy.get("show_following_count", True):
            profile["following_count"] = user.get("social_stats", {}).get("following_count", 0)

        if privacy.get("show_listening_stats", False):
            stats = user.get("social_stats", {})
            profile["listening_stats"] = {
                "total_listening_hours": stats.get("total_listening_hours", 0.0),
                "books_completed": stats.get("books_completed", 0),
                "current_streak_days": stats.get("current_streak_days", 0)
            }

        # Is viewer following this user?
        if viewer_id:
            from app.services.social_service import get_social_service
            social_service = get_social_service(self.db)
            profile["is_following"] = await social_service.is_following(viewer_id, user_id)
            profile["is_follower"] = await social_service.is_following(user_id, viewer_id)

        return profile

    async def can_view_profile(
        self, user: Dict[str, Any], viewer_id: Optional[str]
    ) -> bool:
        """
        Check if viewer can see user's profile.

        Args:
            user: User document
            viewer_id: Optional viewer user ID

        Returns:
            True if profile is visible
        """
        privacy = user.get("privacy_settings", {})
        visibility = privacy.get("profile_visibility", "followers_only")

        if visibility == "public":
            return True

        if visibility == "private":
            # Only owner can view
            return viewer_id == user["user_id"]

        if visibility == "followers_only":
            # Owner can view
            if viewer_id == user["user_id"]:
                return True

            # Check if viewer is a follower
            if viewer_id:
                from app.services.social_service import get_social_service
                social_service = get_social_service(self.db)
                return await social_service.is_following(viewer_id, user["user_id"])

            return False

        return False

    async def get_currently_reading(
        self, user_id: str, viewer_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get books user is currently reading.

        Args:
            user_id: User ID to get books for
            viewer_id: Optional viewer user ID

        Returns:
            List of books with progress

        Raises:
            ValueError: If not authorized
        """
        # Get user
        user = await self.users_collection.find_one({"user_id": user_id})
        if not user:
            raise ValueError("User not found")

        # Check privacy
        privacy = user.get("privacy_settings", {})
        if not privacy.get("show_currently_reading", False):
            # Only owner can see
            if viewer_id != user_id:
                raise ValueError("User has disabled currently reading visibility")

        # Check profile visibility
        can_view = await self.can_view_profile(user, viewer_id)
        if not can_view:
            raise ValueError("This profile is private")

        # Get active reading sessions
        sessions = await self.reading_sessions_collection.find({
            "user_id": user_id,
            "current_chunk_index": {"$gte": 0}  # Has made progress
        }).sort("last_accessed", -1).limit(5).to_list(length=5)

        # Get book details
        books = []
        for session in sessions:
            book = await self.books_collection.find_one({"book_id": session["book_id"]})
            if book:
                books.append({
                    "book_id": book["book_id"],
                    "title": book.get("title"),
                    "author": book.get("author"),
                    "cover_url": book.get("cover_url"),
                    "progress_percentage": session.get("progress_percentage", 0),
                    "last_read": session.get("last_accessed")
                })

        return books

    async def get_reading_activity(
        self, user_id: str, viewer_id: Optional[str] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get user's reading activity.

        Args:
            user_id: User ID to get activity for
            viewer_id: Optional viewer user ID
            limit: Number of activities to return

        Returns:
            List of activities

        Raises:
            ValueError: If not authorized
        """
        # Get user
        user = await self.users_collection.find_one({"user_id": user_id})
        if not user:
            raise ValueError("User not found")

        # Check privacy
        privacy = user.get("privacy_settings", {})
        if not privacy.get("show_reading_history", False):
            if viewer_id != user_id:
                raise ValueError("User has disabled reading history visibility")

        # Check profile visibility
        can_view = await self.can_view_profile(user, viewer_id)
        if not can_view:
            raise ValueError("This profile is private")

        # Build filter
        filter_query: Dict[str, Any] = {"user_id": user_id}

        # Apply visibility filter
        if viewer_id != user_id:
            # Non-owner: check activity visibility
            from app.services.social_service import get_social_service
            social_service = get_social_service(self.db)
            is_follower = await social_service.is_following(viewer_id, user_id) if viewer_id else False

            if is_follower:
                filter_query["visibility"] = {"$in": ["public", "followers_only"]}
            else:
                filter_query["visibility"] = "public"

        # Get activities
        activities = await self.reading_activity_collection.find(
            filter_query
        ).sort("created_at", -1).limit(limit).to_list(length=limit)

        return activities

    async def validate_username(self, username: str) -> bool:
        """
        Validate username format.

        Args:
            username: Username to validate

        Returns:
            True if valid

        Raises:
            ValueError: If invalid with reason
        """
        if not username:
            raise ValueError("Username is required")

        if len(username) < 3:
            raise ValueError("Username must be at least 3 characters")

        if len(username) > 30:
            raise ValueError("Username must be at most 30 characters")

        # Check format
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9._-]*[a-zA-Z0-9]$', username):
            raise ValueError(
                'Username must be alphanumeric and can contain dots, underscores, '
                'or hyphens (but cannot start or end with them)'
            )

        # Check for consecutive special characters
        if re.search(r'[._-]{2,}', username):
            raise ValueError('Username cannot contain consecutive special characters')

        return True

    async def is_username_available(self, username: str) -> bool:
        """
        Check if username is available.

        Args:
            username: Username to check

        Returns:
            True if available
        """
        username_lower = username.lower()

        # Check if username exists
        existing = await self.users_collection.find_one({"username": username_lower})
        if existing:
            return False

        # TODO: Check reserved usernames (from recent changes)
        # For now, just check if it exists

        return True

    async def update_username(
        self, user_id: str, new_username: str
    ) -> Dict[str, Any]:
        """
        Update user's username.

        Enforces 30-day cooldown between changes.

        Args:
            user_id: User ID
            new_username: New username

        Returns:
            Updated user document

        Raises:
            ValueError: If validation fails
        """
        # Validate format
        await self.validate_username(new_username)

        # Check availability
        is_available = await self.is_username_available(new_username)
        if not is_available:
            raise ValueError("Username is already taken")

        # Get user
        user = await self.users_collection.find_one({"user_id": user_id})
        if not user:
            raise ValueError("User not found")

        # Check cooldown
        last_changed = user.get("username_last_changed")
        if last_changed:
            cooldown_end = last_changed + timedelta(days=self.USERNAME_CHANGE_COOLDOWN_DAYS)
            if datetime.utcnow() < cooldown_end:
                days_remaining = (cooldown_end - datetime.utcnow()).days
                raise ValueError(
                    f"You can change your username again in {days_remaining} days. "
                    f"Usernames can only be changed once every {self.USERNAME_CHANGE_COOLDOWN_DAYS} days."
                )

        # Update username
        result = await self.users_collection.find_one_and_update(
            {"user_id": user_id},
            {
                "$set": {
                    "username": new_username.lower(),
                    "username_last_changed": datetime.utcnow()
                }
            },
            return_document=True
        )

        logger.info(f"User {user_id} changed username to {new_username}")

        return result


def get_user_discovery_service(db: AsyncIOMotorDatabase) -> UserDiscoveryService:
    """
    Get user discovery service instance.

    Args:
        db: MongoDB database instance

    Returns:
        UserDiscoveryService instance
    """
    return UserDiscoveryService(db)
