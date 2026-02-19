"""
Pytest configuration and fixtures for docs backend tests.
"""
import os
import sys
from pathlib import Path
import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

# Load environment variables
load_dotenv("/opt/kasaai/.env")

# Add paths for imports
apps_path = str(Path(__file__).parent.parent.parent.parent)
sys.path.insert(0, apps_path)
kasaai_root = str(Path(__file__).parent.parent.parent.parent.parent)
sys.path.insert(0, kasaai_root)


@pytest.fixture(scope="module")
def test_client():
    """
    Create a test client for the FastAPI application.

    Returns:
        TestClient: FastAPI test client instance.
    """
    from main import app
    return TestClient(app)


@pytest.fixture
def test_user_data():
    """
    Provide test user data for signup tests.

    Returns:
        dict: Test user registration data.
    """
    import time
    return {
        "email": f"test-{int(time.time())}@example.com",
        "password": "TestPass123!SecurePassword",
        "full_name": "Test User"
    }


@pytest.fixture
def cleanup_test_users():
    """
    Cleanup test users after tests complete.

    Yields:
        list: List to track created user IDs for cleanup.
    """
    created_users = []
    yield created_users

    # Cleanup after tests
    if created_users:
        from docs_database import DocsDatabase
        db = DocsDatabase()
        for user_id in created_users:
            try:
                # Delete from MongoDB
                import asyncio
                asyncio.run(db.delete_user(user_id))
            except Exception as e:
                print(f"Cleanup warning: Could not delete test user {user_id}: {e}")
