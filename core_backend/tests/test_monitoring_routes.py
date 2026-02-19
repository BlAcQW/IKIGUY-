"""
Unit tests for the monitoring API routes.

This module tests the monitoring API endpoints for VAPI call analytics,
automation health tracking, and campaign performance metrics.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from backend.main import app
from backend.routes.monitoring import (
    VAPICallMetricsRequest,
    AutomationHealthRequest,
    MetricsQuery
)


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Mock authentication headers."""
    return {"Authorization": "Bearer test_token"}


@pytest.fixture
def mock_current_user():
    """Mock current user data."""
    return {
        "user_id": "test_user_123",
        "tenant_id": "test_tenant_456",
        "email": "test@example.com"
    }


class TestVAPICallMetricsEndpoints:
    """Test VAPI call metrics API endpoints."""

    @patch('backend.routes.monitoring.get_current_user')
    @patch('backend.routes.monitoring.AutomationMonitoringService')
    def test_record_vapi_call_metrics_success(self, mock_service, mock_get_user, client, auth_headers, mock_current_user):
        """Test successful recording of VAPI call metrics."""
        # Setup mocks
        mock_get_user.return_value = mock_current_user
        mock_service_instance = Mock()
        mock_service_instance.record_vapi_call_metrics = AsyncMock(return_value="metric_id_123")
        mock_service.return_value = mock_service_instance

        # Test data
        request_data = {
            "automation_id": "test_automation_123",
            "campaign_id": "test_campaign_456",
            "call_duration": 180.5,
            "call_status": "completed",
            "sentiment_score": 0.75,
            "transcript": "Customer called about insurance claim",
            "cost": 0.45,
            "metadata": {"call_id": "call_789"}
        }

        # Make request
        response = client.post(
            "/api/monitoring/vapi-calls",
            json=request_data,
            headers=auth_headers
        )

        # Assertions
        assert response.status_code == 200
        assert response.json()["metrics_id"] == "metric_id_123"
        mock_service_instance.record_vapi_call_metrics.assert_called_once()

    @patch('backend.routes.monitoring.get_current_user')
    @patch('backend.routes.monitoring.AutomationMonitoringService')
    def test_get_vapi_call_metrics_success(self, mock_service, mock_get_user, client, auth_headers, mock_current_user):
        """Test successful retrieval of VAPI call metrics."""
        # Setup mocks
        mock_get_user.return_value = mock_current_user
        mock_service_instance = Mock()

        # Mock metrics data
        mock_metrics = [
            Mock(
                id="metric_1",
                automation_id="test_automation_123",
                call_duration=180.5,
                call_status="completed",
                sentiment_score=0.75,
                cost=0.45,
                created_at=datetime.utcnow()
            )
        ]
        mock_service_instance.get_vapi_call_metrics = AsyncMock(return_value=mock_metrics)
        mock_service.return_value = mock_service_instance

        # Make request
        response = client.get(
            "/api/monitoring/vapi-calls?limit=10",
            headers=auth_headers
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        mock_service_instance.get_vapi_call_metrics.assert_called_once()

    @patch('backend.routes.monitoring.get_current_user')
    def test_record_vapi_call_metrics_validation_error(self, mock_get_user, client, auth_headers, mock_current_user):
        """Test validation error for invalid VAPI call metrics."""
        mock_get_user.return_value = mock_current_user

        # Test data with missing required fields
        request_data = {
            "automation_id": "test_automation_123",
            # Missing call_duration and call_status
        }

        # Make request
        response = client.post(
            "/api/monitoring/vapi-calls",
            json=request_data,
            headers=auth_headers
        )

        # Should return validation error
        assert response.status_code == 422


class TestAutomationHealthEndpoints:
    """Test automation health API endpoints."""

    @patch('backend.routes.monitoring.get_current_user')
    @patch('backend.routes.monitoring.AutomationMonitoringService')
    def test_update_automation_health_success(self, mock_service, mock_get_user, client, auth_headers, mock_current_user):
        """Test successful automation health update."""
        # Setup mocks
        mock_get_user.return_value = mock_current_user
        mock_service_instance = Mock()
        mock_service_instance.update_automation_health = AsyncMock(return_value="health_id_123")
        mock_service.return_value = mock_service_instance

        # Test data
        request_data = {
            "automation_id": "test_automation_123",
            "campaign_id": "test_campaign_456",
            "status": "healthy",
            "error_count": 2,
            "success_rate": 95.5,
            "last_execution": datetime.utcnow().isoformat(),
            "performance_metrics": {"avg_response_time": 2.3}
        }

        # Make request
        response = client.post(
            "/api/monitoring/automation-health",
            json=request_data,
            headers=auth_headers
        )

        # Assertions
        assert response.status_code == 200
        assert response.json()["health_id"] == "health_id_123"
        mock_service_instance.update_automation_health.assert_called_once()

    @patch('backend.routes.monitoring.get_current_user')
    @patch('backend.routes.monitoring.AutomationMonitoringService')
    def test_get_automation_health_success(self, mock_service, mock_get_user, client, auth_headers, mock_current_user):
        """Test successful retrieval of automation health."""
        # Setup mocks
        mock_get_user.return_value = mock_current_user
        mock_service_instance = Mock()

        # Mock health data
        mock_health = [
            Mock(
                id="health_1",
                automation_id="test_automation_123",
                status="healthy",
                error_count=2,
                success_rate=95.5,
                last_execution=datetime.utcnow(),
                performance_metrics={}
            )
        ]
        mock_service_instance.get_automation_health = AsyncMock(return_value=mock_health)
        mock_service.return_value = mock_service_instance

        # Make request
        response = client.get(
            "/api/monitoring/automation-health?automation_id=test_automation_123",
            headers=auth_headers
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        mock_service_instance.get_automation_health.assert_called_once()


class TestCampaignPerformanceEndpoints:
    """Test campaign performance API endpoints."""

    @patch('backend.routes.monitoring.get_current_user')
    @patch('backend.routes.monitoring.AutomationMonitoringService')
    def test_get_campaign_performance_success(self, mock_service, mock_get_user, client, auth_headers, mock_current_user):
        """Test successful retrieval of campaign performance."""
        # Setup mocks
        mock_get_user.return_value = mock_current_user
        mock_service_instance = Mock()

        # Mock performance data
        mock_performance = [
            Mock(
                id="perf_1",
                campaign_id="test_campaign_456",
                total_calls=100,
                successful_calls=85,
                failed_calls=15,
                total_cost=45.0,
                avg_call_duration=180.0,
                success_rate=85.0,
                total_conversions=42,
                conversion_rate=42.0
            )
        ]
        mock_service_instance.get_campaign_performance = AsyncMock(return_value=mock_performance)
        mock_service.return_value = mock_service_instance

        # Make request
        response = client.get(
            "/api/monitoring/campaign-performance?campaign_id=test_campaign_456",
            headers=auth_headers
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        mock_service_instance.get_campaign_performance.assert_called_once()


class TestDashboardSummaryEndpoint:
    """Test dashboard summary API endpoint."""

    @patch('backend.routes.monitoring.get_current_user')
    @patch('backend.routes.monitoring.AutomationMonitoringService')
    def test_get_dashboard_summary_success(self, mock_service, mock_get_user, client, auth_headers, mock_current_user):
        """Test successful retrieval of dashboard summary."""
        # Setup mocks
        mock_get_user.return_value = mock_current_user
        mock_service_instance = Mock()

        # Mock data for different service calls
        mock_vapi_metrics = [
            Mock(call_duration=180, cost=0.45, sentiment_score=0.75),
            Mock(call_duration=120, cost=0.30, sentiment_score=0.60)
        ]
        mock_automation_health = [
            Mock(status="healthy"),
            Mock(status="warning"),
            Mock(status="healthy")
        ]
        mock_campaign_performance = [
            Mock(success_rate=85.0, total_conversions=42),
            Mock(success_rate=90.0, total_conversions=38)
        ]

        mock_service_instance.get_vapi_call_metrics = AsyncMock(return_value=mock_vapi_metrics)
        mock_service_instance.get_automation_health = AsyncMock(return_value=mock_automation_health)
        mock_service_instance.get_campaign_performance = AsyncMock(return_value=mock_campaign_performance)
        mock_service.return_value = mock_service_instance

        # Make request
        response = client.get(
            "/api/monitoring/dashboard-summary",
            headers=auth_headers
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "period" in data
        assert "vapi_metrics" in data
        assert "automation_health" in data
        assert "campaign_performance" in data

        # Check calculated metrics
        vapi_metrics = data["vapi_metrics"]
        assert vapi_metrics["total_calls"] == 2
        assert vapi_metrics["total_cost"] == 0.75
        assert vapi_metrics["avg_call_duration"] == 150.0

        automation_health = data["automation_health"]
        assert automation_health["total_automations"] == 3
        assert automation_health["healthy_automations"] == 2
        assert automation_health["health_percentage"] == 66.7


class TestWebhookEndpoint:
    """Test VAPI webhook endpoint."""

    @patch('backend.routes.monitoring.AutomationMonitoringService')
    def test_handle_vapi_webhook_success(self, mock_service, client):
        """Test successful VAPI webhook handling."""
        # Setup mocks
        mock_service_instance = Mock()
        mock_service_instance.record_vapi_call_metrics = AsyncMock(return_value="metric_id_123")
        mock_service.return_value = mock_service_instance

        # Test webhook data
        webhook_data = {
            "metadata": {
                "automation_id": "test_automation_123",
                "campaign_id": "test_campaign_456",
                "tenant_id": "test_tenant"
            },
            "duration": 180,
            "status": "completed",
            "transcript": "Customer called about claim",
            "cost": 0.45
        }

        # Make request
        response = client.post(
            "/api/monitoring/webhook/vapi-call",
            json=webhook_data
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processed"
        assert data["metrics_id"] == "metric_id_123"

    def test_handle_vapi_webhook_missing_automation_id(self, client):
        """Test VAPI webhook handling with missing automation_id."""
        # Test webhook data without automation_id
        webhook_data = {
            "metadata": {},
            "duration": 180,
            "status": "completed"
        }

        # Make request
        response = client.post(
            "/api/monitoring/webhook/vapi-call",
            json=webhook_data
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "skipped"
        assert data["reason"] == "missing automation_id"


class TestErrorHandling:
    """Test error handling in monitoring routes."""

    @patch('backend.routes.monitoring.get_current_user')
    @patch('backend.routes.monitoring.AutomationMonitoringService')
    def test_service_error_handling(self, mock_service, mock_get_user, client, auth_headers, mock_current_user):
        """Test service error handling."""
        # Setup mocks
        mock_get_user.return_value = mock_current_user
        mock_service_instance = Mock()
        mock_service_instance.record_vapi_call_metrics = AsyncMock(side_effect=Exception("Database error"))
        mock_service.return_value = mock_service_instance

        # Test data
        request_data = {
            "automation_id": "test_automation_123",
            "call_duration": 180.5,
            "call_status": "completed"
        }

        # Make request
        response = client.post(
            "/api/monitoring/vapi-calls",
            json=request_data,
            headers=auth_headers
        )

        # Should return internal server error
        assert response.status_code == 500
        assert "Failed to record VAPI call metrics" in response.json()["detail"]

    def test_authentication_required(self, client):
        """Test that authentication is required for protected endpoints."""
        # Test data
        request_data = {
            "automation_id": "test_automation_123",
            "call_duration": 180.5,
            "call_status": "completed"
        }

        # Make request without auth headers
        response = client.post(
            "/api/monitoring/vapi-calls",
            json=request_data
        )

        # Should return unauthorized
        assert response.status_code == 401


class TestParameterValidation:
    """Test parameter validation in monitoring routes."""

    @patch('backend.routes.monitoring.get_current_user')
    def test_date_parameter_validation(self, mock_get_user, client, auth_headers, mock_current_user):
        """Test date parameter validation."""
        mock_get_user.return_value = mock_current_user

        # Test with invalid date format
        response = client.get(
            "/api/monitoring/vapi-calls?start_date=invalid-date",
            headers=auth_headers
        )

        # Should handle invalid date gracefully or return error
        assert response.status_code in [400, 422, 500]

    @patch('backend.routes.monitoring.get_current_user')
    def test_limit_parameter_validation(self, mock_get_user, client, auth_headers, mock_current_user):
        """Test limit parameter validation."""
        mock_get_user.return_value = mock_current_user

        # Test with negative limit
        response = client.get(
            "/api/monitoring/vapi-calls?limit=-1",
            headers=auth_headers
        )

        # Should handle invalid limit gracefully
        assert response.status_code in [400, 422]


if __name__ == "__main__":
    pytest.main([__file__])