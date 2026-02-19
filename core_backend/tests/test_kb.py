import pathlib
import sys
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

import mongomock
from backend.models import ServiceAccount
from backend.services import service_account_service
from backend import kb

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from backend.main import app  # noqa: E402


client = TestClient(app)


@pytest.fixture(autouse=True)
def _setup() -> None:
    service_account_service._collection = mongomock.MongoClient().db.service_accounts
    kb._sources = mongomock.MongoClient().db.kb_sources
    kb._chunks = mongomock.MongoClient().db.kb_chunks
    yield


@pytest.fixture()
def auth_header() -> dict[str, str]:
    token = "testtoken"
    service_account_service.create_account(
        ServiceAccount(id=str(uuid4()), name="tester", token=token, tenant_id=str(uuid4()), permissions={"admin": True})
    )
    return {"X-Service-Token": token}


def test_ingest_kb(auth_header: dict[str, str]) -> None:
    tenant_id = uuid4()
    payload = {"tenant_id": str(tenant_id), "content": "Hello world"}
    resp = client.post("/internal/kb", json=payload, headers=auth_header)
    assert resp.status_code == 200
    data = resp.json()
    assert data["chunks"] == 1
    docs = list(kb._chunks.find())
    assert len(docs) == 1
    assert docs[0]["text"] == "Hello world"


def test_ingest_requires_content(auth_header: dict[str, str]) -> None:
    tenant_id = uuid4()
    resp = client.post(
        "/internal/kb", json={"tenant_id": str(tenant_id)}, headers=auth_header
    )
    assert resp.status_code == 400


def test_ingest_requires_auth() -> None:
    tenant_id = uuid4()
    resp = client.post(
        "/internal/kb",
        json={"tenant_id": str(tenant_id), "content": "hi"},
        headers={"X-Service-Token": "bad"},
    )
    assert resp.status_code == 401


def test_kb_search(auth_header: dict[str, str]) -> None:
    tenant_id = uuid4()
    client.post(
        "/internal/kb",
        json={"tenant_id": str(tenant_id), "content": "Fast cars"},
        headers=auth_header,
    )
    client.post(
        "/internal/kb",
        json={"tenant_id": str(tenant_id), "content": "Slow bikes"},
        headers=auth_header,
    )
    resp = client.post(
        "/internal/kb/search",
        json={"tenant_id": str(tenant_id), "query": "cars"},
        headers=auth_header,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data[0]["text"] == "Fast cars"


def test_kb_search_requires_auth() -> None:
    tenant_id = uuid4()
    resp = client.post(
        "/internal/kb/search",
        json={"tenant_id": str(tenant_id), "query": "hi"},
        headers={"X-Service-Token": "bad"},
    )
    assert resp.status_code == 401
