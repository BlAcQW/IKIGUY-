import pathlib
import sys
from uuid import uuid4
import os
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from backend import database
from backend.models import ServiceAccount, License

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

os.environ["CORE_DB_URL"] = "sqlite:///:memory:"
from backend.main import app


@pytest.fixture(autouse=True)
def _cleanup_db() -> None:
    database.init_db()
    yield


@pytest.fixture()
def auth_header() -> dict[str, str]:
    token = "testtoken"
    session = database.get_session()
    account = ServiceAccount(name="tester", token=token, scopes=["admin"])
    session.add(account)
    session.commit()
    return {"X-Service-Token": token}


client = TestClient(app)


def test_edge_sync_returns_license(auth_header: dict[str, str]) -> None:
    tenant_id = uuid4()
    session = database.get_session()
    session.add(
        License(
            tenant_id=tenant_id,
            mode="saas",
            expires_at=datetime.utcnow() + timedelta(days=1),
        )
    )
    session.commit()
    resp = client.get(f"/internal/edge/sync?tenant_id={tenant_id}", headers=auth_header)
    assert resp.status_code == 200
    data = resp.json()
    assert data["license"]["tenant_id"] == str(tenant_id)
    assert "usage_export" in data["capabilities"]


def test_edge_sync_without_license(auth_header: dict[str, str]) -> None:
    tenant_id = uuid4()
    resp = client.get(f"/internal/edge/sync?tenant_id={tenant_id}", headers=auth_header)
    assert resp.status_code == 200
    data = resp.json()
    assert data["license"] is None
    assert data["capabilities"] == ["usage_export", "usage_import"]
