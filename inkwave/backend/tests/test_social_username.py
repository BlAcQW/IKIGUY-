"""
Tests for username management functionality.

This module tests:
- Username uniqueness validation
- Username format validation
- Username updates
- Username availability checks
- Case sensitivity handling
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
async def test_user(db: Database) -> Dict[str, Any]:
    """Create a test user."""
    user_id = f"test_user_{ObjectId()}"
    username = f"testuser_{ObjectId()}"

    await db.users.insert_one({
        "user_id": user_id,
        "email": f"{user_id}@test.com",
        "display_name": "Test User",
        "username": username,
        "created_at": datetime.utcnow(),
    })

    user = {
        "user_id": user_id,
        "username": username,
        "token": f"Bearer test_token_{user_id}",
    }

    yield user

    # Cleanup
    await db.users.delete_one({"user_id": user_id})


@pytest_asyncio.fixture
async def existing_user(db: Database) -> Dict[str, Any]:
    """Create another user with a taken username."""
    user_id = f"test_existing_{ObjectId()}"
    username = f"taken_username_{ObjectId()}"

    await db.users.insert_one({
        "user_id": user_id,
        "email": f"{user_id}@test.com",
        "display_name": "Existing User",
        "username": username,
        "created_at": datetime.utcnow(),
    })

    user = {
        "user_id": user_id,
        "username": username,
        "token": f"Bearer test_token_{user_id}",
    }

    yield user

    # Cleanup
    await db.users.delete_one({"user_id": user_id})


class TestUsernameAvailability:
    """Test username availability checking."""

    @pytest.mark.asyncio
    async def test_check_available_username(
        self,
        client: AsyncClient,
        test_user: Dict[str, Any],
    ):
        """Test checking an available username."""
        new_username = f"available_{ObjectId()}"

        response = await client.get(
            f"/api/social/username/check?username={new_username}",
            headers={"Authorization": test_user["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        assert "available" in data
        assert data["available"] is True

    @pytest.mark.asyncio
    async def test_check_taken_username(
        self,
        client: AsyncClient,
        test_user: Dict[str, Any],
        existing_user: Dict[str, Any],
    ):
        """Test checking a taken username."""
        response = await client.get(
            f"/api/social/username/check?username={existing_user['username']}",
            headers={"Authorization": test_user["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        assert "available" in data
        assert data["available"] is False

    @pytest.mark.asyncio
    async def test_check_own_username(
        self,
        client: AsyncClient,
        test_user: Dict[str, Any],
    ):
        """Test checking own username (should be considered available)."""
        response = await client.get(
            f"/api/social/username/check?username={test_user['username']}",
            headers={"Authorization": test_user["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        # Own username should be available (can keep it)
        assert data["available"] is True

    @pytest.mark.asyncio
    async def test_check_username_case_insensitive(
        self,
        client: AsyncClient,
        test_user: Dict[str, Any],
        existing_user: Dict[str, Any],
    ):
        """Test that username check is case-insensitive."""
        # Check with different case
        username_upper = existing_user['username'].upper()

        response = await client.get(
            f"/api/social/username/check?username={username_upper}",
            headers={"Authorization": test_user["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        # Should be unavailable even with different case
        assert data["available"] is False

    @pytest.mark.asyncio
    async def test_check_username_without_auth(self, client: AsyncClient):
        """Test checking username without authentication."""
        response = await client.get(
            "/api/social/username/check?username=testuser"
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_check_empty_username(
        self,
        client: AsyncClient,
        test_user: Dict[str, Any],
    ):
        """Test checking empty username."""
        response = await client.get(
            "/api/social/username/check?username=",
            headers={"Authorization": test_user["token"]},
        )

        assert response.status_code == 422


class TestUsernameFormat:
    """Test username format validation."""

    @pytest.mark.asyncio
    async def test_valid_username_formats(
        self,
        client: AsyncClient,
        test_user: Dict[str, Any],
    ):
        """Test various valid username formats."""
        valid_usernames = [
            "user123",
            "user_name",
            "user-name",
            "u",  # Single character
            "a" * 30,  # Max length (assuming 30)
            "User_123-test",  # Mixed
        ]

        for username in valid_usernames:
            response = await client.get(
                f"/api/social/username/check?username={username}",
                headers={"Authorization": test_user["token"]},
            )

            assert response.status_code == 200, f"Failed for username: {username}"

    @pytest.mark.asyncio
    async def test_invalid_username_formats(
        self,
        client: AsyncClient,
        test_user: Dict[str, Any],
    ):
        """Test invalid username formats."""
        invalid_usernames = [
            "user name",  # Space
            "user@name",  # Special char
            "user#name",  # Special char
            "user.name",  # Period
            "a" * 100,  # Too long
            "",  # Empty
            "   ",  # Only spaces
        ]

        for username in invalid_usernames:
            response = await client.get(
                f"/api/social/username/check?username={username}",
                headers={"Authorization": test_user["token"]},
            )

            assert response.status_code == 422, f"Should fail for username: {username}"

    @pytest.mark.asyncio
    async def test_username_with_special_characters(
        self,
        client: AsyncClient,
        test_user: Dict[str, Any],
    ):
        """Test usernames with special characters are rejected."""
        special_chars = ["@", "#", "$", "%", "^", "&", "*", "(", ")", "=", "+"]

        for char in special_chars:
            username = f"user{char}name"
            response = await client.get(
                f"/api/social/username/check?username={username}",
                headers={"Authorization": test_user["token"]},
            )

            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_username_min_length(
        self,
        client: AsyncClient,
        test_user: Dict[str, Any],
    ):
        """Test minimum username length validation."""
        # Assuming minimum is 1 character
        response = await client.get(
            "/api/social/username/check?username=a",
            headers={"Authorization": test_user["token"]},
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_username_max_length(
        self,
        client: AsyncClient,
        test_user: Dict[str, Any],
    ):
        """Test maximum username length validation."""
        # Try very long username
        long_username = "a" * 100

        response = await client.get(
            f"/api/social/username/check?username={long_username}",
            headers={"Authorization": test_user["token"]},
        )

        assert response.status_code == 422


class TestUsernameUpdate:
    """Test updating usernames."""

    @pytest.mark.asyncio
    async def test_update_username_success(
        self,
        client: AsyncClient,
        db: Database,
        test_user: Dict[str, Any],
    ):
        """Test successfully updating username."""
        new_username = f"new_username_{ObjectId()}"

        response = await client.put(
            "/api/social/username",
            headers={"Authorization": test_user["token"]},
            json={"username": new_username},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["username"] == new_username

        # Verify in database
        user_doc = await db.users.find_one({"user_id": test_user["user_id"]})
        assert user_doc["username"] == new_username

    @pytest.mark.asyncio
    async def test_update_to_taken_username(
        self,
        client: AsyncClient,
        test_user: Dict[str, Any],
        existing_user: Dict[str, Any],
    ):
        """Test updating to a username that's already taken."""
        response = await client.put(
            "/api/social/username",
            headers={"Authorization": test_user["token"]},
            json={"username": existing_user["username"]},
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_update_to_same_username(
        self,
        client: AsyncClient,
        test_user: Dict[str, Any],
    ):
        """Test updating to the same username (no change)."""
        response = await client.put(
            "/api/social/username",
            headers={"Authorization": test_user["token"]},
            json={"username": test_user["username"]},
        )

        # Should succeed (no change) or return 200
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_update_username_case_change(
        self,
        client: AsyncClient,
        db: Database,
        test_user: Dict[str, Any],
    ):
        """Test changing only the case of username."""
        new_username = test_user["username"].upper()

        response = await client.put(
            "/api/social/username",
            headers={"Authorization": test_user["token"]},
            json={"username": new_username},
        )

        # Should succeed (same username, different case)
        assert response.status_code == 200

        # Verify case is updated
        user_doc = await db.users.find_one({"user_id": test_user["user_id"]})
        assert user_doc["username"] == new_username

    @pytest.mark.asyncio
    async def test_update_username_invalid_format(
        self,
        client: AsyncClient,
        test_user: Dict[str, Any],
    ):
        """Test updating to invalid username format."""
        invalid_username = "user@name"

        response = await client.put(
            "/api/social/username",
            headers={"Authorization": test_user["token"]},
            json={"username": invalid_username},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_username_without_auth(self, client: AsyncClient):
        """Test updating username without authentication."""
        response = await client.put(
            "/api/social/username",
            json={"username": "newusername"},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_username_empty(
        self,
        client: AsyncClient,
        test_user: Dict[str, Any],
    ):
        """Test updating to empty username."""
        response = await client.put(
            "/api/social/username",
            headers={"Authorization": test_user["token"]},
            json={"username": ""},
        )

        assert response.status_code == 422


class TestUsernameHistory:
    """Test username change history (if implemented)."""

    @pytest.mark.asyncio
    async def test_username_changes_tracked(
        self,
        client: AsyncClient,
        db: Database,
        test_user: Dict[str, Any],
    ):
        """Test that username changes are tracked."""
        old_username = test_user["username"]
        new_username = f"new_{ObjectId()}"

        # Update username
        response = await client.put(
            "/api/social/username",
            headers={"Authorization": test_user["token"]},
            json={"username": new_username},
        )

        assert response.status_code == 200

        # Check if history exists (optional feature)
        user_doc = await db.users.find_one({"user_id": test_user["user_id"]})

        if "username_history" in user_doc:
            # If tracking is implemented
            assert old_username in [h["username"] for h in user_doc["username_history"]]

    @pytest.mark.asyncio
    async def test_multiple_username_changes(
        self,
        client: AsyncClient,
        db: Database,
        test_user: Dict[str, Any],
    ):
        """Test multiple consecutive username changes."""
        usernames = [f"username_{i}_{ObjectId()}" for i in range(3)]

        for new_username in usernames:
            response = await client.put(
                "/api/social/username",
                headers={"Authorization": test_user["token"]},
                json={"username": new_username},
            )

            assert response.status_code == 200

        # Verify final username
        user_doc = await db.users.find_one({"user_id": test_user["user_id"]})
        assert user_doc["username"] == usernames[-1]


class TestUsernameLookup:
    """Test looking up users by username."""

    @pytest.mark.asyncio
    async def test_lookup_by_username(
        self,
        client: AsyncClient,
        test_user: Dict[str, Any],
        existing_user: Dict[str, Any],
    ):
        """Test finding a user by their username."""
        response = await client.get(
            f"/api/social/users/by-username/{existing_user['username']}",
            headers={"Authorization": test_user["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["user_id"] == existing_user["user_id"]
        assert data["username"] == existing_user["username"]

    @pytest.mark.asyncio
    async def test_lookup_nonexistent_username(
        self,
        client: AsyncClient,
        test_user: Dict[str, Any],
    ):
        """Test looking up a username that doesn't exist."""
        fake_username = f"nonexistent_{ObjectId()}"

        response = await client.get(
            f"/api/social/users/by-username/{fake_username}",
            headers={"Authorization": test_user["token"]},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_lookup_case_insensitive(
        self,
        client: AsyncClient,
        test_user: Dict[str, Any],
        existing_user: Dict[str, Any],
    ):
        """Test that username lookup is case-insensitive."""
        username_upper = existing_user["username"].upper()

        response = await client.get(
            f"/api/social/users/by-username/{username_upper}",
            headers={"Authorization": test_user["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["user_id"] == existing_user["user_id"]

    @pytest.mark.asyncio
    async def test_lookup_without_auth(
        self,
        client: AsyncClient,
        existing_user: Dict[str, Any],
    ):
        """Test username lookup without authentication."""
        response = await client.get(
            f"/api/social/users/by-username/{existing_user['username']}"
        )

        assert response.status_code == 401


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_concurrent_username_changes(
        self,
        client: AsyncClient,
        db: Database,
        test_user: Dict[str, Any],
        existing_user: Dict[str, Any],
    ):
        """Test handling of concurrent username updates."""
        target_username = f"target_{ObjectId()}"

        # Both users try to claim the same username
        # (In practice, database constraints should prevent this)

        # First user updates
        response1 = await client.put(
            "/api/social/username",
            headers={"Authorization": test_user["token"]},
            json={"username": target_username},
        )

        # Second user tries same username
        response2 = await client.put(
            "/api/social/username",
            headers={"Authorization": existing_user["token"]},
            json={"username": target_username},
        )

        # One should succeed, one should fail
        assert (response1.status_code == 200 and response2.status_code == 400) or \
               (response1.status_code == 400 and response2.status_code == 200)

    @pytest.mark.asyncio
    async def test_username_with_leading_trailing_spaces(
        self,
        client: AsyncClient,
        test_user: Dict[str, Any],
    ):
        """Test usernames with leading/trailing spaces are trimmed or rejected."""
        response = await client.put(
            "/api/social/username",
            headers={"Authorization": test_user["token"]},
            json={"username": "  username  "},
        )

        # Should either trim and succeed, or reject
        assert response.status_code in [200, 422]

        if response.status_code == 200:
            # If trimmed, verify it's stored without spaces
            data = response.json()
            assert data["username"] == "username"

    @pytest.mark.asyncio
    async def test_username_with_unicode_characters(
        self,
        client: AsyncClient,
        test_user: Dict[str, Any],
    ):
        """Test usernames with unicode characters."""
        unicode_usernames = [
            "usér",  # Accented character
            "用户",  # Chinese characters
            "юзер",  # Cyrillic
        ]

        for username in unicode_usernames:
            response = await client.get(
                f"/api/social/username/check?username={username}",
                headers={"Authorization": test_user["token"]},
            )

            # Depends on policy: either accept or reject unicode
            assert response.status_code in [200, 422]

    @pytest.mark.asyncio
    async def test_username_sql_injection_attempt(
        self,
        client: AsyncClient,
        test_user: Dict[str, Any],
    ):
        """Test that SQL injection attempts are handled safely."""
        malicious_username = "admin' OR '1'='1"

        response = await client.get(
            f"/api/social/username/check?username={malicious_username}",
            headers={"Authorization": test_user["token"]},
        )

        # Should be rejected or handled safely (MongoDB isn't SQL but test anyway)
        assert response.status_code in [200, 422]

    @pytest.mark.asyncio
    async def test_username_reserved_words(
        self,
        client: AsyncClient,
        test_user: Dict[str, Any],
    ):
        """Test that reserved words are handled."""
        reserved = [
            "admin",
            "root",
            "system",
            "api",
            "inkwave",
        ]

        for username in reserved:
            response = await client.get(
                f"/api/social/username/check?username={username}",
                headers={"Authorization": test_user["token"]},
            )

            # Implementation may or may not reserve these
            # Just verify it responds correctly
            assert response.status_code in [200, 422]
