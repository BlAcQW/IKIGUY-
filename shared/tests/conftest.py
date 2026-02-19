"""Pytest configuration for shared library tests."""

import pytest
import asyncio
from typing import AsyncGenerator


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def memory_storage():
    """Create memory storage backend for testing"""
    from ..storage.interfaces import StorageConfig
    from ..storage.memory import MemoryStorageBackend

    config = StorageConfig(backend_type="memory")
    storage = MemoryStorageBackend(config)
    await storage.connect()
    return storage


@pytest.fixture
async def redis_storage():
    """Create Redis storage backend for testing"""
    from ..storage.interfaces import StorageConfig
    from ..storage.redis import RedisStorageBackend

    config = StorageConfig(
        backend_type="redis",
        host="127.0.0.1",
        port=6379,
        username="inspireadmin",
        password="aawwER444444",
    )
    storage = RedisStorageBackend(config)

    # Try to connect, skip tests if Redis is not available
    try:
        connected = await storage.connect()
        if not connected:
            pytest.skip("Redis not available")
        return storage
    except Exception:
        pytest.skip("Redis not available")


@pytest.fixture
async def postgres_storage():
    """Create PostgreSQL storage backend for testing"""
    from ..storage.interfaces import StorageConfig
    from ..storage.postgres import PostgresStorageBackend

    config = StorageConfig(
        backend_type="postgresql",
        host="85.214.12.174",
        port=5432,
        database="kasaai",
        username="postgres",
        password="aawwER444444",
    )
    storage = PostgresStorageBackend(config)

    # Try to connect, skip tests if PostgreSQL is not available
    try:
        connected = await storage.connect()
        if not connected:
            pytest.skip("PostgreSQL not available")
        return storage
    except Exception:
        pytest.skip("PostgreSQL not available")
