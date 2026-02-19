"""
Unit tests for authentication routes.

Tests user registration, profile management, and student linking.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId

from app.models.user import UserRole, User


class TestAuthRoutes:
    """Test authentication API endpoints."""

    @pytest.mark.asyncio
    async def test_register_user_success(self, client, mock_supabase_auth, mock_mongodb):
        """
        Test successful user registration.

        Expected: 201 status, user data returned
        """
        # Mock MongoDB insert
        mock_result = MagicMock()
        mock_result.inserted_id = ObjectId()
        mock_mongodb.insert_one = AsyncMock(return_value=mock_result)

        # Mock user doesn't exist
        mock_mongodb.find_one = AsyncMock(return_value=None)

        request_data = {
            "role": "student",
            "full_name": "John Doe",
            "grade": 10
        }

        response = client.post(
            "/api/v1/auth/register",
            json=request_data,
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["full_name"] == "John Doe"
        assert data["role"] == "student"

    @pytest.mark.asyncio
    async def test_register_user_already_exists(self, client, mock_supabase_auth, mock_mongodb):
        """
        Test registration with existing user.

        Expected: 400 status, error message
        """
        # Mock user already exists
        existing_user = {
            "_id": ObjectId(),
            "supabase_id": "test-user-id-123",
            "role": UserRole.STUDENT.value,
            "full_name": "Existing User"
        }
        mock_mongodb.find_one = AsyncMock(return_value=existing_user)

        request_data = {
            "role": "student",
            "full_name": "John Doe"
        }

        response = client.post(
            "/api/v1/auth/register",
            json=request_data,
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_student_without_grade(self, client, mock_supabase_auth, mock_mongodb):
        """
        Test student registration without grade.

        Expected: 422 validation error
        """
        request_data = {
            "role": "student",
            "full_name": "John Doe"
            # Missing grade for student
        }

        response = client.post(
            "/api/v1/auth/register",
            json=request_data,
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_current_user_profile_success(self, client, mock_supabase_auth, mock_mongodb):
        """
        Test getting current user profile.

        Expected: 200 status, user profile returned
        """
        user_data = {
            "_id": ObjectId(),
            "supabase_id": "test-user-id-123",
            "role": UserRole.STUDENT.value,
            "full_name": "John Doe",
            "grade": 10,
            "email": "test@example.com"
        }
        mock_mongodb.find_one = AsyncMock(return_value=user_data)

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "John Doe"
        assert data["role"] == "student"

    @pytest.mark.asyncio
    async def test_get_current_user_profile_not_found(self, client, mock_supabase_auth, mock_mongodb):
        """
        Test getting profile for non-existent user.

        Expected: 404 status
        """
        mock_mongodb.find_one = AsyncMock(return_value=None)

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_user_profile_success(self, client, mock_supabase_auth, mock_mongodb):
        """
        Test updating user profile.

        Expected: 200 status, updated user returned
        """
        user_data = {
            "_id": ObjectId(),
            "supabase_id": "test-user-id-123",
            "role": UserRole.STUDENT.value,
            "full_name": "John Doe",
            "grade": 10
        }
        mock_mongodb.find_one = AsyncMock(return_value=user_data)
        mock_mongodb.update_one = AsyncMock()

        update_data = {
            "full_name": "Jane Doe",
            "grade": 11
        }

        response = client.put(
            "/api/v1/auth/me",
            json=update_data,
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_link_student_to_parent_success(self, client, mock_supabase_auth, mock_mongodb):
        """
        Test linking student to parent account.

        Expected: 200 status, success message
        """
        # Mock parent user
        parent_data = {
            "_id": ObjectId(),
            "supabase_id": "parent-id-123",
            "role": UserRole.PARENT.value,
            "student_ids": []
        }

        # Mock student user
        student_data = {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "supabase_id": "student-id-456",
            "role": UserRole.STUDENT.value,
            "email": "student@example.com"
        }

        # Setup mock responses
        def find_one_side_effect(*args, **kwargs):
            query = args[0] if args else kwargs.get("filter")
            if "supabase_id" in query and query["supabase_id"] == "parent-id-123":
                return parent_data
            elif "email" in query:
                return student_data
            return None

        mock_mongodb.find_one = AsyncMock(side_effect=find_one_side_effect)
        mock_mongodb.update_one = AsyncMock()

        # Mock Supabase user with parent role
        with patch("app.core.auth.supabase_auth.verify_token") as mock_verify:
            mock_verify.return_value = {
                "sub": "parent-id-123",
                "user_metadata": {"role": UserRole.PARENT.value}
            }

            response = client.post(
                "/api/v1/auth/link-student",
                json={"student_email": "student@example.com"},
                headers={"Authorization": "Bearer parent-token"}
            )

        assert response.status_code == 200
        assert "linked successfully" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_link_student_wrong_role(self, client, mock_supabase_auth, mock_mongodb):
        """
        Test linking student when user is not parent.

        Expected: 403 status, access denied
        """
        # Mock user with student role (not parent)
        with patch("app.core.auth.supabase_auth.verify_token") as mock_verify:
            mock_verify.return_value = {
                "sub": "student-id-123",
                "user_metadata": {"role": UserRole.STUDENT.value}
            }

            response = client.post(
                "/api/v1/auth/link-student",
                json={"student_email": "student@example.com"},
                headers={"Authorization": "Bearer student-token"}
            )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_link_student_not_found(self, client, mock_supabase_auth, mock_mongodb):
        """
        Test linking non-existent student.

        Expected: 404 status
        """
        # Mock parent exists
        parent_data = {
            "_id": ObjectId(),
            "supabase_id": "parent-id-123",
            "role": UserRole.PARENT.value
        }

        def find_one_side_effect(*args, **kwargs):
            query = args[0] if args else kwargs.get("filter")
            if "supabase_id" in query:
                return parent_data
            return None  # Student not found

        mock_mongodb.find_one = AsyncMock(side_effect=find_one_side_effect)

        with patch("app.core.auth.supabase_auth.verify_token") as mock_verify:
            mock_verify.return_value = {
                "sub": "parent-id-123",
                "user_metadata": {"role": UserRole.PARENT.value}
            }

            response = client.post(
                "/api/v1/auth/link-student",
                json={"student_email": "nonexistent@example.com"},
                headers={"Authorization": "Bearer parent-token"}
            )

        assert response.status_code == 404
