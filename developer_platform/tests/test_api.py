from __future__ import annotations

from uuid import uuid4

import os
import pathlib
import sys

import pytest
from fastapi.testclient import TestClient

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

os.environ["DEVPLAT_DB_URL"] = "sqlite:///:memory:"
from apps.developer_platform.backend.main import app


@pytest.fixture(autouse=True)
def _cleanup_db() -> None:
    yield


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_and_get_api_key() -> None:
    tenant_id = uuid4()
    payload = {"tenant_id": str(tenant_id), "scopes": ["assistants:write"]}
    create_resp = client.post("/api-keys", json=payload)
    assert create_resp.status_code == 200
    data = create_resp.json()
    key_id = data["id"]
    assert data["tenant_id"] == str(tenant_id)
    assert data["scopes"] == ["assistants:write"]
    assert data["secret"]

    get_resp = client.get(f"/api-keys/{key_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == key_id


def test_get_missing_api_key() -> None:
    response = client.get(f"/api-keys/{uuid4()}")
    assert response.status_code == 404


def test_rotate_and_revoke_api_key() -> None:
    tenant_id = uuid4()
    payload = {"tenant_id": str(tenant_id), "scopes": ["kb:read"]}
    create_resp = client.post("/api-keys", json=payload)
    key_id = create_resp.json()["id"]

    rotate_resp = client.post(f"/api-keys/{key_id}/rotate")
    assert rotate_resp.status_code == 200
    new_secret = rotate_resp.json()["secret"]
    assert new_secret

    revoke_resp = client.delete(f"/api-keys/{key_id}")
    assert revoke_resp.status_code == 200
    assert revoke_resp.json()["status"] == "revoked"


def test_quota_endpoints() -> None:
    tenant_id = uuid4()
    payload = {"tenant_id": str(tenant_id), "scopes": ["kb:read"]}
    create_resp = client.post("/api-keys", json=payload)
    key_id = create_resp.json()["id"]

    quota_payload = {
        "api_key_id": key_id,
        "period": "daily",
        "limit": 2,
    }
    quota_resp = client.post(f"/api-keys/{key_id}/quota", json=quota_payload)
    assert quota_resp.status_code == 200
    assert quota_resp.json()["limit"] == 2

    inc1 = client.post(f"/api-keys/{key_id}/quota/daily/increment")
    assert inc1.status_code == 200
    assert inc1.json()["used"] == 1

    inc2 = client.post(f"/api-keys/{key_id}/quota/daily/increment")
    assert inc2.status_code == 200
    assert inc2.json()["used"] == 2

    inc3 = client.post(f"/api-keys/{key_id}/quota/daily/increment")
    assert inc3.status_code == 429
