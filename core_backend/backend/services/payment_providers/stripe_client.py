"""
Real Stripe Payment Integration.

Handles card payments, payment intents, and webhooks.
"""

import logging
import stripe
from typing import Dict, Any, Optional, List
from decimal import Decimal
from datetime import datetime

logger = logging.getLogger(__name__)


class StripeClient:
    """Stripe payment client for card processing."""

    def __init__(self, secret_key: str, webhook_secret: Optional[str] = None):
        """
        Initialize Stripe client.

        Args:
            secret_key: Stripe secret key (sk_test_... or sk_live_...)
            webhook_secret: Webhook signing secret
        """
        stripe.api_key = secret_key
        self.webhook_secret = webhook_secret
        logger.info("Stripe client initialized")

    async def create_payment_intent(
        self,
        amount: Decimal,
        currency: str,
        customer_id: Optional[str] = None,
        payment_method_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        confirm: bool = False
    ) -> Dict[str, Any]:
        """
        Create Stripe Payment Intent.

        Args:
            amount: Amount in currency units (e.g., 50.00 for $50)
            currency: Currency code (usd, eur, etc.)
            customer_id: Stripe customer ID
            payment_method_id: Stripe payment method ID
            metadata: Additional metadata
            confirm: Automatically confirm the payment

        Returns:
            Payment intent data
        """
        try:
            # Convert to cents
            amount_cents = int(amount * 100)

            params = {
                "amount": amount_cents,
                "currency": currency.lower(),
                "metadata": metadata or {},
            }

            if customer_id:
                params["customer"] = customer_id

            if payment_method_id:
                params["payment_method"] = payment_method_id
                if confirm:
                    params["confirm"] = True
                    params["return_url"] = metadata.get("return_url") if metadata else None

            # Create payment intent
            intent = stripe.PaymentIntent.create(**params)

            logger.info(f"Created Stripe PaymentIntent: {intent.id}")

            return {
                "id": intent.id,
                "client_secret": intent.client_secret,
                "status": intent.status,
                "amount": intent.amount,
                "currency": intent.currency,
                "created": intent.created,
                "metadata": intent.metadata
            }

        except stripe.error.CardError as e:
            # Card declined
            logger.error(f"Stripe card error: {e.user_message}")
            raise ValueError(f"Card declined: {e.user_message}")

        except stripe.error.InvalidRequestError as e:
            # Invalid parameters
            logger.error(f"Stripe invalid request: {str(e)}")
            raise ValueError(f"Invalid payment request: {str(e)}")

        except stripe.error.StripeError as e:
            # Generic Stripe error
            logger.error(f"Stripe error: {str(e)}")
            raise Exception(f"Payment processing error: {str(e)}")

    async def retrieve_payment_intent(self, payment_intent_id: str) -> Dict[str, Any]:
        """
        Retrieve payment intent status.

        Args:
            payment_intent_id: Payment intent ID

        Returns:
            Payment intent data
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
                "created": intent.created
            }

        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve payment intent: {str(e)}")
            raise

    async def create_customer(
        self,
        email: str,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create Stripe customer.

        Args:
            email: Customer email
            name: Customer name
            metadata: Additional metadata

        Returns:
            Customer ID
        """
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata=metadata or {}
            )

            logger.info(f"Created Stripe customer: {customer.id}")
            return customer.id

        except stripe.error.StripeError as e:
            logger.error(f"Failed to create customer: {str(e)}")
            raise

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

    def verify_webhook_signature(
        self,
        payload: str,
        signature: str
    ) -> Dict[str, Any]:
        """
        Verify webhook signature and construct event.

        Args:
            payload: Raw request body
            signature: Stripe-Signature header value

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

    async def refund_payment(
        self,
        payment_intent_id: str,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Refund a payment.

        Args:
            payment_intent_id: Payment intent ID
            amount: Amount to refund (None for full refund)
            reason: Refund reason

        Returns:
            Refund data
        """
        try:
            params = {"payment_intent": payment_intent_id}

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
                "created": refund.created
            }

        except stripe.error.StripeError as e:
            logger.error(f"Failed to create refund: {str(e)}")
            raise

    async def cancel_payment_intent(self, payment_intent_id: str) -> bool:
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
