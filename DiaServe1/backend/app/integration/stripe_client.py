"""
Stripe Payment Client (Stub) for EstateFlow.

Payment integration is deferred. This module provides a no-op
implementation so that payment_service.py does not crash on import.
All methods raise NotImplementedError when called.
"""

import logging
from typing import Optional, Dict, Any
from decimal import Decimal

logger = logging.getLogger(__name__)


class StripeClient:
    """
    Stub Stripe client.

    Prevents import errors in payment_service.py.
    Real implementation will be added when payment features are prioritized.
    """

    def __init__(
        self,
        secret_key: Optional[str] = None,
        publishable_key: Optional[str] = None,
        webhook_secret: Optional[str] = None,
    ):
        self.secret_key = secret_key
        self.publishable_key = publishable_key
        self.webhook_secret = webhook_secret
        if not secret_key:
            logger.info("Stripe client initialized without API key (stub mode)")

    async def create_payment_intent(
        self,
        amount: Decimal,
        currency: str,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a Stripe PaymentIntent. (Not yet implemented)"""
        raise NotImplementedError(
            "Stripe payment integration is not yet implemented. "
            "Configure STRIPE_SECRET_KEY and install the stripe package to enable."
        )

    async def retrieve_payment(self, payment_id: str) -> Dict[str, Any]:
        """Retrieve a Stripe PaymentIntent. (Not yet implemented)"""
        raise NotImplementedError("Stripe payment retrieval not yet implemented.")

    async def refund_payment(
        self, payment_id: str, amount: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """Refund a Stripe payment. (Not yet implemented)"""
        raise NotImplementedError("Stripe refund not yet implemented.")

    def construct_webhook_event(self, payload: bytes, sig_header: str) -> Dict[str, Any]:
        """Construct and verify a webhook event. (Not yet implemented)"""
        raise NotImplementedError("Stripe webhook handling not yet implemented.")
