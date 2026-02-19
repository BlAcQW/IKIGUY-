"""
Tests for user discovery functionality.

This module tests:
- User search by username and display name
- Suggested users (popular readers, similar tastes)
- Search filtering and pagination
- Privacy considerations in discovery
- Profile viewing
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
async def test_users(db: Database) -> List[Dict[str, Any]]:
    """Create diverse test users for discovery tests."""
    users = []

    # User 1: Popular reader with many followers
    user1_id = f"test_popular_user_{ObjectId()}"
    await db.users.insert_one({
        "user_id": user1_id,
        "email": f"{user1_id}@test.com",
        "display_name": "Popular Reader",
        "username": f"popular_reader_{ObjectId()}",
        "bio": "I love reading fantasy and sci-fi books!",
        "created_at": datetime.utcnow() - timedelta(days=365),
        "is_private": False,
        "stats": {
            "followers_count": 1000,
            "following_count": 50,
            "books_read": 200,
        },
    })
    users.append({
        "user_id": user1_id,
        "type": "popular",
        "token": f"Bearer test_token_{user1_id}",
    })

    # User 2: Private user
    user2_id = f"test_private_user_{ObjectId()}"
    await db.users.insert_one({
        "user_id": user2_id,
        "email": f"{user2_id}@test.com",
        "display_name": "Private Reader",
        "username": f"private_reader_{ObjectId()}",
        "bio": "I read in private.",
        "created_at": datetime.utcnow(),
        "is_private": True,
        "stats": {
            "followers_count": 10,
            "following_count": 5,
            "books_read": 50,
        },
    })
    users.append({
        "user_id": user2_id,
        "type": "private",
        "token": f"Bearer test_token_{user2_id}",
    })

    # User 3: New user
    user3_id = f"test_new_user_{ObjectId()}"
    await db.users.insert_one({
        "user_id": user3_id,
        "email": f"{user3_id}@test.com",
        "display_name": "New Reader",
        "username": f"new_reader_{ObjectId()}",
        "bio": "Just started my reading journey!",
        "created_at": datetime.utcnow() - timedelta(days=7),
        "is_private": False,
        "stats": {
            "followers_count": 0,
            "following_count": 0,
            "books_read": 2,
        },
    })
    users.append({
        "user_id": user3_id,
        "type": "new",
        "token": f"Bearer test_token_{user3_id}",
    })

    # User 4: Active reader with specific tastes
    user4_id = f"test_active_user_{ObjectId()}"
    await db.users.insert_one({
        "user_id": user4_id,
        "email": f"{user4_id}@test.com",
        "display_name": "Active Reader",
        "username": f"active_reader_{ObjectId()}",
        "bio": "Mystery and thriller enthusiast",
        "created_at": datetime.utcnow() - timedelta(days=180),
        "is_private": False,
        "stats": {
            "followers_count": 100,
            "following_count": 80,
            "books_read": 75,
        },
    })
    users.append({
        "user_id": user4_id,
        "type": "active",
        "token": f"Bearer test_token_{user4_id}",
    })

    # User 5: Searchable by unique username
    user5_id = f"test_unique_user_{ObjectId()}"
    unique_username = f"bookworm_2025_{ObjectId()}"
    await db.users.insert_one({
        "user_id": user5_id,
        "email": f"{user5_id}@test.com",
        "display_name": "Unique Bookworm",
        "username": unique_username,
        "bio": "Reading everything I can get my hands on!",
        "created_at": datetime.utcnow(),
        "is_private": False,
        "stats": {
            "followers_count": 25,
            "following_count": 30,
            "books_read": 40,
        },
    })
    users.append({
        "user_id": user5_id,
        "type": "unique",
        "username": unique_username,
        "token": f"Bearer test_token_{user5_id}",
    })

    yield users

    # Cleanup
    await db.users.delete_many({
        "user_id": {"$in": [u["user_id"] for u in users]}
    })


@pytest_asyncio.fixture
async def searcher_user(db: Database) -> Dict[str, Any]:
    """Create a user who will search for others."""
    user_id = f"test_searcher_{ObjectId()}"
    await db.users.insert_one({
        "user_id": user_id,
        "email": f"{user_id}@test.com",
        "display_name": "Searcher",
        "username": f"searcher_{ObjectId()}",
        "created_at": datetime.utcnow(),
        "is_private": False,
        "stats": {
            "followers_count": 10,
            "following_count": 15,
            "books_read": 30,
        },
    })

    user = {
        "user_id": user_id,
        "token": f"Bearer test_token_{user_id}",
    }

    yield user

    # Cleanup
    await db.users.delete_one({"user_id": user_id})


class TestUserSearch:
    """Test user search functionality."""

    @pytest.mark.asyncio
    async def test_search_by_username(
        self,
        client: AsyncClient,
        searcher_user: Dict[str, Any],
        test_users: List[Dict[str, Any]],
    ):
        """Test searching users by username."""
        unique_user = next(u for u in test_users if u["type"] == "unique")
        search_term = "bookworm"

        response = await client.get(
            f"/api/social/users/search?query={search_term}",
            headers={"Authorization": searcher_user["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        assert "users" in data
        assert isinstance(data["users"], list)
        assert len(data["users"]) > 0

        # Verify unique user is in results
        found = any(u["user_id"] == unique_user["user_id"] for u in data["users"])
        assert found

    @pytest.mark.asyncio
    async def test_search_by_display_name(
        self,
        client: AsyncClient,
        searcher_user: Dict[str, Any],
        test_users: List[Dict[str, Any]],
    ):
        """Test searching users by display name."""
        search_term = "Popular"

        response = await client.get(
            f"/api/social/users/search?query={search_term}",
            headers={"Authorization": searcher_user["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        # Should find "Popular Reader"
        found = any("Popular" in u["display_name"] for u in data["users"])
        assert found

    @pytest.mark.asyncio
    async def test_search_case_insensitive(
        self,
        client: AsyncClient,
        searcher_user: Dict[str, Any],
        test_users: List[Dict[str, Any]],
    ):
        """Test that search is case-insensitive."""
        # Search with lowercase
        response1 = await client.get(
            "/api/social/users/search?query=popular",
            headers={"Authorization": searcher_user["token"]},
        )

        # Search with uppercase
        response2 = await client.get(
            "/api/social/users/search?query=POPULAR",
            headers={"Authorization": searcher_user["token"]},
        )

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Both should return same results
        users1 = {u["user_id"] for u in response1.json()["users"]}
        users2 = {u["user_id"] for u in response2.json()["users"]}
        assert users1 == users2

    @pytest.mark.asyncio
    async def test_search_partial_match(
        self,
        client: AsyncClient,
        searcher_user: Dict[str, Any],
        test_users: List[Dict[str, Any]],
    ):
        """Test partial matching in search."""
        # Search for "reader" should match multiple users
        response = await client.get(
            "/api/social/users/search?query=reader",
            headers={"Authorization": searcher_user["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        # Should match "Popular Reader", "Private Reader", "New Reader", etc.
        assert len(data["users"]) >= 3

    @pytest.mark.asyncio
    async def test_search_empty_query(
        self,
        client: AsyncClient,
        searcher_user: Dict[str, Any],
    ):
        """Test search with empty query."""
        response = await client.get(
            "/api/social/users/search?query=",
            headers={"Authorization": searcher_user["token"]},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_search_no_results(
        self,
        client: AsyncClient,
        searcher_user: Dict[str, Any],
    ):
        """Test search with no matching results."""
        response = await client.get(
            "/api/social/users/search?query=nonexistentuser123456",
            headers={"Authorization": searcher_user["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["users"]) == 0

    @pytest.mark.asyncio
    async def test_search_without_auth(self, client: AsyncClient):
        """Test search without authentication."""
        response = await client.get("/api/social/users/search?query=test")

        assert response.status_code == 401


class TestSearchPagination:
    """Test search pagination."""

    @pytest.mark.asyncio
    async def test_search_with_limit(
        self,
        client: AsyncClient,
        searcher_user: Dict[str, Any],
        test_users: List[Dict[str, Any]],
    ):
        """Test limiting search results."""
        response = await client.get(
            "/api/social/users/search?query=reader&limit=2",
            headers={"Authorization": searcher_user["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["users"]) <= 2

    @pytest.mark.asyncio
    async def test_search_with_skip(
        self,
        client: AsyncClient,
        searcher_user: Dict[str, Any],
        test_users: List[Dict[str, Any]],
    ):
        """Test skipping search results."""
        # Get first page
        response1 = await client.get(
            "/api/social/users/search?query=reader&limit=2",
            headers={"Authorization": searcher_user["token"]},
        )

        # Get second page
        response2 = await client.get(
            "/api/social/users/search?query=reader&limit=2&skip=2",
            headers={"Authorization": searcher_user["token"]},
        )

        assert response1.status_code == 200
        assert response2.status_code == 200

        users1 = {u["user_id"] for u in response1.json()["users"]}
        users2 = {u["user_id"] for u in response2.json()["users"]}

        # No overlap between pages
        assert len(users1.intersection(users2)) == 0

    @pytest.mark.asyncio
    async def test_search_max_limit(
        self,
        client: AsyncClient,
        searcher_user: Dict[str, Any],
    ):
        """Test maximum limit enforcement."""
        response = await client.get(
            "/api/social/users/search?query=reader&limit=500",
            headers={"Authorization": searcher_user["token"]},
        )

        assert response.status_code == 422


class TestSuggestedUsers:
    """Test suggested users functionality."""

    @pytest.mark.asyncio
    async def test_get_suggested_users(
        self,
        client: AsyncClient,
        searcher_user: Dict[str, Any],
        test_users: List[Dict[str, Any]],
    ):
        """Test retrieving suggested users."""
        response = await client.get(
            "/api/social/users/suggested",
            headers={"Authorization": searcher_user["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        assert "users" in data
        assert isinstance(data["users"], list)

    @pytest.mark.asyncio
    async def test_suggested_users_exclude_already_following(
        self,
        client: AsyncClient,
        db: Database,
        searcher_user: Dict[str, Any],
        test_users: List[Dict[str, Any]],
    ):
        """Test that suggested users excludes users already following."""
        popular_user = next(u for u in test_users if u["type"] == "popular")

        # Create follow relationship
        await db.followers.insert_one({
            "follower_id": searcher_user["user_id"],
            "following_id": popular_user["user_id"],
            "created_at": datetime.utcnow(),
        })

        response = await client.get(
            "/api/social/users/suggested",
            headers={"Authorization": searcher_user["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        # Popular user should not be in suggestions
        user_ids = [u["user_id"] for u in data["users"]]
        assert popular_user["user_id"] not in user_ids

        # Cleanup
        await db.followers.delete_one({
            "follower_id": searcher_user["user_id"],
            "following_id": popular_user["user_id"],
        })

    @pytest.mark.asyncio
    async def test_suggested_users_exclude_self(
        self,
        client: AsyncClient,
        searcher_user: Dict[str, Any],
    ):
        """Test that user is not suggested to themselves."""
        response = await client.get(
            "/api/social/users/suggested",
            headers={"Authorization": searcher_user["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        # Self should not be in suggestions
        user_ids = [u["user_id"] for u in data["users"]]
        assert searcher_user["user_id"] not in user_ids

    @pytest.mark.asyncio
    async def test_suggested_users_prioritize_popular(
        self,
        client: AsyncClient,
        searcher_user: Dict[str, Any],
        test_users: List[Dict[str, Any]],
    ):
        """Test that popular users are prioritized in suggestions."""
        response = await client.get(
            "/api/social/users/suggested?limit=10",
            headers={"Authorization": searcher_user["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        if len(data["users"]) > 0:
            # First user should have higher followers than last user
            first_followers = data["users"][0]["stats"]["followers_count"]
            last_followers = data["users"][-1]["stats"]["followers_count"]
            assert first_followers >= last_followers

    @pytest.mark.asyncio
    async def test_suggested_users_without_auth(self, client: AsyncClient):
        """Test suggested users without authentication."""
        response = await client.get("/api/social/users/suggested")

        assert response.status_code == 401


class TestUserProfile:
    """Test user profile viewing."""

    @pytest.mark.asyncio
    async def test_get_user_profile(
        self,
        client: AsyncClient,
        searcher_user: Dict[str, Any],
        test_users: List[Dict[str, Any]],
    ):
        """Test retrieving a user's profile."""
        popular_user = next(u for u in test_users if u["type"] == "popular")

        response = await client.get(
            f"/api/social/users/{popular_user['user_id']}",
            headers={"Authorization": searcher_user["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["user_id"] == popular_user["user_id"]
        assert "display_name" in data
        assert "username" in data
        assert "bio" in data
        assert "stats" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_get_private_profile_without_following(
        self,
        client: AsyncClient,
        searcher_user: Dict[str, Any],
        test_users: List[Dict[str, Any]],
    ):
        """Test retrieving private user profile without following."""
        private_user = next(u for u in test_users if u["type"] == "private")

        response = await client.get(
            f"/api/social/users/{private_user['user_id']}",
            headers={"Authorization": searcher_user["token"]},
        )

        # Should return limited info or 403
        assert response.status_code in [200, 403]

        if response.status_code == 200:
            data = response.json()
            # Profile visible but limited
            assert "user_id" in data
            assert "display_name" in data

    @pytest.mark.asyncio
    async def test_get_private_profile_with_following(
        self,
        client: AsyncClient,
        db: Database,
        searcher_user: Dict[str, Any],
        test_users: List[Dict[str, Any]],
    ):
        """Test retrieving private user profile when following."""
        private_user = next(u for u in test_users if u["type"] == "private")

        # Create follow relationship
        await db.followers.insert_one({
            "follower_id": searcher_user["user_id"],
            "following_id": private_user["user_id"],
            "created_at": datetime.utcnow(),
        })

        response = await client.get(
            f"/api/social/users/{private_user['user_id']}",
            headers={"Authorization": searcher_user["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        # Full profile should be visible
        assert data["user_id"] == private_user["user_id"]
        assert "stats" in data

        # Cleanup
        await db.followers.delete_one({
            "follower_id": searcher_user["user_id"],
            "following_id": private_user["user_id"],
        })

    @pytest.mark.asyncio
    async def test_get_own_profile(
        self,
        client: AsyncClient,
        searcher_user: Dict[str, Any],
    ):
        """Test retrieving own profile."""
        response = await client.get(
            f"/api/social/users/{searcher_user['user_id']}",
            headers={"Authorization": searcher_user["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["user_id"] == searcher_user["user_id"]
        # Own profile should always be fully visible
        assert "stats" in data
        assert "email" in data

    @pytest.mark.asyncio
    async def test_get_nonexistent_profile(
        self,
        client: AsyncClient,
        searcher_user: Dict[str, Any],
    ):
        """Test retrieving nonexistent user profile."""
        fake_user_id = f"fake_user_{ObjectId()}"

        response = await client.get(
            f"/api/social/users/{fake_user_id}",
            headers={"Authorization": searcher_user["token"]},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_profile_without_auth(
        self,
        client: AsyncClient,
        test_users: List[Dict[str, Any]],
    ):
        """Test retrieving profile without authentication."""
        popular_user = next(u for u in test_users if u["type"] == "popular")

        response = await client.get(
            f"/api/social/users/{popular_user['user_id']}"
        )

        assert response.status_code == 401


class TestSearchPrivacy:
    """Test privacy considerations in search."""

    @pytest.mark.asyncio
    async def test_search_includes_private_users(
        self,
        client: AsyncClient,
        searcher_user: Dict[str, Any],
        test_users: List[Dict[str, Any]],
    ):
        """Test that private users appear in search results."""
        response = await client.get(
            "/api/social/users/search?query=private",
            headers={"Authorization": searcher_user["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        # Private users should be searchable (but profiles may be limited)
        private_user = next(u for u in test_users if u["type"] == "private")
        found = any(u["user_id"] == private_user["user_id"] for u in data["users"])
        assert found

    @pytest.mark.asyncio
    async def test_suggested_excludes_private_users(
        self,
        client: AsyncClient,
        searcher_user: Dict[str, Any],
        test_users: List[Dict[str, Any]],
    ):
        """Test that private users are not in suggestions."""
        response = await client.get(
            "/api/social/users/suggested",
            headers={"Authorization": searcher_user["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        # Private users should not be suggested
        private_user = next(u for u in test_users if u["type"] == "private")
        user_ids = [u["user_id"] for u in data["users"]]
        assert private_user["user_id"] not in user_ids


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_search_with_special_characters(
        self,
        client: AsyncClient,
        searcher_user: Dict[str, Any],
    ):
        """Test search with special characters."""
        response = await client.get(
            "/api/social/users/search?query=@#$%",
            headers={"Authorization": searcher_user["token"]},
        )

        assert response.status_code == 200
        data = response.json()
        # Should handle gracefully
        assert isinstance(data["users"], list)

    @pytest.mark.asyncio
    async def test_search_very_long_query(
        self,
        client: AsyncClient,
        searcher_user: Dict[str, Any],
    ):
        """Test search with very long query string."""
        long_query = "a" * 1000

        response = await client.get(
            f"/api/social/users/search?query={long_query}",
            headers={"Authorization": searcher_user["token"]},
        )

        # Should either validate or handle gracefully
        assert response.status_code in [200, 422]

    @pytest.mark.asyncio
    async def test_profile_stats_structure(
        self,
        client: AsyncClient,
        searcher_user: Dict[str, Any],
        test_users: List[Dict[str, Any]],
    ):
        """Test that profile stats have correct structure."""
        popular_user = next(u for u in test_users if u["type"] == "popular")

        response = await client.get(
            f"/api/social/users/{popular_user['user_id']}",
            headers={"Authorization": searcher_user["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify stats structure
        assert "stats" in data
        stats = data["stats"]
        assert "followers_count" in stats
        assert "following_count" in stats
        assert "books_read" in stats
        assert isinstance(stats["followers_count"], int)
        assert isinstance(stats["following_count"], int)
