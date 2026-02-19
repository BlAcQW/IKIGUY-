"""
Pydantic Schemas for Core Backend API

Centralized schema definitions for type safety and OpenAPI documentation.
"""

from .affiliate import *
from .cdr import (
    CallDirection,
    CallDisposition,
    CallSummary,
    CallBreakdown,
    DailyUsage,
    RecentCall,
    CDRStatsResponse,
    CDRStatsRequest,
    AllPhonesStatsResponse,
)

__all__ = [
    # CDR schemas
    "CallDirection",
    "CallDisposition",
    "CallSummary",
    "CallBreakdown",
    "DailyUsage",
    "RecentCall",
    "CDRStatsResponse",
    "CDRStatsRequest",
    "AllPhonesStatsResponse",
]
