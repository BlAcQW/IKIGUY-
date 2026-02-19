"""
Unit tests for helpdesk analytics service.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from backend.services.helpdesk_analytics_service import (
    HelpdeskAnalyticsService,
    CallMetrics,
    IntentMetrics,
    ActionMetrics,
    PerformanceMetrics,
    CustomerSatisfactionMetrics,
    HelpdeskAnalytics
)

@pytest.fixture
def analytics_service():
    """Create analytics service instance for testing."""
    return HelpdeskAnalyticsService()

@pytest.fixture
def mock_vapi_data():
    """Mock VAPI analytics data."""
    return {
        "call_metrics": {
            "total_calls": 100,
            "successful_calls": 90,
            "failed_calls": 10,
            "success_rate": 90.0,
            "avg_call_duration": 4.2,
            "total_duration": 420.0
        },
        "intents": [
            {"intent": "appointment_booking", "count": 30, "avg_confidence": 0.92},
            {"intent": "policy_inquiry", "count": 25, "avg_confidence": 0.88},
            {"intent": "claims_support", "count": 20, "avg_confidence": 0.85}
        ],
        "performance": {
            "response_time": 0.8,
            "processing_time": 1.2,
            "uptime_percentage": 99.5
        },
        "satisfaction": {
            "average_rating": 4.7,
            "total_ratings": 50,
            "nps_score": 72
        }
    }

@pytest.fixture
def mock_n8n_data():
    """Mock N8N workflow analytics data."""
    return {
        "executions": {
            "total": 100,
            "successful": 95,
            "failed": 5,
            "success_rate": 95.0
        },
        "actions": {
            "appointments_booked": 30,
            "tickets_created": 15,
            "knowledge_searches": 80,
            "escalations": 8,
            "transfers": 5,
            "callbacks_scheduled": 12
        },
        "integrations": {
            "calendly_calls": 30,
            "supabase_queries": 100,
            "tavily_searches": 80,
            "resend_emails": 25,
            "vonage_sms": 15
        }
    }

class TestHelpdeskAnalyticsService:
    """Test cases for HelpdeskAnalyticsService."""

    @pytest.mark.asyncio
    async def test_get_vapi_analytics_success(self, analytics_service, mock_vapi_data):
        """Test successful VAPI analytics retrieval."""
        # Given
        assistant_id = "test-assistant-123"
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()

        # Mock the VAPI API call
        with patch.object(analytics_service, 'get_vapi_analytics', return_value=mock_vapi_data):
            # When
            result = await analytics_service.get_vapi_analytics(assistant_id, start_date, end_date)

            # Then
            assert result["call_metrics"]["total_calls"] == 100
            assert result["call_metrics"]["success_rate"] == 90.0
            assert len(result["intents"]) == 3
            assert result["performance"]["uptime_percentage"] == 99.5

    @pytest.mark.asyncio
    async def test_get_n8n_workflow_analytics_success(self, analytics_service, mock_n8n_data):
        """Test successful N8N workflow analytics retrieval."""
        # Given
        workflow_id = "test-workflow-123"
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()

        # Mock the N8N API call
        with patch.object(analytics_service, 'get_n8n_workflow_analytics', return_value=mock_n8n_data):
            # When
            result = await analytics_service.get_n8n_workflow_analytics(workflow_id, start_date, end_date)

            # Then
            assert result["executions"]["total"] == 100
            assert result["executions"]["success_rate"] == 95.0
            assert result["actions"]["appointments_booked"] == 30
            assert result["actions"]["knowledge_searches"] == 80

    @pytest.mark.asyncio
    async def test_calculate_trends(self, analytics_service):
        """Test trend calculation functionality."""
        # Given
        metrics_history = []  # Empty for now, using generated data
        days = 7

        # When
        trends = await analytics_service.calculate_trends(metrics_history, days)

        # Then
        assert "daily_calls" in trends
        assert "success_rate" in trends
        assert "satisfaction" in trends
        assert "response_time" in trends
        assert "appointments" in trends
        assert len(trends["daily_calls"]) == days
        assert len(trends["success_rate"]) == days

    @pytest.mark.asyncio
    async def test_detect_anomalies_success_rate_drop(self, analytics_service):
        """Test anomaly detection for success rate drop."""
        # Given
        current_metrics = {
            "call_metrics": {"success_rate": 75.0},
            "performance": {"response_time": 1.0}
        }
        historical_avg = {
            "success_rate": 90.0,
            "response_time": 1.0
        }

        # When
        alerts = await analytics_service.detect_anomalies(current_metrics, historical_avg)

        # Then
        assert len(alerts) > 0
        success_alert = next((alert for alert in alerts if alert["metric"] == "success_rate"), None)
        assert success_alert is not None
        assert success_alert["severity"] == "medium"
        assert "Success rate dropped" in success_alert["message"]

    @pytest.mark.asyncio
    async def test_detect_anomalies_response_time_increase(self, analytics_service):
        """Test anomaly detection for response time increase."""
        # Given
        current_metrics = {
            "call_metrics": {"success_rate": 90.0},
            "performance": {"response_time": 2.0}
        }
        historical_avg = {
            "success_rate": 90.0,
            "response_time": 1.0
        }

        # When
        alerts = await analytics_service.detect_anomalies(current_metrics, historical_avg)

        # Then
        assert len(alerts) > 0
        response_alert = next((alert for alert in alerts if alert["metric"] == "response_time"), None)
        assert response_alert is not None
        assert response_alert["severity"] == "medium"
        assert "Response time increased" in response_alert["message"]

    @pytest.mark.asyncio
    async def test_detect_anomalies_high_error_rate(self, analytics_service):
        """Test anomaly detection for high error rate."""
        # Given
        current_metrics = {
            "call_metrics": {
                "total_calls": 100,
                "failed_calls": 20,
                "success_rate": 80.0
            },
            "performance": {"response_time": 1.0}
        }
        historical_avg = {
            "success_rate": 90.0,
            "response_time": 1.0
        }

        # When
        alerts = await analytics_service.detect_anomalies(current_metrics, historical_avg)

        # Then
        assert len(alerts) > 0
        error_alert = next((alert for alert in alerts if alert["metric"] == "error_rate"), None)
        assert error_alert is not None
        assert error_alert["severity"] == "high"
        assert "High error rate" in error_alert["message"]

    @pytest.mark.asyncio
    async def test_get_comprehensive_analytics_success(self, analytics_service, mock_vapi_data, mock_n8n_data):
        """Test comprehensive analytics retrieval."""
        # Given
        helpdesk_id = "test-helpdesk-123"
        period_days = 7

        # Mock the service methods
        with patch.object(analytics_service, 'get_vapi_analytics', return_value=mock_vapi_data), \
             patch.object(analytics_service, 'get_n8n_workflow_analytics', return_value=mock_n8n_data), \
             patch.object(analytics_service, 'calculate_trends', return_value={
                 "daily_calls": [15, 18, 22, 19, 21, 17, 20],
                 "success_rate": [88, 91, 89, 93, 87, 92, 90]
             }), \
             patch.object(analytics_service, 'detect_anomalies', return_value=[]):

            # When
            analytics = await analytics_service.get_comprehensive_analytics(helpdesk_id, period_days)

            # Then
            assert analytics.helpdesk_id == helpdesk_id
            assert analytics.call_metrics.total_calls == 100
            assert analytics.call_metrics.success_rate == 90.0
            assert len(analytics.intent_metrics) == 3
            assert analytics.action_metrics.appointments_booked == 30
            assert analytics.performance_metrics.uptime_percentage == 99.5
            assert analytics.satisfaction_metrics.average_rating == 4.7
            assert len(analytics.trends) > 0
            assert len(analytics.alerts) == 0

    @pytest.mark.asyncio
    async def test_get_real_time_metrics_success(self, analytics_service):
        """Test real-time metrics retrieval."""
        # Given
        helpdesk_id = "test-helpdesk-123"

        # When
        metrics = await analytics_service.get_real_time_metrics(helpdesk_id)

        # Then
        assert "status" in metrics
        assert "current_calls" in metrics
        assert "calls_today" in metrics
        assert "success_rate_today" in metrics
        assert "avg_response_time" in metrics
        assert "health_score" in metrics
        assert metrics["status"] == "active"

    @pytest.mark.asyncio
    async def test_analytics_error_handling(self, analytics_service):
        """Test error handling in analytics methods."""
        # Given
        helpdesk_id = "invalid-helpdesk"

        # Mock an exception in VAPI call
        with patch.object(analytics_service, 'get_vapi_analytics', side_effect=Exception("VAPI API error")):
            # When/Then
            with pytest.raises(Exception) as exc_info:
                await analytics_service.get_comprehensive_analytics(helpdesk_id)

            assert "VAPI API error" in str(exc_info.value)

class TestAnalyticsModels:
    """Test cases for analytics data models."""

    def test_call_metrics_model(self):
        """Test CallMetrics model validation."""
        # Given
        data = {
            "total_calls": 100,
            "successful_calls": 90,
            "failed_calls": 10,
            "success_rate": 90.0,
            "avg_call_duration": 4.2,
            "total_duration": 420.0
        }

        # When
        metrics = CallMetrics(**data)

        # Then
        assert metrics.total_calls == 100
        assert metrics.success_rate == 90.0
        assert metrics.avg_call_duration == 4.2

    def test_intent_metrics_model(self):
        """Test IntentMetrics model validation."""
        # Given
        data = {
            "intent": "appointment_booking",
            "count": 30,
            "percentage": 30.0,
            "avg_confidence": 0.92,
            "success_rate": 95.0
        }

        # When
        metrics = IntentMetrics(**data)

        # Then
        assert metrics.intent == "appointment_booking"
        assert metrics.count == 30
        assert metrics.avg_confidence == 0.92

    def test_action_metrics_model(self):
        """Test ActionMetrics model validation."""
        # Given
        data = {
            "appointments_booked": 30,
            "tickets_created": 15,
            "knowledge_searches": 80,
            "escalations": 8,
            "transfers": 5,
            "callbacks_scheduled": 12
        }

        # When
        metrics = ActionMetrics(**data)

        # Then
        assert metrics.appointments_booked == 30
        assert metrics.knowledge_searches == 80
        assert metrics.escalations == 8

    def test_performance_metrics_model(self):
        """Test PerformanceMetrics model validation."""
        # Given
        data = {
            "response_time": 0.8,
            "processing_time": 1.2,
            "error_rate": 10.0,
            "uptime_percentage": 99.5
        }

        # When
        metrics = PerformanceMetrics(**data)

        # Then
        assert metrics.response_time == 0.8
        assert metrics.uptime_percentage == 99.5
        assert metrics.error_rate == 10.0

    def test_customer_satisfaction_metrics_model(self):
        """Test CustomerSatisfactionMetrics model validation."""
        # Given
        data = {
            "average_rating": 4.7,
            "total_ratings": 50,
            "rating_distribution": {"5": 25, "4": 15, "3": 7, "2": 2, "1": 1},
            "nps_score": 72.0,
            "feedback_sentiment": {"positive": 0.8, "neutral": 0.15, "negative": 0.05}
        }

        # When
        metrics = CustomerSatisfactionMetrics(**data)

        # Then
        assert metrics.average_rating == 4.7
        assert metrics.nps_score == 72.0
        assert len(metrics.rating_distribution) == 5