"""
Integration Tests for Auto-Reload Service.

Tests auto-reload functionality with real MongoDB database operations.
These are integration tests that verify end-to-end auto-reload workflow.

Author: KasaAI Team
Date: 2025-11-23
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from bson import ObjectId
from unittest.mock import AsyncMock, Mock

from ..auto_reload_service import AutoReloadService
from ..wallet_service import WalletService


@pytest.mark.asyncio
class TestAutoReloadIntegration:
    """Integration tests for auto-reload service with real database."""

    @pytest.fixture
    async def mock_wallet_service(self, test_db):
        """Create mock wallet service for testing."""
        service = Mock(spec=WalletService)
        service.charge_saved_payment_method = AsyncMock(return_value={
            "success": True,
            "transaction_id": "tx_test_123"
        })
        return service

    @pytest.fixture
    async def auto_reload_service(self, test_db, mock_wallet_service):
        """Create auto-reload service instance."""
        return AutoReloadService(
            database=test_db,
            wallet_service=mock_wallet_service,
            notification_service=None  # No notifications for these tests
        )

    async def test_auto_reload_triggers_when_below_threshold(
        self,
        test_db,
        auto_reload_service
    ):
        """Test that auto-reload triggers when balance falls below threshold."""
        # Create wallet with auto-reload enabled
        wallet_id = str(ObjectId())
        await test_db.wallets.insert_one({
            "_id": wallet_id,
            "user_id": "user_001",
            "balance": 5.00,  # Below threshold
            "auto_reload_enabled": True,
            "auto_reload_threshold": 10.00,
            "auto_reload_amount": 50.00,
            "auto_reload_payment_method_id": "pm_test_123",
            "currency": "GHS",
            "is_active": True
        })

        # Create payment method
        await test_db.payment_methods.insert_one({
            "_id": "pm_test_123",
            "wallet_id": wallet_id,
            "provider": "stripe",
            "provider_payment_method_id": "pm_stripe_123",
            "is_active": True,
            "type": "card"
        })

        # Trigger auto-reload check
        result = await auto_reload_service.check_and_reload_wallet(wallet_id)

        # Verify reload was triggered
        assert result is not None
        assert result["success"] is True
        assert result["reason"] == "auto_reload_triggered"
        assert Decimal(result["amount"]) == Decimal("50.00")

        # Verify reload log was created
        log = await test_db.auto_reload_logs.find_one({"wallet_id": wallet_id})
        assert log is not None
        assert log["success"] is True
        assert log["amount"] == 50.00

    async def test_auto_reload_skipped_when_above_threshold(
        self,
        test_db,
        auto_reload_service
    ):
        """Test that auto-reload is skipped when balance is sufficient."""
        wallet_id = str(ObjectId())
        await test_db.wallets.insert_one({
            "_id": wallet_id,
            "user_id": "user_002",
            "balance": 100.00,  # Above threshold
            "auto_reload_enabled": True,
            "auto_reload_threshold": 10.00,
            "auto_reload_amount": 50.00,
            "auto_reload_payment_method_id": "pm_test_123",
            "currency": "GHS",
            "is_active": True
        })

        # Trigger check
        result = await auto_reload_service.check_and_reload_wallet(wallet_id)

        # Should be None (no reload needed)
        assert result is None

        # No log should be created
        log = await test_db.auto_reload_logs.find_one({"wallet_id": wallet_id})
        assert log is None

    async def test_auto_reload_disabled_wallet(self, test_db, auto_reload_service):
        """Test that auto-reload doesn't trigger for disabled wallets."""
        wallet_id = str(ObjectId())
        await test_db.wallets.insert_one({
            "_id": wallet_id,
            "user_id": "user_003",
            "balance": 5.00,  # Below threshold but disabled
            "auto_reload_enabled": False,  # Disabled
            "auto_reload_threshold": 10.00,
            "auto_reload_amount": 50.00,
            "currency": "GHS",
            "is_active": True
        })

        # Trigger check
        result = await auto_reload_service.check_and_reload_wallet(wallet_id)

        # Should be None (auto-reload disabled)
        assert result is None

    async def test_safety_limit_max_reloads_per_day(
        self,
        test_db,
        auto_reload_service
    ):
        """Test that safety limit prevents excessive reloads."""
        wallet_id = str(ObjectId())
        await test_db.wallets.insert_one({
            "_id": wallet_id,
            "user_id": "user_004",
            "balance": 5.00,
            "auto_reload_enabled": True,
            "auto_reload_threshold": 10.00,
            "auto_reload_amount": 50.00,
            "auto_reload_payment_method_id": "pm_test_123",
            "currency": "GHS",
            "is_active": True
        })

        await test_db.payment_methods.insert_one({
            "_id": "pm_test_123",
            "wallet_id": wallet_id,
            "is_active": True,
            "provider": "stripe"
        })

        # Create 5 successful reload logs (daily limit)
        yesterday = datetime.utcnow() - timedelta(hours=12)
        for i in range(5):
            await test_db.auto_reload_logs.insert_one({
                "wallet_id": wallet_id,
                "amount": 50.00,
                "success": True,
                "created_at": yesterday - timedelta(hours=i)
            })

        # Try to reload again (should be blocked)
        result = await auto_reload_service.check_and_reload_wallet(wallet_id)

        # Should fail due to safety limit
        assert result is not None
        assert result["success"] is False
        assert result["reason"] == "safety_limits_exceeded"

    async def test_safety_limit_minimum_interval(
        self,
        test_db,
        auto_reload_service
    ):
        """Test minimum interval between reloads."""
        wallet_id = str(ObjectId())
        await test_db.wallets.insert_one({
            "_id": wallet_id,
            "user_id": "user_005",
            "balance": 5.00,
            "auto_reload_enabled": True,
            "auto_reload_threshold": 10.00,
            "auto_reload_amount": 50.00,
            "auto_reload_payment_method_id": "pm_test_123",
            "currency": "GHS",
            "is_active": True
        })

        await test_db.payment_methods.insert_one({
            "_id": "pm_test_123",
            "wallet_id": wallet_id,
            "is_active": True,
            "provider": "stripe"
        })

        # Create recent reload log (30 minutes ago)
        await test_db.auto_reload_logs.insert_one({
            "wallet_id": wallet_id,
            "amount": 50.00,
            "success": True,
            "created_at": datetime.utcnow() - timedelta(minutes=30)
        })

        # Try to reload again (should be blocked - min interval is 1 hour)
        result = await auto_reload_service.check_and_reload_wallet(wallet_id)

        # Should fail due to minimum interval
        assert result is not None
        assert result["success"] is False
        assert result["reason"] == "safety_limits_exceeded"

    async def test_missing_payment_method(self, test_db, auto_reload_service):
        """Test handling of missing payment method."""
        wallet_id = str(ObjectId())
        await test_db.wallets.insert_one({
            "_id": wallet_id,
            "user_id": "user_006",
            "balance": 5.00,
            "auto_reload_enabled": True,
            "auto_reload_threshold": 10.00,
            "auto_reload_amount": 50.00,
            "auto_reload_payment_method_id": "pm_nonexistent",  # Doesn't exist
            "currency": "GHS",
            "is_active": True
        })

        # Trigger reload
        result = await auto_reload_service.check_and_reload_wallet(wallet_id)

        # Should fail gracefully
        assert result is not None
        assert result["success"] is False
        assert result["reason"] == "payment_method_unavailable"

    async def test_check_all_wallets_batch_processing(
        self,
        test_db,
        auto_reload_service
    ):
        """Test batch processing of all wallets."""
        # Create multiple wallets with different states
        wallets = []
        for i in range(5):
            wallet_id = str(ObjectId())
            needs_reload = i < 2  # First 2 need reload

            wallets.append({
                "_id": wallet_id,
                "user_id": f"user_{i}",
                "balance": 5.00 if needs_reload else 100.00,
                "auto_reload_enabled": True,
                "auto_reload_threshold": 10.00,
                "auto_reload_amount": 50.00,
                "auto_reload_payment_method_id": f"pm_{i}",
                "currency": "GHS",
                "is_active": True
            })

            # Create payment methods
            await test_db.payment_methods.insert_one({
                "_id": f"pm_{i}",
                "wallet_id": wallet_id,
                "is_active": True,
                "provider": "stripe"
            })

        await test_db.wallets.insert_many(wallets)

        # Run batch check
        summary = await auto_reload_service.check_all_wallets()

        # Verify summary
        assert summary["checked"] == 5
        assert summary["reloaded"] == 2  # 2 wallets needed reload
        assert summary["skipped"] == 3  # 3 had sufficient balance

    async def test_enable_auto_reload(self, test_db, auto_reload_service):
        """Test enabling auto-reload for a wallet."""
        wallet_id = str(ObjectId())
        payment_method_id = str(ObjectId())

        # Create wallet without auto-reload
        await test_db.wallets.insert_one({
            "_id": wallet_id,
            "user_id": "user_007",
            "balance": 50.00,
            "auto_reload_enabled": False,
            "currency": "GHS",
            "is_active": True
        })

        # Create payment method
        await test_db.payment_methods.insert_one({
            "_id": payment_method_id,
            "wallet_id": wallet_id,
            "is_active": True,
            "provider": "paystack"
        })

        # Enable auto-reload
        success = await auto_reload_service.enable_auto_reload(
            wallet_id=wallet_id,
            threshold=Decimal("20.00"),
            reload_amount=Decimal("100.00"),
            payment_method_id=payment_method_id
        )

        assert success is True

        # Verify wallet updated
        wallet = await test_db.wallets.find_one({"_id": wallet_id})
        assert wallet["auto_reload_enabled"] is True
        assert wallet["auto_reload_threshold"] == 20.00
        assert wallet["auto_reload_amount"] == 100.00
        assert wallet["auto_reload_payment_method_id"] == payment_method_id

    async def test_disable_auto_reload(self, test_db, auto_reload_service):
        """Test disabling auto-reload for a wallet."""
        wallet_id = str(ObjectId())

        # Create wallet with auto-reload enabled
        await test_db.wallets.insert_one({
            "_id": wallet_id,
            "user_id": "user_008",
            "balance": 50.00,
            "auto_reload_enabled": True,
            "auto_reload_threshold": 10.00,
            "auto_reload_amount": 50.00,
            "currency": "GHS",
            "is_active": True
        })

        # Disable auto-reload
        success = await auto_reload_service.disable_auto_reload(wallet_id)

        assert success is True

        # Verify wallet updated
        wallet = await test_db.wallets.find_one({"_id": wallet_id})
        assert wallet["auto_reload_enabled"] is False

    async def test_force_reload_option(self, test_db, auto_reload_service):
        """Test force reload even when above threshold."""
        wallet_id = str(ObjectId())
        await test_db.wallets.insert_one({
            "_id": wallet_id,
            "user_id": "user_009",
            "balance": 100.00,  # Above threshold
            "auto_reload_enabled": True,
            "auto_reload_threshold": 10.00,
            "auto_reload_amount": 50.00,
            "auto_reload_payment_method_id": "pm_test_123",
            "currency": "GHS",
            "is_active": True
        })

        await test_db.payment_methods.insert_one({
            "_id": "pm_test_123",
            "wallet_id": wallet_id,
            "is_active": True,
            "provider": "stripe"
        })

        # Force reload
        result = await auto_reload_service.check_and_reload_wallet(
            wallet_id,
            force=True
        )

        # Should reload even though balance is sufficient
        assert result is not None
        assert result["success"] is True

    async def test_invalid_reload_amount(self, test_db, auto_reload_service):
        """Test handling of invalid reload amount (zero or negative)."""
        wallet_id = str(ObjectId())
        await test_db.wallets.insert_one({
            "_id": wallet_id,
            "user_id": "user_010",
            "balance": 5.00,
            "auto_reload_enabled": True,
            "auto_reload_threshold": 10.00,
            "auto_reload_amount": 0.00,  # Invalid
            "auto_reload_payment_method_id": "pm_test_123",
            "currency": "GHS",
            "is_active": True
        })

        # Trigger check
        result = await auto_reload_service.check_and_reload_wallet(wallet_id)

        # Should be None (invalid configuration)
        assert result is None

    async def test_reload_logs_audit_trail(self, test_db, auto_reload_service):
        """Test that all reload attempts are logged for audit."""
        wallet_id = str(ObjectId())
        await test_db.wallets.insert_one({
            "_id": wallet_id,
            "user_id": "user_011",
            "balance": 5.00,
            "auto_reload_enabled": True,
            "auto_reload_threshold": 10.00,
            "auto_reload_amount": 50.00,
            "auto_reload_payment_method_id": "pm_test_123",
            "currency": "GHS",
            "is_active": True
        })

        await test_db.payment_methods.insert_one({
            "_id": "pm_test_123",
            "wallet_id": wallet_id,
            "is_active": True,
            "provider": "paystack"
        })

        # Trigger reload
        await auto_reload_service.check_and_reload_wallet(wallet_id)

        # Check audit log
        logs = await test_db.auto_reload_logs.find({"wallet_id": wallet_id}).to_list(None)

        assert len(logs) == 1
        log = logs[0]
        assert log["wallet_id"] == wallet_id
        assert log["amount"] == 50.00
        assert log["success"] is True
        assert "details" in log
        assert "created_at" in log

    async def test_tenant_filtering_in_batch_check(
        self,
        test_db,
        auto_reload_service
    ):
        """Test tenant filtering when checking all wallets."""
        # Create wallets for different tenants
        for i in range(3):
            wallet_id = str(ObjectId())
            await test_db.wallets.insert_one({
                "_id": wallet_id,
                "user_id": f"user_t1_{i}",
                "balance": 5.00,
                "auto_reload_enabled": True,
                "auto_reload_threshold": 10.00,
                "auto_reload_amount": 50.00,
                "auto_reload_payment_method_id": f"pm_{i}",
                "tenant_id": "tenant_001",
                "currency": "GHS",
                "is_active": True
            })

            await test_db.payment_methods.insert_one({
                "_id": f"pm_{i}",
                "wallet_id": wallet_id,
                "is_active": True,
                "provider": "stripe"
            })

        # Create wallet for different tenant
        other_wallet_id = str(ObjectId())
        await test_db.wallets.insert_one({
            "_id": other_wallet_id,
            "user_id": "user_t2_1",
            "balance": 5.00,
            "auto_reload_enabled": True,
            "auto_reload_threshold": 10.00,
            "auto_reload_amount": 50.00,
            "auto_reload_payment_method_id": "pm_other",
            "tenant_id": "tenant_002",
            "currency": "GHS",
            "is_active": True
        })

        await test_db.payment_methods.insert_one({
            "_id": "pm_other",
            "wallet_id": other_wallet_id,
            "is_active": True,
            "provider": "stripe"
        })

        # Check only tenant_001 wallets
        summary = await auto_reload_service.check_all_wallets(tenant_id="tenant_001")

        # Should only check tenant_001 wallets
        assert summary["checked"] == 3
        assert summary["reloaded"] == 3
