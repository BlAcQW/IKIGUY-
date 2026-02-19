"""
Gamification Challenges Service

Manages time-bound challenges for individual members and teams.
Tracks participation, progress, and rewards completion.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.gamification import (
    GamificationChallenge,
    ChallengeParticipant,
    ChallengeType,
    ChallengeStatus
)
from app.services.gamification_service import get_gamification_service


class GamificationChallengesService:
    """
    Service for managing gamification challenges.

    Handles:
    - Creating challenges
    - Joining/leaving challenges
    - Tracking progress
    - Determining winners
    - Awarding completion rewards
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.challenges_collection = db.gamification_challenges

    async def create_challenge(
        self,
        organization_id: str,
        challenge_data: Dict[str, Any],
        created_by: str
    ) -> GamificationChallenge:
        """
        Create a new challenge.

        Args:
            organization_id: Organization ID
            challenge_data: Challenge details
            created_by: Admin user ID who created challenge

        Returns:
            Created challenge

        Example:
            >>> challenge = await service.create_challenge(
            ...     organization_id="...",
            ...     challenge_data={
            ...         "name": "21-Day Commitment",
            ...         "description": "Attend service 3 weeks in a row",
            ...         "challenge_type": "individual",
            ...         "start_date": datetime(2025, 1, 1),
            ...         "end_date": datetime(2025, 1, 21),
            ...         "goal_type": "attendance",
            ...         "goal_target": 3,
            ...         "points_reward": 100
            ...     },
            ...     created_by="admin_user_id"
            ... )
        """
        challenge_doc = {
            "organization_id": ObjectId(organization_id),
            "name": challenge_data["name"],
            "description": challenge_data.get("description", ""),
            "challenge_type": challenge_data.get("challenge_type", "individual"),
            "start_date": challenge_data["start_date"],
            "end_date": challenge_data["end_date"],
            "goal_type": challenge_data["goal_type"],
            "goal_target": challenge_data["goal_target"],
            "goal_unit": challenge_data.get("goal_unit", "count"),
            "points_reward": challenge_data.get("points_reward", 0),
            "badge_reward": challenge_data.get("badge_reward"),
            "status": ChallengeStatus.UPCOMING.value,
            "participants": [],
            "max_participants": challenge_data.get("max_participants"),
            "is_public": challenge_data.get("is_public", True),
            "created_by": ObjectId(created_by),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        # Set initial status based on dates
        now = datetime.utcnow()
        if challenge_doc["start_date"] <= now <= challenge_doc["end_date"]:
            challenge_doc["status"] = ChallengeStatus.ACTIVE.value
        elif now > challenge_doc["end_date"]:
            challenge_doc["status"] = ChallengeStatus.COMPLETED.value

        result = await self.challenges_collection.insert_one(challenge_doc)
        challenge_doc["_id"] = result.inserted_id

        return GamificationChallenge(**challenge_doc)

    async def get_challenge(self, challenge_id: str) -> Optional[GamificationChallenge]:
        """Get challenge by ID."""
        doc = await self.challenges_collection.find_one({"_id": ObjectId(challenge_id)})
        if doc:
            return GamificationChallenge(**doc)
        return None

    async def list_challenges(
        self,
        organization_id: str,
        status: Optional[ChallengeStatus] = None,
        challenge_type: Optional[ChallengeType] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        List challenges with filters.

        Args:
            organization_id: Organization ID
            status: Filter by status (upcoming, active, completed)
            challenge_type: Filter by type (individual, team, cell_group)
            page: Page number
            page_size: Items per page

        Returns:
            Paginated challenge list
        """
        query = {"organization_id": ObjectId(organization_id)}

        if status:
            query["status"] = status.value
        if challenge_type:
            query["challenge_type"] = challenge_type.value

        # Update statuses before querying
        await self._update_challenge_statuses(organization_id)

        total = await self.challenges_collection.count_documents(query)

        cursor = self.challenges_collection.find(query).sort("start_date", -1)
        cursor.skip((page - 1) * page_size).limit(page_size)

        docs = await cursor.to_list(length=page_size)
        challenges = [GamificationChallenge(**doc) for doc in docs]

        return {
            "challenges": challenges,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": total > page * page_size
        }

    async def join_challenge(
        self,
        challenge_id: str,
        user_id: str,
        team_name: Optional[str] = None
    ) -> GamificationChallenge:
        """
        Join a challenge.

        Args:
            challenge_id: Challenge ID
            user_id: User ID
            team_name: Team name (for team challenges)

        Returns:
            Updated challenge

        Raises:
            ValueError: If challenge is full, not active, or user already joined
        """
        challenge = await self.get_challenge(challenge_id)
        if not challenge:
            raise ValueError("Challenge not found")

        if challenge.status != ChallengeStatus.ACTIVE:
            raise ValueError("Challenge is not active")

        # Check if already joined
        for participant in challenge.participants:
            if str(participant.user_id) == user_id:
                raise ValueError("Already joined this challenge")

        # Check max participants
        if challenge.max_participants:
            if len(challenge.participants) >= challenge.max_participants:
                raise ValueError("Challenge is full")

        # Create participant
        participant = ChallengeParticipant(
            user_id=ObjectId(user_id),
            joined_at=datetime.utcnow(),
            current_progress=0,
            completed=False,
            team_name=team_name
        )

        # Add to challenge
        await self.challenges_collection.update_one(
            {"_id": ObjectId(challenge_id)},
            {
                "$push": {"participants": participant.model_dump()},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

        return await self.get_challenge(challenge_id)

    async def leave_challenge(
        self,
        challenge_id: str,
        user_id: str
    ) -> GamificationChallenge:
        """
        Leave a challenge (only if not completed).

        Args:
            challenge_id: Challenge ID
            user_id: User ID

        Returns:
            Updated challenge

        Raises:
            ValueError: If challenge not found or already completed
        """
        challenge = await self.get_challenge(challenge_id)
        if not challenge:
            raise ValueError("Challenge not found")

        if challenge.status == ChallengeStatus.COMPLETED:
            raise ValueError("Cannot leave completed challenge")

        # Remove participant
        await self.challenges_collection.update_one(
            {"_id": ObjectId(challenge_id)},
            {
                "$pull": {"participants": {"user_id": ObjectId(user_id)}},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

        return await self.get_challenge(challenge_id)

    async def update_participant_progress(
        self,
        challenge_id: str,
        user_id: str,
        progress_increment: int = 1
    ) -> Dict[str, Any]:
        """
        Update participant's progress in challenge.

        Called automatically when relevant actions occur (attendance, donations, etc.).

        Args:
            challenge_id: Challenge ID
            user_id: User ID
            progress_increment: Amount to increment progress by

        Returns:
            Progress update result with completion status
        """
        challenge = await self.get_challenge(challenge_id)
        if not challenge:
            return {"updated": False, "reason": "Challenge not found"}

        if challenge.status != ChallengeStatus.ACTIVE:
            return {"updated": False, "reason": "Challenge not active"}

        # Find participant
        participant_idx = None
        for idx, participant in enumerate(challenge.participants):
            if str(participant.user_id) == user_id:
                participant_idx = idx
                break

        if participant_idx is None:
            return {"updated": False, "reason": "Not a participant"}

        participant = challenge.participants[participant_idx]

        # Don't update if already completed
        if participant.completed:
            return {"updated": False, "reason": "Already completed"}

        # Update progress
        new_progress = participant.current_progress + progress_increment
        completed = new_progress >= challenge.goal_target

        await self.challenges_collection.update_one(
            {
                "_id": ObjectId(challenge_id),
                f"participants.{participant_idx}.user_id": ObjectId(user_id)
            },
            {
                "$set": {
                    f"participants.{participant_idx}.current_progress": new_progress,
                    f"participants.{participant_idx}.completed": completed,
                    f"participants.{participant_idx}.completed_at": datetime.utcnow() if completed else None,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        result = {
            "updated": True,
            "new_progress": new_progress,
            "goal_target": challenge.goal_target,
            "completed": completed
        }

        # Award rewards if just completed
        if completed:
            await self._award_challenge_completion(
                challenge_id=challenge_id,
                user_id=user_id,
                organization_id=str(challenge.organization_id)
            )
            result["points_awarded"] = challenge.points_reward

        return result

    async def get_user_challenges(
        self,
        user_id: str,
        organization_id: str,
        active_only: bool = False
    ) -> List[GamificationChallenge]:
        """
        Get all challenges user is participating in.

        Args:
            user_id: User ID
            organization_id: Organization ID
            active_only: Only return active challenges

        Returns:
            List of challenges
        """
        query = {
            "organization_id": ObjectId(organization_id),
            "participants.user_id": ObjectId(user_id)
        }

        if active_only:
            query["status"] = ChallengeStatus.ACTIVE.value

        cursor = self.challenges_collection.find(query).sort("start_date", -1)
        docs = await cursor.to_list(length=100)

        return [GamificationChallenge(**doc) for doc in docs]

    async def complete_challenge(
        self,
        challenge_id: str
    ) -> GamificationChallenge:
        """
        Mark challenge as completed and award rewards to all completers.

        Called automatically when end_date is reached.

        Args:
            challenge_id: Challenge ID

        Returns:
            Updated challenge with winner information
        """
        challenge = await self.get_challenge(challenge_id)
        if not challenge:
            raise ValueError("Challenge not found")

        if challenge.status == ChallengeStatus.COMPLETED:
            return challenge

        # Award rewards to all who completed
        for participant in challenge.participants:
            if participant.completed and not participant.rewards_claimed:
                await self._award_challenge_completion(
                    challenge_id=challenge_id,
                    user_id=str(participant.user_id),
                    organization_id=str(challenge.organization_id)
                )

        # Update challenge status
        await self.challenges_collection.update_one(
            {"_id": ObjectId(challenge_id)},
            {
                "$set": {
                    "status": ChallengeStatus.COMPLETED.value,
                    "completed_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )

        return await self.get_challenge(challenge_id)

    async def _award_challenge_completion(
        self,
        challenge_id: str,
        user_id: str,
        organization_id: str
    ):
        """Award points/badges for completing challenge."""
        challenge = await self.get_challenge(challenge_id)
        if not challenge:
            return

        gamification_service = get_gamification_service(self.db)

        # Award points
        if challenge.points_reward > 0:
            await gamification_service.award_points(
                user_id=user_id,
                organization_id=organization_id,
                points=challenge.points_reward,
                action="challenge_completed",
                reference_id=challenge_id,
                reference_type="challenge",
                metadata={"challenge_name": challenge.name}
            )

        # Award badge if specified
        if challenge.badge_reward:
            await gamification_service.award_badge(
                user_id=user_id,
                organization_id=organization_id,
                badge_id=challenge.badge_reward
            )

        # Mark rewards as claimed
        await self.challenges_collection.update_one(
            {
                "_id": ObjectId(challenge_id),
                "participants.user_id": ObjectId(user_id)
            },
            {
                "$set": {
                    "participants.$.rewards_claimed": True,
                    "participants.$.rewards_claimed_at": datetime.utcnow()
                }
            }
        )

    async def _update_challenge_statuses(self, organization_id: str):
        """Update challenge statuses based on current date."""
        now = datetime.utcnow()

        # Mark upcoming as active
        await self.challenges_collection.update_many(
            {
                "organization_id": ObjectId(organization_id),
                "status": ChallengeStatus.UPCOMING.value,
                "start_date": {"$lte": now}
            },
            {"$set": {"status": ChallengeStatus.ACTIVE.value}}
        )

        # Mark active as completed
        active_challenges = await self.challenges_collection.find({
            "organization_id": ObjectId(organization_id),
            "status": ChallengeStatus.ACTIVE.value,
            "end_date": {"$lt": now}
        }).to_list(length=100)

        for challenge_doc in active_challenges:
            await self.complete_challenge(str(challenge_doc["_id"]))


def get_gamification_challenges_service(db: AsyncIOMotorDatabase) -> GamificationChallengesService:
    """Get challenges service instance."""
    return GamificationChallengesService(db)
