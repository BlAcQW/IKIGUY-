"""
Unit tests for ConferenceService.

Tests conference management and check-in functionality.
"""

import pytest
from datetime import datetime
from bson import ObjectId
from unittest.mock import patch

from app.services.conference_service import ConferenceService


@pytest.mark.asyncio
class TestConferenceService:
    """Test cases for ConferenceService."""

    async def test_create_conference_success(self, test_db):
        """
        Test successful conference creation.

        Expected: Conference created with all fields populated.
        """
        with patch('app.services.conference_service.get_database', return_value=test_db):
            service = ConferenceService()

            conf_data = {
                "name": "Impact 2025",
                "description": "Annual church conference",
                "start_date": datetime(2025, 12, 25),
                "end_date": datetime(2025, 12, 27),
                "venue": "National Theatre",
                "registration_open": True,
                "max_attendees": 500,
                "status": "upcoming"
            }

            result = await service.create_conference(conf_data)

            # Assertions
            assert result is not None
            assert result.name == "Impact 2025"
            assert result.max_attendees == 500
            assert result.current_attendees == 0
            assert result.created_at is not None

    async def test_create_conference_with_invalid_data(self, test_db):
        """
        Test conference creation with missing required fields.

        Expected: Exception raised for invalid data.
        """
        with patch('app.services.conference_service.get_database', return_value=test_db):
            service = ConferenceService()

            conf_data = {
                "name": "Test Conference"
                # Missing required fields
            }

            with pytest.raises(Exception):
                await service.create_conference(conf_data)

    async def test_get_conference_success(self, test_db, sample_conference):
        """
        Test retrieving conference by ID.

        Expected: Conference retrieved successfully.
        """
        with patch('app.services.conference_service.get_database', return_value=test_db):
            service = ConferenceService()

            result = await service.get_conference(str(sample_conference["_id"]))

            # Assertions
            assert result is not None
            assert result.name == sample_conference["name"]
            assert result.venue == sample_conference["venue"]

    async def test_get_conference_invalid_id(self, test_db):
        """
        Test retrieving conference with invalid ID.

        Expected: None returned.
        """
        with patch('app.services.conference_service.get_database', return_value=test_db):
            service = ConferenceService()

            result = await service.get_conference("invalid_id")

            # Assertions
            assert result is None

    async def test_get_conference_not_found(self, test_db):
        """
        Test retrieving non-existent conference.

        Expected: None returned.
        """
        with patch('app.services.conference_service.get_database', return_value=test_db):
            service = ConferenceService()

            result = await service.get_conference(str(ObjectId()))

            # Assertions
            assert result is None

    async def test_list_conferences_no_filters(self, test_db, sample_conference):
        """
        Test listing all conferences without filters.

        Expected: All conferences returned.
        """
        with patch('app.services.conference_service.get_database', return_value=test_db):
            service = ConferenceService()

            results = await service.list_conferences()

            # Assertions
            assert len(results) >= 1
            assert any(c.name == sample_conference["name"] for c in results)

    async def test_list_conferences_with_status_filter(self, test_db, sample_conference):
        """
        Test listing conferences filtered by status.

        Expected: Only conferences with specified status returned.
        """
        with patch('app.services.conference_service.get_database', return_value=test_db):
            service = ConferenceService()

            results = await service.list_conferences(status="upcoming")

            # Assertions
            assert len(results) >= 1
            assert all(c.status == "upcoming" for c in results)

    async def test_list_conferences_with_registration_filter(
        self, test_db, sample_conference
    ):
        """
        Test listing conferences filtered by registration status.

        Expected: Only conferences with matching registration status returned.
        """
        with patch('app.services.conference_service.get_database', return_value=test_db):
            service = ConferenceService()

            results = await service.list_conferences(registration_open=True)

            # Assertions
            assert len(results) >= 1
            assert all(c.registration_open is True for c in results)

    async def test_update_conference_success(self, test_db, sample_conference):
        """
        Test updating conference.

        Expected: Conference updated successfully.
        """
        with patch('app.services.conference_service.get_database', return_value=test_db):
            service = ConferenceService()

            update_data = {
                "status": "ongoing",
                "venue": "Updated Venue"
            }

            result = await service.update_conference(
                str(sample_conference["_id"]), update_data
            )

            # Assertions
            assert result is not None
            assert result.status == "ongoing"
            assert result.venue == "Updated Venue"
            assert result.updated_at is not None

    async def test_update_conference_invalid_id(self, test_db):
        """
        Test updating conference with invalid ID.

        Expected: None returned.
        """
        with patch('app.services.conference_service.get_database', return_value=test_db):
            service = ConferenceService()

            result = await service.update_conference("invalid_id", {"status": "ongoing"})

            # Assertions
            assert result is None

    async def test_delete_conference_success(self, test_db, sample_conference):
        """
        Test deleting conference.

        Expected: Conference and associated registrations deleted.
        """
        with patch('app.services.conference_service.get_database', return_value=test_db):
            service = ConferenceService()

            result = await service.delete_conference(str(sample_conference["_id"]))

            # Assertions
            assert result is True

            # Verify conference is deleted
            deleted_conf = await service.get_conference(str(sample_conference["_id"]))
            assert deleted_conf is None

    async def test_delete_conference_invalid_id(self, test_db):
        """
        Test deleting conference with invalid ID.

        Expected: False returned.
        """
        with patch('app.services.conference_service.get_database', return_value=test_db):
            service = ConferenceService()

            result = await service.delete_conference("invalid_id")

            # Assertions
            assert result is False

    async def test_register_for_conference_success(
        self, test_db, sample_user, sample_conference
    ):
        """
        Test successful conference registration.

        Expected: User registered with QR code generated.
        """
        with patch('app.services.conference_service.get_database', return_value=test_db):
            service = ConferenceService()

            result = await service.register_for_conference(
                user_id=str(sample_user["_id"]),
                conference_id=str(sample_conference["_id"])
            )

            # Assertions
            assert result is not None
            assert result.user_id == sample_user["_id"]
            assert result.conference_id == sample_conference["_id"]
            assert result.qr_code is not None
            assert len(result.qr_code) == 32
            assert result.status == "confirmed"
            assert result.checked_in is False

            # Verify attendee count updated
            updated_conf = await service.get_conference(str(sample_conference["_id"]))
            assert updated_conf.current_attendees == 1

    async def test_register_for_conference_not_found(self, test_db, sample_user):
        """
        Test registering for non-existent conference.

        Expected: Exception raised.
        """
        with patch('app.services.conference_service.get_database', return_value=test_db):
            service = ConferenceService()

            with pytest.raises(Exception, match="Conference not found"):
                await service.register_for_conference(
                    user_id=str(sample_user["_id"]),
                    conference_id=str(ObjectId())
                )

    async def test_register_for_conference_closed(
        self, test_db, sample_user, sample_conference
    ):
        """
        Test registering for closed conference.

        Expected: Exception raised.
        """
        with patch('app.services.conference_service.get_database', return_value=test_db):
            service = ConferenceService()

            # Close registration
            await test_db.conferences.update_one(
                {"_id": sample_conference["_id"]},
                {"$set": {"registration_open": False}}
            )

            with pytest.raises(Exception, match="Registration is closed"):
                await service.register_for_conference(
                    user_id=str(sample_user["_id"]),
                    conference_id=str(sample_conference["_id"])
                )

    async def test_register_for_conference_full(
        self, test_db, sample_user, sample_conference
    ):
        """
        Test registering for full conference.

        Expected: Exception raised.
        """
        with patch('app.services.conference_service.get_database', return_value=test_db):
            service = ConferenceService()

            # Make conference full
            await test_db.conferences.update_one(
                {"_id": sample_conference["_id"]},
                {"$set": {"current_attendees": sample_conference["max_attendees"]}}
            )

            with pytest.raises(Exception, match="Conference is full"):
                await service.register_for_conference(
                    user_id=str(sample_user["_id"]),
                    conference_id=str(sample_conference["_id"])
                )

    async def test_register_for_conference_duplicate(
        self, test_db, sample_user, sample_conference
    ):
        """
        Test duplicate registration for same conference.

        Expected: Exception raised.
        """
        with patch('app.services.conference_service.get_database', return_value=test_db):
            service = ConferenceService()

            # First registration
            await service.register_for_conference(
                user_id=str(sample_user["_id"]),
                conference_id=str(sample_conference["_id"])
            )

            # Second registration attempt
            with pytest.raises(Exception, match="User already registered for this conference"):
                await service.register_for_conference(
                    user_id=str(sample_user["_id"]),
                    conference_id=str(sample_conference["_id"])
                )

    async def test_check_in_user_success(
        self, test_db, sample_user, sample_conference
    ):
        """
        Test successful user check-in.

        Expected: User checked in successfully.
        """
        with patch('app.services.conference_service.get_database', return_value=test_db):
            service = ConferenceService()

            # Register user first
            registration = await service.register_for_conference(
                user_id=str(sample_user["_id"]),
                conference_id=str(sample_conference["_id"])
            )

            # Check in
            result = await service.check_in_user(registration.qr_code)

            # Assertions
            assert result["success"] is True
            assert result["user_name"] == sample_user["name"]
            assert result["user_phone"] == sample_user["phone"]
            assert result["conference_name"] == sample_conference["name"]
            assert result["check_in_time"] is not None

            # Verify registration updated
            reg_doc = await test_db.conference_registrations.find_one(
                {"qr_code": registration.qr_code}
            )
            assert reg_doc["checked_in"] is True
            assert reg_doc["check_in_time"] is not None

    async def test_check_in_user_invalid_qr(self, test_db):
        """
        Test check-in with invalid QR code.

        Expected: Exception raised.
        """
        with patch('app.services.conference_service.get_database', return_value=test_db):
            service = ConferenceService()

            with pytest.raises(Exception, match="Invalid QR code"):
                await service.check_in_user("invalid_qr_code")

    async def test_check_in_user_already_checked_in(
        self, test_db, sample_user, sample_conference
    ):
        """
        Test check-in for already checked-in user.

        Expected: Exception raised.
        """
        with patch('app.services.conference_service.get_database', return_value=test_db):
            service = ConferenceService()

            # Register and check in first time
            registration = await service.register_for_conference(
                user_id=str(sample_user["_id"]),
                conference_id=str(sample_conference["_id"])
            )
            await service.check_in_user(registration.qr_code)

            # Try to check in again
            with pytest.raises(Exception, match="User already checked in"):
                await service.check_in_user(registration.qr_code)

    async def test_generate_qr_code_uniqueness(self, test_db):
        """
        Test QR code generation produces unique codes.

        Expected: Each registration gets unique QR code.
        """
        with patch('app.services.conference_service.get_database', return_value=test_db):
            service = ConferenceService()

            # Generate multiple QR codes
            qr_codes = set()
            user_id = str(ObjectId())
            conf_id = str(ObjectId())

            for _ in range(10):
                qr_code = service._generate_qr_code(user_id, conf_id)
                qr_codes.add(qr_code)

            # All should be unique
            assert len(qr_codes) == 10

    async def test_generate_qr_code_length(self, test_db):
        """
        Test QR code has correct length.

        Expected: QR code is 32 characters.
        """
        with patch('app.services.conference_service.get_database', return_value=test_db):
            service = ConferenceService()

            qr_code = service._generate_qr_code(str(ObjectId()), str(ObjectId()))

            # Should be 32 characters (SHA256 truncated)
            assert len(qr_code) == 32
