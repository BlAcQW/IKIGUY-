"""
Tests for Wallet Analytics Service.

Tests analytics metrics, reporting, and insights.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from motor.motor_asyncio import AsyncIOMotorClient

from ..analytics.wallet_analytics import (
    WalletAnalyticsService,
    MetricPeriod,
)


@pytest.fixture
async def db():
    """Create test database."""
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.test_wallet_analytics
    yield db
    await client.drop_database("test_wallet_analytics")
    client.close()


@pytest.fixture
async def analytics_service(db):
    """Create analytics service."""
    return WalletAnalyticsService(database=db)


@pytest.fixture
async def sample_data(db):
    """Create sample wallets and transactions."""
    # Create wallets
    wallets = [
        {"_id": f"wallet_{i}", "user_id": f"user_{i}", "balance": 100.00, "is_active": True}
        for i in range(10)
    ]
    await db.wallets.insert_many(wallets)

    # Create transactions
    now = datetime.utcnow()
    transactions = []

    for i in range(10):
        # Credit transactions
        transactions.append({
            "wallet_id": f"wallet_{i}",
            "user_id": f"user_{i}",
            "type": "credit",
            "amount": 100.00,
            "status": "completed",
            "created_at": now - timedelta(days=i),
            "metadata": {"payment_gateway": "paystack"}
        })

        # Debit transactions
        transactions.append({
            "wallet_id": f"wallet_{i}",
            "user_id": f"user_{i}",
            "type": "debit",
            "amount": 25.00,
            "status": "completed",
            "created_at": now - timedelta(days=i),
            "metadata": {"service": "test_service"}
        })

    await db.transactions.insert_many(transactions)
    return {"wallets": wallets, "transactions": transactions}


@pytest.mark.asyncio
async def test_get_transaction_volume(analytics_service, sample_data):
    """Test transaction volume metrics."""
    result = await analytics_service.get_transaction_volume(
        period=MetricPeriod.DAILY,
        start_date=datetime.utcnow() - timedelta(days=30)
    )

    assert result["total_transactions"] > 0
    assert "by_type" in result
    assert "credit" in result["by_type"]
    assert "debit" in result["by_type"]


@pytest.mark.asyncio
async def test_get_revenue_by_provider(analytics_service, sample_data):
    """Test revenue breakdown by provider."""
    result = await analytics_service.get_revenue_by_provider(
        start_date=datetime.utcnow() - timedelta(days=30)
    )

    assert "total_revenue" in result
    assert "by_provider" in result
    assert len(result["by_provider"]) > 0
    assert result["by_provider"][0]["provider"] == "paystack"


@pytest.mark.asyncio
async def test_get_user_spending_patterns(analytics_service, sample_data):
    """Test user spending pattern analysis."""
    result = await analytics_service.get_user_spending_patterns(
        start_date=datetime.utcnow() - timedelta(days=30),
        limit=5
    )

    assert "total_users" in result
    assert result["total_users"] > 0
    assert "users" in result
    assert len(result["users"]) <= 5


@pytest.mark.asyncio
async def test_get_low_balance_users(analytics_service, db):
    """Test low balance user identification."""
    # Create wallets with low balance
    low_balance_wallets = [
        {"_id": f"low_wallet_{i}", "user_id": f"low_user_{i}", "balance": 5.00, "is_active": True}
        for i in range(3)
    ]
    await db.wallets.insert_many(low_balance_wallets)

    result = await analytics_service.get_low_balance_users(threshold=Decimal("10.00"))

    assert len(result) >= 3
    for user in result:
        assert Decimal(user["balance"]) < Decimal("10.00")


@pytest.mark.asyncio
async def test_get_system_health_metrics(analytics_service, sample_data):
    """Test system health metrics."""
    result = await analytics_service.get_system_health_metrics()

    assert "active_wallets" in result
    assert "total_system_balance" in result
    assert "success_rate_percent" in result
    assert result["active_wallets"] >= 10  # From sample_data


@pytest.mark.asyncio
async def test_get_dashboard_summary(analytics_service, sample_data):
    """Test comprehensive dashboard summary."""
    result = await analytics_service.get_dashboard_summary()

    assert "transaction_volume_24h" in result
    assert "transaction_volume_30d" in result
    assert "revenue_30d" in result
    assert "system_health" in result
    assert "low_balance_users" in result


@pytest.mark.asyncio
async def test_get_fraud_statistics(analytics_service, db):
    """Test fraud statistics."""
    # Create fraud alerts
    alerts = [
        {
            "wallet_id": "wallet_1",
            "severity": "high",
            "alert_type": "velocity_check",
            "action_taken": "blocked",
            "amount": 1000.00,
            "created_at": datetime.utcnow()
        },
        {
            "wallet_id": "wallet_2",
            "severity": "medium",
            "alert_type": "anomaly",
            "action_taken": "flagged",
            "amount": 500.00,
            "created_at": datetime.utcnow()
        }
    ]
    await db.fraud_alerts.insert_many(alerts)

    result = await analytics_service.get_fraud_statistics(
        start_date=datetime.utcnow() - timedelta(days=1)
    )

    assert result["total_alerts"] == 2
    assert result["blocked_transactions"] == 1
    assert "by_severity" in result
    assert result["by_severity"]["high"] == 1


@pytest.mark.asyncio
async def test_get_transaction_volume_with_tenant_filter(analytics_service, db):
    """Test transaction volume with tenant filtering."""
    # Create transactions for specific tenant
    transactions = [
        {
            "wallet_id": "wallet_tenant1",
            "type": "credit",
            "amount": 50.00,
            "status": "completed",
            "tenant_id": "tenant_001",
            "created_at": datetime.utcnow()
        }
    ]
    await db.transactions.insert_many(transactions)

    result = await analytics_service.get_transaction_volume(
        period=MetricPeriod.DAILY,
        tenant_id="tenant_001"
    )

    assert result["total_transactions"] >= 1
