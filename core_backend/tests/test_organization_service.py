"""Unit tests for Organization Service."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any

from ..backend.models import (
    Organization, OrganizationUser, OrganizationInvitation,
    OrganizationCreate, OrganizationUpdate, OrganizationUserUpdate,
    OrganizationInviteRequest, OrganizationRole, InvitationStatus
)
from ..backend.services.organization_service import MongoDBOrganizationService


@pytest.fixture
def mock_mongodb():
    """Mock MongoDB connection and collections."""
    with patch('pymongo.MongoClient') as mock_client:
        # Mock client and database
        mock_client_instance = MagicMock()
        mock_db = MagicMock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.__getitem__.return_value = mock_db

        # Mock collections
        mock_organizations = MagicMock()
        mock_organization_users = MagicMock()
        mock_organization_invitations = MagicMock()

        def mock_get_collection(name):
            collection_map = {
                "organizations": mock_organizations,
                "organization_users": mock_organization_users,
                "organization_invitations": mock_organization_invitations
            }
            return collection_map.get(name, MagicMock())

        mock_db.__getitem__.side_effect = mock_get_collection

        yield {
            "client": mock_client_instance,
            "db": mock_db,
            "organizations": mock_organizations,
            "organization_users": mock_organization_users,
            "organization_invitations": mock_organization_invitations
        }


@pytest.fixture
def organization_service(mock_mongodb):
    """Create organization service instance with mocked MongoDB."""
    service = MongoDBOrganizationService()
    service.organizations = mock_mongodb["organizations"]
    service.organization_users = mock_mongodb["organization_users"]
    service.organization_invitations = mock_mongodb["organization_invitations"]
    return service


@pytest.fixture
def sample_organization_data():
    """Sample organization creation data."""
    return OrganizationCreate(
        name="Test Organization",
        display_name="Test Org",
        description="A test organization",
        industry="Technology",
        website="https://test.org"
    )


@pytest.fixture
def sample_organization():
    """Sample organization model."""
    return Organization(
        id="test-org-id",
        name="Test Organization",
        display_name="Test Org",
        description="A test organization",
        industry="Technology",
        website="https://test.org"
    )


@pytest.fixture
def sample_organization_user():
    """Sample organization user model."""
    return OrganizationUser(
        id="test-user-id",
        organization_id="test-org-id",
        user_id="test-supabase-user-id",
        email="test@example.com",
        role=OrganizationRole.OWNER,
        display_name="Test User"
    )


class TestOrganizationCRUD:
    """Test organization CRUD operations."""

    def test_create_organization(self, organization_service, mock_mongodb, sample_organization_data):
        """Test creating a new organization."""
        # Mock insert_one to return success
        mock_mongodb["organizations"].insert_one.return_value = Mock(inserted_id="test-org-id")
        mock_mongodb["organization_users"].insert_one.return_value = Mock(inserted_id="test-user-id")

        # Create organization
        result = organization_service.create_organization(
            sample_organization_data,
            "test-user-id",
            "test@example.com"
        )

        # Verify organization was created
        assert result.name == sample_organization_data.name
        assert result.display_name == sample_organization_data.display_name

        # Verify database calls
        mock_mongodb["organizations"].insert_one.assert_called_once()
        mock_mongodb["organization_users"].insert_one.assert_called_once()

        # Verify owner user was created
        user_call_args = mock_mongodb["organization_users"].insert_one.call_args[0][0]
        assert user_call_args["role"] == OrganizationRole.OWNER
        assert user_call_args["email"] == "test@example.com"

    def test_get_organization(self, organization_service, mock_mongodb, sample_organization):
        """Test getting an organization by ID."""
        # Mock find_one to return organization data
        mock_mongodb["organizations"].find_one.return_value = sample_organization.model_dump()

        result = organization_service.get_organization("test-org-id")

        assert result is not None
        assert result.id == sample_organization.id
        assert result.name == sample_organization.name
        mock_mongodb["organizations"].find_one.assert_called_once_with({"id": "test-org-id"})

    def test_get_organization_not_found(self, organization_service, mock_mongodb):
        """Test getting non-existent organization."""
        mock_mongodb["organizations"].find_one.return_value = None

        result = organization_service.get_organization("non-existent-id")

        assert result is None
        mock_mongodb["organizations"].find_one.assert_called_once_with({"id": "non-existent-id"})

    def test_get_organizations_for_user(self, organization_service, mock_mongodb, sample_organization):
        """Test getting organizations for a user."""
        # Mock user memberships
        mock_mongodb["organization_users"].find.return_value = [
            {"organization_id": "test-org-id", "user_id": "test-user-id"}
        ]

        # Mock organizations
        mock_mongodb["organizations"].find.return_value = [sample_organization.model_dump()]

        result = organization_service.get_organizations_for_user("test-user-id")

        assert len(result) == 1
        assert result[0].id == sample_organization.id

    def test_update_organization(self, organization_service, mock_mongodb, sample_organization):
        """Test updating an organization."""
        update_data = OrganizationUpdate(
            name="Updated Organization",
            description="Updated description"
        )

        # Mock update and find operations
        mock_mongodb["organizations"].update_one.return_value = Mock(modified_count=1)
        mock_mongodb["organizations"].find_one.return_value = {
            **sample_organization.model_dump(),
            "name": "Updated Organization",
            "description": "Updated description"
        }

        result = organization_service.update_organization("test-org-id", update_data)

        assert result is not None
        assert result.name == "Updated Organization"
        assert result.description == "Updated description"

        # Verify update call
        mock_mongodb["organizations"].update_one.assert_called_once()
        update_call_args = mock_mongodb["organizations"].update_one.call_args
        assert update_call_args[0][0] == {"id": "test-org-id"}
        assert "name" in update_call_args[0][1]["$set"]
        assert "description" in update_call_args[0][1]["$set"]

    def test_delete_organization(self, organization_service, mock_mongodb):
        """Test deleting an organization (soft delete)."""
        mock_mongodb["organizations"].update_one.return_value = Mock(modified_count=1)

        result = organization_service.delete_organization("test-org-id")

        assert result is True

        # Verify soft delete call
        mock_mongodb["organizations"].update_one.assert_called_once()
        update_call_args = mock_mongodb["organizations"].update_one.call_args
        assert update_call_args[0][0] == {"id": "test-org-id"}
        assert update_call_args[0][1]["$set"]["is_active"] is False


class TestUserManagement:
    """Test user management within organizations."""

    def test_get_organization_users(self, organization_service, mock_mongodb, sample_organization_user):
        """Test getting all users in an organization."""
        mock_mongodb["organization_users"].find.return_value = [sample_organization_user.model_dump()]

        result = organization_service.get_organization_users("test-org-id")

        assert len(result) == 1
        assert result[0].id == sample_organization_user.id
        assert result[0].role == OrganizationRole.OWNER

    def test_get_user_in_organization(self, organization_service, mock_mongodb, sample_organization_user):
        """Test getting specific user in organization."""
        mock_mongodb["organization_users"].find_one.return_value = sample_organization_user.model_dump()

        result = organization_service.get_user_in_organization("test-org-id", "test-user-id")

        assert result is not None
        assert result.id == sample_organization_user.id

    def test_update_organization_user(self, organization_service, mock_mongodb, sample_organization_user):
        """Test updating user role in organization."""
        update_data = OrganizationUserUpdate(role=OrganizationRole.ADMIN)

        mock_mongodb["organization_users"].update_one.return_value = Mock(modified_count=1)
        mock_mongodb["organization_users"].find_one.return_value = {
            **sample_organization_user.model_dump(),
            "role": OrganizationRole.ADMIN
        }

        result = organization_service.update_organization_user("test-org-id", "test-user-id", update_data)

        assert result is not None
        assert result.role == OrganizationRole.ADMIN

    def test_remove_user_from_organization(self, organization_service, mock_mongodb):
        """Test removing user from organization."""
        mock_mongodb["organization_users"].update_one.return_value = Mock(modified_count=1)

        result = organization_service.remove_user_from_organization("test-org-id", "test-user-id")

        assert result is True

    def test_check_user_permission_owner(self, organization_service, mock_mongodb, sample_organization_user):
        """Test permission check for organization owner."""
        mock_mongodb["organization_users"].find_one.return_value = sample_organization_user.model_dump()

        result = organization_service.check_user_permission("test-org-id", "test-user-id", "manage_users")

        assert result is True  # Owners have all permissions

    def test_check_user_permission_admin(self, organization_service, mock_mongodb, sample_organization_user):
        """Test permission check for organization admin."""
        admin_user = {**sample_organization_user.model_dump(), "role": OrganizationRole.ADMIN}
        mock_mongodb["organization_users"].find_one.return_value = admin_user

        # Admin should have manage_users permission
        result = organization_service.check_user_permission("test-org-id", "test-user-id", "manage_users")
        assert result is True

        # Admin should not have owner-only permissions
        result = organization_service.check_user_permission("test-org-id", "test-user-id", "delete_organization")
        assert result is False

    def test_check_user_permission_member(self, organization_service, mock_mongodb, sample_organization_user):
        """Test permission check for organization member."""
        member_user = {**sample_organization_user.model_dump(), "role": OrganizationRole.MEMBER}
        mock_mongodb["organization_users"].find_one.return_value = member_user

        # Member should have view permissions
        result = organization_service.check_user_permission("test-org-id", "test-user-id", "view_campaigns")
        assert result is True

        # Member should not have management permissions
        result = organization_service.check_user_permission("test-org-id", "test-user-id", "manage_users")
        assert result is False


class TestInvitationSystem:
    """Test organization invitation system."""

    def test_create_invitation(self, organization_service, mock_mongodb):
        """Test creating an invitation."""
        invite_data = OrganizationInviteRequest(
            email="newuser@example.com",
            role=OrganizationRole.MEMBER,
            message="Welcome to the team!"
        )

        mock_mongodb["organization_invitations"].insert_one.return_value = Mock(inserted_id="invite-id")

        result = organization_service.create_invitation(
            "test-org-id",
            invite_data,
            "inviter-user-id",
            "inviter@example.com"
        )

        assert result.email == invite_data.email
        assert result.role == invite_data.role
        assert result.status == InvitationStatus.PENDING
        assert result.invited_by_user_id == "inviter-user-id"

        # Verify database call
        mock_mongodb["organization_invitations"].insert_one.assert_called_once()

    def test_get_invitation_by_token(self, organization_service, mock_mongodb):
        """Test getting invitation by token."""
        invitation_data = {
            "id": "invite-id",
            "organization_id": "test-org-id",
            "email": "user@example.com",
            "role": OrganizationRole.MEMBER,
            "invitation_token": "test-token",
            "status": InvitationStatus.PENDING,
            "invited_by_user_id": "inviter-id",
            "invited_by_email": "inviter@example.com",
            "expires_at": datetime.utcnow() + timedelta(days=7),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        mock_mongodb["organization_invitations"].find_one.return_value = invitation_data

        result = organization_service.get_invitation_by_token("test-token")

        assert result is not None
        assert result.invitation_token == "test-token"
        assert result.email == "user@example.com"

    def test_accept_invitation(self, organization_service, mock_mongodb):
        """Test accepting an invitation."""
        invitation_data = {
            "id": "invite-id",
            "organization_id": "test-org-id",
            "email": "user@example.com",
            "role": OrganizationRole.MEMBER,
            "invitation_token": "test-token",
            "status": InvitationStatus.PENDING,
            "invited_by_user_id": "inviter-id",
            "invited_by_email": "inviter@example.com",
            "expires_at": datetime.utcnow() + timedelta(days=7),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        # Mock invitation lookup
        mock_mongodb["organization_invitations"].find_one.return_value = invitation_data

        # Mock existing user check (should return None)
        mock_mongodb["organization_users"].find_one.return_value = None

        # Mock user creation and invitation update
        mock_mongodb["organization_users"].insert_one.return_value = Mock(inserted_id="user-id")
        mock_mongodb["organization_invitations"].update_one.return_value = Mock(modified_count=1)

        result = organization_service.accept_invitation("test-token", "new-user-id", "user@example.com")

        assert result is not None
        assert result.organization_id == "test-org-id"
        assert result.user_id == "new-user-id"
        assert result.email == "user@example.com"
        assert result.role == OrganizationRole.MEMBER

        # Verify database calls
        mock_mongodb["organization_users"].insert_one.assert_called_once()
        mock_mongodb["organization_invitations"].update_one.assert_called()

    def test_accept_invitation_expired(self, organization_service, mock_mongodb):
        """Test accepting an expired invitation."""
        invitation_data = {
            "id": "invite-id",
            "organization_id": "test-org-id",
            "email": "user@example.com",
            "role": OrganizationRole.MEMBER,
            "invitation_token": "test-token",
            "status": InvitationStatus.PENDING,
            "invited_by_user_id": "inviter-id",
            "invited_by_email": "inviter@example.com",
            "expires_at": datetime.utcnow() - timedelta(days=1),  # Expired
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        mock_mongodb["organization_invitations"].find_one.return_value = invitation_data
        mock_mongodb["organization_invitations"].update_one.return_value = Mock(modified_count=1)

        result = organization_service.accept_invitation("test-token", "new-user-id", "user@example.com")

        assert result is None

        # Verify invitation was marked as expired
        mock_mongodb["organization_invitations"].update_one.assert_called()
        update_call_args = mock_mongodb["organization_invitations"].update_one.call_args
        assert update_call_args[0][1]["$set"]["status"] == InvitationStatus.EXPIRED

    def test_decline_invitation(self, organization_service, mock_mongodb):
        """Test declining an invitation."""
        mock_mongodb["organization_invitations"].update_one.return_value = Mock(modified_count=1)

        result = organization_service.decline_invitation("test-token", "Not interested")

        assert result is True

        # Verify database call
        mock_mongodb["organization_invitations"].update_one.assert_called_once()
        update_call_args = mock_mongodb["organization_invitations"].update_one.call_args
        assert update_call_args[0][1]["$set"]["status"] == InvitationStatus.DECLINED
        assert update_call_args[0][1]["$set"]["response_message"] == "Not interested"

    def test_cancel_invitation(self, organization_service, mock_mongodb):
        """Test cancelling a pending invitation."""
        mock_mongodb["organization_invitations"].delete_one.return_value = Mock(deleted_count=1)

        result = organization_service.cancel_invitation("invite-id")

        assert result is True

        # Verify database call
        mock_mongodb["organization_invitations"].delete_one.assert_called_once()


class TestStyleSettings:
    """Test organization style settings management."""

    def test_update_organization_style_settings(self, organization_service, mock_mongodb, sample_organization):
        """Test updating organization style settings."""
        style_settings = {
            "primary_color": "#FF0000",
            "secondary_color": "#00FF00",
            "logo_url": "https://example.com/logo.png"
        }

        mock_mongodb["organizations"].update_one.return_value = Mock(modified_count=1)
        mock_mongodb["organizations"].find_one.return_value = {
            **sample_organization.model_dump(),
            "style_settings": style_settings
        }

        result = organization_service.update_organization_style_settings("test-org-id", style_settings)

        assert result is not None
        assert result.style_settings == style_settings

        # Verify database call
        mock_mongodb["organizations"].update_one.assert_called_once()
        update_call_args = mock_mongodb["organizations"].update_one.call_args
        assert update_call_args[0][1]["$set"]["style_settings"] == style_settings


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_create_organization_duplicate_name(self, organization_service, mock_mongodb, sample_organization_data):
        """Test creating organization with duplicate name."""
        # Mock insert_one to raise duplicate key error
        from pymongo.errors import DuplicateKeyError
        mock_mongodb["organizations"].insert_one.side_effect = DuplicateKeyError("Duplicate key")

        with pytest.raises(DuplicateKeyError):
            organization_service.create_organization(
                sample_organization_data,
                "test-user-id",
                "test@example.com"
            )

    def test_update_nonexistent_organization(self, organization_service, mock_mongodb):
        """Test updating non-existent organization."""
        update_data = OrganizationUpdate(name="New Name")
        mock_mongodb["organizations"].update_one.return_value = Mock(modified_count=0)

        result = organization_service.update_organization("non-existent-id", update_data)

        assert result is None

    def test_user_without_organization_access(self, organization_service, mock_mongodb):
        """Test user permission check without organization access."""
        mock_mongodb["organization_users"].find_one.return_value = None

        result = organization_service.check_user_permission("test-org-id", "test-user-id", "view_campaigns")

        assert result is False

    def test_accept_invitation_email_mismatch(self, organization_service, mock_mongodb):
        """Test accepting invitation with mismatched email."""
        invitation_data = {
            "id": "invite-id",
            "organization_id": "test-org-id",
            "email": "user@example.com",
            "role": OrganizationRole.MEMBER,
            "invitation_token": "test-token",
            "status": InvitationStatus.PENDING,
            "invited_by_user_id": "inviter-id",
            "invited_by_email": "inviter@example.com",
            "expires_at": datetime.utcnow() + timedelta(days=7),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        mock_mongodb["organization_invitations"].find_one.return_value = invitation_data

        # Try to accept with different email
        result = organization_service.accept_invitation("test-token", "new-user-id", "different@example.com")

        assert result is None