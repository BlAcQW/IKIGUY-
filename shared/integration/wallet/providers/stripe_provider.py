"""
Stripe Payment Provider

Handles card payments via Stripe with support for:
- Payment Intents
- Customer management
- Payment method management
- Webhook verification
- Refunds

Ported from core_backend with enhancements.

Author: KasaAI Team
Date: 2025-10-27
"""

import logging
import stripe
from typing import Dict, Any, Optional, Tuple, List
from decimal import Decimal

from .base import BasePaymentProvider
from ..models import (
    PaymentInitiationResult,
    ProviderConfig,
    Currency,
    PaymentProvider
)
from ..exceptions import (
    ProviderAPIError,
    PaymentDeclinedError,
    InvalidWebhookSignatureError,
    ValidationError
)

logger = logging.getLogger(__name__)


class StripeProvider(BasePaymentProvider):
    """
    Stripe payment provider implementation.

    Supports:
    - Credit/debit card payments
    - Customer management
    - Saved payment methods
    - 3D Secure authentication
    - Webhook verification
    - Refunds (full and partial)

    Example:
        provider = StripeProvider(stripe_config)

        # Initialize payment
        result = await provider.initialize_payment(
            amount=Decimal("100.00"),
            currency=Currency.USD,
            payment_method_id="pm_xxx",
            metadata={"transaction_id": "txn_123"}
        )

        # Verify webhook
        is_valid = await provider.verify_webhook(
            payload=webhook_data,
            signature=stripe_signature,
            raw_payload=raw_body
        )
    """

    def __init__(self, config: ProviderConfig):
        """
        Initialize Stripe provider.

        Args:
            config: Provider configuration with Stripe credentials
        """
        super().__init__(config)

        # Set Stripe API key
        stripe.api_key = config.secret_key

        # Store webhook secret
        self.webhook_secret = config.webhook_secret

        logger.info(f"Stripe provider initialized (test_mode={self.is_test_mode})")

    def _validate_config(self):
        """Validate Stripe configuration."""
        super()._validate_config()

        # Validate secret key format
        if not self.config.secret_key.startswith('sk_'):
            raise ValidationError(
                'secret_key',
                'Stripe secret key must start with sk_'
            )

        # Warn if no webhook secret (needed for webhook verification)
        if not self.config.webhook_secret:
            logger.warning(
                "Stripe webhook_secret not configured. "
                "Webhook verification will fail."
            )

    # ========================================================================
    # PAYMENT PROCESSING
    # ========================================================================

    async def initialize_payment(
        self,
        amount: Decimal,
        currency: Currency,
        payment_method_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PaymentInitiationResult:
        """
        Initialize Stripe Payment Intent.

        Args:
            amount: Amount to charge
            currency: Currency code
            payment_method_id: Stripe payment method ID (pm_xxx)
            customer_id: Stripe customer ID (cus_xxx)
            metadata: Additional metadata

        Returns:
            PaymentInitiationResult with payment details

        Raises:
            PaymentDeclinedError: If card is declined
            ProviderAPIError: If Stripe API returns an error
        """
        try:
            # Convert amount to cents
            amount_cents = self._convert_to_minor_unit(amount, currency)

            # Build payment intent params
            params: Dict[str, Any] = {
                "amount": amount_cents,
                "currency": currency.value.lower(),
                "metadata": metadata or {},
            }

            # Add customer if provided
            if customer_id:
                params["customer"] = customer_id

            # Add payment method if provided
            if payment_method_id:
                params["payment_method"] = payment_method_id
                params["confirm"] = True  # Auto-confirm with saved payment method
                params["return_url"] = self._get_redirect_url()

                # Enable automatic payment methods for card fallbacks
                params["automatic_payment_methods"] = {
                    "enabled": True,
                    "allow_redirects": "never"  # Don't redirect for card payments
                }
            else:
                # No payment method - generate client secret for frontend
                params["automatic_payment_methods"] = {
                    "enabled": True
                }

            # Create payment intent
            intent = stripe.PaymentIntent.create(**params)

            logger.info(f"Created Stripe PaymentIntent: {intent.id}")

            # Determine if user action is required
            payment_url = None
            if intent.status == "requires_action" and intent.next_action:
                # 3D Secure or other authentication required
                next_action = intent.next_action
                if hasattr(next_action, 'redirect_to_url'):
                    payment_url = next_action.redirect_to_url.url

            return PaymentInitiationResult(
                success=True,
                payment_url=payment_url,
                reference=intent.id,
                amount=amount,
                currency=currency,
                gateway=PaymentProvider.STRIPE,
                metadata={
                    "client_secret": intent.client_secret,
                    "status": intent.status,
                    "payment_method": intent.payment_method,
                    "requires_action": intent.status == "requires_action"
                }
            )

        except stripe.error.CardError as e:
            # Card was declined
            logger.error(f"Stripe card declined: {e.user_message}")
            raise PaymentDeclinedError(
                provider=self.provider_name,
                reason=e.user_message or "Card declined"
            )

        except stripe.error.InvalidRequestError as e:
            # Invalid parameters
            logger.error(f"Stripe invalid request: {str(e)}")
            raise ProviderAPIError(
                provider=self.provider_name,
                error_message=f"Invalid payment request: {str(e)}",
                error_code="invalid_request"
            )

        except stripe.error.AuthenticationError as e:
            # Authentication failed (bad API key)
            logger.error(f"Stripe authentication error: {str(e)}")
            raise ProviderAPIError(
                provider=self.provider_name,
                error_message="Authentication failed - check API key",
                error_code="authentication_error"
            )

        except stripe.error.StripeError as e:
            # Generic Stripe error
            logger.error(f"Stripe error: {str(e)}")
            raise ProviderAPIError(
                provider=self.provider_name,
                error_message=str(e),
                error_code="stripe_error"
            )

    # ========================================================================
    # WEBHOOK HANDLING
    # ========================================================================

    async def verify_webhook(
        self,
        payload: Dict[str, Any],
        signature: Optional[str] = None,
        raw_payload: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Verify Stripe webhook signature.

        Args:
            payload: Parsed webhook payload (not used for Stripe)
            signature: Stripe-Signature header value
            raw_payload: Raw request body (required for Stripe)
            headers: Request headers

        Returns:
            True if signature is valid

        Raises:
            InvalidWebhookSignatureError: If signature is invalid
        """
        if not signature or not raw_payload:
            logger.error("Stripe webhook verification requires signature and raw_payload")
            return False

        if not self.webhook_secret:
            logger.error("Stripe webhook_secret not configured")
            return False

        try:
            # Use Stripe's signature verification
            event = stripe.Webhook.construct_event(
                raw_payload,
                signature,
                self.webhook_secret
            )

            logger.info(f"Verified Stripe webhook: {event.type}")
            return True

        except ValueError as e:
            # Invalid payload
            logger.error(f"Invalid Stripe webhook payload: {str(e)}")
            return False

        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            logger.error(f"Invalid Stripe webhook signature: {str(e)}")
            return False

    async def process_webhook(
        self,
        payload: Dict[str, Any]
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Process Stripe webhook event.

        Args:
            payload: Verified webhook payload

        Returns:
            Tuple of (success, transaction_id, provider_data)

        Supported Events:
        - payment_intent.succeeded: Payment completed successfully
        - payment_intent.payment_failed: Payment failed
        - payment_intent.requires_action: Additional action needed (3DS)
        """
        event_type = payload.get('type')

        if event_type == 'payment_intent.succeeded':
            # Payment succeeded
            payment_intent = payload['data']['object']
            transaction_id = payment_intent['metadata'].get('transaction_id')

            provider_data = {
                'provider_id': payment_intent['id'],
                'amount': self._convert_from_minor_unit(
                    payment_intent['amount'],
                    Currency.USD  # Will be corrected by actual currency
                ),
                'currency': payment_intent['currency'],
                'status': 'completed',
                'payment_method': payment_intent.get('payment_method'),
                'charges': payment_intent.get('charges')
            }

            logger.info(f"Stripe payment succeeded: {payment_intent['id']}")
            return True, transaction_id, provider_data

        elif event_type == 'payment_intent.payment_failed':
            # Payment failed
            payment_intent = payload['data']['object']
            transaction_id = payment_intent['metadata'].get('transaction_id')

            failure_message = "Payment failed"
            if payment_intent.get('last_payment_error'):
                failure_message = payment_intent['last_payment_error'].get(
                    'message',
                    failure_message
                )

            provider_data = {
                'provider_id': payment_intent['id'],
                'failure_reason': failure_message,
                'status': 'failed',
                'error_code': payment_intent.get('last_payment_error', {}).get('code'),
                'decline_code': payment_intent.get('last_payment_error', {}).get(
                    'decline_code'
                )
            }

            logger.warning(f"Stripe payment failed: {payment_intent['id']} - {failure_message}")
            return False, transaction_id, provider_data

        elif event_type == 'payment_intent.requires_action':
            # Payment requires additional action (3D Secure)
            payment_intent = payload['data']['object']
            transaction_id = payment_intent['metadata'].get('transaction_id')

            provider_data = {
                'provider_id': payment_intent['id'],
                'status': 'requires_action',
                'next_action': payment_intent.get('next_action')
            }

            logger.info(f"Stripe payment requires action: {payment_intent['id']}")
            # Return None to indicate no action needed yet (wait for completion)
            return True, None, provider_data

        else:
            # Unknown event type
            logger.info(f"Ignoring Stripe webhook event: {event_type}")
            return True, None, None

    # ========================================================================
    # TRANSACTION MANAGEMENT
    # ========================================================================

    async def get_transaction_status(
        self,
        provider_transaction_id: str
    ) -> Dict[str, Any]:
        """
        Get Stripe Payment Intent status.

        Args:
            provider_transaction_id: Stripe payment intent ID (pi_xxx)

        Returns:
            Transaction status details
        """
        try:
            intent = stripe.PaymentIntent.retrieve(provider_transaction_id)

            return {
                'id': intent.id,
                'status': intent.status,
                'amount': self._convert_from_minor_unit(intent.amount, Currency.USD),
                'currency': intent.currency,
                'payment_method': intent.payment_method,
                'customer': intent.customer,
                'metadata': intent.metadata,
                'created': intent.created,
                'charges': intent.charges.data if intent.charges else []
            }

        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve Stripe payment intent: {str(e)}")
            raise ProviderAPIError(
                provider=self.provider_name,
                error_message=f"Failed to get transaction status: {str(e)}",
                error_code="retrieval_error"
            )

    async def refund_payment(
        self,
        provider_transaction_id: str,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Refund a Stripe payment.

        Args:
            provider_transaction_id: Stripe payment intent ID (pi_xxx)
            amount: Amount to refund (None = full refund)
            reason: Refund reason

        Returns:
            Refund result with refund_id and status
        """
        try:
            # Build refund params
            params: Dict[str, Any] = {
                "payment_intent": provider_transaction_id
            }

            if amount:
                params["amount"] = self._convert_to_minor_unit(amount, Currency.USD)

            if reason:
                # Stripe refund reasons: duplicate, fraudulent, requested_by_customer
                stripe_reason = "requested_by_customer"
                if "fraud" in reason.lower():
                    stripe_reason = "fraudulent"
                elif "duplicate" in reason.lower():
                    stripe_reason = "duplicate"

                params["reason"] = stripe_reason

            # Create refund
            refund = stripe.Refund.create(**params)

            logger.info(f"Created Stripe refund: {refund.id} for {provider_transaction_id}")

            return {
                'success': True,
                'refund_id': refund.id,
                'amount': self._convert_from_minor_unit(refund.amount, Currency.USD),
                'currency': refund.currency,
                'status': refund.status,
                'reason': refund.reason,
                'created': refund.created
            }

        except stripe.error.InvalidRequestError as e:
            logger.error(f"Invalid Stripe refund request: {str(e)}")
            return {
                'success': False,
                'error': f"Invalid refund request: {str(e)}"
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe refund error: {str(e)}")
            return {
                'success': False,
                'error': f"Refund failed: {str(e)}"
            }

    # ========================================================================
    # CUSTOMER MANAGEMENT
    # ========================================================================

    async def create_customer(
        self,
        user_id: str,
        email: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create Stripe customer.

        Args:
            user_id: Our user ID
            email: User's email
            metadata: Additional metadata

        Returns:
            Customer details with customer_id
        """
        try:
            customer_metadata = metadata or {}
            customer_metadata['user_id'] = user_id

            customer = stripe.Customer.create(
                email=email,
                metadata=customer_metadata
            )

            logger.info(f"Created Stripe customer: {customer.id} for user {user_id}")

            return {
                'customer_id': customer.id,
                'email': customer.email,
                'created': customer.created
            }

        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe customer: {str(e)}")
            raise ProviderAPIError(
                provider=self.provider_name,
                error_message=f"Failed to create customer: {str(e)}",
                error_code="customer_creation_error"
            )

    async def attach_payment_method(
        self,
        customer_id: str,
        payment_method_id: str
    ) -> bool:
        """
        Attach payment method to Stripe customer.

        Args:
            customer_id: Stripe customer ID (cus_xxx)
            payment_method_id: Stripe payment method ID (pm_xxx)

        Returns:
            True if successful
        """
        try:
            payment_method = stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer_id
            )

            logger.info(
                f"Attached payment method {payment_method_id} "
                f"to customer {customer_id}"
            )

            return True

        except stripe.error.StripeError as e:
            logger.error(f"Failed to attach payment method: {str(e)}")
            return False

    async def detach_payment_method(
        self,
        payment_method_id: str
    ) -> bool:
        """
        Detach payment method from customer.

        Args:
            payment_method_id: Stripe payment method ID (pm_xxx)

        Returns:
            True if successful
        """
        try:
            stripe.PaymentMethod.detach(payment_method_id)

            logger.info(f"Detached payment method: {payment_method_id}")

            return True

        except stripe.error.StripeError as e:
            logger.error(f"Failed to detach payment method: {str(e)}")
            return False

    async def list_payment_methods(
        self,
        customer_id: str,
        method_type: str = "card"
    ) -> List[Dict[str, Any]]:
        """
        List Stripe customer's payment methods.

        Args:
            customer_id: Stripe customer ID (cus_xxx)
            method_type: Payment method type (card, etc.)

        Returns:
            List of payment methods
        """
        try:
            payment_methods = stripe.PaymentMethod.list(
                customer=customer_id,
                type=method_type
            )

            return [
                {
                    "id": pm.id,
                    "type": pm.type,
                    "card": {
                        "brand": pm.card.brand,
                        "last4": pm.card.last4,
                        "exp_month": pm.card.exp_month,
                        "exp_year": pm.card.exp_year,
                        "fingerprint": pm.card.fingerprint
                    } if pm.card else None,
                    "created": pm.created
                }
                for pm in payment_methods.data
            ]

        except stripe.error.StripeError as e:
            logger.error(f"Failed to list payment methods: {str(e)}")
            return []

    # ========================================================================
    # HEALTH CHECK
    # ========================================================================

    async def health_check(self) -> Dict[str, Any]:
        """
        Check Stripe API connectivity.

        Returns:
            Health status
        """
        try:
            # Try to retrieve balance (simple API call)
            balance = stripe.Balance.retrieve()

            return {
                "provider": self.provider_name,
                "status": "healthy",
                "message": "Successfully connected to Stripe API",
                "test_mode": self.is_test_mode,
                "available_balance": balance.available[0].amount if balance.available else None
            }

        except stripe.error.AuthenticationError:
            return {
                "provider": self.provider_name,
                "status": "unhealthy",
                "message": "Authentication failed - check API key",
                "test_mode": self.is_test_mode
            }

        except stripe.error.StripeError as e:
            return {
                "provider": self.provider_name,
                "status": "unhealthy",
                "message": f"Stripe API error: {str(e)}",
                "test_mode": self.is_test_mode
            }

    # ========================================================================
    # ADDITIONAL STRIPE METHODS
    # ========================================================================

    async def cancel_payment_intent(self, payment_intent_id: str) -> bool:
        """
        Cancel a Stripe payment intent.

        Args:
            payment_intent_id: Stripe payment intent ID (pi_xxx)

        Returns:
            True if cancelled successfully
        """
        try:
            intent = stripe.PaymentIntent.cancel(payment_intent_id)
            logger.info(f"Cancelled Stripe payment intent: {payment_intent_id}")
            return intent.status == "canceled"

        except stripe.error.StripeError as e:
            logger.error(f"Failed to cancel payment intent: {str(e)}")
            return False

    async def create_setup_intent(
        self,
        customer_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create Setup Intent for saving payment method without charging.

        Args:
            customer_id: Stripe customer ID
            metadata: Additional metadata

        Returns:
            Setup intent details with client_secret
        """
        try:
            setup_intent = stripe.SetupIntent.create(
                customer=customer_id,
                payment_method_types=['card'],
                metadata=metadata or {}
            )

            logger.info(f"Created Stripe SetupIntent: {setup_intent.id}")

            return {
                'id': setup_intent.id,
                'client_secret': setup_intent.client_secret,
                'status': setup_intent.status
            }

        except stripe.error.StripeError as e:
            logger.error(f"Failed to create setup intent: {str(e)}")
            raise ProviderAPIError(
                provider=self.provider_name,
                error_message=f"Failed to create setup intent: {str(e)}",
                error_code="setup_intent_error"
            )
