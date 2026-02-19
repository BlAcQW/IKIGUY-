"""
Integration Tests for Wallet Analytics Service.

Tests analytics with real MongoDB database operations and actual data.
These are integration tests that verify end-to-end analytics functionality.

Author: KasaAI Team
Date: 2025-11-23
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from bson import ObjectId

from ..analytics.wallet_analytics import (
    WalletAnalyticsService,
    MetricPeriod,
)


@pytest.mark.asyncio
class TestWalletAnalyticsIntegration:
    """Integration tests for wallet analytics with real database."""

    async def test_transaction_volume_with_real_data(self, test_db):
        """Test transaction volume calculation with actual database transactions."""
        service = WalletAnalyticsService(database=test_db)

        # Create real transaction data
        now = datetime.utcnow()
        transactions = []

        for i in range(10):
            transactions.append({
                "wallet_id": f"wallet_{i % 3}",
                "user_id": f"user_{i % 3}",
                "type": "credit",
                "amount": 100.00 + (i * 10),
                "status": "completed",
                "created_at": now - timedelta(days=i % 7),
                "metadata": {"service": "test"}
            })

        for i in range(5):
            transactions.append({
                "wallet_id": f"wallet_{i % 3}",
                "user_id": f"user_{i % 3}",
                "type": "debit",
                "amount": 50.00 + (i * 5),
                "status": "completed",
                "created_at": now - timedelta(days=i % 7),
                "metadata": {"service": "test"}
            })

        await test_db.transactions.insert_many(transactions)

        # Get transaction volume
        result = await service.get_transaction_volume(
            period=MetricPeriod.WEEKLY,
            start_date=now - timedelta(days=7)
        )

        # Verify metrics
        assert result["total_transactions"] == 15
        assert "by_type" in result
        assert result["by_type"]["credit"]["count"] == 10
        assert result["by_type"]["debit"]["count"] == 5
        assert Decimal(result["total_volume"]) > Decimal("0")

    async def test_revenue_by_provider_real_data(self, test_db):
        """Test revenue calculation by provider with real transactions."""
        service = WalletAnalyticsService(database=test_db)

        now = datetime.utcnow()

        # Create deposits from different providers
        await test_db.transactions.insert_many([
            {
                "wallet_id": "wallet_1",
                "type": "credit",
                "amount": 500.00,
                "status": "completed",
                "created_at": now - timedelta(days=1),
                "metadata": {"payment_gateway": "paystack"}
            },
            {
                "wallet_id": "wallet_2",
                "type": "credit",
                "amount": 300.00,
                "status": "completed",
                "created_at": now - timedelta(days=2),
                "metadata": {"payment_gateway": "paystack"}
            },
            {
                "wallet_id": "wallet_3",
                "type": "credit",
                "amount": 200.00,
                "status": "completed",
                "created_at": now - timedelta(days=3),
                "metadata": {"payment_gateway": "stripe"}
            },
            {
                "wallet_id": "wallet_4",
                "type": "credit",
                "amount": 150.00,
                "status": "completed",
                "created_at": now - timedelta(days=4),
                "metadata": {"payment_gateway": "flutterwave"}
            }
        ])

        # Get revenue by provider
        result = await service.get_revenue_by_provider(
            start_date=now - timedelta(days=30)
        )

        # Verify results
        assert Decimal(result["total_revenue"]) == Decimal("1150.00")
        assert result["total_deposits"] == 4
        assert len(result["by_provider"]) == 3  # 3 different providers

        # Check paystack (highest revenue)
        paystack_data = next(p for p in result["by_provider"] if p["provider"] == "paystack")
        assert paystack_data["deposit_count"] == 2
        assert Decimal(paystack_data["total_revenue"]) == Decimal("800.00")

    async def test_user_spending_patterns_real_data(self, test_db):
        """Test user spending pattern analysis with real user data."""
        service = WalletAnalyticsService(database=test_db)

        now = datetime.utcnow()

        # Create spending data for multiple users
        await test_db.transactions.insert_many([
            # User 1: Heavy spender
            {
                "user_id": "user_001",
                "wallet_id": "wallet_001",
                "type": "debit",
                "amount": 100.00,
                "status": "completed",
                "created_at": now - timedelta(days=1),
                "metadata": {"service": "premium_feature"}
            },
            {
                "user_id": "user_001",
                "wallet_id": "wallet_001",
                "type": "debit",
                "amount": 150.00,
                "status": "completed",
                "created_at": now - timedelta(days=2),
                "metadata": {"service": "consultation"}
            },
            # User 2: Moderate spender
            {
                "user_id": "user_002",
                "wallet_id": "wallet_002",
                "type": "debit",
                "amount": 50.00,
                "status": "completed",
                "created_at": now - timedelta(days=1),
                "metadata": {"service": "basic_feature"}
            },
            # User 3: Light spender
            {
                "user_id": "user_003",
                "wallet_id": "wallet_003",
                "type": "debit",
                "amount": 25.00,
                "status": "completed",
                "created_at": now - timedelta(days=3),
                "metadata": {"service": "basic_feature"}
            }
        ])

        # Get spending patterns
        result = await service.get_user_spending_patterns(
            start_date=now - timedelta(days=30),
            limit=10
        )

        # Verify results
        assert result["total_users"] == 3
        assert Decimal(result["total_spending"]) == Decimal("325.00")

        # User 1 should be first (highest spender)
        top_user = result["users"][0]
        assert top_user["user_id"] == "user_001"
        assert Decimal(top_user["total_spent"]) == Decimal("250.00")
        assert top_user["transaction_count"] == 2
        assert "premium_feature" in top_user["services_used"]

    async def test_fraud_statistics_real_data(self, test_db):
        """Test fraud statistics with real fraud alert data."""
        service = WalletAnalyticsService(database=test_db)

        now = datetime.utcnow()

        # Create fraud alerts
        await test_db.fraud_alerts.insert_many([
            {
                "wallet_id": "wallet_001",
                "severity": "high",
                "alert_type": "velocity_check",
                "action_taken": "blocked",
                "amount": 5000.00,
                "created_at": now - timedelta(hours=2)
            },
            {
                "wallet_id": "wallet_002",
                "severity": "high",
                "alert_type": "velocity_check",
                "action_taken": "blocked",
                "amount": 3000.00,
                "created_at": now - timedelta(hours=5)
            },
            {
                "wallet_id": "wallet_003",
                "severity": "medium",
                "alert_type": "anomaly",
                "action_taken": "flagged",
                "amount": 1000.00,
                "created_at": now - timedelta(hours=10)
            },
            {
                "wallet_id": "wallet_004",
                "severity": "low",
                "alert_type": "pattern_match",
                "action_taken": "logged",
                "amount": 100.00,
                "created_at": now - timedelta(hours=24)
            }
        ])

        # Get fraud statistics
        result = await service.get_fraud_statistics(
            start_date=now - timedelta(days=7)
        )

        # Verify results
        assert result["total_alerts"] == 4
        assert result["blocked_transactions"] == 2
        assert Decimal(result["total_amount_blocked"]) == Decimal("8000.00")
        assert result["by_severity"]["high"] == 2
        assert result["by_severity"]["medium"] == 1
        assert result["by_severity"]["low"] == 1
        assert result["by_type"]["velocity_check"] == 2

    async def test_low_balance_users_identification(self, test_db):
        """Test identification of users with low wallet balance."""
        service = WalletAnalyticsService(database=test_db)

        # Create wallets with various balances
        await test_db.wallets.insert_many([
            {
                "_id": "wallet_low_1",
                "user_id": "user_low_1",
                "balance": 5.00,
                "currency": "GHS",
                "is_active": True,
                "last_transaction_at": datetime.utcnow() - timedelta(days=1)
            },
            {
                "_id": "wallet_low_2",
                "user_id": "user_low_2",
                "balance": 2.50,
                "currency": "GHS",
                "is_active": True,
                "last_transaction_at": datetime.utcnow() - timedelta(days=5)
            },
            {
                "_id": "wallet_good",
                "user_id": "user_good",
                "balance": 100.00,
                "currency": "GHS",
                "is_active": True,
                "last_transaction_at": datetime.utcnow()
            },
            {
                "_id": "wallet_inactive",
                "user_id": "user_inactive",
                "balance": 1.00,
                "currency": "GHS",
                "is_active": False,  # Should be excluded
                "last_transaction_at": datetime.utcnow() - timedelta(days=30)
            }
        ])

        # Get low balance users (threshold = 10.00)
        result = await service.get_low_balance_users(threshold=Decimal("10.00"))

        # Verify results
        assert len(result) == 2  # Only active wallets with balance < 10

        balances = [Decimal(u["balance"]) for u in result]
        assert all(b < Decimal("10.00") for b in balances)

        user_ids = [u["user_id"] for u in result]
        assert "user_low_1" in user_ids
        assert "user_low_2" in user_ids
        assert "user_inactive" not in user_ids

    async def test_system_health_metrics_real_data(self, test_db):
        """Test system health metrics with actual database state."""
        service = WalletAnalyticsService(database=test_db)

        now = datetime.utcnow()

        # Create wallets
        await test_db.wallets.insert_many([
            {"_id": f"wallet_{i}", "user_id": f"user_{i}", "balance": 100.00 * i, "is_active": True, "currency": "GHS"}
            for i in range(1, 6)
        ])
        await test_db.wallets.insert_many([
            {"_id": "wallet_suspended_1", "user_id": "user_suspended", "balance": 50.00, "status": "suspended", "is_active": False, "currency": "GHS"},
            {"_id": "wallet_suspended_2", "user_id": "user_suspended_2", "balance": 25.00, "status": "suspended", "is_active": False, "currency": "GHS"}
        ])

        # Create transactions (last 24 hours)
        await test_db.transactions.insert_many([
            {
                "wallet_id": f"wallet_{i}",
                "type": "credit",
                "amount": 50.00,
                "status": "completed",
                "created_at": now - timedelta(hours=i)
            }
            for i in range(1, 9)
        ])
        # Add 2 failed transactions
        await test_db.transactions.insert_many([
            {
                "wallet_id": "wallet_1",
                "type": "debit",
                "amount": 10.00,
                "status": "failed",
                "created_at": now - timedelta(hours=10)
            },
            {
                "wallet_id": "wallet_2",
                "type": "debit",
                "amount": 15.00,
                "status": "failed",
                "created_at": now - timedelta(hours=12)
            }
        ])

        # Get system health
        result = await service.get_system_health_metrics()

        # Verify results
        assert result["active_wallets"] == 5
        assert result["suspended_wallets"] == 2
        assert Decimal(result["total_system_balance"]) == Decimal("1000.00")  # 100+200+300+400+500
        assert result["transactions_last_24h"] == 10
        assert result["successful_transactions"] == 8
        assert result["success_rate_percent"] == 80.0

    async def test_dashboard_summary_comprehensive(self, test_db):
        """Test comprehensive dashboard summary with all metrics."""
        service = WalletAnalyticsService(database=test_db)

        now = datetime.utcnow()

        # Set up comprehensive test data
        # Wallets
        await test_db.wallets.insert_many([
            {"_id": f"wallet_{i}", "user_id": f"user_{i}", "balance": 5.00 if i < 3 else 100.00, "is_active": True, "currency": "GHS"}
            for i in range(10)
        ])

        # Transactions
        await test_db.transactions.insert_many([
            {
                "wallet_id": f"wallet_{i % 10}",
                "user_id": f"user_{i % 10}",
                "type": "credit" if i % 2 == 0 else "debit",
                "amount": 50.00 + (i * 5),
                "status": "completed",
                "created_at": now - timedelta(days=i % 30),
                "metadata": {"payment_gateway": "paystack" if i % 2 == 0 else None, "service": "test"}
            }
            for i in range(20)
        ])

        # Fraud alerts
        await test_db.fraud_alerts.insert_many([
            {
                "wallet_id": "wallet_1",
                "severity": "high",
                "alert_type": "velocity_check",
                "action_taken": "blocked",
                "amount": 1000.00,
                "created_at": now - timedelta(days=5)
            }
        ])

        # Get dashboard summary
        summary = await service.get_dashboard_summary()

        # Verify all sections present
        assert "transaction_volume_24h" in summary
        assert "transaction_volume_30d" in summary
        assert "revenue_30d" in summary
        assert "fraud_statistics_30d" in summary
        assert "system_health" in summary
        assert "low_balance_users" in summary

        # Verify low balance users
        assert summary["low_balance_users"]["count"] == 3  # 3 wallets with balance < 10
        assert len(summary["low_balance_users"]["users"]) <= 10  # Top 10 limit

    async def test_tenant_filtering(self, test_db):
        """Test that tenant filtering works correctly in analytics."""
        service = WalletAnalyticsService(database=test_db)

        now = datetime.utcnow()

        # Create transactions for different tenants
        await test_db.transactions.insert_many([
            {
                "wallet_id": "wallet_t1_1",
                "type": "credit",
                "amount": 100.00,
                "status": "completed",
                "tenant_id": "tenant_001",
                "created_at": now
            },
            {
                "wallet_id": "wallet_t1_2",
                "type": "credit",
                "amount": 150.00,
                "status": "completed",
                "tenant_id": "tenant_001",
                "created_at": now
            },
            {
                "wallet_id": "wallet_t2_1",
                "type": "credit",
                "amount": 200.00,
                "status": "completed",
                "tenant_id": "tenant_002",
                "created_at": now
            }
        ])

        # Get volume for tenant_001 only
        result = await service.get_transaction_volume(
            period=MetricPeriod.DAILY,
            tenant_id="tenant_001"
        )

        # Should only include tenant_001 transactions
        assert result["total_transactions"] == 2
        assert Decimal(result["total_volume"]) == Decimal("250.00")

    async def test_analytics_with_no_data(self, test_db):
        """Test analytics gracefully handle empty database."""
        service = WalletAnalyticsService(database=test_db)

        # Get metrics with no data
        volume = await service.get_transaction_volume()
        revenue = await service.get_revenue_by_provider()
        health = await service.get_system_health_metrics()

        # Should return empty/zero results, not errors
        assert volume["total_transactions"] == 0
        assert Decimal(volume["total_volume"]) == Decimal("0.00")
        assert Decimal(revenue["total_revenue"]) == Decimal("0.00")
        assert health["active_wallets"] == 0
        assert health["success_rate_percent"] == 0
