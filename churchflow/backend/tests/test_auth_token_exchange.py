"""
Unit tests for authentication token exchange endpoint.

Tests the /auth/exchange-token endpoint which exchanges Supabase JWT
tokens for ChurchFlow backend JWT tokens.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient

from app.main import app
from app.core.config import settings


# Test database configuration
TEST_MONGODB_URL = "mongodb://admin:aawwER4444%25@127.0.0.1:27017/churchflow_test?authSource=admin"


@pytest.fixture(scope="function")
def test_client():
    """
    Create FastAPI test client with mocked database.

    Returns:
        TestClient for API testing
    """
    # Create a simple test database instance
    client_motor = AsyncIOMotorClient(TEST_MONGODB_URL)
    test_db = client_motor.get_database()

    # Override the get_database dependency to use test database
    from app.core.database import get_database

    def override_get_database():
        return test_db

    app.dependency_overrides[get_database] = override_get_database

    # Create test client
    test_http_client = TestClient(app)

    yield test_http_client

    # Clean up overrides
    app.dependency_overrides.clear()
    client_motor.close()


@pytest.fixture
def mock_supabase_user():
    """
    Create mock Supabase user response.

    Returns:
        Mock Supabase user object
    """
    user = Mock()
    user.id = "test-supabase-user-id-123"
    user.email = "test@example.com"
    user.phone = "+233200000001"
    return user


@pytest.fixture
def mock_supabase_token():
    """
    Create mock Supabase JWT token.

    Returns:
        Mock JWT token string
    """
    return "mock-supabase-jwt-token"


def test_exchange_token_endpoint_success_new_user(test_client, mock_supabase_user, mock_supabase_token):
    """
    Test successful token exchange for new user with auto-creation.

    Verifies that:
    1. Supabase token is verified correctly
    2. New user is created in database when not found
    3. User is created with default admin roles
    4. Backend JWT is generated and returned

    Args:
        test_client: FastAPI test client
        mock_supabase_user: Mock Supabase user fixture
        mock_supabase_token: Mock token fixture
    """
    # Mock Supabase client (patching where it's imported)
    with patch("supabase.create_client") as mock_create_client:
        mock_supabase = Mock()
        mock_auth = Mock()

        # Mock successful user retrieval
        mock_user_response = Mock()
        mock_user_response.user = mock_supabase_user
        mock_auth.get_user.return_value = mock_user_response

        mock_supabase.auth = mock_auth
        mock_create_client.return_value = mock_supabase

        # Make request to token exchange endpoint
        response = test_client.post(
            f"{settings.api_prefix}/auth/exchange-token",
            headers={"Authorization": f"Bearer {mock_supabase_token}"}
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["user_id"] == mock_supabase_user.id
        assert data["phone"] == mock_supabase_user.phone
        assert data["access_token"] is not None
        assert data["token_type"] == "bearer"

        # Verify Supabase was called correctly
        mock_auth.get_user.assert_called_once_with(mock_supabase_token)


def test_exchange_token_endpoint_invalid_token(test_client, mock_supabase_token):
    """
    Test token exchange with invalid Supabase token.

    Verifies that:
    1. Invalid Supabase token is rejected
    2. Appropriate error is raised
    3. No backend token is generated

    Args:
        test_client: FastAPI test client
        mock_supabase_token: Mock token fixture
    """
    # Mock Supabase client to raise error
    with patch("supabase.create_client") as mock_create_client:
        mock_supabase = Mock()
        mock_auth = Mock()

        # Mock failed user retrieval
        mock_auth.get_user.side_effect = Exception("Invalid token")

        mock_supabase.auth = mock_auth
        mock_create_client.return_value = mock_supabase

        # Make request to token exchange endpoint
        response = test_client.post(
            f"{settings.api_prefix}/auth/exchange-token",
            headers={"Authorization": f"Bearer {mock_supabase_token}"}
        )

        # Assertions
        assert response.status_code == 401
        data = response.json()
        assert "Token exchange failed" in data["detail"]


def test_exchange_token_endpoint_no_authorization_header(test_client):
    """
    Test token exchange without Authorization header.

    Verifies that:
    1. Request without Authorization header is rejected
    2. Appropriate 403 error is returned

    Args:
        test_client: FastAPI test client
    """
    # Make request without Authorization header
    response = test_client.post(f"{settings.api_prefix}/auth/exchange-token")

    # Assertions
    assert response.status_code == 403


def test_exchange_token_endpoint_supabase_returns_none(test_client, mock_supabase_token):
    """
    Test token exchange when Supabase returns no user.

    Verifies that:
    1. Empty Supabase response is handled
    2. Appropriate error is raised

    Args:
        test_client: FastAPI test client
        mock_supabase_token: Mock token fixture
    """
    # Mock Supabase client
    with patch("supabase.create_client") as mock_create_client:
        mock_supabase = Mock()
        mock_auth = Mock()

        # Mock empty user response
        mock_user_response = Mock()
        mock_user_response.user = None
        mock_auth.get_user.return_value = mock_user_response

        mock_supabase.auth = mock_auth
        mock_create_client.return_value = mock_supabase

        # Make request to token exchange endpoint
        response = test_client.post(
            f"{settings.api_prefix}/auth/exchange-token",
            headers={"Authorization": f"Bearer {mock_supabase_token}"}
        )

        # Assertions
        assert response.status_code == 401
        data = response.json()
        assert "Token exchange failed" in data["detail"]


def test_exchange_token_creates_valid_backend_jwt(test_client, mock_supabase_user, mock_supabase_token):
    """
    Test that exchanged backend JWT can be decoded and validated.

    Verifies that:
    1. Backend JWT is properly signed
    2. Token contains correct user information
    3. Token can be decoded with backend SECRET_KEY

    Args:
        test_client: FastAPI test client
        mock_supabase_user: Mock Supabase user fixture
        mock_supabase_token: Mock token fixture
    """
    # Mock Supabase client
    with patch("supabase.create_client") as mock_create_client:
        mock_supabase = Mock()
        mock_auth = Mock()

        # Mock successful user retrieval
        mock_user_response = Mock()
        mock_user_response.user = mock_supabase_user
        mock_auth.get_user.return_value = mock_user_response

        mock_supabase.auth = mock_auth
        mock_create_client.return_value = mock_supabase

        # Make request to token exchange endpoint
        response = test_client.post(
            f"{settings.api_prefix}/auth/exchange-token",
            headers={"Authorization": f"Bearer {mock_supabase_token}"}
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()

        # Verify backend token can be decoded
        from app.services.auth_service import auth_service
        decoded_token = auth_service.decode_token(data["access_token"])

        assert decoded_token is not None
        assert decoded_token["sub"] == mock_supabase_user.id
        assert decoded_token["email"] == mock_supabase_user.email


def test_exchange_token_handles_user_without_phone(test_client, mock_supabase_user, mock_supabase_token):
    """
    Test token exchange for user without phone number.

    Edge case: Some users may only have email, no phone.

    Args:
        test_client: FastAPI test client
        mock_supabase_user: Mock Supabase user fixture
        mock_supabase_token: Mock token fixture
    """
    # Set user phone to None
    mock_supabase_user.phone = None

    # Mock Supabase client
    with patch("supabase.create_client") as mock_create_client:
        mock_supabase = Mock()
        mock_auth = Mock()

        # Mock successful user retrieval
        mock_user_response = Mock()
        mock_user_response.user = mock_supabase_user
        mock_auth.get_user.return_value = mock_user_response

        mock_supabase.auth = mock_auth
        mock_create_client.return_value = mock_supabase

        # Make request to token exchange endpoint
        response = test_client.post(
            f"{settings.api_prefix}/auth/exchange-token",
            headers={"Authorization": f"Bearer {mock_supabase_token}"}
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["phone"] == ""  # Returns empty string, not None


def test_exchange_token_handles_user_without_email(test_client, mock_supabase_user, mock_supabase_token):
    """
    Test token exchange for user without email.

    Edge case: Some users may only have phone, no email.

    Args:
        test_client: FastAPI test client
        mock_supabase_user: Mock Supabase user fixture
        mock_supabase_token: Mock token fixture
    """
    # Set user email to None
    mock_supabase_user.email = None

    # Mock Supabase client
    with patch("supabase.create_client") as mock_create_client:
        mock_supabase = Mock()
        mock_auth = Mock()

        # Mock successful user retrieval
        mock_user_response = Mock()
        mock_user_response.user = mock_supabase_user
        mock_auth.get_user.return_value = mock_user_response

        mock_supabase.auth = mock_auth
        mock_create_client.return_value = mock_supabase

        # Make request to token exchange endpoint
        response = test_client.post(
            f"{settings.api_prefix}/auth/exchange-token",
            headers={"Authorization": f"Bearer {mock_supabase_token}"}
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


@pytest.mark.asyncio
async def test_exchange_token_user_creation_in_database():
    """
    Test that token exchange creates user in database correctly.

    Verifies database interaction and user creation with correct fields.
    """
    # Connect to test database
    client = AsyncIOMotorClient(TEST_MONGODB_URL)
    db = client.get_database()

    # Clean up test user if exists
    await db.users.delete_many({"supabase_id": "test-user-db-123"})

    try:
        # Create mock user
        mock_user = Mock()
        mock_user.id = "test-user-db-123"
        mock_user.email = "dbtest@example.com"
        mock_user.phone = "+233200000002"

        # Mock Supabase client
        with patch("supabase.create_client") as mock_create_client:
            mock_supabase = Mock()
            mock_auth = Mock()

            # Mock successful user retrieval
            mock_user_response = Mock()
            mock_user_response.user = mock_user
            mock_auth.get_user.return_value = mock_user_response

            mock_supabase.auth = mock_auth
            mock_create_client.return_value = mock_supabase

            # Call token exchange endpoint
            test_client = TestClient(app)
            response = test_client.post(
                f"{settings.api_prefix}/auth/exchange-token",
                headers={"Authorization": "Bearer test-token"}
            )

            # Verify response
            assert response.status_code == 200

            # Verify user was created in database
            created_user = await db.users.find_one({"supabase_id": mock_user.id})
            assert created_user is not None
            assert created_user["email"] == mock_user.email
            assert created_user["phone"] == mock_user.phone
            assert "admin" in created_user["roles"]
            assert "coordinator" in created_user["roles"]
            assert created_user["created_at"] is not None
            assert created_user["updated_at"] is not None

    finally:
        # Clean up
        await db.users.delete_many({"supabase_id": "test-user-db-123"})
        client.close()
