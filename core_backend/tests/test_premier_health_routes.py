"""
Unit tests for Premier Health Insurance Service Location API routes.

Tests core functionality with proper mocking and dependency handling.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import status
import sys
import os
from typing import Dict, Any, List

# Import the router directly
import apps.core_backend.backend.routes.premier_health as premier_health
from fastapi import FastAPI


# Mock for HealthcareVoiceTools
class HealthcareVoiceToolsMock:
    """Mock class for HealthcareVoiceTools to avoid external dependencies."""

    def __init__(self, db_config):
        self.db_config = db_config

    def search_healthcare_providers(self, query: str = "", max_results: int = 5,
                                   location: str = None, specialty: str = None,
                                   provider_type: str = None) -> Dict[str, Any]:
        """Mock search healthcare providers."""
        return {
            "success": True,
            "providers": [
                {
                    "id": 1,
                    "name": "Test Hospital",
                    "address": "123 Test St, Accra",
                    "phone": "+233123456789",
                    "specialty": specialty or "General Medicine"
                }
            ],
            "total_found": 1,
            "confidence": 0.95,
            "voice_response": "I found 1 healthcare provider matching your search."
        }

    def get_emergency_providers(self, location: str = None, max_results: int = 5) -> Dict[str, Any]:
        """Mock emergency providers."""
        return {
            "success": True,
            "providers": [
                {
                    "id": 1,
                    "name": "Emergency Hospital",
                    "address": "Emergency St, Accra",
                    "phone": "+233911",
                    "type": "Emergency"
                }
            ],
            "emergency_guidance": "For life-threatening emergencies, call 911 immediately.",
            "voice_response": "Here are nearby emergency healthcare providers."
        }

    def get_available_areas(self) -> Dict[str, Any]:
        """Mock available areas."""
        return {
            "success": True,
            "areas": ["Accra", "Kumasi", "Takoradi"],
            "total_areas": 3
        }

    def get_available_specialties(self) -> Dict[str, Any]:
        """Mock available specialties."""
        return {
            "success": True,
            "specialties": ["Cardiology", "Pediatrics", "General Medicine"],
            "total_specialties": 3
        }


# Mock auth dependency
async def mock_get_current_user():
    return {"id": "test_user_id", "email": "test@example.com"}


# Create test app with mocked dependencies
def create_test_app():
    app = FastAPI()

    # Override the auth dependency
    app.dependency_overrides[premier_health.get_current_user_mongo] = mock_get_current_user

    app.include_router(premier_health.router)
    return app


class TestPremierHealthRoutes:
    """Test suite for Premier Health routes with proper dependency mocking."""

    def setup_method(self):
        """Set up test app for each test."""
        self.app = create_test_app()
        self.client = TestClient(self.app)

    @patch('apps.core_backend.backend.routes.premier_health.HealthcareVoiceTools', HealthcareVoiceToolsMock)
    def test_search_healthcare_providers_success(self):
        """Test successful healthcare provider search."""
        request_data = {
            "query": "cardiology doctor",
            "max_results": 5,
            "location": "Accra",
            "specialty": "Cardiology",
            "call_id": "test_call_123",
            "customer_number": "+233123456789"
        }

        response = self.client.post("/premier-health/search", json=request_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["call_id"] == "test_call_123"
        assert data["data"]["customer_number"] == "+233123456789"
        assert "search_timestamp" in data["data"]

    @patch('apps.core_backend.backend.routes.premier_health.HealthcareVoiceTools', HealthcareVoiceToolsMock)
    def test_search_healthcare_providers_minimal_request(self):
        """Test healthcare search with minimal required data."""
        request_data = {"query": "hospital"}

        response = self.client.post("/premier-health/search", json=request_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["data"]["providers"][0]["name"] == "Test Hospital"

    @patch('apps.core_backend.backend.routes.premier_health.HealthcareVoiceTools')
    def test_search_healthcare_providers_failure(self, mock_tools):
        """Test healthcare search error handling."""
        mock_tools.side_effect = Exception("Database connection error")

        request_data = {"query": "cardiology"}

        response = self.client.post("/premier-health/search", json=request_data)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Healthcare search failed" in response.json()["detail"]

    @patch('apps.core_backend.backend.routes.premier_health.HealthcareVoiceTools', HealthcareVoiceToolsMock)
    def test_get_emergency_providers_success(self):
        """Test successful emergency provider retrieval."""
        request_data = {"location": "Accra", "max_results": 3}

        response = self.client.post("/premier-health/emergency-providers", json=request_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "emergency_guidance" in data["data"]
        assert data["data"]["providers"][0]["name"] == "Emergency Hospital"

    @patch('apps.core_backend.backend.routes.premier_health.HealthcareVoiceTools', HealthcareVoiceToolsMock)
    def test_get_available_areas_success(self):
        """Test successful areas retrieval."""
        response = self.client.get("/premier-health/areas")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "Accra" in data["data"]["areas"]
        assert data["data"]["total_areas"] == 3

    @patch('apps.core_backend.backend.routes.premier_health.HealthcareVoiceTools', HealthcareVoiceToolsMock)
    def test_get_available_specialties_success(self):
        """Test successful specialties retrieval."""
        response = self.client.get("/premier-health/specialties")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "Cardiology" in data["data"]["specialties"]
        assert data["data"]["total_specialties"] == 3

    @patch('apps.core_backend.backend.routes.premier_health.TOOL_SCHEMAS', {"mock": "schema"})
    def test_get_tool_schemas_success(self):
        """Test successful tool schemas retrieval."""
        response = self.client.get("/premier-health/tool-schemas")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["schemas"]["mock"] == "schema"

    @patch('apps.core_backend.backend.routes.premier_health.HealthcareVoiceTools', HealthcareVoiceToolsMock)
    def test_health_check_success(self):
        """Test successful health check."""
        response = self.client.get("/premier-health/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Premier Health Insurance Service Location Agent"
        assert data["database_connected"] is True
        assert data["total_areas"] == 3

    @patch('apps.core_backend.backend.routes.premier_health.HealthcareVoiceTools')
    def test_health_check_failure(self, mock_tools):
        """Test health check with database connection failure."""
        mock_instance = Mock()
        mock_instance.get_available_areas.side_effect = Exception("Connection failed")
        mock_tools.return_value = mock_instance

        response = self.client.get("/premier-health/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "Connection failed" in data["error"]


class TestVAPIWebhook:
    """Test suite for VAPI webhook functionality."""

    def setup_method(self):
        """Set up test app for each test."""
        self.app = create_test_app()
        self.client = TestClient(self.app)

    @patch('apps.core_backend.backend.routes.premier_health.HealthcareVoiceTools', HealthcareVoiceToolsMock)
    def test_vapi_webhook_search_function_call(self):
        """Test VAPI webhook with search function call."""
        webhook_data = {
            "call": {"id": "test_call_123"},
            "phoneNumber": "+233123456789",
            "message": {
                "function_call": {
                    "name": "search_healthcare_providers",
                    "arguments": {
                        "query": "cardiology doctor",
                        "max_results": 3,
                        "location": "Accra"
                    }
                }
            }
        }

        response = self.client.post("/premier-health/vapi-webhook", json=webhook_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"]["type"] == "assistant"
        assert "found 1 healthcare provider" in data["message"]["content"]
        assert data["message"]["function_call_result"]["success"] is True

    @patch('apps.core_backend.backend.routes.premier_health.HealthcareVoiceTools', HealthcareVoiceToolsMock)
    def test_vapi_webhook_emergency_function_call(self):
        """Test VAPI webhook with emergency providers function call."""
        webhook_data = {
            "call": {"id": "emergency_call_123"},
            "message": {
                "function_call": {
                    "name": "get_emergency_providers",
                    "arguments": {
                        "location": "Accra",
                        "max_results": 5
                    }
                }
            }
        }

        response = self.client.post("/premier-health/vapi-webhook", json=webhook_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"]["type"] == "assistant"
        assert "nearby emergency healthcare providers" in data["message"]["content"]
        assert "emergency_guidance" in data["message"]["function_call_result"]["data"]

    def test_vapi_webhook_no_function_call(self):
        """Test VAPI webhook without function call - fallback response."""
        webhook_data = {
            "call": {"id": "general_call_123"},
            "transcript": "Hello, I need help finding a doctor"
        }

        response = self.client.post("/premier-health/vapi-webhook", json=webhook_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"]["type"] == "assistant"
        assert "help you find healthcare providers" in data["message"]["content"]

    @patch('apps.core_backend.backend.routes.premier_health.HealthcareVoiceTools')
    def test_vapi_webhook_error_handling(self, mock_tools):
        """Test VAPI webhook error handling."""
        mock_tools.side_effect = Exception("Service unavailable")

        webhook_data = {
            "message": {
                "function_call": {
                    "name": "search_healthcare_providers",
                    "arguments": {"query": "test"}
                }
            }
        }

        response = self.client.post("/premier-health/vapi-webhook", json=webhook_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "technical difficulties" in data["message"]["content"]


class TestValidationAndEdgeCases:
    """Test suite for validation and edge cases."""

    def setup_method(self):
        """Set up test app for each test."""
        self.app = create_test_app()
        self.client = TestClient(self.app)

    def test_invalid_search_request_missing_query(self):
        """Test search request with missing required query field."""
        response = self.client.post("/premier-health/search", json={})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_invalid_email_request_missing_fields(self):
        """Test SMS request with missing required fields (updated from email to SMS)."""
        response = self.client.post("/premier-health/send-email", json={"customer_phone": "+233123456789"})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_invalid_escalation_request_missing_fields(self):
        """Test escalation request with missing required fields."""
        incomplete_data = {
            "first_name": "Test User"
            # Missing required fields like customer_phone, search_query, location_searched
        }

        response = self.client.post("/premier-health/escalate-to-support", json=incomplete_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestUpdatedFunctionality:
    """Test suite for updated email-to-SMS and escalation functionality."""

    def setup_method(self):
        """Set up test app for each test."""
        self.app = create_test_app()
        self.client = TestClient(self.app)

    @patch('apps.core_backend.backend.routes.premier_health.HealthcareVoiceTools')
    def test_send_provider_email_with_phone(self, mock_tools):
        """Test sending provider info via SMS using customer_phone instead of email."""
        mock_instance = Mock()
        mock_instance.send_provider_info_sms.return_value = {
            "success": True,
            "message": "SMS sent successfully",
            "message_id": "sms_123"
        }
        mock_tools.return_value = mock_instance

        request_data = {
            "customer_phone": "+233123456789",
            "first_name": "John",
            "provider_data": [
                {
                    "name": "Test Hospital",
                    "address": "123 Test St",
                    "phone": "+233987654321"
                }
            ],
            "search_query": "cardiologist in Accra"
        }

        response = self.client.post("/premier-health/send-email", json=request_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        mock_instance.send_provider_info_sms.assert_called_once()

    @patch('apps.core_backend.backend.routes.premier_health.HealthcareVoiceTools')
    def test_escalate_to_support_with_first_name(self, mock_tools):
        """Test escalation using first_name and customer_phone only."""
        mock_instance = Mock()
        mock_instance.escalate_to_support.return_value = {
            "success": True,
            "ticket_id": "FD123",
            "message": "Escalated successfully"
        }
        mock_tools.return_value = mock_instance

        request_data = {
            "first_name": "Jane",
            "customer_phone": "+233123456789",
            "search_query": "pediatrician in Tema",
            "location_searched": "Tema",
            "issue_description": "No providers found in this location"
        }

        response = self.client.post("/premier-health/escalate-to-support", json=request_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        mock_instance.escalate_to_support.assert_called_once_with(
            customer_name="Jane",
            customer_phone="+233123456789",
            search_query="pediatrician in Tema",
            location_searched="Tema",
            issue_description="No providers found in this location"
        )

    def test_send_email_requires_customer_phone(self):
        """Test that customer_phone is required for SMS sending."""
        request_data = {
            "first_name": "John",
            "provider_data": [{"name": "Test Hospital"}]
            # Missing customer_phone
        }

        response = self.client.post("/premier-health/send-email", json=request_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_escalation_requires_first_name_and_phone(self):
        """Test that both first_name and customer_phone are required for escalation."""
        request_data = {
            "search_query": "cardiologist",
            "location_searched": "Accra"
            # Missing first_name and customer_phone
        }

        response = self.client.post("/premier-health/escalate-to-support", json=request_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


if __name__ == "__main__":
    pytest.main([__file__, "-v"])