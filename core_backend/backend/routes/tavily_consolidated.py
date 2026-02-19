"""
Tavily Consolidated Routes - FastAPI endpoints for AI-powered search operations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ..auth import get_current_user_mongo
from ..services.tavily_consolidated_service import get_tavily_service

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../shared"))

from integration.tavily import (
    TavilySearchRequest,
    TavilySearchTopic,
    TavilySearchDepth,
    TavilyResponse,
)


router = APIRouter(prefix="/tavily", tags=["tavily", "search", "ai"])


# Request/Response Models
class TavilySearchRequestModel(BaseModel):
    """Request model for Tavily search."""
    tenant_id: str = Field(..., description="Tenant identifier")
    query: str = Field(..., description="Search query")
    topic: TavilySearchTopic = Field(TavilySearchTopic.GENERAL, description="Search topic")
    search_depth: TavilySearchDepth = Field(TavilySearchDepth.BASIC, description="Search depth")
    include_answer: bool = Field(False, description="Generate AI answer")
    include_raw_content: bool = Field(False, description="Extract full content")
    include_images: bool = Field(False, description="Include relevant images")
    include_domains: Optional[List[str]] = Field(None, description="Domains to include")
    exclude_domains: Optional[List[str]] = Field(None, description="Domains to exclude")
    max_results: int = Field(5, description="Maximum results to return", ge=1, le=20)
    include_favicon: bool = Field(False, description="Include website favicons")
    auto_parameters: bool = Field(True, description="Auto-configure parameters")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for tracking")


class TavilyQuickSearchRequest(BaseModel):
    """Request model for quick search."""
    tenant_id: str = Field(..., description="Tenant identifier")
    query: str = Field(..., description="Search query")
    max_results: int = Field(5, description="Maximum results to return", ge=1, le=10)
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for tracking")


class TavilyNewsSearchRequest(BaseModel):
    """Request model for news search."""
    tenant_id: str = Field(..., description="Tenant identifier")
    query: str = Field(..., description="News search query")
    max_results: int = Field(5, description="Maximum results to return", ge=1, le=15)
    include_answer: bool = Field(True, description="Generate AI summary")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for tracking")


class TavilyFinancialSearchRequest(BaseModel):
    """Request model for financial search."""
    tenant_id: str = Field(..., description="Tenant identifier")
    query: str = Field(..., description="Financial search query")
    max_results: int = Field(5, description="Maximum results to return", ge=1, le=15)
    include_answer: bool = Field(True, description="Generate AI summary")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for tracking")


class TavilyAdvancedSearchRequest(BaseModel):
    """Request model for advanced search."""
    tenant_id: str = Field(..., description="Tenant identifier")
    query: str = Field(..., description="Search query")
    topic: TavilySearchTopic = Field(TavilySearchTopic.GENERAL, description="Search topic")
    include_domains: Optional[List[str]] = Field(None, description="Domains to include")
    exclude_domains: Optional[List[str]] = Field(None, description="Domains to exclude")
    max_results: int = Field(10, description="Maximum results to return", ge=1, le=20)
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for tracking")


# Basic Search Routes
@router.post("/search", response_model=Dict[str, Any])
async def search(
    search_request: TavilySearchRequestModel,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Perform AI-powered web search with Tavily.

    Args:
        search_request (TavilySearchRequestModel): Search parameters
        current_user (Dict[str, Any]): Current authenticated user

    Returns:
        Dict[str, Any]: Search results with AI insights
    """
    try:
        tavily_service = await get_tavily_service()

        # Create Tavily search request
        request = TavilySearchRequest(
            query=search_request.query,
            topic=search_request.topic,
            search_depth=search_request.search_depth,
            include_answer=search_request.include_answer,
            include_raw_content=search_request.include_raw_content,
            include_images=search_request.include_images,
            include_domains=search_request.include_domains,
            exclude_domains=search_request.exclude_domains,
            max_results=search_request.max_results,
            include_favicon=search_request.include_favicon,
            auto_parameters=search_request.auto_parameters
        )

        # Perform search with tenant context
        result = await tavily_service.search_for_tenant(
            tenant_id=search_request.tenant_id,
            request=request,
            context=search_request.context
        )

        # Format response
        response_data = {
            "success": result.success,
            "query": result.query,
            "answer": result.answer,
            "results": [
                {
                    "title": r.title,
                    "url": r.url,
                    "content": r.content,
                    "score": r.score,
                    "published_date": r.published_date,
                    "favicon": r.favicon,
                    "raw_content": r.raw_content
                } for r in result.results
            ],
            "images": [
                {
                    "url": img.url,
                    "title": img.title,
                    "alt_text": img.alt_text
                } for img in result.images
            ],
            "search_depth": result.search_depth,
            "search_time": result.search_time,
            "response_time": result.response_time,
            "credits_used": 2 if search_request.search_depth == TavilySearchDepth.ADVANCED else 1
        }

        if not result.success:
            response_data["error"] = result.error

        return response_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/search/quick", response_model=Dict[str, Any])
async def quick_search(
    search_request: TavilyQuickSearchRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Perform quick search with basic results.

    Args:
        search_request (TavilyQuickSearchRequest): Quick search parameters
        current_user (Dict[str, Any]): Current authenticated user

    Returns:
        Dict[str, Any]: Quick search results
    """
    try:
        tavily_service = await get_tavily_service()

        # Create basic search request
        request = TavilySearchRequest(
            query=search_request.query,
            search_depth=TavilySearchDepth.BASIC,
            include_answer=False,
            max_results=search_request.max_results,
            auto_parameters=True
        )

        result = await tavily_service.search_for_tenant(
            tenant_id=search_request.tenant_id,
            request=request,
            context=search_request.context
        )

        return {
            "success": result.success,
            "query": result.query,
            "results": [
                {
                    "title": r.title,
                    "url": r.url,
                    "content": r.content,
                    "score": r.score
                } for r in result.results
            ],
            "search_time": result.search_time,
            "credits_used": 1
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quick search failed: {str(e)}")


@router.post("/search/answer", response_model=Dict[str, Any])
async def quick_answer(
    question: str,
    tenant_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Get a quick AI-generated answer to a question.

    Args:
        question (str): Question to answer
        tenant_id (str): Tenant identifier
        current_user (Dict[str, Any]): Current authenticated user

    Returns:
        Dict[str, Any]: AI answer with supporting results
    """
    try:
        tavily_service = await get_tavily_service()

        result = await tavily_service.quick_answer_for_tenant(
            tenant_id=tenant_id,
            question=question
        )

        return {
            "success": result.success,
            "question": question,
            "answer": result.answer,
            "sources": [
                {
                    "title": r.title,
                    "url": r.url,
                    "content": r.content[:200] + "..." if len(r.content) > 200 else r.content,
                    "score": r.score
                } for r in result.results
            ],
            "search_time": result.search_time,
            "credits_used": 2
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Answer generation failed: {str(e)}")


# Specialized Search Routes
@router.post("/search/news", response_model=Dict[str, Any])
async def search_news(
    news_request: TavilyNewsSearchRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Search for news articles with AI summary.

    Args:
        news_request (TavilyNewsSearchRequest): News search parameters
        current_user (Dict[str, Any]): Current authenticated user

    Returns:
        Dict[str, Any]: News search results with AI summary
    """
    try:
        tavily_service = await get_tavily_service()

        result = await tavily_service.search_news_for_tenant(
            tenant_id=news_request.tenant_id,
            query=news_request.query,
            max_results=news_request.max_results,
            include_answer=news_request.include_answer,
            context=news_request.context
        )

        return {
            "success": result.success,
            "query": result.query,
            "summary": result.answer,
            "news_articles": [
                {
                    "title": r.title,
                    "url": r.url,
                    "content": r.content,
                    "score": r.score,
                    "published_date": r.published_date
                } for r in result.results
            ],
            "search_time": result.search_time,
            "credits_used": 2
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"News search failed: {str(e)}")


@router.post("/search/financial", response_model=Dict[str, Any])
async def search_financial(
    financial_request: TavilyFinancialSearchRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Search for financial information with AI analysis.

    Args:
        financial_request (TavilyFinancialSearchRequest): Financial search parameters
        current_user (Dict[str, Any]): Current authenticated user

    Returns:
        Dict[str, Any]: Financial search results with AI analysis
    """
    try:
        tavily_service = await get_tavily_service()

        result = await tavily_service.search_financial_for_tenant(
            tenant_id=financial_request.tenant_id,
            query=financial_request.query,
            max_results=financial_request.max_results,
            include_answer=financial_request.include_answer,
            context=financial_request.context
        )

        return {
            "success": result.success,
            "query": result.query,
            "analysis": result.answer,
            "financial_data": [
                {
                    "title": r.title,
                    "url": r.url,
                    "content": r.content,
                    "score": r.score,
                    "published_date": r.published_date
                } for r in result.results
            ],
            "search_time": result.search_time,
            "credits_used": 2
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Financial search failed: {str(e)}")


@router.post("/search/advanced", response_model=Dict[str, Any])
async def advanced_search(
    advanced_request: TavilyAdvancedSearchRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Perform advanced search with domain filtering.

    Args:
        advanced_request (TavilyAdvancedSearchRequest): Advanced search parameters
        current_user (Dict[str, Any]): Current authenticated user

    Returns:
        Dict[str, Any]: Advanced search results with all features
    """
    try:
        tavily_service = await get_tavily_service()

        result = await tavily_service.advanced_search_for_tenant(
            tenant_id=advanced_request.tenant_id,
            query=advanced_request.query,
            topic=advanced_request.topic,
            include_domains=advanced_request.include_domains,
            exclude_domains=advanced_request.exclude_domains,
            max_results=advanced_request.max_results,
            context=advanced_request.context
        )

        return {
            "success": result.success,
            "query": result.query,
            "answer": result.answer,
            "results": [
                {
                    "title": r.title,
                    "url": r.url,
                    "content": r.content,
                    "raw_content": r.raw_content,
                    "score": r.score,
                    "published_date": r.published_date,
                    "favicon": r.favicon
                } for r in result.results
            ],
            "images": [
                {
                    "url": img.url,
                    "title": img.title,
                    "alt_text": img.alt_text
                } for img in result.images
            ],
            "search_depth": "advanced",
            "search_time": result.search_time,
            "credits_used": 2,
            "domain_filters": {
                "included": advanced_request.include_domains,
                "excluded": advanced_request.exclude_domains
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Advanced search failed: {str(e)}")


# Content Extraction Routes
@router.post("/search/content", response_model=Dict[str, Any])
async def search_with_content(
    query: str,
    tenant_id: str,
    max_results: int = 3,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Search with full content extraction.

    Args:
        query (str): Search query
        tenant_id (str): Tenant identifier
        max_results (int): Maximum results to return
        current_user (Dict[str, Any]): Current authenticated user

    Returns:
        Dict[str, Any]: Search results with full extracted content
    """
    try:
        tavily_service = await get_tavily_service()

        result = await tavily_service.search_with_content_for_tenant(
            tenant_id=tenant_id,
            query=query,
            max_results=max_results
        )

        return {
            "success": result.success,
            "query": result.query,
            "answer": result.answer,
            "results": [
                {
                    "title": r.title,
                    "url": r.url,
                    "content": r.content,
                    "raw_content": r.raw_content,
                    "score": r.score,
                    "favicon": r.favicon
                } for r in result.results
            ],
            "search_time": result.search_time,
            "credits_used": 2
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content search failed: {str(e)}")


@router.post("/search/images", response_model=Dict[str, Any])
async def search_with_images(
    query: str,
    tenant_id: str,
    max_results: int = 5,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Search including relevant images.

    Args:
        query (str): Search query
        tenant_id (str): Tenant identifier
        max_results (int): Maximum results to return
        current_user (Dict[str, Any]): Current authenticated user

    Returns:
        Dict[str, Any]: Search results with images
    """
    try:
        tavily_service = await get_tavily_service()

        result = await tavily_service.search_with_images_for_tenant(
            tenant_id=tenant_id,
            query=query,
            max_results=max_results
        )

        return {
            "success": result.success,
            "query": result.query,
            "answer": result.answer,
            "results": [
                {
                    "title": r.title,
                    "url": r.url,
                    "content": r.content,
                    "score": r.score,
                    "favicon": r.favicon
                } for r in result.results
            ],
            "images": [
                {
                    "url": img.url,
                    "title": img.title,
                    "alt_text": img.alt_text
                } for img in result.images
            ],
            "search_time": result.search_time,
            "credits_used": 1
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image search failed: {str(e)}")


# Analytics Routes
@router.get("/analytics", response_model=Dict[str, Any])
async def get_analytics(
    tenant_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Get Tavily analytics for a tenant.

    Args:
        tenant_id (str): Tenant identifier
        start_date (Optional[datetime]): Start date for analytics
        end_date (Optional[datetime]): End date for analytics
        current_user (Dict[str, Any]): Current authenticated user

    Returns:
        Dict[str, Any]: Analytics data for the tenant
    """
    try:
        tavily_service = await get_tavily_service()

        analytics_data = await tavily_service.get_tenant_analytics(
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date
        )

        return {
            "success": True,
            "tenant_id": tenant_id,
            "analytics": analytics_data,
            "message": "Tavily analytics retrieved successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")


@router.get("/search-history", response_model=Dict[str, Any])
async def get_search_history(
    tenant_id: str,
    limit: int = Query(100, ge=1, le=1000),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Get search history for a tenant.

    Args:
        tenant_id (str): Tenant identifier
        limit (int): Maximum number of searches to return
        start_date (Optional[datetime]): Start date filter
        end_date (Optional[datetime]): End date filter
        current_user (Dict[str, Any]): Current authenticated user

    Returns:
        Dict[str, Any]: Search history data
    """
    try:
        tavily_service = await get_tavily_service()

        history_data = await tavily_service.get_tenant_search_history(
            tenant_id=tenant_id,
            limit=limit,
            start_date=start_date,
            end_date=end_date
        )

        return {
            "success": True,
            "tenant_id": tenant_id,
            "search_history": history_data,
            "message": "Search history retrieved successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get search history: {str(e)}")


# Health and Capabilities Routes
@router.get("/health", response_model=Dict[str, Any])
async def health_check(current_user: Dict[str, Any] = Depends(get_current_user_mongo)):
    """
    Check Tavily service health.

    Args:
        current_user (Dict[str, Any]): Current authenticated user

    Returns:
        Dict[str, Any]: Health status of Tavily service
    """
    try:
        tavily_service = await get_tavily_service()
        health_status = await tavily_service.health_check()

        return {
            "service": "tavily",
            "status": "healthy" if health_status.get("connected") else "unhealthy",
            "connected": health_status.get("connected", False),
            "capabilities": health_status.get("capabilities", []),
            "native_client": health_status.get("native_client", False),
            "api_key_configured": health_status.get("api_key_configured", False),
            "message": "Tavily service health check completed"
        }

    except Exception as e:
        return {
            "service": "tavily",
            "status": "unhealthy",
            "connected": False,
            "error": str(e),
            "message": "Tavily service health check failed"
        }


@router.get("/capabilities", response_model=Dict[str, Any])
async def get_capabilities(current_user: Dict[str, Any] = Depends(get_current_user_mongo)):
    """
    Get Tavily service capabilities.

    Args:
        current_user (Dict[str, Any]): Current authenticated user

    Returns:
        Dict[str, Any]: Available capabilities of Tavily service
    """
    try:
        tavily_service = await get_tavily_service()
        capabilities = await tavily_service.get_capabilities()

        return {
            "service": "tavily",
            "capabilities": capabilities,
            "mcp_enabled": True,
            "supported_operations": [
                "search",
                "quick_search",
                "quick_answer",
                "news_search",
                "financial_search",
                "advanced_search",
                "content_extraction",
                "image_search",
                "analytics",
                "search_history"
            ],
            "message": "Tavily service capabilities retrieved successfully"
        }

    except Exception as e:
        return {
            "service": "tavily",
            "capabilities": {},
            "error": str(e),
            "message": "Failed to get Tavily service capabilities"
        }