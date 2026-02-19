"""
Cost Monitoring Dashboard API.

Provides real-time cost tracking and analytics for AI services usage.

Features:
- Per-interaction cost breakdown (ASR, LLM, TTS)
- Per-assessment costs
- Monthly budget tracking
- Cost projections
- Organization-wide analytics

Author: KasaAI
Created: 2025-11-07
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import logging

from app.core.auth import get_current_user_with_org, OrganizationRoleChecker
from app.models.user import UserRole
from app.core.database import MongoDB

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cost-dashboard", tags=["Cost Dashboard"])

# Require admin for organization-wide stats
require_admin = OrganizationRoleChecker([UserRole.ADMIN])


# ============================================================================
# Response Models
# ============================================================================

class CostBreakdown(BaseModel):
    """Cost breakdown by service."""
    asr_cost: float = 0.0
    llm_cost: float = 0.0
    tts_cost: float = 0.0
    total_cost: float = 0.0


class InteractionCosts(BaseModel):
    """Per-interaction average costs."""
    voice_question_avg: float
    assessment_question_avg: float
    total_interactions: int
    total_cost: float


class BudgetStatus(BaseModel):
    """Monthly budget status."""
    allocated: float
    spent: float
    remaining: float
    projected: float
    percentage_used: float
    on_track: bool


class CostTrend(BaseModel):
    """Cost trend data point."""
    date: str
    cost: float
    interactions: int


class DashboardData(BaseModel):
    """Complete dashboard data."""
    # Summary
    period_start: datetime
    period_end: datetime
    total_cost: float
    cost_breakdown: CostBreakdown

    # Per-interaction costs
    interaction_costs: InteractionCosts

    # Budget
    budget_status: BudgetStatus

    # Trends
    daily_trends: List[CostTrend]

    # Top users (admin only)
    top_users: Optional[List[Dict[str, Any]]] = None


# ============================================================================
# Helper Functions
# ============================================================================

async def calculate_cost_breakdown(
    organization_id: str,
    start_date: datetime,
    end_date: datetime,
    user_id: Optional[str] = None
) -> CostBreakdown:
    """
    Calculate cost breakdown for a period.

    Args:
        organization_id: Organization ID
        start_date: Period start
        end_date: Period end
        user_id: Optional user filter

    Returns:
        Cost breakdown
    """
    db = MongoDB.get_database()

    # Query questions collection for costs
    query = {
        "organization_id": organization_id,
        "created_at": {"$gte": start_date, "$lte": end_date}
    }

    if user_id:
        query["student_id"] = user_id

    # Aggregate costs from questions
    questions = db["questions"]

    pipeline = [
        {"$match": query},
        {
            "$group": {
                "_id": None,
                "total_llm_cost": {"$sum": "$cost"},
                "total_audio_cost": {"$sum": "$metadata.audio_cost"},
                "total_asr_cost": {"$sum": "$metadata.asr_cost"},
                "total_tts_cost": {"$sum": "$metadata.tts_cost"}
            }
        }
    ]

    result = await questions.aggregate(pipeline).to_list(1)

    if result:
        data = result[0]
        asr_cost = data.get("total_asr_cost", 0) or 0
        llm_cost = data.get("total_llm_cost", 0) or 0
        tts_cost = data.get("total_tts_cost", 0) or data.get("total_audio_cost", 0) or 0

        return CostBreakdown(
            asr_cost=asr_cost,
            llm_cost=llm_cost,
            tts_cost=tts_cost,
            total_cost=asr_cost + llm_cost + tts_cost
        )
    else:
        return CostBreakdown()


async def calculate_interaction_costs(
    organization_id: str,
    start_date: datetime,
    end_date: datetime
) -> InteractionCosts:
    """Calculate average costs per interaction type."""
    db = MongoDB.get_database()

    # Voice questions
    voice_query = {
        "organization_id": organization_id,
        "question_type": "voice",
        "created_at": {"$gte": start_date, "$lte": end_date}
    }

    voice_questions = await db["questions"].find(voice_query).to_list(None)
    voice_count = len(voice_questions)
    voice_total_cost = sum(
        (q.get("cost", 0) or 0) +
        (q.get("metadata", {}).get("total_cost", 0) or 0)
        for q in voice_questions
    )

    voice_avg = voice_total_cost / voice_count if voice_count > 0 else 0

    # Assessment questions
    assessment_query = {
        "organization_id": organization_id,
        "created_at": {"$gte": start_date, "$lte": end_date}
    }

    assessments = await db["assessment_sessions"].find(assessment_query).to_list(None)
    assessment_interactions = sum(len(a.get("responses", [])) for a in assessments)
    assessment_total_cost = sum(a.get("total_cost", 0) or 0 for a in assessments)

    assessment_avg = assessment_total_cost / assessment_interactions if assessment_interactions > 0 else 0

    return InteractionCosts(
        voice_question_avg=voice_avg,
        assessment_question_avg=assessment_avg,
        total_interactions=voice_count + assessment_interactions,
        total_cost=voice_total_cost + assessment_total_cost
    )


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/summary", response_model=DashboardData)
async def get_cost_summary(
    period_days: int = Query(30, ge=1, le=365),
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Get cost summary for current user or organization.

    Args:
        period_days: Number of days to analyze (default 30)
        user_context: User context with organization info

    Returns:
        Complete dashboard data
    """
    try:
        user_id = user_context["user_id"]
        organization_id = user_context["organization_id"]
        is_admin = user_context.get("role") in [UserRole.ADMIN, UserRole.STAFF]

        # Calculate period
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)

        # Calculate costs (user-specific for non-admins)
        cost_breakdown = await calculate_cost_breakdown(
            organization_id=organization_id,
            start_date=start_date,
            end_date=end_date,
            user_id=None if is_admin else user_id
        )

        # Interaction costs (org-wide for admins)
        interaction_costs = await calculate_interaction_costs(
            organization_id=organization_id,
            start_date=start_date,
            end_date=end_date
        )

        # Budget status (mock for now, can be configured per org)
        monthly_budget = 100.00  # $100/month default
        projected = (cost_breakdown.total_cost / period_days) * 30  # Project to 30 days

        budget_status = BudgetStatus(
            allocated=monthly_budget,
            spent=cost_breakdown.total_cost,
            remaining=monthly_budget - cost_breakdown.total_cost,
            projected=projected,
            percentage_used=(cost_breakdown.total_cost / monthly_budget) * 100 if monthly_budget > 0 else 0,
            on_track=projected <= monthly_budget
        )

        # Daily trends (simplified for now)
        daily_trends = []
        for i in range(min(period_days, 14)):  # Last 14 days
            day_start = end_date - timedelta(days=i+1)
            day_end = end_date - timedelta(days=i)

            day_costs = await calculate_cost_breakdown(
                organization_id=organization_id,
                start_date=day_start,
                end_date=day_end,
                user_id=None if is_admin else user_id
            )

            daily_trends.append(CostTrend(
                date=day_start.strftime("%Y-%m-%d"),
                cost=day_costs.total_cost,
                interactions=0  # TODO: Count interactions
            ))

        # Top users (admin only)
        top_users = None
        if is_admin:
            # TODO: Implement top users query
            top_users = []

        return DashboardData(
            period_start=start_date,
            period_end=end_date,
            total_cost=cost_breakdown.total_cost,
            cost_breakdown=cost_breakdown,
            interaction_costs=interaction_costs,
            budget_status=budget_status,
            daily_trends=list(reversed(daily_trends)),  # Oldest first
            top_users=top_users
        )

    except Exception as e:
        logger.error(f"Failed to get cost summary: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cost summary: {str(e)}"
        )


@router.get("/breakdown", response_model=CostBreakdown)
async def get_cost_breakdown_endpoint(
    days: int = Query(30, ge=1, le=365),
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Get detailed cost breakdown.

    Args:
        days: Number of days to analyze
        user_context: User context

    Returns:
        Cost breakdown by service
    """
    try:
        user_id = user_context["user_id"]
        organization_id = user_context["organization_id"]
        is_admin = user_context.get("role") in [UserRole.ADMIN, UserRole.STAFF]

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        breakdown = await calculate_cost_breakdown(
            organization_id=organization_id,
            start_date=start_date,
            end_date=end_date,
            user_id=None if is_admin else user_id
        )

        return breakdown

    except Exception as e:
        logger.error(f"Failed to get cost breakdown: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cost breakdown: {str(e)}"
        )


@router.post("/budget/set")
async def set_monthly_budget(
    budget: float,
    user_context: dict = Depends(require_admin)
):
    """
    Set monthly budget for organization (admin only).

    Args:
        budget: Monthly budget amount in USD
        user_context: Admin user context

    Returns:
        Success message
    """
    try:
        organization_id = user_context["organization_id"]

        # TODO: Store in organization settings
        # For now, this is a placeholder

        logger.info(f"Budget set for org {organization_id}: ${budget:.2f}/month")

        return {
            "message": "Budget updated successfully",
            "organization_id": organization_id,
            "monthly_budget": budget
        }

    except Exception as e:
        logger.error(f"Failed to set budget: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set budget: {str(e)}"
        )


@router.get("/alerts")
async def get_cost_alerts(
    user_context: dict = Depends(require_admin)
):
    """
    Get cost alerts for organization (admin only).

    Returns:
        List of active alerts
    """
    try:
        organization_id = user_context["organization_id"]

        # Calculate current month costs
        start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = datetime.utcnow()

        breakdown = await calculate_cost_breakdown(
            organization_id=organization_id,
            start_date=start_of_month,
            end_date=end_date
        )

        # Check for alerts
        monthly_budget = 100.00  # Default, should be from org settings
        percentage_used = (breakdown.total_cost / monthly_budget) * 100 if monthly_budget > 0 else 0

        alerts = []

        if percentage_used >= 80:
            alerts.append({
                "type": "budget_warning",
                "severity": "high" if percentage_used >= 90 else "medium",
                "message": f"Budget usage at {percentage_used:.0f}% (${breakdown.total_cost:.2f} / ${monthly_budget:.2f})",
                "timestamp": datetime.utcnow().isoformat()
            })

        # Check for unusual spikes
        # TODO: Implement spike detection

        return {
            "alerts": alerts,
            "total_alerts": len(alerts)
        }

    except Exception as e:
        logger.error(f"Failed to get alerts: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get alerts: {str(e)}"
        )
