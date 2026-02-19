"""
Tests for Developer Platform Telephony APIs.

This module tests the comprehensive telephony API endpoints
implemented in the Developer Platform.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import json

from backend.main import app
from backend.services.shared.telephony_service import SharedTelephonyService

client = TestClient(app)


class TestTelephonyAPIs:
    """Test suite for telephony API endpoints."""

    @pytest.fixture
    def mock_api_key(self):
        """Mock API key for testing."""
        return "test-api-key-12345"

    @pytest.fixture
    def mock_tenant_id(self):
        """Mock tenant ID for testing."""
        return "test-tenant-123"

    @pytest.fixture
    def mock_call_data(self):
        """Mock call data for testing."""
        return {
            "to": "+1234567890",
            "from": "+0987654321",
            "assistant_id": "assistant-123",
            "metadata": {
                "campaign_id": "campaign-123",
                "customer_id": "customer-456"
            }
        }

    @pytest.fixture
    def mock_transfer_data(self):
        """Mock transfer data for testing."""
        return {
            "destination": "+1555123456",
            "reason": "customer_request"
        }

    @pytest.fixture
    def mock_conference_data(self):
        """Mock conference data for testing."""
        return {
            "participants": ["+1555123456", "+1555987654"],
            "name": "Sales Conference"
        }

    @pytest.fixture
    def mock_recording_data(self):
        """Mock recording data for testing."""
        return {
            "format": "mp3",
            "quality": "high"
        }

    @pytest.fixture
    def mock_assignment_data(self):
        """Mock DID assignment data for testing."""
        return {
            "use_case": "sales_campaign",
            "description": "Primary sales line"
        }

    @patch('backend.main.security_middleware.verify_api_key')
    def test_create_call_success(self, mock_verify, mock_api_key, mock_tenant_id, mock_call_data):
        """Test successful call creation."""
        # Mock API key verification
        mock_verify.return_value = {"tenant_id": mock_tenant_id}
        
        # Mock telephony service
        with patch.object(SharedTelephonyService, 'create_call') as mock_create:
            mock_create.return_value = {
                "call_id": "call-123",
                "status": "initiated",
                "provider": "vapi"
            }
            
            response = client.post(
                "/v1/calls",
                json=mock_call_data,
                headers={"x-api-key": mock_api_key}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["call_id"] == "call-123"
            assert data["status"] == "initiated"
            assert data["provider"] == "vapi"

    @patch('backend.main.security_middleware.verify_api_key')
    def test_list_calls_success(self, mock_verify, mock_api_key, mock_tenant_id):
        """Test successful call listing."""
        # Mock API key verification
        mock_verify.return_value = {"tenant_id": mock_tenant_id}
        
        # Mock telephony service
        with patch.object(SharedTelephonyService, 'list_calls') as mock_list:
            mock_list.return_value = [
                {
                    "call_id": "call-123",
                    "to": "+1234567890",
                    "from_": "+0987654321",
                    "status": "completed",
                    "duration": 300
                }
            ]
            
            response = client.get(
                "/v1/calls",
                headers={"x-api-key": mock_api_key}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "calls" in data
            assert len(data["calls"]) == 1
            assert data["calls"][0]["call_id"] == "call-123"

    @patch('backend.main.security_middleware.verify_api_key')
    def test_get_call_success(self, mock_verify, mock_api_key, mock_tenant_id):
        """Test successful call retrieval."""
        # Mock API key verification
        mock_verify.return_value = {"tenant_id": mock_tenant_id}
        
        # Mock telephony service
        with patch.object(SharedTelephonyService, 'get_call') as mock_get:
            mock_get.return_value = {
                "call_id": "call-123",
                "to": "+1234567890",
                "from_": "+0987654321",
                "status": "completed",
                "duration": 300
            }
            
            response = client.get(
                "/v1/calls/call-123",
                headers={"x-api-key": mock_api_key}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["call_id"] == "call-123"
            assert data["status"] == "completed"

    @patch('backend.main.security_middleware.verify_api_key')
    def test_get_call_not_found(self, mock_verify, mock_api_key, mock_tenant_id):
        """Test call retrieval when call not found."""
        # Mock API key verification
        mock_verify.return_value = {"tenant_id": mock_tenant_id}
        
        # Mock telephony service
        with patch.object(SharedTelephonyService, 'get_call') as mock_get:
            mock_get.return_value = None
            
            response = client.get(
                "/v1/calls/nonexistent-call",
                headers={"x-api-key": mock_api_key}
            )
            
            assert response.status_code == 404
            assert "Call not found" in response.json()["detail"]

    @patch('backend.main.security_middleware.verify_api_key')
    def test_transfer_call_success(self, mock_verify, mock_api_key, mock_tenant_id, mock_transfer_data):
        """Test successful call transfer."""
        # Mock API key verification
        mock_verify.return_value = {"tenant_id": mock_tenant_id}
        
        # Mock telephony service
        with patch.object(SharedTelephonyService, 'transfer_call') as mock_transfer:
            mock_transfer.return_value = {
                "call_id": "call-123",
                "transfer_id": "transfer-123",
                "destination": "+1555123456",
                "status": "transferred"
            }
            
            response = client.post(
                "/v1/calls/call-123/transfer",
                json=mock_transfer_data,
                headers={"x-api-key": mock_api_key}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["call_id"] == "call-123"
            assert data["status"] == "transferred"

    @patch('backend.main.security_middleware.verify_api_key')
    def test_create_conference_success(self, mock_verify, mock_api_key, mock_tenant_id, mock_conference_data):
        """Test successful conference creation."""
        # Mock API key verification
        mock_verify.return_value = {"tenant_id": mock_tenant_id}
        
        # Mock telephony service
        with patch.object(SharedTelephonyService, 'create_conference') as mock_conference:
            mock_conference.return_value = {
                "conference_id": "conf-123",
                "call_id": "call-123",
                "participants": ["+1555123456", "+1555987654"],
                "status": "created"
            }
            
            response = client.post(
                "/v1/calls/call-123/conference",
                json=mock_conference_data,
                headers={"x-api-key": mock_api_key}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["conference_id"] == "conf-123"
            assert data["status"] == "created"

    @patch('backend.main.security_middleware.verify_api_key')
    def test_start_recording_success(self, mock_verify, mock_api_key, mock_tenant_id, mock_recording_data):
        """Test successful recording start."""
        # Mock API key verification
        mock_verify.return_value = {"tenant_id": mock_tenant_id}
        
        # Mock telephony service
        with patch.object(SharedTelephonyService, 'start_recording') as mock_recording:
            mock_recording.return_value = {
                "recording_id": "rec-123",
                "call_id": "call-123",
                "format": "mp3",
                "status": "recording"
            }
            
            response = client.post(
                "/v1/calls/call-123/record",
                json=mock_recording_data,
                headers={"x-api-key": mock_api_key}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["recording_id"] == "rec-123"
            assert data["status"] == "recording"

    @patch('backend.main.security_middleware.verify_api_key')
    def test_stop_recording_success(self, mock_verify, mock_api_key, mock_tenant_id):
        """Test successful recording stop."""
        # Mock API key verification
        mock_verify.return_value = {"tenant_id": mock_tenant_id}
        
        # Mock telephony service
        with patch.object(SharedTelephonyService, 'stop_recording') as mock_recording:
            mock_recording.return_value = {
                "recording_id": "rec-123",
                "call_id": "call-123",
                "status": "stopped",
                "duration": 300
            }
            
            response = client.delete(
                "/v1/calls/call-123/record",
                headers={"x-api-key": mock_api_key}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["recording_id"] == "rec-123"
            assert data["status"] == "stopped"

    @patch('backend.main.security_middleware.verify_api_key')
    def test_list_providers_success(self, mock_verify, mock_api_key, mock_tenant_id):
        """Test successful provider listing."""
        # Mock API key verification
        mock_verify.return_value = {"tenant_id": mock_tenant_id}
        
        # Mock telephony service
        with patch.object(SharedTelephonyService, 'list_providers') as mock_list:
            mock_list.return_value = [
                {
                    "id": "vapi",
                    "name": "VAPI",
                    "status": "healthy",
                    "capabilities": ["voice", "sms", "recording"]
                }
            ]
            
            response = client.get(
                "/v1/providers",
                headers={"x-api-key": mock_api_key}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "providers" in data
            assert len(data["providers"]) == 1
            assert data["providers"][0]["id"] == "vapi"

    @patch('backend.main.security_middleware.verify_api_key')
    def test_get_provider_health_success(self, mock_verify, mock_api_key, mock_tenant_id):
        """Test successful provider health retrieval."""
        # Mock API key verification
        mock_verify.return_value = {"tenant_id": mock_tenant_id}
        
        # Mock telephony service
        with patch.object(SharedTelephonyService, 'get_provider_health') as mock_health:
            mock_health.return_value = {
                "provider_id": "vapi",
                "status": "healthy",
                "response_time": 100
            }
            
            response = client.get(
                "/v1/providers/vapi/health",
                headers={"x-api-key": mock_api_key}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["provider_id"] == "vapi"
            assert data["status"] == "healthy"

    @patch('backend.main.security_middleware.verify_api_key')
    def test_get_provider_costs_success(self, mock_verify, mock_api_key, mock_tenant_id):
        """Test successful provider cost retrieval."""
        # Mock API key verification
        mock_verify.return_value = {"tenant_id": mock_tenant_id}
        
        # Mock telephony service
        with patch.object(SharedTelephonyService, 'get_provider_costs') as mock_costs:
            mock_costs.return_value = {
                "provider_id": "vapi",
                "period": "monthly",
                "total_cost": 150.50,
                "call_minutes": 7500
            }
            
            response = client.get(
                "/v1/providers/vapi/costs",
                headers={"x-api-key": mock_api_key}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["provider_id"] == "vapi"
            assert data["total_cost"] == 150.50

    @patch('backend.main.security_middleware.verify_api_key')
    def test_compare_providers_success(self, mock_verify, mock_api_key, mock_tenant_id):
        """Test successful provider comparison."""
        # Mock API key verification
        mock_verify.return_value = {"tenant_id": mock_tenant_id}
        
        # Mock telephony service
        with patch.object(SharedTelephonyService, 'compare_providers') as mock_compare:
            mock_compare.return_value = {
                "providers": [
                    {"id": "vapi", "name": "VAPI"},
                    {"id": "vonage", "name": "Vonage"}
                ],
                "recommendations": {
                    "best_cost": "vonage",
                    "best_quality": "vapi"
                }
            }
            
            response = client.get(
                "/v1/providers/comparison",
                headers={"x-api-key": mock_api_key}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "providers" in data
            assert "recommendations" in data
            assert len(data["providers"]) == 2

    @patch('backend.main.security_middleware.verify_api_key')
    def test_list_dids_success(self, mock_verify, mock_api_key, mock_tenant_id):
        """Test successful DID listing."""
        # Mock API key verification
        mock_verify.return_value = {"tenant_id": mock_tenant_id}
        
        # Mock telephony service
        with patch.object(SharedTelephonyService, 'list_dids') as mock_list:
            mock_list.return_value = [
                {
                    "did": "+1234567890",
                    "country": "US",
                    "type": "local",
                    "capabilities": ["voice", "sms"]
                }
            ]
            
            response = client.get(
                "/v1/dids",
                headers={"x-api-key": mock_api_key}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "dids" in data
            assert len(data["dids"]) == 1
            assert data["dids"][0]["did"] == "+1234567890"

    @patch('backend.main.security_middleware.verify_api_key')
    def test_assign_did_success(self, mock_verify, mock_api_key, mock_tenant_id, mock_assignment_data):
        """Test successful DID assignment."""
        # Mock API key verification
        mock_verify.return_value = {"tenant_id": mock_tenant_id}
        
        # Mock telephony service
        with patch.object(SharedTelephonyService, 'assign_did') as mock_assign:
            mock_assign.return_value = {
                "did": "+1234567890",
                "tenant_id": mock_tenant_id,
                "use_case": "sales_campaign",
                "assigned": True
            }
            
            response = client.post(
                "/v1/dids/+1234567890/assign",
                json=mock_assignment_data,
                headers={"x-api-key": mock_api_key}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["did"] == "+1234567890"
            assert data["assigned"] is True

    @patch('backend.main.security_middleware.verify_api_key')
    def test_get_available_dids_success(self, mock_verify, mock_api_key, mock_tenant_id):
        """Test successful available DID retrieval."""
        # Mock API key verification
        mock_verify.return_value = {"tenant_id": mock_tenant_id}
        
        # Mock telephony service
        with patch.object(SharedTelephonyService, 'get_available_dids') as mock_available:
            mock_available.return_value = [
                {
                    "did": "+1555123456",
                    "country": "US",
                    "type": "local",
                    "capabilities": ["voice", "sms"],
                    "monthly_cost": 3.00
                }
            ]
            
            response = client.get(
                "/v1/dids/available",
                headers={"x-api-key": mock_api_key}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "available_dids" in data
            assert len(data["available_dids"]) == 1
            assert data["available_dids"][0]["did"] == "+1555123456"

    @patch('backend.main.security_middleware.verify_api_key')
    def test_get_call_analytics_success(self, mock_verify, mock_api_key, mock_tenant_id):
        """Test successful call analytics retrieval."""
        # Mock API key verification
        mock_verify.return_value = {"tenant_id": mock_tenant_id}
        
        # Mock telephony service
        with patch.object(SharedTelephonyService, 'get_call_analytics') as mock_analytics:
            mock_analytics.return_value = {
                "period": "daily",
                "total_calls": 1250,
                "completed_calls": 1180,
                "success_rate": 94.4
            }
            
            response = client.get(
                "/v1/analytics/calls",
                headers={"x-api-key": mock_api_key}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["period"] == "daily"
            assert data["total_calls"] == 1250
            assert data["success_rate"] == 94.4

    @patch('backend.main.security_middleware.verify_api_key')
    def test_get_quality_metrics_success(self, mock_verify, mock_api_key, mock_tenant_id):
        """Test successful quality metrics retrieval."""
        # Mock API key verification
        mock_verify.return_value = {"tenant_id": mock_tenant_id}
        
        # Mock telephony service
        with patch.object(SharedTelephonyService, 'get_quality_metrics') as mock_metrics:
            mock_metrics.return_value = {
                "period": "daily",
                "average_quality_score": 4.2,
                "call_completion_rate": 94.4
            }
            
            response = client.get(
                "/v1/analytics/quality",
                headers={"x-api-key": mock_api_key}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["period"] == "daily"
            assert data["average_quality_score"] == 4.2
            assert data["call_completion_rate"] == 94.4

    @patch('backend.main.security_middleware.verify_api_key')
    def test_get_usage_analytics_success(self, mock_verify, mock_api_key, mock_tenant_id):
        """Test successful usage analytics retrieval."""
        # Mock API key verification
        mock_verify.return_value = {"tenant_id": mock_tenant_id}
        
        # Mock usage service
        with patch('backend.main.shared_usage_service.get_usage_summary') as mock_usage:
            mock_usage.return_value = type('obj', (object,), {
                'dict': lambda: {
                    "period": "daily",
                    "total_usage": 1000,
                    "cost": 50.00
                }
            })()
            
            response = client.get(
                "/v1/analytics/usage",
                headers={"x-api-key": mock_api_key}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["period"] == "daily"
            assert data["total_usage"] == 1000
            assert data["cost"] == 50.00

    def test_create_call_missing_api_key(self, mock_call_data):
        """Test call creation without API key."""
        response = client.post("/v1/calls", json=mock_call_data)
        assert response.status_code == 422  # Validation error for missing header

    @patch('backend.main.security_middleware.verify_api_key')
    def test_create_call_invalid_api_key(self, mock_verify, mock_call_data):
        """Test call creation with invalid API key."""
        # Mock API key verification to fail
        mock_verify.side_effect = ValueError("Invalid API key")
        
        response = client.post(
            "/v1/calls",
            json=mock_call_data,
            headers={"x-api-key": "invalid-key"}
        )
        
        assert response.status_code == 401
        assert "Invalid API key" in response.json()["detail"]

    @patch('backend.main.security_middleware.verify_api_key')
    def test_telephony_service_error_handling(self, mock_verify, mock_api_key, mock_tenant_id, mock_call_data):
        """Test error handling when telephony service fails."""
        # Mock API key verification
        mock_verify.return_value = {"tenant_id": mock_tenant_id}
        
        # Mock telephony service to raise exception
        with patch.object(SharedTelephonyService, 'create_call') as mock_create:
            mock_create.side_effect = Exception("Telephony service unavailable")
            
            response = client.post(
                "/v1/calls",
                json=mock_call_data,
                headers={"x-api-key": mock_api_key}
            )
            
            assert response.status_code == 500
            assert "Telephony service unavailable" in response.json()["detail"]


class TestTelephonyServiceMethods:
    """Test suite for telephony service methods."""

    @pytest.fixture
    def telephony_service(self):
        """Create telephony service instance."""
        return SharedTelephonyService()

    @pytest.mark.asyncio
    async def test_create_call(self, telephony_service):
        """Test create_call method."""
        call_data = {
            "to": "+1234567890",
            "from": "+0987654321",
            "assistant_id": "assistant-123"
        }
        
        result = await telephony_service.create_call("tenant-123", call_data)
        
        assert "call_id" in result
        assert result["status"] == "initiated"
        assert result["provider"] == "default"

    @pytest.mark.asyncio
    async def test_list_calls(self, telephony_service):
        """Test list_calls method."""
        result = await telephony_service.list_calls("tenant-123", limit=10)
        
        assert isinstance(result, list)
        assert len(result) <= 10

    @pytest.mark.asyncio
    async def test_get_call(self, telephony_service):
        """Test get_call method."""
        result = await telephony_service.get_call("tenant-123", "call-123")
        
        # Should return None for non-existent call
        assert result is None

    @pytest.mark.asyncio
    async def test_list_providers(self, telephony_service):
        """Test list_providers method."""
        result = await telephony_service.list_providers("tenant-123")
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert "id" in result[0]
        assert "name" in result[0]

    @pytest.mark.asyncio
    async def test_get_provider_health(self, telephony_service):
        """Test get_provider_health method."""
        result = await telephony_service.get_provider_health("tenant-123")
        
        assert "status" in result
        assert "providers" in result

    @pytest.mark.asyncio
    async def test_get_provider_costs(self, telephony_service):
        """Test get_provider_costs method."""
        result = await telephony_service.get_provider_costs("tenant-123", "vapi")
        
        assert "provider_id" in result
        assert "total_cost" in result
        assert "call_minutes" in result

    @pytest.mark.asyncio
    async def test_compare_providers(self, telephony_service):
        """Test compare_providers method."""
        result = await telephony_service.compare_providers("tenant-123")
        
        assert "providers" in result
        assert "recommendations" in result

    @pytest.mark.asyncio
    async def test_list_dids(self, telephony_service):
        """Test list_dids method."""
        result = await telephony_service.list_dids("tenant-123")
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert "did" in result[0]

    @pytest.mark.asyncio
    async def test_get_available_dids(self, telephony_service):
        """Test get_available_dids method."""
        result = await telephony_service.get_available_dids("tenant-123")
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert "did" in result[0]
        assert "monthly_cost" in result[0]

    @pytest.mark.asyncio
    async def test_get_call_analytics(self, telephony_service):
        """Test get_call_analytics method."""
        result = await telephony_service.get_call_analytics("tenant-123")
        
        assert "period" in result
        assert "total_calls" in result
        assert "success_rate" in result

    @pytest.mark.asyncio
    async def test_get_quality_metrics(self, telephony_service):
        """Test get_quality_metrics method."""
        result = await telephony_service.get_quality_metrics("tenant-123")
        
        assert "period" in result
        assert "average_quality_score" in result
        assert "call_completion_rate" in result

