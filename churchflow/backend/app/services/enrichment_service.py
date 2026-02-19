"""
Enrichment Service.

Manages member data enrichment and life event tracking.
Provides full audit trail for all data updates by cell leaders,
zone leaders, and department heads.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from bson import ObjectId

from app.core.database import get_database
from app.models.user import User, DataEnrichment, LifeEvent

logger = logging.getLogger(__name__)


class EnrichmentService:
    """
    Service for managing member data enrichment and life events.

    Handles:
    - Updating member data with full audit trail
    - Recording significant life events
    - Tracking pending follow-ups
    - Retrieving enrichment history
    """

    def __init__(self):
        """Initialize the enrichment service."""
        self.db = None

    def set_database(self, db):
        """Set the database connection."""
        self.db = db

    async def enrich_member_data(
        self,
        user_id: str,
        field_updates: Dict[str, Any],
        enriched_by_user_id: str,
        enriched_by_role: str,
        notes: Optional[str] = None
    ) -> User:
        """
        Update member data with full audit trail.

        Records who enriched what data and when, enabling accountability
        and tracking data quality improvements over time.

        Args:
            user_id: User ID to enrich
            field_updates: Dictionary of field names and new values
            enriched_by_user_id: ID of user making the enrichment
            enriched_by_role: Role of enricher (cell_leader, zone_leader, etc.)
            notes: Optional notes about the enrichment

        Returns:
            User: Updated user object

        Raises:
            ValueError: If user not found or invalid fields
            Exception: If database operation fails

        Example:
            field_updates = {
                "occupation": "Teacher",
                "marital_status": "Married",
                "address": "123 Main St, Accra"
            }
        """
        if self.db is None:
            self.db = get_database()

        logger.info(f"Enriching data for user {user_id}")

        # Fetch user
        user_doc = await self.db.users.find_one({"_id": ObjectId(user_id)})
        if not user_doc:
            raise ValueError(f"User {user_id} not found")

        user = User(**user_doc)

        # Define allowed enrichment fields
        allowed_fields = {
            # Extended profile
            "date_of_birth", "gender", "occupation", "marital_status",
            "address", "emergency_contact_name", "emergency_contact_phone",
            # Basic info that can be enriched
            "email", "full_name",
            # Communication preferences
            "preferred_communication_channel",
            # Location
            "branch_id"
        }

        # Validate fields
        invalid_fields = set(field_updates.keys()) - allowed_fields
        if invalid_fields:
            raise ValueError(f"Cannot enrich these fields: {', '.join(invalid_fields)}")

        # Build update document and enrichment history
        update_data = {"updated_at": datetime.utcnow()}
        enrichment_entries = []

        for field_name, new_value in field_updates.items():
            # Get previous value
            previous_value = getattr(user, field_name, None)

            # Skip if value unchanged
            if previous_value == new_value:
                logger.info(f"Skipping unchanged field: {field_name}")
                continue

            # Add to update document
            update_data[field_name] = new_value

            # Create enrichment history entry
            enrichment_entry = {
                "field_name": field_name,
                "previous_value": str(previous_value) if previous_value else None,
                "new_value": str(new_value) if new_value else None,
                "enriched_by_user_id": ObjectId(enriched_by_user_id),
                "enriched_by_role": enriched_by_role,
                "enriched_at": datetime.utcnow(),
                "notes": notes
            }
            enrichment_entries.append(enrichment_entry)

            logger.info(f"Enriching {field_name}: {previous_value} → {new_value}")

        # Update user if there are changes
        if len(update_data) > 1:  # More than just updated_at
            await self.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": update_data,
                    "$push": {"enrichment_history": {"$each": enrichment_entries}}
                }
            )

            logger.info(f"Enriched {len(enrichment_entries)} fields for user {user_id}")
        else:
            logger.info("No changes to enrich")

        # Fetch and return updated user
        updated_user_doc = await self.db.users.find_one({"_id": ObjectId(user_id)})
        updated_user = User(**updated_user_doc)

        return updated_user

    async def record_life_event(
        self,
        user_id: str,
        event_type: str,
        event_date: datetime,
        description: str,
        recorded_by_user_id: str,
        requires_followup: bool = False
    ) -> User:
        """
        Record significant life event for member.

        Life events help cell leaders and zone leaders provide pastoral care
        and maintain meaningful relationships with members.

        Args:
            user_id: User ID
            event_type: Type of event (birth, death, marriage, job_change, etc.)
            event_date: Date when event occurred
            description: Event description
            recorded_by_user_id: ID of user recording the event
            requires_followup: Whether this event needs follow-up (default: False)

        Returns:
            User: Updated user object

        Raises:
            ValueError: If user not found or invalid event type
            Exception: If database operation fails

        Event types:
        - birth: Birth of child
        - death: Death of family member
        - marriage: Wedding
        - job_change: New job or job loss
        - relocation: Moving to new location
        - illness: Serious illness
        - celebration: Achievement or milestone
        """
        if self.db is None:
            self.db = get_database()

        logger.info(f"Recording {event_type} life event for user {user_id}")

        # Validate event type
        valid_event_types = {
            "birth", "death", "marriage", "job_change",
            "relocation", "illness", "celebration", "other"
        }
        if event_type not in valid_event_types:
            raise ValueError(f"Invalid event type: {event_type}. Must be one of {valid_event_types}")

        # Fetch user to verify existence
        user_doc = await self.db.users.find_one({"_id": ObjectId(user_id)})
        if not user_doc:
            raise ValueError(f"User {user_id} not found")

        # Create life event entry
        life_event = {
            "event_type": event_type,
            "event_date": event_date,
            "description": description,
            "recorded_by_user_id": ObjectId(recorded_by_user_id),
            "recorded_at": datetime.utcnow(),
            "requires_followup": requires_followup,
            "followup_completed": False
        }

        # Add life event to user
        await self.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$push": {"life_events": life_event},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

        logger.info(f"Recorded life event: {event_type} for user {user_id}")

        # Fetch and return updated user
        updated_user_doc = await self.db.users.find_one({"_id": ObjectId(user_id)})
        updated_user = User(**updated_user_doc)

        return updated_user

    async def mark_followup_completed(
        self,
        user_id: str,
        event_index: int,
        completed_by_user_id: str
    ) -> User:
        """
        Mark life event follow-up as completed.

        Args:
            user_id: User ID
            event_index: Index of life event in life_events array
            completed_by_user_id: ID of user marking follow-up complete

        Returns:
            User: Updated user object

        Raises:
            ValueError: If user not found or invalid event index
            Exception: If database operation fails
        """
        if self.db is None:
            self.db = get_database()

        logger.info(f"Marking follow-up completed for user {user_id}, event {event_index}")

        # Fetch user
        user_doc = await self.db.users.find_one({"_id": ObjectId(user_id)})
        if not user_doc:
            raise ValueError(f"User {user_id} not found")

        user = User(**user_doc)

        # Validate event index
        if not user.life_events or event_index >= len(user.life_events):
            raise ValueError(f"Invalid event index: {event_index}")

        # Update specific life event
        await self.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    f"life_events.{event_index}.followup_completed": True,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        logger.info(f"Marked follow-up completed")

        # Fetch and return updated user
        updated_user_doc = await self.db.users.find_one({"_id": ObjectId(user_id)})
        updated_user = User(**updated_user_doc)

        return updated_user

    async def get_pending_followups(
        self,
        organization_id: str,
        assigned_to_user_id: Optional[str] = None,
        limit: int = 50,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get life events requiring follow-up.

        Useful for cell leaders and zone leaders to track pastoral care needs.

        Args:
            organization_id: Organization ID
            assigned_to_user_id: Filter by assigned leader (cell/zone leader) (optional)
            limit: Maximum number of results (default: 50)
            skip: Number of results to skip for pagination (default: 0)

        Returns:
            List[Dict]: List of pending follow-ups with member details

        Each result contains:
        - user_id: Member's user ID
        - user_name: Member's name
        - event_type: Type of life event
        - event_date: When event occurred
        - description: Event description
        - days_pending: Days since event was recorded
        """
        if self.db is None:
            self.db = get_database()

        logger.info(f"Fetching pending follow-ups for organization {organization_id}")

        # Build aggregation pipeline
        pipeline = [
            {
                "$match": {
                    "life_events": {
                        "$elemMatch": {
                            "requires_followup": True,
                            "followup_completed": False
                        }
                    }
                }
            },
            {
                "$unwind": "$life_events"
            },
            {
                "$match": {
                    "life_events.requires_followup": True,
                    "life_events.followup_completed": False
                }
            }
        ]

        # Filter by assigned leader if specified
        if assigned_to_user_id:
            pipeline.insert(0, {
                "$match": {
                    "$or": [
                        {"assigned_cell_leader_id": ObjectId(assigned_to_user_id)},
                        {"zone_id": {"$in": await self._get_zone_ids_for_leader(assigned_to_user_id)}}
                    ]
                }
            })

        # Project relevant fields
        pipeline.append({
            "$project": {
                "user_id": "$_id",
                "user_name": {"$ifNull": ["$full_name", "$name"]},
                "user_phone": "$phone",
                "event_type": "$life_events.event_type",
                "event_date": "$life_events.event_date",
                "description": "$life_events.description",
                "recorded_at": "$life_events.recorded_at",
                "days_pending": {
                    "$divide": [
                        {"$subtract": [datetime.utcnow(), "$life_events.recorded_at"]},
                        86400000  # Convert milliseconds to days
                    ]
                }
            }
        })

        # Sort by days pending (oldest first)
        pipeline.append({"$sort": {"days_pending": -1}})

        # Pagination
        pipeline.extend([
            {"$skip": skip},
            {"$limit": limit}
        ])

        # Execute aggregation
        pending_followups = []
        async for result in self.db.users.aggregate(pipeline):
            # Convert ObjectId to string for JSON serialization
            result["user_id"] = str(result["user_id"])
            result["event_date"] = result["event_date"].isoformat() if result.get("event_date") else None
            result["recorded_at"] = result["recorded_at"].isoformat() if result.get("recorded_at") else None
            result["days_pending"] = int(result.get("days_pending", 0))
            pending_followups.append(result)

        logger.info(f"Found {len(pending_followups)} pending follow-ups")

        return pending_followups

    async def _get_zone_ids_for_leader(self, user_id: str) -> List[ObjectId]:
        """
        Get zone IDs where user is zone leader.

        Helper method for filtering pending follow-ups.

        Args:
            user_id: User ID

        Returns:
            List[ObjectId]: List of zone IDs
        """
        if self.db is None:
            self.db = get_database()

        zones = await self.db.zones.find({"zone_leader_id": ObjectId(user_id)}).to_list(length=100)
        return [zone["_id"] for zone in zones]

    async def get_enrichment_history(
        self,
        user_id: str,
        limit: int = 50,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get complete enrichment history for a member.

        Shows audit trail of who updated what data and when.

        Args:
            user_id: User ID
            limit: Maximum number of results (default: 50)
            skip: Number of results to skip for pagination (default: 0)

        Returns:
            List[Dict]: List of enrichment records, newest first

        Each record contains:
        - field_name: Field that was updated
        - previous_value: Old value
        - new_value: New value
        - enriched_by_user_id: ID of user who made the update
        - enriched_by_role: Role of enricher
        - enriched_at: Timestamp of update
        - notes: Optional notes
        """
        if self.db is None:
            self.db = get_database()

        logger.info(f"Fetching enrichment history for user {user_id}")

        # Fetch user
        user_doc = await self.db.users.find_one({"_id": ObjectId(user_id)})
        if not user_doc:
            raise ValueError(f"User {user_id} not found")

        user = User(**user_doc)
        enrichment_history = user.enrichment_history or []

        # Convert to dict and sort by date (newest first)
        history_list = [
            {
                "field_name": entry.field_name,
                "previous_value": entry.previous_value,
                "new_value": entry.new_value,
                "enriched_by_user_id": str(entry.enriched_by_user_id) if entry.enriched_by_user_id else None,
                "enriched_by_role": entry.enriched_by_role,
                "enriched_at": entry.enriched_at.isoformat() if entry.enriched_at else None,
                "notes": entry.notes
            }
            for entry in enrichment_history
        ]

        # Sort by enriched_at (newest first)
        history_list.sort(key=lambda x: x["enriched_at"] or "", reverse=True)

        # Pagination
        paginated_history = history_list[skip:skip + limit]

        logger.info(f"Found {len(history_list)} enrichment records, returning {len(paginated_history)}")

        return paginated_history

    async def get_life_events(
        self,
        user_id: str,
        event_type: Optional[str] = None,
        limit: int = 50,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get life events for a member.

        Args:
            user_id: User ID
            event_type: Filter by event type (optional)
            limit: Maximum number of results (default: 50)
            skip: Number of results to skip for pagination (default: 0)

        Returns:
            List[Dict]: List of life events, newest first
        """
        if self.db is None:
            self.db = get_database()

        logger.info(f"Fetching life events for user {user_id}")

        # Fetch user
        user_doc = await self.db.users.find_one({"_id": ObjectId(user_id)})
        if not user_doc:
            raise ValueError(f"User {user_id} not found")

        user = User(**user_doc)
        life_events = user.life_events or []

        # Filter by event type if specified
        if event_type:
            life_events = [event for event in life_events if event.event_type == event_type]

        # Convert to dict and sort by date (newest first)
        events_list = [
            {
                "event_type": event.event_type,
                "event_date": event.event_date.isoformat() if event.event_date else None,
                "description": event.description,
                "recorded_by_user_id": str(event.recorded_by_user_id) if event.recorded_by_user_id else None,
                "recorded_at": event.recorded_at.isoformat() if event.recorded_at else None,
                "requires_followup": event.requires_followup,
                "followup_completed": event.followup_completed
            }
            for event in life_events
        ]

        # Sort by event_date (newest first)
        events_list.sort(key=lambda x: x["event_date"] or "", reverse=True)

        # Pagination
        paginated_events = events_list[skip:skip + limit]

        logger.info(f"Found {len(events_list)} life events, returning {len(paginated_events)}")

        return paginated_events

    async def bulk_enrich_members(
        self,
        enrichments: List[Dict[str, Any]],
        enriched_by_user_id: str,
        enriched_by_role: str
    ) -> Dict[str, Any]:
        """
        Bulk enrich multiple members at once.

        Useful for importing data from external sources or mass updates.

        Args:
            enrichments: List of enrichment records
            enriched_by_user_id: ID of user making the enrichments
            enriched_by_role: Role of enricher

        Returns:
            dict: Summary with success/failure counts

        Each enrichment record should contain:
        - user_id: User ID to enrich
        - field_updates: Dictionary of field names and new values
        - notes: Optional notes

        Example:
            enrichments = [
                {
                    "user_id": "507f1f77bcf86cd799439011",
                    "field_updates": {"occupation": "Teacher"},
                    "notes": "Updated from church form"
                },
                ...
            ]
        """
        if self.db is None:
            self.db = get_database()

        logger.info(f"Bulk enriching {len(enrichments)} members")

        success_count = 0
        failure_count = 0
        errors = []

        for enrichment in enrichments:
            try:
                await self.enrich_member_data(
                    user_id=enrichment["user_id"],
                    field_updates=enrichment.get("field_updates", {}),
                    enriched_by_user_id=enriched_by_user_id,
                    enriched_by_role=enriched_by_role,
                    notes=enrichment.get("notes")
                )
                success_count += 1
            except Exception as e:
                failure_count += 1
                errors.append({
                    "user_id": enrichment.get("user_id"),
                    "error": str(e)
                })
                logger.error(f"Failed to enrich user {enrichment.get('user_id')}: {e}")

        summary = {
            "total": len(enrichments),
            "success": success_count,
            "failure": failure_count,
            "errors": errors
        }

        logger.info(f"Bulk enrichment complete: {success_count} success, {failure_count} failure")

        return summary


# Global instance
enrichment_service = EnrichmentService()
