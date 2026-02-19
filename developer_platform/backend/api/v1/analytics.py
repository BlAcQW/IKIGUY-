"""
Analytics API v1 Endpoints

Public, versioned, stable API for usage analytics and cost tracking.

**Version:** 1.0.0
**Stability:** Stable - no breaking changes allowed
**Rate Limits:** 20 requests/minute (Free tier)
**Authentication:** API Key required (X-API-Key header)

Breaking changes require releasing v2.
"""

import logging
import httpx
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from pydantic import BaseModel, Field

# Import middleware
from ...middleware.api_key_auth import verify_api_key
from ...middleware.rate_limiter import get_rate_limit_dependency

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/analytics",
    tags=["Analytics v1"],
    responses={
        401: {"description": "Invalid API key"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"},
    }
)

# ============================================================================
# Pydantic Models
# ============================================================================

class UsageMetrics(BaseModel):
    """Overall usage metrics."""
    total_requests: int
    total_cost: float
    total_calls: int
    total_duration_seconds: float
    avg_cost_per_request: float
    services_used: List[str]
    period_start: str
    period_end: str


class ServiceUsage(BaseModel):
    """Usage breakdown by service."""
    service: str
    request_count: int
    total_cost: float
    avg_cost: float
    success_rate: float


class AssistantMetrics(BaseModel):
    """Metrics for a VAPI assistant."""
    assistant_id: str
    assistant_name: Optional[str] = None
    total_calls: int
    successful_calls: int
    failed_calls: int
    avg_duration_seconds: float
    total_duration_seconds: float
    success_rate: float
    total_cost: float
    cost_breakdown: Dict[str, float]
    period_start: str
    period_end: str


class CallRecord(BaseModel):
    """Individual call record."""
    call_id: str
    assistant_id: str
    status: str
    duration_seconds: Optional[float] = None
    cost: float
    started_at: str
    ended_at: Optional[str] = None
    transcript: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CallListResponse(BaseModel):
    """List of calls with pagination."""
    calls: List[CallRecord]
    pagination: Dict[str, Any]
    summary: Dict[str, Any]


class CostBreakdown(BaseModel):
    """Detailed cost breakdown."""
    total_cost: float
    currency: str
    services: Dict[str, float]
    breakdown: List[Dict[str, Any]]
    period_start: str
    period_end: str


# ============================================================================
# Helper Functions
# ============================================================================

async def get_core_backend_url() -> str:
    """Get Core Backend URL from environment or default."""
    import os
    return os.getenv("CORE_BACKEND_URL", "https://api.ailabsafrica.com")


async def call_core_backend(
    endpoint: str,
    method: str = "GET",
    json_data: Optional[Dict] = None,
    user_id: Optional[str] = None,
    timeout: float = 30.0
) -> Dict[str, Any]:
    """Call Core Backend API."""
    base_url = await get_core_backend_url()
    url = f"{base_url}{endpoint}"

    headers = {"Content-Type": "application/json"}

    if user_id:
        headers["X-User-Id"] = user_id

    logger.info(f"Calling Core Backend: {method} {url}")

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            if method == "GET":
                response = await client.get(url, headers=headers)
            elif method == "POST":
                response = await client.post(url, json=json_data, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            if response.status_code >= 400:
                error_text = response.text
                logger.error(f"Core Backend error: {response.status_code} - {error_text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail={
                        "error": {
                            "code": "BACKEND_ERROR",
                            "message": f"Core Backend error: {error_text}"
                        },
                        "request_id": f"req_{datetime.utcnow().timestamp()}",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )

            return response.json()

        except httpx.RequestError as e:
            logger.error(f"Core Backend request failed: {e}")
            raise HTTPException(
                status_code=503,
                detail={
                    "error": {
                        "code": "SERVICE_UNAVAILABLE",
                        "message": "Core Backend service unavailable"
                    },
                    "request_id": f"req_{datetime.utcnow().timestamp()}",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )


# ============================================================================
# API Routes
# ============================================================================

@router.get(
    "/usage",
    response_model=UsageMetrics,
    summary="Get overall usage metrics",
    description="""
    Get comprehensive usage metrics across all services.

    **Rate Limit:** 20 requests/minute
    **Cost:** Free

    **Query Parameters:**
    - `period`: Time period (7d, 30d, 90d, all) - default: 30d
    - `start_date`: Custom start date (ISO 8601) - overrides period
    - `end_date`: Custom end date (ISO 8601)

    **Example Response:**
    ```json
    {
        "total_requests": 1250,
        "total_cost": 125.50,
        "total_calls": 450,
        "total_duration_seconds": 12500.0,
        "avg_cost_per_request": 0.10,
        "services_used": ["tts", "asr", "llm", "vapi"],
        "period_start": "2025-09-26T00:00:00",
        "period_end": "2025-10-26T23:59:59"
    }
    ```
    """,
    response_description="Overall usage metrics"
)
async def get_usage_metrics(
    period: str = Query("30d", description="Time period (7d, 30d, 90d, all)"),
    start_date: Optional[str] = Query(None, description="Custom start date (ISO 8601)"),
    end_date: Optional[str] = Query(None, description="Custom end date (ISO 8601)"),
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(get_rate_limit_dependency("free", cost=1))
):
    """Get overall usage metrics."""
    try:
        logger.info(f"Fetching usage metrics: period={period}")

        # Get user ID from API key info
        user_id = api_key.get("tenant_id")

        # Build query parameters
        params = {"period": period}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        query_string = "&".join(f"{k}={v}" for k, v in params.items())

        # Call Core Backend
        result = await call_core_backend(
            endpoint=f"/api/analytics/usage?{query_string}",
            method="GET",
            user_id=user_id
        )

        return UsageMetrics(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching usage metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/services",
    response_model=List[ServiceUsage],
    summary="Get usage breakdown by service",
    description="""
    Get usage metrics broken down by service (TTS, ASR, LLM, VAPI, etc.).

    **Rate Limit:** 20 requests/minute
    **Cost:** Free

    **Example Response:**
    ```json
    [
        {
            "service": "tts",
            "request_count": 450,
            "total_cost": 45.00,
            "avg_cost": 0.10,
            "success_rate": 98.5
        },
        {
            "service": "asr",
            "request_count": 380,
            "total_cost": 38.00,
            "avg_cost": 0.10,
            "success_rate": 99.2
        }
    ]
    ```
    """,
    response_description="Usage breakdown by service"
)
async def get_service_usage(
    period: str = Query("30d", description="Time period (7d, 30d, 90d, all)"),
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(get_rate_limit_dependency("free", cost=1))
):
    """Get usage breakdown by service."""
    try:
        logger.info(f"Fetching service usage: period={period}")

        # Get user ID from API key info
        user_id = api_key.get("tenant_id")

        # Call Core Backend
        result = await call_core_backend(
            endpoint=f"/api/analytics/services?period={period}",
            method="GET",
            user_id=user_id
        )

        return [ServiceUsage(**item) for item in result.get("services", [])]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching service usage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/assistants/{assistant_id}",
    response_model=AssistantMetrics,
    summary="Get metrics for a specific assistant",
    description="""
    Get comprehensive analytics for a VAPI assistant including call metrics,
    costs, and success rates.

    **Rate Limit:** 20 requests/minute
    **Cost:** Free

    **Example Response:**
    ```json
    {
        "assistant_id": "ast_123abc",
        "assistant_name": "Customer Support Bot",
        "total_calls": 150,
        "successful_calls": 145,
        "failed_calls": 5,
        "avg_duration_seconds": 85.5,
        "total_duration_seconds": 12825.0,
        "success_rate": 96.7,
        "total_cost": 45.50,
        "cost_breakdown": {
            "vapi_calls": 30.00,
            "vonage_telephony": 12.50,
            "llm_processing": 2.00,
            "tts_generation": 1.00
        },
        "period_start": "2025-09-26T00:00:00",
        "period_end": "2025-10-26T23:59:59"
    }
    ```
    """,
    response_description="Assistant-specific metrics"
)
async def get_assistant_metrics(
    assistant_id: str = Path(..., description="VAPI assistant ID"),
    period: str = Query("30d", description="Time period (7d, 30d, 90d, all)"),
    start_date: Optional[str] = Query(None, description="Custom start date (ISO 8601)"),
    end_date: Optional[str] = Query(None, description="Custom end date (ISO 8601)"),
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(get_rate_limit_dependency("free", cost=1))
):
    """Get metrics for a specific assistant."""
    try:
        logger.info(f"Fetching assistant metrics: assistant_id={assistant_id}, period={period}")

        # Get user ID from API key info
        user_id = api_key.get("tenant_id")

        # Build query parameters
        params = {"period": period}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        query_string = "&".join(f"{k}={v}" for k, v in params.items())

        # Call Core Backend
        result = await call_core_backend(
            endpoint=f"/api/analytics/assistants/{assistant_id}?{query_string}",
            method="GET",
            user_id=user_id
        )

        return AssistantMetrics(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching assistant metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/calls",
    response_model=CallListResponse,
    summary="Get call history",
    description="""
    Get paginated call history with optional filtering.

    **Rate Limit:** 20 requests/minute
    **Cost:** Free

    **Query Parameters:**
    - `limit`: Number of calls to return (default: 50, max: 100)
    - `offset`: Offset for pagination (default: 0)
    - `assistant_id`: Filter by assistant ID
    - `status`: Filter by status (answered, ended, failed)
    - `start_date`: Filter calls after this date (ISO 8601)
    - `end_date`: Filter calls before this date (ISO 8601)

    **Example Response:**
    ```json
    {
        "calls": [
            {
                "call_id": "call_123",
                "assistant_id": "ast_abc",
                "status": "ended",
                "duration_seconds": 125.5,
                "cost": 0.50,
                "started_at": "2025-10-26T12:00:00",
                "ended_at": "2025-10-26T12:02:05",
                "transcript": "Full conversation transcript...",
                "metadata": {"customer_id": "cust_456"}
            }
        ],
        "pagination": {
            "limit": 50,
            "offset": 0,
            "total": 1250
        },
        "summary": {
            "total_calls": 1250,
            "total_cost": 625.00,
            "total_duration": 156250.0
        }
    }
    ```
    """,
    response_description="Paginated call history"
)
async def get_calls(
    limit: int = Query(50, ge=1, le=100, description="Number of calls to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    assistant_id: Optional[str] = Query(None, description="Filter by assistant ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    start_date: Optional[str] = Query(None, description="Start date (ISO 8601)"),
    end_date: Optional[str] = Query(None, description="End date (ISO 8601)"),
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(get_rate_limit_dependency("free", cost=1))
):
    """Get call history."""
    try:
        logger.info(f"Fetching calls: limit={limit}, offset={offset}")

        # Get user ID from API key info
        user_id = api_key.get("tenant_id")

        # Build query parameters
        params = {"limit": limit, "offset": offset}
        if assistant_id:
            params["assistant_id"] = assistant_id
        if status:
            params["status"] = status
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        query_string = "&".join(f"{k}={v}" for k, v in params.items())

        # Call Core Backend
        result = await call_core_backend(
            endpoint=f"/api/analytics/calls?{query_string}",
            method="GET",
            user_id=user_id
        )

        return CallListResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching calls: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/costs",
    response_model=CostBreakdown,
    summary="Get detailed cost breakdown",
    description="""
    Get detailed cost breakdown across all services and operations.

    **Rate Limit:** 20 requests/minute
    **Cost:** Free

    **Example Response:**
    ```json
    {
        "total_cost": 125.50,
        "currency": "USD",
        "services": {
            "tts": 45.00,
            "asr": 38.00,
            "llm": 25.50,
            "vapi": 15.00,
            "vonage": 2.00
        },
        "breakdown": [
            {
                "service": "tts",
                "provider": "coqui_xtts",
                "cost": 30.00,
                "request_count": 300
            },
            {
                "service": "tts",
                "provider": "melotts",
                "cost": 15.00,
                "request_count": 150
            }
        ],
        "period_start": "2025-09-26T00:00:00",
        "period_end": "2025-10-26T23:59:59"
    }
    ```
    """,
    response_description="Detailed cost breakdown"
)
async def get_cost_breakdown(
    period: str = Query("30d", description="Time period (7d, 30d, 90d, all)"),
    start_date: Optional[str] = Query(None, description="Custom start date (ISO 8601)"),
    end_date: Optional[str] = Query(None, description="Custom end date (ISO 8601)"),
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(get_rate_limit_dependency("free", cost=1))
):
    """Get detailed cost breakdown."""
    try:
        logger.info(f"Fetching cost breakdown: period={period}")

        # Get user ID from API key info
        user_id = api_key.get("tenant_id")

        # Build query parameters
        params = {"period": period}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        query_string = "&".join(f"{k}={v}" for k, v in params.items())

        # Call Core Backend
        result = await call_core_backend(
            endpoint=f"/api/analytics/costs?{query_string}",
            method="GET",
            user_id=user_id
        )

        return CostBreakdown(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching cost breakdown: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/health",
    summary="Health check for analytics service",
    description="""
    Health check for analytics service.

    **Rate Limit:** None
    **Cost:** Free
    """,
    response_description="Health status"
)
async def health_check():
    """Health check for analytics service."""
    try:
        # Call Core Backend health endpoint
        result = await call_core_backend(
            endpoint="/api/analytics/health",
            method="GET"
        )

        return result

    except HTTPException:
        return {
            "status": "unhealthy",
            "service": "analytics",
            "error": "Core Backend unavailable",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Analytics health check error: {e}")
        return {
            "status": "unhealthy",
            "service": "analytics",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


# Export router
__all__ = ["router"]
