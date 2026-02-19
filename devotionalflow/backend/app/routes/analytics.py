"""
Analytics API routes for DevotionalFlow.
Provides comprehensive analytics and insights.
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import Optional, Literal, List
import csv
import io
import logging

from app.services.analytics_service import (
    get_dashboard_stats,
    get_engagement_trends,
    get_top_devotionals,
    get_reader_insights,
    get_audience_growth,
)
from app.models.analytics import (
    DashboardStatsResponse,
    EngagementTrendsResponse,
    TopDevotionalResponse,
    ReaderInsightsResponse,
    AudienceGrowthResponse,
)
from app.utils.auth import get_current_admin, get_current_author, TokenData

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/dashboard", response_model=DashboardStatsResponse)
async def get_dashboard_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: TokenData = Depends(get_current_admin),
):
    """
    Get dashboard statistics.

    **Query Parameters:**
    - days: Number of days to analyze (default: 30, max: 365)

    **Returns:**
    - Dashboard statistics including total readers, devotionals published,
      engagement rate, views, likes, comments, shares, and trends

    **Auth Required:** Admin only
    """
    try:
        stats = await get_dashboard_stats(days=days)
        return stats
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard stats: {str(e)}",
        )


@router.get("/engagement/trends", response_model=EngagementTrendsResponse)
async def get_engagement_trends_endpoint(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    granularity: Literal["daily", "weekly", "monthly"] = Query(
        "daily", description="Time granularity"
    ),
    current_user: TokenData = Depends(get_current_admin),
):
    """
    Get engagement trends over time.

    **Query Parameters:**
    - days: Number of days to analyze (default: 30)
    - granularity: "daily", "weekly", or "monthly" (default: "daily")

    **Returns:**
    - Time series data for views, likes, comments, shares, bookmarks

    **Auth Required:** Admin only
    """
    try:
        trends = await get_engagement_trends(days=days, granularity=granularity)
        return trends
    except Exception as e:
        logger.error(f"Error getting engagement trends: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get engagement trends: {str(e)}",
        )


@router.get("/devotionals/top", response_model=List[TopDevotionalResponse])
async def get_top_devotionals_endpoint(
    limit: int = Query(10, ge=1, le=100, description="Number of devotionals to return"),
    metric: Literal["views", "likes", "comments", "shares", "engagement"] = Query(
        "views", description="Metric to sort by"
    ),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: TokenData = Depends(get_current_admin),
):
    """
    Get top-performing devotionals.

    **Query Parameters:**
    - limit: Number of devotionals to return (default: 10, max: 100)
    - metric: Sort by "views", "likes", "comments", "shares", or "engagement" (default: "views")
    - days: Number of days to look back (default: 30)

    **Returns:**
    - List of top devotionals with metrics

    **Auth Required:** Admin only
    """
    try:
        top_devotionals = await get_top_devotionals(
            limit=limit, metric=metric, days=days
        )
        return top_devotionals
    except Exception as e:
        logger.error(f"Error getting top devotionals: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get top devotionals: {str(e)}",
        )


@router.get("/readers/insights", response_model=ReaderInsightsResponse)
async def get_reader_insights_endpoint(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: TokenData = Depends(get_current_admin),
):
    """
    Get reader insights.

    **Query Parameters:**
    - days: Number of days to analyze (default: 30)

    **Returns:**
    - Reader insights including device breakdown, time of day,
      referral sources, geographic distribution, and returning readers

    **Auth Required:** Admin only
    """
    try:
        insights = await get_reader_insights(days=days)
        return insights
    except Exception as e:
        logger.error(f"Error getting reader insights: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get reader insights: {str(e)}",
        )


@router.get("/audience/growth", response_model=AudienceGrowthResponse)
async def get_audience_growth_endpoint(
    days: int = Query(90, ge=1, le=365, description="Number of days to analyze"),
    current_user: TokenData = Depends(get_current_admin),
):
    """
    Get audience growth and retention metrics.

    **Query Parameters:**
    - days: Number of days to analyze (default: 90)

    **Returns:**
    - Audience growth metrics including new readers, retention rate,
      churn rate, and retained readers

    **Auth Required:** Admin only
    """
    try:
        growth = await get_audience_growth(days=days)
        return growth
    except Exception as e:
        logger.error(f"Error getting audience growth: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get audience growth: {str(e)}",
        )


@router.get("/export/csv")
async def export_analytics_csv(
    days: int = Query(30, ge=1, le=365, description="Number of days to export"),
    current_user: TokenData = Depends(get_current_admin),
):
    """
    Export analytics data to CSV.

    **Query Parameters:**
    - days: Number of days to export (default: 30)

    **Returns:**
    - CSV file with analytics data

    **Auth Required:** Admin only
    """
    try:
        # Get all analytics data
        dashboard = await get_dashboard_stats(days=days)
        trends = await get_engagement_trends(days=days, granularity="daily")
        top_devotionals = await get_top_devotionals(limit=50, days=days)
        insights = await get_reader_insights(days=days)
        growth = await get_audience_growth(days=days)
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write dashboard stats
        writer.writerow(["Dashboard Statistics"])
        writer.writerow(["Metric", "Value", "Change (%)"])
        writer.writerow(["Total Readers", dashboard["total_readers"], f"{dashboard['readers_change']:.2f}"])
        writer.writerow(["Devotionals Published", dashboard["devotionals_published"], f"{dashboard['published_change']:.2f}"])
        writer.writerow(["Engagement Rate (%)", f"{dashboard['engagement_rate']:.2f}", ""])
        writer.writerow(["Total Views", dashboard["total_views"], f"{dashboard['views_change']:.2f}"])
        writer.writerow(["Total Likes", dashboard["total_likes"], f"{dashboard['likes_change']:.2f}"])
        writer.writerow(["Total Comments", dashboard["total_comments"], f"{dashboard['comments_change']:.2f}"])
        writer.writerow(["Total Shares", dashboard["total_shares"], f"{dashboard['shares_change']:.2f}"])
        writer.writerow(["Total Bookmarks", dashboard["total_bookmarks"], ""])
        writer.writerow(["Avg Read Time (min)", f"{dashboard['avg_read_time']:.2f}", ""])
        writer.writerow([])
        
        # Write engagement trends
        writer.writerow(["Engagement Trends"])
        writer.writerow(["Date", "Views", "Likes", "Comments", "Shares", "Bookmarks"])
        for trend in trends["trends"]:
            writer.writerow([
                trend["date"],
                trend["views"],
                trend["likes"],
                trend["comments"],
                trend["shares"],
                trend["bookmarks"],
            ])
        writer.writerow([])
        
        # Write top devotionals
        writer.writerow(["Top Devotionals"])
        writer.writerow(["Title", "Author", "Views", "Likes", "Comments", "Shares", "Engagement Rate (%)"])
        for dev in top_devotionals:
            writer.writerow([
                dev["title"],
                dev["author_name"],
                dev["views"],
                dev["likes"],
                dev["comments"],
                dev["shares"],
                f"{dev['engagement_rate']:.2f}",
            ])
        writer.writerow([])
        
        # Write reader insights
        writer.writerow(["Reader Insights"])
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Total Readers", insights["total_readers"]])
        writer.writerow(["Returning Readers", insights["returning_readers"]])
        writer.writerow(["Returning Rate (%)", f"{insights['returning_rate']:.2f}"])
        writer.writerow([])
        writer.writerow(["Device Breakdown"])
        writer.writerow(["Device", "Count"])
        for device, count in insights["device_breakdown"].items():
            writer.writerow([device, count])
        writer.writerow([])
        writer.writerow(["Time of Day"])
        writer.writerow(["Hour", "Reads"])
        for hour, count in insights["time_of_day"].items():
            writer.writerow([hour, count])
        writer.writerow([])
        writer.writerow(["Referral Sources"])
        writer.writerow(["Platform", "Shares"])
        for platform, count in insights["referral_sources"].items():
            writer.writerow([platform, count])
        writer.writerow([])
        
        # Write audience growth
        writer.writerow(["Audience Growth"])
        writer.writerow(["Metric", "Value"])
        writer.writerow(["New Readers", growth["new_readers"]])
        writer.writerow(["Total Readers", growth["total_readers"]])
        writer.writerow(["Retained Readers", growth["retained_readers"]])
        writer.writerow(["Retention Rate (%)", f"{growth['retention_rate']:.2f}"])
        writer.writerow(["Churned Readers", growth["churned_readers"]])
        writer.writerow(["Churn Rate (%)", f"{growth['churn_rate']:.2f}"])
        
        # Prepare response
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=analytics_export_{days}days.csv"
            }
        )
    except Exception as e:
        logger.error(f"Error exporting analytics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export analytics: {str(e)}",
        )

