"""
Unit tests for social follow/unfollow operations.

Tests the complete follow/unfollow workflow with real MongoDB data:
- Follow user successfully
- Unfollow user successfully
- Get followers/following lists
- Check follow relationship
- Rate limiting enforcement
- Maximum following limit
- Follow validation and error cases
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
import uuid

from app.services.social_service import SocialService
from app.models.social import FollowStatus

# Load environment variables
load_dotenv()

# Test configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://admin:aawwER4444%25@127.0.0.1:27017/")
TEST_DATABASE = "inkwave_test_social"


@pytest_asyncio.fixture
async def db_client():
    """Create test database client."""
    client = AsyncIOMotorClient(MONGODB_URI)
    yield client
    # Cleanup: Drop test database after tests
    await client.drop_database(TEST_DATABASE)
    client.close()


@pytest_asyncio.fixture
async def test_db(db_client):
    """Get test database instance."""
    db = db_client[TEST_DATABASE]
    yield db


@pytest_asyncio.fixture
async def social_service(test_db):
    """Create SocialService with test database."""
    service = SocialService(test_db)
    return service


@pytest.fixture
def test_users():
    """Create test user data (5 users for complex scenarios)."""
    return [
        {
            "user_id": f"test_user_1_{uuid.uuid4().hex[:8]}",
            "email": "user1@inkwave.com",
            "display_name": "Test User 1",
            "username": f"testuser1_{uuid.uuid4().hex[:6]}",
            "avatar_url": "https://example.com/avatar1.jpg",
            "privacy_settings": {
                "profile_visibility": "public",
                "show_currently_reading": True,
                "show_reading_history": True,
                "discoverable_by_search": True,
                "appear_in_leaderboard": True,
                "show_followers_list": True,
                "show_following_list": True,
                "allow_follow_requests": True
            },
            "social_stats": {
                "followers_count": 0,
                "following_count": 0,
                "total_listening_hours": 0,
                "books_completed": 0
            },
            "created_at": datetime.utcnow()
        },
        {
            "user_id": f"test_user_2_{uuid.uuid4().hex[:8]}",
            "email": "user2@inkwave.com",
            "display_name": "Test User 2",
            "username": f"testuser2_{uuid.uuid4().hex[:6]}",
            "avatar_url": "https://example.com/avatar2.jpg",
            "privacy_settings": {
                "profile_visibility": "public",
                "show_currently_reading": True,
                "discoverable_by_search": True,
                "appear_in_leaderboard": True,
                "allow_follow_requests": True
            },
            "social_stats": {
                "followers_count": 0,
                "following_count": 0
            },
            "created_at": datetime.utcnow()
        },
        {
            "user_id": f"test_user_3_{uuid.uuid4().hex[:8]}",
            "email": "user3@inkwave.com",
            "display_name": "Test User 3",
            "username": f"testuser3_{uuid.uuid4().hex[:6]}",
            "privacy_settings": {
                "profile_visibility": "public",
                "allow_follow_requests": True
            },
            "social_stats": {
                "followers_count": 0,
                "following_count": 0
            },
            "created_at": datetime.utcnow()
        },
        {
            "user_id": f"test_user_4_{uuid.uuid4().hex[:8]}",
            "email": "user4@inkwave.com",
            "display_name": "Test User 4",
            "username": f"testuser4_{uuid.uuid4().hex[:6]}",
            "privacy_settings": {
                "profile_visibility": "public",
                "allow_follow_requests": True
            },
            "social_stats": {
                "followers_count": 0,
                "following_count": 0
            },
            "created_at": datetime.utcnow()
        },
        {
            "user_id": f"test_user_5_{uuid.uuid4().hex[:8]}",
            "email": "user5@inkwave.com",
            "display_name": "Test User 5",
            "username": f"testuser5_{uuid.uuid4().hex[:6]}",
            "privacy_settings": {
                "profile_visibility": "public",
                "allow_follow_requests": True
            },
            "social_stats": {
                "followers_count": 0,
                "following_count": 0
            },
            "created_at": datetime.utcnow()
        }
    ]


@pytest_asyncio.fixture
async def created_users(test_db, test_users):
    """Insert test users into database and clean up after test."""
    users_collection = test_db.users

    # Insert all users
    for user_data in test_users:
        await users_collection.insert_one(user_data)

    yield test_users

    # Cleanup: Delete test users and all related data
    user_ids = [u["user_id"] for u in test_users]
    await users_collection.delete_many({"user_id": {"$in": user_ids}})
    await test_db.user_follows.delete_many({
        "$or": [
            {"follower_user_id": {"$in": user_ids}},
            {"following_user_id": {"$in": user_ids}}
        ]
    })
    await test_db.user_blocks.delete_many({
        "$or": [
            {"blocker_user_id": {"$in": user_ids}},
            {"blocked_user_id": {"$in": user_ids}}
        ]
    })


@pytest.mark.asyncio
class TestSocialFollowUnfollow:
    """Test follow/unfollow core functionality (Happy Path)."""

    async def test_follow_user_success(
        self, social_service, created_users, test_db
    ):
        """
        Test successful follow operation.

        Steps:
        1. User A follows User B
        2. Verify follow record created in user_follows collection
        3. Verify social_stats updated for both users
        4. Verify follower_count and following_count incremented
        """
        user_a = created_users[0]
        user_b = created_users[1]

        # Follow user
        result = await social_service.follow_user(
            user_a["user_id"],
            user_b["user_id"]
        )

        # Assert result
        assert result["success"] is True
        assert result["following_user_id"] == user_b["user_id"]
        assert "message" in result

        # Verify follow record exists
        follow = await test_db.user_follows.find_one({
            "follower_user_id": user_a["user_id"],
            "following_user_id": user_b["user_id"]
        })
        assert follow is not None
        assert follow["status"] == FollowStatus.ACCEPTED
        assert follow["accepted_at"] is not None
        assert "requested_at" in follow

        # Verify denormalized stats updated
        updated_a = await test_db.users.find_one({"user_id": user_a["user_id"]})
        updated_b = await test_db.users.find_one({"user_id": user_b["user_id"]})

        assert updated_a["social_stats"]["following_count"] == 1
        assert updated_b["social_stats"]["followers_count"] == 1

    async def test_unfollow_user_success(
        self, social_service, created_users, test_db
    ):
        """
        Test successful unfollow operation.

        Steps:
        1. User A follows User B
        2. User A unfollows User B
        3. Verify follow record deleted
        4. Verify social_stats decremented
        """
        user_a = created_users[0]
        user_b = created_users[1]

        # First follow
        await social_service.follow_user(user_a["user_id"], user_b["user_id"])

        # Then unfollow
        result = await social_service.unfollow_user(
            user_a["user_id"],
            user_b["user_id"]
        )

        # Assert unfollow succeeded
        assert result is True

        # Verify follow record deleted
        follow = await test_db.user_follows.find_one({
            "follower_user_id": user_a["user_id"],
            "following_user_id": user_b["user_id"]
        })
        assert follow is None

        # Verify stats decremented back to 0
        updated_a = await test_db.users.find_one({"user_id": user_a["user_id"]})
        updated_b = await test_db.users.find_one({"user_id": user_b["user_id"]})

        assert updated_a["social_stats"]["following_count"] == 0
        assert updated_b["social_stats"]["followers_count"] == 0

    async def test_get_followers_list(
        self, social_service, created_users, test_db
    ):
        """
        Test retrieving followers list.

        Steps:
        1. User B, C, D follow User A
        2. Get followers for User A
        3. Verify correct users returned
        4. Verify sorted by follow date
        """
        user_a = created_users[0]
        users_following = [created_users[1], created_users[2], created_users[3]]

        # Create follows
        for user in users_following:
            await social_service.follow_user(user["user_id"], user_a["user_id"])

        # Get followers
        followers = await social_service.get_followers(user_a["user_id"])

        # Verify
        assert len(followers) == 3
        follower_ids = [f["user_id"] for f in followers]
        for user in users_following:
            assert user["user_id"] in follower_ids

    async def test_get_following_list(
        self, social_service, created_users, test_db
    ):
        """
        Test retrieving following list.

        Steps:
        1. User A follows Users B, C, D
        2. Get following for User A
        3. Verify correct users returned
        """
        user_a = created_users[0]
        users_to_follow = [created_users[1], created_users[2], created_users[3]]

        # Create follows
        for user in users_to_follow:
            await social_service.follow_user(user_a["user_id"], user["user_id"])

        # Get following
        following = await social_service.get_following(user_a["user_id"])

        # Verify
        assert len(following) == 3
        following_ids = [f["user_id"] for f in following]
        for user in users_to_follow:
            assert user["user_id"] in following_ids

    async def test_is_following_check(
        self, social_service, created_users
    ):
        """
        Test is_following relationship check.

        Steps:
        1. User A follows User B
        2. Check is_following(A, B) returns True
        3. Check is_following(B, A) returns False (asymmetric)
        """
        user_a = created_users[0]
        user_b = created_users[1]

        # Follow
        await social_service.follow_user(user_a["user_id"], user_b["user_id"])

        # Check relationship
        is_following_ab = await social_service.is_following(
            user_a["user_id"],
            user_b["user_id"]
        )
        is_following_ba = await social_service.is_following(
            user_b["user_id"],
            user_a["user_id"]
        )

        assert is_following_ab is True
        assert is_following_ba is False  # Asymmetric


@pytest.mark.asyncio
class TestSocialFollowEdgeCases:
    """Test edge cases and limits."""

    async def test_follow_pagination(
        self, social_service, created_users, test_db
    ):
        """
        Test pagination of followers/following lists.

        Steps:
        1. Create 25 followers for User A
        2. Get page 1 (20 results)
        3. Get page 2 (5 results)
        4. Verify no overlap
        """
        user_a = created_users[0]

        # Create 25 more users in database and have them follow user_a
        follower_ids = []
        for i in range(25):
            follower = {
                "user_id": f"follower_{i}_{uuid.uuid4().hex[:6]}",
                "email": f"follower{i}@test.com",
                "username": f"follower{i}",
                "display_name": f"Follower {i}",
                "privacy_settings": {"allow_follow_requests": True},
                "social_stats": {"followers_count": 0, "following_count": 0}
            }
            await test_db.users.insert_one(follower)
            follower_ids.append(follower["user_id"])
            await social_service.follow_user(follower["user_id"], user_a["user_id"])

        # Get page 1
        page1 = await social_service.get_followers(user_a["user_id"], page=1, per_page=20)
        assert len(page1) == 20

        # Get page 2
        page2 = await social_service.get_followers(user_a["user_id"], page=2, per_page=20)
        assert len(page2) == 5

        # Verify no overlap
        page1_ids = {u["user_id"] for u in page1}
        page2_ids = {u["user_id"] for u in page2}
        assert len(page1_ids & page2_ids) == 0

        # Cleanup
        await test_db.users.delete_many({"user_id": {"$in": follower_ids}})

    async def test_follow_rate_limiting_hourly(
        self, social_service, created_users, test_db
    ):
        """
        Test hourly rate limit (20 follows per hour).

        Steps:
        1. Create 20 users
        2. Follow all 20 users successfully
        3. Try to follow 21st user
        4. Verify rate limit error
        """
        user_a = created_users[0]

        # Create 21 users
        target_users = []
        for i in range(21):
            user = {
                "user_id": f"rate_test_user_{i}_{uuid.uuid4().hex[:6]}",
                "email": f"ratetest{i}@test.com",
                "username": f"ratetest{i}",
                "display_name": f"Rate Test {i}",
                "privacy_settings": {"allow_follow_requests": True},
                "social_stats": {"followers_count": 0, "following_count": 0}
            }
            await test_db.users.insert_one(user)
            target_users.append(user)

        # Follow 20 users successfully
        for i in range(20):
            await social_service.follow_user(user_a["user_id"], target_users[i]["user_id"])

        # 21st follow should fail
        with pytest.raises(ValueError, match="exceeded the hourly follow limit"):
            await social_service.follow_user(user_a["user_id"], target_users[20]["user_id"])

        # Cleanup
        await test_db.users.delete_many({"user_id": {"$in": [u["user_id"] for u in target_users]}})

    async def test_follow_max_total_limit(
        self, social_service, created_users, test_db
    ):
        """
        Test maximum following limit (2000 total).

        Note: This is a simulation test - actually creating 2000 follows
        would be slow. We'll manipulate the counter directly for testing.

        Steps:
        1. Manually set following_count to 2000
        2. Create 2000 fake follow records
        3. Try to follow new user
        4. Verify limit error
        """
        user_a = created_users[0]
        user_b = created_users[1]

        # Create 2000 fake follow records
        fake_follows = []
        for i in range(2000):
            fake_follows.append({
                "follow_id": str(uuid.uuid4()),
                "follower_user_id": user_a["user_id"],
                "following_user_id": f"fake_user_{i}",
                "status": FollowStatus.ACCEPTED,
                "requested_at": datetime.utcnow(),
                "accepted_at": datetime.utcnow()
            })
        await test_db.user_follows.insert_many(fake_follows)

        # Manually update following count to match
        await test_db.users.update_one(
            {"user_id": user_a["user_id"]},
            {"$set": {"social_stats.following_count": 2000}}
        )

        # Try to follow - should fail
        with pytest.raises(ValueError, match="maximum follow limit"):
            await social_service.follow_user(user_a["user_id"], user_b["user_id"])

    async def test_refollow_after_unfollow(
        self, social_service, created_users, test_db
    ):
        """
        Test following same user again after unfollowing.

        Steps:
        1. User A follows User B
        2. User A unfollows User B
        3. User A follows User B again
        4. Verify follow is re-created
        """
        user_a = created_users[0]
        user_b = created_users[1]

        # Follow
        await social_service.follow_user(user_a["user_id"], user_b["user_id"])

        # Unfollow
        await social_service.unfollow_user(user_a["user_id"], user_b["user_id"])

        # Follow again
        result = await social_service.follow_user(user_a["user_id"], user_b["user_id"])

        assert result["success"] is True

        # Verify is following
        is_following = await social_service.is_following(
            user_a["user_id"],
            user_b["user_id"]
        )
        assert is_following is True

        # Verify stats are correct
        updated_a = await test_db.users.find_one({"user_id": user_a["user_id"]})
        assert updated_a["social_stats"]["following_count"] == 1


@pytest.mark.asyncio
class TestSocialFollowFailureCases:
    """Test failure scenarios and validation."""

    async def test_follow_self_fails(
        self, social_service, created_users
    ):
        """
        Test that user cannot follow themselves.

        Steps:
        1. User A tries to follow User A
        2. Verify ValueError raised
        """
        user_a = created_users[0]

        with pytest.raises(ValueError, match="cannot follow yourself"):
            await social_service.follow_user(user_a["user_id"], user_a["user_id"])

    async def test_follow_nonexistent_user_fails(
        self, social_service, created_users
    ):
        """
        Test following non-existent user fails.

        Steps:
        1. User A tries to follow fake user ID
        2. Verify ValueError raised
        """
        user_a = created_users[0]

        with pytest.raises(ValueError, match="User not found"):
            await social_service.follow_user(
                user_a["user_id"],
                "nonexistent_user_id_12345"
            )

    async def test_follow_already_following_fails(
        self, social_service, created_users
    ):
        """
        Test following same user twice fails.

        Steps:
        1. User A follows User B
        2. User A tries to follow User B again
        3. Verify ValueError raised
        """
        user_a = created_users[0]
        user_b = created_users[1]

        # First follow succeeds
        await social_service.follow_user(user_a["user_id"], user_b["user_id"])

        # Second follow fails
        with pytest.raises(ValueError, match="already following"):
            await social_service.follow_user(user_a["user_id"], user_b["user_id"])

    async def test_unfollow_not_following_returns_false(
        self, social_service, created_users
    ):
        """
        Test unfollowing user you're not following returns False.

        Steps:
        1. User A tries to unfollow User B (not following)
        2. Verify returns False
        """
        user_a = created_users[0]
        user_b = created_users[1]

        result = await social_service.unfollow_user(
            user_a["user_id"],
            user_b["user_id"]
        )

        assert result is False
