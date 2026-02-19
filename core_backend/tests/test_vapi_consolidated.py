"""
Unit tests for VAPI consolidated endpoints.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException

from backend.main import app
from backend.routes.vapi_consolidated import VapiAgentCreateRequest


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_current_user():
    """Mock current user for authentication."""
    return {
        "user_id": "test_user_123",
        "email": "test@example.com"
    }


@pytest.fixture
def valid_agent_request():
    """Valid VAPI agent creation request."""
    return {
        "name": "Test Agent",
        "description": "Test agent for unit testing",
        "system_prompt": "You are a helpful test assistant. Respond to user queries professionally.",
        "voice": "paige",
        "language": "en",
        "speed": 1.0,
        "call_type": "both",
        "max_duration": 600,
        "silence_timeout": 10,
        "interruptible": True,
        "record_calls": True,
        "integrations": ["calendly_scheduling", "resend_email"],
        "custom_tools": [
            {
                "id": "tool_1",
                "name": "test_tool",
                "description": "Test tool",
                "endpoint": "https://example.com/webhook",
                "method": "POST",
                "schema": {"type": "object", "properties": {}}
            }
        ],
        "tenant_id": "test_tenant",
        "vapi_config": {
            "firstMessage": "Hello! How can I help you today?",
            "endCallMessage": "Thank you for calling. Goodbye!",
            "transcriber": {
                "model": "nova-3-general",
                "language": "en",
                "provider": "deepgram"
            }
        }
    }


class TestVAPIAgentCreation:
    """Test VAPI agent creation functionality."""

    @patch('backend.routes.vapi_consolidated.get_current_user_mongo')
    @patch('backend.routes.vapi_consolidated.vapi_service')
    def test_create_vapi_agent_success(self, mock_vapi_service, mock_get_user, client, mock_current_user, valid_agent_request):
        """Test successful VAPI agent creation."""
        # Mock authentication
        mock_get_user.return_value = mock_current_user

        # Mock VAPI service response
        mock_vapi_service.create_tenant_agent = AsyncMock(return_value={
            "success": True,
            "agent_id": "vapi_agent_123",
            "assistant_id": "vapi_agent_123",
            "name": "Test Agent",
            "voice": "paige",
            "created_at": "2024-01-01T00:00:00Z"
        })

        # Make request
        response = client.post("/vapi-consolidated/agents", json=valid_agent_request)

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "agent" in data
        assert data["message"] == "VAPI agent created successfully via consolidated service"

        # Verify VAPI service was called correctly
        mock_vapi_service.create_tenant_agent.assert_called_once()
        call_args = mock_vapi_service.create_tenant_agent.call_args
        assert call_args[1]["tenant_id"] == "test_tenant"
        assert call_args[1]["agent"].name == "Test Agent"
        assert call_args[1]["agent"].system_prompt == valid_agent_request["system_prompt"]
        assert call_args[1]["agent"].voice == "paige"

    @patch('backend.routes.vapi_consolidated.get_current_user_mongo')
    def test_create_vapi_agent_missing_name(self, mock_get_user, client, mock_current_user, valid_agent_request):
        """Test VAPI agent creation with missing name."""
        mock_get_user.return_value = mock_current_user

        # Remove name from request
        del valid_agent_request["name"]

        response = client.post("/vapi-consolidated/agents", json=valid_agent_request)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @patch('backend.routes.vapi_consolidated.get_current_user_mongo')
    def test_create_vapi_agent_short_name(self, mock_get_user, client, mock_current_user, valid_agent_request):
        """Test VAPI agent creation with name too short."""
        mock_get_user.return_value = mock_current_user

        # Set name too short
        valid_agent_request["name"] = "AB"

        response = client.post("/vapi-consolidated/agents", json=valid_agent_request)

        assert response.status_code == 422
        data = response.json()
        assert "Agent name must be at least 3 characters long" in data["detail"]

    @patch('backend.routes.vapi_consolidated.get_current_user_mongo')
    def test_create_vapi_agent_missing_system_prompt(self, mock_get_user, client, mock_current_user, valid_agent_request):
        """Test VAPI agent creation with missing system prompt."""
        mock_get_user.return_value = mock_current_user

        # Remove system_prompt from request
        del valid_agent_request["system_prompt"]

        response = client.post("/vapi-consolidated/agents", json=valid_agent_request)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @patch('backend.routes.vapi_consolidated.get_current_user_mongo')
    def test_create_vapi_agent_short_system_prompt(self, mock_get_user, client, mock_current_user, valid_agent_request):
        """Test VAPI agent creation with system prompt too short."""
        mock_get_user.return_value = mock_current_user

        # Set system prompt too short
        valid_agent_request["system_prompt"] = "Hi"

        response = client.post("/vapi-consolidated/agents", json=valid_agent_request)

        assert response.status_code == 422
        data = response.json()
        assert "System prompt must be at least 10 characters long" in data["detail"]

    @patch('backend.routes.vapi_consolidated.get_current_user_mongo')
    @patch('backend.routes.vapi_consolidated.vapi_service')
    def test_create_vapi_agent_service_failure(self, mock_vapi_service, mock_get_user, client, mock_current_user, valid_agent_request):
        """Test VAPI agent creation when service fails."""
        mock_get_user.return_value = mock_current_user

        # Mock VAPI service failure
        mock_vapi_service.create_tenant_agent = AsyncMock(return_value={
            "success": False,
            "error": "VAPI API connection failed"
        })

        response = client.post("/vapi-consolidated/agents", json=valid_agent_request)

        assert response.status_code == 400
        data = response.json()
        assert "VAPI API connection failed" in data["detail"]

    @patch('backend.routes.vapi_consolidated.get_current_user_mongo')
    @patch('backend.routes.vapi_consolidated.vapi_service')
    def test_create_vapi_agent_with_vapi_config(self, mock_vapi_service, mock_get_user, client, mock_current_user, valid_agent_request):
        """Test VAPI agent creation with advanced VAPI configuration."""
        mock_get_user.return_value = mock_current_user

        # Mock VAPI service response
        mock_vapi_service.create_tenant_agent = AsyncMock(return_value={
            "success": True,
            "agent_id": "vapi_agent_123",
            "assistant_id": "vapi_agent_123"
        })

        response = client.post("/vapi-consolidated/agents", json=valid_agent_request)

        assert response.status_code == 200

        # Verify VAPI config was passed correctly
        call_args = mock_vapi_service.create_tenant_agent.call_args
        context = call_args[1]["context"]
        assert "vapi_config" in context
        assert context["vapi_config"]["firstMessage"] == "Hello! How can I help you today?"

    def test_vapi_agent_create_request_model(self):
        """Test VapiAgentCreateRequest model validation."""
        # Test valid request
        valid_data = {
            "name": "Test Agent",
            "system_prompt": "You are a helpful assistant.",
            "voice": "paige"
        }
        request = VapiAgentCreateRequest(**valid_data)
        assert request.name == "Test Agent"
        assert request.voice == "paige"
        assert request.language == "en"  # default value
        assert request.speed == 1.0  # default value

        # Test with vapi_config
        data_with_config = {
            **valid_data,
            "vapi_config": {
                "firstMessage": "Hello there!",
                "transcriber": {"model": "nova-3"}
            }
        }
        request_with_config = VapiAgentCreateRequest(**data_with_config)
        assert request_with_config.vapi_config is not None
        assert request_with_config.vapi_config["firstMessage"] == "Hello there!"

    @patch('backend.routes.vapi_consolidated.get_current_user_mongo')
    def test_authentication_required(self, mock_get_user, client, valid_agent_request):
        """Test that authentication is required for agent creation."""
        # Mock authentication failure
        mock_get_user.side_effect = HTTPException(status_code=401, detail="Unauthorized")

        response = client.post("/vapi-consolidated/agents", json=valid_agent_request)

        assert response.status_code == 401


class TestVAPIHealthCheck:
    """Test VAPI health check functionality."""

    @patch('backend.routes.vapi_consolidated.vapi_service')
    def test_vapi_health_check_success(self, mock_vapi_service, client):
        """Test successful VAPI health check."""
        mock_vapi_service.test_connection = AsyncMock(return_value={
            "success": True,
            "message": "Connection successful"
        })

        response = client.get("/vapi-consolidated/health")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["service"] == "vapi_consolidated"
        assert data["status"] == "healthy"

    @patch('backend.routes.vapi_consolidated.vapi_service')
    def test_vapi_health_check_failure(self, mock_vapi_service, client):
        """Test VAPI health check when service is down."""
        mock_vapi_service.test_connection = AsyncMock(return_value={
            "success": False,
            "error": "Connection failed"
        })

        response = client.get("/vapi-consolidated/health")

        assert response.status_code == 200  # Health check always returns 200
        data = response.json()
        assert data["success"] is True  # Health endpoint itself succeeded
        assert data["status"] == "degraded"


class TestVAPICapabilities:
    """Test VAPI capabilities endpoint."""

    @patch('backend.routes.vapi_consolidated.vapi_service')
    def test_get_vapi_capabilities(self, mock_vapi_service, client):
        """Test getting VAPI service capabilities."""
        mock_vapi_service.get_capabilities.return_value = {
            "service": "vapi",
            "capabilities": ["create_agent", "initiate_call"],
            "configured": True
        }

        response = client.get("/vapi-consolidated/capabilities")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "capabilities" in data
        assert data["service_version"] == "consolidated"