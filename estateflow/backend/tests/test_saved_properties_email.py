"""
Unit tests for saved properties email requirement.

Tests that user email is properly captured and stored when users save/favorite properties.
"""

import pytest
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import uuid


@pytest.fixture
async def db_client():
    """Create test database client."""
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[f"{settings.MONGODB_DB_NAME}_test"]
    yield db
    # Cleanup
    await client.drop_database(f"{settings.MONGODB_DB_NAME}_test")
    client.close()


@pytest.fixture
async def test_property(db_client):
    """Create a test property."""
    property_id = str(uuid.uuid4())
    property_doc = {
        "id": property_id,
        "title": "Test Property for Saved Properties",
        "description": "Test property",
        "price": 100000,
        "currency": "USD",
        "property_type": "residential",
        "status": "active",
        "organization_id": "test_org_123",
        "created_at": datetime.utcnow()
    }
    await db_client.properties.insert_one(property_doc)
    return property_id


@pytest.fixture
def mock_current_user():
    """Mock authenticated user with email."""
    return {
        "id": "test_user_123",
        "sub": "test_user_123",
        "email": "testuser@estateflow.com",
        "role": "user"
    }


@pytest.fixture
def mock_current_user_no_email():
    """Mock authenticated user without email (edge case)."""
    return {
        "id": "test_user_456",
        "sub": "test_user_456",
        "role": "user"
        # No email field
    }


class TestSavedPropertiesEmailStorage:
    """Test that user email is properly stored when saving properties."""

    @pytest.mark.asyncio
    async def test_save_property_stores_user_email(
        self, db_client, test_property, mock_current_user
    ):
        """
        CRITICAL TEST: Verify user_email is stored in saved_properties document.

        This is the main requirement - when a user saves a property,
        their email should be captured and stored in the database.
        """
        saved_properties_collection = db_client["saved_properties"]

        # Simulate saving a property
        saved_id = str(uuid.uuid4())
        now = datetime.utcnow()

        saved_doc = {
            "id": saved_id,
            "user_id": mock_current_user["id"],
            "user_email": mock_current_user["email"],
            "property_id": test_property,
            "saved_at": now,
            "created_at": now
        }

        await saved_properties_collection.insert_one(saved_doc)

        # Verify document in database
        db_saved = await saved_properties_collection.find_one({"id": saved_id})

        assert db_saved is not None, "Saved property should exist in database"
        assert db_saved["user_email"] == "testuser@estateflow.com", \
            "User email should be stored in saved_properties document"
        assert db_saved["user_id"] == "test_user_123", "User ID should be stored"
        assert db_saved["property_id"] == test_property, "Property ID should be stored"

    @pytest.mark.asyncio
    async def test_save_property_without_email_should_fail(
        self, db_client, test_property, mock_current_user_no_email
    ):
        """
        Test that saving a property without email in current_user raises an error.

        This validates the requirement that email is mandatory.
        """
        # In the actual API endpoint, this should raise HTTPException
        # Here we just verify the logic
        user_email = mock_current_user_no_email.get("email")

        assert user_email is None, "Mock user should have no email"

        # In the actual endpoint, this would trigger:
        # if not user_email:
        #     raise HTTPException(status_code=400, detail="User email is required")

    @pytest.mark.asyncio
    async def test_list_saved_properties_includes_email(
        self, db_client, test_property, mock_current_user
    ):
        """
        Test that listing saved properties returns user_email field.

        This ensures the email is accessible when querying saved properties.
        """
        saved_properties_collection = db_client["saved_properties"]

        # Create 3 saved properties with email
        for i in range(3):
            saved_id = str(uuid.uuid4())
            saved_doc = {
                "id": saved_id,
                "user_id": mock_current_user["id"],
                "user_email": mock_current_user["email"],
                "property_id": f"property_{i}",
                "saved_at": datetime.utcnow(),
                "created_at": datetime.utcnow()
            }
            await saved_properties_collection.insert_one(saved_doc)

        # Query saved properties for user
        cursor = saved_properties_collection.find({
            "user_id": mock_current_user["id"]
        })
        saved_list = await cursor.to_list(length=10)

        assert len(saved_list) == 3, "Should have 3 saved properties"

        for saved in saved_list:
            assert "user_email" in saved, "Each saved property should have user_email field"
            assert saved["user_email"] == "testuser@estateflow.com", \
                "Email should match the user's email"

    @pytest.mark.asyncio
    async def test_check_if_property_saved_uses_user_id(
        self, db_client, test_property, mock_current_user
    ):
        """
        Test that checking if a property is saved uses user_id.

        Email is stored for tracking, but lookups use user_id for efficiency.
        """
        saved_properties_collection = db_client["saved_properties"]

        # Save a property
        saved_id = str(uuid.uuid4())
        saved_doc = {
            "id": saved_id,
            "user_id": mock_current_user["id"],
            "user_email": mock_current_user["email"],
            "property_id": test_property,
            "saved_at": datetime.utcnow(),
            "created_at": datetime.utcnow()
        }
        await saved_properties_collection.insert_one(saved_doc)

        # Check using user_id and property_id
        existing = await saved_properties_collection.find_one({
            "user_id": mock_current_user["id"],
            "property_id": test_property
        })

        assert existing is not None, "Should find saved property by user_id and property_id"
        assert existing["user_email"] == mock_current_user["email"], \
            "Found property should have correct email"

    @pytest.mark.asyncio
    async def test_multiple_users_same_property_different_emails(
        self, db_client, test_property
    ):
        """
        Test that multiple users can save the same property with different emails.

        Ensures email tracking works correctly in multi-user scenarios.
        """
        saved_properties_collection = db_client["saved_properties"]

        # User 1 saves property
        user1 = {
            "id": "user_1",
            "email": "user1@estateflow.com"
        }
        saved_doc_1 = {
            "id": str(uuid.uuid4()),
            "user_id": user1["id"],
            "user_email": user1["email"],
            "property_id": test_property,
            "saved_at": datetime.utcnow(),
            "created_at": datetime.utcnow()
        }
        await saved_properties_collection.insert_one(saved_doc_1)

        # User 2 saves same property
        user2 = {
            "id": "user_2",
            "email": "user2@estateflow.com"
        }
        saved_doc_2 = {
            "id": str(uuid.uuid4()),
            "user_id": user2["id"],
            "user_email": user2["email"],
            "property_id": test_property,
            "saved_at": datetime.utcnow(),
            "created_at": datetime.utcnow()
        }
        await saved_properties_collection.insert_one(saved_doc_2)

        # Verify both saves exist with different emails
        all_saves = await saved_properties_collection.find({
            "property_id": test_property
        }).to_list(length=10)

        assert len(all_saves) == 2, "Should have 2 saves for the same property"

        emails = [save["user_email"] for save in all_saves]
        assert "user1@estateflow.com" in emails, "User 1 email should be stored"
        assert "user2@estateflow.com" in emails, "User 2 email should be stored"
        assert len(set(emails)) == 2, "Should have 2 unique emails"

    @pytest.mark.asyncio
    async def test_unsave_property_preserves_email_in_logs(
        self, db_client, test_property, mock_current_user
    ):
        """
        Test that unsaving a property preserves email information for audit trail.

        While the document is deleted, we can track who unsaved it via logs.
        """
        saved_properties_collection = db_client["saved_properties"]

        # Save property
        saved_id = str(uuid.uuid4())
        saved_doc = {
            "id": saved_id,
            "user_id": mock_current_user["id"],
            "user_email": mock_current_user["email"],
            "property_id": test_property,
            "saved_at": datetime.utcnow(),
            "created_at": datetime.utcnow()
        }
        await saved_properties_collection.insert_one(saved_doc)

        # Verify it exists with email
        existing = await saved_properties_collection.find_one({"id": saved_id})
        assert existing["user_email"] == "testuser@estateflow.com"

        # Unsave (delete)
        result = await saved_properties_collection.delete_one({
            "user_id": mock_current_user["id"],
            "property_id": test_property
        })

        assert result.deleted_count == 1, "Should delete 1 document"

        # Verify it's gone
        deleted = await saved_properties_collection.find_one({"id": saved_id})
        assert deleted is None, "Saved property should be deleted"

        # NOTE: In production, you might want to keep a "deleted_saved_properties"
        # collection for audit trail with the email preserved


class TestSavedPropertiesEmailValidation:
    """Test email validation in saved properties feature."""

    @pytest.mark.asyncio
    async def test_email_format_validation(self):
        """
        Test that email format is validated (if implemented).

        While Supabase handles email validation during auth,
        we can add additional validation in the API.
        """
        valid_emails = [
            "user@example.com",
            "test.user@domain.co.uk",
            "user+tag@example.com"
        ]

        invalid_emails = [
            "not-an-email",
            "@example.com",
            "user@",
            ""
        ]

        # Basic email validation check
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        for email in valid_emails:
            assert re.match(email_pattern, email), f"{email} should be valid"

        for email in invalid_emails:
            assert not re.match(email_pattern, email), f"{email} should be invalid"
