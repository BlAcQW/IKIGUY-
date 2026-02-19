"""
Tests for activity feed functionality.

This module tests:
- Activity feed generation and retrieval
- Activity type filtering
- Pagination and sorting
- Privacy and visibility rules
- Activity content validation
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
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
    """Create test users for activity feed tests."""
    users = {}

    # Active user who generates content
    active_user_id = f"test_active_user_{ObjectId()}"
    await db.users.insert_one({
        "user_id": active_user_id,
        "email": f"{active_user_id}@test.com",
        "display_name": "Active Reader",
        "username": f"active_{ObjectId()}",
        "created_at": datetime.utcnow(),
        "is_private": False,
    })
    users["active"] = {
        "user_id": active_user_id,
        "token": f"Bearer test_token_{active_user_id}"
    }

    # Follower user who views feed
    follower_user_id = f"test_follower_user_{ObjectId()}"
    await db.users.insert_one({
        "user_id": follower_user_id,
        "email": f"{follower_user_id}@test.com",
        "display_name": "Follower User",
        "username": f"follower_{ObjectId()}",
        "created_at": datetime.utcnow(),
        "is_private": False,
    })
    users["follower"] = {
        "user_id": follower_user_id,
        "token": f"Bearer test_token_{follower_user_id}"
    }

    # Private user for privacy tests
    private_user_id = f"test_private_user_{ObjectId()}"
    await db.users.insert_one({
        "user_id": private_user_id,
        "email": f"{private_user_id}@test.com",
        "display_name": "Private User",
        "username": f"private_{ObjectId()}",
        "created_at": datetime.utcnow(),
        "is_private": True,
    })
    users["private"] = {
        "user_id": private_user_id,
        "token": f"Bearer test_token_{private_user_id}"
    }

    yield users

    # Cleanup
    await db.users.delete_many({
        "user_id": {
            "$in": [u["user_id"] for u in users.values()]
        }
    })


@pytest_asyncio.fixture
async def test_books(db: Database) -> Dict[str, str]:
    """Create test books."""
    books = {}

    for i in range(3):
        book_id = f"test_book_{ObjectId()}"
        await db.books.insert_one({
            "book_id": book_id,
            "title": f"Test Book {i+1}",
            "author": f"Test Author {i+1}",
            "created_at": datetime.utcnow(),
        })
        books[f"book_{i+1}"] = book_id

    yield books

    # Cleanup
    await db.books.delete_many({
        "book_id": {"$in": list(books.values())}
    })


class TestActivityFeedBasics:
    """Test basic activity feed functionality."""

    @pytest.mark.asyncio
    async def test_get_empty_feed(
        self,
        client: AsyncClient,
        test_users: Dict[str, Dict[str, Any]],
    ):
        """Test retrieving an empty activity feed."""
        follower = test_users["follower"]

        response = await client.get(
            "/api/social/activity-feed",
            headers={"Authorization": follower["token"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert "activities" in data
        assert isinstance(data["activities"], list)
        assert len(data["activities"]) == 0
        assert "total" in data
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_get_feed_with_activities(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_books: Dict[str, str],
    ):
        """Test retrieving activity feed with activities."""
        active = test_users["active"]
        follower = test_users["follower"]
        book_id = test_books["book_1"]

        # Create follow relationship
        await db.followers.insert_one({
            "follower_id": follower["user_id"],
            "following_id": active["user_id"],
            "created_at": datetime.utcnow(),
        })

        # Create activity: Reading progress
        activity_id = f"activity_{ObjectId()}"
        await db.activities.insert_one({
            "activity_id": activity_id,
            "user_id": active["user_id"],
            "activity_type": "reading_progress",
            "book_id": book_id,
            "metadata": {
                "progress": 50,
                "book_title": "Test Book 1",
            },
            "created_at": datetime.utcnow(),
        })

        # Get feed
        response = await client.get(
            "/api/social/activity-feed",
            headers={"Authorization": follower["token"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["activities"]) == 1
        assert data["total"] == 1

        activity = data["activities"][0]
        assert activity["activity_type"] == "reading_progress"
        assert activity["user_id"] == active["user_id"]
        assert activity["book_id"] == book_id
        assert activity["metadata"]["progress"] == 50

        # Cleanup
        await db.followers.delete_many({
            "follower_id": follower["user_id"]
        })
        await db.activities.delete_many({"activity_id": activity_id})

    @pytest.mark.asyncio
    async def test_feed_pagination(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_books: Dict[str, str],
    ):
        """Test activity feed pagination."""
        active = test_users["active"]
        follower = test_users["follower"]
        book_id = test_books["book_1"]

        # Create follow relationship
        await db.followers.insert_one({
            "follower_id": follower["user_id"],
            "following_id": active["user_id"],
            "created_at": datetime.utcnow(),
        })

        # Create 15 activities
        activity_ids = []
        for i in range(15):
            activity_id = f"activity_{ObjectId()}"
            activity_ids.append(activity_id)
            await db.activities.insert_one({
                "activity_id": activity_id,
                "user_id": active["user_id"],
                "activity_type": "reading_progress",
                "book_id": book_id,
                "metadata": {"progress": i * 10},
                "created_at": datetime.utcnow() - timedelta(minutes=i),
            })

        # Get first page (limit 10)
        response = await client.get(
            "/api/social/activity-feed?limit=10",
            headers={"Authorization": follower["token"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["activities"]) == 10
        assert data["total"] == 15

        # Get second page (skip 10)
        response = await client.get(
            "/api/social/activity-feed?skip=10&limit=10",
            headers={"Authorization": follower["token"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["activities"]) == 5
        assert data["total"] == 15

        # Cleanup
        await db.followers.delete_many({
            "follower_id": follower["user_id"]
        })
        await db.activities.delete_many({
            "activity_id": {"$in": activity_ids}
        })

    @pytest.mark.asyncio
    async def test_feed_without_auth(self, client: AsyncClient):
        """Test accessing feed without authentication."""
        response = await client.get("/api/social/activity-feed")

        assert response.status_code == 401


class TestActivityTypes:
    """Test different activity types in feed."""

    @pytest.mark.asyncio
    async def test_filter_by_activity_type(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_books: Dict[str, str],
    ):
        """Test filtering activities by type."""
        active = test_users["active"]
        follower = test_users["follower"]
        book_id = test_books["book_1"]

        # Create follow relationship
        await db.followers.insert_one({
            "follower_id": follower["user_id"],
            "following_id": active["user_id"],
            "created_at": datetime.utcnow(),
        })

        # Create different activity types
        activity_ids = []

        # Reading progress
        activity_id_1 = f"activity_{ObjectId()}"
        activity_ids.append(activity_id_1)
        await db.activities.insert_one({
            "activity_id": activity_id_1,
            "user_id": active["user_id"],
            "activity_type": "reading_progress",
            "book_id": book_id,
            "metadata": {"progress": 50},
            "created_at": datetime.utcnow(),
        })

        # Book review
        activity_id_2 = f"activity_{ObjectId()}"
        activity_ids.append(activity_id_2)
        await db.activities.insert_one({
            "activity_id": activity_id_2,
            "user_id": active["user_id"],
            "activity_type": "book_review",
            "book_id": book_id,
            "metadata": {"rating": 5, "review": "Great book!"},
            "created_at": datetime.utcnow(),
        })

        # Book completed
        activity_id_3 = f"activity_{ObjectId()}"
        activity_ids.append(activity_id_3)
        await db.activities.insert_one({
            "activity_id": activity_id_3,
            "user_id": active["user_id"],
            "activity_type": "book_completed",
            "book_id": book_id,
            "metadata": {"completion_time": "5 days"},
            "created_at": datetime.utcnow(),
        })

        # Filter by reading_progress
        response = await client.get(
            "/api/social/activity-feed?activity_type=reading_progress",
            headers={"Authorization": follower["token"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["activities"]) == 1
        assert data["activities"][0]["activity_type"] == "reading_progress"

        # Filter by book_review
        response = await client.get(
            "/api/social/activity-feed?activity_type=book_review",
            headers={"Authorization": follower["token"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["activities"]) == 1
        assert data["activities"][0]["activity_type"] == "book_review"

        # Cleanup
        await db.followers.delete_many({
            "follower_id": follower["user_id"]
        })
        await db.activities.delete_many({
            "activity_id": {"$in": activity_ids}
        })

    @pytest.mark.asyncio
    async def test_multiple_activity_types(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_books: Dict[str, str],
    ):
        """Test retrieving multiple activity types."""
        active = test_users["active"]
        follower = test_users["follower"]

        # Create follow relationship
        await db.followers.insert_one({
            "follower_id": follower["user_id"],
            "following_id": active["user_id"],
            "created_at": datetime.utcnow(),
        })

        # Create various activities
        activity_ids = []
        activity_types = [
            "reading_progress",
            "book_review",
            "book_completed",
            "book_added_to_library",
            "reading_goal_set",
        ]

        for activity_type in activity_types:
            activity_id = f"activity_{ObjectId()}"
            activity_ids.append(activity_id)
            await db.activities.insert_one({
                "activity_id": activity_id,
                "user_id": active["user_id"],
                "activity_type": activity_type,
                "book_id": test_books["book_1"],
                "metadata": {},
                "created_at": datetime.utcnow(),
            })

        # Get all activities
        response = await client.get(
            "/api/social/activity-feed",
            headers={"Authorization": follower["token"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["activities"]) == len(activity_types)

        # Verify all types are present
        returned_types = {a["activity_type"] for a in data["activities"]}
        assert returned_types == set(activity_types)

        # Cleanup
        await db.followers.delete_many({
            "follower_id": follower["user_id"]
        })
        await db.activities.delete_many({
            "activity_id": {"$in": activity_ids}
        })


class TestActivityPrivacy:
    """Test privacy rules for activity feed."""

    @pytest.mark.asyncio
    async def test_private_user_activities_hidden(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_books: Dict[str, str],
    ):
        """Test that private user activities are not shown to non-followers."""
        private = test_users["private"]
        follower = test_users["follower"]
        book_id = test_books["book_1"]

        # Create activity from private user
        activity_id = f"activity_{ObjectId()}"
        await db.activities.insert_one({
            "activity_id": activity_id,
            "user_id": private["user_id"],
            "activity_type": "reading_progress",
            "book_id": book_id,
            "metadata": {"progress": 50},
            "created_at": datetime.utcnow(),
        })

        # Follower should not see activity (not following private user)
        response = await client.get(
            "/api/social/activity-feed",
            headers={"Authorization": follower["token"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["activities"]) == 0

        # Cleanup
        await db.activities.delete_many({"activity_id": activity_id})

    @pytest.mark.asyncio
    async def test_private_user_activities_visible_to_followers(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_books: Dict[str, str],
    ):
        """Test that private user activities are shown to approved followers."""
        private = test_users["private"]
        follower = test_users["follower"]
        book_id = test_books["book_1"]

        # Create approved follow relationship
        await db.followers.insert_one({
            "follower_id": follower["user_id"],
            "following_id": private["user_id"],
            "created_at": datetime.utcnow(),
        })

        # Create activity from private user
        activity_id = f"activity_{ObjectId()}"
        await db.activities.insert_one({
            "activity_id": activity_id,
            "user_id": private["user_id"],
            "activity_type": "reading_progress",
            "book_id": book_id,
            "metadata": {"progress": 50},
            "created_at": datetime.utcnow(),
        })

        # Follower should see activity
        response = await client.get(
            "/api/social/activity-feed",
            headers={"Authorization": follower["token"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["activities"]) == 1
        assert data["activities"][0]["user_id"] == private["user_id"]

        # Cleanup
        await db.followers.delete_many({
            "follower_id": follower["user_id"]
        })
        await db.activities.delete_many({"activity_id": activity_id})

    @pytest.mark.asyncio
    async def test_own_activities_always_visible(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_books: Dict[str, str],
    ):
        """Test that users can always see their own activities."""
        private = test_users["private"]
        book_id = test_books["book_1"]

        # Create activity from private user
        activity_id = f"activity_{ObjectId()}"
        await db.activities.insert_one({
            "activity_id": activity_id,
            "user_id": private["user_id"],
            "activity_type": "reading_progress",
            "book_id": book_id,
            "metadata": {"progress": 50},
            "created_at": datetime.utcnow(),
        })

        # Private user should see their own activity
        response = await client.get(
            "/api/social/activity-feed",
            headers={"Authorization": private["token"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["activities"]) == 1
        assert data["activities"][0]["user_id"] == private["user_id"]

        # Cleanup
        await db.activities.delete_many({"activity_id": activity_id})


class TestActivitySorting:
    """Test activity feed sorting."""

    @pytest.mark.asyncio
    async def test_activities_sorted_by_time(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_books: Dict[str, str],
    ):
        """Test that activities are sorted by creation time (newest first)."""
        active = test_users["active"]
        follower = test_users["follower"]
        book_id = test_books["book_1"]

        # Create follow relationship
        await db.followers.insert_one({
            "follower_id": follower["user_id"],
            "following_id": active["user_id"],
            "created_at": datetime.utcnow(),
        })

        # Create activities at different times
        activity_ids = []
        timestamps = []

        for i in range(5):
            activity_id = f"activity_{ObjectId()}"
            activity_ids.append(activity_id)

            timestamp = datetime.utcnow() - timedelta(hours=i)
            timestamps.append(timestamp)

            await db.activities.insert_one({
                "activity_id": activity_id,
                "user_id": active["user_id"],
                "activity_type": "reading_progress",
                "book_id": book_id,
                "metadata": {"progress": i * 20},
                "created_at": timestamp,
            })

        # Get feed
        response = await client.get(
            "/api/social/activity-feed",
            headers={"Authorization": follower["token"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["activities"]) == 5

        # Verify sorted by newest first
        for i in range(len(data["activities"]) - 1):
            current_time = datetime.fromisoformat(
                data["activities"][i]["created_at"].replace("Z", "+00:00")
            )
            next_time = datetime.fromisoformat(
                data["activities"][i + 1]["created_at"].replace("Z", "+00:00")
            )
            assert current_time >= next_time

        # Cleanup
        await db.followers.delete_many({
            "follower_id": follower["user_id"]
        })
        await db.activities.delete_many({
            "activity_id": {"$in": activity_ids}
        })


class TestActivityMetadata:
    """Test activity metadata validation and retrieval."""

    @pytest.mark.asyncio
    async def test_activity_with_rich_metadata(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_books: Dict[str, str],
    ):
        """Test activities with complex metadata."""
        active = test_users["active"]
        follower = test_users["follower"]
        book_id = test_books["book_1"]

        # Create follow relationship
        await db.followers.insert_one({
            "follower_id": follower["user_id"],
            "following_id": active["user_id"],
            "created_at": datetime.utcnow(),
        })

        # Create activity with rich metadata
        activity_id = f"activity_{ObjectId()}"
        await db.activities.insert_one({
            "activity_id": activity_id,
            "user_id": active["user_id"],
            "activity_type": "book_review",
            "book_id": book_id,
            "metadata": {
                "rating": 5,
                "review": "An absolutely amazing book!",
                "review_length": 27,
                "tags": ["thriller", "suspense", "must-read"],
                "recommended": True,
            },
            "created_at": datetime.utcnow(),
        })

        # Get feed
        response = await client.get(
            "/api/social/activity-feed",
            headers={"Authorization": follower["token"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["activities"]) == 1

        activity = data["activities"][0]
        assert activity["metadata"]["rating"] == 5
        assert activity["metadata"]["review"] == "An absolutely amazing book!"
        assert activity["metadata"]["tags"] == ["thriller", "suspense", "must-read"]
        assert activity["metadata"]["recommended"] is True

        # Cleanup
        await db.followers.delete_many({
            "follower_id": follower["user_id"]
        })
        await db.activities.delete_many({"activity_id": activity_id})

    @pytest.mark.asyncio
    async def test_activity_with_user_info(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_books: Dict[str, str],
    ):
        """Test that activities include user information."""
        active = test_users["active"]
        follower = test_users["follower"]
        book_id = test_books["book_1"]

        # Create follow relationship
        await db.followers.insert_one({
            "follower_id": follower["user_id"],
            "following_id": active["user_id"],
            "created_at": datetime.utcnow(),
        })

        # Create activity
        activity_id = f"activity_{ObjectId()}"
        await db.activities.insert_one({
            "activity_id": activity_id,
            "user_id": active["user_id"],
            "activity_type": "reading_progress",
            "book_id": book_id,
            "metadata": {"progress": 50},
            "created_at": datetime.utcnow(),
        })

        # Get feed
        response = await client.get(
            "/api/social/activity-feed",
            headers={"Authorization": follower["token"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["activities"]) == 1

        activity = data["activities"][0]
        assert "user_id" in activity
        assert activity["user_id"] == active["user_id"]

        # Cleanup
        await db.followers.delete_many({
            "follower_id": follower["user_id"]
        })
        await db.activities.delete_many({"activity_id": activity_id})


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_feed_with_deleted_book(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
    ):
        """Test activity feed when referenced book is deleted."""
        active = test_users["active"]
        follower = test_users["follower"]
        deleted_book_id = f"deleted_book_{ObjectId()}"

        # Create follow relationship
        await db.followers.insert_one({
            "follower_id": follower["user_id"],
            "following_id": active["user_id"],
            "created_at": datetime.utcnow(),
        })

        # Create activity referencing deleted book
        activity_id = f"activity_{ObjectId()}"
        await db.activities.insert_one({
            "activity_id": activity_id,
            "user_id": active["user_id"],
            "activity_type": "reading_progress",
            "book_id": deleted_book_id,
            "metadata": {"progress": 50},
            "created_at": datetime.utcnow(),
        })

        # Get feed (should handle gracefully)
        response = await client.get(
            "/api/social/activity-feed",
            headers={"Authorization": follower["token"]},
        )

        assert response.status_code == 200
        data = response.json()
        # Activity should still be returned, frontend handles missing book
        assert len(data["activities"]) == 1

        # Cleanup
        await db.followers.delete_many({
            "follower_id": follower["user_id"]
        })
        await db.activities.delete_many({"activity_id": activity_id})

    @pytest.mark.asyncio
    async def test_feed_with_invalid_pagination(
        self,
        client: AsyncClient,
        test_users: Dict[str, Dict[str, Any]],
    ):
        """Test feed with invalid pagination parameters."""
        follower = test_users["follower"]

        # Negative skip
        response = await client.get(
            "/api/social/activity-feed?skip=-1",
            headers={"Authorization": follower["token"]},
        )
        assert response.status_code == 422

        # Negative limit
        response = await client.get(
            "/api/social/activity-feed?limit=-1",
            headers={"Authorization": follower["token"]},
        )
        assert response.status_code == 422

        # Limit too large
        response = await client.get(
            "/api/social/activity-feed?limit=1000",
            headers={"Authorization": follower["token"]},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_feed_with_no_following(
        self,
        client: AsyncClient,
        test_users: Dict[str, Dict[str, Any]],
    ):
        """Test feed when user is not following anyone."""
        follower = test_users["follower"]

        response = await client.get(
            "/api/social/activity-feed",
            headers={"Authorization": follower["token"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["activities"]) == 0
        assert data["total"] == 0
