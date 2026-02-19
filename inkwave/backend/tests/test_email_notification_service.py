"""
Unit tests for InkWave Email Notification Service.

Tests payment confirmation emails, wallet top-up notifications,
and welcome emails.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import os

# Set test environment variable before importing the service
os.environ["RESEND_API_KEY"] = "re_test_key_for_testing"
os.environ["EMAIL_FROM"] = "InkWave Test <test@inkwave.test>"
os.environ["SUPPORT_EMAIL"] = "support@inkwave.test"

from app.services.email_notification_service import (
    InkWaveEmailService,
    get_email_service,
)


class TestInkWaveEmailService:
    """Test suite for InkWaveEmailService."""

    @pytest.fixture
    def mock_resend_integration(self):
        """Create a mock ResendIntegration."""
        with patch("app.services.email_notification_service.ResendIntegration") as mock:
            mock_instance = MagicMock()
            mock.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def email_service(self, mock_resend_integration):
        """Create email service with mocked Resend."""
        service = InkWaveEmailService(resend_api_key="re_test_key")
        service.resend = mock_resend_integration
        service.initialized = True
        return service

    @pytest.fixture
    def sample_payment_data(self):
        """Sample payment data for testing."""
        return {
            "to_email": "customer@example.com",
            "customer_name": "John Doe",
            "amount": 49.99,
            "currency": "GHS",
            "order_id": "ORDER_123456",
            "transaction_id": "TXN_789012",
            "item_description": "Purchase of audiobook: The Great Gatsby",
            "payment_method": "Card",
            "card_last4": "4242",
        }

    @pytest.fixture
    def sample_topup_data(self):
        """Sample wallet top-up data for testing."""
        return {
            "to_email": "customer@example.com",
            "customer_name": "Jane Doe",
            "amount": 100.00,
            "currency": "GHS",
            "credits_added": 500,
            "new_balance": 1500,
            "transaction_id": "TOPUP_123456",
        }


class TestPaymentConfirmationEmail(TestInkWaveEmailService):
    """Tests for payment confirmation emails."""

    @pytest.mark.asyncio
    async def test_send_payment_confirmation_success(self, email_service, mock_resend_integration, sample_payment_data):
        """
        Test successful payment confirmation email sending.

        Expected: Email is sent successfully with correct parameters.
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.email_id = "email_123"
        mock_resend_integration.send_email = AsyncMock(return_value=mock_response)

        # Act
        result = await email_service.send_payment_confirmation(**sample_payment_data)

        # Assert
        assert result["success"] is True
        assert result["email_id"] == "email_123"
        mock_resend_integration.send_email.assert_called_once()

        # Verify email content
        call_args = mock_resend_integration.send_email.call_args[0][0]
        assert call_args.to == [sample_payment_data["to_email"]]
        assert "Payment Confirmed" in call_args.subject
        assert sample_payment_data["customer_name"] in call_args.html
        assert sample_payment_data["order_id"] in call_args.html
        assert sample_payment_data["transaction_id"] in call_args.html

    @pytest.mark.asyncio
    async def test_send_payment_confirmation_failure(self, email_service, mock_resend_integration, sample_payment_data):
        """
        Test payment confirmation email failure handling.

        Expected: Returns error when email sending fails.
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.success = False
        mock_response.error = "API rate limit exceeded"
        mock_resend_integration.send_email = AsyncMock(return_value=mock_response)

        # Act
        result = await email_service.send_payment_confirmation(**sample_payment_data)

        # Assert
        assert result["success"] is False
        assert result["error"] == "API rate limit exceeded"

    @pytest.mark.asyncio
    async def test_send_payment_confirmation_without_card_last4(self, email_service, mock_resend_integration, sample_payment_data):
        """
        Test payment confirmation without card last4 digits.

        Expected: Email is sent with payment method as fallback.
        """
        # Arrange
        del sample_payment_data["card_last4"]
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.email_id = "email_124"
        mock_resend_integration.send_email = AsyncMock(return_value=mock_response)

        # Act
        result = await email_service.send_payment_confirmation(**sample_payment_data)

        # Assert
        assert result["success"] is True
        call_args = mock_resend_integration.send_email.call_args[0][0]
        assert "Card" in call_args.html  # Payment method without card info

    @pytest.mark.asyncio
    async def test_send_payment_confirmation_service_not_initialized(self, sample_payment_data):
        """
        Test payment confirmation when service is not initialized.

        Expected: Returns error indicating service not configured.
        """
        # Arrange
        service = InkWaveEmailService(resend_api_key=None)
        service.initialized = False

        # Act
        result = await service.send_payment_confirmation(**sample_payment_data)

        # Assert
        assert result["success"] is False
        assert "not configured" in result["error"]


class TestWalletTopupEmail(TestInkWaveEmailService):
    """Tests for wallet top-up confirmation emails."""

    @pytest.mark.asyncio
    async def test_send_wallet_topup_confirmation_success(self, email_service, mock_resend_integration, sample_topup_data):
        """
        Test successful wallet top-up email sending.

        Expected: Email is sent with credits information.
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.email_id = "email_topup_123"
        mock_resend_integration.send_email = AsyncMock(return_value=mock_response)

        # Act
        result = await email_service.send_wallet_topup_confirmation(**sample_topup_data)

        # Assert
        assert result["success"] is True
        assert result["email_id"] == "email_topup_123"

        # Verify email content
        call_args = mock_resend_integration.send_email.call_args[0][0]
        assert "Top-Up Confirmed" in call_args.subject
        assert str(sample_topup_data["credits_added"]) in call_args.html
        assert str(sample_topup_data["new_balance"]) in call_args.html

    @pytest.mark.asyncio
    async def test_send_wallet_topup_confirmation_failure(self, email_service, mock_resend_integration, sample_topup_data):
        """
        Test wallet top-up email failure handling.

        Expected: Returns error when email sending fails.
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.success = False
        mock_response.error = "Invalid email address"
        mock_resend_integration.send_email = AsyncMock(return_value=mock_response)

        # Act
        result = await email_service.send_wallet_topup_confirmation(**sample_topup_data)

        # Assert
        assert result["success"] is False
        assert result["error"] == "Invalid email address"


class TestWelcomeEmail(TestInkWaveEmailService):
    """Tests for welcome emails."""

    @pytest.mark.asyncio
    async def test_send_welcome_email_success(self, email_service, mock_resend_integration):
        """
        Test successful welcome email sending.

        Expected: Welcome email is sent with free credits info.
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.email_id = "email_welcome_123"
        mock_resend_integration.send_email = AsyncMock(return_value=mock_response)

        # Act
        result = await email_service.send_welcome_email(
            to_email="newuser@example.com",
            customer_name="New User",
            free_credits=200
        )

        # Assert
        assert result["success"] is True
        assert result["email_id"] == "email_welcome_123"

        # Verify email content
        call_args = mock_resend_integration.send_email.call_args[0][0]
        assert "Welcome to InkWave" in call_args.subject
        assert "200" in call_args.html  # Free credits
        assert "New User" in call_args.html

    @pytest.mark.asyncio
    async def test_send_welcome_email_custom_credits(self, email_service, mock_resend_integration):
        """
        Test welcome email with custom free credits amount.

        Expected: Email shows correct custom credits amount.
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.email_id = "email_welcome_124"
        mock_resend_integration.send_email = AsyncMock(return_value=mock_response)

        custom_credits = 500

        # Act
        result = await email_service.send_welcome_email(
            to_email="vipuser@example.com",
            customer_name="VIP User",
            free_credits=custom_credits
        )

        # Assert
        assert result["success"] is True
        call_args = mock_resend_integration.send_email.call_args[0][0]
        assert str(custom_credits) in call_args.html


class TestEmailServiceSingleton(TestInkWaveEmailService):
    """Tests for email service singleton pattern."""

    def test_get_email_service_returns_instance(self):
        """
        Test that get_email_service returns an instance.

        Expected: Returns InkWaveEmailService instance.
        """
        # Act
        service = get_email_service()

        # Assert
        assert isinstance(service, InkWaveEmailService)

    def test_get_email_service_returns_same_instance(self):
        """
        Test singleton pattern - same instance returned.

        Expected: Returns the same instance on multiple calls.
        """
        # Act
        service1 = get_email_service()
        service2 = get_email_service()

        # Assert
        assert service1 is service2


class TestEmailServiceEdgeCases(TestInkWaveEmailService):
    """Edge case tests for email service."""

    @pytest.mark.asyncio
    async def test_payment_confirmation_with_special_characters(self, email_service, mock_resend_integration):
        """
        Test payment confirmation with special characters in customer name.

        Expected: Email is sent successfully with escaped characters.
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.email_id = "email_special_123"
        mock_resend_integration.send_email = AsyncMock(return_value=mock_response)

        # Act
        result = await email_service.send_payment_confirmation(
            to_email="user@example.com",
            customer_name="John O'Brien & Co.",
            amount=100.00,
            currency="GHS",
            order_id="ORDER_SPECIAL",
            transaction_id="TXN_SPECIAL",
            item_description="Book with <special> characters",
        )

        # Assert
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_payment_confirmation_with_zero_amount(self, email_service, mock_resend_integration):
        """
        Test payment confirmation with zero amount (edge case).

        Expected: Email is sent even with zero amount.
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.email_id = "email_zero_123"
        mock_resend_integration.send_email = AsyncMock(return_value=mock_response)

        # Act
        result = await email_service.send_payment_confirmation(
            to_email="user@example.com",
            customer_name="Test User",
            amount=0.00,
            currency="GHS",
            order_id="ORDER_FREE",
            transaction_id="TXN_FREE",
            item_description="Free promotional book",
        )

        # Assert
        assert result["success"] is True
        call_args = mock_resend_integration.send_email.call_args[0][0]
        assert "GHS 0.00" in call_args.html

    @pytest.mark.asyncio
    async def test_payment_confirmation_exception_handling(self, email_service, mock_resend_integration, sample_payment_data):
        """
        Test exception handling in payment confirmation.

        Expected: Returns error dict when exception occurs.
        """
        # Arrange
        mock_resend_integration.send_email = AsyncMock(side_effect=Exception("Network error"))

        # Act
        result = await email_service.send_payment_confirmation(**sample_payment_data)

        # Assert
        assert result["success"] is False
        assert "Network error" in result["error"]


class TestWalletTopupSuccessEmail(TestInkWaveEmailService):
    """Tests for wallet top-up success emails (with amounts, not credits)."""

    @pytest.fixture
    def sample_topup_success_data(self):
        """Sample wallet top-up success data for testing."""
        return {
            "to_email": "customer@example.com",
            "customer_name": "John Doe",
            "amount": 50.00,
            "currency": "GHS",
            "new_balance": 150.00,
            "reference": "paystack_ref_123456789",
            "payment_method": "Paystack",
        }

    @pytest.mark.asyncio
    async def test_send_wallet_topup_success(self, email_service, mock_resend_integration, sample_topup_success_data):
        """
        Test successful wallet top-up success email sending.

        Expected: Email is sent with amount and balance information.
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.email_id = "email_topup_success_123"
        mock_resend_integration.send_email = AsyncMock(return_value=mock_response)

        # Act
        result = await email_service.send_wallet_topup_success(**sample_topup_success_data)

        # Assert
        assert result["success"] is True
        assert result["email_id"] == "email_topup_success_123"

        # Verify email content
        call_args = mock_resend_integration.send_email.call_args[0][0]
        assert "Wallet Topped Up" in call_args.subject
        assert "GHS 50.00" in call_args.html
        assert "GHS 150.00" in call_args.html  # New balance
        assert "Paystack" in call_args.html

    @pytest.mark.asyncio
    async def test_send_wallet_topup_success_failure(self, email_service, mock_resend_integration, sample_topup_success_data):
        """
        Test wallet top-up success email failure handling.

        Expected: Returns error when email sending fails.
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.success = False
        mock_response.error = "Invalid email address"
        mock_resend_integration.send_email = AsyncMock(return_value=mock_response)

        # Act
        result = await email_service.send_wallet_topup_success(**sample_topup_success_data)

        # Assert
        assert result["success"] is False
        assert result["error"] == "Invalid email address"

    @pytest.mark.asyncio
    async def test_send_wallet_topup_success_not_initialized(self, sample_topup_success_data):
        """
        Test wallet top-up success when service is not initialized.

        Expected: Returns error indicating service not configured.
        """
        # Arrange
        service = InkWaveEmailService(resend_api_key=None)
        service.initialized = False

        # Act
        result = await service.send_wallet_topup_success(**sample_topup_success_data)

        # Assert
        assert result["success"] is False
        assert "not configured" in result["error"]

    @pytest.mark.asyncio
    async def test_send_wallet_topup_success_with_expresspay(self, email_service, mock_resend_integration):
        """
        Test wallet top-up success email with ExpressPay.

        Expected: Email shows ExpressPay as payment method.
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.email_id = "email_expresspay_123"
        mock_resend_integration.send_email = AsyncMock(return_value=mock_response)

        # Act
        result = await email_service.send_wallet_topup_success(
            to_email="user@example.com",
            customer_name="Ghana User",
            amount=100.00,
            currency="GHS",
            new_balance=200.00,
            reference="expresspay_token_abc123",
            payment_method="ExpressPay",
        )

        # Assert
        assert result["success"] is True
        call_args = mock_resend_integration.send_email.call_args[0][0]
        assert "ExpressPay" in call_args.html


class TestPaymentFailedEmail(TestInkWaveEmailService):
    """Tests for payment failed notification emails."""

    @pytest.fixture
    def sample_failed_payment_data(self):
        """Sample failed payment data for testing."""
        return {
            "to_email": "customer@example.com",
            "customer_name": "John Doe",
            "amount": 50.00,
            "currency": "GHS",
            "reason": "Insufficient funds",
            "reference": "paystack_ref_failed_123",
            "payment_method": "Paystack",
        }

    @pytest.mark.asyncio
    async def test_send_payment_failed_success(self, email_service, mock_resend_integration, sample_failed_payment_data):
        """
        Test payment failed email sending.

        Expected: Email is sent with failure reason and amount.
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.email_id = "email_failed_123"
        mock_resend_integration.send_email = AsyncMock(return_value=mock_response)

        # Act
        result = await email_service.send_payment_failed(**sample_failed_payment_data)

        # Assert
        assert result["success"] is True
        assert result["email_id"] == "email_failed_123"

        # Verify email content
        call_args = mock_resend_integration.send_email.call_args[0][0]
        assert "Payment Failed" in call_args.subject
        assert "Insufficient funds" in call_args.html
        assert "GHS 50.00" in call_args.html
        assert "Paystack" in call_args.html

    @pytest.mark.asyncio
    async def test_send_payment_failed_without_reference(self, email_service, mock_resend_integration):
        """
        Test payment failed email without reference.

        Expected: Email is sent without reference field.
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.email_id = "email_failed_no_ref"
        mock_resend_integration.send_email = AsyncMock(return_value=mock_response)

        # Act
        result = await email_service.send_payment_failed(
            to_email="user@example.com",
            customer_name="Test User",
            amount=25.00,
            currency="GHS",
            reason="Card declined",
            reference=None,
            payment_method="ExpressPay",
        )

        # Assert
        assert result["success"] is True
        call_args = mock_resend_integration.send_email.call_args[0][0]
        assert "Card declined" in call_args.html

    @pytest.mark.asyncio
    async def test_send_payment_failed_not_initialized(self, sample_failed_payment_data):
        """
        Test payment failed when service is not initialized.

        Expected: Returns error indicating service not configured.
        """
        # Arrange
        service = InkWaveEmailService(resend_api_key=None)
        service.initialized = False

        # Act
        result = await service.send_payment_failed(**sample_failed_payment_data)

        # Assert
        assert result["success"] is False
        assert "not configured" in result["error"]

    @pytest.mark.asyncio
    async def test_send_payment_failed_exception_handling(self, email_service, mock_resend_integration, sample_failed_payment_data):
        """
        Test exception handling in payment failed email.

        Expected: Returns error dict when exception occurs.
        """
        # Arrange
        mock_resend_integration.send_email = AsyncMock(side_effect=Exception("SMTP error"))

        # Act
        result = await email_service.send_payment_failed(**sample_failed_payment_data)

        # Assert
        assert result["success"] is False
        assert "SMTP error" in result["error"]

    @pytest.mark.asyncio
    async def test_send_payment_failed_with_different_reasons(self, email_service, mock_resend_integration):
        """
        Test payment failed email with various failure reasons.

        Expected: Email correctly shows different failure reasons.
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.email_id = "email_failed_reasons"
        mock_resend_integration.send_email = AsyncMock(return_value=mock_response)

        failure_reasons = [
            "Payment not completed: declined",
            "Transaction timeout",
            "Invalid card number",
            "3DS authentication failed",
        ]

        for reason in failure_reasons:
            # Act
            result = await email_service.send_payment_failed(
                to_email="user@example.com",
                customer_name="Test User",
                amount=100.00,
                currency="GHS",
                reason=reason,
            )

            # Assert
            assert result["success"] is True
            call_args = mock_resend_integration.send_email.call_args[0][0]
            assert reason in call_args.html
