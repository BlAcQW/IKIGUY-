"""
Stripe Payment Gateway Integration.

Handles card payments, payment intents, customer management, and webhooks.
Centralized implementation for use across all backend applications.
"""

import logging
import stripe
from typing import Dict, Any, Optional, List
from decimal import Decimal

from .base import PaymentGatewayBase, PaymentStatus

logger = logging.getLogger(__name__)


class StripeClient(PaymentGatewayBase):
    """
    Stripe payment gateway client.

    Supports:
    - Payment intents
    - Customer management
    - Payment methods
    - Refunds
    - Webhook verification
    """

    def __init__(
        self,
        secret_key: str,
        publishable_key: Optional[str] = None,
        webhook_secret: Optional[str] = None,
        api_version: Optional[str] = None
    ):
        """
        Initialize Stripe client.

        Args:
            secret_key: Stripe secret key (sk_test_... or sk_live_...)
            publishable_key: Stripe publishable key (optional)
            webhook_secret: Webhook signing secret
            api_version: API version (e.g., "2023-10-16")
        """
        super().__init__({
            "secret_key": secret_key,
            "publishable_key": publishable_key,
            "webhook_secret": webhook_secret,
            "api_version": api_version
        })

        stripe.api_key = secret_key
        if api_version:
            stripe.api_version = api_version

        self.webhook_secret = webhook_secret
        logger.info("Stripe client initialized")

    # ==================== Payment Intents ====================

    async def create_payment_intent(
        self,
        amount: Decimal,
        currency: str,
        customer_id: Optional[str] = None,
        payment_method_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        confirm: bool = False,
        return_url: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create Stripe Payment Intent.

        Args:
            amount: Amount in currency units (e.g., 50.00 for $50)
            currency: Currency code (usd, eur, ghs, etc.)
            customer_id: Stripe customer ID
            payment_method_id: Stripe payment method ID
            metadata: Additional metadata
            confirm: Automatically confirm the payment
            return_url: URL to return after 3D Secure
            **kwargs: Additional Stripe parameters

        Returns:
            Payment intent data with client_secret
        """
        try:
            # Convert to cents/smallest currency unit
            amount_cents = int(amount * 100)

            params = {
                "amount": amount_cents,
                "currency": currency.lower(),
                "metadata": metadata or {},
                **kwargs
            }

            if customer_id:
                params["customer"] = customer_id

            if payment_method_id:
                params["payment_method"] = payment_method_id
                if confirm:
                    params["confirm"] = True
                    if return_url:
                        params["return_url"] = return_url

            # Create payment intent
            intent = stripe.PaymentIntent.create(**params)

            logger.info(f"Created Stripe PaymentIntent: {intent.id}")

            return {
                "id": intent.id,
                "client_secret": intent.client_secret,
                "status": intent.status,
                "amount": intent.amount,
                "currency": intent.currency,
                "customer": intent.customer,
                "payment_method": intent.payment_method,
                "created": intent.created,
                "metadata": intent.metadata
            }

        except stripe.error.CardError as e:
            logger.error(f"Stripe card error: {e.user_message}")
            raise ValueError(f"Card declined: {e.user_message}")

        except stripe.error.InvalidRequestError as e:
            logger.error(f"Stripe invalid request: {str(e)}")
            raise ValueError(f"Invalid payment request: {str(e)}")

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            raise Exception(f"Payment processing error: {str(e)}")

    async def retrieve_payment(self, payment_intent_id: str) -> Dict[str, Any]:
        """
        Retrieve payment intent status.

        Args:
            payment_intent_id: Payment intent ID

        Returns:
            Payment intent data with current status
        """
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            return {
                "id": intent.id,
                "status": intent.status,
                "amount": intent.amount,
                "currency": intent.currency,
                "payment_method": intent.payment_method,
                "customer": intent.customer,
                "metadata": intent.metadata,
                "created": intent.created,
                "charges": [
                    {
                        "id": charge.id,
                        "status": charge.status,
                        "paid": charge.paid,
                        "refunded": charge.refunded,
                        "amount_refunded": charge.amount_refunded
                    }
                    for charge in intent.charges.data
                ] if intent.charges else []
            }

        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve payment intent: {str(e)}")
            raise

    async def confirm_payment_intent(
        self,
        payment_intent_id: str,
        payment_method_id: Optional[str] = None,
        return_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Confirm a payment intent.

        Args:
            payment_intent_id: Payment intent ID
            payment_method_id: Payment method to use
            return_url: Return URL for 3D Secure

        Returns:
            Confirmed payment intent data
        """
        try:
            params = {}
            if payment_method_id:
                params["payment_method"] = payment_method_id
            if return_url:
                params["return_url"] = return_url

            intent = stripe.PaymentIntent.confirm(payment_intent_id, **params)

            logger.info(f"Confirmed payment intent: {payment_intent_id}")

            return {
                "id": intent.id,
                "status": intent.status,
                "client_secret": intent.client_secret,
                "amount": intent.amount,
                "currency": intent.currency
            }

        except stripe.error.StripeError as e:
            logger.error(f"Failed to confirm payment: {str(e)}")
            raise

    async def cancel_payment(self, payment_intent_id: str) -> bool:
        """
        Cancel a payment intent.

        Args:
            payment_intent_id: Payment intent ID

        Returns:
            Success status
        """
        try:
            intent = stripe.PaymentIntent.cancel(payment_intent_id)
            logger.info(f"Cancelled payment intent: {payment_intent_id}")
            return intent.status == "canceled"

        except stripe.error.StripeError as e:
            logger.error(f"Failed to cancel payment intent: {str(e)}")
            return False

    # ==================== Refunds ====================

    async def refund_payment(
        self,
        payment_intent_id: str,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Refund a payment.

        Args:
            payment_intent_id: Payment intent ID
            amount: Amount to refund (None for full refund)
            reason: Refund reason (duplicate, fraudulent, requested_by_customer)
            metadata: Additional metadata

        Returns:
            Refund data
        """
        try:
            params = {
                "payment_intent": payment_intent_id,
                "metadata": metadata or {}
            }

            if amount:
                params["amount"] = int(amount * 100)

            if reason:
                params["reason"] = reason

            refund = stripe.Refund.create(**params)

            logger.info(f"Created refund: {refund.id}")

            return {
                "id": refund.id,
                "amount": refund.amount,
                "currency": refund.currency,
                "status": refund.status,
                "reason": refund.reason,
                "created": refund.created,
                "metadata": refund.metadata
            }

        except stripe.error.StripeError as e:
            logger.error(f"Failed to create refund: {str(e)}")
            raise

    async def list_refunds(
        self,
        payment_intent_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        List refunds for a payment.

        Args:
            payment_intent_id: Filter by payment intent ID
            limit: Maximum number of refunds to return

        Returns:
            List of refund data
        """
        try:
            params = {"limit": limit}
            if payment_intent_id:
                params["payment_intent"] = payment_intent_id

            refunds = stripe.Refund.list(**params)

            return [
                {
                    "id": refund.id,
                    "amount": refund.amount,
                    "currency": refund.currency,
                    "status": refund.status,
                    "reason": refund.reason,
                    "created": refund.created
                }
                for refund in refunds.data
            ]

        except stripe.error.StripeError as e:
            logger.error(f"Failed to list refunds: {str(e)}")
            raise

    # ==================== Customer Management ====================

    async def create_customer(
        self,
        email: str,
        name: Optional[str] = None,
        phone: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create Stripe customer.

        Args:
            email: Customer email
            name: Customer name
            phone: Customer phone
            metadata: Additional metadata

        Returns:
            Customer ID
        """
        try:
            params = {
                "email": email,
                "metadata": metadata or {}
            }
            if name:
                params["name"] = name
            if phone:
                params["phone"] = phone

            customer = stripe.Customer.create(**params)

            logger.info(f"Created Stripe customer: {customer.id}")
            return customer.id

        except stripe.error.StripeError as e:
            logger.error(f"Failed to create customer: {str(e)}")
            raise

    async def retrieve_customer(self, customer_id: str) -> Dict[str, Any]:
        """
        Retrieve customer details.

        Args:
            customer_id: Customer ID

        Returns:
            Customer data
        """
        try:
            customer = stripe.Customer.retrieve(customer_id)

            return {
                "id": customer.id,
                "email": customer.email,
                "name": customer.name,
                "phone": customer.phone,
                "metadata": customer.metadata,
                "created": customer.created
            }

        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve customer: {str(e)}")
            raise

    async def update_customer(
        self,
        customer_id: str,
        email: Optional[str] = None,
        name: Optional[str] = None,
        phone: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update customer details.

        Args:
            customer_id: Customer ID
            email: New email
            name: New name
            phone: New phone
            metadata: New metadata

        Returns:
            Updated customer data
        """
        try:
            params = {}
            if email:
                params["email"] = email
            if name:
                params["name"] = name
            if phone:
                params["phone"] = phone
            if metadata:
                params["metadata"] = metadata

            customer = stripe.Customer.modify(customer_id, **params)

            logger.info(f"Updated customer: {customer_id}")

            return {
                "id": customer.id,
                "email": customer.email,
                "name": customer.name,
                "phone": customer.phone,
                "metadata": customer.metadata
            }

        except stripe.error.StripeError as e:
            logger.error(f"Failed to update customer: {str(e)}")
            raise

    # ==================== Payment Methods ====================

    async def attach_payment_method(
        self,
        payment_method_id: str,
        customer_id: str
    ) -> Dict[str, Any]:
        """
        Attach payment method to customer.

        Args:
            payment_method_id: Payment method ID
            customer_id: Customer ID

        Returns:
            Payment method data
        """
        try:
            payment_method = stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer_id
            )

            return {
                "id": payment_method.id,
                "type": payment_method.type,
                "card": payment_method.card.__dict__ if payment_method.card else None,
                "created": payment_method.created
            }

        except stripe.error.StripeError as e:
            logger.error(f"Failed to attach payment method: {str(e)}")
            raise

    async def list_payment_methods(
        self,
        customer_id: str,
        method_type: str = "card"
    ) -> List[Dict[str, Any]]:
        """
        List customer payment methods.

        Args:
            customer_id: Customer ID
            method_type: Payment method type (card, us_bank_account, etc.)

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
                        "exp_year": pm.card.exp_year
                    } if pm.card else None,
                    "created": pm.created
                }
                for pm in payment_methods.data
            ]

        except stripe.error.StripeError as e:
            logger.error(f"Failed to list payment methods: {str(e)}")
            raise

    async def detach_payment_method(self, payment_method_id: str) -> bool:
        """
        Detach payment method from customer.

        Args:
            payment_method_id: Payment method ID

        Returns:
            Success status
        """
        try:
            stripe.PaymentMethod.detach(payment_method_id)
            logger.info(f"Detached payment method: {payment_method_id}")
            return True

        except stripe.error.StripeError as e:
            logger.error(f"Failed to detach payment method: {str(e)}")
            return False

    # ==================== Webhooks ====================

    def verify_webhook_signature(
        self,
        payload: str,
        signature: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Verify webhook signature and construct event.

        Args:
            payload: Raw request body (bytes or string)
            signature: Stripe-Signature header value
            **kwargs: Additional parameters (ignored)

        Returns:
            Verified event data

        Raises:
            ValueError: If signature is invalid
        """
        try:
            if not self.webhook_secret:
                raise ValueError("Webhook secret not configured")

            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )

            logger.info(f"Verified Stripe webhook: {event.type}")
            return event

        except ValueError as e:
            logger.error(f"Invalid webhook signature: {str(e)}")
            raise

        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Webhook signature verification failed: {str(e)}")
            raise ValueError("Invalid webhook signature")

    # ==================== Status Normalization ====================

    def normalize_payment_status(self, stripe_status: str) -> PaymentStatus:
        """
        Normalize Stripe status to common PaymentStatus.

        Args:
            stripe_status: Stripe payment intent status

        Returns:
            Normalized PaymentStatus
        """
        status_map = {
            "requires_payment_method": PaymentStatus.PENDING,
            "requires_confirmation": PaymentStatus.PENDING,
            "requires_action": PaymentStatus.PENDING,
            "processing": PaymentStatus.PROCESSING,
            "requires_capture": PaymentStatus.PROCESSING,
            "succeeded": PaymentStatus.COMPLETED,
            "canceled": PaymentStatus.CANCELLED,
        }
        return status_map.get(stripe_status, PaymentStatus.PENDING)
