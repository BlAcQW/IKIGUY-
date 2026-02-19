"""
Integration Tests for Wallet Service CRUD Operations.

Tests create, read, update, delete operations with real MongoDB database.
Uses actual data and verifies database state after each operation.

Author: KasaAI Team
Date: 2025-11-23
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from bson import ObjectId

from ..wallet_service import WalletService
from ..models import Currency, TransactionType, TransactionStatus, WalletStatus
from ..exceptions import (
    WalletNotFoundError,
    InsufficientBalanceError,
    DuplicateTransactionError,
)


@pytest.mark.asyncio
class TestWalletCRUDIntegration:
    """Integration tests for wallet CRUD operations with real database."""

    async def test_create_wallet_with_real_data(self, test_db):
        """Test creating a wallet and verifying in database."""
        service = WalletService(database=test_db)

        # Create wallet
        wallet = await service.create_wallet(
            user_id="user_crud_001",
            currency=Currency.GHS,
            tenant_id="churchflow",
            low_balance_threshold=Decimal("20.00"),
            low_balance_alert_enabled=True
        )

        # Verify wallet created
        assert wallet.id is not None
        assert wallet.user_id == "user_crud_001"
        assert wallet.currency == Currency.GHS
        assert wallet.balance == Decimal("0.00")
        assert wallet.status == WalletStatus.ACTIVE

        # Verify in database
        db_wallet = await test_db.wallets.find_one({"id": wallet.id})
        assert db_wallet is not None
        assert db_wallet["user_id"] == "user_crud_001"
        assert db_wallet["balance"] == 0.00
        assert db_wallet["low_balance_threshold"] == 20.00

    async def test_read_wallet_by_id(self, test_db):
        """Test reading wallet by ID from database."""
        service = WalletService(database=test_db)

        # Create wallet
        created_wallet = await service.create_wallet(
            user_id="user_crud_002",
            currency=Currency.USD
        )

        # Read wallet back
        read_wallet = await service.get_wallet(created_wallet.id)

        # Verify data matches
        assert read_wallet.id == created_wallet.id
        assert read_wallet.user_id == created_wallet.user_id
        assert read_wallet.currency == created_wallet.currency
        assert read_wallet.balance == created_wallet.balance

    async def test_read_nonexistent_wallet_raises_error(self, test_db):
        """Test reading nonexistent wallet raises appropriate error."""
        service = WalletService(database=test_db)

        # Try to read nonexistent wallet
        with pytest.raises(WalletNotFoundError):
            await service.get_wallet("nonexistent_wallet_id")

    async def test_get_wallet_by_user(self, test_db):
        """Test getting wallet by user ID."""
        service = WalletService(database=test_db)

        # Create wallet
        created_wallet = await service.create_wallet(
            user_id="user_crud_003",
            currency=Currency.GHS
        )

        # Get by user ID
        wallet = await service.get_wallet_by_user(
            user_id="user_crud_003",
            currency=Currency.GHS
        )

        assert wallet.id == created_wallet.id
        assert wallet.user_id == "user_crud_003"

    async def test_credit_wallet_updates_balance(self, test_db):
        """Test crediting wallet updates balance in database."""
        service = WalletService(database=test_db)

        # Create wallet
        wallet = await service.create_wallet(
            user_id="user_crud_004",
            currency=Currency.GHS
        )

        initial_balance = wallet.balance

        # Credit wallet
        transaction = await service.credit(
            wallet_id=wallet.id,
            amount=Decimal("100.00"),
            description="Test credit",
            metadata={"test": True}
        )

        # Verify transaction
        assert transaction.transaction_type == TransactionType.CREDIT
        assert transaction.amount == Decimal("100.00")
        assert transaction.status == TransactionStatus.COMPLETED

        # Verify wallet balance updated in database
        updated_wallet = await service.get_wallet(wallet.id)
        assert updated_wallet.balance == initial_balance + Decimal("100.00")

        # Verify transaction saved in database
        db_transaction = await test_db.transactions.find_one({"id": transaction.id})
        assert db_transaction is not None
        assert db_transaction["amount"] == 100.00
        assert db_transaction["transaction_type"] == "credit"

    async def test_debit_wallet_with_sufficient_balance(self, test_db):
        """Test debiting wallet with sufficient balance."""
        service = WalletService(database=test_db)

        # Create wallet with balance
        wallet = await service.create_wallet(
            user_id="user_crud_005",
            currency=Currency.GHS
        )

        # Add balance
        await service.credit(
            wallet_id=wallet.id,
            amount=Decimal("200.00"),
            description="Initial balance"
        )

        # Debit wallet
        transaction = await service.debit(
            wallet_id=wallet.id,
            amount=Decimal("75.00"),
            description="Test debit",
            allow_negative=False
        )

        # Verify transaction
        assert transaction.transaction_type == TransactionType.DEBIT
        assert transaction.amount == Decimal("75.00")
        assert transaction.status == TransactionStatus.COMPLETED

        # Verify balance
        updated_wallet = await service.get_wallet(wallet.id)
        assert updated_wallet.balance == Decimal("125.00")  # 200 - 75

    async def test_debit_wallet_insufficient_balance_raises_error(self, test_db):
        """Test debiting more than available balance raises error."""
        service = WalletService(database=test_db)

        # Create wallet with limited balance
        wallet = await service.create_wallet(
            user_id="user_crud_006",
            currency=Currency.GHS
        )

        await service.credit(
            wallet_id=wallet.id,
            amount=Decimal("50.00"),
            description="Limited balance"
        )

        # Try to debit more than available
        with pytest.raises(InsufficientBalanceError):
            await service.debit(
                wallet_id=wallet.id,
                amount=Decimal("100.00"),
                description="Overdraw attempt",
                allow_negative=False
            )

        # Balance should remain unchanged
        wallet_after = await service.get_wallet(wallet.id)
        assert wallet_after.balance == Decimal("50.00")

    async def test_idempotency_prevents_duplicate_transactions(self, test_db):
        """Test idempotency key prevents duplicate transactions."""
        service = WalletService(database=test_db)

        wallet = await service.create_wallet(
            user_id="user_crud_007",
            currency=Currency.GHS
        )

        idempotency_key = "test_idem_key_unique_123"

        # First transaction
        tx1 = await service.credit(
            wallet_id=wallet.id,
            amount=Decimal("100.00"),
            description="First attempt",
            idempotency_key=idempotency_key
        )

        # Second transaction with same key should raise error
        with pytest.raises(DuplicateTransactionError):
            await service.credit(
                wallet_id=wallet.id,
                amount=Decimal("100.00"),
                description="Duplicate attempt",
                idempotency_key=idempotency_key
            )

        # Balance should only reflect first transaction
        wallet_after = await service.get_wallet(wallet.id)
        assert wallet_after.balance == Decimal("100.00")  # Not 200

    async def test_get_transactions_for_wallet(self, test_db):
        """Test retrieving transaction history for wallet."""
        service = WalletService(database=test_db)

        wallet = await service.create_wallet(
            user_id="user_crud_008",
            currency=Currency.GHS
        )

        # Create multiple transactions
        await service.credit(wallet.id, Decimal("100.00"), "Credit 1")
        await service.credit(wallet.id, Decimal("50.00"), "Credit 2")
        await service.debit(wallet.id, Decimal("25.00"), "Debit 1")

        # Get transactions
        transactions = await service.get_transactions(
            wallet_id=wallet.id,
            limit=10
        )

        # Verify all transactions retrieved
        assert len(transactions) == 3
        # Should be in reverse chronological order (newest first)
        assert transactions[0].description == "Debit 1"
        assert transactions[2].description == "Credit 1"

    async def test_get_balance(self, test_db):
        """Test getting wallet balance."""
        service = WalletService(database=test_db)

        wallet = await service.create_wallet(
            user_id="user_crud_009",
            currency=Currency.GHS
        )

        # Add some balance
        await service.credit(wallet.id, Decimal("175.50"), "Test balance")

        # Get balance
        balance = await service.get_balance(wallet.id)

        assert balance == Decimal("175.50")

    async def test_suspend_wallet(self, test_db):
        """Test suspending a wallet."""
        service = WalletService(database=test_db)

        wallet = await service.create_wallet(
            user_id="user_crud_010",
            currency=Currency.GHS
        )

        # Suspend wallet
        await service.suspend_wallet(
            wallet_id=wallet.id,
            reason="Test suspension"
        )

        # Verify wallet suspended
        suspended_wallet = await service.get_wallet(wallet.id)
        assert suspended_wallet.status == WalletStatus.SUSPENDED

        # Verify in database
        db_wallet = await test_db.wallets.find_one({"id": wallet.id})
        assert db_wallet["status"] == "suspended"

    async def test_reactivate_wallet(self, test_db):
        """Test reactivating a suspended wallet."""
        service = WalletService(database=test_db)

        wallet = await service.create_wallet(
            user_id="user_crud_011",
            currency=Currency.GHS
        )

        # Suspend then reactivate
        await service.suspend_wallet(wallet.id, "Test")
        await service.activate_wallet(wallet.id)

        # Verify wallet active
        active_wallet = await service.get_wallet(wallet.id)
        assert active_wallet.status == WalletStatus.ACTIVE

    async def test_close_wallet(self, test_db):
        """Test closing a wallet."""
        service = WalletService(database=test_db)

        wallet = await service.create_wallet(
            user_id="user_crud_012",
            currency=Currency.GHS
        )

        # Close wallet
        await service.close_wallet(
            wallet_id=wallet.id,
            reason="User request"
        )

        # Verify wallet closed
        closed_wallet = await service.get_wallet(wallet.id)
        assert closed_wallet.status == WalletStatus.CLOSED

    async def test_transaction_filtering_by_type(self, test_db):
        """Test filtering transactions by type."""
        service = WalletService(database=test_db)

        wallet = await service.create_wallet(
            user_id="user_crud_013",
            currency=Currency.GHS
        )

        # Create mixed transactions
        await service.credit(wallet.id, Decimal("100.00"), "Credit")
        await service.credit(wallet.id, Decimal("50.00"), "Credit")
        await service.debit(wallet.id, Decimal("25.00"), "Debit")

        # Filter by credit only
        credits = await service.get_transactions(
            wallet_id=wallet.id,
            transaction_type=TransactionType.CREDIT
        )

        assert len(credits) == 2
        assert all(tx.transaction_type == TransactionType.CREDIT for tx in credits)

    async def test_transaction_pagination(self, test_db):
        """Test transaction pagination."""
        service = WalletService(database=test_db)

        wallet = await service.create_wallet(
            user_id="user_crud_014",
            currency=Currency.GHS
        )

        # Create many transactions
        for i in range(15):
            await service.credit(wallet.id, Decimal("10.00"), f"Transaction {i}")

        # Get first page
        page1 = await service.get_transactions(
            wallet_id=wallet.id,
            limit=5,
            skip=0
        )

        # Get second page
        page2 = await service.get_transactions(
            wallet_id=wallet.id,
            limit=5,
            skip=5
        )

        assert len(page1) == 5
        assert len(page2) == 5
        # Should be different transactions
        assert page1[0].id != page2[0].id

    async def test_complex_transaction_flow(self, test_db):
        """Test complex transaction flow with multiple operations."""
        service = WalletService(database=test_db)

        wallet = await service.create_wallet(
            user_id="user_crud_015",
            currency=Currency.GHS
        )

        # Deposit
        await service.credit(wallet.id, Decimal("1000.00"), "Initial deposit")

        # Multiple purchases
        await service.debit(wallet.id, Decimal("150.00"), "Purchase 1")
        await service.debit(wallet.id, Decimal("200.00"), "Purchase 2")
        await service.debit(wallet.id, Decimal("75.00"), "Purchase 3")

        # Refund
        await service.credit(wallet.id, Decimal("200.00"), "Refund")

        # Another deposit
        await service.credit(wallet.id, Decimal("300.00"), "Additional deposit")

        # Verify final balance
        final_wallet = await service.get_wallet(wallet.id)
        # 1000 - 150 - 200 - 75 + 200 + 300 = 1075
        assert final_wallet.balance == Decimal("1075.00")

        # Verify transaction count
        all_transactions = await service.get_transactions(wallet.id, limit=100)
        assert len(all_transactions) == 6

    async def test_get_wallet_by_user_pattern(self, test_db):
        """Test get wallet by user pattern (create if not exists)."""
        service = WalletService(database=test_db)

        user_id = "user_crud_016"
        currency = Currency.GHS

        # First - wallet doesn't exist, create it
        wallet1 = await service.create_wallet(
            user_id=user_id,
            currency=currency
        )
        assert wallet1 is not None

        # Second - get existing wallet by user
        wallet2 = await service.get_wallet_by_user(
            user_id=user_id,
            currency=currency
        )

        # Should be same wallet
        assert wallet1.id == wallet2.id

    async def test_multi_currency_wallets(self, test_db):
        """Test user can have multiple wallets in different currencies."""
        service = WalletService(database=test_db)

        user_id = "user_crud_017"

        # Create GHS wallet
        ghs_wallet = await service.create_wallet(
            user_id=user_id,
            currency=Currency.GHS
        )

        # Create USD wallet
        usd_wallet = await service.create_wallet(
            user_id=user_id,
            currency=Currency.USD
        )

        # Should be different wallets
        assert ghs_wallet.id != usd_wallet.id
        assert ghs_wallet.currency == Currency.GHS
        assert usd_wallet.currency == Currency.USD

    async def test_tenant_isolation(self, test_db):
        """Test tenant isolation in wallet operations."""
        service = WalletService(database=test_db)

        # Create wallets for different tenants
        wallet_t1 = await service.create_wallet(
            user_id="user_001",
            currency=Currency.GHS,
            tenant_id="tenant_001"
        )

        wallet_t2 = await service.create_wallet(
            user_id="user_001",
            currency=Currency.GHS,
            tenant_id="tenant_002"
        )

        # Same user, different tenants = different wallets
        assert wallet_t1.id != wallet_t2.id
        assert wallet_t1.tenant_id == "tenant_001"
        assert wallet_t2.tenant_id == "tenant_002"
