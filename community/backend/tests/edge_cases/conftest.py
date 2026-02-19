"""
Pytest configuration and fixtures for edge case tests.

These fixtures provide real service connections for edge case testing.
"""

import pytest
import asyncio
import os
from typing import Generator, AsyncGenerator
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure custom markers for edge case tests."""
    config.addinivalue_line(
        "markers", "edge_case: mark test as edge case test (tests unusual scenarios)"
    )


@pytest.fixture(scope="function")
def event_loop() -> Generator:
    """Create an instance of the default event loop for each test."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


# ============================================================================
# Environment Configuration
# ============================================================================

@pytest.fixture(scope="session")
def test_mongodb_url() -> str:
    """Get test MongoDB connection URL from environment."""
    return os.getenv(
        "TEST_MONGODB_URL",
        "mongodb://admin:aawwER4444%25@127.0.0.1:27017/kasaai_test?authSource=admin"
    )


@pytest.fixture(scope="session")
def test_database_name() -> str:
    """Get test database name."""
    return "kasaai_test"


# ============================================================================
# Real MongoDB Connection
# ============================================================================

@pytest.fixture(scope="function")
async def real_mongodb_client(test_mongodb_url: str) -> AsyncGenerator:
    """
    Create real MongoDB client connection for edge case tests.

    This is NOT a mock - it connects to an actual MongoDB instance.
    """
    client = AsyncIOMotorClient(test_mongodb_url)

    # Verify connection
    try:
        await client.admin.command('ping')
        print(f"\n✅ Connected to test MongoDB: {test_mongodb_url}")
    except Exception as e:
        pytest.skip(f"MongoDB connection failed: {e}")

    yield client

    # Cleanup: Close connection
    client.close()


@pytest.fixture(scope="function")
async def real_test_db(
    real_mongodb_client: AsyncIOMotorClient,
    test_database_name: str
) -> AsyncGenerator:
    """
    Provide real test database with automatic cleanup.

    Each test gets a fresh database state.
    """
    db = real_mongodb_client[test_database_name]

    # Clean database before test
    collection_names = await db.list_collection_names()
    for collection_name in collection_names:
        await db[collection_name].delete_many({})

    yield db

    # Clean database after test
    collection_names = await db.list_collection_names()
    for collection_name in collection_names:
        await db[collection_name].delete_many({})
