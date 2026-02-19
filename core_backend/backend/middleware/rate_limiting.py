"""
Rate limiting middleware for authentication and API endpoints.

This module provides comprehensive rate limiting functionality with Redis backend
for distributed rate limiting across multiple server instances.
"""

import time
import json
import logging
import os
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timezone, timedelta
from fastapi import Request, HTTPException, Response
from fastapi.responses import JSONResponse
import redis
import asyncio
from functools import wraps

from ..utils.error_handling import ErrorCode

logger = logging.getLogger(__name__)


class RateLimiter:
    """Redis-backed rate limiter with sliding window algorithm."""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        default_limit: int = 100,
        default_window: int = 3600  # 1 hour in seconds
    ):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.default_limit = default_limit
        self.default_window = default_window

    async def is_allowed(
        self,
        key: str,
        limit: int = None,
        window: int = None,
        cost: int = 1
    ) -> Dict[str, Any]:
        """
        Check if request is allowed under rate limit.

        Args:
            key: Unique identifier for rate limiting (IP, user ID, etc.)
            limit: Maximum requests allowed in window
            window: Time window in seconds
            cost: Cost of this request (default: 1)

        Returns:
            Dict with allowed status and rate limit info
        """
        limit = limit or self.default_limit
        window = window or self.default_window

        try:
            current_time = int(time.time())
            window_start = current_time - window

            # Use Redis pipeline for atomic operations
            pipeline = self.redis_client.pipeline()

            # Remove old entries
            pipeline.zremrangebyscore(key, 0, window_start)

            # Count current requests
            pipeline.zcard(key)

            # Add current request
            pipeline.zadd(key, {str(current_time): current_time})

            # Set expiry
            pipeline.expire(key, window + 60)  # Extra 60 seconds buffer

            results = pipeline.execute()
            current_count = results[1] + cost  # Add cost to current count

            # Calculate rate limit info
            reset_time = current_time + window
            remaining = max(0, limit - current_count)

            result = {
                "allowed": current_count <= limit,
                "limit": limit,
                "remaining": remaining,
                "reset_time": reset_time,
                "retry_after": window if current_count > limit else None
            }

            return result

        except redis.RedisError as e:
            logger.error(f"Redis error in rate limiter: {str(e)}")
            # Fail open - allow request if Redis is down
            return {
                "allowed": True,
                "limit": limit,
                "remaining": limit - 1,
                "reset_time": int(time.time()) + window,
                "retry_after": None
            }
        except Exception as e:
            logger.error(f"Unexpected error in rate limiter: {str(e)}")
            # Fail open
            return {
                "allowed": True,
                "limit": limit,
                "remaining": limit - 1,
                "reset_time": int(time.time()) + window,
                "retry_after": None
            }

    async def increment(
        self,
        key: str,
        cost: int = 1,
        window: int = None
    ) -> None:
        """Increment rate limit counter without checking limit."""
        window = window or self.default_window

        try:
            current_time = int(time.time())
            window_start = current_time - window

            pipeline = self.redis_client.pipeline()
            pipeline.zremrangebyscore(key, 0, window_start)

            for _ in range(cost):
                pipeline.zadd(key, {f"{current_time}_{cost}": current_time})

            pipeline.expire(key, window + 60)
            pipeline.execute()

        except Exception as e:
            logger.error(f"Error incrementing rate limit: {str(e)}")

    def get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded IP first (reverse proxy)
        forwarded_ip = request.headers.get("X-Forwarded-For")
        if forwarded_ip:
            return forwarded_ip.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return getattr(request.client, "host", "unknown")

    def get_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request if authenticated."""
        # This would typically extract from JWT token
        # For now, return None to use IP-based limiting
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                # Would decode JWT here to get user ID
                # token = auth_header[7:]
                # payload = decode_access_token(token)
                # return payload.get("sub")
                pass
            except Exception:
                pass
        return None


# Build Redis URL from environment variables
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_USERNAME = os.getenv("REDIS_USERNAME", "")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

# Construct Redis URL with authentication
if REDIS_USERNAME and REDIS_PASSWORD:
    redis_url = f"redis://{REDIS_USERNAME}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0"
elif REDIS_PASSWORD:
    redis_url = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0"
else:
    redis_url = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

# Global rate limiter instance
rate_limiter = RateLimiter(redis_url=redis_url)


class RateLimitConfig:
    """Rate limiting configurations for different endpoints."""

    # Authentication endpoints (per IP)
    AUTH_SIGNIN = {"limit": 5, "window": 300}  # 5 attempts per 5 minutes
    AUTH_SIGNUP = {"limit": 3, "window": 300}  # 3 attempts per 5 minutes
    AUTH_REFRESH = {"limit": 10, "window": 300}  # 10 attempts per 5 minutes
    PASSWORD_RESET = {"limit": 3, "window": 900}  # 3 attempts per 15 minutes
    EMAIL_VERIFICATION = {"limit": 5, "window": 300}  # 5 attempts per 5 minutes

    # API endpoints (per user)
    API_GENERAL = {"limit": 100, "window": 3600}  # 100 requests per hour
    API_ADMIN = {"limit": 50, "window": 3600}  # 50 requests per hour for admin
    API_ORGANIZATION = {"limit": 200, "window": 3600}  # 200 requests per hour

    # Global rate limits (per IP)
    GLOBAL_IP = {"limit": 1000, "window": 3600}  # 1000 requests per hour per IP

    # TTS endpoints (per user) - Tiered based on user plan
    # Free tier
    TTS_SYNTHESIZE_FREE = {"limit": 10, "window": 60}  # 10 requests per minute
    TTS_CLONE_FREE = {"limit": 3, "window": 60}  # 3 voice cloning requests per minute
    TTS_ESTIMATE_FREE = {"limit": 30, "window": 60}  # 30 cost estimations per minute
    TTS_INFO_FREE = {"limit": 50, "window": 60}  # 50 info requests per minute (providers, voices, etc.)

    # Starter tier
    TTS_SYNTHESIZE_STARTER = {"limit": 30, "window": 60}  # 30 requests per minute
    TTS_CLONE_STARTER = {"limit": 10, "window": 60}  # 10 voice cloning requests per minute
    TTS_ESTIMATE_STARTER = {"limit": 100, "window": 60}  # 100 cost estimations per minute
    TTS_INFO_STARTER = {"limit": 200, "window": 60}  # 200 info requests per minute

    # Pro tier
    TTS_SYNTHESIZE_PRO = {"limit": 100, "window": 60}  # 100 requests per minute
    TTS_CLONE_PRO = {"limit": 30, "window": 60}  # 30 voice cloning requests per minute
    TTS_ESTIMATE_PRO = {"limit": 300, "window": 60}  # 300 cost estimations per minute
    TTS_INFO_PRO = {"limit": 500, "window": 60}  # 500 info requests per minute

    # Enterprise tier
    TTS_SYNTHESIZE_ENTERPRISE = {"limit": 500, "window": 60}  # 500 requests per minute
    TTS_CLONE_ENTERPRISE = {"limit": 100, "window": 60}  # 100 voice cloning requests per minute
    TTS_ESTIMATE_ENTERPRISE = {"limit": 1000, "window": 60}  # 1000 cost estimations per minute
    TTS_INFO_ENTERPRISE = {"limit": 2000, "window": 60}  # 2000 info requests per minute

    # ASR endpoints (per user) - Tiered based on user plan
    # Free tier
    ASR_TRANSCRIBE_FREE = {"limit": 10, "window": 60}  # 10 transcriptions per minute
    ASR_ESTIMATE_FREE = {"limit": 30, "window": 60}  # 30 cost estimations per minute
    ASR_INFO_FREE = {"limit": 50, "window": 60}  # 50 info requests per minute (providers, languages, etc.)

    # Starter tier
    ASR_TRANSCRIBE_STARTER = {"limit": 30, "window": 60}  # 30 transcriptions per minute
    ASR_ESTIMATE_STARTER = {"limit": 100, "window": 60}  # 100 cost estimations per minute
    ASR_INFO_STARTER = {"limit": 200, "window": 60}  # 200 info requests per minute

    # Pro tier
    ASR_TRANSCRIBE_PRO = {"limit": 100, "window": 60}  # 100 transcriptions per minute
    ASR_ESTIMATE_PRO = {"limit": 300, "window": 60}  # 300 cost estimations per minute
    ASR_INFO_PRO = {"limit": 500, "window": 60}  # 500 info requests per minute

    # Enterprise tier
    ASR_TRANSCRIBE_ENTERPRISE = {"limit": 500, "window": 60}  # 500 transcriptions per minute
    ASR_ESTIMATE_ENTERPRISE = {"limit": 1000, "window": 60}  # 1000 cost estimations per minute
    ASR_INFO_ENTERPRISE = {"limit": 2000, "window": 60}  # 2000 info requests per minute

    # LLM endpoints (per user) - Tiered based on user plan
    # Free tier
    LLM_CHAT_FREE = {"limit": 5, "window": 60}  # 5 chat requests per minute
    LLM_CHAT_STREAM_FREE = {"limit": 3, "window": 60}  # 3 streaming requests per minute
    LLM_ESTIMATE_FREE = {"limit": 30, "window": 60}  # 30 cost estimations per minute
    LLM_INFO_FREE = {"limit": 50, "window": 60}  # 50 info requests per minute (providers, models, etc.)

    # Starter tier
    LLM_CHAT_STARTER = {"limit": 20, "window": 60}  # 20 chat requests per minute
    LLM_CHAT_STREAM_STARTER = {"limit": 10, "window": 60}  # 10 streaming requests per minute
    LLM_ESTIMATE_STARTER = {"limit": 100, "window": 60}  # 100 cost estimations per minute
    LLM_INFO_STARTER = {"limit": 200, "window": 60}  # 200 info requests per minute

    # Pro tier
    LLM_CHAT_PRO = {"limit": 100, "window": 60}  # 100 chat requests per minute
    LLM_CHAT_STREAM_PRO = {"limit": 50, "window": 60}  # 50 streaming requests per minute
    LLM_ESTIMATE_PRO = {"limit": 9999, "window": 60}  # Unlimited cost estimations
    LLM_INFO_PRO = {"limit": 1000, "window": 60}  # 1000 info requests per minute

    # Enterprise tier
    LLM_CHAT_ENTERPRISE = {"limit": 500, "window": 60}  # 500 chat requests per minute
    LLM_CHAT_STREAM_ENTERPRISE = {"limit": 200, "window": 60}  # 200 streaming requests per minute
    LLM_ESTIMATE_ENTERPRISE = {"limit": 9999, "window": 60}  # Unlimited cost estimations
    LLM_INFO_ENTERPRISE = {"limit": 2000, "window": 60}  # 2000 info requests per minute


def rate_limit(
    limit: int = None,
    window: int = None,
    per: str = "ip",  # "ip", "user", or "custom"
    key_func: Optional[Callable] = None,
    cost: int = 1,
    skip_successful_auth: bool = False
):
    """
    Rate limiting decorator for FastAPI endpoints.

    Args:
        limit: Maximum requests allowed in window
        window: Time window in seconds
        per: Rate limiting scope ("ip", "user", or "custom")
        key_func: Custom function to generate rate limit key
        cost: Cost of this request
        skip_successful_auth: Skip rate limiting for successful auth requests
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find request object in args or kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if not request:
                request = kwargs.get('request')

            if not request:
                # No request object found, proceed without rate limiting
                return await func(*args, **kwargs)

            # Generate rate limit key
            if key_func:
                key = key_func(request)
            elif per == "ip":
                key = f"rate_limit:ip:{rate_limiter.get_client_ip(request)}"
            elif per == "user":
                user_id = rate_limiter.get_user_id(request)
                if user_id:
                    key = f"rate_limit:user:{user_id}"
                else:
                    # Fall back to IP if no user
                    key = f"rate_limit:ip:{rate_limiter.get_client_ip(request)}"
            else:
                key = f"rate_limit:custom:{per}"

            # Check rate limit
            result = await rate_limiter.is_allowed(key, limit, window, cost)

            # Add rate limit headers to response
            def add_rate_limit_headers(response):
                if hasattr(response, 'headers'):
                    response.headers["X-RateLimit-Limit"] = str(result["limit"])
                    response.headers["X-RateLimit-Remaining"] = str(result["remaining"])
                    response.headers["X-RateLimit-Reset"] = str(result["reset_time"])
                    if result["retry_after"]:
                        response.headers["Retry-After"] = str(result["retry_after"])
                return response

            if not result["allowed"]:
                # Rate limit exceeded
                error_response = {
                    "code": ErrorCode.RATE_LIMIT_EXCEEDED,
                    "message": "Rate limit exceeded",
                    "details": {
                        "limit": result["limit"],
                        "reset_time": result["reset_time"],
                        "retry_after": result["retry_after"]
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

                response = JSONResponse(
                    status_code=429,
                    content=error_response
                )
                return add_rate_limit_headers(response)

            # Execute the original function
            try:
                response = await func(*args, **kwargs)

                # For successful auth requests, we might want to reset the counter
                if skip_successful_auth and hasattr(response, 'status_code') and response.status_code == 200:
                    # Reset rate limit for successful auth
                    try:
                        rate_limiter.redis_client.delete(key)
                    except Exception as e:
                        logger.warning(f"Failed to reset rate limit after successful auth: {e}")

                return add_rate_limit_headers(response)

            except HTTPException as e:
                # For failed requests, still respect rate limiting
                raise e
            except Exception as e:
                # For other errors, still respect rate limiting
                raise e

        return wrapper
    return decorator


def auth_rate_limit(endpoint_type: str):
    """Convenience decorator for authentication endpoints."""
    configs = {
        "signin": RateLimitConfig.AUTH_SIGNIN,
        "signup": RateLimitConfig.AUTH_SIGNUP,
        "refresh": RateLimitConfig.AUTH_REFRESH,
        "password_reset": RateLimitConfig.PASSWORD_RESET,
        "email_verification": RateLimitConfig.EMAIL_VERIFICATION
    }

    config = configs.get(endpoint_type, RateLimitConfig.API_GENERAL)

    return rate_limit(
        limit=config["limit"],
        window=config["window"],
        per="ip",
        skip_successful_auth=(endpoint_type in ["signin", "refresh"])
    )


def api_rate_limit(endpoint_type: str = "general"):
    """Convenience decorator for API endpoints."""
    configs = {
        "general": RateLimitConfig.API_GENERAL,
        "admin": RateLimitConfig.API_ADMIN,
        "organization": RateLimitConfig.API_ORGANIZATION
    }

    config = configs.get(endpoint_type, RateLimitConfig.API_GENERAL)

    return rate_limit(
        limit=config["limit"],
        window=config["window"],
        per="user"
    )


def tts_rate_limit(endpoint_type: str = "synthesize", tier: str = "free"):
    """
    Convenience decorator for TTS endpoints with tiered rate limiting.

    Args:
        endpoint_type: Type of TTS endpoint ("synthesize", "clone", "estimate", "info")
        tier: User tier ("free", "starter", "pro", "enterprise")
    """
    # Map endpoint types and tiers to configurations
    config_map = {
        "synthesize": {
            "free": RateLimitConfig.TTS_SYNTHESIZE_FREE,
            "starter": RateLimitConfig.TTS_SYNTHESIZE_STARTER,
            "pro": RateLimitConfig.TTS_SYNTHESIZE_PRO,
            "enterprise": RateLimitConfig.TTS_SYNTHESIZE_ENTERPRISE,
        },
        "clone": {
            "free": RateLimitConfig.TTS_CLONE_FREE,
            "starter": RateLimitConfig.TTS_CLONE_STARTER,
            "pro": RateLimitConfig.TTS_CLONE_PRO,
            "enterprise": RateLimitConfig.TTS_CLONE_ENTERPRISE,
        },
        "estimate": {
            "free": RateLimitConfig.TTS_ESTIMATE_FREE,
            "starter": RateLimitConfig.TTS_ESTIMATE_STARTER,
            "pro": RateLimitConfig.TTS_ESTIMATE_PRO,
            "enterprise": RateLimitConfig.TTS_ESTIMATE_ENTERPRISE,
        },
        "info": {
            "free": RateLimitConfig.TTS_INFO_FREE,
            "starter": RateLimitConfig.TTS_INFO_STARTER,
            "pro": RateLimitConfig.TTS_INFO_PRO,
            "enterprise": RateLimitConfig.TTS_INFO_ENTERPRISE,
        },
    }

    # Get config for endpoint type and tier (default to free tier if tier not found)
    endpoint_configs = config_map.get(endpoint_type, config_map["info"])
    config = endpoint_configs.get(tier, endpoint_configs["free"])

    return rate_limit(
        limit=config["limit"],
        window=config["window"],
        per="user"
    )


def custom_rate_limit_key(prefix: str):
    """Generate custom rate limit key function."""
    def key_func(request: Request) -> str:
        ip = rate_limiter.get_client_ip(request)
        user_id = rate_limiter.get_user_id(request)
        if user_id:
            return f"rate_limit:{prefix}:user:{user_id}"
        else:
            return f"rate_limit:{prefix}:ip:{ip}"
    return key_func


# ============================================================================
# FastAPI Dependency-based Rate Limiting
# ============================================================================

class RateLimitDependency:
    """
    FastAPI dependency for rate limiting.

    Usage:
        @router.get("/endpoint")
        async def endpoint(
            request: Request,
            rate_limit_check: None = Depends(RateLimitDependency(limit=10, window=60))
        ):
            ...
    """

    def __init__(
        self,
        limit: int = None,
        window: int = None,
        per: str = "user",
        config: Dict[str, int] = None
    ):
        """
        Initialize rate limit dependency.

        Args:
            limit: Maximum requests allowed in window
            window: Time window in seconds
            per: Rate limiting scope ("ip" or "user")
            config: Pre-configured rate limit config (e.g., RateLimitConfig.TTS_SYNTHESIZE_FREE)
        """
        if config:
            self.limit = config["limit"]
            self.window = config["window"]
        else:
            self.limit = limit or 100
            self.window = window or 60
        self.per = per

    async def __call__(self, request: Request, response: Response):
        """Check rate limit and raise HTTPException if exceeded."""
        # Generate rate limit key
        if self.per == "ip":
            ip = rate_limiter.get_client_ip(request)
            key = f"rate_limit:ip:{ip}"
        else:  # per == "user"
            user_id = rate_limiter.get_user_id(request)
            if user_id:
                key = f"rate_limit:user:{user_id}"
            else:
                # Fall back to IP if no user
                ip = rate_limiter.get_client_ip(request)
                key = f"rate_limit:ip:{ip}"

        # Check rate limit
        result = await rate_limiter.is_allowed(key, self.limit, self.window)

        if not result["allowed"]:
            # Rate limit exceeded
            error_response = {
                "code": ErrorCode.RATE_LIMIT_EXCEEDED,
                "message": "Rate limit exceeded. Please try again later.",
                "details": {
                    "limit": result["limit"],
                    "reset_time": result["reset_time"],
                    "retry_after": result["retry_after"]
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            # Raise exception with rate limit headers
            raise HTTPException(
                status_code=429,
                detail=error_response,
                headers={
                    "X-RateLimit-Limit": str(result["limit"]),
                    "X-RateLimit-Remaining": str(result["remaining"]),
                    "X-RateLimit-Reset": str(result["reset_time"]),
                    "Retry-After": str(result["retry_after"])
                }
            )

        # Rate limit not exceeded - add headers to response
        response.headers["X-RateLimit-Limit"] = str(result["limit"])
        response.headers["X-RateLimit-Remaining"] = str(result["remaining"])
        response.headers["X-RateLimit-Reset"] = str(result["reset_time"])

        return None


def get_tts_rate_limit(endpoint_type: str = "synthesize", tier: str = "free"):
    """
    Get rate limit dependency for TTS endpoints.

    Args:
        endpoint_type: Type of TTS endpoint ("synthesize", "clone", "estimate", "info")
        tier: User tier ("free", "starter", "pro", "enterprise")

    Returns:
        RateLimitDependency configured for the specified endpoint and tier

    Usage:
        @router.post("/synthesize")
        async def synthesize(
            request: Request,
            rate_limit: None = Depends(get_tts_rate_limit("synthesize", "free")),
            user: dict = Depends(get_current_user_mongo)
        ):
            ...
    """
    # Map endpoint types and tiers to configurations
    config_map = {
        "synthesize": {
            "free": RateLimitConfig.TTS_SYNTHESIZE_FREE,
            "starter": RateLimitConfig.TTS_SYNTHESIZE_STARTER,
            "pro": RateLimitConfig.TTS_SYNTHESIZE_PRO,
            "enterprise": RateLimitConfig.TTS_SYNTHESIZE_ENTERPRISE,
        },
        "clone": {
            "free": RateLimitConfig.TTS_CLONE_FREE,
            "starter": RateLimitConfig.TTS_CLONE_STARTER,
            "pro": RateLimitConfig.TTS_CLONE_PRO,
            "enterprise": RateLimitConfig.TTS_CLONE_ENTERPRISE,
        },
        "estimate": {
            "free": RateLimitConfig.TTS_ESTIMATE_FREE,
            "starter": RateLimitConfig.TTS_ESTIMATE_STARTER,
            "pro": RateLimitConfig.TTS_ESTIMATE_PRO,
            "enterprise": RateLimitConfig.TTS_ESTIMATE_ENTERPRISE,
        },
        "info": {
            "free": RateLimitConfig.TTS_INFO_FREE,
            "starter": RateLimitConfig.TTS_INFO_STARTER,
            "pro": RateLimitConfig.TTS_INFO_PRO,
            "enterprise": RateLimitConfig.TTS_INFO_ENTERPRISE,
        },
    }

    # Get config for endpoint type and tier (default to free tier if tier not found)
    endpoint_configs = config_map.get(endpoint_type, config_map["info"])
    config = endpoint_configs.get(tier, endpoint_configs["free"])

    return RateLimitDependency(config=config, per="user")


def get_asr_rate_limit(endpoint_type: str = "transcribe", tier: str = "free"):
    """
    Get rate limit dependency for ASR endpoints.

    Args:
        endpoint_type: Type of ASR endpoint ("transcribe", "estimate", "info")
        tier: User tier ("free", "starter", "pro", "enterprise")

    Returns:
        RateLimitDependency configured for the specified endpoint and tier

    Usage:
        @router.post("/transcribe")
        async def transcribe(
            request: Request,
            rate_limit: None = Depends(get_asr_rate_limit("transcribe", "free")),
            user: dict = Depends(get_current_user_mongo)
        ):
            ...
    """
    # Map endpoint types and tiers to configurations
    config_map = {
        "transcribe": {
            "free": RateLimitConfig.ASR_TRANSCRIBE_FREE,
            "starter": RateLimitConfig.ASR_TRANSCRIBE_STARTER,
            "pro": RateLimitConfig.ASR_TRANSCRIBE_PRO,
            "enterprise": RateLimitConfig.ASR_TRANSCRIBE_ENTERPRISE,
        },
        "estimate": {
            "free": RateLimitConfig.ASR_ESTIMATE_FREE,
            "starter": RateLimitConfig.ASR_ESTIMATE_STARTER,
            "pro": RateLimitConfig.ASR_ESTIMATE_PRO,
            "enterprise": RateLimitConfig.ASR_ESTIMATE_ENTERPRISE,
        },
        "info": {
            "free": RateLimitConfig.ASR_INFO_FREE,
            "starter": RateLimitConfig.ASR_INFO_STARTER,
            "pro": RateLimitConfig.ASR_INFO_PRO,
            "enterprise": RateLimitConfig.ASR_INFO_ENTERPRISE,
        },
    }

    # Get config for endpoint type and tier (default to free tier if tier not found)
    endpoint_configs = config_map.get(endpoint_type, config_map["info"])
    config = endpoint_configs.get(tier, endpoint_configs["free"])

    return RateLimitDependency(config=config, per="user")


def get_llm_rate_limit(endpoint_type: str = "chat", tier: str = "free"):
    """
    Get rate limit dependency for LLM endpoints.

    Args:
        endpoint_type: Type of LLM endpoint ("chat", "chat_stream", "estimate", "info")
        tier: User tier ("free", "starter", "pro", "enterprise")

    Returns:
        RateLimitDependency configured for the specified endpoint and tier

    Usage:
        @router.post("/chat")
        async def chat(
            request: Request,
            rate_limit: None = Depends(get_llm_rate_limit("chat", "free")),
            user: dict = Depends(get_current_user_mongo)
        ):
            ...
    """
    # Map endpoint types and tiers to configurations
    config_map = {
        "chat": {
            "free": RateLimitConfig.LLM_CHAT_FREE,
            "starter": RateLimitConfig.LLM_CHAT_STARTER,
            "pro": RateLimitConfig.LLM_CHAT_PRO,
            "enterprise": RateLimitConfig.LLM_CHAT_ENTERPRISE,
        },
        "chat_stream": {
            "free": RateLimitConfig.LLM_CHAT_STREAM_FREE,
            "starter": RateLimitConfig.LLM_CHAT_STREAM_STARTER,
            "pro": RateLimitConfig.LLM_CHAT_STREAM_PRO,
            "enterprise": RateLimitConfig.LLM_CHAT_STREAM_ENTERPRISE,
        },
        "estimate": {
            "free": RateLimitConfig.LLM_ESTIMATE_FREE,
            "starter": RateLimitConfig.LLM_ESTIMATE_STARTER,
            "pro": RateLimitConfig.LLM_ESTIMATE_PRO,
            "enterprise": RateLimitConfig.LLM_ESTIMATE_ENTERPRISE,
        },
        "info": {
            "free": RateLimitConfig.LLM_INFO_FREE,
            "starter": RateLimitConfig.LLM_INFO_STARTER,
            "pro": RateLimitConfig.LLM_INFO_PRO,
            "enterprise": RateLimitConfig.LLM_INFO_ENTERPRISE,
        },
    }

    # Get config for endpoint type and tier (default to free tier if tier not found)
    endpoint_configs = config_map.get(endpoint_type, config_map["info"])
    config = endpoint_configs.get(tier, endpoint_configs["free"])

    return RateLimitDependency(config=config, per="user")


class RateLimitHeadersMiddleware:
    """
    Middleware to add rate limit headers to responses.

    This middleware checks if rate limit info was added to request.state
    by RateLimitDependency and adds the appropriate headers to the response.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Track if headers have been sent
        headers_added = False

        async def send_wrapper(message):
            nonlocal headers_added

            if message["type"] == "http.response.start" and not headers_added:
                # Try to get rate limit info from request state
                request = scope.get("state", {})
                rate_limit_info = getattr(request, "rate_limit_info", None) if hasattr(request, "__dict__") else None

                # If we have rate limit info from a dependency, add headers
                if rate_limit_info:
                    headers = list(message.get("headers", []))

                    # Add rate limit headers
                    headers.append((b"x-ratelimit-limit", str(rate_limit_info["limit"]).encode()))
                    headers.append((b"x-ratelimit-remaining", str(rate_limit_info["remaining"]).encode()))
                    headers.append((b"x-ratelimit-reset", str(rate_limit_info["reset_time"]).encode()))

                    message["headers"] = headers
                    headers_added = True

            await send(message)

        await self.app(scope, receive, send_wrapper)


class RateLimitMiddleware:
    """Global rate limiting middleware for all requests."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)

        # Global IP rate limiting
        ip = rate_limiter.get_client_ip(request)
        key = f"rate_limit:global:ip:{ip}"

        result = await rate_limiter.is_allowed(
            key,
            RateLimitConfig.GLOBAL_IP["limit"],
            RateLimitConfig.GLOBAL_IP["window"]
        )

        if not result["allowed"]:
            # Send rate limit exceeded response
            error_response = {
                "code": ErrorCode.RATE_LIMIT_EXCEEDED,
                "message": "Global rate limit exceeded",
                "details": {
                    "limit": result["limit"],
                    "reset_time": result["reset_time"],
                    "retry_after": result["retry_after"]
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            response = JSONResponse(
                status_code=429,
                content=error_response
            )

            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(result["limit"])
            response.headers["X-RateLimit-Remaining"] = str(result["remaining"])
            response.headers["X-RateLimit-Reset"] = str(result["reset_time"])
            response.headers["Retry-After"] = str(result["retry_after"])

            await response(scope, receive, send)
            return

        # Continue with the request
        await self.app(scope, receive, send)


# Utility functions for manual rate limiting

async def check_rate_limit(
    request: Request,
    endpoint_type: str,
    custom_key: str = None
) -> Dict[str, Any]:
    """Manually check rate limit for a request."""
    configs = {
        "signin": RateLimitConfig.AUTH_SIGNIN,
        "signup": RateLimitConfig.AUTH_SIGNUP,
        "refresh": RateLimitConfig.AUTH_REFRESH,
        "password_reset": RateLimitConfig.PASSWORD_RESET,
        "general": RateLimitConfig.API_GENERAL,
        "admin": RateLimitConfig.API_ADMIN
    }

    config = configs.get(endpoint_type, RateLimitConfig.API_GENERAL)

    if custom_key:
        key = custom_key
    else:
        ip = rate_limiter.get_client_ip(request)
        user_id = rate_limiter.get_user_id(request)

        if user_id and endpoint_type not in ["signin", "signup", "password_reset"]:
            key = f"rate_limit:user:{user_id}"
        else:
            key = f"rate_limit:ip:{ip}"

    return await rate_limiter.is_allowed(
        key,
        config["limit"],
        config["window"]
    )


async def increment_rate_limit(
    request: Request,
    endpoint_type: str,
    cost: int = 1,
    custom_key: str = None
) -> None:
    """Manually increment rate limit counter."""
    configs = {
        "signin": RateLimitConfig.AUTH_SIGNIN,
        "signup": RateLimitConfig.AUTH_SIGNUP,
        "refresh": RateLimitConfig.AUTH_REFRESH,
        "password_reset": RateLimitConfig.PASSWORD_RESET,
        "general": RateLimitConfig.API_GENERAL,
        "admin": RateLimitConfig.API_ADMIN
    }

    config = configs.get(endpoint_type, RateLimitConfig.API_GENERAL)

    if custom_key:
        key = custom_key
    else:
        ip = rate_limiter.get_client_ip(request)
        user_id = rate_limiter.get_user_id(request)

        if user_id and endpoint_type not in ["signin", "signup", "password_reset"]:
            key = f"rate_limit:user:{user_id}"
        else:
            key = f"rate_limit:ip:{ip}"

    await rate_limiter.increment(key, cost, config["window"])


# Health check for rate limiter
async def rate_limiter_health_check() -> Dict[str, Any]:
    """Check rate limiter health."""
    try:
        # Test Redis connection
        rate_limiter.redis_client.ping()

        # Test basic rate limiting functionality
        test_key = f"health_check:{int(time.time())}"
        result = await rate_limiter.is_allowed(test_key, 1, 60)

        # Cleanup test key
        try:
            rate_limiter.redis_client.delete(test_key)
        except Exception:
            pass

        return {
            "status": "healthy",
            "redis_connected": True,
            "rate_limiting_functional": result["allowed"]
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "redis_connected": False,
            "error": str(e)
        }