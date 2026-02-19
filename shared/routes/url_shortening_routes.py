"""
Shared URL Shortening Routes.

FastAPI routes for URL shortening that can be included in any application.
Provides endpoints for creating, redirecting, and managing short URLs.

Usage in app:
    from apps.shared.routes.url_shortening_routes import create_url_shortening_router

    router = create_url_shortening_router(
        get_database_func=lambda: Database.get_database(),
        base_url="https://myapp.example.com",
        app_name="myapp"
    )
    app.include_router(router, prefix="/api/v1", tags=["Short URLs"])
    app.include_router(router, tags=["Short URLs"])  # For /s/{code} redirect
"""

import logging
from typing import Callable, Optional
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from datetime import datetime

from apps.shared.services.url_shortening_service import get_url_shortening_service

logger = logging.getLogger(__name__)


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class CreateShortUrlRequest(BaseModel):
    """Request to create a short URL."""

    target_url: str = Field(..., description="The full URL to shorten")
    custom_code: Optional[str] = Field(None, description="Optional custom short code")
    expires_at: Optional[datetime] = Field(None, description="Optional expiration datetime")


class ShortUrlResponse(BaseModel):
    """Response with short URL details."""

    short_code: str
    short_url: str
    target_url: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    clicks: int = 0


class ShortUrlStatsResponse(BaseModel):
    """Response with URL analytics."""

    short_code: str
    target_url: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    clicks: int
    recent_clicks: list
    app_name: Optional[str] = None


# ============================================================================
# ROUTER FACTORY
# ============================================================================

def create_url_shortening_router(
    get_database_func: Callable,
    base_url: str,
    app_name: str,
    require_auth: bool = False,
    get_current_user_func: Optional[Callable] = None
) -> APIRouter:
    """
    Create a URL shortening router for an application.

    Args:
        get_database_func: Function that returns the MongoDB database instance
        base_url: Base URL for the application (e.g., "https://inkwave.ailabsafrica.com")
        app_name: Application identifier (e.g., "inkwave", "churchflow")
        require_auth: Whether to require authentication for creating URLs (default: False)
        get_current_user_func: Optional function to get current user if auth required

    Returns:
        Configured APIRouter instance with URL shortening endpoints
    """
    router = APIRouter()

    # ========================================================================
    # CREATE SHORT URL
    # ========================================================================

    @router.post("/short-urls/create", response_model=ShortUrlResponse)
    async def create_short_url(request: CreateShortUrlRequest):
        """
        Create a short URL.

        This endpoint creates a shortened version of the provided URL.
        The short URL will be in format: {base_url}/s/{short_code}

        Args:
            request: URL shortening request

        Returns:
            Short URL details including the short code and full short URL
        """
        db = get_database_func()
        service = get_url_shortening_service(db)

        try:
            result = await service.create_short_url(
                target_url=request.target_url,
                custom_code=request.custom_code,
                expires_at=request.expires_at,
                app_name=app_name
            )

            # Build full short URL
            short_url = f"{base_url}/s/{result['short_code']}"

            return ShortUrlResponse(
                short_code=result["short_code"],
                short_url=short_url,
                target_url=result["target_url"],
                created_at=result["created_at"],
                expires_at=result.get("expires_at"),
                clicks=result.get("clicks", 0)
            )

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Failed to create short URL: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create short URL: {str(e)}"
            )

    # ========================================================================
    # REDIRECT SHORT URL
    # ========================================================================

    @router.get("/s/{short_code}")
    async def redirect_short_url(short_code: str):
        """
        Redirect from short URL to target URL.

        This endpoint handles the actual redirection. When a user visits
        /s/{short_code}, they are redirected to the original URL.

        Args:
            short_code: The short code to redirect

        Returns:
            302 redirect to the target URL
        """
        db = get_database_func()
        service = get_url_shortening_service(db)

        # Get target URL
        doc = await service.get_target_url(short_code)

        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Short URL not found or expired"
            )

        # Record the click
        await service.record_click(short_code)

        # Redirect to target URL
        return RedirectResponse(url=doc["target_url"], status_code=302)

    # ========================================================================
    # GET SHORT URL STATS
    # ========================================================================

    @router.get("/short-urls/{short_code}/stats", response_model=ShortUrlStatsResponse)
    async def get_short_url_stats(short_code: str):
        """
        Get analytics for a short URL.

        Returns click count, recent activity, and other metrics.

        Args:
            short_code: The short code to get stats for

        Returns:
            Analytics data for the short URL
        """
        db = get_database_func()
        service = get_url_shortening_service(db)

        stats = await service.get_stats(short_code)

        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Short URL not found"
            )

        return ShortUrlStatsResponse(**stats)

    # ========================================================================
    # DELETE SHORT URL
    # ========================================================================

    @router.delete("/short-urls/{short_code}")
    async def delete_short_url(short_code: str):
        """
        Delete a short URL.

        Args:
            short_code: The short code to delete

        Returns:
            Success message
        """
        db = get_database_func()
        service = get_url_shortening_service(db)

        deleted = await service.delete_short_url(short_code)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Short URL not found"
            )

        return {"message": "Short URL deleted successfully"}

    # ========================================================================
    # GET APP STATS
    # ========================================================================

    @router.get("/short-urls/stats/app")
    async def get_app_stats():
        """
        Get URL shortening statistics for this application.

        Returns aggregate metrics including total URLs, clicks, and top URLs.

        Returns:
            Application-level analytics
        """
        db = get_database_func()
        service = get_url_shortening_service(db)

        stats = await service.get_app_stats(app_name)

        return stats

    return router
