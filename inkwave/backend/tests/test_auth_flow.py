"""
Unit tests for authentication flow.

Tests sign-in, sign-up, token validation, and session management.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from app.main import app
from app.core.auth import get_current_user

# Test client
client = TestClient(app)


class TestAuthEndpoints:
    """Test authentication endpoints"""

    @pytest.mark.skip(reason="Requires database connection - run as integration test")
    @patch("app.api.routes.auth.supabase_admin")
    @patch("app.api.routes.auth.supabase")
    @pytest.mark.asyncio
    async def test_signup_success(self, mock_supabase, mock_supabase_admin):
        """Test successful user signup"""
        # Mock admin user creation
        mock_user = Mock()
        mock_user.id = "test-user-id"
        mock_user.email = "test@example.com"
        mock_user.created_at = "2025-01-01T00:00:00Z"

        mock_admin_response = Mock()
        mock_admin_response.user = mock_user
        mock_supabase_admin.auth.admin.create_user.return_value = mock_admin_response

        # Mock sign-in response
        mock_session = Mock()
        mock_session.access_token = "test-access-token"
        mock_session.refresh_token = "test-refresh-token"

        mock_signin_response = Mock()
        mock_signin_response.session = mock_session
        mock_supabase.auth.sign_in_with_password.return_value = mock_signin_response

        # Make request
        response = client.post(
            "/api/v1/auth/signup",
            json={"email": "test@example.com", "password": "password123"}
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["user"]["email"] == "test@example.com"
        assert data["session"]["access_token"] == "test-access-token"

    @patch("app.api.routes.auth.supabase_admin")
    @pytest.mark.asyncio
    async def test_signup_duplicate_email(self, mock_supabase_admin):
        """Test signup with duplicate email"""
        # Mock admin user creation failure
        mock_admin_response = Mock()
        mock_admin_response.user = None
        mock_supabase_admin.auth.admin.create_user.return_value = mock_admin_response

        # Make request
        response = client.post(
            "/api/v1/auth/signup",
            json={"email": "existing@example.com", "password": "password123"}
        )

        # Assertions
        assert response.status_code == 400
        assert "already be in use" in response.json()["detail"]

    @patch("app.api.routes.auth.supabase")
    @pytest.mark.asyncio
    async def test_login_success(self, mock_supabase):
        """Test successful login"""
        # Mock user and session
        mock_user = Mock()
        mock_user.id = "test-user-id"
        mock_user.email = "test@example.com"

        mock_session = Mock()
        mock_session.access_token = "test-access-token"
        mock_session.refresh_token = "test-refresh-token"

        mock_response = Mock()
        mock_response.user = mock_user
        mock_response.session = mock_session
        mock_supabase.auth.sign_in_with_password.return_value = mock_response

        # Make request
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123"}
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["user"]["email"] == "test@example.com"
        assert data["session"]["access_token"] == "test-access-token"

    @patch("app.api.routes.auth.supabase")
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, mock_supabase):
        """Test login with invalid credentials"""
        # Mock failed login
        mock_response = Mock()
        mock_response.user = None
        mock_response.session = None
        mock_supabase.auth.sign_in_with_password.return_value = mock_response

        # Make request
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "wrongpassword"}
        )

        # Assertions
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]


class TestTokenValidation:
    """Test token validation and authentication"""

    @pytest.mark.skip(reason="Requires database connection - run as integration test")
    @patch("app.core.auth.supabase")
    @pytest.mark.asyncio
    async def test_valid_token(self, mock_supabase):
        """Test authentication with valid token"""
        # Mock Supabase response
        mock_user = Mock()
        mock_user.id = "test-user-id"
        mock_user.email = "test@example.com"
        mock_user.user_metadata = {"display_name": "Test User"}

        mock_response = Mock()
        mock_response.user = mock_user
        mock_supabase.auth.get_user.return_value = mock_response

        # Test token validation
        authorization = "Bearer valid-test-token"
        with patch("app.core.auth.get_db") as mock_get_db:
            # Mock database user
            mock_db = MagicMock()
            mock_db.users.find_one.return_value = {
                "_id": "mongo-id",
                "user_id": "test-user-id",
                "email": "test@example.com",
                "display_name": "Test User",
            }
            mock_get_db.return_value = mock_db

            # Call get_current_user
            user = await get_current_user(authorization=authorization)

            assert user.user_id == "test-user-id"
            assert user.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_missing_token(self):
        """Test authentication with missing token"""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(authorization=None)

        assert exc_info.value.status_code == 401
        assert "Authorization header missing" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_invalid_token_format(self):
        """Test authentication with invalid token format"""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(authorization="InvalidFormat")

        assert exc_info.value.status_code == 401
        assert "Invalid authorization header format" in exc_info.value.detail

    @patch("app.core.auth.supabase")
    @pytest.mark.asyncio
    async def test_expired_token(self, mock_supabase):
        """Test authentication with expired token"""
        from fastapi import HTTPException

        # Mock expired token response
        mock_response = Mock()
        mock_response.user = None
        mock_supabase.auth.get_user.return_value = mock_response

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(authorization="Bearer expired-token")

        assert exc_info.value.status_code == 401
        assert "Invalid or expired token" in exc_info.value.detail


class TestSessionManagement:
    """Test session creation and management"""

    @patch("app.api.routes.auth.supabase")
    @pytest.mark.asyncio
    async def test_session_structure(self, mock_supabase):
        """Test that login returns properly structured session"""
        # Mock user and session
        mock_user = Mock()
        mock_user.id = "test-user-id"
        mock_user.email = "test@example.com"

        mock_session = Mock()
        mock_session.access_token = "test-access-token-12345"
        mock_session.refresh_token = "test-refresh-token-67890"

        mock_response = Mock()
        mock_response.user = mock_user
        mock_response.session = mock_session
        mock_supabase.auth.sign_in_with_password.return_value = mock_response

        # Make request
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123"}
        )

        # Verify session structure
        data = response.json()
        assert "session" in data
        assert "access_token" in data["session"]
        assert "refresh_token" in data["session"]
        assert len(data["session"]["access_token"]) > 0
        assert len(data["session"]["refresh_token"]) > 0

    @pytest.mark.asyncio
    async def test_protected_route_without_auth(self):
        """Test accessing protected route without authentication"""
        # Attempt to access profile without token
        response = client.get("/api/v1/profile")

        # Should return 401
        assert response.status_code == 401


class TestUserCreation:
    """Test user creation in MongoDB after auth"""

    @pytest.mark.skip(reason="Requires database connection - run as integration test")
    @patch("app.core.auth.supabase")
    @pytest.mark.asyncio
    async def test_user_created_on_first_auth(self, mock_supabase):
        """Test that user is created in MongoDB on first authentication"""
        # Mock Supabase response
        mock_user = Mock()
        mock_user.id = "new-user-id"
        mock_user.email = "newuser@example.com"
        mock_user.user_metadata = {}

        mock_response = Mock()
        mock_response.user = mock_user
        mock_supabase.auth.get_user.return_value = mock_response

        with patch("app.core.auth.get_db") as mock_get_db:
            # Mock database - no existing user
            mock_db = MagicMock()
            mock_db.users.find_one.side_effect = [
                None,  # First call returns None (no user)
                {      # Second call returns created user
                    "_id": "mongo-id",
                    "user_id": "new-user-id",
                    "email": "newuser@example.com",
                    "display_name": None,
                }
            ]
            mock_get_db.return_value = mock_db

            # Call get_current_user
            user = await get_current_user(authorization="Bearer new-user-token")

            # Verify user was created
            assert mock_db.users.insert_one.called
            assert user.user_id == "new-user-id"
            assert user.email == "newuser@example.com"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
