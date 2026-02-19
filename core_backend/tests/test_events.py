import pathlib
import sys
from uuid import uuid4

import pytest
import mongomock
from fastapi.testclient import TestClient

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from backend.events import event_bus, EventType, webhook_queue
from backend.main import app
from backend.models import ServiceAccount
from backend.sessions import SessionManager
from backend.services import (
    service_account_service,
    event_record_service,
)


@pytest.fixture(autouse=True)
def _setup() -> None:
    service_account_service._collection = mongomock.MongoClient().db.service_accounts
    event_record_service._collection = mongomock.MongoClient().db.events
    event_bus.clear()
    webhook_queue.drain()
    yield


@pytest.fixture()
def auth_header() -> dict[str, str]:
    token = "testtoken"
    service_account_service.create_account(
        ServiceAccount(id=uuid4(), name="tester", token=token, scopes=["admin"])
    )
    return {"X-Service-Token": token}


client = TestClient(app)


def test_session_events() -> None:
    manager = SessionManager()
    sid = uuid4()
    manager.start_session(sid)
    manager.add_turn(sid, "user", "hi")
    manager.end_session(sid)
    types = [e.type for e in event_bus.list()]
    assert types == [
        EventType.CALL_STARTED,
        EventType.CALL_TURN,
        EventType.CALL_ENDED,
    ]




def test_event_etl_persists(auth_header: dict[str, str]) -> None:
    event_bus.emit(EventType.CALL_STARTED, session_id="1")
    resp = client.post("/internal/events/etl", headers=auth_header)
    assert resp.status_code == 200
    assert resp.json()["persisted"] == 1
    records = list(event_record_service._collection.find())
    assert len(records) == 1
    assert records[0]["payload"]["session_id"] == "1"
    assert not event_bus.list()


def test_webhook_queue(auth_header: dict[str, str]) -> None:
    event_bus.emit(EventType.CALL_STARTED, session_id="abc")
    resp = client.get("/internal/events/webhooks", headers=auth_header)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["payload"]["session_id"] == "abc"
    resp = client.get("/internal/events/webhooks", headers=auth_header)
    assert resp.status_code == 200
    assert resp.json() == []
