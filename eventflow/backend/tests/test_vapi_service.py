"""
Tests for VAPI service integration.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from apps.eventflow.backend.app.services.vapi_service import EventFlowVAPIService
from apps.shared.integration.vapi import VAPIAgent, VAPIWebhookEvent, WebhookEventType


class TestEventFlowVAPIService:
    """Test EventFlow VAPI service."""

    @pytest.mark.asyncio
    async def test_vapi_service_initialization(self):
        """Test VAPI service initialization."""
        service = EventFlowVAPIService()

        assert service.shared_vapi is None
        assert service.initialized is False
        assert service.ama_assistant_id is None

    @pytest.mark.asyncio
    async def test_initialize_without_api_key(self):
        """Test initialization fails gracefully without API key."""
        service = EventFlowVAPIService()

        # Mock environment without VAPI_API_KEY
        with patch.dict(os.environ, {}, clear=True):
            result = await service.initialize()

        assert result is False
        assert service.initialized is False

    @pytest.mark.asyncio
    async def test_initialize_with_api_key(self):
        """Test initialization succeeds with API key."""
        service = EventFlowVAPIService()

        # Mock environment with VAPI_API_KEY
        with patch.dict(os.environ, {"VAPI_API_KEY": "test_key_123"}):
            # Mock the _ensure_ama_assistant method
            with patch.object(service, "_ensure_ama_assistant", return_value=True):
                result = await service.initialize()

        assert result is True
        assert service.initialized is True

    @pytest.mark.asyncio
    async def test_call_responsible_person_not_initialized(self):
        """Test call fails when service not initialized."""
        service = EventFlowVAPIService()

        result = await service.call_responsible_person(
            task_id="task_123",
            event_id="event_456",
            person_name="John Doe",
            person_phone="+233244567890",
            task_title="Test Task",
            task_deadline=datetime.now() + timedelta(days=7),
            wallet_id="wallet_789"
        )

        assert result["success"] is False
        assert "not initialized" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_call_responsible_person_success(self):
        """Test successful call initiation."""
        service = EventFlowVAPIService()
        service.initialized = True
        service.ama_assistant_id = "assistant_123"

        # Mock shared VAPI service
        mock_vapi = Mock()
        mock_vapi.initiate_call = AsyncMock(return_value={
            "success": True,
            "call_id": "call_abc123",
            "status": "initiated",
            "to_number": "+233244567890"
        })
        service.shared_vapi = mock_vapi

        result = await service.call_responsible_person(
            task_id="task_123",
            event_id="event_456",
            person_name="Sarah Johnson",
            person_phone="0244567890",  # Local format
            task_title="Book conference venue",
            task_deadline=datetime.now() + timedelta(days=14),
            wallet_id="wallet_789"
        )

        assert result["success"] is True
        assert "call_id" in result
        assert result["call_id"] == "call_abc123"

        # Verify call was made with correct metadata
        mock_vapi.initiate_call.assert_called_once()
        call_args = mock_vapi.initiate_call.call_args
        assert call_args[1]["assistant_id"] == "assistant_123"
        assert "+233" in call_args[1]["to_number"]  # Converted to E.164
        assert call_args[1]["metadata"]["task_id"] == "task_123"
        assert call_args[1]["metadata"]["app"] == "eventflow"

    @pytest.mark.asyncio
    async def test_webhook_handling_call_ended(self):
        """Test webhook handling for call ended event."""
        service = EventFlowVAPIService()
        service.initialized = True

        # Mock shared VAPI service
        mock_vapi = Mock()
        mock_vapi.get_call_status = AsyncMock(return_value={
            "success": True,
            "call": {
                "call_id": "call_123",
                "duration": 180,
                "metadata": {
                    "task_id": "task_456",
                    "event_id": "event_789",
                    "wallet_id": "wallet_abc",
                    "person_name": "John Smith"
                }
            }
        })
        service.shared_vapi = mock_vapi

        # Mock wallet service (mocked at the point of import within the function)
        mock_wallet_module = Mock()
        mock_wallet_instance = Mock()
        mock_wallet_instance.initialize = AsyncMock()
        mock_wallet_instance.deduct_voice_call_cost = AsyncMock(return_value={"id": "txn_123"})
        mock_wallet_module.EventFlowWalletService = Mock(return_value=mock_wallet_instance)

        with patch.dict("sys.modules", {"apps.eventflow.backend.app.services.wallet_service": mock_wallet_module}):
            event_data = {
                "event": "call.ended",
                "callId": "call_123",
                "duration": 180,
                "endedReason": "customer-ended-call"
            }

            result = await service.handle_webhook(event_data)

        assert result["success"] is True
        assert result["event_type"] == "call_ended"
        assert result["duration"] == 180

    @pytest.mark.asyncio
    async def test_webhook_handling_function_call(self):
        """Test webhook handling for function call event."""
        service = EventFlowVAPIService()
        service.initialized = True

        # Mock shared VAPI service
        mock_vapi = Mock()
        mock_vapi.get_call_status = AsyncMock(return_value={
            "success": True,
            "call": {
                "call_id": "call_123",
                "metadata": {
                    "task_id": "task_456",
                    "event_id": "event_789"
                }
            }
        })
        service.shared_vapi = mock_vapi

        event_data = {
            "event": "function-call",
            "callId": "call_123",
            "functionCall": {
                "name": "update_task_status",
                "parameters": {
                    "status": "in_progress",
                    "notes": "Working on it now",
                    "completion_percentage": 30
                }
            }
        }

        result = await service.handle_webhook(event_data)

        assert result["success"] is True
        assert result["message"] == "Task status updated successfully"
        assert result["task_id"] == "task_456"
        assert result["status"] == "in_progress"

    @pytest.mark.asyncio
    async def test_webhook_handling_transcript(self):
        """Test webhook handling for transcript event."""
        service = EventFlowVAPIService()
        service.initialized = True
        service.shared_vapi = Mock()

        event_data = {
            "event": "transcript",
            "callId": "call_123",
            "transcript": "Hello, this is Ama calling about your task..."
        }

        result = await service.handle_webhook(event_data)

        assert result["success"] is True
        assert result["event_type"] == "transcript"
        assert result["call_id"] == "call_123"
        assert result["transcript_length"] > 0

    @pytest.mark.asyncio
    async def test_get_call_history_filtered_by_event(self):
        """Test getting call history filtered by event."""
        service = EventFlowVAPIService()
        service.initialized = True

        # Mock shared VAPI service with call data
        mock_vapi = Mock()
        mock_vapi.get_calls = AsyncMock(return_value={
            "success": True,
            "data": [
                {
                    "call_id": "call_1",
                    "metadata": {"event_id": "event_123", "app": "eventflow"}
                },
                {
                    "call_id": "call_2",
                    "metadata": {"event_id": "event_456", "app": "eventflow"}
                },
                {
                    "call_id": "call_3",
                    "metadata": {"event_id": "event_123", "app": "eventflow"}
                },
            ]
        })
        service.shared_vapi = mock_vapi

        result = await service.get_call_history(event_id="event_123")

        assert result["success"] is True
        assert result["total"] == 2
        assert len(result["calls"]) == 2
        assert all(call["metadata"]["event_id"] == "event_123" for call in result["calls"])

    @pytest.mark.asyncio
    async def test_get_call_history_filtered_by_task(self):
        """Test getting call history filtered by task."""
        service = EventFlowVAPIService()
        service.initialized = True

        # Mock shared VAPI service with call data
        mock_vapi = Mock()
        mock_vapi.get_calls = AsyncMock(return_value={
            "success": True,
            "data": [
                {
                    "call_id": "call_1",
                    "metadata": {"task_id": "task_123", "app": "eventflow"}
                },
                {
                    "call_id": "call_2",
                    "metadata": {"task_id": "task_456", "app": "eventflow"}
                },
            ]
        })
        service.shared_vapi = mock_vapi

        result = await service.get_call_history(task_id="task_123")

        assert result["success"] is True
        assert result["total"] == 1
        assert result["calls"][0]["metadata"]["task_id"] == "task_123"

    @pytest.mark.asyncio
    async def test_ama_assistant_creation(self):
        """Test Ama assistant creation with proper configuration."""
        service = EventFlowVAPIService()
        service.initialized = True

        # Mock shared VAPI service
        mock_vapi = Mock()
        mock_vapi.list_agents = AsyncMock(return_value={
            "success": True,
            "agents": []  # No existing Ama
        })
        mock_vapi.create_agent = AsyncMock(return_value={
            "success": True,
            "agent_id": "assistant_ama_123",
            "name": "Ama - EventFlow Assistant"
        })
        service.shared_vapi = mock_vapi

        result = await service._ensure_ama_assistant()

        assert result is True
        assert service.ama_assistant_id == "assistant_ama_123"

        # Verify Ama was created with correct configuration
        mock_vapi.create_agent.assert_called_once()
        agent_arg = mock_vapi.create_agent.call_args[0][0]
        assert agent_arg.name == "Ama - EventFlow Assistant"
        assert agent_arg.voice == "Savannah"
        assert "EventFlow" in agent_arg.system_prompt
        assert agent_arg.metadata["app"] == "eventflow"

    @pytest.mark.asyncio
    async def test_phone_number_formatting(self):
        """Test phone number formatting to E.164."""
        service = EventFlowVAPIService()
        service.initialized = True
        service.ama_assistant_id = "assistant_123"

        # Mock shared VAPI service
        mock_vapi = Mock()
        mock_vapi.initiate_call = AsyncMock(return_value={
            "success": True,
            "call_id": "call_123"
        })
        service.shared_vapi = mock_vapi

        # Test with local Ghana number
        await service.call_responsible_person(
            task_id="task_1",
            event_id="event_1",
            person_name="Test",
            person_phone="0244567890",  # Local format
            task_title="Test",
            task_deadline=datetime.now(),
            wallet_id="wallet_1"
        )

        call_args = mock_vapi.initiate_call.call_args
        phone = call_args[1]["to_number"]

        # Should be converted to E.164 format
        assert phone.startswith("+233")
        assert phone == "+233244567890"  # Leading zero removed, +233 added


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
