"""
Submission management service for African Language Community Platform.

Handles community data submissions with quality validation.
"""

from typing import List, Optional, Dict, Any
from bson import ObjectId
from datetime import datetime
import logging

from models.submission_models import (
    Submission, SubmissionCreate, SubmissionUpdate,
    QualityTier, ValidationStatus, SubmissionType
)
from models.user_models import UserLevel
from database import get_database

logger = logging.getLogger(__name__)


class SubmissionService:
    """
    Service for managing community submissions.

    Handles creation, retrieval, and management of all submission types.
    """

    def __init__(self):
        """Initialize submission service."""
        pass

    async def _get_db(self):
        """Get database connection for current request."""
        # Always get a fresh connection to avoid stale event loop issues
        return get_database()

    async def create_submission(
        self,
        submission_data: SubmissionCreate,
        user_id: ObjectId
    ) -> Submission:
        """
        Create a new submission.

        Args:
            submission_data: Submission data
            user_id: ID of submitting user

        Returns:
            Submission: Created submission object
        """
        try:
            db = await self._get_db()

            submission_doc = {
                "contributor_id": user_id,
                "language_code": submission_data.language_code,
                "language_family": submission_data.language_family,
                "type": submission_data.type,
                "title": submission_data.title,
                "description": submission_data.description,
                "category": submission_data.category,
                "dialect": submission_data.dialect,
                "text_content": submission_data.text_content,
                "translation": submission_data.translation,
                "external_url": submission_data.external_url,
                "cultural_context": submission_data.cultural_context,
                "usage_context": submission_data.usage_context,
                "source_attribution": submission_data.source_attribution,
                "tier": QualityTier.TIER_3_SUBMITTED,
                "validation_status": ValidationStatus.PENDING,
                "quality_scores": {},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            result = await db.submissions.insert_one(submission_doc)
            submission_doc["_id"] = result.inserted_id

            return Submission(**submission_doc)

        except Exception as e:
            logger.error(f"Submission creation failed: {str(e)}")
            raise

    async def get_submissions_by_user(
        self,
        user_id: ObjectId,
        skip: int = 0,
        limit: int = 50
    ) -> List[Submission]:
        """
        Get submissions by user ID.

        Args:
            user_id: User ID
            skip: Number of submissions to skip
            limit: Maximum number of submissions to return

        Returns:
            List[Submission]: List of user submissions
        """
        try:
            db = await self._get_db()

            submissions = await db.submissions.find(
                {"contributor_id": user_id}
            ).skip(skip).limit(limit).to_list(length=None)

            return [Submission(**sub) for sub in submissions]

        except Exception as e:
            logger.error(f"Failed to get user submissions: {str(e)}")
            raise

    async def get_submissions_by_language(
        self,
        language_code: str,
        tier: Optional[QualityTier] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Submission]:
        """
        Get submissions for a specific language.

        Args:
            language_code: Language code
            tier: Optional quality tier filter
            skip: Number of submissions to skip
            limit: Maximum number of submissions to return

        Returns:
            List[Submission]: Language submissions
        """
        try:
            db = await self._get_db()

            query = {"language_code": language_code}
            if tier:
                query["tier"] = tier

            submissions = await db.submissions.find(query)\
                .skip(skip).limit(limit).to_list(length=None)

            return [Submission(**sub) for sub in submissions]

        except Exception as e:
            logger.error(f"Failed to get language submissions: {str(e)}")
            raise

    async def get_submission_by_id(self, submission_id: ObjectId) -> Optional[Submission]:
        """
        Get submission by ID.

        Args:
            submission_id: Submission ID

        Returns:
            Submission: Submission object or None if not found
        """
        try:
            db = await self._get_db()

            submission = await db.submissions.find_one({"_id": submission_id})
            return Submission(**submission) if submission else None

        except Exception as e:
            logger.error(f"Failed to get submission: {str(e)}")
            return None

    async def update_submission(
        self,
        submission_id: ObjectId,
        updates: SubmissionUpdate,
        user_id: ObjectId
    ) -> Optional[Submission]:
        """
        Update a submission (only by owner).

        Args:
            submission_id: Submission ID
            updates: Updates to apply
            user_id: ID of requesting user

        Returns:
            Submission: Updated submission or None if not found/not authorized
        """
        try:
            db = await self._get_db()

            # Verify ownership
            submission = await db.submissions.find_one({
                "_id": submission_id,
                "contributor_id": user_id
            })

            if not submission:
                return None

            # Prepare update data
            update_data = {}
            for field, value in updates.dict(exclude_unset=True).items():
                if value is not None:
                    update_data[field] = value

            update_data["updated_at"] = datetime.utcnow()

            # Update submission
            await db.submissions.update_one(
                {"_id": submission_id},
                {"$set": update_data}
            )

            # Return updated submission
            updated_submission = await db.submissions.find_one({"_id": submission_id})
            return Submission(**updated_submission)

        except Exception as e:
            logger.error(f"Failed to update submission: {str(e)}")
            return None

    async def update_submission_status(
        self,
        submission_id: ObjectId,
        status: ValidationStatus,
        tier: Optional[QualityTier] = None
    ) -> bool:
        """
        Update submission status and optionally tier.

        Args:
            submission_id: Submission ID
            status: New status
            tier: Optional new tier

        Returns:
            bool: True if update successful
        """
        try:
            db = await self._get_db()

            update_data = {
                "validation_status": status,
                "updated_at": datetime.utcnow()
            }

            if tier:
                update_data["tier"] = tier

            result = await db.submissions.update_one(
                {"_id": submission_id},
                {"$set": update_data}
            )

            return result.modified_count > 0

        except Exception as e:
            logger.error(f"Failed to update submission status: {str(e)}")
            return False

    async def get_pending_submissions(
        self,
        limit: int = 50,
        submission_type: Optional[SubmissionType] = None,
        user_level: UserLevel = UserLevel.NEWCOMER
    ) -> List[Submission]:
        """
        Get pending submissions for validation.

        Args:
            limit: Maximum number of submissions to return
            submission_type: Optional submission type filter
            user_level: User level to determine accessible submissions

        Returns:
            List[Submission]: Pending submissions
        """
        try:
            db = await self._get_db()

            query = {"validation_status": ValidationStatus.PENDING}

            if submission_type:
                query["type"] = submission_type

            # Filter by tier based on user level
            if user_level == UserLevel.NEWCOMER:
                query["tier"] = QualityTier.TIER_3_SUBMITTED

            submissions = await db.submissions.find(query)\
                .limit(limit).sort("created_at", 1).to_list(length=None)

            return [Submission(**sub) for sub in submissions]

        except Exception as e:
            logger.error(f"Failed to get pending submissions: {str(e)}")
            raise

    async def delete_submission(
        self,
        submission_id: ObjectId,
        user_id: ObjectId
    ) -> bool:
        """
        Delete a submission (only by owner).

        Args:
            submission_id: Submission ID
            user_id: ID of requesting user

        Returns:
            bool: True if deletion successful
        """
        try:
            db = await self._get_db()

            result = await db.submissions.delete_one({
                "_id": submission_id,
                "contributor_id": user_id  # Only owner can delete
            })

            return result.deleted_count > 0

        except Exception as e:
            logger.error(f"Failed to delete submission: {str(e)}")
            return False

    async def get_submission_statistics(
        self,
        language_code: Optional[str] = None,
        user_id: Optional[ObjectId] = None
    ) -> Dict[str, Any]:
        """
        Get submission statistics.

        Args:
            language_code: Optional language filter
            user_id: Optional user filter

        Returns:
            Dict: Submission statistics
        """
        try:
            db = await self._get_db()

            pipeline = []

            # Match filters
            match_conditions = {}
            if language_code:
                match_conditions["language_code"] = language_code
            if user_id:
                match_conditions["contributor_id"] = user_id

            if match_conditions:
                pipeline.append({"$match": match_conditions})

            # Group by various dimensions
            pipeline.extend([
                {
                    "$facet": {
                        "by_type": [
                            {"$group": {"_id": "$type", "count": {"$sum": 1}}}
                        ],
                        "by_tier": [
                            {"$group": {"_id": "$tier", "count": {"$sum": 1}}}
                        ],
                        "by_status": [
                            {"$group": {"_id": "$validation_status", "count": {"$sum": 1}}}
                        ],
                        "total": [
                            {"$count": "total"}
                        ]
                    }
                }
            ])

            result = await db.submissions.aggregate(pipeline).to_list(length=None)

            if not result:
                return {
                    "total_submissions": 0,
                    "by_type": {},
                    "by_tier": {},
                    "by_status": {}
                }

            stats = result[0]

            return {
                "total_submissions": stats["total"][0]["total"] if stats["total"] else 0,
                "by_type": {item["_id"]: item["count"] for item in stats["by_type"]},
                "by_tier": {item["_id"]: item["count"] for item in stats["by_tier"]},
                "by_status": {item["_id"]: item["count"] for item in stats["by_status"]}
            }

        except Exception as e:
            logger.error(f"Failed to get submission statistics: {str(e)}")
            raise

    async def create_audio_submission(
        self,
        submission_data: SubmissionCreate,
        audio_file,
        user_id: ObjectId
    ) -> Submission:
        """
        Create a new audio submission.

        Args:
            submission_data: Submission data
            audio_file: Audio file upload
            user_id: ID of submitting user

        Returns:
            Submission: Created submission object
        """
        try:
            db = await self._get_db()

            # TODO: Process audio file (save to storage, extract metadata, etc.)
            # For now, just create the submission record

            submission_doc = {
                "contributor_id": user_id,
                "language_code": submission_data.language_code,
                "type": "audio",
                "title": submission_data.title,
                "description": submission_data.description,
                "category": submission_data.category,
                "dialect": submission_data.dialect,
                "cultural_context": submission_data.cultural_context,
                "usage_context": submission_data.usage_context,
                "audio_file_name": audio_file.filename,
                "audio_file_size": audio_file.size if hasattr(audio_file, 'size') else 0,
                "duration_seconds": 0,  # TODO: Extract from audio file
                "tier": QualityTier.TIER_3_SUBMITTED,
                "validation_status": ValidationStatus.PENDING,
                "quality_scores": {},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            result = await db.submissions.insert_one(submission_doc)
            submission_doc["_id"] = result.inserted_id

            return Submission(**submission_doc)

        except Exception as e:
            logger.error(f"Audio submission creation failed: {str(e)}")
            raise

    async def create_text_submission(
        self,
        submission_data: SubmissionCreate,
        user_id: ObjectId
    ) -> Submission:
        """
        Create a new text submission.

        Args:
            submission_data: Submission data
            user_id: ID of submitting user

        Returns:
            Submission: Created submission object
        """
        try:
            db = await self._get_db()

            submission_doc = {
                "contributor_id": user_id,
                "language_code": submission_data.language_code,
                "language_family": submission_data.language_family,
                "type": "text",
                "title": submission_data.title,
                "description": submission_data.description,
                "category": submission_data.category,
                "dialect": submission_data.dialect,
                "text_content": submission_data.text_content,
                "translation": submission_data.translation,
                "cultural_context": submission_data.cultural_context,
                "usage_context": submission_data.usage_context,
                "source_attribution": submission_data.source_attribution,
                "tier": QualityTier.TIER_3_SUBMITTED,
                "validation_status": ValidationStatus.PENDING,
                "quality_scores": {},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            result = await db.submissions.insert_one(submission_doc)
            submission_doc["_id"] = result.inserted_id

            return Submission(**submission_doc)

        except Exception as e:
            logger.error(f"Text submission creation failed: {str(e)}")
            raise

    async def create_link_submission(
        self,
        submission_data: SubmissionCreate,
        user_id: ObjectId
    ) -> Submission:
        """
        Create a new link submission.

        Args:
            submission_data: Submission data
            user_id: ID of submitting user

        Returns:
            Submission: Created submission object
        """
        try:
            db = await self._get_db()

            submission_doc = {
                "contributor_id": user_id,
                "language_code": submission_data.language_code,
                "language_family": submission_data.language_family,
                "type": "link",
                "title": submission_data.title,
                "description": submission_data.description,
                "category": submission_data.category,
                "dialect": submission_data.dialect,
                "external_url": submission_data.external_url,
                "cultural_context": submission_data.cultural_context,
                "usage_context": submission_data.usage_context,
                "source_attribution": submission_data.source_attribution,
                "tier": QualityTier.TIER_3_SUBMITTED,
                "validation_status": ValidationStatus.PENDING,
                "quality_scores": {},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            result = await db.submissions.insert_one(submission_doc)
            submission_doc["_id"] = result.inserted_id

            return Submission(**submission_doc)

        except Exception as e:
            logger.error(f"Link submission creation failed: {str(e)}")
            raise

    async def get_user_submissions(
        self,
        user_id: ObjectId,
        page: int = 1,
        page_size: int = 20,
        submission_type: Optional[str] = None,
        language_code: Optional[str] = None
    ):
        """
        Get user's submission history with pagination and filtering.

        Args:
            user_id: User ID
            page: Page number (1-based)
            page_size: Items per page
            submission_type: Optional submission type filter
            language_code: Optional language code filter

        Returns:
            Tuple[List[Submission], int]: List of submissions and total count
        """
        try:
            db = await self._get_db()

            # Build query filters
            query = {"contributor_id": user_id}
            if submission_type:
                query["type"] = submission_type
            if language_code:
                query["language_code"] = language_code

            # Calculate skip
            skip = (page - 1) * page_size

            # Get submissions with pagination
            cursor = db.submissions.find(query).sort("created_at", -1).skip(skip).limit(page_size)
            submissions_docs = await cursor.to_list(length=page_size)

            # Get total count
            total_count = await db.submissions.count_documents(query)

            submissions = [Submission(**doc) for doc in submissions_docs]
            return submissions, total_count

        except Exception as e:
            logger.error(f"Failed to get user submissions: {str(e)}")
            raise

    async def get_submission_details(
        self,
        submission_id: str,
        user_id: ObjectId
    ) -> Optional[Submission]:
        """
        Get detailed information about a specific submission.

        Args:
            submission_id: Submission ID
            user_id: ID of requesting user

        Returns:
            Submission: Submission object or None if not found/not authorized
        """
        try:
            db = await self._get_db()

            # Check if submission exists and user has access
            submission_doc = await db.submissions.find_one({
                "_id": ObjectId(submission_id),
                "contributor_id": user_id  # Only owner can view details for now
            })

            return Submission(**submission_doc) if submission_doc else None

        except Exception as e:
            logger.error(f"Failed to get submission details: {str(e)}")
            return None

    async def browse_language_submissions(
        self,
        language_code: str,
        page: int = 1,
        page_size: int = 20,
        filters: Dict[str, Any] = None
    ):
        """
        Browse submissions for a specific language.

        Args:
            language_code: Language code
            page: Page number (1-based)
            page_size: Items per page
            filters: Additional filters (tier, category, type)

        Returns:
            Tuple[List[Submission], int]: List of submissions and total count
        """
        try:
            db = await self._get_db()

            # Build query
            query = {"language_code": language_code}
            if filters:
                if filters.get("tier"):
                    query["tier"] = filters["tier"]
                if filters.get("category"):
                    query["category"] = filters["category"]
                if filters.get("type"):
                    query["type"] = filters["type"]

            # Calculate skip
            skip = (page - 1) * page_size

            # Get submissions with pagination
            cursor = db.submissions.find(query).sort("created_at", -1).skip(skip).limit(page_size)
            submissions_docs = await cursor.to_list(length=page_size)

            # Get total count
            total_count = await db.submissions.count_documents(query)

            submissions = [Submission(**doc) for doc in submissions_docs]
            return submissions, total_count

        except Exception as e:
            logger.error(f"Failed to browse language submissions: {str(e)}")
            raise

    async def get_submission_by_id(self, submission_id: str) -> Optional[Submission]:
        """
        Get submission by string ID.

        Args:
            submission_id: Submission ID as string

        Returns:
            Submission: Submission object or None if not found
        """
        try:
            db = await self._get_db()

            submission_doc = await db.submissions.find_one({"_id": ObjectId(submission_id)})
            return Submission(**submission_doc) if submission_doc else None

        except Exception as e:
            logger.error(f"Failed to get submission: {str(e)}")
            return None

    async def update_submission(
        self,
        submission_id: str,
        updates: SubmissionUpdate
    ) -> Optional[Submission]:
        """
        Update a submission.

        Args:
            submission_id: Submission ID as string
            updates: Updates to apply

        Returns:
            Submission: Updated submission or None if not found
        """
        try:
            db = await self._get_db()

            # Prepare update data
            update_data = {}
            for field, value in updates.dict(exclude_unset=True).items():
                if value is not None:
                    update_data[field] = value

            update_data["updated_at"] = datetime.utcnow()

            # Update submission
            result = await db.submissions.update_one(
                {"_id": ObjectId(submission_id)},
                {"$set": update_data}
            )

            if result.modified_count == 0:
                return None

            # Return updated submission
            updated_submission = await db.submissions.find_one({"_id": ObjectId(submission_id)})
            return Submission(**updated_submission) if updated_submission else None

        except Exception as e:
            logger.error(f"Failed to update submission: {str(e)}")
            return None

    async def delete_submission(self, submission_id: str) -> bool:
        """
        Delete a submission by string ID.

        Args:
            submission_id: Submission ID as string

        Returns:
            bool: True if deletion successful
        """
        try:
            db = await self._get_db()

            result = await db.submissions.delete_one({"_id": ObjectId(submission_id)})
            return result.deleted_count > 0

        except Exception as e:
            logger.error(f"Failed to delete submission: {str(e)}")
            return False