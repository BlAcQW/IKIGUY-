import pytest
from uuid import uuid4
from fastapi.testclient import TestClient

from ..backend.main import app
from ..backend.models import Webhook

client = TestClient(app)


def test_create_webhook():
    """Test creating a webhook."""
    webhook_data = {
        "tenant_id": str(uuid4()),
        "url": "https://example.com/webhook",
        "events": ["call.started", "call.ended"]
    }
    
    response = client.post("/webhooks", json=webhook_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["url"] == webhook_data["url"]
    assert data["events"] == webhook_data["events"]
    assert data["enabled"] is True
    assert "secret" in data


def test_list_webhooks():
    """Test listing webhooks."""
    response = client.get("/webhooks")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_webhook():
    """Test getting a specific webhook."""
    # First create a webhook
    webhook_data = {
        "tenant_id": str(uuid4()),
        "url": "https://example.com/webhook",
        "events": ["call.started"]
    }
    
    create_response = client.post("/webhooks", json=webhook_data)
    webhook_id = create_response.json()["id"]
    
    # Then get it
    response = client.get(f"/webhooks/{webhook_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == webhook_id
    assert data["url"] == webhook_data["url"]


def test_delete_webhook():
    """Test deleting a webhook."""
    # First create a webhook
    webhook_data = {
        "tenant_id": str(uuid4()),
        "url": "https://example.com/webhook",
        "events": ["call.started"]
    }
    
    create_response = client.post("/webhooks", json=webhook_data)
    webhook_id = create_response.json()["id"]
    
    # Then delete it
    response = client.delete(f"/webhooks/{webhook_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"
    
    # Verify it's gone
    get_response = client.get(f"/webhooks/{webhook_id}")
    assert get_response.status_code == 404


def test_get_nonexistent_webhook():
    """Test getting a webhook that doesn't exist."""
    response = client.get(f"/webhooks/{uuid4()}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Webhook not found"


def test_delete_nonexistent_webhook():
    """Test deleting a webhook that doesn't exist."""
    response = client.delete(f"/webhooks/{uuid4()}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Webhook not found" 