"""
Pytest fixtures for integration tests.

Shared fixtures for integration testing across all test modules.
"""

import pytest
from unittest.mock import MagicMock
from apps.shared.integration.ai_services.provider_registry import reset_global_registry


@pytest.fixture(autouse=True)
def reset_global_state():
    """Reset global registry state before each test."""
    reset_global_registry()
    yield
    reset_global_registry()


@pytest.fixture
def mock_mongodb_connection():
    """Mock MongoDB connection for testing."""
    mock_client = MagicMock()
    mock_db = MagicMock()
    mock_collection = MagicMock()

    mock_client.__getitem__.return_value = mock_db
    mock_db.__getitem__.return_value = mock_collection

    return mock_client, mock_db, mock_collection


@pytest.fixture
def mock_postgres_connection():
    """Mock PostgreSQL connection for testing."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    mock_conn.cursor.return_value = mock_cursor

    return mock_conn, mock_cursor


@pytest.fixture
def mock_redis_connection():
    """Mock Redis connection for caching tests."""
    mock_redis = MagicMock()

    # Mock common Redis operations
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    mock_redis.delete.return_value = 1
    mock_redis.exists.return_value = 0

    return mock_redis


@pytest.fixture
def test_auth_token():
    """Test authentication token."""
    return "test_token_123456"


@pytest.fixture
def test_user_id():
    """Test user ID."""
    return "user_123"
