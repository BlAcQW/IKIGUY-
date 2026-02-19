"""
Unit tests for wallet top-up functionality.

Tests wallet payment initiation, verification, and credit operations
for both Stripe and Paystack payment gateways.
"""

import os
import sys
import pytest
import pytest_asyncio
from decimal import Decimal
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from app.services.wallet_service import InkWaveWalletService
from apps.shared.integration.wallet import Currency


@pytest_asyncio.fixture
async def wallet_service():
    """
    Create a wallet service instance for testing.
    """
    service = InkWaveWalletService()

    # Use test database
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    test_db_name = "inkwave_test_wallets"

    # Initialize service
    await service.initialize(mongodb_uri=mongodb_uri, database_name=test_db_name)

    yield service

    # Cleanup: Drop test database
    if service.shared_wallet and service.shared_wallet.db:
        client = AsyncIOMotorClient(mongodb_uri)
        await client.drop_database(test_db_name)
        client.close()


@pytest.fixture
def test_user_id():
    """Test user ID fixture."""
    return "test_user_topup_123"


@pytest.fixture
def test_email():
    """Test email fixture."""
    return "test_topup@inkwave.com"


class TestWalletTopUp:
    """Test wallet top-up functionality."""

    @pytest.mark.asyncio
    async def test_create_wallet_with_welcome_bonus(self, wallet_service, test_user_id):
        """
        Test wallet creation with welcome bonus.

        Expected: Wallet created with $10 welcome bonus
        """
        wallet = await wallet_service.create_user_wallet(
            user_id=test_user_id,
            initial_balance=Decimal("0.00"),
            currency=Currency.USD,
            welcome_bonus=Decimal("10.00")
        )

        assert wallet is not None
        assert wallet.user_id == test_user_id
        assert wallet.balance == Decimal("10.00")
        assert wallet.currency == Currency.USD

    @pytest.mark.asyncio
    async def test_get_balance(self, wallet_service, test_user_id):
        """
        Test getting wallet balance.

        Expected: Returns correct balance
        """
        # Create wallet
        await wallet_service.create_user_wallet(
            user_id=test_user_id,
            welcome_bonus=Decimal("10.00")
        )

        # Get balance
        balance = await wallet_service.get_balance(test_user_id)

        assert balance is not None
        assert balance == Decimal("10.00")

    @pytest.mark.asyncio
    async def test_initiate_paystack_topup_without_keys(self, wallet_service, test_user_id, test_email):
        """
        Test Paystack top-up initiation without API keys configured.

        Expected: Returns error about missing configuration
        Edge case: Missing API keys
        """
        # Create wallet
        await wallet_service.create_user_wallet(test_user_id)

        # Try to initiate Paystack payment without keys
        result = await wallet_service.initiate_paystack_topup(
            user_id=test_user_id,
            amount=Decimal("50.00"),
            email=test_email,
            callback_url="https://inkwave.ailabsafrica.com/wallet?payment=success"
        )

        assert result is not None
        assert result["success"] is False
        assert "error" in result
        # Should mention Paystack or secret key in error
        assert "paystack" in result["error"].lower() or "secret" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_initiate_stripe_topup_without_keys(self, wallet_service, test_user_id):
        """
        Test Stripe top-up initiation without API keys configured.

        Expected: Returns error about missing configuration
        Edge case: Missing API keys
        """
        # Create wallet
        await wallet_service.create_user_wallet(test_user_id)

        # Try to initiate Stripe payment without keys
        result = await wallet_service.initiate_stripe_topup(
            user_id=test_user_id,
            amount=Decimal("50.00"),
            success_url="https://inkwave.ailabsafrica.com/wallet?payment=success",
            cancel_url="https://inkwave.ailabsafrica.com/wallet?payment=cancelled"
        )

        assert result is not None
        assert result["success"] is False
        assert "error" in result
        # Should mention Stripe or secret key in error
        assert "stripe" in result["error"].lower() or "secret" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_top_up_wallet_direct_credit(self, wallet_service, test_user_id):
        """
        Test direct wallet credit (simulating successful payment).

        Expected: Wallet balance increases by top-up amount
        """
        # Create wallet
        await wallet_service.create_user_wallet(test_user_id, welcome_bonus=Decimal("10.00"))

        # Get initial balance
        initial_balance = await wallet_service.get_balance(test_user_id)

        # Top up wallet (simulating successful payment)
        from apps.shared.integration.wallet import PaymentGateway
        transaction = await wallet_service.top_up_wallet(
            user_id=test_user_id,
            amount=Decimal("50.00"),
            payment_gateway=PaymentGateway.PAYSTACK,
            payment_reference="test_ref_123"
        )

        assert transaction is not None
        assert transaction.amount == Decimal("50.00")

        # Check new balance
        new_balance = await wallet_service.get_balance(test_user_id)
        assert new_balance == initial_balance + Decimal("50.00")

    @pytest.mark.asyncio
    async def test_get_transactions_after_topup(self, wallet_service, test_user_id):
        """
        Test transaction history after top-up.

        Expected: Transaction appears in history with correct details
        """
        # Create wallet and top up
        await wallet_service.create_user_wallet(test_user_id)

        from apps.shared.integration.wallet import PaymentGateway
        await wallet_service.top_up_wallet(
            user_id=test_user_id,
            amount=Decimal("25.00"),
            payment_gateway=PaymentGateway.STRIPE,
            payment_reference="test_ref_456"
        )

        # Get transactions
        transactions = await wallet_service.get_transactions(test_user_id, limit=10)

        assert transactions is not None
        assert len(transactions) > 0

        # Find the top-up transaction
        topup_tx = None
        for tx in transactions:
            if "Top-up" in tx.description:
                topup_tx = tx
                break

        assert topup_tx is not None
        assert topup_tx.amount == Decimal("25.00")
        assert topup_tx.metadata.get("payment_gateway") == "stripe"
        assert topup_tx.metadata.get("payment_reference") == "test_ref_456"

    @pytest.mark.asyncio
    async def test_multiple_topups(self, wallet_service, test_user_id):
        """
        Test multiple successive top-ups.

        Expected: Each top-up correctly increases balance
        """
        # Create wallet
        await wallet_service.create_user_wallet(test_user_id, welcome_bonus=Decimal("0.00"))

        from apps.shared.integration.wallet import PaymentGateway

        # First top-up
        await wallet_service.top_up_wallet(
            user_id=test_user_id,
            amount=Decimal("10.00"),
            payment_gateway=PaymentGateway.PAYSTACK,
            payment_reference="ref_1"
        )

        balance_1 = await wallet_service.get_balance(test_user_id)
        assert balance_1 == Decimal("10.00")

        # Second top-up
        await wallet_service.top_up_wallet(
            user_id=test_user_id,
            amount=Decimal("25.00"),
            payment_gateway=PaymentGateway.STRIPE,
            payment_reference="ref_2"
        )

        balance_2 = await wallet_service.get_balance(test_user_id)
        assert balance_2 == Decimal("35.00")

        # Third top-up
        await wallet_service.top_up_wallet(
            user_id=test_user_id,
            amount=Decimal("15.00"),
            payment_gateway=PaymentGateway.PAYSTACK,
            payment_reference="ref_3"
        )

        balance_3 = await wallet_service.get_balance(test_user_id)
        assert balance_3 == Decimal("50.00")

    @pytest.mark.asyncio
    async def test_topup_for_nonexistent_user(self, wallet_service):
        """
        Test top-up for user without wallet.

        Expected: Wallet created automatically and credited
        Edge case: User doesn't have wallet yet
        """
        new_user_id = "new_user_no_wallet"

        from apps.shared.integration.wallet import PaymentGateway

        # Top up without creating wallet first
        transaction = await wallet_service.top_up_wallet(
            user_id=new_user_id,
            amount=Decimal("100.00"),
            payment_gateway=PaymentGateway.PAYSTACK,
            payment_reference="new_user_ref"
        )

        assert transaction is not None

        # Verify wallet was created and credited
        balance = await wallet_service.get_balance(new_user_id)
        # Should have welcome bonus + top-up
        assert balance >= Decimal("100.00")

    @pytest.mark.asyncio
    async def test_charge_listening_time_after_topup(self, wallet_service, test_user_id):
        """
        Test charging for listening time after wallet top-up.

        Expected: Balance decreases correctly after charge
        """
        # Create wallet and top up
        await wallet_service.create_user_wallet(test_user_id, welcome_bonus=Decimal("0.00"))

        from apps.shared.integration.wallet import PaymentGateway
        await wallet_service.top_up_wallet(
            user_id=test_user_id,
            amount=Decimal("50.00"),
            payment_gateway=PaymentGateway.STRIPE,
            payment_reference="listening_test_ref"
        )

        initial_balance = await wallet_service.get_balance(test_user_id)

        # Charge for 10 minutes of listening ($0.10/min = $1.00)
        await wallet_service.charge_listening_time(
            user_id=test_user_id,
            book_id="book_123",
            duration_minutes=10.0,
            book_title="Test Book"
        )

        # Verify balance decreased
        new_balance = await wallet_service.get_balance(test_user_id)
        assert new_balance == initial_balance - Decimal("1.00")

    @pytest.mark.asyncio
    async def test_verify_paystack_payment_without_keys(self, wallet_service):
        """
        Test Paystack payment verification without API keys.

        Expected: Returns error about missing configuration
        Failure case: Missing API keys
        """
        result = await wallet_service.verify_paystack_payment("fake_reference")

        assert result is not None
        assert result["success"] is False
        assert "error" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
