"""
Pytest configuration for StudyFlow backend tests.

Sets up paths and fixtures needed for testing.
"""

import sys
import os

# Set up paths before any imports
sys.path.insert(0, "/opt/kasaai/apps/studyflow/backend")
sys.path.insert(0, "/opt/kasaai/apps")

import pytest


@pytest.fixture(scope="session")
def event_loop_policy():
    """Use default event loop policy."""
    import asyncio
    return asyncio.DefaultEventLoopPolicy()
