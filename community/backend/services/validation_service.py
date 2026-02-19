"""
Validation service for African Language Community Platform.

Handles community validation of submissions with quality scoring.
"""

from typing import List, Optional, Dict, Any
from bson import ObjectId
from datetime import datetime
import logging

from models.validation_models import (
    Validation, ValidationCreate, ValidationAction, ValidationCategory
)
from models.submission_models import QualityTier, ValidationStatus
from models.user_models import UserLevel
from database import get_database

logger = logging.getLogger(__name__)


class ValidationService:
    """
    Service for managing community validation of submissions.

    Handles validation creation, scoring, and quality tier promotion.
    """

    def __init__(self):
        """Initialize validation service."""
        pass

    async def _get_db(self):
        """Get database connection for current request."""
        # Always get a fresh connection to avoid stale event loop issues
        return get_database()

    async def create_validation(
        self,
        validation_data: ValidationCreate,
        validator_id: ObjectId
    ) -> Validation:
        """
        Create a new validation for a submission.

        Args:
            validation_data: Validation data
            validator_id: ID of validating user

        Returns:
            Validation: Created validation object
        """
        try:
            db = await self._get_db()

            # Check if user already validated this submission
            existing_validation = await db.validations.find_one({
                "validator_id": validator_id,
                "submission_id": ObjectId(validation_data.submission_id),
                "submission_type": validation_data.submission_type
            })

            if existing_validation:
                raise Exception("User has already validated this submission")

            validation_doc = {
                "validator_id": validator_id,
                "submission_id": ObjectId(validation_data.submission_id),
                "submission_type": validation_data.submission_type,
                "action": validation_data.action,
                "category": validation_data.category,
                "quality_rating": validation_data.quality_rating,
                "comments": validation_data.comments,
                "specific_issues": validation_data.specific_issues,
                "suggested_corrections": validation_data.suggested_corrections,
                "confidence_level": validation_data.confidence_level,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            result = await db.validations.insert_one(validation_doc)
            validation_doc["_id"] = result.inserted_id

            # Update submission with validation
            await self._update_submission_validation(
                validation_data.submission_id,
                validation_data.submission_type,
                validation_data.action,
                validation_data.quality_rating
            )

            return Validation(**validation_doc)

        except Exception as e:
            logger.error(f"Validation creation failed: {str(e)}")
            raise

    async def _update_submission_validation(
        self,
        submission_id: str,
        submission_type: str,
        action: ValidationAction,
        quality_rating: int
    ):
        """
        Update submission with new validation data.

        Args:
            submission_id: Submission ID
            submission_type: Type of submission
            action: Validation action
            quality_rating: Quality rating
        """
        try:
            db = await self._get_db()

            collection = db.submissions

            # Get current submission
            submission = await collection.find_one({"_id": ObjectId(submission_id)})
            if not submission:
                return

            # Update validation counts
            validation_count = submission.get("validation_count", 0) + 1
            positive_validations = submission.get("positive_validations", 0)

            if action == ValidationAction.APPROVE:
                positive_validations += 1

            # Calculate new quality score
            current_score = submission.get("quality_score", 0.0)
            new_score = ((current_score * (validation_count - 1)) + quality_rating) / validation_count

            # Determine new status and data tier
            status = submission.get("validation_status", ValidationStatus.PENDING)
            data_tier = submission.get("tier", QualityTier.TIER_3_SUBMITTED)

            # Promote to higher tiers based on validation threshold
            approval_rate = positive_validations / validation_count if validation_count > 0 else 0

            if validation_count >= 3 and approval_rate >= 0.8 and new_score >= 4.0:
                if data_tier == QualityTier.TIER_3_SUBMITTED:
                    data_tier = QualityTier.TIER_2_REVIEWED
                    status = ValidationStatus.VALIDATED
                elif data_tier == QualityTier.TIER_2_REVIEWED and validation_count >= 5 and new_score >= 4.5:
                    data_tier = QualityTier.TIER_1_VALIDATED
                    status = ValidationStatus.VALIDATED
            elif validation_count >= 3 and approval_rate < 0.4:
                status = ValidationStatus.REJECTED

            # Update submission
            await collection.update_one(
                {"_id": ObjectId(submission_id)},
                {"$set": {
                    "validation_count": validation_count,
                    "positive_validations": positive_validations,
                    "quality_score": new_score,
                    "validation_status": status,
                    "tier": data_tier,
                    "updated_at": datetime.utcnow()
                }}
            )

        except Exception as e:
            logger.error(f"Failed to update submission validation: {str(e)}")

    async def get_pending_validations(
        self,
        validator_id: ObjectId,
        page: int = 1,
        page_size: int = 20,
        language_code: Optional[str] = None,
        submission_type: Optional[str] = None
    ) -> tuple[List[dict], int]:
        """
        Get submissions pending validation that the user can review.

        Args:
            validator_id: ID of the validator
            page: Page number (1-indexed)
            page_size: Number of items per page
            language_code: Optional language filter
            submission_type: Optional submission type filter

        Returns:
            Tuple of (pending submissions list, total count)
        """
        try:
            db = await self._get_db()

            # Build query for pending submissions
            query = {
                "validation_status": "pending",
                "contributor_id": {"$ne": validator_id}  # Can't validate own submissions
            }

            if language_code:
                query["language_code"] = language_code

            if submission_type:
                query["type"] = submission_type

            # Exclude submissions already validated by this user
            validated_submission_ids = await db.validations.distinct(
                "submission_id",
                {"validator_id": validator_id}
            )
            if validated_submission_ids:
                query["_id"] = {"$nin": validated_submission_ids}

            # Get total count
            total_count = await db.submissions.count_documents(query)

            # Get paginated results
            skip = (page - 1) * page_size
            submissions = await db.submissions.find(query)\
                .skip(skip).limit(page_size).to_list(length=None)

            # Convert ObjectIds to strings for JSON serialization
            for sub in submissions:
                sub["id"] = str(sub["_id"])
                sub["_id"] = str(sub["_id"])
                if "contributor_id" in sub:
                    sub["contributor_id"] = str(sub["contributor_id"])

            return submissions, total_count

        except Exception as e:
            logger.error(f"Failed to get pending validations: {str(e)}")
            raise

    async def get_user_validations(
        self,
        validator_id: ObjectId,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[dict], int]:
        """
        Get validations performed by a specific user.

        Args:
            validator_id: ID of the validator
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Tuple of (validations list, total count)
        """
        try:
            db = await self._get_db()

            # Get total count
            total_count = await db.validations.count_documents({"validator_id": validator_id})

            # Get paginated results
            skip = (page - 1) * page_size
            validations = await db.validations.find({"validator_id": validator_id})\
                .skip(skip).limit(page_size).to_list(length=None)

            # Convert ObjectIds to strings for JSON serialization
            for val in validations:
                val["id"] = str(val["_id"])
                val["_id"] = str(val["_id"])
                val["validator_id"] = str(val["validator_id"])
                val["submission_id"] = str(val["submission_id"])

            return validations, total_count

        except Exception as e:
            logger.error(f"Failed to get user validations: {str(e)}")
            raise

    async def get_validations_by_user(
        self,
        user_id: ObjectId,
        skip: int = 0,
        limit: int = 50
    ) -> List[Validation]:
        """
        Get validations performed by a user.

        Args:
            user_id: User ID
            skip: Number of validations to skip
            limit: Maximum number of validations to return

        Returns:
            List[Validation]: User validations
        """
        try:
            db = await self._get_db()

            validations = await db.validations.find(
                {"validator_id": user_id}
            ).skip(skip).limit(limit).to_list(length=None)

            return [Validation(**val) for val in validations]

        except Exception as e:
            logger.error(f"Failed to get user validations: {str(e)}")
            raise

    async def get_validations_for_submission(
        self,
        submission_id: str,
        submission_type: str
    ) -> List[Validation]:
        """
        Get all validations for a specific submission.

        Args:
            submission_id: Submission ID
            submission_type: Type of submission

        Returns:
            List[Validation]: Submission validations
        """
        try:
            db = await self._get_db()

            validations = await db.validations.find({
                "submission_id": ObjectId(submission_id),
                "submission_type": submission_type
            }).to_list(length=None)

            return [Validation(**val) for val in validations]

        except Exception as e:
            logger.error(f"Failed to get submission validations: {str(e)}")
            raise

    async def get_validation_statistics(
        self,
        user_id: Optional[ObjectId] = None,
        language_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get validation statistics.

        Args:
            user_id: Optional user ID for user-specific stats
            language_id: Optional language ID for language-specific stats

        Returns:
            Dict: Validation statistics
        """
        try:
            db = await self._get_db()

            pipeline = []

            # Match filters
            match_conditions = {}
            if user_id:
                match_conditions["validator_id"] = user_id

            if match_conditions:
                pipeline.append({"$match": match_conditions})

            # Group by action to get counts
            pipeline.extend([
                {
                    "$group": {
                        "_id": "$action",
                        "count": {"$sum": 1},
                        "avg_quality_rating": {"$avg": "$quality_rating"},
                        "avg_confidence": {"$avg": "$confidence_level"}
                    }
                }
            ])

            validation_stats = await db.validations.aggregate(pipeline).to_list(length=None)

            # Format results
            stats = {
                "total_validations": sum(stat["count"] for stat in validation_stats),
                "approved": 0,
                "rejected": 0,
                "flagged": 0,
                "avg_quality_rating": 0.0,
                "avg_confidence": 0.0
            }

            for stat in validation_stats:
                action = stat["_id"]
                if action == ValidationAction.APPROVE:
                    stats["approved"] = stat["count"]
                elif action == ValidationAction.REJECT:
                    stats["rejected"] = stat["count"]
                elif action == ValidationAction.FLAG:
                    stats["flagged"] = stat["count"]

                stats["avg_quality_rating"] += stat["avg_quality_rating"] * stat["count"]
                stats["avg_confidence"] += stat["avg_confidence"] * stat["count"]

            if stats["total_validations"] > 0:
                stats["avg_quality_rating"] /= stats["total_validations"]
                stats["avg_confidence"] /= stats["total_validations"]

            return stats

        except Exception as e:
            logger.error(f"Failed to get validation statistics: {str(e)}")
            raise

    async def can_user_validate_submission(
        self,
        user_id: ObjectId,
        submission_id: str,
        submission_type: Optional[str] = None,
        user_level: Optional[UserLevel] = None
    ) -> bool:
        """
        Check if user can validate a specific submission.

        Args:
            user_id: User ID
            submission_id: Submission ID
            submission_type: Type of submission (optional, will be fetched if not provided)
            user_level: User level (optional, defaults to NEWCOMER)

        Returns:
            bool: True if user can validate
        """
        try:
            db = await self._get_db()

            # Get submission to check type if not provided
            collection = db.submissions
            submission = await collection.find_one({"_id": ObjectId(submission_id)})

            if not submission:
                return False  # Submission doesn't exist

            # Get submission type from submission if not provided
            actual_type = submission_type or submission.get("type")
            actual_level = user_level or UserLevel.NEWCOMER

            # Check if user already validated this submission
            existing_query = {
                "validator_id": user_id,
                "submission_id": ObjectId(submission_id)
            }
            if actual_type:
                existing_query["submission_type"] = actual_type

            existing_validation = await db.validations.find_one(existing_query)

            if existing_validation:
                return False

            # Check if user is the submitter
            if str(submission.get("contributor_id")) == str(user_id):
                return False  # Users cannot validate their own submissions

            # Check user level permissions
            if actual_level in [UserLevel.NEWCOMER, UserLevel.CONTRIBUTOR]:
                # Can only validate SUBMITTED tier
                return submission.get("tier") == QualityTier.TIER_3_SUBMITTED.value or \
                       submission.get("tier") == QualityTier.TIER_3_SUBMITTED

            return True  # Higher level users can validate all submissions

        except Exception as e:
            logger.error(f"Failed to check validation permission: {str(e)}")
            return False

    async def get_validator_statistics(
        self,
        validator_id: str
    ) -> Dict[str, Any]:
        """
        Get statistics for a specific validator.

        Args:
            validator_id: Validator user ID

        Returns:
            Dict: Validator statistics
        """
        try:
            db = await self._get_db()

            # Convert string to ObjectId if needed
            if isinstance(validator_id, str):
                validator_oid = ObjectId(validator_id)
            else:
                validator_oid = validator_id

            # Get validation counts by action
            pipeline = [
                {"$match": {"validator_id": validator_oid}},
                {
                    "$group": {
                        "_id": "$action",
                        "count": {"$sum": 1},
                        "avg_rating": {"$avg": "$quality_rating"},
                        "avg_confidence": {"$avg": "$confidence_level"}
                    }
                }
            ]

            validation_stats = await db.validations.aggregate(pipeline).to_list(length=None)

            # Calculate totals
            total_validations = sum(stat["count"] for stat in validation_stats)
            approved = 0
            rejected = 0
            flagged = 0
            avg_quality_rating = 0.0
            avg_confidence = 0.0

            for stat in validation_stats:
                action = stat["_id"]
                if action == ValidationAction.APPROVE or action == "approve":
                    approved = stat["count"]
                elif action == ValidationAction.REJECT or action == "reject":
                    rejected = stat["count"]
                elif action == ValidationAction.FLAG or action == "flag":
                    flagged = stat["count"]

                if stat.get("avg_rating"):
                    avg_quality_rating += stat["avg_rating"] * stat["count"]
                if stat.get("avg_confidence"):
                    avg_confidence += stat["avg_confidence"] * stat["count"]

            if total_validations > 0:
                avg_quality_rating /= total_validations
                avg_confidence /= total_validations

            # Get recent validations
            recent_validations = await db.validations.find(
                {"validator_id": validator_oid}
            ).sort("created_at", -1).limit(5).to_list(length=None)

            # Convert ObjectIds to strings in recent validations
            for val in recent_validations:
                val["_id"] = str(val["_id"])
                val["submission_id"] = str(val["submission_id"])
                val["validator_id"] = str(val["validator_id"])

            return {
                "total_validations": total_validations,
                "approved": approved,
                "rejected": rejected,
                "flagged": flagged,
                "avg_quality_rating": round(avg_quality_rating, 2),
                "avg_confidence": round(avg_confidence, 2),
                "accuracy_rate": round(approved / max(total_validations, 1) * 100, 2),
                "recent_validations": recent_validations
            }

        except Exception as e:
            logger.error(f"Failed to get validator statistics: {str(e)}")
            raise