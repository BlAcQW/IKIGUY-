"""
Community management service for African Language Community Platform.

Handles leaderboards, achievements, gamification, and community statistics.
"""

from typing import List, Optional, Dict, Any
from bson import ObjectId
from datetime import datetime, timedelta
import logging

from models.user_models import User, UserLevel
from models.community_models import (
    Achievement, Badge, Leaderboard, CommunityStats, LeaderboardEntry
)
from database import get_database

logger = logging.getLogger(__name__)


class CommunityService:
    """
    Service for managing community features and gamification.

    Handles achievements, badges, leaderboards, and community statistics.
    """

    def __init__(self):
        """Initialize community service."""
        pass

    async def _get_db(self):
        """Get database connection - always fresh to support test fixtures."""
        # Always call get_database() fresh to support test database patching
        return get_database()

    async def get_leaderboard(
        self,
        category: str = "total_points",
        language_id: Optional[str] = None,
        timeframe: str = "all_time",
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get community leaderboard.

        Args:
            category: Leaderboard category (total_points, contributions, validations, etc.)
            language_id: Optional language ID to filter by
            timeframe: Time frame (all_time, monthly, weekly)
            limit: Maximum number of entries to return

        Returns:
            List[Dict]: Leaderboard entries
        """
        try:
            db = await self._get_db()

            pipeline = []

            # Match filters
            match_conditions = {"is_active": True}
            if language_id:
                # language_id is actually a language code (e.g., 'twi'), not ObjectId
                # First, look up the language to get its ObjectId
                language_doc = await db.languages.find_one({"code": language_id})
                if language_doc:
                    # Filter users who have contributed to specific language
                    match_conditions["verified_languages"] = language_doc["_id"]
                else:
                    # If language not found, use the code as-is in case stored as string
                    match_conditions["verified_languages"] = language_id

            pipeline.append({"$match": match_conditions})

            # Sort by category
            sort_field = category
            if category == "contributions":
                sort_field = "contributions_count"
            elif category == "validations":
                sort_field = "validations_count"
            elif category == "reputation":
                sort_field = "reputation_score"
            elif category == "quality":
                sort_field = "quality_rating"

            pipeline.extend([
                {"$sort": {sort_field: -1}},
                {"$limit": limit},
                {
                    "$project": {
                        "_id": 0,  # Exclude _id to avoid serialization issues
                        "user_id": {"$toString": "$_id"},  # Convert ObjectId to string
                        "username": 1,
                        "full_name": 1,
                        "avatar_url": 1,
                        "level": 1,
                        "total_points": 1,
                        "contributions_count": 1,
                        "validations_count": 1,
                        "quality_rating": 1,
                        "reputation_score": 1,
                        "verified_languages_count": {"$size": {"$ifNull": ["$verified_languages", []]}},
                        "badges_count": {"$size": {"$ifNull": ["$badges", []]}},
                        "achievements_count": {"$size": {"$ifNull": ["$achievements", []]}}
                    }
                }
            ])

            leaderboard = await db.users.aggregate(pipeline).to_list(length=None)

            # Add rank to each entry
            for i, entry in enumerate(leaderboard):
                entry["rank"] = i + 1
                entry["score"] = entry.get(sort_field, 0)

            return leaderboard

        except Exception as e:
            logger.error(f"Failed to get leaderboard: {str(e)}")
            raise

    async def get_community_statistics(
        self,
        language_id: Optional[str] = None
    ) -> CommunityStats:
        """
        Get community statistics.

        Args:
            language_id: Optional language ID for language-specific stats

        Returns:
            CommunityStats: Community statistics
        """
        try:
            db = await self._get_db()

            # Base match conditions
            match_conditions = {}
            if language_id:
                match_conditions["language_id"] = ObjectId(language_id)

            # Get user statistics
            user_pipeline = [
                {"$match": {"is_active": True}},
                {
                    "$group": {
                        "_id": None,
                        "total_users": {"$sum": 1},
                        "active_users": {
                            "$sum": {
                                "$cond": [
                                    {"$gte": ["$last_activity", datetime.utcnow() - timedelta(days=30)]},
                                    1,
                                    0
                                ]
                            }
                        },
                        "total_contributions": {"$sum": "$contributions_count"},
                        "total_validations": {"$sum": "$validations_count"}
                    }
                }
            ]

            user_stats = await db.users.aggregate(user_pipeline).to_list(length=None)
            user_stats = user_stats[0] if user_stats else {}

            # Get submission statistics
            submission_pipeline = []
            if match_conditions:
                submission_pipeline.append({"$match": match_conditions})

            submission_pipeline.append({
                "$group": {
                    "_id": None,
                    "total": {"$sum": 1},
                    "pending": {
                        "$sum": {
                            "$cond": [{"$eq": ["$validation_status", "pending"]}, 1, 0]
                        }
                    },
                    "validated": {
                        "$sum": {
                            "$cond": [{"$eq": ["$validation_status", "validated"]}, 1, 0]
                        }
                    },
                    "gold_standard": {
                        "$sum": {
                            "$cond": [{"$eq": ["$tier", "tier-1-validated"]}, 1, 0]
                        }
                    },
                    "by_type": {
                        "$push": {
                            "type": "$type",
                            "count": 1
                        }
                    }
                }
            })

            submission_stats = await db.submissions.aggregate(submission_pipeline).to_list(length=None)
            submission_stats = submission_stats[0] if submission_stats else {}

            # Get language statistics
            language_pipeline = []
            if language_id:
                language_pipeline.append({"$match": {"_id": ObjectId(language_id)}})

            language_pipeline.append({
                "$group": {
                    "_id": None,
                    "total_languages": {"$sum": 1},
                    "active_languages": {
                        "$sum": {
                            "$cond": [{"$gt": ["$submission_count", 0]}, 1, 0]
                        }
                    }
                }
            })

            language_stats = await db.languages.aggregate(language_pipeline).to_list(length=None)
            language_stats = language_stats[0] if language_stats else {}

            return CommunityStats(
                total_users=user_stats.get("total_users", 0),
                active_users=user_stats.get("active_users", 0),
                total_contributions=user_stats.get("total_contributions", 0),
                total_validations=user_stats.get("total_validations", 0),
                total_languages=language_stats.get("total_languages", 0),
                active_languages=language_stats.get("active_languages", 0),
                text_submissions=submission_stats.get("total", 0),
                audio_submissions=0,  # Will be calculated from by_type if needed
                translation_submissions=0,  # Will be calculated from by_type if needed
                gold_standard_submissions=submission_stats.get("gold_standard", 0),
                pending_submissions=submission_stats.get("pending", 0)
            )

        except Exception as e:
            logger.error(f"Failed to get community statistics: {str(e)}")
            raise

    async def award_achievement(
        self,
        user_id: ObjectId,
        achievement_type: str,
        description: str
    ) -> bool:
        """
        Award achievement to user.

        Args:
            user_id: User ID
            achievement_type: Type of achievement
            description: Achievement description

        Returns:
            bool: True if achievement awarded
        """
        try:
            db = await self._get_db()

            # Check if user already has this achievement
            user = await db.users.find_one({"_id": user_id})
            if not user:
                return False

            achievements = user.get("achievements", [])
            for achievement in achievements:
                if achievement.get("type") == achievement_type:
                    return False  # Already has this achievement

            # Add achievement
            new_achievement = {
                "type": achievement_type,
                "description": description,
                "earned_at": datetime.utcnow()
            }

            await db.users.update_one(
                {"_id": user_id},
                {
                    "$push": {"achievements": new_achievement},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )

            return True

        except Exception as e:
            logger.error(f"Failed to award achievement: {str(e)}")
            return False

    async def award_badge(
        self,
        user_id: ObjectId,
        badge_type: str,
        description: str,
        icon_url: str
    ) -> bool:
        """
        Award badge to user.

        Args:
            user_id: User ID
            badge_type: Type of badge
            description: Badge description
            icon_url: Badge icon URL

        Returns:
            bool: True if badge awarded
        """
        try:
            db = await self._get_db()

            # Check if user already has this badge
            user = await db.users.find_one({"_id": user_id})
            if not user:
                return False

            badges = user.get("badges", [])
            for badge in badges:
                if badge.get("type") == badge_type:
                    return False  # Already has this badge

            # Add badge
            new_badge = {
                "type": badge_type,
                "description": description,
                "icon_url": icon_url,
                "earned_at": datetime.utcnow()
            }

            await db.users.update_one(
                {"_id": user_id},
                {
                    "$push": {"badges": new_badge},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )

            return True

        except Exception as e:
            logger.error(f"Failed to award badge: {str(e)}")
            return False

    async def update_user_points(
        self,
        user_id: ObjectId,
        points_to_add: int,
        activity_type: str
    ) -> bool:
        """
        Update user points and check for level progression.

        Args:
            user_id: User ID
            points_to_add: Points to add
            activity_type: Type of activity that earned points

        Returns:
            bool: True if update successful
        """
        try:
            db = await self._get_db()

            user = await db.users.find_one({"_id": user_id})
            if not user:
                return False

            current_total = user.get("total_points", 0)
            current_level_points = user.get("level_points", 0)
            current_level = user.get("level", UserLevel.NEWCOMER)

            new_total = current_total + points_to_add
            new_level_points = current_level_points + points_to_add

            # Check for level progression
            new_level = self._calculate_user_level(new_total)

            # Reset level points if level changed
            if new_level != current_level:
                new_level_points = new_total - self._get_level_threshold(new_level)

            # Update user
            await db.users.update_one(
                {"_id": user_id},
                {
                    "$set": {
                        "total_points": new_total,
                        "level_points": new_level_points,
                        "level": new_level,
                        "updated_at": datetime.utcnow()
                    }
                }
            )

            # Award level progression achievement if level changed
            if new_level != current_level:
                await self.award_achievement(
                    user_id,
                    f"level_{new_level.lower()}",
                    f"Reached {new_level.title()} level"
                )

            return True

        except Exception as e:
            logger.error(f"Failed to update user points: {str(e)}")
            return False

    def _calculate_user_level(self, total_points: int) -> UserLevel:
        """Calculate user level based on total points."""
        if total_points >= 10000:
            return UserLevel.EXPERT
        elif total_points >= 5000:
            return UserLevel.VALIDATOR
        elif total_points >= 2000:
            return UserLevel.TRUSTED_CONTRIBUTOR
        elif total_points >= 500:
            return UserLevel.CONTRIBUTOR
        else:
            return UserLevel.NEWCOMER

    def _get_level_threshold(self, level: UserLevel) -> int:
        """Get minimum points threshold for a level."""
        thresholds = {
            UserLevel.NEWCOMER: 0,
            UserLevel.CONTRIBUTOR: 500,
            UserLevel.TRUSTED_CONTRIBUTOR: 2000,
            UserLevel.VALIDATOR: 5000,
            UserLevel.EXPERT: 10000
        }
        return thresholds.get(level, 0)

    async def get_recent_community_activity(
        self,
        limit: int = 50,
        language_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent community activity.

        Args:
            limit: Maximum number of activities to return
            language_id: Optional language ID filter

        Returns:
            List[Dict]: Recent community activities
        """
        try:
            db = await self._get_db()

            activities = []

            # Get recent submissions
            match_conditions = {}
            if language_id:
                match_conditions["language_code"] = language_id

            submissions = await db.submissions.find(match_conditions)\
                .sort("created_at", -1).limit(limit).to_list(length=None)

            for submission in submissions:
                activities.append({
                    "type": "submission",
                    "subtype": submission.get("type", "unknown"),
                    "user_id": submission["contributor_id"],
                    "created_at": submission["created_at"],
                    "data": submission
                })

            # Get recent validations
            validations = await db.validations.find()\
                .sort("created_at", -1).limit(limit).to_list(length=None)

            for validation in validations:
                activities.append({
                    "type": "validation",
                    "user_id": validation["validator_id"],
                    "created_at": validation["created_at"],
                    "data": validation
                })

            # Sort all activities by creation date
            activities.sort(key=lambda x: x["created_at"], reverse=True)

            return activities[:limit]

        except Exception as e:
            logger.error(f"Failed to get recent activity: {str(e)}")
            raise

    async def get_all_achievements(self) -> Dict[str, Any]:
        """
        Get all available achievements with their requirements.

        Returns:
            Dict: Dictionary containing list of achievements
        """
        try:
            db = await self._get_db()

            achievements = await db.achievements.find().to_list(length=None)

            # Convert ObjectIds to strings for JSON serialization
            for achievement in achievements:
                achievement["_id"] = str(achievement["_id"])

            return {"achievements": achievements}

        except Exception as e:
            logger.error(f"Failed to get all achievements: {str(e)}")
            raise

    async def get_user_achievements(self, user_id: str) -> Dict[str, Any]:
        """
        Get user's earned achievements and progress.

        Args:
            user_id: User ID

        Returns:
            Dict: User achievements and progress
        """
        try:
            db = await self._get_db()

            user = await db.users.find_one({"_id": ObjectId(user_id)})
            if not user:
                return {"earned": [], "progress": []}

            earned = user.get("achievements", [])

            # Get all achievements to show progress
            all_achievements = await db.achievements.find().to_list(length=None)
            earned_types = {a.get("type") for a in earned}

            progress = []
            for achievement in all_achievements:
                if achievement.get("code") not in earned_types:
                    progress.append({
                        "code": achievement.get("code"),
                        "name": achievement.get("name"),
                        "description": achievement.get("description"),
                        "progress_percent": 0  # Could calculate based on criteria
                    })

            return {
                "earned": earned,
                "progress": progress
            }

        except Exception as e:
            logger.error(f"Failed to get user achievements: {str(e)}")
            raise

    async def get_engagement_statistics(self) -> Dict[str, Any]:
        """
        Get community engagement statistics.

        Returns:
            Dict: Engagement statistics
        """
        try:
            db = await self._get_db()

            # Get user activity stats
            total_users = await db.users.count_documents({"is_active": True})

            # Active users in last 7 days
            week_ago = datetime.utcnow() - timedelta(days=7)
            active_users = await db.users.count_documents({
                "last_activity": {"$gte": week_ago}
            })

            # Submission stats
            total_submissions = await db.submissions.count_documents({})
            submissions_this_week = await db.submissions.count_documents({
                "created_at": {"$gte": week_ago}
            })

            # Validation stats
            total_validations = await db.validations.count_documents({})
            validations_this_week = await db.validations.count_documents({
                "created_at": {"$gte": week_ago}
            })

            return {
                "total_users": total_users,
                "active_users_week": active_users,
                "total_submissions": total_submissions,
                "submissions_this_week": submissions_this_week,
                "total_validations": total_validations,
                "validations_this_week": validations_this_week,
                "engagement_rate": round(active_users / max(total_users, 1) * 100, 2)
            }

        except Exception as e:
            logger.error(f"Failed to get engagement statistics: {str(e)}")
            raise

    async def get_activity_feed(
        self,
        language_family: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Get community activity feed with pagination.

        Args:
            language_family: Optional language family filter
            page: Page number
            page_size: Items per page

        Returns:
            Tuple: (activities list, total count)
        """
        try:
            db = await self._get_db()

            match_conditions = {}
            if language_family:
                match_conditions["language_family"] = language_family

            # Get total count
            total_count = await db.activity_feed.count_documents(match_conditions)

            # Get paginated activities
            skip = (page - 1) * page_size
            activities = await db.activity_feed.find(match_conditions)\
                .sort("created_at", -1)\
                .skip(skip)\
                .limit(page_size)\
                .to_list(length=None)

            # Convert ObjectIds to strings
            for activity in activities:
                activity["_id"] = str(activity["_id"])

            return activities, total_count

        except Exception as e:
            logger.error(f"Failed to get activity feed: {str(e)}")
            raise

    async def create_proposal(
        self,
        proposer_id: str,
        proposal_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new community proposal.

        Args:
            proposer_id: ID of user creating the proposal
            proposal_data: Proposal information

        Returns:
            Dict: Created proposal
        """
        try:
            db = await self._get_db()

            proposal_doc = {
                "_id": ObjectId(),
                "proposer_id": proposer_id,
                "title": proposal_data.get("title"),
                "description": proposal_data.get("description"),
                "proposal_type": proposal_data.get("proposal_type", "general"),
                "details": proposal_data.get("details", {}),
                "status": "active",
                "votes_for": 0,
                "votes_against": 0,
                "voters": [],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "voting_deadline": datetime.utcnow() + timedelta(days=7)
            }

            await db.community_proposals.insert_one(proposal_doc)

            # Convert ObjectId and datetime to string for response
            proposal_doc["_id"] = str(proposal_doc["_id"])
            proposal_doc["proposer_id"] = str(proposal_doc["proposer_id"])
            proposal_doc["created_at"] = proposal_doc["created_at"].isoformat()
            proposal_doc["updated_at"] = proposal_doc["updated_at"].isoformat()
            proposal_doc["voting_deadline"] = proposal_doc["voting_deadline"].isoformat()
            return proposal_doc

        except Exception as e:
            logger.error(f"Failed to create proposal: {str(e)}")
            raise

    async def get_proposals(
        self,
        status_filter: str = "active",
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Get community proposals with pagination.

        Args:
            status_filter: Filter by status
            page: Page number
            page_size: Items per page

        Returns:
            Tuple: (proposals list, total count)
        """
        try:
            db = await self._get_db()

            match_conditions = {"status": status_filter}

            total_count = await db.community_proposals.count_documents(match_conditions)

            skip = (page - 1) * page_size
            proposals = await db.community_proposals.find(match_conditions)\
                .sort("created_at", -1)\
                .skip(skip)\
                .limit(page_size)\
                .to_list(length=None)

            # Convert ObjectIds to strings
            for proposal in proposals:
                proposal["_id"] = str(proposal["_id"])

            return proposals, total_count

        except Exception as e:
            logger.error(f"Failed to get proposals: {str(e)}")
            raise

    async def can_user_vote(self, user_id: str, proposal_id: str) -> bool:
        """
        Check if user can vote on a proposal.

        Args:
            user_id: User ID
            proposal_id: Proposal ID

        Returns:
            bool: True if user can vote
        """
        try:
            db = await self._get_db()

            proposal = await db.community_proposals.find_one({
                "_id": ObjectId(proposal_id)
            })

            if not proposal:
                return False

            # Check if proposal is still active
            if proposal.get("status") != "active":
                return False

            # Check if voting deadline has passed
            if proposal.get("voting_deadline") and proposal["voting_deadline"] < datetime.utcnow():
                return False

            # Check if user has already voted
            voters = proposal.get("voters", [])
            if user_id in voters:
                return False

            return True

        except Exception as e:
            logger.error(f"Failed to check voting eligibility: {str(e)}")
            return False

    async def cast_vote(
        self,
        proposal_id: str,
        voter_id: str,
        vote_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Cast a vote on a proposal.

        Args:
            proposal_id: Proposal ID
            voter_id: Voter's user ID
            vote_data: Vote information (vote: "for" or "against")

        Returns:
            Dict: Updated proposal vote counts
        """
        try:
            db = await self._get_db()

            vote = vote_data.get("vote", "for")
            vote_field = "votes_for" if vote == "for" else "votes_against"

            result = await db.community_proposals.find_one_and_update(
                {"_id": ObjectId(proposal_id)},
                {
                    "$inc": {vote_field: 1},
                    "$push": {"voters": voter_id},
                    "$set": {"updated_at": datetime.utcnow()}
                },
                return_document=True
            )

            if result:
                result["_id"] = str(result["_id"])
                return {
                    "proposal_id": str(result["_id"]),
                    "votes_for": result.get("votes_for", 0),
                    "votes_against": result.get("votes_against", 0),
                    "voted": vote
                }

            raise ValueError("Proposal not found")

        except Exception as e:
            logger.error(f"Failed to cast vote: {str(e)}")
            raise