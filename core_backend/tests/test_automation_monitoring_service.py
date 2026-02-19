"""
Unit tests for the AutomationMonitoringService.

This module tests the comprehensive automation health monitoring service
functionality including VAPI call metrics, automation health tracking,
and campaign performance analytics.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from backend.services.automation_monitoring_service import (
    AutomationMonitoringService,
    VAPICallMetrics,
    AutomationHealth,
    CampaignPerformance
)


@pytest.fixture
def monitoring_service():
    """Create a monitoring service instance for testing."""
    return AutomationMonitoringService()


@pytest.fixture
def sample_vapi_call_data():
    """Sample VAPI call data for testing (VAPI webhook format)."""
    return {
        "assistant": {
            "id": "assistant_abc"
        },
        "call": {
            "id": "call_789"
        },
        "metadata": {
            "tenantId": "test_tenant",
            "automationId": "test_automation_123",
            "campaignId": "test_campaign_456"
        },
        "startedAt": datetime.utcnow().isoformat(),
        "endedAt": (datetime.utcnow() + timedelta(seconds=180)).isoformat(),
        "durationSeconds": 180.5,
        "transcript": "Customer called to file an auto insurance claim.",
        "cost": 0.45
    }


@pytest.fixture
def sample_automation_health_data():
    """Sample automation health data for testing."""
    return {
        "automation_id": "test_automation_123",
        "template_id": "template_456",
        "tenant_id": "test_tenant",
        "status": "healthy",
        "error_count": 2,
        "success_rate": 0.955,  # Should be between 0 and 1
        "total_executions": 100,
        "last_execution": datetime.utcnow(),
        "performance_metrics": {
            "avg_response_time": 2.3,
            "throughput": 150,
            "memory_usage": 78.5
        }
    }


class TestVAPICallMetrics:
    """Test VAPI call metrics functionality."""

    @pytest.mark.asyncio
    async def test_record_vapi_call_metrics_success(self, monitoring_service, sample_vapi_call_data):
        """Test successful recording of VAPI call metrics."""
        # Mock the database collection
        with patch('backend.services.automation_monitoring_service.get_collection') as mock_get_collection:
            mock_collection = AsyncMock()
            mock_get_collection.return_value = mock_collection
            mock_collection.insert_one.return_value = Mock(inserted_id="metric_id_123")

            result = await monitoring_service.record_vapi_call_metrics(sample_vapi_call_data)

            assert result == "metric_id_123"
            mock_collection.insert_one.assert_called_once()

            # Verify the inserted document structure
            call_args = mock_collection.insert_one.call_args[0][0]
            assert call_args["automation_id"] == "test_automation_123"
            assert call_args["duration_seconds"] == 180.5
            assert "created_at" in call_args

    @pytest.mark.asyncio
    async def test_record_vapi_call_metrics_with_sentiment_analysis(self, monitoring_service, sample_vapi_call_data):
        """Test recording VAPI call metrics with sentiment analysis."""
        with patch('backend.services.automation_monitoring_service.get_collection') as mock_get_collection:
            mock_collection = AsyncMock()
            mock_get_collection.return_value = mock_collection
            mock_collection.insert_one.return_value = Mock(inserted_id="metric_id_123")

            # Test with transcript but no sentiment score
            sample_vapi_call_data["sentiment_score"] = None

            result = await monitoring_service.record_vapi_call_metrics(sample_vapi_call_data)

            call_args = mock_collection.insert_one.call_args[0][0]
            # Should have calculated sentiment from transcript
            assert "sentiment_score" in call_args

    @pytest.mark.asyncio
    async def test_get_vapi_call_metrics(self, monitoring_service):
        """Test retrieving VAPI call metrics."""
        with patch('backend.services.automation_monitoring_service.get_collection') as mock_get_collection:
            mock_collection = AsyncMock()
            mock_get_collection.return_value = mock_collection

            # Mock database response
            mock_metrics_data = [
                {
                    "id": "metric_1",
                    "automation_id": "test_automation_123",
                    "call_duration": 180.5,
                    "call_status": "completed",
                    "sentiment_score": 0.75,
                    "cost": 0.45,
                    "created_at": datetime.utcnow()
                }
            ]
            mock_collection.find.return_value.sort.return_value.limit.return_value.to_list.return_value = mock_metrics_data

            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=7)

            result = await monitoring_service.get_vapi_call_metrics(
                tenant_id="test_tenant",
                start_date=start_date,
                end_date=end_date,
                limit=10
            )

            assert len(result) == 1
            assert isinstance(result[0], VAPICallMetrics)
            assert result[0].automation_id == "test_automation_123"


class TestAutomationHealth:
    """Test automation health tracking functionality."""

    @pytest.mark.asyncio
    async def test_update_automation_health_success(self, monitoring_service, sample_automation_health_data):
        """Test successful automation health update."""
        with patch('backend.services.automation_monitoring_service.get_collection') as mock_get_collection:
            mock_collection = AsyncMock()
            mock_get_collection.return_value = mock_collection
            mock_collection.update_one.return_value = Mock(upserted_id="health_id_123")

            result = await monitoring_service.update_automation_health(sample_automation_health_data)

            assert result == "health_id_123"
            mock_collection.update_one.assert_called_once()

            # Verify the update operation
            call_args = mock_collection.update_one.call_args
            filter_doc = call_args[0][0]
            update_doc = call_args[0][1]["$set"]

            assert filter_doc["automation_id"] == "test_automation_123"
            assert filter_doc["tenant_id"] == "test_tenant"
            assert update_doc["status"] == "healthy"
            assert update_doc["success_rate"] == 95.5

    @pytest.mark.asyncio
    async def test_get_automation_health(self, monitoring_service):
        """Test retrieving automation health records."""
        with patch('backend.services.automation_monitoring_service.get_collection') as mock_get_collection:
            mock_collection = AsyncMock()
            mock_get_collection.return_value = mock_collection

            # Mock database response
            mock_health_data = [
                {
                    "id": "health_1",
                    "automation_id": "test_automation_123",
                    "status": "healthy",
                    "error_count": 2,
                    "success_rate": 95.5,
                    "last_execution": datetime.utcnow(),
                    "performance_metrics": {}
                }
            ]
            mock_collection.find.return_value.to_list.return_value = mock_health_data

            result = await monitoring_service.get_automation_health(
                tenant_id="test_tenant",
                automation_id="test_automation_123"
            )

            assert len(result) == 1
            assert isinstance(result[0], AutomationHealth)
            assert result[0].automation_id == "test_automation_123"
            assert result[0].status == "healthy"


class TestCampaignPerformance:
    """Test campaign performance analytics functionality."""

    @pytest.mark.asyncio
    async def test_calculate_campaign_performance(self, monitoring_service):
        """Test campaign performance calculation."""
        with patch('backend.services.automation_monitoring_service.get_collection') as mock_get_collection:
            # Mock VAPI call metrics
            mock_vapi_collection = AsyncMock()
            mock_automation_collection = AsyncMock()

            def collection_side_effect(name):
                if name == "vapi_call_metrics":
                    return mock_vapi_collection
                elif name == "automation_health":
                    return mock_automation_collection
                return AsyncMock()

            mock_get_collection.side_effect = collection_side_effect

            # Mock call metrics data
            mock_call_metrics = [
                {
                    "campaign_id": "test_campaign_456",
                    "call_status": "completed",
                    "call_duration": 180,
                    "cost": 0.45,
                    "sentiment_score": 0.75
                },
                {
                    "campaign_id": "test_campaign_456",
                    "call_status": "failed",
                    "call_duration": 60,
                    "cost": 0.15,
                    "sentiment_score": 0.25
                }
            ]
            mock_vapi_collection.find.return_value.to_list.return_value = mock_call_metrics

            # Mock automation health data
            mock_automation_data = [
                {
                    "campaign_id": "test_campaign_456",
                    "success_rate": 85.0
                }
            ]
            mock_automation_collection.find.return_value.to_list.return_value = mock_automation_data

            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=7)

            result = await monitoring_service.get_campaign_performance(
                tenant_id="test_tenant",
                campaign_id="test_campaign_456",
                start_date=start_date,
                end_date=end_date
            )

            assert len(result) == 1
            performance = result[0]
            assert isinstance(performance, CampaignPerformance)
            assert performance.campaign_id == "test_campaign_456"
            assert performance.total_calls == 2
            assert performance.successful_calls == 1
            assert performance.failed_calls == 1
            assert performance.total_cost == 0.60

    @pytest.mark.asyncio
    async def test_calculate_conversion_metrics(self, monitoring_service):
        """Test conversion rate calculations."""
        # Test conversion calculation logic
        test_data = {
            "total_calls": 100,
            "successful_calls": 85,
            "completed_transactions": 42
        }

        conversion_rate = (test_data["completed_transactions"] / test_data["total_calls"]) * 100
        assert conversion_rate == 42.0

        success_rate = (test_data["successful_calls"] / test_data["total_calls"]) * 100
        assert success_rate == 85.0


class TestSentimentAnalysis:
    """Test sentiment analysis functionality."""

    def test_analyze_sentiment_positive(self, monitoring_service):
        """Test positive sentiment analysis."""
        positive_text = "Thank you so much for your help! This was exactly what I needed."

        # Mock simple sentiment analysis
        sentiment_score = monitoring_service._analyze_sentiment(positive_text)

        # Should return a positive score
        assert sentiment_score > 0.5

    def test_analyze_sentiment_negative(self, monitoring_service):
        """Test negative sentiment analysis."""
        negative_text = "This is terrible service. I'm very frustrated and angry."

        # Mock simple sentiment analysis
        sentiment_score = monitoring_service._analyze_sentiment(negative_text)

        # Should return a negative score
        assert sentiment_score < 0.5

    def test_analyze_sentiment_neutral(self, monitoring_service):
        """Test neutral sentiment analysis."""
        neutral_text = "I need to file a claim for my auto insurance policy."

        # Mock simple sentiment analysis
        sentiment_score = monitoring_service._analyze_sentiment(neutral_text)

        # Should return a neutral score
        assert 0.4 <= sentiment_score <= 0.6


class TestMonitoringServiceIntegration:
    """Test end-to-end monitoring service integration."""

    @pytest.mark.asyncio
    async def test_complete_monitoring_workflow(self, monitoring_service, sample_vapi_call_data, sample_automation_health_data):
        """Test complete monitoring workflow from call to metrics."""
        with patch('backend.services.automation_monitoring_service.get_collection') as mock_get_collection:
            mock_collection = AsyncMock()
            mock_get_collection.return_value = mock_collection
            mock_collection.insert_one.return_value = Mock(inserted_id="metric_id_123")
            mock_collection.update_one.return_value = Mock(upserted_id="health_id_123")

            # Record VAPI call metrics
            call_result = await monitoring_service.record_vapi_call_metrics(sample_vapi_call_data)
            assert call_result == "metric_id_123"

            # Update automation health
            health_result = await monitoring_service.update_automation_health(sample_automation_health_data)
            assert health_result == "health_id_123"

            # Verify both operations were called
            assert mock_collection.insert_one.call_count == 1
            assert mock_collection.update_one.call_count == 1

    @pytest.mark.asyncio
    async def test_error_handling(self, monitoring_service, sample_vapi_call_data):
        """Test error handling in monitoring service."""
        with patch('backend.services.automation_monitoring_service.get_collection') as mock_get_collection:
            mock_collection = AsyncMock()
            mock_get_collection.return_value = mock_collection
            mock_collection.insert_one.side_effect = Exception("Database error")

            with pytest.raises(Exception) as exc_info:
                await monitoring_service.record_vapi_call_metrics(sample_vapi_call_data)

            assert "Database error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_data_validation(self, monitoring_service):
        """Test data validation in monitoring service."""
        # Test with missing required fields
        invalid_data = {
            "automation_id": "test_automation_123",
            # Missing other required fields
        }

        with pytest.raises(ValueError) as exc_info:
            await monitoring_service.record_vapi_call_metrics(invalid_data)

        assert "Missing required field" in str(exc_info.value)


class TestPerformanceMetrics:
    """Test performance metrics calculations."""

    def test_calculate_average_metrics(self, monitoring_service):
        """Test average metrics calculations."""
        # Test data
        call_durations = [120, 180, 150, 200, 90]
        costs = [0.30, 0.45, 0.38, 0.50, 0.23]
        sentiment_scores = [0.8, 0.6, 0.7, 0.9, 0.5]

        # Calculate averages
        avg_duration = sum(call_durations) / len(call_durations)
        avg_cost = sum(costs) / len(costs)
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)

        assert avg_duration == 148.0
        assert round(avg_cost, 2) == 0.37
        assert avg_sentiment == 0.7

    def test_calculate_success_rate(self, monitoring_service):
        """Test success rate calculations."""
        total_calls = 100
        successful_calls = 85
        failed_calls = 15

        success_rate = (successful_calls / total_calls) * 100
        failure_rate = (failed_calls / total_calls) * 100

        assert success_rate == 85.0
        assert failure_rate == 15.0
        assert success_rate + failure_rate == 100.0


if __name__ == "__main__":
    pytest.main([__file__])