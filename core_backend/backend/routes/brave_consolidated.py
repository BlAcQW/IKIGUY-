"""
Brave Search Consolidated API Routes.

Provides comprehensive endpoints for web, news, and local search operations
with tenant-specific context and analytics tracking.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from ..services.brave_consolidated_service import get_brave_service
from ..auth import get_current_user_mongo

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../shared"))

from integration.brave import (
    BraveSearchOptions,
    BraveLocalSearchOptions,
    BraveSearchType,
    BraveFreshness,
    BraveSafeSearch
)

router = APIRouter(prefix="/brave", tags=["brave"])


class WebSearchRequest(BaseModel):
    """Request model for web search."""
    query: str = Field(..., description="Search query")
    count: Optional[int] = Field(default=10, description="Number of results", ge=1, le=20)
    offset: Optional[int] = Field(default=0, description="Pagination offset", ge=0, le=9)
    freshness: Optional[BraveFreshness] = Field(default=BraveFreshness.ALL, description="Result freshness")
    safe_search: Optional[BraveSafeSearch] = Field(default=BraveSafeSearch.MODERATE, description="Safe search level")
    search_lang: Optional[str] = Field(default="en", description="Search language")
    country: Optional[str] = Field(default="US", description="Country code")
    extra_snippets: Optional[bool] = Field(default=False, description="Include extra snippets")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")


class NewsSearchRequest(BaseModel):
    """Request model for news search."""
    query: str = Field(..., description="Search query")
    count: Optional[int] = Field(default=10, description="Number of results", ge=1, le=20)
    offset: Optional[int] = Field(default=0, description="Pagination offset", ge=0, le=9)
    freshness: Optional[BraveFreshness] = Field(default=BraveFreshness.PAST_WEEK, description="Result freshness")
    safe_search: Optional[BraveSafeSearch] = Field(default=BraveSafeSearch.MODERATE, description="Safe search level")
    search_lang: Optional[str] = Field(default="en", description="Search language")
    country: Optional[str] = Field(default="US", description="Country code")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")


class LocalSearchRequest(BaseModel):
    """Request model for local search."""
    query: str = Field(..., description="Local search query (e.g., 'pizza near me')")
    count: Optional[int] = Field(default=5, description="Number of results", ge=1, le=20)
    search_lang: Optional[str] = Field(default="en", description="Search language")
    country: Optional[str] = Field(default="US", description="Country code")
    units: Optional[str] = Field(default="metric", description="Units (metric or imperial)")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")


class BatchSearchRequest(BaseModel):
    """Request model for batch search."""
    queries: List[str] = Field(..., description="List of search queries")
    search_type: Optional[BraveSearchType] = Field(default=BraveSearchType.WEB, description="Type of search")
    count: Optional[int] = Field(default=10, description="Number of results per query", ge=1, le=20)
    safe_search: Optional[BraveSafeSearch] = Field(default=BraveSafeSearch.MODERATE, description="Safe search level")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")


class SmartSearchRequest(BaseModel):
    """Request model for smart search."""
    query: str = Field(..., description="Search query")
    search_intent: str = Field(default="general", description="Search intent (general, news, local, recent, research)")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")


class TrendingSearchRequest(BaseModel):
    """Request model for trending search."""
    query: str = Field(..., description="Search query")
    timeframe: str = Field(default="week", description="Timeframe (day, week, month, year)")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")


class MultiTypeSearchRequest(BaseModel):
    """Request model for multi-type search."""
    query: str = Field(..., description="Search query")
    include_news: bool = Field(default=True, description="Include news results")
    include_local: bool = Field(default=False, description="Include local results")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")


@router.get("/health")
async def health_check():
    """Check Brave Search service health."""
    try:
        service = await get_brave_service()
        capabilities = await service.get_capabilities()
        return {
            "status": "healthy",
            "service": "brave_search",
            "capabilities": capabilities,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Brave Search service unavailable: {str(e)}")


@router.post("/web-search")
async def web_search(
    request: WebSearchRequest,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Perform web search with specified options.

    Returns web search results with analytics tracking.
    """
    try:
        service = await get_brave_service()

        options = BraveSearchOptions(
            count=request.count,
            offset=request.offset,
            freshness=request.freshness,
            safe_search=request.safe_search,
            search_lang=request.search_lang,
            country=request.country,
            extra_snippets=request.extra_snippets
        )

        result = await service.web_search_for_tenant(
            tenant_id=current_user.id,
            query=request.query,
            options=options,
            context=request.context
        )

        return result.__dict__

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Web search failed: {str(e)}")


@router.post("/news-search")
async def news_search(
    request: NewsSearchRequest,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Perform news search with specified options.

    Returns news search results with analytics tracking.
    """
    try:
        service = await get_brave_service()

        options = BraveSearchOptions(
            count=request.count,
            offset=request.offset,
            freshness=request.freshness,
            safe_search=request.safe_search,
            search_lang=request.search_lang,
            country=request.country
        )

        result = await service.news_search_for_tenant(
            tenant_id=current_user.id,
            query=request.query,
            options=options,
            context=request.context
        )

        return result.__dict__

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"News search failed: {str(e)}")


@router.post("/local-search")
async def local_search(
    request: LocalSearchRequest,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Perform local search for businesses and places.

    Returns local search results with analytics tracking.
    """
    try:
        service = await get_brave_service()

        options = BraveLocalSearchOptions(
            count=request.count,
            search_lang=request.search_lang,
            country=request.country,
            units=request.units
        )

        result = await service.local_search_for_tenant(
            tenant_id=current_user.id,
            query=request.query,
            options=options,
            context=request.context
        )

        return result.__dict__

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Local search failed: {str(e)}")


@router.post("/batch-search")
async def batch_search(
    request: BatchSearchRequest,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Perform batch search for multiple queries.

    Returns batch search results with analytics tracking.
    """
    try:
        service = await get_brave_service()

        options = BraveSearchOptions(
            count=request.count,
            safe_search=request.safe_search
        )

        results = await service.batch_search_for_tenant(
            tenant_id=current_user.id,
            queries=request.queries,
            search_type=request.search_type,
            options=options,
            context=request.context
        )

        return [result.__dict__ for result in results]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch search failed: {str(e)}")


@router.post("/smart-search")
async def smart_search(
    request: SmartSearchRequest,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Smart search with optimized settings based on search intent.

    Automatically configures search options based on intent type.
    """
    try:
        service = await get_brave_service()

        result = await service.smart_search_for_tenant(
            tenant_id=current_user.id,
            query=request.query,
            search_intent=request.search_intent,
            context=request.context
        )

        return result.__dict__

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Smart search failed: {str(e)}")


@router.post("/trending-search")
async def trending_search(
    request: TrendingSearchRequest,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Search for trending content within a specific timeframe.

    Returns recent/trending search results based on timeframe.
    """
    try:
        service = await get_brave_service()

        result = await service.trending_search_for_tenant(
            tenant_id=current_user.id,
            query=request.query,
            timeframe=request.timeframe,
            context=request.context
        )

        return result.__dict__

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trending search failed: {str(e)}")


@router.post("/multi-type-search")
async def multi_type_search(
    request: MultiTypeSearchRequest,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Perform search across multiple content types (web, news, local).

    Returns comprehensive results organized by search type.
    """
    try:
        service = await get_brave_service()

        results = await service.multi_type_search_for_tenant(
            tenant_id=current_user.id,
            query=request.query,
            include_news=request.include_news,
            include_local=request.include_local,
            context=request.context
        )

        return {
            search_type: result.__dict__ for search_type, result in results.items()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Multi-type search failed: {str(e)}")


@router.get("/analytics/{tenant_id}")
async def get_analytics(
    tenant_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get Brave Search analytics for a specific tenant.

    Returns usage analytics and metrics for the specified time period.
    """
    try:
        service = await get_brave_service()

        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None

        analytics = await service.get_tenant_analytics(
            tenant_id=tenant_id,
            start_date=start_dt,
            end_date=end_dt
        )

        return analytics

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics retrieval failed: {str(e)}")


@router.get("/usage/{tenant_id}")
async def get_usage_summary(
    tenant_id: str,
    period_days: int = 30,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get usage summary for tenant including search statistics.

    Returns comprehensive usage metrics and search tracking.
    """
    try:
        service = await get_brave_service()

        usage = await service.get_tenant_usage_summary(
            tenant_id=tenant_id,
            period_days=period_days
        )

        return usage

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Usage summary retrieval failed: {str(e)}")


@router.get("/capabilities")
async def get_capabilities():
    """
    Get Brave Search service capabilities.

    Returns available features and configuration options.
    """
    try:
        service = await get_brave_service()
        capabilities = await service.get_capabilities()

        return {
            "service": "brave_search",
            "capabilities": capabilities,
            "supported_search_types": [t.value for t in BraveSearchType],
            "supported_freshness": [f.value for f in BraveFreshness],
            "supported_safe_search": [s.value for s in BraveSafeSearch],
            "features": {
                "web_search": True,
                "news_search": True,
                "local_search": True,
                "batch_search": True,
                "smart_search": True,
                "trending_search": True,
                "multi_type_search": True,
                "analytics_tracking": True,
                "tenant_isolation": True,
                "mcp_support": True
            },
            "limits": {
                "max_results_per_request": 20,
                "max_batch_queries": 10,
                "max_query_length": 400,
                "max_offset": 9
            },
            "search_intents": ["general", "news", "local", "recent", "research"],
            "timeframes": ["day", "week", "month", "year"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Capabilities retrieval failed: {str(e)}")


@router.get("/search-types")
async def get_search_types():
    """
    Get available search types and their descriptions.

    Returns comprehensive information about supported search operations.
    """
    return {
        "search_types": {
            "web": {
                "type": BraveSearchType.WEB.value,
                "description": "General web search across indexed pages",
                "endpoint": "/web-search",
                "features": ["pagination", "freshness_filtering", "safe_search", "extra_snippets"]
            },
            "news": {
                "type": BraveSearchType.NEWS.value,
                "description": "Search news articles and recent publications",
                "endpoint": "/news-search",
                "features": ["freshness_filtering", "safe_search", "language_filtering"]
            },
            "local": {
                "type": BraveSearchType.LOCAL.value,
                "description": "Search for local businesses and places",
                "endpoint": "/local-search",
                "features": ["location_based", "business_info", "ratings", "contact_details"]
            },
            "batch": {
                "type": "batch",
                "description": "Search multiple queries simultaneously",
                "endpoint": "/batch-search",
                "features": ["multiple_queries", "configurable_search_type", "bulk_processing"]
            },
            "smart": {
                "type": "smart",
                "description": "AI-optimized search based on intent",
                "endpoint": "/smart-search",
                "features": ["intent_detection", "auto_optimization", "adaptive_filtering"]
            },
            "trending": {
                "type": "trending",
                "description": "Search for trending content by timeframe",
                "endpoint": "/trending-search",
                "features": ["time_filtering", "trend_analysis", "recent_content"]
            },
            "multi_type": {
                "type": "multi_type",
                "description": "Combined search across multiple content types",
                "endpoint": "/multi-type-search",
                "features": ["comprehensive_results", "cross_type_search", "organized_output"]
            }
        },
        "usage_tips": {
            "web_search": "Best for general information and research",
            "news_search": "Use for current events and recent news",
            "local_search": "Include location context (e.g., 'pizza near me')",
            "batch_search": "Efficient for processing multiple related queries",
            "smart_search": "Let AI optimize settings based on your intent",
            "trending_search": "Find what's popular in your timeframe",
            "multi_type_search": "Get comprehensive view across content types"
        }
    }