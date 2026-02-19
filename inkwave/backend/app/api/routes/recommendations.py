"""
Recommendation API routes for Church Content.

Endpoints for personalized sermon and teaching recommendations:
- GET /recommendations - Get personalized recommendations
- GET /recommendations/category/{category} - Get sermons by spiritual topic
- GET /recommendations/latest - Get latest sermons
- GET /recommendations/similar/{book_id} - Get similar sermons
- GET /recommendations/series - Get popular sermon series
- GET /recommendations/featured - Get featured sermon for homepage
"""

from fastapi import APIRouter, HTTPException, Query, Depends, Header
from typing import List, Dict, Any, Optional

from app.services.recommendation_service import recommendation_service, CHURCH_CATEGORIES
from apps.shared.dependencies.auth import get_current_user

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("")
async def get_recommendations(
    limit: int = Query(10, ge=1, le=50, description="Number of recommendations"),
    exclude_completed: bool = Query(True, description="Exclude completed sermons"),
    authorization: Optional[str] = Header(None)
):
    """
    Get personalized sermon recommendations.

    For Archbishop Duncan-Williams' church members, recommendations are based on:
    - Listening history (if authenticated)
    - Preferred spiritual topics (Prayer, Faith, Deliverance, etc.)
    - Latest messages
    - Popular series

    If user is not authenticated, returns latest sermons.
    """
    try:
        user = None
        # Try to get user if authenticated
        if authorization:
            try:
                user = await get_current_user(authorization)
            except:
                pass  # Not authenticated, continue without user

        if user:
            user_id = user.user_id if hasattr(user, 'user_id') else user.get("user_id")
            recommendations = await recommendation_service.get_recommendations(
                user_id=user_id,
                limit=limit,
                exclude_completed=exclude_completed
            )
        else:
            # Not authenticated, return latest sermons
            recommendations = await recommendation_service.get_latest_sermons(limit)

        return {
            "recommendations": recommendations,
            "total": len(recommendations),
            "personalized": user is not None
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch recommendations: {str(e)}"
        )


@router.get("/categories")
async def get_categories():
    """
    Get available spiritual content categories.

    Returns categories for filtering sermons:
    - Prayer & Intercession
    - Faith & Breakthrough
    - Deliverance & Spiritual Warfare
    - Prosperity & Abundance
    - Healing & Restoration
    - Leadership & Ministry
    - Marriage & Family
    - Youth & Young Adults
    - Praise & Worship
    - Prophetic Messages
    """
    return {
        "categories": [
            {"key": key, "name": name}
            for key, name in CHURCH_CATEGORIES.items()
        ]
    }


@router.get("/category/{category}")
async def get_by_category(
    category: str,
    limit: int = Query(10, ge=1, le=50, description="Number of sermons")
):
    """
    Get sermons by spiritual category.

    Categories:
    - prayer: Prayer & Intercession
    - faith: Faith & Breakthrough
    - deliverance: Deliverance & Spiritual Warfare
    - prosperity: Prosperity & Abundance
    - healing: Healing & Restoration
    - leadership: Leadership & Ministry
    - family: Marriage & Family
    - youth: Youth & Young Adults
    - praise: Praise & Worship
    - prophecy: Prophetic Messages
    """
    try:
        if category not in CHURCH_CATEGORIES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category. Available: {', '.join(CHURCH_CATEGORIES.keys())}"
            )

        sermons = await recommendation_service.get_by_category(
            category=category,
            limit=limit
        )

        return {
            "sermons": sermons,
            "category": CHURCH_CATEGORIES[category],
            "total": len(sermons)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch sermons by category: {str(e)}"
        )


@router.get("/latest")
async def get_latest_sermons(
    limit: int = Query(10, ge=1, le=50, description="Number of sermons")
):
    """
    Get latest sermons from Archbishop Duncan-Williams.

    Returns the most recently added messages, ordered by date.
    """
    try:
        sermons = await recommendation_service.get_latest_sermons(limit)

        return {
            "sermons": sermons,
            "total": len(sermons)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch latest sermons: {str(e)}"
        )


@router.get("/series")
async def get_popular_series(
    limit: int = Query(5, ge=1, le=20, description="Number of series")
):
    """
    Get popular sermon series.

    Returns the most listened-to sermon series from Archbishop Duncan-Williams.
    """
    try:
        series = await recommendation_service.get_popular_series(limit)

        return {
            "series": series,
            "total": len(series)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch popular series: {str(e)}"
        )


@router.get("/series/detailed")
async def get_series_detailed(
    limit: int = Query(10, ge=1, le=50, description="Number of series")
):
    """
    Get sermon series with full metadata.

    Returns detailed information about sermon series including:
    - Series name
    - Number of sermons in series
    - Representative sermon
    - Topics covered

    Useful for browsing content by series.
    """
    try:
        series_list = await recommendation_service.get_series_with_metadata(limit)

        return {
            "series": series_list,
            "total": len(series_list)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch detailed series: {str(e)}"
        )


@router.get("/similar/{book_id}")
async def get_similar_sermons(
    book_id: str,
    limit: int = Query(5, ge=1, le=20, description="Number of similar sermons")
):
    """
    Get sermons similar to a specific message.

    Similarity is based on:
    - Spiritual topic overlap
    - Themes
    - Series
    """
    try:
        similar = await recommendation_service.get_similar_sermons(
            book_id=book_id,
            limit=limit
        )

        return {
            "similar_sermons": similar,
            "total": len(similar)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch similar sermons: {str(e)}"
        )


@router.get("/featured")
async def get_featured():
    """
    Get featured sermon for homepage hero banner.

    Returns the most recent or specially featured message
    from Archbishop Duncan-Williams.
    """
    try:
        featured = await recommendation_service.get_featured_content()

        if not featured:
            raise HTTPException(
                status_code=404,
                detail="No featured content available"
            )

        return {"featured": featured}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch featured content: {str(e)}"
        )


@router.get("/for-you")
async def get_for_you(
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get comprehensive "For You" page with multiple recommendation sections.

    Returns:
    - Continue Listening (in-progress sermons)
    - Recommended for You (personalized)
    - Latest Messages
    - Similar to what you've listened to
    """
    try:
        user_id = user.get("id") or user.get("user_id")

        # Get personalized recommendations
        personalized = await recommendation_service.get_recommendations(
            user_id=user_id,
            limit=10,
            exclude_completed=True
        )

        # Get latest sermons
        latest = await recommendation_service.get_latest_sermons(limit=10)

        # Get similar sermons based on listening history
        history = await recommendation_service._get_user_listening_history(user_id)
        similar_sermons = []
        if history:
            # Get similar to the most recent sermon
            recent_book_id = history[0].get("book_id")
            if recent_book_id:
                similar_sermons = await recommendation_service.get_similar_sermons(
                    book_id=recent_book_id,
                    limit=5
                )

        return {
            "personalized": personalized,
            "latest": latest,
            "similar_to_recent": similar_sermons,
            "generated_at": "now"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate For You page: {str(e)}"
        )
