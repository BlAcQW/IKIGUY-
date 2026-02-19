"""
Church service management service.

Handles CRUD operations for regular church services (Sunday, midweek)
and recurring service generation.
"""

from typing import List, Optional, Dict, Any
from bson import ObjectId
from datetime import datetime, timedelta
import logging
import secrets
import hashlib

from app.core.database import get_database
from app.models.service import Service

logger = logging.getLogger(__name__)


class ServiceService:
    """Service for church service operations."""

    def _generate_qr_code(self, service_type: str, service_date: datetime, branch_id: str) -> str:
        """
        Generate unique QR code for service check-in.

        Args:
            service_type: Type of service
            service_date: Service date
            branch_id: Branch ID

        Returns:
            Unique QR code string
        """
        # Create deterministic but unique hash
        date_str = service_date.strftime("%Y%m%d")
        data = f"{service_type}:{branch_id}:{date_str}:{secrets.token_hex(8)}"
        hash_code = hashlib.sha256(data.encode()).hexdigest()[:16].upper()
        return f"SVC_{date_str}_{service_type.upper()}_{hash_code}"

    async def create_service(self, service_data: Dict) -> Service:
        """
        Create new service.

        Args:
            service_data: Service data

        Returns:
            Created Service object
        """
        db = get_database()

        # Generate QR code if not provided
        if "qr_code" not in service_data or not service_data["qr_code"]:
            service_data["qr_code"] = self._generate_qr_code(
                service_data["service_type"],
                service_data["service_date"],
                str(service_data["branch_id"])
            )

        service_data["created_at"] = datetime.utcnow()
        service_data["updated_at"] = datetime.utcnow()
        service_data["actual_attendance"] = service_data.get("actual_attendance", 0)

        try:
            result = await db.services.insert_one(service_data)
            service_data["_id"] = result.inserted_id

            logger.info(
                f"Created service: {service_data.get('service_type')} "
                f"on {service_data.get('service_date')}"
            )
            return Service(**service_data)

        except Exception as e:
            logger.error(f"Failed to create service: {str(e)}")
            raise Exception(f"Failed to create service: {str(e)}")

    async def get_service(self, service_id: str) -> Optional[Service]:
        """
        Get service by ID with dynamically calculated actual_attendance.

        Args:
            service_id: Service ID

        Returns:
            Service object with accurate actual_attendance count
        """
        db = get_database()

        if not ObjectId.is_valid(service_id):
            return None

        service_doc = await db.services.find_one({"_id": ObjectId(service_id)})

        if service_doc:
            # Calculate actual_attendance dynamically from check-ins
            attendance_count = await db.session_attendance.count_documents({
                "service_id": ObjectId(service_id)
            })
            service_doc["actual_attendance"] = attendance_count
            return Service(**service_doc)
        return None

    async def list_services(
        self,
        branch_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        service_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Service]:
        """
        List services with optional filters.

        Args:
            branch_id: Filter by branch
            start_date: Filter services on or after this date
            end_date: Filter services on or before this date
            service_type: Filter by service type
            status: Filter by status
            limit: Maximum number of results

        Returns:
            List of Service objects with dynamically calculated actual_attendance
        """
        db = get_database()

        query = {}

        if branch_id:
            if not ObjectId.is_valid(branch_id):
                return []
            query["branch_id"] = ObjectId(branch_id)

        if start_date:
            query.setdefault("service_date", {})
            query["service_date"]["$gte"] = start_date

        if end_date:
            query.setdefault("service_date", {})
            query["service_date"]["$lte"] = end_date

        if service_type:
            query["service_type"] = service_type

        if status:
            query["status"] = status

        cursor = db.services.find(query).sort("service_date", -1).limit(limit)
        services = await cursor.to_list(length=limit)

        # Calculate actual_attendance dynamically for each service
        result = []
        for service in services:
            # Count actual check-ins
            attendance_count = await db.session_attendance.count_documents({
                "service_id": service["_id"]
            })
            service["actual_attendance"] = attendance_count
            result.append(Service(**service))

        return result

    async def update_service(
        self,
        service_id: str,
        update_data: Dict
    ) -> Optional[Service]:
        """
        Update service.

        Args:
            service_id: Service ID
            update_data: Fields to update

        Returns:
            Updated Service object
        """
        db = get_database()

        if not ObjectId.is_valid(service_id):
            return None

        # Remove fields that shouldn't be updated directly
        update_data.pop("_id", None)
        update_data.pop("created_at", None)
        update_data.pop("actual_attendance", None)  # Calculated from check-ins

        update_data["updated_at"] = datetime.utcnow()

        try:
            result = await db.services.update_one(
                {"_id": ObjectId(service_id)},
                {"$set": update_data}
            )

            if result.modified_count > 0:
                logger.info(f"Updated service: {service_id}")
                return await self.get_service(service_id)

            return None

        except Exception as e:
            logger.error(f"Failed to update service: {str(e)}")
            raise Exception(f"Failed to update service: {str(e)}")

    async def delete_service(self, service_id: str) -> bool:
        """
        Delete service.

        Args:
            service_id: Service ID

        Returns:
            True if deleted, False otherwise
        """
        db = get_database()

        if not ObjectId.is_valid(service_id):
            return False

        try:
            result = await db.services.delete_one({"_id": ObjectId(service_id)})

            if result.deleted_count > 0:
                logger.info(f"Deleted service: {service_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to delete service: {str(e)}")
            raise Exception(f"Failed to delete service: {str(e)}")

    async def _service_exists(
        self,
        branch_id: str,
        service_date: datetime,
        service_type: str
    ) -> bool:
        """
        Check if a service already exists for given branch, date, and type.

        Args:
            branch_id: Branch ID
            service_date: Service date
            service_type: Service type

        Returns:
            True if service exists, False otherwise
        """
        db = get_database()

        # Check for service on the same date with same type and branch
        existing = await db.services.find_one({
            "branch_id": ObjectId(branch_id),
            "service_date": {
                "$gte": datetime(service_date.year, service_date.month, service_date.day),
                "$lt": datetime(service_date.year, service_date.month, service_date.day) + timedelta(days=1)
            },
            "service_type": service_type
        })

        return existing is not None

    async def generate_recurring_services(
        self,
        branch_id: str,
        organization_id: str,
        weeks_ahead: int = 8
    ) -> Dict[str, int]:
        """
        Auto-generate weekly services (Sunday 8am, 10am, Wednesday 7pm).

        Args:
            branch_id: Branch ID
            organization_id: Organization ID
            weeks_ahead: Number of weeks to generate ahead (default: 8)

        Returns:
            Dict with counts of services created by type
        """
        if not ObjectId.is_valid(branch_id):
            raise ValueError("Invalid branch_id")

        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = today + timedelta(weeks=weeks_ahead)

        stats = {
            "sunday_8am": 0,
            "sunday_10am": 0,
            "midweek": 0,
            "total": 0
        }

        current_date = today
        while current_date <= end_date:
            # Sunday services
            if current_date.weekday() == 6:  # Sunday (0=Monday, 6=Sunday)
                # Sunday 8am service
                if not await self._service_exists(branch_id, current_date, "sunday_8am"):
                    await self.create_service({
                        "service_type": "sunday_8am",
                        "service_date": current_date,
                        "start_time": "08:00",
                        "end_time": "10:30",
                        "branch_id": ObjectId(branch_id),
                        "organization_id": organization_id,
                        "status": "upcoming",
                        "is_recurring": True,
                        "recurrence_rule": {"pattern": "weekly", "day": "sunday", "time": "08:00"}
                    })
                    stats["sunday_8am"] += 1
                    stats["total"] += 1

                # Sunday 10am service
                if not await self._service_exists(branch_id, current_date, "sunday_10am"):
                    await self.create_service({
                        "service_type": "sunday_10am",
                        "service_date": current_date,
                        "start_time": "10:00",
                        "end_time": "12:30",
                        "branch_id": ObjectId(branch_id),
                        "organization_id": organization_id,
                        "status": "upcoming",
                        "is_recurring": True,
                        "recurrence_rule": {"pattern": "weekly", "day": "sunday", "time": "10:00"}
                    })
                    stats["sunday_10am"] += 1
                    stats["total"] += 1

            # Wednesday midweek service
            if current_date.weekday() == 2:  # Wednesday
                if not await self._service_exists(branch_id, current_date, "midweek"):
                    await self.create_service({
                        "service_type": "midweek",
                        "service_date": current_date,
                        "start_time": "19:00",
                        "end_time": "21:00",
                        "branch_id": ObjectId(branch_id),
                        "organization_id": organization_id,
                        "status": "upcoming",
                        "is_recurring": True,
                        "recurrence_rule": {"pattern": "weekly", "day": "wednesday", "time": "19:00"}
                    })
                    stats["midweek"] += 1
                    stats["total"] += 1

            current_date += timedelta(days=1)

        logger.info(
            f"Generated {stats['total']} services for branch {branch_id}: "
            f"{stats['sunday_8am']} Sunday 8am, {stats['sunday_10am']} Sunday 10am, "
            f"{stats['midweek']} midweek"
        )

        return stats

    async def get_service_attendance_summary(
        self,
        service_id: str
    ) -> Dict[str, Any]:
        """
        Get attendance stats: total, members, visitors, first-timers.

        Args:
            service_id: Service ID

        Returns:
            Dict with attendance statistics
        """
        db = get_database()

        if not ObjectId.is_valid(service_id):
            raise ValueError("Invalid service_id")

        # Aggregate attendance with user info
        pipeline = [
            {"$match": {"service_id": ObjectId(service_id)}},
            {
                "$lookup": {
                    "from": "users",
                    "localField": "registration_id",
                    "foreignField": "_id",
                    "as": "user"
                }
            },
            {"$unwind": {"path": "$user", "preserveNullAndEmptyArrays": True}},
            {
                "$group": {
                    "_id": None,
                    "total_attendees": {"$sum": 1},
                    "members": {
                        "$sum": {
                            "$cond": [
                                {"$in": ["$user.member_status", ["active_member", "inactive_member"]]},
                                1,
                                0
                            ]
                        }
                    },
                    "visitors": {
                        "$sum": {
                            "$cond": [
                                {"$eq": ["$user.member_status", "visitor"]},
                                1,
                                0
                            ]
                        }
                    },
                    "first_timers": {
                        "$sum": {
                            "$cond": [
                                {"$eq": ["$user.current_spiritual_stage", "first_timer"]},
                                1,
                                0
                            ]
                        }
                    }
                }
            }
        ]

        cursor = db.session_attendance.aggregate(pipeline)
        results = await cursor.to_list(length=1)

        if results:
            stats = results[0]
            return {
                "total_attendees": stats.get("total_attendees", 0),
                "members": stats.get("members", 0),
                "visitors": stats.get("visitors", 0),
                "first_timers": stats.get("first_timers", 0)
            }

        return {
            "total_attendees": 0,
            "members": 0,
            "visitors": 0,
            "first_timers": 0
        }


# Singleton instance
service_service = ServiceService()
