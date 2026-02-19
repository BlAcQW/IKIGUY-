"""Tests for MongoDB-backed storage utilities."""

from uuid import uuid4

import mongomock
import pytest

from .. import storage
from ..models import APIKeyCreate, MCPServer, Webhook
from ..storage import APIKeyStore, MCPServerStore, QuotaStore, WebhookStore


@pytest.fixture(autouse=True)
def mock_collections(monkeypatch) -> None:
    """Provide mongomock collections to the storage module."""

    client = mongomock.MongoClient()
    db = client["kasaai_dev"]
    monkeypatch.setattr(storage, "_api_keys", db["api_keys"])
    monkeypatch.setattr(storage, "_quotas", db["quotas"])
    monkeypatch.setattr(storage, "_webhooks", db["webhooks"])
    monkeypatch.setattr(storage, "_mcp_servers", db["mcp_servers"])


def test_api_key_store_crud() -> None:
    """Test create, retrieve, rotate, revoke, and list operations for API keys."""

    store = APIKeyStore()
    payload = APIKeyCreate(tenant_id=uuid4(), scopes=["read"])
    key = store.create(payload)
    assert store.get(key.id) is not None

    old_secret = key.secret
    rotated = store.rotate(key.id)
    assert rotated.secret != old_secret

    revoked = store.revoke(key.id)
    assert revoked.revoked is True

    keys = store.list()
    assert any(k.id == key.id for k in keys)


def test_api_key_store_missing() -> None:
    """Edge and failure cases for missing API keys."""

    store = APIKeyStore()
    missing = uuid4()
    assert store.get(missing) is None
    with pytest.raises(ValueError):
        store.rotate(missing)


def test_quota_store_flow() -> None:
    """Test quota creation, update, increment, and retrieval."""

    api_key = APIKeyStore().create(APIKeyCreate(tenant_id=uuid4(), scopes=[]))
    store = QuotaStore()

    quota = store.create_or_update(api_key.id, "day", 5)
    assert quota.limit == 5

    quota = store.create_or_update(api_key.id, "day", 10)
    assert quota.limit == 10

    quota = store.increment(api_key.id, "day", 3)
    assert quota.used == 3

    fetched = store.get(api_key.id, "day")
    assert fetched is not None and fetched.used == 3


def test_quota_store_limit_exceeded() -> None:
    """Failure when quota increment exceeds limit."""

    api_key = APIKeyStore().create(APIKeyCreate(tenant_id=uuid4(), scopes=[]))
    store = QuotaStore()
    store.create_or_update(api_key.id, "day", 2)
    with pytest.raises(RuntimeError):
        store.increment(api_key.id, "day", 3)


def test_quota_store_get_missing() -> None:
    """Edge case: retrieving a non-existent quota returns None."""

    store = QuotaStore()
    assert store.get(uuid4(), "day") is None


def test_webhook_store_crud() -> None:
    """Test create, update, list, get, and delete operations for webhooks."""

    store = WebhookStore()
    webhook = Webhook(tenant_id=uuid4(), url="https://example.com", events=["event"])
    created = store.create(webhook)
    assert created.secret

    fetched = store.get(created.id)
    assert fetched is not None and fetched.url == "https://example.com"

    updated = store.update(created.id, url="https://new.com")
    assert updated.url == "https://new.com"

    store.delete(created.id)
    assert store.get(created.id) is None


def test_webhook_store_missing_and_delete() -> None:
    """Edge and failure cases for webhooks."""

    store = WebhookStore()
    missing = uuid4()
    assert store.get(missing) is None
    with pytest.raises(ValueError):
        store.delete(missing)


def test_mcp_server_store_crud() -> None:
    """Test create, update, call_tool, and delete for MCP servers."""

    store = MCPServerStore()
    server = MCPServer(
        tenant_id=uuid4(), url="https://mcp.example", tool_names=["tool"]
    )
    created = store.create(server)
    assert store.get(created.id) is not None

    updated = store.update(created.id, status="inactive")
    assert updated.status == "inactive"

    response = store.call_tool(created.id, "tool", {"a": 1})
    assert response["result"] == "mock_result"

    store.delete(created.id)
    assert store.get(created.id) is None


def test_mcp_server_store_missing() -> None:
    """Edge and failure cases for MCP servers."""

    store = MCPServerStore()
    missing = uuid4()
    assert store.get(missing) is None
    with pytest.raises(ValueError):
        store.call_tool(missing, "tool", {})
