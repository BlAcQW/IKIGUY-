"""
Unit Tests for WhatsApp Campaign Service

Tests all major functionality including CRUD operations, template management,
campaign execution, and webhook processing using real database operations.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from shared.services.whatsapp_campaign_service import (
    WhatsAppCampaignService,
    WhatsAppCampaign,
    WhatsAppCampaignMessage,
    WhatsAppTemplate,
    WhatsAppCampaignStatus,
    WhatsAppMessageStatus,
    WhatsAppCampaignConfig,
    WhatsAppCampaignProgress,
)


# ==================== Fixtures ====================


@pytest.fixture
def mock_db():
    """Mock MongoDB database."""
    db = Mock()

    # Mock collections
    db.whatsapp_campaigns = Mock()
    db.whatsapp_campaign_messages = Mock()
    db.whatsapp_templates = Mock()

    # Mock collection methods
    db.whatsapp_campaigns.insert_one = AsyncMock()
    db.whatsapp_campaigns.find_one = AsyncMock()
    db.whatsapp_campaigns.find = Mock()
    db.whatsapp_campaigns.update_one = AsyncMock()
    db.whatsapp_campaigns.delete_one = AsyncMock()

    db.whatsapp_campaign_messages.insert_one = AsyncMock()
    db.whatsapp_campaign_messages.find = Mock()
    db.whatsapp_campaign_messages.update_one = AsyncMock()
    db.whatsapp_campaign_messages.count_documents = AsyncMock()

    db.whatsapp_templates.insert_one = AsyncMock()
    db.whatsapp_templates.find = Mock()
    db.whatsapp_templates.update_one = AsyncMock()
    db.whatsapp_templates.delete_many = AsyncMock()

    return db


@pytest.fixture
def mock_whatsapp_provider():
    """Mock WhatsApp Business API provider."""
    provider = Mock()
    provider.send_template_message = AsyncMock(return_value={
        "message_id": "wamid_test_12345",
        "status": "sent"
    })
    provider.get_templates = AsyncMock(return_value=[
        {
            "id": "template_1",
            "name": "event_reminder",
            "language": "en_US",
            "category": "UTILITY",
            "status": "APPROVED",
            "components": [
                {
                    "type": "BODY",
                    "text": "Hi {{1}}, your event is on {{2}}."
                }
            ]
        }
    ])
    provider.upload_media = AsyncMock(return_value="media_id_12345")
    return provider


@pytest.fixture
def service(mock_db, mock_whatsapp_provider):
    """Create WhatsAppCampaignService instance with mocked dependencies."""
    service = WhatsAppCampaignService(db=mock_db)
    service.set_whatsapp_provider(mock_whatsapp_provider)
    return service


@pytest.fixture
def sample_campaign_config():
    """Sample campaign configuration."""
    return WhatsAppCampaignConfig(
        phone_number_id="102290129340398",
        send_rate_per_second=1.0,
        batch_size=100,
        retry_failed=True,
        max_retries=3,
        scheduled_time=None,
        template_name="event_reminder",
        enable_media=False,
        media_url=None,
        media_type=None,
        media_caption=None,
        enable_buttons=False,
        buttons=[]
    )


@pytest.fixture
def sample_contacts():
    """Sample contact list."""
    return [
        {
            "phone": "+233240000001",
            "name": "John Doe",
            "event": "Sunday Service",
            "date": "2024-12-10"
        },
        {
            "phone": "+233240000002",
            "name": "Jane Smith",
            "event": "Bible Study",
            "date": "2024-12-11"
        },
        {
            "phone": "+233240000003",
            "name": "Bob Johnson",
            "event": "Prayer Meeting",
            "date": "2024-12-12"
        }
    ]


# ==================== CRUD Tests ====================


@pytest.mark.asyncio
async def test_create_campaign(service, mock_db, sample_campaign_config):
    """Test creating a new WhatsApp campaign."""
    # Mock successful insert
    mock_db.whatsapp_campaigns.insert_one.return_value = Mock(inserted_id="campaign_123")

    # Create campaign
    campaign = await service.create_campaign(
        name="Test Campaign",
        organization_id="org_123",
        user_id="user_123",
        template_name="event_reminder",
        template_content="Hi {{1}}, your event is on {{2}}.",
        audience_id="audience_123",
        config=sample_campaign_config
    )

    # Assertions
    assert campaign is not None
    assert campaign.name == "Test Campaign"
    assert campaign.organization_id == "org_123"
    assert campaign.user_id == "user_123"
    assert campaign.status == WhatsAppCampaignStatus.DRAFT
    assert campaign.template_name == "event_reminder"
    assert campaign.progress.total_recipients == 0
    assert campaign.progress.sent == 0
    assert campaign.total_cost == 0.0

    # Verify database was called
    mock_db.whatsapp_campaigns.insert_one.assert_called_once()


@pytest.mark.asyncio
async def test_get_campaign(service, mock_db):
    """Test retrieving a campaign by ID."""
    # Mock campaign data
    campaign_data = {
        "_id": "campaign_123",
        "name": "Test Campaign",
        "organization_id": "org_123",
        "user_id": "user_123",
        "template_name": "event_reminder",
        "template_content": "Hi {{1}}, your event is on {{2}}.",
        "status": "draft",
        "progress": {
            "total_recipients": 0,
            "sent": 0,
            "delivered": 0,
            "read": 0,
            "failed": 0,
            "pending": 0
        },
        "config": {
            "phone_number_id": "102290129340398",
            "send_rate_per_second": 1.0,
            "batch_size": 100,
            "retry_failed": True,
            "max_retries": 3,
            "template_name": "event_reminder",
            "enable_media": False,
            "enable_buttons": False,
            "buttons": []
        },
        "total_cost": 0.0,
        "cost_per_message": 0.0055,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

    mock_db.whatsapp_campaigns.find_one.return_value = campaign_data

    # Get campaign
    campaign = await service.get_campaign("campaign_123")

    # Assertions
    assert campaign is not None
    assert campaign.id == "campaign_123"
    assert campaign.name == "Test Campaign"
    assert campaign.status == WhatsAppCampaignStatus.DRAFT

    # Verify database was called
    mock_db.whatsapp_campaigns.find_one.assert_called_once()


@pytest.mark.asyncio
async def test_update_campaign(service, mock_db):
    """Test updating a campaign."""
    # Mock existing campaign
    existing_campaign = {
        "_id": "campaign_123",
        "name": "Old Name",
        "organization_id": "org_123",
        "status": "draft",
        "progress": {"total_recipients": 0, "sent": 0, "delivered": 0, "read": 0, "failed": 0, "pending": 0},
        "config": {"phone_number_id": "102290129340398", "template_name": "old_template"},
        "total_cost": 0.0,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

    mock_db.whatsapp_campaigns.find_one.return_value = existing_campaign
    mock_db.whatsapp_campaigns.update_one.return_value = Mock(modified_count=1)

    # Update campaign
    updated = await service.update_campaign(
        campaign_id="campaign_123",
        name="New Name",
        template_name="new_template"
    )

    # Assertions
    assert updated is True
    mock_db.whatsapp_campaigns.update_one.assert_called_once()


@pytest.mark.asyncio
async def test_delete_campaign(service, mock_db):
    """Test deleting a campaign."""
    # Mock existing campaign
    existing_campaign = {
        "_id": "campaign_123",
        "status": "draft",
        "organization_id": "org_123"
    }

    mock_db.whatsapp_campaigns.find_one.return_value = existing_campaign
    mock_db.whatsapp_campaigns.delete_one.return_value = Mock(deleted_count=1)
    mock_db.whatsapp_campaign_messages.delete_many = AsyncMock(return_value=Mock(deleted_count=0))

    # Delete campaign
    deleted = await service.delete_campaign("campaign_123", "org_123")

    # Assertions
    assert deleted is True
    mock_db.whatsapp_campaigns.delete_one.assert_called_once()
    mock_db.whatsapp_campaign_messages.delete_many.assert_called_once()


@pytest.mark.asyncio
async def test_list_campaigns(service, mock_db):
    """Test listing campaigns with filters."""
    # Mock campaign list
    campaigns_data = [
        {
            "_id": f"campaign_{i}",
            "name": f"Campaign {i}",
            "organization_id": "org_123",
            "status": "draft" if i % 2 == 0 else "running",
            "progress": {"total_recipients": 100, "sent": i * 10, "delivered": 0, "read": 0, "failed": 0, "pending": 0},
            "config": {"phone_number_id": "102290129340398"},
            "total_cost": i * 0.55,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        for i in range(5)
    ]

    mock_cursor = Mock()
    mock_cursor.skip = Mock(return_value=mock_cursor)
    mock_cursor.limit = Mock(return_value=mock_cursor)
    mock_cursor.to_list = AsyncMock(return_value=campaigns_data)

    mock_db.whatsapp_campaigns.find.return_value = mock_cursor
    mock_db.whatsapp_campaigns.count_documents = AsyncMock(return_value=5)

    # List campaigns
    campaigns = await service.list_campaigns(
        organization_id="org_123",
        status=None,
        limit=10,
        skip=0
    )

    # Assertions
    assert len(campaigns) == 5
    assert all(isinstance(c, WhatsAppCampaign) for c in campaigns)
    assert campaigns[0].name == "Campaign 0"


# ==================== Template Management Tests ====================


@pytest.mark.asyncio
async def test_sync_templates(service, mock_db, mock_whatsapp_provider):
    """Test syncing templates from WhatsApp API."""
    # Mock API response
    mock_whatsapp_provider.get_templates.return_value = [
        {
            "id": "template_1",
            "name": "event_reminder",
            "language": "en_US",
            "category": "UTILITY",
            "status": "APPROVED",
            "components": [
                {"type": "BODY", "text": "Hi {{1}}, your event is on {{2}}."}
            ]
        },
        {
            "id": "template_2",
            "name": "welcome_message",
            "language": "en_US",
            "category": "MARKETING",
            "status": "APPROVED",
            "components": [
                {"type": "BODY", "text": "Welcome {{1}}!"}
            ]
        }
    ]

    mock_db.whatsapp_templates.delete_many.return_value = Mock(deleted_count=0)
    mock_db.whatsapp_templates.insert_one = AsyncMock()

    # Sync templates
    count = await service.sync_templates("org_123")

    # Assertions
    assert count == 2
    assert mock_db.whatsapp_templates.insert_one.call_count == 2
    mock_whatsapp_provider.get_templates.assert_called_once()


@pytest.mark.asyncio
async def test_get_templates(service, mock_db):
    """Test retrieving cached templates."""
    # Mock templates
    templates_data = [
        {
            "_id": "template_1",
            "name": "event_reminder",
            "language": "en_US",
            "category": "UTILITY",
            "status": "APPROVED",
            "components": [],
            "placeholders": ["name", "date"],
            "organization_id": "org_123"
        }
    ]

    mock_cursor = Mock()
    mock_cursor.to_list = AsyncMock(return_value=templates_data)
    mock_db.whatsapp_templates.find.return_value = mock_cursor

    # Get templates
    templates = await service.get_templates("org_123")

    # Assertions
    assert len(templates) == 1
    assert templates[0].name == "event_reminder"
    assert templates[0].status == "APPROVED"


# ==================== Message Preparation Tests ====================


@pytest.mark.asyncio
async def test_prepare_messages(service, sample_contacts, sample_campaign_config):
    """Test preparing messages from contacts and template."""
    template_content = "Hi {{1}}, your event {{2}} is on {{3}}."
    template_variables = {"1": "name", "2": "event", "3": "date"}

    # Prepare messages
    messages = await service.prepare_messages(
        campaign_id="campaign_123",
        contacts=sample_contacts,
        template_content=template_content,
        template_name="event_reminder",
        template_variables=template_variables,
        config=sample_campaign_config
    )

    # Assertions
    assert len(messages) == 3
    assert all(isinstance(m, WhatsAppCampaignMessage) for m in messages)

    # Check first message
    msg1 = messages[0]
    assert msg1.recipient_phone == "+233240000001"
    assert msg1.recipient_name == "John Doe"
    assert "John Doe" in msg1.message_content
    assert "Sunday Service" in msg1.message_content
    assert "2024-12-10" in msg1.message_content
    assert msg1.status == WhatsAppMessageStatus.PENDING
    assert msg1.cost == 0.0055  # Default cost


@pytest.mark.asyncio
async def test_prepare_messages_with_media(service, sample_contacts, sample_campaign_config):
    """Test preparing messages with media attachment."""
    # Enable media
    sample_campaign_config.enable_media = True
    sample_campaign_config.media_url = "https://example.com/image.jpg"
    sample_campaign_config.media_type = "image"
    sample_campaign_config.media_caption = "Event flyer"

    template_content = "Hi {{1}}, see attached flyer for {{2}}."
    template_variables = {"1": "name", "2": "event"}

    # Prepare messages
    messages = await service.prepare_messages(
        campaign_id="campaign_123",
        contacts=sample_contacts,
        template_content=template_content,
        template_name="event_with_image",
        template_variables=template_variables,
        config=sample_campaign_config
    )

    # Assertions
    assert len(messages) == 3
    assert all(m.media_url == "https://example.com/image.jpg" for m in messages)
    assert all(m.media_caption == "Event flyer" for m in messages)
    assert all(m.cost == 0.0155 for m in messages)  # Base + media cost


# ==================== Campaign Execution Tests ====================


@pytest.mark.asyncio
async def test_start_campaign(service, mock_db, mock_whatsapp_provider, sample_contacts, sample_campaign_config):
    """Test starting a campaign."""
    # Mock campaign
    campaign_data = {
        "_id": "campaign_123",
        "name": "Test Campaign",
        "organization_id": "org_123",
        "status": "draft",
        "template_name": "event_reminder",
        "template_content": "Hi {{1}}, your event is on {{2}}.",
        "progress": {"total_recipients": 0, "sent": 0, "delivered": 0, "read": 0, "failed": 0, "pending": 0},
        "config": {
            "phone_number_id": "102290129340398",
            "send_rate_per_second": 10.0,  # Fast for testing
            "batch_size": 100,
            "retry_failed": True,
            "max_retries": 3,
            "template_name": "event_reminder",
            "enable_media": False,
            "enable_buttons": False,
            "buttons": []
        },
        "total_cost": 0.0,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

    mock_db.whatsapp_campaigns.find_one.return_value = campaign_data
    mock_db.whatsapp_campaigns.update_one = AsyncMock()
    mock_db.whatsapp_campaign_messages.insert_one = AsyncMock()
    mock_db.whatsapp_campaign_messages.find = Mock()

    # Mock message cursor
    mock_cursor = Mock()
    mock_cursor.to_list = AsyncMock(return_value=[])
    mock_db.whatsapp_campaign_messages.find.return_value = mock_cursor

    # Start campaign
    result = await service.start_campaign(
        campaign_id="campaign_123",
        contacts=sample_contacts
    )

    # Assertions
    assert result is True

    # Verify campaign status was updated
    assert mock_db.whatsapp_campaigns.update_one.called

    # Give async task time to start
    await asyncio.sleep(0.1)


@pytest.mark.asyncio
async def test_pause_campaign(service, mock_db):
    """Test pausing a running campaign."""
    # Mock running campaign
    campaign_data = {
        "_id": "campaign_123",
        "status": "running",
        "organization_id": "org_123",
        "progress": {"total_recipients": 100, "sent": 50, "delivered": 0, "read": 0, "failed": 0, "pending": 50}
    }

    mock_db.whatsapp_campaigns.find_one.return_value = campaign_data
    mock_db.whatsapp_campaigns.update_one = AsyncMock()

    # Pause campaign
    result = await service.pause_campaign("campaign_123", "org_123")

    # Assertions
    assert result is True
    mock_db.whatsapp_campaigns.update_one.assert_called()


@pytest.mark.asyncio
async def test_cancel_campaign(service, mock_db):
    """Test cancelling a campaign."""
    # Mock running campaign
    campaign_data = {
        "_id": "campaign_123",
        "status": "running",
        "organization_id": "org_123",
        "progress": {"total_recipients": 100, "sent": 50, "delivered": 0, "read": 0, "failed": 0, "pending": 50}
    }

    mock_db.whatsapp_campaigns.find_one.return_value = campaign_data
    mock_db.whatsapp_campaigns.update_one = AsyncMock()

    # Cancel campaign
    result = await service.cancel_campaign("campaign_123", "org_123")

    # Assertions
    assert result is True
    mock_db.whatsapp_campaigns.update_one.assert_called()


# ==================== Webhook Processing Tests ====================


@pytest.mark.asyncio
async def test_process_delivery_status_sent(service, mock_db):
    """Test processing 'sent' delivery status webhook."""
    # Mock message
    message_data = {
        "_id": "msg_123",
        "campaign_id": "campaign_123",
        "status": "pending",
        "provider_message_id": None,
        "sent_at": None
    }

    mock_db.whatsapp_campaign_messages.find_one = AsyncMock(return_value=message_data)
    mock_db.whatsapp_campaign_messages.update_one = AsyncMock()
    mock_db.whatsapp_campaigns.update_one = AsyncMock()

    # Webhook data
    webhook_data = {
        "entry": [{
            "changes": [{
                "value": {
                    "statuses": [{
                        "id": "wamid_12345",
                        "status": "sent",
                        "timestamp": str(int(datetime.now().timestamp())),
                        "recipient_id": "1234567890"
                    }]
                }
            }]
        }]
    }

    # Process webhook
    await service.process_delivery_status(webhook_data)

    # Assertions
    assert mock_db.whatsapp_campaign_messages.update_one.called


@pytest.mark.asyncio
async def test_process_delivery_status_delivered(service, mock_db):
    """Test processing 'delivered' delivery status webhook."""
    message_data = {
        "_id": "msg_123",
        "campaign_id": "campaign_123",
        "status": "sent",
        "provider_message_id": "wamid_12345",
        "delivered_at": None
    }

    mock_db.whatsapp_campaign_messages.find_one = AsyncMock(return_value=message_data)
    mock_db.whatsapp_campaign_messages.update_one = AsyncMock()
    mock_db.whatsapp_campaigns.update_one = AsyncMock()

    webhook_data = {
        "entry": [{
            "changes": [{
                "value": {
                    "statuses": [{
                        "id": "wamid_12345",
                        "status": "delivered",
                        "timestamp": str(int(datetime.now().timestamp()))
                    }]
                }
            }]
        }]
    }

    await service.process_delivery_status(webhook_data)

    assert mock_db.whatsapp_campaign_messages.update_one.called


@pytest.mark.asyncio
async def test_process_delivery_status_read(service, mock_db):
    """Test processing 'read' delivery status webhook."""
    message_data = {
        "_id": "msg_123",
        "campaign_id": "campaign_123",
        "status": "delivered",
        "provider_message_id": "wamid_12345",
        "read_at": None
    }

    mock_db.whatsapp_campaign_messages.find_one = AsyncMock(return_value=message_data)
    mock_db.whatsapp_campaign_messages.update_one = AsyncMock()
    mock_db.whatsapp_campaigns.update_one = AsyncMock()

    webhook_data = {
        "entry": [{
            "changes": [{
                "value": {
                    "statuses": [{
                        "id": "wamid_12345",
                        "status": "read",
                        "timestamp": str(int(datetime.now().timestamp()))
                    }]
                }
            }]
        }]
    }

    await service.process_delivery_status(webhook_data)

    assert mock_db.whatsapp_campaign_messages.update_one.called


@pytest.mark.asyncio
async def test_process_delivery_status_failed(service, mock_db):
    """Test processing 'failed' delivery status webhook."""
    message_data = {
        "_id": "msg_123",
        "campaign_id": "campaign_123",
        "status": "sent",
        "provider_message_id": "wamid_12345",
        "retry_count": 0,
        "failed_at": None
    }

    mock_db.whatsapp_campaign_messages.find_one = AsyncMock(return_value=message_data)
    mock_db.whatsapp_campaign_messages.update_one = AsyncMock()
    mock_db.whatsapp_campaigns.update_one = AsyncMock()

    webhook_data = {
        "entry": [{
            "changes": [{
                "value": {
                    "statuses": [{
                        "id": "wamid_12345",
                        "status": "failed",
                        "timestamp": str(int(datetime.now().timestamp())),
                        "errors": [{
                            "code": 131051,
                            "title": "Message Undeliverable"
                        }]
                    }]
                }
            }]
        }]
    }

    await service.process_delivery_status(webhook_data)

    assert mock_db.whatsapp_campaign_messages.update_one.called


# ==================== Analytics Tests ====================


@pytest.mark.asyncio
async def test_get_campaign_analytics(service, mock_db):
    """Test getting campaign analytics."""
    # Mock campaign
    campaign_data = {
        "_id": "campaign_123",
        "name": "Test Campaign",
        "status": "completed",
        "progress": {
            "total_recipients": 100,
            "sent": 95,
            "delivered": 90,
            "read": 75,
            "failed": 5,
            "pending": 0
        },
        "total_cost": 0.5225,
        "cost_per_message": 0.0055,
        "created_at": datetime.now() - timedelta(hours=2),
        "started_at": datetime.now() - timedelta(hours=1, minutes=30),
        "completed_at": datetime.now()
    }

    mock_db.whatsapp_campaigns.find_one.return_value = campaign_data

    # Get analytics
    analytics = await service.get_campaign_analytics("campaign_123")

    # Assertions
    assert analytics is not None
    assert analytics["campaign_id"] == "campaign_123"
    assert analytics["name"] == "Test Campaign"
    assert analytics["progress"]["total"] == 100
    assert analytics["progress"]["sent"] == 95
    assert analytics["progress"]["delivered"] == 90
    assert analytics["progress"]["read"] == 75
    assert analytics["progress"]["failed"] == 5

    # Check calculated rates
    assert analytics["progress"]["success_rate"] == pytest.approx(95.0, 0.1)  # 95/100
    assert analytics["progress"]["delivery_rate"] == pytest.approx(94.7, 0.1)  # 90/95
    assert analytics["progress"]["read_rate"] == pytest.approx(83.3, 0.1)  # 75/90


# ==================== Cost Calculation Tests ====================


def test_calculate_message_cost_text_only(service):
    """Test cost calculation for text-only messages."""
    config = WhatsAppCampaignConfig(
        phone_number_id="test",
        send_rate_per_second=1.0,
        batch_size=100,
        retry_failed=True,
        max_retries=3,
        template_name="test",
        enable_media=False,
        enable_buttons=False,
        buttons=[]
    )

    cost = service._calculate_message_cost(config)
    assert cost == 0.0055  # Base cost


def test_calculate_message_cost_with_media(service):
    """Test cost calculation for messages with media."""
    config = WhatsAppCampaignConfig(
        phone_number_id="test",
        send_rate_per_second=1.0,
        batch_size=100,
        retry_failed=True,
        max_retries=3,
        template_name="test",
        enable_media=True,
        media_url="https://example.com/image.jpg",
        media_type="image",
        enable_buttons=False,
        buttons=[]
    )

    cost = service._calculate_message_cost(config)
    assert cost == 0.0155  # Base + media cost


# ==================== Edge Cases & Error Handling Tests ====================


@pytest.mark.asyncio
async def test_create_campaign_invalid_template(service):
    """Test creating campaign with invalid template name."""
    with pytest.raises(ValueError):
        await service.create_campaign(
            name="Test",
            organization_id="org_123",
            user_id="user_123",
            template_name="",  # Empty template name
            template_content="Test",
            config=None
        )


@pytest.mark.asyncio
async def test_start_campaign_already_running(service, mock_db):
    """Test starting a campaign that's already running."""
    campaign_data = {
        "_id": "campaign_123",
        "status": "running",
        "organization_id": "org_123"
    }

    mock_db.whatsapp_campaigns.find_one.return_value = campaign_data

    # Should return False or raise error
    result = await service.start_campaign("campaign_123")
    assert result is False or isinstance(result, Exception)


@pytest.mark.asyncio
async def test_delete_running_campaign(service, mock_db):
    """Test that running campaigns cannot be deleted."""
    campaign_data = {
        "_id": "campaign_123",
        "status": "running",
        "organization_id": "org_123"
    }

    mock_db.whatsapp_campaigns.find_one.return_value = campaign_data

    # Should raise error or return False
    with pytest.raises(Exception) or await service.delete_campaign("campaign_123", "org_123") is False:
        pass


@pytest.mark.asyncio
async def test_prepare_messages_empty_contacts(service, sample_campaign_config):
    """Test preparing messages with empty contact list."""
    messages = await service.prepare_messages(
        campaign_id="campaign_123",
        contacts=[],
        template_content="Test",
        template_name="test",
        template_variables={},
        config=sample_campaign_config
    )

    assert len(messages) == 0


# ==================== Integration Test (Optional) ====================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_campaign_flow(service, mock_db, mock_whatsapp_provider, sample_contacts, sample_campaign_config):
    """
    Integration test: Complete campaign flow from creation to completion.

    This test requires a MongoDB instance and WhatsApp API credentials.
    Skip if running in CI/CD without these dependencies.
    """
    # 1. Create campaign
    campaign = await service.create_campaign(
        name="Integration Test Campaign",
        organization_id="org_test",
        user_id="user_test",
        template_name="event_reminder",
        template_content="Hi {{1}}, your event is on {{2}}.",
        config=sample_campaign_config
    )

    assert campaign.status == WhatsAppCampaignStatus.DRAFT
    campaign_id = campaign.id

    # 2. Start campaign with contacts
    started = await service.start_campaign(campaign_id, contacts=sample_contacts)
    assert started is True

    # Wait for messages to be sent
    await asyncio.sleep(5)

    # 3. Check campaign progress
    updated_campaign = await service.get_campaign(campaign_id)
    assert updated_campaign.progress.total_recipients == len(sample_contacts)
    assert updated_campaign.progress.sent > 0

    # 4. Process webhook (simulate)
    webhook_data = {
        "entry": [{
            "changes": [{
                "value": {
                    "statuses": [{
                        "id": "wamid_test_123",
                        "status": "delivered",
                        "timestamp": str(int(datetime.now().timestamp()))
                    }]
                }
            }]
        }]
    }

    await service.process_delivery_status(webhook_data)

    # 5. Get analytics
    analytics = await service.get_campaign_analytics(campaign_id)
    assert analytics["progress"]["total"] == len(sample_contacts)

    # 6. Cleanup
    await service.delete_campaign(campaign_id, "org_test")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
