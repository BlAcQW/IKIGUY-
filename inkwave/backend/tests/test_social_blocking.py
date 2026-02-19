"""
Integration tests for social blocking functionality.

Tests cover:
- Happy path: block/unblock operations
- Edge cases: mutual follows removal, blocked user cannot refollow
- Failure cases: self-blocking, duplicate blocks

All tests use real MongoDB operations (no mocks).
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List

import pytest
import pytest_asyncio
from motor.motor_asyncio import AsyncIOMotorClient

from app.services.social_service import SocialService
from app.models.social import FollowStatus

# Test configuration
MONGODB_URI = os.getenv(
    "MONGODB_URI", "mongodb://admin:aawwER4444%25@127.0.0.1:27017/"
)
TEST_DATABASE = "inkwave_test_social_blocking"


@pytest_asyncio.fixture
async def db_client():
    """Create test database client."""
    client = AsyncIOMotorClient(MONGODB_URI)
    yield client
    # Cleanup: Drop test database
    await client.drop_database(TEST_DATABASE)
    client.close()


@pytest_asyncio.fixture
async def test_db(db_client):
    """Get test database instance."""
    return db_client[TEST_DATABASE]


@pytest_asyncio.fixture
async def social_service(test_db):
    """Create social service instance."""
    return SocialService(test_db)


@pytest_asyncio.fixture
def test_users() -> List[Dict]:
    """Create test user data."""
    return [
        {
            "user_id": "block_user_001",
            "email": "blocker@test.com",
            "username": "blocker_user",
            "display_name": "Blocker User",
            "created_at": datetime.utcnow(),
            "social_settings": {
                "profile_visibility": "public",
                "discoverable_by_search": True,
                "show_reading_activity": True,
            },
            "social_stats": {
                "followers_count": 0,
                "following_count": 0,
                "total_listening_hours": 10.5,
            },
        },
        {
            "user_id": "block_user_002",
            "email": "blocked@test.com",
            "username": "blocked_user",
            "display_name": "Blocked User",
            "created_at": datetime.utcnow(),
            "social_settings": {
                "profile_visibility": "public",
                "discoverable_by_search": True,
                "show_reading_activity": True,
            },
            "social_stats": {
                "followers_count": 0,
                "following_count": 0,
                "total_listening_hours": 5.0,
            },
        },
        {
            "user_id": "block_user_003",
            "email": "user3@test.com",
            "username": "user_three",
            "display_name": "User Three",
            "created_at": datetime.utcnow(),
            "social_settings": {
                "profile_visibility": "public",
                "discoverable_by_search": True,
                "show_reading_activity": True,
            },
            "social_stats": {
                "followers_count": 0,
                "following_count": 0,
                "total_listening_hours": 8.0,
            },
        },
    ]


@pytest_asyncio.fixture
async def created_users(test_db, test_users):
    """Insert test users and clean up after test."""
    users_collection = test_db.users
    for user_data in test_users:
        await users_collection.insert_one(user_data)

    yield test_users

    # Cleanup all related data
    user_ids = [u["user_id"] for u in test_users]
    await users_collection.delete_many({"user_id": {"$in": user_ids}})
    await test_db.user_follows.delete_many({
        "$or": [
            {"follower_user_id": {"$in": user_ids}},
            {"following_user_id": {"$in": user_ids}},
        ]
    })
    await test_db.user_blocks.delete_many({
        "$or": [
            {"blocker_user_id": {"$in": user_ids}},
            {"blocked_user_id": {"$in": user_ids}},
        ]
    })


# ============================================================================
# HAPPY PATH TESTS
# ============================================================================


class TestSocialBlocking:
    """Test successful blocking operations."""

    @pytest.mark.asyncio
    async def test_block_user_success(
        self, social_service, test_db, created_users
    ):
        """
        Test blocking a user successfully.

        Verifies:
        - Block record is created
        - Existing follow relationships are removed
        - Social stats are updated
        """
        blocker_id = created_users[0]["user_id"]
        blocked_id = created_users[1]["user_id"]

        # First, create a follow relationship
        await social_service.follow_user(blocker_id, blocked_id)

        # Verify follow exists before blocking
        is_following_before = await social_service.is_following(blocker_id, blocked_id)
        assert is_following_before is True

        # Block the user
        result = await social_service.block_user(
            blocker_id, blocked_id, reason="Test blocking"
        )
        assert result is True

        # Verify block record exists
        block = await test_db.user_blocks.find_one({
            "blocker_user_id": blocker_id,
            "blocked_user_id": blocked_id,
        })
        assert block is not None
        assert block["blocker_user_id"] == blocker_id
        assert block["blocked_user_id"] == blocked_id
        assert block["reason"] == "Test blocking"
        assert "blocked_at" in block
        assert "block_id" in block

        # Verify follow relationship was removed
        is_following_after = await social_service.is_following(blocker_id, blocked_id)
        assert is_following_after is False

        # Verify follow record deleted from database
        follow_record = await test_db.user_follows.find_one({
            "follower_user_id": blocker_id,
            "following_user_id": blocked_id,
        })
        assert follow_record is None

        # Verify social stats updated
        blocker_user = await test_db.users.find_one({"user_id": blocker_id})
        assert blocker_user["social_stats"]["following_count"] == 0

    @pytest.mark.asyncio
    async def test_unblock_user_success(
        self, social_service, test_db, created_users
    ):
        """
        Test unblocking a user successfully.

        Verifies:
        - Block record is deleted
        - Returns True on successful unblock
        """
        blocker_id = created_users[0]["user_id"]
        blocked_id = created_users[1]["user_id"]

        # First, block the user
        await social_service.block_user(blocker_id, blocked_id)

        # Verify block exists
        block_before = await test_db.user_blocks.find_one({
            "blocker_user_id": blocker_id,
            "blocked_user_id": blocked_id,
        })
        assert block_before is not None

        # Unblock the user
        result = await social_service.unblock_user(blocker_id, blocked_id)
        assert result is True

        # Verify block record deleted
        block_after = await test_db.user_blocks.find_one({
            "blocker_user_id": blocker_id,
            "blocked_user_id": blocked_id,
        })
        assert block_after is None

        # Verify is_blocked returns False
        is_blocked = await social_service.is_blocked(blocker_id, blocked_id)
        assert is_blocked is False

    @pytest.mark.asyncio
    async def test_is_blocked_check(
        self, social_service, test_db, created_users
    ):
        """
        Test checking block status (unidirectional).

        Verifies:
        - is_blocked returns True when blocked
        - is_blocked returns False when not blocked
        - is_blocked checks both directions
        """
        blocker_id = created_users[0]["user_id"]
        blocked_id = created_users[1]["user_id"]
        unrelated_id = created_users[2]["user_id"]

        # Verify not blocked initially
        is_blocked_before = await social_service.is_blocked(blocker_id, blocked_id)
        assert is_blocked_before is False

        # Block the user
        await social_service.block_user(blocker_id, blocked_id)

        # Verify blocked from blocker's perspective
        is_blocked_forward = await social_service.is_blocked(blocker_id, blocked_id)
        assert is_blocked_forward is True

        # Verify blocked from blocked user's perspective (bidirectional check)
        is_blocked_reverse = await social_service.is_blocked(blocked_id, blocker_id)
        assert is_blocked_reverse is True

        # Verify unrelated user is not blocked
        is_blocked_unrelated = await social_service.is_blocked(blocker_id, unrelated_id)
        assert is_blocked_unrelated is False


# ============================================================================
# EDGE CASE TESTS
# ============================================================================


class TestSocialBlockingEdgeCases:
    """Test edge cases for blocking operations."""

    @pytest.mark.asyncio
    async def test_block_removes_mutual_follows(
        self, social_service, test_db, created_users
    ):
        """
        Test that blocking removes follow relationships in BOTH directions.

        Scenario:
        - User A follows User B
        - User B follows User A (mutual follows)
        - User A blocks User B
        - BOTH follow relationships should be deleted
        """
        user_a = created_users[0]["user_id"]
        user_b = created_users[1]["user_id"]

        # Create mutual follows
        await social_service.follow_user(user_a, user_b)  # A follows B
        await social_service.follow_user(user_b, user_a)  # B follows A

        # Verify mutual follows exist
        a_follows_b = await social_service.is_following(user_a, user_b)
        b_follows_a = await social_service.is_following(user_b, user_a)
        assert a_follows_b is True
        assert b_follows_a is True

        # Verify stats before blocking
        user_a_before = await test_db.users.find_one({"user_id": user_a})
        user_b_before = await test_db.users.find_one({"user_id": user_b})
        assert user_a_before["social_stats"]["following_count"] == 1
        assert user_a_before["social_stats"]["followers_count"] == 1
        assert user_b_before["social_stats"]["following_count"] == 1
        assert user_b_before["social_stats"]["followers_count"] == 1

        # User A blocks User B
        await social_service.block_user(user_a, user_b)

        # Verify BOTH follow relationships removed
        a_follows_b_after = await social_service.is_following(user_a, user_b)
        b_follows_a_after = await social_service.is_following(user_b, user_a)
        assert a_follows_b_after is False
        assert b_follows_a_after is False

        # Verify database has no follow records
        follows_count = await test_db.user_follows.count_documents({
            "$or": [
                {"follower_user_id": user_a, "following_user_id": user_b},
                {"follower_user_id": user_b, "following_user_id": user_a},
            ]
        })
        assert follows_count == 0

        # Verify stats updated for both users
        user_a_after = await test_db.users.find_one({"user_id": user_a})
        user_b_after = await test_db.users.find_one({"user_id": user_b})
        assert user_a_after["social_stats"]["following_count"] == 0
        assert user_a_after["social_stats"]["followers_count"] == 0
        assert user_b_after["social_stats"]["following_count"] == 0
        assert user_b_after["social_stats"]["followers_count"] == 0

    @pytest.mark.asyncio
    async def test_blocked_user_cannot_refollow(
        self, social_service, created_users
    ):
        """
        Test that a blocked user cannot follow the blocker.

        Scenario:
        - User A blocks User B
        - User B attempts to follow User A
        - Should raise ValueError due to block
        """
        blocker_id = created_users[0]["user_id"]
        blocked_id = created_users[1]["user_id"]

        # User A blocks User B
        await social_service.block_user(blocker_id, blocked_id)

        # User B attempts to follow User A (should fail)
        with pytest.raises(ValueError, match="Cannot follow this user"):
            await social_service.follow_user(blocked_id, blocker_id)

        # Verify no follow relationship created
        is_following = await social_service.is_following(blocked_id, blocker_id)
        assert is_following is False


# ============================================================================
# FAILURE CASE TESTS
# ============================================================================


class TestSocialBlockingFailures:
    """Test failure scenarios for blocking operations."""

    @pytest.mark.asyncio
    async def test_cannot_block_self(self, social_service, created_users):
        """
        Test that a user cannot block themselves.

        Verifies:
        - ValueError is raised with appropriate message
        - No block record is created
        """
        user_id = created_users[0]["user_id"]

        with pytest.raises(ValueError, match="cannot block yourself"):
            await social_service.block_user(user_id, user_id)

        # Verify no block record created
        is_blocked = await social_service.is_blocked(user_id, user_id)
        assert is_blocked is False

    @pytest.mark.asyncio
    async def test_cannot_block_same_user_twice(
        self, social_service, test_db, created_users
    ):
        """
        Test that blocking the same user twice raises an error.

        Verifies:
        - First block succeeds
        - Second block raises ValueError
        - Only one block record exists
        """
        blocker_id = created_users[0]["user_id"]
        blocked_id = created_users[1]["user_id"]

        # First block should succeed
        result = await social_service.block_user(blocker_id, blocked_id)
        assert result is True

        # Second block should fail
        with pytest.raises(ValueError, match="already blocked"):
            await social_service.block_user(blocker_id, blocked_id)

        # Verify only one block record exists
        block_count = await test_db.user_blocks.count_documents({
            "blocker_user_id": blocker_id,
            "blocked_user_id": blocked_id,
        })
        assert block_count == 1

    @pytest.mark.asyncio
    async def test_unblock_non_blocked_user_returns_false(
        self, social_service, created_users
    ):
        """
        Test that unblocking a user who is not blocked returns False.

        Verifies:
        - unblock_user returns False (not an error)
        - No exception is raised
        """
        blocker_id = created_users[0]["user_id"]
        blocked_id = created_users[1]["user_id"]

        # Attempt to unblock when no block exists
        result = await social_service.unblock_user(blocker_id, blocked_id)
        assert result is False

        # Verify still not blocked
        is_blocked = await social_service.is_blocked(blocker_id, blocked_id)
        assert is_blocked is False
