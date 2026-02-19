import sys
import pathlib
from uuid import uuid4

import mongomock
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from apps.developer_platform.backend import mongo, models


def _setup_mongo(monkeypatch):
    """Configure mongomock client for tests."""

    monkeypatch.setenv("MONGODB_URL", "mongodb://localhost")
    monkeypatch.setenv("MONGODB_DB", "test_db")
    monkeypatch.setattr(mongo, "MongoClient", mongomock.MongoClient)


def test_api_key_and_quota_stores(monkeypatch):
    """Validate Mongo-backed API key and quota storage operations."""

    _setup_mongo(monkeypatch)
    from apps.developer_platform.backend import storage

    key_store = storage.APIKeyStore()
    quota_store = storage.QuotaStore()
    key = key_store.create(models.APIKeyCreate(tenant_id=uuid4(), scopes=["x"]))
    quota = quota_store.create_or_update(key.id, "daily", 1)
    assert quota.limit == 1
    quota_store.increment(key.id, "daily")
    with pytest.raises(RuntimeError):
        quota_store.increment(key.id, "daily")
