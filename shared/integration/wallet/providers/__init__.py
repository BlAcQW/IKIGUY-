"""
Payment Provider Implementations

This module contains payment provider implementations for the wallet system.
Each provider implements the BasePaymentProvider interface.

Available Providers:
- StripeProvider: Credit/debit card payments via Stripe
- FlutterwaveProvider: Cards and mobile money via Flutterwave
- PaystackProvider: Cards and mobile money via Paystack
- ExpressPayProvider: Cards and mobile money via ExpressPay (Ghana)
- MTNMoMoProvider: MTN Mobile Money (Ghana)
- VodafoneProvider: Vodafone Cash (Ghana)
- AirtelTigoProvider: AirtelTigo Money (Ghana)
- MPesaProvider: M-Pesa (Kenya)

Author: KasaAI Team
Date: 2025-10-27
"""

from .base import BasePaymentProvider, validate_provider_credentials
from .stripe_provider import StripeProvider
from .flutterwave_provider import FlutterwaveProvider
from .paystack import PaystackProvider
from .expresspay_provider import ExpressPayProvider
from .mpesa import MPesaProvider

# Providers (will be imported as they're implemented)
# from .mtn_momo_provider import MTNMoMoProvider
# from .vodafone_provider import VodafoneProvider
# from .airteltigo_provider import AirtelTigoProvider

__all__ = [
    "BasePaymentProvider",
    "validate_provider_credentials",
    "StripeProvider",
    "FlutterwaveProvider",
    "PaystackProvider",
    "ExpressPayProvider",
    "MPesaProvider",
    # Providers (uncomment as implemented)
    # "MTNMoMoProvider",
    # "VodafoneProvider",
    # "AirtelTigoProvider",
]
