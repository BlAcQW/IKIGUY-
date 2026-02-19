"""
Pytest configuration and fixtures for InkWave tests.
"""

import pytest
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings


@pytest.fixture(scope="session")
def event_loop():
    """
    Create event loop for async tests.

    Returns:
        asyncio event loop
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def db_client():
    """
    Create MongoDB client for testing.

    Yields:
        AsyncIOMotorClient instance
    """
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    yield client
    client.close()


@pytest.fixture(scope="session")
async def test_db(db_client):
    """
    Get test database instance.

    Args:
        db_client: MongoDB client fixture

    Yields:
        AsyncIOMotorDatabase instance
    """
    db = db_client[settings.MONGODB_DB_NAME]
    yield db


@pytest.fixture
async def test_user_data():
    """
    Test user data fixture.

    Returns:
        dict: Test user data
    """
    return {
        "email": "test@example.com",
        "display_name": "Test User",
        "is_admin": False,
        "credits": 100
    }


@pytest.fixture
async def test_book_data():
    """
    Test book data fixture.

    Returns:
        dict: Test book data
    """
    return {
        "title": "Test Book",
        "author": "Test Author",
        "isbn": "978-0000000000",
        "description": "A test book for unit testing.",
        "genre": ["Test", "Fiction"],
        "metadata": {
            "summary": "Test summary",
            "word_count": 50000,
            "page_count": 200,
            "estimated_reading_time_minutes": 250,
            "difficulty_level": "intermediate",
            "language": "en"
        }
    }
