"""Simple per-tenant rate limiting utilities.

This module provides a minimal in-memory requests-per-minute limiter intended
for Demo 22. It is not designed for production use.
"""
from collections import defaultdict, deque
import time
from typing import Deque, Dict


class RateLimiter:
    """Enforce a requests-per-minute limit per tenant."""

    def __init__(self, rpm: int, window_seconds: int = 60) -> None:
        self.rpm = rpm
        self.window_seconds = window_seconds
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)

    def allow(self, tenant_id: str) -> bool:
        """Return ``True`` if the request is within the tenant's quota."""
        now = time.time()
        window_start = now - self.window_seconds
        hits = self._hits[tenant_id]
        while hits and hits[0] < window_start:
            hits.popleft()
        if len(hits) >= self.rpm:
            return False
        hits.append(now)
        return True
