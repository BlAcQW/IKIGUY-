"""
Subscription service for ChurchFlow SaaS billing.

Manages church organization subscriptions with Stripe integration.
Uses shared payment infrastructure from apps/shared/integration/stripe.py
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from decimal import Decimal
from motor.motor_asyncio import AsyncIOMotorDatabase

from apps.shared.integration.stripe import StripeService, StripeConfig, SubscriptionRequest, CustomerRequest
from app.models.subscription import (
    Subscription,
    SubscriptionPlan,
    SubscriptionStatus,
    PaymentMethod,
    STRIPE_PRICE_IDS,
    PLAN_LIMITS,
)
from app.models.usage_metrics import UsageMetrics, BillingEvent, UsageMetricsResponse


logger = logging.getLogger(__name__)


# Global service instance
_subscription_service: Optional['SubscriptionService'] = None


async def get_subscription_service(db: AsyncIOMotorDatabase) -> 'SubscriptionService':
    """
    Get or create subscription service singleton.

    Args:
        db: MongoDB database instance

    Returns:
        SubscriptionService instance
    """
    global _subscription_service
    if _subscription_service is None:
        _subscription_service = SubscriptionService(db)
        await _subscription_service.initialize()
    return _subscription_service


class SubscriptionService:
    """
    Service for managing church organization subscriptions.

    Handles subscription creation, upgrades, downgrades, cancellations,
    and usage tracking with plan limit enforcement.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize subscription service.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.subscriptions = db["subscriptions"]
        self.usage_metrics = db["usage_metrics"]
        self.billing_events = db["billing_events"]
        self.organizations = db["organizations"]
        self.users = db["users"]

        self.stripe_service = StripeBillingService(db)
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize service and create database indexes."""
        if self.initialized:
            return

        try:
            # Create indexes
            await self.subscriptions.create_index("organization_id", unique=True)
            await self.subscriptions.create_index("stripe_customer_id")
            await self.subscriptions.create_index("stripe_subscription_id")
            await self.subscriptions.create_index([("status", 1), ("current_period_end", 1)])

            await self.usage_metrics.create_index("organization_id", unique=True)
            await self.usage_metrics.create_index("period_start")

            await self.billing_events.create_index([("organization_id", 1), ("created_at", -1)])

            self.initialized = True
            logger.info("SubscriptionService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize SubscriptionService: {e}")
            raise

    async def create_subscription(
        self,
        organization_id: str,
        plan: SubscriptionPlan,
        email: str,
        church_name: str,
        payment_method_id: Optional[str] = None,
        trial_days: int = 14
    ) -> Subscription:
        """
        Create a new subscription for an organization.

        Args:
            organization_id: Organization ID
            plan: Subscription plan
            email: Church admin email
            church_name: Church name
            payment_method_id: Stripe payment method ID (required for paid plans)
            trial_days: Trial period days (default 14)

        Returns:
            Created subscription

        Raises:
            ValueError: If subscription already exists or validation fails
        """
        # Check if subscription already exists
        existing = await self.subscriptions.find_one({"organization_id": organization_id})
        if existing:
            raise ValueError(f"Subscription already exists for organization {organization_id}")

        # For FREE plan, no Stripe integration needed
        if plan == SubscriptionPlan.FREE:
            subscription = Subscription(
                organization_id=organization_id,
                plan=plan,
                status=SubscriptionStatus.ACTIVE,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            await self.subscriptions.insert_one(subscription.dict())
            await self._initialize_usage_metrics(organization_id)
            await self._log_billing_event(
                organization_id=organization_id,
                event_type="subscription.created",
                description=f"Free plan subscription created for {church_name}"
            )

            return subscription

        # For paid plans, create Stripe customer and subscription
        if not payment_method_id:
            raise ValueError("Payment method required for paid plans")

        # Create Stripe customer
        customer_id = await self.stripe_service.create_customer(
            email=email,
            name=church_name,
            organization_id=organization_id
        )

        # Attach payment method
        await self.stripe_service.attach_payment_method(
            customer_id=customer_id,
            payment_method_id=payment_method_id
        )

        # Create Stripe subscription
        stripe_subscription = await self.stripe_service.create_subscription(
            customer_id=customer_id,
            plan=plan,
            trial_days=trial_days
        )

        # Parse and save subscription
        subscription = self.stripe_service.parse_subscription_from_stripe(
            stripe_subscription=stripe_subscription,
            organization_id=organization_id
        )

        await self.subscriptions.insert_one(subscription.dict())
        await self._initialize_usage_metrics(organization_id)
        await self._log_billing_event(
            organization_id=organization_id,
            event_type="subscription.created",
            description=f"{plan.value.title()} plan subscription created for {church_name}",
            stripe_event_id=stripe_subscription.get("id"),
            metadata={"plan": plan.value, "trial_days": trial_days}
        )

        return subscription

    async def get_subscription(self, organization_id: str) -> Optional[Subscription]:
        """
        Get subscription for an organization.

        Args:
            organization_id: Organization ID

        Returns:
            Subscription or None if not found
        """
        data = await self.subscriptions.find_one({"organization_id": organization_id})
        if not data:
            return None
        return Subscription(**data)

    async def update_subscription(
        self,
        organization_id: str,
        new_plan: SubscriptionPlan
    ) -> Subscription:
        """
        Update subscription plan (upgrade/downgrade).

        Args:
            organization_id: Organization ID
            new_plan: New subscription plan

        Returns:
            Updated subscription

        Raises:
            ValueError: If subscription not found or update fails
        """
        subscription = await self.get_subscription(organization_id)
        if not subscription:
            raise ValueError(f"Subscription not found for organization {organization_id}")

        # Same plan, nothing to do
        if subscription.plan == new_plan:
            return subscription

        old_plan = subscription.plan

        # Upgrading/downgrading to FREE plan
        if new_plan == SubscriptionPlan.FREE:
            if subscription.stripe_subscription_id:
                await self.stripe_service.cancel_subscription(
                    subscription_id=subscription.stripe_subscription_id,
                    immediately=False  # Cancel at period end
                )

            subscription.plan = new_plan
            subscription.cancel_at_period_end = True
            subscription.updated_at = datetime.utcnow()

            await self.subscriptions.update_one(
                {"organization_id": organization_id},
                {"$set": subscription.dict()}
            )

            await self._log_billing_event(
                organization_id=organization_id,
                event_type="subscription.downgraded",
                description=f"Downgraded from {old_plan.value} to FREE plan",
                metadata={"old_plan": old_plan.value, "new_plan": new_plan.value}
            )

            return subscription

        # Upgrading/downgrading between paid plans
        if subscription.stripe_subscription_id:
            stripe_subscription = await self.stripe_service.update_subscription(
                subscription_id=subscription.stripe_subscription_id,
                new_plan=new_plan
            )

            # Update local subscription
            subscription = self.stripe_service.parse_subscription_from_stripe(
                stripe_subscription=stripe_subscription,
                organization_id=organization_id
            )

            await self.subscriptions.update_one(
                {"organization_id": organization_id},
                {"$set": subscription.dict()}
            )

            event_type = "subscription.upgraded" if new_plan.value > old_plan.value else "subscription.downgraded"
            await self._log_billing_event(
                organization_id=organization_id,
                event_type=event_type,
                description=f"Plan changed from {old_plan.value} to {new_plan.value}",
                stripe_event_id=stripe_subscription.get("id"),
                metadata={"old_plan": old_plan.value, "new_plan": new_plan.value}
            )

            return subscription

        # Upgrading from FREE to paid plan (shouldn't normally happen)
        raise ValueError("Cannot upgrade from FREE plan without payment setup")

    async def cancel_subscription(
        self,
        organization_id: str,
        immediately: bool = False
    ) -> Subscription:
        """
        Cancel a subscription.

        Args:
            organization_id: Organization ID
            immediately: Cancel immediately (True) or at period end (False)

        Returns:
            Canceled subscription

        Raises:
            ValueError: If subscription not found
        """
        subscription = await self.get_subscription(organization_id)
        if not subscription:
            raise ValueError(f"Subscription not found for organization {organization_id}")

        if subscription.stripe_subscription_id:
            stripe_subscription = await self.stripe_service.cancel_subscription(
                subscription_id=subscription.stripe_subscription_id,
                immediately=immediately
            )

            subscription = self.stripe_service.parse_subscription_from_stripe(
                stripe_subscription=stripe_subscription,
                organization_id=organization_id
            )

            await self.subscriptions.update_one(
                {"organization_id": organization_id},
                {"$set": subscription.dict()}
            )

            await self._log_billing_event(
                organization_id=organization_id,
                event_type="subscription.canceled",
                description=f"Subscription canceled {'immediately' if immediately else 'at period end'}",
                stripe_event_id=stripe_subscription.get("id"),
                metadata={"immediately": immediately}
            )

        else:
            # FREE plan, just mark as canceled
            subscription.status = SubscriptionStatus.CANCELED
            subscription.updated_at = datetime.utcnow()

            await self.subscriptions.update_one(
                {"organization_id": organization_id},
                {"$set": subscription.dict()}
            )

            await self._log_billing_event(
                organization_id=organization_id,
                event_type="subscription.canceled",
                description="Free plan subscription canceled"
            )

        return subscription

    async def get_usage_metrics(self, organization_id: str) -> UsageMetricsResponse:
        """
        Get current usage metrics for an organization.

        Args:
            organization_id: Organization ID

        Returns:
            Usage metrics with plan limits

        Raises:
            ValueError: If subscription not found
        """
        subscription = await self.get_subscription(organization_id)
        if not subscription:
            raise ValueError(f"Subscription not found for organization {organization_id}")

        # Get usage metrics
        metrics_data = await self.usage_metrics.find_one({"organization_id": organization_id})
        if not metrics_data:
            # Initialize if not exists
            await self._initialize_usage_metrics(organization_id)
            metrics_data = await self.usage_metrics.find_one({"organization_id": organization_id})

        metrics = UsageMetrics(**metrics_data)

        # Get plan limits
        plan_limits = PLAN_LIMITS[subscription.plan]

        return UsageMetricsResponse(
            organization_id=organization_id,
            member_count=metrics.member_count,
            member_limit=plan_limits["member_limit"],
            member_limit_reached=metrics.member_count >= plan_limits["member_limit"]
            if plan_limits["member_limit"] > 0
            else False,
            sms_credits_used=metrics.sms_credits_used,
            sms_credits_remaining=metrics.sms_credits_remaining,
            sms_credits_limit=plan_limits["sms_credits_monthly"],
            storage_used_mb=metrics.storage_used_mb,
            events_count=metrics.events_count,
            check_ins_count=metrics.check_ins_count,
            period_start=metrics.period_start,
            period_end=metrics.period_end,
            last_calculated=metrics.last_calculated
        )

    async def check_member_limit(self, organization_id: str) -> bool:
        """
        Check if organization can add more members.

        Args:
            organization_id: Organization ID

        Returns:
            True if can add members, False if limit reached
        """
        usage = await self.get_usage_metrics(organization_id)
        if usage.member_limit == -1:  # Unlimited
            return True
        return usage.member_count < usage.member_limit

    async def increment_member_count(self, organization_id: str) -> None:
        """
        Increment member count for usage tracking.

        Args:
            organization_id: Organization ID
        """
        await self.usage_metrics.update_one(
            {"organization_id": organization_id},
            {
                "$inc": {"member_count": 1},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

    async def decrement_sms_credits(self, organization_id: str, count: int = 1) -> bool:
        """
        Decrement SMS credits after sending messages.

        Args:
            organization_id: Organization ID
            count: Number of credits to deduct

        Returns:
            True if successful, False if insufficient credits
        """
        metrics = await self.usage_metrics.find_one({"organization_id": organization_id})
        if not metrics or metrics["sms_credits_remaining"] < count:
            return False

        await self.usage_metrics.update_one(
            {"organization_id": organization_id},
            {
                "$inc": {
                    "sms_credits_used": count,
                    "sms_credits_remaining": -count
                },
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

        return True

    async def _initialize_usage_metrics(self, organization_id: str) -> None:
        """
        Initialize usage metrics for a new subscription.

        Args:
            organization_id: Organization ID
        """
        subscription = await self.get_subscription(organization_id)
        plan_limits = PLAN_LIMITS[subscription.plan]

        period_start = datetime.utcnow()
        period_end = period_start + timedelta(days=30)

        metrics = UsageMetrics(
            organization_id=organization_id,
            member_count=0,
            sms_credits_used=0,
            sms_credits_remaining=plan_limits["sms_credits_monthly"],
            storage_used_mb=0.0,
            events_count=0,
            check_ins_count=0,
            period_start=period_start,
            period_end=period_end
        )

        await self.usage_metrics.insert_one(metrics.dict())

    async def _log_billing_event(
        self,
        organization_id: str,
        event_type: str,
        description: str,
        stripe_event_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log a billing event for audit trail.

        Args:
            organization_id: Organization ID
            event_type: Event type
            description: Event description
            stripe_event_id: Stripe event ID if from webhook
            metadata: Additional metadata
        """
        event = BillingEvent(
            organization_id=organization_id,
            event_type=event_type,
            description=description,
            stripe_event_id=stripe_event_id,
            metadata=metadata or {}
        )

        await self.billing_events.insert_one(event.dict())
