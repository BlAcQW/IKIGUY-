"""
Visitor Service.

Handles visitor capture, initial onboarding, and first-time communications.
Manages the transition from first-time visitor to engaged member.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from bson import ObjectId

from app.core.database import get_database
from app.models.user import User, StageTransition
from app.services.user_service import user_service

logger = logging.getLogger(__name__)


class VisitorService:
    """
    Service for managing visitor capture and onboarding.

    Handles:
    - Capturing new visitors or updating existing
    - Triggering immediate welcome communications
    - Auto-assigning to cell groups
    - Scheduling follow-up communications
    - Retrieving recent visitors for follow-up
    """

    def __init__(self):
        """Initialize the visitor service."""
        self.db = None

    def set_database(self, db):
        """Set the database connection."""
        self.db = db

    async def capture_visitor(
        self,
        visitor_data: Dict[str, Any],
        organization_id: str,
        captured_by_user_id: str,
        send_immediate_welcome: bool = True
    ) -> User:
        """
        Capture new visitor or update existing.

        Creates a new user record or updates an existing visitor,
        sets initial journey stage, and triggers welcome communications
        if enabled.

        Args:
            visitor_data: Visitor information (phone, name, email, etc.)
            organization_id: Organization ID
            captured_by_user_id: ID of user who captured this visitor
            send_immediate_welcome: Whether to send immediate welcome message

        Returns:
            User: Created or updated user object

        Raises:
            ValueError: If required fields are missing
            Exception: If database operation fails
        """
        if self.db is None:
            self.db = get_database()

        logger.info(f"Capturing visitor: {visitor_data.get('phone')}")

        # Validate required fields
        if not visitor_data.get("phone"):
            raise ValueError("Phone number is required")

        # Check if visitor already exists by phone
        existing_user = await user_service.get_user_by_phone(visitor_data["phone"])

        if existing_user:
            logger.info(f"Updating existing visitor: {existing_user.id}")

            # Increment visit count
            update_data = {
                "visit_count": (existing_user.visit_count or 0) + 1,
                "last_visit_date": datetime.utcnow(),
                "consecutive_absences": 0,  # Reset absences on new visit
                "updated_at": datetime.utcnow()
            }

            # Update any provided fields
            for field in ["name", "full_name", "email", "branch_id", "first_visit_source"]:
                if field in visitor_data and visitor_data[field]:
                    update_data[field] = visitor_data[field]

            # Update user
            await self.db.users.update_one(
                {"_id": existing_user.id},
                {"$set": update_data}
            )

            # Fetch updated user
            updated_user_doc = await self.db.users.find_one({"_id": existing_user.id})
            user = User(**updated_user_doc)

            logger.info(f"Updated visitor: Visit count = {user.visit_count}")

        else:
            # Create new visitor
            logger.info("Creating new visitor")

            user_doc = {
                "phone": visitor_data["phone"],
                "name": visitor_data.get("name") or visitor_data.get("full_name"),
                "full_name": visitor_data.get("full_name") or visitor_data.get("name"),
                "email": visitor_data.get("email"),
                "organization_id": organization_id,  # Store organization ID
                "branch_id": ObjectId(visitor_data["branch_id"]) if visitor_data.get("branch_id") else None,

                # Member status and journey tracking
                "member_status": "visitor",
                "current_spiritual_stage": "first_timer",
                "current_cell_stage": None,
                "current_ministry_stage": None,

                # Visit tracking
                "first_visit_date": datetime.utcnow(),
                "visit_count": 1,
                "last_visit_date": datetime.utcnow(),
                "consecutive_absences": 0,
                "first_visit_source": visitor_data.get("first_visit_source"),
                "captured_by_user_id": ObjectId(captured_by_user_id) if captured_by_user_id else None,

                # Journey history
                "stage_history": [
                    {
                        "previous_stage": None,
                        "new_stage": "first_timer",
                        "journey_type": "spiritual",
                        "transitioned_at": datetime.utcnow(),
                        "transitioned_by_user_id": ObjectId(captured_by_user_id) if captured_by_user_id else None,
                        "notes": "Initial visitor capture"
                    }
                ],
                "enrichment_history": [],
                "life_events": [],

                # Communication preferences
                "preferred_communication_channel": visitor_data.get("preferred_communication_channel", "sms"),
                "allow_automated_communications": visitor_data.get("allow_automated_communications", True),

                # Engagement metrics
                "sms_sent_count": 0,
                "whatsapp_sent_count": 0,
                "calls_made_count": 0,
                "calls_answered_count": 0,

                # Roles
                "roles": ["member"],
                "volunteer_roles": [],

                # Timestamps
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "last_active": datetime.utcnow()
            }

            # Add optional profile fields if provided
            for field in ["date_of_birth", "gender", "occupation", "marital_status", "address",
                         "emergency_contact_name", "emergency_contact_phone"]:
                if field in visitor_data and visitor_data[field]:
                    user_doc[field] = visitor_data[field]

            result = await self.db.users.insert_one(user_doc)
            user_doc["_id"] = result.inserted_id
            user = User(**user_doc)

            logger.info(f"Created new visitor: {user.id}")

        # Send immediate welcome if enabled
        if send_immediate_welcome and user.allow_automated_communications:
            logger.info("Triggering immediate welcome communication")
            try:
                await self.send_welcome_communication(
                    user_id=str(user.id),
                    organization_id=organization_id
                )
            except Exception as e:
                logger.error(f"Failed to send welcome communication: {e}")
                # Don't fail the whole operation if welcome fails

        return user

    async def send_welcome_communication(
        self,
        user_id: str,
        organization_id: str,
        stage_name: str = "first_timer",
        channels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send welcome communication to visitor.

        Fetches the journey stage configuration and sends welcome
        message via configured channels. This will be implemented
        fully in Phase 3 with CommunicationOrchestrationService.

        Args:
            user_id: User ID to send welcome to
            organization_id: Organization ID
            stage_name: Journey stage name (default: "first_timer")
            channels: Communication channels (default: from stage config)

        Returns:
            dict: Result with status and details

        Note:
            This is a placeholder that will be fully implemented in Phase 3
            when CommunicationOrchestrationService is created.
        """
        if self.db is None:
            self.db = get_database()

        logger.info(f"Sending welcome communication to user {user_id}")

        # Fetch journey stage config
        stage = await self.db.journey_stages.find_one({
            "organization_id": ObjectId(organization_id),
            "stage_name": stage_name,
            "is_active": True
        })

        if not stage:
            logger.warning(f"Journey stage '{stage_name}' not found for organization {organization_id}")
            return {
                "status": "skipped",
                "reason": "Journey stage not configured"
            }

        # Check if auto-send is enabled
        if not stage.get("auto_send_welcome", True):
            logger.info(f"Auto-send welcome disabled for stage {stage_name}")
            return {
                "status": "skipped",
                "reason": "Auto-send welcome disabled"
            }

        # Placeholder: Will be implemented with CommunicationOrchestrationService in Phase 3
        logger.info(f"Welcome communication will be sent via: {channels or stage.get('welcome_channels', ['sms'])}")

        return {
            "status": "scheduled",
            "stage_id": str(stage["_id"]),
            "channels": channels or stage.get("welcome_channels", ["sms"]),
            "message": "Welcome communication scheduling will be implemented in Phase 3"
        }

    async def assign_to_cell_group(
        self,
        user_id: str,
        cell_group_id: str,
        assigned_by_user_id: str
    ) -> User:
        """
        Assign visitor to a cell group and cell leader.

        Updates the user's cell group assignment and automatically
        assigns them to the cell leader.

        Args:
            user_id: User ID to assign
            cell_group_id: Cell group ID
            assigned_by_user_id: ID of user making the assignment

        Returns:
            User: Updated user object

        Raises:
            ValueError: If cell group not found or is full
            Exception: If database operation fails
        """
        if self.db is None:
            self.db = get_database()

        logger.info(f"Assigning user {user_id} to cell group {cell_group_id}")

        # Fetch cell group
        cell_group = await self.db.cell_groups.find_one({"_id": ObjectId(cell_group_id)})
        if not cell_group:
            raise ValueError(f"Cell group {cell_group_id} not found")

        # Check if cell group is full
        if cell_group.get("is_full", False):
            raise ValueError(f"Cell group {cell_group.get('name')} is full")

        # Update user assignment
        update_data = {
            "cell_group_id": ObjectId(cell_group_id),
            "assigned_cell_leader_id": cell_group.get("cell_leader_id"),
            "zone_id": cell_group.get("zone_id"),
            "updated_at": datetime.utcnow()
        }

        # Add to enrichment history
        enrichment_entry = {
            "field_name": "cell_group_assignment",
            "previous_value": None,
            "new_value": str(cell_group_id),
            "enriched_by_user_id": ObjectId(assigned_by_user_id),
            "enriched_by_role": "admin",  # Will be determined by actual role in Phase 5
            "enriched_at": datetime.utcnow(),
            "notes": f"Assigned to cell group: {cell_group.get('name')}"
        }

        await self.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": update_data,
                "$push": {"enrichment_history": enrichment_entry}
            }
        )

        # Update cell group member count
        await self.db.cell_groups.update_one(
            {"_id": ObjectId(cell_group_id)},
            {"$inc": {"current_member_count": 1}}
        )

        # Fetch and return updated user
        updated_user_doc = await self.db.users.find_one({"_id": ObjectId(user_id)})
        user = User(**updated_user_doc)

        logger.info(f"Successfully assigned user to cell group")

        return user

    async def get_recent_visitors(
        self,
        organization_id: str,
        days: int = 7,
        limit: int = 50,
        skip: int = 0
    ) -> List[User]:
        """
        Get visitors (users without branch_id) captured in the last N days.

        Visitors are users from other churches who registered at events like IMPACT.
        They are identified by NOT having a branch_id (Action Chapel members have branch_id).

        Args:
            organization_id: Organization ID
            days: Number of days to look back (default: 7)
            limit: Maximum number of results (default: 50)
            skip: Number of results to skip for pagination (default: 0)

        Returns:
            List[User]: List of recent visitors sorted by created_at (newest first)
        """
        if self.db is None:
            self.db = get_database()

        logger.info(f"Fetching visitors (users without branch_id) from last {days} days")

        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Visitors = users WITHOUT branch_id (from other churches)
        # Sort by created_at since first_visit_date may not be set for all
        cursor = self.db.users.find({
            "created_at": {"$gte": cutoff_date},
            "$or": [
                {"branch_id": {"$exists": False}},
                {"branch_id": None},
                {"branch_id": ""}
            ]
        }).sort("created_at", -1).skip(skip).limit(limit)

        visitors = []
        async for doc in cursor:
            try:
                visitors.append(User(**doc))
            except Exception as e:
                logger.error(f"Error parsing user document: {e}")
                continue

        logger.info(f"Found {len(visitors)} recent visitors")

        return visitors

    async def get_visitors_by_stage(
        self,
        organization_id: str,
        stage_name: str,
        limit: int = 100,
        skip: int = 0
    ) -> List[User]:
        """
        Get all visitors at a specific spiritual stage.

        Args:
            organization_id: Organization ID
            stage_name: Stage name (e.g., "first_timer", "second_timer")
            limit: Maximum number of results (default: 100)
            skip: Number of results to skip for pagination (default: 0)

        Returns:
            List[User]: List of visitors at this stage
        """
        if self.db is None:
            self.db = get_database()

        logger.info(f"Fetching visitors at stage: {stage_name}")

        cursor = self.db.users.find({
            "current_spiritual_stage": stage_name,
            "member_status": "visitor"
        }).sort("first_visit_date", -1).skip(skip).limit(limit)

        visitors = []
        async for doc in cursor:
            try:
                visitors.append(User(**doc))
            except Exception as e:
                logger.error(f"Error parsing user document: {e}")
                continue

        logger.info(f"Found {len(visitors)} visitors at stage {stage_name}")

        return visitors

    async def update_absence_tracking(
        self,
        organization_id: str,
        days_since_last_visit: int = 14
    ) -> Dict[str, int]:
        """
        Update consecutive absences for members who haven't visited recently.

        This should be run as a background job (weekly) to track member engagement.

        Args:
            organization_id: Organization ID
            days_since_last_visit: Threshold for marking absence (default: 14 days)

        Returns:
            dict: Summary with count of updated members
        """
        if self.db is None:
            self.db = get_database()

        logger.info(f"Updating absence tracking (threshold: {days_since_last_visit} days)")

        cutoff_date = datetime.utcnow() - timedelta(days=days_since_last_visit)

        # Find members who haven't visited since cutoff
        result = await self.db.users.update_many(
            {
                "last_visit_date": {"$lt": cutoff_date},
                "member_status": {"$in": ["visitor", "active_member"]}
            },
            {
                "$inc": {"consecutive_absences": 1},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

        logger.info(f"Updated {result.modified_count} members with consecutive absences")

        return {
            "updated_count": result.modified_count,
            "threshold_days": days_since_last_visit
        }


# Global instance
visitor_service = VisitorService()
