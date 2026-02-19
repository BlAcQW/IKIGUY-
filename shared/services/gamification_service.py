"""
Gamification Service.

Provides gamification features including points, levels, leaderboards,
challenges, and rewards to enhance student engagement.

Features:
- Points system (earn points for activities)
- Experience levels with progression
- Leaderboards (organization, course, global)
- Daily/weekly challenges
- Achievement tracking
- Reward redemption
- Streak bonuses

Author: KasaAI
Created: 2025-11-07
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ActivityType(str, Enum):
    """Types of activities that earn points."""
    QUESTION_ASKED = "question_asked"
    ASSESSMENT_COMPLETED = "assessment_completed"
    ASSESSMENT_PASSED = "assessment_passed"
    MODULE_COMPLETED = "module_completed"
    PERFECT_SCORE = "perfect_score"
    DAILY_LOGIN = "daily_login"
    STREAK_MAINTAINED = "streak_maintained"
    VOICE_QUESTION = "voice_question"
    HELPING_PEER = "helping_peer"
    CHALLENGE_COMPLETED = "challenge_completed"


class ChallengeType(str, Enum):
    """Types of challenges."""
    DAILY = "daily"
    WEEKLY = "weekly"
    SPECIAL = "special"


# Points configuration for each activity
POINTS_CONFIG = {
    ActivityType.QUESTION_ASKED: 5,
    ActivityType.ASSESSMENT_COMPLETED: 50,
    ActivityType.ASSESSMENT_PASSED: 100,
    ActivityType.MODULE_COMPLETED: 200,
    ActivityType.PERFECT_SCORE: 150,
    ActivityType.DAILY_LOGIN: 10,
    ActivityType.STREAK_MAINTAINED: 25,
    ActivityType.VOICE_QUESTION: 10,
    ActivityType.HELPING_PEER: 75,
    ActivityType.CHALLENGE_COMPLETED: 100,
}

# Level thresholds (points needed for each level)
LEVEL_THRESHOLDS = [
    0,      # Level 1
    100,    # Level 2
    250,    # Level 3
    500,    # Level 4
    1000,   # Level 5
    2000,   # Level 6
    3500,   # Level 7
    5500,   # Level 8
    8000,   # Level 9
    12000,  # Level 10
    17000,  # Level 11
    23000,  # Level 12
    30000,  # Level 13
    40000,  # Level 14
    50000,  # Level 15
]


class GamificationService:
    """Service for managing gamification features."""

    def __init__(self, db):
        """
        Initialize gamification service.

        Args:
            db: Database connection
        """
        self.db = db

    async def award_points(
        self,
        user_id: str,
        organization_id: str,
        activity_type: ActivityType,
        points: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Award points to a user for an activity.

        Args:
            user_id: User identifier
            organization_id: Organization identifier
            activity_type: Type of activity
            points: Optional custom points (uses default if not provided)
            metadata: Optional activity metadata

        Returns:
            Updated user gamification data with level changes
        """
        # Get points for activity
        points_awarded = points if points is not None else POINTS_CONFIG.get(activity_type, 0)

        # Get user's gamification record
        user_gamification = await self.db["gamification"].find_one({
            "user_id": user_id,
            "organization_id": organization_id
        })

        if not user_gamification:
            # Create new record
            user_gamification = {
                "user_id": user_id,
                "organization_id": organization_id,
                "total_points": 0,
                "current_level": 1,
                "current_streak": 0,
                "longest_streak": 0,
                "last_activity_date": None,
                "activities": [],
                "achievements": [],
                "created_at": datetime.utcnow()
            }

        # Calculate new totals
        old_level = user_gamification.get("current_level", 1)
        new_total_points = user_gamification.get("total_points", 0) + points_awarded
        new_level = self._calculate_level(new_total_points)

        # Check for level up
        level_up = new_level > old_level

        # Record activity
        activity_record = {
            "activity_type": activity_type,
            "points_awarded": points_awarded,
            "timestamp": datetime.utcnow(),
            "metadata": metadata or {}
        }

        # Update user record
        update_data = {
            "$set": {
                "total_points": new_total_points,
                "current_level": new_level,
                "updated_at": datetime.utcnow()
            },
            "$push": {
                "activities": activity_record
            }
        }

        await self.db["gamification"].update_one(
            {"user_id": user_id, "organization_id": organization_id},
            update_data,
            upsert=True
        )

        logger.info(
            f"Awarded {points_awarded} points to user {user_id} for {activity_type}"
            + (f" - LEVEL UP to {new_level}!" if level_up else "")
        )

        return {
            "points_awarded": points_awarded,
            "total_points": new_total_points,
            "current_level": new_level,
            "previous_level": old_level,
            "level_up": level_up,
            "points_to_next_level": self._points_to_next_level(new_total_points)
        }

    def _calculate_level(self, total_points: int) -> int:
        """
        Calculate level based on total points.

        Args:
            total_points: Total points earned

        Returns:
            Current level
        """
        for level, threshold in enumerate(LEVEL_THRESHOLDS, start=1):
            if level == len(LEVEL_THRESHOLDS):
                # Max level
                return level
            if total_points < LEVEL_THRESHOLDS[level]:
                return level

        return len(LEVEL_THRESHOLDS)

    def _points_to_next_level(self, total_points: int) -> int:
        """
        Calculate points needed to reach next level.

        Args:
            total_points: Current total points

        Returns:
            Points needed for next level
        """
        current_level = self._calculate_level(total_points)

        if current_level >= len(LEVEL_THRESHOLDS):
            return 0  # Max level reached

        next_threshold = LEVEL_THRESHOLDS[current_level]
        return next_threshold - total_points

    async def update_streak(
        self,
        user_id: str,
        organization_id: str
    ) -> Dict[str, Any]:
        """
        Update user's daily login streak.

        Args:
            user_id: User identifier
            organization_id: Organization identifier

        Returns:
            Streak information
        """
        user_gamification = await self.db["gamification"].find_one({
            "user_id": user_id,
            "organization_id": organization_id
        })

        if not user_gamification:
            # First login
            await self.award_points(
                user_id,
                organization_id,
                ActivityType.DAILY_LOGIN
            )

            await self.db["gamification"].update_one(
                {"user_id": user_id, "organization_id": organization_id},
                {
                    "$set": {
                        "current_streak": 1,
                        "longest_streak": 1,
                        "last_activity_date": datetime.utcnow().date()
                    }
                },
                upsert=True
            )

            return {
                "current_streak": 1,
                "longest_streak": 1,
                "streak_continued": True
            }

        last_date = user_gamification.get("last_activity_date")
        if isinstance(last_date, datetime):
            last_date = last_date.date()

        today = datetime.utcnow().date()

        if last_date == today:
            # Already logged in today
            return {
                "current_streak": user_gamification.get("current_streak", 1),
                "longest_streak": user_gamification.get("longest_streak", 1),
                "streak_continued": False
            }

        yesterday = today - timedelta(days=1)

        if last_date == yesterday:
            # Streak continues
            new_streak = user_gamification.get("current_streak", 0) + 1
            longest = max(new_streak, user_gamification.get("longest_streak", 0))

            # Award points for streak
            await self.award_points(
                user_id,
                organization_id,
                ActivityType.STREAK_MAINTAINED
            )

            await self.db["gamification"].update_one(
                {"user_id": user_id, "organization_id": organization_id},
                {
                    "$set": {
                        "current_streak": new_streak,
                        "longest_streak": longest,
                        "last_activity_date": today
                    }
                }
            )

            return {
                "current_streak": new_streak,
                "longest_streak": longest,
                "streak_continued": True
            }
        else:
            # Streak broken
            await self.db["gamification"].update_one(
                {"user_id": user_id, "organization_id": organization_id},
                {
                    "$set": {
                        "current_streak": 1,
                        "last_activity_date": today
                    }
                }
            )

            return {
                "current_streak": 1,
                "longest_streak": user_gamification.get("longest_streak", 1),
                "streak_continued": False
            }

    async def get_leaderboard(
        self,
        organization_id: str,
        timeframe: str = "all_time",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get leaderboard for organization.

        Args:
            organization_id: Organization identifier
            timeframe: Timeframe (all_time, month, week)
            limit: Number of users to return

        Returns:
            Leaderboard entries
        """
        # Query for leaderboard
        query = {"organization_id": organization_id}

        # For timeframe filtering, we'd need to aggregate activities
        # Simplified version: all_time leaderboard
        leaderboard = await self.db["gamification"].find(query).sort(
            "total_points", -1
        ).limit(limit).to_list(limit)

        # Get user details
        result = []
        for rank, entry in enumerate(leaderboard, start=1):
            # Get user name from users collection
            user = await self.db["users"].find_one({"_id": entry["user_id"]})
            user_name = user.get("full_name", "Unknown") if user else "Unknown"

            result.append({
                "rank": rank,
                "user_id": entry["user_id"],
                "user_name": user_name,
                "total_points": entry.get("total_points", 0),
                "current_level": entry.get("current_level", 1),
                "current_streak": entry.get("current_streak", 0)
            })

        return result

    async def create_challenge(
        self,
        organization_id: str,
        challenge_type: ChallengeType,
        title: str,
        description: str,
        target: int,
        target_metric: str,
        points_reward: int,
        start_date: datetime,
        end_date: datetime,
        created_by: str
    ) -> Dict[str, Any]:
        """
        Create a challenge for students.

        Args:
            organization_id: Organization identifier
            challenge_type: Type of challenge
            title: Challenge title
            description: Challenge description
            target: Target value to achieve
            target_metric: Metric to track (modules, questions, assessments)
            points_reward: Points awarded on completion
            start_date: Challenge start date
            end_date: Challenge end date
            created_by: Admin/teacher who created challenge

        Returns:
            Challenge record
        """
        challenge = {
            "organization_id": organization_id,
            "challenge_type": challenge_type,
            "title": title,
            "description": description,
            "target": target,
            "target_metric": target_metric,
            "points_reward": points_reward,
            "start_date": start_date,
            "end_date": end_date,
            "created_by": created_by,
            "created_at": datetime.utcnow(),
            "is_active": True,
            "participants": []
        }

        result = await self.db["challenges"].insert_one(challenge)
        challenge["_id"] = str(result.inserted_id)

        logger.info(f"Challenge created: {title} ({challenge_type})")

        return challenge

    async def get_active_challenges(
        self,
        organization_id: str,
        challenge_type: Optional[ChallengeType] = None
    ) -> List[Dict[str, Any]]:
        """
        Get active challenges for organization.

        Args:
            organization_id: Organization identifier
            challenge_type: Optional filter by challenge type

        Returns:
            List of active challenges
        """
        now = datetime.utcnow()

        query = {
            "organization_id": organization_id,
            "is_active": True,
            "start_date": {"$lte": now},
            "end_date": {"$gte": now}
        }

        if challenge_type:
            query["challenge_type"] = challenge_type

        challenges = await self.db["challenges"].find(query).to_list(None)

        return challenges

    async def check_challenge_completion(
        self,
        user_id: str,
        organization_id: str,
        challenge_id: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if user has completed a challenge.

        Args:
            user_id: User identifier
            organization_id: Organization identifier
            challenge_id: Challenge identifier

        Returns:
            Tuple of (completed, progress_data)
        """
        challenge = await self.db["challenges"].find_one({"_id": challenge_id})

        if not challenge:
            return False, {}

        # Check if already completed
        if user_id in challenge.get("participants", []):
            return True, {"already_completed": True}

        # Check progress based on target_metric
        metric = challenge["target_metric"]
        target = challenge["target"]

        # Get user's progress
        # This would query relevant collections based on metric
        # Simplified version:
        progress = 0

        if metric == "modules":
            # Count completed modules
            completed = await self.db["assessment_sessions"].count_documents({
                "user_id": user_id,
                "organization_id": organization_id,
                "status": "completed"
            })
            progress = completed

        elif metric == "questions":
            # Count questions asked
            progress = await self.db["questions"].count_documents({
                "student_id": user_id,
                "organization_id": organization_id
            })

        elif metric == "assessments":
            # Count completed assessments
            progress = await self.db["assessment_sessions"].count_documents({
                "user_id": user_id,
                "organization_id": organization_id,
                "status": "completed"
            })

        completed = progress >= target

        if completed:
            # Award points and mark as completed
            await self.award_points(
                user_id,
                organization_id,
                ActivityType.CHALLENGE_COMPLETED,
                points=challenge["points_reward"]
            )

            await self.db["challenges"].update_one(
                {"_id": challenge_id},
                {"$addToSet": {"participants": user_id}}
            )

            logger.info(f"Challenge completed: {challenge['title']} by user {user_id}")

        return completed, {
            "progress": progress,
            "target": target,
            "percentage": (progress / target * 100) if target > 0 else 0
        }

    async def get_user_stats(
        self,
        user_id: str,
        organization_id: str
    ) -> Dict[str, Any]:
        """
        Get comprehensive gamification stats for user.

        Args:
            user_id: User identifier
            organization_id: Organization identifier

        Returns:
            User gamification statistics
        """
        user_gamification = await self.db["gamification"].find_one({
            "user_id": user_id,
            "organization_id": organization_id
        })

        if not user_gamification:
            return {
                "total_points": 0,
                "current_level": 1,
                "current_streak": 0,
                "longest_streak": 0,
                "points_to_next_level": LEVEL_THRESHOLDS[1],
                "recent_activities": []
            }

        total_points = user_gamification.get("total_points", 0)

        return {
            "total_points": total_points,
            "current_level": user_gamification.get("current_level", 1),
            "current_streak": user_gamification.get("current_streak", 0),
            "longest_streak": user_gamification.get("longest_streak", 0),
            "points_to_next_level": self._points_to_next_level(total_points),
            "recent_activities": user_gamification.get("activities", [])[-10:]  # Last 10
        }
