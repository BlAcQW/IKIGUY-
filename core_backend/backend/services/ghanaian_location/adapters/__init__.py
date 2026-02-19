"""
Tool-specific adapters for Ghanaian Location Services

Provides customized behavior for different tools and services
while maintaining a consistent core API.
"""

from .base_adapter import BaseLocationAdapter
from .premier_health_adapter import PremierHealthAdapter
from .vapi_adapter import VapiAdapter
from .general_adapter import GeneralAdapter

__all__ = [
    'BaseLocationAdapter',
    'PremierHealthAdapter',
    'VapiAdapter',
    'GeneralAdapter'
]