"""
Tests for User Management API endpoints.

Tests cover:
- POST /api/v1/admin/users/invite - Create platform invitation
- GET /api/v1/admin/users/invites - List invitations with filters
- GET /api/v1/admin/users/invites/stats - Get invitation statistics
- GET /api/v1/admin/users/invites/{id} - Get invitation details
- POST /api/v1/admin/users/invites/{id}/resend - Resend invitation email
- DELETE /api/v1/admin/users/invites/{id} - Revoke invitation
- GET /api/v1/users/invites/verify/{token} - Verify invitation token (public)
- GET /api/v1/admin/users/{user_id} - Get user details
- POST /api/v1/auth/signup with invite_token - Signup with invitation
"""

import pytest
from datetime import datetime, timedelta
from bson import ObjectId
from tests.conftest import create_auth_header
import secrets


class TestPlatformInvitations:
    """Test suite for platform invitation functionality."""

    @pytest.fixture
    async def test_invite(self, test_db):
        """Create a test invitation in the database."""
        invite = {
            "_id": ObjectId(),
            "email": "testinvite@test.com",
            "role": "user",
            "status": "pending",
            "token": secrets.token_urlsafe(32),
            "invited_by_id": "693acf37d221b83bb8f2d2a7",
            "invited_by_name": "Test Admin",
            "invited_by_email": "admin@freshmanna.com",
            "message": "Welcome to FreshManna!",
            "invited_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=7),
            "email_count": 1,
            "last_email_sent_at": datetime.utcnow()
        }
        await test_db.platform_invites.insert_one(invite)
        yield invite
        # Cleanup
        await test_db.platform_invites.delete_one({"_id": invite["_id"]})

    @pytest.fixture
    async def expired_invite(self, test_db):
        """Create an expired test invitation."""
        invite = {
            "_id": ObjectId(),
            "email": "expired@test.com",
            "role": "user",
            "status": "pending",
            "token": secrets.token_urlsafe(32),
            "invited_by_id": "693acf37d221b83bb8f2d2a7",
            "invited_by_name": "Test Admin",
            "invited_by_email": "admin@freshmanna.com",
            "invited_at": datetime.utcnow() - timedelta(days=14),
            "expires_at": datetime.utcnow() - timedelta(days=7),  # Expired
            "email_count": 1
        }
        await test_db.platform_invites.insert_one(invite)
        yield invite
        await test_db.platform_invites.delete_one({"_id": invite["_id"]})

    # ============ Create Invitation Tests ============

    @pytest.mark.asyncio
    async def test_create_invite_success(self, client, admin_token, test_db):
        """
        Test creating a platform invitation.
        Expected: Returns 201 with invitation details.
        """
        test_email = f"newinvite_{secrets.token_hex(4)}@test.com"

        response = client.post(
            "/api/v1/admin/users/invite",
            headers=create_auth_header(admin_token),
            json={
                "email": test_email,
                "role": "user",
                "message": "Join us on FreshManna!"
            }
        )

        assert response.status_code == 201
        data = response.json()

        assert data["email"] == test_email
        assert data["role"] == "user"
        assert data["status"] == "pending"
        assert data["message"] == "Join us on FreshManna!"
        assert "id" in data
        assert "invited_at" in data
        assert "expires_at" in data

        # Cleanup
        await test_db.platform_invites.delete_one({"email": test_email})

    @pytest.mark.asyncio
    async def test_create_admin_invite(self, client, admin_token, test_db):
        """
        Test creating an admin invitation.
        Expected: Returns 201 with admin role.
        """
        test_email = f"admintest_{secrets.token_hex(4)}@test.com"

        response = client.post(
            "/api/v1/admin/users/invite",
            headers=create_auth_header(admin_token),
            json={
                "email": test_email,
                "role": "admin"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["role"] == "admin"

        # Cleanup
        await test_db.platform_invites.delete_one({"email": test_email})

    @pytest.mark.asyncio
    async def test_create_invite_duplicate_pending(
        self, client, admin_token, test_invite
    ):
        """
        Test creating duplicate invitation for pending invite.
        Expected: Returns 400 error.
        """
        response = client.post(
            "/api/v1/admin/users/invite",
            headers=create_auth_header(admin_token),
            json={
                "email": test_invite["email"],
                "role": "user"
            }
        )

        assert response.status_code == 400
        assert "pending" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_invite_existing_user(
        self, client, admin_token, test_db
    ):
        """
        Test creating invitation for existing user.
        Expected: Returns 400 error.
        """
        # Use the admin's email which definitely exists
        response = client.post(
            "/api/v1/admin/users/invite",
            headers=create_auth_header(admin_token),
            json={
                "email": "admin@freshmanna.com",
                "role": "user"
            }
        )

        assert response.status_code == 400
        assert "already" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_invite_without_auth(self, client):
        """
        Test creating invitation without authentication.
        Expected: Returns 401.
        """
        response = client.post(
            "/api/v1/admin/users/invite",
            json={
                "email": "unauthorized@test.com",
                "role": "user"
            }
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_invite_invalid_email(self, client, admin_token):
        """
        Test creating invitation with invalid email.
        Expected: Returns 422.
        """
        response = client.post(
            "/api/v1/admin/users/invite",
            headers=create_auth_header(admin_token),
            json={
                "email": "not-an-email",
                "role": "user"
            }
        )

        assert response.status_code == 422

    # ============ List Invitations Tests ============

    @pytest.mark.asyncio
    async def test_list_invites_success(self, client, admin_token, test_invite):
        """
        Test listing platform invitations.
        Expected: Returns 200 with paginated list.
        """
        response = client.get(
            "/api/v1/admin/users/invites",
            headers=create_auth_header(admin_token)
        )

        assert response.status_code == 200
        data = response.json()

        assert "invites" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_list_invites_with_status_filter(
        self, client, admin_token, test_invite
    ):
        """
        Test listing invitations filtered by status.
        Expected: Returns only pending invitations.
        """
        response = client.get(
            "/api/v1/admin/users/invites?status=pending",
            headers=create_auth_header(admin_token)
        )

        assert response.status_code == 200
        data = response.json()

        # All returned invites should be pending
        for invite in data["invites"]:
            assert invite["status"] == "pending"

    @pytest.mark.asyncio
    async def test_list_invites_with_search(
        self, client, admin_token, test_invite
    ):
        """
        Test searching invitations by email.
        Expected: Returns matching invitations.
        """
        response = client.get(
            f"/api/v1/admin/users/invites?search={test_invite['email']}",
            headers=create_auth_header(admin_token)
        )

        assert response.status_code == 200
        data = response.json()

        # Should find our test invite
        emails = [i["email"] for i in data["invites"]]
        assert test_invite["email"] in emails

    @pytest.mark.asyncio
    async def test_list_invites_pagination(
        self, client, admin_token, test_db
    ):
        """
        Test invitation list pagination.
        Expected: Returns correct page of results.
        """
        # Create multiple invites
        invites = []
        for i in range(5):
            invite = {
                "_id": ObjectId(),
                "email": f"paginate_{i}@test.com",
                "role": "user",
                "status": "pending",
                "token": secrets.token_urlsafe(32),
                "invited_by_id": "693acf37d221b83bb8f2d2a7",
                "invited_by_name": "Test Admin",
                "invited_by_email": "admin@freshmanna.com",
                "invited_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(days=7),
                "email_count": 1
            }
            invites.append(invite)

        await test_db.platform_invites.insert_many(invites)

        # Request first page with small page size
        response = client.get(
            "/api/v1/admin/users/invites?page=1&page_size=2",
            headers=create_auth_header(admin_token)
        )

        assert response.status_code == 200
        data = response.json()

        assert data["page"] == 1
        assert data["page_size"] == 2
        assert len(data["invites"]) <= 2

        # Cleanup
        await test_db.platform_invites.delete_many({
            "_id": {"$in": [i["_id"] for i in invites]}
        })

    # ============ Get Invitation Stats Tests ============

    @pytest.mark.asyncio
    async def test_get_invite_stats(self, client, admin_token, test_invite):
        """
        Test getting invitation statistics.
        Expected: Returns stats with counts.
        """
        response = client.get(
            "/api/v1/admin/users/invites/stats",
            headers=create_auth_header(admin_token)
        )

        assert response.status_code == 200
        data = response.json()

        assert "total_invites" in data
        assert "pending_invites" in data
        assert "accepted_invites" in data
        assert "expired_invites" in data
        assert "revoked_invites" in data
        assert "invites_this_week" in data
        assert "acceptance_rate" in data
        assert data["pending_invites"] >= 1

    # ============ Get Invitation Detail Tests ============

    @pytest.mark.asyncio
    async def test_get_invite_by_id(self, client, admin_token, test_invite):
        """
        Test getting a specific invitation.
        Expected: Returns 200 with invite details.
        """
        invite_id = str(test_invite["_id"])

        response = client.get(
            f"/api/v1/admin/users/invites/{invite_id}",
            headers=create_auth_header(admin_token)
        )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == invite_id
        assert data["email"] == test_invite["email"]
        assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_get_invite_not_found(self, client, admin_token):
        """
        Test getting non-existent invitation.
        Expected: Returns 404.
        """
        fake_id = str(ObjectId())

        response = client.get(
            f"/api/v1/admin/users/invites/{fake_id}",
            headers=create_auth_header(admin_token)
        )

        assert response.status_code == 404

    # ============ Resend Invitation Tests ============

    @pytest.mark.asyncio
    async def test_resend_invite_success(
        self, client, admin_token, test_invite, test_db
    ):
        """
        Test resending an invitation email.
        Expected: Returns 200 and increments email count.
        """
        invite_id = str(test_invite["_id"])
        original_email_count = test_invite["email_count"]

        response = client.post(
            f"/api/v1/admin/users/invites/{invite_id}/resend",
            headers=create_auth_header(admin_token)
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify email count increased
        updated = await test_db.platform_invites.find_one(
            {"_id": test_invite["_id"]}
        )
        assert updated["email_count"] == original_email_count + 1

    @pytest.mark.asyncio
    async def test_resend_invite_extends_expiry(
        self, client, admin_token, test_invite, test_db
    ):
        """
        Test that resending extends expiry date.
        Expected: Expiry is extended by 7 days from now.
        """
        invite_id = str(test_invite["_id"])
        original_expiry = test_invite["expires_at"]

        response = client.post(
            f"/api/v1/admin/users/invites/{invite_id}/resend",
            headers=create_auth_header(admin_token)
        )

        assert response.status_code == 200

        # Verify expiry was extended
        updated = await test_db.platform_invites.find_one(
            {"_id": test_invite["_id"]}
        )
        # New expiry should be roughly 7 days from now
        expected_expiry = datetime.utcnow() + timedelta(days=7)
        assert abs((updated["expires_at"] - expected_expiry).total_seconds()) < 60

    # ============ Revoke Invitation Tests ============

    @pytest.mark.asyncio
    async def test_revoke_invite_success(
        self, client, admin_token, test_db
    ):
        """
        Test revoking a pending invitation.
        Expected: Returns 200 and changes status to revoked.
        """
        # Create an invite to revoke
        invite = {
            "_id": ObjectId(),
            "email": "revoke@test.com",
            "role": "user",
            "status": "pending",
            "token": secrets.token_urlsafe(32),
            "invited_by_id": "693acf37d221b83bb8f2d2a7",
            "invited_by_name": "Test Admin",
            "invited_by_email": "admin@freshmanna.com",
            "invited_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=7),
            "email_count": 1
        }
        await test_db.platform_invites.insert_one(invite)
        invite_id = str(invite["_id"])

        response = client.delete(
            f"/api/v1/admin/users/invites/{invite_id}",
            headers=create_auth_header(admin_token)
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify status changed
        updated = await test_db.platform_invites.find_one({"_id": invite["_id"]})
        assert updated["status"] == "revoked"

        # Cleanup
        await test_db.platform_invites.delete_one({"_id": invite["_id"]})

    # ============ Verify Token Tests (Public) ============

    @pytest.mark.asyncio
    async def test_verify_token_valid(self, client, test_invite):
        """
        Test verifying a valid invitation token.
        Expected: Returns valid=True with invitation details.
        """
        response = client.get(
            f"/api/v1/users/invites/verify/{test_invite['token']}"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is True
        assert data["email"] == test_invite["email"]
        assert data["role"] == test_invite["role"]
        assert data["invited_by_name"] == test_invite["invited_by_name"]

    @pytest.mark.asyncio
    async def test_verify_token_expired(self, client, expired_invite):
        """
        Test verifying an expired invitation token.
        Expected: Returns valid=False with error.
        """
        response = client.get(
            f"/api/v1/users/invites/verify/{expired_invite['token']}"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is False
        assert "expired" in data["error"].lower()

    @pytest.mark.asyncio
    async def test_verify_token_invalid(self, client):
        """
        Test verifying an invalid/non-existent token.
        Expected: Returns valid=False with error.
        """
        response = client.get(
            "/api/v1/users/invites/verify/invalid-token-12345"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is False
        assert "error" in data

    @pytest.mark.asyncio
    async def test_verify_token_revoked(self, client, test_db):
        """
        Test verifying a revoked invitation token.
        Expected: Returns valid=False with error.
        """
        # Create a revoked invite
        invite = {
            "_id": ObjectId(),
            "email": "revoked@test.com",
            "role": "user",
            "status": "revoked",
            "token": secrets.token_urlsafe(32),
            "invited_by_id": "693acf37d221b83bb8f2d2a7",
            "invited_by_name": "Test Admin",
            "invited_by_email": "admin@freshmanna.com",
            "invited_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=7),
            "email_count": 1
        }
        await test_db.platform_invites.insert_one(invite)

        response = client.get(
            f"/api/v1/users/invites/verify/{invite['token']}"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is False
        assert "revoked" in data["error"].lower()

        # Cleanup
        await test_db.platform_invites.delete_one({"_id": invite["_id"]})

    # ============ Get User Details Tests ============

    @pytest.mark.asyncio
    async def test_get_user_details(self, client, admin_token, test_db):
        """
        Test getting user details.
        Expected: Returns 200 with user stats.
        """
        # Create a test user
        user = {
            "_id": ObjectId(),
            "email": "detailuser@test.com",
            "name": "Detail User",
            "role": "user",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        await test_db.users.insert_one(user)

        response = client.get(
            f"/api/v1/admin/users/{str(user['_id'])}",
            headers=create_auth_header(admin_token)
        )

        assert response.status_code == 200
        data = response.json()

        assert data["email"] == user["email"]
        assert "devotional_count" in data or "id" in data

        # Cleanup
        await test_db.users.delete_one({"_id": user["_id"]})

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, client, admin_token):
        """
        Test getting non-existent user.
        Expected: Returns 404.
        """
        fake_id = str(ObjectId())

        response = client.get(
            f"/api/v1/admin/users/{fake_id}",
            headers=create_auth_header(admin_token)
        )

        assert response.status_code == 404


class TestSignupWithInvite:
    """Test suite for signup with invitation token."""

    @pytest.fixture
    async def valid_invite_for_signup(self, test_db):
        """Create a valid invite for signup testing."""
        test_email = f"signuptest_{secrets.token_hex(4)}@test.com"
        invite = {
            "_id": ObjectId(),
            "email": test_email,
            "role": "admin",  # Testing admin role assignment
            "status": "pending",
            "token": secrets.token_urlsafe(32),
            "invited_by_id": "693acf37d221b83bb8f2d2a7",
            "invited_by_name": "Test Admin",
            "invited_by_email": "admin@freshmanna.com",
            "message": "Welcome!",
            "invited_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=7),
            "email_count": 1
        }
        await test_db.platform_invites.insert_one(invite)
        yield invite
        # Cleanup invite and any created user
        await test_db.platform_invites.delete_one({"_id": invite["_id"]})
        await test_db.users.delete_one({"email": test_email})

    @pytest.mark.asyncio
    async def test_signup_with_valid_invite(
        self, client, valid_invite_for_signup, test_db
    ):
        """
        Test signup with a valid invitation token.
        Expected: Creates user with role from invite, marks invite accepted.
        """
        invite = valid_invite_for_signup

        response = client.post(
            f"/api/v1/auth/signup?invite_token={invite['token']}",
            json={
                "email": invite["email"],
                "password": "TestPass@123",
                "name": "Test Signup User"
            }
        )

        assert response.status_code == 201
        data = response.json()

        # Verify user was created with correct role
        assert data["user"]["role"] == "admin"  # From invite
        assert data["user"]["email"] == invite["email"]
        assert "access_token" in data

        # Verify invite was marked as accepted
        updated_invite = await test_db.platform_invites.find_one(
            {"_id": invite["_id"]}
        )
        assert updated_invite["status"] == "accepted"
        assert updated_invite["accepted_at"] is not None

    @pytest.mark.asyncio
    async def test_signup_with_email_mismatch(
        self, client, valid_invite_for_signup
    ):
        """
        Test signup with invite but different email.
        Expected: Returns 400 error about email mismatch.
        """
        invite = valid_invite_for_signup

        response = client.post(
            f"/api/v1/auth/signup?invite_token={invite['token']}",
            json={
                "email": "different@email.com",
                "password": "TestPass@123",
                "name": "Different User"
            }
        )

        assert response.status_code == 400
        assert "match" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_signup_with_expired_invite(
        self, client, test_db
    ):
        """
        Test signup with expired invitation token.
        Expected: Returns 400 error about expired invite.
        """
        test_email = f"expiredsignup_{secrets.token_hex(4)}@test.com"
        invite = {
            "_id": ObjectId(),
            "email": test_email,
            "role": "user",
            "status": "pending",
            "token": secrets.token_urlsafe(32),
            "invited_by_id": "693acf37d221b83bb8f2d2a7",
            "invited_by_name": "Test Admin",
            "invited_by_email": "admin@freshmanna.com",
            "invited_at": datetime.utcnow() - timedelta(days=14),
            "expires_at": datetime.utcnow() - timedelta(days=7),
            "email_count": 1
        }
        await test_db.platform_invites.insert_one(invite)

        response = client.post(
            f"/api/v1/auth/signup?invite_token={invite['token']}",
            json={
                "email": test_email,
                "password": "TestPass@123",
                "name": "Expired User"
            }
        )

        assert response.status_code == 400
        assert "expired" in response.json()["detail"].lower()

        # Cleanup
        await test_db.platform_invites.delete_one({"_id": invite["_id"]})

    @pytest.mark.asyncio
    async def test_signup_with_invalid_invite_token(self, client):
        """
        Test signup with non-existent invitation token.
        Expected: Returns 400 error about invalid token.
        """
        response = client.post(
            "/api/v1/auth/signup?invite_token=invalid-token-xyz",
            json={
                "email": "noinvite@test.com",
                "password": "TestPass@123",
                "name": "No Invite User"
            }
        )

        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()


class TestInviteWorkflow:
    """End-to-end workflow tests for the invitation system."""

    @pytest.mark.asyncio
    async def test_complete_invite_workflow(
        self, client, admin_token, test_db
    ):
        """
        Test complete invitation workflow: create, verify, signup.
        Expected: All steps succeed and user is created correctly.
        """
        test_email = f"workflow_{secrets.token_hex(4)}@test.com"

        # Step 1: Admin creates invitation
        create_response = client.post(
            "/api/v1/admin/users/invite",
            headers=create_auth_header(admin_token),
            json={
                "email": test_email,
                "role": "user",
                "message": "Welcome to the team!"
            }
        )
        assert create_response.status_code == 201
        invite_data = create_response.json()
        invite_id = invite_data["id"]

        # Step 2: Get the invite token from DB (simulating email link)
        invite_doc = await test_db.platform_invites.find_one(
            {"_id": ObjectId(invite_id)}
        )
        token = invite_doc["token"]

        # Step 3: User verifies token on signup page
        verify_response = client.get(
            f"/api/v1/users/invites/verify/{token}"
        )
        assert verify_response.status_code == 200
        verify_data = verify_response.json()
        assert verify_data["valid"] is True
        assert verify_data["email"] == test_email

        # Step 4: User signs up with the token
        signup_response = client.post(
            f"/api/v1/auth/signup?invite_token={token}",
            json={
                "email": test_email,
                "password": "WorkflowPass@123",
                "name": "Workflow Test User"
            }
        )
        assert signup_response.status_code == 201
        signup_data = signup_response.json()
        assert signup_data["user"]["email"] == test_email

        # Step 5: Verify invite is marked as accepted
        updated_invite = await test_db.platform_invites.find_one(
            {"_id": ObjectId(invite_id)}
        )
        assert updated_invite["status"] == "accepted"

        # Step 6: Verify can list invites and see accepted status
        list_response = client.get(
            f"/api/v1/admin/users/invites?search={test_email}",
            headers=create_auth_header(admin_token)
        )
        assert list_response.status_code == 200
        list_data = list_response.json()
        found_invite = next(
            (i for i in list_data["invites"] if i["email"] == test_email),
            None
        )
        assert found_invite is not None
        assert found_invite["status"] == "accepted"

        # Cleanup
        await test_db.platform_invites.delete_one({"_id": ObjectId(invite_id)})
        await test_db.users.delete_one({"email": test_email})

    @pytest.mark.asyncio
    async def test_invite_resend_and_use(
        self, client, admin_token, test_db
    ):
        """
        Test resending an invite and then using it.
        Expected: Resend extends expiry, user can still sign up.
        """
        test_email = f"resenduse_{secrets.token_hex(4)}@test.com"

        # Create invite
        create_response = client.post(
            "/api/v1/admin/users/invite",
            headers=create_auth_header(admin_token),
            json={
                "email": test_email,
                "role": "user"
            }
        )
        assert create_response.status_code == 201
        invite_id = create_response.json()["id"]

        # Resend invite
        resend_response = client.post(
            f"/api/v1/admin/users/invites/{invite_id}/resend",
            headers=create_auth_header(admin_token)
        )
        assert resend_response.status_code == 200

        # Get token and sign up
        invite_doc = await test_db.platform_invites.find_one(
            {"_id": ObjectId(invite_id)}
        )
        assert invite_doc["email_count"] == 2  # Original + resend

        signup_response = client.post(
            f"/api/v1/auth/signup?invite_token={invite_doc['token']}",
            json={
                "email": test_email,
                "password": "ResendPass@123",
                "name": "Resend Test User"
            }
        )
        assert signup_response.status_code == 201

        # Cleanup
        await test_db.platform_invites.delete_one({"_id": ObjectId(invite_id)})
        await test_db.users.delete_one({"email": test_email})

    @pytest.mark.asyncio
    async def test_invite_revoke_prevents_signup(
        self, client, admin_token, test_db
    ):
        """
        Test that revoking an invite prevents signup.
        Expected: Signup fails after revocation.
        """
        test_email = f"revokeprev_{secrets.token_hex(4)}@test.com"

        # Create invite
        create_response = client.post(
            "/api/v1/admin/users/invite",
            headers=create_auth_header(admin_token),
            json={
                "email": test_email,
                "role": "user"
            }
        )
        invite_id = create_response.json()["id"]

        # Get token before revoking
        invite_doc = await test_db.platform_invites.find_one(
            {"_id": ObjectId(invite_id)}
        )
        token = invite_doc["token"]

        # Revoke the invite
        revoke_response = client.delete(
            f"/api/v1/admin/users/invites/{invite_id}",
            headers=create_auth_header(admin_token)
        )
        assert revoke_response.status_code == 200

        # Try to sign up with revoked token
        signup_response = client.post(
            f"/api/v1/auth/signup?invite_token={token}",
            json={
                "email": test_email,
                "password": "RevokePass@123",
                "name": "Revoke Test User"
            }
        )
        assert signup_response.status_code == 400
        assert "revoked" in signup_response.json()["detail"].lower()

        # Cleanup
        await test_db.platform_invites.delete_one({"_id": ObjectId(invite_id)})
