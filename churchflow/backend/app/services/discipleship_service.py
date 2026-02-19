"""
Discipleship Service.

Manages member journey progression through discipleship stages including:
- Advancing members between stages
- Scheduling automated follow-up communications
- Tracking journey analytics and conversion funnels
- Managing custom and predefined stages
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from bson import ObjectId

from app.core.database import get_database
from app.models.user import User, StageTransition
from app.models.journey_stage import JourneyStage, ScheduledFollowup

logger = logging.getLogger(__name__)


class DiscipleshipService:
    """
    Service for managing member discipleship journeys.

    Handles:
    - Stage progression (first_timer → new_convert → baptism_class → baptized)
    - Automated follow-up scheduling
    - Journey analytics and funnel metrics
    - Custom stage management
    """

    def __init__(self):
        """Initialize the discipleship service."""
        self.db = None

    def set_database(self, db):
        """Set the database connection."""
        self.db = db

    async def advance_member_stage(
        self,
        user_id: str,
        journey_type: str,
        new_stage: str,
        transitioned_by_user_id: str,
        notes: Optional[str] = None
    ) -> User:
        """
        Advance member to a new journey stage.

        Updates the member's current stage, records transition in history,
        triggers stage-specific welcome communication, and schedules follow-ups.

        Args:
            user_id: User ID to advance
            journey_type: Type of journey (spiritual, cell, ministry)
            new_stage: New stage name
            transitioned_by_user_id: ID of user making the advancement
            notes: Optional notes about the transition

        Returns:
            User: Updated user object

        Raises:
            ValueError: If stage not found or invalid journey type
            Exception: If database operation fails
        """
        if self.db is None:
            self.db = get_database()

        logger.info(f"Advancing user {user_id} to {journey_type} stage: {new_stage}")

        # Validate journey type
        if journey_type not in ["spiritual", "cell", "ministry"]:
            raise ValueError(f"Invalid journey type: {journey_type}")

        # Fetch user
        user_doc = await self.db.users.find_one({"_id": ObjectId(user_id)})
        if not user_doc:
            raise ValueError(f"User {user_id} not found")

        user = User(**user_doc)

        # Get current stage for this journey type
        if journey_type == "spiritual":
            previous_stage = user.current_spiritual_stage
            stage_field = "current_spiritual_stage"
        elif journey_type == "cell":
            previous_stage = user.current_cell_stage
            stage_field = "current_cell_stage"
        else:  # ministry
            previous_stage = user.current_ministry_stage
            stage_field = "current_ministry_stage"

        # Create stage transition record
        transition = {
            "previous_stage": previous_stage,
            "new_stage": new_stage,
            "journey_type": journey_type,
            "transitioned_at": datetime.utcnow(),
            "transitioned_by_user_id": ObjectId(transitioned_by_user_id) if transitioned_by_user_id else None,
            "notes": notes
        }

        # Update user document
        update_data = {
            stage_field: new_stage,
            "updated_at": datetime.utcnow()
        }

        await self.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": update_data,
                "$push": {"stage_history": transition}
            }
        )

        # Fetch journey stage configuration
        stage_config = await self.db.journey_stages.find_one({
            "stage_name": new_stage,
            "journey_type": journey_type,
            "is_active": True
        })

        if stage_config:
            logger.info(f"Found stage config for {new_stage}")

            # Schedule follow-up communications
            try:
                await self.schedule_stage_followups(
                    user_id=user_id,
                    stage=JourneyStage(**stage_config)
                )
            except Exception as e:
                logger.error(f"Failed to schedule follow-ups: {e}")
                # Don't fail the whole operation if scheduling fails

        # Fetch and return updated user
        updated_user_doc = await self.db.users.find_one({"_id": ObjectId(user_id)})
        updated_user = User(**updated_user_doc)

        logger.info(f"Successfully advanced user to {new_stage}")

        return updated_user

    async def schedule_stage_followups(
        self,
        user_id: str,
        stage: JourneyStage
    ) -> List[Dict[str, Any]]:
        """
        Schedule automated follow-up communications based on stage configuration.

        Creates scheduled communication records for each follow-up defined
        in the stage configuration.

        Args:
            user_id: User ID to schedule followups for
            stage: Journey stage configuration with followup schedules

        Returns:
            List[Dict]: List of created scheduled communication records

        Note:
            This creates records in scheduled_communications collection.
            Actual sending is handled by SchedulerService in Phase 3.
        """
        if self.db is None:
            self.db = get_database()

        logger.info(f"Scheduling follow-ups for user {user_id}, stage {stage.stage_name}")

        scheduled_comms = []

        # Fetch user for template variables
        user_doc = await self.db.users.find_one({"_id": ObjectId(user_id)})
        if not user_doc:
            logger.error(f"User {user_id} not found")
            return []

        user = User(**user_doc)

        # Schedule each follow-up
        for followup in stage.scheduled_followups:
            try:
                scheduled_for = datetime.utcnow() + timedelta(days=followup.delay_days)

                # Prepare template variables
                template_vars = {
                    "name": user.full_name or user.name or "Friend",
                    "stage_name": stage.stage_display_name,
                    "delay_days": str(followup.delay_days)
                }

                # Create deduplication key
                dedup_key = f"{user_id}_{stage.stage_name}_day_{followup.delay_days}"

                # Check if already scheduled
                existing = await self.db.scheduled_communications.find_one({
                    "deduplication_key": dedup_key,
                    "status": "pending"
                })

                if existing:
                    logger.info(f"Follow-up already scheduled: {dedup_key}")
                    continue

                # Create scheduled communication record
                scheduled_comm = {
                    "organization_id": stage.organization_id,
                    "user_id": ObjectId(user_id),
                    "stage_id": stage.id,
                    "followup_type": f"day_{followup.delay_days}",
                    "scheduled_for": scheduled_for,
                    "channels": followup.communication_channels,
                    "message_template": followup.message_template,
                    "template_variables": template_vars,
                    "status": "pending",
                    "deduplication_key": dedup_key,
                    "retry_count": 0,
                    "max_retries": 3,
                    "created_at": datetime.utcnow()
                }

                result = await self.db.scheduled_communications.insert_one(scheduled_comm)
                scheduled_comm["_id"] = result.inserted_id
                scheduled_comms.append(scheduled_comm)

                logger.info(f"Scheduled {followup.delay_days}-day follow-up for {scheduled_for}")

            except Exception as e:
                logger.error(f"Failed to schedule follow-up: {e}")
                continue

        logger.info(f"Scheduled {len(scheduled_comms)} follow-ups")

        return scheduled_comms

    async def get_members_by_stage(
        self,
        organization_id: str,
        journey_type: str,
        stage: str,
        limit: int = 100,
        skip: int = 0
    ) -> List[User]:
        """
        Get all members at a specific journey stage.

        Useful for creating targeted campaigns or generating reports.

        Args:
            organization_id: Organization ID
            journey_type: Type of journey (spiritual, cell, ministry)
            stage: Stage name
            limit: Maximum number of results (default: 100)
            skip: Number of results to skip for pagination (default: 0)

        Returns:
            List[User]: List of members at this stage
        """
        if self.db is None:
            self.db = get_database()

        logger.info(f"Fetching members at {journey_type} stage: {stage}")

        # Determine field to query based on journey type
        if journey_type == "spiritual":
            stage_field = "current_spiritual_stage"
        elif journey_type == "cell":
            stage_field = "current_cell_stage"
        elif journey_type == "ministry":
            stage_field = "current_ministry_stage"
        else:
            raise ValueError(f"Invalid journey type: {journey_type}")

        # Query members at this stage
        cursor = self.db.users.find({
            stage_field: stage
        }).sort("first_visit_date", -1).skip(skip).limit(limit)

        members = []
        async for doc in cursor:
            try:
                members.append(User(**doc))
            except Exception as e:
                logger.error(f"Error parsing user document: {e}")
                continue

        logger.info(f"Found {len(members)} members at {journey_type} stage {stage}")

        return members

    async def get_journey_analytics(
        self,
        organization_id: str,
        journey_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get journey analytics including funnel metrics and conversion rates.

        Provides insights into member progression through journey stages.

        Args:
            organization_id: Organization ID
            journey_type: Type of journey (spiritual, cell, ministry)
            start_date: Start date for filtering (optional)
            end_date: End date for filtering (optional)

        Returns:
            dict: Analytics data with stage counts, conversion rates, etc.
        """
        if self.db is None:
            self.db = get_database()

        logger.info(f"Calculating {journey_type} journey analytics")

        # Determine stage field
        if journey_type == "spiritual":
            stage_field = "current_spiritual_stage"
        elif journey_type == "cell":
            stage_field = "current_cell_stage"
        elif journey_type == "ministry":
            stage_field = "current_ministry_stage"
        else:
            raise ValueError(f"Invalid journey type: {journey_type}")

        # Build date filter if provided
        date_filter = {}
        if start_date:
            date_filter["$gte"] = start_date
        if end_date:
            date_filter["$lte"] = end_date

        # Aggregate member counts by stage
        pipeline = [
            {
                "$match": {
                    stage_field: {"$ne": None}
                }
            }
        ]

        # Add date filter if provided
        if date_filter:
            pipeline[0]["$match"]["first_visit_date"] = date_filter

        pipeline.extend([
            {
                "$group": {
                    "_id": f"${stage_field}",
                    "count": {"$sum": 1}
                }
            },
            {
                "$sort": {"count": -1}
            }
        ])

        stage_counts = {}
        async for result in self.db.users.aggregate(pipeline):
            stage_name = result["_id"]
            count = result["count"]
            stage_counts[stage_name] = count

        # Fetch journey stages for ordering
        stages_cursor = self.db.journey_stages.find({
            "organization_id": ObjectId(organization_id),
            "journey_type": journey_type,
            "is_active": True
        }).sort("stage_order", 1)

        stages_list = []
        async for stage_doc in stages_cursor:
            stage_name = stage_doc["stage_name"]
            stages_list.append({
                "stage_name": stage_name,
                "stage_display_name": stage_doc["stage_display_name"],
                "stage_order": stage_doc["stage_order"],
                "count": stage_counts.get(stage_name, 0)
            })

        # Calculate conversion rates between stages
        conversions = []
        for i in range(len(stages_list) - 1):
            current_stage = stages_list[i]
            next_stage = stages_list[i + 1]

            if current_stage["count"] > 0:
                conversion_rate = (next_stage["count"] / current_stage["count"]) * 100
            else:
                conversion_rate = 0.0

            conversions.append({
                "from_stage": current_stage["stage_name"],
                "to_stage": next_stage["stage_name"],
                "conversion_rate": round(conversion_rate, 2),
                "from_count": current_stage["count"],
                "to_count": next_stage["count"]
            })

        # Calculate total members in journey
        total_members = sum(stage["count"] for stage in stages_list)

        analytics = {
            "journey_type": journey_type,
            "total_members": total_members,
            "stages": stages_list,
            "conversions": conversions,
            "date_range": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None
            }
        }

        logger.info(f"Journey analytics calculated: {total_members} members across {len(stages_list)} stages")

        return analytics

    async def get_stage_transition_history(
        self,
        user_id: str,
        journey_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get complete stage transition history for a member.

        Args:
            user_id: User ID
            journey_type: Filter by journey type (optional)

        Returns:
            List[Dict]: List of stage transitions, newest first
        """
        if self.db is None:
            self.db = get_database()

        logger.info(f"Fetching stage history for user {user_id}")

        user_doc = await self.db.users.find_one({"_id": ObjectId(user_id)})
        if not user_doc:
            raise ValueError(f"User {user_id} not found")

        user = User(**user_doc)
        stage_history = user.stage_history or []

        # Filter by journey type if specified
        if journey_type:
            stage_history = [
                transition for transition in stage_history
                if transition.journey_type == journey_type
            ]

        # Convert to dict and sort by date (newest first)
        history_list = [
            {
                "previous_stage": t.previous_stage,
                "new_stage": t.new_stage,
                "journey_type": t.journey_type,
                "transitioned_at": t.transitioned_at.isoformat() if t.transitioned_at else None,
                "transitioned_by_user_id": str(t.transitioned_by_user_id) if t.transitioned_by_user_id else None,
                "notes": t.notes
            }
            for t in stage_history
        ]

        history_list.sort(key=lambda x: x["transitioned_at"] or "", reverse=True)

        logger.info(f"Found {len(history_list)} stage transitions")

        return history_list


# Global instance
discipleship_service = DiscipleshipService()
