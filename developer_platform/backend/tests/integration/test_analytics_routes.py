"""
Integration tests for Analytics routes.

Tests the analytics-related API endpoints using the DeveloperAnalyticsService.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import json

from main import app

client = TestClient(app)

class TestAnalyticsRoutes:
    """Test cases for Analytics routes."""
    
    @pytest.fixture
    def mock_api_key(self):
        """Mock API key for testing."""
        return "test_api_key_123"
    
    def test_create_dashboard_success(self, mock_api_key):
        """Test successful dashboard creation."""
        with patch('routes.analytics_routes.analytics_service.create_dashboard', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = {"dashboard_id": "dashboard_123", "name": "Test Dashboard"}
            
            response = client.post(
                "/v1/analytics/dashboard/create",
                headers={"x-api-key": mock_api_key},
                json={
                    "dashboard_config": {"name": "Test Dashboard"},
                    "metrics": [{"name": "test_metric", "value": 100}]
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["dashboard_id"] == "dashboard_123"
    
    def test_generate_report_success(self, mock_api_key):
        """Test successful report generation."""
        with patch('routes.analytics_routes.analytics_service.generate_report', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = {"report_id": "report_123", "type": "summary"}
            
            response = client.post(
                "/v1/analytics/report/generate",
                headers={"x-api-key": mock_api_key},
                json={
                    "report_type": "summary",
                    "data": {"metric": "calls", "value": 1000}
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["report_id"] == "report_123"
    
    def test_track_kpi_success(self, mock_api_key):
        """Test successful KPI tracking."""
        with patch('routes.analytics_routes.analytics_service.track_kpi', new_callable=AsyncMock) as mock_track:
            mock_track.return_value = {"kpi_id": "kpi_123", "value": 95.5}
            
            response = client.post(
                "/v1/analytics/kpi/track",
                headers={"x-api-key": mock_api_key},
                json={
                    "kpi_name": "success_rate",
                    "value": 95.5,
                    "category": "performance"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["kpi_id"] == "kpi_123"
    
    def test_predict_call_outcome_success(self, mock_api_key):
        """Test successful call outcome prediction."""
        with patch('routes.analytics_routes.analytics_service.predict_call_outcome', new_callable=AsyncMock) as mock_predict:
            mock_predict.return_value = {"prediction": "success", "confidence": 0.85}
            
            response = client.post(
                "/v1/analytics/prediction/call-outcome",
                headers={"x-api-key": mock_api_key},
                json={
                    "call_data": {"duration": 300, "customer_type": "premium"}
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["prediction"] == "success"
    
    def test_get_analytics_config_success(self, mock_api_key):
        """Test successful analytics config retrieval."""
        with patch('routes.analytics_routes.analytics_service.get_developer_analytics_config', new_callable=AsyncMock) as mock_config:
            mock_config.return_value = {"analytics_enabled": True, "reports_enabled": True}
            
            response = client.get(
                "/v1/analytics/config",
                headers={"x-api-key": mock_api_key}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["analytics_enabled"] is True
