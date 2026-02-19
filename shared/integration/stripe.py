"""
Stripe Payment Gateway Integration.

Provides comprehensive Stripe payment processing capabilities including:
- Payment processing and charge creation
- Customer management
- Subscription handling
- Webhook processing
- Product and price management
"""

import os
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from decimal import Decimal
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Try to import Stripe library
try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    logger.warning("Stripe library not available. Install stripe for payment processing.")


@dataclass
class StripeConfig:
    """Stripe configuration."""
    secret_key: str
    publishable_key: str
    webhook_secret: Optional[str] = None
    environment: str = "sandbox"  # sandbox or production


@dataclass
class PaymentIntentRequest:
    """Payment intent creation request."""
    amount: int  # Amount in cents
    currency: str = "usd"
    customer_id: Optional[str] = None
    payment_method_id: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None
    description: Optional[str] = None
    automatic_payment_methods: bool = True


@dataclass
class CustomerRequest:
    """Customer creation request."""
    email: str
    name: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None


@dataclass
class SubscriptionRequest:
    """Subscription creation request."""
    customer_id: str
    price_id: str
    metadata: Optional[Dict[str, str]] = None
    trial_period_days: Optional[int] = None


class StripeService:
    """
    Stripe payment gateway integration service.

    Provides comprehensive Stripe functionality including payments,
    customers, subscriptions, and webhook handling.
    """

    def __init__(self, config: Optional[StripeConfig] = None):
        """
        Initialize Stripe service.

        Args:
            config: Stripe configuration. If None, loads from environment.
        """
        self.provider = "stripe"

        if not STRIPE_AVAILABLE:
            raise ImportError("Stripe library is not available. Install with: pip install stripe")

        # Load configuration
        if config:
            self.config = config
        else:
            self.config = self._load_config_from_env()

        # Configure Stripe
        stripe.api_key = self.config.secret_key

        logger.info(f"Stripe service initialized for {self.config.environment} environment")

    def _load_config_from_env(self) -> StripeConfig:
        """Load Stripe configuration from environment variables."""
        secret_key = os.getenv("STRIPE_SECRET_KEY")
        if not secret_key:
            raise ValueError("STRIPE_SECRET_KEY environment variable is required")

        return StripeConfig(
            secret_key=secret_key,
            publishable_key=os.getenv("STRIPE_PUBLISHABLE_KEY", ""),
            webhook_secret=os.getenv("STRIPE_WEBHOOK_SECRET"),
            environment=os.getenv("STRIPE_ENVIRONMENT", "sandbox")
        )

    async def test_connection(self) -> Dict[str, Any]:
        """
        Test Stripe API connection.

        Returns:
            Test result with connection status
        """
        try:
            # Try to retrieve account information
            account = stripe.Account.retrieve()

            return {
                "success": True,
                "message": "Stripe connection successful",
                "account_id": account.id,
                "account_email": account.email,
                "environment": self.config.environment,
                "charges_enabled": account.charges_enabled,
                "details_submitted": account.details_submitted
            }
        except Exception as e:
            logger.error(f"Stripe connection test failed: {e}")
            return {
                "success": False,
                "message": f"Stripe connection failed: {str(e)}",
                "error": str(e)
            }

    async def create_payment_intent(self, request: PaymentIntentRequest) -> Dict[str, Any]:
        """
        Create a Stripe payment intent.

        Args:
            request: Payment intent request data

        Returns:
            Payment intent creation result
        """
        try:
            # Prepare payment intent parameters
            params = {
                "amount": request.amount,
                "currency": request.currency,
                "metadata": request.metadata or {}
            }

            # Add optional parameters
            if request.customer_id:
                params["customer"] = request.customer_id

            if request.payment_method_id:
                params["payment_method"] = request.payment_method_id
                params["confirm"] = True

            if request.description:
                params["description"] = request.description

            if request.automatic_payment_methods:
                params["automatic_payment_methods"] = {"enabled": True}

            # Create payment intent
            payment_intent = stripe.PaymentIntent.create(**params)

            logger.info(f"Created payment intent {payment_intent.id} for {request.amount} {request.currency}")

            return {
                "success": True,
                "payment_intent": {
                    "id": payment_intent.id,
                    "client_secret": payment_intent.client_secret,
                    "amount": payment_intent.amount,
                    "currency": payment_intent.currency,
                    "status": payment_intent.status,
                    "customer": payment_intent.customer,
                    "payment_method": payment_intent.payment_method
                }
            }

        except Exception as e:
            logger.error(f"Failed to create payment intent: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Payment intent creation failed"
            }

    async def create_customer(self, request: CustomerRequest) -> Dict[str, Any]:
        """
        Create a Stripe customer.

        Args:
            request: Customer creation request data

        Returns:
            Customer creation result
        """
        try:
            # Prepare customer parameters
            params = {
                "email": request.email,
                "metadata": request.metadata or {}
            }

            # Add optional parameters
            if request.name:
                params["name"] = request.name

            if request.phone:
                params["phone"] = request.phone

            if request.description:
                params["description"] = request.description

            # Create customer
            customer = stripe.Customer.create(**params)

            logger.info(f"Created customer {customer.id} for email {request.email}")

            return {
                "success": True,
                "customer": {
                    "id": customer.id,
                    "email": customer.email,
                    "name": customer.name,
                    "phone": customer.phone,
                    "created": customer.created,
                    "metadata": customer.metadata
                }
            }

        except Exception as e:
            logger.error(f"Failed to create customer: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Customer creation failed"
            }

    async def get_customer(self, customer_id: str) -> Dict[str, Any]:
        """
        Retrieve a Stripe customer.

        Args:
            customer_id: Customer ID

        Returns:
            Customer data or error
        """
        try:
            customer = stripe.Customer.retrieve(customer_id)

            return {
                "success": True,
                "customer": {
                    "id": customer.id,
                    "email": customer.email,
                    "name": customer.name,
                    "phone": customer.phone,
                    "created": customer.created,
                    "metadata": customer.metadata,
                    "default_source": customer.default_source
                }
            }

        except Exception as e:
            logger.error(f"Failed to retrieve customer {customer_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Customer {customer_id} not found"
            }

    async def create_subscription(self, request: SubscriptionRequest) -> Dict[str, Any]:
        """
        Create a Stripe subscription.

        Args:
            request: Subscription creation request data

        Returns:
            Subscription creation result
        """
        try:
            # Prepare subscription parameters
            params = {
                "customer": request.customer_id,
                "items": [{"price": request.price_id}],
                "metadata": request.metadata or {}
            }

            # Add optional parameters
            if request.trial_period_days:
                params["trial_period_days"] = request.trial_period_days

            # Create subscription
            subscription = stripe.Subscription.create(**params)

            logger.info(f"Created subscription {subscription.id} for customer {request.customer_id}")

            return {
                "success": True,
                "subscription": {
                    "id": subscription.id,
                    "customer": subscription.customer,
                    "status": subscription.status,
                    "current_period_start": subscription.current_period_start,
                    "current_period_end": subscription.current_period_end,
                    "trial_start": subscription.trial_start,
                    "trial_end": subscription.trial_end,
                    "metadata": subscription.metadata
                }
            }

        except Exception as e:
            logger.error(f"Failed to create subscription: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Subscription creation failed"
            }

    async def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """
        Cancel a Stripe subscription.

        Args:
            subscription_id: Subscription ID to cancel

        Returns:
            Cancellation result
        """
        try:
            subscription = stripe.Subscription.delete(subscription_id)

            logger.info(f"Cancelled subscription {subscription_id}")

            return {
                "success": True,
                "subscription": {
                    "id": subscription.id,
                    "status": subscription.status,
                    "canceled_at": subscription.canceled_at
                }
            }

        except Exception as e:
            logger.error(f"Failed to cancel subscription {subscription_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Subscription cancellation failed"
            }

    async def process_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """
        Process Stripe webhook.

        Args:
            payload: Webhook payload
            signature: Stripe signature header

        Returns:
            Webhook processing result
        """
        try:
            if not self.config.webhook_secret:
                logger.warning("Webhook secret not configured, skipping signature verification")
                event = stripe.Event.construct_from(payload.decode(), stripe.api_key)
            else:
                # Verify webhook signature
                event = stripe.Webhook.construct_event(
                    payload, signature, self.config.webhook_secret
                )

            # Process different event types
            event_type = event["type"]
            event_data = event["data"]["object"]

            logger.info(f"Processing Stripe webhook event: {event_type}")

            result = {
                "success": True,
                "event_type": event_type,
                "event_id": event["id"],
                "processed_at": datetime.utcnow().isoformat()
            }

            # Handle specific event types
            if event_type == "payment_intent.succeeded":
                result["payment_intent_id"] = event_data["id"]
                result["amount"] = event_data["amount"]
                result["currency"] = event_data["currency"]

            elif event_type == "payment_intent.payment_failed":
                result["payment_intent_id"] = event_data["id"]
                result["failure_reason"] = event_data.get("last_payment_error", {}).get("message")

            elif event_type == "customer.subscription.created":
                result["subscription_id"] = event_data["id"]
                result["customer_id"] = event_data["customer"]

            elif event_type == "customer.subscription.updated":
                result["subscription_id"] = event_data["id"]
                result["status"] = event_data["status"]

            elif event_type == "invoice.payment_succeeded":
                result["invoice_id"] = event_data["id"]
                result["subscription_id"] = event_data["subscription"]

            elif event_type == "invoice.payment_failed":
                result["invoice_id"] = event_data["id"]
                result["subscription_id"] = event_data["subscription"]

            return result

        except Exception as e:
            logger.error(f"Failed to process Stripe webhook: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Webhook processing failed"
            }

    async def list_payment_methods(self, customer_id: str) -> Dict[str, Any]:
        """
        List payment methods for a customer.

        Args:
            customer_id: Customer ID

        Returns:
            List of payment methods
        """
        try:
            payment_methods = stripe.PaymentMethod.list(
                customer=customer_id,
                type="card"
            )

            return {
                "success": True,
                "payment_methods": [
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
            }

        except Exception as e:
            logger.error(f"Failed to list payment methods for customer {customer_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to retrieve payment methods"
            }

    async def get_payment_intent(self, payment_intent_id: str) -> Dict[str, Any]:
        """
        Retrieve a payment intent.

        Args:
            payment_intent_id: Payment intent ID

        Returns:
            Payment intent data
        """
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            return {
                "success": True,
                "payment_intent": {
                    "id": payment_intent.id,
                    "amount": payment_intent.amount,
                    "currency": payment_intent.currency,
                    "status": payment_intent.status,
                    "customer": payment_intent.customer,
                    "payment_method": payment_intent.payment_method,
                    "created": payment_intent.created,
                    "metadata": payment_intent.metadata
                }
            }

        except Exception as e:
            logger.error(f"Failed to retrieve payment intent {payment_intent_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Payment intent {payment_intent_id} not found"
            }

    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get Stripe integration capabilities.

        Returns:
            Dictionary of capabilities and methods
        """
        return {
            "provider": self.provider,
            "name": "Stripe Payment Gateway",
            "category": "payment_gateways",
            "capabilities": [
                "test_connection",
                "create_payment_intent",
                "create_customer",
                "get_customer",
                "create_subscription",
                "cancel_subscription",
                "process_webhook",
                "list_payment_methods",
                "get_payment_intent"
            ],
            "supported_features": [
                "one_time_payments",
                "recurring_subscriptions",
                "customer_management",
                "webhook_processing",
                "payment_methods",
                "multi_currency"
            ],
            "webhook_events": [
                "payment_intent.succeeded",
                "payment_intent.payment_failed",
                "customer.subscription.created",
                "customer.subscription.updated",
                "invoice.payment_succeeded",
                "invoice.payment_failed"
            ],
            "currencies_supported": ["usd", "eur", "gbp", "cad", "aud", "jpy"],
            "environment": self.config.environment,
            "configured": bool(self.config.secret_key)
        }


# Create default service instance (lazy initialization)
def get_stripe_service():
    """Get Stripe service instance with lazy initialization."""
    if not STRIPE_AVAILABLE:
        return None

    try:
        return StripeService()
    except ValueError:
        # Return None if environment variables are not configured
        return None

stripe_service = None