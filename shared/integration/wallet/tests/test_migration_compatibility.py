"""
Migration Compatibility Tests

Tests to ensure backward compatibility after migrating from wallet.py to wallet_new/.
This test suite verifies that all apps can continue to use the wallet service with
the same API as before.

Author: KasaAI Team
Date: 2025-11-23
"""

import pytest
from decimal import Decimal
from motor.motor_asyncio import AsyncIOMotorClient
import os

from apps.shared.integration.wallet import (
    WalletService,
    Currency,
    TransactionType,
    PaymentGateway,
    Transaction,
    Wallet,
    WalletNotFoundError,
    InsufficientBalanceError,
    WalletSuspendedError,
    create_wallet_service_from_env,
)


@pytest.fixture
async def wallet_service():
    """Create wallet service for testing."""
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://admin:aawwER4444%@127.0.0.1:27017/")
    client = AsyncIOMotorClient(mongodb_uri)
    db = client["test_wallet_migration"]

    # Clean up test database
    await db.wallets.delete_many({})
    await db.transactions.delete_many({})

    service = WalletService(database=db)
    yield service

    # Cleanup after test
    await db.wallets.delete_many({})
    await db.transactions.delete_many({})


@pytest.fixture
async def wallet_service_via_create():
    """Test backward compatibility of WalletService.create() classmethod."""
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://admin:aawwER4444%@127.0.0.1:27017/")
    service = await WalletService.create(
        mongodb_uri=mongodb_uri,
        database_name="test_wallet_migration_create"
    )

    # Clean up test database
    await service.wallets_collection.delete_many({})
    await service.transactions_collection.delete_many({})

    yield service

    # Cleanup
    await service.wallets_collection.delete_many({})
    await service.transactions_collection.delete_many({})


class TestBackwardCompatibility:
    """Test backward compatibility with old wallet.py API."""

    @pytest.mark.asyncio
    async def test_create_wallet(self, wallet_service):
        """Test wallet creation - backward compatible API."""
        wallet = await wallet_service.create_wallet(
            user_id="test_user_1",
            currency=Currency.USD
        )

        assert wallet is not None
        assert wallet.user_id == "test_user_1"
        assert wallet.currency == Currency.USD
        assert wallet.balance == Decimal("0.00")

    @pytest.mark.asyncio
    async def test_get_wallet_by_user(self, wallet_service):
        """Test get_wallet_by_user - backward compatible API."""
        # Create wallet
        created = await wallet_service.create_wallet(
            user_id="test_user_2",
            currency=Currency.GHS
        )

        # Get wallet
        wallet = await wallet_service.get_wallet_by_user("test_user_2", currency=Currency.GHS)
        assert wallet.id == created.id
        assert wallet.user_id == "test_user_2"

    @pytest.mark.asyncio
    async def test_credit_method(self, wallet_service):
        """Test credit() backward compatibility method."""
        # Create wallet
        wallet = await wallet_service.create_wallet(
            user_id="test_user_3",
            currency=Currency.USD
        )

        # Credit wallet using old API
        transaction = await wallet_service.credit(
            wallet_id=wallet.id,
            amount=Decimal("100.00"),
            description="Test credit",
            idempotency_key="test-credit-1"
        )

        assert transaction is not None
        assert transaction.amount == Decimal("100.00")
        assert transaction.transaction_type == TransactionType.CREDIT
        assert transaction.balance_after == Decimal("100.00")

        # Verify wallet balance updated
        updated_wallet = await wallet_service.get_wallet(wallet.id)
        assert updated_wallet.balance == Decimal("100.00")

    @pytest.mark.asyncio
    async def test_debit_method(self, wallet_service):
        """Test debit() backward compatibility method."""
        # Create wallet with initial balance
        wallet = await wallet_service.create_wallet(
            user_id="test_user_4",
            currency=Currency.USD
        )

        # Credit first
        await wallet_service.credit(
            wallet_id=wallet.id,
            amount=Decimal("100.00"),
            description="Initial credit"
        )

        # Debit using old API
        transaction = await wallet_service.debit(
            wallet_id=wallet.id,
            amount=Decimal("30.00"),
            description="Test debit",
            allow_negative=False
        )

        assert transaction.amount == Decimal("30.00")
        assert transaction.transaction_type == TransactionType.DEBIT
        assert transaction.balance_after == Decimal("70.00")

        # Verify balance
        updated_wallet = await wallet_service.get_wallet(wallet.id)
        assert updated_wallet.balance == Decimal("70.00")

    @pytest.mark.asyncio
    async def test_debit_insufficient_balance(self, wallet_service):
        """Test debit with insufficient balance raises InsufficientBalanceError."""
        wallet = await wallet_service.create_wallet(
            user_id="test_user_5",
            currency=Currency.USD
        )

        # Try to debit more than available
        with pytest.raises(InsufficientBalanceError):
            await wallet_service.debit(
                wallet_id=wallet.id,
                amount=Decimal("50.00"),
                description="Test overdraft",
                allow_negative=False
            )

    @pytest.mark.asyncio
    async def test_debit_allow_negative(self, wallet_service):
        """Test debit with allow_negative=True."""
        wallet = await wallet_service.create_wallet(
            user_id="test_user_6",
            currency=Currency.USD
        )

        # Debit with allow_negative=True
        transaction = await wallet_service.debit(
            wallet_id=wallet.id,
            amount=Decimal("25.00"),
            description="Negative balance test",
            allow_negative=True
        )

        assert transaction.balance_after == Decimal("-25.00")

        # Verify balance
        updated_wallet = await wallet_service.get_wallet(wallet.id)
        assert updated_wallet.balance == Decimal("-25.00")

    @pytest.mark.asyncio
    async def test_get_balance(self, wallet_service):
        """Test get_balance() backward compatibility method."""
        wallet = await wallet_service.create_wallet(
            user_id="test_user_7",
            currency=Currency.USD
        )

        await wallet_service.credit(
            wallet_id=wallet.id,
            amount=Decimal("123.45"),
            description="Test"
        )

        balance = await wallet_service.get_balance(wallet.id)
        assert balance == Decimal("123.45")

    @pytest.mark.asyncio
    async def test_get_transactions(self, wallet_service):
        """Test get_transactions() backward compatibility method."""
        wallet = await wallet_service.create_wallet(
            user_id="test_user_8",
            currency=Currency.USD
        )

        # Create some transactions
        await wallet_service.credit(wallet.id, Decimal("50.00"), "Credit 1")
        await wallet_service.debit(wallet.id, Decimal("10.00"), "Debit 1")
        await wallet_service.credit(wallet.id, Decimal("25.00"), "Credit 2")

        # Get transactions using old API
        transactions = await wallet_service.get_transactions(
            wallet_id=wallet.id,
            limit=10
        )

        assert len(transactions) == 3
        assert all(isinstance(t, Transaction) for t in transactions)

    @pytest.mark.asyncio
    async def test_idempotency(self, wallet_service):
        """Test idempotency still works after migration."""
        wallet = await wallet_service.create_wallet(
            user_id="test_user_9",
            currency=Currency.USD
        )

        # First credit with idempotency key
        tx1 = await wallet_service.credit(
            wallet_id=wallet.id,
            amount=Decimal("50.00"),
            description="Idempotent credit",
            idempotency_key="unique-key-123"
        )

        # Try again with same idempotency key - should raise error
        from apps.shared.integration.wallet import DuplicateTransactionError
        with pytest.raises(DuplicateTransactionError):
            await wallet_service.credit(
                wallet_id=wallet.id,
                amount=Decimal("50.00"),
                description="Duplicate",
                idempotency_key="unique-key-123"
            )

        # Balance should only reflect first transaction
        balance = await wallet_service.get_balance(wallet.id)
        assert balance == Decimal("50.00")

    @pytest.mark.asyncio
    async def test_classmethod_create(self, wallet_service_via_create):
        """Test WalletService.create() classmethod backward compatibility."""
        service = wallet_service_via_create

        # Should be able to create wallet
        wallet = await service.create_wallet(
            user_id="test_user_classmethod",
            currency=Currency.GHS
        )

        assert wallet is not None
        assert wallet.user_id == "test_user_classmethod"

    @pytest.mark.asyncio
    async def test_exception_types(self, wallet_service):
        """Test that new exception types are raised correctly."""
        # Test WalletNotFoundError
        with pytest.raises(WalletNotFoundError):
            await wallet_service.get_wallet("non-existent-id")

        # Test WalletSuspendedError
        wallet = await wallet_service.create_wallet(
            user_id="test_user_suspended",
            currency=Currency.USD
        )
        await wallet_service.suspend_wallet(wallet.id, "Test suspension")

        with pytest.raises(WalletSuspendedError):
            await wallet_service.credit(
                wallet_id=wallet.id,
                amount=Decimal("10.00"),
                description="Should fail"
            )

    @pytest.mark.asyncio
    async def test_payment_gateway_alias(self):
        """Test that PaymentGateway is an alias for PaymentProvider."""
        from apps.shared.integration.wallet import PaymentProvider

        # PaymentGateway should be same as PaymentProvider
        assert PaymentGateway == PaymentProvider
        assert PaymentGateway.STRIPE == PaymentProvider.STRIPE
        assert PaymentGateway.PAYSTACK == PaymentProvider.PAYSTACK


class TestAppIntegrationPatterns:
    """Test common patterns used by apps (InkWave, ChurchFlow, etc.)."""

    @pytest.mark.asyncio
    async def test_get_or_create_pattern(self, wallet_service):
        """Test get-or-create pattern used by apps."""
        user_id = "test_app_user_1"

        # First call - should create
        try:
            wallet = await wallet_service.get_wallet_by_user(user_id, currency=Currency.USD)
        except WalletNotFoundError:
            wallet = await wallet_service.create_wallet(
                user_id=user_id,
                currency=Currency.USD
            )

        assert wallet.user_id == user_id
        wallet_id_1 = wallet.id

        # Second call - should get existing
        try:
            wallet = await wallet_service.get_wallet_by_user(user_id, currency=Currency.USD)
        except WalletNotFoundError:
            wallet = await wallet_service.create_wallet(
                user_id=user_id,
                currency=Currency.USD
            )

        assert wallet.id == wallet_id_1  # Same wallet

    @pytest.mark.asyncio
    async def test_usage_charging_pattern(self, wallet_service):
        """Test usage charging pattern used by InkWave, ChurchFlow."""
        # Create wallet with balance
        wallet = await wallet_service.create_wallet(
            user_id="test_usage_user",
            currency=Currency.USD
        )
        await wallet_service.credit(
            wallet_id=wallet.id,
            amount=Decimal("10.00"),
            description="Top-up"
        )

        # Charge for usage (pattern from InkWave)
        usage_cost = Decimal("2.50")
        transaction = await wallet_service.debit(
            wallet_id=wallet.id,
            amount=usage_cost,
            description="AI interaction charge",
            metadata={
                "service": "test_app",
                "interaction_type": "chat",
                "tokens": 1000
            },
            allow_negative=False
        )

        assert transaction.amount == usage_cost
        assert transaction.metadata["service"] == "test_app"

        # Verify balance
        balance = await wallet_service.get_balance(wallet.id)
        assert balance == Decimal("7.50")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
