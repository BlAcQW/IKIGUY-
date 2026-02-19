"""
Unit tests for wallet authentication and authorization.

Tests wallet endpoints with proper authentication flow.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException
from app.core.auth import get_current_user
from app.models.user import UserInDB


class TestWalletAuthentication:
    """Test wallet endpoint authentication."""

    @pytest.mark.asyncio
    async def test_get_current_user_with_valid_token(self):
        """
        Test that get_current_user returns user with valid token.

        Expected:
            - Returns UserInDB object
            - User has valid user_id and email
        """
        # Mock Supabase response
        mock_user = Mock()
        mock_user.id = "test-user-123"
        mock_user.email = "test@example.com"
        mock_user.user_metadata = {"display_name": "Test User"}

        mock_response = Mock()
        mock_response.user = mock_user

        # Mock database
        mock_db = AsyncMock()
        mock_db.users.find_one = AsyncMock(return_value={
            "_id": "mongo-id-123",
            "user_id": "test-user-123",
            "email": "test@example.com",
            "display_name": "Test User",
            "is_admin": False,
            "credits": 100
        })

        with patch("app.core.auth.supabase.auth.get_user", return_value=mock_response):
            with patch("app.core.auth.get_db", return_value=mock_db):
                user = await get_current_user(authorization="Bearer valid-token-123")

                assert isinstance(user, UserInDB)
                assert user.user_id == "test-user-123"
                assert user.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_current_user_without_auth_header(self):
        """
        Test that get_current_user raises 401 without auth header.

        Expected:
            - Raises HTTPException with status 401
            - Error message indicates authentication required
        """
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(authorization=None)

        assert exc_info.value.status_code == 401
        # Error message should indicate authentication is required
        detail = str(exc_info.value.detail).lower()
        assert "authentication" in detail or "login" in detail or "authorization" in detail

    @pytest.mark.asyncio
    async def test_get_current_user_with_invalid_scheme(self):
        """
        Test that get_current_user raises 401 with invalid auth scheme.

        Expected:
            - Raises HTTPException with status 401
            - Error message indicates invalid scheme
        """
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(authorization="Basic invalid-scheme")

        assert exc_info.value.status_code == 401
        assert "Invalid authentication scheme" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_current_user_with_invalid_token(self):
        """
        Test that get_current_user raises 401 with invalid token.

        Expected:
            - Raises HTTPException with status 401
            - Error message indicates invalid/expired token
        """
        # Mock Supabase response with no user
        mock_response = Mock()
        mock_response.user = None

        with patch("app.core.auth.supabase.auth.get_user", return_value=mock_response):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(authorization="Bearer invalid-token")

            assert exc_info.value.status_code == 401
            assert "Invalid or expired token" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_current_user_creates_new_user(self):
        """
        Test that get_current_user creates new user if not in database.

        Expected:
            - Creates new user in database
            - Returns UserInDB object with correct data
        """
        # Mock Supabase response
        mock_user = Mock()
        mock_user.id = "new-user-456"
        mock_user.email = "newuser@example.com"
        mock_user.user_metadata = {
            "display_name": "New User",
            "avatar_url": "https://example.com/avatar.jpg"
        }

        mock_response = Mock()
        mock_response.user = mock_user

        # Mock database - no existing user, then return created user
        mock_db = AsyncMock()
        mock_db.users.find_one = AsyncMock(side_effect=[
            None,  # First call - user doesn't exist
            {  # Second call - user exists after creation
                "_id": "mongo-id-456",
                "user_id": "new-user-456",
                "email": "newuser@example.com",
                "display_name": "New User",
                "avatar_url": "https://example.com/avatar.jpg",
                "is_admin": False,
                "credits": 0
            }
        ])
        mock_db.users.insert_one = AsyncMock()

        with patch("app.core.auth.supabase.auth.get_user", return_value=mock_response):
            with patch("app.core.auth.get_db", return_value=mock_db):
                user = await get_current_user(authorization="Bearer new-user-token")

                assert isinstance(user, UserInDB)
                assert user.user_id == "new-user-456"
                assert user.email == "newuser@example.com"
                # Verify insert_one was called
                mock_db.users.insert_one.assert_called_once()


class TestWalletEndpointProtection:
    """Test that wallet endpoints are properly protected."""

    @pytest.mark.asyncio
    async def test_wallet_balance_requires_auth(self):
        """
        Test that wallet balance endpoint requires authentication.

        Edge case:
            - Request without authentication should be rejected
        """
        # This test validates the endpoint dependency
        from app.api.routes.wallet import get_balance
        import inspect

        # Check that get_balance has get_current_user as dependency
        sig = inspect.signature(get_balance)
        params = sig.parameters

        assert "current_user" in params
        assert params["current_user"].default is not None

    @pytest.mark.asyncio
    async def test_wallet_topup_requires_auth(self):
        """
        Test that wallet top-up endpoints require authentication.

        Edge case:
            - Request without authentication should be rejected
        """
        from app.api.routes.wallet import initiate_paystack_topup, initiate_stripe_topup
        import inspect

        # Check Paystack endpoint
        sig = inspect.signature(initiate_paystack_topup)
        params = sig.parameters
        assert "current_user" in params

        # Check Stripe endpoint
        sig = inspect.signature(initiate_stripe_topup)
        params = sig.parameters
        assert "current_user" in params
