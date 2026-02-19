"""
Rate Limiting Middleware for Developer Platform API.

Implements token bucket algorithm for rate limiting API requests.
Supports per-API-key rate limits with configurable tiers.
Redis persistence for distributed rate limiting.
"""

import time
import json
import logging
from typing import Dict, Optional, Tuple
from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

logger = logging.getLogger(__name__)


class TokenBucket:
    """
    Token bucket implementation for rate limiting.

    Each API key gets a bucket with:
    - Capacity: Maximum number of tokens
    - Refill rate: Tokens added per second
    - Current tokens: Available tokens
    """

    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.

        Args:
            capacity: Maximum tokens in bucket
            refill_rate: Tokens refilled per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_refill = time.time()

    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from bucket.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens were consumed, False if insufficient tokens
        """
        self._refill()

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill

        # Add tokens based on elapsed time and refill rate
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now

    def get_wait_time(self, tokens: int = 1) -> float:
        """
        Get time to wait until tokens are available.

        Args:
            tokens: Number of tokens needed

        Returns:
            Seconds to wait (0 if tokens available now)
        """
        self._refill()

        if self.tokens >= tokens:
            return 0.0

        tokens_needed = tokens - self.tokens
        return tokens_needed / self.refill_rate

    def to_dict(self) -> Dict:
        """
        Serialize bucket to dictionary for Redis storage.

        Returns:
            Dict representation of bucket state
        """
        return {
            "capacity": self.capacity,
            "refill_rate": self.refill_rate,
            "tokens": self.tokens,
            "last_refill": self.last_refill
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "TokenBucket":
        """
        Deserialize bucket from dictionary.

        Args:
            data: Dict with bucket state

        Returns:
            TokenBucket instance
        """
        bucket = cls(
            capacity=data["capacity"],
            refill_rate=data["refill_rate"]
        )
        bucket.tokens = data["tokens"]
        bucket.last_refill = data["last_refill"]
        return bucket


class RateLimiter:
    """
    Rate limiter with tiered limits based on API key plan.

    Plans:
    - Free: 10 requests/minute
    - Starter: 60 requests/minute
    - Professional: 600 requests/minute
    - Enterprise: Custom limits
    """

    # Rate limit tiers (requests per minute)
    RATE_LIMITS = {
        "free": {"capacity": 20, "refill_rate": 10/60},  # 10 req/min, burst 20
        "starter": {"capacity": 100, "refill_rate": 60/60},  # 60 req/min, burst 100
        "professional": {"capacity": 1000, "refill_rate": 600/60},  # 600 req/min, burst 1000
        "enterprise": {"capacity": 10000, "refill_rate": 6000/60},  # 6000 req/min, burst 10000
    }

    def __init__(self, redis_client: Optional['redis.Redis'] = None):
        """
        Initialize rate limiter with optional Redis persistence.

        Args:
            redis_client: Optional Redis client for persistence
        """
        self.buckets: Dict[str, TokenBucket] = {}  # In-memory cache
        self.redis_client = redis_client
        self.last_cleanup = time.time()

        if redis_client:
            logger.info("✅ Rate limiter initialized with Redis persistence")
        else:
            logger.warning("⚠️  Rate limiter running in memory-only mode (no persistence)")

    def _get_bucket(self, api_key: str, tier: str = "free") -> TokenBucket:
        """
        Get or create token bucket for API key.
        Loads from Redis if available, otherwise creates new.

        Args:
            api_key: API key identifier
            tier: Rate limit tier (free, starter, professional, enterprise)

        Returns:
            TokenBucket for the API key
        """
        # Cleanup old buckets every hour
        if time.time() - self.last_cleanup > 3600:
            self._cleanup_old_buckets()

        # Check in-memory cache first
        if api_key in self.buckets:
            return self.buckets[api_key]

        # Try to load from Redis
        if self.redis_client:
            try:
                bucket_data = self.redis_client.get(f"ratelimit:{api_key}")
                if bucket_data:
                    data = json.loads(bucket_data)
                    bucket = TokenBucket.from_dict(data)
                    self.buckets[api_key] = bucket  # Cache in memory
                    return bucket
            except Exception as e:
                logger.error(f"Error loading bucket from Redis: {e}")

        # Create new bucket if not found
        limits = self.RATE_LIMITS.get(tier, self.RATE_LIMITS["free"])
        bucket = TokenBucket(
            capacity=limits["capacity"],
            refill_rate=limits["refill_rate"]
        )
        self.buckets[api_key] = bucket
        self._save_bucket(api_key, bucket)

        return bucket

    def _save_bucket(self, api_key: str, bucket: TokenBucket):
        """
        Save bucket to Redis with TTL.

        Args:
            api_key: API key identifier
            bucket: TokenBucket to save
        """
        if not self.redis_client:
            return

        try:
            data = json.dumps(bucket.to_dict())
            # Save with 1 hour TTL
            self.redis_client.setex(
                f"ratelimit:{api_key}",
                3600,  # 1 hour TTL
                data
            )
        except Exception as e:
            logger.error(f"Error saving bucket to Redis: {e}")

    def _cleanup_old_buckets(self):
        """Remove buckets from memory that haven't been used in 1 hour."""
        now = time.time()
        to_remove = []

        for key, bucket in self.buckets.items():
            if now - bucket.last_refill > 3600:  # 1 hour
                to_remove.append(key)

        for key in to_remove:
            del self.buckets[key]

        self.last_cleanup = now
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old rate limit buckets from memory")

    def check_rate_limit(
        self,
        api_key: str,
        tier: str = "free",
        cost: int = 1
    ) -> Tuple[bool, Optional[Dict]]:
        """
        Check if request is within rate limit.
        Saves bucket state to Redis after each check.

        Args:
            api_key: API key identifier
            tier: Rate limit tier
            cost: Token cost for this request (default 1)

        Returns:
            Tuple of (allowed: bool, headers: dict or None)
            If allowed=False, headers contains retry-after info
        """
        bucket = self._get_bucket(api_key, tier)
        limits = self.RATE_LIMITS.get(tier, self.RATE_LIMITS["free"])

        if bucket.consume(cost):
            # Request allowed
            self._save_bucket(api_key, bucket)  # Persist to Redis
            return True, {
                "X-RateLimit-Limit": str(int(limits["refill_rate"] * 60)),
                "X-RateLimit-Remaining": str(int(bucket.tokens)),
                "X-RateLimit-Reset": str(int(bucket.last_refill + 60))
            }
        else:
            # Rate limit exceeded
            wait_time = bucket.get_wait_time(cost)
            return False, {
                "Retry-After": str(int(wait_time) + 1),
                "X-RateLimit-Limit": str(int(limits["refill_rate"] * 60)),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(time.time() + wait_time))
            }

    def get_stats(self, api_key: str) -> Dict:
        """
        Get rate limit statistics for an API key.

        Args:
            api_key: API key identifier

        Returns:
            Dict with rate limit stats
        """
        if api_key not in self.buckets:
            return {
                "tokens_remaining": 0,
                "tokens_capacity": 0,
                "refill_rate": 0.0,
                "last_request": None
            }

        bucket = self.buckets[api_key]
        bucket._refill()  # Update tokens before reporting

        return {
            "tokens_remaining": int(bucket.tokens),
            "tokens_capacity": bucket.capacity,
            "refill_rate": bucket.refill_rate * 60,  # Convert to per minute
            "last_request": datetime.fromtimestamp(bucket.last_refill).isoformat()
        }


# Global rate limiter instance (initialized without Redis by default)
# Redis client should be set via set_redis_client() after creation
rate_limiter = RateLimiter()


def set_redis_client(redis_client: 'redis.Redis'):
    """
    Set Redis client for rate limiter persistence.
    Call this during app startup after creating Redis connection.

    Args:
        redis_client: Redis client instance
    """
    global rate_limiter
    rate_limiter.redis_client = redis_client
    logger.info("✅ Redis persistence enabled for rate limiter")


async def rate_limit_middleware(request: Request, call_next):
    """
    Rate limiting middleware for FastAPI.

    Checks rate limits before processing requests.
    Adds rate limit headers to all responses.

    Args:
        request: FastAPI request
        call_next: Next middleware/handler

    Returns:
        Response with rate limit headers
    """
    # Skip rate limiting for health checks and docs
    if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
        return await call_next(request)

    # Get API key from header
    api_key = request.headers.get("X-API-Key") or request.headers.get("x-api-key")

    if not api_key:
        # No API key = strict rate limiting
        api_key = request.client.host  # Use IP address
        tier = "free"
    else:
        # TODO: Get tier from database based on API key
        # For now, default to free tier
        tier = "free"

    # Check rate limit
    allowed, headers = rate_limiter.check_rate_limit(api_key, tier)

    if not allowed:
        logger.warning(f"Rate limit exceeded for {api_key[:10]}... on {request.url.path}")
        return JSONResponse(
            status_code=429,
            content={
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": f"Rate limit exceeded. Please retry after {headers['Retry-After']} seconds.",
                    "field": None
                },
                "request_id": f"req_{int(time.time())}",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            },
            headers=headers
        )

    # Process request
    response = await call_next(request)

    # Add rate limit headers to response
    for key, value in headers.items():
        response.headers[key] = value

    return response


def get_rate_limit_dependency(tier: str = "free", cost: int = 1):
    """
    Create a dependency for endpoint-specific rate limiting.

    Usage:
        @router.get("/expensive-endpoint", dependencies=[Depends(get_rate_limit_dependency("professional", cost=5))])
        async def expensive_endpoint():
            ...

    Args:
        tier: Rate limit tier
        cost: Token cost for this endpoint

    Returns:
        Dependency function
    """
    async def check_rate_limit(request: Request):
        api_key = request.headers.get("X-API-Key") or request.headers.get("x-api-key")

        if not api_key:
            api_key = request.client.host

        allowed, headers = rate_limiter.check_rate_limit(api_key, tier, cost)

        if not allowed:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Rate limit exceeded. Please retry after {headers['Retry-After']} seconds.",
                        "field": None
                    },
                    "request_id": f"req_{int(time.time())}",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                },
                headers=headers
            )

    return check_rate_limit
