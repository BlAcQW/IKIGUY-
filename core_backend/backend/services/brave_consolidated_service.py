"""
Brave Search Consolidated Service with tenant-specific context and analytics.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

# Removed circular imports - consolidated services should be independent
# from backend.services.integration_service import IntegrationService
from .analytics_service import AnalyticsService

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../shared"))

from integration.brave import (
    BraveIntegration,
    BraveConfig,
    BraveSearchOptions,
    BraveLocalSearchOptions,
    BraveSearchType,
    BraveFreshness,
    BraveSafeSearch,
    BraveResponse,
)


class BraveServiceWrapper(BraveIntegration):
    """
    Tenant-aware Brave Search service with analytics and context tracking.

    Extends BraveIntegration to provide tenant-specific search operations,
    analytics tracking, and comprehensive context management.
    """

    def __init__(self, config: BraveConfig):
        super().__init__(config)
        self.analytics_service = AnalyticsService()

    async def web_search_for_tenant(
        self,
        tenant_id: str,
        query: str,
        options: Optional[BraveSearchOptions] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> BraveResponse:
        """
        Perform web search with tenant context and analytics tracking.

        Args:
            tenant_id (str): Unique identifier for the tenant
            query (str): Search query
            options (Optional[BraveSearchOptions]): Search options
            context (Optional[Dict[str, Any]]): Additional context for tracking

        Returns:
            BraveResponse: Search results with analytics
        """
        start_time = datetime.now()
        operation_id = str(uuid.uuid4())

        try:
            result = await self.web_search(query, options)

            await self._record_analytics(
                tenant_id=tenant_id,
                operation="web_search",
                success=result.success,
                duration=(datetime.now() - start_time).total_seconds(),
                context=context,
                operation_id=operation_id,
                query=query,
                search_type=BraveSearchType.WEB.value,
                results_count=len(result.results) if result.results else 0,
                has_more=result.has_more
            )

            return result

        except Exception as e:
            await self._record_analytics(
                tenant_id=tenant_id,
                operation="web_search",
                success=False,
                duration=(datetime.now() - start_time).total_seconds(),
                context=context,
                operation_id=operation_id,
                query=query,
                error=str(e)
            )
            raise

    async def news_search_for_tenant(
        self,
        tenant_id: str,
        query: str,
        options: Optional[BraveSearchOptions] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> BraveResponse:
        """
        Perform news search with tenant context and analytics tracking.

        Args:
            tenant_id (str): Unique identifier for the tenant
            query (str): Search query
            options (Optional[BraveSearchOptions]): Search options
            context (Optional[Dict[str, Any]]): Additional context for tracking

        Returns:
            BraveResponse: News search results with analytics
        """
        start_time = datetime.now()
        operation_id = str(uuid.uuid4())

        try:
            result = await self.news_search(query, options)

            await self._record_analytics(
                tenant_id=tenant_id,
                operation="news_search",
                success=result.success,
                duration=(datetime.now() - start_time).total_seconds(),
                context=context,
                operation_id=operation_id,
                query=query,
                search_type=BraveSearchType.NEWS.value,
                results_count=len(result.results) if result.results else 0,
                has_more=result.has_more
            )

            return result

        except Exception as e:
            await self._record_analytics(
                tenant_id=tenant_id,
                operation="news_search",
                success=False,
                duration=(datetime.now() - start_time).total_seconds(),
                context=context,
                operation_id=operation_id,
                query=query,
                error=str(e)
            )
            raise

    async def local_search_for_tenant(
        self,
        tenant_id: str,
        query: str,
        options: Optional[BraveLocalSearchOptions] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> BraveResponse:
        """
        Perform local search with tenant context and analytics tracking.

        Args:
            tenant_id (str): Unique identifier for the tenant
            query (str): Search query (e.g., "pizza near me")
            options (Optional[BraveLocalSearchOptions]): Local search options
            context (Optional[Dict[str, Any]]): Additional context for tracking

        Returns:
            BraveResponse: Local search results with analytics
        """
        start_time = datetime.now()
        operation_id = str(uuid.uuid4())

        try:
            result = await self.local_search(query, options)

            await self._record_analytics(
                tenant_id=tenant_id,
                operation="local_search",
                success=result.success,
                duration=(datetime.now() - start_time).total_seconds(),
                context=context,
                operation_id=operation_id,
                query=query,
                search_type=BraveSearchType.LOCAL.value,
                results_count=len(result.results) if result.results else 0,
                locations_count=len(result.locations) if result.locations else 0
            )

            return result

        except Exception as e:
            await self._record_analytics(
                tenant_id=tenant_id,
                operation="local_search",
                success=False,
                duration=(datetime.now() - start_time).total_seconds(),
                context=context,
                operation_id=operation_id,
                query=query,
                error=str(e)
            )
            raise

    async def batch_search_for_tenant(
        self,
        tenant_id: str,
        queries: List[str],
        search_type: BraveSearchType = BraveSearchType.WEB,
        options: Optional[BraveSearchOptions] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> List[BraveResponse]:
        """
        Perform batch search with tenant context and analytics tracking.

        Args:
            tenant_id (str): Unique identifier for the tenant
            queries (List[str]): List of search queries
            search_type (BraveSearchType): Type of search to perform
            options (Optional[BraveSearchOptions]): Search options
            context (Optional[Dict[str, Any]]): Additional context for tracking

        Returns:
            List[BraveResponse]: List of search results
        """
        start_time = datetime.now()
        operation_id = str(uuid.uuid4())

        try:
            results = await self.batch_search(queries, search_type, options)

            # Calculate aggregate metrics
            successful_searches = len([r for r in results if r.success])
            total_results = sum(len(r.results) if r.results else 0 for r in results)

            await self._record_analytics(
                tenant_id=tenant_id,
                operation="batch_search",
                success=successful_searches > 0,
                duration=(datetime.now() - start_time).total_seconds(),
                context=context,
                operation_id=operation_id,
                queries_count=len(queries),
                queries=queries[:10],  # Store first 10 queries for reference
                search_type=search_type.value,
                successful_searches=successful_searches,
                total_results=total_results
            )

            return results

        except Exception as e:
            await self._record_analytics(
                tenant_id=tenant_id,
                operation="batch_search",
                success=False,
                duration=(datetime.now() - start_time).total_seconds(),
                context=context,
                operation_id=operation_id,
                queries_count=len(queries),
                error=str(e)
            )
            raise

    async def smart_search_for_tenant(
        self,
        tenant_id: str,
        query: str,
        search_intent: str = "general",
        context: Optional[Dict[str, Any]] = None
    ) -> BraveResponse:
        """
        Smart search with optimized settings based on search intent.

        Args:
            tenant_id (str): Unique identifier for the tenant
            query (str): Search query
            search_intent (str): Intent type (general, news, local, recent, research)
            context (Optional[Dict[str, Any]]): Additional context for tracking

        Returns:
            BraveResponse: Smart search results
        """
        # Configure options based on search intent
        if search_intent == "news":
            options = BraveSearchOptions(
                count=15,
                freshness=BraveFreshness.PAST_WEEK,
                safe_search=BraveSafeSearch.MODERATE
            )
            return await self.news_search_for_tenant(tenant_id, query, options, context)
        elif search_intent == "local":
            local_options = BraveLocalSearchOptions(
                count=10,
                search_lang="en",
                country="US"
            )
            return await self.local_search_for_tenant(tenant_id, query, local_options, context)
        elif search_intent == "recent":
            options = BraveSearchOptions(
                count=10,
                freshness=BraveFreshness.PAST_DAY,
                extra_snippets=True
            )
            return await self.web_search_for_tenant(tenant_id, query, options, context)
        elif search_intent == "research":
            options = BraveSearchOptions(
                count=20,
                extra_snippets=True,
                safe_search=BraveSafeSearch.MODERATE
            )
            return await self.web_search_for_tenant(tenant_id, query, options, context)
        else:
            # General search
            options = BraveSearchOptions(
                count=10,
                safe_search=BraveSafeSearch.MODERATE
            )
            return await self.web_search_for_tenant(tenant_id, query, options, context)

    async def trending_search_for_tenant(
        self,
        tenant_id: str,
        query: str,
        timeframe: str = "week",
        context: Optional[Dict[str, Any]] = None
    ) -> BraveResponse:
        """
        Search for trending content within a specific timeframe.

        Args:
            tenant_id (str): Unique identifier for the tenant
            query (str): Search query
            timeframe (str): Time period (day, week, month, year)
            context (Optional[Dict[str, Any]]): Additional context for tracking

        Returns:
            BraveResponse: Trending search results
        """
        # Map timeframe to freshness
        freshness_map = {
            "day": BraveFreshness.PAST_DAY,
            "week": BraveFreshness.PAST_WEEK,
            "month": BraveFreshness.PAST_MONTH,
            "year": BraveFreshness.PAST_YEAR
        }

        freshness = freshness_map.get(timeframe, BraveFreshness.PAST_WEEK)

        options = BraveSearchOptions(
            count=15,
            freshness=freshness,
            extra_snippets=True,
            safe_search=BraveSafeSearch.MODERATE
        )

        return await self.web_search_for_tenant(tenant_id, query, options, context)

    async def multi_type_search_for_tenant(
        self,
        tenant_id: str,
        query: str,
        include_news: bool = True,
        include_local: bool = False,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, BraveResponse]:
        """
        Perform search across multiple content types.

        Args:
            tenant_id (str): Unique identifier for the tenant
            query (str): Search query
            include_news (bool): Whether to include news results
            include_local (bool): Whether to include local results
            context (Optional[Dict[str, Any]]): Additional context for tracking

        Returns:
            Dict[str, BraveResponse]: Results organized by search type
        """
        try:
            tasks = {}

            # Always include web search
            tasks["web"] = self.web_search_for_tenant(tenant_id, query, None, context)

            if include_news:
                tasks["news"] = self.news_search_for_tenant(tenant_id, query, None, context)

            if include_local:
                tasks["local"] = self.local_search_for_tenant(tenant_id, query, None, context)

            results = await asyncio.gather(*tasks.values(), return_exceptions=True)

            # Combine results with their types
            combined_results = {}
            for search_type, result in zip(tasks.keys(), results):
                if isinstance(result, Exception):
                    combined_results[search_type] = BraveResponse(
                        success=False,
                        query=query,
                        search_type=getattr(BraveSearchType, search_type.upper(), BraveSearchType.WEB),
                        error=f"Multi-type search failed for {search_type}: {str(result)}"
                    )
                else:
                    combined_results[search_type] = result

            return combined_results

        except Exception as e:
            return {
                "web": BraveResponse(
                    success=False,
                    query=query,
                    search_type=BraveSearchType.WEB,
                    error=f"Multi-type search failed: {str(e)}"
                )
            }

    async def get_tenant_analytics(
        self,
        tenant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get Brave Search analytics for a specific tenant.

        Args:
            tenant_id (str): Unique identifier for the tenant
            start_date (Optional[datetime]): Start date for analytics
            end_date (Optional[datetime]): End date for analytics

        Returns:
            Dict[str, Any]: Analytics data for the tenant
        """
        return await self.analytics_service.get_tenant_analytics(
            tenant_id=tenant_id,
            service="brave_search",
            start_date=start_date,
            end_date=end_date
        )

    async def get_tenant_usage_summary(
        self,
        tenant_id: str,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Get usage summary for tenant including search statistics.

        Args:
            tenant_id (str): Unique identifier for the tenant
            period_days (int): Number of days to analyze

        Returns:
            Dict[str, Any]: Usage summary with search tracking
        """
        try:
            from datetime import timedelta
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_days)

            analytics_data = await self.get_tenant_analytics(
                tenant_id=tenant_id,
                start_date=start_date,
                end_date=end_date
            )

            operations = analytics_data.get("operations", [])

            # Calculate usage metrics
            total_searches = len(operations)
            web_searches = len([op for op in operations if op.get("operation") == "web_search"])
            news_searches = len([op for op in operations if op.get("operation") == "news_search"])
            local_searches = len([op for op in operations if op.get("operation") == "local_search"])
            batch_searches = len([op for op in operations if op.get("operation") == "batch_search"])

            total_results = sum(op.get("results_count", 0) for op in operations)

            usage_summary = {
                "tenant_id": tenant_id,
                "period_days": period_days,
                "total_searches": total_searches,
                "successful_searches": len([op for op in operations if op.get("success", False)]),
                "failed_searches": len([op for op in operations if not op.get("success", True)]),
                "total_results_retrieved": total_results,
                "search_breakdown": {
                    "web_searches": web_searches,
                    "news_searches": news_searches,
                    "local_searches": local_searches,
                    "batch_searches": batch_searches
                },
                "average_response_time": 0,
                "most_common_queries": [],
                "last_activity": None
            }

            # Calculate average response time
            response_times = [op.get("duration", 0) for op in operations if op.get("duration")]
            if response_times:
                usage_summary["average_response_time"] = sum(response_times) / len(response_times)

            # Find most common queries
            query_counts = {}
            for op in operations:
                query = op.get("query", "")
                if query:
                    query_counts[query] = query_counts.get(query, 0) + 1

            usage_summary["most_common_queries"] = sorted(
                query_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]

            # Find last activity
            if operations:
                timestamps = [op.get("timestamp") for op in operations if op.get("timestamp")]
                if timestamps:
                    usage_summary["last_activity"] = max(timestamps)

            return usage_summary

        except Exception as e:
            return {
                "tenant_id": tenant_id,
                "error": str(e),
                "period_days": period_days,
                "total_searches": 0,
                "total_results_retrieved": 0
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
        Record analytics data for Brave Search operations.

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
            "service": "brave_search",
            "operation": operation,
            "success": success,
            "duration": duration,
            "timestamp": datetime.now().isoformat(),
            "context": context or {},
            **kwargs
        }

        await self.analytics_service.record_operation(analytics_data)


# Global service instance
brave_consolidated_service: Optional[BraveServiceWrapper] = None


async def get_brave_service() -> BraveServiceWrapper:
    """
    Get the global Brave Search service instance.

    Returns:
        BraveServiceWrapper: The Brave Search service instance
    """
    global brave_consolidated_service

    if brave_consolidated_service is None:
        # Initialize directly with API key from environment
        api_key = os.getenv("BRAVE_API_KEY")
        if not api_key:
            raise RuntimeError("Brave Search API key not configured")

        config = BraveConfig(api_key=api_key)
        brave_consolidated_service = BraveServiceWrapper(config)

        # Test connection
        await brave_consolidated_service.connect()

    return brave_consolidated_service


async def init_brave_service() -> None:
    """Initialize the Brave Search service on startup."""
    try:
        await get_brave_service()
        print("✅ Brave Search service initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Brave Search service: {e}")


async def close_brave_service() -> None:
    """Close the Brave Search service on shutdown."""
    global brave_consolidated_service

    if brave_consolidated_service:
        await brave_consolidated_service.disconnect()
        brave_consolidated_service = None
        print("✅ Brave Search service closed successfully")