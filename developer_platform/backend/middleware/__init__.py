"""
Middleware Module for Developer Platform API.

Provides rate limiting, usage tracking, and authentication middleware.
"""

from .rate_limiter import (
    rate_limiter,
    rate_limit_middleware,
    get_rate_limit_dependency,
    set_redis_client,
    RateLimiter,
    TokenBucket
)

from .usage_tracker import (
    usage_tracker,
    usage_tracking_middleware,
    set_mongo_db,
    UsageTracker,
    UsageRecord,
    QuotaLimit
)

__all__ = [
    # Rate limiting
    "rate_limiter",
    "rate_limit_middleware",
    "get_rate_limit_dependency",
    "set_redis_client",
    "RateLimiter",
    "TokenBucket",
    # Usage tracking
    "usage_tracker",
    "usage_tracking_middleware",
    "set_mongo_db",
    "UsageTracker",
    "UsageRecord",
    "QuotaLimit",
]
