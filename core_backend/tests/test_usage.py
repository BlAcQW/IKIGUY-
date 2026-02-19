import pathlib
import sys
from uuid import uuid4
import os
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from backend import database
from backend.models import ServiceAccount, Usage

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


def test_report_and_get_usage(auth_header: dict[str, str]) -> None:
    tenant_id = uuid4()
    payload = {
        "tenant_id": str(tenant_id),
        "minutes": 1.5,
        "messages": 3,
        "stt_calls": 3,
        "tts_calls": 3,
        "telephony_provider": "twilio",
        "telephony_cost": 0.5,
        "stt_provider": "openai",
        "stt_cost": 0.1,
        "tts_provider": "aws",
        "tts_cost": 0.2,
    }
    resp = client.post("/internal/usage", json=payload, headers=auth_header)
    assert resp.status_code == 200
    get_resp = client.get(f"/internal/usage?tenant_id={tenant_id}", headers=auth_header)
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["minutes"] == pytest.approx(1.5)
    assert data["messages"] == 3
    assert data["telephony_cost"] == pytest.approx(0.5)
    assert data["stt_cost"] == pytest.approx(0.1)
    assert data["tts_cost"] == pytest.approx(0.2)


def test_get_usage_without_records(auth_header: dict[str, str]) -> None:
    tenant_id = uuid4()
    resp = client.get(f"/internal/usage?tenant_id={tenant_id}", headers=auth_header)
    assert resp.status_code == 200
    assert resp.json() == {
        "minutes": 0.0,
        "messages": 0,
        "stt_calls": 0,
        "tts_calls": 0,
        "telephony_cost": 0.0,
        "stt_cost": 0.0,
        "tts_cost": 0.0,
    }


def test_session_records_usage(auth_header: dict[str, str]) -> None:
    tenant_id = uuid4()
    sid = uuid4()
    with client.websocket_connect(
        f"/internal/sessions/{sid}?tenant_id={tenant_id}", headers=auth_header
    ) as ws:
        ws.send_text("hello")
        ws.receive_text()
    resp = client.get(f"/internal/usage?tenant_id={tenant_id}", headers=auth_header)
    data = resp.json()
    assert data["messages"] == 2
    assert data["stt_calls"] == 1
    assert data["tts_calls"] == 1


def test_usage_rollup_and_invoice(auth_header: dict[str, str]) -> None:
    tenant_id = uuid4()
    day = datetime.utcnow().date()
    session = database.get_session()
    session.add(
        Usage(
            tenant_id=tenant_id,
            minutes=1,
            messages=2,
            telephony_cost=0.1,
            created_at=datetime.combine(day, datetime.min.time()),
        )
    )
    session.add(
        Usage(
            tenant_id=tenant_id,
            minutes=2,
            messages=3,
            telephony_cost=0.2,
            created_at=datetime.combine(day, datetime.min.time()) + timedelta(hours=1),
        )
    )
    session.commit()
    resp = client.post(
        f"/internal/usage/rollup?day={day.isoformat()}", headers=auth_header
    )
    assert resp.status_code == 200
    invoice = client.get(
        f"/internal/usage/invoice?tenant_id={tenant_id}&start_date={day.isoformat()}&end_date={day.isoformat()}",
        headers=auth_header,
    )
    assert invoice.status_code == 200
    data = invoice.json()
    assert len(data) == 1
    assert data[0]["minutes"] == pytest.approx(3.0)
    assert data[0]["messages"] == 5
    assert data[0]["telephony_cost"] == pytest.approx(0.3)


def test_cost_breakdown(auth_header: dict[str, str]) -> None:
    tenant_id = uuid4()
    records = [
        {
            "tenant_id": str(tenant_id),
            "telephony_provider": "twilio",
            "telephony_cost": 0.5,
        },
        {
            "tenant_id": str(tenant_id),
            "telephony_provider": "twilio",
            "telephony_cost": 0.2,
            "stt_provider": "openai",
            "stt_cost": 0.1,
        },
        {
            "tenant_id": str(tenant_id),
            "tts_provider": "aws",
            "tts_cost": 0.3,
        },
    ]
    for rec in records:
        assert (
            client.post("/internal/usage", json=rec, headers=auth_header).status_code
            == 200
        )
    resp = client.get(
        f"/internal/usage/costs?tenant_id={tenant_id}", headers=auth_header
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["telephony"]["twilio"] == pytest.approx(0.7)
    assert data["stt"]["openai"] == pytest.approx(0.1)
    assert data["tts"]["aws"] == pytest.approx(0.3)


def test_usage_export_import(auth_header: dict[str, str]) -> None:
    tenant_id = uuid4()
    record = {"tenant_id": str(tenant_id), "minutes": 1.0}
    assert (
        client.post("/internal/usage", json=record, headers=auth_header).status_code
        == 200
    )
    export_resp = client.get(
        f"/internal/usage/export?tenant_id={tenant_id}", headers=auth_header
    )
    assert export_resp.status_code == 200
    exported = export_resp.json()
    assert len(exported) == 1

    new_tenant = uuid4()
    exported[0]["tenant_id"] = str(new_tenant)
    exported[0].pop("id")
    import_resp = client.post(
        "/internal/usage/import", json=exported, headers=auth_header
    )
    assert import_resp.status_code == 200
    usage_resp = client.get(
        f"/internal/usage?tenant_id={new_tenant}", headers=auth_header
    )
    assert usage_resp.status_code == 200
    assert usage_resp.json()["minutes"] == pytest.approx(1.0)
