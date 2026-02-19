"""
Unit tests for ExpressPay payment integration.

Tests the wallet service ExpressPay integration using the shared ExpressPayProvider.
"""

import os
import sys
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from decimal import Decimal

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))

from apps.shared.integration.wallet import (
    Currency,
    Wallet,
    PaymentProvider,
    ProviderConfig,
    PaymentInitiationResult,
)
from apps.shared.integration.wallet.providers.expresspay_provider import ExpressPayProvider


class TestExpressPayIntegration:
    """Test ExpressPay integration with wallet service"""

    @pytest.mark.asyncio
    async def test_initiate_expresspay_topup_not_configured(self):
        """Test initiate topup when ExpressPay not configured"""
        from app.services.wallet_service import InkWaveWalletService

        wallet_service = InkWaveWalletService()
        wallet_service.initialized = True

        # Mock _get_expresspay_provider to return None (not configured)
        with patch.object(
            wallet_service, "_get_expresspay_provider", return_value=None
        ):
            with patch.object(
                wallet_service, "_get_or_create_wallet"
            ) as mock_get_wallet:
                mock_wallet = Wallet(
                    id="wallet_123",
                    user_id="user_123",
                    currency=Currency.GHS,
                    balance=Decimal("50.00"),
                )
                mock_get_wallet.return_value = mock_wallet

                result = await wallet_service.initiate_expresspay_topup(
                    user_id="user_123",
                    amount=Decimal("100.00"),
                    email="test@example.com",
                )

                assert not result["success"]
                assert result["error"] == "ExpressPay not configured"

    @pytest.mark.asyncio
    async def test_initiate_expresspay_topup_success(self):
        """Test successful ExpressPay topup initiation"""
        from app.services.wallet_service import InkWaveWalletService

        wallet_service = InkWaveWalletService()
        wallet_service.initialized = True

        # Mock wallet
        mock_wallet = Wallet(
            id="wallet_123",
            user_id="user_123",
            currency=Currency.GHS,
            balance=Decimal("50.00"),
        )

        # Mock ExpressPayProvider
        mock_provider = MagicMock(spec=ExpressPayProvider)
        mock_init_result = PaymentInitiationResult(
            success=True,
            payment_url="https://sandbox.expresspaygh.com/api/checkout.php?token=test123",
            reference="test_token_123",  # ExpressPay stores token in reference field
            amount=Decimal("100.00"),
            currency=Currency.GHS,
            gateway=PaymentProvider.EXPRESSPAY,
        )
        mock_provider.initialize_payment = AsyncMock(return_value=mock_init_result)

        with patch.object(
            wallet_service, "_get_or_create_wallet", return_value=mock_wallet
        ):
            with patch.object(
                wallet_service, "_get_expresspay_provider", return_value=mock_provider
            ):
                result = await wallet_service.initiate_expresspay_topup(
                    user_id="user_123",
                    amount=Decimal("100.00"),
                    email="test@example.com",
                    firstname="John",
                    lastname="Doe",
                    phone="0244123456",
                )

                assert result["success"]
                assert "expresspay" in result["payment_url"]
                assert result["token"] == "test_token_123"  # Token comes from reference field
                assert result["amount"] == 100.00
                assert result["currency"] == "GHS"

    @pytest.mark.asyncio
    async def test_initiate_expresspay_topup_failure(self):
        """Test failed ExpressPay topup initiation"""
        from app.services.wallet_service import InkWaveWalletService

        wallet_service = InkWaveWalletService()
        wallet_service.initialized = True

        # Mock wallet
        mock_wallet = Wallet(
            id="wallet_123",
            user_id="user_123",
            currency=Currency.GHS,
            balance=Decimal("50.00"),
        )

        # Mock ExpressPayProvider with failed result
        mock_provider = MagicMock(spec=ExpressPayProvider)
        mock_init_result = PaymentInitiationResult(
            success=False,
            reference="",
            amount=Decimal("100.00"),
            currency=Currency.GHS,
            gateway=PaymentProvider.EXPRESSPAY,
            error="Server IP not whitelisted with ExpressPay",
        )
        mock_provider.initialize_payment = AsyncMock(return_value=mock_init_result)

        with patch.object(
            wallet_service, "_get_or_create_wallet", return_value=mock_wallet
        ):
            with patch.object(
                wallet_service, "_get_expresspay_provider", return_value=mock_provider
            ):
                result = await wallet_service.initiate_expresspay_topup(
                    user_id="user_123",
                    amount=Decimal("100.00"),
                    email="test@example.com",
                )

                assert not result["success"]
                assert "not whitelisted" in result["error"]

    @pytest.mark.asyncio
    async def test_verify_expresspay_payment_success(self):
        """Test successful ExpressPay payment verification"""
        from app.services.wallet_service import InkWaveWalletService

        wallet_service = InkWaveWalletService()
        wallet_service.initialized = True

        # Mock ExpressPayProvider
        mock_provider = MagicMock(spec=ExpressPayProvider)
        mock_provider.get_transaction_status = AsyncMock(return_value={
            "result": 1,  # Approved
            "result-text": "Approved",
            "order-id": "inkwave_topup_user_123_1732540800_abc12345",
            "token": "test_token_123",
            "transaction-id": "EP123456",
            "currency": "GHS",
            "amount": 100.00,
            "date-processed": "25th November, 2025",
        })

        # Mock wallet
        mock_wallet = Wallet(
            id="wallet_456",
            user_id="user_123",
            currency=Currency.GHS,
            balance=Decimal("50.00"),
        )

        # Mock shared wallet credit
        mock_shared_wallet = MagicMock()
        mock_transaction = MagicMock()
        mock_transaction.id = "txn_123"
        mock_shared_wallet.credit = AsyncMock(return_value=mock_transaction)
        wallet_service.shared_wallet = mock_shared_wallet

        with patch.object(
            wallet_service, "_get_expresspay_provider", return_value=mock_provider
        ):
            with patch.object(
                wallet_service, "_get_or_create_wallet", return_value=mock_wallet
            ):
                result = await wallet_service.verify_expresspay_payment("test_token_123")

                assert result["success"]
                assert result["payment_data"]["status"] == "approved"
                assert result["payment_data"]["amount"] == 100.00
                assert result["payment_data"]["currency"] == "GHS"
                assert result["payment_data"]["transaction_id"] == "txn_123"

    @pytest.mark.asyncio
    async def test_verify_expresspay_payment_pending(self):
        """Test verification of pending ExpressPay transaction (mobile money)"""
        from app.services.wallet_service import InkWaveWalletService

        wallet_service = InkWaveWalletService()
        wallet_service.initialized = True

        # Mock ExpressPayProvider with pending status
        mock_provider = MagicMock(spec=ExpressPayProvider)
        mock_provider.get_transaction_status = AsyncMock(return_value={
            "result": 4,  # Pending
            "result-text": "Pending",
            "order-id": "inkwave_topup_user_123_1732540800_abc12345",
            "token": "test_token_123",
        })

        with patch.object(
            wallet_service, "_get_expresspay_provider", return_value=mock_provider
        ):
            result = await wallet_service.verify_expresspay_payment("test_token_123")

            assert not result["success"]
            assert result["status"] == "pending"
            assert "still being processed" in result["error"]
            assert result["payment_data"]["status"] == "pending"

    @pytest.mark.asyncio
    async def test_verify_expresspay_payment_declined(self):
        """Test verification of declined ExpressPay transaction"""
        from app.services.wallet_service import InkWaveWalletService

        wallet_service = InkWaveWalletService()
        wallet_service.initialized = True

        # Mock ExpressPayProvider with declined status
        mock_provider = MagicMock(spec=ExpressPayProvider)
        mock_provider.get_transaction_status = AsyncMock(return_value={
            "result": 2,  # Declined
            "result-text": "Insufficient funds",
            "order-id": "inkwave_topup_user_123_1732540800_abc12345",
            "token": "test_token_123",
        })

        with patch.object(
            wallet_service, "_get_expresspay_provider", return_value=mock_provider
        ):
            result = await wallet_service.verify_expresspay_payment("test_token_123")

            assert not result["success"]
            assert "Insufficient funds" in result["error"]
            assert result["payment_data"]["status"] == "failed"
            assert result["payment_data"]["result_code"] == 2

    @pytest.mark.asyncio
    async def test_verify_expresspay_payment_invalid_order_id(self):
        """Test verification when order_id doesn't match expected pattern"""
        from app.services.wallet_service import InkWaveWalletService

        wallet_service = InkWaveWalletService()
        wallet_service.initialized = True

        # Mock ExpressPayProvider with approved but invalid order_id
        mock_provider = MagicMock(spec=ExpressPayProvider)
        mock_provider.get_transaction_status = AsyncMock(return_value={
            "result": 1,  # Approved
            "result-text": "Approved",
            "order-id": "external_order_123",  # Doesn't match our pattern
            "token": "test_token_123",
            "transaction-id": "EP123456",
            "currency": "GHS",
            "amount": 100.00,
        })

        with patch.object(
            wallet_service, "_get_expresspay_provider", return_value=mock_provider
        ):
            result = await wallet_service.verify_expresspay_payment("test_token_123")

            assert not result["success"]
            assert "could not identify user" in result["error"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
