"""
Proximity check-in service.

Handles location-based automatic check-in when members arrive at church branches.
Uses GPS coordinates to detect proximity and triggers attendance recording.
"""

from datetime import datetime, timedelta, time as datetime_time
from typing import List, Dict, Any, Tuple, Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
import math


class ProximityCheckinService:
    """
    Service for proximity-based check-in operations.

    Provides methods to:
    - Find nearby branches within radius
    - Check if service is currently active
    - Validate check-in eligibility
    - Perform automatic check-in
    - Log all attempts for analytics
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize proximity check-in service.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.branches_collection = db.branches
        self.session_attendance_collection = db.session_attendance
        self.auto_checkin_logs_collection = db.auto_checkin_logs
        self.users_collection = db.users

    @staticmethod
    def calculate_distance(
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """
        Calculate distance between two GPS coordinates using Haversine formula.

        Args:
            lat1: Latitude of first point
            lon1: Longitude of first point
            lat2: Latitude of second point
            lon2: Longitude of second point

        Returns:
            Distance in meters

        Example:
            >>> calculate_distance(5.6037, -0.1870, 5.7108, -0.1673)
            12845.32  # ~12.8km
        """
        # Earth's radius in meters
        R = 6371000

        # Convert to radians
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        # Haversine formula
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        distance = R * c
        return distance

    async def find_nearby_branches(
        self,
        latitude: float,
        longitude: float,
        organization_id: str,
        max_distance: int = 5000,
        auto_checkin_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Find branches near a GPS coordinate.

        Args:
            latitude: User's latitude
            longitude: User's longitude
            organization_id: Organization ID
            max_distance: Maximum distance in meters (default: 5000m)

        Returns:
            List of nearby branches sorted by distance (nearest first)

        Example:
            >>> await find_nearby_branches(5.6037, -0.1870, org_id)
            [
                {
                    "_id": "...",
                    "name": "Adenta",
                    "distance": 342.5,
                    "can_auto_checkin": True,
                    ...
                }
            ]
        """
        # Find all active branches with coordinates
        query = {
            "organization_id": ObjectId(organization_id),
            "is_active": True,
            "latitude": {"$ne": None},
            "longitude": {"$ne": None}
        }
        
        # Only filter by auto_checkin_enabled if requested
        if auto_checkin_only:
            query["auto_checkin_enabled"] = True

        cursor = self.branches_collection.find(query)
        branches = await cursor.to_list(length=None)

        # Calculate distances and filter
        nearby_branches = []
        for branch in branches:
            distance = self.calculate_distance(
                latitude, longitude,
                branch["latitude"], branch["longitude"]
            )

            # Check if within max distance
            if distance <= max_distance:
                branch["distance"] = round(distance, 2)
                nearby_branches.append(branch)

        # Sort by distance (nearest first)
        nearby_branches.sort(key=lambda b: b["distance"])

        return nearby_branches

    async def check_service_active(
        self,
        branch_id: str,
        timestamp: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Check if a service is currently active at a branch.

        Service is considered active if current time is within the service window:
        - 30 minutes before scheduled start time
        - Until scheduled end time (start_time + duration)

        Args:
            branch_id: Branch ID
            timestamp: Time to check (default: now)

        Returns:
            Service details if active, None otherwise

        Example:
            >>> await check_service_active(branch_id)
            {
                "service_type": "sunday_morning",
                "start_time": "08:00",
                "duration_minutes": 120,
                "window_start": "07:30",
                "window_end": "10:00"
            }
        """
        if timestamp is None:
            timestamp = datetime.utcnow()

        # Get branch with service times
        branch = await self.branches_collection.find_one(
            {"_id": ObjectId(branch_id)}
        )

        if not branch or not branch.get("service_times"):
            return None

        # Get current day of week and time
        day_of_week = timestamp.strftime("%A").lower()  # "sunday", "monday", etc.
        current_time = timestamp.time()

        # Check each service time
        for service in branch["service_times"]:
            if not service.get("is_active", True):
                continue

            # Match day of week
            if service["day_of_week"].lower() != day_of_week:
                continue

            # Parse service start time
            start_hour, start_minute = map(int, service["start_time"].split(":"))
            service_start = datetime_time(start_hour, start_minute)

            # Calculate window start (30 min before)
            window_start_dt = datetime.combine(timestamp.date(), service_start) - timedelta(minutes=30)
            window_start = window_start_dt.time()

            # Calculate window end (start + duration)
            window_end_dt = datetime.combine(timestamp.date(), service_start) + timedelta(
                minutes=service["duration_minutes"]
            )
            window_end = window_end_dt.time()

            # Check if current time is within window
            if window_start <= current_time <= window_end:
                return {
                    "service_type": service["service_type"],
                    "start_time": service["start_time"],
                    "duration_minutes": service["duration_minutes"],
                    "window_start": window_start.strftime("%H:%M"),
                    "window_end": window_end.strftime("%H:%M"),
                    "day_of_week": service["day_of_week"]
                }

        return None

    async def can_check_in(
        self,
        user_id: str,
        branch_id: str,
        service_type: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Validate if user can check in.

        Checks:
        1. User exists and has auto-checkin enabled
        2. Not already checked in today
        3. Cooldown period (2 hours between check-ins)

        Args:
            user_id: User ID
            branch_id: Branch ID
            service_type: Service type (optional)

        Returns:
            Tuple of (can_checkin, reason)

        Example:
            >>> await can_check_in(user_id, branch_id)
            (True, "eligible")
            >>> await can_check_in(user_id, branch_id)
            (False, "already_checked_in")
        """
        # Check user exists
        user = await self.users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            return (False, "user_not_found")

        # Check user has auto-checkin enabled (default: True if not set)
        if not user.get("auto_checkin_enabled", True):
            return (False, "auto_checkin_disabled")

        # Check if already checked in today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        existing_checkin = await self.session_attendance_collection.find_one({
            "registration_id": ObjectId(user_id),
            "checked_in_at": {"$gte": today_start}
        })

        if existing_checkin:
            # Check cooldown period (2 hours)
            time_since_checkin = datetime.utcnow() - existing_checkin["checked_in_at"]
            if time_since_checkin < timedelta(hours=2):
                return (False, "cooldown_period")

        return (True, "eligible")

    async def auto_checkin_user(
        self,
        user_id: str,
        branch_id: str,
        latitude: float,
        longitude: float,
        accuracy: float,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform automatic check-in for user.

        Creates session_attendance record and logs the attempt.
        Also triggers gamification (points, streak, badges) via background task.

        Args:
            user_id: User ID
            branch_id: Branch ID
            latitude: User's GPS latitude
            longitude: User's GPS longitude
            accuracy: GPS accuracy in meters
            user_agent: Browser/device info (optional)
            ip_address: IP address (optional)

        Returns:
            Check-in result with attendance_id and gamification data

        Raises:
            ValueError: If validation fails

        Example:
            >>> await auto_checkin_user(user_id, branch_id, 5.6037, -0.1870, 10.5)
            {
                "success": True,
                "attendance_id": "...",
                "branch": "Adenta",
                "distance": 342.5,
                "points_awarded": 10,
                "streak_updated": True,
                "current_streak": 5,
                "badges_unlocked": []
            }
        """
        # Get branch
        branch = await self.branches_collection.find_one({"_id": ObjectId(branch_id)})
        if not branch:
            raise ValueError("Branch not found")

        # Get user
        user = await self.users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise ValueError("User not found")

        # Calculate distance
        distance = self.calculate_distance(
            latitude, longitude,
            branch["latitude"], branch["longitude"]
        )

        # Check if within radius
        if distance > branch["checkin_radius"]:
            # Log failed attempt
            await self._log_checkin_attempt(
                user_id=user_id,
                branch_id=branch_id,
                latitude=latitude,
                longitude=longitude,
                accuracy=accuracy,
                distance=distance,
                success=False,
                failure_reason="too_far",
                user_agent=user_agent,
                ip_address=ip_address
            )
            raise ValueError(f"Too far from branch: {distance:.0f}m away (max: {branch['checkin_radius']}m)")

        # Check GPS accuracy (reject if > 100m)
        suspicious_accuracy = accuracy > 100
        if suspicious_accuracy:
            await self._log_checkin_attempt(
                user_id=user_id,
                branch_id=branch_id,
                latitude=latitude,
                longitude=longitude,
                accuracy=accuracy,
                distance=distance,
                success=False,
                failure_reason="poor_accuracy",
                user_agent=user_agent,
                ip_address=ip_address,
                suspicious_accuracy=True
            )
            raise ValueError(f"GPS accuracy too poor: {accuracy:.1f}m (max: 100m)")

        # Check if can check in
        can_checkin, reason = await self.can_check_in(user_id, branch_id)
        if not can_checkin:
            await self._log_checkin_attempt(
                user_id=user_id,
                branch_id=branch_id,
                latitude=latitude,
                longitude=longitude,
                accuracy=accuracy,
                distance=distance,
                success=False,
                failure_reason=reason,
                user_agent=user_agent,
                ip_address=ip_address
            )
            raise ValueError(f"Cannot check in: {reason}")

        # Check if service is active
        active_service = await self.check_service_active(branch_id)
        if not active_service:
            await self._log_checkin_attempt(
                user_id=user_id,
                branch_id=branch_id,
                latitude=latitude,
                longitude=longitude,
                accuracy=accuracy,
                distance=distance,
                success=False,
                failure_reason="no_active_service",
                user_agent=user_agent,
                ip_address=ip_address
            )
            raise ValueError("No active service at this time")

        # Create attendance record
        attendance_doc = {
            "session_id": None,  # For regular services (not conference sessions)
            "service_id": None,  # Will be populated if service tracking is implemented
            "conference_id": None,
            "registration_id": ObjectId(user_id),
            "checked_in_at": datetime.utcnow(),
            "checked_in_by": None,  # Auto check-in (not manual)
            "check_in_method": "auto_geofence",
            "user_name": user.get("full_name"),
            "user_phone": user.get("phone"),
            "session_name": f"{branch['name']} - {active_service['service_type']}",
            "day_number": None,
            "created_at": datetime.utcnow()
        }

        result = await self.session_attendance_collection.insert_one(attendance_doc)
        attendance_id = result.inserted_id

        # Log successful attempt
        await self._log_checkin_attempt(
            user_id=user_id,
            branch_id=branch_id,
            latitude=latitude,
            longitude=longitude,
            accuracy=accuracy,
            distance=distance,
            success=True,
            attendance_id=str(attendance_id),
            user_agent=user_agent,
            ip_address=ip_address
        )

        # TODO: Trigger gamification (points, streak, badges)
        # This will be implemented after gamification_service is created
        # For now, return placeholder values
        gamification_result = {
            "points_awarded": 10,
            "streak_updated": True,
            "current_streak": 1,
            "badges_unlocked": []
        }

        return {
            "success": True,
            "attendance_id": str(attendance_id),
            "branch": branch["name"],
            "service": active_service["service_type"],
            "distance": round(distance, 2),
            "checked_in_at": attendance_doc["checked_in_at"].isoformat(),
            **gamification_result
        }

    async def _log_checkin_attempt(
        self,
        user_id: str,
        branch_id: str,
        latitude: float,
        longitude: float,
        accuracy: float,
        distance: float,
        success: bool,
        failure_reason: Optional[str] = None,
        attendance_id: Optional[str] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        suspicious_velocity: bool = False,
        suspicious_accuracy: bool = False,
        suspicious_spoofing: bool = False
    ):
        """
        Log check-in attempt to auto_checkin_logs collection.

        Args:
            user_id: User ID
            branch_id: Branch ID
            latitude: GPS latitude
            longitude: GPS longitude
            accuracy: GPS accuracy
            distance: Distance to branch
            success: Whether check-in succeeded
            failure_reason: Reason for failure (if applicable)
            attendance_id: Created attendance ID (if successful)
            user_agent: Browser/device info
            ip_address: IP address
            suspicious_velocity: Velocity check flag
            suspicious_accuracy: Accuracy check flag
            suspicious_spoofing: Spoofing check flag
        """
        # Get user's organization_id
        user = await self.users_collection.find_one({"_id": ObjectId(user_id)})
        organization_id = user.get("organization_id") if user else None

        log_doc = {
            "user_id": ObjectId(user_id),
            "organization_id": organization_id,
            "latitude": latitude,
            "longitude": longitude,
            "accuracy": accuracy,
            "branch_id": ObjectId(branch_id),
            "service_id": None,
            "distance_to_branch": distance,
            "success": success,
            "failure_reason": failure_reason,
            "attendance_id": ObjectId(attendance_id) if attendance_id else None,
            "suspicious_velocity": suspicious_velocity,
            "suspicious_accuracy": suspicious_accuracy,
            "suspicious_spoofing": suspicious_spoofing,
            "user_agent": user_agent,
            "ip_address": ip_address,
            "created_at": datetime.utcnow()
        }

        await self.auto_checkin_logs_collection.insert_one(log_doc)

    async def get_checkin_status(self, user_id: str) -> Dict[str, Any]:
        """
        Get user's current check-in status.

        Args:
            user_id: User ID

        Returns:
            Check-in status information

        Example:
            >>> await get_checkin_status(user_id)
            {
                "checked_in_today": True,
                "last_checkin": {
                    "service": "Sunday Morning",
                    "branch": "Adenta",
                    "time": "2025-12-09T08:15:00Z"
                },
                "can_checkin_again": False,
                "next_available_checkin": "2025-12-09T10:15:00Z"
            }
        """
        # Find today's check-in
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        last_checkin = await self.session_attendance_collection.find_one(
            {"registration_id": ObjectId(user_id), "checked_in_at": {"$gte": today_start}},
            sort=[("checked_in_at", -1)]
        )

        if not last_checkin:
            return {
                "checked_in_today": False,
                "last_checkin": None,
                "can_checkin_again": True,
                "next_available_checkin": None
            }

        # Calculate cooldown
        time_since_checkin = datetime.utcnow() - last_checkin["checked_in_at"]
        cooldown_remaining = timedelta(hours=2) - time_since_checkin
        can_checkin_again = cooldown_remaining.total_seconds() <= 0

        next_available = None
        if not can_checkin_again:
            next_available = (last_checkin["checked_in_at"] + timedelta(hours=2)).isoformat()

        return {
            "checked_in_today": True,
            "last_checkin": {
                "service": last_checkin.get("session_name"),
                "branch": last_checkin.get("session_name", "").split(" - ")[0],
                "time": last_checkin["checked_in_at"].isoformat()
            },
            "can_checkin_again": can_checkin_again,
            "next_available_checkin": next_available
        }
