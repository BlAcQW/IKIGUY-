"""
Pytest configuration and fixtures for integration tests.

These fixtures provide real service connections (not mocks):
- Real MongoDB database connection
- Real HTTP client for API testing
- JWT token generation for authentication
- Test data fixtures with cleanup
"""

import pytest
import asyncio
import os
import sys
from typing import Generator, AsyncGenerator
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timedelta
from bson import ObjectId
import uuid
import jwt

# Add backend directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure custom markers for integration tests."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires real services)"
    )
    config.addinivalue_line(
        "markers", "api: mark test as API-level integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end user journey test"
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
        "mongodb://admin:aawwER4444%25@127.0.0.1:27017/community_integration_test?authSource=admin"
    )


@pytest.fixture(scope="session")
def test_database_name() -> str:
    """Get test database name."""
    return "community_integration_test"


@pytest.fixture(scope="session")
def jwt_secret() -> str:
    """Get JWT secret for test token generation."""
    return os.getenv("JWT_SECRET", "test-jwt-secret-key-for-integration-tests")


# ============================================================================
# Real MongoDB Connection
# ============================================================================

@pytest.fixture(scope="function")
async def real_mongodb_client(test_mongodb_url: str) -> AsyncGenerator:
    """
    Create real MongoDB client connection for integration tests.

    This is NOT a mock - it connects to an actual MongoDB instance.
    """
    client = AsyncIOMotorClient(test_mongodb_url)

    # Verify connection
    try:
        await client.admin.command('ping')
        print(f"\n✅ Connected to test MongoDB")
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


# ============================================================================
# Test User & Authentication
# ============================================================================

@pytest.fixture
def test_user_id() -> str:
    """Return the dev user ObjectId that matches the dev-token authentication."""
    # Use a fixed valid ObjectId for dev user (matches mongodb_auth_service.py)
    return "000000000000000000000001"


@pytest.fixture
def test_user_data(test_user_id: str) -> dict:
    """Generate test user data with unique identifiers."""
    timestamp = datetime.utcnow()
    return {
        "_id": ObjectId(test_user_id),  # Use the fixed dev user ObjectId
        "user_id": test_user_id,  # Store the string ID for lookups
        "supabase_id": f"test-user-{uuid.uuid4().hex[:8]}",
        "email": "dev@example.com",  # Match the dev-token user email
        "username": "dev_user",  # Match the dev-token username
        "full_name": "Development User",
        "avatar_url": None,
        "bio": "Integration test user",
        "location": "Test City",
        "languages_spoken": ["twi", "eng"],
        "level": "newcomer",
        "role": "admin",  # Admin role for testing governance endpoints
        "total_points": 0,
        "achievements": [],
        "badges": [],
        "language_expertise": [],
        "verified_languages": [],
        "permissions": ["submit", "comment", "validate", "moderate"],
        "can_validate": True,
        "can_moderate": True,  # Enable moderation for testing
        "can_create_proposals": True,
        "contributions_count": 0,
        "validations_count": 0,
        "quality_rating": 0.0,
        "reputation_score": 0.0,
        "is_active": True,
        "member_since": timestamp,
        "created_at": timestamp,
        "updated_at": timestamp
    }


@pytest.fixture
def generate_auth_token(jwt_secret: str):
    """Factory to generate JWT auth tokens for testing."""
    def _generate(user_id: str, email: str = "test@example.com") -> str:
        payload = {
            "user_id": user_id,
            "id": user_id,
            "email": email,
            "name": "Test User",
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, jwt_secret, algorithm="HS256")
    return _generate


@pytest.fixture
def auth_headers(generate_auth_token, test_user_id: str) -> dict:
    """Generate authentication headers with valid JWT token."""
    token = generate_auth_token(test_user_id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def dev_auth_headers() -> dict:
    """Generate dev authentication headers (bypasses JWT validation)."""
    return {"Authorization": "Bearer dev-token"}


# ============================================================================
# Real HTTP Client for API Testing
# ============================================================================

@pytest.fixture
async def api_client(real_test_db: AsyncIOMotorDatabase) -> AsyncGenerator:
    """
    Create HTTP client for API integration tests with real database.

    This patches the database dependency to use the test database.
    """
    # Import app after database is set up
    from main import app
    import database as db_module

    # Store original get_database
    original_get_database = db_module.get_database

    # Patch get_database to return test database
    def test_get_database():
        return real_test_db

    db_module.get_database = test_get_database

    # Also set global mongodb to test db
    db_module.mongodb = real_test_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    # Restore original
    db_module.get_database = original_get_database


# ============================================================================
# Test Data Fixtures - Languages
# ============================================================================

@pytest.fixture
def sample_language_family() -> dict:
    """Generate sample language family data."""
    return {
        "_id": ObjectId(),
        "name": "niger-congo",
        "display_name": "Niger-Congo Languages",
        "description": "The largest language family in Africa",
        "geographic_region": ["West Africa", "Central Africa"],
        "subfamilies": ["kwa", "bantu", "yoruboid"],
        "shared_features": {
            "noun_classes": True,
            "tone_language": True
        },
        "speaker_count_estimate": 700000000,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def sample_language() -> dict:
    """Generate sample language data."""
    return {
        "_id": ObjectId(),
        "subfamily_id": str(ObjectId()),
        "code": "twi",
        "name": "Twi (Akan)",
        "native_name": "Twi",
        "alternative_names": ["Akan", "Asante Twi"],
        "countries": ["Ghana"],
        "regions": ["Ashanti Region", "Brong-Ahafo Region"],
        "speaker_count": 9000000,
        "linguistic_features": {"word_order": "SVO", "tone_levels": 2},
        "phonetic_inventory": {"vowels": 10, "consonants": 20},
        "tonal_system": {"levels": ["high", "low"]},
        "writing_systems": ["Latin", "Adinkra"],
        "cultural_context": {"primary_use": "daily_communication"},
        "dialects": ["Asante", "Akuapem", "Fante"],
        "data_tier": "tier-1-validated",
        "voice_support_level": "full",
        "active_contributors": 156,
        "available_models": [],
        "available_datasets": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


# ============================================================================
# Test Data Fixtures - MLOps
# ============================================================================

@pytest.fixture
def sample_model_create_data() -> dict:
    """Generate sample ML model creation data."""
    return {
        "name": "Twi TTS Model v1",
        "description": "Text-to-speech model for Twi language",
        "model_type": "tts",
        "architecture": "melotts",
        "version": "1.0.0",
        "languages": ["twi"],
        "primary_language": "twi",
        "is_multilingual": False,
        "storage_path": f"models/tts/test-model-{uuid.uuid4().hex[:8]}/v1.0.0",
        "checkpoint_path": f"models/tts/test-model-{uuid.uuid4().hex[:8]}/v1.0.0/checkpoint.pt",
        "deployment_status": "experimental",
        "license": "MIT",
        "is_public": True,
        "access_level": "public",
        "tags": ["tts", "melotts", "twi"],
        "training_datasets": [],
        "evaluation_datasets": []
    }


@pytest.fixture
def sample_pipeline_create_data() -> dict:
    """Generate sample training pipeline creation data."""
    return {
        "name": f"Twi TTS Training Pipeline {uuid.uuid4().hex[:8]}",
        "description": "Training pipeline for Twi TTS model",
        "model_type": "tts",
        "target_version": "1.0.0",
        "priority": "medium",
        "tags": ["tts", "twi"],
        "datasets": []
    }


@pytest.fixture
def sample_resource_link_data() -> dict:
    """Generate sample external resource link data."""
    return {
        "title": f"Twi Speech Dataset {uuid.uuid4().hex[:8]}",
        "url": f"https://github.com/example/twi-speech-{uuid.uuid4().hex[:8]}",
        "resource_type": "dataset",
        "languages": ["twi"],
        "is_multilingual": False,
        "description": "Open source Twi speech dataset for ASR training",
        "tags": ["speech", "twi", "dataset", "asr"],
        "license": "MIT"
    }


@pytest.fixture
def sample_dataset_version_data() -> dict:
    """Generate sample dataset version data."""
    return {
        "version": "1.0.0",
        "changelog": "Initial release with 1000 audio samples",
        "storage_path": f"datasets/test-dataset-{uuid.uuid4().hex[:8]}/v1.0.0",
        "file_count": 1000,
        "total_size_mb": 500.0,
        "quality_report": {
            "validation_passed": True,
            "error_count": 0
        }
    }


# ============================================================================
# Database Seeding Fixtures
# ============================================================================

@pytest.fixture
async def seeded_language(real_test_db: AsyncIOMotorDatabase, sample_language: dict) -> dict:
    """Insert a language into the test database and return it."""
    result = await real_test_db.languages.insert_one(sample_language)
    sample_language["_id"] = result.inserted_id
    return sample_language


@pytest.fixture
async def seeded_user(real_test_db: AsyncIOMotorDatabase, test_user_data: dict) -> dict:
    """Insert a user into the test database and return it."""
    result = await real_test_db.users.insert_one(test_user_data)
    test_user_data["_id"] = result.inserted_id
    return test_user_data


@pytest.fixture
async def seeded_model(
    real_test_db: AsyncIOMotorDatabase,
    sample_model_create_data: dict,
    test_user_id: str,
    seeded_language: dict
) -> dict:
    """Insert an ML model into the test database and return it."""
    model_doc = {
        **sample_model_create_data,
        "_id": ObjectId(),
        "model_uuid": str(uuid.uuid4()),
        "language_ids": [str(seeded_language["_id"])],
        "version_history": [],
        "created_by": test_user_id,
        "contributors": [],
        "known_issues": [],
        "download_count": 0,
        "view_count": 0,
        "performance_metrics": {},
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    result = await real_test_db.ml_models.insert_one(model_doc)
    model_doc["_id"] = result.inserted_id
    return model_doc


# ============================================================================
# Utility Fixtures
# ============================================================================

@pytest.fixture
def measure_time():
    """Measure execution time of operations."""
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


@pytest.fixture
async def verify_db_state():
    """Helper to verify database state in tests."""
    async def _verify(db: AsyncIOMotorDatabase, collection: str, query: dict):
        """Verify a document exists in the database."""
        doc = await db[collection].find_one(query)
        assert doc is not None, f"Document not found in {collection}: {query}"
        return doc
    return _verify


# ============================================================================
# Mock Cursor for unit test compatibility
# ============================================================================

class AsyncIterator:
    """Mock async iterator for testing."""
    def __init__(self, items: list):
        self.items = items
        self.index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.index >= len(self.items):
            raise StopAsyncIteration
        item = self.items[self.index]
        self.index += 1
        return item


class MockCursor:
    """Mock MongoDB cursor with async iteration and to_list support."""
    def __init__(self, items: list):
        self.items = items
        self._sorted = False
        self._skip_count = 0
        self._limit_count = None

    def sort(self, *args, **kwargs):
        self._sorted = True
        return self

    def skip(self, count: int):
        self._skip_count = count
        return self

    def limit(self, count: int):
        self._limit_count = count
        return self

    async def to_list(self, length: int = None):
        result = self.items[self._skip_count:]
        if self._limit_count is not None:
            result = result[:self._limit_count]
        elif length is not None:
            result = result[:length]
        return result

    def __aiter__(self):
        result = self.items[self._skip_count:]
        if self._limit_count is not None:
            result = result[:self._limit_count]
        return AsyncIterator(result)
