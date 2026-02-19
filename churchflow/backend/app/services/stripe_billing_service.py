"""
Stripe billing service for subscription management.

Handles Stripe API interactions for creating customers, subscriptions,
payment methods, and webhook processing.

Adapted from InkWave's payment system architecture.
"""

import stripe
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.models.subscription import (
    Subscription,
    SubscriptionPlan,
    SubscriptionStatus,
    STRIPE_PRICE_IDS
)
from app.models.usage_metrics import BillingEvent


logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = settings.stripe_secret_key


class StripeBillingService:
    """
    Service for Stripe billing operations.

    Follows InkWave payment service patterns with dependency injection
    and async MongoDB integration.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize billing service.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.subscriptions = db["subscriptions"]
        self.billing_events = db["billing_events"]
        self.usage_metrics = db["usage_metrics"]

    async def create_customer(
        self,
        email: str,
        name: str,
        organization_id: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Create a Stripe customer.

        Args:
            email: Customer email
            name: Customer/organization name
            organization_id: ChurchFlow organization ID
            metadata: Additional metadata

        Returns:
            Stripe customer ID
        """
        customer_metadata = {
            "organization_id": organization_id,
            **(metadata or {})
        }

        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata=customer_metadata
            )

            # Log billing event
            await self._log_billing_event(
                organization_id=organization_id,
                event_type="customer.created",
                description=f"Stripe customer created for {name}",
                metadata={"customer_id": customer.id, "email": email}
            )

            return customer.id
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe customer: {str(e)}")
            raise ValueError(f"Payment processing error: {str(e)}")

    @staticmethod
    async def attach_payment_method(
        customer_id: str,
        payment_method_id: str
    ) -> None:
        """
        Attach a payment method to a customer.

        Args:
            customer_id: Stripe customer ID
            payment_method_id: Stripe payment method ID
        """
        # Attach payment method to customer
        stripe.PaymentMethod.attach(
            payment_method_id,
            customer=customer_id
        )

        # Set as default payment method
        stripe.Customer.modify(
            customer_id,
            invoice_settings={
                "default_payment_method": payment_method_id
            }
        )

    @staticmethod
    async def create_subscription(
        customer_id: str,
        plan: SubscriptionPlan,
        trial_days: Optional[int] = 14
    ) -> Dict[str, Any]:
        """
        Create a Stripe subscription.

        Args:
            customer_id: Stripe customer ID
            plan: Subscription plan
            trial_days: Number of trial days (default 14)

        Returns:
            Stripe subscription data

        Raises:
            ValueError: If plan is FREE or price ID not found
        """
        if plan == SubscriptionPlan.FREE:
            raise ValueError("FREE plan does not require Stripe subscription")

        price_id = STRIPE_PRICE_IDS.get(plan)
        if not price_id:
            raise ValueError(f"Price ID not found for plan: {plan}")

        # Create subscription with trial period
        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": price_id}],
            trial_period_days=trial_days,
            payment_behavior="default_incomplete",
            payment_settings={
                "save_default_payment_method": "on_subscription"
            },
            expand=["latest_invoice.payment_intent"]
        )

        return subscription

    @staticmethod
    async def update_subscription(
        subscription_id: str,
        new_plan: SubscriptionPlan
    ) -> Dict[str, Any]:
        """
        Update subscription plan (upgrade/downgrade).

        Args:
            subscription_id: Stripe subscription ID
            new_plan: New subscription plan

        Returns:
            Updated subscription data

        Raises:
            ValueError: If plan is invalid
        """
        if new_plan == SubscriptionPlan.FREE:
            # Cancel subscription for free plan
            return await StripeBillingService.cancel_subscription(subscription_id)

        price_id = STRIPE_PRICE_IDS.get(new_plan)
        if not price_id:
            raise ValueError(f"Price ID not found for plan: {new_plan}")

        # Get current subscription
        subscription = stripe.Subscription.retrieve(subscription_id)

        # Update subscription items
        stripe.Subscription.modify(
            subscription_id,
            items=[{
                "id": subscription["items"]["data"][0].id,
                "price": price_id
            }],
            proration_behavior="create_prorations"  # Prorate charges
        )

        return stripe.Subscription.retrieve(subscription_id)

    @staticmethod
    async def cancel_subscription(
        subscription_id: str,
        immediately: bool = False
    ) -> Dict[str, Any]:
        """
        Cancel a subscription.

        Args:
            subscription_id: Stripe subscription ID
            immediately: Cancel immediately (True) or at period end (False)

        Returns:
            Canceled subscription data
        """
        if immediately:
            subscription = stripe.Subscription.cancel(subscription_id)
        else:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )

        return subscription

    @staticmethod
    async def reactivate_subscription(subscription_id: str) -> Dict[str, Any]:
        """
        Reactivate a subscription that was set to cancel at period end.

        Args:
            subscription_id: Stripe subscription ID

        Returns:
            Reactivated subscription data
        """
        subscription = stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=False
        )

        return subscription

    @staticmethod
    async def get_subscription(subscription_id: str) -> Dict[str, Any]:
        """
        Retrieve subscription details from Stripe.

        Args:
            subscription_id: Stripe subscription ID

        Returns:
            Subscription data
        """
        return stripe.Subscription.retrieve(subscription_id)

    @staticmethod
    async def get_customer(customer_id: str) -> Dict[str, Any]:
        """
        Retrieve customer details from Stripe.

        Args:
            customer_id: Stripe customer ID

        Returns:
            Customer data
        """
        return stripe.Customer.retrieve(customer_id)

    @staticmethod
    async def list_payment_methods(customer_id: str) -> list:
        """
        List payment methods for a customer.

        Args:
            customer_id: Stripe customer ID

        Returns:
            List of payment methods
        """
        payment_methods = stripe.PaymentMethod.list(
            customer=customer_id,
            type="card"
        )

        return payment_methods.data

    @staticmethod
    async def detach_payment_method(payment_method_id: str) -> None:
        """
        Detach a payment method from a customer.

        Args:
            payment_method_id: Stripe payment method ID
        """
        stripe.PaymentMethod.detach(payment_method_id)

    @staticmethod
    async def create_invoice(
        customer_id: str,
        description: str,
        amount: int,
        currency: str = "usd"
    ) -> Dict[str, Any]:
        """
        Create a one-time invoice for a customer.

        Args:
            customer_id: Stripe customer ID
            description: Invoice description
            amount: Amount in cents
            currency: Currency code

        Returns:
            Invoice data
        """
        # Create invoice item
        stripe.InvoiceItem.create(
            customer=customer_id,
            amount=amount,
            currency=currency,
            description=description
        )

        # Create and finalize invoice
        invoice = stripe.Invoice.create(
            customer=customer_id,
            auto_advance=True  # Auto-finalize
        )

        return invoice

    @staticmethod
    async def list_invoices(customer_id: str, limit: int = 10) -> list:
        """
        List invoices for a customer.

        Args:
            customer_id: Stripe customer ID
            limit: Number of invoices to retrieve

        Returns:
            List of invoices
        """
        invoices = stripe.Invoice.list(
            customer=customer_id,
            limit=limit
        )

        return invoices.data

    @staticmethod
    def construct_webhook_event(
        payload: bytes,
        signature: str
    ) -> stripe.Event:
        """
        Construct and verify a Stripe webhook event.

        Args:
            payload: Raw webhook payload
            signature: Stripe signature header

        Returns:
            Verified Stripe event

        Raises:
            ValueError: If signature verification fails
        """
        return stripe.Webhook.construct_event(
            payload,
            signature,
            settings.stripe_webhook_secret
        )

    @staticmethod
    def parse_subscription_from_stripe(
        stripe_subscription: Dict[str, Any],
        organization_id: str
    ) -> Subscription:
        """
        Parse Stripe subscription data into ChurchFlow Subscription model.

        Args:
            stripe_subscription: Stripe subscription object
            organization_id: Organization ID

        Returns:
            Subscription model instance
        """
        # Map Stripe status to our enum
        status_mapping = {
            "active": SubscriptionStatus.ACTIVE,
            "trialing": SubscriptionStatus.TRIALING,
            "past_due": SubscriptionStatus.PAST_DUE,
            "canceled": SubscriptionStatus.CANCELED,
            "unpaid": SubscriptionStatus.UNPAID,
            "incomplete": SubscriptionStatus.INCOMPLETE,
            "incomplete_expired": SubscriptionStatus.INCOMPLETE_EXPIRED
        }

        # Determine plan from price ID
        price_id = stripe_subscription["items"]["data"][0]["price"]["id"]
        plan = SubscriptionPlan.FREE  # Default
        for sub_plan, sub_price_id in STRIPE_PRICE_IDS.items():
            if price_id == sub_price_id:
                plan = sub_plan
                break

        return Subscription(
            organization_id=organization_id,
            stripe_customer_id=stripe_subscription["customer"],
            stripe_subscription_id=stripe_subscription["id"],
            plan=plan,
            status=status_mapping.get(
                stripe_subscription["status"],
                SubscriptionStatus.ACTIVE
            ),
            current_period_start=datetime.fromtimestamp(
                stripe_subscription["current_period_start"]
            ),
            current_period_end=datetime.fromtimestamp(
                stripe_subscription["current_period_end"]
            ),
            cancel_at_period_end=stripe_subscription.get("cancel_at_period_end", False),
            trial_end=datetime.fromtimestamp(stripe_subscription["trial_end"])
            if stripe_subscription.get("trial_end")
            else None
        )
