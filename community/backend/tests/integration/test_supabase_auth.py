"""
Integration tests for Supabase authentication in African Language Community Platform.

Tests both dev-token bypass and real Supabase JWT validation.
"""

import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from core.auth import get_current_user, validate_supabase_token


class TestDevTokenAuth:
    """Test dev-token authentication bypass."""

    @pytest.mark.asyncio
    async def test_dev_token_returns_dev_user(self):
        """Test that dev-token returns the development user."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="dev-token"
        )

        user = await get_current_user(credentials)

        assert user["id"] == "000000000000000000000001"
        assert user["email"] == "dev@example.com"
        assert user["name"] == "Development User"
        assert user["role"] == "user"  # Regular user role

    @pytest.mark.asyncio
    async def test_dev_moderator_token_returns_moderator_user(self):
        """Test that dev-moderator-token returns the moderator user."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="dev-moderator-token"
        )

        user = await get_current_user(credentials)

        assert user["id"] == "000000000000000000000002"
        assert user["email"] == "moderator@example.com"
        assert user["name"] == "Development Moderator"
        assert user["role"] == "moderator"

    @pytest.mark.asyncio
    async def test_dev_admin_token_returns_admin_user(self):
        """Test that dev-admin-token returns the admin user."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="dev-admin-token"
        )

        user = await get_current_user(credentials)

        assert user["id"] == "000000000000000000000003"
        assert user["email"] == "admin@example.com"
        assert user["name"] == "Development Admin"
        assert user["role"] == "admin"

    @pytest.mark.asyncio
    async def test_dev_token_includes_user_id_for_compatibility(self):
        """Test that dev-token response includes user_id for backwards compatibility."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="dev-token"
        )

        user = await get_current_user(credentials)

        assert user["user_id"] == user["id"]
        assert user["user_id"] == "000000000000000000000001"


class TestSupabaseTokenValidation:
    """Test real Supabase token validation."""

    @pytest.mark.asyncio
    async def test_validate_supabase_token_success(self):
        """Test successful Supabase token validation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "supabase-user-uuid-123",
            "email": "user@example.com",
            "role": "authenticated",
            "user_metadata": {"name": "Test User"},
            "app_metadata": {"provider": "email"},
        }

        with patch("core.auth.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await validate_supabase_token("valid-supabase-token")

            assert result is not None
            assert result["id"] == "supabase-user-uuid-123"
            assert result["email"] == "user@example.com"
            assert result["name"] == "Test User"
            assert result["role"] == "authenticated"

    @pytest.mark.asyncio
    async def test_validate_supabase_token_unauthorized(self):
        """Test Supabase token validation with invalid token."""
        mock_response = MagicMock()
        mock_response.status_code = 401

        with patch("core.auth.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            with pytest.raises(HTTPException) as exc_info:
                await validate_supabase_token("invalid-token")

            assert exc_info.value.status_code == 401
            assert "Invalid or expired token" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_validate_supabase_token_timeout(self):
        """Test Supabase token validation with timeout."""
        with patch("core.auth.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.TimeoutException("Connection timed out")
            )

            with pytest.raises(HTTPException) as exc_info:
                await validate_supabase_token("some-token")

            assert exc_info.value.status_code == 503
            assert "temporarily unavailable" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_validate_supabase_token_connection_error(self):
        """Test Supabase token validation with connection error."""
        with patch("core.auth.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.RequestError("Connection failed")
            )

            with pytest.raises(HTTPException) as exc_info:
                await validate_supabase_token("some-token")

            assert exc_info.value.status_code == 503
            assert "unavailable" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_validate_supabase_token_not_configured(self):
        """Test Supabase token validation when Supabase is not configured."""
        with patch("core.auth.settings") as mock_settings:
            mock_settings.SUPABASE_URL = ""
            mock_settings.SUPABASE_ANON_KEY = ""

            result = await validate_supabase_token("any-token")

            assert result is None

    @pytest.mark.asyncio
    async def test_validate_supabase_token_extracts_name_from_metadata(self):
        """Test that name is extracted from user_metadata."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "user-123",
            "email": "john.doe@example.com",
            "user_metadata": {"name": "John Doe"},
            "app_metadata": {},
        }

        with patch("core.auth.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await validate_supabase_token("valid-token")

            assert result["name"] == "John Doe"

    @pytest.mark.asyncio
    async def test_validate_supabase_token_fallback_name_from_email(self):
        """Test that name falls back to email prefix if not in metadata."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "user-456",
            "email": "jane.smith@example.com",
            "user_metadata": {},
            "app_metadata": {},
        }

        with patch("core.auth.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await validate_supabase_token("valid-token")

            assert result["name"] == "jane.smith"


class TestGetCurrentUser:
    """Test get_current_user function with various token types."""

    @pytest.mark.asyncio
    async def test_get_current_user_with_valid_supabase_token(self):
        """Test get_current_user with a valid Supabase token."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="valid-supabase-token"
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "supabase-user-id",
            "email": "authenticated@example.com",
            "user_metadata": {"name": "Authenticated User"},
            "app_metadata": {},
        }

        with patch("core.auth.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            user = await get_current_user(credentials)

            assert user["id"] == "supabase-user-id"
            assert user["email"] == "authenticated@example.com"
            assert user["name"] == "Authenticated User"

    @pytest.mark.asyncio
    async def test_get_current_user_falls_back_to_jwt_decode(self):
        """Test that get_current_user falls back to JWT decode when Supabase returns None."""
        import jwt as pyjwt
        from datetime import datetime, timedelta

        # Create a valid JWT token (unsigned for testing)
        payload = {
            "sub": "jwt-user-id",
            "email": "jwt@example.com",
            "name": "JWT User",
            "exp": datetime.utcnow() + timedelta(hours=1),
        }
        token = pyjwt.encode(payload, "secret", algorithm="HS256")

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        # Mock Supabase returning None (not configured)
        with patch("core.auth.validate_supabase_token", return_value=None):
            user = await get_current_user(credentials)

            assert user["id"] == "jwt-user-id"
            assert user["email"] == "jwt@example.com"
            assert user["name"] == "JWT User"

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token_format(self):
        """Test get_current_user with invalid token format."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="not-a-valid-token"
        )

        # Mock Supabase returning None (not configured)
        with patch("core.auth.validate_supabase_token", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials)

            assert exc_info.value.status_code == 401
            assert "Invalid token" in str(exc_info.value.detail)


class TestRealSupabaseIntegration:
    """
    Integration tests that connect to real Supabase.

    These tests require:
    - SUPABASE_URL configured in .env
    - SUPABASE_ANON_KEY configured in .env
    - Network connectivity to Supabase

    Tests are skipped if Supabase is not configured or unreachable.
    """

    @pytest.fixture
    def supabase_configured(self):
        """Check if Supabase is configured."""
        from core.config import get_settings

        settings = get_settings()
        return bool(settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY)

    @pytest.mark.asyncio
    async def test_real_supabase_connection(self, supabase_configured):
        """Test that we can connect to real Supabase (health check)."""
        if not supabase_configured:
            pytest.skip("Supabase not configured")

        from core.config import get_settings

        settings = get_settings()

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.SUPABASE_URL}/rest/v1/",
                    headers={"apikey": settings.SUPABASE_ANON_KEY},
                    timeout=10.0,
                )
                # 200 or 400 both indicate Supabase is reachable
                assert response.status_code in [200, 400, 404]
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            pytest.skip(f"Supabase not reachable: {e}")

    @pytest.mark.asyncio
    async def test_real_invalid_token_rejected(self, supabase_configured):
        """Test that an invalid token is rejected by real Supabase."""
        if not supabase_configured:
            pytest.skip("Supabase not configured")

        try:
            with pytest.raises(HTTPException) as exc_info:
                await validate_supabase_token("definitely-not-a-valid-token")

            # 401 = invalid token, 503 = service unavailable (network issue)
            assert exc_info.value.status_code in [401, 503]
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            pytest.skip(f"Supabase not reachable: {e}")


class TestAuthEdgeCases:
    """Test edge cases in authentication."""

    @pytest.mark.asyncio
    async def test_empty_token_raises_error(self):
        """Test that empty token raises appropriate error."""
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="")

        # Mock Supabase returning None
        with patch("core.auth.validate_supabase_token", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials)

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_whitespace_token_raises_error(self):
        """Test that whitespace-only token raises appropriate error."""
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="   ")

        # Mock Supabase returning None
        with patch("core.auth.validate_supabase_token", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials)

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_supabase_returns_user_without_name(self):
        """Test handling when Supabase user has no name in metadata."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "user-no-name",
            "email": "noname@example.com",
            # No user_metadata.name
        }

        with patch("core.auth.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await validate_supabase_token("valid-token")

            # Should fall back to email prefix
            assert result["name"] == "noname"
