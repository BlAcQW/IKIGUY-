"""
Tests for book clubs membership functionality.

This module tests:
- Joining clubs
- Leaving clubs
- Member listing
- Role management (creator, moderator, member)
- Member removal
- Approval workflows
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
    """Create test users."""
    users = {}

    for i in range(3):
        user_id = f"test_user_{i}_{ObjectId()}"
        await db.users.insert_one({
            "user_id": user_id,
            "email": f"{user_id}@test.com",
            "display_name": f"User {i}",
            "username": f"user{i}_{ObjectId()}",
            "created_at": datetime.utcnow(),
        })
        users[f"user{i}"] = {
            "user_id": user_id,
            "token": f"Bearer test_token_{user_id}",
        }

    yield users

    # Cleanup
    await db.users.delete_many({
        "user_id": {"$in": [u["user_id"] for u in users.values()]}
    })


@pytest_asyncio.fixture
async def test_book(db: Database) -> Dict[str, Any]:
    """Create a test book."""
    book_id = f"test_book_{ObjectId()}"
    await db.books.insert_one({
        "book_id": book_id,
        "title": "Test Book",
        "author": "Test Author",
        "created_at": datetime.utcnow(),
    })

    book = {"book_id": book_id}

    yield book

    # Cleanup
    await db.books.delete_one({"book_id": book_id})


@pytest_asyncio.fixture
async def public_club(
    db: Database,
    test_users: Dict[str, Dict[str, Any]],
    test_book: Dict[str, Any],
) -> Dict[str, Any]:
    """Create a public test club."""
    club_id = f"club_{ObjectId()}"
    creator = test_users["user0"]

    await db.book_clubs.insert_one({
        "club_id": club_id,
        "name": "Public Test Club",
        "book_id": test_book["book_id"],
        "creator_id": creator["user_id"],
        "visibility": "public",
        "description": "A public club for testing",
        "settings": {"require_approval": False},
        "stats": {"member_count": 1, "discussion_count": 0},
        "created_at": datetime.utcnow(),
        "last_activity": datetime.utcnow(),
    })

    # Add creator as member
    await db.club_members.insert_one({
        "club_id": club_id,
        "user_id": creator["user_id"],
        "role": "creator",
        "joined_at": datetime.utcnow(),
    })

    club = {"club_id": club_id, "creator_id": creator["user_id"]}

    yield club

    # Cleanup
    await db.book_clubs.delete_one({"club_id": club_id})
    await db.club_members.delete_many({"club_id": club_id})


class TestJoinClub:
    """Test joining book clubs."""

    @pytest.mark.asyncio
    async def test_join_public_club(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        public_club: Dict[str, Any],
    ):
        """Test joining a public club."""
        user = test_users["user1"]

        response = await client.post(
            f"/api/book-clubs/{public_club['club_id']}/join",
            headers={"Authorization": user["token"]},
        )

        assert response.status_code == 200

        # Verify member record created
        member_doc = await db.club_members.find_one({
            "club_id": public_club["club_id"],
            "user_id": user["user_id"],
        })

        assert member_doc is not None
        assert member_doc["role"] == "member"

        # Verify member count updated
        club_doc = await db.book_clubs.find_one({"club_id": public_club["club_id"]})
        assert club_doc["stats"]["member_count"] == 2

    @pytest.mark.asyncio
    async def test_join_club_with_approval_required(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_book: Dict[str, Any],
    ):
        """Test joining a club that requires approval."""
        creator = test_users["user0"]
        joiner = test_users["user1"]

        # Create club with approval required
        club_id = f"approval_club_{ObjectId()}"
        await db.book_clubs.insert_one({
            "club_id": club_id,
            "name": "Approval Required Club",
            "book_id": test_book["book_id"],
            "creator_id": creator["user_id"],
            "visibility": "public",
            "description": "Need approval",
            "settings": {"require_approval": True},
            "stats": {"member_count": 1, "discussion_count": 0},
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
        })

        # User tries to join
        response = await client.post(
            f"/api/book-clubs/{club_id}/join",
            headers={"Authorization": joiner["token"]},
        )

        # Should create pending membership or join request
        assert response.status_code in [200, 202]

        # Cleanup
        await db.book_clubs.delete_one({"club_id": club_id})
        await db.club_members.delete_many({"club_id": club_id})

    @pytest.mark.asyncio
    async def test_join_club_already_member(
        self,
        client: AsyncClient,
        test_users: Dict[str, Dict[str, Any]],
        public_club: Dict[str, Any],
    ):
        """Test joining a club user is already a member of."""
        user = test_users["user1"]

        # Join once
        await client.post(
            f"/api/book-clubs/{public_club['club_id']}/join",
            headers={"Authorization": user["token"]},
        )

        # Try to join again
        response = await client.post(
            f"/api/book-clubs/{public_club['club_id']}/join",
            headers={"Authorization": user["token"]},
        )

        # Should return error or 200 with message
        assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_join_nonexistent_club(
        self,
        client: AsyncClient,
        test_users: Dict[str, Dict[str, Any]],
    ):
        """Test joining a club that doesn't exist."""
        user = test_users["user1"]
        fake_club_id = f"fake_club_{ObjectId()}"

        response = await client.post(
            f"/api/book-clubs/{fake_club_id}/join",
            headers={"Authorization": user["token"]},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_join_club_without_auth(
        self,
        client: AsyncClient,
        public_club: Dict[str, Any],
    ):
        """Test joining club without authentication."""
        response = await client.post(
            f"/api/book-clubs/{public_club['club_id']}/join"
        )

        assert response.status_code == 401


class TestLeaveClub:
    """Test leaving book clubs."""

    @pytest.mark.asyncio
    async def test_leave_club(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        public_club: Dict[str, Any],
    ):
        """Test leaving a club."""
        user = test_users["user1"]

        # Join club first
        await client.post(
            f"/api/book-clubs/{public_club['club_id']}/join",
            headers={"Authorization": user["token"]},
        )

        # Leave club
        response = await client.post(
            f"/api/book-clubs/{public_club['club_id']}/leave",
            headers={"Authorization": user["token"]},
        )

        assert response.status_code == 200

        # Verify member record deleted
        member_doc = await db.club_members.find_one({
            "club_id": public_club["club_id"],
            "user_id": user["user_id"],
        })

        assert member_doc is None

        # Verify member count updated
        club_doc = await db.book_clubs.find_one({"club_id": public_club["club_id"]})
        assert club_doc["stats"]["member_count"] == 1

    @pytest.mark.asyncio
    async def test_leave_club_not_member(
        self,
        client: AsyncClient,
        test_users: Dict[str, Dict[str, Any]],
        public_club: Dict[str, Any],
    ):
        """Test leaving a club user is not a member of."""
        user = test_users["user1"]

        response = await client.post(
            f"/api/book-clubs/{public_club['club_id']}/leave",
            headers={"Authorization": user["token"]},
        )

        # Should return error
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_creator_cannot_leave_club(
        self,
        client: AsyncClient,
        test_users: Dict[str, Dict[str, Any]],
        public_club: Dict[str, Any],
    ):
        """Test that creator cannot leave their own club."""
        creator = test_users["user0"]

        response = await client.post(
            f"/api/book-clubs/{public_club['club_id']}/leave",
            headers={"Authorization": creator["token"]},
        )

        # Should return error
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_leave_nonexistent_club(
        self,
        client: AsyncClient,
        test_users: Dict[str, Any],
    ):
        """Test leaving a club that doesn't exist."""
        user = test_users["user1"]
        fake_club_id = f"fake_club_{ObjectId()}"

        response = await client.post(
            f"/api/book-clubs/{fake_club_id}/leave",
            headers={"Authorization": user["token"]},
        )

        assert response.status_code == 404


class TestListMembers:
    """Test listing club members."""

    @pytest.mark.asyncio
    async def test_list_club_members(
        self,
        client: AsyncClient,
        test_users: Dict[str, Dict[str, Any]],
        public_club: Dict[str, Any],
    ):
        """Test listing all members of a club."""
        user1 = test_users["user1"]
        user2 = test_users["user2"]

        # Add members
        await client.post(
            f"/api/book-clubs/{public_club['club_id']}/join",
            headers={"Authorization": user1["token"]},
        )
        await client.post(
            f"/api/book-clubs/{public_club['club_id']}/join",
            headers={"Authorization": user2["token"]},
        )

        # List members
        response = await client.get(
            f"/api/book-clubs/{public_club['club_id']}/members",
            headers={"Authorization": user1["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        assert "members" in data
        assert len(data["members"]) == 3  # creator + 2 members

    @pytest.mark.asyncio
    async def test_list_members_shows_roles(
        self,
        client: AsyncClient,
        test_users: Dict[str, Dict[str, Any]],
        public_club: Dict[str, Any],
    ):
        """Test that member list shows roles."""
        user = test_users["user1"]

        response = await client.get(
            f"/api/book-clubs/{public_club['club_id']}/members",
            headers={"Authorization": user["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        # Should have creator
        creator = next((m for m in data["members"] if m["role"] == "creator"), None)
        assert creator is not None

    @pytest.mark.asyncio
    async def test_list_members_pagination(
        self,
        client: AsyncClient,
        test_users: Dict[str, Dict[str, Any]],
        public_club: Dict[str, Any],
    ):
        """Test member list pagination."""
        response = await client.get(
            f"/api/book-clubs/{public_club['club_id']}/members?limit=2&skip=0",
            headers={"Authorization": test_users["user0"]["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["members"]) <= 2


class TestRemoveMember:
    """Test removing members from clubs."""

    @pytest.mark.asyncio
    async def test_creator_can_remove_member(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        public_club: Dict[str, Any],
    ):
        """Test that creator can remove members."""
        creator = test_users["user0"]
        member = test_users["user1"]

        # Member joins
        await client.post(
            f"/api/book-clubs/{public_club['club_id']}/join",
            headers={"Authorization": member["token"]},
        )

        # Creator removes member
        response = await client.delete(
            f"/api/book-clubs/{public_club['club_id']}/members/{member['user_id']}",
            headers={"Authorization": creator["token"]},
        )

        assert response.status_code == 200

        # Verify member removed
        member_doc = await db.club_members.find_one({
            "club_id": public_club["club_id"],
            "user_id": member["user_id"],
        })

        assert member_doc is None

    @pytest.mark.asyncio
    async def test_moderator_can_remove_member(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        public_club: Dict[str, Any],
    ):
        """Test that moderator can remove regular members."""
        creator = test_users["user0"]
        moderator = test_users["user1"]
        member = test_users["user2"]

        # Add moderator
        await db.club_members.insert_one({
            "club_id": public_club["club_id"],
            "user_id": moderator["user_id"],
            "role": "moderator",
            "joined_at": datetime.utcnow(),
        })

        # Add member
        await client.post(
            f"/api/book-clubs/{public_club['club_id']}/join",
            headers={"Authorization": member["token"]},
        )

        # Moderator removes member
        response = await client.delete(
            f"/api/book-clubs/{public_club['club_id']}/members/{member['user_id']}",
            headers={"Authorization": moderator["token"]},
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_regular_member_cannot_remove_member(
        self,
        client: AsyncClient,
        test_users: Dict[str, Dict[str, Any]],
        public_club: Dict[str, Any],
    ):
        """Test that regular member cannot remove other members."""
        member1 = test_users["user1"]
        member2 = test_users["user2"]

        # Both join
        await client.post(
            f"/api/book-clubs/{public_club['club_id']}/join",
            headers={"Authorization": member1["token"]},
        )
        await client.post(
            f"/api/book-clubs/{public_club['club_id']}/join",
            headers={"Authorization": member2["token"]},
        )

        # Member 1 tries to remove Member 2
        response = await client.delete(
            f"/api/book-clubs/{public_club['club_id']}/members/{member2['user_id']}",
            headers={"Authorization": member1["token"]},
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_cannot_remove_creator(
        self,
        client: AsyncClient,
        test_users: Dict[str, Dict[str, Any]],
        public_club: Dict[str, Any],
    ):
        """Test that creator cannot be removed."""
        creator = test_users["user0"]
        moderator = test_users["user1"]

        # Add moderator
        await client.post(
            f"/api/book-clubs/{public_club['club_id']}/join",
            headers={"Authorization": moderator["token"]},
        )

        # Moderator tries to remove creator (should fail)
        response = await client.delete(
            f"/api/book-clubs/{public_club['club_id']}/members/{creator['user_id']}",
            headers={"Authorization": moderator["token"]},
        )

        assert response.status_code == 403


class TestUpdateMemberRole:
    """Test updating member roles."""

    @pytest.mark.asyncio
    async def test_creator_can_promote_to_moderator(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        public_club: Dict[str, Any],
    ):
        """Test that creator can promote member to moderator."""
        creator = test_users["user0"]
        member = test_users["user1"]

        # Member joins
        await client.post(
            f"/api/book-clubs/{public_club['club_id']}/join",
            headers={"Authorization": member["token"]},
        )

        # Creator promotes to moderator
        response = await client.put(
            f"/api/book-clubs/{public_club['club_id']}/members/{member['user_id']}/role",
            headers={"Authorization": creator["token"]},
            json={"role": "moderator"},
        )

        assert response.status_code == 200

        # Verify role updated
        member_doc = await db.club_members.find_one({
            "club_id": public_club["club_id"],
            "user_id": member["user_id"],
        })

        assert member_doc["role"] == "moderator"

    @pytest.mark.asyncio
    async def test_creator_can_demote_moderator(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        public_club: Dict[str, Any],
    ):
        """Test that creator can demote moderator to member."""
        creator = test_users["user0"]
        moderator = test_users["user1"]

        # Add as moderator
        await db.club_members.insert_one({
            "club_id": public_club["club_id"],
            "user_id": moderator["user_id"],
            "role": "moderator",
            "joined_at": datetime.utcnow(),
        })

        # Creator demotes to member
        response = await client.put(
            f"/api/book-clubs/{public_club['club_id']}/members/{moderator['user_id']}/role",
            headers={"Authorization": creator["token"]},
            json={"role": "member"},
        )

        assert response.status_code == 200

        # Verify role updated
        member_doc = await db.club_members.find_one({
            "club_id": public_club["club_id"],
            "user_id": moderator["user_id"],
        })

        assert member_doc["role"] == "member"

    @pytest.mark.asyncio
    async def test_moderator_cannot_change_roles(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        public_club: Dict[str, Any],
    ):
        """Test that moderator cannot change roles."""
        moderator = test_users["user1"]
        member = test_users["user2"]

        # Add moderator
        await db.club_members.insert_one({
            "club_id": public_club["club_id"],
            "user_id": moderator["user_id"],
            "role": "moderator",
            "joined_at": datetime.utcnow(),
        })

        # Add member
        await client.post(
            f"/api/book-clubs/{public_club['club_id']}/join",
            headers={"Authorization": member["token"]},
        )

        # Moderator tries to promote member
        response = await client.put(
            f"/api/book-clubs/{public_club['club_id']}/members/{member['user_id']}/role",
            headers={"Authorization": moderator["token"]},
            json={"role": "moderator"},
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_cannot_change_creator_role(
        self,
        client: AsyncClient,
        test_users: Dict[str, Dict[str, Any]],
        public_club: Dict[str, Any],
    ):
        """Test that creator role cannot be changed."""
        creator = test_users["user0"]

        response = await client.put(
            f"/api/book-clubs/{public_club['club_id']}/members/{creator['user_id']}/role",
            headers={"Authorization": creator["token"]},
            json={"role": "member"},
        )

        # Should fail
        assert response.status_code == 400


class TestMemberStats:
    """Test member count statistics."""

    @pytest.mark.asyncio
    async def test_member_count_increments_on_join(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        public_club: Dict[str, Any],
    ):
        """Test that member count increments when user joins."""
        user = test_users["user1"]

        # Get initial count
        club_doc = await db.book_clubs.find_one({"club_id": public_club["club_id"]})
        initial_count = club_doc["stats"]["member_count"]

        # Join
        await client.post(
            f"/api/book-clubs/{public_club['club_id']}/join",
            headers={"Authorization": user["token"]},
        )

        # Check count incremented
        club_doc = await db.book_clubs.find_one({"club_id": public_club["club_id"]})
        assert club_doc["stats"]["member_count"] == initial_count + 1

    @pytest.mark.asyncio
    async def test_member_count_decrements_on_leave(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        public_club: Dict[str, Any],
    ):
        """Test that member count decrements when user leaves."""
        user = test_users["user1"]

        # Join
        await client.post(
            f"/api/book-clubs/{public_club['club_id']}/join",
            headers={"Authorization": user["token"]},
        )

        # Get count after join
        club_doc = await db.book_clubs.find_one({"club_id": public_club["club_id"]})
        count_after_join = club_doc["stats"]["member_count"]

        # Leave
        await client.post(
            f"/api/book-clubs/{public_club['club_id']}/leave",
            headers={"Authorization": user["token"]},
        )

        # Check count decremented
        club_doc = await db.book_clubs.find_one({"club_id": public_club["club_id"]})
        assert club_doc["stats"]["member_count"] == count_after_join - 1

    @pytest.mark.asyncio
    async def test_member_count_consistency(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        public_club: Dict[str, Any],
    ):
        """Test that member count matches actual member records."""
        # Add some members
        await client.post(
            f"/api/book-clubs/{public_club['club_id']}/join",
            headers={"Authorization": test_users["user1"]["token"]},
        )
        await client.post(
            f"/api/book-clubs/{public_club['club_id']}/join",
            headers={"Authorization": test_users["user2"]["token"]},
        )

        # Count actual members
        actual_count = await db.club_members.count_documents({
            "club_id": public_club["club_id"]
        })

        # Check denormalized count matches
        club_doc = await db.book_clubs.find_one({"club_id": public_club["club_id"]})
        assert club_doc["stats"]["member_count"] == actual_count
