"""
Social service for user follow/unfollow and blocking functionality.

Handles:
- Follow/unfollow relationships
- Follower/following lists
- Block/unblock users
- Social stats updates
- Follow suggestions
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.social import UserFollow, FollowStatus, UserBlock
from app.models.user import User

logger = logging.getLogger(__name__)


class SocialService:
    """Service for managing social interactions between users."""

    # Rate limiting constants
    MAX_FOLLOW_PER_HOUR = 20
    MAX_FOLLOWING_TOTAL = 2000

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize social service.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.users_collection = db.users
        self.follows_collection = db.user_follows
        self.blocks_collection = db.user_blocks

    async def follow_user(
        self, follower_id: str, following_id: str
    ) -> Dict[str, Any]:
        """
        Follow a user.

        Args:
            follower_id: User ID doing the following
            following_id: User ID being followed

        Returns:
            Dict with follow details

        Raises:
            ValueError: If validation fails
        """
        # Validation
        if follower_id == following_id:
            raise ValueError("You cannot follow yourself")

        # Check if users exist
        follower = await self.users_collection.find_one({"user_id": follower_id})
        following = await self.users_collection.find_one({"user_id": following_id})

        if not follower or not following:
            raise ValueError("User not found")

        # Check if blocked
        is_blocked = await self.is_blocked(follower_id, following_id)
        is_blocking = await self.is_blocked(following_id, follower_id)

        if is_blocked or is_blocking:
            raise ValueError("Cannot follow this user")

        # Check follow limits
        following_count = await self.follows_collection.count_documents({
            "follower_user_id": follower_id,
            "status": FollowStatus.ACCEPTED
        })

        if following_count >= self.MAX_FOLLOWING_TOTAL:
            raise ValueError(
                f"You have reached the maximum follow limit ({self.MAX_FOLLOWING_TOTAL})"
            )

        # Check rate limiting (follows in last hour)
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_follows = await self.follows_collection.count_documents({
            "follower_user_id": follower_id,
            "requested_at": {"$gte": one_hour_ago}
        })

        if recent_follows >= self.MAX_FOLLOW_PER_HOUR:
            raise ValueError(
                f"You have exceeded the hourly follow limit ({self.MAX_FOLLOW_PER_HOUR}). "
                "Please try again later."
            )

        # Check if already following
        existing_follow = await self.follows_collection.find_one({
            "follower_user_id": follower_id,
            "following_user_id": following_id
        })

        if existing_follow:
            if existing_follow.get("status") == FollowStatus.ACCEPTED:
                raise ValueError("You are already following this user")
            # If previously rejected/pending, update to accepted
            await self.follows_collection.update_one(
                {"_id": existing_follow["_id"]},
                {
                    "$set": {
                        "status": FollowStatus.ACCEPTED,
                        "accepted_at": datetime.utcnow()
                    }
                }
            )
        else:
            # Create new follow
            # Auto-accept unless user requires approval (future feature)
            follow = UserFollow(
                follower_user_id=follower_id,
                following_user_id=following_id,
                status=FollowStatus.ACCEPTED,
                accepted_at=datetime.utcnow()
            )
            await self.follows_collection.insert_one(follow.dict())

        # Update denormalized stats
        await self.update_social_stats(follower_id)
        await self.update_social_stats(following_id)

        # Send notification to the followed user
        try:
            from app.services.notification_service import NotificationService
            from app.models.notification import NotificationType, NotificationPriority
            notification_service = NotificationService(self.db)

            # Get follower's display name for notification
            follower_doc = await self.users_collection.find_one({"user_id": follower_id})
            follower_name = (follower_doc.get("display_name") or
                            follower_doc.get("username") or
                            f"User {follower_id[:8]}...")

            await notification_service.create_notification(
                user_id=following_id,
                notification_type=NotificationType.SOCIAL_FOLLOW,
                title="New Follower",
                message=f"{follower_name} started following you",
                priority=NotificationPriority.LOW,
                action_url=f"/users/{follower_id}",
                action_label="View Profile",
                metadata={"follower_id": follower_id, "follower_name": follower_name}
            )
        except Exception as notif_error:
            logger.error(f"Failed to send follow notification: {notif_error}")

        logger.info(f"User {follower_id} followed {following_id}")

        return {
            "success": True,
            "message": "Successfully followed user",
            "following_user_id": following_id
        }

    async def unfollow_user(
        self, follower_id: str, following_id: str
    ) -> bool:
        """
        Unfollow a user.

        Args:
            follower_id: User ID doing the unfollowing
            following_id: User ID being unfollowed

        Returns:
            True if successful
        """
        result = await self.follows_collection.delete_one({
            "follower_user_id": follower_id,
            "following_user_id": following_id
        })

        if result.deleted_count > 0:
            # Update denormalized stats
            await self.update_social_stats(follower_id)
            await self.update_social_stats(following_id)
            logger.info(f"User {follower_id} unfollowed {following_id}")
            return True

        return False

    async def get_followers(
        self, user_id: str, page: int = 1, per_page: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get list of users following this user.

        Args:
            user_id: User ID to get followers for
            page: Page number (1-indexed)
            per_page: Results per page

        Returns:
            List of user dictionaries
        """
        skip = (page - 1) * per_page

        # Get follower IDs
        follows = await self.follows_collection.find({
            "following_user_id": user_id,
            "status": FollowStatus.ACCEPTED
        }).sort("accepted_at", -1).skip(skip).limit(per_page).to_list(length=per_page)

        follower_ids = [f["follower_user_id"] for f in follows]

        # Get user details
        if not follower_ids:
            return []

        users = await self.users_collection.find({
            "user_id": {"$in": follower_ids}
        }).to_list(length=len(follower_ids))

        return users

    async def get_following(
        self, user_id: str, page: int = 1, per_page: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get list of users this user is following.

        Args:
            user_id: User ID to get following for
            page: Page number (1-indexed)
            per_page: Results per page

        Returns:
            List of user dictionaries
        """
        skip = (page - 1) * per_page

        # Get following IDs
        follows = await self.follows_collection.find({
            "follower_user_id": user_id,
            "status": FollowStatus.ACCEPTED
        }).sort("accepted_at", -1).skip(skip).limit(per_page).to_list(length=per_page)

        following_ids = [f["following_user_id"] for f in follows]

        # Get user details
        if not following_ids:
            return []

        users = await self.users_collection.find({
            "user_id": {"$in": following_ids}
        }).to_list(length=len(following_ids))

        return users

    async def is_following(
        self, follower_id: str, following_id: str
    ) -> bool:
        """
        Check if user is following another user.

        Args:
            follower_id: User ID doing the following
            following_id: User ID being followed

        Returns:
            True if following
        """
        follow = await self.follows_collection.find_one({
            "follower_user_id": follower_id,
            "following_user_id": following_id,
            "status": FollowStatus.ACCEPTED
        })
        return follow is not None

    async def get_follow_suggestions(
        self, user_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get follow suggestions for a user.

        Currently returns users with:
        - Most followers
        - Most listening hours
        - Recently active
        - Not already following
        - Not blocked

        Args:
            user_id: User ID to get suggestions for
            limit: Number of suggestions to return

        Returns:
            List of suggested users
        """
        # Get users this user is already following
        following = await self.follows_collection.find({
            "follower_user_id": user_id,
            "status": FollowStatus.ACCEPTED
        }).to_list(length=None)
        following_ids = [f["following_user_id"] for f in following]

        # Get blocked users
        blocks = await self.blocks_collection.find({
            "$or": [
                {"blocker_user_id": user_id},
                {"blocked_user_id": user_id}
            ]
        }).to_list(length=None)
        blocked_ids = set()
        for block in blocks:
            blocked_ids.add(block["blocker_user_id"])
            blocked_ids.add(block["blocked_user_id"])

        # Exclude: self, already following, blocked users
        exclude_ids = following_ids + list(blocked_ids) + [user_id]

        # Find users with high social stats who are discoverable
        users = await self.users_collection.find({
            "user_id": {"$nin": exclude_ids},
            "username": {"$ne": None},  # Must have username
            "privacy_settings.discoverable_by_search": True,
            "privacy_settings.allow_follow_requests": True
        }).sort([
            ("social_stats.followers_count", -1),
            ("social_stats.total_listening_hours", -1)
        ]).limit(limit).to_list(length=limit)

        return users

    async def update_social_stats(self, user_id: str) -> None:
        """
        Update denormalized social stats for a user.

        Recalculates:
        - Follower count
        - Following count

        Args:
            user_id: User ID to update stats for
        """
        # Count followers
        followers_count = await self.follows_collection.count_documents({
            "following_user_id": user_id,
            "status": FollowStatus.ACCEPTED
        })

        # Count following
        following_count = await self.follows_collection.count_documents({
            "follower_user_id": user_id,
            "status": FollowStatus.ACCEPTED
        })

        # Update user document
        await self.users_collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "social_stats.followers_count": followers_count,
                    "social_stats.following_count": following_count,
                    "social_stats.last_stats_update": datetime.utcnow()
                }
            }
        )

        logger.debug(
            f"Updated social stats for {user_id}: "
            f"{followers_count} followers, {following_count} following"
        )

    async def block_user(
        self, blocker_id: str, blocked_id: str, reason: Optional[str] = None
    ) -> bool:
        """
        Block a user.

        Removes existing follow relationships in both directions.

        Args:
            blocker_id: User ID doing the blocking
            blocked_id: User ID being blocked
            reason: Optional reason for blocking

        Returns:
            True if successful

        Raises:
            ValueError: If validation fails
        """
        if blocker_id == blocked_id:
            raise ValueError("You cannot block yourself")

        # Check if already blocked
        existing_block = await self.blocks_collection.find_one({
            "blocker_user_id": blocker_id,
            "blocked_user_id": blocked_id
        })

        if existing_block:
            raise ValueError("User is already blocked")

        # Create block
        block = UserBlock(
            blocker_user_id=blocker_id,
            blocked_user_id=blocked_id,
            reason=reason
        )
        await self.blocks_collection.insert_one(block.dict())

        # Remove follow relationships in both directions
        await self.follows_collection.delete_many({
            "$or": [
                {"follower_user_id": blocker_id, "following_user_id": blocked_id},
                {"follower_user_id": blocked_id, "following_user_id": blocker_id}
            ]
        })

        # Update stats
        await self.update_social_stats(blocker_id)
        await self.update_social_stats(blocked_id)

        logger.info(f"User {blocker_id} blocked {blocked_id}")
        return True

    async def unblock_user(
        self, blocker_id: str, blocked_id: str
    ) -> bool:
        """
        Unblock a user.

        Args:
            blocker_id: User ID doing the unblocking
            blocked_id: User ID being unblocked

        Returns:
            True if successful
        """
        result = await self.blocks_collection.delete_one({
            "blocker_user_id": blocker_id,
            "blocked_user_id": blocked_id
        })

        if result.deleted_count > 0:
            logger.info(f"User {blocker_id} unblocked {blocked_id}")
            return True

        return False

    async def is_blocked(
        self, user_id: str, other_user_id: str
    ) -> bool:
        """
        Check if user is blocked by or has blocked another user.

        Args:
            user_id: First user ID
            other_user_id: Second user ID

        Returns:
            True if blocked in either direction
        """
        block = await self.blocks_collection.find_one({
            "$or": [
                {"blocker_user_id": user_id, "blocked_user_id": other_user_id},
                {"blocker_user_id": other_user_id, "blocked_user_id": user_id}
            ]
        })
        return block is not None


def get_social_service(db: AsyncIOMotorDatabase) -> SocialService:
    """
    Get social service instance.

    Args:
        db: MongoDB database instance

    Returns:
        SocialService instance
    """
    return SocialService(db)
