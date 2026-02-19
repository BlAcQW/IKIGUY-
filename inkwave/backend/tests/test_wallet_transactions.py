"""
Unit tests for wallet transaction history.

Tests transaction listing and formatting.
"""

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from app.models.user import UserInDB


class MockTransaction:
    """Mock transaction object for testing."""

    def __init__(
        self,
        id: str,
        type_value: str,
        amount: Decimal,
        description: str,
        created_at: datetime,
        metadata: dict = None
    ):
        self.id = id
        self.type = Mock(value=type_value)
        self.amount = amount
        self.description = description
        self.created_at = created_at
        self.metadata = metadata or {}


class TestWalletTransactions:
    """Test cases for wallet transaction history."""

    @pytest.fixture
    def mock_user(self):
        """
        Create a mock authenticated user.

        Returns:
            UserInDB: Mock user object
        """
        return UserInDB(
            user_id="test-user-123",
            email="test@example.com",
            display_name="Test User",
            is_admin=False
        )

    @pytest.fixture
    def mock_wallet_service(self):
        """
        Create a mock wallet service.

        Returns:
            MagicMock: Mock wallet service
        """
        service = MagicMock()
        service.initialized = True
        return service

    @pytest.fixture
    def sample_transactions(self):
        """
        Create sample transaction data.

        Returns:
            list: List of mock transactions
        """
        return [
            MockTransaction(
                id="tx_001",
                type_value="credit",
                amount=Decimal("10.00"),
                description="Wallet top-up via Paystack",
                created_at=datetime(2024, 1, 15, 10, 30, 0),
                metadata={"gateway": "paystack", "reference": "ref_123"}
            ),
            MockTransaction(
                id="tx_002",
                type_value="debit",
                amount=Decimal("2.50"),
                description="Audio narration - Chapter 1",
                created_at=datetime(2024, 1, 15, 11, 0, 0),
                metadata={"book_id": "book_123", "chunk_index": 0}
            ),
            MockTransaction(
                id="tx_003",
                type_value="debit",
                amount=Decimal("0.40"),
                description="Voice Q&A question",
                created_at=datetime(2024, 1, 15, 11, 30, 0),
                metadata={"book_id": "book_123", "question_id": "q_456"}
            ),
            MockTransaction(
                id="tx_004",
                type_value="refund",
                amount=Decimal("1.00"),
                description="Refund for failed audio generation",
                created_at=datetime(2024, 1, 15, 12, 0, 0),
                metadata={"original_tx": "tx_002", "reason": "generation_failed"}
            ),
        ]

    @pytest.mark.asyncio
    async def test_get_transactions_success(
        self, mock_user, mock_wallet_service, sample_transactions
    ):
        """
        Test getting transaction history successfully.

        Expected:
            - Returns formatted transaction list
            - All fields are properly formatted
            - Correct response structure
        """
        from app.api.routes.wallet import get_transactions

        mock_wallet_service.get_transactions = AsyncMock(
            return_value=sample_transactions
        )

        with patch(
            "app.api.routes.wallet.get_current_user",
            return_value=mock_user
        ):
            with patch(
                "app.api.routes.wallet.get_wallet_service",
                return_value=mock_wallet_service
            ):
                result = await get_transactions(
                    limit=20,
                    skip=0,
                    current_user=mock_user,
                    wallet_service=mock_wallet_service
                )

        assert result["user_id"] == "test-user-123"
        assert result["total"] == 4
        assert result["limit"] == 20
        assert result["skip"] == 0
        assert len(result["transactions"]) == 4

        # Check first transaction format
        first_tx = result["transactions"][0]
        assert first_tx["id"] == "tx_001"
        assert first_tx["type"] == "credit"
        assert first_tx["amount"] == 10.00
        assert first_tx["description"] == "Wallet top-up via Paystack"
        assert "created_at" in first_tx
        assert first_tx["metadata"]["gateway"] == "paystack"

    @pytest.mark.asyncio
    async def test_get_transactions_empty(self, mock_user, mock_wallet_service):
        """
        Test getting transaction history when empty.

        Edge case:
            - User has no transactions
            - Should return empty list
        """
        from app.api.routes.wallet import get_transactions

        mock_wallet_service.get_transactions = AsyncMock(return_value=[])

        result = await get_transactions(
            limit=20,
            skip=0,
            current_user=mock_user,
            wallet_service=mock_wallet_service
        )

        assert result["user_id"] == "test-user-123"
        assert result["total"] == 0
        assert len(result["transactions"]) == 0

    @pytest.mark.asyncio
    async def test_get_transactions_with_pagination(
        self, mock_user, mock_wallet_service, sample_transactions
    ):
        """
        Test transaction history pagination.

        Expected:
            - limit parameter limits results
            - skip parameter offsets results
        """
        from app.api.routes.wallet import get_transactions

        # Return only 2 transactions for pagination test
        mock_wallet_service.get_transactions = AsyncMock(
            return_value=sample_transactions[:2]
        )

        result = await get_transactions(
            limit=2,
            skip=0,
            current_user=mock_user,
            wallet_service=mock_wallet_service
        )

        assert result["limit"] == 2
        assert result["skip"] == 0
        assert len(result["transactions"]) == 2

        # Verify get_transactions was called with correct params
        mock_wallet_service.get_transactions.assert_called_once_with(
            "test-user-123", limit=2, skip=0
        )

    @pytest.mark.asyncio
    async def test_get_transactions_failure(self, mock_user, mock_wallet_service):
        """
        Test transaction history failure handling.

        Failure case:
            - Service returns None
            - Should raise HTTPException with 500
        """
        from fastapi import HTTPException
        from app.api.routes.wallet import get_transactions

        mock_wallet_service.get_transactions = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await get_transactions(
                limit=20,
                skip=0,
                current_user=mock_user,
                wallet_service=mock_wallet_service
            )

        assert exc_info.value.status_code == 500
        assert "Failed to get transactions" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_transactions_endpoint_requires_auth(self):
        """
        Test that transactions endpoint requires authentication.

        Expected:
            - Endpoint has current_user dependency
        """
        from app.api.routes.wallet import get_transactions
        import inspect

        sig = inspect.signature(get_transactions)
        params = sig.parameters

        assert "current_user" in params
        assert params["current_user"].default is not None

    @pytest.mark.asyncio
    async def test_transaction_types_correctly_formatted(
        self, mock_user, mock_wallet_service, sample_transactions
    ):
        """
        Test that all transaction types are correctly formatted.

        Expected:
            - Credit transactions show correct type
            - Debit transactions show correct type
            - Refund transactions show correct type
        """
        from app.api.routes.wallet import get_transactions

        mock_wallet_service.get_transactions = AsyncMock(
            return_value=sample_transactions
        )

        result = await get_transactions(
            limit=20,
            skip=0,
            current_user=mock_user,
            wallet_service=mock_wallet_service
        )

        types_found = {tx["type"] for tx in result["transactions"]}
        assert "credit" in types_found
        assert "debit" in types_found
        assert "refund" in types_found


class TestTransactionResponseModel:
    """Test transaction response model validation."""

    def test_transaction_response_model_fields(self):
        """
        Test TransactionResponse model has required fields.

        Expected:
            - Model has all required fields
            - Fields have correct types
        """
        from app.api.routes.wallet import TransactionResponse

        model_fields = TransactionResponse.model_fields
        assert "id" in model_fields
        assert "type" in model_fields
        assert "amount" in model_fields
        assert "description" in model_fields
        assert "created_at" in model_fields
        assert "metadata" in model_fields

    def test_transaction_list_response_model_fields(self):
        """
        Test TransactionListResponse model has required fields.

        Expected:
            - Model has pagination fields
            - Model has transactions list
        """
        from app.api.routes.wallet import TransactionListResponse

        model_fields = TransactionListResponse.model_fields
        assert "user_id" in model_fields
        assert "transactions" in model_fields
        assert "total" in model_fields
        assert "limit" in model_fields
        assert "skip" in model_fields
