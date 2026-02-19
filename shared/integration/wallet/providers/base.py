"""
Base Payment Provider Interface

Abstract base class that all payment providers must implement.
Provides consistent interface for payment processing, webhook handling,
and transaction management across different payment gateways.

Author: KasaAI Team
Date: 2025-10-27
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from decimal import Decimal
import logging

from ..models import PaymentInitiationResult, ProviderConfig, Currency
from ..exceptions import ProviderError, ProviderAPIError

logger = logging.getLogger(__name__)


class BasePaymentProvider(ABC):
    """
    Abstract base class for payment providers.

    All payment providers (Stripe, Flutterwave, Paystack, etc.) must implement
    this interface to ensure consistent behavior across the wallet system.

    Example:
        class StripeProvider(BasePaymentProvider):
            async def initialize_payment(self, amount, currency, **kwargs):
                # Stripe-specific implementation
                pass
    """

    def __init__(self, config: ProviderConfig):
        """
        Initialize provider with configuration.

        Args:
            config: Provider configuration with credentials and settings
        """
        self.config = config
        self.provider_name = config.provider.value
        self.is_test_mode = config.is_test_mode

        # Validate configuration
        self._validate_config()

        logger.info(
            f"Initialized {self.provider_name} provider "
            f"({'test' if self.is_test_mode else 'production'} mode)"
        )

    def _validate_config(self):
        """
        Validate provider configuration.

        Raises:
            ProviderError: If configuration is invalid
        """
        if not self.config.secret_key:
            raise ProviderError(
                f"{self.provider_name} secret_key is required"
            )

    # ========================================================================
    # PAYMENT PROCESSING (Required Methods)
    # ========================================================================

    @abstractmethod
    async def initialize_payment(
        self,
        amount: Decimal,
        currency: Currency,
        payment_method_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PaymentInitiationResult:
        """
        Initialize a payment with the provider.

        This method creates a payment intent/charge with the payment provider
        and returns the result with a payment URL if user action is required.

        Args:
            amount: Amount to charge (in major currency unit, e.g., dollars)
            currency: Currency code
            payment_method_id: Optional saved payment method ID
            customer_id: Optional customer ID in provider's system
            metadata: Additional metadata (transaction_id, user_id, etc.)

        Returns:
            PaymentInitiationResult with payment URL or confirmation

        Raises:
            ProviderAPIError: If provider API returns an error
            PaymentDeclinedError: If payment is declined

        Example:
            result = await provider.initialize_payment(
                amount=Decimal("100.00"),
                currency=Currency.GHS,
                payment_method_id="pm_xxx",
                metadata={"transaction_id": "txn_123"}
            )

            if result.success:
                # Redirect user to result.payment_url
                print(f"Payment URL: {result.payment_url}")
            else:
                print(f"Error: {result.error}")
        """
        pass

    @abstractmethod
    async def verify_webhook(
        self,
        payload: Dict[str, Any],
        signature: Optional[str] = None,
        raw_payload: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Verify webhook signature from provider.

        Critical for security - ensures webhook is from legitimate provider.

        Args:
            payload: Parsed webhook payload (dict)
            signature: Signature header from request
            raw_payload: Raw request body string (needed for some providers)
            headers: Full request headers dict

        Returns:
            True if signature is valid, False otherwise

        Example:
            is_valid = await provider.verify_webhook(
                payload=webhook_data,
                signature=request.headers.get('Stripe-Signature'),
                raw_payload=request.body.decode()
            )

            if not is_valid:
                raise InvalidWebhookSignatureError(provider.provider_name)
        """
        pass

    @abstractmethod
    async def process_webhook(
        self,
        payload: Dict[str, Any]
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Process webhook payload and extract transaction information.

        Args:
            payload: Verified webhook payload

        Returns:
            Tuple of (success, transaction_id, provider_data)
            - success: Whether transaction succeeded
            - transaction_id: Our transaction ID from metadata
            - provider_data: Additional provider-specific data

        Example:
            success, txn_id, data = await provider.process_webhook(payload)

            if success:
                # Complete the transaction
                await wallet_service._complete_transaction(txn_id, data)
            else:
                # Fail the transaction
                await wallet_service._fail_transaction(
                    txn_id,
                    data.get('failure_reason')
                )
        """
        pass

    # ========================================================================
    # TRANSACTION MANAGEMENT (Required Methods)
    # ========================================================================

    @abstractmethod
    async def get_transaction_status(
        self,
        provider_transaction_id: str
    ) -> Dict[str, Any]:
        """
        Get transaction status from provider.

        Useful for manual verification or recovery from webhook failures.

        Args:
            provider_transaction_id: Provider's transaction ID

        Returns:
            Transaction status details

        Example:
            status = await provider.get_transaction_status("pi_xxx")
            print(f"Status: {status['status']}")
            print(f"Amount: {status['amount']}")
        """
        pass

    @abstractmethod
    async def refund_payment(
        self,
        provider_transaction_id: str,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Refund a payment (full or partial).

        Args:
            provider_transaction_id: Provider's transaction ID
            amount: Amount to refund (None = full refund)
            reason: Refund reason

        Returns:
            Refund result with refund_id and status

        Example:
            result = await provider.refund_payment(
                provider_transaction_id="pi_xxx",
                amount=Decimal("50.00"),  # Partial refund
                reason="Customer request"
            )

            if result['success']:
                print(f"Refunded ${result['amount']}")
        """
        pass

    # ========================================================================
    # PAYMENT METHOD MANAGEMENT (Optional but Recommended)
    # ========================================================================

    async def create_customer(
        self,
        user_id: str,
        email: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a customer in provider's system.

        Optional but recommended for storing payment methods.

        Args:
            user_id: Our user ID
            email: User's email
            metadata: Additional metadata

        Returns:
            Customer details with customer_id

        Note:
            Default implementation returns None. Override for providers
            that support customer objects (Stripe, Flutterwave, etc.)
        """
        logger.warning(
            f"{self.provider_name} does not implement create_customer"
        )
        return {"customer_id": None}

    async def attach_payment_method(
        self,
        customer_id: str,
        payment_method_id: str
    ) -> bool:
        """
        Attach payment method to customer.

        Args:
            customer_id: Provider's customer ID
            payment_method_id: Provider's payment method ID

        Returns:
            True if successful

        Note:
            Default implementation returns True. Override for providers
            that require explicit attachment.
        """
        logger.warning(
            f"{self.provider_name} does not implement attach_payment_method"
        )
        return True

    async def detach_payment_method(
        self,
        payment_method_id: str
    ) -> bool:
        """
        Detach/delete payment method.

        Args:
            payment_method_id: Provider's payment method ID

        Returns:
            True if successful

        Note:
            Default implementation returns True. Override for providers
            that support payment method deletion.
        """
        logger.warning(
            f"{self.provider_name} does not implement detach_payment_method"
        )
        return True

    # ========================================================================
    # FEE CALCULATION
    # ========================================================================

    def calculate_fee(self, amount: Decimal) -> Decimal:
        """
        Calculate processing fee for this provider.

        Uses fee configuration from database (percent + fixed).

        Args:
            amount: Transaction amount

        Returns:
            Processing fee

        Example:
            # If fee_config = {"percent": 2.9, "fixed": 0.30, "cap": 10.00}
            fee = provider.calculate_fee(Decimal("100.00"))
            # Returns: Decimal("3.20") = (100 * 0.029) + 0.30
        """
        fee_config = self.config.fee_config
        if not fee_config:
            logger.warning(
                f"No fee configuration for {self.provider_name}, "
                f"defaulting to 0"
            )
            return Decimal('0.00')

        # Get fee parameters
        percent = Decimal(str(fee_config.get('percent', 0)))
        fixed = Decimal(str(fee_config.get('fixed', 0)))
        cap = fee_config.get('cap')

        # Calculate fee: (amount * percent / 100) + fixed
        fee = (amount * percent / Decimal('100')) + fixed

        # Apply cap if configured
        if cap and fee > Decimal(str(cap)):
            fee = Decimal(str(cap))
            logger.info(
                f"Fee capped at {cap} for {self.provider_name} "
                f"(calculated: {fee})"
            )

        return fee.quantize(Decimal('0.01'))

    # ========================================================================
    # HEALTH CHECK
    # ========================================================================

    async def health_check(self) -> Dict[str, Any]:
        """
        Check provider API connectivity.

        Returns:
            Health status with provider, status, and message

        Example:
            health = await provider.health_check()
            if health['status'] == 'healthy':
                print(f"{health['provider']} is operational")
        """
        return {
            "provider": self.provider_name,
            "status": "unknown",
            "message": "Health check not implemented for this provider"
        }

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def _convert_to_minor_unit(self, amount: Decimal, currency: Currency) -> int:
        """
        Convert amount to minor currency unit (cents, kobo, etc.).

        Most payment providers expect amounts in smallest currency unit.

        Args:
            amount: Amount in major unit (dollars, cedis, etc.)
            currency: Currency code

        Returns:
            Amount in minor unit (cents, pesewas, etc.)

        Example:
            cents = provider._convert_to_minor_unit(
                Decimal("100.50"),
                Currency.USD
            )
            # Returns: 10050 (cents)
        """
        # Most currencies use 2 decimal places (cents)
        # Special cases can be added here
        return int(amount * 100)

    def _convert_from_minor_unit(
        self,
        amount_minor: int,
        currency: Currency
    ) -> Decimal:
        """
        Convert amount from minor currency unit to major unit.

        Args:
            amount_minor: Amount in minor unit (cents, pesewas, etc.)
            currency: Currency code

        Returns:
            Amount in major unit (dollars, cedis, etc.)

        Example:
            dollars = provider._convert_from_minor_unit(10050, Currency.USD)
            # Returns: Decimal("100.50")
        """
        return Decimal(amount_minor) / Decimal(100)

    def _get_webhook_url(self) -> Optional[str]:
        """
        Get webhook URL for this provider.

        Returns:
            Webhook URL if configured
        """
        return self.config.webhook_url

    def _get_redirect_url(self) -> Optional[str]:
        """
        Get redirect URL for successful payments.

        Returns:
            Redirect URL if configured
        """
        return self.config.redirect_url

    def __repr__(self) -> str:
        """String representation of provider."""
        return (
            f"<{self.__class__.__name__} "
            f"provider={self.provider_name} "
            f"test_mode={self.is_test_mode}>"
        )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def validate_provider_credentials(config: ProviderConfig) -> Tuple[bool, Optional[str]]:
    """
    Validate that provider has required credentials.

    Args:
        config: Provider configuration

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        is_valid, error = validate_provider_credentials(config)
        if not is_valid:
            raise ConfigurationError(error)
    """
    if not config.secret_key:
        return False, f"{config.provider.value} secret_key is required"

    # Provider-specific validation
    if config.provider.value == 'stripe':
        if not config.secret_key.startswith('sk_'):
            return False, "Stripe secret key must start with 'sk_'"

    return True, None
