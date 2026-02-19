"""Stripe service wrapper for core backend."""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

try:
    from apps.shared.integration.stripe import get_stripe_service
    STRIPE_AVAILABLE = True
except ImportError:
    get_stripe_service = None
    STRIPE_AVAILABLE = False
    logger.warning("Stripe integration not available")


class StripeServiceWrapper:
    """Wrapper for the shared Stripe service."""

    def __init__(self):
        self.provider = "stripe"
        self._service = None

    @property
    def service(self):
        """Lazy initialization of Stripe service."""
        if self._service is None and get_stripe_service:
            self._service = get_stripe_service()
        return self._service

    async def test_connection(self) -> Dict[str, Any]:
        """Test Stripe connection."""
        if not self.service:
            return {
                "success": False,
                "message": "Stripe service not available",
                "error": "Stripe library not installed"
            }

        return await self.service.test_connection()

    async def create_payment_intent(self, config: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Create payment intent."""
        if not self.service:
            return {"success": False, "error": "Stripe service not available"}

        from apps.shared.integration.stripe import PaymentIntentRequest

        request = PaymentIntentRequest(
            amount=kwargs.get("amount"),
            currency=kwargs.get("currency", "usd"),
            customer_id=kwargs.get("customer_id"),
            payment_method_id=kwargs.get("payment_method_id"),
            metadata=kwargs.get("metadata"),
            description=kwargs.get("description"),
            automatic_payment_methods=kwargs.get("automatic_payment_methods", True)
        )

        return await self.service.create_payment_intent(request)

    async def create_customer(self, config: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Create customer."""
        if not self.service:
            return {"success": False, "error": "Stripe service not available"}

        from apps.shared.integration.stripe import CustomerRequest

        request = CustomerRequest(
            email=kwargs.get("email"),
            name=kwargs.get("name"),
            phone=kwargs.get("phone"),
            description=kwargs.get("description"),
            metadata=kwargs.get("metadata")
        )

        return await self.service.create_customer(request)

    async def create_subscription(self, config: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Create subscription."""
        if not self.service:
            return {"success": False, "error": "Stripe service not available"}

        from apps.shared.integration.stripe import SubscriptionRequest

        request = SubscriptionRequest(
            customer_id=kwargs.get("customer_id"),
            price_id=kwargs.get("price_id"),
            metadata=kwargs.get("metadata"),
            trial_period_days=kwargs.get("trial_period_days")
        )

        return await self.service.create_subscription(request)

    async def process_webhook(self, config: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Process webhook."""
        if not self.service:
            return {"success": False, "error": "Stripe service not available"}

        payload = kwargs.get("payload")
        signature = kwargs.get("signature")

        return await self.service.process_webhook(payload, signature)

    def get_capabilities(self) -> Dict[str, Any]:
        """Get capabilities."""
        if not self.service:
            return {
                "provider": "stripe",
                "configured": False,
                "error": "Stripe service not available"
            }

        return self.service.get_capabilities()


# Create service instance
stripe_service = StripeServiceWrapper() if STRIPE_AVAILABLE else None