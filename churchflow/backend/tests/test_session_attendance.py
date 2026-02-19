"""
Unit tests for session attendance service.

Tests session check-in functionality including QR code check-in,
manual check-in, duplicate prevention, and attendance list retrieval.
"""

import pytest
from datetime import datetime
from bson import ObjectId
from unittest.mock import patch, AsyncMock


@pytest.mark.asyncio
class TestSessionAttendanceService:
    """Test cases for SessionAttendanceService."""

    @pytest.mark.asyncio
    async def test_check_in_by_code_success(
        self, test_db, sample_conference, sample_session, sample_registration
    ):
        """
        Test successful check-in with valid registration code.

        Expected: Creates attendance record with correct data.
        """
        # Import service after db is set up
        with patch('app.core.database.get_database', return_value=test_db):
            from app.services.session_attendance_service import SessionAttendanceService

            service = SessionAttendanceService()

            # Perform check-in
            result = await service.check_in_by_code(
                registration_code=sample_registration["registration_code"],
                session_id=str(sample_session["_id"]),
                admin_id=None
            )

            # Verify result
            assert result is not None
            assert result.session_id == sample_session["_id"]
            assert result.registration_id == sample_registration["_id"]
            assert result.user_name == sample_registration["user_name"]
            assert result.user_phone == sample_registration["user_phone"]
            assert result.session_name == sample_session["name"]
            assert result.check_in_method == "qr_scan"

            # Verify stored in database
            stored = await test_db.session_attendance.find_one({
                "session_id": sample_session["_id"],
                "registration_id": sample_registration["_id"]
            })
            assert stored is not None

    @pytest.mark.asyncio
    async def test_check_in_duplicate_prevented(
        self, test_db, sample_conference, sample_session, sample_registration
    ):
        """
        Test that duplicate check-in to same session is prevented.

        Expected: First check-in succeeds, second raises exception.
        """
        with patch('app.core.database.get_database', return_value=test_db):
            from app.services.session_attendance_service import SessionAttendanceService

            service = SessionAttendanceService()

            # First check-in should succeed
            await service.check_in_by_code(
                registration_code=sample_registration["registration_code"],
                session_id=str(sample_session["_id"]),
                admin_id=None
            )

            # Second check-in should fail
            with pytest.raises(Exception) as exc_info:
                await service.check_in_by_code(
                    registration_code=sample_registration["registration_code"],
                    session_id=str(sample_session["_id"]),
                    admin_id=None
                )

            assert "Already checked in" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_check_in_invalid_registration_code(
        self, test_db, sample_conference, sample_session
    ):
        """
        Test check-in with non-existent registration code.

        Expected: Raises ValueError with "Registration not found".
        """
        with patch('app.core.database.get_database', return_value=test_db):
            from app.services.session_attendance_service import SessionAttendanceService

            service = SessionAttendanceService()

            with pytest.raises(ValueError) as exc_info:
                await service.check_in_by_code(
                    registration_code="REG-NONEXISTENT",
                    session_id=str(sample_session["_id"]),
                    admin_id=None
                )

            assert "Registration not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_check_in_invalid_session_id(
        self, test_db, sample_conference, sample_registration
    ):
        """
        Test check-in with invalid session ID.

        Expected: Raises ValueError with "Session not found".
        """
        with patch('app.core.database.get_database', return_value=test_db):
            from app.services.session_attendance_service import SessionAttendanceService

            service = SessionAttendanceService()

            # Use a valid ObjectId that doesn't exist
            fake_session_id = str(ObjectId())

            with pytest.raises(ValueError) as exc_info:
                await service.check_in_by_code(
                    registration_code=sample_registration["registration_code"],
                    session_id=fake_session_id,
                    admin_id=None
                )

            assert "Session not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_manual_check_in_success(
        self, test_db, sample_conference, sample_session, sample_registration
    ):
        """
        Test successful check-in via registration ID (manual search).

        Expected: Creates attendance record with method="manual_search".
        """
        with patch('app.core.database.get_database', return_value=test_db):
            from app.services.session_attendance_service import SessionAttendanceService

            service = SessionAttendanceService()

            result = await service.check_in_by_registration_id(
                registration_id=str(sample_registration["_id"]),
                session_id=str(sample_session["_id"]),
                admin_id=None
            )

            assert result is not None
            assert result.check_in_method == "manual_search"
            assert result.user_name == sample_registration["user_name"]

    @pytest.mark.asyncio
    async def test_get_session_attendance(
        self, test_db, sample_conference, sample_session, sample_registration
    ):
        """
        Test fetching attendance list for session.

        Expected: Returns list of checked-in attendees.
        """
        with patch('app.core.database.get_database', return_value=test_db):
            from app.services.session_attendance_service import SessionAttendanceService

            service = SessionAttendanceService()

            # Check in first
            await service.check_in_by_code(
                registration_code=sample_registration["registration_code"],
                session_id=str(sample_session["_id"]),
                admin_id=None
            )

            # Get attendance list
            attendees = await service.get_session_attendance(
                session_id=str(sample_session["_id"]),
                conference_id=str(sample_conference["_id"])
            )

            assert len(attendees) == 1
            assert attendees[0].user_name == sample_registration["user_name"]

    @pytest.mark.asyncio
    async def test_search_registrations_by_name(
        self, test_db, sample_conference, sample_registration
    ):
        """
        Test searching registrations by partial name.

        Expected: Returns matching registrations.
        """
        with patch('app.core.database.get_database', return_value=test_db):
            from app.services.session_attendance_service import SessionAttendanceService

            service = SessionAttendanceService()

            # Search by name
            results = await service.search_registrations(
                conference_id=str(sample_conference["_id"]),
                query="Test"
            )

            assert len(results) == 1
            assert results[0]["user_name"] == sample_registration["user_name"]

    @pytest.mark.asyncio
    async def test_search_registrations_by_phone(
        self, test_db, sample_conference, sample_registration
    ):
        """
        Test searching registrations by full phone number.

        Expected: Returns matching registrations when using full local format.
        Note: Uses full local format since partial matches now require proper phone format.
        """
        with patch('app.core.database.get_database', return_value=test_db):
            from app.services.session_attendance_service import SessionAttendanceService

            service = SessionAttendanceService()

            # Search by full local phone format (which normalizes correctly)
            results = await service.search_registrations(
                conference_id=str(sample_conference["_id"]),
                query="0244123456"  # Full local format
            )

            assert len(results) == 1
            assert results[0]["user_phone"] == sample_registration["user_phone"]

    @pytest.mark.asyncio
    async def test_search_registrations_by_local_phone_format(
        self, test_db, sample_conference, sample_registration
    ):
        """
        Test searching registrations using LOCAL phone format.

        DB stores: +233244123456
        Admin searches: 0244123456

        Expected: Returns matching registration.
        """
        with patch('app.core.database.get_database', return_value=test_db):
            from app.services.session_attendance_service import SessionAttendanceService

            service = SessionAttendanceService()

            # Search by local format phone
            results = await service.search_registrations(
                conference_id=str(sample_conference["_id"]),
                query="0244123456"  # Local format
            )

            assert len(results) == 1
            assert results[0]["user_phone"] == sample_registration["user_phone"]  # +233244123456

    @pytest.mark.asyncio
    async def test_search_registrations_by_international_phone_format(
        self, test_db, sample_conference, sample_registration
    ):
        """
        Test searching registrations using INTERNATIONAL phone format.

        DB stores: +233244123456
        Admin searches: +233244123456

        Expected: Returns matching registration.
        """
        with patch('app.core.database.get_database', return_value=test_db):
            from app.services.session_attendance_service import SessionAttendanceService

            service = SessionAttendanceService()

            # Search by international format phone
            results = await service.search_registrations(
                conference_id=str(sample_conference["_id"]),
                query="+233244123456"  # International format
            )

            assert len(results) == 1
            assert results[0]["user_phone"] == sample_registration["user_phone"]

    @pytest.mark.asyncio
    async def test_search_registrations_by_phone_without_prefix(
        self, test_db, sample_conference, sample_registration
    ):
        """
        Test searching registrations using phone WITHOUT prefix.

        DB stores: +233244123456
        Admin searches: 244123456

        Expected: Returns matching registration.
        """
        with patch('app.core.database.get_database', return_value=test_db):
            from app.services.session_attendance_service import SessionAttendanceService

            service = SessionAttendanceService()

            # Search by phone without prefix
            results = await service.search_registrations(
                conference_id=str(sample_conference["_id"]),
                query="244123456"  # Without prefix
            )

            assert len(results) == 1
            assert results[0]["user_phone"] == sample_registration["user_phone"]

    @pytest.mark.asyncio
    async def test_is_checked_in_to_session(
        self, test_db, sample_conference, sample_session, sample_registration
    ):
        """
        Test checking if registration is already checked in to session.

        Expected: Returns True after check-in, False before.
        """
        with patch('app.core.database.get_database', return_value=test_db):
            from app.services.session_attendance_service import SessionAttendanceService

            service = SessionAttendanceService()

            # Before check-in
            is_checked_in = await service.is_checked_in_to_session(
                session_id=str(sample_session["_id"]),
                registration_id=str(sample_registration["_id"])
            )
            assert is_checked_in is False

            # Perform check-in
            await service.check_in_by_code(
                registration_code=sample_registration["registration_code"],
                session_id=str(sample_session["_id"]),
                admin_id=None
            )

            # After check-in
            is_checked_in = await service.is_checked_in_to_session(
                session_id=str(sample_session["_id"]),
                registration_id=str(sample_registration["_id"])
            )
            assert is_checked_in is True

    @pytest.mark.asyncio
    async def test_check_in_by_phone_success(
        self, test_db, sample_conference, sample_session, sample_registration
    ):
        """
        Test successful check-in via phone number.

        Expected: Creates attendance record with method="phone_lookup".
        """
        with patch('app.core.database.get_database', return_value=test_db):
            from app.services.session_attendance_service import SessionAttendanceService

            service = SessionAttendanceService()

            result = await service.check_in_by_phone(
                phone=sample_registration["user_phone"],
                session_id=str(sample_session["_id"]),
                admin_id=None
            )

            assert result is not None
            assert result.check_in_method == "phone_lookup"
            assert result.user_name == sample_registration["user_name"]
            assert result.user_phone == sample_registration["user_phone"]

    @pytest.mark.asyncio
    async def test_check_in_by_phone_not_found(
        self, test_db, sample_conference, sample_session
    ):
        """
        Test check-in via phone with non-existent phone number.

        Expected: Raises ValueError with "No registration found".
        """
        with patch('app.core.database.get_database', return_value=test_db):
            from app.services.session_attendance_service import SessionAttendanceService

            service = SessionAttendanceService()

            with pytest.raises(ValueError) as exc_info:
                await service.check_in_by_phone(
                    phone="+233999999999",
                    session_id=str(sample_session["_id"]),
                    admin_id=None
                )

            assert "No registration found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_check_in_by_phone_local_format(
        self, test_db, sample_conference, sample_session, sample_registration
    ):
        """
        Test check-in via phone using LOCAL format when DB has INTERNATIONAL format.

        DB stores: +233244123456
        Admin enters: 0244123456

        Expected: Creates attendance record successfully.
        """
        with patch('app.core.database.get_database', return_value=test_db):
            from app.services.session_attendance_service import SessionAttendanceService

            service = SessionAttendanceService()

            # sample_registration has user_phone="+233244123456"
            # Use local format (0244123456) to check in
            result = await service.check_in_by_phone(
                phone="0244123456",  # Local format
                session_id=str(sample_session["_id"]),
                admin_id=None
            )

            assert result is not None
            assert result.check_in_method == "phone_lookup"
            assert result.user_phone == sample_registration["user_phone"]  # +233244123456

    @pytest.mark.asyncio
    async def test_check_in_by_phone_without_prefix(
        self, test_db, sample_conference, sample_session, sample_registration
    ):
        """
        Test check-in via phone WITHOUT prefix when DB has INTERNATIONAL format.

        DB stores: +233244123456
        Admin enters: 244123456

        Expected: Creates attendance record successfully.
        """
        with patch('app.core.database.get_database', return_value=test_db):
            from app.services.session_attendance_service import SessionAttendanceService

            service = SessionAttendanceService()

            # Use format without prefix (244123456) to check in
            result = await service.check_in_by_phone(
                phone="244123456",  # Without prefix
                session_id=str(sample_session["_id"]),
                admin_id=None
            )

            assert result is not None
            assert result.check_in_method == "phone_lookup"
            assert result.user_phone == sample_registration["user_phone"]

    @pytest.mark.asyncio
    async def test_check_in_by_phone_with_country_code_no_plus(
        self, test_db, sample_conference, sample_session, sample_registration
    ):
        """
        Test check-in via phone WITH country code but NO plus sign.

        DB stores: +233244123456
        Admin enters: 233244123456

        Expected: Creates attendance record successfully.
        """
        with patch('app.core.database.get_database', return_value=test_db):
            from app.services.session_attendance_service import SessionAttendanceService

            service = SessionAttendanceService()

            # Use format with country code but no plus (233244123456)
            result = await service.check_in_by_phone(
                phone="233244123456",  # With country code, no plus
                session_id=str(sample_session["_id"]),
                admin_id=None
            )

            assert result is not None
            assert result.check_in_method == "phone_lookup"
            assert result.user_phone == sample_registration["user_phone"]

    @pytest.mark.asyncio
    async def test_get_conference_attendance_report_success(
        self, test_db, sample_conference, sample_session, sample_registration
    ):
        """
        Test getting conference attendance report.

        Expected: Returns list of attendees with session details.
        """
        with patch('app.core.database.get_database', return_value=test_db):
            from app.services.session_attendance_service import SessionAttendanceService

            service = SessionAttendanceService()

            # First check in the attendee
            await service.check_in_by_code(
                registration_code=sample_registration["registration_code"],
                session_id=str(sample_session["_id"]),
                admin_id=None
            )

            # Get the report
            report = await service.get_conference_attendance_report(
                conference_id=str(sample_conference["_id"])
            )

            assert len(report) == 1
            assert report[0]["user_name"] == sample_registration["user_name"]
            assert report[0]["user_phone"] == sample_registration["user_phone"]
            assert len(report[0]["sessions_attended"]) == 1
            assert sample_session["name"] in report[0]["sessions_attended"]
            assert report[0]["total_sessions"] == 1

    @pytest.mark.asyncio
    async def test_get_conference_attendance_report_empty(
        self, test_db, sample_conference
    ):
        """
        Test getting conference attendance report when no one has checked in.

        Expected: Returns empty list.
        """
        with patch('app.core.database.get_database', return_value=test_db):
            from app.services.session_attendance_service import SessionAttendanceService

            service = SessionAttendanceService()

            report = await service.get_conference_attendance_report(
                conference_id=str(sample_conference["_id"])
            )

            assert len(report) == 0

    @pytest.mark.asyncio
    async def test_get_conference_attendance_report_multiple_sessions(
        self, test_db, sample_conference, sample_session, sample_registration
    ):
        """
        Test attendance report with attendee checked into multiple sessions.

        Expected: Returns one report item with multiple sessions listed.
        """
        with patch('app.core.database.get_database', return_value=test_db):
            from app.services.session_attendance_service import SessionAttendanceService

            service = SessionAttendanceService()

            # Create second session
            session2_data = {
                "conference_id": sample_conference["_id"],
                "name": "Evening Service",
                "description": "Evening worship session",
                "location": "Main Auditorium",
                "day_number": 1,
                "day_label": "Day 1",
                "session_date": datetime(2025, 12, 25, 18, 0),
                "order": 2,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            result = await test_db.conference_sessions.insert_one(session2_data)
            session2_data["_id"] = result.inserted_id

            # Check into both sessions
            await service.check_in_by_code(
                registration_code=sample_registration["registration_code"],
                session_id=str(sample_session["_id"]),
                admin_id=None
            )
            await service.check_in_by_code(
                registration_code=sample_registration["registration_code"],
                session_id=str(session2_data["_id"]),
                admin_id=None
            )

            # Get the report
            report = await service.get_conference_attendance_report(
                conference_id=str(sample_conference["_id"])
            )

            assert len(report) == 1
            assert report[0]["total_sessions"] == 2
            assert len(report[0]["sessions_attended"]) == 2
            assert sample_session["name"] in report[0]["sessions_attended"]
            assert "Evening Service" in report[0]["sessions_attended"]

    @pytest.mark.asyncio
    async def test_get_conference_attendance_report_with_bus_route(
        self, test_db, sample_conference, sample_session, sample_bus_route
    ):
        """
        Test attendance report includes bus route information.

        Expected: Returns report with bus route name and pickup location.
        """
        with patch('app.core.database.get_database', return_value=test_db):
            from app.services.session_attendance_service import SessionAttendanceService

            service = SessionAttendanceService()

            # Create registration with bus route
            reg_data = {
                "conference_id": sample_conference["_id"],
                "user_name": "Bus Rider",
                "user_phone": "+233244999888",
                "user_email": "busrider@example.com",
                "registration_code": "REG-BUSTEST001",
                "status": "confirmed",
                "checked_in": False,
                "bus_route_id": sample_bus_route["_id"],
                "branch_id": "Tema",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            result = await test_db.conference_registrations.insert_one(reg_data)
            reg_data["_id"] = result.inserted_id

            # Check in
            await service.check_in_by_code(
                registration_code=reg_data["registration_code"],
                session_id=str(sample_session["_id"]),
                admin_id=None
            )

            # Get the report
            report = await service.get_conference_attendance_report(
                conference_id=str(sample_conference["_id"])
            )

            assert len(report) == 1
            assert report[0]["bus_route_name"] == sample_bus_route["route_name"]
            assert report[0]["bus_pickup_location"] == sample_bus_route["pickup_location"]
            assert report[0]["branch_name"] == "Tema"

    @pytest.mark.asyncio
    async def test_get_conference_attendance_report_with_branch_name_lookup(
        self, test_db, sample_conference, sample_session, sample_branch
    ):
        """
        Test attendance report looks up branch name from branches collection.

        Expected: Returns report with actual branch name (not ObjectId string).
        """
        with patch('app.core.database.get_database', return_value=test_db):
            from app.services.session_attendance_service import SessionAttendanceService

            service = SessionAttendanceService()

            # Create registration with branch_id (ObjectId)
            reg_data = {
                "conference_id": sample_conference["_id"],
                "user_name": "Branch Member",
                "user_phone": "+233244777666",
                "user_email": "branchmember@example.com",
                "registration_code": "REG-BRANCHTEST001",
                "status": "confirmed",
                "checked_in": False,
                "branch_id": sample_branch["_id"],  # ObjectId reference
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            result = await test_db.conference_registrations.insert_one(reg_data)
            reg_data["_id"] = result.inserted_id

            # Check in
            await service.check_in_by_code(
                registration_code=reg_data["registration_code"],
                session_id=str(sample_session["_id"]),
                admin_id=None
            )

            # Get the report
            report = await service.get_conference_attendance_report(
                conference_id=str(sample_conference["_id"])
            )

            assert len(report) == 1
            # Should display branch name, not ObjectId string
            assert report[0]["branch_name"] == "Adenta"
            assert report[0]["branch_name"] != str(sample_branch["_id"])

    @pytest.mark.asyncio
    async def test_get_conference_attendance_report_branch_fallback_to_church_name(
        self, test_db, sample_conference, sample_session
    ):
        """
        Test attendance report falls back to church_name when branch_id not found.

        Expected: Returns church_name when branch doesn't exist in database.
        """
        with patch('app.core.database.get_database', return_value=test_db):
            from app.services.session_attendance_service import SessionAttendanceService

            service = SessionAttendanceService()

            # Create registration with non-existent branch_id and church_name fallback
            fake_branch_id = ObjectId()  # Non-existent branch
            reg_data = {
                "conference_id": sample_conference["_id"],
                "user_name": "Non-Branch Member",
                "user_phone": "+233244555444",
                "user_email": "visitor@example.com",
                "registration_code": "REG-FALLBACKTEST001",
                "status": "confirmed",
                "checked_in": False,
                "branch_id": fake_branch_id,
                "church_name": "Independent Chapel",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            result = await test_db.conference_registrations.insert_one(reg_data)
            reg_data["_id"] = result.inserted_id

            # Check in
            await service.check_in_by_code(
                registration_code=reg_data["registration_code"],
                session_id=str(sample_session["_id"]),
                admin_id=None
            )

            # Get the report
            report = await service.get_conference_attendance_report(
                conference_id=str(sample_conference["_id"])
            )

            assert len(report) == 1
            # Should fallback to church_name since branch_id doesn't exist
            assert report[0]["branch_name"] == "Independent Chapel"


@pytest.mark.asyncio
class TestMemberSessionCheckIn:
    """Test cases for member self-service session check-in with GPS validation."""

    @pytest.mark.asyncio
    async def test_member_check_in_by_code_success(
        self, test_db, sample_conference_with_gps, sample_todays_session, sample_registration_for_gps_conf
    ):
        """
        Test successful member check-in with registration code and valid GPS.

        Expected: Creates attendance record with method="member_self_checkin".
        """
        with patch('app.core.database.get_database', return_value=test_db):
            from app.services.session_attendance_service import SessionAttendanceService

            service = SessionAttendanceService()

            # GPS coordinates within venue radius (Accra area)
            result = await service.member_check_in_by_code(
                registration_code=sample_registration_for_gps_conf["registration_code"],
                session_id=str(sample_todays_session["_id"]),
                latitude=5.6037,  # Same as venue
                longitude=-0.1870
            )

            assert result is not None
            assert result.session_id == sample_todays_session["_id"]
            assert result.registration_id == sample_registration_for_gps_conf["_id"]
            assert result.user_name == sample_registration_for_gps_conf["user_name"]
            assert result.check_in_method == "self_checkin"

            # Verify stored in database
            stored = await test_db.session_attendance.find_one({
                "session_id": sample_todays_session["_id"],
                "registration_id": sample_registration_for_gps_conf["_id"]
            })
            assert stored is not None

    @pytest.mark.asyncio
    async def test_member_check_in_by_code_gps_too_far(
        self, test_db, sample_conference_with_gps, sample_todays_session, sample_registration_for_gps_conf
    ):
        """
        Test member check-in fails when GPS is too far from venue.

        Expected: Raises PermissionError with "Too far from venue".
        """
        with patch('app.core.database.get_database', return_value=test_db):
            from app.services.session_attendance_service import SessionAttendanceService

            service = SessionAttendanceService()

            # GPS coordinates far from venue (Lagos, Nigeria)
            with pytest.raises(PermissionError) as exc_info:
                await service.member_check_in_by_code(
                    registration_code=sample_registration_for_gps_conf["registration_code"],
                    session_id=str(sample_todays_session["_id"]),
                    latitude=6.5244,  # Lagos coordinates
                    longitude=3.3792
                )

            assert "too far from the venue" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_member_check_in_by_code_invalid_code(
        self, test_db, sample_conference_with_gps, sample_todays_session
    ):
        """
        Test member check-in fails with non-existent registration code.

        Expected: Raises ValueError with "Registration not found".
        """
        with patch('app.core.database.get_database', return_value=test_db):
            from app.services.session_attendance_service import SessionAttendanceService

            service = SessionAttendanceService()

            with pytest.raises(ValueError) as exc_info:
                await service.member_check_in_by_code(
                    registration_code="REG-NONEXISTENT",
                    session_id=str(sample_todays_session["_id"]),
                    latitude=5.6037,
                    longitude=-0.1870
                )

            assert "Registration not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_member_check_in_duplicate_prevented(
        self, test_db, sample_conference_with_gps, sample_todays_session, sample_registration_for_gps_conf
    ):
        """
        Test duplicate member check-in to same session is prevented.

        Expected: First check-in succeeds, second raises Exception.
        """
        with patch('app.core.database.get_database', return_value=test_db):
            from app.services.session_attendance_service import SessionAttendanceService

            service = SessionAttendanceService()

            # First check-in should succeed
            await service.member_check_in_by_code(
                registration_code=sample_registration_for_gps_conf["registration_code"],
                session_id=str(sample_todays_session["_id"]),
                latitude=5.6037,
                longitude=-0.1870
            )

            # Second check-in should fail
            with pytest.raises(Exception) as exc_info:
                await service.member_check_in_by_code(
                    registration_code=sample_registration_for_gps_conf["registration_code"],
                    session_id=str(sample_todays_session["_id"]),
                    latitude=5.6037,
                    longitude=-0.1870
                )

            assert "Already checked in" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_member_check_in_by_phone_success(
        self, test_db, sample_conference_with_gps, sample_todays_session, sample_registration_for_gps_conf
    ):
        """
        Test successful member check-in with phone number and valid GPS.

        Expected: Creates attendance record with method="member_phone_checkin".
        """
        with patch('app.core.database.get_database', return_value=test_db):
            from app.services.session_attendance_service import SessionAttendanceService

            service = SessionAttendanceService()

            result = await service.member_check_in_by_phone(
                phone=sample_registration_for_gps_conf["user_phone"],
                session_id=str(sample_todays_session["_id"]),
                latitude=5.6037,
                longitude=-0.1870
            )

            assert result is not None
            assert result.session_id == sample_todays_session["_id"]
            assert result.user_phone == sample_registration_for_gps_conf["user_phone"]
            assert result.check_in_method == "self_checkin_phone"

    @pytest.mark.asyncio
    async def test_member_check_in_by_phone_gps_too_far(
        self, test_db, sample_conference_with_gps, sample_todays_session, sample_registration_for_gps_conf
    ):
        """
        Test member phone check-in fails when GPS is too far from venue.

        Expected: Raises PermissionError with "Too far from venue".
        """
        with patch('app.core.database.get_database', return_value=test_db):
            from app.services.session_attendance_service import SessionAttendanceService

            service = SessionAttendanceService()

            with pytest.raises(PermissionError) as exc_info:
                await service.member_check_in_by_phone(
                    phone=sample_registration_for_gps_conf["user_phone"],
                    session_id=str(sample_todays_session["_id"]),
                    latitude=6.5244,  # Lagos coordinates
                    longitude=3.3792
                )

            assert "too far from the venue" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_member_check_in_by_phone_not_found(
        self, test_db, sample_conference_with_gps, sample_todays_session
    ):
        """
        Test member phone check-in fails with non-existent phone.

        Expected: Raises ValueError with "No registration found".
        """
        with patch('app.core.database.get_database', return_value=test_db):
            from app.services.session_attendance_service import SessionAttendanceService

            service = SessionAttendanceService()

            with pytest.raises(ValueError) as exc_info:
                await service.member_check_in_by_phone(
                    phone="+233999888777",
                    session_id=str(sample_todays_session["_id"]),
                    latitude=5.6037,
                    longitude=-0.1870
                )

            assert "No registration found" in str(exc_info.value)


@pytest.mark.asyncio
class TestTodaysSessions:
    """Test cases for get_todays_sessions functionality."""

    @pytest.mark.asyncio
    async def test_get_todays_sessions_returns_today_only(
        self, test_db, sample_conference_with_gps, sample_todays_session, sample_registration_for_gps_conf
    ):
        """
        Test get_todays_sessions filters sessions by today's date.

        Expected: Returns only sessions scheduled for today.
        """
        with patch('app.core.database.get_database', return_value=test_db):
            from app.services.session_service import SessionService

            service = SessionService()

            # Add a session for tomorrow (should be excluded)
            from datetime import timedelta
            tomorrow = datetime.utcnow() + timedelta(days=1)
            tomorrow_session = {
                "conference_id": sample_conference_with_gps["_id"],
                "name": "Tomorrow's Session",
                "description": "Session scheduled for tomorrow",
                "location": "Room B",
                "day_number": 2,
                "day_label": "Day 2",
                "session_date": tomorrow,
                "order": 1,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            await test_db.conference_sessions.insert_one(tomorrow_session)

            # Get today's sessions
            sessions = await service.get_todays_sessions(
                conference_id=str(sample_conference_with_gps["_id"]),
                registration_id=str(sample_registration_for_gps_conf["_id"])
            )

            # Should only return today's session, not tomorrow's
            assert len(sessions) == 1
            assert sessions[0]["name"] == sample_todays_session["name"]
            assert sessions[0]["already_checked_in"] == False

    @pytest.mark.asyncio
    async def test_get_todays_sessions_shows_checkin_status(
        self, test_db, sample_conference_with_gps, sample_todays_session, sample_registration_for_gps_conf
    ):
        """
        Test get_todays_sessions shows correct check-in status.

        Expected: already_checked_in is True after check-in.
        """
        with patch('app.core.database.get_database', return_value=test_db):
            from app.services.session_service import SessionService
            from app.services.session_attendance_service import SessionAttendanceService

            session_service = SessionService()
            attendance_service = SessionAttendanceService()

            # Before check-in
            sessions_before = await session_service.get_todays_sessions(
                conference_id=str(sample_conference_with_gps["_id"]),
                registration_id=str(sample_registration_for_gps_conf["_id"])
            )
            assert sessions_before[0]["already_checked_in"] == False

            # Perform check-in
            await attendance_service.member_check_in_by_code(
                registration_code=sample_registration_for_gps_conf["registration_code"],
                session_id=str(sample_todays_session["_id"]),
                latitude=5.6037,
                longitude=-0.1870
            )

            # After check-in
            sessions_after = await session_service.get_todays_sessions(
                conference_id=str(sample_conference_with_gps["_id"]),
                registration_id=str(sample_registration_for_gps_conf["_id"])
            )
            assert sessions_after[0]["already_checked_in"] == True

    @pytest.mark.asyncio
    async def test_get_todays_sessions_empty_for_no_sessions(
        self, test_db, sample_conference_with_gps
    ):
        """
        Test get_todays_sessions returns empty list when no sessions today.

        Expected: Returns empty list.
        """
        with patch('app.core.database.get_database', return_value=test_db):
            from app.services.session_service import SessionService

            service = SessionService()

            # Delete the session to test empty case
            await test_db.conference_sessions.delete_many({
                "conference_id": sample_conference_with_gps["_id"]
            })

            sessions = await service.get_todays_sessions(
                conference_id=str(sample_conference_with_gps["_id"])
            )

            assert len(sessions) == 0


@pytest.mark.asyncio
class TestGPSValidation:
    """Test cases for GPS distance validation."""

    @pytest.mark.asyncio
    async def test_gps_within_radius_succeeds(
        self, test_db, sample_conference_with_gps, sample_todays_session, sample_registration_for_gps_conf
    ):
        """
        Test GPS check-in succeeds when within venue radius.

        Expected: Check-in succeeds for coordinates within 500m radius.
        """
        with patch('app.core.database.get_database', return_value=test_db):
            from app.services.session_attendance_service import SessionAttendanceService

            service = SessionAttendanceService()

            # Coordinates ~100m away from venue (within 500m radius)
            result = await service.member_check_in_by_code(
                registration_code=sample_registration_for_gps_conf["registration_code"],
                session_id=str(sample_todays_session["_id"]),
                latitude=5.6040,  # Slightly different
                longitude=-0.1865
            )

            assert result is not None

    @pytest.mark.asyncio
    async def test_gps_conference_without_venue_coords(
        self, test_db, sample_conference, sample_session, sample_registration
    ):
        """
        Test GPS check-in behavior when conference has no venue coordinates.

        Expected: Raises ValueError requiring venue coordinates to be configured.
        """
        with patch('app.core.database.get_database', return_value=test_db):
            from app.services.session_attendance_service import SessionAttendanceService

            # Update the conference dates to be ongoing
            from datetime import timedelta
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            await test_db.conferences.update_one(
                {"_id": sample_conference["_id"]},
                {"$set": {
                    "start_date": today,
                    "end_date": today + timedelta(days=2)
                }}
            )

            # Update session date to today
            await test_db.conference_sessions.update_one(
                {"_id": sample_session["_id"]},
                {"$set": {"session_date": datetime.utcnow()}}
            )

            service = SessionAttendanceService()

            # Should fail because venue GPS coordinates are not configured
            with pytest.raises(ValueError) as exc_info:
                await service.member_check_in_by_code(
                    registration_code=sample_registration["registration_code"],
                    session_id=str(sample_session["_id"]),
                    latitude=0.0,
                    longitude=0.0
                )

            assert "Venue GPS coordinates not configured" in str(exc_info.value)
