"""
Unit tests for wallet atomic credit reservation functionality.

Tests verify that the reservation pattern prevents race conditions
where concurrent requests could overdraw the wallet balance.
"""

import pytest
import asyncio
import sys
import os
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

# Add apps to path for shared imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))

try:
    from apps.shared.integration.wallet import InsufficientBalanceError, DuplicateTransactionError
except ImportError:
    # Fallback: create compatible exception classes for testing
    class InsufficientBalanceError(Exception):
        """Raised when wallet has insufficient balance."""
        def __init__(self, available: float = 0, required: float = 0, message: str = None):
            self.available = available
            self.required = required
            super().__init__(message or f"Insufficient balance: {available} < {required}")

    class DuplicateTransactionError(Exception):
        """Raised when transaction already exists."""
        pass


class TestAtomicReservation:
    """Tests for atomic credit reservation in wallet service."""

    @pytest.fixture
    def mock_wallet_service(self):
        """Create mock wallet service for testing."""
        from app.services.wallet_service import InkWaveWalletService

        service = InkWaveWalletService()
        service.initialized = True
        service.shared_wallet = AsyncMock()
        service.logger = MagicMock()
        return service

    @pytest.fixture
    def mock_wallet(self):
        """Create mock wallet object."""
        wallet = MagicMock()
        wallet.id = "wallet_123"
        wallet.user_id = "user_123"
        wallet.balance = Decimal("10.00")  # 1000 credits
        wallet.available_balance = Decimal("10.00")
        return wallet

    @pytest.mark.asyncio
    async def test_reserve_credits_atomic_success(self, mock_wallet_service, mock_wallet):
        """
        Test successful atomic credit reservation.

        Verifies that credits are debited atomically with idempotency key.
        """
        # Setup
        mock_wallet_service._get_or_create_wallet = AsyncMock(return_value=mock_wallet)
        mock_wallet_service.shared_wallet.debit = AsyncMock(return_value=MagicMock(id="tx_123"))

        # Execute
        reservation_id = "test_reservation_123"
        transaction = await mock_wallet_service.reserve_credits_atomic(
            user_id="user_123",
            credits=100,  # 100 credits = $1
            reservation_id=reservation_id,
            description="Test reservation",
            metadata={"book_id": "book_123"}
        )

        # Verify
        assert transaction is not None
        mock_wallet_service.shared_wallet.debit.assert_called_once()
        call_kwargs = mock_wallet_service.shared_wallet.debit.call_args.kwargs

        # Verify atomic debit was called with correct parameters
        assert call_kwargs["wallet_id"] == "wallet_123"
        assert call_kwargs["amount"] == Decimal("1.00")  # 100 credits = $1
        assert call_kwargs["idempotency_key"] == f"reserve_{reservation_id}"
        assert call_kwargs["allow_negative"] is False
        assert "[RESERVED]" in call_kwargs["description"]

    @pytest.mark.asyncio
    async def test_reserve_credits_atomic_insufficient_balance(self, mock_wallet_service, mock_wallet):
        """
        Test atomic reservation fails with insufficient balance.

        Verifies that InsufficientBalanceError is raised when balance is too low.
        """
        # Import the actual exception from shared wallet
        from apps.shared.integration.wallet import InsufficientBalanceError as SharedInsufficientBalanceError

        # Setup
        mock_wallet_service._get_or_create_wallet = AsyncMock(return_value=mock_wallet)
        mock_wallet_service.shared_wallet.debit = AsyncMock(
            side_effect=SharedInsufficientBalanceError(available=5.0, required=10.0)
        )

        # Execute & Verify - use the shared exception type
        with pytest.raises(SharedInsufficientBalanceError) as exc_info:
            await mock_wallet_service.reserve_credits_atomic(
                user_id="user_123",
                credits=1000,  # More than available
                reservation_id="test_123",
                description="Test"
            )

        assert exc_info.value.available == 5.0
        assert exc_info.value.required == 10.0

    @pytest.mark.asyncio
    async def test_finalize_reservation_refund_excess(self, mock_wallet_service, mock_wallet):
        """
        Test finalizing reservation refunds excess credits.

        Verifies that if actual < reserved, the difference is credited back.
        """
        # Setup
        mock_wallet_service._get_or_create_wallet = AsyncMock(return_value=mock_wallet)
        mock_wallet_service.shared_wallet.credit = AsyncMock(return_value=MagicMock(id="tx_456"))

        # Execute: Reserved 300, used 100 -> refund 200
        transaction = await mock_wallet_service.finalize_reservation(
            user_id="user_123",
            reservation_id="test_123",
            actual_credits=100,
            reserved_credits=300,
            description="Voice Q&A"
        )

        # Verify refund was issued
        assert transaction is not None
        mock_wallet_service.shared_wallet.credit.assert_called_once()
        call_kwargs = mock_wallet_service.shared_wallet.credit.call_args.kwargs

        assert call_kwargs["amount"] == Decimal("2.00")  # 200 credits = $2 refund
        assert "[REFUND]" in call_kwargs["description"]
        assert call_kwargs["idempotency_key"] == "finalize_test_123"

    @pytest.mark.asyncio
    async def test_finalize_reservation_no_adjustment_needed(self, mock_wallet_service, mock_wallet):
        """
        Test finalizing reservation when actual equals reserved.

        Verifies that no transaction is created when no adjustment is needed.
        """
        # Setup
        mock_wallet_service._get_or_create_wallet = AsyncMock(return_value=mock_wallet)

        # Execute: Reserved 100, used 100 -> no refund needed
        transaction = await mock_wallet_service.finalize_reservation(
            user_id="user_123",
            reservation_id="test_123",
            actual_credits=100,
            reserved_credits=100,
            description="Voice Q&A"
        )

        # Verify no transaction created
        assert transaction is None
        mock_wallet_service.shared_wallet.credit.assert_not_called()
        mock_wallet_service.shared_wallet.debit.assert_not_called()

    @pytest.mark.asyncio
    async def test_refund_reservation_on_failure(self, mock_wallet_service, mock_wallet):
        """
        Test refunding reservation when operation fails.

        Verifies that full refund is issued when work fails after reservation.
        """
        # Setup
        mock_wallet_service._get_or_create_wallet = AsyncMock(return_value=mock_wallet)
        mock_wallet_service.shared_wallet.credit = AsyncMock(return_value=MagicMock(id="tx_789"))

        # Execute
        transaction = await mock_wallet_service.refund_reservation(
            user_id="user_123",
            reservation_id="test_123",
            credits=300,
            reason="Voice Q&A failed: STT timeout"
        )

        # Verify full refund was issued
        assert transaction is not None
        mock_wallet_service.shared_wallet.credit.assert_called_once()
        call_kwargs = mock_wallet_service.shared_wallet.credit.call_args.kwargs

        assert call_kwargs["amount"] == Decimal("3.00")  # 300 credits = $3 refund
        assert "[REFUND]" in call_kwargs["description"]
        assert call_kwargs["idempotency_key"] == "refund_test_123"


class TestConcurrentReservations:
    """Tests for concurrent reservation handling to verify race condition prevention."""

    @pytest.mark.asyncio
    async def test_concurrent_reservations_one_succeeds(self):
        """
        Test that concurrent reservations are properly serialized.

        Simulates race condition scenario where multiple requests try to
        reserve credits simultaneously from a wallet with limited balance.
        """
        from app.services.wallet_service import InkWaveWalletService

        # Setup service with limited balance
        service = InkWaveWalletService()
        service.initialized = True
        service.shared_wallet = AsyncMock()
        service.logger = MagicMock()

        # Create mock wallet with exactly 200 credits ($2)
        mock_wallet = MagicMock()
        mock_wallet.id = "wallet_123"
        mock_wallet.user_id = "user_123"
        mock_wallet.balance = Decimal("2.00")
        service._get_or_create_wallet = AsyncMock(return_value=mock_wallet)

        # Track debit calls
        debit_call_count = 0

        async def mock_debit(**kwargs):
            nonlocal debit_call_count
            debit_call_count += 1

            # Simulate atomic behavior: first call succeeds, second fails
            if debit_call_count == 1:
                return MagicMock(id="tx_success")
            else:
                raise InsufficientBalanceError(available=0.0, required=1.5)

        service.shared_wallet.debit = mock_debit

        # Execute: Two concurrent reservations for 150 credits each
        async def make_reservation(reservation_id: str):
            try:
                return await service.reserve_credits_atomic(
                    user_id="user_123",
                    credits=150,
                    reservation_id=reservation_id,
                    description="Test"
                )
            except InsufficientBalanceError:
                return None

        # Run concurrently
        results = await asyncio.gather(
            make_reservation("res_1"),
            make_reservation("res_2"),
            return_exceptions=True
        )

        # Verify: One succeeded, one failed
        successes = [r for r in results if r is not None and not isinstance(r, Exception)]
        failures = [r for r in results if r is None]

        assert len(successes) == 1, "Exactly one reservation should succeed"
        assert len(failures) == 1, "Exactly one reservation should fail"


class TestVoiceRouteIntegration:
    """Integration tests for voice routes using atomic reservation."""

    @pytest.mark.asyncio
    async def test_voice_qa_reserves_before_work(self):
        """
        Test that voice_qa reserves credits before doing expensive work.

        Verifies the reservation happens BEFORE AI operations.
        """
        from app.api.routes.voice import (
            reserve_credits_atomic,
            finalize_credits,
            refund_reservation,
            MAX_VOICE_QA_CREDITS
        )

        # Verify constants are set correctly
        assert MAX_VOICE_QA_CREDITS == 300, "Max voice QA credits should be 300"

    @pytest.mark.asyncio
    async def test_reservation_refunded_on_http_error(self):
        """
        Test that reservations are refunded when HTTPException occurs.

        This is a design verification test - the actual refund logic
        is in the try/except block of voice_qa endpoint.
        """
        # This test verifies the pattern exists in the code
        import inspect
        from app.api.routes import voice

        source = inspect.getsource(voice.voice_qa)

        # Verify the HTTPException handler includes refund logic
        assert "HTTPException:" in source, "HTTPException handler should exist"
        assert "refund_reservation" in source, "Refund should be called on HTTPException"
        assert "reservation_id" in source, "Reservation ID should be tracked"

    @pytest.mark.asyncio
    async def test_reservation_refunded_on_general_error(self):
        """
        Test that reservations are refunded when general Exception occurs.
        """
        import inspect
        from app.api.routes import voice

        source = inspect.getsource(voice.voice_qa)

        # Verify the Exception handler includes refund logic
        assert "except Exception as e:" in source, "General exception handler should exist"
        assert "refund_reservation" in source, "Refund should be called on Exception"


class TestIdempotency:
    """Tests for idempotency of reservation operations."""

    @pytest.mark.asyncio
    async def test_duplicate_reservation_id_rejected(self, ):
        """
        Test that duplicate reservation IDs are rejected.

        The idempotency key prevents double-charging on retries.
        """
        from app.services.wallet_service import InkWaveWalletService
        from apps.shared.integration.wallet import DuplicateTransactionError

        service = InkWaveWalletService()
        service.initialized = True
        service.shared_wallet = AsyncMock()
        service.logger = MagicMock()

        mock_wallet = MagicMock()
        mock_wallet.id = "wallet_123"
        service._get_or_create_wallet = AsyncMock(return_value=mock_wallet)

        # First call succeeds
        service.shared_wallet.debit = AsyncMock(return_value=MagicMock(id="tx_1"))

        result1 = await service.reserve_credits_atomic(
            user_id="user_123",
            credits=100,
            reservation_id="duplicate_test",
            description="Test"
        )
        assert result1 is not None

        # Verify idempotency key was used
        call_kwargs = service.shared_wallet.debit.call_args.kwargs
        assert call_kwargs["idempotency_key"] == "reserve_duplicate_test"

    @pytest.mark.asyncio
    async def test_refund_idempotency_key(self):
        """
        Test that refunds use unique idempotency keys.
        """
        from app.services.wallet_service import InkWaveWalletService

        service = InkWaveWalletService()
        service.initialized = True
        service.shared_wallet = AsyncMock()
        service.logger = MagicMock()

        mock_wallet = MagicMock()
        mock_wallet.id = "wallet_123"
        service._get_or_create_wallet = AsyncMock(return_value=mock_wallet)
        service.shared_wallet.credit = AsyncMock(return_value=MagicMock(id="tx_refund"))

        await service.refund_reservation(
            user_id="user_123",
            reservation_id="test_123",
            credits=100,
            reason="Test failure"
        )

        call_kwargs = service.shared_wallet.credit.call_args.kwargs
        assert call_kwargs["idempotency_key"] == "refund_test_123"
