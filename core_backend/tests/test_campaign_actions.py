import os
import pathlib
import sys
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

os.environ["CORE_DB_URL"] = "sqlite:///:memory:"

from backend import database
from backend.models import Campaign, ServiceAccount
from backend.main import app  # noqa: E402


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


def _create_campaign(tenant_id: str, auth_header: dict[str, str]) -> Campaign:
    payload = {
        "tenant_id": tenant_id,
        "name": "Test Campaign",
        "cron": "* * * * *",
        "pacing_per_minute": 1,
    }
    resp = client.post("/internal/campaigns", json=payload, headers=auth_header)
    assert resp.status_code == 200
    return Campaign(**resp.json())


def test_start_campaign(auth_header: dict[str, str]) -> None:
    tenant_id = str(uuid4())
    campaign = _create_campaign(tenant_id, auth_header)

    resp = client.post(f"/internal/campaigns/{campaign.id}/start", headers=auth_header)
    assert resp.status_code == 200
    assert resp.json()["status"] == "running"


def test_resume_paused_campaign(auth_header: dict[str, str]) -> None:
    tenant_id = str(uuid4())
    campaign = _create_campaign(tenant_id, auth_header)

    client.post(f"/internal/campaigns/{campaign.id}/pause", headers=auth_header)
    resp = client.post(f"/internal/campaigns/{campaign.id}/resume", headers=auth_header)
    assert resp.status_code == 200
    assert resp.json()["status"] == "running"


def test_stop_missing_campaign(auth_header: dict[str, str]) -> None:
    resp = client.post(f"/internal/campaigns/{uuid4()}/stop", headers=auth_header)
    assert resp.status_code == 404
