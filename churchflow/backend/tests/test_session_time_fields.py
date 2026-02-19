"""
Unit tests for session time fields functionality.

Tests CRUD operations for session start_time and end_time fields with real data.
Verifies that time fields are properly created, updated, and retrieved.
"""

import pytest
from datetime import datetime
from bson import ObjectId
from unittest.mock import patch

# Import service at module level (not inside patch context)
from app.services.session_service import SessionService


@pytest.mark.asyncio
class TestSessionTimeFieldsCRUD:
    """Test cases for session time fields CRUD operations with real data."""

    @pytest.mark.asyncio
    async def test_create_session_with_time_fields(
        self, test_db, sample_conference
    ):
        """
        Test creating a session with start_time and end_time fields.

        Expected: Session is created with time fields and stored correctly.
        """
        with patch('app.services.session_service.get_database', return_value=test_db):

            service = SessionService()

            # Create session with time fields
            session_data = {
                "name": "Morning Worship",
                "description": "Morning worship with time fields",
                "location": "Main Auditorium",
                "day_number": 1,
                "day_label": "Day 1 - Opening",
                "session_date": datetime(2025, 12, 25, 9, 0),
                "start_time": "09:00",
                "end_time": "11:00",
                "order": 1,
                "sms_confirmation_enabled": False
            }

            session = await service.create_session(
                conference_id=str(sample_conference["_id"]),
                session_data=session_data,
                user_id=str(ObjectId())
            )

            # Verify session was created
            assert session is not None
            assert session.name == "Morning Worship"
            assert session.start_time == "09:00"
            assert session.end_time == "11:00"

            # Verify in database
            stored = await test_db.conference_sessions.find_one({"_id": session.id})
            assert stored is not None
            assert stored["start_time"] == "09:00"
            assert stored["end_time"] == "11:00"

    @pytest.mark.asyncio
    async def test_create_session_without_time_fields(
        self, test_db, sample_conference
    ):
        """
        Test creating a session without time fields (backwards compatibility).

        Expected: Session is created without time fields (None values).
        """
        with patch('app.services.session_service.get_database', return_value=test_db):

            service = SessionService()

            # Create session without time fields
            session_data = {
                "name": "Evening Service",
                "description": "Service without time fields",
                "location": "Chapel",
                "day_number": 1,
                "day_label": "Day 1",
                "session_date": datetime(2025, 12, 25, 18, 0),
                "order": 2
            }

            session = await service.create_session(
                conference_id=str(sample_conference["_id"]),
                session_data=session_data,
                user_id=str(ObjectId())
            )

            # Verify session was created without time fields
            assert session is not None
            assert session.name == "Evening Service"
            assert not hasattr(session, 'start_time') or session.start_time is None
            assert not hasattr(session, 'end_time') or session.end_time is None

    @pytest.mark.asyncio
    async def test_update_session_add_time_fields(
        self, test_db, sample_conference
    ):
        """
        Test updating an existing session to add time fields.

        Expected: Session is updated with new time fields.
        """
        with patch('app.services.session_service.get_database', return_value=test_db):

            service = SessionService()

            # Create session without time fields
            session_data = {
                "name": "Afternoon Workshop",
                "description": "Workshop session",
                "location": "Room 101",
                "day_number": 1,
                "day_label": "Day 1",
                "session_date": datetime(2025, 12, 25, 14, 0),
                "order": 3
            }

            session = await service.create_session(
                conference_id=str(sample_conference["_id"]),
                session_data=session_data,
                user_id=str(ObjectId())
            )

            # Update with time fields
            update_data = {
                "start_time": "14:00",
                "end_time": "16:30"
            }

            updated = await service.update_session(
                session_id=str(session.id),
                conference_id=str(sample_conference["_id"]),
                update_data=update_data
            )

            # Verify update
            assert updated is not None
            assert updated.start_time == "14:00"
            assert updated.end_time == "16:30"

            # Verify in database
            stored = await test_db.conference_sessions.find_one({"_id": session.id})
            assert stored["start_time"] == "14:00"
            assert stored["end_time"] == "16:30"

    @pytest.mark.asyncio
    async def test_update_session_modify_time_fields(
        self, test_db, sample_conference
    ):
        """
        Test updating existing time fields on a session.

        Expected: Time fields are updated to new values.
        """
        with patch('app.services.session_service.get_database', return_value=test_db):

            service = SessionService()

            # Create session with time fields
            session_data = {
                "name": "Youth Service",
                "description": "Youth ministry session",
                "location": "Youth Hall",
                "day_number": 2,
                "day_label": "Day 2",
                "session_date": datetime(2025, 12, 26, 10, 0),
                "start_time": "10:00",
                "end_time": "12:00",
                "order": 1
            }

            session = await service.create_session(
                conference_id=str(sample_conference["_id"]),
                session_data=session_data,
                user_id=str(ObjectId())
            )

            # Update time fields
            update_data = {
                "start_time": "10:30",
                "end_time": "12:30"
            }

            updated = await service.update_session(
                session_id=str(session.id),
                conference_id=str(sample_conference["_id"]),
                update_data=update_data
            )

            # Verify update
            assert updated.start_time == "10:30"
            assert updated.end_time == "12:30"

            # Verify in database
            stored = await test_db.conference_sessions.find_one({"_id": session.id})
            assert stored["start_time"] == "10:30"
            assert stored["end_time"] == "12:30"

    @pytest.mark.asyncio
    async def test_get_session_returns_time_fields(
        self, test_db, sample_conference
    ):
        """
        Test retrieving a session returns time fields correctly.

        Expected: Retrieved session includes time fields.
        """
        with patch('app.services.session_service.get_database', return_value=test_db):

            service = SessionService()

            # Create session with time fields
            session_data = {
                "name": "Prayer Meeting",
                "description": "Corporate prayer time",
                "location": "Prayer Room",
                "day_number": 1,
                "day_label": "Day 1",
                "session_date": datetime(2025, 12, 25, 6, 0),
                "start_time": "06:00",
                "end_time": "07:30",
                "order": 0
            }

            created = await service.create_session(
                conference_id=str(sample_conference["_id"]),
                session_data=session_data,
                user_id=str(ObjectId())
            )

            # Retrieve session
            retrieved = await service.get_session(
                session_id=str(created.id),
                conference_id=str(sample_conference["_id"])
            )

            # Verify time fields are returned
            assert retrieved is not None
            assert retrieved.name == "Prayer Meeting"
            assert retrieved.start_time == "06:00"
            assert retrieved.end_time == "07:30"

    @pytest.mark.asyncio
    async def test_list_sessions_includes_time_fields(
        self, test_db, sample_conference
    ):
        """
        Test listing sessions returns time fields for all sessions.

        Expected: All sessions in list include their time fields.
        """
        with patch('app.services.session_service.get_database', return_value=test_db):

            service = SessionService()

            # Create multiple sessions with different time fields
            sessions_to_create = [
                {
                    "name": "Session 1",
                    "day_number": 1,
                    "day_label": "Day 1",
                    "session_date": datetime(2025, 12, 25, 9, 0),
                    "start_time": "09:00",
                    "end_time": "10:30",
                    "order": 1
                },
                {
                    "name": "Session 2",
                    "day_number": 1,
                    "day_label": "Day 1",
                    "session_date": datetime(2025, 12, 25, 11, 0),
                    "start_time": "11:00",
                    "end_time": "12:30",
                    "order": 2
                },
                {
                    "name": "Session 3 - No Times",
                    "day_number": 1,
                    "day_label": "Day 1",
                    "session_date": datetime(2025, 12, 25, 14, 0),
                    "order": 3
                }
            ]

            for session_data in sessions_to_create:
                await service.create_session(
                    conference_id=str(sample_conference["_id"]),
                    session_data=session_data,
                    user_id=str(ObjectId())
                )

            # List all sessions
            sessions = await service.list_sessions(
                conference_id=str(sample_conference["_id"])
            )

            # Verify we got all sessions with time fields
            assert len(sessions) == 3
            assert sessions[0].start_time == "09:00"
            assert sessions[0].end_time == "10:30"
            assert sessions[1].start_time == "11:00"
            assert sessions[1].end_time == "12:30"
            # Third session should have None for times
            assert sessions[2].start_time is None or not hasattr(sessions[2], 'start_time')
            assert sessions[2].end_time is None or not hasattr(sessions[2], 'end_time')

    @pytest.mark.asyncio
    async def test_delete_session_with_time_fields(
        self, test_db, sample_conference
    ):
        """
        Test deleting a session that has time fields.

        Expected: Session is deleted completely including time fields.
        """
        with patch('app.services.session_service.get_database', return_value=test_db):

            service = SessionService()

            # Create session with time fields
            session_data = {
                "name": "Temporary Session",
                "day_number": 1,
                "day_label": "Day 1",
                "session_date": datetime(2025, 12, 25, 15, 0),
                "start_time": "15:00",
                "end_time": "16:00",
                "order": 5
            }

            session = await service.create_session(
                conference_id=str(sample_conference["_id"]),
                session_data=session_data,
                user_id=str(ObjectId())
            )

            # Verify it exists
            stored = await test_db.conference_sessions.find_one({"_id": session.id})
            assert stored is not None

            # Delete the session
            deleted = await service.delete_session(
                session_id=str(session.id),
                conference_id=str(sample_conference["_id"])
            )

            assert deleted is True

            # Verify it's deleted
            not_found = await test_db.conference_sessions.find_one({"_id": session.id})
            assert not_found is None

    @pytest.mark.asyncio
    async def test_time_format_validation(
        self, test_db, sample_conference
    ):
        """
        Test that various time formats are accepted and stored correctly.

        Expected: Time fields accept HH:MM format variations.
        """
        with patch('app.services.session_service.get_database', return_value=test_db):

            service = SessionService()

            # Test different valid time formats
            time_formats = [
                ("09:00", "10:30"),  # Standard format
                ("00:00", "23:59"),  # Edge times
                ("13:45", "15:15"),  # Afternoon times
            ]

            for idx, (start, end) in enumerate(time_formats):
                session_data = {
                    "name": f"Time Test Session {idx}",
                    "day_number": 1,
                    "day_label": "Day 1",
                    "session_date": datetime(2025, 12, 25, 9, 0),
                    "start_time": start,
                    "end_time": end,
                    "order": idx
                }

                session = await service.create_session(
                    conference_id=str(sample_conference["_id"]),
                    session_data=session_data,
                    user_id=str(ObjectId())
                )

                # Verify times are stored exactly as provided
                assert session.start_time == start
                assert session.end_time == end

                # Verify in database
                stored = await test_db.conference_sessions.find_one({"_id": session.id})
                assert stored["start_time"] == start
                assert stored["end_time"] == end
