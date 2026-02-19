"""
Usage and Analytics API v1 Endpoints

Provides usage statistics, quota information, and analytics for API keys.

**Version:** 1.0.0
**Stability:** Stable
**Authentication:** API Key required
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from ...middleware.api_key_auth import verify_api_key
from ...middleware.usage_tracker import usage_tracker
from ...middleware.rate_limiter import rate_limiter

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/usage",
    tags=["Usage & Analytics (v1)"],
    responses={
        401: {"description": "Invalid API key"},
        429: {"description": "Rate limit exceeded"},
    }
)


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class QuotaStatusResponse(BaseModel):
    """Quota status for an API key."""
    plan: str = Field(..., description="Plan tier")
    daily: dict = Field(..., description="Daily quota information")
    monthly: dict = Field(..., description="Monthly quota information")

    class Config:
        json_schema_extra = {
            "example": {
                "plan": "free",
                "daily": {
                    "limit": 100,
                    "used": 45,
                    "remaining": 55,
                    "reset_at": "2025-10-24T00:00:00"
                },
                "monthly": {
                    "limit": 1000,
                    "used": 456,
                    "remaining": 544,
                    "reset_at": "2025-11-01T00:00:00"
                }
            }
        }


class RateLimitStatusResponse(BaseModel):
    """Rate limit status for an API key."""
    tokens_remaining: int = Field(..., description="Tokens remaining in current window")
    tokens_capacity: int = Field(..., description="Maximum tokens")
    refill_rate: float = Field(..., description="Tokens refilled per minute")
    last_request: Optional[str] = Field(None, description="Last request timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "tokens_remaining": 8,
                "tokens_capacity": 20,
                "refill_rate": 10.0,
                "last_request": "2025-10-23T12:05:00"
            }
        }


class UsageStatsResponse(BaseModel):
    """Usage statistics for an API key."""
    total_requests: int = Field(..., description="Total number of requests")
    total_cost: float = Field(..., description="Total cost in credits")
    avg_response_time_ms: float = Field(..., description="Average response time")
    requests_by_endpoint: dict = Field(..., description="Requests grouped by endpoint")
    requests_by_status: dict = Field(..., description="Requests grouped by status code")
    daily_usage: list = Field(..., description="Daily usage breakdown")

    class Config:
        json_schema_extra = {
            "example": {
                "total_requests": 150,
                "total_cost": 125.5,
                "avg_response_time_ms": 245.3,
                "requests_by_endpoint": {
                    "/api/v1/assistants": 50,
                    "/api/v1/calls": 100
                },
                "requests_by_status": {
                    "200": 145,
                    "201": 5
                },
                "daily_usage": [
                    {"date": "2025-10-20", "requests": 30, "cost": 25.0},
                    {"date": "2025-10-21", "requests": 45, "cost": 37.5}
                ]
            }
        }


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/quota", response_model=QuotaStatusResponse)
async def get_quota_status(
    api_key_info: dict = Depends(verify_api_key)
):
    """
    Get quota status for your API key.

    Returns current usage and limits for daily and monthly quotas.

    **Example Request:**
    ```bash
    curl -X GET https://developer.ailabsafrica.com/api/v1/usage/quota \\
      -H "X-API-Key: your_api_key"
    ```

    **Example Response:**
    ```json
    {
      "plan": "free",
      "daily": {
        "limit": 100,
        "used": 45,
        "remaining": 55,
        "reset_at": "2025-10-24T00:00:00"
      },
      "monthly": {
        "limit": 1000,
        "used": 456,
        "remaining": 544,
        "reset_at": "2025-11-01T00:00:00"
      }
    }
    ```

    Returns:
        QuotaStatusResponse: Quota information
    """
    api_key = api_key_info["key_id"]
    plan = api_key_info.get("plan", "free")

    quota_status = usage_tracker.get_quota_status(api_key, plan)
    return QuotaStatusResponse(**quota_status)


@router.get("/rate-limit", response_model=RateLimitStatusResponse)
async def get_rate_limit_status(
    api_key_info: dict = Depends(verify_api_key)
):
    """
    Get rate limit status for your API key.

    Returns current rate limit information including remaining tokens
    and refill rate.

    **Example Request:**
    ```bash
    curl -X GET https://developer.ailabsafrica.com/api/v1/usage/rate-limit \\
      -H "X-API-Key: your_api_key"
    ```

    **Example Response:**
    ```json
    {
      "tokens_remaining": 8,
      "tokens_capacity": 20,
      "refill_rate": 10.0,
      "last_request": "2025-10-23T12:05:00"
    }
    ```

    Returns:
        RateLimitStatusResponse: Rate limit information
    """
    api_key = api_key_info["key_id"]

    rate_limit_stats = rate_limiter.get_stats(api_key)
    return RateLimitStatusResponse(**rate_limit_stats)


@router.get("/stats", response_model=UsageStatsResponse)
async def get_usage_stats(
    days: int = Query(30, ge=1, le=90, description="Number of days to include (1-90)"),
    api_key_info: dict = Depends(verify_api_key)
):
    """
    Get usage statistics for your API key.

    Returns detailed usage analytics including:
    - Total requests and costs
    - Average response time
    - Requests by endpoint
    - Requests by status code
    - Daily usage breakdown

    **Query Parameters:**
    - `days` (optional): Number of days to include (1-90, default: 30)

    **Example Request:**
    ```bash
    curl -X GET "https://developer.ailabsafrica.com/api/v1/usage/stats?days=7" \\
      -H "X-API-Key: your_api_key"
    ```

    **Example Response:**
    ```json
    {
      "total_requests": 150,
      "total_cost": 125.5,
      "avg_response_time_ms": 245.3,
      "requests_by_endpoint": {
        "/api/v1/assistants": 50,
        "/api/v1/calls": 100
      },
      "requests_by_status": {
        "200": 145,
        "201": 5
      },
      "daily_usage": [
        {"date": "2025-10-20", "requests": 30, "cost": 25.0},
        {"date": "2025-10-21", "requests": 45, "cost": 37.5}
      ]
    }
    ```

    Args:
        days: Number of days to include in stats

    Returns:
        UsageStatsResponse: Usage statistics
    """
    api_key = api_key_info["key_id"]

    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Get usage stats
    stats = usage_tracker.get_usage_stats(api_key, start_date, end_date)

    return UsageStatsResponse(**stats)


@router.get("/summary")
async def get_usage_summary(
    api_key_info: dict = Depends(verify_api_key)
):
    """
    Get a comprehensive usage summary.

    Returns all usage information in a single response:
    - Quota status
    - Rate limit status
    - Usage statistics (last 7 days)

    **Example Request:**
    ```bash
    curl -X GET https://developer.ailabsafrica.com/api/v1/usage/summary \\
      -H "X-API-Key: your_api_key"
    ```

    **Example Response:**
    ```json
    {
      "quota": {
        "plan": "free",
        "daily": {...},
        "monthly": {...}
      },
      "rate_limit": {
        "tokens_remaining": 8,
        "tokens_capacity": 20,
        ...
      },
      "stats": {
        "total_requests": 150,
        "total_cost": 125.5,
        ...
      }
    }
    ```

    Returns:
        Dict with comprehensive usage summary
    """
    api_key = api_key_info["key_id"]
    plan = api_key_info.get("plan", "free")

    # Get all usage information
    quota_status = usage_tracker.get_quota_status(api_key, plan)
    rate_limit_stats = rate_limiter.get_stats(api_key)

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)
    usage_stats = usage_tracker.get_usage_stats(api_key, start_date, end_date)

    return {
        "quota": quota_status,
        "rate_limit": rate_limit_stats,
        "stats": usage_stats
    }
