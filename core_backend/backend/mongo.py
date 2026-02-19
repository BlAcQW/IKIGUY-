"""MongoDB connection helpers for Core Backend."""

from __future__ import annotations

import os
from motor.motor_asyncio import AsyncIOMotorClient
from motor.motor_asyncio import AsyncIOMotorCollection
from motor.motor_asyncio import AsyncIOMotorDatabase

_client: AsyncIOMotorClient | None = None


def get_client() -> AsyncIOMotorClient:
    """Create or return an async MongoDB client.

    Returns:
        AsyncIOMotorClient: Active async client connected to the configured URL.
    """

    global _client
    if _client is None:
        url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        _client = AsyncIOMotorClient(url)
    return _client


def get_collection(name: str) -> AsyncIOMotorCollection:
    """Return a collection from the Core database.

    Args:
        name (str): Collection name.

    Returns:
        AsyncIOMotorCollection: MongoDB collection instance.
    """

    db_name = os.getenv("MONGODB_DB", "kasaai_core")
    return get_client()[db_name][name]


def get_database() -> AsyncIOMotorDatabase:
    """Return the Core database.

    Returns:
        AsyncIOMotorDatabase: MongoDB database instance.
    """
    db_name = os.getenv("MONGODB_DB", "kasaai_core")
    return get_client()[db_name]
