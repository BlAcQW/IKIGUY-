"""
Community governance service for dispute resolution and content moderation.

Handles disputes, content reports, moderation actions, and community guidelines.
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from bson import ObjectId
import logging

import database as db_module
from models.governance_models import (
    Dispute, DisputeCreate, DisputeUpdate, DisputeStats,
    ContentReport, ContentReportCreate,
    ModerationActionRecord, ModerationActionCreate, ModerationAction,
    GuidelineViolation, CommunityGuideline, ModerationStats
)
from models.user_models import User

logger = logging.getLogger(__name__)


class GovernanceService:
    """Service for community governance operations."""

    def __init__(self):
        pass

    async def _get_db(self):
        """Get database connection - always fresh to support test fixtures."""
        # Use db_module to allow test patching
        return db_module.get_database()

    # Dispute Management
    async def create_dispute(
        self,
        dispute_data: DisputeCreate,
        reporter_id: str
    ) -> Dispute:
        """
        Create a new dispute.

        Args:
            dispute_data: Dispute creation data
            reporter_id: ID of user creating the dispute

        Returns:
            Dispute: Created dispute
        """
        try:
            db = await self._get_db()

            # Validate related entities exist
            if dispute_data.related_submission_id:
                submission = await db.submissions.find_one(
                    {"_id": ObjectId(dispute_data.related_submission_id)}
                )
                if not submission:
                    raise ValueError("Related submission not found")

            if dispute_data.related_user_id:
                user = await db.users.find_one(
                    {"_id": ObjectId(dispute_data.related_user_id)}
                )
                if not user:
                    raise ValueError("Related user not found")

            dispute_doc = {
                "_id": ObjectId(),
                "dispute_type": dispute_data.dispute_type,
                "title": dispute_data.title,
                "description": dispute_data.description,
                "status": "open",
                "priority": dispute_data.priority,
                "reporter_id": reporter_id,
                "related_submission_id": dispute_data.related_submission_id,
                "related_user_id": dispute_data.related_user_id,
                "assigned_moderator_id": None,
                "evidence_urls": dispute_data.evidence_urls,
                "language_code": dispute_data.language_code,
                "resolution": None,
                "moderator_notes": None,
                "moderation_actions": [],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "resolved_at": None,
                "escalated_at": None,
                "community_votes": {}
            }

            await db.disputes.insert_one(dispute_doc)

            # Auto-assign to moderator based on language and type
            await self._auto_assign_dispute(str(dispute_doc["_id"]))

            # Create notification for moderators
            await self._notify_moderators_new_dispute(dispute_doc)

            return Dispute(**dispute_doc)

        except Exception as e:
            logger.error(f"Error creating dispute: {str(e)}")
            raise

    async def get_disputes(
        self,
        status: Optional[str] = None,
        dispute_type: Optional[str] = None,
        language_code: Optional[str] = None,
        assigned_to: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Dispute], int]:
        """
        Get disputes with filtering and pagination.

        Args:
            status: Filter by status
            dispute_type: Filter by type
            language_code: Filter by language
            assigned_to: Filter by assigned moderator
            page: Page number
            page_size: Items per page

        Returns:
            Tuple[List[Dispute], int]: Disputes and total count
        """
        try:
            db = await self._get_db()

            # Build filter
            filter_query = {}
            if status:
                filter_query["status"] = status
            if dispute_type:
                filter_query["dispute_type"] = dispute_type
            if language_code:
                filter_query["language_code"] = language_code
            if assigned_to:
                filter_query["assigned_moderator_id"] = assigned_to

            # Get total count
            total_count = await db.disputes.count_documents(filter_query)

            # Get paginated results
            cursor = db.disputes.find(filter_query)
            cursor = cursor.sort("created_at", -1)
            cursor = cursor.skip((page - 1) * page_size).limit(page_size)

            disputes = []
            async for doc in cursor:
                disputes.append(Dispute(**doc))

            return disputes, total_count

        except Exception as e:
            logger.error(f"Error getting disputes: {str(e)}")
            raise

    async def update_dispute(
        self,
        dispute_id: str,
        update_data: DisputeUpdate,
        moderator_id: str
    ) -> Dispute:
        """
        Update a dispute.

        Args:
            dispute_id: Dispute ID
            update_data: Update data
            moderator_id: ID of moderator making update

        Returns:
            Dispute: Updated dispute
        """
        try:
            db = await self._get_db()

            update_fields = {"updated_at": datetime.utcnow()}

            if update_data.status:
                update_fields["status"] = update_data.status
                if update_data.status == "resolved":
                    update_fields["resolved_at"] = datetime.utcnow()
                elif update_data.status == "escalated":
                    update_fields["escalated_at"] = datetime.utcnow()

            if update_data.moderator_notes:
                update_fields["moderator_notes"] = update_data.moderator_notes

            if update_data.resolution:
                update_fields["resolution"] = update_data.resolution

            if update_data.assigned_moderator_id:
                update_fields["assigned_moderator_id"] = update_data.assigned_moderator_id

            result = await db.disputes.find_one_and_update(
                {"_id": ObjectId(dispute_id)},
                {"$set": update_fields},
                return_document=True
            )

            if not result:
                raise ValueError("Dispute not found")

            # Log moderation action
            await self._log_dispute_action(dispute_id, moderator_id, update_data)

            return Dispute(**result)

        except Exception as e:
            logger.error(f"Error updating dispute: {str(e)}")
            raise

    async def vote_on_dispute(
        self,
        dispute_id: str,
        user_id: str,
        vote: int
    ) -> None:
        """
        Allow community voting on disputes.

        Args:
            dispute_id: Dispute ID
            user_id: User ID
            vote: Vote value (-1, 0, 1)
        """
        try:
            if vote not in [-1, 0, 1]:
                raise ValueError("Vote must be -1, 0, or 1")

            db = await self._get_db()

            await db.disputes.update_one(
                {"_id": ObjectId(dispute_id)},
                {"$set": {f"community_votes.{user_id}": vote}}
            )

        except Exception as e:
            logger.error(f"Error voting on dispute: {str(e)}")
            raise

    # Content Moderation
    async def create_content_report(
        self,
        report_data: ContentReportCreate,
        reporter_id: str
    ) -> ContentReport:
        """
        Create a content report.

        Args:
            report_data: Report data
            reporter_id: ID of reporting user

        Returns:
            ContentReport: Created report
        """
        try:
            db = await self._get_db()

            report_doc = {
                "_id": ObjectId(),
                "content_type": report_data.content_type,
                "content_id": report_data.content_id,
                "reporter_id": reporter_id,
                "report_reason": report_data.report_reason,
                "category": report_data.category,
                "severity": report_data.severity,
                "status": "pending",
                "reviewer_id": None,
                "review_notes": None,
                "action_taken": None,
                "created_at": datetime.utcnow(),
                "reviewed_at": None
            }

            await db.content_reports.insert_one(report_doc)

            # Auto-escalate high severity reports
            if report_data.severity >= 4:
                await self._escalate_content_report(str(report_doc["_id"]))

            return ContentReport(**report_doc)

        except Exception as e:
            logger.error(f"Error creating content report: {str(e)}")
            raise

    async def execute_moderation_action(
        self,
        action_data: ModerationActionCreate,
        moderator_id: str
    ) -> ModerationActionRecord:
        """
        Execute a moderation action.

        Args:
            action_data: Moderation action data
            moderator_id: ID of moderator

        Returns:
            ModerationActionRecord: Executed action record
        """
        try:
            db = await self._get_db()

            # Calculate expiration for temporary actions
            expires_at = None
            if action_data.duration_hours:
                expires_at = datetime.utcnow() + timedelta(hours=action_data.duration_hours)

            action_doc = {
                "_id": ObjectId(),
                "action_type": action_data.action_type,
                "moderator_id": moderator_id,
                "target_user_id": action_data.target_user_id,
                "target_content_id": action_data.target_content_id,
                "reason": action_data.reason,
                "duration_hours": action_data.duration_hours,
                "points_affected": action_data.points_affected,
                "internal_notes": action_data.internal_notes,
                "is_active": True,
                "executed_at": datetime.utcnow(),
                "expires_at": expires_at,
                "reversed_at": None,
                "reversed_by": None,
                "reverse_reason": None,
                "related_dispute_id": None
            }

            await db.moderation_actions.insert_one(action_doc)

            # Execute the action
            await self._apply_moderation_action(action_data, action_doc["_id"])

            # Notify affected user
            await self._notify_user_moderation_action(action_data.target_user_id, action_doc)

            return ModerationActionRecord(**action_doc)

        except Exception as e:
            logger.error(f"Error executing moderation action: {str(e)}")
            raise

    async def get_content_reports(
        self,
        status: Optional[str] = None,
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[ContentReport], int]:
        """
        Get content reports with filtering and pagination.

        Args:
            status: Filter by status (pending, reviewed, dismissed)
            category: Filter by category
            page: Page number (1-indexed)
            page_size: Number of reports per page

        Returns:
            Tuple[List[ContentReport], int]: List of reports and total count
        """
        try:
            db = await self._get_db()

            # Build query filter
            query = {}
            if status:
                query["status"] = status
            if category:
                query["category"] = category

            # Get total count
            total_count = await db.content_reports.count_documents(query)

            # Get paginated reports
            skip = (page - 1) * page_size
            cursor = db.content_reports.find(query).sort("created_at", -1).skip(skip).limit(page_size)

            reports = []
            async for doc in cursor:
                reports.append(ContentReport(**doc))

            return reports, total_count

        except Exception as e:
            logger.error(f"Error getting content reports: {str(e)}")
            raise

    async def get_moderation_actions(
        self,
        moderator_id: Optional[str] = None,
        action_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[ModerationActionRecord], int]:
        """
        Get moderation actions with filtering and pagination.

        Args:
            moderator_id: Filter by moderator ID
            action_type: Filter by action type
            page: Page number (1-indexed)
            page_size: Number of actions per page

        Returns:
            Tuple[List[ModerationActionRecord], int]: List of actions and total count
        """
        try:
            db = await self._get_db()

            # Build query filter
            query = {}
            if moderator_id:
                query["moderator_id"] = moderator_id
            if action_type:
                query["action"] = action_type

            # Get total count
            total_count = await db.moderation_actions.count_documents(query)

            # Get paginated actions
            skip = (page - 1) * page_size
            cursor = db.moderation_actions.find(query).sort("action_timestamp", -1).skip(skip).limit(page_size)

            actions = []
            async for doc in cursor:
                actions.append(ModerationActionRecord(**doc))

            return actions, total_count

        except Exception as e:
            logger.error(f"Error getting moderation actions: {str(e)}")
            raise

    async def get_moderation_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> ModerationStats:
        """
        Get moderation statistics.

        Args:
            start_date: Start date filter
            end_date: End date filter

        Returns:
            ModerationStats: Statistics
        """
        try:
            db = await self._get_db()

            # Build date filter
            date_filter = {}
            if start_date or end_date:
                date_filter["executed_at"] = {}
                if start_date:
                    date_filter["executed_at"]["$gte"] = start_date
                if end_date:
                    date_filter["executed_at"]["$lte"] = end_date

            # Aggregate statistics
            pipeline = [
                {"$match": date_filter},
                {
                    "$group": {
                        "_id": None,
                        "total_actions": {"$sum": 1},
                        "actions_by_type": {
                            "$push": "$action_type"
                        },
                        "active_suspensions": {
                            "$sum": {
                                "$cond": [
                                    {
                                        "$and": [
                                            {"$eq": ["$action_type", "temporary_suspension"]},
                                            {"$eq": ["$is_active", True]}
                                        ]
                                    },
                                    1,
                                    0
                                ]
                            }
                        },
                        "total_points_deducted": {
                            "$sum": {
                                "$cond": [
                                    {"$gt": ["$points_affected", 0]},
                                    "$points_affected",
                                    0
                                ]
                            }
                        }
                    }
                }
            ]

            result = await db.moderation_actions.aggregate(pipeline).to_list(1)

            if not result:
                return ModerationStats(
                    total_actions=0,
                    actions_by_type={},
                    active_suspensions=0,
                    points_deducted_total=0,
                    content_removed_total=0,
                    average_response_time_hours=0.0
                )

            stats = result[0]

            # Count actions by type
            actions_by_type = {}
            for action_type in stats.get("actions_by_type", []):
                actions_by_type[action_type] = actions_by_type.get(action_type, 0) + 1

            # Count content removals
            content_removed = actions_by_type.get("content_removal", 0)

            return ModerationStats(
                total_actions=stats.get("total_actions", 0),
                actions_by_type=actions_by_type,
                active_suspensions=stats.get("active_suspensions", 0),
                points_deducted_total=stats.get("total_points_deducted", 0),
                content_removed_total=content_removed,
                average_response_time_hours=await self._calculate_average_response_time()
            )

        except Exception as e:
            logger.error(f"Error getting moderation stats: {str(e)}")
            raise

    # Helper methods
    async def _auto_assign_dispute(self, dispute_id: str) -> None:
        """Auto-assign dispute to appropriate moderator."""
        try:
            db = await self._get_db()

            # Find available moderators with language expertise
            # This is a simplified assignment - could be more sophisticated
            moderator = await db.users.find_one({
                "role": {"$in": ["moderator", "admin"]},
                "is_active": True
            })

            if moderator:
                await db.disputes.update_one(
                    {"_id": ObjectId(dispute_id)},
                    {"$set": {"assigned_moderator_id": str(moderator["_id"])}}
                )

        except Exception as e:
            logger.error(f"Error auto-assigning dispute: {str(e)}")

    async def _notify_moderators_new_dispute(self, dispute_doc: Dict[str, Any]) -> None:
        """Notify moderators of new dispute."""
        # Implementation would integrate with notification service
        logger.info(f"New dispute created: {dispute_doc['title']}")

    async def _log_dispute_action(
        self,
        dispute_id: str,
        moderator_id: str,
        update_data: DisputeUpdate
    ) -> None:
        """Log moderator action on dispute."""
        try:
            db = await self._get_db()

            action_log = {
                "_id": ObjectId(),
                "dispute_id": dispute_id,
                "moderator_id": moderator_id,
                "action": "update",
                "changes": update_data.dict(exclude_unset=True),
                "timestamp": datetime.utcnow()
            }

            await db.dispute_action_logs.insert_one(action_log)

        except Exception as e:
            logger.error(f"Error logging dispute action: {str(e)}")

    async def _escalate_content_report(self, report_id: str) -> None:
        """Escalate high-severity content report."""
        try:
            db = await self._get_db()

            await db.content_reports.update_one(
                {"_id": ObjectId(report_id)},
                {"$set": {"status": "escalated", "escalated_at": datetime.utcnow()}}
            )

            # Notify senior moderators
            logger.info(f"Content report escalated: {report_id}")

        except Exception as e:
            logger.error(f"Error escalating content report: {str(e)}")

    async def _apply_moderation_action(
        self,
        action_data: ModerationActionCreate,
        action_id: ObjectId
    ) -> None:
        """Apply the actual moderation action."""
        try:
            db = await self._get_db()

            if action_data.action_type == ModerationAction.POINTS_DEDUCTION:
                # Deduct points from user
                await db.users.update_one(
                    {"_id": ObjectId(action_data.target_user_id)},
                    {"$inc": {"total_points": -action_data.points_affected}}
                )

            elif action_data.action_type == ModerationAction.CONTENT_REMOVAL:
                # Mark content as removed
                if action_data.target_content_id:
                    await db.submissions.update_one(
                        {"_id": ObjectId(action_data.target_content_id)},
                        {"$set": {"status": "removed", "removed_at": datetime.utcnow()}}
                    )

            elif action_data.action_type in [
                ModerationAction.TEMPORARY_SUSPENSION,
                ModerationAction.PERMANENT_BAN
            ]:
                # Update user status
                suspension_end = None
                if action_data.duration_hours:
                    suspension_end = datetime.utcnow() + timedelta(hours=action_data.duration_hours)

                await db.users.update_one(
                    {"_id": ObjectId(action_data.target_user_id)},
                    {
                        "$set": {
                            "is_suspended": True,
                            "suspension_end": suspension_end,
                            "suspension_reason": action_data.reason
                        }
                    }
                )

        except Exception as e:
            logger.error(f"Error applying moderation action: {str(e)}")
            raise

    async def _notify_user_moderation_action(
        self,
        user_id: str,
        action_doc: Dict[str, Any]
    ) -> None:
        """Notify user of moderation action."""
        # Implementation would integrate with notification service
        logger.info(f"Moderation action applied to user {user_id}: {action_doc['action_type']}")

    async def _calculate_average_response_time(self) -> float:
        """Calculate average response time for moderation actions."""
        try:
            db = await self._get_db()

            pipeline = [
                {
                    "$lookup": {
                        "from": "content_reports",
                        "localField": "target_content_id",
                        "foreignField": "content_id",
                        "as": "related_report"
                    }
                },
                {"$unwind": "$related_report"},
                {
                    "$addFields": {
                        "response_time_hours": {
                            "$divide": [
                                {"$subtract": ["$executed_at", "$related_report.created_at"]},
                                3600000  # Convert milliseconds to hours
                            ]
                        }
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "avg_response_time": {"$avg": "$response_time_hours"}
                    }
                }
            ]

            result = await db.moderation_actions.aggregate(pipeline).to_list(1)
            return result[0]["avg_response_time"] if result else 0.0

        except Exception as e:
            logger.error(f"Error calculating average response time: {str(e)}")
            return 0.0