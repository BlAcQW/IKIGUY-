"""Tests for MongoDB-based authentication system."""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone
import asyncio

from backend.main import app
from backend.services.auth_service import AuthService
from backend.models import SignupRequest, SigninRequest
from backend.utils.auth import hash_password, verify_password


client = TestClient(app)


class TestPasswordHashing:
    """Test password hashing utilities."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "test_password123"
        hashed = hash_password(password)

        assert hashed != password
        assert len(hashed) > 50  # bcrypt hashes are typically 60 chars
        assert hashed.startswith("$2b$")  # bcrypt identifier

    def test_verify_password(self):
        """Test password verification."""
        password = "test_password123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False

    def test_verify_password_invalid_hash(self):
        """Test password verification with invalid hash."""
        password = "test_password123"
        invalid_hash = "invalid_hash"

        assert verify_password(password, invalid_hash) is False


class TestAuthAPI:
    """Test authentication API endpoints."""

    def test_auth_health_check(self):
        """Test auth service health check."""
        response = client.get("/auth/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "mongodb_authentication"
        assert "email_password_auth" in data["features"]

    def test_signup_success(self):
        """Test successful user signup."""
        signup_data = {
            "email": f"test_{datetime.now().timestamp()}@example.com",
            "password": "test_password123",
            "first_name": "Test",
            "last_name": "User",
            "organization_name": "Test Organization"
        }

        response = client.post("/auth/signup", json=signup_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["user"] is not None
        assert data["user"]["email"] == signup_data["email"]
        assert data["access_token"] is not None
        assert data["refresh_token"] is not None
        assert data["organization"] is not None
        assert data["organization"]["display_name"] == signup_data["organization_name"]

    def test_signup_duplicate_email(self):
        """Test signup with duplicate email."""
        email = f"duplicate_{datetime.now().timestamp()}@example.com"
        signup_data = {
            "email": email,
            "password": "test_password123",
            "first_name": "Test",
            "last_name": "User"
        }

        # First signup
        response1 = client.post("/auth/signup", json=signup_data)
        assert response1.status_code == 200

        # Second signup with same email
        response2 = client.post("/auth/signup", json=signup_data)
        assert response2.status_code == 400
        assert "already registered" in response2.json()["detail"]

    def test_signup_weak_password(self):
        """Test signup with weak password."""
        signup_data = {
            "email": f"test_{datetime.now().timestamp()}@example.com",
            "password": "weak",  # Too short
            "first_name": "Test",
            "last_name": "User"
        }

        response = client.post("/auth/signup", json=signup_data)
        assert response.status_code == 422  # Pydantic validation error

    def test_signin_success(self):
        """Test successful user signin."""
        # First create a user
        email = f"signin_test_{datetime.now().timestamp()}@example.com"
        password = "test_password123"
        signup_data = {
            "email": email,
            "password": password,
            "first_name": "Test",
            "last_name": "User"
        }

        signup_response = client.post("/auth/signup", json=signup_data)
        assert signup_response.status_code == 200

        # Now sign in
        signin_data = {
            "email": email,
            "password": password,
            "remember_me": False
        }

        signin_response = client.post("/auth/signin", json=signin_data)
        assert signin_response.status_code == 200

        data = signin_response.json()
        assert data["success"] is True
        assert data["user"]["email"] == email
        assert data["access_token"] is not None
        assert data["refresh_token"] is not None

    def test_signin_invalid_credentials(self):
        """Test signin with invalid credentials."""
        signin_data = {
            "email": "nonexistent@example.com",
            "password": "wrong_password",
            "remember_me": False
        }

        response = client.post("/auth/signin", json=signin_data)
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    def test_signin_wrong_password(self):
        """Test signin with wrong password."""
        # First create a user
        email = f"wrong_pass_test_{datetime.now().timestamp()}@example.com"
        password = "test_password123"
        signup_data = {
            "email": email,
            "password": password,
            "first_name": "Test",
            "last_name": "User"
        }

        signup_response = client.post("/auth/signup", json=signup_data)
        assert signup_response.status_code == 200

        # Try to sign in with wrong password
        signin_data = {
            "email": email,
            "password": "wrong_password",
            "remember_me": False
        }

        signin_response = client.post("/auth/signin", json=signin_data)
        assert signin_response.status_code == 401
        assert "Invalid email or password" in signin_response.json()["detail"]

    def test_get_current_user(self):
        """Test getting current user with valid token."""
        # First create and sign in a user
        email = f"current_user_test_{datetime.now().timestamp()}@example.com"
        password = "test_password123"
        signup_data = {
            "email": email,
            "password": password,
            "first_name": "Test",
            "last_name": "User"
        }

        signup_response = client.post("/auth/signup", json=signup_data)
        assert signup_response.status_code == 200

        signup_data_resp = signup_response.json()
        access_token = signup_data_resp["access_token"]

        # Get current user
        headers = {"authorization": f"Bearer {access_token}"}
        me_response = client.get("/auth/me", headers=headers)
        assert me_response.status_code == 200

        data = me_response.json()
        assert data["email"] == email
        assert data["sub"] is not None

    def test_get_current_user_invalid_token(self):
        """Test getting current user with invalid token."""
        headers = {"authorization": "Bearer invalid_token"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 401

    def test_refresh_token(self):
        """Test token refresh."""
        # First create and sign in a user
        email = f"refresh_test_{datetime.now().timestamp()}@example.com"
        password = "test_password123"
        signup_data = {
            "email": email,
            "password": password,
            "first_name": "Test",
            "last_name": "User"
        }

        signup_response = client.post("/auth/signup", json=signup_data)
        assert signup_response.status_code == 200

        signup_data_resp = signup_response.json()
        refresh_token = signup_data_resp["refresh_token"]

        # Refresh token
        refresh_data = {"refresh_token": refresh_token}
        refresh_response = client.post("/auth/refresh", json=refresh_data)
        assert refresh_response.status_code == 200

        data = refresh_response.json()
        assert data["success"] is True
        assert data["access_token"] is not None
        assert data["refresh_token"] is not None
        assert data["user"]["email"] == email

    def test_signout(self):
        """Test user signout."""
        # First create and sign in a user
        email = f"signout_test_{datetime.now().timestamp()}@example.com"
        password = "test_password123"
        signup_data = {
            "email": email,
            "password": password,
            "first_name": "Test",
            "last_name": "User"
        }

        signup_response = client.post("/auth/signup", json=signup_data)
        assert signup_response.status_code == 200

        signup_data_resp = signup_response.json()
        access_token = signup_data_resp["access_token"]

        # Sign out
        headers = {"authorization": f"Bearer {access_token}"}
        signout_response = client.post("/auth/signout", headers=headers)
        assert signout_response.status_code == 200

        data = signout_response.json()
        assert data["success"] is True

    def test_password_reset_placeholder(self):
        """Test password reset placeholder endpoint."""
        reset_data = {"email": "test@example.com"}
        response = client.post("/auth/password/reset", json=reset_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "reset instructions" in data["message"]

    def test_password_confirm_placeholder(self):
        """Test password reset confirmation placeholder endpoint."""
        confirm_data = {
            "token": "dummy_token",
            "new_password": "new_password123"
        }
        response = client.post("/auth/password/confirm", json=confirm_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "reset successfully" in data["message"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])