"""
Tests for Balance Reconciliation Service.

Tests reconciliation logic, discrepancy detection, and reporting.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from motor.motor_asyncio import AsyncIOMotorClient

from ..reports.balance_reconciliation import (
    BalanceReconciliationService,
    ReconciliationStatus,
    DiscrepancyType,
)


@pytest.fixture
async def db():
    """Create test database."""
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.test_wallet_reconciliation
    yield db
    await client.drop_database("test_wallet_reconciliation")
    client.close()


@pytest.fixture
async def reconciliation_service(db):
    """Create reconciliation service."""
    return BalanceReconciliationService(database=db)


@pytest.fixture
async def sample_wallet(db):
    """Create sample wallet for testing."""
    wallet = {
        "_id": "test_wallet_001",
        "user_id": "user_001",
        "balance": 100.00,
        "currency": "USD",
        "is_active": True,
        "created_at": datetime.utcnow()
    }
    await db.wallets.insert_one(wallet)
    return wallet


@pytest.fixture
async def sample_transactions(db, sample_wallet):
    """Create sample transactions."""
    transactions = [
        {
            "wallet_id": "test_wallet_001",
            "type": "credit",
            "amount": 50.00,
            "status": "completed",
            "created_at": datetime.utcnow() - timedelta(days=2)
        },
        {
            "wallet_id": "test_wallet_001",
            "type": "credit",
            "amount": 75.00,
            "status": "completed",
            "created_at": datetime.utcnow() - timedelta(days=1)
        },
        {
            "wallet_id": "test_wallet_001",
            "type": "debit",
            "amount": 25.00,
            "status": "completed",
            "created_at": datetime.utcnow() - timedelta(hours=12)
        }
    ]
    await db.transactions.insert_many(transactions)
    return transactions


@pytest.mark.asyncio
async def test_reconcile_wallet_balanced(reconciliation_service, sample_wallet, sample_transactions):
    """Test reconciliation of balanced wallet."""
    # Wallet balance: 100.00
    # Transactions: +50 +75 -25 = 100.00
    # Should be balanced

    is_balanced, discrepancy = await reconciliation_service.reconcile_wallet("test_wallet_001")

    assert is_balanced is True
    assert discrepancy is None


@pytest.mark.asyncio
async def test_reconcile_wallet_discrepancy(reconciliation_service, db):
    """Test reconciliation of wallet with discrepancy."""
    # Create wallet with incorrect balance
    wallet = {
        "_id": "test_wallet_002",
        "user_id": "user_002",
        "balance": 200.00,  # Incorrect balance
        "currency": "USD",
        "is_active": True,
        "created_at": datetime.utcnow()
    }
    await db.wallets.insert_one(wallet)

    # Create transactions that should total 100.00
    transactions = [
        {
            "wallet_id": "test_wallet_002",
            "type": "credit",
            "amount": 150.00,
            "status": "completed",
            "created_at": datetime.utcnow()
        },
        {
            "wallet_id": "test_wallet_002",
            "type": "debit",
            "amount": 50.00,
            "status": "completed",
            "created_at": datetime.utcnow()
        }
    ]
    await db.transactions.insert_many(transactions)

    is_balanced, discrepancy = await reconciliation_service.reconcile_wallet("test_wallet_002")

    assert is_balanced is False
    assert discrepancy is not None
    assert discrepancy.discrepancy_type == DiscrepancyType.BALANCE_MISMATCH
    assert discrepancy.expected_value == Decimal("100.00")
    assert discrepancy.actual_value == Decimal("200.00")
    assert discrepancy.difference == Decimal("100.00")


@pytest.mark.asyncio
async def test_reconcile_all_wallets(reconciliation_service, db):
    """Test reconciliation of all wallets."""
    # Create multiple wallets
    wallets = [
        {"_id": f"wallet_{i}", "user_id": f"user_{i}", "balance": 100.00, "is_active": True}
        for i in range(5)
    ]
    await db.wallets.insert_many(wallets)

    # Create matching transactions for each
    transactions = []
    for i in range(5):
        transactions.extend([
            {"wallet_id": f"wallet_{i}", "type": "credit", "amount": 100.00, "status": "completed", "created_at": datetime.utcnow()}
        ])
    await db.transactions.insert_many(transactions)

    report = await reconciliation_service.reconcile_all_wallets()

    assert report.wallets_checked == 5
    assert report.wallets_balanced == 5
    assert report.wallets_discrepancies == 0
    assert report.status == ReconciliationStatus.BALANCED


@pytest.mark.asyncio
async def test_export_report_csv(reconciliation_service, db):
    """Test CSV export of reconciliation report."""
    # Create wallet with discrepancy
    wallet = {
        "_id": "test_wallet_003",
        "user_id": "user_003",
        "balance": 50.00,
        "currency": "USD",
        "is_active": True
    }
    await db.wallets.insert_one(wallet)

    transactions = [
        {"wallet_id": "test_wallet_003", "type": "credit", "amount": 100.00, "status": "completed", "created_at": datetime.utcnow()}
    ]
    await db.transactions.insert_many(transactions)

    report = await reconciliation_service.reconcile_all_wallets()
    csv_output = await reconciliation_service.export_report_csv(report)

    assert "Wallet ID" in csv_output
    assert "Discrepancy Type" in csv_output
    assert "test_wallet_003" in csv_output


@pytest.mark.asyncio
async def test_reconcile_wallet_not_found(reconciliation_service):
    """Test reconciliation of non-existent wallet."""
    is_balanced, discrepancy = await reconciliation_service.reconcile_wallet("nonexistent_wallet")

    assert is_balanced is False
    assert discrepancy is not None
    assert discrepancy.discrepancy_type == DiscrepancyType.ORPHANED_TRANSACTION


@pytest.mark.asyncio
async def test_reconcile_wallet_as_of_date(reconciliation_service, db):
    """Test reconciliation as of specific date."""
    wallet = {
        "_id": "test_wallet_004",
        "user_id": "user_004",
        "balance": 100.00,
        "currency": "USD",
        "is_active": True
    }
    await db.wallets.insert_one(wallet)

    # Create transactions spanning multiple days
    yesterday = datetime.utcnow() - timedelta(days=1)
    today = datetime.utcnow()

    transactions = [
        {"wallet_id": "test_wallet_004", "type": "credit", "amount": 100.00, "status": "completed", "created_at": yesterday},
        {"wallet_id": "test_wallet_004", "type": "credit", "amount": 50.00, "status": "completed", "created_at": today}
    ]
    await db.transactions.insert_many(transactions)

    # Reconcile as of yesterday (should only count first transaction)
    is_balanced, discrepancy = await reconciliation_service.reconcile_wallet(
        "test_wallet_004",
        as_of_date=yesterday
    )

    # Wallet balance is 100, but as of yesterday only 100 was credited
    # So it should be balanced as of that date
    assert is_balanced is True
