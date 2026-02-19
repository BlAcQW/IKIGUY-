"""
Unit tests for phone-based registration lookup endpoint.
"""

import pytest
from datetime import datetime
from bson import ObjectId
from unittest.mock import Mock, patch

from app.utils.phone import normalize_phone_number


@pytest.fixture(scope="function")
async def sample_registration(test_db, sample_conference):
    """
    Create sample registration for testing.

    Args:
        test_db: Test database fixture
        sample_conference: Conference fixture

    Returns:
        Registration document with _id
    """
    reg_data = {
        "conference_id": sample_conference["_id"],
        "user_phone": "+233244123456",
        "user_name": "Test User",
        "user_email": "test@example.com",
        "branch_id": None,
        "church_name": "Test Church",
        "registration_code": "REG-TEST123",
        "requires_bus": False,
        "bus_route_id": None,
        "special_needs": None,
        "emergency_contact": None,
        "checked_in": False,
        "checked_in_at": None,
        "status": "confirmed",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    result = await test_db.conference_registrations.insert_one(reg_data)
    reg_data["_id"] = result.inserted_id
    return reg_data


@pytest.fixture
async def multiple_registrations(test_db, sample_conference):
    """
    Create multiple registrations with same phone for testing.

    Args:
        test_db: Test database fixture
        sample_conference: Conference fixture

    Returns:
        List of registration documents
    """
    # Create another conference
    conf2_data = {
        "name": "Another Conference 2025",
        "description": "Another test conference",
        "start_date": datetime(2025, 11, 20),
        "end_date": datetime(2025, 11, 22),
        "venue": "Another Venue",
        "registration_open": True,
        "max_attendees": 100,
        "current_attendees": 0,
        "status": "upcoming",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    conf2_result = await test_db.conferences.insert_one(conf2_data)
    conf2_data["_id"] = conf2_result.inserted_id

    # Create registrations with same phone
    registrations = []
    for i, conf_id in enumerate([sample_conference["_id"], conf2_data["_id"]]):
        reg_data = {
            "conference_id": conf_id,
            "user_phone": "+233244999888",
            "user_name": "Multi Reg User",
            "user_email": "multireg@example.com",
            "branch_id": None,
            "church_name": "Multi Church",
            "registration_code": f"REG-MULTI{i}",
            "requires_bus": False,
            "bus_route_id": None,
            "special_needs": None,
            "emergency_contact": None,
            "checked_in": False,
            "checked_in_at": None,
            "status": "confirmed",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        result = await test_db.conference_registrations.insert_one(reg_data)
        reg_data["_id"] = result.inserted_id
        registrations.append(reg_data)

    return registrations


class TestPhoneLookupEndpoint:
    """Test cases for phone lookup endpoint."""

    @pytest.mark.asyncio
    async def test_normalize_phone_lookup(self, test_db, sample_registration):
        """Test that phone lookup uses normalization correctly."""
        # Test with different formats
        phone_formats = [
            "+233244123456",
            "0244123456",
            "244123456"
        ]

        for phone in phone_formats:
            normalized = normalize_phone_number(phone)
            query = {
                "user_phone": {"$in": normalized},
                "status": "confirmed"
            }
            result = await test_db.conference_registrations.find_one(query)
            assert result is not None, f"Should find registration with phone format: {phone}"
            assert result["user_phone"] == "+233244123456"

    @pytest.mark.asyncio
    async def test_find_single_registration(self, test_db, sample_registration):
        """Test finding a single registration by phone."""
        normalized = normalize_phone_number("+233244123456")
        query = {
            "user_phone": {"$in": normalized},
            "status": "confirmed"
        }
        results = await test_db.conference_registrations.find(query).to_list(length=100)
        assert len(results) == 1
        assert results[0]["user_phone"] == "+233244123456"
        assert results[0]["user_name"] == "Test User"

    @pytest.mark.asyncio
    async def test_find_multiple_registrations(self, test_db, multiple_registrations):
        """Test finding multiple registrations with same phone."""
        normalized = normalize_phone_number("+233244999888")
        query = {
            "user_phone": {"$in": normalized},
            "status": "confirmed"
        }
        results = await test_db.conference_registrations.find(query).to_list(length=100)
        assert len(results) == 2
        assert all(r["user_phone"] == "+233244999888" for r in results)

    @pytest.mark.asyncio
    async def test_filter_by_conference(self, test_db, multiple_registrations, sample_conference):
        """Test filtering results by conference ID."""
        normalized = normalize_phone_number("+233244999888")
        query = {
            "user_phone": {"$in": normalized},
            "status": "confirmed",
            "conference_id": sample_conference["_id"]
        }
        results = await test_db.conference_registrations.find(query).to_list(length=100)
        assert len(results) == 1
        assert results[0]["conference_id"] == sample_conference["_id"]

    @pytest.mark.asyncio
    async def test_no_results_for_unknown_phone(self, test_db):
        """Test that unknown phone returns no results."""
        normalized = normalize_phone_number("+233000000000")
        query = {
            "user_phone": {"$in": normalized},
            "status": "confirmed"
        }
        results = await test_db.conference_registrations.find(query).to_list(length=100)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_exclude_cancelled_registrations(self, test_db, sample_registration):
        """Test that cancelled registrations are excluded."""
        # Update registration to cancelled
        await test_db.conference_registrations.update_one(
            {"_id": sample_registration["_id"]},
            {"$set": {"status": "cancelled"}}
        )

        normalized = normalize_phone_number("+233244123456")
        query = {
            "user_phone": {"$in": normalized},
            "status": "confirmed"
        }
        results = await test_db.conference_registrations.find(query).to_list(length=100)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_phone_with_spaces_lookup(self, test_db, sample_registration):
        """Test phone lookup with spaces in input."""
        normalized = normalize_phone_number("+233 244 123 456")
        query = {
            "user_phone": {"$in": normalized},
            "status": "confirmed"
        }
        result = await test_db.conference_registrations.find_one(query)
        assert result is not None
        assert result["user_phone"] == "+233244123456"

    @pytest.mark.asyncio
    async def test_phone_with_dashes_lookup(self, test_db, sample_registration):
        """Test phone lookup with dashes in input."""
        normalized = normalize_phone_number("+233-244-123-456")
        query = {
            "user_phone": {"$in": normalized},
            "status": "confirmed"
        }
        result = await test_db.conference_registrations.find_one(query)
        assert result is not None
        assert result["user_phone"] == "+233244123456"

    @pytest.mark.asyncio
    async def test_national_format_lookup(self, test_db, sample_registration):
        """Test lookup with national format (0244...)."""
        normalized = normalize_phone_number("0244123456")
        query = {
            "user_phone": {"$in": normalized},
            "status": "confirmed"
        }
        result = await test_db.conference_registrations.find_one(query)
        assert result is not None
        assert result["user_phone"] == "+233244123456"

    @pytest.mark.asyncio
    async def test_local_format_lookup(self, test_db, sample_registration):
        """Test lookup with local format (244...)."""
        normalized = normalize_phone_number("244123456")
        query = {
            "user_phone": {"$in": normalized},
            "status": "confirmed"
        }
        result = await test_db.conference_registrations.find_one(query)
        assert result is not None
        assert result["user_phone"] == "+233244123456"


class TestPhoneLookupValidation:
    """Test cases for phone lookup validation logic."""

    def test_invalid_phone_formats(self):
        """Test that invalid phone formats are handled correctly."""
        from app.utils.phone import validate_phone_number

        # Should be invalid
        assert validate_phone_number("123") is False
        assert validate_phone_number("abc") is False
        assert validate_phone_number("") is False
        assert validate_phone_number(None) is False

    def test_valid_phone_formats(self):
        """Test that valid phone formats pass validation."""
        from app.utils.phone import validate_phone_number

        # Should be valid
        assert validate_phone_number("+233244123456") is True
        assert validate_phone_number("0244123456") is True
        assert validate_phone_number("244123456") is True
        assert validate_phone_number("+233 244 123 456") is True
