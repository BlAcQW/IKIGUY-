"""
Middleware for EstateFlow API.

Includes rate limiting for anonymous booking requests.
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware for anonymous booking requests.

    Limits anonymous users to 3 bookings per IP address per hour.
    Authenticated users are not rate limited.
    """

    def __init__(self, app, limit: int = 3, window_hours: int = 1):
        """
        Initialize rate limiter.

        Args:
            app: FastAPI application
            limit: Maximum requests per window (default: 3)
            window_hours: Time window in hours (default: 1)
        """
        super().__init__(app)
        self.requests: Dict[str, List[datetime]] = defaultdict(list)
        self.limit = limit
        self.window = timedelta(hours=window_hours)

    async def dispatch(self, request: Request, call_next):
        """
        Process request and apply rate limiting.

        Only applies to POST /api/v1/bookings for anonymous users.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler

        Returns:
            Response from next handler

        Raises:
            HTTPException: 429 if rate limit exceeded
        """
        # Only apply to POST /bookings for anonymous users
        if request.method == "POST" and "/bookings" in str(request.url.path):
            # Check if authenticated
            auth_header = request.headers.get("authorization")

            if not auth_header:  # Anonymous request
                # Get client IP
                ip = request.client.host if request.client else "unknown"

                # Skip for unknown IPs (shouldn't happen)
                if ip != "unknown":
                    now = datetime.now()

                    # Clean old requests outside time window
                    self.requests[ip] = [
                        req_time
                        for req_time in self.requests[ip]
                        if now - req_time < self.window
                    ]

                    # Check if limit exceeded
                    if len(self.requests[ip]) >= self.limit:
                        logger.warning(
                            f"Rate limit exceeded for IP {ip}. "
                            f"{len(self.requests[ip])} requests in last hour."
                        )
                        raise HTTPException(
                            status_code=429,
                            detail=f"Rate limit exceeded. Maximum {self.limit} bookings per hour for anonymous users. Please try again later or create an account.",
                        )

                    # Record this request
                    self.requests[ip].append(now)
                    logger.info(
                        f"Anonymous booking request from IP {ip}. "
                        f"Count: {len(self.requests[ip])}/{self.limit}"
                    )

        # Process request
        return await call_next(request)

    def reset(self):
        """Reset rate limit counters. Useful for testing."""
        self.requests.clear()
