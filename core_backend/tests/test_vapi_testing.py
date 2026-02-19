"""
Tests for VAPI Testing Routes - Comprehensive Testing Suite

Tests the programmatic testing capabilities for VAPI assistants,
including health checks, call triggering, webhook testing, and tool call validation.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone
import json

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from backend.routes.vapi_testing import (
    VAPITestingService,
    VAPITestRequest,
    CallTestRequest,
    WebhookTestRequest,
    ToolCallTestRequest,
    TestSuiteRequest,
    TestResult
)


class TestVAPITestingService:
    """Test suite for VAPI testing service."""

    @pytest.fixture
    def testing_service(self):
        """Create testing service instance."""
        service = VAPITestingService()
        # Mock VAPI service for testing
        service.vapi_service = Mock()
        service.vapi_service.api_key = "test_api_key"
        return service

    @pytest.fixture
    def sample_assistant_data(self):
        """Sample assistant data for testing."""
        return {
            "id": "assistant_12345",
            "name": "Test Healthcare Assistant",
            "model": {"provider": "openai", "model": "gpt-4"},
            "voice": {"provider": "openai", "voiceId": "alloy"},
            "systemPrompt": "You are a healthcare assistant.",
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "search_providers",
                        "description": "Search for healthcare providers",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "Search query"},
                                "location": {"type": "string", "description": "Location filter"}
                            },
                            "required": ["query"]
                        }
                    }
                }
            ],
            "serverUrl": "https://api.example.com/webhook"
        }

    @pytest.mark.asyncio
    async def test_assistant_health_check_success(self, testing_service, sample_assistant_data):
        """Test successful assistant health check."""
        assistant_id = "assistant_12345"

        # Mock successful assistant retrieval
        testing_service.vapi_service.get_assistant = AsyncMock(return_value={
            "success": True,
            "assistant": sample_assistant_data
        })

        result = await testing_service.test_assistant_health(assistant_id)

        assert result.success is True
        assert result.test_type == "health"
        assert result.details["assistant_accessible"] is True
        assert result.details["assistant_name"] == "Test Healthcare Assistant"
        assert result.details["model_configured"] is True
        assert result.details["voice_configured"] is True
        assert result.details["tools_count"] == 1
        assert result.details["webhook_configured"] is True
        assert result.error is None

    @pytest.mark.asyncio
    async def test_assistant_health_check_failure(self, testing_service):
        """Test assistant health check with failure."""
        assistant_id = "nonexistent_assistant"

        # Mock failed assistant retrieval
        testing_service.vapi_service.get_assistant = AsyncMock(return_value={
            "success": False,
            "error": "Assistant not found"
        })

        result = await testing_service.test_assistant_health(assistant_id)

        assert result.success is False
        assert result.test_type == "health"
        assert result.error == "Assistant not accessible: Assistant not found"

    @pytest.mark.asyncio
    async def test_assistant_health_check_no_vapi_service(self):
        """Test health check when VAPI service is not available."""
        service = VAPITestingService()
        service.vapi_service = None

        result = await service.test_assistant_health("any_id")

        assert result.success is False
        assert "VAPI service not available" in result.error

    @pytest.mark.asyncio
    async def test_trigger_test_call_success(self, testing_service):
        """Test successful test call triggering."""
        request = CallTestRequest(
            assistant_id="assistant_12345",
            phone_number="+1234567890",
            test_scenario="health_check",
            max_duration=300,
            wait_for_completion=False
        )

        # Mock successful VAPI call creation
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                "id": "call_12345",
                "status": "initiated",
                "assistantId": "assistant_12345"
            }

            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

            result = await testing_service.trigger_test_call(request)

            assert result.success is True
            assert result.test_type == "call"
            assert result.details["call_id"] == "call_12345"
            assert result.details["call_status"] == "initiated"
            assert result.details["phone_number"] == "+1234567890"

    @pytest.mark.asyncio
    async def test_trigger_test_call_with_completion_wait(self, testing_service):
        """Test call triggering with completion waiting."""
        request = CallTestRequest(
            assistant_id="assistant_12345",
            phone_number="+1234567890",
            wait_for_completion=True,
            max_duration=60  # Short duration for testing
        )

        # Mock call creation and status checking
        with patch('httpx.AsyncClient') as mock_client:
            # Mock call creation
            mock_create_response = Mock()
            mock_create_response.status_code = 201
            mock_create_response.json.return_value = {"id": "call_12345", "status": "initiated"}

            # Mock call status check
            mock_status_response = Mock()
            mock_status_response.status_code = 200
            mock_status_response.json.return_value = {"id": "call_12345", "status": "completed"}

            mock_client_instance = mock_client.return_value.__aenter__.return_value
            mock_client_instance.post.return_value = mock_create_response
            mock_client_instance.get.return_value = mock_status_response

            with patch.object(testing_service, '_wait_for_call_completion', return_value="completed"):
                result = await testing_service.trigger_test_call(request)

                assert result.success is True
                assert result.details["call_status"] == "completed"

    @pytest.mark.asyncio
    async def test_trigger_test_call_api_error(self, testing_service):
        """Test call triggering with API error."""
        request = CallTestRequest(
            assistant_id="assistant_12345",
            phone_number="+1234567890"
        )

        # Mock failed VAPI call creation
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.text = "Invalid phone number"

            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

            result = await testing_service.trigger_test_call(request)

            assert result.success is False
            assert result.test_type == "call"
            assert "Failed to create call: 400" in result.error

    @pytest.mark.asyncio
    async def test_wait_for_call_completion_success(self, testing_service):
        """Test waiting for call completion."""
        call_id = "call_12345"
        max_wait = 30

        # Mock status progression: initiated -> in_progress -> completed
        status_sequence = [
            {"id": call_id, "status": "initiated"},
            {"id": call_id, "status": "in_progress"},
            {"id": call_id, "status": "completed"}
        ]

        with patch('httpx.AsyncClient') as mock_client:
            mock_responses = []
            for status_data in status_sequence:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = status_data
                mock_responses.append(mock_response)

            mock_client.return_value.__aenter__.return_value.get.side_effect = mock_responses

            with patch('asyncio.sleep', new_callable=AsyncMock):  # Speed up the test
                result = await testing_service._wait_for_call_completion(call_id, max_wait)

                assert result == "completed"

    @pytest.mark.asyncio
    async def test_wait_for_call_completion_timeout(self, testing_service):
        """Test call completion waiting with timeout."""
        call_id = "call_12345"
        max_wait = 5  # Short timeout

        # Mock status that never completes
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"id": call_id, "status": "in_progress"}

            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

            with patch('asyncio.sleep', new_callable=AsyncMock):  # Speed up the test
                result = await testing_service._wait_for_call_completion(call_id, max_wait)

                assert result == "timeout"

    @pytest.mark.asyncio
    async def test_webhook_test_success(self, testing_service):
        """Test successful webhook testing."""
        request = WebhookTestRequest(
            webhook_url="https://api.example.com/test-webhook",
            payload={"test": "data"},
            method="POST",
            timeout=30
        )

        # Mock successful webhook response
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"Content-Type": "application/json"}
            mock_response.text = '{"success": true}'

            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

            result = await testing_service.test_webhook_endpoint(request)

            assert result.success is True
            assert result.test_type == "webhook"
            assert result.details["status_code"] == 200
            assert result.details["webhook_url"] == request.webhook_url
            assert result.error is None

    @pytest.mark.asyncio
    async def test_webhook_test_failure(self, testing_service):
        """Test webhook testing with HTTP error."""
        request = WebhookTestRequest(
            webhook_url="https://api.example.com/test-webhook",
            payload={"test": "data"}
        )

        # Mock failed webhook response
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.headers = {"Content-Type": "application/json"}
            mock_response.text = '{"error": "Not found"}'

            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

            result = await testing_service.test_webhook_endpoint(request)

            assert result.success is False
            assert result.test_type == "webhook"
            assert result.details["status_code"] == 404
            assert result.error == "HTTP 404"

    @pytest.mark.asyncio
    async def test_webhook_test_connection_error(self, testing_service):
        """Test webhook testing with connection error."""
        request = WebhookTestRequest(
            webhook_url="https://invalid-url.example.com/webhook",
            payload={"test": "data"}
        )

        # Mock connection error
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.side_effect = Exception("Connection failed")

            result = await testing_service.test_webhook_endpoint(request)

            assert result.success is False
            assert "Connection failed" in result.error

    @pytest.mark.asyncio
    async def test_tool_call_validation_success(self, testing_service, sample_assistant_data):
        """Test successful tool call validation."""
        request = ToolCallTestRequest(
            assistant_id="assistant_12345",
            tool_name="search_providers",
            tool_parameters={"query": "cardiologist", "location": "Accra"}
        )

        # Mock health check to return assistant with tools
        testing_service.test_assistant_health = AsyncMock(return_value=TestResult(
            test_id="health_test",
            test_type="health",
            success=True,
            duration=1.0,
            details={"assistant_data": sample_assistant_data},
            timestamp=datetime.now(timezone.utc)
        ))

        result = await testing_service.test_tool_calls(request)

        assert result.success is True
        assert result.test_type == "tool_call"
        assert result.details["tool_found"] is True
        assert result.details["parameters_valid"] is True
        assert result.details["tool_name"] == "search_providers"

    @pytest.mark.asyncio
    async def test_tool_call_validation_tool_not_found(self, testing_service, sample_assistant_data):
        """Test tool call validation when tool is not found."""
        request = ToolCallTestRequest(
            assistant_id="assistant_12345",
            tool_name="nonexistent_tool",
            tool_parameters={"param": "value"}
        )

        # Mock health check
        testing_service.test_assistant_health = AsyncMock(return_value=TestResult(
            test_id="health_test",
            test_type="health",
            success=True,
            duration=1.0,
            details={"assistant_data": sample_assistant_data},
            timestamp=datetime.now(timezone.utc)
        ))

        result = await testing_service.test_tool_calls(request)

        assert result.success is False
        assert "Tool 'nonexistent_tool' not found" in result.error

    @pytest.mark.asyncio
    async def test_tool_call_validation_missing_parameters(self, testing_service, sample_assistant_data):
        """Test tool call validation with missing required parameters."""
        request = ToolCallTestRequest(
            assistant_id="assistant_12345",
            tool_name="search_providers",
            tool_parameters={"location": "Accra"}  # Missing required 'query' parameter
        )

        # Mock health check
        testing_service.test_assistant_health = AsyncMock(return_value=TestResult(
            test_id="health_test",
            test_type="health",
            success=True,
            duration=1.0,
            details={"assistant_data": sample_assistant_data},
            timestamp=datetime.now(timezone.utc)
        ))

        result = await testing_service.test_tool_calls(request)

        assert result.success is False
        assert "Missing required parameters: ['query']" in result.error

    @pytest.mark.asyncio
    async def test_tool_call_validation_assistant_health_fails(self, testing_service):
        """Test tool call validation when assistant health check fails."""
        request = ToolCallTestRequest(
            assistant_id="assistant_12345",
            tool_name="search_providers",
            tool_parameters={"query": "test"}
        )

        # Mock failed health check
        testing_service.test_assistant_health = AsyncMock(return_value=TestResult(
            test_id="health_test",
            test_type="health",
            success=False,
            duration=1.0,
            details={},
            error="Assistant not found",
            timestamp=datetime.now(timezone.utc)
        ))

        result = await testing_service.test_tool_calls(request)

        assert result.success is False
        assert "Assistant health check failed" in result.error

    @pytest.mark.asyncio
    async def test_run_basic_test_suite(self, testing_service):
        """Test running basic test suite."""
        request = TestSuiteRequest(
            assistant_id="assistant_12345",
            test_suite="basic",
            parallel_execution=False
        )

        # Mock health check
        testing_service.test_assistant_health = AsyncMock(return_value=TestResult(
            test_id="health_test",
            test_type="health",
            success=True,
            duration=1.0,
            details={"assistant_accessible": True},
            timestamp=datetime.now(timezone.utc)
        ))

        results = await testing_service.run_test_suite(request)

        assert len(results) == 1
        assert results[0].test_type == "health"
        assert results[0].success is True

    @pytest.mark.asyncio
    async def test_run_test_suite_parallel(self, testing_service):
        """Test running test suite in parallel."""
        request = TestSuiteRequest(
            assistant_id="assistant_12345",
            test_suite="basic",
            parallel_execution=True
        )

        # Mock health check
        testing_service.test_assistant_health = AsyncMock(return_value=TestResult(
            test_id="health_test",
            test_type="health",
            success=True,
            duration=1.0,
            details={"assistant_accessible": True},
            timestamp=datetime.now(timezone.utc)
        ))

        results = await testing_service.run_test_suite(request)

        assert len(results) == 1
        assert results[0].test_type == "health"
        assert results[0].success is True

    @pytest.mark.asyncio
    async def test_run_test_suite_with_exception(self, testing_service):
        """Test test suite handling of exceptions."""
        request = TestSuiteRequest(
            assistant_id="assistant_12345",
            test_suite="basic",
            parallel_execution=True
        )

        # Mock health check that raises exception
        testing_service.test_assistant_health = AsyncMock(side_effect=Exception("Test exception"))

        results = await testing_service.run_test_suite(request)

        assert len(results) == 1
        assert results[0].success is False
        assert "Test exception" in results[0].error

    def test_get_test_result_exists(self, testing_service):
        """Test retrieving existing test result."""
        test_id = "test_12345"
        test_result = TestResult(
            test_id=test_id,
            test_type="health",
            success=True,
            duration=1.0,
            details={"test": "data"},
            timestamp=datetime.now(timezone.utc)
        )

        testing_service.test_results[test_id] = test_result

        result = testing_service.get_test_result(test_id)

        assert result is not None
        assert result.test_id == test_id
        assert result.success is True

    def test_get_test_result_not_exists(self, testing_service):
        """Test retrieving non-existent test result."""
        result = testing_service.get_test_result("nonexistent_id")
        assert result is None

    def test_get_recent_test_results(self, testing_service):
        """Test retrieving recent test results."""
        # Add multiple test results
        for i in range(5):
            test_result = TestResult(
                test_id=f"test_{i}",
                test_type="health",
                success=True,
                duration=1.0,
                details={"test": f"data_{i}"},
                timestamp=datetime.now(timezone.utc)
            )
            testing_service.test_results[f"test_{i}"] = test_result

        results = testing_service.get_recent_test_results(limit=3)

        assert len(results) == 3
        # Results should be sorted by timestamp (most recent first)
        assert results[0].test_id in ["test_0", "test_1", "test_2", "test_3", "test_4"]

    def test_get_recent_test_results_empty(self, testing_service):
        """Test retrieving recent test results when none exist."""
        results = testing_service.get_recent_test_results()
        assert len(results) == 0


class TestVAPITestingModels:
    """Test VAPI testing request/response models."""

    def test_vapi_test_request_validation(self):
        """Test VAPITestRequest model validation."""
        # Valid request
        request = VAPITestRequest(
            assistant_id="assistant_123",
            test_type="health"
        )
        assert request.assistant_id == "assistant_123"
        assert request.test_type == "health"
        assert request.timeout == 30  # Default value

        # Request with all fields
        request_full = VAPITestRequest(
            assistant_id="assistant_123",
            test_type="call",
            test_scenario="integration_test",
            phone_number="+1234567890",
            message="Test message",
            webhook_data={"url": "https://example.com"},
            timeout=60
        )
        assert request_full.phone_number == "+1234567890"
        assert request_full.webhook_data["url"] == "https://example.com"

    def test_call_test_request_validation(self):
        """Test CallTestRequest model validation."""
        request = CallTestRequest(
            assistant_id="assistant_123",
            phone_number="+1234567890"
        )
        assert request.assistant_id == "assistant_123"
        assert request.phone_number == "+1234567890"
        assert request.test_scenario == "health_check"  # Default
        assert request.max_duration == 300  # Default
        assert request.wait_for_completion is True  # Default

    def test_webhook_test_request_validation(self):
        """Test WebhookTestRequest model validation."""
        request = WebhookTestRequest(
            webhook_url="https://api.example.com/webhook",
            payload={"test": "data"}
        )
        assert request.webhook_url == "https://api.example.com/webhook"
        assert request.method == "POST"  # Default
        assert request.timeout == 30  # Default

    def test_tool_call_test_request_validation(self):
        """Test ToolCallTestRequest model validation."""
        request = ToolCallTestRequest(
            assistant_id="assistant_123",
            tool_name="search_providers",
            tool_parameters={"query": "test"}
        )
        assert request.assistant_id == "assistant_123"
        assert request.tool_name == "search_providers"
        assert request.tool_parameters["query"] == "test"
        assert request.test_scenario == "single_tool"  # Default

    def test_test_suite_request_validation(self):
        """Test TestSuiteRequest model validation."""
        request = TestSuiteRequest(
            assistant_id="assistant_123",
            test_suite="basic"
        )
        assert request.assistant_id == "assistant_123"
        assert request.test_suite == "basic"
        assert request.parallel_execution is True  # Default
        assert request.include_performance is False  # Default

    def test_test_result_model(self):
        """Test TestResult model."""
        timestamp = datetime.now(timezone.utc)
        result = TestResult(
            test_id="test_123",
            test_type="health",
            success=True,
            duration=2.5,
            details={"status": "healthy"},
            timestamp=timestamp
        )
        assert result.test_id == "test_123"
        assert result.test_type == "health"
        assert result.success is True
        assert result.duration == 2.5
        assert result.details["status"] == "healthy"
        assert result.error is None
        assert result.timestamp == timestamp

        # Test with error
        error_result = TestResult(
            test_id="test_456",
            test_type="call",
            success=False,
            duration=1.0,
            details={"error_code": 400},
            error="API error",
            timestamp=timestamp
        )
        assert error_result.success is False
        assert error_result.error == "API error"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])