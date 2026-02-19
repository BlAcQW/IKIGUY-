"""
Notification service for InkWave.

Handles creating and delivering notifications for achievements, streaks, and social activities.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.notification import (
    Notification,
    NotificationType,
    NotificationPriority,
    NotificationPreferences
)

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing notifications."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize notification service.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.notifications_collection = db.notifications
        self.users_collection = db.users

    async def create_notification(
        self,
        user_id: str,
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        action_url: Optional[str] = None,
        action_label: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        expires_in_days: Optional[int] = 30
    ) -> Notification:
        """
        Create a new notification.

        Args:
            user_id: User ID
            notification_type: Type of notification
            title: Notification title
            message: Message body
            priority: Priority level
            action_url: Optional URL for action
            action_label: Optional action button label
            metadata: Additional context data
            expires_in_days: Days until notification expires (None = never)

        Returns:
            Created notification
        """
        # Get user preferences
        preferences = await self._get_user_preferences(user_id)

        # Check if user wants this type of notification
        if not self._should_send_notification(notification_type, preferences):
            logger.debug(f"User {user_id} has disabled {notification_type} notifications")
            return None

        # Check quiet hours
        if preferences.quiet_hours_enabled and self._is_quiet_hours(preferences):
            logger.debug(f"Skipping notification for user {user_id} (quiet hours)")
            return None

        # Create notification
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        notification = Notification(
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
            priority=priority,
            action_url=action_url,
            action_label=action_label,
            metadata=metadata or {},
            expires_at=expires_at
        )

        # Save to database
        await self.notifications_collection.insert_one(notification.dict())

        logger.info(f"Created {notification_type} notification for user {user_id}")

        # TODO: Send push notification if enabled
        # if preferences.push:
        #     await self._send_push_notification(notification)

        return notification

    async def notify_achievement_earned(
        self,
        user_id: str,
        achievement_name: str,
        achievement_tier: str,
        points: int,
        achievement_id: str
    ):
        """
        Send notification for newly earned achievement.

        Args:
            user_id: User ID
            achievement_name: Achievement name
            achievement_tier: Tier (bronze, silver, gold, etc.)
            points: Points earned
            achievement_id: Achievement ID
        """
        tier_emoji = {
            "bronze": "🥉",
            "silver": "🥈",
            "gold": "🥇",
            "platinum": "💎",
            "diamond": "💠"
        }

        emoji = tier_emoji.get(achievement_tier, "🏆")

        await self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.ACHIEVEMENT_EARNED,
            title=f"{emoji} Achievement Unlocked!",
            message=f"You earned '{achievement_name}' (+{points} points)",
            priority=NotificationPriority.HIGH,
            action_url="/achievements",
            action_label="View Achievements",
            metadata={
                "achievement_id": achievement_id,
                "achievement_name": achievement_name,
                "tier": achievement_tier,
                "points": points
            }
        )

    async def notify_streak_milestone(
        self,
        user_id: str,
        streak_days: int
    ):
        """
        Send notification for streak milestone.

        Args:
            user_id: User ID
            streak_days: Current streak in days
        """
        milestones = [7, 14, 30, 50, 100, 365]
        if streak_days not in milestones:
            return

        milestone_messages = {
            7: "🔥 Amazing! You've maintained a 7-day listening streak!",
            14: "🔥🔥 Incredible! 2 weeks of consistent listening!",
            30: "🔥🔥🔥 Outstanding! 30-day streak achieved!",
            50: "🔥🔥🔥🔥 Phenomenal! 50 days in a row!",
            100: "🔥🔥🔥🔥🔥 Legendary! 100-day streak!",
            365: "🔥🏆🔥 EPIC! A full year of daily listening!"
        }

        await self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.STREAK_MILESTONE,
            title=f"🔥 {streak_days}-Day Streak!",
            message=milestone_messages.get(streak_days, f"You've listened {streak_days} days in a row!"),
            priority=NotificationPriority.HIGH,
            action_url="/streaks",
            action_label="View Streak",
            metadata={"streak_days": streak_days}
        )

    async def notify_streak_reminder(
        self,
        user_id: str,
        streak_days: int
    ):
        """
        Send daily reminder to maintain streak.

        Args:
            user_id: User ID
            streak_days: Current streak in days
        """
        await self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.STREAK_REMINDER,
            title="📚 Don't break your streak!",
            message=f"You're on a {streak_days}-day streak. Listen today to keep it going!",
            priority=NotificationPriority.MEDIUM,
            action_url="/books",
            action_label="Continue Listening",
            metadata={"streak_days": streak_days},
            expires_in_days=1  # Expires tomorrow
        )

    async def notify_streak_broken(
        self,
        user_id: str,
        broken_streak: int
    ):
        """
        Send notification when streak is broken.

        Args:
            user_id: User ID
            broken_streak: Length of broken streak
        """
        await self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.STREAK_BROKEN,
            title="💔 Streak ended",
            message=f"Your {broken_streak}-day streak ended. Start a new one today!",
            priority=NotificationPriority.LOW,
            action_url="/books",
            action_label="Start Listening",
            metadata={"broken_streak": broken_streak}
        )

    async def notify_leaderboard_position(
        self,
        user_id: str,
        new_rank: int,
        old_rank: Optional[int] = None,
        leaderboard_type: str = "listening_hours"
    ):
        """
        Send notification for leaderboard position change.

        Args:
            user_id: User ID
            new_rank: New rank
            old_rank: Previous rank (None if first time)
            leaderboard_type: Type of leaderboard
        """
        if old_rank is None:
            message = f"You're now #{new_rank} on the {leaderboard_type} leaderboard!"
        elif new_rank < old_rank:
            change = old_rank - new_rank
            message = f"🎉 You moved up {change} places to #{new_rank}!"
        else:
            return  # Don't notify for rank decrease

        await self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.LEADERBOARD_POSITION,
            title="📊 Leaderboard Update",
            message=message,
            priority=NotificationPriority.MEDIUM,
            action_url="/leaderboard",
            action_label="View Leaderboard",
            metadata={
                "new_rank": new_rank,
                "old_rank": old_rank,
                "leaderboard_type": leaderboard_type
            }
        )

    async def get_user_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Notification]:
        """
        Get user's notifications.

        Args:
            user_id: User ID
            unread_only: Only return unread notifications
            limit: Maximum notifications to return

        Returns:
            List of notifications
        """
        query = {"user_id": user_id}

        if unread_only:
            query["is_read"] = False

        # Filter expired notifications
        query["$or"] = [
            {"expires_at": None},
            {"expires_at": {"$gt": datetime.utcnow()}}
        ]

        notifications = await self.notifications_collection.find(query)\
            .sort("created_at", -1)\
            .limit(limit)\
            .to_list(length=limit)

        return [Notification(**notif) for notif in notifications]

    async def mark_as_read(
        self,
        user_id: str,
        notification_id: str
    ) -> bool:
        """
        Mark notification as read.

        Args:
            user_id: User ID
            notification_id: Notification ID

        Returns:
            True if successful
        """
        result = await self.notifications_collection.update_one(
            {
                "notification_id": notification_id,
                "user_id": user_id
            },
            {
                "$set": {
                    "is_read": True,
                    "read_at": datetime.utcnow()
                }
            }
        )

        return result.modified_count > 0

    async def mark_all_as_read(self, user_id: str) -> int:
        """
        Mark all user's notifications as read.

        Args:
            user_id: User ID

        Returns:
            Number of notifications marked as read
        """
        result = await self.notifications_collection.update_many(
            {
                "user_id": user_id,
                "is_read": False
            },
            {
                "$set": {
                    "is_read": True,
                    "read_at": datetime.utcnow()
                }
            }
        )

        return result.modified_count

    async def get_unread_count(self, user_id: str) -> int:
        """
        Get count of unread notifications.

        Args:
            user_id: User ID

        Returns:
            Number of unread notifications
        """
        count = await self.notifications_collection.count_documents({
            "user_id": user_id,
            "is_read": False,
            "$or": [
                {"expires_at": None},
                {"expires_at": {"$gt": datetime.utcnow()}}
            ]
        })

        return count

    async def delete_notification(
        self,
        user_id: str,
        notification_id: str
    ) -> bool:
        """
        Delete a notification.

        Args:
            user_id: User ID
            notification_id: Notification ID

        Returns:
            True if successful
        """
        result = await self.notifications_collection.delete_one({
            "notification_id": notification_id,
            "user_id": user_id
        })

        return result.deleted_count > 0

    async def cleanup_expired_notifications(self) -> int:
        """
        Delete expired notifications.

        Returns:
            Number of notifications deleted
        """
        result = await self.notifications_collection.delete_many({
            "expires_at": {"$lte": datetime.utcnow()}
        })

        logger.info(f"Cleaned up {result.deleted_count} expired notifications")
        return result.deleted_count

    async def _get_user_preferences(self, user_id: str) -> NotificationPreferences:
        """Get user's notification preferences."""
        user = await self.users_collection.find_one({"user_id": user_id})

        if not user or "notification_preferences" not in user:
            # Return default preferences
            return NotificationPreferences()

        return NotificationPreferences(**user["notification_preferences"])

    def _should_send_notification(
        self,
        notification_type: NotificationType,
        preferences: NotificationPreferences
    ) -> bool:
        """Check if notification should be sent based on user preferences."""
        if not preferences.in_app:
            return False

        type_mapping = {
            NotificationType.ACHIEVEMENT_EARNED: preferences.achievement_earned,
            NotificationType.STREAK_MILESTONE: preferences.streak_milestones,
            NotificationType.STREAK_REMINDER: preferences.streak_reminders,
            NotificationType.STREAK_BROKEN: preferences.streak_broken,
            NotificationType.LEADERBOARD_POSITION: preferences.leaderboard_position,
            NotificationType.SOCIAL_FOLLOW: preferences.social_follows,
            NotificationType.SOCIAL_MENTION: preferences.social_mentions,
            NotificationType.BOOK_RECOMMENDATION: preferences.book_recommendations,
            NotificationType.SYSTEM_ANNOUNCEMENT: preferences.system_announcements,
        }

        return type_mapping.get(notification_type, True)

    def _is_quiet_hours(self, preferences: NotificationPreferences) -> bool:
        """Check if currently in quiet hours."""
        if not preferences.quiet_hours_enabled:
            return False

        if not preferences.quiet_hours_start or not preferences.quiet_hours_end:
            return False

        now = datetime.utcnow()
        current_time = now.strftime("%H:%M")

        start = preferences.quiet_hours_start
        end = preferences.quiet_hours_end

        # Handle wraparound (e.g., 22:00 to 06:00)
        if start <= end:
            return start <= current_time <= end
        else:
            return current_time >= start or current_time <= end
