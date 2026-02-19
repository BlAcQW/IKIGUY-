"""
Tests for Enhanced Automation Monitoring Service with Vonage Integration

Tests the consolidated monitoring service that integrates VAPI call metrics
with Vonage cost tracking for comprehensive automation monitoring.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import json

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from backend.services.automation_monitoring_service import (
    AutomationMonitoringService,
    VAPICallMetrics,
    AutomationHealth,
    CampaignPerformance,
    automation_monitoring_service
)
from backend.services.vonage_cost_monitoring_service import VonageCostRecord, VonageServiceType


class TestEnhancedAutomationMonitoring:
    """Test suite for enhanced automation monitoring with Vonage integration."""

    @pytest.fixture
    def monitoring_service(self):
        """Create monitoring service instance for testing."""
        return AutomationMonitoringService()

    @pytest.fixture
    def sample_vapi_call_data(self):
        """Sample VAPI call data for testing."""
        return {
            "call": {
                "id": "test_call_123",
                "phoneNumber": "+12345678901"
            },
            "assistant": {
                "id": "assistant_456"
            },
            "metadata": {
                "tenantId": "test_tenant",
                "automationId": "automation_789"
            },
            "startedAt": "2025-09-23T01:00:00.000Z",
            "endedAt": "2025-09-23T01:05:30.000Z",
            "durationSeconds": 330,
            "cost": 0.25,
            "costBreakdown": {
                "model": 0.15,
                "transcription": 0.05,
                "synthesis": 0.05
            },
            "transcript": "Test conversation transcript",
            "toolCalls": [
                {"function": {"name": "search_medical_providers"}},
                {"function": {"name": "book_appointment"}}
            ],
            "analysis": {
                "structuredData": {
                    "sentiment": "positive",
                    "score": 8
                }
            },
            "interruptionsCount": 2,
            "silenceDuration": 5.5
        }

    @pytest.fixture
    def sample_vonage_cost_record(self):
        """Sample Vonage cost record for testing."""
        return VonageCostRecord(
            service_type=VonageServiceType.VOICE_CALL,
            cost_amount=Decimal("0.066"),
            currency="USD",
            timestamp=datetime.now(timezone.utc),
            transaction_id="vonage_tx_123",
            phone_number="+12345678901",
            duration=330,
            vapi_call_id="test_call_123",
            metadata={"source": "vapi_integration", "estimated": True}
        )

    @pytest.mark.asyncio
    async def test_record_vapi_call_metrics_with_vonage_integration(self, monitoring_service, sample_vapi_call_data, sample_vonage_cost_record):
        """Test recording VAPI call metrics with Vonage cost integration."""

        # Mock Vonage service
        with patch('backend.services.automation_monitoring_service.get_vonage_cost_service') as mock_vonage_service:
            mock_service = AsyncMock()
            mock_service.track_vapi_call_cost.return_value = sample_vonage_cost_record
            mock_vonage_service.return_value = mock_service

            # Mock MongoDB collection
            with patch.object(monitoring_service, 'metrics_collection') as mock_collection:
                mock_collection.insert_one.return_value = AsyncMock(inserted_id="test_record_id")

                # Mock health update and alert check
                with patch.object(monitoring_service, '_update_automation_health') as mock_health_update, \
                     patch.object(monitoring_service, '_check_call_quality_alerts') as mock_alerts:

                    # Test the method
                    result = await monitoring_service.record_vapi_call_metrics(sample_vapi_call_data)

                    # Verify Vonage service was called
                    mock_service.track_vapi_call_cost.assert_called_once_with(
                        vapi_call_id="test_call_123",
                        phone_number="+12345678901",
                        duration=330
                    )

                    # Verify metrics were stored
                    mock_collection.insert_one.assert_called_once()
                    call_args = mock_collection.insert_one.call_args[0][0]

                    # Verify Vonage integration fields
                    assert call_args["vonage_transaction_id"] == "vonage_tx_123"
                    assert call_args["estimated_vonage_cost"] == 0.066
                    assert call_args["vonage_cost_record"] is not None

                    # Verify basic call metrics
                    assert call_args["call_id"] == "test_call_123"
                    assert call_args["total_cost"] == 0.25
                    assert call_args["duration_seconds"] == 330

                    assert result == "test_record_id"

    @pytest.mark.asyncio
    async def test_record_vapi_call_metrics_without_vonage_data(self, monitoring_service, sample_vapi_call_data):
        """Test recording VAPI call metrics when Vonage tracking fails."""

        # Remove phone number to test without Vonage tracking
        incomplete_call_data = sample_vapi_call_data.copy()
        del incomplete_call_data["call"]["phoneNumber"]

        with patch.object(monitoring_service, 'metrics_collection') as mock_collection:
            mock_collection.insert_one.return_value = AsyncMock(inserted_id="test_record_id")

            with patch.object(monitoring_service, '_update_automation_health'), \
                 patch.object(monitoring_service, '_check_call_quality_alerts'):

                result = await monitoring_service.record_vapi_call_metrics(incomplete_call_data)

                # Verify metrics were stored without Vonage data
                call_args = mock_collection.insert_one.call_args[0][0]
                assert call_args["vonage_transaction_id"] is None
                assert call_args["estimated_vonage_cost"] is None
                assert call_args["call_id"] == "test_call_123"

    @pytest.mark.asyncio
    async def test_update_vonage_costs_from_api(self, monitoring_service, sample_vonage_cost_record):
        """Test updating actual Vonage costs from Vonage API."""

        start_date = datetime.now(timezone.utc) - timedelta(days=1)
        end_date = datetime.now(timezone.utc)

        with patch('backend.services.automation_monitoring_service.get_vonage_cost_service') as mock_vonage_service:
            mock_service = AsyncMock()
            mock_service.fetch_vonage_costs.return_value = [sample_vonage_cost_record]
            mock_vonage_service.return_value = mock_service

            with patch.object(monitoring_service, 'metrics_collection') as mock_collection:
                mock_collection.update_one.return_value = AsyncMock(modified_count=1)

                result = await monitoring_service.update_vonage_costs_from_api(start_date, end_date)

                # Verify Vonage API was called
                mock_service.fetch_vonage_costs.assert_called_once_with(start_date, end_date)

                # Verify database update
                mock_collection.update_one.assert_called_once()
                update_query, update_data = mock_collection.update_one.call_args[0]

                assert update_query["call_id"] == "test_call_123"
                assert update_data["$set"]["actual_vonage_cost"] == 0.066

                assert result == 1

    @pytest.mark.asyncio
    async def test_get_cost_summary_with_vonage(self, monitoring_service):
        """Test comprehensive cost summary with Vonage integration."""

        tenant_id = "test_tenant"
        start_date = datetime.now(timezone.utc) - timedelta(days=7)
        end_date = datetime.now(timezone.utc)

        # Mock call data with Vonage costs
        mock_calls = [
            {
                "total_cost": 0.25,
                "estimated_vonage_cost": 0.066,
                "actual_vonage_cost": 0.065
            },
            {
                "total_cost": 0.30,
                "estimated_vonage_cost": 0.055,
                "actual_vonage_cost": None
            }
        ]

        with patch.object(monitoring_service, 'metrics_collection') as mock_collection:
            mock_cursor = AsyncMock()
            mock_cursor.to_list.return_value = mock_calls
            mock_collection.find.return_value = mock_cursor

            with patch('backend.services.automation_monitoring_service.get_vonage_cost_service') as mock_vonage_service:
                mock_service = AsyncMock()
                mock_summary = Mock()
                mock_summary.cost_breakdown = {"voice_call": Decimal("0.12")}
                mock_service.get_cost_summary.return_value = mock_summary
                mock_vonage_service.return_value = mock_service

                result = await monitoring_service.get_cost_summary_with_vonage(tenant_id, start_date, end_date)

                # Verify cost calculations
                assert result["vapi_costs"]["total_vapi_cost"] == 0.55  # 0.25 + 0.30
                assert result["vapi_costs"]["total_calls"] == 2

                assert result["vonage_costs"]["estimated_costs"] == 0.121  # 0.066 + 0.055
                assert result["vonage_costs"]["actual_costs"] == 0.065
                assert result["vonage_costs"]["total_vonage_cost"] == 0.065  # Use actual where available

                assert result["combined_metrics"]["total_cost"] == 0.615  # 0.55 + 0.065
                assert result["combined_metrics"]["cost_per_call"] == 0.3075  # 0.615 / 2

    @pytest.mark.asyncio
    async def test_get_high_cost_calls(self, monitoring_service):
        """Test retrieving high-cost calls for analysis."""

        tenant_id = "test_tenant"
        cost_threshold = 0.50

        mock_high_cost_calls = [
            {
                "_id": "call_1",
                "call_id": "high_cost_call_1",
                "total_cost": 0.45,
                "actual_vonage_cost": 0.15,
                "combined_cost": 0.60
            },
            {
                "_id": "call_2",
                "call_id": "high_cost_call_2",
                "total_cost": 0.40,
                "estimated_vonage_cost": 0.12,
                "combined_cost": 0.52
            }
        ]

        with patch.object(monitoring_service, 'metrics_collection') as mock_collection:
            mock_cursor = AsyncMock()
            mock_cursor.to_list.return_value = mock_high_cost_calls
            mock_collection.aggregate.return_value = mock_cursor

            result = await monitoring_service.get_high_cost_calls(tenant_id, cost_threshold, limit=10)

            # Verify aggregation pipeline was called
            mock_collection.aggregate.assert_called_once()
            pipeline = mock_collection.aggregate.call_args[0][0]

            # Verify pipeline structure
            assert pipeline[0]["$match"]["tenant_id"] == tenant_id
            assert "$expr" in pipeline[0]["$match"]
            assert pipeline[1]["$addFields"]["combined_cost"]
            assert pipeline[2]["$sort"]["combined_cost"] == -1
            assert pipeline[3]["$limit"] == 10

            assert len(result) == 2
            assert result[0]["combined_cost"] == 0.60

    @pytest.mark.asyncio
    async def test_vonage_integration_error_handling(self, monitoring_service, sample_vapi_call_data):
        """Test error handling when Vonage integration fails."""

        with patch('backend.services.automation_monitoring_service.get_vonage_cost_service') as mock_vonage_service:
            mock_service = AsyncMock()
            mock_service.track_vapi_call_cost.side_effect = Exception("Vonage API error")
            mock_vonage_service.return_value = mock_service

            with patch.object(monitoring_service, 'metrics_collection') as mock_collection:
                mock_collection.insert_one.return_value = AsyncMock(inserted_id="test_record_id")

                with patch.object(monitoring_service, '_update_automation_health'), \
                     patch.object(monitoring_service, '_check_call_quality_alerts'):

                    # Should not raise exception, but log error
                    result = await monitoring_service.record_vapi_call_metrics(sample_vapi_call_data)

                    # Verify call was still recorded without Vonage data
                    call_args = mock_collection.insert_one.call_args[0][0]
                    assert call_args["vonage_transaction_id"] is None
                    assert call_args["estimated_vonage_cost"] is None
                    assert result == "test_record_id"

    def test_vapi_call_metrics_model_validation(self, sample_vonage_cost_record):
        """Test VAPICallMetrics model validation with Vonage fields."""

        metrics = VAPICallMetrics(
            agent_id="assistant_456",
            call_id="test_call_123",
            tenant_id="test_tenant",
            automation_id="automation_789",
            started_at=datetime.now(timezone.utc),
            ended_at=datetime.now(timezone.utc),
            duration_seconds=330,
            status="completed",
            sentiment_score=0.8,
            satisfaction_rating=8,
            intent_accuracy=0.9,
            response_time_avg=2.5,
            cost_breakdown={"model": 0.15},
            total_cost=0.25,
            vonage_transaction_id="vonage_tx_123",
            vonage_cost_record=sample_vonage_cost_record,
            estimated_vonage_cost=0.066,
            actual_vonage_cost=0.065,
            functions_called=["search_providers"],
            workflow_triggers=2,
            interruptions_count=1,
            silence_duration=3.0,
            transcript_length=150
        )

        # Verify all fields are properly set
        assert metrics.vonage_transaction_id == "vonage_tx_123"
        assert metrics.estimated_vonage_cost == 0.066
        assert metrics.actual_vonage_cost == 0.065
        assert metrics.vonage_cost_record == sample_vonage_cost_record

    def test_cost_calculations(self):
        """Test cost calculation logic."""

        # Test preferring actual costs over estimates
        calls_data = [
            {"total_cost": 0.25, "estimated_vonage_cost": 0.066, "actual_vonage_cost": 0.065},
            {"total_cost": 0.30, "estimated_vonage_cost": 0.055, "actual_vonage_cost": None},
            {"total_cost": 0.20, "estimated_vonage_cost": None, "actual_vonage_cost": 0.045}
        ]

        total_estimated = sum(call.get("estimated_vonage_cost", 0) for call in calls_data if call.get("estimated_vonage_cost"))
        total_actual = sum(call.get("actual_vonage_cost", 0) for call in calls_data if call.get("actual_vonage_cost"))

        assert total_estimated == 0.121  # 0.066 + 0.055
        assert total_actual == 0.11     # 0.065 + 0.045

        # Should use actual costs when available
        total_vonage_cost = total_actual if total_actual > 0 else total_estimated
        assert total_vonage_cost == 0.11

    @pytest.mark.asyncio
    async def test_service_integration_with_existing_methods(self, monitoring_service):
        """Test integration with existing automation monitoring methods."""

        # Test that existing methods still work with enhanced model
        automation_id = "test_automation"
        tenant_id = "test_tenant"

        with patch.object(monitoring_service, 'metrics_collection') as mock_collection:
            mock_cursor = AsyncMock()
            mock_cursor.to_list.return_value = [
                {
                    "automation_id": automation_id,
                    "status": "completed",
                    "duration_seconds": 300,
                    "estimated_vonage_cost": 0.05,
                    "started_at": datetime.now(timezone.utc)
                }
            ]
            mock_collection.find.return_value = mock_cursor

            with patch.object(monitoring_service, 'health_collection') as mock_health_collection:
                mock_health_collection.replace_one.return_value = AsyncMock(upserted_id="health_id")

                health = await monitoring_service.update_automation_health(automation_id, tenant_id)

                # Verify health update still works
                assert health.automation_id == automation_id
                assert health.tenant_id == tenant_id
                assert health.total_executions == 1
                assert health.success_rate == 1.0

    def test_model_serialization_with_vonage_fields(self, sample_vonage_cost_record):
        """Test that enhanced models serialize correctly for MongoDB storage."""

        metrics = VAPICallMetrics(
            agent_id="assistant_456",
            call_id="test_call_123",
            tenant_id="test_tenant",
            started_at=datetime.now(timezone.utc),
            status="completed",
            total_cost=0.25,
            vonage_cost_record=sample_vonage_cost_record.dict(),
            estimated_vonage_cost=0.066
        )

        # Test serialization
        metrics_dict = metrics.dict()

        assert "vonage_cost_record" in metrics_dict
        assert "estimated_vonage_cost" in metrics_dict
        assert metrics_dict["estimated_vonage_cost"] == 0.066

        # Verify JSON serialization works
        json_str = json.dumps(metrics_dict, default=str)
        assert "vonage_cost_record" in json_str


class TestMonitoringServiceEdgeCases:
    """Test edge cases and error scenarios for enhanced monitoring."""

    @pytest.fixture
    def monitoring_service(self):
        """Create monitoring service instance for testing."""
        return AutomationMonitoringService()

    @pytest.fixture
    def sample_vapi_call_data(self):
        """Sample VAPI call data for testing."""
        return {
            "call": {
                "id": "test_call_123",
                "phoneNumber": "+12345678901"
            },
            "assistant": {
                "id": "assistant_456"
            },
            "metadata": {
                "tenantId": "test_tenant",
                "automationId": "automation_789"
            },
            "startedAt": "2025-09-23T01:00:00.000Z",
            "endedAt": "2025-09-23T01:05:30.000Z",
            "durationSeconds": 330,
            "cost": 0.25,
            "transcript": "Test conversation transcript"
        }

    @pytest.mark.asyncio
    async def test_incomplete_call_data_handling(self, monitoring_service):
        """Test handling of incomplete VAPI call data."""

        incomplete_data = {
            "call": {"id": "incomplete_call"},
            # Missing many required fields
        }

        with patch.object(monitoring_service, 'metrics_collection') as mock_collection:
            mock_collection.insert_one.return_value = AsyncMock(inserted_id="test_id")

            with patch.object(monitoring_service, '_update_automation_health'), \
                 patch.object(monitoring_service, '_check_call_quality_alerts'):

                # Should handle gracefully with defaults
                result = await monitoring_service.record_vapi_call_metrics(incomplete_data)
                assert result == "test_id"

    @pytest.mark.asyncio
    async def test_vonage_service_unavailable(self, monitoring_service, sample_vapi_call_data):
        """Test handling when Vonage service is unavailable."""

        with patch('backend.services.automation_monitoring_service.get_vonage_cost_service') as mock_vonage_service:
            mock_vonage_service.side_effect = Exception("Service unavailable")

            with patch.object(monitoring_service, 'metrics_collection') as mock_collection:
                mock_collection.insert_one.return_value = AsyncMock(inserted_id="test_id")

                with patch.object(monitoring_service, '_update_automation_health'), \
                     patch.object(monitoring_service, '_check_call_quality_alerts'):

                    # Should continue without Vonage integration
                    result = await monitoring_service.record_vapi_call_metrics(sample_vapi_call_data)
                    assert result == "test_id"

    @pytest.mark.asyncio
    async def test_large_dataset_performance(self, monitoring_service):
        """Test performance with large datasets."""

        tenant_id = "test_tenant"
        start_date = datetime.now(timezone.utc) - timedelta(days=30)
        end_date = datetime.now(timezone.utc)

        # Mock large dataset
        large_dataset = [
            {
                "total_cost": 0.25,
                "estimated_vonage_cost": 0.05,
                "actual_vonage_cost": 0.045
            }
        ] * 1000  # 1000 calls

        with patch.object(monitoring_service, 'metrics_collection') as mock_collection:
            mock_cursor = AsyncMock()
            mock_cursor.to_list.return_value = large_dataset
            mock_collection.find.return_value = mock_cursor

            with patch('backend.services.automation_monitoring_service.get_vonage_cost_service') as mock_vonage_service:
                mock_service = AsyncMock()
                mock_summary = Mock()
                mock_summary.cost_breakdown = {"voice_call": Decimal("45.0")}
                mock_service.get_cost_summary.return_value = mock_summary
                mock_vonage_service.return_value = mock_service

                result = await monitoring_service.get_cost_summary_with_vonage(tenant_id, start_date, end_date)

                # Verify calculations are correct for large dataset
                assert result["vapi_costs"]["total_calls"] == 1000
                assert result["vapi_costs"]["total_vapi_cost"] == 250.0  # 0.25 * 1000
                assert result["vonage_costs"]["actual_costs"] == 45.0   # 0.045 * 1000


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])