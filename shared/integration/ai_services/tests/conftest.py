"""
Pytest configuration for AI services tests.

Provides common fixtures and configuration for all test modules.
"""

import pytest
import asyncio


@pytest.fixture(scope="session")
def event_loop():
    """
    Create an instance of the default event loop for the test session.

    This fixture ensures that async tests have access to an event loop.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def reset_global_state():
    """
    Reset global state before each test.

    This ensures that tests don't interfere with each other.
    """
    from apps.shared.integration.ai_services.provider_registry import (
        reset_global_registry,
    )

    # Reset global registry before each test
    reset_global_registry()

    yield

    # Cleanup after test
    reset_global_registry()
