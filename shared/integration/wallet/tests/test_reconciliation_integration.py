"""
Integration Tests for Balance Reconciliation Service.

Tests reconciliation with real MongoDB database operations and actual data.
These are integration tests, not unit tests - they test the full flow.

Author: KasaAI Team
Date: 2025-11-23
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from bson import ObjectId

from ..reports.balance_reconciliation import (
    BalanceReconciliationService,
    ReconciliationStatus,
    DiscrepancyType,
)


@pytest.mark.asyncio
class TestBalanceReconciliationIntegration:
    """Integration tests for balance reconciliation with real database."""

    async def test_reconcile_wallet_balanced_with_real_data(self, test_db):
        """Test reconciliation of balanced wallet with actual transactions."""
        service = BalanceReconciliationService(database=test_db)

        # Create wallet with real data
        wallet_id = str(ObjectId())
        await test_db.wallets.insert_one({
            "_id": wallet_id,
            "user_id": "user_001",
            "balance": 250.00,
            "currency": "GHS",
            "is_active": True,
            "created_at": datetime.utcnow()
        })

        # Create actual transaction history: +300 -50 = 250
        await test_db.transactions.insert_many([
            {
                "wallet_id": wallet_id,
                "type": "credit",
                "amount": 150.00,
                "status": "completed",
                "created_at": datetime.utcnow() - timedelta(days=5),
                "description": "Initial deposit"
            },
            {
                "wallet_id": wallet_id,
                "type": "credit",
                "amount": 150.00,
                "status": "completed",
                "created_at": datetime.utcnow() - timedelta(days=3),
                "description": "Second deposit"
            },
            {
                "wallet_id": wallet_id,
                "type": "debit",
                "amount": 50.00,
                "status": "completed",
                "created_at": datetime.utcnow() - timedelta(days=1),
                "description": "Purchase"
            }
        ])

        # Run reconciliation
        is_balanced, discrepancy = await service.reconcile_wallet(wallet_id)

        # Verify balanced
        assert is_balanced is True
        assert discrepancy is None

        # Verify wallet still exists in database
        wallet = await test_db.wallets.find_one({"_id": wallet_id})
        assert wallet is not None
        assert wallet["balance"] == 250.00

    async def test_reconcile_wallet_with_discrepancy_real_db(self, test_db):
        """Test reconciliation detects actual balance mismatch in database."""
        service = BalanceReconciliationService(database=test_db)

        wallet_id = str(ObjectId())
        # Create wallet with INCORRECT balance
        await test_db.wallets.insert_one({
            "_id": wallet_id,
            "user_id": "user_002",
            "balance": 500.00,  # Should be 300.00
            "currency": "GHS",
            "is_active": True,
            "created_at": datetime.utcnow()
        })

        # Create transactions: +400 -100 = 300 (but balance says 500)
        await test_db.transactions.insert_many([
            {
                "wallet_id": wallet_id,
                "type": "credit",
                "amount": 400.00,
                "status": "completed",
                "created_at": datetime.utcnow() - timedelta(days=2)
            },
            {
                "wallet_id": wallet_id,
                "type": "debit",
                "amount": 100.00,
                "status": "completed",
                "created_at": datetime.utcnow() - timedelta(days=1)
            }
        ])

        # Run reconciliation
        is_balanced, discrepancy = await service.reconcile_wallet(wallet_id)

        # Verify discrepancy detected
        assert is_balanced is False
        assert discrepancy is not None
        assert discrepancy.discrepancy_type == DiscrepancyType.BALANCE_MISMATCH
        assert discrepancy.expected_value == Decimal("300.00")
        assert discrepancy.actual_value == Decimal("500.00")
        assert discrepancy.difference == Decimal("200.00")

    async def test_reconcile_all_wallets_with_mixed_results(self, test_db):
        """Test system-wide reconciliation with multiple wallets."""
        service = BalanceReconciliationService(database=test_db)

        # Create 5 wallets: 3 balanced, 2 with discrepancies
        wallets_data = []
        transactions_data = []

        # Balanced wallets
        for i in range(3):
            wallet_id = str(ObjectId())
            wallets_data.append({
                "_id": wallet_id,
                "user_id": f"user_{i}",
                "balance": 100.00,
                "is_active": True,
                "currency": "GHS"
            })
            transactions_data.append({
                "wallet_id": wallet_id,
                "type": "credit",
                "amount": 100.00,
                "status": "completed",
                "created_at": datetime.utcnow()
            })

        # Wallets with discrepancies
        for i in range(3, 5):
            wallet_id = str(ObjectId())
            wallets_data.append({
                "_id": wallet_id,
                "user_id": f"user_{i}",
                "balance": 200.00,  # Wrong balance
                "is_active": True,
                "currency": "GHS"
            })
            transactions_data.append({
                "wallet_id": wallet_id,
                "type": "credit",
                "amount": 100.00,  # Should total 100, not 200
                "status": "completed",
                "created_at": datetime.utcnow()
            })

        await test_db.wallets.insert_many(wallets_data)
        await test_db.transactions.insert_many(transactions_data)

        # Run system-wide reconciliation
        report = await service.reconcile_all_wallets()

        # Verify report
        assert report.wallets_checked == 5
        assert report.wallets_balanced == 3
        assert report.wallets_discrepancies == 2
        assert report.status == ReconciliationStatus.DISCREPANCY
        assert len(report.discrepancies) == 2

        # Verify report saved to database
        saved_report = await test_db.reconciliation_reports.find_one(
            {"report_id": report.report_id}
        )
        assert saved_report is not None
        assert saved_report["wallets_checked"] == 5

    async def test_reconcile_with_pending_transactions(self, test_db):
        """Test that pending transactions are excluded from reconciliation."""
        service = BalanceReconciliationService(database=test_db)

        wallet_id = str(ObjectId())
        await test_db.wallets.insert_one({
            "_id": wallet_id,
            "user_id": "user_003",
            "balance": 100.00,
            "currency": "GHS",
            "is_active": True
        })

        # Create completed and pending transactions
        await test_db.transactions.insert_many([
            {
                "wallet_id": wallet_id,
                "type": "credit",
                "amount": 100.00,
                "status": "completed",  # Counted
                "created_at": datetime.utcnow()
            },
            {
                "wallet_id": wallet_id,
                "type": "credit",
                "amount": 50.00,
                "status": "pending",  # NOT counted
                "created_at": datetime.utcnow()
            }
        ])

        # Run reconciliation
        is_balanced, discrepancy = await service.reconcile_wallet(wallet_id)

        # Should be balanced (only completed transactions counted)
        assert is_balanced is True
        assert discrepancy is None

    async def test_reconcile_as_of_date(self, test_db):
        """Test reconciliation as of specific date."""
        service = BalanceReconciliationService(database=test_db)

        wallet_id = str(ObjectId())
        yesterday = datetime.utcnow() - timedelta(days=1)
        today = datetime.utcnow()

        await test_db.wallets.insert_one({
            "_id": wallet_id,
            "user_id": "user_004",
            "balance": 150.00,  # Current balance
            "currency": "GHS",
            "is_active": True
        })

        # Transactions over time
        await test_db.transactions.insert_many([
            {
                "wallet_id": wallet_id,
                "type": "credit",
                "amount": 100.00,
                "status": "completed",
                "created_at": yesterday - timedelta(days=1)
            },
            {
                "wallet_id": wallet_id,
                "type": "credit",
                "amount": 50.00,
                "status": "completed",
                "created_at": today  # After yesterday
            }
        ])

        # Reconcile as of yesterday (should only count first transaction)
        is_balanced, discrepancy = await service.reconcile_wallet(
            wallet_id,
            as_of_date=yesterday
        )

        # Should show discrepancy (100 expected, 150 actual)
        assert is_balanced is False
        assert discrepancy.expected_value == Decimal("100.00")

    async def test_export_report_to_csv(self, test_db):
        """Test CSV export with real report data."""
        service = BalanceReconciliationService(database=test_db)

        # Create wallet with discrepancy
        wallet_id = str(ObjectId())
        await test_db.wallets.insert_one({
            "_id": wallet_id,
            "user_id": "user_005",
            "balance": 75.00,
            "currency": "GHS",
            "is_active": True
        })

        await test_db.transactions.insert_one({
            "wallet_id": wallet_id,
            "type": "credit",
            "amount": 100.00,
            "status": "completed",
            "created_at": datetime.utcnow()
        })

        # Run reconciliation
        report = await service.reconcile_all_wallets()

        # Export to CSV
        csv_output = await service.export_report_csv(report)

        # Verify CSV contains expected data
        assert "Wallet ID" in csv_output
        assert "Discrepancy Type" in csv_output
        assert wallet_id in csv_output
        assert "balance_mismatch" in csv_output
        assert "100.00" in csv_output  # Expected value
        assert "75.00" in csv_output   # Actual value

    async def test_reconcile_with_refunds_and_adjustments(self, test_db):
        """Test reconciliation handles refunds and adjustments correctly."""
        service = BalanceReconciliationService(database=test_db)

        wallet_id = str(ObjectId())
        await test_db.wallets.insert_one({
            "_id": wallet_id,
            "user_id": "user_006",
            "balance": 125.00,
            "currency": "GHS",
            "is_active": True
        })

        # Complex transaction history with refunds and adjustments
        await test_db.transactions.insert_many([
            {
                "wallet_id": wallet_id,
                "type": "credit",
                "amount": 200.00,
                "status": "completed",
                "created_at": datetime.utcnow() - timedelta(days=4)
            },
            {
                "wallet_id": wallet_id,
                "type": "debit",
                "amount": 50.00,
                "status": "completed",
                "created_at": datetime.utcnow() - timedelta(days=3)
            },
            {
                "wallet_id": wallet_id,
                "type": "refund",  # Adds back
                "amount": 25.00,
                "status": "completed",
                "created_at": datetime.utcnow() - timedelta(days=2)
            },
            {
                "wallet_id": wallet_id,
                "type": "adjustment",  # Can be + or -
                "amount": -50.00,
                "status": "completed",
                "created_at": datetime.utcnow() - timedelta(days=1)
            }
        ])

        # Expected: 200 - 50 + 25 - 50 = 125
        is_balanced, discrepancy = await service.reconcile_wallet(wallet_id)

        assert is_balanced is True
        assert discrepancy is None

    async def test_get_recent_reports(self, test_db):
        """Test retrieving recent reconciliation reports."""
        service = BalanceReconciliationService(database=test_db)

        # Create and save multiple reports
        for i in range(5):
            wallet_id = str(ObjectId())
            await test_db.wallets.insert_one({
                "_id": wallet_id,
                "user_id": f"user_{i}",
                "balance": 100.00,
                "is_active": True,
                "currency": "GHS"
            })
            await test_db.transactions.insert_one({
                "wallet_id": wallet_id,
                "type": "credit",
                "amount": 100.00,
                "status": "completed",
                "created_at": datetime.utcnow()
            })

            # Run reconciliation (creates report)
            await service.reconcile_all_wallets()

        # Get recent reports
        reports = await service.get_recent_reports(limit=3)

        assert len(reports) == 3
        # Most recent first
        assert reports[0]["wallets_checked"] >= 1

    async def test_reconcile_inactive_wallets_excluded(self, test_db):
        """Test that inactive wallets are excluded from reconciliation."""
        service = BalanceReconciliationService(database=test_db)

        # Create active and inactive wallets
        active_wallet_id = str(ObjectId())
        inactive_wallet_id = str(ObjectId())

        await test_db.wallets.insert_many([
            {
                "_id": active_wallet_id,
                "user_id": "user_active",
                "balance": 100.00,
                "is_active": True,
                "currency": "GHS"
            },
            {
                "_id": inactive_wallet_id,
                "user_id": "user_inactive",
                "balance": 100.00,
                "is_active": False,  # Inactive
                "currency": "GHS"
            }
        ])

        # Add transactions for both
        await test_db.transactions.insert_many([
            {
                "wallet_id": active_wallet_id,
                "type": "credit",
                "amount": 100.00,
                "status": "completed",
                "created_at": datetime.utcnow()
            },
            {
                "wallet_id": inactive_wallet_id,
                "type": "credit",
                "amount": 100.00,
                "status": "completed",
                "created_at": datetime.utcnow()
            }
        ])

        # Run reconciliation
        report = await service.reconcile_all_wallets()

        # Only active wallet should be checked
        assert report.wallets_checked == 1
        assert report.wallets_balanced == 1
