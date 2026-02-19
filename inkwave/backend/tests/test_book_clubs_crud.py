"""
Tests for book clubs CRUD operations.

This module tests:
- Creating book clubs
- Reading/listing book clubs
- Updating book clubs
- Deleting book clubs
- Club settings and visibility
- Access control
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
    await db.users.insert_one({
        "user_id": user_id,
        "email": f"{user_id}@test.com",
        "display_name": "Test User",
        "username": f"testuser_{ObjectId()}",
        "created_at": datetime.utcnow(),
    })

    user = {
        "user_id": user_id,
        "token": f"Bearer test_token_{user_id}",
    }

    yield user

    # Cleanup
    await db.users.delete_one({"user_id": user_id})


@pytest_asyncio.fixture
async def test_book(db: Database) -> Dict[str, Any]:
    """Create a test book."""
    book_id = f"test_book_{ObjectId()}"
    await db.books.insert_one({
        "book_id": book_id,
        "title": "Test Book for Club",
        "author": "Test Author",
        "created_at": datetime.utcnow(),
    })

    book = {"book_id": book_id}

    yield book

    # Cleanup
    await db.books.delete_one({"book_id": book_id})


class TestCreateClub:
    """Test creating book clubs."""

    @pytest.mark.asyncio
    async def test_create_public_club(
        self,
        client: AsyncClient,
        db: Database,
        test_user: Dict[str, Any],
        test_book: Dict[str, Any],
    ):
        """Test creating a public book club."""
        response = await client.post(
            "/api/book-clubs",
            headers={"Authorization": test_user["token"]},
            json={
                "name": "Test Public Club",
                "book_id": test_book["book_id"],
                "description": "A club for testing",
                "visibility": "public",
                "require_approval": False,
            },
        )

        assert response.status_code == 201
        data = response.json()

        assert "club_id" in data
        assert data["name"] == "Test Public Club"
        assert data["book_id"] == test_book["book_id"]
        assert data["visibility"] == "public"
        assert data["creator_id"] == test_user["user_id"]
        assert data["stats"]["member_count"] == 1  # Creator is auto-member

        # Verify in database
        club_doc = await db.book_clubs.find_one({"club_id": data["club_id"]})
        assert club_doc is not None
        assert club_doc["name"] == "Test Public Club"

        # Cleanup
        await db.book_clubs.delete_one({"club_id": data["club_id"]})
        await db.club_members.delete_many({"club_id": data["club_id"]})

    @pytest.mark.asyncio
    async def test_create_private_club(
        self,
        client: AsyncClient,
        db: Database,
        test_user: Dict[str, Any],
        test_book: Dict[str, Any],
    ):
        """Test creating a private book club."""
        response = await client.post(
            "/api/book-clubs",
            headers={"Authorization": test_user["token"]},
            json={
                "name": "Test Private Club",
                "book_id": test_book["book_id"],
                "description": "Private club for friends",
                "visibility": "private",
                "require_approval": True,
            },
        )

        assert response.status_code == 201
        data = response.json()

        assert data["visibility"] == "private"
        assert data["settings"]["require_approval"] is True

        # Cleanup
        await db.book_clubs.delete_one({"club_id": data["club_id"]})
        await db.club_members.delete_many({"club_id": data["club_id"]})

    @pytest.mark.asyncio
    async def test_create_followers_only_club(
        self,
        client: AsyncClient,
        db: Database,
        test_user: Dict[str, Any],
        test_book: Dict[str, Any],
    ):
        """Test creating a followers-only book club."""
        response = await client.post(
            "/api/book-clubs",
            headers={"Authorization": test_user["token"]},
            json={
                "name": "Followers Only Club",
                "book_id": test_book["book_id"],
                "description": "For my followers",
                "visibility": "followers_only",
                "require_approval": False,
            },
        )

        assert response.status_code == 201
        data = response.json()

        assert data["visibility"] == "followers_only"

        # Cleanup
        await db.book_clubs.delete_one({"club_id": data["club_id"]})
        await db.club_members.delete_many({"club_id": data["club_id"]})

    @pytest.mark.asyncio
    async def test_create_club_without_auth(
        self,
        client: AsyncClient,
        test_book: Dict[str, Any],
    ):
        """Test creating club without authentication."""
        response = await client.post(
            "/api/book-clubs",
            json={
                "name": "Test Club",
                "book_id": test_book["book_id"],
                "visibility": "public",
            },
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_club_with_invalid_book(
        self,
        client: AsyncClient,
        test_user: Dict[str, Any],
    ):
        """Test creating club with nonexistent book."""
        fake_book_id = f"fake_book_{ObjectId()}"

        response = await client.post(
            "/api/book-clubs",
            headers={"Authorization": test_user["token"]},
            json={
                "name": "Test Club",
                "book_id": fake_book_id,
                "visibility": "public",
            },
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_club_missing_required_fields(
        self,
        client: AsyncClient,
        test_user: Dict[str, Any],
    ):
        """Test creating club with missing required fields."""
        response = await client.post(
            "/api/book-clubs",
            headers={"Authorization": test_user["token"]},
            json={
                "name": "Test Club",
                # Missing book_id
            },
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_creator_auto_added_as_member(
        self,
        client: AsyncClient,
        db: Database,
        test_user: Dict[str, Any],
        test_book: Dict[str, Any],
    ):
        """Test that creator is automatically added as member."""
        response = await client.post(
            "/api/book-clubs",
            headers={"Authorization": test_user["token"]},
            json={
                "name": "Test Club",
                "book_id": test_book["book_id"],
                "visibility": "public",
            },
        )

        assert response.status_code == 201
        data = response.json()

        # Check member record exists
        member_doc = await db.club_members.find_one({
            "club_id": data["club_id"],
            "user_id": test_user["user_id"],
        })

        assert member_doc is not None
        assert member_doc["role"] == "creator"

        # Cleanup
        await db.book_clubs.delete_one({"club_id": data["club_id"]})
        await db.club_members.delete_many({"club_id": data["club_id"]})


class TestReadClub:
    """Test reading book club information."""

    @pytest_asyncio.fixture
    async def test_club(
        self,
        db: Database,
        test_user: Dict[str, Any],
        test_book: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a test club."""
        club_id = f"club_{ObjectId()}"
        await db.book_clubs.insert_one({
            "club_id": club_id,
            "name": "Test Reading Club",
            "book_id": test_book["book_id"],
            "creator_id": test_user["user_id"],
            "visibility": "public",
            "description": "A test club",
            "settings": {
                "require_approval": False,
            },
            "stats": {
                "member_count": 1,
                "discussion_count": 0,
            },
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
        })

        # Add creator as member
        await db.club_members.insert_one({
            "club_id": club_id,
            "user_id": test_user["user_id"],
            "role": "creator",
            "joined_at": datetime.utcnow(),
        })

        club = {"club_id": club_id}

        yield club

        # Cleanup
        await db.book_clubs.delete_one({"club_id": club_id})
        await db.club_members.delete_many({"club_id": club_id})

    @pytest.mark.asyncio
    async def test_get_club_by_id(
        self,
        client: AsyncClient,
        test_user: Dict[str, Any],
        test_club: Dict[str, Any],
    ):
        """Test getting a club by its ID."""
        response = await client.get(
            f"/api/book-clubs/{test_club['club_id']}",
            headers={"Authorization": test_user["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["club_id"] == test_club["club_id"]
        assert data["name"] == "Test Reading Club"
        assert "stats" in data
        assert "settings" in data

    @pytest.mark.asyncio
    async def test_get_nonexistent_club(
        self,
        client: AsyncClient,
        test_user: Dict[str, Any],
    ):
        """Test getting a club that doesn't exist."""
        fake_club_id = f"fake_club_{ObjectId()}"

        response = await client.get(
            f"/api/book-clubs/{fake_club_id}",
            headers={"Authorization": test_user["token"]},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_public_clubs(
        self,
        client: AsyncClient,
        test_user: Dict[str, Any],
        test_club: Dict[str, Any],
    ):
        """Test listing public clubs."""
        response = await client.get(
            "/api/book-clubs",
            headers={"Authorization": test_user["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        assert "clubs" in data
        assert isinstance(data["clubs"], list)
        assert len(data["clubs"]) > 0

        # Find our test club
        found = any(c["club_id"] == test_club["club_id"] for c in data["clubs"])
        assert found

    @pytest.mark.asyncio
    async def test_list_clubs_by_book(
        self,
        client: AsyncClient,
        test_user: Dict[str, Any],
        test_book: Dict[str, Any],
        test_club: Dict[str, Any],
    ):
        """Test listing clubs for a specific book."""
        response = await client.get(
            f"/api/book-clubs?book_id={test_book['book_id']}",
            headers={"Authorization": test_user["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        # All clubs should be for this book
        for club in data["clubs"]:
            assert club["book_id"] == test_book["book_id"]

    @pytest.mark.asyncio
    async def test_list_clubs_pagination(
        self,
        client: AsyncClient,
        test_user: Dict[str, Any],
    ):
        """Test club listing pagination."""
        response = await client.get(
            "/api/book-clubs?limit=5&skip=0",
            headers={"Authorization": test_user["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["clubs"]) <= 5


class TestUpdateClub:
    """Test updating book clubs."""

    @pytest_asyncio.fixture
    async def test_club(
        self,
        db: Database,
        test_user: Dict[str, Any],
        test_book: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a test club."""
        club_id = f"club_{ObjectId()}"
        await db.book_clubs.insert_one({
            "club_id": club_id,
            "name": "Original Name",
            "book_id": test_book["book_id"],
            "creator_id": test_user["user_id"],
            "visibility": "public",
            "description": "Original description",
            "settings": {
                "require_approval": False,
            },
            "stats": {
                "member_count": 1,
                "discussion_count": 0,
            },
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
        })

        # Add creator as member
        await db.club_members.insert_one({
            "club_id": club_id,
            "user_id": test_user["user_id"],
            "role": "creator",
            "joined_at": datetime.utcnow(),
        })

        club = {"club_id": club_id}

        yield club

        # Cleanup
        await db.book_clubs.delete_one({"club_id": club_id})
        await db.club_members.delete_many({"club_id": club_id})

    @pytest.mark.asyncio
    async def test_update_club_name(
        self,
        client: AsyncClient,
        db: Database,
        test_user: Dict[str, Any],
        test_club: Dict[str, Any],
    ):
        """Test updating club name."""
        response = await client.put(
            f"/api/book-clubs/{test_club['club_id']}",
            headers={"Authorization": test_user["token"]},
            json={"name": "Updated Club Name"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["name"] == "Updated Club Name"

        # Verify in database
        club_doc = await db.book_clubs.find_one({"club_id": test_club["club_id"]})
        assert club_doc["name"] == "Updated Club Name"

    @pytest.mark.asyncio
    async def test_update_club_description(
        self,
        client: AsyncClient,
        db: Database,
        test_user: Dict[str, Any],
        test_club: Dict[str, Any],
    ):
        """Test updating club description."""
        new_description = "This is a new description for the club."

        response = await client.put(
            f"/api/book-clubs/{test_club['club_id']}",
            headers={"Authorization": test_user["token"]},
            json={"description": new_description},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["description"] == new_description

    @pytest.mark.asyncio
    async def test_update_club_visibility(
        self,
        client: AsyncClient,
        db: Database,
        test_user: Dict[str, Any],
        test_club: Dict[str, Any],
    ):
        """Test updating club visibility."""
        response = await client.put(
            f"/api/book-clubs/{test_club['club_id']}",
            headers={"Authorization": test_user["token"]},
            json={"visibility": "private"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["visibility"] == "private"

    @pytest.mark.asyncio
    async def test_update_club_settings(
        self,
        client: AsyncClient,
        db: Database,
        test_user: Dict[str, Any],
        test_club: Dict[str, Any],
    ):
        """Test updating club settings."""
        response = await client.put(
            f"/api/book-clubs/{test_club['club_id']}",
            headers={"Authorization": test_user["token"]},
            json={
                "settings": {
                    "require_approval": True,
                }
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["settings"]["require_approval"] is True

    @pytest.mark.asyncio
    async def test_update_club_non_creator(
        self,
        client: AsyncClient,
        db: Database,
        test_club: Dict[str, Any],
    ):
        """Test that non-creator cannot update club."""
        # Create another user
        other_user_id = f"other_user_{ObjectId()}"
        await db.users.insert_one({
            "user_id": other_user_id,
            "email": f"{other_user_id}@test.com",
            "display_name": "Other User",
            "username": f"otheruser_{ObjectId()}",
            "created_at": datetime.utcnow(),
        })

        other_token = f"Bearer test_token_{other_user_id}"

        response = await client.put(
            f"/api/book-clubs/{test_club['club_id']}",
            headers={"Authorization": other_token},
            json={"name": "Hacked Name"},
        )

        assert response.status_code == 403

        # Cleanup
        await db.users.delete_one({"user_id": other_user_id})

    @pytest.mark.asyncio
    async def test_update_nonexistent_club(
        self,
        client: AsyncClient,
        test_user: Dict[str, Any],
    ):
        """Test updating a club that doesn't exist."""
        fake_club_id = f"fake_club_{ObjectId()}"

        response = await client.put(
            f"/api/book-clubs/{fake_club_id}",
            headers={"Authorization": test_user["token"]},
            json={"name": "New Name"},
        )

        assert response.status_code == 404


class TestDeleteClub:
    """Test deleting book clubs."""

    @pytest_asyncio.fixture
    async def test_club(
        self,
        db: Database,
        test_user: Dict[str, Any],
        test_book: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a test club."""
        club_id = f"club_{ObjectId()}"
        await db.book_clubs.insert_one({
            "club_id": club_id,
            "name": "Club to Delete",
            "book_id": test_book["book_id"],
            "creator_id": test_user["user_id"],
            "visibility": "public",
            "description": "Will be deleted",
            "settings": {
                "require_approval": False,
            },
            "stats": {
                "member_count": 1,
                "discussion_count": 0,
            },
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
        })

        # Add creator as member
        await db.club_members.insert_one({
            "club_id": club_id,
            "user_id": test_user["user_id"],
            "role": "creator",
            "joined_at": datetime.utcnow(),
        })

        club = {"club_id": club_id}

        yield club

        # Cleanup (in case test doesn't delete)
        await db.book_clubs.delete_one({"club_id": club_id})
        await db.club_members.delete_many({"club_id": club_id})

    @pytest.mark.asyncio
    async def test_delete_club_as_creator(
        self,
        client: AsyncClient,
        db: Database,
        test_user: Dict[str, Any],
        test_club: Dict[str, Any],
    ):
        """Test deleting club as creator."""
        response = await client.delete(
            f"/api/book-clubs/{test_club['club_id']}",
            headers={"Authorization": test_user["token"]},
        )

        assert response.status_code == 200

        # Verify club is deleted
        club_doc = await db.book_clubs.find_one({"club_id": test_club["club_id"]})
        assert club_doc is None

        # Verify members are deleted
        member_count = await db.club_members.count_documents({
            "club_id": test_club["club_id"]
        })
        assert member_count == 0

    @pytest.mark.asyncio
    async def test_delete_club_non_creator(
        self,
        client: AsyncClient,
        db: Database,
        test_club: Dict[str, Any],
    ):
        """Test that non-creator cannot delete club."""
        # Create another user
        other_user_id = f"other_user_{ObjectId()}"
        await db.users.insert_one({
            "user_id": other_user_id,
            "email": f"{other_user_id}@test.com",
            "display_name": "Other User",
            "username": f"otheruser_{ObjectId()}",
            "created_at": datetime.utcnow(),
        })

        other_token = f"Bearer test_token_{other_user_id}"

        response = await client.delete(
            f"/api/book-clubs/{test_club['club_id']}",
            headers={"Authorization": other_token},
        )

        assert response.status_code == 403

        # Cleanup
        await db.users.delete_one({"user_id": other_user_id})

    @pytest.mark.asyncio
    async def test_delete_nonexistent_club(
        self,
        client: AsyncClient,
        test_user: Dict[str, Any],
    ):
        """Test deleting a club that doesn't exist."""
        fake_club_id = f"fake_club_{ObjectId()}"

        response = await client.delete(
            f"/api/book-clubs/{fake_club_id}",
            headers={"Authorization": test_user["token"]},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_club_cascades(
        self,
        client: AsyncClient,
        db: Database,
        test_user: Dict[str, Any],
        test_club: Dict[str, Any],
    ):
        """Test that deleting club also deletes related data."""
        # Add a discussion
        discussion_id = f"discussion_{ObjectId()}"
        await db.club_discussions.insert_one({
            "discussion_id": discussion_id,
            "club_id": test_club["club_id"],
            "user_id": test_user["user_id"],
            "content": "Test discussion",
            "created_at": datetime.utcnow(),
        })

        # Delete club
        response = await client.delete(
            f"/api/book-clubs/{test_club['club_id']}",
            headers={"Authorization": test_user["token"]},
        )

        assert response.status_code == 200

        # Verify discussions are deleted
        discussion_doc = await db.club_discussions.find_one({
            "club_id": test_club["club_id"]
        })
        assert discussion_doc is None


class TestClubAccessControl:
    """Test access control for clubs."""

    @pytest.mark.asyncio
    async def test_private_club_not_visible_to_non_members(
        self,
        client: AsyncClient,
        db: Database,
        test_user: Dict[str, Any],
        test_book: Dict[str, Any],
    ):
        """Test that private clubs are not visible to non-members."""
        # Create private club
        club_id = f"club_{ObjectId()}"
        await db.book_clubs.insert_one({
            "club_id": club_id,
            "name": "Private Club",
            "book_id": test_book["book_id"],
            "creator_id": test_user["user_id"],
            "visibility": "private",
            "description": "Secret club",
            "settings": {"require_approval": True},
            "stats": {"member_count": 1, "discussion_count": 0},
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
        })

        # Create another user
        other_user_id = f"other_user_{ObjectId()}"
        await db.users.insert_one({
            "user_id": other_user_id,
            "email": f"{other_user_id}@test.com",
            "display_name": "Other User",
            "username": f"otheruser_{ObjectId()}",
            "created_at": datetime.utcnow(),
        })

        other_token = f"Bearer test_token_{other_user_id}"

        # Other user tries to get private club
        response = await client.get(
            f"/api/book-clubs/{club_id}",
            headers={"Authorization": other_token},
        )

        # Should be hidden or return 403/404
        assert response.status_code in [403, 404]

        # Cleanup
        await db.book_clubs.delete_one({"club_id": club_id})
        await db.users.delete_one({"user_id": other_user_id})

    @pytest.mark.asyncio
    async def test_get_club_without_auth(
        self,
        client: AsyncClient,
        db: Database,
        test_user: Dict[str, Any],
        test_book: Dict[str, Any],
    ):
        """Test getting club without authentication."""
        # Create public club
        club_id = f"club_{ObjectId()}"
        await db.book_clubs.insert_one({
            "club_id": club_id,
            "name": "Public Club",
            "book_id": test_book["book_id"],
            "creator_id": test_user["user_id"],
            "visibility": "public",
            "description": "Public club",
            "settings": {"require_approval": False},
            "stats": {"member_count": 1, "discussion_count": 0},
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
        })

        response = await client.get(f"/api/book-clubs/{club_id}")

        assert response.status_code == 401

        # Cleanup
        await db.book_clubs.delete_one({"club_id": club_id})
