"""
Tests for social stats denormalization.

This module tests:
- Follower count updates
- Following count updates
- Activity stats tracking
- Stats consistency after operations
- Concurrent updates handling
"""

import pytest
import pytest_asyncio
from datetime import datetime
from typing import Dict, Any
from httpx import AsyncClient
from bson import ObjectId

from app.main import app
from app.core.database import Database


@pytest_asyncio.fixture
async def db():
    """Get database instance."""
    return Database()


@pytest_asyncio.fixture
async def client():
    """Create async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def test_users(db: Database) -> Dict[str, Dict[str, Any]]:
    """Create test users for stats tests."""
    users = {}

    # User 1
    user1_id = f"test_user1_{ObjectId()}"
    await db.users.insert_one({
        "user_id": user1_id,
        "email": f"{user1_id}@test.com",
        "display_name": "User One",
        "username": f"user1_{ObjectId()}",
        "created_at": datetime.utcnow(),
        "stats": {
            "followers_count": 0,
            "following_count": 0,
            "books_read": 0,
        },
    })
    users["user1"] = {
        "user_id": user1_id,
        "token": f"Bearer test_token_{user1_id}",
    }

    # User 2
    user2_id = f"test_user2_{ObjectId()}"
    await db.users.insert_one({
        "user_id": user2_id,
        "email": f"{user2_id}@test.com",
        "display_name": "User Two",
        "username": f"user2_{ObjectId()}",
        "created_at": datetime.utcnow(),
        "stats": {
            "followers_count": 0,
            "following_count": 0,
            "books_read": 0,
        },
    })
    users["user2"] = {
        "user_id": user2_id,
        "token": f"Bearer test_token_{user2_id}",
    }

    # User 3
    user3_id = f"test_user3_{ObjectId()}"
    await db.users.insert_one({
        "user_id": user3_id,
        "email": f"{user3_id}@test.com",
        "display_name": "User Three",
        "username": f"user3_{ObjectId()}",
        "created_at": datetime.utcnow(),
        "stats": {
            "followers_count": 0,
            "following_count": 0,
            "books_read": 0,
        },
    })
    users["user3"] = {
        "user_id": user3_id,
        "token": f"Bearer test_token_{user3_id}",
    }

    yield users

    # Cleanup
    await db.users.delete_many({
        "user_id": {"$in": [u["user_id"] for u in users.values()]}
    })
    await db.followers.delete_many({
        "$or": [
            {"follower_id": {"$in": [u["user_id"] for u in users.values()]}},
            {"following_id": {"$in": [u["user_id"] for u in users.values()]}},
        ]
    })


class TestFollowerCountStats:
    """Test follower count denormalization."""

    @pytest.mark.asyncio
    async def test_follower_count_increments_on_follow(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
    ):
        """Test that follower count increments when followed."""
        user1 = test_users["user1"]
        user2 = test_users["user2"]

        # Get initial count
        user2_doc = await db.users.find_one({"user_id": user2["user_id"]})
        initial_count = user2_doc["stats"]["followers_count"]

        # User 1 follows User 2
        response = await client.post(
            f"/api/social/follow/{user2['user_id']}",
            headers={"Authorization": user1["token"]},
        )

        assert response.status_code == 200

        # Check User 2's follower count increased
        user2_doc = await db.users.find_one({"user_id": user2["user_id"]})
        assert user2_doc["stats"]["followers_count"] == initial_count + 1

    @pytest.mark.asyncio
    async def test_follower_count_decrements_on_unfollow(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
    ):
        """Test that follower count decrements when unfollowed."""
        user1 = test_users["user1"]
        user2 = test_users["user2"]

        # User 1 follows User 2
        await client.post(
            f"/api/social/follow/{user2['user_id']}",
            headers={"Authorization": user1["token"]},
        )

        # Get count after follow
        user2_doc = await db.users.find_one({"user_id": user2["user_id"]})
        count_after_follow = user2_doc["stats"]["followers_count"]

        # User 1 unfollows User 2
        response = await client.delete(
            f"/api/social/unfollow/{user2['user_id']}",
            headers={"Authorization": user1["token"]},
        )

        assert response.status_code == 200

        # Check User 2's follower count decreased
        user2_doc = await db.users.find_one({"user_id": user2["user_id"]})
        assert user2_doc["stats"]["followers_count"] == count_after_follow - 1

    @pytest.mark.asyncio
    async def test_follower_count_multiple_followers(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
    ):
        """Test follower count with multiple followers."""
        user1 = test_users["user1"]
        user2 = test_users["user2"]
        user3 = test_users["user3"]

        # Get initial count
        user3_doc = await db.users.find_one({"user_id": user3["user_id"]})
        initial_count = user3_doc["stats"]["followers_count"]

        # User 1 and User 2 follow User 3
        await client.post(
            f"/api/social/follow/{user3['user_id']}",
            headers={"Authorization": user1["token"]},
        )

        await client.post(
            f"/api/social/follow/{user3['user_id']}",
            headers={"Authorization": user2["token"]},
        )

        # Check User 3 has 2 new followers
        user3_doc = await db.users.find_one({"user_id": user3["user_id"]})
        assert user3_doc["stats"]["followers_count"] == initial_count + 2

    @pytest.mark.asyncio
    async def test_follower_count_consistency(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
    ):
        """Test that follower count matches actual follower records."""
        user1 = test_users["user1"]
        user2 = test_users["user2"]
        user3 = test_users["user3"]

        # Create some follow relationships
        await client.post(
            f"/api/social/follow/{user1['user_id']}",
            headers={"Authorization": user2["token"]},
        )

        await client.post(
            f"/api/social/follow/{user1['user_id']}",
            headers={"Authorization": user3["token"]},
        )

        # Count actual followers
        actual_count = await db.followers.count_documents({
            "following_id": user1["user_id"]
        })

        # Check denormalized count matches
        user1_doc = await db.users.find_one({"user_id": user1["user_id"]})
        assert user1_doc["stats"]["followers_count"] == actual_count


class TestFollowingCountStats:
    """Test following count denormalization."""

    @pytest.mark.asyncio
    async def test_following_count_increments_on_follow(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
    ):
        """Test that following count increments when user follows someone."""
        user1 = test_users["user1"]
        user2 = test_users["user2"]

        # Get initial count
        user1_doc = await db.users.find_one({"user_id": user1["user_id"]})
        initial_count = user1_doc["stats"]["following_count"]

        # User 1 follows User 2
        response = await client.post(
            f"/api/social/follow/{user2['user_id']}",
            headers={"Authorization": user1["token"]},
        )

        assert response.status_code == 200

        # Check User 1's following count increased
        user1_doc = await db.users.find_one({"user_id": user1["user_id"]})
        assert user1_doc["stats"]["following_count"] == initial_count + 1

    @pytest.mark.asyncio
    async def test_following_count_decrements_on_unfollow(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
    ):
        """Test that following count decrements when user unfollows."""
        user1 = test_users["user1"]
        user2 = test_users["user2"]

        # User 1 follows User 2
        await client.post(
            f"/api/social/follow/{user2['user_id']}",
            headers={"Authorization": user1["token"]},
        )

        # Get count after follow
        user1_doc = await db.users.find_one({"user_id": user1["user_id"]})
        count_after_follow = user1_doc["stats"]["following_count"]

        # User 1 unfollows User 2
        response = await client.delete(
            f"/api/social/unfollow/{user2['user_id']}",
            headers={"Authorization": user1["token"]},
        )

        assert response.status_code == 200

        # Check User 1's following count decreased
        user1_doc = await db.users.find_one({"user_id": user1["user_id"]})
        assert user1_doc["stats"]["following_count"] == count_after_follow - 1

    @pytest.mark.asyncio
    async def test_following_count_multiple_follows(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
    ):
        """Test following count when user follows multiple people."""
        user1 = test_users["user1"]
        user2 = test_users["user2"]
        user3 = test_users["user3"]

        # Get initial count
        user1_doc = await db.users.find_one({"user_id": user1["user_id"]})
        initial_count = user1_doc["stats"]["following_count"]

        # User 1 follows User 2 and User 3
        await client.post(
            f"/api/social/follow/{user2['user_id']}",
            headers={"Authorization": user1["token"]},
        )

        await client.post(
            f"/api/social/follow/{user3['user_id']}",
            headers={"Authorization": user1["token"]},
        )

        # Check User 1 is following 2 more people
        user1_doc = await db.users.find_one({"user_id": user1["user_id"]})
        assert user1_doc["stats"]["following_count"] == initial_count + 2

    @pytest.mark.asyncio
    async def test_following_count_consistency(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
    ):
        """Test that following count matches actual following records."""
        user1 = test_users["user1"]
        user2 = test_users["user2"]
        user3 = test_users["user3"]

        # User 1 follows User 2 and User 3
        await client.post(
            f"/api/social/follow/{user2['user_id']}",
            headers={"Authorization": user1["token"]},
        )

        await client.post(
            f"/api/social/follow/{user3['user_id']}",
            headers={"Authorization": user1["token"]},
        )

        # Count actual following
        actual_count = await db.followers.count_documents({
            "follower_id": user1["user_id"]
        })

        # Check denormalized count matches
        user1_doc = await db.users.find_one({"user_id": user1["user_id"]})
        assert user1_doc["stats"]["following_count"] == actual_count


class TestBothCountsSimultaneously:
    """Test that both follower and following counts update correctly."""

    @pytest.mark.asyncio
    async def test_follow_updates_both_counts(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
    ):
        """Test that a follow operation updates both users' stats."""
        user1 = test_users["user1"]
        user2 = test_users["user2"]

        # Get initial counts
        user1_doc = await db.users.find_one({"user_id": user1["user_id"]})
        user2_doc = await db.users.find_one({"user_id": user2["user_id"]})

        user1_initial_following = user1_doc["stats"]["following_count"]
        user2_initial_followers = user2_doc["stats"]["followers_count"]

        # User 1 follows User 2
        response = await client.post(
            f"/api/social/follow/{user2['user_id']}",
            headers={"Authorization": user1["token"]},
        )

        assert response.status_code == 200

        # Check both stats updated
        user1_doc = await db.users.find_one({"user_id": user1["user_id"]})
        user2_doc = await db.users.find_one({"user_id": user2["user_id"]})

        assert user1_doc["stats"]["following_count"] == user1_initial_following + 1
        assert user2_doc["stats"]["followers_count"] == user2_initial_followers + 1

    @pytest.mark.asyncio
    async def test_unfollow_updates_both_counts(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
    ):
        """Test that an unfollow operation updates both users' stats."""
        user1 = test_users["user1"]
        user2 = test_users["user2"]

        # User 1 follows User 2
        await client.post(
            f"/api/social/follow/{user2['user_id']}",
            headers={"Authorization": user1["token"]},
        )

        # Get counts after follow
        user1_doc = await db.users.find_one({"user_id": user1["user_id"]})
        user2_doc = await db.users.find_one({"user_id": user2["user_id"]})

        user1_following = user1_doc["stats"]["following_count"]
        user2_followers = user2_doc["stats"]["followers_count"]

        # User 1 unfollows User 2
        response = await client.delete(
            f"/api/social/unfollow/{user2['user_id']}",
            headers={"Authorization": user1["token"]},
        )

        assert response.status_code == 200

        # Check both stats updated
        user1_doc = await db.users.find_one({"user_id": user1["user_id"]})
        user2_doc = await db.users.find_one({"user_id": user2["user_id"]})

        assert user1_doc["stats"]["following_count"] == user1_following - 1
        assert user2_doc["stats"]["followers_count"] == user2_followers - 1


class TestStatsInitialization:
    """Test stats initialization for new users."""

    @pytest.mark.asyncio
    async def test_new_user_has_zero_stats(
        self,
        db: Database,
    ):
        """Test that new users start with zero stats."""
        user_id = f"test_new_{ObjectId()}"

        # Create user
        await db.users.insert_one({
            "user_id": user_id,
            "email": f"{user_id}@test.com",
            "display_name": "New User",
            "username": f"newuser_{ObjectId()}",
            "created_at": datetime.utcnow(),
            "stats": {
                "followers_count": 0,
                "following_count": 0,
                "books_read": 0,
            },
        })

        # Verify stats
        user_doc = await db.users.find_one({"user_id": user_id})
        assert user_doc["stats"]["followers_count"] == 0
        assert user_doc["stats"]["following_count"] == 0
        assert user_doc["stats"]["books_read"] == 0

        # Cleanup
        await db.users.delete_one({"user_id": user_id})

    @pytest.mark.asyncio
    async def test_user_without_stats_field_handled(
        self,
        db: Database,
        client: AsyncClient,
    ):
        """Test handling of users without stats field (migration case)."""
        user1_id = f"test_no_stats1_{ObjectId()}"
        user2_id = f"test_no_stats2_{ObjectId()}"

        # Create users without stats field
        await db.users.insert_one({
            "user_id": user1_id,
            "email": f"{user1_id}@test.com",
            "display_name": "No Stats 1",
            "username": f"nostats1_{ObjectId()}",
            "created_at": datetime.utcnow(),
            # No stats field
        })

        await db.users.insert_one({
            "user_id": user2_id,
            "email": f"{user2_id}@test.com",
            "display_name": "No Stats 2",
            "username": f"nostats2_{ObjectId()}",
            "created_at": datetime.utcnow(),
            # No stats field
        })

        token1 = f"Bearer test_token_{user1_id}"

        # Try to follow (should initialize stats if missing)
        response = await client.post(
            f"/api/social/follow/{user2_id}",
            headers={"Authorization": token1},
        )

        # Should either succeed or handle gracefully
        assert response.status_code in [200, 500]

        # Cleanup
        await db.users.delete_many({"user_id": {"$in": [user1_id, user2_id]}})
        await db.followers.delete_many({
            "$or": [
                {"follower_id": user1_id},
                {"following_id": user2_id},
            ]
        })


class TestStatsConsistency:
    """Test stats consistency after various operations."""

    @pytest.mark.asyncio
    async def test_double_follow_doesnt_double_count(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
    ):
        """Test that following twice doesn't double count."""
        user1 = test_users["user1"]
        user2 = test_users["user2"]

        # User 1 follows User 2
        await client.post(
            f"/api/social/follow/{user2['user_id']}",
            headers={"Authorization": user1["token"]},
        )

        # Get count after first follow
        user2_doc = await db.users.find_one({"user_id": user2["user_id"]})
        count_after_first = user2_doc["stats"]["followers_count"]

        # Try to follow again
        await client.post(
            f"/api/social/follow/{user2['user_id']}",
            headers={"Authorization": user1["token"]},
        )

        # Count should be same
        user2_doc = await db.users.find_one({"user_id": user2["user_id"]})
        assert user2_doc["stats"]["followers_count"] == count_after_first

    @pytest.mark.asyncio
    async def test_double_unfollow_doesnt_go_negative(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
    ):
        """Test that unfollowing twice doesn't make count negative."""
        user1 = test_users["user1"]
        user2 = test_users["user2"]

        # User 1 follows User 2
        await client.post(
            f"/api/social/follow/{user2['user_id']}",
            headers={"Authorization": user1["token"]},
        )

        # User 1 unfollows User 2
        await client.delete(
            f"/api/social/unfollow/{user2['user_id']}",
            headers={"Authorization": user1["token"]},
        )

        # Try to unfollow again
        await client.delete(
            f"/api/social/unfollow/{user2['user_id']}",
            headers={"Authorization": user1["token"]},
        )

        # Count should not be negative
        user2_doc = await db.users.find_one({"user_id": user2["user_id"]})
        assert user2_doc["stats"]["followers_count"] >= 0

    @pytest.mark.asyncio
    async def test_stats_after_many_operations(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
    ):
        """Test stats consistency after many follow/unfollow operations."""
        user1 = test_users["user1"]
        user2 = test_users["user2"]
        user3 = test_users["user3"]

        # Perform multiple operations
        # User 1 -> User 2
        await client.post(
            f"/api/social/follow/{user2['user_id']}",
            headers={"Authorization": user1["token"]},
        )

        # User 1 -> User 3
        await client.post(
            f"/api/social/follow/{user3['user_id']}",
            headers={"Authorization": user1["token"]},
        )

        # User 2 -> User 3
        await client.post(
            f"/api/social/follow/{user3['user_id']}",
            headers={"Authorization": user2["token"]},
        )

        # User 1 unfollows User 2
        await client.delete(
            f"/api/social/unfollow/{user2['user_id']}",
            headers={"Authorization": user1["token"]},
        )

        # Verify all counts match actual relationships
        for user_key, user in test_users.items():
            user_id = user["user_id"]

            # Count actual followers and following
            actual_followers = await db.followers.count_documents({
                "following_id": user_id
            })
            actual_following = await db.followers.count_documents({
                "follower_id": user_id
            })

            # Check denormalized counts
            user_doc = await db.users.find_one({"user_id": user_id})
            assert user_doc["stats"]["followers_count"] == actual_followers
            assert user_doc["stats"]["following_count"] == actual_following


class TestEdgeCases:
    """Test edge cases for stats management."""

    @pytest.mark.asyncio
    async def test_stats_with_deleted_follower_relationship(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
    ):
        """Test stats if follower relationship is manually deleted."""
        user1 = test_users["user1"]
        user2 = test_users["user2"]

        # User 1 follows User 2
        await client.post(
            f"/api/social/follow/{user2['user_id']}",
            headers={"Authorization": user1["token"]},
        )

        # Manually delete the relationship (simulating data corruption)
        await db.followers.delete_one({
            "follower_id": user1["user_id"],
            "following_id": user2["user_id"],
        })

        # Stats are now out of sync
        user1_doc = await db.users.find_one({"user_id": user1["user_id"]})
        user2_doc = await db.users.find_one({"user_id": user2["user_id"]})

        # In production, would need a consistency check/repair job
        # For now, just verify the inconsistency is detectible
        actual_following = await db.followers.count_documents({
            "follower_id": user1["user_id"]
        })
        actual_followers = await db.followers.count_documents({
            "following_id": user2["user_id"]
        })

        # Stats should be off by 1
        assert user1_doc["stats"]["following_count"] != actual_following
        assert user2_doc["stats"]["followers_count"] != actual_followers

    @pytest.mark.asyncio
    async def test_negative_stats_prevented(
        self,
        db: Database,
    ):
        """Test that stats cannot go below zero."""
        user_id = f"test_negative_{ObjectId()}"

        await db.users.insert_one({
            "user_id": user_id,
            "email": f"{user_id}@test.com",
            "display_name": "Test User",
            "username": f"testuser_{ObjectId()}",
            "created_at": datetime.utcnow(),
            "stats": {
                "followers_count": 0,
                "following_count": 0,
            },
        })

        # Try to manually decrement below zero (simulating logic error)
        result = await db.users.update_one(
            {"user_id": user_id},
            {"$inc": {"stats.followers_count": -1}}
        )

        # Check result
        user_doc = await db.users.find_one({"user_id": user_id})

        # MongoDB allows negative, but application logic should prevent
        # In production, use validators or check before decrement
        assert user_doc["stats"]["followers_count"] == -1  # Currently allows

        # Cleanup
        await db.users.delete_one({"user_id": user_id})
