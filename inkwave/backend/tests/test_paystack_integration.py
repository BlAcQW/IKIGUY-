"""
Unit tests for Paystack payment integration.

Tests the wallet service Paystack integration using the shared PaystackProvider.
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
from apps.shared.integration.wallet.providers.paystack import PaystackProvider


class TestSharedPaystackProvider:
    """Test shared PaystackProvider functionality"""

    def test_provider_initialization_with_valid_config(self):
        """Test PaystackProvider initialization with valid config"""
        config = ProviderConfig(
            provider=PaymentProvider.PAYSTACK,
            secret_key="sk_test_abc123",
            webhook_secret="whsec_test",
            is_active=True,
        )

        provider = PaystackProvider(config)
        assert provider is not None
        assert provider.config.secret_key == "sk_test_abc123"

    def test_provider_initialization_with_invalid_key(self):
        """Test PaystackProvider initialization with invalid secret key"""
        config = ProviderConfig(
            provider=PaymentProvider.PAYSTACK,
            secret_key="invalid_key",  # Doesn't start with sk_
            is_active=True,
        )

        # Should raise ValidationError because key doesn't start with sk_
        with pytest.raises(Exception):  # ValidationError
            PaystackProvider(config)

    def test_currency_conversion_to_minor_units(self):
        """Test currency conversion to minor units (pesewas/kobo)"""
        config = ProviderConfig(
            provider=PaymentProvider.PAYSTACK,
            secret_key="sk_test_abc123",
            is_active=True,
        )
        provider = PaystackProvider(config)

        # 100 GHS = 10000 pesewas
        assert provider._convert_to_minor_unit(Decimal("100.00"), Currency.GHS) == 10000

        # 50.50 GHS = 5050 pesewas
        assert provider._convert_to_minor_unit(Decimal("50.50"), Currency.GHS) == 5050

        # 1 GHS = 100 pesewas
        assert provider._convert_to_minor_unit(Decimal("1.00"), Currency.GHS) == 100

    def test_currency_conversion_from_minor_units(self):
        """Test currency conversion from minor units (pesewas/kobo)"""
        config = ProviderConfig(
            provider=PaymentProvider.PAYSTACK,
            secret_key="sk_test_abc123",
            is_active=True,
        )
        provider = PaystackProvider(config)

        # 10000 pesewas = 100 GHS
        assert provider._convert_from_minor_unit(10000, Currency.GHS) == Decimal("100.00")

        # 5050 pesewas = 50.50 GHS
        assert provider._convert_from_minor_unit(5050, Currency.GHS) == Decimal("50.50")


class TestPaystackIntegration:
    """Test Paystack integration with wallet service"""

    @pytest.mark.asyncio
    async def test_initiate_paystack_topup_not_configured(self):
        """Test initiate topup when Paystack not configured"""
        from app.services.wallet_service import InkWaveWalletService

        wallet_service = InkWaveWalletService()
        wallet_service.initialized = True

        # Mock _get_paystack_provider to return None (not configured)
        with patch.object(
            wallet_service, "_get_paystack_provider", return_value=None
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

                result = await wallet_service.initiate_paystack_topup(
                    user_id="user_123",
                    amount=Decimal("100.00"),
                    email="test@example.com",
                )

                assert not result["success"]
                assert result["error"] == "Paystack not configured"

    @pytest.mark.asyncio
    async def test_initiate_paystack_topup_success(self):
        """Test successful Paystack topup initiation"""
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

        # Mock PaystackProvider
        mock_provider = MagicMock(spec=PaystackProvider)
        mock_init_result = PaymentInitiationResult(
            success=True,
            payment_url="https://checkout.paystack.com/test123",
            reference="test_ref_123",
            amount=Decimal("100.00"),
            currency=Currency.GHS,
            gateway=PaymentProvider.PAYSTACK,
        )
        mock_provider.initialize_payment = AsyncMock(return_value=mock_init_result)

        with patch.object(
            wallet_service, "_get_or_create_wallet", return_value=mock_wallet
        ):
            with patch.object(
                wallet_service, "_get_paystack_provider", return_value=mock_provider
            ):
                result = await wallet_service.initiate_paystack_topup(
                    user_id="user_123",
                    amount=Decimal("100.00"),
                    email="test@example.com",
                    callback_url="https://example.com/callback",
                )

                assert result["success"]
                assert result["payment_url"] == "https://checkout.paystack.com/test123"
                assert result["reference"] == "test_ref_123"
                assert result["amount"] == 100.00
                assert result["currency"] == "GHS"

    @pytest.mark.asyncio
    async def test_initiate_paystack_topup_failure(self):
        """Test failed Paystack topup initiation"""
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

        # Mock PaystackProvider with failed result
        mock_provider = MagicMock(spec=PaystackProvider)
        mock_init_result = PaymentInitiationResult(
            success=False,
            reference="",
            amount=Decimal("100.00"),
            currency=Currency.GHS,
            gateway=PaymentProvider.PAYSTACK,
            error="Invalid email address",
        )
        mock_provider.initialize_payment = AsyncMock(return_value=mock_init_result)

        with patch.object(
            wallet_service, "_get_or_create_wallet", return_value=mock_wallet
        ):
            with patch.object(
                wallet_service, "_get_paystack_provider", return_value=mock_provider
            ):
                result = await wallet_service.initiate_paystack_topup(
                    user_id="user_123",
                    amount=Decimal("100.00"),
                    email="invalid_email",
                )

                assert not result["success"]
                assert "Invalid email address" in result["error"]

    @pytest.mark.asyncio
    async def test_verify_paystack_payment_success(self):
        """Test successful Paystack payment verification"""
        from app.services.wallet_service import InkWaveWalletService

        wallet_service = InkWaveWalletService()
        wallet_service.initialized = True

        # Mock PaystackProvider
        mock_provider = MagicMock(spec=PaystackProvider)
        mock_provider.get_transaction_status = AsyncMock(return_value={
            "status": "success",
            "reference": "test_ref_123",
            "amount": Decimal("100.00"),
            "currency": "GHS",
            "channel": "card",
            "paid_at": "2025-11-25T10:30:00Z",
            "customer": {"email": "test@example.com"},
            "metadata": {
                "user_id": "user_123",
                "wallet_id": "wallet_456",
            },
        })

        # Mock shared wallet credit
        mock_shared_wallet = MagicMock()
        mock_transaction = MagicMock()
        mock_transaction.id = "txn_123"
        mock_shared_wallet.credit = AsyncMock(return_value=mock_transaction)
        wallet_service.shared_wallet = mock_shared_wallet

        with patch.object(
            wallet_service, "_get_paystack_provider", return_value=mock_provider
        ):
            result = await wallet_service.verify_paystack_payment("test_ref_123")

            assert result["success"]
            assert result["payment_data"]["status"] == "success"
            assert result["payment_data"]["amount"] == 100.00
            assert result["payment_data"]["currency"] == "GHS"
            assert result["payment_data"]["transaction_id"] == "txn_123"

    @pytest.mark.asyncio
    async def test_verify_paystack_payment_not_paid(self):
        """Test verification of unpaid Paystack transaction"""
        from app.services.wallet_service import InkWaveWalletService

        wallet_service = InkWaveWalletService()
        wallet_service.initialized = True

        # Mock PaystackProvider with pending status
        mock_provider = MagicMock(spec=PaystackProvider)
        mock_provider.get_transaction_status = AsyncMock(return_value={
            "status": "pending",
            "reference": "test_ref_123",
        })

        with patch.object(
            wallet_service, "_get_paystack_provider", return_value=mock_provider
        ):
            result = await wallet_service.verify_paystack_payment("test_ref_123")

            assert not result["success"]
            assert "not completed" in result["error"]
            assert result["payment_data"]["status"] == "pending"

    @pytest.mark.asyncio
    async def test_verify_paystack_payment_missing_metadata(self):
        """Test verification when metadata is missing user/wallet info"""
        from app.services.wallet_service import InkWaveWalletService

        wallet_service = InkWaveWalletService()
        wallet_service.initialized = True

        # Mock PaystackProvider with success but no metadata
        mock_provider = MagicMock(spec=PaystackProvider)
        mock_provider.get_transaction_status = AsyncMock(return_value={
            "status": "success",
            "reference": "test_ref_123",
            "amount": Decimal("100.00"),
            "currency": "GHS",
            "metadata": {},  # Empty metadata
        })

        with patch.object(
            wallet_service, "_get_paystack_provider", return_value=mock_provider
        ):
            result = await wallet_service.verify_paystack_payment("test_ref_123")

            assert not result["success"]
            assert "Invalid transaction metadata" in result["error"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
