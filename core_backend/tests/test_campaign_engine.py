import pathlib
import sys
import os
import time
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from backend import database
from backend.models import ServiceAccount

os.environ["CORE_DB_URL"] = "sqlite:///:memory:"
from backend.main import (
    app,
    campaign_runs,
    scheduler,
    dialer,
    _reset_campaign_state,
)
from backend.dialer import CallOutcome


@pytest.fixture(autouse=True)
def _setup_db() -> None:
    """Initialize database and reset scheduler state."""

    database.init_db()
    _reset_campaign_state()
    yield
    scheduler.remove_all_jobs()


@pytest.fixture()
def auth_header() -> dict[str, str]:
    token = "camp_token"
    session = database.get_session()
    account = ServiceAccount(name="svc", token=token, scopes=["admin"])
    session.add(account)
    session.commit()
    return {"X-Service-Token": token}


client = TestClient(app)


def test_campaign_scheduler_pacing(auth_header: dict[str, str]) -> None:
    payload = {
        "tenant_id": str(uuid4()),
        "name": "Test Campaign",
        "cron": "*/1 * * * * *",
        "pacing_per_minute": 1,
    }
    resp = client.post("/internal/campaigns", json=payload, headers=auth_header)
    assert resp.status_code == 200
    cid = UUID(resp.json()["id"])

    time.sleep(1.2)
    assert campaign_runs[cid] == 1
    time.sleep(1.2)
    assert campaign_runs[cid] == 1


def test_campaign_retry_success(auth_header: dict[str, str]) -> None:
    payload = {
        "tenant_id": str(uuid4()),
        "name": "Retry Campaign",
        "cron": "*/1 * * * * *",
        "pacing_per_minute": 10,
        "max_attempts": 3,
        "backoff_minutes": 0,
    }
    resp = client.post("/internal/campaigns", json=payload, headers=auth_header)
    assert resp.status_code == 200
    cid = UUID(resp.json()["id"])
    dialer.set_outcomes(cid, [CallOutcome.BUSY, CallOutcome.ANSWERED])

    time.sleep(1.2)
    assert campaign_runs[cid] == 2
    time.sleep(1.2)
    assert campaign_runs[cid] == 2


def test_campaign_retry_exhausts_attempts(auth_header: dict[str, str]) -> None:
    payload = {
        "tenant_id": str(uuid4()),
        "name": "Fail Campaign",
        "cron": "*/1 * * * * *",
        "pacing_per_minute": 10,
        "max_attempts": 2,
        "backoff_minutes": 0,
    }
    resp = client.post("/internal/campaigns", json=payload, headers=auth_header)
    assert resp.status_code == 200
    cid = UUID(resp.json()["id"])
    dialer.set_outcomes(cid, [CallOutcome.BUSY, CallOutcome.BUSY])

    time.sleep(1.2)
    assert campaign_runs[cid] == 2
    time.sleep(1.2)
    assert campaign_runs[cid] == 2
