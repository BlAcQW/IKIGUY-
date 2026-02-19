"""
ExpressPay Provider Tests

Tests for ExpressPay payment provider integration, covering:
- Payment initialization (hosted payment page)
- Webhook verification (without signature - security limitation)
- Transaction status querying
- Error handling
- Refund API (should raise NotImplementedError)

Author: KasaAI Team
Date: 2025-11-23
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch
import httpx

from apps.shared.integration.wallet.providers import ExpressPayProvider
from apps.shared.integration.wallet.models import (
    ProviderConfig,
    PaymentProvider,
    Currency
)
from apps.shared.integration.wallet.exceptions import (
    ProviderAPIError,
    ValidationError
)


@pytest.fixture
def expresspay_config():
    """Create ExpressPay provider configuration for testing."""
    return ProviderConfig(
        provider=PaymentProvider.EXPRESSPAY,
        secret_key="test-api-key-12345",
        credentials={
            "merchant_id": "test-merchant-id-67890"
        },
        is_test_mode=True,
        webhook_url="https://test.ailabsafrica.com/webhook/expresspay",
        redirect_url="https://test.ailabsafrica.com/payment/success"
    )


@pytest.fixture
def expresspay_provider(expresspay_config):
    """Create ExpressPay provider instance."""
    return ExpressPayProvider(expresspay_config)


class TestExpressPayProviderInitialization:
    """Test ExpressPay provider initialization."""

    def test_initialization_success(self, expresspay_provider):
        """Test successful provider initialization."""
        assert expresspay_provider.provider_name == "expresspay"
        assert expresspay_provider.is_test_mode is True
        assert expresspay_provider.merchant_id == "test-merchant-id-67890"
        assert expresspay_provider.api_url == ExpressPayProvider.SANDBOX_API_URL

    def test_initialization_production_mode(self):
        """Test provider uses live URL in production mode."""
        config = ProviderConfig(
            provider=PaymentProvider.EXPRESSPAY,
            secret_key="live-api-key",
            credentials={"merchant_id": "live-merchant-id"},
            is_test_mode=False
        )
        provider = ExpressPayProvider(config)
        assert provider.api_url == ExpressPayProvider.LIVE_API_URL

    def test_initialization_missing_merchant_id(self):
        """Test initialization fails without merchant_id."""
        config = ProviderConfig(
            provider=PaymentProvider.EXPRESSPAY,
            secret_key="test-api-key",
            credentials={},  # Missing merchant_id
            is_test_mode=True
        )

        with pytest.raises(ValidationError) as exc:
            ExpressPayProvider(config)

        assert "merchant_id" in str(exc.value).lower()


class TestPaymentInitialization:
    """Test payment initialization via ExpressPay Merchant API."""

    @pytest.mark.asyncio
    async def test_initialize_payment_success(self, expresspay_provider):
        """Test successful payment initialization."""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": 1,  # Success
            "order-id": "txn_12345",
            "token": "test_token_abcdefgh123456",
            "redirect-url": "https://sandbox.expresspaygh.com/api/checkout.php?token=test_token_abcdefgh123456"
        }

        with patch.object(expresspay_provider.http_client, 'post', return_value=mock_response):
            result = await expresspay_provider.initialize_payment(
                amount=Decimal("100.00"),
                currency=Currency.GHS,
                customer_id="user@example.com",
                metadata={
                    "transaction_id": "txn_12345",
                    "firstname": "John",
                    "lastname": "Doe",
                    "phone": "0241234567",
                    "description": "Test payment"
                }
            )

        assert result.success is True
        assert result.payment_url is not None
        assert "checkout.php" in result.payment_url
        assert result.provider_transaction_id == "test_token_abcdefgh123456"
        assert result.metadata["order_id"] == "txn_12345"
        assert result.metadata["currency"] == "GHS"
        assert result.metadata["amount"] == 100.00

    @pytest.mark.asyncio
    async def test_initialize_payment_invalid_currency(self, expresspay_provider):
        """Test payment initialization fails with unsupported currency."""
        with pytest.raises(ValidationError) as exc:
            await expresspay_provider.initialize_payment(
                amount=Decimal("100.00"),
                currency=Currency.USD,  # ExpressPay only supports GHS
                customer_id="user@example.com",
                metadata={"transaction_id": "txn_12345"}
            )

        assert "GHS" in str(exc.value)

    @pytest.mark.asyncio
    async def test_initialize_payment_missing_email(self, expresspay_provider):
        """Test payment initialization fails without customer email."""
        with pytest.raises(ValidationError) as exc:
            await expresspay_provider.initialize_payment(
                amount=Decimal("100.00"),
                currency=Currency.GHS,
                customer_id=None,  # Missing email
                metadata={"transaction_id": "txn_12345"}
            )

        assert "email" in str(exc.value).lower()

    @pytest.mark.asyncio
    async def test_initialize_payment_invalid_credentials(self, expresspay_provider):
        """Test payment initialization with invalid credentials."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": 2,  # Invalid credentials
            "message": "Invalid merchant-id or api-key"
        }

        with patch.object(expresspay_provider.http_client, 'post', return_value=mock_response):
            with pytest.raises(ProviderAPIError) as exc:
                await expresspay_provider.initialize_payment(
                    amount=Decimal("100.00"),
                    currency=Currency.GHS,
                    customer_id="user@example.com",
                    metadata={"transaction_id": "txn_12345"}
                )

            assert "credentials" in str(exc.value).lower()

    @pytest.mark.asyncio
    async def test_initialize_payment_invalid_ip(self, expresspay_provider):
        """Test payment initialization with IP not whitelisted."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": 4,  # Invalid IP
            "message": "IP not whitelisted"
        }

        with patch.object(expresspay_provider.http_client, 'post', return_value=mock_response):
            with pytest.raises(ProviderAPIError) as exc:
                await expresspay_provider.initialize_payment(
                    amount=Decimal("100.00"),
                    currency=Currency.GHS,
                    customer_id="user@example.com",
                    metadata={"transaction_id": "txn_12345"}
                )

            assert "whitelisted" in str(exc.value).lower()


class TestWebhookVerification:
    """Test webhook verification (security limitation: no signature)."""

    @pytest.mark.asyncio
    async def test_verify_webhook_with_required_fields(self, expresspay_provider):
        """Test webhook verification succeeds with required fields."""
        payload = {
            "order-id": "txn_12345",
            "token": "test_token_abcdefgh123456"
        }

        is_valid = await expresspay_provider.verify_webhook(payload)

        assert is_valid is True

    @pytest.mark.asyncio
    async def test_verify_webhook_missing_order_id(self, expresspay_provider):
        """Test webhook verification fails without order-id."""
        payload = {
            "token": "test_token_abcdefgh123456"
            # Missing order-id
        }

        is_valid = await expresspay_provider.verify_webhook(payload)

        assert is_valid is False

    @pytest.mark.asyncio
    async def test_verify_webhook_missing_token(self, expresspay_provider):
        """Test webhook verification fails without token."""
        payload = {
            "order-id": "txn_12345"
            # Missing token
        }

        is_valid = await expresspay_provider.verify_webhook(payload)

        assert is_valid is False

    @pytest.mark.asyncio
    async def test_verify_webhook_alternate_field_names(self, expresspay_provider):
        """Test webhook verification with alternate field names (order_id vs order-id)."""
        payload = {
            "order_id": "txn_12345",  # Underscore instead of hyphen
            "token": "test_token_abcdefgh123456"
        }

        is_valid = await expresspay_provider.verify_webhook(payload)

        assert is_valid is True


class TestWebhookProcessing:
    """Test webhook processing and status querying."""

    @pytest.mark.asyncio
    async def test_process_webhook_approved(self, expresspay_provider):
        """Test processing webhook for approved transaction."""
        webhook_payload = {
            "order-id": "txn_12345",
            "token": "test_token_abcdefgh123456"
        }

        # Mock status query response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": 1,  # Approved
            "result-text": "Approved",
            "order-id": "txn_12345",
            "token": "test_token_abcdefgh123456",
            "transaction-id": "EXPR123456789",
            "currency": "GHS",
            "amount": 100.00,
            "date-processed": "23rd November, 2025"
        }

        with patch.object(expresspay_provider.http_client, 'post', return_value=mock_response):
            success, txn_id, data = await expresspay_provider.process_webhook(webhook_payload)

        assert success is True
        assert txn_id == "txn_12345"
        assert data["result"] == 1
        assert data["transaction-id"] == "EXPR123456789"

    @pytest.mark.asyncio
    async def test_process_webhook_declined(self, expresspay_provider):
        """Test processing webhook for declined transaction."""
        webhook_payload = {
            "order-id": "txn_12345",
            "token": "test_token_abcdefgh123456"
        }

        # Mock status query response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": 2,  # Declined
            "result-text": "Insufficient funds",
            "order-id": "txn_12345",
            "token": "test_token_abcdefgh123456"
        }

        with patch.object(expresspay_provider.http_client, 'post', return_value=mock_response):
            success, txn_id, data = await expresspay_provider.process_webhook(webhook_payload)

        assert success is False
        assert txn_id == "txn_12345"
        assert data["failure_reason"] == "Insufficient funds"

    @pytest.mark.asyncio
    async def test_process_webhook_pending(self, expresspay_provider):
        """Test processing webhook for pending transaction (mobile money)."""
        webhook_payload = {
            "order-id": "txn_12345",
            "token": "test_token_abcdefgh123456"
        }

        # Mock status query response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": 4,  # Pending
            "result-text": "Pending approval",
            "order-id": "txn_12345",
            "token": "test_token_abcdefgh123456"
        }

        with patch.object(expresspay_provider.http_client, 'post', return_value=mock_response):
            success, txn_id, data = await expresspay_provider.process_webhook(webhook_payload)

        assert success is False
        assert txn_id == "txn_12345"
        assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_process_webhook_error(self, expresspay_provider):
        """Test processing webhook for failed transaction."""
        webhook_payload = {
            "order-id": "txn_12345",
            "token": "test_token_abcdefgh123456"
        }

        # Mock status query response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": 3,  # Error
            "result-text": "Transaction failed",
            "order-id": "txn_12345",
            "token": "test_token_abcdefgh123456"
        }

        with patch.object(expresspay_provider.http_client, 'post', return_value=mock_response):
            success, txn_id, data = await expresspay_provider.process_webhook(webhook_payload)

        assert success is False
        assert txn_id == "txn_12345"
        assert "failure_reason" in data


class TestTransactionStatus:
    """Test transaction status querying."""

    @pytest.mark.asyncio
    async def test_get_transaction_status_success(self, expresspay_provider):
        """Test getting transaction status."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": 1,
            "result-text": "Approved",
            "order-id": "txn_12345",
            "token": "test_token_abcdefgh123456",
            "transaction-id": "EXPR123456789",
            "currency": "GHS",
            "amount": 100.00,
            "date-processed": "23rd November, 2025"
        }

        with patch.object(expresspay_provider.http_client, 'post', return_value=mock_response):
            status = await expresspay_provider.get_transaction_status("test_token_abcdefgh123456")

        assert status["result"] == 1
        assert status["result-text"] == "Approved"
        assert status["transaction-id"] == "EXPR123456789"

    @pytest.mark.asyncio
    async def test_get_transaction_status_api_error(self, expresspay_provider):
        """Test getting transaction status with API error."""
        with patch.object(expresspay_provider.http_client, 'post', side_effect=Exception("Network error")):
            with pytest.raises(ProviderAPIError) as exc:
                await expresspay_provider.get_transaction_status("test_token_abcdefgh123456")

            assert "failed" in str(exc.value).lower()


class TestRefund:
    """Test refund functionality (not supported)."""

    @pytest.mark.asyncio
    async def test_refund_not_implemented(self, expresspay_provider):
        """Test that refund raises NotImplementedError."""
        with pytest.raises(NotImplementedError) as exc:
            await expresspay_provider.refund_payment(
                provider_transaction_id="test_token_abcdefgh123456",
                amount=Decimal("50.00"),
                reason="Customer request"
            )

        assert "not provide a refund API" in str(exc.value)
        assert "support@expresspaygh.com" in str(exc.value)


class TestHealthCheck:
    """Test health check functionality."""

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, expresspay_provider):
        """Test health check when API is reachable."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": 3,  # Error expected for invalid token, but proves connectivity
            "result-text": "Invalid token"
        }

        with patch.object(expresspay_provider.http_client, 'post', return_value=mock_response):
            health = await expresspay_provider.health_check()

        assert health["provider"] == "expresspay"
        assert health["status"] == "healthy"
        assert health["test_mode"] is True

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, expresspay_provider):
        """Test health check when API is unreachable."""
        with patch.object(expresspay_provider.http_client, 'post', side_effect=Exception("Connection timeout")):
            health = await expresspay_provider.health_check()

        assert health["provider"] == "expresspay"
        assert health["status"] == "unhealthy"
        assert "unreachable" in health["message"].lower()


class TestCustomerManagement:
    """Test customer management (not supported)."""

    @pytest.mark.asyncio
    async def test_create_customer_not_supported(self, expresspay_provider):
        """Test that create_customer returns empty result."""
        result = await expresspay_provider.create_customer(
            user_id="user_123",
            email="user@example.com"
        )

        assert result["customer_id"] is None
        assert result["email"] == "user@example.com"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
