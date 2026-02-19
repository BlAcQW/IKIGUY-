"""
Streak tracking service for InkWave.

Manages daily listening streaks and updates.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, date, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.streak import ListeningStreak

logger = logging.getLogger(__name__)


class StreakService:
    """Service for managing daily listening streaks."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize streak service.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.users_collection = db.users

    async def update_streak(self, user_id: str) -> ListeningStreak:
        """
        Update user's listening streak after listening activity.

        Called when user completes a listening session.

        Args:
            user_id: User ID

        Returns:
            Updated streak data
        """
        # Get current user streak data
        user = await self.users_collection.find_one({"user_id": user_id})
        if not user:
            logger.warning(f"User {user_id} not found for streak update")
            return ListeningStreak()

        # Get existing streak or create new
        streak_data = user.get("streak", {})
        streak = ListeningStreak(**streak_data) if streak_data else ListeningStreak()

        # Get today's date
        today = date.today()

        # Convert last_activity_date if it exists
        last_activity_date = None
        if streak.last_activity_date:
            if isinstance(streak.last_activity_date, str):
                last_activity_date = date.fromisoformat(streak.last_activity_date)
            else:
                last_activity_date = streak.last_activity_date

        # Check if this is first activity today
        if last_activity_date == today:
            # Already counted today, no update needed
            logger.debug(f"User {user_id} already has activity for today")
            return streak

        # Calculate streak
        if last_activity_date is None:
            # First ever activity
            streak.current_days = 1
            streak.longest_days = 1
            streak.streak_start_date = today
            streak.total_active_days = 1
            logger.info(f"Started first streak for user {user_id}")

        elif last_activity_date == today - timedelta(days=1):
            # Consecutive day - extend streak
            old_streak = streak.current_days
            streak.current_days += 1
            streak.total_active_days += 1

            # Update longest if needed
            if streak.current_days > streak.longest_days:
                streak.longest_days = streak.current_days

            logger.info(f"Extended streak for user {user_id} to {streak.current_days} days")

            # Send milestone notification if applicable
            try:
                from app.services.notification_service import NotificationService
                notification_service = NotificationService(self.db)
                await notification_service.notify_streak_milestone(
                    user_id=user_id,
                    streak_days=streak.current_days
                )
            except Exception as notif_error:
                logger.error(f"Failed to send streak milestone notification: {notif_error}")

        else:
            # Streak broken - start new streak
            logger.info(f"Streak broken for user {user_id}, starting new streak")
            streak.current_days = 1
            streak.streak_start_date = today
            streak.total_active_days += 1

        # Update last activity date
        streak.last_activity_date = today
        streak.last_checked = datetime.utcnow()
        streak.updated_at = datetime.utcnow()

        # Save to database
        await self.users_collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "streak": {
                        "current_days": streak.current_days,
                        "longest_days": streak.longest_days,
                        "last_activity_date": streak.last_activity_date.isoformat(),
                        "streak_start_date": streak.streak_start_date.isoformat() if streak.streak_start_date else None,
                        "total_active_days": streak.total_active_days,
                        "last_checked": streak.last_checked,
                        "updated_at": streak.updated_at
                    },
                    # Also update denormalized cache in social_stats
                    "social_stats.current_streak_days": streak.current_days
                }
            },
            upsert=True
        )

        logger.info(f"Updated streak for user {user_id}: {streak.current_days} days")
        return streak

    async def get_streak(self, user_id: str) -> Optional[ListeningStreak]:
        """
        Get user's current streak data.

        Args:
            user_id: User ID

        Returns:
            Streak data or None if not found
        """
        user = await self.users_collection.find_one({"user_id": user_id})
        if not user:
            return None

        streak_data = user.get("streak")
        if not streak_data:
            return ListeningStreak()

        return ListeningStreak(**streak_data)

    async def check_streak_expiry(self, user_id: str) -> ListeningStreak:
        """
        Check if user's streak has expired and reset if needed.

        A streak expires if the user didn't listen yesterday or today.

        Args:
            user_id: User ID

        Returns:
            Current streak data (possibly reset)
        """
        streak = await self.get_streak(user_id)
        if not streak or not streak.last_activity_date:
            return streak or ListeningStreak()

        # Convert last_activity_date if string
        last_activity_date = None
        if isinstance(streak.last_activity_date, str):
            last_activity_date = date.fromisoformat(streak.last_activity_date)
        else:
            last_activity_date = streak.last_activity_date

        today = date.today()
        yesterday = today - timedelta(days=1)

        # Streak is valid if last activity was today or yesterday
        if last_activity_date >= yesterday:
            return streak

        # Streak expired - reset current streak but keep stats
        logger.info(f"Streak expired for user {user_id} (last activity: {last_activity_date})")

        streak.current_days = 0
        streak.streak_start_date = None
        streak.updated_at = datetime.utcnow()

        # Save to database
        await self.users_collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "streak.current_days": 0,
                    "streak.streak_start_date": None,
                    "streak.updated_at": streak.updated_at,
                    "social_stats.current_streak_days": 0
                }
            }
        )

        return streak

    async def get_leaderboard(self, limit: int = 20) -> list[Dict[str, Any]]:
        """
        Get top users by current streak.

        Args:
            limit: Number of results to return

        Returns:
            List of users with streak data
        """
        pipeline = [
            {
                "$match": {
                    "streak.current_days": {"$gt": 0},
                    "privacy_settings.appear_in_leaderboard": True
                }
            },
            {
                "$project": {
                    "user_id": 1,
                    "username": 1,
                    "display_name": 1,
                    "avatar_url": 1,
                    "current_streak": "$streak.current_days",
                    "longest_streak": "$streak.longest_days",
                    "display_mode": "$privacy_settings.leaderboard_display_mode"
                }
            },
            {
                "$sort": {"current_streak": -1}
            },
            {
                "$limit": limit
            }
        ]

        users = await self.users_collection.aggregate(pipeline).to_list(length=limit)

        # Apply privacy settings
        leaderboard = []
        for rank, user in enumerate(users, 1):
            display_mode = user.get("display_mode", "full_profile")

            entry = {
                "rank": rank,
                "user_id": user["user_id"],
                "current_streak": user.get("current_streak", 0),
                "longest_streak": user.get("longest_streak", 0),
                "display_mode": display_mode
            }

            # Apply privacy
            if display_mode == "anonymous":
                # Generate nature-inspired username if user doesn't have one
                from app.services.username_generator import get_display_username
                display_username = get_display_username(user)

                entry["username"] = display_username
                entry["display_name"] = display_username
                entry["avatar_url"] = None
            else:
                entry["username"] = user.get("username")
                entry["display_name"] = user.get("display_name")
                entry["avatar_url"] = user.get("avatar_url")

            leaderboard.append(entry)

        return leaderboard
