"""
Telephony Interfaces and Adapters

This module provides shared telephony interfaces and adapters for consistent
telephony operations across all components.
"""

from .interfaces import (
    TelephonyEvent,
    TelephonyPort,
    ProviderManager,
    TelephonyEventType,
)
from .models import CallContext, ProviderHealth, ProviderSettings, CallResult
from .inbound import bridge_webhook_to_ws, INBOUND_CALL_LOG

__all__ = [
    "TelephonyEvent",
    "TelephonyPort",
    "ProviderManager",
    "TelephonyEventType",
    "CallContext",
    "ProviderHealth",
    "ProviderSettings",
    "CallResult",
    "bridge_webhook_to_ws",
    "INBOUND_CALL_LOG",
]
