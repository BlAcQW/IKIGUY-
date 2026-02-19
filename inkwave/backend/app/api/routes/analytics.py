"""
Analytics API routes for InkWave.

Provides endpoints for tracking book analytics, listening stats, and popular books.
"""

import logging
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from ...services.analytics_service import get_analytics_service, InkWaveAnalyticsService
from ...core.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])
logger = logging.getLogger(__name__)


class BookAnalyticsResponse(BaseModel):
    """Response model for book analytics."""
    book_id: str
    period: dict
    total_cost: float
    listening: dict
    ai_interactions: dict
    cost_distribution: dict


class UserListeningStatsResponse(BaseModel):
    """Response model for user listening stats."""
    user_id: str
    period: dict
    total_cost: float
    listening: dict
    ai_interactions: dict


class PopularBooksResponse(BaseModel):
    """Response model for popular books."""
    period: dict
    books: list
    count: int


@router.get(
    "/books/{book_id}",
    response_model=BookAnalyticsResponse,
    summary="Get book analytics",
    description="""
    Get comprehensive analytics for a book including:
    - Total listening time and cost
    - AI interaction metrics (Q&A, summaries, explanations)
    - Cost distribution
    """
)
async def get_book_analytics(
    book_id: str,
    start_date: Optional[str] = Query(None, description="Start date (ISO 8601 format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO 8601 format)"),
    current_user: dict = Depends(get_current_user),
    analytics_service: InkWaveAnalyticsService = Depends(get_analytics_service)
):
    """
    Get comprehensive analytics for a book.

    Args:
        book_id: Book ID
        start_date: Optional start date filter (ISO 8601)
        end_date: Optional end date filter (ISO 8601)

    Returns:
        Book analytics
    """
    try:
        # Parse dates if provided
        start_dt = None
        end_dt = None

        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))

        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

        # Get book analytics
        analytics = await analytics_service.get_book_analytics(
            book_id=book_id,
            start_date=start_dt,
            end_date=end_dt
        )

        # Check for errors
        if "error" in analytics:
            raise HTTPException(status_code=404, detail=analytics["error"])

        return analytics

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get book analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get book analytics: {str(e)}")


@router.get(
    "/listening-stats",
    response_model=UserListeningStatsResponse,
    summary="Get user listening stats",
    description="""
    Get listening statistics for the authenticated user including:
    - Total listening time
    - Number of unique books listened to
    - AI interaction count
    - Total costs
    """
)
async def get_listening_stats(
    start_date: Optional[str] = Query(None, description="Start date (ISO 8601 format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO 8601 format)"),
    current_user: dict = Depends(get_current_user),
    analytics_service: InkWaveAnalyticsService = Depends(get_analytics_service)
):
    """
    Get listening statistics for the user.

    Args:
        start_date: Optional start date filter (ISO 8601)
        end_date: Optional end date filter (ISO 8601)

    Returns:
        User listening stats
    """
    try:
        # Parse dates if provided
        start_dt = None
        end_dt = None

        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))

        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

        # Get user ID
        user_id = current_user.get("user_id") or current_user.get("sub")

        # Get listening stats
        stats = await analytics_service.get_user_listening_stats(
            user_id=user_id,
            start_date=start_dt,
            end_date=end_dt
        )

        # Check for errors
        if "error" in stats:
            raise HTTPException(status_code=500, detail=stats["error"])

        return stats

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get listening stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get listening stats: {str(e)}")


@router.get(
    "/popular-books",
    response_model=PopularBooksResponse,
    summary="Get popular books",
    description="""
    Get most popular books ranked by total listening time.

    Shows:
    - Total listening minutes
    - Number of unique listeners
    - Number of sessions
    - Average session duration
    """
)
async def get_popular_books(
    limit: int = Query(10, ge=1, le=50, description="Number of books to return (1-50)"),
    start_date: Optional[str] = Query(None, description="Start date (ISO 8601 format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO 8601 format)"),
    current_user: dict = Depends(get_current_user),
    analytics_service: InkWaveAnalyticsService = Depends(get_analytics_service)
):
    """
    Get most popular books by listening time.

    Args:
        limit: Number of books to return (1-50, default: 10)
        start_date: Optional start date filter (ISO 8601)
        end_date: Optional end date filter (ISO 8601)

    Returns:
        Popular books list
    """
    try:
        # Parse dates if provided
        start_dt = None
        end_dt = None

        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))

        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

        # Get popular books
        popular = await analytics_service.get_popular_books(
            limit=limit,
            start_date=start_dt,
            end_date=end_dt
        )

        # Check for errors
        if "error" in popular:
            raise HTTPException(status_code=500, detail=popular["error"])

        return popular

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get popular books: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get popular books: {str(e)}")


@router.get(
    "/health",
    summary="Analytics service health check",
    description="Check if analytics service is initialized and working"
)
async def analytics_health(
    analytics_service: InkWaveAnalyticsService = Depends(get_analytics_service)
):
    """
    Health check for analytics service.

    Returns:
        Service health status
    """
    return {
        "status": "healthy" if analytics_service.initialized else "not_initialized",
        "service": "inkwave_analytics"
    }
