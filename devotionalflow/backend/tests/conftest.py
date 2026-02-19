"""
Pytest configuration and shared fixtures for DevotionalFlow tests.
"""

import pytest
import asyncio
from typing import Generator, Dict, Any
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.db.mongodb import get_database
from app.config import settings


@pytest.fixture(scope="session")
def event_loop():
    """
    Create an event loop for the test session.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings():
    """
    Get test settings.
    """
    return settings


@pytest.fixture(scope="session")
async def test_db(test_settings):
    """
    Create a test database connection.
    Uses the real database specified in .env for integration testing.
    """
    client = AsyncIOMotorClient(test_settings.MONGODB_URI)
    db = client[test_settings.DATABASE_NAME]
    yield db
    # Note: We don't close the client here as it's used across the session


@pytest.fixture
def client() -> Generator:
    """
    Create a test client for the FastAPI app.
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def admin_token(client) -> str:
    """
    Get an admin authentication token.
    """
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin@freshmanna.com",
            "password": "Admin@123"
        }
    )
    assert response.status_code == 200, f"Admin login failed: {response.json()}"
    return response.json()["access_token"]


@pytest.fixture
async def author_token(client) -> str:
    """
    Get an author authentication token.
    Creates a test author if needed.
    """
    # Try to login with existing author
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "author@test.com",
            "password": "Author@123"
        }
    )

    if response.status_code == 200:
        return response.json()["access_token"]

    # If author doesn't exist, register one
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "author@test.com",
            "password": "Author@123",
            "full_name": "Test Author",
            "role": "author"
        }
    )

    if register_response.status_code == 201:
        # Login after registration
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "author@test.com",
                "password": "Author@123"
            }
        )
        return login_response.json()["access_token"]

    raise Exception(f"Failed to create author token: {register_response.json()}")


@pytest.fixture
async def test_devotional(test_db, admin_token) -> Dict[str, Any]:
    """
    Create a test devotional in the database.
    Returns the devotional document.
    """
    devotional = {
        "_id": ObjectId(),
        "title": "Test Devotional for Testing",
        "content": "This is a test devotional content for comprehensive testing.",
        "scripture_reference": "John 3:16",
        "author_id": "693acf37d221b83bb8f2d2a7",  # Admin user ID
        "author_name": "Test Admin",
        "author_email": "admin@freshmanna.com",
        "category": "prayer",
        "tags": ["test", "prayer", "faith"],
        "status": "published",
        "scheduled_date": datetime.utcnow(),
        "view_count": 0,
        "like_count": 0,
        "comment_count": 0,
        "share_count": 0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "published_at": datetime.utcnow()
    }

    await test_db.devotionals.insert_one(devotional)
    yield devotional

    # Cleanup: Delete the devotional after test
    await test_db.devotionals.delete_one({"_id": devotional["_id"]})


@pytest.fixture
async def test_user(test_db) -> Dict[str, Any]:
    """
    Create a test user in the database.
    """
    user = {
        "_id": ObjectId(),
        "email": "testuser@test.com",
        "full_name": "Test User",
        "role": "user",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    await test_db.users.insert_one(user)
    yield user

    # Cleanup
    await test_db.users.delete_one({"_id": user["_id"]})


@pytest.fixture
async def cleanup_collections(test_db):
    """
    Cleanup test data after tests.
    Use this for tests that create data but don't clean up.
    """
    yield

    # Clean up test data (data created during tests with 'test' in fields)
    await test_db.devotionals.delete_many({"title": {"$regex": "Test", "$options": "i"}})
    await test_db.comments.delete_many({"content": {"$regex": "Test", "$options": "i"}})
    await test_db.flags.delete_many({"reason": {"$regex": "Test", "$options": "i"}})


def create_auth_header(token: str) -> Dict[str, str]:
    """
    Helper function to create authorization header.

    Args:
        token: JWT token string

    Returns:
        Dictionary with Authorization header
    """
    return {"Authorization": f"Bearer {token}"}
