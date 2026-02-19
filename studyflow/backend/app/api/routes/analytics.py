"""
API routes for admin analytics.
"""

from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime, timedelta

from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard")
async def get_dashboard_stats(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze")
):
    """
    Get comprehensive dashboard statistics.

    Returns overview metrics including users, sessions, questions, and materials.
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    end_date = datetime.utcnow()

    stats = await AnalyticsService.get_dashboard_stats(
        start_date=start_date,
        end_date=end_date
    )

    return stats


@router.get("/users")
async def get_user_metrics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze")
):
    """
    Get user engagement and retention metrics.

    Returns active users, engagement levels, and growth trends.
    """
    metrics = await AnalyticsService.get_user_metrics(days=days)
    return metrics


@router.get("/content")
async def get_content_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze")
):
    """
    Get content usage and performance analytics.

    Returns popular subjects, topics, and areas needing improvement.
    """
    analytics = await AnalyticsService.get_content_analytics(days=days)
    return analytics


@router.get("/system/health")
async def get_system_health():
    """
    Get system health and performance metrics.

    Returns database stats, recent activity, API performance, and error indicators.
    """
    health = await AnalyticsService.get_system_health()
    return health


@router.get("/financial")
async def get_financial_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze")
):
    """
    Get financial analytics.

    Returns wallet balances, transaction volumes, and revenue metrics.
    """
    analytics = await AnalyticsService.get_financial_analytics(days=days)
    return analytics


@router.get("/top-users")
async def get_top_users(
    metric: str = Query("questions", description="Metric to rank by (questions, sessions, learning_time)"),
    limit: int = Query(10, ge=1, le=100, description="Number of top users to return")
):
    """
    Get top users by various metrics.

    Returns leaderboard of users by questions, sessions, or learning time.
    """
    if metric not in ["questions", "sessions", "learning_time"]:
        return {
            "error": "Invalid metric. Must be one of: questions, sessions, learning_time"
        }

    top_users = await AnalyticsService.get_top_users(metric=metric, limit=limit)
    return {
        "metric": metric,
        "limit": limit,
        "users": top_users
    }
