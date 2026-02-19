"""MongoDB connection utilities for the Developer Platform backend."""

from __future__ import annotations

import os
from pymongo import MongoClient
from pymongo.collection import Collection

_client: MongoClient | None = None


def get_client() -> MongoClient:
    """Return a shared MongoDB client instance."""

    global _client
    if _client is None:
        url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        _client = MongoClient(url)
    return _client


def get_collection(name: str) -> Collection:
    """Return a collection from the Developer Platform database."""

    db_name = os.getenv("MONGODB_DB", "kasaai_dev")
    return get_client()[db_name][name]

