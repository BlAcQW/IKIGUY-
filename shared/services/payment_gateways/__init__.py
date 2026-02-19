"""
Payment Gateway Integrations.

Centralized payment gateway clients for use across all backend applications.

Usage:
    from shared.services.payment_gateways import StripeClient, FlutterwaveClient

    # Stripe
    stripe_client = StripeClient(
        secret_key=os.getenv("STRIPE_SECRET_KEY"),
        webhook_secret=os.getenv("STRIPE_WEBHOOK_SECRET")
    )

    # Flutterwave
    flutterwave_client = FlutterwaveClient(
        secret_key=os.getenv("FLUTTERWAVE_SECRET_KEY"),
        webhook_secret=os.getenv("FLUTTERWAVE_WEBHOOK_SECRET")
    )

Supported Gateways:
- Stripe: Card payments, subscriptions, customer management
- Flutterwave: Cards, mobile money, bank transfers for African markets
"""

from .base import PaymentGatewayBase, PaymentStatus
from .stripe_client import StripeClient
from .flutterwave_client import FlutterwaveClient

__all__ = [
    "PaymentGatewayBase",
    "PaymentStatus",
    "StripeClient",
    "FlutterwaveClient",
]
