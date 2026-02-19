"""
Pytest configuration and fixtures for security tests.

These fixtures provide real service connections for security testing:
- Real MongoDB database connection
- Real HTTP client for API testing
- Security test utilities
"""

import pytest
import asyncio
import os
from typing import Generator, AsyncGenerator
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from httpx import AsyncClient
from datetime import datetime


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure custom markers for security tests."""
    config.addinivalue_line(
        "markers", "security: mark test as security test (tests vulnerabilities)"
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


@pytest.fixture(scope="session")
def test_api_base_url() -> str:
    """Get test API base URL."""
    return os.getenv("TEST_API_BASE_URL", "http://localhost:8001")


# ============================================================================
# Real MongoDB Connection
# ============================================================================

@pytest.fixture(scope="function")
async def real_mongodb_client(test_mongodb_url: str) -> AsyncGenerator:
    """
    Create real MongoDB client connection for security tests.

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

    Each test gets a fresh database state:
    - Database is cleaned before test
    - Test runs with real database
    - Database is cleaned after test
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


# ============================================================================
# Real HTTP Client for API Testing
# ============================================================================

@pytest.fixture
async def real_api_client(test_api_base_url: str) -> AsyncGenerator:
    """
    Create real HTTP client for API security tests.

    This makes actual HTTP requests to the running API.
    """
    async with AsyncClient(base_url=test_api_base_url, timeout=30.0) as client:
        # Verify API is reachable
        try:
            response = await client.get("/health")
            if response.status_code not in [200, 404]:
                pytest.skip(f"API not reachable at {test_api_base_url}")
        except Exception as e:
            pytest.skip(f"API connection failed: {e}")

        yield client


# ============================================================================
# Security Test Utilities
# ============================================================================

@pytest.fixture
def attack_payloads():
    """
    Provide common attack payloads for security testing.

    Returns dictionary of attack vectors categorized by type.
    """
    return {
        "xss": [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg/onload=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(\"XSS\")'></iframe>"
        ],
        "sql_injection": [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users--",
            "admin'--",
            "1' AND '1'='1"
        ],
        "nosql_injection": [
            {"$ne": None},
            {"$gt": ""},
            {"$regex": ".*"},
            {"$where": "function() { return true; }"}
        ],
        "command_injection": [
            "; ls -la",
            "| cat /etc/passwd",
            "& ping -c 10 evil.com",
            "`whoami`",
            "$(cat /etc/passwd)"
        ],
        "path_traversal": [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "....//....//etc/passwd",
            "..%2f..%2fetc%2fpasswd"
        ],
        "template_injection": [
            "{{7*7}}",
            "${7*7}",
            "<%=7*7%>",
            "{{config}}",
            "{{request}}"
        ]
    }


@pytest.fixture
def malicious_headers():
    """Provide malicious HTTP headers for testing."""
    return {
        "X-Forwarded-For": "127.0.0.1, 10.0.0.1",  # IP spoofing
        "X-Real-IP": "192.168.1.1",
        "User-Agent": "<script>alert('XSS')</script>",
        "Referer": "javascript:alert('XSS')",
        "Cookie": "admin=true; session=malicious",
    }


@pytest.fixture
async def create_test_user(real_test_db: AsyncIOMotorDatabase):
    """Helper to create test users for security tests."""
    async def _create_user(username: str, **kwargs):
        """
        Create a test user in the database.

        Args:
            username: Username for the test user
            **kwargs: Additional user fields

        Returns:
            ObjectId: ID of created user
        """
        from bson import ObjectId
        import uuid

        user_data = {
            "supabase_id": f"test-{username}-{uuid.uuid4()}",
            "email": kwargs.get("email", f"{username}@example.com"),
            "username": username,
            "is_active": kwargs.get("is_active", True),
            "created_at": datetime.utcnow(),
            **kwargs
        }

        result = await real_test_db.users.insert_one(user_data)
        return result.inserted_id

    return _create_user


@pytest.fixture
def measure_timing():
    """
    Measure execution timing for timing attack tests.

    Usage:
        with measure_timing() as timer:
            # ... operation ...
        elapsed = timer.elapsed
    """
    import time

    class Timer:
        def __init__(self):
            self.start = None
            self.end = None
            self.elapsed = None

        def __enter__(self):
            self.start = time.time()
            return self

        def __exit__(self, *args):
            self.end = time.time()
            self.elapsed = self.end - self.start

    return Timer
