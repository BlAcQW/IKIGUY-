"""
Telephony Adapters

This package contains telephony provider adapters that implement the TelephonyPort interface.
"""

from .base import BaseTelephonyAdapter
from .vapi import VapiAdapter
from .vonage import VonageAdapter
from .telnyx import TelnyxAdapter
from .sip import SipAdapter
from .abena_ai import AbenaAITelephonyAdapter
from .azure_speech import AzureSpeechAdapter
from .google_speech import GoogleSpeechAdapter
from .openai_whisper import WhisperAdapter

__all__ = [
    "BaseTelephonyAdapter",
    "VapiAdapter", 
    "VonageAdapter",
    "TelnyxAdapter",
    "SipAdapter",
    "AbenaAITelephonyAdapter",
    "AzureSpeechAdapter",
    "GoogleSpeechAdapter",
    "WhisperAdapter",
]
