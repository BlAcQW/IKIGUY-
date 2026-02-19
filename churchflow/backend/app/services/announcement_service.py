"""
Announcement Service.

Handles business logic for announcements.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.announcement import Announcement
from app.core.database import get_database


class AnnouncementService:
    """Service for managing announcements."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize service.

        Args:
            db: MongoDB database instance
        """
        self.db = db

    async def create_announcement(
        self,
        announcement_data: Dict[str, Any],
        organization_id: str,
        created_by_user_id: str
    ) -> Announcement:
        """
        Create a new announcement.

        Args:
            announcement_data: Announcement information
            organization_id: Organization ID
            created_by_user_id: User creating this announcement

        Returns:
            Created Announcement object

        Raises:
            ValueError: If validation fails
        """
        # Add metadata
        announcement_data["organization_id"] = ObjectId(organization_id)
        announcement_data["created_by_user_id"] = ObjectId(created_by_user_id)
        announcement_data["created_at"] = datetime.utcnow()
        announcement_data["updated_at"] = datetime.utcnow()

        # Convert event_id to ObjectId if provided
        if announcement_data.get("event_id"):
            announcement_data["event_id"] = ObjectId(announcement_data["event_id"])

        # Validate with Pydantic model
        announcement = Announcement(**announcement_data)

        # Insert into database
        result = await self.db.announcements.insert_one(announcement.model_dump(by_alias=True, exclude={"id"}))

        # Return created announcement
        created_doc = await self.db.announcements.find_one({"_id": result.inserted_id})
        return Announcement(**created_doc)

    async def get_announcement(
        self,
        announcement_id: str,
        organization_id: Optional[str] = None
    ) -> Optional[Announcement]:
        """
        Get announcement by ID.

        Args:
            announcement_id: Announcement ID
            organization_id: Optional organization ID for filtering

        Returns:
            Announcement object or None if not found
        """
        query = {"_id": ObjectId(announcement_id)}
        if organization_id:
            query["organization_id"] = ObjectId(organization_id)

        doc = await self.db.announcements.find_one(query)
        if not doc:
            return None

        return Announcement(**doc)

    async def list_announcements(
        self,
        organization_id: str,
        is_active: Optional[bool] = None,
        include_past: bool = False
    ) -> List[Announcement]:
        """
        List announcements for an organization.

        Args:
            organization_id: Organization ID
            is_active: Optional filter by active status
            include_past: Whether to include past announcements (end_date < now)

        Returns:
            List of Announcement objects
        """
        query: Dict[str, Any] = {"organization_id": ObjectId(organization_id)}

        if is_active is not None:
            query["is_active"] = is_active

        # Filter by date ranges
        now = datetime.utcnow()
        date_filters = []
        
        # Start date filter - show if start_date is None or start_date <= now
        date_filters.append({
            "$or": [
                {"start_date": None},
                {"start_date": {"$lte": now}}
            ]
        })
        
        # End date filter (if not including past) - show if end_date is None or end_date >= now
        if not include_past:
            date_filters.append({
                "$or": [
                    {"end_date": None},
                    {"end_date": {"$gte": now}}
                ]
            })
        
        if date_filters:
            if "$and" in query:
                query["$and"].extend(date_filters)
            else:
                query["$and"] = date_filters

        cursor = self.db.announcements.find(query).sort("display_order", 1).sort("created_at", -1)
        docs = await cursor.to_list(length=None)

        return [Announcement(**doc) for doc in docs]

    async def get_public_announcements(
        self,
        organization_id: str
    ) -> List[Announcement]:
        """
        Get active announcements visible on landing page.

        Args:
            organization_id: Organization ID

        Returns:
            List of active Announcement objects (hero announcements first, then by display_order)
        """
        now = datetime.utcnow()

        query = {
            "organization_id": ObjectId(organization_id),
            "is_active": True,
            "$and": [
                {
                    "$or": [
                        {"start_date": None},
                        {"start_date": {"$lte": now}}
                    ]
                },
                {
                    "$or": [
                        {"end_date": None},
                        {"end_date": {"$gte": now}}
                    ]
                }
            ]
        }

        # Sort: hero announcements first (is_hero: true), then by display_order, then by created_at
        cursor = self.db.announcements.find(query).sort([
            ("is_hero", -1),  # Hero announcements first (true = -1 comes before false = 1)
            ("display_order", 1),
            ("created_at", -1)
        ])
        docs = await cursor.to_list(length=None)

        return [Announcement(**doc) for doc in docs]

    async def update_announcement(
        self,
        announcement_id: str,
        organization_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[Announcement]:
        """
        Update an announcement.

        Args:
            announcement_id: Announcement ID
            organization_id: Organization ID
            update_data: Fields to update

        Returns:
            Updated Announcement object or None if not found

        Raises:
            ValueError: If validation fails
        """
        # Convert event_id to ObjectId if provided
        if update_data.get("event_id"):
            update_data["event_id"] = ObjectId(update_data["event_id"])
        elif "event_id" in update_data and update_data["event_id"] is None:
            update_data["event_id"] = None

        update_data["updated_at"] = datetime.utcnow()

        # Remove None values for partial update
        update_data = {k: v for k, v in update_data.items() if v is not None}

        result = await self.db.announcements.update_one(
            {"_id": ObjectId(announcement_id), "organization_id": ObjectId(organization_id)},
            {"$set": update_data}
        )

        if result.matched_count == 0:
            return None

        # Return updated announcement
        doc = await self.db.announcements.find_one({"_id": ObjectId(announcement_id)})
        return Announcement(**doc)

    async def delete_announcement(
        self,
        announcement_id: str,
        organization_id: str
    ) -> bool:
        """
        Delete an announcement (soft delete by setting is_active=False).

        Args:
            announcement_id: Announcement ID
            organization_id: Organization ID

        Returns:
            True if deleted, False if not found
        """
        result = await self.db.announcements.update_one(
            {"_id": ObjectId(announcement_id), "organization_id": ObjectId(organization_id)},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )

        return result.matched_count > 0

    async def hard_delete_announcement(
        self,
        announcement_id: str,
        organization_id: str
    ) -> bool:
        """
        Permanently delete an announcement.

        Args:
            announcement_id: Announcement ID
            organization_id: Organization ID

        Returns:
            True if deleted, False if not found
        """
        result = await self.db.announcements.delete_one(
            {"_id": ObjectId(announcement_id), "organization_id": ObjectId(organization_id)}
        )

        return result.deleted_count > 0

