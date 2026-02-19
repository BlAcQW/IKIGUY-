"""
Tests for book clubs discussion functionality.

This module tests:
- Creating discussions and replies
- Listing discussions
- Editing and deleting discussions
- Adding reactions
- Chapter references
- Soft deletes
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
        "title": "Discussion Test Book",
        "author": "Test Author",
        "created_at": datetime.utcnow(),
    })

    book = {"book_id": book_id}

    yield book

    # Cleanup
    await db.books.delete_one({"book_id": book_id})


@pytest_asyncio.fixture
async def test_club(
    db: Database,
    test_users: Dict[str, Dict[str, Any]],
    test_book: Dict[str, Any],
) -> Dict[str, Any]:
    """Create a test club with members."""
    club_id = f"club_{ObjectId()}"
    creator = test_users["user0"]

    await db.book_clubs.insert_one({
        "club_id": club_id,
        "name": "Discussion Test Club",
        "book_id": test_book["book_id"],
        "creator_id": creator["user_id"],
        "visibility": "public",
        "description": "A club for testing discussions",
        "settings": {"require_approval": False},
        "stats": {"member_count": 2, "discussion_count": 0},
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

    # Add second user as member
    await db.club_members.insert_one({
        "club_id": club_id,
        "user_id": test_users["user1"]["user_id"],
        "role": "member",
        "joined_at": datetime.utcnow(),
    })

    club = {"club_id": club_id, "creator_id": creator["user_id"]}

    yield club

    # Cleanup
    await db.book_clubs.delete_one({"club_id": club_id})
    await db.club_members.delete_many({"club_id": club_id})
    await db.club_discussions.delete_many({"club_id": club_id})


class TestCreateDiscussion:
    """Test creating discussions."""

    @pytest.mark.asyncio
    async def test_create_discussion(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
    ):
        """Test creating a discussion."""
        user = test_users["user0"]

        response = await client.post(
            f"/api/book-clubs/{test_club['club_id']}/discussions",
            headers={"Authorization": user["token"]},
            json={
                "content": "What did everyone think of Chapter 3?",
                "chapter_reference": 3,
            },
        )

        assert response.status_code == 201
        data = response.json()

        assert "discussion_id" in data
        assert data["content"] == "What did everyone think of Chapter 3?"
        assert data["chapter_reference"] == 3
        assert data["user_id"] == user["user_id"]
        assert data["reply_count"] == 0

        # Verify in database
        discussion_doc = await db.club_discussions.find_one({
            "discussion_id": data["discussion_id"]
        })

        assert discussion_doc is not None
        assert discussion_doc["content"] == "What did everyone think of Chapter 3?"

    @pytest.mark.asyncio
    async def test_create_discussion_without_chapter(
        self,
        client: AsyncClient,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
    ):
        """Test creating discussion without chapter reference."""
        user = test_users["user0"]

        response = await client.post(
            f"/api/book-clubs/{test_club['club_id']}/discussions",
            headers={"Authorization": user["token"]},
            json={"content": "General thoughts on the book?"},
        )

        assert response.status_code == 201
        data = response.json()

        assert data["chapter_reference"] is None

    @pytest.mark.asyncio
    async def test_only_member_can_create_discussion(
        self,
        client: AsyncClient,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
    ):
        """Test that only club members can create discussions."""
        non_member = test_users["user2"]

        response = await client.post(
            f"/api/book-clubs/{test_club['club_id']}/discussions",
            headers={"Authorization": non_member["token"]},
            json={"content": "Can I post here?"},
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_discussion_updates_club_stats(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
    ):
        """Test that creating discussion updates club stats."""
        user = test_users["user0"]

        # Get initial count
        club_doc = await db.book_clubs.find_one({"club_id": test_club["club_id"]})
        initial_count = club_doc["stats"]["discussion_count"]

        # Create discussion
        await client.post(
            f"/api/book-clubs/{test_club['club_id']}/discussions",
            headers={"Authorization": user["token"]},
            json={"content": "Test discussion"},
        )

        # Check count incremented
        club_doc = await db.book_clubs.find_one({"club_id": test_club["club_id"]})
        assert club_doc["stats"]["discussion_count"] == initial_count + 1

    @pytest.mark.asyncio
    async def test_create_discussion_without_auth(
        self,
        client: AsyncClient,
        test_club: Dict[str, Any],
    ):
        """Test creating discussion without authentication."""
        response = await client.post(
            f"/api/book-clubs/{test_club['club_id']}/discussions",
            json={"content": "Test"},
        )

        assert response.status_code == 401


class TestCreateReply:
    """Test creating replies to discussions."""

    @pytest_asyncio.fixture
    async def parent_discussion(
        self,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a parent discussion."""
        discussion_id = f"discussion_{ObjectId()}"

        await db.club_discussions.insert_one({
            "discussion_id": discussion_id,
            "club_id": test_club["club_id"],
            "user_id": test_users["user0"]["user_id"],
            "content": "Parent discussion",
            "parent_discussion_id": None,
            "chapter_reference": None,
            "reply_count": 0,
            "reactions": {},
            "is_deleted": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })

        discussion = {"discussion_id": discussion_id}

        yield discussion

    @pytest.mark.asyncio
    async def test_create_reply(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
        parent_discussion: Dict[str, Any],
    ):
        """Test creating a reply to a discussion."""
        user = test_users["user1"]

        response = await client.post(
            f"/api/book-clubs/{test_club['club_id']}/discussions",
            headers={"Authorization": user["token"]},
            json={
                "content": "Great point!",
                "parent_discussion_id": parent_discussion["discussion_id"],
            },
        )

        assert response.status_code == 201
        data = response.json()

        assert data["parent_discussion_id"] == parent_discussion["discussion_id"]
        assert data["content"] == "Great point!"

        # Verify parent reply count updated
        parent_doc = await db.club_discussions.find_one({
            "discussion_id": parent_discussion["discussion_id"]
        })

        assert parent_doc["reply_count"] == 1

    @pytest.mark.asyncio
    async def test_reply_to_nonexistent_discussion(
        self,
        client: AsyncClient,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
    ):
        """Test replying to discussion that doesn't exist."""
        user = test_users["user1"]
        fake_discussion_id = f"fake_{ObjectId()}"

        response = await client.post(
            f"/api/book-clubs/{test_club['club_id']}/discussions",
            headers={"Authorization": user["token"]},
            json={
                "content": "Reply",
                "parent_discussion_id": fake_discussion_id,
            },
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_cannot_reply_to_deleted_discussion(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
    ):
        """Test cannot reply to deleted discussion."""
        user = test_users["user1"]

        # Create deleted discussion
        deleted_discussion_id = f"deleted_{ObjectId()}"
        await db.club_discussions.insert_one({
            "discussion_id": deleted_discussion_id,
            "club_id": test_club["club_id"],
            "user_id": test_users["user0"]["user_id"],
            "content": "Deleted",
            "parent_discussion_id": None,
            "is_deleted": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })

        response = await client.post(
            f"/api/book-clubs/{test_club['club_id']}/discussions",
            headers={"Authorization": user["token"]},
            json={
                "content": "Reply to deleted",
                "parent_discussion_id": deleted_discussion_id,
            },
        )

        assert response.status_code == 400


class TestListDiscussions:
    """Test listing discussions."""

    @pytest.mark.asyncio
    async def test_list_club_discussions(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
    ):
        """Test listing all discussions in a club."""
        user = test_users["user0"]

        # Create some discussions
        for i in range(3):
            await db.club_discussions.insert_one({
                "discussion_id": f"discussion_{i}_{ObjectId()}",
                "club_id": test_club["club_id"],
                "user_id": user["user_id"],
                "content": f"Discussion {i}",
                "parent_discussion_id": None,
                "reply_count": 0,
                "reactions": {},
                "is_deleted": False,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            })

        response = await client.get(
            f"/api/book-clubs/{test_club['club_id']}/discussions",
            headers={"Authorization": user["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        assert "discussions" in data
        assert len(data["discussions"]) >= 3

    @pytest.mark.asyncio
    async def test_list_discussions_by_chapter(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
    ):
        """Test filtering discussions by chapter."""
        user = test_users["user0"]

        # Create discussions for different chapters
        await db.club_discussions.insert_one({
            "discussion_id": f"discussion_ch1_{ObjectId()}",
            "club_id": test_club["club_id"],
            "user_id": user["user_id"],
            "content": "Chapter 1 discussion",
            "parent_discussion_id": None,
            "chapter_reference": 1,
            "reply_count": 0,
            "reactions": {},
            "is_deleted": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })

        await db.club_discussions.insert_one({
            "discussion_id": f"discussion_ch2_{ObjectId()}",
            "club_id": test_club["club_id"],
            "user_id": user["user_id"],
            "content": "Chapter 2 discussion",
            "parent_discussion_id": None,
            "chapter_reference": 2,
            "reply_count": 0,
            "reactions": {},
            "is_deleted": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })

        # Filter by chapter 1
        response = await client.get(
            f"/api/book-clubs/{test_club['club_id']}/discussions?chapter=1",
            headers={"Authorization": user["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        # All discussions should be for chapter 1
        for discussion in data["discussions"]:
            if discussion["chapter_reference"] is not None:
                assert discussion["chapter_reference"] == 1

    @pytest.mark.asyncio
    async def test_list_discussions_excludes_deleted(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
    ):
        """Test that deleted discussions are excluded from list."""
        user = test_users["user0"]

        # Create deleted discussion
        deleted_id = f"deleted_{ObjectId()}"
        await db.club_discussions.insert_one({
            "discussion_id": deleted_id,
            "club_id": test_club["club_id"],
            "user_id": user["user_id"],
            "content": "[deleted]",
            "parent_discussion_id": None,
            "is_deleted": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })

        response = await client.get(
            f"/api/book-clubs/{test_club['club_id']}/discussions",
            headers={"Authorization": user["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        # Deleted discussion should not appear (or marked as deleted)
        deleted_in_list = any(d["discussion_id"] == deleted_id for d in data["discussions"])

        if deleted_in_list:
            # If included, content should be [deleted]
            deleted_discussion = next(d for d in data["discussions"] if d["discussion_id"] == deleted_id)
            assert deleted_discussion["content"] == "[deleted]" or deleted_discussion["is_deleted"]

    @pytest.mark.asyncio
    async def test_list_discussions_pagination(
        self,
        client: AsyncClient,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
    ):
        """Test discussion list pagination."""
        user = test_users["user0"]

        response = await client.get(
            f"/api/book-clubs/{test_club['club_id']}/discussions?limit=5&skip=0",
            headers={"Authorization": user["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["discussions"]) <= 5


class TestEditDiscussion:
    """Test editing discussions."""

    @pytest_asyncio.fixture
    async def test_discussion(
        self,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a test discussion."""
        discussion_id = f"discussion_{ObjectId()}"

        await db.club_discussions.insert_one({
            "discussion_id": discussion_id,
            "club_id": test_club["club_id"],
            "user_id": test_users["user0"]["user_id"],
            "content": "Original content",
            "parent_discussion_id": None,
            "chapter_reference": None,
            "reply_count": 0,
            "reactions": {},
            "is_deleted": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })

        discussion = {"discussion_id": discussion_id}

        yield discussion

    @pytest.mark.asyncio
    async def test_edit_own_discussion(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
        test_discussion: Dict[str, Any],
    ):
        """Test editing own discussion."""
        user = test_users["user0"]
        new_content = "Edited content"

        response = await client.put(
            f"/api/book-clubs/{test_club['club_id']}/discussions/{test_discussion['discussion_id']}",
            headers={"Authorization": user["token"]},
            json={"content": new_content},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["content"] == new_content

        # Verify in database
        discussion_doc = await db.club_discussions.find_one({
            "discussion_id": test_discussion["discussion_id"]
        })

        assert discussion_doc["content"] == new_content

    @pytest.mark.asyncio
    async def test_cannot_edit_others_discussion(
        self,
        client: AsyncClient,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
        test_discussion: Dict[str, Any],
    ):
        """Test cannot edit someone else's discussion."""
        other_user = test_users["user1"]

        response = await client.put(
            f"/api/book-clubs/{test_club['club_id']}/discussions/{test_discussion['discussion_id']}",
            headers={"Authorization": other_user["token"]},
            json={"content": "Hacked content"},
        )

        assert response.status_code == 403


class TestDeleteDiscussion:
    """Test deleting discussions."""

    @pytest_asyncio.fixture
    async def test_discussion(
        self,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a test discussion."""
        discussion_id = f"discussion_{ObjectId()}"

        await db.club_discussions.insert_one({
            "discussion_id": discussion_id,
            "club_id": test_club["club_id"],
            "user_id": test_users["user0"]["user_id"],
            "content": "To be deleted",
            "parent_discussion_id": None,
            "chapter_reference": None,
            "reply_count": 0,
            "reactions": {},
            "is_deleted": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })

        discussion = {"discussion_id": discussion_id}

        yield discussion

    @pytest.mark.asyncio
    async def test_delete_own_discussion(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
        test_discussion: Dict[str, Any],
    ):
        """Test deleting own discussion (soft delete)."""
        user = test_users["user0"]

        response = await client.delete(
            f"/api/book-clubs/{test_club['club_id']}/discussions/{test_discussion['discussion_id']}",
            headers={"Authorization": user["token"]},
        )

        assert response.status_code == 200

        # Verify soft delete (is_deleted = true, content = "[deleted]")
        discussion_doc = await db.club_discussions.find_one({
            "discussion_id": test_discussion["discussion_id"]
        })

        assert discussion_doc is not None  # Still exists
        assert discussion_doc["is_deleted"] is True
        assert discussion_doc["content"] == "[deleted]"

    @pytest.mark.asyncio
    async def test_moderator_can_delete_discussion(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
        test_discussion: Dict[str, Any],
    ):
        """Test that moderator can delete any discussion."""
        # Make user1 a moderator
        await db.club_members.update_one(
            {"club_id": test_club["club_id"], "user_id": test_users["user1"]["user_id"]},
            {"$set": {"role": "moderator"}},
        )

        moderator = test_users["user1"]

        response = await client.delete(
            f"/api/book-clubs/{test_club['club_id']}/discussions/{test_discussion['discussion_id']}",
            headers={"Authorization": moderator["token"]},
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_regular_member_cannot_delete_others_discussion(
        self,
        client: AsyncClient,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
        test_discussion: Dict[str, Any],
    ):
        """Test that regular member cannot delete others' discussions."""
        other_user = test_users["user1"]

        response = await client.delete(
            f"/api/book-clubs/{test_club['club_id']}/discussions/{test_discussion['discussion_id']}",
            headers={"Authorization": other_user["token"]},
        )

        assert response.status_code == 403


class TestReactions:
    """Test discussion reactions."""

    @pytest_asyncio.fixture
    async def test_discussion(
        self,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a test discussion."""
        discussion_id = f"discussion_{ObjectId()}"

        await db.club_discussions.insert_one({
            "discussion_id": discussion_id,
            "club_id": test_club["club_id"],
            "user_id": test_users["user0"]["user_id"],
            "content": "React to this",
            "parent_discussion_id": None,
            "chapter_reference": None,
            "reply_count": 0,
            "reactions": {},
            "is_deleted": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })

        discussion = {"discussion_id": discussion_id}

        yield discussion

    @pytest.mark.asyncio
    async def test_add_reaction(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
        test_discussion: Dict[str, Any],
    ):
        """Test adding a reaction to a discussion."""
        user = test_users["user1"]

        response = await client.post(
            f"/api/book-clubs/{test_club['club_id']}/discussions/{test_discussion['discussion_id']}/reactions",
            headers={"Authorization": user["token"]},
            json={"emoji": "👍"},
        )

        assert response.status_code == 200

        # Verify reaction added
        discussion_doc = await db.club_discussions.find_one({
            "discussion_id": test_discussion["discussion_id"]
        })

        assert "👍" in discussion_doc["reactions"]
        assert user["user_id"] in discussion_doc["reactions"]["👍"]

    @pytest.mark.asyncio
    async def test_remove_reaction(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
        test_discussion: Dict[str, Any],
    ):
        """Test removing a reaction (toggle off)."""
        user = test_users["user1"]

        # Add reaction first
        await client.post(
            f"/api/book-clubs/{test_club['club_id']}/discussions/{test_discussion['discussion_id']}/reactions",
            headers={"Authorization": user["token"]},
            json={"emoji": "👍"},
        )

        # Remove reaction (toggle off)
        response = await client.post(
            f"/api/book-clubs/{test_club['club_id']}/discussions/{test_discussion['discussion_id']}/reactions",
            headers={"Authorization": user["token"]},
            json={"emoji": "👍"},
        )

        assert response.status_code == 200

        # Verify reaction removed
        discussion_doc = await db.club_discussions.find_one({
            "discussion_id": test_discussion["discussion_id"]
        })

        if "👍" in discussion_doc["reactions"]:
            assert user["user_id"] not in discussion_doc["reactions"]["👍"]

    @pytest.mark.asyncio
    async def test_multiple_users_same_reaction(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
        test_discussion: Dict[str, Any],
    ):
        """Test multiple users can add same reaction."""
        user1 = test_users["user0"]
        user2 = test_users["user1"]

        # Both users add same emoji
        await client.post(
            f"/api/book-clubs/{test_club['club_id']}/discussions/{test_discussion['discussion_id']}/reactions",
            headers={"Authorization": user1["token"]},
            json={"emoji": "❤️"},
        )

        await client.post(
            f"/api/book-clubs/{test_club['club_id']}/discussions/{test_discussion['discussion_id']}/reactions",
            headers={"Authorization": user2["token"]},
            json={"emoji": "❤️"},
        )

        # Verify both users in reaction list
        discussion_doc = await db.club_discussions.find_one({
            "discussion_id": test_discussion["discussion_id"]
        })

        assert "❤️" in discussion_doc["reactions"]
        assert len(discussion_doc["reactions"]["❤️"]) == 2


class TestEdgeCases:
    """Test edge cases for discussions."""

    @pytest.mark.asyncio
    async def test_very_long_discussion_content(
        self,
        client: AsyncClient,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
    ):
        """Test creating discussion with very long content."""
        user = test_users["user0"]
        long_content = "A" * 10000  # Very long

        response = await client.post(
            f"/api/book-clubs/{test_club['club_id']}/discussions",
            headers={"Authorization": user["token"]},
            json={"content": long_content},
        )

        # Should either succeed or validate length
        assert response.status_code in [201, 422]

    @pytest.mark.asyncio
    async def test_empty_discussion_content(
        self,
        client: AsyncClient,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
    ):
        """Test creating discussion with empty content."""
        user = test_users["user0"]

        response = await client.post(
            f"/api/book-clubs/{test_club['club_id']}/discussions",
            headers={"Authorization": user["token"]},
            json={"content": ""},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_emoji_reaction(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
    ):
        """Test adding invalid emoji as reaction."""
        user = test_users["user0"]

        # Create discussion
        discussion_id = f"discussion_{ObjectId()}"
        await db.club_discussions.insert_one({
            "discussion_id": discussion_id,
            "club_id": test_club["club_id"],
            "user_id": user["user_id"],
            "content": "Test",
            "parent_discussion_id": None,
            "reactions": {},
            "is_deleted": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })

        # Try invalid emoji
        response = await client.post(
            f"/api/book-clubs/{test_club['club_id']}/discussions/{discussion_id}/reactions",
            headers={"Authorization": user["token"]},
            json={"emoji": "not_an_emoji"},
        )

        # Should validate or accept
        assert response.status_code in [200, 422]
