import pathlib
import sys
from uuid import uuid4
import os

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from backend import database
from backend.models import ServiceAccount

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


def test_health() -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_create_and_get_assistant(auth_header: dict[str, str]) -> None:
    tenant_id = uuid4()
    payload = {
        "tenant_id": str(tenant_id),
        "name": "Test",
        "channel": "voice",
        "voice": "en-US",
        "language": "en",
        "prompt": "hi",
    }
    create = client.post("/internal/assistants", json=payload, headers=auth_header)
    assert create.status_code == 200
    data = create.json()
    assert data["name"] == "Test"
    aid = data["id"]

    get_resp = client.get(f"/internal/assistants/{aid}", headers=auth_header)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == aid


def test_activate_license(auth_header: dict[str, str]) -> None:
    tenant_id = uuid4()
    payload = {
        "tenant_id": str(tenant_id),
        "mode": "saas",
        "expires_at": "2030-01-01T00:00:00Z",
    }
    resp = client.post("/internal/licenses/activate", json=payload, headers=auth_header)
    assert resp.status_code == 200
    data = resp.json()
    assert data["tenant_id"] == str(tenant_id)

    status = client.get(f"/internal/licenses/status/{tenant_id}", headers=auth_header)
    assert status.status_code == 200
    assert status.json()["mode"] == "saas"


def test_agent_limit_enforced(auth_header: dict[str, str]) -> None:
    tenant_id = uuid4()
    activate = {
        "tenant_id": str(tenant_id),
        "mode": "saas",
        "expires_at": "2030-01-01T00:00:00Z",
        "max_agents": 1,
    }
    client.post("/internal/licenses/activate", json=activate, headers=auth_header)
    payload = {
        "tenant_id": str(tenant_id),
        "name": "A",
        "channel": "voice",
        "voice": "en-US",
        "language": "en",
        "prompt": "hi",
    }
    assert client.post("/internal/assistants", json=payload, headers=auth_header).status_code == 200
    resp = client.post("/internal/assistants", json=payload, headers=auth_header)
    assert resp.status_code == 403


def test_license_verify_endpoint(auth_header: dict[str, str]) -> None:
    tenant_id = uuid4()
    activate = {
        "tenant_id": str(tenant_id),
        "mode": "saas",
        "expires_at": "2030-01-01T00:00:00Z",
        "max_agents": 1,
        "max_minutes": 3.0,
    }
    client.post("/internal/licenses/activate", json=activate, headers=auth_header)
    payload = {
        "tenant_id": str(tenant_id),
        "name": "A",
        "channel": "voice",
        "voice": "en-US",
        "language": "en",
        "prompt": "hi",
    }
    client.post("/internal/assistants", json=payload, headers=auth_header)
    verify = {
        "tenant_id": str(tenant_id),
        "agents": 1,
    }
    resp = client.post("/internal/licenses/verify", json=verify, headers=auth_header)
    assert resp.status_code == 200
    assert not resp.json()["allowed"]
    check_minutes = {
        "tenant_id": str(tenant_id),
        "minutes": 2.0,
    }
    ok = client.post("/internal/licenses/verify", json=check_minutes, headers=auth_header)
    assert ok.json()["allowed"] is True
    too_many = {
        "tenant_id": str(tenant_id),
        "minutes": 5.0,
    }
    fail = client.post("/internal/licenses/verify", json=too_many, headers=auth_header)
    assert fail.json()["allowed"] is False


def test_invalid_token() -> None:
    tenant_id = uuid4()
    payload = {
        "tenant_id": str(tenant_id),
        "name": "X",
        "channel": "voice",
        "voice": "en-US",
        "language": "en",
        "prompt": "hi",
    }
    resp = client.post(
        "/internal/assistants", json=payload, headers={"X-Service-Token": "bad"}
    )
    assert resp.status_code == 401


def test_create_service_account(auth_header: dict[str, str]) -> None:
    payload = {"name": "new", "scopes": ["dev"]}
    resp = client.post("/internal/service-accounts", json=payload, headers=auth_header)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "new"
    assert "token" in data


def test_session_websocket(auth_header: dict[str, str]) -> None:
    sid = uuid4()
    with client.websocket_connect(
        f"/internal/sessions/{sid}", headers=auth_header
    ) as ws:
        ws.send_text("hello")
        assert ws.receive_text() == "HELLO"


def test_session_guardrail(auth_header: dict[str, str]) -> None:
    sid = uuid4()
    with client.websocket_connect(
        f"/internal/sessions/{sid}", headers=auth_header
    ) as ws:
        ws.send_text("bad")
        assert ws.receive_text() == "guardrail triggered"
        with pytest.raises(WebSocketDisconnect):
            ws.receive_text()


def test_session_grounding(auth_header: dict[str, str]) -> None:
    tenant_id = uuid4()
    client.post(
        "/internal/kb",
        json={"tenant_id": str(tenant_id), "content": "The sky is blue"},
        headers=auth_header,
    )
    sid = uuid4()
    with client.websocket_connect(
        f"/internal/sessions/{sid}?tenant_id={tenant_id}", headers=auth_header
    ) as ws:
        ws.send_text("sky")
        assert "blue" in ws.receive_text().lower()
        ws.send_text("unknown")
        assert "clarify" in ws.receive_text().lower()


def test_session_invalid_token() -> None:
    sid = uuid4()
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(f"/internal/sessions/{sid}"):
            pass


def test_session_handover(auth_header: dict[str, str]) -> None:
    sid = uuid4()
    with client.websocket_connect(
        f"/internal/sessions/{sid}", headers=auth_header
    ) as ws:
        ws.send_text("hello")
        ws.receive_text()

    resp = client.post(
        f"/internal/sessions/{sid}/handover",
        json={"target": "sip:agent@example.com"},
        headers=auth_header,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "transferring"

    status = client.get(f"/internal/sessions/{sid}", headers=auth_header)
    assert status.status_code == 200
    assert status.json()["handover_target"] == "sip:agent@example.com"


def test_handover_requires_auth() -> None:
    sid = uuid4()
    resp = client.post(
        f"/internal/sessions/{sid}/handover",
        json={"target": "sip:agent@example.com"},
        headers={"X-Service-Token": "bad"},
    )
    assert resp.status_code == 401


def test_handover_without_session(auth_header: dict[str, str]) -> None:
    sid = uuid4()
    resp = client.post(
        f"/internal/sessions/{sid}/handover",
        json={"target": "sip:agent@example.com"},
        headers=auth_header,
    )
    assert resp.status_code == 200
    status = client.get(f"/internal/sessions/{sid}", headers=auth_header)
    assert status.json()["handover_target"] == "sip:agent@example.com"
