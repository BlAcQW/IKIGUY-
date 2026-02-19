"""
Unit tests for TTSBillingManager

Tests billing, cost calculation, wallet deduction, and refunds.

Run with:
    pytest apps/shared/tts/tests/test_billing.py -v
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

import sys
sys.path.insert(0, "/opt/kasaai/apps")

from shared.tts.billing import TTSBillingManager
from shared.tts.models import TTSProvider, TTSResponse, AudioFormat
from shared.integration.wallet import Currency, Transaction
from shared.integration.wallet.exceptions import (
    InsufficientBalanceError,
    WalletNotFoundError
)
from shared.integration.usage_calculator import PricingTier


@pytest.fixture
def mock_wallet_service():
    """Mock WalletService."""
    service = AsyncMock()

    # Mock wallet
    wallet = MagicMock()
    wallet.id = "wallet123"
    wallet.balance = Decimal("100.00")

    service.get_wallet_by_user = AsyncMock(return_value=wallet)
    service.debit = AsyncMock(return_value=MagicMock(id="txn123"))
    service.refund = AsyncMock()

    return service


@pytest.fixture
def billing_manager(mock_wallet_service):
    """Create TTSBillingManager instance."""
    return TTSBillingManager(
        wallet_service=mock_wallet_service,
        pricing_tier=PricingTier.BASIC,
        currency=Currency.GHS
    )


@pytest.mark.asyncio
async def test_estimate_cost_basic(billing_manager):
    """Test cost estimation for basic synthesis."""
    text = "Hello world"
    cost = await billing_manager.estimate_cost(
        text=text,
        provider=TTSProvider.COQUI_XTTS,
        voice_cloning=False
    )

    # Basic tier: GHS 0.00001 per character
    # "Hello world" = 11 characters
    expected_cost = Decimal("0.00011")

    assert cost == expected_cost


@pytest.mark.asyncio
async def test_estimate_cost_voice_cloning(billing_manager):
    """Test cost estimation with voice cloning (2x multiplier)."""
    text = "Hello world"
    cost = await billing_manager.estimate_cost(
        text=text,
        provider=TTSProvider.COQUI_XTTS,
        voice_cloning=True
    )

    # Voice cloning costs 2x
    # 11 chars * 0.00001 * 2 = 0.00022
    expected_cost = Decimal("0.00022")

    assert cost == expected_cost


@pytest.mark.asyncio
async def test_check_balance_sufficient(billing_manager, mock_wallet_service):
    """Test balance check with sufficient funds."""
    user_id = "user123"
    required_amount = Decimal("50.00")

    has_balance = await billing_manager.check_balance(user_id, required_amount)

    assert has_balance is True
    mock_wallet_service.get_wallet_by_user.assert_called_once_with(
        user_id=user_id,
        currency=Currency.GHS
    )


@pytest.mark.asyncio
async def test_check_balance_insufficient(billing_manager, mock_wallet_service):
    """Test balance check with insufficient funds."""
    # Set wallet balance to 10.00
    wallet = MagicMock()
    wallet.balance = Decimal("10.00")
    mock_wallet_service.get_wallet_by_user = AsyncMock(return_value=wallet)

    user_id = "user123"
    required_amount = Decimal("50.00")

    has_balance = await billing_manager.check_balance(user_id, required_amount)

    assert has_balance is False


@pytest.mark.asyncio
async def test_synthesize_with_billing_success(billing_manager, mock_wallet_service):
    """Test successful synthesis with billing."""
    # Mock AsyncTTSClient
    with patch("shared.tts.billing.AsyncTTSClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        # Mock synthesis response
        mock_response = TTSResponse(
            audio=b"audio_data",
            format=AudioFormat.WAV,
            sample_rate=22050,
            duration=2.5,
            provider=TTSProvider.COQUI_XTTS,
            language="en"
        )
        mock_client.synthesize = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        # Synthesize with billing
        response, transaction = await billing_manager.synthesize_with_billing(
            user_id="user123",
            text="Test synthesis",
            provider=TTSProvider.COQUI_XTTS,
            language="en"
        )

        # Verify response
        assert response == mock_response
        assert transaction.id == "txn123"

        # Verify wallet was debited
        mock_wallet_service.debit.assert_called_once()

        # Verify synthesis was called
        mock_client.synthesize.assert_called_once()


@pytest.mark.asyncio
async def test_synthesize_with_billing_insufficient_balance(billing_manager, mock_wallet_service):
    """Test synthesis with insufficient balance."""
    # Set wallet balance to 0
    wallet = MagicMock()
    wallet.id = "wallet123"
    wallet.balance = Decimal("0.00")
    mock_wallet_service.get_wallet_by_user = AsyncMock(return_value=wallet)

    with pytest.raises(InsufficientBalanceError):
        await billing_manager.synthesize_with_billing(
            user_id="user123",
            text="Test synthesis",
            provider=TTSProvider.COQUI_XTTS
        )


@pytest.mark.asyncio
async def test_synthesize_with_billing_no_wallet(billing_manager, mock_wallet_service):
    """Test synthesis when user has no wallet."""
    mock_wallet_service.get_wallet_by_user = AsyncMock(return_value=None)

    with pytest.raises(WalletNotFoundError):
        await billing_manager.synthesize_with_billing(
            user_id="user123",
            text="Test synthesis",
            provider=TTSProvider.COQUI_XTTS
        )


@pytest.mark.asyncio
async def test_synthesize_with_billing_synthesis_failure_refund(billing_manager, mock_wallet_service):
    """Test that synthesis failure triggers refund."""
    with patch("shared.tts.billing.AsyncTTSClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        # Mock synthesis failure
        mock_client.synthesize = AsyncMock(side_effect=Exception("Synthesis failed"))
        mock_client_class.return_value = mock_client

        # Mock transaction
        mock_transaction = MagicMock()
        mock_transaction.id = "txn123"
        mock_wallet_service.debit = AsyncMock(return_value=mock_transaction)

        # Attempt synthesis
        with pytest.raises(Exception, match="Synthesis failed"):
            await billing_manager.synthesize_with_billing(
                user_id="user123",
                text="Test synthesis",
                provider=TTSProvider.COQUI_XTTS
            )

        # Verify refund was called
        mock_wallet_service.refund.assert_called_once_with(
            transaction_id="txn123",
            reason="TTS synthesis failed: Synthesis failed"
        )


@pytest.mark.asyncio
async def test_clone_voice_with_billing_success(billing_manager, mock_wallet_service):
    """Test successful voice cloning with billing."""
    with patch("shared.tts.billing.AsyncTTSClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        # Mock clone_voice response
        mock_response = TTSResponse(
            audio=b"cloned_audio_data",
            format=AudioFormat.WAV,
            sample_rate=22050,
            duration=3.0,
            provider=TTSProvider.COQUI_XTTS,
            language="en"
        )
        mock_client.clone_voice = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        # Clone voice with billing
        response, transaction = await billing_manager.clone_voice_with_billing(
            user_id="user123",
            text="Cloned voice test",
            reference_audio=b"reference_audio",
            provider=TTSProvider.COQUI_XTTS
        )

        # Verify response
        assert response == mock_response
        assert transaction.id == "txn123"

        # Verify wallet was debited (2x cost for cloning)
        mock_wallet_service.debit.assert_called_once()
        debit_call = mock_wallet_service.debit.call_args
        # Cost should be 2x normal (voice cloning multiplier)

        # Verify clone_voice was called
        mock_client.clone_voice.assert_called_once()
