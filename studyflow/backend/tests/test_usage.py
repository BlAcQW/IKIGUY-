"""
Unit tests for usage tracking service.
"""

import pytest
import sys
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, "/opt/kasaai/apps")

from shared.integration.usage_calculator import PricingTier, ServiceType, Currency

from app.services.usage_service import UsageService


class TestUsageService:
    """Test suite for UsageService."""

    @pytest.mark.asyncio
    async def test_get_user_tier_default(self):
        """Test getting user tier returns BASIC by default."""
        with patch('app.services.usage_service.mongodb') as mock_mongodb:
            mock_collection = MagicMock()
            mock_collection.find_one = AsyncMock(return_value=None)
            mock_mongodb.get_collection.return_value = mock_collection

            tier = await UsageService.get_user_tier("user123")
            assert tier == PricingTier.BASIC

    @pytest.mark.asyncio
    async def test_get_user_tier_existing(self):
        """Test getting existing user tier."""
        with patch('app.services.usage_service.mongodb') as mock_mongodb:
            mock_collection = MagicMock()
            mock_collection.find_one = AsyncMock(return_value={
                "user_id": "user123",
                "tier": "premium"
            })
            mock_mongodb.get_collection.return_value = mock_collection

            tier = await UsageService.get_user_tier("user123")
            assert tier == PricingTier.PREMIUM

    @pytest.mark.asyncio
    async def test_set_user_tier(self):
        """Test setting user tier."""
        with patch('app.services.usage_service.mongodb') as mock_mongodb:
            mock_collection = MagicMock()
            mock_collection.update_one = AsyncMock()
            mock_mongodb.get_collection.return_value = mock_collection

            success = await UsageService.set_user_tier("user123", PricingTier.ENTERPRISE)
            assert success is True

            # Verify update_one was called
            mock_collection.update_one.assert_called_once()
            call_args = mock_collection.update_one.call_args
            assert call_args[0][0] == {"user_id": "user123"}
            assert call_args[0][1]["$set"]["tier"] == "enterprise"

    @pytest.mark.asyncio
    async def test_track_rag_usage(self):
        """Test tracking RAG usage."""
        with patch('app.services.usage_service.mongodb') as mock_mongodb:
            # Mock tier query
            mock_tier_collection = MagicMock()
            mock_tier_collection.find_one = AsyncMock(return_value={
                "user_id": "user123",
                "tier": "basic"
            })

            # Mock metrics save
            mock_metrics_collection = MagicMock()
            mock_metrics_collection.insert_one = AsyncMock(
                return_value=MagicMock(inserted_id="metric123")
            )

            def get_collection(name):
                if "user_pricing_tiers" in name:
                    return mock_tier_collection
                elif "usage_metrics" in name:
                    return mock_metrics_collection
                return MagicMock()

            mock_mongodb.get_collection.side_effect = get_collection

            metric = await UsageService.track_rag_usage(
                user_id="user123",
                session_id="session123",
                question_id="question123",
                input_tokens=500,
                output_tokens=200,
                num_queries=1,
                provider="gemini",
                model="gemini-2.5-flash",
                subject="Mathematics",
                topic="Algebra"
            )

            assert metric.service_type == ServiceType.RAG_QUERY
            assert metric.quantity > 0
            assert metric.total_cost > 0
            assert metric.metadata["user_id"] == "user123"
            assert metric.metadata["subject"] == "Mathematics"

            # Verify metric was saved
            mock_metrics_collection.insert_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_track_document_processing(self):
        """Test tracking document processing usage."""
        with patch('app.services.usage_service.mongodb') as mock_mongodb:
            # Mock tier query
            mock_tier_collection = MagicMock()
            mock_tier_collection.find_one = AsyncMock(return_value={
                "user_id": "user123",
                "tier": "premium"
            })

            # Mock metrics save
            mock_metrics_collection = MagicMock()
            mock_metrics_collection.insert_one = AsyncMock(
                return_value=MagicMock(inserted_id="metric123")
            )

            def get_collection(name):
                if "user_pricing_tiers" in name:
                    return mock_tier_collection
                elif "usage_metrics" in name:
                    return mock_metrics_collection
                return MagicMock()

            mock_mongodb.get_collection.side_effect = get_collection

            metric = await UsageService.track_document_processing(
                user_id="user123",
                material_id="material123",
                num_pages=50,
                file_size_mb=5.5,
                document_type="pdf"
            )

            assert metric.service_type == ServiceType.DOCUMENT_PROCESSING
            assert metric.metadata["user_id"] == "user123"
            assert metric.metadata["material_id"] == "material123"
            assert metric.metadata["num_pages"] == 50

    @pytest.mark.asyncio
    async def test_get_user_usage(self):
        """Test getting user usage metrics."""
        with patch('app.services.usage_service.mongodb') as mock_mongodb:
            # Mock metrics
            mock_metrics = [
                {
                    "service_type": "rag_query",
                    "quantity": 700.0,
                    "unit": "tokens",
                    "unit_cost": 0.0015,
                    "total_cost": 1.05,
                    "currency": "GHS",
                    "metadata": {"user_id": "user123"},
                    "timestamp": datetime.utcnow()
                }
            ]

            mock_collection = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.__aiter__.return_value = iter(mock_metrics)
            mock_collection.find.return_value.sort.return_value = mock_cursor
            mock_mongodb.get_collection.return_value = mock_collection

            metrics = await UsageService.get_user_usage(
                user_id="user123",
                start_date=datetime.utcnow() - timedelta(days=7),
                end_date=datetime.utcnow()
            )

            assert len(metrics) == 1
            assert metrics[0].service_type == ServiceType.RAG_QUERY

    @pytest.mark.asyncio
    async def test_get_usage_summary(self):
        """Test getting usage summary."""
        with patch('app.services.usage_service.mongodb') as mock_mongodb:
            # Mock metrics
            mock_metrics = [
                {
                    "service_type": "rag_query",
                    "quantity": 700.0,
                    "unit": "tokens",
                    "unit_cost": 0.0015,
                    "total_cost": 1.05,
                    "currency": "GHS",
                    "metadata": {
                        "user_id": "user123",
                        "subject": "Mathematics",
                        "input_tokens": 500,
                        "output_tokens": 200
                    },
                    "timestamp": datetime.utcnow()
                },
                {
                    "service_type": "rag_query",
                    "quantity": 300.0,
                    "unit": "tokens",
                    "unit_cost": 0.0012,
                    "total_cost": 0.36,
                    "currency": "GHS",
                    "metadata": {
                        "user_id": "user123",
                        "subject": "Science",
                        "input_tokens": 200,
                        "output_tokens": 100
                    },
                    "timestamp": datetime.utcnow()
                }
            ]

            mock_collection = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.__aiter__.return_value = iter(mock_metrics)
            mock_collection.find.return_value.sort.return_value = mock_cursor
            mock_mongodb.get_collection.return_value = mock_collection

            summary = await UsageService.get_usage_summary(
                user_id="user123",
                start_date=datetime.utcnow() - timedelta(days=7),
                end_date=datetime.utcnow()
            )

            assert summary["user_id"] == "user123"
            assert summary["total_cost"] > 0
            assert summary["total_queries"] == 2
            assert summary["total_tokens"] == 1000
            assert "Mathematics" in summary["by_subject"]
            assert "Science" in summary["by_subject"]

    @pytest.mark.asyncio
    async def test_get_usage_summary_empty(self):
        """Test getting usage summary with no metrics."""
        with patch('app.services.usage_service.mongodb') as mock_mongodb:
            mock_collection = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.__aiter__.return_value = iter([])
            mock_collection.find.return_value.sort.return_value = mock_cursor
            mock_mongodb.get_collection.return_value = mock_collection

            summary = await UsageService.get_usage_summary(
                user_id="user123",
                start_date=datetime.utcnow() - timedelta(days=7),
                end_date=datetime.utcnow()
            )

            assert summary["total_cost"] == 0.0
            assert summary["total_queries"] == 0
            assert summary["total_tokens"] == 0
            assert len(summary["by_subject"]) == 0

    @pytest.mark.asyncio
    async def test_get_cost_estimate(self):
        """Test getting cost estimate."""
        estimate = await UsageService.get_cost_estimate(
            tier=PricingTier.BASIC,
            input_tokens=500,
            output_tokens=200,
            num_queries=1
        )

        assert estimate["tier"] == "basic"
        assert estimate["input_tokens"] == 500
        assert estimate["output_tokens"] == 200
        assert estimate["total_tokens"] == 700
        assert estimate["estimated_cost"] > 0
        assert "cost_breakdown" in estimate
        assert "input_cost" in estimate["cost_breakdown"]
        assert "output_cost" in estimate["cost_breakdown"]
        assert "base_cost" in estimate["cost_breakdown"]

    @pytest.mark.asyncio
    async def test_get_admin_analytics(self):
        """Test getting admin analytics."""
        with patch('app.services.usage_service.mongodb') as mock_mongodb:
            mock_collection = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.to_list = AsyncMock(return_value=[{
                "_id": None,
                "total_cost": 150.50,
                "total_metrics": 500,
                "unique_users": ["user1", "user2", "user3"],
                "by_service": [
                    {"service": "rag_query", "cost": 100.0, "quantity": 50000},
                    {"service": "document_processing", "cost": 50.5, "quantity": 1000}
                ]
            }])
            mock_collection.aggregate.return_value = mock_cursor
            mock_mongodb.get_collection.return_value = mock_collection

            analytics = await UsageService.get_admin_analytics(
                start_date=datetime.utcnow() - timedelta(days=30),
                end_date=datetime.utcnow()
            )

            assert analytics["total_cost"] == 150.50
            assert analytics["total_metrics"] == 500
            assert analytics["unique_users"] == 3
            assert "rag_query" in analytics["by_service"]
            assert "document_processing" in analytics["by_service"]

    @pytest.mark.asyncio
    async def test_pricing_tiers(self):
        """Test that all pricing tiers are available."""
        calculator_basic = UsageService.get_calculator(PricingTier.BASIC)
        calculator_premium = UsageService.get_calculator(PricingTier.PREMIUM)
        calculator_enterprise = UsageService.get_calculator(PricingTier.ENTERPRISE)
        calculator_free = UsageService.get_calculator(PricingTier.FREE)

        assert calculator_basic.pricing.tier == PricingTier.BASIC
        assert calculator_premium.pricing.tier == PricingTier.PREMIUM
        assert calculator_enterprise.pricing.tier == PricingTier.ENTERPRISE
        assert calculator_free.pricing.tier == PricingTier.FREE

        # Verify free tier has zero costs
        assert calculator_free.pricing.rag_input_token_cost == 0
        assert calculator_free.pricing.rag_output_token_cost == 0

    @pytest.mark.asyncio
    async def test_rag_cost_calculation(self):
        """Test RAG cost calculation with different tiers."""
        # Basic tier
        calc_basic = UsageService.get_calculator(PricingTier.BASIC)
        metric_basic = calc_basic.calculate_rag_cost(
            input_tokens=1000,
            output_tokens=500,
            num_queries=1
        )

        # Premium tier (should be cheaper)
        calc_premium = UsageService.get_calculator(PricingTier.PREMIUM)
        metric_premium = calc_premium.calculate_rag_cost(
            input_tokens=1000,
            output_tokens=500,
            num_queries=1
        )

        # Premium should cost less than basic
        assert metric_premium.total_cost < metric_basic.total_cost

        # Free tier (should be zero)
        calc_free = UsageService.get_calculator(PricingTier.FREE)
        metric_free = calc_free.calculate_rag_cost(
            input_tokens=1000,
            output_tokens=500,
            num_queries=1
        )

        assert metric_free.total_cost == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
