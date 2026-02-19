"""
Conference session management service.

This module provides business logic for managing conference sessions,
including CRUD operations and day-based organization.
"""

from typing import List, Optional, Dict
from bson import ObjectId
from datetime import datetime, timedelta
import logging

from app.core.database import get_database
from app.models.session import ConferenceSession
from app.models.conference import Conference

logger = logging.getLogger(__name__)


class SessionService:
    """Service for conference session operations."""

    async def create_session(
        self,
        conference_id: str,
        session_data: Dict,
        user_id: Optional[str] = None
    ) -> ConferenceSession:
        """
        Create new conference session.

        Args:
            conference_id: Parent conference ID
            session_data: Session data
            user_id: Creator user ID (optional)

        Returns:
            Created ConferenceSession object

        Raises:
            ValueError: If conference not found or date validation fails
            Exception: If database operation fails
        """
        db = get_database()

        # Validate conference exists
        if not ObjectId.is_valid(conference_id):
            raise ValueError("Invalid conference ID")

        conference = await db.conferences.find_one({"_id": ObjectId(conference_id)})
        if not conference:
            raise ValueError(f"Conference not found: {conference_id}")

        # Validate session_date is within conference dates
        session_date = session_data.get("session_date")
        if session_date:
            conf_start = conference.get("start_date")
            conf_end = conference.get("end_date")

            # Convert to date for comparison (ignore time)
            session_date_only = session_date.date() if hasattr(session_date, 'date') else session_date
            conf_start_only = conf_start.date() if hasattr(conf_start, 'date') else conf_start
            conf_end_only = conf_end.date() if hasattr(conf_end, 'date') else conf_end

            if not (conf_start_only <= session_date_only <= conf_end_only):
                raise ValueError(
                    f"Session date must be between conference start ({conf_start_only}) "
                    f"and end ({conf_end_only}) dates"
                )

        # Prepare session document
        session_data["conference_id"] = ObjectId(conference_id)
        session_data["created_at"] = datetime.utcnow()
        session_data["updated_at"] = datetime.utcnow()

        if user_id and ObjectId.is_valid(user_id):
            session_data["created_by"] = ObjectId(user_id)

        try:
            result = await db.conference_sessions.insert_one(session_data)
            session_data["_id"] = result.inserted_id

            logger.info(
                f"Created session '{session_data.get('name')}' for conference {conference_id}"
            )
            return ConferenceSession(**session_data)

        except Exception as e:
            logger.error(f"Failed to create session: {str(e)}")
            raise Exception(f"Failed to create session: {str(e)}")

    async def get_session(
        self,
        session_id: str,
        conference_id: Optional[str] = None
    ) -> Optional[ConferenceSession]:
        """
        Get session by ID.

        Args:
            session_id: Session ID
            conference_id: Optional conference ID for validation

        Returns:
            ConferenceSession object or None if not found
        """
        db = get_database()

        if not ObjectId.is_valid(session_id):
            return None

        query = {"_id": ObjectId(session_id)}

        # Optionally validate conference ownership
        if conference_id and ObjectId.is_valid(conference_id):
            query["conference_id"] = ObjectId(conference_id)

        session_doc = await db.conference_sessions.find_one(query)

        if session_doc:
            return ConferenceSession(**session_doc)
        return None

    async def list_sessions(
        self,
        conference_id: str,
        day_number: Optional[int] = None,
        limit: int = 100
    ) -> List[ConferenceSession]:
        """
        List sessions for a conference.

        Args:
            conference_id: Conference ID
            day_number: Optional filter by day number
            limit: Maximum number of results

        Returns:
            List of ConferenceSession objects ordered by day and order
        """
        db = get_database()

        if not ObjectId.is_valid(conference_id):
            return []

        query = {"conference_id": ObjectId(conference_id)}

        if day_number is not None:
            query["day_number"] = day_number

        cursor = db.conference_sessions.find(query).sort([
            ("day_number", 1),
            ("order", 1),
            ("session_date", 1)
        ]).limit(limit)

        sessions = await cursor.to_list(length=limit)

        return [ConferenceSession(**session) for session in sessions]

    async def list_sessions_grouped_by_day(
        self,
        conference_id: str
    ) -> Dict[int, List[ConferenceSession]]:
        """
        List sessions grouped by day number.

        Args:
            conference_id: Conference ID

        Returns:
            Dictionary mapping day_number to list of sessions
        """
        sessions = await self.list_sessions(conference_id, limit=1000)

        # Group by day_number
        sessions_by_day = {}
        for session in sessions:
            day = session.day_number
            if day not in sessions_by_day:
                sessions_by_day[day] = []
            sessions_by_day[day].append(session)

        return sessions_by_day

    async def update_session(
        self,
        session_id: str,
        conference_id: str,
        update_data: Dict
    ) -> Optional[ConferenceSession]:
        """
        Update session.

        Args:
            session_id: Session ID
            conference_id: Conference ID (for validation)
            update_data: Fields to update

        Returns:
            Updated ConferenceSession object or None

        Raises:
            ValueError: If date validation fails
            Exception: If database operation fails
        """
        db = get_database()

        if not ObjectId.is_valid(session_id) or not ObjectId.is_valid(conference_id):
            return None

        # If updating session_date, validate against conference dates
        if "session_date" in update_data:
            conference = await db.conferences.find_one({"_id": ObjectId(conference_id)})
            if conference:
                session_date = update_data["session_date"]
                conf_start = conference.get("start_date")
                conf_end = conference.get("end_date")

                session_date_only = session_date.date() if hasattr(session_date, 'date') else session_date
                conf_start_only = conf_start.date() if hasattr(conf_start, 'date') else conf_start
                conf_end_only = conf_end.date() if hasattr(conf_end, 'date') else conf_end

                if not (conf_start_only <= session_date_only <= conf_end_only):
                    raise ValueError("Session date must be within conference date range")

        update_data["updated_at"] = datetime.utcnow()

        try:
            result = await db.conference_sessions.find_one_and_update(
                {
                    "_id": ObjectId(session_id),
                    "conference_id": ObjectId(conference_id)
                },
                {"$set": update_data},
                return_document=True
            )

            if result:
                logger.info(f"Updated session: {session_id}")
                return ConferenceSession(**result)

            return None

        except Exception as e:
            logger.error(f"Failed to update session: {str(e)}")
            raise Exception(f"Failed to update session: {str(e)}")

    async def delete_session(
        self,
        session_id: str,
        conference_id: str
    ) -> bool:
        """
        Delete session.

        Args:
            session_id: Session ID
            conference_id: Conference ID (for validation)

        Returns:
            True if deleted, False if not found
        """
        db = get_database()

        if not ObjectId.is_valid(session_id) or not ObjectId.is_valid(conference_id):
            return False

        try:
            result = await db.conference_sessions.delete_one({
                "_id": ObjectId(session_id),
                "conference_id": ObjectId(conference_id)
            })

            if result.deleted_count > 0:
                logger.info(f"Deleted session: {session_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to delete session: {str(e)}")
            return False

    async def generate_conference_days(
        self,
        conference_id: str
    ) -> List[Dict]:
        """
        Generate list of conference days from date range.

        Helpful for UI to show available days when creating sessions.

        Args:
            conference_id: Conference ID

        Returns:
            List of day information dictionaries with:
                - day_number: Day number (1, 2, 3...)
                - day_label: Suggested label (e.g., "Day 1")
                - date: ISO format date string
                - date_display: Human-readable date

        Raises:
            ValueError: If conference not found
        """
        db = get_database()

        if not ObjectId.is_valid(conference_id):
            raise ValueError("Invalid conference ID")

        conference = await db.conferences.find_one({"_id": ObjectId(conference_id)})
        if not conference:
            raise ValueError(f"Conference not found: {conference_id}")

        start_date = conference.get("start_date")
        end_date = conference.get("end_date")

        if not start_date or not end_date:
            raise ValueError("Conference missing start or end date")

        days = []
        current = start_date.date() if hasattr(start_date, 'date') else start_date
        end = end_date.date() if hasattr(end_date, 'date') else end_date
        day_num = 1

        while current <= end:
            days.append({
                "day_number": day_num,
                "day_label": f"Day {day_num}",
                "date": current.isoformat(),
                "date_display": current.strftime("%B %d, %Y")
            })
            current += timedelta(days=1)
            day_num += 1

        return days

    async def get_session_count(self, conference_id: str) -> int:
        """
        Get total number of sessions for a conference.

        Args:
            conference_id: Conference ID

        Returns:
            Number of sessions
        """
        db = get_database()

        if not ObjectId.is_valid(conference_id):
            return 0

        count = await db.conference_sessions.count_documents({
            "conference_id": ObjectId(conference_id)
        })

        return count

    async def get_todays_sessions(
        self,
        conference_id: str,
        registration_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Get sessions scheduled for today with optional check-in status.

        Args:
            conference_id: Conference ID
            registration_id: Optional registration ID to check attendance status

        Returns:
            List of session dictionaries with:
                - id, name, description, location
                - day_number, day_label, order, session_date
                - already_checked_in: bool (if registration_id provided)
        """
        from datetime import time
        db = get_database()

        if not ObjectId.is_valid(conference_id):
            return []

        # Get today's date range (start of day to end of day)
        today_start = datetime.combine(datetime.utcnow().date(), time.min)
        today_end = datetime.combine(datetime.utcnow().date(), time.max)

        # Find sessions for today
        cursor = db.conference_sessions.find({
            "conference_id": ObjectId(conference_id),
            "session_date": {"$gte": today_start, "$lte": today_end}
        }).sort([("order", 1), ("session_date", 1)])

        sessions = await cursor.to_list(length=100)

        if not sessions:
            return []

        # Get check-in status for each session if registration_id provided
        checked_in_sessions = set()
        if registration_id and ObjectId.is_valid(registration_id):
            session_ids = [s["_id"] for s in sessions]
            attendance_records = await db.session_attendance.find({
                "session_id": {"$in": session_ids},
                "registration_id": ObjectId(registration_id)
            }).to_list(length=100)
            checked_in_sessions = {str(r["session_id"]) for r in attendance_records}

        # Build response
        result = []
        for session in sessions:
            result.append({
                "id": str(session["_id"]),
                "name": session.get("name", "Session"),
                "description": session.get("description"),
                "location": session.get("location"),
                "day_number": session.get("day_number", 1),
                "day_label": session.get("day_label", "Day 1"),
                "order": session.get("order", 0),
                "session_date": session.get("session_date"),
                "already_checked_in": str(session["_id"]) in checked_in_sessions
            })

        return result


# Global service instance
session_service = SessionService()
