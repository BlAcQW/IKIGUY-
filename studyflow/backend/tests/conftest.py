"""
Pytest configuration and fixtures for StudyFlow tests.
"""

import pytest
import os
import sys
from typing import Generator
from unittest.mock import MagicMock, patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app
from app.models.user import UserRole


@pytest.fixture
def client() -> Generator:
    """
    Create FastAPI test client.

    Yields:
        TestClient: FastAPI test client instance
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_supabase_auth():
    """
    Mock Supabase authentication.

    Returns:
        MagicMock: Mocked Supabase user data
    """
    with patch("app.core.auth.supabase_auth.verify_token") as mock_verify:
        mock_user = {
            "sub": "test-user-id-123",
            "email": "test@example.com",
            "user_metadata": {
                "role": UserRole.STUDENT.value
            }
        }
        mock_verify.return_value = mock_user
        yield mock_verify


@pytest.fixture
def auth_headers_student() -> dict:
    """
    Get authorization headers for student user.

    Returns:
        dict: Headers with Bearer token
    """
    return {
        "Authorization": "Bearer test-student-token"
    }


@pytest.fixture
def auth_headers_teacher() -> dict:
    """
    Get authorization headers for teacher user.

    Returns:
        dict: Headers with Bearer token
    """
    return {
        "Authorization": "Bearer test-teacher-token"
    }


@pytest.fixture
def auth_headers_admin() -> dict:
    """
    Get authorization headers for admin user.

    Returns:
        dict: Headers with Bearer token
    """
    return {
        "Authorization": "Bearer test-admin-token"
    }


@pytest.fixture
def mock_mongodb():
    """
    Mock MongoDB operations.

    Returns:
        MagicMock: Mocked MongoDB collection
    """
    with patch("app.core.database.mongodb") as mock_mongo:
        mock_collection = MagicMock()
        mock_mongo.get_collection.return_value = mock_collection
        yield mock_collection


@pytest.fixture
def sample_material_data() -> dict:
    """
    Get sample material data for testing.

    Returns:
        dict: Sample material metadata
    """
    return {
        "title": "Introduction to Python",
        "subject": "Computer Science",
        "description": "Basic Python programming concepts",
        "topics": "variables,functions,loops",
        "grade": 10,
        "school_id": "school-123"
    }


@pytest.fixture
def sample_session_data() -> dict:
    """
    Get sample session data for testing.

    Returns:
        dict: Sample session metadata
    """
    return {
        "student_id": "student-123",
        "subject": "Mathematics",
        "topics": ["algebra", "equations"],
        "metadata": {}
    }


@pytest.fixture
def sample_question_data() -> dict:
    """
    Get sample question data for testing.

    Returns:
        dict: Sample question metadata
    """
    return {
        "session_id": "session-123",
        "subject": "Mathematics",
        "topic": "algebra",
        "question_text": "What is the quadratic formula?",
        "question_type": "text"
    }
