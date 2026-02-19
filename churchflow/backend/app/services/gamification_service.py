"""
Core Gamification Service.

Handles all gamification logic including points, levels, streaks, and badges
for member engagement and consistent attendance tracking.
"""

from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import asyncio

from app.services.gamification_points_service import (
    POINT_RULES,
    calculate_level_from_points,
    calculate_points_to_next_level,
    get_level_tier
)


class GamificationService:
    """
    Core service for gamification features.

    Manages user profiles, points, levels, streaks, and badges to encourage
    consistent attendance and member engagement.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize gamification service.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.profiles_collection = db.gamification_profiles
        self.badges_collection = db.gamification_badges
        self.challenges_collection = db.gamification_challenges
        self.attendance_collection = db.session_attendance


    # ============================================================================
    # PROFILE MANAGEMENT
    # ============================================================================

    async def get_or_create_profile(
        self,
        user_id: str,
        organization_id: str
    ) -> Dict:
        """
        Get existing gamification profile or create new one.

        Args:
            user_id: User ID
            organization_id: Organization ID

        Returns:
            Gamification profile document
        """
        user_oid = ObjectId(user_id)
        org_oid = ObjectId(organization_id)

        # Try to find existing profile
        profile = await self.profiles_collection.find_one({
            "user_id": user_oid,
            "organization_id": org_oid
        })

        if profile:
            return profile

        # Create new profile
        new_profile = {
            "user_id": user_oid,
            "organization_id": org_oid,

            # Points & Levels
            "total_points": 0,
            "current_level": 1,
            "level_tier": "bronze",
            "points_to_next_level": 100,

            # Streaks
            "current_streak": 0,
            "longest_streak": 0,
            "last_attendance_week": None,  # ISO week (e.g., "2025-W49")
            "streak_freeze_available": True,
            "streak_freeze_used_at": None,

            # Badges
            "badges_earned": [],  # [{badge_id, name, earned_at, icon_emoji}]
            "badges_in_progress": [],  # [{badge_id, progress, target}]

            # Statistics
            "total_services_attended": 0,
            "total_volunteer_hours": 0.0,
            "total_donations_count": 0,
            "visitors_brought": 0,
            "total_conferences_attended": 0,
            "branches_visited": [],  # List of branch ObjectIds

            # Preferences
            "leaderboard_visible": True,
            "display_name": None,  # Uses user's name by default
            "notification_preferences": {
                "level_up": True,
                "badge_earned": True,
                "streak_reminder": True,
                "challenge_invitation": True,
                "weekly_summary": True
            },

            # Point history (for transparency)
            "points_history": [],  # [{action, points, date, reference_id}]

            # Metadata
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        result = await self.profiles_collection.insert_one(new_profile)
        new_profile["_id"] = result.inserted_id

        return new_profile


    async def get_profile(
        self,
        user_id: str,
        organization_id: str
    ) -> Optional[Dict]:
        """
        Get gamification profile without creating if doesn't exist.

        Args:
            user_id: User ID
            organization_id: Organization ID

        Returns:
            Profile document or None
        """
        return await self.profiles_collection.find_one({
            "user_id": ObjectId(user_id),
            "organization_id": ObjectId(organization_id)
        })


    # ============================================================================
    # POINTS & LEVELS
    # ============================================================================

    async def award_points(
        self,
        user_id: str,
        organization_id: str,
        points: int,
        action: str,
        reference_id: str,
        reference_type: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Award points to user and check for level ups.

        Args:
            user_id: User ID
            organization_id: Organization ID
            points: Number of points to award
            action: Action type (e.g., "attend_service", "donation_made")
            reference_id: ID of related entity
            reference_type: Type of reference ("attendance", "donation", etc.)
            metadata: Optional additional data

        Returns:
            {
                "points_awarded": int,
                "new_total": int,
                "level_up": bool,
                "new_level": int,
                "new_tier": str,
                "badges_unlocked": List[str]
            }
        """
        # Get or create profile
        profile = await self.get_or_create_profile(user_id, organization_id)

        # Calculate new points
        old_total = profile["total_points"]
        new_total = old_total + points
        old_level = profile["current_level"]

        # Calculate new level
        new_level = calculate_level_from_points(new_total)
        level_up = new_level > old_level
        new_tier = get_level_tier(new_level)
        points_to_next = calculate_points_to_next_level(new_total)

        # Add to points history
        points_entry = {
            "action": action,
            "points": points,
            "date": datetime.utcnow(),
            "reference_id": reference_id,
            "reference_type": reference_type,
            "metadata": metadata or {}
        }

        # Update profile
        update_doc = {
            "$set": {
                "total_points": new_total,
                "current_level": new_level,
                "level_tier": new_tier,
                "points_to_next_level": points_to_next,
                "updated_at": datetime.utcnow()
            },
            "$push": {
                "points_history": {
                    "$each": [points_entry],
                    "$slice": -100  # Keep last 100 entries
                }
            }
        }

        await self.profiles_collection.update_one(
            {"_id": profile["_id"]},
            update_doc
        )

        # Check for newly unlocked badges
        badges_unlocked = await self.check_badge_eligibility(user_id, organization_id)

        # TODO: Send notifications for level up and badges
        # if level_up:
        #     await notification_service.send_level_up(user_id, new_level)
        # for badge_id in badges_unlocked:
        #     await notification_service.send_badge_earned(user_id, badge_id)

        return {
            "points_awarded": points,
            "new_total": new_total,
            "level_up": level_up,
            "old_level": old_level,
            "new_level": new_level,
            "new_tier": new_tier,
            "points_to_next_level": points_to_next,
            "badges_unlocked": badges_unlocked
        }


    async def award_attendance_points(
        self,
        user_id: str,
        organization_id: str,
        attendance_id: str,
        service_type: str
    ) -> Dict:
        """
        Award points for service attendance.

        Args:
            user_id: User ID
            organization_id: Organization ID
            attendance_id: Attendance record ID
            service_type: Type of service attended

        Returns:
            Points award result
        """
        # Determine points based on service type
        point_map = {
            "sunday_morning": "attend_service",
            "sunday_evening": "attend_service",
            "midweek_service": "attend_midweek",
            "conference": "attend_conference",
            "special_event": "attend_service"
        }

        action_key = point_map.get(service_type, "attend_service")
        points = POINT_RULES.get(action_key, 10)

        # Award points
        result = await self.award_points(
            user_id=user_id,
            organization_id=organization_id,
            points=points,
            action=action_key,
            reference_id=attendance_id,
            reference_type="attendance",
            metadata={"service_type": service_type}
        )

        # Update attendance statistics
        increment_field = "total_services_attended"
        if service_type == "conference":
            increment_field = "total_conferences_attended"

        await self.profiles_collection.update_one(
            {"user_id": ObjectId(user_id), "organization_id": ObjectId(organization_id)},
            {
                "$inc": {increment_field: 1},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

        return result


    # ============================================================================
    # STREAK CALCULATION
    # ============================================================================

    async def calculate_streak(
        self,
        user_id: str,
        organization_id: str
    ) -> Dict:
        """
        Calculate attendance streak from session_attendance records.

        Streak logic:
        - Count consecutive weeks with at least 1 attendance
        - Week defined as Sunday to Saturday (ISO week)
        - Streak resets if a week is missed (unless freeze used)

        Args:
            user_id: User ID
            organization_id: Organization ID

        Returns:
            {
                "current_streak": int,
                "longest_streak": int,
                "last_attendance_week": str,
                "milestone_badges_earned": List[str],
                "streak_broken": bool
            }
        """
        user_oid = ObjectId(user_id)
        org_oid = ObjectId(organization_id)

        # Get current profile
        profile = await self.get_or_create_profile(user_id, organization_id)

        # Fetch all attendance records, sorted by date
        cursor = self.attendance_collection.find({
            "user_id": user_oid,
            "organization_id": org_oid,
            "checked_in_at": {"$exists": True}
        }).sort("checked_in_at", -1)

        attendance_records = await cursor.to_list(length=None)

        if not attendance_records:
            # No attendance yet
            return {
                "current_streak": 0,
                "longest_streak": 0,
                "last_attendance_week": None,
                "milestone_badges_earned": [],
                "streak_broken": False
            }

        # Group by ISO week
        weeks_attended = set()
        for record in attendance_records:
            checked_in_at = record.get("checked_in_at")
            if checked_in_at:
                iso_week = checked_in_at.isocalendar()
                week_str = f"{iso_week[0]}-W{iso_week[1]:02d}"
                weeks_attended.add(week_str)

        # Sort weeks
        weeks_sorted = sorted(list(weeks_attended), reverse=True)

        # Calculate current streak
        current_week = datetime.utcnow().isocalendar()
        current_week_str = f"{current_week[0]}-W{current_week[1]:02d}"

        streak = 0
        for week_str in weeks_sorted:
            expected_week = self._subtract_weeks(current_week_str, streak)

            if week_str == expected_week:
                streak += 1
            else:
                break

        # Check if streak was broken
        old_streak = profile.get("current_streak", 0)
        streak_broken = streak < old_streak and old_streak > 0

        # Update longest streak
        longest_streak = max(profile.get("longest_streak", 0), streak)

        # Update profile
        await self.profiles_collection.update_one(
            {"_id": profile["_id"]},
            {
                "$set": {
                    "current_streak": streak,
                    "longest_streak": longest_streak,
                    "last_attendance_week": weeks_sorted[0] if weeks_sorted else None,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        # Check for streak milestone badges
        milestone_badges = await self._check_streak_milestones(
            user_id,
            organization_id,
            streak
        )

        return {
            "current_streak": streak,
            "longest_streak": longest_streak,
            "last_attendance_week": weeks_sorted[0] if weeks_sorted else None,
            "milestone_badges_earned": milestone_badges,
            "streak_broken": streak_broken
        }


    def _subtract_weeks(self, week_str: str, num_weeks: int) -> str:
        """
        Subtract weeks from ISO week string.

        Args:
            week_str: ISO week string (e.g., "2025-W49")
            num_weeks: Number of weeks to subtract

        Returns:
            New ISO week string
        """
        year, week = week_str.split('-W')
        year = int(year)
        week = int(week)

        # Simple approximation (doesn't handle year boundaries perfectly)
        new_week = week - num_weeks
        new_year = year

        while new_week < 1:
            new_year -= 1
            new_week += 52  # Approximate

        return f"{new_year}-W{new_week:02d}"


    async def _check_streak_milestones(
        self,
        user_id: str,
        organization_id: str,
        streak: int
    ) -> List[str]:
        """
        Check if streak has reached milestone and award badges.

        Args:
            user_id: User ID
            organization_id: Organization ID
            streak: Current streak count

        Returns:
            List of badge IDs awarded
        """
        milestones = {
            4: "streak_4w",
            8: "streak_8w",
            13: "streak_13w",
            26: "streak_26w",
            52: "streak_52w"
        }

        badges_earned = []

        for weeks, badge_id in milestones.items():
            if streak >= weeks:
                # Check if badge already earned
                profile = await self.get_profile(user_id, organization_id)
                badge_ids = [b["badge_id"] for b in profile.get("badges_earned", [])]

                if badge_id not in badge_ids:
                    # Award badge
                    badge_doc = await self.badges_collection.find_one({"badge_id": badge_id})
                    if badge_doc:
                        await self._award_badge(user_id, organization_id, badge_doc)
                        badges_earned.append(badge_id)

        return badges_earned


    # ============================================================================
    # BADGE MANAGEMENT
    # ============================================================================

    async def check_badge_eligibility(
        self,
        user_id: str,
        organization_id: str
    ) -> List[str]:
        """
        Check all badges user qualifies for but hasn't earned yet.

        Args:
            user_id: User ID
            organization_id: Organization ID

        Returns:
            List of newly earned badge IDs
        """
        profile = await self.get_or_create_profile(user_id, organization_id)

        # Get already earned badges
        earned_badge_ids = [b["badge_id"] for b in profile.get("badges_earned", [])]

        # Get all badge definitions
        cursor = self.badges_collection.find({
            "organization_id": ObjectId(organization_id),
            "badge_id": {"$nin": earned_badge_ids}
        })

        available_badges = await cursor.to_list(length=None)

        newly_earned = []

        for badge in available_badges:
            if await self._check_badge_requirement(profile, badge):
                await self._award_badge(user_id, organization_id, badge)
                newly_earned.append(badge["badge_id"])

        return newly_earned


    async def _check_badge_requirement(
        self,
        profile: Dict,
        badge: Dict
    ) -> bool:
        """
        Check if user meets badge requirement.

        Args:
            profile: User gamification profile
            badge: Badge definition document

        Returns:
            True if requirement met
        """
        req_type = badge.get("requirement_type")
        req_field = badge.get("requirement_field")
        req_value = badge.get("requirement_value")

        if req_type == "count":
            # Simple count comparison
            current_value = profile.get(req_field, 0)
            return current_value >= req_value

        elif req_type == "streak":
            # Streak requirement
            current_streak = profile.get("current_streak", 0)
            return current_streak >= req_value

        elif req_type == "level":
            # Level requirement
            current_level = profile.get("current_level", 1)
            return current_level >= req_value

        elif req_type == "custom":
            # Custom requirement (implement specific logic)
            # For now, return False
            return False

        return False


    async def _award_badge(
        self,
        user_id: str,
        organization_id: str,
        badge: Dict
    ) -> None:
        """
        Award badge to user.

        Args:
            user_id: User ID
            organization_id: Organization ID
            badge: Badge definition document
        """
        earned_badge = {
            "badge_id": badge["badge_id"],
            "name": badge["name"],
            "earned_at": datetime.utcnow(),
            "icon_emoji": badge.get("icon_emoji", "🏆"),
            "tier": badge.get("tier", "bronze")
        }

        await self.profiles_collection.update_one(
            {
                "user_id": ObjectId(user_id),
                "organization_id": ObjectId(organization_id)
            },
            {
                "$push": {"badges_earned": earned_badge},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

        # Award bonus points for badge
        bonus_points = badge.get("points_reward", 0)
        if bonus_points > 0:
            await self.award_points(
                user_id=user_id,
                organization_id=organization_id,
                points=bonus_points,
                action="badge_earned",
                reference_id=badge["badge_id"],
                reference_type="badge",
                metadata={"badge_name": badge["name"]}
            )


    # ============================================================================
    # STATISTICS & QUERIES
    # ============================================================================

    async def get_profile_summary(
        self,
        user_id: str,
        organization_id: str
    ) -> Dict:
        """
        Get comprehensive profile summary for user.

        Args:
            user_id: User ID
            organization_id: Organization ID

        Returns:
            Profile summary with all stats
        """
        profile = await self.get_or_create_profile(user_id, organization_id)

        return {
            "user_id": str(profile["user_id"]),
            "total_points": profile["total_points"],
            "current_level": profile["current_level"],
            "level_tier": profile["level_tier"],
            "points_to_next_level": profile["points_to_next_level"],
            "current_streak": profile["current_streak"],
            "longest_streak": profile["longest_streak"],
            "badges_earned_count": len(profile.get("badges_earned", [])),
            "badges_earned": profile.get("badges_earned", []),
            "total_services_attended": profile["total_services_attended"],
            "total_volunteer_hours": profile["total_volunteer_hours"],
            "total_donations_count": profile["total_donations_count"],
            "visitors_brought": profile["visitors_brought"],
            "leaderboard_visible": profile["leaderboard_visible"],
            "created_at": profile["created_at"],
            "updated_at": profile["updated_at"]
        }


    async def get_points_history(
        self,
        user_id: str,
        organization_id: str,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get recent points history for user.

        Args:
            user_id: User ID
            organization_id: Organization ID
            limit: Maximum number of entries

        Returns:
            List of point transactions
        """
        profile = await self.get_profile(user_id, organization_id)

        if not profile:
            return []

        history = profile.get("points_history", [])

        # Return most recent entries
        return list(reversed(history))[:limit]


# Global service instance (will be initialized with database)
gamification_service: Optional[GamificationService] = None


def get_gamification_service(db: AsyncIOMotorDatabase) -> GamificationService:
    """
    Get or create gamification service instance.

    Args:
        db: MongoDB database instance

    Returns:
        GamificationService instance
    """
    global gamification_service

    if gamification_service is None:
        gamification_service = GamificationService(db)

    return gamification_service
