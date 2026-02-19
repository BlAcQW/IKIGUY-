"""
API routes for usage tracking and analytics.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Security
from typing import Optional
from datetime import datetime, timedelta

import sys
sys.path.insert(0, "/opt/kasaai/apps")

from shared.integration.usage_calculator import PricingTier, ServiceType

from app.core.auth import get_current_user, require_admin
from app.models.user import User, UserRole
from app.services.usage_service import UsageService

router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("/me")
async def get_my_usage(
    days: int = Query(30, ge=1, le=365, description="Number of days to fetch"),
    service_type: Optional[str] = Query(None, description="Filter by service type"),
    current_user: dict = Security(get_current_user)
):
    """
    Get current user's usage metrics.

    Returns usage metrics for the specified time period.
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    end_date = datetime.utcnow()

    # Parse service type
    service_filter = None
    if service_type:
        try:
            service_filter = ServiceType(service_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid service type: {service_type}"
            )

    # Get usage metrics
    user_id = current_user.get("sub")
    metrics = await UsageService.get_user_usage(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        service_type=service_filter
    )

    return {
        "user_id": user_id,
        "metrics": [m.dict() for m in metrics],
        "count": len(metrics),
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat()
    }


@router.get("/summary")
async def get_usage_summary(
    days: int = Query(30, ge=1, le=365, description="Number of days to summarize"),
    current_user: dict = Security(get_current_user)
):
    """
    Get usage summary for current user.

    Returns aggregated usage statistics including costs, queries, and breakdowns.
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    end_date = datetime.utcnow()
    user_id = current_user.get("sub")

    summary = await UsageService.get_usage_summary(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date
    )

    return summary


@router.get("/student/{student_id}/summary")
async def get_student_usage_summary(
    student_id: str,
    days: int = Query(30, ge=1, le=365, description="Number of days to summarize"),
    current_user: dict = Security(get_current_user)
):
    """
    Get usage summary for a specific student.

    Parents can view their children's usage.
    Admins can view any student's usage.
    """
    # Check authorization
    user_role = current_user.get("user_metadata", {}).get("role")
    user_id = current_user.get("sub")

    if user_role == UserRole.PARENT.value:
        # Verify student is linked to parent
        from app.services.user_service import UserService
        student = await UserService.get_user_by_supabase_id(student_id)

        if not student or student.parent_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="You can only view usage for your own children"
            )
    elif user_role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=403,
            detail="Only parents and admins can view student usage"
        )

    start_date = datetime.utcnow() - timedelta(days=days)
    end_date = datetime.utcnow()

    summary = await UsageService.get_usage_summary(
        user_id=student_id,
        start_date=start_date,
        end_date=end_date
    )

    return summary


@router.get("/tier")
async def get_my_tier(
    current_user: dict = Security(get_current_user)
):
    """
    Get current user's pricing tier.
    """
    user_id = current_user.get("sub")
    tier = await UsageService.get_user_tier(user_id)

    return {
        "user_id": user_id,
        "tier": tier.value
    }


@router.post("/estimate")
async def estimate_cost(
    input_tokens: int = Query(..., ge=0, description="Number of input tokens"),
    output_tokens: int = Query(..., ge=0, description="Number of output tokens"),
    num_queries: int = Query(1, ge=1, description="Number of queries"),
    current_user: dict = Security(get_current_user)
):
    """
    Get cost estimate for RAG queries.

    Useful for showing users estimated costs before queries.
    """
    # Get user's tier
    user_id = current_user.get("sub")
    tier = await UsageService.get_user_tier(user_id)

    # Get estimate
    estimate = await UsageService.get_cost_estimate(
        tier=tier,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        num_queries=num_queries
    )

    return estimate


# Admin endpoints


@router.post("/admin/tier/{user_id}")
async def set_user_tier(
    user_id: str,
    tier: str = Query(..., description="Pricing tier (free, basic, premium, enterprise)"),
    current_user: dict = Security(require_admin)
):
    """
    Set pricing tier for a user (Admin only).
    """
    try:
        pricing_tier = PricingTier(tier)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid tier: {tier}. Must be one of: free, basic, premium, enterprise"
        )

    success = await UsageService.set_user_tier(user_id, pricing_tier)

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to set user tier"
        )

    return {
        "user_id": user_id,
        "tier": pricing_tier.value,
        "success": True
    }


@router.get("/admin/analytics")
async def get_admin_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: dict = Security(require_admin)
):
    """
    Get system-wide usage analytics (Admin only).

    Returns aggregated statistics for all users.
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    end_date = datetime.utcnow()

    analytics = await UsageService.get_admin_analytics(
        start_date=start_date,
        end_date=end_date
    )

    return analytics


@router.get("/admin/user/{user_id}")
async def get_user_usage_admin(
    user_id: str,
    days: int = Query(30, ge=1, le=365, description="Number of days to fetch"),
    current_user: dict = Security(require_admin)
):
    """
    Get usage for any user (Admin only).
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    end_date = datetime.utcnow()

    summary = await UsageService.get_usage_summary(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date
    )

    return summary


@router.get("/tiers")
async def list_pricing_tiers():
    """
    List all available pricing tiers with their configurations.

    Public endpoint - no authentication required.
    """
    from shared.integration.usage_calculator import UsageCalculator

    tiers = {}
    for tier in PricingTier:
        config = UsageCalculator.PRICING_CONFIGS[tier]
        tiers[tier.value] = {
            "tier": tier.value,
            "currency": config.currency.value,
            "rag_pricing": {
                "input_token_cost_per_1k": float(config.rag_input_token_cost),
                "output_token_cost_per_1k": float(config.rag_output_token_cost),
                "query_base_cost": float(config.rag_query_base_cost)
            },
            "document_processing": {
                "cost_per_page": float(config.doc_processing_cost_per_page),
                "cost_per_mb": float(config.doc_processing_cost_per_mb)
            }
        }

    return {
        "tiers": tiers,
        "default_tier": PricingTier.BASIC.value
    }
