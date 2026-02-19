"""
Rate Limiting Middleware for KasaAI Services

Provides rate limiting functionality for API endpoints and services with
support for per-user, per-organization, and per-IP rate limiting.

Author: AI Labs Africa
Created: November 8, 2025
"""

import time
from collections import defaultdict, deque
from typing import Dict, Deque, Optional, Tuple
from enum import Enum
import asyncio


class RateLimitScope(str, Enum):
    """Scope of rate limiting."""
    USER = "user"
    ORGANIZATION = "organization"
    IP_ADDRESS = "ip"
    GLOBAL = "global"


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, message: str, retry_after: int):
        """
        Initialize rate limit exception.

        Args:
            message: Error message
            retry_after: Seconds until rate limit resets
        """
        self.message = message
        self.retry_after = retry_after
        super().__init__(self.message)


class RateLimiter:
    """
    Token bucket rate limiter with sliding window.

    Supports multiple rate limiting strategies:
    - Requests per minute (RPM)
    - Requests per hour (RPH)
    - Requests per day (RPD)
    - Custom time windows

    Example:
        >>> limiter = RateLimiter(requests_per_minute=60)
        >>> if limiter.allow("user_123"):
        ...     # Process request
        ...     pass
        ... else:
        ...     # Rate limit exceeded
        ...     raise RateLimitExceeded("Too many requests", retry_after=30)
    """

    def __init__(
        self,
        requests_per_minute: Optional[int] = None,
        requests_per_hour: Optional[int] = None,
        requests_per_day: Optional[int] = None,
        burst_size: Optional[int] = None
    ):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests per minute
            requests_per_hour: Maximum requests per hour
            requests_per_day: Maximum requests per day
            burst_size: Maximum burst size (defaults to rpm if not set)
        """
        self.limits = []

        if requests_per_minute:
            self.limits.append((requests_per_minute, 60))
        if requests_per_hour:
            self.limits.append((requests_per_hour, 3600))
        if requests_per_day:
            self.limits.append((requests_per_day, 86400))

        if not self.limits:
            raise ValueError("At least one rate limit must be specified")

        self.burst_size = burst_size or (requests_per_minute if requests_per_minute else self.limits[0][0])

        # Track request timestamps per identifier
        self._timestamps: Dict[str, Deque[float]] = defaultdict(deque)

        # Lock for thread safety
        self._lock = asyncio.Lock()

    def allow(self, identifier: str) -> bool:
        """
        Check if request is allowed for identifier.

        Args:
            identifier: Unique identifier (user_id, org_id, ip_address, etc.)

        Returns:
            True if request is allowed, False otherwise
        """
        now = time.time()
        timestamps = self._timestamps[identifier]

        # Clean up old timestamps and check all limits
        for max_requests, window_seconds in self.limits:
            window_start = now - window_seconds

            # Remove timestamps outside the window
            while timestamps and timestamps[0] < window_start:
                timestamps.popleft()

            # Check if limit exceeded
            if len(timestamps) >= max_requests:
                return False

        # Check burst size
        if len(timestamps) >= self.burst_size:
            return False

        # Allow request
        timestamps.append(now)
        return True

    async def allow_async(self, identifier: str) -> bool:
        """
        Async version of allow() with locking.

        Args:
            identifier: Unique identifier

        Returns:
            True if request is allowed, False otherwise
        """
        async with self._lock:
            return self.allow(identifier)

    def get_retry_after(self, identifier: str) -> int:
        """
        Get seconds until rate limit resets for identifier.

        Args:
            identifier: Unique identifier

        Returns:
            Seconds until reset (0 if not rate limited)
        """
        now = time.time()
        timestamps = self._timestamps.get(identifier)

        if not timestamps:
            return 0

        # Check smallest window (most restrictive)
        max_requests, window_seconds = min(self.limits, key=lambda x: x[1])

        if len(timestamps) < max_requests:
            return 0

        # Time until oldest timestamp expires
        oldest_timestamp = timestamps[0]
        window_start = now - window_seconds

        if oldest_timestamp >= window_start:
            retry_after = int(oldest_timestamp + window_seconds - now) + 1
            return max(0, retry_after)

        return 0

    def reset(self, identifier: str):
        """
        Reset rate limit for identifier.

        Args:
            identifier: Unique identifier
        """
        if identifier in self._timestamps:
            del self._timestamps[identifier]

    def get_usage(self, identifier: str) -> Dict[str, Tuple[int, int]]:
        """
        Get current usage for identifier.

        Args:
            identifier: Unique identifier

        Returns:
            Dict mapping window name to (current_count, max_count)
        """
        now = time.time()
        timestamps = self._timestamps.get(identifier, deque())

        usage = {}
        window_names = {60: "per_minute", 3600: "per_hour", 86400: "per_day"}

        for max_requests, window_seconds in self.limits:
            window_start = now - window_seconds
            count = sum(1 for ts in timestamps if ts >= window_start)
            window_name = window_names.get(window_seconds, f"{window_seconds}s")
            usage[window_name] = (count, max_requests)

        return usage


class ServiceRateLimiter:
    """
    Multi-scope rate limiter for services.

    Supports rate limiting by:
    - User ID
    - Organization ID
    - IP address
    - Global (all requests)

    Example:
        >>> limiter = ServiceRateLimiter(
        ...     user_rpm=100,
        ...     org_rpm=1000,
        ...     ip_rpm=60
        ... )
        >>>
        >>> # Check rate limit
        >>> allowed, scope = limiter.check_limit(
        ...     user_id="user_123",
        ...     org_id="org_abc",
        ...     ip_address="192.168.1.1"
        ... )
        >>>
        >>> if not allowed:
        ...     retry_after = limiter.get_retry_after(scope, "user_123")
        ...     raise RateLimitExceeded(f"Rate limit exceeded", retry_after)
    """

    def __init__(
        self,
        user_rpm: Optional[int] = None,
        user_rph: Optional[int] = None,
        user_rpd: Optional[int] = None,
        org_rpm: Optional[int] = None,
        org_rph: Optional[int] = None,
        org_rpd: Optional[int] = None,
        ip_rpm: Optional[int] = None,
        ip_rph: Optional[int] = None,
        global_rpm: Optional[int] = None,
        global_rph: Optional[int] = None
    ):
        """
        Initialize service rate limiter.

        Args:
            user_rpm: Requests per minute per user
            user_rph: Requests per hour per user
            user_rpd: Requests per day per user
            org_rpm: Requests per minute per organization
            org_rph: Requests per hour per organization
            org_rpd: Requests per day per organization
            ip_rpm: Requests per minute per IP
            ip_rph: Requests per hour per IP
            global_rpm: Global requests per minute
            global_rph: Global requests per hour
        """
        self.limiters = {}

        # User-level limits
        if any([user_rpm, user_rph, user_rpd]):
            self.limiters[RateLimitScope.USER] = RateLimiter(
                requests_per_minute=user_rpm,
                requests_per_hour=user_rph,
                requests_per_day=user_rpd
            )

        # Organization-level limits
        if any([org_rpm, org_rph, org_rpd]):
            self.limiters[RateLimitScope.ORGANIZATION] = RateLimiter(
                requests_per_minute=org_rpm,
                requests_per_hour=org_rph,
                requests_per_day=org_rpd
            )

        # IP-level limits
        if any([ip_rpm, ip_rph]):
            self.limiters[RateLimitScope.IP_ADDRESS] = RateLimiter(
                requests_per_minute=ip_rpm,
                requests_per_hour=ip_rph
            )

        # Global limits
        if any([global_rpm, global_rph]):
            self.limiters[RateLimitScope.GLOBAL] = RateLimiter(
                requests_per_minute=global_rpm,
                requests_per_hour=global_rph
            )

    def check_limit(
        self,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, Optional[RateLimitScope]]:
        """
        Check if request is allowed.

        Args:
            user_id: User identifier
            org_id: Organization identifier
            ip_address: IP address

        Returns:
            Tuple of (allowed, failed_scope)
            - allowed: True if request is allowed
            - failed_scope: Scope that failed (None if allowed)
        """
        # Check global limit first
        if RateLimitScope.GLOBAL in self.limiters:
            if not self.limiters[RateLimitScope.GLOBAL].allow("global"):
                return False, RateLimitScope.GLOBAL

        # Check IP limit
        if ip_address and RateLimitScope.IP_ADDRESS in self.limiters:
            if not self.limiters[RateLimitScope.IP_ADDRESS].allow(ip_address):
                return False, RateLimitScope.IP_ADDRESS

        # Check organization limit
        if org_id and RateLimitScope.ORGANIZATION in self.limiters:
            if not self.limiters[RateLimitScope.ORGANIZATION].allow(org_id):
                return False, RateLimitScope.ORGANIZATION

        # Check user limit
        if user_id and RateLimitScope.USER in self.limiters:
            if not self.limiters[RateLimitScope.USER].allow(user_id):
                return False, RateLimitScope.USER

        return True, None

    async def check_limit_async(
        self,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, Optional[RateLimitScope]]:
        """Async version of check_limit()."""
        # Check global limit first
        if RateLimitScope.GLOBAL in self.limiters:
            if not await self.limiters[RateLimitScope.GLOBAL].allow_async("global"):
                return False, RateLimitScope.GLOBAL

        # Check IP limit
        if ip_address and RateLimitScope.IP_ADDRESS in self.limiters:
            if not await self.limiters[RateLimitScope.IP_ADDRESS].allow_async(ip_address):
                return False, RateLimitScope.IP_ADDRESS

        # Check organization limit
        if org_id and RateLimitScope.ORGANIZATION in self.limiters:
            if not await self.limiters[RateLimitScope.ORGANIZATION].allow_async(org_id):
                return False, RateLimitScope.ORGANIZATION

        # Check user limit
        if user_id and RateLimitScope.USER in self.limiters:
            if not await self.limiters[RateLimitScope.USER].allow_async(user_id):
                return False, RateLimitScope.USER

        return True, None

    def get_retry_after(
        self,
        scope: RateLimitScope,
        identifier: str
    ) -> int:
        """
        Get retry-after time for scope.

        Args:
            scope: Rate limit scope that failed
            identifier: Identifier for that scope

        Returns:
            Seconds until reset
        """
        if scope in self.limiters:
            if scope == RateLimitScope.GLOBAL:
                return self.limiters[scope].get_retry_after("global")
            else:
                return self.limiters[scope].get_retry_after(identifier)
        return 0

    def get_all_usage(
        self,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Dict[str, Dict[str, Tuple[int, int]]]:
        """
        Get usage across all scopes.

        Args:
            user_id: User identifier
            org_id: Organization identifier
            ip_address: IP address

        Returns:
            Dict mapping scope to usage info
        """
        usage = {}

        if user_id and RateLimitScope.USER in self.limiters:
            usage["user"] = self.limiters[RateLimitScope.USER].get_usage(user_id)

        if org_id and RateLimitScope.ORGANIZATION in self.limiters:
            usage["organization"] = self.limiters[RateLimitScope.ORGANIZATION].get_usage(org_id)

        if ip_address and RateLimitScope.IP_ADDRESS in self.limiters:
            usage["ip"] = self.limiters[RateLimitScope.IP_ADDRESS].get_usage(ip_address)

        if RateLimitScope.GLOBAL in self.limiters:
            usage["global"] = self.limiters[RateLimitScope.GLOBAL].get_usage("global")

        return usage
