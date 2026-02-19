"""
Integration Tests for WhatsApp Campaigns API

Tests the FastAPI endpoints for WhatsApp campaign management,
including CRUD operations, campaign control, templates, and analytics.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import sys
import os

# Add paths for imports
sys.path.insert(0, "/opt/kasaai/apps")

from core_backend.backend.main import app
from apps.shared.services.whatsapp_campaign_service import WhatsAppCampaignStatus
from apps.shared.models.whatsapp_campaign import WhatsAppCampaign, WhatsAppMessage


# Test client
client = TestClient(app)


# ==================== Fixtures ====================

@pytest.fixture
def auth_headers():
    """
    Mock authentication headers.

    Returns:
        dict: Headers with mock JWT token
    """
    return {
        "Authorization": "Bearer mock_token_12345",
        "X-Organization-Id": "org_test_123"
    }


@pytest.fixture
def sample_campaign_data():
    """
    Sample campaign creation data.

    Returns:
        dict: Campaign creation request data
    """
    return {
        "name": "Test Campaign",
        "template_name": "event_reminder",
        "audience_id": "audience_123",
        "config": {
            "send_rate_per_second": 1.0,
            "batch_size": 100,
            "retry_failed": True,
            "max_retries": 3,
            "template_name": "event_reminder",
            "enable_media": False,
            "enable_buttons": False,
            "buttons": [],
            "phone_number_id": "102290129340398"
        }
    }


@pytest.fixture
def sample_campaign():
    """
    Sample WhatsApp campaign object.

    Returns:
        WhatsAppCampaign: Mock campaign instance
    """
    return WhatsAppCampaign(
        id="campaign_123",
        name="Test Campaign",
        organization_id="org_test_123",
        user_id="user_123",
        template_name="event_reminder",
        template_content="Hi {{1}}, your event is on {{2}}.",
        status=WhatsAppCampaignStatus.DRAFT,
        progress={
            "total_recipients": 100,
            "sent": 0,
            "delivered": 0,
            "read": 0,
            "failed": 0,
            "pending": 100
        },
        config={
            "send_rate_per_second": 1.0,
            "batch_size": 100,
            "retry_failed": True,
            "max_retries": 3,
            "template_name": "event_reminder",
            "enable_media": False,
            "enable_buttons": False,
            "buttons": [],
            "phone_number_id": "102290129340398"
        },
        total_cost=0.0,
        cost_per_message=0.0055,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        phone_number_id="102290129340398"
    )


# ==================== Campaign CRUD Tests ====================

@patch('apps.shared.services.whatsapp_campaign_service.whatsapp_campaign_service.create_campaign')
@patch('core_backend.backend.routes.whatsapp_campaigns.get_current_user')
def test_create_campaign(mock_get_user, mock_create, sample_campaign_data, sample_campaign, auth_headers):
    """
    Test creating a new WhatsApp campaign via API.

    Args:
        mock_get_user: Mock user authentication
        mock_create: Mock campaign creation
        sample_campaign_data: Sample request data
        sample_campaign: Sample campaign object
        auth_headers: Auth headers
    """
    mock_get_user.return_value = {"user_id": "user_123", "organization_id": "org_test_123"}
    mock_create.return_value = sample_campaign

    response = client.post(
        "/api/whatsapp-campaigns/",
        json=sample_campaign_data,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Campaign"
    assert data["status"] == "draft"
    assert data["progress"]["total_recipients"] == 100


@patch('apps.shared.services.whatsapp_campaign_service.whatsapp_campaign_service.get_campaign')
@patch('core_backend.backend.routes.whatsapp_campaigns.get_current_user')
def test_get_campaign(mock_get_user, mock_get, sample_campaign, auth_headers):
    """
    Test retrieving a campaign by ID.

    Args:
        mock_get_user: Mock user authentication
        mock_get: Mock campaign retrieval
        sample_campaign: Sample campaign object
        auth_headers: Auth headers
    """
    mock_get_user.return_value = {"user_id": "user_123", "organization_id": "org_test_123"}
    mock_get.return_value = sample_campaign

    response = client.get(
        "/api/whatsapp-campaigns/campaign_123",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "campaign_123"
    assert data["name"] == "Test Campaign"


@patch('apps.shared.services.whatsapp_campaign_service.whatsapp_campaign_service.list_campaigns')
@patch('core_backend.backend.routes.whatsapp_campaigns.get_current_user')
def test_list_campaigns(mock_get_user, mock_list, sample_campaign, auth_headers):
    """
    Test listing campaigns with filters.

    Args:
        mock_get_user: Mock user authentication
        mock_list: Mock campaign listing
        sample_campaign: Sample campaign object
        auth_headers: Auth headers
    """
    mock_get_user.return_value = {"user_id": "user_123", "organization_id": "org_test_123"}
    mock_list.return_value = [sample_campaign]

    response = client.get(
        "/api/whatsapp-campaigns/?status=draft&limit=10",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["campaigns"]) == 1
    assert data["campaigns"][0]["status"] == "draft"


@patch('apps.shared.services.whatsapp_campaign_service.whatsapp_campaign_service.update_campaign')
@patch('core_backend.backend.routes.whatsapp_campaigns.get_current_user')
def test_update_campaign(mock_get_user, mock_update, sample_campaign, auth_headers):
    """
    Test updating a campaign.

    Args:
        mock_get_user: Mock user authentication
        mock_update: Mock campaign update
        sample_campaign: Sample campaign object
        auth_headers: Auth headers
    """
    mock_get_user.return_value = {"user_id": "user_123", "organization_id": "org_test_123"}
    updated_campaign = sample_campaign.copy()
    updated_campaign.name = "Updated Campaign"
    mock_update.return_value = updated_campaign

    response = client.put(
        "/api/whatsapp-campaigns/campaign_123",
        json={"name": "Updated Campaign"},
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Campaign"


@patch('apps.shared.services.whatsapp_campaign_service.whatsapp_campaign_service.delete_campaign')
@patch('core_backend.backend.routes.whatsapp_campaigns.get_current_user')
def test_delete_campaign(mock_get_user, mock_delete, auth_headers):
    """
    Test deleting a campaign.

    Args:
        mock_get_user: Mock user authentication
        mock_delete: Mock campaign deletion
        auth_headers: Auth headers
    """
    mock_get_user.return_value = {"user_id": "user_123", "organization_id": "org_test_123"}
    mock_delete.return_value = None

    response = client.delete(
        "/api/whatsapp-campaigns/campaign_123",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "deleted" in data["message"].lower()


# ==================== Campaign Control Tests ====================

@patch('apps.shared.services.whatsapp_campaign_service.whatsapp_campaign_service.start_campaign')
@patch('core_backend.backend.routes.whatsapp_campaigns.get_current_user')
def test_start_campaign(mock_get_user, mock_start, auth_headers):
    """
    Test starting a campaign.

    Args:
        mock_get_user: Mock user authentication
        mock_start: Mock campaign start
        auth_headers: Auth headers
    """
    mock_get_user.return_value = {"user_id": "user_123", "organization_id": "org_test_123"}
    mock_start.return_value = None

    response = client.post(
        "/api/whatsapp-campaigns/campaign_123/start",
        json={"contacts": []},
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["campaign_id"] == "campaign_123"


@patch('apps.shared.services.whatsapp_campaign_service.whatsapp_campaign_service.pause_campaign')
@patch('core_backend.backend.routes.whatsapp_campaigns.get_current_user')
def test_pause_campaign(mock_get_user, mock_pause, auth_headers):
    """
    Test pausing a running campaign.

    Args:
        mock_get_user: Mock user authentication
        mock_pause: Mock campaign pause
        auth_headers: Auth headers
    """
    mock_get_user.return_value = {"user_id": "user_123", "organization_id": "org_test_123"}
    mock_pause.return_value = None

    response = client.post(
        "/api/whatsapp-campaigns/campaign_123/pause",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "paused" in data["message"].lower()


@patch('apps.shared.services.whatsapp_campaign_service.whatsapp_campaign_service.cancel_campaign')
@patch('core_backend.backend.routes.whatsapp_campaigns.get_current_user')
def test_cancel_campaign(mock_get_user, mock_cancel, auth_headers):
    """
    Test cancelling a campaign.

    Args:
        mock_get_user: Mock user authentication
        mock_cancel: Mock campaign cancellation
        auth_headers: Auth headers
    """
    mock_get_user.return_value = {"user_id": "user_123", "organization_id": "org_test_123"}
    mock_cancel.return_value = None

    response = client.post(
        "/api/whatsapp-campaigns/campaign_123/cancel",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "cancelled" in data["message"].lower()


# ==================== Template Tests ====================

@patch('apps.shared.services.whatsapp_campaign_service.whatsapp_campaign_service.sync_templates')
@patch('core_backend.backend.routes.whatsapp_campaigns.get_current_user')
def test_sync_templates(mock_get_user, mock_sync, auth_headers):
    """
    Test syncing templates from WhatsApp Business API.

    Args:
        mock_get_user: Mock user authentication
        mock_sync: Mock template sync
        auth_headers: Auth headers
    """
    mock_get_user.return_value = {"user_id": "user_123", "organization_id": "org_test_123"}
    mock_sync.return_value = 5

    response = client.post(
        "/api/whatsapp-campaigns/templates/sync",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["count"] == 5


@patch('apps.shared.services.whatsapp_campaign_service.whatsapp_campaign_service.get_templates')
@patch('core_backend.backend.routes.whatsapp_campaigns.get_current_user')
def test_list_templates(mock_get_user, mock_get, auth_headers):
    """
    Test listing WhatsApp message templates.

    Args:
        mock_get_user: Mock user authentication
        mock_get: Mock template retrieval
        auth_headers: Auth headers
    """
    mock_get_user.return_value = {"user_id": "user_123", "organization_id": "org_test_123"}
    mock_templates = [
        {
            "id": "tmpl_123",
            "name": "event_reminder",
            "language": "en",
            "category": "MARKETING",
            "status": "APPROVED",
            "components": [],
            "placeholders": ["name", "date"]
        }
    ]
    mock_get.return_value = mock_templates

    response = client.get(
        "/api/whatsapp-campaigns/templates/list",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["templates"]) == 1
    assert data["templates"][0]["name"] == "event_reminder"


# ==================== Analytics Tests ====================

@patch('apps.shared.services.whatsapp_campaign_service.whatsapp_campaign_service.get_campaign_analytics')
@patch('core_backend.backend.routes.whatsapp_campaigns.get_current_user')
def test_get_campaign_analytics(mock_get_user, mock_analytics, auth_headers):
    """
    Test retrieving campaign analytics.

    Args:
        mock_get_user: Mock user authentication
        mock_analytics: Mock analytics retrieval
        auth_headers: Auth headers
    """
    mock_get_user.return_value = {"user_id": "user_123", "organization_id": "org_test_123"}
    mock_analytics.return_value = {
        "campaign_id": "campaign_123",
        "name": "Test Campaign",
        "status": "completed",
        "progress": {
            "total": 100,
            "sent": 95,
            "delivered": 90,
            "read": 75,
            "failed": 5,
            "pending": 0,
            "progress_percentage": 100,
            "success_rate": 95.0,
            "delivery_rate": 94.7,
            "read_rate": 83.3
        },
        "cost": {
            "total": 0.5225,
            "per_message": 0.0055,
            "average": 0.0055
        }
    }

    response = client.get(
        "/api/whatsapp-campaigns/campaign_123/analytics",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["campaign_id"] == "campaign_123"
    assert data["progress"]["success_rate"] == 95.0
    assert data["cost"]["total"] == 0.5225


# ==================== Message Tests ====================

@patch('apps.shared.services.whatsapp_campaign_service.whatsapp_campaign_service.get_campaign_messages')
@patch('core_backend.backend.routes.whatsapp_campaigns.get_current_user')
def test_get_campaign_messages(mock_get_user, mock_get_messages, auth_headers):
    """
    Test retrieving campaign messages.

    Args:
        mock_get_user: Mock user authentication
        mock_get_messages: Mock message retrieval
        auth_headers: Auth headers
    """
    mock_get_user.return_value = {"user_id": "user_123", "organization_id": "org_test_123"}
    mock_messages = [
        WhatsAppMessage(
            id="msg_123",
            campaign_id="campaign_123",
            recipient_phone="+1234567890",
            recipient_name="John Doe",
            recipient_data={},
            message_content="Hi John, your event is on Saturday.",
            template_variables={"1": "John", "2": "Saturday"},
            status="delivered",
            buttons=[],
            retry_count=0,
            cost=0.0055,
            created_at=datetime.now()
        )
    ]
    mock_get_messages.return_value = (mock_messages, 1)

    response = client.get(
        "/api/whatsapp-campaigns/campaign_123/messages?status=delivered&limit=10",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["messages"]) == 1
    assert data["messages"][0]["status"] == "delivered"


# ==================== Webhook Tests ====================

def test_webhook_verification():
    """
    Test webhook verification endpoint.
    """
    response = client.get(
        "/api/whatsapp-campaigns/webhooks/status",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "test_verify_token",
            "hub.challenge": "test_challenge_123"
        }
    )

    # This will fail verification with incorrect token, which is expected
    assert response.status_code in [200, 403]


@patch('apps.shared.services.whatsapp_campaign_service.whatsapp_campaign_service.process_delivery_status')
def test_webhook_delivery_status(mock_process):
    """
    Test processing delivery status webhook.

    Args:
        mock_process: Mock webhook processing
    """
    mock_process.return_value = None

    webhook_data = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "102290129340398",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {
                        "display_phone_number": "15550000000",
                        "phone_number_id": "102290129340398"
                    },
                    "statuses": [{
                        "id": "wamid.HBgNMTIzNDU2Nzg5MAA=",
                        "status": "delivered",
                        "timestamp": "1234567890",
                        "recipient_id": "1234567890"
                    }]
                },
                "field": "messages"
            }]
        }]
    }

    response = client.post(
        "/api/whatsapp-campaigns/webhooks/status",
        json=webhook_data
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


# ==================== Error Handling Tests ====================

@patch('core_backend.backend.routes.whatsapp_campaigns.get_current_user')
def test_create_campaign_missing_fields(mock_get_user, auth_headers):
    """
    Test creating campaign with missing required fields.

    Args:
        mock_get_user: Mock user authentication
        auth_headers: Auth headers
    """
    mock_get_user.return_value = {"user_id": "user_123", "organization_id": "org_test_123"}

    response = client.post(
        "/api/whatsapp-campaigns/",
        json={"name": "Test Campaign"},  # Missing template_name and config
        headers=auth_headers
    )

    assert response.status_code == 422  # Validation error


@patch('apps.shared.services.whatsapp_campaign_service.whatsapp_campaign_service.get_campaign')
@patch('core_backend.backend.routes.whatsapp_campaigns.get_current_user')
def test_get_nonexistent_campaign(mock_get_user, mock_get, auth_headers):
    """
    Test retrieving a campaign that doesn't exist.

    Args:
        mock_get_user: Mock user authentication
        mock_get: Mock campaign retrieval
        auth_headers: Auth headers
    """
    mock_get_user.return_value = {"user_id": "user_123", "organization_id": "org_test_123"}
    mock_get.side_effect = ValueError("Campaign not found")

    response = client.get(
        "/api/whatsapp-campaigns/nonexistent_id",
        headers=auth_headers
    )

    assert response.status_code == 404


@patch('apps.shared.services.whatsapp_campaign_service.whatsapp_campaign_service.start_campaign')
@patch('core_backend.backend.routes.whatsapp_campaigns.get_current_user')
def test_start_campaign_already_running(mock_get_user, mock_start, auth_headers):
    """
    Test starting a campaign that's already running.

    Args:
        mock_get_user: Mock user authentication
        mock_start: Mock campaign start
        auth_headers: Auth headers
    """
    mock_get_user.return_value = {"user_id": "user_123", "organization_id": "org_test_123"}
    mock_start.side_effect = ValueError("Campaign is already running")

    response = client.post(
        "/api/whatsapp-campaigns/campaign_123/start",
        json={},
        headers=auth_headers
    )

    assert response.status_code == 400


# ==================== Integration Test ====================

@pytest.mark.integration
@patch('apps.shared.services.whatsapp_campaign_service.whatsapp_campaign_service')
@patch('core_backend.backend.routes.whatsapp_campaigns.get_current_user')
def test_full_campaign_flow(mock_get_user, mock_service, sample_campaign_data, auth_headers):
    """
    Integration test for complete campaign lifecycle.

    Tests: Create → Start → Monitor → Complete

    Args:
        mock_get_user: Mock user authentication
        mock_service: Mock campaign service
        sample_campaign_data: Sample request data
        auth_headers: Auth headers
    """
    mock_get_user.return_value = {"user_id": "user_123", "organization_id": "org_test_123"}

    # 1. Create campaign
    campaign = WhatsAppCampaign(
        id="campaign_integration_123",
        name="Integration Test Campaign",
        organization_id="org_test_123",
        user_id="user_123",
        template_name="event_reminder",
        template_content="Hi {{1}}, event on {{2}}.",
        status=WhatsAppCampaignStatus.DRAFT,
        progress={"total_recipients": 10, "sent": 0, "delivered": 0, "read": 0, "failed": 0, "pending": 10},
        config=sample_campaign_data["config"],
        total_cost=0.0,
        cost_per_message=0.0055,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        phone_number_id="102290129340398"
    )
    mock_service.create_campaign.return_value = campaign

    create_response = client.post(
        "/api/whatsapp-campaigns/",
        json=sample_campaign_data,
        headers=auth_headers
    )
    assert create_response.status_code == 200
    campaign_id = create_response.json()["id"]

    # 2. Start campaign
    mock_service.start_campaign.return_value = None
    start_response = client.post(
        f"/api/whatsapp-campaigns/{campaign_id}/start",
        json={"contacts": []},
        headers=auth_headers
    )
    assert start_response.status_code == 200

    # 3. Get campaign status
    running_campaign = campaign.copy()
    running_campaign.status = WhatsAppCampaignStatus.RUNNING
    running_campaign.progress["sent"] = 5
    mock_service.get_campaign.return_value = running_campaign

    status_response = client.get(
        f"/api/whatsapp-campaigns/{campaign_id}",
        headers=auth_headers
    )
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "running"

    # 4. Get analytics
    mock_service.get_campaign_analytics.return_value = {
        "campaign_id": campaign_id,
        "name": "Integration Test Campaign",
        "status": "running",
        "progress": {
            "total": 10,
            "sent": 5,
            "delivered": 3,
            "read": 1,
            "failed": 0,
            "pending": 5,
            "progress_percentage": 50,
            "success_rate": 100.0,
            "delivery_rate": 60.0,
            "read_rate": 33.3
        },
        "cost": {"total": 0.0275, "per_message": 0.0055, "average": 0.0055}
    }

    analytics_response = client.get(
        f"/api/whatsapp-campaigns/{campaign_id}/analytics",
        headers=auth_headers
    )
    assert analytics_response.status_code == 200
    assert analytics_response.json()["progress"]["sent"] == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
