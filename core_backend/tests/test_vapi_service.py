"""
Tests for VAPI Integration Service
Tests CRUD operations, health checks, and error handling for VAPI agents.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import aiohttp
from datetime import datetime

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../shared"))

from integration.vapi import VAPIService, VAPIAgent, CallType


class TestVAPIService:
    """Test suite for VAPI service operations."""

    @pytest.fixture
    def vapi_service(self):
        """Create VAPI service instance with test configuration."""
        config = {
            "VAPI_API_KEY": "test_api_key_12345",
            "VAPI_US_PHONE_ID": "test_phone_id_67890",
            "webhook_url": "https://test.example.com/vapi/webhook"
        }
        return VAPIService(config)

    @pytest.fixture
    def sample_agent(self):
        """Create sample VAPI agent for testing."""
        return VAPIAgent(
            name="Test Healthcare Agent",
            description="Test agent for healthcare automation",
            system_prompt="You are a helpful healthcare assistant.",
            voice="alloy",
            language="en",
            speed=1.0,
            max_duration=600,
            silence_timeout=10,
            interruptible=True,
            record_calls=True,
            custom_tools=[
                {
                    "name": "search_providers",
                    "description": "Search for healthcare providers",
                    "endpoint": "https://api.example.com/providers/search",
                    "method": "POST"
                }
            ]
        )

    @pytest.mark.asyncio
    async def test_create_agent_success(self, vapi_service, sample_agent):
        """Test successful agent creation."""
        mock_response_data = {
            "id": "assistant_12345",
            "name": "Test Healthcare Agent",
            "created": "2025-09-19T20:00:00Z"
        }

        with patch.object(vapi_service, '_get_session') as mock_session:
            mock_response = Mock()
            mock_response.status = 201
            mock_response.json = AsyncMock(return_value=mock_response_data)

            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response

            result = await vapi_service.create_agent(sample_agent)

            assert result["success"] is True
            assert result["agent_id"] == "assistant_12345"
            assert result["assistant_id"] == "assistant_12345"
            assert result["name"] == "Test Healthcare Agent"
            assert "vapi_response" in result

    @pytest.mark.asyncio
    async def test_create_agent_api_error(self, vapi_service, sample_agent):
        """Test agent creation with API error."""
        with patch.object(vapi_service, '_get_session') as mock_session:
            mock_response = Mock()
            mock_response.status = 400
            mock_response.text = AsyncMock(return_value="Invalid request")

            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response

            result = await vapi_service.create_agent(sample_agent)

            assert result["success"] is False
            assert "VAPI API error: 400" in result["error"]

    @pytest.mark.asyncio
    async def test_create_agent_no_api_key(self, sample_agent):
        """Test agent creation without API key."""
        vapi_service = VAPIService({"VAPI_API_KEY": ""})

        result = await vapi_service.create_agent(sample_agent)

        assert result["success"] is False
        assert result["error"] == "VAPI API key not configured"

    @pytest.mark.asyncio
    async def test_list_agents_success(self, vapi_service):
        """Test successful agent listing."""
        mock_response_data = [
            {
                "id": "assistant_1",
                "name": "Agent 1",
                "created": "2025-09-19T20:00:00Z"
            },
            {
                "id": "assistant_2",
                "name": "Agent 2",
                "created": "2025-09-19T20:01:00Z"
            }
        ]

        with patch.object(vapi_service, '_get_session') as mock_session:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)

            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response

            result = await vapi_service.list_agents(limit=10)

            assert result["success"] is True
            assert len(result["agents"]) == 2
            assert result["agents"][0]["id"] == "assistant_1"
            assert result["total"] == 2
            assert result["limit"] == 10

    @pytest.mark.asyncio
    async def test_get_assistant_success(self, vapi_service):
        """Test successful assistant retrieval."""
        assistant_id = "assistant_12345"
        mock_response_data = {
            "id": assistant_id,
            "name": "Test Agent",
            "model": {"provider": "openai", "model": "gpt-4"},
            "voice": {"provider": "openai", "voiceId": "alloy"}
        }

        with patch.object(vapi_service, '_get_session') as mock_session:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)

            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response

            result = await vapi_service.get_assistant(assistant_id)

            assert result["success"] is True
            assert result["assistant"]["id"] == assistant_id
            assert result["assistant"]["name"] == "Test Agent"

    @pytest.mark.asyncio
    async def test_get_assistant_not_found(self, vapi_service):
        """Test assistant retrieval when not found."""
        assistant_id = "nonexistent_assistant"

        with patch.object(vapi_service, '_get_session') as mock_session:
            mock_response = Mock()
            mock_response.status = 404
            mock_response.text = AsyncMock(return_value="Assistant not found")

            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response

            result = await vapi_service.get_assistant(assistant_id)

            assert result["success"] is False
            assert "Assistant not found" in result["error"]

    @pytest.mark.asyncio
    async def test_create_assistant_from_data(self, vapi_service):
        """Test creating assistant from raw data."""
        assistant_data = {
            "name": "Test Assistant",
            "description": "Test description",
            "systemPrompt": "You are a helpful assistant.",
            "voice": "nova",
            "speed": 1.2,
            "tools": [{"name": "test_tool"}]
        }

        with patch.object(vapi_service, 'create_agent') as mock_create_agent:
            mock_create_agent.return_value = {
                "success": True,
                "agent_id": "assistant_test",
                "name": "Test Assistant"
            }

            result = await vapi_service.create_assistant(assistant_data)

            assert result["success"] is True
            assert result["agent_id"] == "assistant_test"

            # Verify create_agent was called with proper VAPIAgent
            mock_create_agent.assert_called_once()
            called_agent = mock_create_agent.call_args[0][0]
            assert called_agent.name == "Test Assistant"
            assert called_agent.voice == "nova"
            assert called_agent.speed == 1.2

    @pytest.mark.asyncio
    async def test_get_calls_success(self, vapi_service):
        """Test successful call history retrieval."""
        mock_response_data = {
            "data": [
                {
                    "id": "call_1",
                    "status": "completed",
                    "duration": 120,
                    "assistant_id": "assistant_1"
                },
                {
                    "id": "call_2",
                    "status": "failed",
                    "duration": 30,
                    "assistant_id": "assistant_2"
                }
            ]
        }

        with patch.object(vapi_service, '_get_session') as mock_session:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)

            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response

            result = await vapi_service.get_calls()

            assert result["success"] is True
            assert len(result["data"]) == 2
            assert result["data"][0]["id"] == "call_1"

    @pytest.mark.asyncio
    async def test_get_phone_numbers_success(self, vapi_service):
        """Test successful phone numbers retrieval."""
        mock_response_data = [
            {
                "id": "phone_1",
                "number": "+1234567890",
                "provider": "twilio"
            },
            {
                "id": "phone_2",
                "number": "+0987654321",
                "provider": "vonage"
            }
        ]

        with patch.object(vapi_service, '_get_session') as mock_session:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)

            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response

            result = await vapi_service.get_phone_numbers()

            assert len(result) == 2
            assert result[0]["number"] == "+1234567890"

    @pytest.mark.asyncio
    async def test_create_tenant_agent(self, vapi_service, sample_agent):
        """Test creating agent for specific tenant."""
        tenant_id = "tenant_123"
        context = {"automation_id": "auto_456"}

        with patch.object(vapi_service, 'create_agent') as mock_create_agent:
            mock_create_agent.return_value = {
                "success": True,
                "agent_id": "assistant_tenant",
                "name": "Test Healthcare Agent"
            }

            result = await vapi_service.create_tenant_agent(tenant_id, sample_agent, context)

            assert result["success"] is True
            assert result["agent_id"] == "assistant_tenant"

            # Verify tenant metadata was added
            called_agent = mock_create_agent.call_args[0][0]
            assert called_agent.metadata["tenant_id"] == tenant_id
            assert called_agent.metadata["context"] == context

    @pytest.mark.asyncio
    async def test_test_connection_success(self, vapi_service):
        """Test connection test functionality."""
        result = await vapi_service.test_connection()

        assert result["success"] is True
        assert result["api_base"] == "https://api.vapi.ai"
        assert result["api_key_configured"] is True
        assert result["phone_number_configured"] is True
        assert "tested_at" in result

    @pytest.mark.asyncio
    async def test_test_connection_no_api_key(self):
        """Test connection test without API key."""
        vapi_service = VAPIService({"VAPI_API_KEY": ""})

        result = await vapi_service.test_connection()

        assert result["success"] is False
        assert result["error"] == "VAPI API key not configured"

    def test_get_capabilities(self, vapi_service):
        """Test service capabilities reporting."""
        capabilities = vapi_service.get_capabilities()

        assert capabilities["service"] == "vapi"
        assert "create_agent" in capabilities["capabilities"]
        assert "initiate_call" in capabilities["capabilities"]
        assert "list_agents" in capabilities["capabilities"]
        assert "get_analytics" in capabilities["capabilities"]
        assert capabilities["configured"] is True

    @pytest.mark.asyncio
    async def test_close_session(self, vapi_service):
        """Test session cleanup."""
        # Create a mock session
        mock_session = Mock()
        mock_session.close = AsyncMock()
        vapi_service.session = mock_session

        await vapi_service.close()

        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_initiate_call_success(self, vapi_service):
        """Test successful call initiation."""
        to_number = "+1234567890"
        assistant_id = "assistant_123"

        # Mock successful call initiation
        mock_call_id = "call_12345"

        with patch('uuid.uuid4') as mock_uuid:
            mock_uuid.return_value.hex = "mock_call_id_hex"

            result = await vapi_service.initiate_call(to_number, assistant_id)

            assert result["success"] is True
            assert "call_id" in result
            assert result["to_number"] == to_number
            assert result["assistant_id"] == assistant_id

    @pytest.mark.asyncio
    async def test_health_check_comprehensive(self, vapi_service):
        """Test comprehensive health check of VAPI service."""
        # Test connection
        connection_result = await vapi_service.test_connection()
        assert connection_result["success"] is True

        # Test assistant creation and retrieval
        test_agent = VAPIAgent(
            name="Health Check Agent",
            system_prompt="Test prompt",
            voice="alloy"
        )

        # Mock successful operations for health check
        with patch.object(vapi_service, 'create_agent') as mock_create, \
             patch.object(vapi_service, 'get_assistant') as mock_get, \
             patch.object(vapi_service, 'list_agents') as mock_list:

            mock_create.return_value = {"success": True, "agent_id": "health_check_agent"}
            mock_get.return_value = {"success": True, "assistant": {"id": "health_check_agent"}}
            mock_list.return_value = {"success": True, "agents": []}

            # Health check sequence
            create_result = await vapi_service.create_agent(test_agent)
            assert create_result["success"] is True

            get_result = await vapi_service.get_assistant("health_check_agent")
            assert get_result["success"] is True

            list_result = await vapi_service.list_agents()
            assert list_result["success"] is True


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])