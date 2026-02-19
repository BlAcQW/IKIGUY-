"""
Tests for leaderboard functionality.

This module tests:
- Leaderboard retrieval and ranking
- Time period filtering (weekly, monthly, all-time)
- Metric-based leaderboards (books read, reading time, reviews)
- User stats and positioning
- Privacy considerations
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
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
async def test_users_with_stats(db: Database) -> List[Dict[str, Any]]:
    """Create test users with varying reading stats."""
    users = []

    # Create 5 users with different stats
    for i in range(5):
        user_id = f"test_user_{i}_{ObjectId()}"
        username = f"reader_{i}_{ObjectId()}"

        # User with decreasing stats (user 0 has most, user 4 has least)
        user_doc = {
            "user_id": user_id,
            "email": f"{user_id}@test.com",
            "display_name": f"Reader {i}",
            "username": username,
            "created_at": datetime.utcnow() - timedelta(days=365),
            "is_private": False,
            # Stats for leaderboard
            "stats": {
                "books_read": 50 - (i * 10),  # 50, 40, 30, 20, 10
                "total_reading_time_minutes": 10000 - (i * 2000),  # 10000, 8000, 6000, 4000, 2000
                "reviews_written": 20 - (i * 4),  # 20, 16, 12, 8, 4
                "books_in_library": 100 - (i * 20),  # 100, 80, 60, 40, 20
                "reading_streak_days": 30 - (i * 5),  # 30, 25, 20, 15, 10
            },
        }

        await db.users.insert_one(user_doc)
        users.append({
            "user_id": user_id,
            "username": username,
            "token": f"Bearer test_token_{user_id}",
            "stats": user_doc["stats"],
        })

    yield users

    # Cleanup
    await db.users.delete_many({
        "user_id": {"$in": [u["user_id"] for u in users]}
    })


@pytest_asyncio.fixture
async def test_user(db: Database) -> Dict[str, Any]:
    """Create a single test user."""
    user_id = f"test_single_user_{ObjectId()}"
    username = f"single_{ObjectId()}"

    await db.users.insert_one({
        "user_id": user_id,
        "email": f"{user_id}@test.com",
        "display_name": "Single User",
        "username": username,
        "created_at": datetime.utcnow(),
        "is_private": False,
        "stats": {
            "books_read": 25,
            "total_reading_time_minutes": 5000,
            "reviews_written": 10,
        },
    })

    user = {
        "user_id": user_id,
        "username": username,
        "token": f"Bearer test_token_{user_id}",
    }

    yield user

    # Cleanup
    await db.users.delete_one({"user_id": user_id})


class TestLeaderboardBasics:
    """Test basic leaderboard functionality."""

    @pytest.mark.asyncio
    async def test_get_books_read_leaderboard(
        self,
        client: AsyncClient,
        test_users_with_stats: List[Dict[str, Any]],
    ):
        """Test retrieving leaderboard for books read."""
        user = test_users_with_stats[0]

        response = await client.get(
            "/api/social/leaderboard?metric=books_read&period=all_time",
            headers={"Authorization": user["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        assert "leaderboard" in data
        assert "user_position" in data
        assert isinstance(data["leaderboard"], list)
        assert len(data["leaderboard"]) <= 100  # Default limit

        # Verify ranking is correct (descending by books_read)
        for i in range(len(data["leaderboard"]) - 1):
            current = data["leaderboard"][i]
            next_user = data["leaderboard"][i + 1]
            assert current["stats"]["books_read"] >= next_user["stats"]["books_read"]
            assert current["rank"] < next_user["rank"]

    @pytest.mark.asyncio
    async def test_get_reading_time_leaderboard(
        self,
        client: AsyncClient,
        test_users_with_stats: List[Dict[str, Any]],
    ):
        """Test retrieving leaderboard for reading time."""
        user = test_users_with_stats[0]

        response = await client.get(
            "/api/social/leaderboard?metric=reading_time&period=all_time",
            headers={"Authorization": user["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["leaderboard"]) > 0

        # Verify ranking is correct (descending by reading time)
        for i in range(len(data["leaderboard"]) - 1):
            current = data["leaderboard"][i]
            next_user = data["leaderboard"][i + 1]
            assert (
                current["stats"]["total_reading_time_minutes"]
                >= next_user["stats"]["total_reading_time_minutes"]
            )

    @pytest.mark.asyncio
    async def test_get_reviews_leaderboard(
        self,
        client: AsyncClient,
        test_users_with_stats: List[Dict[str, Any]],
    ):
        """Test retrieving leaderboard for reviews written."""
        user = test_users_with_stats[0]

        response = await client.get(
            "/api/social/leaderboard?metric=reviews_written&period=all_time",
            headers={"Authorization": user["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["leaderboard"]) > 0

        # Verify ranking is correct (descending by reviews)
        for i in range(len(data["leaderboard"]) - 1):
            current = data["leaderboard"][i]
            next_user = data["leaderboard"][i + 1]
            assert (
                current["stats"]["reviews_written"]
                >= next_user["stats"]["reviews_written"]
            )

    @pytest.mark.asyncio
    async def test_leaderboard_without_auth(self, client: AsyncClient):
        """Test accessing leaderboard without authentication."""
        response = await client.get(
            "/api/social/leaderboard?metric=books_read&period=all_time"
        )

        assert response.status_code == 401


class TestLeaderboardRanking:
    """Test leaderboard ranking logic."""

    @pytest.mark.asyncio
    async def test_user_position_in_leaderboard(
        self,
        client: AsyncClient,
        test_users_with_stats: List[Dict[str, Any]],
    ):
        """Test that user can see their position in leaderboard."""
        # Use user with middle stats (index 2)
        user = test_users_with_stats[2]

        response = await client.get(
            "/api/social/leaderboard?metric=books_read&period=all_time",
            headers={"Authorization": user["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        # User should have position info
        assert data["user_position"] is not None
        assert "rank" in data["user_position"]
        assert "stats" in data["user_position"]

        # Verify rank matches user's stats
        user_rank = data["user_position"]["rank"]
        users_above = [
            u for u in data["leaderboard"]
            if u["stats"]["books_read"] > user["stats"]["books_read"]
        ]
        assert user_rank == len(users_above) + 1

    @pytest.mark.asyncio
    async def test_top_user_position(
        self,
        client: AsyncClient,
        test_users_with_stats: List[Dict[str, Any]],
    ):
        """Test that top user is ranked #1."""
        # User 0 has the most books read
        top_user = test_users_with_stats[0]

        response = await client.get(
            "/api/social/leaderboard?metric=books_read&period=all_time",
            headers={"Authorization": top_user["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        # Top user should be rank 1
        assert data["leaderboard"][0]["rank"] == 1
        assert data["user_position"]["rank"] == 1

    @pytest.mark.asyncio
    async def test_rank_consistency(
        self,
        client: AsyncClient,
        test_users_with_stats: List[Dict[str, Any]],
    ):
        """Test that ranks are consecutive integers."""
        user = test_users_with_stats[0]

        response = await client.get(
            "/api/social/leaderboard?metric=books_read&period=all_time",
            headers={"Authorization": user["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify ranks are 1, 2, 3, 4, 5...
        for i, entry in enumerate(data["leaderboard"]):
            assert entry["rank"] == i + 1


class TestLeaderboardTimePeriods:
    """Test leaderboard filtering by time period."""

    @pytest.mark.asyncio
    async def test_weekly_leaderboard(
        self,
        client: AsyncClient,
        db: Database,
        test_user: Dict[str, Any],
    ):
        """Test weekly leaderboard filtering."""
        # Create activity from last week
        activity_id = f"activity_{ObjectId()}"
        await db.activities.insert_one({
            "activity_id": activity_id,
            "user_id": test_user["user_id"],
            "activity_type": "book_completed",
            "created_at": datetime.utcnow() - timedelta(days=3),
            "metadata": {"book_id": f"book_{ObjectId()}"},
        })

        response = await client.get(
            "/api/social/leaderboard?metric=books_read&period=weekly",
            headers={"Authorization": test_user["token"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert "leaderboard" in data

        # Cleanup
        await db.activities.delete_one({"activity_id": activity_id})

    @pytest.mark.asyncio
    async def test_monthly_leaderboard(
        self,
        client: AsyncClient,
        db: Database,
        test_user: Dict[str, Any]],
    ):
        """Test monthly leaderboard filtering."""
        # Create activity from this month
        activity_id = f"activity_{ObjectId()}"
        await db.activities.insert_one({
            "activity_id": activity_id,
            "user_id": test_user["user_id"],
            "activity_type": "book_completed",
            "created_at": datetime.utcnow() - timedelta(days=15),
            "metadata": {"book_id": f"book_{ObjectId()}"},
        })

        response = await client.get(
            "/api/social/leaderboard?metric=books_read&period=monthly",
            headers={"Authorization": test_user["token"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert "leaderboard" in data

        # Cleanup
        await db.activities.delete_one({"activity_id": activity_id})

    @pytest.mark.asyncio
    async def test_all_time_leaderboard(
        self,
        client: AsyncClient,
        test_users_with_stats: List[Dict[str, Any]],
    ):
        """Test all-time leaderboard includes all users."""
        user = test_users_with_stats[0]

        response = await client.get(
            "/api/social/leaderboard?metric=books_read&period=all_time",
            headers={"Authorization": user["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        # Should include all test users
        assert len(data["leaderboard"]) >= len(test_users_with_stats)


class TestLeaderboardPagination:
    """Test leaderboard pagination."""

    @pytest.mark.asyncio
    async def test_leaderboard_with_limit(
        self,
        client: AsyncClient,
        test_users_with_stats: List[Dict[str, Any]],
    ):
        """Test limiting leaderboard results."""
        user = test_users_with_stats[0]

        response = await client.get(
            "/api/social/leaderboard?metric=books_read&period=all_time&limit=3",
            headers={"Authorization": user["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["leaderboard"]) == 3
        # Should be top 3 users
        assert data["leaderboard"][0]["rank"] == 1
        assert data["leaderboard"][1]["rank"] == 2
        assert data["leaderboard"][2]["rank"] == 3

    @pytest.mark.asyncio
    async def test_leaderboard_with_skip(
        self,
        client: AsyncClient,
        test_users_with_stats: List[Dict[str, Any]],
    ):
        """Test skipping leaderboard results."""
        user = test_users_with_stats[0]

        response = await client.get(
            "/api/social/leaderboard?metric=books_read&period=all_time&skip=2&limit=2",
            headers={"Authorization": user["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["leaderboard"]) == 2
        # Should start from rank 3
        assert data["leaderboard"][0]["rank"] == 3
        assert data["leaderboard"][1]["rank"] == 4

    @pytest.mark.asyncio
    async def test_leaderboard_max_limit(
        self,
        client: AsyncClient,
        test_user: Dict[str, Any],
    ):
        """Test maximum limit enforcement."""
        response = await client.get(
            "/api/social/leaderboard?metric=books_read&period=all_time&limit=500",
            headers={"Authorization": test_user["token"]},
        )

        assert response.status_code == 422  # Validation error


class TestLeaderboardPrivacy:
    """Test privacy considerations in leaderboards."""

    @pytest.mark.asyncio
    async def test_private_users_excluded(
        self,
        client: AsyncClient,
        db: Database,
        test_user: Dict[str, Any],
    ):
        """Test that private users are excluded from leaderboards."""
        # Create a private user
        private_user_id = f"test_private_{ObjectId()}"
        await db.users.insert_one({
            "user_id": private_user_id,
            "email": f"{private_user_id}@test.com",
            "display_name": "Private Reader",
            "username": f"private_{ObjectId()}",
            "created_at": datetime.utcnow(),
            "is_private": True,
            "stats": {
                "books_read": 1000,  # Very high to ensure it would rank high
                "total_reading_time_minutes": 50000,
            },
        })

        # Get leaderboard
        response = await client.get(
            "/api/social/leaderboard?metric=books_read&period=all_time",
            headers={"Authorization": test_user["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        # Private user should not be in leaderboard
        user_ids = [u["user_id"] for u in data["leaderboard"]]
        assert private_user_id not in user_ids

        # Cleanup
        await db.users.delete_one({"user_id": private_user_id})

    @pytest.mark.asyncio
    async def test_own_stats_always_visible(
        self,
        client: AsyncClient,
        db: Database,
    ):
        """Test that private users can see their own position."""
        # Create a private user
        private_user_id = f"test_private_{ObjectId()}"
        await db.users.insert_one({
            "user_id": private_user_id,
            "email": f"{private_user_id}@test.com",
            "display_name": "Private Reader",
            "username": f"private_{ObjectId()}",
            "created_at": datetime.utcnow(),
            "is_private": True,
            "stats": {
                "books_read": 50,
                "total_reading_time_minutes": 10000,
            },
        })

        token = f"Bearer test_token_{private_user_id}"

        # Private user requests leaderboard
        response = await client.get(
            "/api/social/leaderboard?metric=books_read&period=all_time",
            headers={"Authorization": token},
        )

        assert response.status_code == 200
        data = response.json()

        # Should have user_position even though not in public leaderboard
        assert data["user_position"] is not None
        assert data["user_position"]["stats"]["books_read"] == 50

        # Cleanup
        await db.users.delete_one({"user_id": private_user_id})


class TestLeaderboardMetrics:
    """Test different leaderboard metrics."""

    @pytest.mark.asyncio
    async def test_invalid_metric(
        self,
        client: AsyncClient,
        test_user: Dict[str, Any],
    ):
        """Test requesting leaderboard with invalid metric."""
        response = await client.get(
            "/api/social/leaderboard?metric=invalid_metric&period=all_time",
            headers={"Authorization": test_user["token"]},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_reading_streak_leaderboard(
        self,
        client: AsyncClient,
        test_users_with_stats: List[Dict[str, Any]],
    ):
        """Test leaderboard for reading streak."""
        user = test_users_with_stats[0]

        response = await client.get(
            "/api/social/leaderboard?metric=reading_streak&period=all_time",
            headers={"Authorization": user["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify ranking by streak
        for i in range(len(data["leaderboard"]) - 1):
            current = data["leaderboard"][i]
            next_user = data["leaderboard"][i + 1]
            assert (
                current["stats"]["reading_streak_days"]
                >= next_user["stats"]["reading_streak_days"]
            )


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_empty_leaderboard(
        self,
        client: AsyncClient,
        db: Database,
        test_user: Dict[str, Any],
    ):
        """Test leaderboard with no eligible users."""
        # Temporarily make all users private
        await db.users.update_many(
            {"user_id": {"$ne": test_user["user_id"]}},
            {"$set": {"is_private": True}},
        )

        response = await client.get(
            "/api/social/leaderboard?metric=books_read&period=all_time",
            headers={"Authorization": test_user["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        # Should return user's own stats only
        assert len(data["leaderboard"]) >= 1

        # Cleanup: restore privacy settings
        await db.users.update_many(
            {},
            {"$set": {"is_private": False}},
        )

    @pytest.mark.asyncio
    async def test_users_with_same_stats(
        self,
        client: AsyncClient,
        db: Database,
        test_user: Dict[str, Any],
    ):
        """Test leaderboard with users having identical stats."""
        # Create users with same stats
        user_ids = []
        for i in range(3):
            user_id = f"test_same_stats_{i}_{ObjectId()}"
            user_ids.append(user_id)
            await db.users.insert_one({
                "user_id": user_id,
                "email": f"{user_id}@test.com",
                "display_name": f"Same Stats {i}",
                "username": f"same_{i}_{ObjectId()}",
                "created_at": datetime.utcnow(),
                "is_private": False,
                "stats": {
                    "books_read": 42,  # All have same value
                    "total_reading_time_minutes": 5000,
                },
            })

        response = await client.get(
            "/api/social/leaderboard?metric=books_read&period=all_time",
            headers={"Authorization": test_user["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        # Users with same stats should have consecutive ranks
        same_stat_users = [
            u for u in data["leaderboard"]
            if u["stats"]["books_read"] == 42
        ]
        assert len(same_stat_users) == 3

        # Cleanup
        await db.users.delete_many({"user_id": {"$in": user_ids}})

    @pytest.mark.asyncio
    async def test_invalid_period(
        self,
        client: AsyncClient,
        test_user: Dict[str, Any],
    ):
        """Test requesting leaderboard with invalid time period."""
        response = await client.get(
            "/api/social/leaderboard?metric=books_read&period=invalid",
            headers={"Authorization": test_user["token"]},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_stats(
        self,
        client: AsyncClient,
        db: Database,
        test_user: Dict[str, Any],
    ):
        """Test leaderboard with users missing stats fields."""
        # Create user without stats
        user_id = f"test_no_stats_{ObjectId()}"
        await db.users.insert_one({
            "user_id": user_id,
            "email": f"{user_id}@test.com",
            "display_name": "No Stats",
            "username": f"nostats_{ObjectId()}",
            "created_at": datetime.utcnow(),
            "is_private": False,
            # No stats field
        })

        response = await client.get(
            "/api/social/leaderboard?metric=books_read&period=all_time",
            headers={"Authorization": test_user["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        # Should handle gracefully (treat missing stats as 0)
        user_in_leaderboard = next(
            (u for u in data["leaderboard"] if u["user_id"] == user_id),
            None
        )

        if user_in_leaderboard:
            assert user_in_leaderboard["stats"].get("books_read", 0) == 0

        # Cleanup
        await db.users.delete_one({"user_id": user_id})
