"""
Comprehensive tests for the unified VAPI service.
Tests all functionality including consolidated features.
"""

import pytest
import asyncio
import sys
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Add shared path for imports
sys.path.append('/opt/kasaai/apps/shared')
from integration.vapi import VAPIService, VAPIAgent, VAPIWebhookEvent, CallStatus, WebhookEventType


class TestVAPIServiceUnified:
    """Test suite for the unified VAPI service."""

    @pytest.fixture
    def vapi_config(self):
        """VAPI service configuration."""
        return {
            "VAPI_API_KEY": "test_api_key_12345",
            "VAPI_US_PHONE_ID": "test_phone_id_67890",
            "webhook_url": "https://api.ailabsafrica.com/vapi/webhook"
        }

    @pytest.fixture
    def vapi_service(self, vapi_config):
        """Create VAPI service instance."""
        return VAPIService(vapi_config)

    @pytest.fixture
    def sample_agent(self):
        """Sample VAPI agent for testing."""
        return VAPIAgent(
            name="Test Agent",
            description="A test voice agent",
            system_prompt="You are a helpful test assistant",
            voice="alloy",
            language="en",
            speed=1.0,
            max_duration=300,
            silence_timeout=10,
            interruptible=True,
            record_calls=True
        )

    @pytest.fixture
    def sample_webhook_event(self):
        """Sample webhook event."""
        return VAPIWebhookEvent(
            event=WebhookEventType.CALL_STARTED,
            call_id="test_call_123",
            assistant_id="test_assistant_456",
            phone_number="+1234567890",
            customer_number="+0987654321"
        )

    def test_service_initialization(self, vapi_config):
        """Test VAPI service initialization."""
        service = VAPIService(vapi_config)

        assert service.api_key == "test_api_key_12345"
        assert service.phone_number_id == "test_phone_id_67890"
        assert service.webhook_url == "https://api.ailabsafrica.com/vapi/webhook"
        assert service.base_url == "https://api.vapi.ai"

    def test_service_initialization_without_config(self):
        """Test VAPI service initialization without config."""
        with patch.dict(os.environ, {
            "VAPI_API_KEY": "env_api_key",
            "VAPI_US_PHONE_ID": "env_phone_id"
        }):
            service = VAPIService()
            assert service.api_key is None  # Config not passed, so uses None

    def test_get_capabilities(self, vapi_service):
        """Test getting service capabilities."""
        capabilities = vapi_service.get_capabilities()

        assert capabilities["service"] == "vapi"
        assert "create_agent" in capabilities["capabilities"]
        assert "initiate_call" in capabilities["capabilities"]
        assert "handle_webhook" in capabilities["capabilities"]
        assert "get_analytics" in capabilities["capabilities"]

        # Test new consolidated methods
        assert "get_service_info" in capabilities["capabilities"]
        assert "bulk_create_assistants" in capabilities["capabilities"]
        assert "get_analytics_summary" in capabilities["capabilities"]

    @pytest.mark.asyncio
    async def test_create_agent_success(self, vapi_service, sample_agent):
        """Test successful agent creation."""
        mock_response_data = {
            "id": "assistant_123",
            "name": "Test Agent",
            "created_at": "2025-01-01T00:00:00Z"
        }

        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 201
            mock_response.json = AsyncMock(return_value=mock_response_data)

            mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await vapi_service.create_agent(sample_agent)

            assert result["success"] is True
            assert result["agent_id"] == "assistant_123"
            assert result["name"] == "Test Agent"

    @pytest.mark.asyncio
    async def test_create_agent_no_api_key(self, sample_agent):
        """Test agent creation without API key."""
        service = VAPIService({"VAPI_API_KEY": None})

        result = await service.create_agent(sample_agent)

        assert result["success"] is False
        assert "API key not configured" in result["error"]

    @pytest.mark.asyncio
    async def test_create_agent_api_error(self, vapi_service, sample_agent):
        """Test agent creation with API error."""
        with patch.object(vapi_service, '_get_session') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 400
            mock_response.text = AsyncMock(return_value="Bad request")

            mock_session.return_value.__aenter__ = AsyncMock()
            mock_session.return_value.__aexit__ = AsyncMock()
            mock_session.return_value.post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_session.return_value.post.return_value.__aexit__ = AsyncMock()

            result = await vapi_service.create_agent(sample_agent)

            assert result["success"] is False
            assert "VAPI API error: 400" in result["error"]

    @pytest.mark.asyncio
    async def test_initiate_call_success(self, vapi_service):
        """Test successful call initiation."""
        result = await vapi_service.initiate_call(
            to_number="+1234567890",
            assistant_id="assistant_123",
            metadata={"test": "data"}
        )

        assert result["success"] is True
        assert result["to_number"] == "+1234567890"
        assert result["assistant_id"] == "assistant_123"
        assert result["status"] == CallStatus.INITIATED.value

    @pytest.mark.asyncio
    async def test_initiate_call_no_api_key(self):
        """Test call initiation without API key."""
        service = VAPIService({"VAPI_API_KEY": None})

        result = await service.initiate_call("+1234567890", "assistant_123")

        assert result["success"] is False
        assert "API key not configured" in result["error"]

    @pytest.mark.asyncio
    async def test_get_call_status(self, vapi_service):
        """Test getting call status."""
        # First initiate a call to create tracking data
        await vapi_service.initiate_call("+1234567890", "assistant_123")
        call_id = list(vapi_service.active_calls.keys())[0]

        result = await vapi_service.get_call_status(call_id)

        assert result["success"] is True
        assert "call" in result
        assert result["call"]["call_id"] == call_id

    @pytest.mark.asyncio
    async def test_end_call(self, vapi_service):
        """Test ending a call."""
        # First initiate a call
        init_result = await vapi_service.initiate_call("+1234567890", "assistant_123")
        call_id = init_result["call_id"]

        result = await vapi_service.end_call(call_id)

        assert result["success"] is True
        assert result["call_id"] == call_id
        assert result["status"] == CallStatus.ENDED.value

    @pytest.mark.asyncio
    async def test_handle_webhook_call_started(self, vapi_service, sample_webhook_event):
        """Test handling call started webhook."""
        result = await vapi_service.handle_webhook(sample_webhook_event)

        assert result["success"] is True
        assert result["event_type"] == "call_started"
        assert result["call_id"] == "test_call_123"

    @pytest.mark.asyncio
    async def test_handle_webhook_call_ended(self, vapi_service):
        """Test handling call ended webhook."""
        event = VAPIWebhookEvent(
            event=WebhookEventType.CALL_ENDED,
            call_id="test_call_123",
            duration=120,
            ended_reason="completed"
        )

        result = await vapi_service.handle_webhook(event)

        assert result["success"] is True
        assert result["event_type"] == "call_ended"
        assert result["duration"] == 120

    @pytest.mark.asyncio
    async def test_list_agents_success(self, vapi_service):
        """Test successful agent listing."""
        mock_response_data = [
            {"id": "agent_1", "name": "Agent 1"},
            {"id": "agent_2", "name": "Agent 2"}
        ]

        with patch.object(vapi_service, '_get_session') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)

            mock_session.return_value.__aenter__ = AsyncMock()
            mock_session.return_value.__aexit__ = AsyncMock()
            mock_session.return_value.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_session.return_value.get.return_value.__aexit__ = AsyncMock()

            result = await vapi_service.list_agents(limit=10)

            assert result["success"] is True
            assert len(result["agents"]) == 2
            assert result["total"] == 2

    @pytest.mark.asyncio
    async def test_get_analytics(self, vapi_service):
        """Test getting analytics."""
        result = await vapi_service.get_analytics("assistant_123")

        assert result["success"] is True
        assert "analytics" in result
        assert result["analytics"]["assistant_id"] == "assistant_123"

    @pytest.mark.asyncio
    async def test_test_connection_success(self, vapi_service):
        """Test successful connection test."""
        result = await vapi_service.test_connection()

        assert result["success"] is True
        assert result["api_key_configured"] is True
        assert result["api_base"] == "https://api.vapi.ai"

    @pytest.mark.asyncio
    async def test_test_connection_no_api_key(self):
        """Test connection test without API key."""
        service = VAPIService({"VAPI_API_KEY": None})

        result = await service.test_connection()

        assert result["success"] is False
        assert "API key not configured" in result["error"]

    @pytest.mark.asyncio
    async def test_create_tenant_agent(self, vapi_service, sample_agent):
        """Test creating agent for specific tenant."""
        with patch.object(vapi_service, 'create_agent') as mock_create:
            mock_create.return_value = {"success": True, "agent_id": "agent_123"}

            result = await vapi_service.create_tenant_agent(
                tenant_id="tenant_456",
                agent=sample_agent,
                context={"test": "context"}
            )

            assert result["success"] is True
            # Verify tenant metadata was added
            assert sample_agent.metadata["tenant_id"] == "tenant_456"
            assert sample_agent.metadata["context"]["test"] == "context"

    # Test new consolidated methods
    @pytest.mark.asyncio
    async def test_get_service_info(self, vapi_service):
        """Test getting service information."""
        with patch.object(vapi_service, 'test_connection') as mock_test:
            mock_test.return_value = {"success": True}

            result = await vapi_service.get_service_info()

            assert result["service_name"] == "VAPI Consolidated"
            assert result["service_type"] == "Voice AI Platform"
            assert "voice_calls" in result["capabilities"]

    @pytest.mark.asyncio
    async def test_bulk_create_assistants(self, vapi_service):
        """Test bulk assistant creation."""
        assistants_data = [
            {"name": "Assistant 1", "systemPrompt": "Test prompt 1"},
            {"name": "Assistant 2", "systemPrompt": "Test prompt 2"}
        ]

        with patch.object(vapi_service, 'create_assistant') as mock_create:
            mock_create.side_effect = [
                {"success": True, "agent_id": "agent_1"},
                {"success": True, "agent_id": "agent_2"}
            ]

            results = await vapi_service.bulk_create_assistants(assistants_data)

            assert len(results) == 2
            assert all(r["success"] for r in results)

    @pytest.mark.asyncio
    async def test_bulk_create_assistants_with_error(self, vapi_service):
        """Test bulk assistant creation with one failure."""
        assistants_data = [
            {"name": "Assistant 1", "systemPrompt": "Test prompt 1"},
            {"name": "Assistant 2", "systemPrompt": "Test prompt 2"}
        ]

        with patch.object(vapi_service, 'create_assistant') as mock_create:
            mock_create.side_effect = [
                {"success": True, "agent_id": "agent_1"},
                Exception("Creation failed")
            ]

            results = await vapi_service.bulk_create_assistants(assistants_data)

            assert len(results) == 2
            assert results[0]["success"] is True
            assert results[1]["success"] is False
            assert "Creation failed" in results[1]["error"]

    @pytest.mark.asyncio
    async def test_get_analytics_summary(self, vapi_service):
        """Test getting analytics summary."""
        with patch.object(vapi_service, 'get_calls') as mock_calls, \
             patch.object(vapi_service, 'get_assistants') as mock_assistants, \
             patch.object(vapi_service, 'get_phone_numbers') as mock_phones:

            mock_calls.return_value = {"data": [{"id": "call_1"}, {"id": "call_2"}]}
            mock_assistants.return_value = [{"id": "assistant_1"}]
            mock_phones.return_value = [{"id": "phone_1"}]

            result = await vapi_service.get_analytics_summary(days=7)

            assert result["period_days"] == 7
            assert result["total_calls"] == 2
            assert result["total_assistants"] == 1
            assert result["active_phone_numbers"] == 1

    @pytest.mark.asyncio
    async def test_get_analytics_summary_error(self, vapi_service):
        """Test analytics summary with error."""
        with patch.object(vapi_service, 'get_calls') as mock_calls:
            mock_calls.side_effect = Exception("API error")

            result = await vapi_service.get_analytics_summary()

            assert "error" in result
            assert "API error" in result["error"]

    @pytest.mark.asyncio
    async def test_session_management(self, vapi_service):
        """Test HTTP session management."""
        # Get session creates a new one
        session1 = await vapi_service._get_session()
        assert session1 is not None

        # Getting again returns the same session
        session2 = await vapi_service._get_session()
        assert session1 is session2

        # Close session
        await vapi_service.close()
        assert vapi_service.session is None

    def test_agent_model_validation(self):
        """Test VAPIAgent model validation."""
        # Valid agent
        agent = VAPIAgent(
            name="Test Agent",
            system_prompt="Test prompt",
            speed=1.5,
            max_duration=300
        )
        assert agent.name == "Test Agent"
        assert agent.speed == 1.5

        # Invalid speed should be clamped or raise error
        with pytest.raises(ValueError):
            VAPIAgent(
                name="Test Agent",
                system_prompt="Test prompt",
                speed=3.0,  # Too high
                max_duration=300
            )

    def test_webhook_event_model(self):
        """Test VAPIWebhookEvent model."""
        event_data = {
            "event": "call.started",
            "callId": "call_123",
            "assistantId": "assistant_456"
        }

        event = VAPIWebhookEvent(**event_data)
        assert event.event == WebhookEventType.CALL_STARTED
        assert event.call_id == "call_123"
        assert event.assistant_id == "assistant_456"

    @pytest.mark.asyncio
    async def test_edge_cases(self, vapi_service):
        """Test edge cases and error scenarios."""
        # Test with empty call ID
        result = await vapi_service.get_call_status("")
        assert result["success"] is True

        # Test with a known but unhandled webhook event
        speech_event = VAPIWebhookEvent(event=WebhookEventType.SPEECH_UPDATE)
        result = await vapi_service.handle_webhook(speech_event)
        assert result["success"] is True
        assert "not processed" in result["message"]