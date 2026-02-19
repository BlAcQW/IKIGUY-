"""
Achievement service for InkWave.

Handles achievement checking, awarding, and progress tracking.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.achievement import (
    Achievement,
    UserAchievement,
    AchievementInDB,
    UserAchievementInDB,
    AchievementProgress,
    UserAchievementsResponse,
    AchievementCategory,
    ACHIEVEMENT_DEFINITIONS
)

logger = logging.getLogger(__name__)


class AchievementService:
    """Service for managing achievements and badges."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize achievement service.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.achievements_collection = db.achievements
        self.user_achievements_collection = db.user_achievements
        self.users_collection = db.users
        self.wallet_transactions_collection = db.wallet_transactions
        self.reading_sessions_collection = db.reading_sessions

    async def initialize_achievements(self) -> int:
        """
        Initialize achievement definitions in database.

        Returns:
            Number of achievements created/updated
        """
        count = 0

        for achievement_def in ACHIEVEMENT_DEFINITIONS:
            # Check if achievement exists
            existing = await self.achievements_collection.find_one({
                "achievement_id": achievement_def["achievement_id"]
            })

            if existing:
                # Update existing
                await self.achievements_collection.update_one(
                    {"achievement_id": achievement_def["achievement_id"]},
                    {"$set": {
                        **achievement_def,
                        "is_active": achievement_def.get("is_active", True),  # Default to True
                        "updated_at": datetime.utcnow()
                    }}
                )
            else:
                # Create new
                await self.achievements_collection.insert_one({
                    **achievement_def,
                    "is_active": achievement_def.get("is_active", True),  # Default to True
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                })
                count += 1

        logger.info(f"Initialized {count} new achievements")
        return count

    async def check_and_award_achievements(self, user_id: str) -> List[Achievement]:
        """
        Check all achievements for a user and award any newly earned ones.

        Args:
            user_id: User ID

        Returns:
            List of newly earned achievements
        """
        newly_earned = []

        # Get all active achievements
        achievements = await self.achievements_collection.find({
            "is_active": True
        }).to_list(length=None)

        for achievement_data in achievements:
            achievement = Achievement(**achievement_data)

            # Check if user already has this achievement
            user_achievement = await self.user_achievements_collection.find_one({
                "user_id": user_id,
                "achievement_id": achievement.achievement_id,
                "is_completed": True
            })

            if user_achievement:
                continue  # Already earned

            # Calculate current progress
            progress = await self._calculate_progress(user_id, achievement)

            # Check if requirement met
            if progress >= achievement.requirement_value:
                # Award achievement
                await self._award_achievement(user_id, achievement, progress)
                newly_earned.append(achievement)
                logger.info(f"Awarded achievement '{achievement.name}' to user {user_id}")

            else:
                # Update progress
                await self._update_progress(user_id, achievement, progress)

        return newly_earned

    async def _calculate_progress(
        self,
        user_id: str,
        achievement: Achievement
    ) -> float:
        """
        Calculate user's current progress for an achievement.

        Args:
            user_id: User ID
            achievement: Achievement to check

        Returns:
            Current progress value
        """
        req_type = achievement.requirement_type

        if req_type == "listening_minutes":
            # Total listening minutes
            result = await self.wallet_transactions_collection.aggregate([
                {
                    "$match": {
                        "user_id": user_id,
                        "metadata.service": "inkwave_listening"
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total": {"$sum": "$metadata.duration_minutes"}
                    }
                }
            ]).to_list(length=1)

            return result[0]["total"] if result else 0.0

        elif req_type == "listening_hours":
            # Total listening hours
            result = await self.wallet_transactions_collection.aggregate([
                {
                    "$match": {
                        "user_id": user_id,
                        "metadata.service": "inkwave_listening"
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total": {"$sum": "$metadata.duration_minutes"}
                    }
                }
            ]).to_list(length=1)

            total_minutes = result[0]["total"] if result else 0.0
            return total_minutes / 60.0

        elif req_type == "books_completed":
            # Number of completed books (100% progress)
            count = await self.reading_sessions_collection.count_documents({
                "user_id": user_id,
                "completed": True
            })
            return float(count)

        elif req_type == "streak_days":
            # Calculate current streak
            user = await self.users_collection.find_one({"user_id": user_id})
            if not user:
                return 0.0

            streak_data = user.get("streak", {})
            return float(streak_data.get("current_days", 0))

        elif req_type == "listening_hours_night":
            # Listening between 10 PM and 6 AM
            return await self._calculate_time_period_listening(
                user_id, start_hour=22, end_hour=6
            )

        elif req_type == "listening_hours_morning":
            # Listening between 5 AM and 8 AM
            return await self._calculate_time_period_listening(
                user_id, start_hour=5, end_hour=8
            )

        elif req_type == "following_count":
            # Number of users this user follows
            user = await self.users_collection.find_one({"user_id": user_id})
            if not user:
                return 0.0

            social_stats = user.get("social_stats", {})
            return float(social_stats.get("following_count", 0))

        elif req_type == "followers_count":
            # Number of followers
            user = await self.users_collection.find_one({"user_id": user_id})
            if not user:
                return 0.0

            social_stats = user.get("social_stats", {})
            return float(social_stats.get("followers_count", 0))

        return 0.0

    async def _calculate_time_period_listening(
        self,
        user_id: str,
        start_hour: int,
        end_hour: int
    ) -> float:
        """
        Calculate listening hours during specific time period.

        Args:
            user_id: User ID
            start_hour: Start hour (0-23)
            end_hour: End hour (0-23)

        Returns:
            Total hours listened during time period
        """
        # Get all transactions for user
        transactions = await self.wallet_transactions_collection.find({
            "user_id": user_id,
            "metadata.service": "inkwave_listening"
        }).to_list(length=None)

        total_minutes = 0.0

        for tx in transactions:
            created_at = tx.get("created_at")
            if not created_at:
                continue

            hour = created_at.hour

            # Check if in time range (handle wraparound like 22-6)
            if start_hour <= end_hour:
                in_range = start_hour <= hour < end_hour
            else:  # Wraparound (e.g., 22-6 means 22,23,0,1,2,3,4,5)
                in_range = hour >= start_hour or hour < end_hour

            if in_range:
                total_minutes += tx.get("metadata", {}).get("duration_minutes", 0)

        return total_minutes / 60.0

    async def _award_achievement(
        self,
        user_id: str,
        achievement: Achievement,
        final_progress: float
    ):
        """
        Award an achievement to a user.

        Args:
            user_id: User ID
            achievement: Achievement to award
            final_progress: Final progress value
        """
        # Create or update user achievement record
        await self.user_achievements_collection.update_one(
            {
                "user_id": user_id,
                "achievement_id": achievement.achievement_id
            },
            {
                "$set": {
                    "current_progress": final_progress,
                    "is_completed": True,
                    "completed_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                },
                "$setOnInsert": {
                    "user_achievement_id": str(__import__('uuid').uuid4()),
                    "user_id": user_id,
                    "achievement_id": achievement.achievement_id,
                    "notification_sent": False,
                    "viewed": False,
                    "created_at": datetime.utcnow()
                }
            },
            upsert=True
        )

        # Update user's total achievement points and count
        await self.users_collection.update_one(
            {"user_id": user_id},
            {
                "$inc": {
                    "social_stats.achievement_points": achievement.points,
                    "social_stats.achievements_earned": 1
                }
            }
        )

        # Send notification (non-blocking)
        try:
            from app.services.notification_service import NotificationService
            notification_service = NotificationService(self.db)
            await notification_service.notify_achievement_earned(
                user_id=user_id,
                achievement_name=achievement.name,
                achievement_tier=achievement.tier,
                points=achievement.points,
                achievement_id=achievement.achievement_id
            )
        except Exception as notif_error:
            logger.error(f"Failed to send achievement notification: {notif_error}")

    async def _update_progress(
        self,
        user_id: str,
        achievement: Achievement,
        current_progress: float
    ):
        """
        Update user's progress on an achievement.

        Args:
            user_id: User ID
            achievement: Achievement
            current_progress: Current progress value
        """
        await self.user_achievements_collection.update_one(
            {
                "user_id": user_id,
                "achievement_id": achievement.achievement_id
            },
            {
                "$set": {
                    "current_progress": current_progress,
                    "updated_at": datetime.utcnow()
                },
                "$setOnInsert": {
                    "user_achievement_id": str(__import__('uuid').uuid4()),
                    "user_id": user_id,
                    "achievement_id": achievement.achievement_id,
                    "is_completed": False,
                    "notification_sent": False,
                    "viewed": False,
                    "created_at": datetime.utcnow()
                }
            },
            upsert=True
        )

    async def get_user_achievements(self, user_id: str) -> UserAchievementsResponse:
        """
        Get all achievements for a user (earned, in progress, available).

        Args:
            user_id: User ID

        Returns:
            User's achievements organized by status
        """
        # Get all achievements
        all_achievements = await self.achievements_collection.find({
            "is_active": True
        }).to_list(length=None)

        # Get user's achievement records
        user_achievements = await self.user_achievements_collection.find({
            "user_id": user_id
        }).to_list(length=None)

        # Create lookup dictionary
        user_ach_dict = {
            ua["achievement_id"]: ua for ua in user_achievements
        }

        earned = []
        in_progress = []
        available = []

        for ach_data in all_achievements:
            achievement = Achievement(**ach_data)
            user_ach = user_ach_dict.get(achievement.achievement_id)

            if user_ach and user_ach.get("is_completed"):
                # Earned
                earned.append({
                    **ach_data,
                    "completed_at": user_ach.get("completed_at"),
                    "viewed": user_ach.get("viewed", False)
                })

            elif user_ach and user_ach.get("current_progress", 0) > 0:
                # In progress
                progress = AchievementProgress(
                    achievement=achievement,
                    current_progress=user_ach.get("current_progress", 0),
                    requirement_value=achievement.requirement_value,
                    percentage=min(100, (user_ach.get("current_progress", 0) / achievement.requirement_value) * 100),
                    is_completed=False,
                    completed_at=None
                )
                in_progress.append(progress)

            else:
                # Available (not started)
                if not achievement.is_secret:
                    available.append(achievement)

        # Get total points
        user = await self.users_collection.find_one({"user_id": user_id})
        total_points = user.get("social_stats", {}).get("achievement_points", 0) if user else 0

        return UserAchievementsResponse(
            earned=earned,
            in_progress=in_progress,
            available=available,
            total_points=total_points,
            achievements_earned=len(earned),
            achievements_total=len(all_achievements)
        )

    async def mark_viewed(self, user_id: str, achievement_id: str) -> bool:
        """
        Mark an achievement as viewed by the user.

        Args:
            user_id: User ID
            achievement_id: Achievement ID

        Returns:
            True if successful
        """
        result = await self.user_achievements_collection.update_one(
            {
                "user_id": user_id,
                "achievement_id": achievement_id
            },
            {
                "$set": {"viewed": True, "updated_at": datetime.utcnow()}
            }
        )

        return result.modified_count > 0
