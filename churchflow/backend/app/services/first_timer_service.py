"""
First Timer Service.

Handles business logic for first-time visitors and their journey toward membership.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.first_timer import FirstTimer, FirstTimerStats
from app.models.user import User


class FirstTimerService:
    """Service for managing first-time visitors."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize service.

        Args:
            db: MongoDB database instance
        """
        self.db = db

    async def create_first_timer(
        self,
        first_timer_data: Dict[str, Any],
        organization_id: str,
        created_by_user_id: Optional[str] = None
    ) -> FirstTimer:
        """
        Create a new first timer record.

        Args:
            first_timer_data: First timer information
            organization_id: Organization ID
            created_by_user_id: User creating this record

        Returns:
            Created FirstTimer object

        Raises:
            ValueError: If validation fails
        """
        # Auto-generate full_name if not provided
        if "full_name" not in first_timer_data:
            first_timer_data["full_name"] = f"{first_timer_data['first_name']} {first_timer_data['last_name']}"

        # Add metadata
        first_timer_data["organization_id"] = ObjectId(organization_id)
        
        # Handle created_by_user_id - use system ObjectId for public submissions
        if created_by_user_id:
            # If it's "system", use a placeholder ObjectId
            if created_by_user_id == "system":
                # Create a consistent system ObjectId (using all zeros except last byte)
                first_timer_data["created_by_user_id"] = ObjectId("000000000000000000000000")
            else:
                first_timer_data["created_by_user_id"] = ObjectId(created_by_user_id)
        else:
            # If None, use system ObjectId
            first_timer_data["created_by_user_id"] = ObjectId("000000000000000000000000")
        
        first_timer_data["created_at"] = datetime.utcnow()
        first_timer_data["updated_at"] = datetime.utcnow()
        first_timer_data["is_active"] = True
        first_timer_data["follow_up_status"] = first_timer_data.get("follow_up_status", "pending")
        first_timer_data["converted_to_member"] = False

        # Validate with Pydantic model
        first_timer = FirstTimer(**first_timer_data)

        # Insert into database
        result = await self.db.first_timers.insert_one(
            first_timer.model_dump(by_alias=True, exclude={"id"})
        )

        # Fetch and return created document
        created = await self.db.first_timers.find_one({"_id": result.inserted_id})
        return FirstTimer(**created)

    async def get_first_timers(
        self,
        organization_id: str,
        branch_id: Optional[str] = None,
        interest_type: Optional[str] = None,
        follow_up_status: Optional[str] = None,
        converted_to_member: Optional[bool] = None,
        is_active: bool = True,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Get paginated list of first timers with filters.

        Args:
            organization_id: Organization ID
            branch_id: Optional branch filter
            interest_type: Optional interest type filter
            follow_up_status: Optional follow-up status filter
            converted_to_member: Optional conversion filter
            is_active: Active status filter
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Dictionary with items, total, page, page_size
        """
        # Build query
        query = {
            "organization_id": ObjectId(organization_id),
            "is_active": is_active
        }

        if branch_id:
            query["branch_id"] = ObjectId(branch_id)
        if interest_type:
            query["interest_type"] = interest_type
        if follow_up_status:
            query["follow_up_status"] = follow_up_status
        if converted_to_member is not None:
            query["converted_to_member"] = converted_to_member

        # Get total count
        total = await self.db.first_timers.count_documents(query)

        # Get paginated results
        skip = (page - 1) * page_size
        cursor = self.db.first_timers.find(query).sort("created_at", -1).skip(skip).limit(page_size)
        items = await cursor.to_list(length=page_size)

        return {
            "items": [FirstTimer(**item) for item in items],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }

    async def get_first_timer_by_id(self, first_timer_id: str) -> Optional[FirstTimer]:
        """
        Get first timer by ID.

        Args:
            first_timer_id: First timer ID

        Returns:
            FirstTimer object or None
        """
        first_timer = await self.db.first_timers.find_one({"_id": ObjectId(first_timer_id)})
        if first_timer:
            return FirstTimer(**first_timer)
        return None

    async def update_first_timer(
        self,
        first_timer_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[FirstTimer]:
        """
        Update first timer record.

        Args:
            first_timer_id: First timer ID
            update_data: Fields to update

        Returns:
            Updated FirstTimer object or None

        Raises:
            ValueError: If first timer not found
        """
        # Check if exists
        existing = await self.db.first_timers.find_one({"_id": ObjectId(first_timer_id)})
        if not existing:
            raise ValueError(f"First timer {first_timer_id} not found")

        # Update full_name if first_name or last_name changed
        if "first_name" in update_data or "last_name" in update_data:
            first_name = update_data.get("first_name", existing.get("first_name"))
            last_name = update_data.get("last_name", existing.get("last_name"))
            update_data["full_name"] = f"{first_name} {last_name}"

        # Add updated timestamp
        update_data["updated_at"] = datetime.utcnow()

        # Remove fields that shouldn't be updated
        update_data.pop("_id", None)
        update_data.pop("id", None)
        update_data.pop("organization_id", None)
        update_data.pop("created_by_user_id", None)
        update_data.pop("created_at", None)

        # Update
        await self.db.first_timers.update_one(
            {"_id": ObjectId(first_timer_id)},
            {"$set": update_data}
        )

        # Fetch and return updated document
        updated = await self.db.first_timers.find_one({"_id": ObjectId(first_timer_id)})
        return FirstTimer(**updated)

    async def delete_first_timer(self, first_timer_id: str) -> bool:
        """
        Soft delete first timer (set is_active to False).

        Args:
            first_timer_id: First timer ID

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If first timer not found
        """
        result = await self.db.first_timers.update_one(
            {"_id": ObjectId(first_timer_id)},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )

        if result.matched_count == 0:
            raise ValueError(f"First timer {first_timer_id} not found")

        return result.modified_count > 0

    async def update_follow_up_status(
        self,
        first_timer_id: str,
        follow_up_status: str,
        follow_up_notes: Optional[str] = None,
        assigned_to_user_id: Optional[str] = None,
        next_follow_up_date: Optional[datetime] = None
    ) -> Optional[FirstTimer]:
        """
        Update follow-up status and related fields.

        Args:
            first_timer_id: First timer ID
            follow_up_status: New follow-up status
            follow_up_notes: Optional notes
            assigned_to_user_id: Optional user to assign follow-up
            next_follow_up_date: Optional next follow-up date

        Returns:
            Updated FirstTimer object

        Raises:
            ValueError: If first timer not found
        """
        update_data = {
            "follow_up_status": follow_up_status,
            "last_contact_date": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        if follow_up_notes:
            update_data["follow_up_notes"] = follow_up_notes
        if assigned_to_user_id:
            update_data["assigned_to_user_id"] = ObjectId(assigned_to_user_id)
        if next_follow_up_date:
            update_data["next_follow_up_date"] = next_follow_up_date

        result = await self.db.first_timers.update_one(
            {"_id": ObjectId(first_timer_id)},
            {"$set": update_data}
        )

        if result.matched_count == 0:
            raise ValueError(f"First timer {first_timer_id} not found")

        # Fetch and return updated document
        updated = await self.db.first_timers.find_one({"_id": ObjectId(first_timer_id)})
        return FirstTimer(**updated)

    async def convert_to_member(
        self,
        first_timer_id: str,
        converted_by_user_id: str,
        additional_user_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Convert first timer to full member (create User account).

        Args:
            first_timer_id: First timer ID
            converted_by_user_id: User performing conversion
            additional_user_data: Optional additional user data (e.g., role, department)

        Returns:
            Dictionary with first_timer and user objects

        Raises:
            ValueError: If first timer not found or already converted
        """
        # Get first timer
        first_timer = await self.db.first_timers.find_one({"_id": ObjectId(first_timer_id)})
        if not first_timer:
            raise ValueError(f"First timer {first_timer_id} not found")

        if first_timer.get("converted_to_member"):
            raise ValueError(f"First timer {first_timer_id} already converted to member")

        # Prepare user data from first timer
        user_data = {
            "first_name": first_timer["first_name"],
            "last_name": first_timer["last_name"],
            "full_name": first_timer["full_name"],
            "phone": first_timer["phone"],
            "email": first_timer.get("email"),
            "date_of_birth": first_timer.get("date_of_birth"),
            "gender": first_timer.get("gender"),
            "address": first_timer.get("address"),
            "organization_id": first_timer["organization_id"],
            "branch_id": first_timer.get("branch_id"),
            "role": "member",  # Default role
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "onboarding_completed": False,
            "departments": [],
            "subgroup_memberships": []
        }

        # Merge additional user data if provided
        if additional_user_data:
            user_data.update(additional_user_data)

        # Check if user with this email or phone already exists
        existing_user = None
        if user_data.get("email"):
            existing_user = await self.db.users.find_one({"email": user_data["email"]})
        if not existing_user and user_data.get("phone"):
            existing_user = await self.db.users.find_one({"phone": user_data["phone"]})

        if existing_user:
            # User already exists - just link them
            user_id = existing_user["_id"]
            user = User(**existing_user)
        else:
            # Create new user
            # Validate with Pydantic model
            user = User(**user_data)

            # Insert into database
            result = await self.db.users.insert_one(
                user.model_dump(by_alias=True, exclude={"id"})
            )
            user_id = result.inserted_id

            # Fetch created user
            created_user = await self.db.users.find_one({"_id": user_id})
            user = User(**created_user)

        # Update first timer as converted
        conversion_date = datetime.utcnow()
        await self.db.first_timers.update_one(
            {"_id": ObjectId(first_timer_id)},
            {
                "$set": {
                    "converted_to_member": True,
                    "member_id": user_id,
                    "conversion_date": conversion_date,
                    "follow_up_status": "converted",
                    "updated_at": conversion_date
                }
            }
        )

        # Fetch updated first timer
        updated_first_timer = await self.db.first_timers.find_one({"_id": ObjectId(first_timer_id)})

        return {
            "first_timer": FirstTimer(**updated_first_timer),
            "user": user,
            "is_new_user": existing_user is None
        }

    async def get_first_timer_stats(
        self,
        organization_id: str,
        branch_id: Optional[str] = None
    ) -> FirstTimerStats:
        """
        Get statistics for first timer dashboard.

        Args:
            organization_id: Organization ID
            branch_id: Optional branch filter

        Returns:
            FirstTimerStats object
        """
        # Base query
        base_query = {
            "organization_id": ObjectId(organization_id),
            "is_active": True
        }
        if branch_id:
            base_query["branch_id"] = ObjectId(branch_id)

        # Date ranges
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=today_start.weekday())
        month_start = today_start.replace(day=1)

        # Aggregate statistics
        pipeline = [
            {"$match": base_query},
            {
                "$facet": {
                    "total": [{"$count": "count"}],
                    "today": [
                        {"$match": {"visit_date": {"$gte": today_start}}},
                        {"$count": "count"}
                    ],
                    "this_week": [
                        {"$match": {"visit_date": {"$gte": week_start}}},
                        {"$count": "count"}
                    ],
                    "this_month": [
                        {"$match": {"visit_date": {"$gte": month_start}}},
                        {"$count": "count"}
                    ],
                    "by_interest": [
                        {"$group": {"_id": "$interest_type", "count": {"$sum": 1}}}
                    ],
                    "by_follow_up_status": [
                        {"$group": {"_id": "$follow_up_status", "count": {"$sum": 1}}}
                    ],
                    "converted": [
                        {"$match": {"converted_to_member": True}},
                        {"$count": "count"}
                    ]
                }
            }
        ]

        result = await self.db.first_timers.aggregate(pipeline).to_list(length=1)
        stats_data = result[0] if result else {}

        # Extract counts with safe indexing
        def safe_count(data_list):
            """Safely extract count from aggregation result."""
            if data_list and len(data_list) > 0:
                return data_list[0].get("count", 0)
            return 0

        total = safe_count(stats_data.get("total", []))
        today = safe_count(stats_data.get("today", []))
        this_week = safe_count(stats_data.get("this_week", []))
        this_month = safe_count(stats_data.get("this_month", []))
        converted = safe_count(stats_data.get("converted", []))

        # By interest type
        by_interest = {item["_id"]: item["count"] for item in stats_data.get("by_interest", [])}
        visitors = by_interest.get("visitor", 0)
        new_converts = by_interest.get("new_convert", 0)
        existing_members = by_interest.get("existing_member", 0)
        discipleship_interested = by_interest.get("discipleship", 0)

        # By follow-up status
        by_status = {item["_id"]: item["count"] for item in stats_data.get("by_follow_up_status", [])}
        pending = by_status.get("pending", 0)
        contacted = by_status.get("contacted", 0)
        in_progress = by_status.get("in_progress", 0)
        converted_status = by_status.get("converted", 0)
        lost = by_status.get("lost", 0)

        # Calculate conversion rate
        conversion_rate = (converted / total * 100) if total > 0 else 0.0

        return FirstTimerStats(
            total_first_timers=total,
            today=today,
            this_week=this_week,
            this_month=this_month,
            visitors=visitors,
            new_converts=new_converts,
            existing_members=existing_members,
            discipleship_interested=discipleship_interested,
            pending_follow_up=pending,
            contacted=contacted,
            in_progress=in_progress,
            converted=converted_status,
            lost=lost,
            conversion_rate=round(conversion_rate, 2)
        )
