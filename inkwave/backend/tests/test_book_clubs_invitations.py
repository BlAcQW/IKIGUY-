"""
Tests for book clubs invitation functionality.

This module tests:
- Sending invitations (user_id and email)
- Accepting/declining invitations
- Listing invitations
- Canceling invitations
- Invitation tokens
- Email invitation flow
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
    """Create test users."""
    users = {}

    for i in range(3):
        user_id = f"test_user_{i}_{ObjectId()}"
        await db.users.insert_one({
            "user_id": user_id,
            "email": f"user{i}@test.com",
            "display_name": f"User {i}",
            "username": f"user{i}_{ObjectId()}",
            "created_at": datetime.utcnow(),
        })
        users[f"user{i}"] = {
            "user_id": user_id,
            "email": f"user{i}@test.com",
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
        "title": "Test Book for Invitations",
        "author": "Test Author",
        "created_at": datetime.utcnow(),
    })

    book = {"book_id": book_id, "title": "Test Book for Invitations"}

    yield book

    # Cleanup
    await db.books.delete_one({"book_id": book_id})


@pytest_asyncio.fixture
async def test_club(
    db: Database,
    test_users: Dict[str, Dict[str, Any]],
    test_book: Dict[str, Any],
) -> Dict[str, Any]:
    """Create a test club."""
    club_id = f"club_{ObjectId()}"
    creator = test_users["user0"]

    await db.book_clubs.insert_one({
        "club_id": club_id,
        "name": "Invitation Test Club",
        "book_id": test_book["book_id"],
        "book_title": test_book["title"],
        "creator_id": creator["user_id"],
        "visibility": "public",
        "description": "A club for testing invitations",
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

    club = {
        "club_id": club_id,
        "name": "Invitation Test Club",
        "creator_id": creator["user_id"],
    }

    yield club

    # Cleanup
    await db.book_clubs.delete_one({"club_id": club_id})
    await db.club_members.delete_many({"club_id": club_id})
    await db.club_invitations.delete_many({"club_id": club_id})


class TestSendUserInvitation:
    """Test sending invitations to registered users."""

    @pytest.mark.asyncio
    async def test_send_invitation_to_user(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
    ):
        """Test sending invitation to a registered user."""
        inviter = test_users["user0"]
        invitee = test_users["user1"]

        response = await client.post(
            f"/api/book-clubs/{test_club['club_id']}/invitations",
            headers={"Authorization": inviter["token"]},
            json={
                "user_id": invitee["user_id"],
                "message": "Join my book club!",
            },
        )

        assert response.status_code == 201
        data = response.json()

        assert "invitation_id" in data
        assert data["message"] == "Invitation sent successfully"

        # Verify invitation in database
        invitation_doc = await db.club_invitations.find_one({
            "invitation_id": data["invitation_id"]
        })

        assert invitation_doc is not None
        assert invitation_doc["inviter_id"] == inviter["user_id"]
        assert invitation_doc["invitee_user_id"] == invitee["user_id"]
        assert invitation_doc["status"] == "pending"

    @pytest.mark.asyncio
    async def test_send_invitation_with_custom_message(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
    ):
        """Test sending invitation with custom message."""
        inviter = test_users["user0"]
        invitee = test_users["user1"]

        custom_message = "Hey! I think you'd love this book. Join us!"

        response = await client.post(
            f"/api/book-clubs/{test_club['club_id']}/invitations",
            headers={"Authorization": inviter["token"]},
            json={
                "user_id": invitee["user_id"],
                "message": custom_message,
            },
        )

        assert response.status_code == 201

        # Verify message stored
        invitation_doc = await db.club_invitations.find_one({
            "invitee_user_id": invitee["user_id"],
            "club_id": test_club["club_id"],
        })

        assert invitation_doc["message"] == custom_message

    @pytest.mark.asyncio
    async def test_cannot_invite_already_member(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
    ):
        """Test that cannot invite user who is already a member."""
        inviter = test_users["user0"]
        member = test_users["user1"]

        # Add member to club
        await db.club_members.insert_one({
            "club_id": test_club["club_id"],
            "user_id": member["user_id"],
            "role": "member",
            "joined_at": datetime.utcnow(),
        })

        # Try to invite
        response = await client.post(
            f"/api/book-clubs/{test_club['club_id']}/invitations",
            headers={"Authorization": inviter["token"]},
            json={"user_id": member["user_id"]},
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_cannot_invite_nonexistent_user(
        self,
        client: AsyncClient,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
    ):
        """Test inviting a user that doesn't exist."""
        inviter = test_users["user0"]
        fake_user_id = f"fake_user_{ObjectId()}"

        response = await client.post(
            f"/api/book-clubs/{test_club['club_id']}/invitations",
            headers={"Authorization": inviter["token"]},
            json={"user_id": fake_user_id},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_only_member_can_send_invitation(
        self,
        client: AsyncClient,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
    ):
        """Test that only club members can send invitations."""
        non_member = test_users["user1"]
        invitee = test_users["user2"]

        response = await client.post(
            f"/api/book-clubs/{test_club['club_id']}/invitations",
            headers={"Authorization": non_member["token"]},
            json={"user_id": invitee["user_id"]},
        )

        assert response.status_code == 403


class TestSendEmailInvitation:
    """Test sending invitations to email addresses."""

    @pytest.mark.asyncio
    async def test_send_email_invitation(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
    ):
        """Test sending invitation to an email address."""
        inviter = test_users["user0"]
        email = "newuser@test.com"

        response = await client.post(
            f"/api/book-clubs/{test_club['club_id']}/invitations",
            headers={"Authorization": inviter["token"]},
            json={
                "email": email,
                "message": "Join our book club!",
            },
        )

        assert response.status_code == 201
        data = response.json()

        assert "invitation_id" in data

        # Verify invitation in database
        invitation_doc = await db.club_invitations.find_one({
            "invitation_id": data["invitation_id"]
        })

        assert invitation_doc is not None
        assert invitation_doc["invitee_email"] == email
        assert "invitation_token" in invitation_doc
        assert invitation_doc["status"] == "pending"

    @pytest.mark.asyncio
    async def test_email_invitation_generates_token(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
    ):
        """Test that email invitation generates a token."""
        inviter = test_users["user0"]

        response = await client.post(
            f"/api/book-clubs/{test_club['club_id']}/invitations",
            headers={"Authorization": inviter["token"]},
            json={"email": "newuser@test.com"},
        )

        assert response.status_code == 201

        # Verify token exists and is unique
        invitation_doc = await db.club_invitations.find_one({
            "invitee_email": "newuser@test.com",
            "club_id": test_club["club_id"],
        })

        assert "invitation_token" in invitation_doc
        assert len(invitation_doc["invitation_token"]) > 10

    @pytest.mark.asyncio
    async def test_cannot_invite_email_of_existing_member(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
    ):
        """Test that cannot invite email of existing member."""
        inviter = test_users["user0"]
        member = test_users["user1"]

        # Add member to club
        await db.club_members.insert_one({
            "club_id": test_club["club_id"],
            "user_id": member["user_id"],
            "role": "member",
            "joined_at": datetime.utcnow(),
        })

        # Try to invite their email
        response = await client.post(
            f"/api/book-clubs/{test_club['club_id']}/invitations",
            headers={"Authorization": inviter["token"]},
            json={"email": member["email"]},
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_email_invitation_invalid_email(
        self,
        client: AsyncClient,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
    ):
        """Test sending invitation to invalid email."""
        inviter = test_users["user0"]

        response = await client.post(
            f"/api/book-clubs/{test_club['club_id']}/invitations",
            headers={"Authorization": inviter["token"]},
            json={"email": "invalid-email"},
        )

        assert response.status_code == 422


class TestAcceptInvitation:
    """Test accepting invitations."""

    @pytest_asyncio.fixture
    async def pending_invitation(
        self,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a pending invitation."""
        invitation_id = f"invitation_{ObjectId()}"
        inviter = test_users["user0"]
        invitee = test_users["user1"]

        await db.club_invitations.insert_one({
            "invitation_id": invitation_id,
            "club_id": test_club["club_id"],
            "inviter_id": inviter["user_id"],
            "invitee_user_id": invitee["user_id"],
            "message": "Join us!",
            "status": "pending",
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=7),
        })

        invitation = {"invitation_id": invitation_id}

        yield invitation

        # Cleanup handled by test_club fixture

    @pytest.mark.asyncio
    async def test_accept_invitation(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
        pending_invitation: Dict[str, Any],
    ):
        """Test accepting an invitation."""
        invitee = test_users["user1"]

        response = await client.post(
            f"/api/book-clubs/invitations/{pending_invitation['invitation_id']}/accept",
            headers={"Authorization": invitee["token"]},
        )

        assert response.status_code == 200

        # Verify status updated
        invitation_doc = await db.club_invitations.find_one({
            "invitation_id": pending_invitation["invitation_id"]
        })

        assert invitation_doc["status"] == "accepted"

        # Verify user added as member
        member_doc = await db.club_members.find_one({
            "club_id": test_club["club_id"],
            "user_id": invitee["user_id"],
        })

        assert member_doc is not None
        assert member_doc["role"] == "member"

    @pytest.mark.asyncio
    async def test_accept_expired_invitation(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
    ):
        """Test accepting an expired invitation."""
        invitation_id = f"expired_{ObjectId()}"
        invitee = test_users["user1"]

        # Create expired invitation
        await db.club_invitations.insert_one({
            "invitation_id": invitation_id,
            "club_id": test_club["club_id"],
            "inviter_id": test_users["user0"]["user_id"],
            "invitee_user_id": invitee["user_id"],
            "status": "pending",
            "created_at": datetime.utcnow() - timedelta(days=8),
            "expires_at": datetime.utcnow() - timedelta(days=1),  # Expired
        })

        response = await client.post(
            f"/api/book-clubs/invitations/{invitation_id}/accept",
            headers={"Authorization": invitee["token"]},
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_cannot_accept_someone_elses_invitation(
        self,
        client: AsyncClient,
        test_users: Dict[str, Dict[str, Any]],
        pending_invitation: Dict[str, Any],
    ):
        """Test that user cannot accept invitation meant for someone else."""
        wrong_user = test_users["user2"]

        response = await client.post(
            f"/api/book-clubs/invitations/{pending_invitation['invitation_id']}/accept",
            headers={"Authorization": wrong_user["token"]},
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_cannot_accept_already_accepted_invitation(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        pending_invitation: Dict[str, Any],
    ):
        """Test cannot accept invitation twice."""
        invitee = test_users["user1"]

        # Accept once
        await client.post(
            f"/api/book-clubs/invitations/{pending_invitation['invitation_id']}/accept",
            headers={"Authorization": invitee["token"]},
        )

        # Try to accept again
        response = await client.post(
            f"/api/book-clubs/invitations/{pending_invitation['invitation_id']}/accept",
            headers={"Authorization": invitee["token"]},
        )

        assert response.status_code == 400


class TestDeclineInvitation:
    """Test declining invitations."""

    @pytest_asyncio.fixture
    async def pending_invitation(
        self,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a pending invitation."""
        invitation_id = f"invitation_{ObjectId()}"
        inviter = test_users["user0"]
        invitee = test_users["user1"]

        await db.club_invitations.insert_one({
            "invitation_id": invitation_id,
            "club_id": test_club["club_id"],
            "inviter_id": inviter["user_id"],
            "invitee_user_id": invitee["user_id"],
            "status": "pending",
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=7),
        })

        invitation = {"invitation_id": invitation_id}

        yield invitation

    @pytest.mark.asyncio
    async def test_decline_invitation(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        pending_invitation: Dict[str, Any],
    ):
        """Test declining an invitation."""
        invitee = test_users["user1"]

        response = await client.post(
            f"/api/book-clubs/invitations/{pending_invitation['invitation_id']}/decline",
            headers={"Authorization": invitee["token"]},
        )

        assert response.status_code == 200

        # Verify status updated
        invitation_doc = await db.club_invitations.find_one({
            "invitation_id": pending_invitation["invitation_id"]
        })

        assert invitation_doc["status"] == "declined"

    @pytest.mark.asyncio
    async def test_cannot_decline_someone_elses_invitation(
        self,
        client: AsyncClient,
        test_users: Dict[str, Dict[str, Any]],
        pending_invitation: Dict[str, Any],
    ):
        """Test that user cannot decline invitation meant for someone else."""
        wrong_user = test_users["user2"]

        response = await client.post(
            f"/api/book-clubs/invitations/{pending_invitation['invitation_id']}/decline",
            headers={"Authorization": wrong_user["token"]},
        )

        assert response.status_code == 403


class TestCancelInvitation:
    """Test canceling invitations."""

    @pytest_asyncio.fixture
    async def pending_invitation(
        self,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a pending invitation."""
        invitation_id = f"invitation_{ObjectId()}"
        inviter = test_users["user0"]
        invitee = test_users["user1"]

        await db.club_invitations.insert_one({
            "invitation_id": invitation_id,
            "club_id": test_club["club_id"],
            "inviter_id": inviter["user_id"],
            "invitee_user_id": invitee["user_id"],
            "status": "pending",
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=7),
        })

        invitation = {"invitation_id": invitation_id}

        yield invitation

    @pytest.mark.asyncio
    async def test_cancel_invitation(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        pending_invitation: Dict[str, Any],
    ):
        """Test canceling an invitation."""
        inviter = test_users["user0"]

        response = await client.delete(
            f"/api/book-clubs/invitations/{pending_invitation['invitation_id']}",
            headers={"Authorization": inviter["token"]},
        )

        assert response.status_code == 200

        # Verify status updated
        invitation_doc = await db.club_invitations.find_one({
            "invitation_id": pending_invitation["invitation_id"]
        })

        assert invitation_doc["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_only_inviter_can_cancel(
        self,
        client: AsyncClient,
        test_users: Dict[str, Dict[str, Any]],
        pending_invitation: Dict[str, Any],
    ):
        """Test that only inviter can cancel invitation."""
        other_user = test_users["user2"]

        response = await client.delete(
            f"/api/book-clubs/invitations/{pending_invitation['invitation_id']}",
            headers={"Authorization": other_user["token"]},
        )

        assert response.status_code == 403


class TestListInvitations:
    """Test listing invitations."""

    @pytest.mark.asyncio
    async def test_list_club_invitations(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
    ):
        """Test listing all invitations for a club."""
        inviter = test_users["user0"]

        # Create some invitations
        for i in [1, 2]:
            await db.club_invitations.insert_one({
                "invitation_id": f"invitation_{i}_{ObjectId()}",
                "club_id": test_club["club_id"],
                "inviter_id": inviter["user_id"],
                "invitee_user_id": test_users[f"user{i}"]["user_id"],
                "status": "pending",
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(days=7),
            })

        response = await client.get(
            f"/api/book-clubs/{test_club['club_id']}/invitations",
            headers={"Authorization": inviter["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        assert "invitations" in data
        assert len(data["invitations"]) >= 2

    @pytest.mark.asyncio
    async def test_list_user_received_invitations(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
    ):
        """Test listing invitations received by a user."""
        invitee = test_users["user1"]

        # Create invitation
        await db.club_invitations.insert_one({
            "invitation_id": f"invitation_{ObjectId()}",
            "club_id": test_club["club_id"],
            "inviter_id": test_users["user0"]["user_id"],
            "invitee_user_id": invitee["user_id"],
            "status": "pending",
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=7),
        })

        response = await client.get(
            "/api/book-clubs/invitations/received",
            headers={"Authorization": invitee["token"]},
        )

        assert response.status_code == 200
        data = response.json()

        assert "invitations" in data
        assert len(data["invitations"]) >= 1


class TestEmailInvitationToken:
    """Test email invitation token functionality."""

    @pytest.mark.asyncio
    async def test_accept_invitation_by_token(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
    ):
        """Test accepting invitation using token."""
        invitation_token = f"token_{ObjectId()}"
        email = "newuser@test.com"

        # Create email invitation
        invitation_id = f"invitation_{ObjectId()}"
        await db.club_invitations.insert_one({
            "invitation_id": invitation_id,
            "club_id": test_club["club_id"],
            "inviter_id": test_users["user0"]["user_id"],
            "invitee_email": email,
            "invitation_token": invitation_token,
            "status": "pending",
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=7),
        })

        # Accept by token (public endpoint)
        response = await client.post(
            f"/api/book-clubs/invitations/accept-by-token/{invitation_token}",
        )

        # Should either succeed or require auth
        assert response.status_code in [200, 401]

    @pytest.mark.asyncio
    async def test_invalid_invitation_token(
        self,
        client: AsyncClient,
    ):
        """Test using invalid invitation token."""
        fake_token = f"fake_token_{ObjectId()}"

        response = await client.post(
            f"/api/book-clubs/invitations/accept-by-token/{fake_token}",
        )

        assert response.status_code in [404, 401]

    @pytest.mark.asyncio
    async def test_expired_token_invitation(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
    ):
        """Test accepting invitation with expired token."""
        invitation_token = f"expired_token_{ObjectId()}"

        # Create expired invitation
        await db.club_invitations.insert_one({
            "invitation_id": f"invitation_{ObjectId()}",
            "club_id": test_club["club_id"],
            "inviter_id": test_users["user0"]["user_id"],
            "invitee_email": "newuser@test.com",
            "invitation_token": invitation_token,
            "status": "pending",
            "created_at": datetime.utcnow() - timedelta(days=8),
            "expires_at": datetime.utcnow() - timedelta(days=1),  # Expired
        })

        response = await client.post(
            f"/api/book-clubs/invitations/accept-by-token/{invitation_token}",
        )

        assert response.status_code in [400, 401, 404]


class TestEdgeCases:
    """Test edge cases for invitations."""

    @pytest.mark.asyncio
    async def test_send_duplicate_invitation(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_club: Dict[str, Any],
    ):
        """Test sending duplicate invitation to same user."""
        inviter = test_users["user0"]
        invitee = test_users["user1"]

        # Send first invitation
        await client.post(
            f"/api/book-clubs/{test_club['club_id']}/invitations",
            headers={"Authorization": inviter["token"]},
            json={"user_id": invitee["user_id"]},
        )

        # Try to send again
        response = await client.post(
            f"/api/book-clubs/{test_club['club_id']}/invitations",
            headers={"Authorization": inviter["token"]},
            json={"user_id": invitee["user_id"]},
        )

        # Should fail or replace existing
        assert response.status_code in [400, 201]

    @pytest.mark.asyncio
    async def test_invitation_to_private_club_non_member(
        self,
        client: AsyncClient,
        db: Database,
        test_users: Dict[str, Dict[str, Any]],
        test_book: Dict[str, Any],
    ):
        """Test non-member cannot send invitation to private club."""
        creator = test_users["user0"]
        non_member = test_users["user1"]
        invitee = test_users["user2"]

        # Create private club
        club_id = f"private_club_{ObjectId()}"
        await db.book_clubs.insert_one({
            "club_id": club_id,
            "name": "Private Club",
            "book_id": test_book["book_id"],
            "creator_id": creator["user_id"],
            "visibility": "private",
            "description": "Private",
            "settings": {"require_approval": True},
            "stats": {"member_count": 1, "discussion_count": 0},
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
        })

        # Non-member tries to invite
        response = await client.post(
            f"/api/book-clubs/{club_id}/invitations",
            headers={"Authorization": non_member["token"]},
            json={"user_id": invitee["user_id"]},
        )

        assert response.status_code == 403

        # Cleanup
        await db.book_clubs.delete_one({"club_id": club_id})
