"""
Session attendance management service.

This module provides business logic for managing session-level attendance,
including check-in operations and attendance list retrieval.
"""

from typing import List, Optional, Dict
from bson import ObjectId
from datetime import datetime
from pymongo.errors import DuplicateKeyError
import logging
import asyncio

from app.core.database import get_database
from app.models.session_attendance import SessionAttendance
from app.utils.phone import normalize_phone_number
from app.services.channels.sms_channel import SMSChannel

logger = logging.getLogger(__name__)

# SMS channel instance for sending confirmations
_sms_channel: Optional[SMSChannel] = None

def get_sms_channel() -> Optional[SMSChannel]:
    """Get or create SMS channel instance."""
    global _sms_channel
    if _sms_channel is None:
        try:
            _sms_channel = SMSChannel()
        except Exception as e:
            logger.warning(f"Failed to initialize SMS channel: {e}")
    return _sms_channel


class SessionAttendanceService:
    """Service for session attendance operations."""

    async def check_in_by_code(
        self,
        registration_code: str,
        session_id: str,
        admin_id: Optional[str] = None
    ) -> SessionAttendance:
        """
        Check in attendee to session using registration code (QR code scan).

        Args:
            registration_code: Registration code from QR (REG-XXXXXXXX)
            session_id: Target session ID
            admin_id: ID of admin performing check-in

        Returns:
            SessionAttendance record

        Raises:
            ValueError: If registration or session not found
            Exception: If already checked in to session
        """
        db = get_database()

        # Find registration by code
        registration = await db.conference_registrations.find_one({
            "registration_code": registration_code,
            "status": "confirmed"
        })
        if not registration:
            raise ValueError("Registration not found or cancelled")

        return await self._perform_check_in(
            db=db,
            registration=registration,
            session_id=session_id,
            admin_id=admin_id,
            method="qr_scan"
        )

    async def check_in_by_registration_id(
        self,
        registration_id: str,
        session_id: str,
        admin_id: Optional[str] = None
    ) -> SessionAttendance:
        """
        Check in attendee using registration ID (manual search result).

        Args:
            registration_id: Registration document ID
            session_id: Target session ID
            admin_id: ID of admin performing check-in

        Returns:
            SessionAttendance record

        Raises:
            ValueError: If registration or session not found
            Exception: If already checked in to session
        """
        db = get_database()

        if not ObjectId.is_valid(registration_id):
            raise ValueError("Invalid registration ID")

        registration = await db.conference_registrations.find_one({
            "_id": ObjectId(registration_id),
            "status": "confirmed"
        })
        if not registration:
            raise ValueError("Registration not found or cancelled")

        return await self._perform_check_in(
            db=db,
            registration=registration,
            session_id=session_id,
            admin_id=admin_id,
            method="manual_search"
        )

    async def check_in_by_phone(
        self,
        phone: str,
        session_id: str,
        admin_id: Optional[str] = None
    ) -> SessionAttendance:
        """
        Check in attendee to session using phone number directly.

        Args:
            phone: Phone number to look up
            session_id: Target session ID
            admin_id: ID of admin performing check-in

        Returns:
            SessionAttendance record

        Raises:
            ValueError: If registration or session not found
            Exception: If already checked in to session
        """
        db = get_database()

        # Validate session ID
        if not ObjectId.is_valid(session_id):
            raise ValueError("Invalid session ID")

        # Get session to find conference_id
        session = await db.conference_sessions.find_one({"_id": ObjectId(session_id)})
        if not session:
            raise ValueError("Session not found")

        # Normalize phone to get all possible formats
        phone_variants = normalize_phone_number(phone)
        if not phone_variants:
            raise ValueError("Invalid phone number format")

        # Find registration by phone for this conference using all variants
        registration = await db.conference_registrations.find_one({
            "conference_id": session["conference_id"],
            "user_phone": {"$in": phone_variants},
            "status": "confirmed"
        })

        if not registration:
            raise ValueError(
                f"No registration found for phone: {phone}. "
                f"Please ensure the attendee has registered for this conference. "
                f"Checked formats: {', '.join(phone_variants[:3])}"
            )

        return await self._perform_check_in(
            db=db,
            registration=registration,
            session_id=session_id,
            admin_id=admin_id,
            method="phone_lookup"
        )

    async def _perform_check_in(
        self,
        db,
        registration: Dict,
        session_id: str,
        admin_id: Optional[str],
        method: str
    ) -> SessionAttendance:
        """
        Internal method to perform session check-in.

        Args:
            db: Database instance
            registration: Registration document
            session_id: Target session ID
            admin_id: Admin user ID
            method: Check-in method (qr_scan or manual_search)

        Returns:
            SessionAttendance record

        Raises:
            ValueError: If session not found or invalid
            Exception: If already checked in
        """
        # Validate session exists and belongs to same conference
        if not ObjectId.is_valid(session_id):
            raise ValueError("Invalid session ID")

        session = await db.conference_sessions.find_one({
            "_id": ObjectId(session_id),
            "conference_id": registration["conference_id"]
        })
        if not session:
            raise ValueError("Session not found or not part of this conference")

        # Check for existing check-in - return existing record instead of error
        existing = await db.session_attendance.find_one({
            "session_id": ObjectId(session_id),
            "registration_id": registration["_id"]
        })
        if existing:
            # Return existing check-in with repeat flag
            logger.warning(
                f"REPEAT session check-in: {registration.get('user_name')} -> "
                f"{session.get('name')} (already checked in - NO SMS)"
            )
            attendance = SessionAttendance(**existing)
            attendance.is_repeat_checkin = True
            return attendance

        # Build attendance document with denormalized fields
        attendance_doc = {
            "session_id": ObjectId(session_id),
            "conference_id": registration["conference_id"],
            "registration_id": registration["_id"],
            "checked_in_at": datetime.utcnow(),
            "checked_in_by": ObjectId(admin_id) if admin_id and ObjectId.is_valid(admin_id) else None,
            "check_in_method": method,
            "user_name": registration.get("user_name"),
            "user_phone": registration.get("user_phone"),
            "session_name": session.get("name"),
            "day_number": session.get("day_number"),
            "created_at": datetime.utcnow()
        }

        try:
            result = await db.session_attendance.insert_one(attendance_doc)
            attendance_doc["_id"] = result.inserted_id

            print(f"[DEBUG] Check-in SUCCESS: {registration.get('user_name')} -> {session.get('name')}", flush=True)
            logger.warning(
                f"Session check-in SUCCESS: {registration.get('user_name')} -> "
                f"{session.get('name')} (method: {method}) - About to send SMS"
            )

            # Update the conference registration's overall check-in status
            # This ensures analytics show correct "total checked in" counts
            if not registration.get("checked_in"):
                await db.conference_registrations.update_one(
                    {"_id": registration["_id"]},
                    {
                        "$set": {
                            "checked_in": True,
                            "first_check_in_at": datetime.utcnow()
                        }
                    }
                )
                logger.info(
                    f"Updated registration check-in status for {registration.get('user_name')}"
                )

            # Send SMS confirmation if enabled for this session (non-blocking)
            # Fire and forget - don't wait for SMS delivery
            asyncio.create_task(
                self._send_sms_confirmation(
                    session=session,
                    registration=registration
                )
            )

            return SessionAttendance(**attendance_doc)

        except DuplicateKeyError:
            raise Exception("Already checked in to this session")

    async def _send_sms_confirmation(
        self,
        session: Dict,
        registration: Dict
    ) -> None:
        """
        Send SMS confirmation to attendee after check-in.

        Args:
            session: Session document with SMS settings
            registration: Registration document with user info
        """
        print(f"[DEBUG] _send_sms_confirmation called for {registration.get('user_name')}", flush=True)
        logger.warning(
            f"SMS confirmation check - session: {session.get('name')}, "
            f"sms_enabled: {session.get('sms_confirmation_enabled')}, "
            f"user: {registration.get('user_name')}"
        )

        # Check if SMS confirmation is enabled for this session
        if not session.get("sms_confirmation_enabled"):
            logger.warning(f"SMS not enabled for session {session.get('name')}")
            return

        template = session.get("sms_confirmation_template")
        if not template:
            logger.debug(
                f"SMS confirmation enabled but no template for session {session.get('name')}"
            )
            return

        # Get user phone number
        user_phone = registration.get("user_phone")
        if not user_phone:
            logger.warning(
                f"Cannot send SMS confirmation - no phone for {registration.get('user_name')}"
            )
            return

        # Get SMS channel
        sms_channel = get_sms_channel()
        if not sms_channel:
            logger.warning("SMS channel not available for confirmation")
            return

        try:
            # Format message with placeholders
            message = sms_channel.format_message(
                template,
                name=registration.get("user_name", "Guest"),
                session_name=session.get("name", "Session"),
                day_label=session.get("day_label", "Today"),
                location=session.get("location", "")
            )

            # Send SMS (non-blocking, don't fail check-in if SMS fails)
            result = await sms_channel.send(
                to_phone=user_phone,
                message=message,
                user_name=registration.get("user_name")
            )

            if result.get("success"):
                logger.info(
                    f"SMS confirmation sent to {registration.get('user_name')} "
                    f"for session {session.get('name')}"
                )
            else:
                logger.warning(
                    f"SMS confirmation failed for {registration.get('user_name')}: "
                    f"{result.get('error')}"
                )

        except Exception as e:
            # Don't fail check-in if SMS sending fails
            logger.error(f"Error sending SMS confirmation: {e}")

    async def get_session_attendance(
        self,
        session_id: str,
        conference_id: str,
        limit: int = 500
    ) -> List[SessionAttendance]:
        """
        Get all check-ins for a session.

        Args:
            session_id: Session ID
            conference_id: Conference ID for validation
            limit: Maximum number of records to return

        Returns:
            List of SessionAttendance records sorted by check-in time (newest first)
        """
        db = get_database()

        if not ObjectId.is_valid(session_id) or not ObjectId.is_valid(conference_id):
            return []

        cursor = db.session_attendance.find({
            "session_id": ObjectId(session_id),
            "conference_id": ObjectId(conference_id)
        }).sort("checked_in_at", -1).limit(limit)

        records = await cursor.to_list(length=limit)
        return [SessionAttendance(**r) for r in records]

    async def get_attendance_count(
        self,
        session_id: str
    ) -> int:
        """
        Get attendance count for a session.

        Args:
            session_id: Session ID

        Returns:
            Number of check-ins for the session
        """
        db = get_database()

        if not ObjectId.is_valid(session_id):
            return 0

        count = await db.session_attendance.count_documents({
            "session_id": ObjectId(session_id)
        })
        return count

    async def search_registrations(
        self,
        conference_id: str,
        query: str,
        limit: int = 20
    ) -> List[Dict]:
        """
        Search conference registrations by name or phone.

        Used for manual check-in search functionality.

        Args:
            conference_id: Conference ID to search within
            query: Search query (name or phone)
            limit: Maximum results to return

        Returns:
            List of registration documents matching the query
        """
        db = get_database()

        import re as regex_module

        if not ObjectId.is_valid(conference_id) or len(query) < 2:
            return []

        # Try phone normalization for phone-like queries
        phone_variants = normalize_phone_number(query)

        # Escape special regex characters for safe name search
        escaped_query = regex_module.escape(query)

        # Build search query (name or phone with normalized variants)
        if phone_variants:
            # Query looks like a phone number - search by phone variants primarily
            # Also include name search for cases where someone has numbers in their name
            search_filter = {
                "conference_id": ObjectId(conference_id),
                "status": "confirmed",
                "$or": [
                    {"user_name": {"$regex": escaped_query, "$options": "i"}},
                    {"user_phone": {"$in": phone_variants}}
                ]
            }
        else:
            # Query is not a valid phone number - search by name only
            # Also try partial phone regex for partial phone matches (e.g., "244123")
            search_filter = {
                "conference_id": ObjectId(conference_id),
                "status": "confirmed",
                "$or": [
                    {"user_name": {"$regex": escaped_query, "$options": "i"}},
                    {"user_phone": {"$regex": escaped_query}}
                ]
            }

        cursor = db.conference_registrations.find(search_filter).limit(limit)
        return await cursor.to_list(length=limit)

    async def is_checked_in_to_session(
        self,
        session_id: str,
        registration_id: str
    ) -> bool:
        """
        Check if registration is already checked in to session.

        Args:
            session_id: Session ID
            registration_id: Registration ID

        Returns:
            True if already checked in, False otherwise
        """
        db = get_database()

        if not ObjectId.is_valid(session_id) or not ObjectId.is_valid(registration_id):
            return False

        existing = await db.session_attendance.find_one({
            "session_id": ObjectId(session_id),
            "registration_id": ObjectId(registration_id)
        })
        return existing is not None

    async def get_conference_attendance_report(
        self,
        conference_id: str
    ) -> List[Dict]:
        """
        Get attendance report for a conference.

        Returns registrations who attended at least one session,
        with their session list, branch, and bus route info.

        Args:
            conference_id: Conference ID to get report for.

        Returns:
            List[Dict]: List of attendance report items with:
                - registration_id, user_name, user_phone, user_email
                - branch_name (from constants lookup)
                - bus_route_name, bus_pickup_location (from bus_routes collection)
                - sessions_attended (list of session names)
                - total_sessions, first_check_in
        """
        db = get_database()

        if not ObjectId.is_valid(conference_id):
            return []

        conf_oid = ObjectId(conference_id)

        # Aggregation to group attendance by registration_id
        pipeline = [
            # Match attendance records for this conference
            {"$match": {"conference_id": conf_oid}},
            # Sort by check-in time to get first check-in
            {"$sort": {"checked_in_at": 1}},
            # Group by registration_id
            {
                "$group": {
                    "_id": "$registration_id",
                    "sessions_attended": {"$push": "$session_name"},
                    "first_check_in": {"$first": "$checked_in_at"},
                    "total_sessions": {"$sum": 1}
                }
            }
        ]

        attendance_groups = await db.session_attendance.aggregate(pipeline).to_list(length=None)

        if not attendance_groups:
            return []

        # Get all registration IDs
        registration_ids = [g["_id"] for g in attendance_groups]

        # Fetch all registrations
        registrations = await db.conference_registrations.find({
            "_id": {"$in": registration_ids}
        }).to_list(length=None)

        # Create lookup map
        reg_map = {r["_id"]: r for r in registrations}

        # Get unique bus_route_ids and branch_ids for bulk lookup
        bus_route_ids = set()
        branch_ids = set()
        for reg in registrations:
            if reg.get("bus_route_id"):
                bus_route_ids.add(reg["bus_route_id"])
            if reg.get("branch_id"):
                branch_ids.add(reg["branch_id"])

        # Fetch bus routes
        bus_routes = {}
        if bus_route_ids:
            routes = await db.bus_routes.find({
                "_id": {"$in": list(bus_route_ids)}
            }).to_list(length=None)
            bus_routes = {r["_id"]: r for r in routes}

        # Fetch branches
        branches = {}
        if branch_ids:
            branch_docs = await db.branches.find({
                "_id": {"$in": list(branch_ids)}
            }).to_list(length=None)
            branches = {b["_id"]: b for b in branch_docs}

        # Build report items
        report = []
        for group in attendance_groups:
            reg_id = group["_id"]
            reg = reg_map.get(reg_id)

            if not reg:
                continue

            # Get branch info - lookup name from branches collection
            branch_id = reg.get("branch_id")
            branch_name = None
            if branch_id:
                branch = branches.get(branch_id)
                if branch:
                    branch_name = branch.get("name")
            if not branch_name:
                branch_name = reg.get("church_name")

            # Get bus route info
            bus_route_name = None
            bus_pickup_location = None
            if reg.get("bus_route_id"):
                bus_route = bus_routes.get(reg["bus_route_id"])
                if bus_route:
                    bus_route_name = bus_route.get("name") or bus_route.get("route_name")
                    bus_pickup_location = bus_route.get("pickup_location")

            report.append({
                "registration_id": str(reg_id),
                "user_name": reg.get("user_name", "Unknown"),
                "user_phone": reg.get("user_phone", ""),
                "user_email": reg.get("user_email"),
                "branch_name": branch_name,
                "bus_route_name": bus_route_name,
                "bus_pickup_location": bus_pickup_location,
                "sessions_attended": group["sessions_attended"],
                "total_sessions": group["total_sessions"],
                "first_check_in": group["first_check_in"]
            })

        # Sort by first check-in time
        report.sort(key=lambda x: x["first_check_in"])

        return report

    async def member_check_in_by_code(
        self,
        registration_code: str,
        session_id: str,
        latitude: float,
        longitude: float
    ) -> SessionAttendance:
        """
        Member self-service check-in to session using registration code with GPS validation.

        Args:
            registration_code: Registration code (REG-XXXXXXXX)
            session_id: Target session ID
            latitude: User's current latitude
            longitude: User's current longitude

        Returns:
            SessionAttendance record

        Raises:
            ValueError: If registration, session, or conference not found
            PermissionError: If user is too far from venue
            Exception: If already checked in
        """
        db = get_database()

        # Find registration by code
        registration = await db.conference_registrations.find_one({
            "registration_code": registration_code,
            "status": "confirmed"
        })
        if not registration:
            raise ValueError("Registration not found or cancelled")

        # Validate session exists and belongs to this conference
        if not ObjectId.is_valid(session_id):
            raise ValueError("Invalid session ID")

        session = await db.conference_sessions.find_one({
            "_id": ObjectId(session_id),
            "conference_id": registration["conference_id"]
        })
        if not session:
            raise ValueError("Session not found or not part of this conference")

        # Get conference for GPS validation
        conference = await db.conferences.find_one({
            "_id": registration["conference_id"]
        })
        if not conference:
            raise ValueError("Conference not found")

        # Validate GPS location only if location check-in is required
        location_required = conference.get("location_checkin_required", True)
        if location_required:
            await self._validate_gps_location(
                latitude, longitude,
                conference.get("venue_latitude"),
                conference.get("venue_longitude"),
                conference.get("venue_checkin_radius", 1000)
            )

        return await self._perform_check_in(
            db=db,
            registration=registration,
            session_id=session_id,
            admin_id=None,
            method="self_checkin"
        )

    async def member_check_in_by_phone(
        self,
        phone: str,
        session_id: str,
        latitude: float,
        longitude: float
    ) -> SessionAttendance:
        """
        Member self-service check-in to session using phone number with GPS validation.

        Args:
            phone: Phone number
            session_id: Target session ID
            latitude: User's current latitude
            longitude: User's current longitude

        Returns:
            SessionAttendance record

        Raises:
            ValueError: If registration, session, or conference not found
            PermissionError: If user is too far from venue
            Exception: If already checked in
        """
        db = get_database()

        # Validate session ID first
        if not ObjectId.is_valid(session_id):
            raise ValueError("Invalid session ID")

        # Get session to find conference_id
        session = await db.conference_sessions.find_one({"_id": ObjectId(session_id)})
        if not session:
            raise ValueError("Session not found")

        # Normalize phone to get all possible formats
        phone_variants = normalize_phone_number(phone)
        if not phone_variants:
            raise ValueError("Invalid phone number format")

        # Find registration by phone for this conference using all variants
        registration = await db.conference_registrations.find_one({
            "conference_id": session["conference_id"],
            "user_phone": {"$in": phone_variants},
            "status": "confirmed"
        })

        if not registration:
            raise ValueError(
                f"No registration found for phone: {phone}. "
                f"Please register for this conference first before checking in. "
                f"If you have already registered, please use the same phone number you registered with."
            )

        # Get conference for GPS validation
        conference = await db.conferences.find_one({
            "_id": registration["conference_id"]
        })
        if not conference:
            raise ValueError("Conference not found")

        # Validate GPS location only if location check-in is required
        location_required = conference.get("location_checkin_required", True)
        if location_required:
            await self._validate_gps_location(
                latitude, longitude,
                conference.get("venue_latitude"),
                conference.get("venue_longitude"),
                conference.get("venue_checkin_radius", 1000)
            )

        return await self._perform_check_in(
            db=db,
            registration=registration,
            session_id=session_id,
            admin_id=None,
            method="self_checkin_phone"
        )

    async def _validate_gps_location(
        self,
        user_lat: float,
        user_lon: float,
        venue_lat: Optional[float],
        venue_lon: Optional[float],
        radius: float
    ) -> None:
        """
        Validate that user is within venue radius.

        Args:
            user_lat: User's latitude
            user_lon: User's longitude
            venue_lat: Venue latitude
            venue_lon: Venue longitude
            radius: Maximum allowed distance in meters

        Raises:
            ValueError: If venue coordinates not set
            PermissionError: If user is too far from venue
        """
        import math

        if venue_lat is None or venue_lon is None:
            raise ValueError("Venue GPS coordinates not configured for this conference")

        # Calculate distance using Haversine formula
        R = 6371000  # Earth's radius in meters
        lat1_rad = math.radians(user_lat)
        lat2_rad = math.radians(venue_lat)
        delta_lat = math.radians(venue_lat - user_lat)
        delta_lon = math.radians(venue_lon - user_lon)

        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c

        if distance > radius:
            raise PermissionError(
                f"You are too far from the venue. Distance: {distance:.0f}m, "
                f"Maximum allowed: {radius:.0f}m"
            )

    # ============================================
    # SERVICE CHECK-IN METHODS
    # ============================================

    async def check_in_member_to_service(
        self,
        service_id: str,
        user_id: str,
        check_in_method: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        admin_id: Optional[str] = None
    ) -> SessionAttendance:
        """
        Check in existing member to a church service.

        Args:
            service_id: Service ID
            user_id: User/Member ID
            check_in_method: Method used (qr_scan, phone_lookup, manual_search)
            latitude: User's current latitude (optional)
            longitude: User's current longitude (optional)
            admin_id: Admin performing check-in (optional)

        Returns:
            SessionAttendance record

        Raises:
            ValueError: If service or user not found
            PermissionError: If GPS validation fails
            Exception: If already checked in
        """
        db = get_database()

        # Validate service exists
        if not ObjectId.is_valid(service_id):
            raise ValueError("Invalid service ID")

        service = await db.services.find_one({"_id": ObjectId(service_id)})
        if not service:
            raise ValueError("Service not found")

        # Validate user exists
        if not ObjectId.is_valid(user_id):
            raise ValueError("Invalid user ID")

        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise ValueError("User not found")

        # GPS validation if coordinates provided
        if latitude is not None and longitude is not None:
            venue_lat = service.get("venue_latitude")
            venue_lon = service.get("venue_longitude")
            if venue_lat and venue_lon:
                await self._validate_gps_location(
                    latitude, longitude,
                    venue_lat, venue_lon,
                    service.get("venue_checkin_radius", 1000)
                )

        # Check for existing check-in
        existing = await db.session_attendance.find_one({
            "service_id": ObjectId(service_id),
            "registration_id": ObjectId(user_id)
        })
        if existing:
            logger.warning(
                f"REPEAT service check-in: {user.get('name')} -> "
                f"{service.get('service_type')} on {service.get('service_date')} (already checked in)"
            )
            attendance = SessionAttendance(**existing)
            attendance.is_repeat_checkin = True
            return attendance

        # Build attendance document with denormalized fields
        attendance_doc = {
            "service_id": ObjectId(service_id),
            "conference_id": None,  # Not a conference
            "registration_id": ObjectId(user_id),  # User ID for services
            "checked_in_at": datetime.utcnow(),
            "checked_in_by": ObjectId(admin_id) if admin_id and ObjectId.is_valid(admin_id) else None,
            "check_in_method": check_in_method,
            "user_name": user.get("name") or user.get("full_name"),
            "user_phone": user.get("phone"),
            "session_name": f"{service.get('service_type')} - {service.get('service_date').strftime('%Y-%m-%d') if service.get('service_date') else 'N/A'}",
            "day_number": None,  # Not applicable for services
            "created_at": datetime.utcnow()
        }

        try:
            result = await db.session_attendance.insert_one(attendance_doc)
            attendance_doc["_id"] = result.inserted_id

            logger.info(
                f"Service check-in SUCCESS: {user.get('name')} -> "
                f"{service.get('service_type')} (method: {check_in_method})"
            )

            # Update user's last visit information
            await db.users.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "last_visit_date": datetime.utcnow()
                    },
                    "$inc": {
                        "visit_count": 1
                    }
                }
            )

            # Increment service actual_attendance
            await db.services.update_one(
                {"_id": ObjectId(service_id)},
                {"$inc": {"actual_attendance": 1}}
            )

            return SessionAttendance(**attendance_doc)

        except DuplicateKeyError:
            raise Exception("Already checked in to this service")

    async def check_in_visitor_to_service(
        self,
        service_id: str,
        visitor_data: Dict,
        check_in_method: str = "visitor_registration"
    ) -> Dict:
        """
        Register visitor and check in to service simultaneously.

        Creates a new visitor user profile and checks them in to the service.

        Args:
            service_id: Service ID
            visitor_data: Visitor information (name, phone, email, church_name, department_interests)
            check_in_method: Method used (default: visitor_registration)

        Returns:
            Dict with user_id and attendance_id

        Raises:
            ValueError: If service not found or invalid data
        """
        db = get_database()

        # Validate service exists
        if not ObjectId.is_valid(service_id):
            raise ValueError("Invalid service ID")

        service = await db.services.find_one({"_id": ObjectId(service_id)})
        if not service:
            raise ValueError("Service not found")

        # Normalize phone number
        phone = visitor_data.get("phone")
        if not phone:
            raise ValueError("Phone number is required for visitor registration")

        phone_formats = normalize_phone_number(phone)
        international_phone = next((f for f in phone_formats if f.startswith('+')), phone_formats[0] if phone_formats else phone)

        # Check if user already exists with this phone
        existing_user = await db.users.find_one({"phone": international_phone})

        if existing_user:
            # User exists - just check them in
            user_id = existing_user["_id"]
            logger.info(f"Existing user found for phone {international_phone}, checking in to service")
        else:
            # Create new visitor profile
            user_doc = {
                "phone": international_phone,
                "name": visitor_data.get("name"),
                "full_name": visitor_data.get("name"),
                "email": visitor_data.get("email"),
                "church_name": visitor_data.get("church_name"),
                "member_status": "visitor",
                "current_spiritual_stage": "first_timer",
                "first_visit_date": datetime.utcnow(),
                "last_visit_date": datetime.utcnow(),
                "visit_count": 1,
                "roles": [],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            # Add department interests if provided
            department_interests = visitor_data.get("department_interests", [])
            if department_interests:
                user_doc["departments"] = [
                    {
                        "name": dept,
                        "status": "interested",
                        "assigned_at": None
                    }
                    for dept in department_interests
                ]

            result = await db.users.insert_one(user_doc)
            user_id = result.inserted_id

            logger.info(
                f"Created new visitor profile: {visitor_data.get('name')} "
                f"(phone: {international_phone})"
            )

            # Trigger visitor journey automation (welcome SMS)
            # This would be handled by the visitor_service in a real implementation
            # For now, we'll just log it
            logger.info(f"TODO: Trigger visitor journey automation for user {user_id}")

        # Now check in the user to the service
        attendance_doc = {
            "service_id": ObjectId(service_id),
            "conference_id": None,
            "registration_id": user_id,
            "checked_in_at": datetime.utcnow(),
            "checked_in_by": None,
            "check_in_method": check_in_method,
            "user_name": visitor_data.get("name"),
            "user_phone": international_phone,
            "session_name": f"{service.get('service_type')} - {service.get('service_date').strftime('%Y-%m-%d') if service.get('service_date') else 'N/A'}",
            "day_number": None,
            "created_at": datetime.utcnow()
        }

        try:
            result = await db.session_attendance.insert_one(attendance_doc)
            attendance_id = result.inserted_id

            logger.info(
                f"Visitor check-in SUCCESS: {visitor_data.get('name')} -> "
                f"{service.get('service_type')}"
            )

            # Increment service actual_attendance
            await db.services.update_one(
                {"_id": ObjectId(service_id)},
                {"$inc": {"actual_attendance": 1}}
            )

            return {
                "user_id": str(user_id),
                "attendance_id": str(attendance_id),
                "is_new_visitor": existing_user is None
            }

        except DuplicateKeyError:
            # User already checked in - return their existing record
            existing_attendance = await db.session_attendance.find_one({
                "service_id": ObjectId(service_id),
                "registration_id": user_id
            })
            return {
                "user_id": str(user_id),
                "attendance_id": str(existing_attendance["_id"]),
                "is_new_visitor": False,
                "is_repeat_checkin": True
            }

    async def get_service_attendees(
        self,
        service_id: str,
        member_status: Optional[str] = None
    ) -> List[Dict]:
        """
        Get list of attendees for a service.

        Args:
            service_id: Service ID
            member_status: Filter by member status (visitor, active_member, inactive_member)

        Returns:
            List of attendee dictionaries with user info
        """
        db = get_database()

        if not ObjectId.is_valid(service_id):
            return []

        # Build aggregation pipeline
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
                "$project": {
                    "user_id": {"$toString": "$registration_id"},
                    "name": {"$ifNull": ["$user.name", "$user_name"]},
                    "phone": {"$ifNull": ["$user.phone", "$user_phone"]},
                    "member_status": "$user.member_status",
                    "current_spiritual_stage": "$user.current_spiritual_stage",
                    "checked_in_at": 1,
                    "check_in_method": 1
                }
            },
            {"$sort": {"checked_in_at": -1}}
        ]

        # Add member_status filter if provided
        if member_status:
            pipeline.insert(2, {"$match": {"user.member_status": member_status}})

        cursor = db.session_attendance.aggregate(pipeline)
        attendees = await cursor.to_list(length=None)

        return attendees


# Global service instance
session_attendance_service = SessionAttendanceService()
