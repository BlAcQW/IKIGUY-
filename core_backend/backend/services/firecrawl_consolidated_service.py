"""
Firecrawl Consolidated Service with tenant-specific context and analytics.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

# from backend.services.integration_service import IntegrationService  # Avoid circular import
from .analytics_service import AnalyticsService

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../shared"))

from integration.firecrawl import (
    FirecrawlIntegration,
    FirecrawlConfig,
    FirecrawlScrapeOptions,
    FirecrawlCrawlOptions,
    FirecrawlFormat,
    FirecrawlResponse,
)

logger = logging.getLogger(__name__)


class FirecrawlServiceWrapper(FirecrawlIntegration):
    """
    Tenant-aware Firecrawl service with analytics and context tracking.

    Extends FirecrawlIntegration to provide tenant-specific scraping and crawling operations,
    analytics tracking, and comprehensive context management.
    """

    def __init__(self, config: FirecrawlConfig):
        super().__init__(config)
        self.analytics_service = AnalyticsService()

    async def scrape_for_tenant(
        self,
        tenant_id: str,
        url: str,
        options: Optional[FirecrawlScrapeOptions] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> FirecrawlResponse:
        """
        Scrape URL with tenant context and analytics tracking.

        Args:
            tenant_id (str): Unique identifier for the tenant
            url (str): URL to scrape
            options (Optional[FirecrawlScrapeOptions]): Scraping options
            context (Optional[Dict[str, Any]]): Additional context for tracking

        Returns:
            FirecrawlResponse: Scraping results with analytics
        """
        start_time = datetime.now()
        operation_id = str(uuid.uuid4())

        try:
            result = await self.scrape(url, options)

            await self._record_analytics(
                tenant_id=tenant_id,
                operation="scrape",
                success=result.success,
                duration=(datetime.now() - start_time).total_seconds(),
                context=context,
                operation_id=operation_id,
                url=url,
                formats=options.formats if options else [FirecrawlFormat.MARKDOWN],
                credits_used=result.credits_used or 1
            )

            return result

        except Exception as e:
            await self._record_analytics(
                tenant_id=tenant_id,
                operation="scrape",
                success=False,
                duration=(datetime.now() - start_time).total_seconds(),
                context=context,
                operation_id=operation_id,
                url=url,
                error=str(e)
            )
            raise

    async def crawl_for_tenant(
        self,
        tenant_id: str,
        url: str,
        crawl_options: Optional[FirecrawlCrawlOptions] = None,
        scrape_options: Optional[FirecrawlScrapeOptions] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> FirecrawlResponse:
        """
        Crawl website with tenant context and analytics tracking.

        Args:
            tenant_id (str): Unique identifier for the tenant
            url (str): Starting URL to crawl
            crawl_options (Optional[FirecrawlCrawlOptions]): Crawling options
            scrape_options (Optional[FirecrawlScrapeOptions]): Scraping options for each page
            context (Optional[Dict[str, Any]]): Additional context for tracking

        Returns:
            FirecrawlResponse: Crawling results with analytics
        """
        start_time = datetime.now()
        operation_id = str(uuid.uuid4())

        try:
            result = await self.crawl(url, crawl_options, scrape_options)

            # Calculate pages crawled
            pages_crawled = len(result.data) if result.data and isinstance(result.data, list) else 0

            await self._record_analytics(
                tenant_id=tenant_id,
                operation="crawl",
                success=result.success,
                duration=(datetime.now() - start_time).total_seconds(),
                context=context,
                operation_id=operation_id,
                url=url,
                pages_crawled=pages_crawled,
                limit=crawl_options.limit if crawl_options else 100,
                credits_used=result.credits_used or pages_crawled
            )

            return result

        except Exception as e:
            await self._record_analytics(
                tenant_id=tenant_id,
                operation="crawl",
                success=False,
                duration=(datetime.now() - start_time).total_seconds(),
                context=context,
                operation_id=operation_id,
                url=url,
                error=str(e)
            )
            raise

    async def batch_scrape_for_tenant(
        self,
        tenant_id: str,
        urls: List[str],
        options: Optional[FirecrawlScrapeOptions] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> FirecrawlResponse:
        """
        Batch scrape URLs with tenant context.

        Args:
            tenant_id (str): Unique identifier for the tenant
            urls (List[str]): List of URLs to scrape
            options (Optional[FirecrawlScrapeOptions]): Scraping options
            context (Optional[Dict[str, Any]]): Additional context for tracking

        Returns:
            FirecrawlResponse: Batch scraping results
        """
        start_time = datetime.now()
        operation_id = str(uuid.uuid4())

        try:
            result = await self.batch_scrape(urls, options)

            await self._record_analytics(
                tenant_id=tenant_id,
                operation="batch_scrape",
                success=result.success,
                duration=(datetime.now() - start_time).total_seconds(),
                context=context,
                operation_id=operation_id,
                url_count=len(urls),
                urls=urls[:10],  # Store first 10 URLs for reference
                credits_used=result.credits_used or len(urls)
            )

            return result

        except Exception as e:
            await self._record_analytics(
                tenant_id=tenant_id,
                operation="batch_scrape",
                success=False,
                duration=(datetime.now() - start_time).total_seconds(),
                context=context,
                operation_id=operation_id,
                url_count=len(urls),
                error=str(e)
            )
            raise

    async def smart_scrape_for_tenant(
        self,
        tenant_id: str,
        url: str,
        extract_type: str = "content",
        context: Optional[Dict[str, Any]] = None
    ) -> FirecrawlResponse:
        """
        Smart scraping with optimized settings based on extract type.

        Args:
            tenant_id (str): Unique identifier for the tenant
            url (str): URL to scrape
            extract_type (str): Type of content to extract (content, links, metadata, screenshot)
            context (Optional[Dict[str, Any]]): Additional context for tracking

        Returns:
            FirecrawlResponse: Smart scraping results
        """
        # Configure options based on extract type
        if extract_type == "content":
            options = FirecrawlScrapeOptions(
                formats=[FirecrawlFormat.MARKDOWN, FirecrawlFormat.HTML],
                onlyMainContent=True,
                removeBase64Images=True
            )
        elif extract_type == "links":
            options = FirecrawlScrapeOptions(
                formats=[FirecrawlFormat.LINKS, FirecrawlFormat.MARKDOWN],
                includeLinks=True,
                onlyMainContent=False
            )
        elif extract_type == "metadata":
            options = FirecrawlScrapeOptions(
                formats=[FirecrawlFormat.MARKDOWN],
                onlyMainContent=False
            )
        elif extract_type == "screenshot":
            options = FirecrawlScrapeOptions(
                formats=[FirecrawlFormat.SCREENSHOT, FirecrawlFormat.MARKDOWN],
                onlyMainContent=True
            )
        else:
            options = FirecrawlScrapeOptions()

        return await self.scrape_for_tenant(tenant_id, url, options, context)

    async def monitor_crawl_for_tenant(
        self,
        tenant_id: str,
        url: str,
        max_pages: int = 50,
        include_subdomains: bool = False,
        context: Optional[Dict[str, Any]] = None
    ) -> FirecrawlResponse:
        """
        Monitor and crawl website with reasonable limits.

        Args:
            tenant_id (str): Unique identifier for the tenant
            url (str): Starting URL to crawl
            max_pages (int): Maximum pages to crawl
            include_subdomains (bool): Whether to include subdomains
            context (Optional[Dict[str, Any]]): Additional context for tracking

        Returns:
            FirecrawlResponse: Monitored crawling results
        """
        crawl_options = FirecrawlCrawlOptions(
            limit=max_pages,
            allowSubdomains=include_subdomains,
            crawlEntireDomain=False,
            ignoreQueryParameters=True,
            maxDepth=3  # Reasonable depth limit
        )

        scrape_options = FirecrawlScrapeOptions(
            formats=[FirecrawlFormat.MARKDOWN],
            onlyMainContent=True,
            removeBase64Images=True
        )

        return await self.crawl_for_tenant(
            tenant_id=tenant_id,
            url=url,
            crawl_options=crawl_options,
            scrape_options=scrape_options,
            context=context
        )

    async def extract_content_for_tenant(
        self,
        tenant_id: str,
        url: str,
        content_type: str = "article",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extract structured content optimized for specific content types.

        Args:
            tenant_id (str): Unique identifier for the tenant
            url (str): URL to extract content from
            content_type (str): Type of content (article, product, news, documentation)
            context (Optional[Dict[str, Any]]): Additional context for tracking

        Returns:
            Dict[str, Any]: Extracted structured content
        """
        try:
            # Configure scraping based on content type
            if content_type == "article":
                options = FirecrawlScrapeOptions(
                    formats=[FirecrawlFormat.MARKDOWN, FirecrawlFormat.HTML],
                    onlyMainContent=True,
                    excludeTags=["nav", "footer", "aside", "advertisement"]
                )
            elif content_type == "product":
                options = FirecrawlScrapeOptions(
                    formats=[FirecrawlFormat.MARKDOWN, FirecrawlFormat.SCREENSHOT],
                    onlyMainContent=True,
                    includeLinks=True
                )
            elif content_type == "news":
                options = FirecrawlScrapeOptions(
                    formats=[FirecrawlFormat.MARKDOWN],
                    onlyMainContent=True,
                    excludeTags=["nav", "footer", "sidebar", "comments"]
                )
            elif content_type == "documentation":
                options = FirecrawlScrapeOptions(
                    formats=[FirecrawlFormat.MARKDOWN, FirecrawlFormat.LINKS],
                    onlyMainContent=False,
                    includeLinks=True
                )
            else:
                options = FirecrawlScrapeOptions()

            result = await self.scrape_for_tenant(tenant_id, url, options, context)

            if result.success and result.data:
                page = result.data
                return {
                    "success": True,
                    "url": url,
                    "content_type": content_type,
                    "title": page.title,
                    "description": page.description,
                    "content": page.content,
                    "markdown": page.markdown,
                    "html": page.html,
                    "links": page.links,
                    "metadata": page.metadata,
                    "screenshot": page.screenshot,
                    "extraction_time": datetime.now().isoformat(),
                    "credits_used": result.credits_used
                }
            else:
                return {
                    "success": False,
                    "url": url,
                    "content_type": content_type,
                    "error": result.error,
                    "extraction_time": datetime.now().isoformat()
                }

        except Exception as e:
            return {
                "success": False,
                "url": url,
                "content_type": content_type,
                "error": str(e),
                "extraction_time": datetime.now().isoformat()
            }

    async def get_tenant_analytics(
        self,
        tenant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get Firecrawl analytics for a specific tenant.

        Args:
            tenant_id (str): Unique identifier for the tenant
            start_date (Optional[datetime]): Start date for analytics
            end_date (Optional[datetime]): End date for analytics

        Returns:
            Dict[str, Any]: Analytics data for the tenant
        """
        return await self.analytics_service.get_tenant_analytics(
            tenant_id=tenant_id,
            service="firecrawl",
            start_date=start_date,
            end_date=end_date
        )

    async def get_tenant_usage_summary(
        self,
        tenant_id: str,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Get usage summary for tenant including credit consumption.

        Args:
            tenant_id (str): Unique identifier for the tenant
            period_days (int): Number of days to analyze

        Returns:
            Dict[str, Any]: Usage summary with credit tracking
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
            total_credits = sum(op.get("credits_used", 0) for op in operations)
            total_pages = sum(op.get("pages_crawled", 0) for op in operations if op.get("operation") == "crawl")
            total_scrapes = len([op for op in operations if op.get("operation") == "scrape"])
            total_crawls = len([op for op in operations if op.get("operation") == "crawl"])
            total_batch_operations = len([op for op in operations if op.get("operation") == "batch_scrape"])

            usage_summary = {
                "tenant_id": tenant_id,
                "period_days": period_days,
                "total_operations": len(operations),
                "successful_operations": len([op for op in operations if op.get("success", False)]),
                "failed_operations": len([op for op in operations if not op.get("success", True)]),
                "total_credits_used": total_credits,
                "total_pages_processed": total_pages + total_scrapes,
                "operation_breakdown": {
                    "scrapes": total_scrapes,
                    "crawls": total_crawls,
                    "batch_operations": total_batch_operations,
                    "pages_crawled": total_pages
                },
                "average_response_time": 0,
                "last_activity": None
            }

            # Calculate average response time
            response_times = [op.get("duration", 0) for op in operations if op.get("duration")]
            if response_times:
                usage_summary["average_response_time"] = sum(response_times) / len(response_times)

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
                "total_operations": 0,
                "total_credits_used": 0
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
        Record analytics data for Firecrawl operations.

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
            "service": "firecrawl",
            "operation": operation,
            "success": success,
            "duration": duration,
            "timestamp": datetime.now().isoformat(),
            "context": context or {},
            **kwargs
        }

        await self.analytics_service.record_operation(analytics_data)


# Global service instance
firecrawl_consolidated_service: Optional[FirecrawlServiceWrapper] = None


async def get_firecrawl_service() -> FirecrawlServiceWrapper:
    """
    Get the global Firecrawl service instance.

    Returns:
        FirecrawlServiceWrapper: The Firecrawl service instance
    """
    global firecrawl_consolidated_service

    if firecrawl_consolidated_service is None:
        # Initialize service directly to avoid circular import
        import os
        from integration.firecrawl import FirecrawlConfig

        api_key = os.getenv("FIRECRAWL_API_KEY")
        if not api_key:
            raise RuntimeError("Firecrawl API key not configured. Set FIRECRAWL_API_KEY environment variable")

        config = FirecrawlConfig(api_key=api_key)
        firecrawl_consolidated_service = FirecrawlServiceWrapper(config)

        # Test connection
        try:
            await firecrawl_consolidated_service.connect()
        except Exception as e:
            logger.warning(f"Firecrawl connection test failed: {e}")

    return firecrawl_consolidated_service


async def init_firecrawl_service() -> None:
    """Initialize the Firecrawl service on startup."""
    try:
        await get_firecrawl_service()
        print("✅ Firecrawl service initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Firecrawl service: {e}")


async def close_firecrawl_service() -> None:
    """Close the Firecrawl service on shutdown."""
    global firecrawl_consolidated_service

    if firecrawl_consolidated_service:
        await firecrawl_consolidated_service.disconnect()
        firecrawl_consolidated_service = None
        print("✅ Firecrawl service closed successfully")