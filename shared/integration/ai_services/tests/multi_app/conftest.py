"""
Shared fixtures for multi-app validation tests.
"""

import pytest
import sys
import os
from typing import List
from contextlib import contextmanager


# Apps that consume shared AI services
CONSUMING_APPS = [
    "core_backend",
    "developer_platform",
    "community",
]


@pytest.fixture(params=CONSUMING_APPS)
def app_name(request):
    """Fixture that provides each consuming app name."""
    return request.param


@pytest.fixture
def app_path(app_name):
    """Fixture that provides the full path to an app."""
    return os.path.abspath(f"/opt/kasaai/apps/{app_name}")


@contextmanager
def app_context(app_name: str):
    """
    Context manager that sets up app-specific PYTHONPATH.

    Args:
        app_name: Name of the app (e.g., 'core_backend')

    Yields:
        str: The app name

    Example:
        with app_context("core_backend"):
            from apps.shared.integration.ai_services.tts_service import TTSService
            service = TTSService()
    """
    app_path = os.path.abspath(f"/opt/kasaai/apps/{app_name}")
    shared_path = os.path.abspath("/opt/kasaai")

    # Store original sys.path
    original_path = sys.path.copy()

    try:
        # Add app and shared paths
        if shared_path not in sys.path:
            sys.path.insert(0, shared_path)
        if app_path not in sys.path:
            sys.path.insert(0, app_path)

        yield app_name

    finally:
        # Restore original sys.path
        sys.path = original_path


@pytest.fixture
def with_app_context(app_name):
    """
    Fixture that provides app context for a test.

    Usage:
        def test_something(with_app_context):
            # Test runs with app context active
            from apps.shared.integration.ai_services.tts_service import TTSService
            service = TTSService()
    """
    with app_context(app_name):
        yield app_name


@pytest.fixture
def mock_app_config(app_name):
    """
    Fixture that provides mock configuration for an app.

    Returns:
        dict: Mock configuration specific to the app
    """
    return {
        "app_name": app_name,
        "tts": {
            "default_provider": "coqui_xtts",
            "timeout": 30,
        },
        "llm": {
            "default_provider": "llama_32_3b",
            "timeout": 60,
        },
        "asr": {
            "default_provider": "akan_whisper",
            "timeout": 120,
        },
        "health_monitor": {
            "check_interval": 60,
            "degradation_threshold": 5000,
        },
    }


@pytest.fixture
def all_consuming_apps():
    """Fixture that provides list of all consuming apps."""
    return CONSUMING_APPS.copy()


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--app",
        action="store",
        default=None,
        help="Run tests for specific app only",
        choices=CONSUMING_APPS,
    )


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers",
        "app(name): mark test to run for specific app only",
    )


def pytest_collection_modifyitems(config, items):
    """Filter tests based on --app option."""
    app_filter = config.getoption("--app")

    if app_filter:
        # Skip tests that don't match the specified app
        skip_marker = pytest.mark.skip(reason=f"Not running for app: {app_filter}")

        for item in items:
            # If test has app parameter, check if it matches
            if "app_name" in item.fixturenames:
                # Get the app parameter value for this test
                app_param = item.callspec.params.get("app_name")
                if app_param and app_param != app_filter:
                    item.add_marker(skip_marker)
