"""
Flutterwave Payment Client (Stub) for EstateFlow.

Payment integration is deferred. This module provides a no-op
implementation so that payment_service.py does not crash on import.
All methods raise NotImplementedError when called.
"""

import logging
from typing import Optional, Dict, Any
from decimal import Decimal

logger = logging.getLogger(__name__)


class FlutterwaveClient:
    """
    Stub Flutterwave client.

    Prevents import errors in payment_service.py.
    Real implementation will be added when payment features are prioritized.
    """

    def __init__(
        self,
        secret_key: Optional[str] = None,
        public_key: Optional[str] = None,
        encryption_key: Optional[str] = None,
        webhook_secret: Optional[str] = None,
    ):
        self.secret_key = secret_key
        self.public_key = public_key
        self.encryption_key = encryption_key
        self.webhook_secret = webhook_secret
        if not secret_key:
            logger.info("Flutterwave client initialized without API key (stub mode)")

    async def create_payment_intent(
        self,
        amount: Decimal,
        currency: str,
        customer_email: Optional[str] = None,
        customer_name: Optional[str] = None,
        customer_phone: Optional[str] = None,
        redirect_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tx_ref: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a Flutterwave payment. (Not yet implemented)"""
        raise NotImplementedError(
            "Flutterwave payment integration is not yet implemented. "
            "Configure FLUTTERWAVE_SECRET_KEY to enable."
        )

    async def retrieve_payment(self, transaction_id: str) -> Dict[str, Any]:
        """Retrieve a Flutterwave transaction. (Not yet implemented)"""
        raise NotImplementedError("Flutterwave payment retrieval not yet implemented.")

    async def refund_payment(
        self, transaction_id: str, amount: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """Refund a Flutterwave payment. (Not yet implemented)"""
        raise NotImplementedError("Flutterwave refund not yet implemented.")
