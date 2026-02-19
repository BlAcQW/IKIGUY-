"""
Unit tests for registration update functionality.

Tests CRUD operations for updating registration details including
name, phone, email, church_name, and special_needs fields with real data.
"""

import pytest
from datetime import datetime
from bson import ObjectId
from unittest.mock import patch

# Import service at module level (not inside patch context)
from app.services.registration_service import RegistrationService


@pytest.mark.asyncio
class TestRegistrationUpdatesCRUD:
    """Test cases for registration updates CRUD operations with real data."""

    @pytest.mark.asyncio
    async def test_update_registration_name(
        self, test_db, sample_conference, sample_registration
    ):
        """
        Test updating registration user_name field.

        Expected: Name is updated successfully and persisted to database.
        """
        with patch('app.services.registration_service.get_database', return_value=test_db):

            service = RegistrationService()

            # Update name
            update_data = {
                "user_name": "Updated Test Name"
            }

            updated = await service.update_registration(
                registration_id=str(sample_registration["_id"]),
                update_data=update_data
            )

            # Verify update
            assert updated is not None
            assert updated["user_name"] == "Updated Test Name"
            # Other fields should remain unchanged
            assert updated["user_phone"] == sample_registration["user_phone"]
            assert updated["user_email"] == sample_registration["user_email"]

            # Verify in database
            stored = await test_db.conference_registrations.find_one(
                {"_id": sample_registration["_id"]}
            )
            assert stored["user_name"] == "Updated Test Name"

    @pytest.mark.asyncio
    async def test_update_registration_phone(
        self, test_db, sample_conference, sample_registration
    ):
        """
        Test updating registration user_phone field with validation.

        Expected: Phone is validated, normalized, and updated.
        """
        with patch('app.services.registration_service.get_database', return_value=test_db):

            service = RegistrationService()

            # Update with local format phone
            update_data = {
                "user_phone": "0201234567"  # Local format
            }

            updated = await service.update_registration(
                registration_id=str(sample_registration["_id"]),
                update_data=update_data
            )

            # Verify phone is normalized to international format
            assert updated is not None
            assert updated["user_phone"] == "+233201234567"  # Normalized

            # Verify in database
            stored = await test_db.conference_registrations.find_one(
                {"_id": sample_registration["_id"]}
            )
            assert stored["user_phone"] == "+233201234567"

    @pytest.mark.asyncio
    async def test_update_registration_phone_validation_fails(
        self, test_db, sample_conference, sample_registration
    ):
        """
        Test updating registration with invalid phone format.

        Expected: Raises exception with validation error.
        """
        with patch('app.services.registration_service.get_database', return_value=test_db):

            service = RegistrationService()

            # Update with invalid phone
            update_data = {
                "user_phone": "invalid"
            }

            # Should raise validation error
            with pytest.raises(Exception) as exc_info:
                await service.update_registration(
                    registration_id=str(sample_registration["_id"]),
                    update_data=update_data
                )

            assert "Invalid" in str(exc_info.value) or "phone" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_update_registration_email(
        self, test_db, sample_conference, sample_registration
    ):
        """
        Test updating registration user_email field.

        Expected: Email is updated successfully.
        """
        with patch('app.services.registration_service.get_database', return_value=test_db):

            service = RegistrationService()

            # Update email
            update_data = {
                "user_email": "newemail@example.com"
            }

            updated = await service.update_registration(
                registration_id=str(sample_registration["_id"]),
                update_data=update_data
            )

            # Verify update
            assert updated is not None
            assert updated["user_email"] == "newemail@example.com"

            # Verify in database
            stored = await test_db.conference_registrations.find_one(
                {"_id": sample_registration["_id"]}
            )
            assert stored["user_email"] == "newemail@example.com"

    @pytest.mark.asyncio
    async def test_update_registration_church_name(
        self, test_db, sample_conference, sample_registration
    ):
        """
        Test updating registration church_name field.

        Expected: Church name is updated successfully.
        """
        with patch('app.services.registration_service.get_database', return_value=test_db):

            service = RegistrationService()

            # Update church name
            update_data = {
                "church_name": "New Hope Chapel"
            }

            updated = await service.update_registration(
                registration_id=str(sample_registration["_id"]),
                update_data=update_data
            )

            # Verify update
            assert updated is not None
            assert updated.get("church_name") == "New Hope Chapel"

            # Verify in database
            stored = await test_db.conference_registrations.find_one(
                {"_id": sample_registration["_id"]}
            )
            assert stored.get("church_name") == "New Hope Chapel"

    @pytest.mark.asyncio
    async def test_update_registration_special_needs(
        self, test_db, sample_conference, sample_registration
    ):
        """
        Test updating registration special_needs field.

        Expected: Special needs is updated successfully.
        """
        with patch('app.services.registration_service.get_database', return_value=test_db):

            service = RegistrationService()

            # Update special needs
            update_data = {
                "special_needs": "Wheelchair access required"
            }

            updated = await service.update_registration(
                registration_id=str(sample_registration["_id"]),
                update_data=update_data
            )

            # Verify update
            assert updated is not None
            assert updated.get("special_needs") == "Wheelchair access required"

            # Verify in database
            stored = await test_db.conference_registrations.find_one(
                {"_id": sample_registration["_id"]}
            )
            assert stored.get("special_needs") == "Wheelchair access required"

    @pytest.mark.asyncio
    async def test_update_registration_multiple_fields(
        self, test_db, sample_conference, sample_registration
    ):
        """
        Test updating multiple registration fields at once.

        Expected: All fields are updated successfully in single operation.
        """
        with patch('app.services.registration_service.get_database', return_value=test_db):

            service = RegistrationService()

            # Update multiple fields
            update_data = {
                "user_name": "John Smith Updated",
                "user_phone": "0244555666",  # Local format
                "user_email": "johnsmith@newdomain.com",
                "church_name": "Victory Chapel",
                "special_needs": "Dietary restrictions: Vegetarian"
            }

            updated = await service.update_registration(
                registration_id=str(sample_registration["_id"]),
                update_data=update_data
            )

            # Verify all updates
            assert updated is not None
            assert updated["user_name"] == "John Smith Updated"
            assert updated["user_phone"] == "+233244555666"  # Normalized
            assert updated["user_email"] == "johnsmith@newdomain.com"
            assert updated.get("church_name") == "Victory Chapel"
            assert updated.get("special_needs") == "Dietary restrictions: Vegetarian"

            # Verify in database
            stored = await test_db.conference_registrations.find_one(
                {"_id": sample_registration["_id"]}
            )
            assert stored["user_name"] == "John Smith Updated"
            assert stored["user_phone"] == "+233244555666"
            assert stored["user_email"] == "johnsmith@newdomain.com"
            assert stored.get("church_name") == "Victory Chapel"
            assert stored.get("special_needs") == "Dietary restrictions: Vegetarian"

    @pytest.mark.asyncio
    async def test_update_registration_preserves_other_fields(
        self, test_db, sample_conference
    ):
        """
        Test that updating specific fields doesn't affect other fields.

        Expected: Only updated fields change, others remain intact.
        """
        with patch('app.services.registration_service.get_database', return_value=test_db):

            service = RegistrationService()

            # Create registration with full data
            reg_data = {
                "conference_id": sample_conference["_id"],
                "user_name": "Original Name",
                "user_phone": "+233200111222",
                "user_email": "original@example.com",
                "church_name": "Original Church",
                "special_needs": "Original needs",
                "registration_code": "REG-PRESERVE123",
                "status": "confirmed",
                "checked_in": False,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            result = await test_db.conference_registrations.insert_one(reg_data)
            reg_id = result.inserted_id

            # Update only name
            update_data = {
                "user_name": "New Name Only"
            }

            updated = await service.update_registration(
                registration_id=str(reg_id),
                update_data=update_data
            )

            # Verify only name changed
            assert updated["user_name"] == "New Name Only"
            assert updated["user_phone"] == "+233200111222"  # Unchanged
            assert updated["user_email"] == "original@example.com"  # Unchanged
            assert updated.get("church_name") == "Original Church"  # Unchanged
            assert updated.get("special_needs") == "Original needs"  # Unchanged

    @pytest.mark.asyncio
    async def test_update_registration_not_found(
        self, test_db, sample_conference
    ):
        """
        Test updating non-existent registration.

        Expected: Returns None or raises exception.
        """
        with patch('app.services.registration_service.get_database', return_value=test_db):

            service = RegistrationService()

            # Try to update non-existent registration
            fake_id = str(ObjectId())
            update_data = {
                "user_name": "Should Not Work"
            }

            updated = await service.update_registration(
                registration_id=fake_id,
                update_data=update_data
            )

            # Should return None for not found
            assert updated is None

    @pytest.mark.asyncio
    async def test_update_registration_clears_optional_field(
        self, test_db, sample_conference
    ):
        """
        Test clearing optional fields by setting to None or empty string.

        Expected: Optional fields can be cleared.
        """
        with patch('app.services.registration_service.get_database', return_value=test_db):

            service = RegistrationService()

            # Create registration with optional fields
            reg_data = {
                "conference_id": sample_conference["_id"],
                "user_name": "Test User",
                "user_phone": "+233200333444",
                "user_email": "test@example.com",
                "church_name": "Some Church",
                "special_needs": "Some needs",
                "registration_code": "REG-CLEAR123",
                "status": "confirmed",
                "checked_in": False,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            result = await test_db.conference_registrations.insert_one(reg_data)
            reg_id = result.inserted_id

            # Clear optional fields
            update_data = {
                "special_needs": None,
                "church_name": None
            }

            updated = await service.update_registration(
                registration_id=str(reg_id),
                update_data=update_data
            )

            # Verify fields are cleared
            assert updated.get("special_needs") is None
            assert updated.get("church_name") is None
            # Required fields still present
            assert updated["user_name"] == "Test User"
            assert updated["user_phone"] == "+233200333444"

    @pytest.mark.asyncio
    async def test_update_registration_updated_at_timestamp(
        self, test_db, sample_conference, sample_registration
    ):
        """
        Test that updated_at timestamp is updated on modification.

        Expected: updated_at field reflects the update time.
        """
        with patch('app.services.registration_service.get_database', return_value=test_db):
            import time

            service = RegistrationService()

            # Get original updated_at
            original = await test_db.conference_registrations.find_one(
                {"_id": sample_registration["_id"]}
            )
            original_updated_at = original.get("updated_at")

            # Wait a moment to ensure timestamp difference
            time.sleep(0.1)

            # Update registration
            update_data = {
                "user_name": "Timestamp Test"
            }

            updated = await service.update_registration(
                registration_id=str(sample_registration["_id"]),
                update_data=update_data
            )

            # Verify updated_at changed
            new_updated_at = updated.get("updated_at")
            if original_updated_at and new_updated_at:
                assert new_updated_at > original_updated_at

    @pytest.mark.asyncio
    async def test_get_registration_after_update(
        self, test_db, sample_conference, sample_registration
    ):
        """
        Test retrieving registration after update returns updated data.

        Expected: GET returns the updated values.
        """
        with patch('app.services.registration_service.get_database', return_value=test_db):

            service = RegistrationService()

            # Update registration
            update_data = {
                "user_name": "Retrieval Test Name",
                "user_email": "retrievaltest@example.com"
            }

            await service.update_registration(
                registration_id=str(sample_registration["_id"]),
                update_data=update_data
            )

            # Retrieve registration
            retrieved = await service.get_registration(
                registration_id=str(sample_registration["_id"])
            )

            # Verify retrieved data matches update
            assert retrieved is not None
            assert retrieved["user_name"] == "Retrieval Test Name"
            assert retrieved["user_email"] == "retrievaltest@example.com"
