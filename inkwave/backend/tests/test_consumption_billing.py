"""
Tests for consumption billing integration.

Verifies that progress updates correctly charge credits for listening time.
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.api.routes.consumption import update_progress
from app.models.consumption import (
    ProgressUpdateRequest,
    ConsumptionMode,
)
from app.core.config import settings


class MockTransaction:
    """Mock transaction returned by wallet service."""
    def __init__(self, amount: Decimal):
        self.amount = amount


class MockCurrentUser:
    """Mock authenticated user."""
    def __init__(self, user_id: str = "test-user-123"):
        self.user_id = user_id


@pytest.fixture
def mock_user():
    """Create a mock authenticated user."""
    return MockCurrentUser()


@pytest.fixture
def progress_request():
    """Create a valid progress update request."""
    return ProgressUpdateRequest(
        session_id="test-session-123",
        book_id="test-book-456",
        consumption_mode=ConsumptionMode.AUDIO_PLAYBACK,
        chunk_index=5,
        position_seconds=120.5,
        duration_since_last_update=30.0,  # 30 seconds of listening
        cumulative_time_seconds=300.0,
        total_chunks=20,
        is_final_chunk=False,
    )


class TestConsumptionBilling:
    """Test suite for consumption billing."""

    @pytest.mark.asyncio
    async def test_progress_update_charges_credits(
        self,
        mock_user,
        progress_request,
    ):
        """Test that progress updates charge credits based on duration."""
        # Expected billing calculation:
        # duration_minutes = 30 / 60 = 0.5 minutes
        # credits = 0.5 * 2 (PRICING_NARRATION_PER_MINUTE) = 1 credit
        # cost = 1 / 100 = $0.01
        expected_credits = 0.5 * settings.PRICING_NARRATION_PER_MINUTE
        expected_cost = Decimal(str(expected_credits)) / Decimal("100")

        with patch('app.api.routes.consumption.consumption_service') as mock_consumption:
            with patch('app.api.routes.consumption.wallet_service') as mock_wallet:
                # Mock consumption service
                mock_event = MagicMock()
                mock_event.event_id = "event-123"
                mock_event.progress_percentage = 25.0
                mock_event.cumulative_time_seconds = 300.0
                mock_consumption.record_progress_update = AsyncMock(return_value=mock_event)

                # Mock wallet service to return successful transaction
                mock_transaction = MockTransaction(amount=expected_cost)
                mock_wallet.charge_listening_time = AsyncMock(return_value=mock_transaction)

                # Call the endpoint
                result = await update_progress(progress_request, mock_user)

                # Verify consumption service was called
                mock_consumption.record_progress_update.assert_called_once()

                # Verify wallet service was called with correct parameters
                mock_wallet.charge_listening_time.assert_called_once_with(
                    user_id="test-user-123",
                    book_id="test-book-456",
                    duration_minutes=0.5,  # 30 seconds / 60
                    book_title=None,
                )

                # Verify response includes billing info
                assert "billing" in result
                assert result["billing"]["duration_seconds"] == 30.0
                assert result["billing"]["duration_minutes"] == 0.5
                assert result["billing"]["credits_charged"] == float(expected_cost)
                assert result["billing"]["billing_success"] is True

    @pytest.mark.asyncio
    async def test_progress_update_handles_billing_failure(
        self,
        mock_user,
        progress_request,
    ):
        """Test that progress update succeeds even if billing fails."""
        with patch('app.api.routes.consumption.consumption_service') as mock_consumption:
            with patch('app.api.routes.consumption.wallet_service') as mock_wallet:
                # Mock consumption service
                mock_event = MagicMock()
                mock_event.event_id = "event-123"
                mock_event.progress_percentage = 25.0
                mock_event.cumulative_time_seconds = 300.0
                mock_consumption.record_progress_update = AsyncMock(return_value=mock_event)

                # Mock wallet service to return None (billing failed)
                mock_wallet.charge_listening_time = AsyncMock(return_value=None)

                # Call the endpoint
                result = await update_progress(progress_request, mock_user)

                # Verify progress update still succeeded
                assert result["message"] == "Progress updated"
                assert result["event_id"] == "event-123"

                # Verify billing info shows failure
                assert result["billing"]["billing_success"] is False
                assert result["billing"]["credits_charged"] == 0.0

    @pytest.mark.asyncio
    async def test_progress_update_zero_duration_no_charge(
        self,
        mock_user,
    ):
        """Test that zero duration doesn't trigger billing."""
        zero_duration_request = ProgressUpdateRequest(
            session_id="test-session-123",
            book_id="test-book-456",
            consumption_mode=ConsumptionMode.AUDIO_PLAYBACK,
            chunk_index=5,
            position_seconds=120.5,
            duration_since_last_update=0.0,  # Zero duration
            cumulative_time_seconds=300.0,
            total_chunks=20,
            is_final_chunk=False,
        )

        with patch('app.api.routes.consumption.consumption_service') as mock_consumption:
            with patch('app.api.routes.consumption.wallet_service') as mock_wallet:
                # Mock consumption service
                mock_event = MagicMock()
                mock_event.event_id = "event-123"
                mock_event.progress_percentage = 25.0
                mock_event.cumulative_time_seconds = 300.0
                mock_consumption.record_progress_update = AsyncMock(return_value=mock_event)

                # Call the endpoint
                result = await update_progress(zero_duration_request, mock_user)

                # Verify wallet service was NOT called
                mock_wallet.charge_listening_time.assert_not_called()

                # Verify billing info shows no charge
                assert result["billing"]["credits_charged"] == 0.0
                assert result["billing"]["billing_success"] is False  # No billing attempted

    @pytest.mark.asyncio
    async def test_billing_uses_config_pricing(self):
        """Test that billing uses pricing from config, not hardcoded values."""
        # Verify config values are accessible
        assert hasattr(settings, 'PRICING_NARRATION_PER_MINUTE')
        assert settings.PRICING_NARRATION_PER_MINUTE == 2  # 2 credits per minute

        # Calculate expected cost for 1 minute of listening
        duration_minutes = 1.0
        expected_credits = duration_minutes * settings.PRICING_NARRATION_PER_MINUTE
        expected_cost = expected_credits / 100  # 100 credits = $1

        assert expected_credits == 2.0  # 2 credits for 1 minute
        assert expected_cost == 0.02  # $0.02 for 1 minute


class TestPricingConsistency:
    """Test pricing consistency between frontend and backend."""

    def test_pricing_matches_frontend_constants(self):
        """Verify backend pricing matches frontend PRICING constants."""
        # Frontend constants (from frontend/src/config/constants.ts):
        # NARRATION_PER_MINUTE: 0.02  ($0.02 per minute)
        # CREDITS_PER_DOLLAR: 100    (100 credits = $1)

        # Backend config:
        backend_credits_per_minute = settings.PRICING_NARRATION_PER_MINUTE  # 2 credits

        # Calculate dollar cost per minute from backend
        backend_cost_per_minute = backend_credits_per_minute / 100  # $0.02

        # This should match frontend's NARRATION_PER_MINUTE: 0.02
        assert backend_cost_per_minute == 0.02, (
            f"Backend cost ${backend_cost_per_minute}/min doesn't match "
            f"frontend's $0.02/min"
        )
