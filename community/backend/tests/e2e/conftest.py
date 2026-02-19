"""
Pytest configuration and fixtures for End-to-End tests.

E2E tests share fixtures with integration tests but focus on
complete user journey workflows rather than individual endpoints.

These tests require real services:
- Real MongoDB database
- Real HTTP client
- Authentication tokens
"""

import pytest

# Import all fixtures from integration tests
from tests.integration.conftest import (
    # Configuration
    pytest_configure,
    event_loop,
    test_mongodb_url,
    test_database_name,
    jwt_secret,

    # Database
    real_mongodb_client,
    real_test_db,

    # Authentication
    test_user_id,
    test_user_data,
    generate_auth_token,
    auth_headers,
    dev_auth_headers,

    # API Client
    api_client,

    # Test Data - Languages
    sample_language_family,
    sample_language,

    # Test Data - MLOps
    sample_model_create_data,
    sample_pipeline_create_data,
    sample_resource_link_data,
    sample_dataset_version_data,

    # Seeded Data
    seeded_language,
    seeded_user,
    seeded_model,

    # Utilities
    measure_time,
    verify_db_state,

    # Mock utilities (for compatibility)
    AsyncIterator,
    MockCursor,
)


# E2E specific markers
def pytest_configure(config):
    """Configure custom markers for E2E tests."""
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end user journey test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow-running"
    )


@pytest.fixture
async def clean_test_data(real_test_db):
    """
    Clean up test data after E2E tests.

    This ensures each E2E test starts with a clean slate.
    """
    yield

    # Cleanup collections after test
    collections_to_clean = [
        "ml_models",
        "ml_training_pipelines",
        "dataset_versions",
        "resource_links",
        "file_uploads",
        "users",
        "languages",
        "submissions",
        "validations"
    ]

    for collection in collections_to_clean:
        await real_test_db[collection].delete_many({})


@pytest.fixture
async def seeded_complete_environment(
    real_test_db,
    seeded_user,
    seeded_language,
    seeded_model
):
    """
    Provide a fully seeded test environment for E2E tests.

    Includes:
    - A test user
    - A language (Twi)
    - A model
    """
    return {
        "user": seeded_user,
        "language": seeded_language,
        "model": seeded_model,
        "db": real_test_db
    }
