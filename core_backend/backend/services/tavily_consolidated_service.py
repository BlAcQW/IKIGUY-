"""
Tavily Consolidated Service with tenant-specific context and analytics.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

# from backend.services.integration_service import IntegrationService  # Avoid circular import
# from backend.services.analytics_service import AnalyticsService  # Will implement later

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../shared"))

from integration.tavily import (
    TavilyIntegration,
    TavilyConfig,
    TavilySearchRequest,
    TavilySearchTopic,
    TavilySearchDepth,
    TavilyResponse,
)


class TavilyServiceWrapper(TavilyIntegration):
    """
    Tenant-aware Tavily service with analytics and context tracking.

    Extends TavilyIntegration to provide tenant-specific search operations,
    analytics tracking, and comprehensive context management.
    """

    def __init__(self, config: TavilyConfig):
        super().__init__(config)
        self.analytics_service = AnalyticsService()

    async def search_for_tenant(
        self,
        tenant_id: str,
        request: TavilySearchRequest,
        context: Optional[Dict[str, Any]] = None
    ) -> TavilyResponse:
        """
        Perform search with tenant context and analytics tracking.

        Args:
            tenant_id (str): Unique identifier for the tenant
            request (TavilySearchRequest): Search parameters
            context (Optional[Dict[str, Any]]): Additional context for tracking

        Returns:
            TavilyResponse: Search results with analytics
        """
        # Track analytics
        start_time = datetime.now()
        search_id = str(uuid.uuid4())

        try:
            result = await self.search(request)

            # Record success analytics
            await self._record_analytics(
                tenant_id=tenant_id,
                operation="search",
                success=result.success,
                duration=(datetime.now() - start_time).total_seconds(),
                context=context,
                search_id=search_id,
                query=request.query,
                topic=request.topic.value,
                search_depth=request.search_depth.value,
                result_count=len(result.results),
                credits_used=2 if request.search_depth == TavilySearchDepth.ADVANCED else 1
            )

            return result

        except Exception as e:
            # Record failure analytics
            await self._record_analytics(
                tenant_id=tenant_id,
                operation="search",
                success=False,
                duration=(datetime.now() - start_time).total_seconds(),
                context=context,
                search_id=search_id,
                query=request.query,
                error=str(e)
            )
            raise

    async def search_news_for_tenant(
        self,
        tenant_id: str,
        query: str,
        max_results: int = 5,
        include_answer: bool = True,
        context: Optional[Dict[str, Any]] = None
    ) -> TavilyResponse:
        """
        Search news with tenant context.

        Args:
            tenant_id (str): Unique identifier for the tenant
            query (str): News search query
            max_results (int): Maximum results to return
            include_answer (bool): Generate AI answer
            context (Optional[Dict[str, Any]]): Additional context for tracking

        Returns:
            TavilyResponse: News search results
        """
        request = TavilySearchRequest(
            query=query,
            topic=TavilySearchTopic.NEWS,
            search_depth=TavilySearchDepth.ADVANCED,
            include_answer=include_answer,
            max_results=max_results,
            auto_parameters=True
        )

        return await self.search_for_tenant(tenant_id, request, context)

    async def search_financial_for_tenant(
        self,
        tenant_id: str,
        query: str,
        max_results: int = 5,
        include_answer: bool = True,
        context: Optional[Dict[str, Any]] = None
    ) -> TavilyResponse:
        """
        Search financial information with tenant context.

        Args:
            tenant_id (str): Unique identifier for the tenant
            query (str): Financial search query
            max_results (int): Maximum results to return
            include_answer (bool): Generate AI answer
            context (Optional[Dict[str, Any]]): Additional context for tracking

        Returns:
            TavilyResponse: Financial search results
        """
        request = TavilySearchRequest(
            query=query,
            topic=TavilySearchTopic.FINANCE,
            search_depth=TavilySearchDepth.ADVANCED,
            include_answer=include_answer,
            max_results=max_results,
            auto_parameters=True
        )

        return await self.search_for_tenant(tenant_id, request, context)

    async def quick_answer_for_tenant(
        self,
        tenant_id: str,
        question: str,
        context: Optional[Dict[str, Any]] = None
    ) -> TavilyResponse:
        """
        Get quick AI answer with tenant context.

        Args:
            tenant_id (str): Unique identifier for the tenant
            question (str): Question to answer
            context (Optional[Dict[str, Any]]): Additional context for tracking

        Returns:
            TavilyResponse: AI answer and supporting results
        """
        request = TavilySearchRequest(
            query=question,
            search_depth=TavilySearchDepth.ADVANCED,
            include_answer=True,
            max_results=3,
            auto_parameters=True
        )

        return await self.search_for_tenant(tenant_id, request, context)

    async def search_with_content_for_tenant(
        self,
        tenant_id: str,
        query: str,
        max_results: int = 3,
        context: Optional[Dict[str, Any]] = None
    ) -> TavilyResponse:
        """
        Search with full content extraction for tenant.

        Args:
            tenant_id (str): Unique identifier for the tenant
            query (str): Search query
            max_results (int): Maximum results to return
            context (Optional[Dict[str, Any]]): Additional context for tracking

        Returns:
            TavilyResponse: Search results with full content
        """
        request = TavilySearchRequest(
            query=query,
            search_depth=TavilySearchDepth.ADVANCED,
            include_answer=True,
            include_raw_content=True,
            include_favicon=True,
            max_results=max_results,
            auto_parameters=True
        )

        return await self.search_for_tenant(tenant_id, request, context)

    async def search_with_images_for_tenant(
        self,
        tenant_id: str,
        query: str,
        max_results: int = 5,
        context: Optional[Dict[str, Any]] = None
    ) -> TavilyResponse:
        """
        Search including images for tenant.

        Args:
            tenant_id (str): Unique identifier for the tenant
            query (str): Search query
            max_results (int): Maximum results to return
            context (Optional[Dict[str, Any]]): Additional context for tracking

        Returns:
            TavilyResponse: Search results with images
        """
        request = TavilySearchRequest(
            query=query,
            include_answer=True,
            include_images=True,
            include_favicon=True,
            max_results=max_results,
            auto_parameters=True
        )

        return await self.search_for_tenant(tenant_id, request, context)

    async def advanced_search_for_tenant(
        self,
        tenant_id: str,
        query: str,
        topic: TavilySearchTopic = TavilySearchTopic.GENERAL,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        max_results: int = 10,
        context: Optional[Dict[str, Any]] = None
    ) -> TavilyResponse:
        """
        Advanced search with domain filtering for tenant.

        Args:
            tenant_id (str): Unique identifier for the tenant
            query (str): Search query
            topic (TavilySearchTopic): Search topic category
            include_domains (Optional[List[str]]): Domains to include
            exclude_domains (Optional[List[str]]): Domains to exclude
            max_results (int): Maximum results to return
            context (Optional[Dict[str, Any]]): Additional context for tracking

        Returns:
            TavilyResponse: Advanced search results
        """
        request = TavilySearchRequest(
            query=query,
            topic=topic,
            search_depth=TavilySearchDepth.ADVANCED,
            include_answer=True,
            include_raw_content=True,
            include_images=True,
            include_favicon=True,
            include_domains=include_domains,
            exclude_domains=exclude_domains,
            max_results=max_results,
            auto_parameters=True
        )

        return await self.search_for_tenant(tenant_id, request, context)

    async def get_tenant_analytics(
        self,
        tenant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get Tavily analytics for a specific tenant.

        Args:
            tenant_id (str): Unique identifier for the tenant
            start_date (Optional[datetime]): Start date for analytics
            end_date (Optional[datetime]): End date for analytics

        Returns:
            Dict[str, Any]: Analytics data for the tenant
        """
        return await self.analytics_service.get_tenant_analytics(
            tenant_id=tenant_id,
            service="tavily",
            start_date=start_date,
            end_date=end_date
        )

    async def get_tenant_search_history(
        self,
        tenant_id: str,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get search history for a tenant.

        Args:
            tenant_id (str): Unique identifier for the tenant
            limit (int): Maximum number of searches to return
            start_date (Optional[datetime]): Start date filter
            end_date (Optional[datetime]): End date filter

        Returns:
            Dict[str, Any]: Search history data
        """
        try:
            # This would typically query a database of search history
            # For now, return from analytics service
            analytics_data = await self.get_tenant_analytics(
                tenant_id=tenant_id,
                start_date=start_date,
                end_date=end_date
            )

            return {
                "tenant_id": tenant_id,
                "search_history": analytics_data.get("operations", [])[:limit],
                "total_searches": analytics_data.get("total_operations", 0),
                "period": {
                    "start": start_date.isoformat() if start_date else None,
                    "end": end_date.isoformat() if end_date else None
                }
            }

        except Exception as e:
            return {
                "tenant_id": tenant_id,
                "search_history": [],
                "total_searches": 0,
                "error": str(e)
            }

    async def _record_analytics(
        self,
        tenant_id: str,
        operation: str,
        success: bool,
        duration: float,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """
        Record analytics data for Tavily operations.

        Args:
            tenant_id (str): Unique identifier for the tenant
            operation (str): Operation performed
            success (bool): Whether operation was successful
            duration (float): Operation duration in seconds
            context (Optional[Dict[str, Any]]): Additional context
            **kwargs: Additional data to record
        """
        analytics_data = {
            "tenant_id": tenant_id,
            "service": "tavily",
            "operation": operation,
            "success": success,
            "duration": duration,
            "timestamp": datetime.now().isoformat(),
            "context": context or {},
            **kwargs
        }

        await self.analytics_service.record_operation(analytics_data)


# Global service instance
tavily_consolidated_service: Optional[TavilyServiceWrapper] = None


async def get_tavily_service() -> TavilyServiceWrapper:
    """
    Get the global Tavily service instance.

    Returns:
        TavilyServiceWrapper: The Tavily service instance
    """
    global tavily_consolidated_service

    if tavily_consolidated_service is None:
        # Initialize service from integration service
        integration_service = IntegrationService()
        tavily_integration = await integration_service.get_integration("tavily")

        if not tavily_integration:
            raise RuntimeError("Tavily integration not configured")

        tavily_consolidated_service = TavilyServiceWrapper(tavily_integration.config)

        # Test connection
        await tavily_consolidated_service.connect()

    return tavily_consolidated_service


async def init_tavily_service() -> None:
    """Initialize the Tavily service on startup."""
    try:
        await get_tavily_service()
        print("✅ Tavily service initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Tavily service: {e}")


async def close_tavily_service() -> None:
    """Close the Tavily service on shutdown."""
    global tavily_consolidated_service

    if tavily_consolidated_service:
        await tavily_consolidated_service.disconnect()
        tavily_consolidated_service = None
        print("✅ Tavily service closed successfully")