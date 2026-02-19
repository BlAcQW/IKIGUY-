"""
Unit tests for API Key Service with Organization Isolation.

Tests CRUD operations with real database operations to verify:
1. API keys are properly scoped to organizations
2. Cross-organization access is prevented
3. All database operations work correctly with organization_id
4. Data is properly isolated between organizations

Uses real MongoDB test database with actual CRUD operations.
"""
import pytest
import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.services.api_key_service import APIKeyService, APIKeyCreate

# Test configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://admin:aawwER4444%25@127.0.0.1:27017/?authSource=admin")
TEST_DATABASE = "kasaai_core_test"

# Test data
TEST_ORG_A = "test_org_a_" + datetime.now().strftime("%Y%m%d%H%M%S")
TEST_ORG_B = "test_org_b_" + datetime.now().strftime("%Y%m%d%H%M%S")
TEST_USER_A = "user_a_test"
TEST_USER_B = "user_b_test"


@pytest.fixture
async def db_client():
    """Create test database client."""
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[TEST_DATABASE]
    yield db
    # Cleanup after all tests
    await db.api_keys.delete_many({"organization_id": {"$in": [TEST_ORG_A, TEST_ORG_B]}})
    client.close()


@pytest.fixture
async def api_key_service(db_client):
    """Create API key service instance."""
    service = APIKeyService()
    # Override database to use test database
    service.client = AsyncIOMotorClient(MONGODB_URL)
    service.db = service.client[TEST_DATABASE]
    service.collection = service.db["api_keys"]
    await service.create_indexes()
    return service


class TestAPIKeyServiceOrganizationCRUD:
    """Test API key service CRUD operations with organization isolation."""

    @pytest.mark.asyncio
    async def test_create_api_key_with_organization_id(self, api_key_service):
        """Test creating API key with organization_id."""
        # Create API key for organization A
        api_key = await api_key_service.create_api_key(
            user_id=TEST_USER_A,
            name="Test Key Org A",
            scopes=["tts:synthesize", "tts:history"],
            rate_limit=100,
            organization_id=TEST_ORG_A
        )

        # Verify API key was created
        assert api_key is not None
        assert api_key.name == "Test Key Org A"
        assert api_key.api_key is not None
        assert api_key.api_key.startswith("kas_")

        # Verify in database (convert string ID to ObjectId for direct query)
        doc = await api_key_service.collection.find_one({"_id": ObjectId(api_key.id)})
        assert doc is not None
        assert doc["organization_id"] == TEST_ORG_A
        assert doc["user_id"] == TEST_USER_A

        print(f"✅ Created API key {api_key.id} for organization {TEST_ORG_A}")

    @pytest.mark.asyncio
    async def test_list_api_keys_filtered_by_organization(self, api_key_service):
        """Test listing API keys filtered by organization."""
        # Create keys in different organizations
        key_a1 = await api_key_service.create_api_key(
            user_id=TEST_USER_A,
            name="Key A1",
            scopes=["tts:synthesize"],
            organization_id=TEST_ORG_A
        )

        key_a2 = await api_key_service.create_api_key(
            user_id=TEST_USER_A,
            name="Key A2",
            scopes=["tts:synthesize"],
            organization_id=TEST_ORG_A
        )

        key_b1 = await api_key_service.create_api_key(
            user_id=TEST_USER_A,
            name="Key B1",
            scopes=["tts:synthesize"],
            organization_id=TEST_ORG_B
        )

        # List keys for organization A
        keys_org_a = await api_key_service.list_user_keys(
            user_id=TEST_USER_A,
            organization_id=TEST_ORG_A
        )

        # List keys for organization B
        keys_org_b = await api_key_service.list_user_keys(
            user_id=TEST_USER_A,
            organization_id=TEST_ORG_B
        )

        # Verify organization A has 2 keys
        assert len(keys_org_a) == 2
        org_a_ids = {k.id for k in keys_org_a}
        assert key_a1.id in org_a_ids
        assert key_a2.id in org_a_ids
        assert key_b1.id not in org_a_ids

        # Verify organization B has 1 key
        assert len(keys_org_b) == 1
        assert keys_org_b[0].id == key_b1.id

        print(f"✅ Organization A has {len(keys_org_a)} keys")
        print(f"✅ Organization B has {len(keys_org_b)} keys")
        print(f"✅ Keys properly isolated between organizations")

    @pytest.mark.asyncio
    async def test_get_api_key_validates_organization(self, api_key_service):
        """Test getting API key validates organization ownership."""
        # Create key in organization A
        key_a = await api_key_service.create_api_key(
            user_id=TEST_USER_A,
            name="Key for Org A",
            scopes=["tts:synthesize"],
            organization_id=TEST_ORG_A
        )

        # Get key with correct organization
        retrieved_key = await api_key_service.get_api_key(
            user_id=TEST_USER_A,
            key_id=key_a.id,
            organization_id=TEST_ORG_A
        )
        assert retrieved_key is not None
        assert retrieved_key.id == key_a.id

        # Try to get key with wrong organization
        wrong_org_key = await api_key_service.get_api_key(
            user_id=TEST_USER_A,
            key_id=key_a.id,
            organization_id=TEST_ORG_B
        )
        assert wrong_org_key is None

        print(f"✅ API key accessible in correct organization")
        print(f"✅ API key NOT accessible in wrong organization")

    @pytest.mark.asyncio
    async def test_revoke_api_key_validates_organization(self, api_key_service):
        """Test revoking API key validates organization ownership."""
        # Create key in organization A
        key_a = await api_key_service.create_api_key(
            user_id=TEST_USER_A,
            name="Key to Revoke",
            scopes=["tts:synthesize"],
            organization_id=TEST_ORG_A
        )

        # Try to revoke from wrong organization (should fail)
        revoked_wrong = await api_key_service.revoke_api_key(
            user_id=TEST_USER_A,
            key_id=key_a.id,
            organization_id=TEST_ORG_B
        )
        assert revoked_wrong is False

        # Verify key still exists
        key_check = await api_key_service.get_api_key(
            user_id=TEST_USER_A,
            key_id=key_a.id,
            organization_id=TEST_ORG_A
        )
        assert key_check is not None
        assert key_check.revoked is False

        # Revoke from correct organization (should succeed)
        revoked_correct = await api_key_service.revoke_api_key(
            user_id=TEST_USER_A,
            key_id=key_a.id,
            organization_id=TEST_ORG_A
        )
        assert revoked_correct is True

        # Verify key is revoked in database (convert string ID to ObjectId)
        doc = await api_key_service.collection.find_one({"_id": ObjectId(key_a.id)})
        assert doc is not None
        assert doc["revoked"] is True

        print(f"✅ Cannot revoke key from wrong organization")
        print(f"✅ Successfully revoked key from correct organization")

    @pytest.mark.asyncio
    async def test_get_usage_stats_validates_organization(self, api_key_service):
        """Test getting usage stats validates organization."""
        # Create key in organization A
        key_a = await api_key_service.create_api_key(
            user_id=TEST_USER_A,
            name="Key with Stats",
            scopes=["tts:synthesize"],
            organization_id=TEST_ORG_A
        )

        # Get stats with correct organization
        stats_correct = await api_key_service.get_usage_stats(
            user_id=TEST_USER_A,
            key_id=key_a.id,
            organization_id=TEST_ORG_A
        )
        assert stats_correct is not None
        assert stats_correct.key_id == key_a.id

        # Try to get stats with wrong organization
        stats_wrong = await api_key_service.get_usage_stats(
            user_id=TEST_USER_A,
            key_id=key_a.id,
            organization_id=TEST_ORG_B
        )
        assert stats_wrong is None

        print(f"✅ Usage stats accessible in correct organization")
        print(f"✅ Usage stats NOT accessible in wrong organization")

    @pytest.mark.asyncio
    async def test_complete_crud_cycle_with_organization(self, api_key_service):
        """Test complete CREATE -> READ -> UPDATE (revoke) -> DELETE cycle."""
        # CREATE: Create API key
        created_key = await api_key_service.create_api_key(
            user_id=TEST_USER_A,
            name="Full CRUD Test Key",
            scopes=["tts:synthesize", "tts:history"],
            rate_limit=150,
            organization_id=TEST_ORG_A
        )
        assert created_key is not None
        print(f"✅ CREATE: Created key {created_key.id}")

        # READ: Retrieve key
        read_key = await api_key_service.get_api_key(
            user_id=TEST_USER_A,
            key_id=created_key.id,
            organization_id=TEST_ORG_A
        )
        assert read_key is not None
        assert read_key.name == "Full CRUD Test Key"
        assert read_key.rate_limit == 150
        print(f"✅ READ: Retrieved key successfully")

        # UPDATE: Revoke key
        revoked = await api_key_service.revoke_api_key(
            user_id=TEST_USER_A,
            key_id=created_key.id,
            organization_id=TEST_ORG_A
        )
        assert revoked is True
        print(f"✅ UPDATE: Revoked key successfully")

        # Verify revocation
        revoked_key = await api_key_service.get_api_key(
            user_id=TEST_USER_A,
            key_id=created_key.id,
            organization_id=TEST_ORG_A
        )
        assert revoked_key.revoked is True
        print(f"✅ VERIFY: Key marked as revoked")

        # DELETE: Remove from database (convert string ID to ObjectId)
        delete_result = await api_key_service.collection.delete_one({
            "_id": ObjectId(created_key.id),
            "organization_id": TEST_ORG_A
        })
        assert delete_result.deleted_count == 1
        print(f"✅ DELETE: Removed key from database")

        # Verify deletion
        deleted_check = await api_key_service.get_api_key(
            user_id=TEST_USER_A,
            key_id=created_key.id,
            organization_id=TEST_ORG_A
        )
        assert deleted_check is None
        print(f"✅ VERIFY: Key completely removed")

    @pytest.mark.asyncio
    async def test_cross_organization_access_prevention(self, api_key_service):
        """Test that cross-organization access is completely prevented."""
        # Create keys in both organizations
        key_a = await api_key_service.create_api_key(
            user_id=TEST_USER_A,
            name="Org A Key",
            scopes=["tts:synthesize"],
            organization_id=TEST_ORG_A
        )

        key_b = await api_key_service.create_api_key(
            user_id=TEST_USER_B,
            name="Org B Key",
            scopes=["tts:synthesize"],
            organization_id=TEST_ORG_B
        )

        # User A tries to access User B's key
        accessed_b_from_a = await api_key_service.get_api_key(
            user_id=TEST_USER_B,
            key_id=key_b.id,
            organization_id=TEST_ORG_A  # Wrong organization
        )
        assert accessed_b_from_a is None

        # User B tries to access User A's key
        accessed_a_from_b = await api_key_service.get_api_key(
            user_id=TEST_USER_A,
            key_id=key_a.id,
            organization_id=TEST_ORG_B  # Wrong organization
        )
        assert accessed_a_from_b is None

        # User A tries to revoke User B's key
        revoked_b_from_a = await api_key_service.revoke_api_key(
            user_id=TEST_USER_B,
            key_id=key_b.id,
            organization_id=TEST_ORG_A  # Wrong organization
        )
        assert revoked_b_from_a is False

        # Verify key B is still active
        key_b_check = await api_key_service.get_api_key(
            user_id=TEST_USER_B,
            key_id=key_b.id,
            organization_id=TEST_ORG_B
        )
        assert key_b_check is not None
        assert key_b_check.revoked is False

        print(f"✅ User A cannot access User B's key")
        print(f"✅ User B cannot access User A's key")
        print(f"✅ User A cannot revoke User B's key")
        print(f"✅ Cross-organization access completely prevented")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
