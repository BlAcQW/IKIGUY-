"""
Firecrawl Web Data Integration Service.

Provides comprehensive web scraping, crawling, and data extraction capabilities
with stealth mode, JavaScript rendering, and LLM-ready output formats.

MCP Support: Yes (firecrawl-mcp server available)
API Documentation: https://docs.firecrawl.dev/
GitHub: https://github.com/firecrawl/firecrawl
"""

import asyncio
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum

import httpx

# Try to import firecrawl client, fall back to HTTP client
FIRECRAWL_AVAILABLE = False
try:
    from firecrawl import FirecrawlApp
    FIRECRAWL_AVAILABLE = True
except ImportError:
    FirecrawlApp = None


class FirecrawlFormat(str, Enum):
    """Output format options for Firecrawl."""
    MARKDOWN = "markdown"
    HTML = "html"
    RAW_HTML = "rawHtml"
    SCREENSHOT = "screenshot"
    LINKS = "links"
    SUMMARY = "summary"


class FirecrawlAction(str, Enum):
    """Action types for Firecrawl operations."""
    WAIT = "wait"
    CLICK = "click"
    SCREENSHOT = "screenshot"
    WRITE = "write"
    PRESS = "press"
    SCROLL = "scroll"
    SCRAPE = "scrape"


@dataclass
class FirecrawlConfig:
    """Configuration for Firecrawl integration."""
    api_key: str
    base_url: str = "https://api.firecrawl.dev"
    timeout: int = 60
    max_retries: int = 3


@dataclass
class FirecrawlScrapeOptions:
    """Options for scraping operations."""
    formats: List[FirecrawlFormat] = field(default_factory=lambda: [FirecrawlFormat.MARKDOWN])
    onlyMainContent: bool = True
    includeLinks: bool = False
    includeTags: Optional[List[str]] = None
    excludeTags: Optional[List[str]] = None
    waitFor: Optional[int] = None
    mobile: bool = False
    removeBase64Images: bool = False


@dataclass
class FirecrawlCrawlOptions:
    """Options for crawling operations."""
    limit: int = 100
    allowSubdomains: bool = False
    crawlEntireDomain: bool = False
    excludePaths: Optional[List[str]] = None
    includePaths: Optional[List[str]] = None
    maxDepth: Optional[int] = None
    ignoreQueryParameters: bool = True
    webhook: Optional[str] = None


@dataclass
class FirecrawlPage:
    """Represents a scraped/crawled page."""
    url: str
    content: str
    title: Optional[str] = None
    description: Optional[str] = None
    markdown: Optional[str] = None
    html: Optional[str] = None
    screenshot: Optional[str] = None
    links: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    status_code: Optional[int] = None


@dataclass
class FirecrawlResponse:
    """Response from Firecrawl operation."""
    success: bool
    data: Optional[Union[FirecrawlPage, List[FirecrawlPage]]] = None
    job_id: Optional[str] = None
    status: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None
    credits_used: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class FirecrawlIntegration:
    """
    Firecrawl web data integration service.

    Provides comprehensive web scraping, crawling, and data extraction
    with advanced features like stealth mode and JavaScript rendering.
    """

    def __init__(self, config: FirecrawlConfig):
        """
        Initialize Firecrawl integration.

        Args:
            config (FirecrawlConfig): Firecrawl configuration
        """
        self.config = config
        self._connected = False
        self.client = None
        self.session = httpx.AsyncClient(
            timeout=config.timeout,
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json"
            }
        )

        # Initialize native client if available
        if FIRECRAWL_AVAILABLE and config.api_key:
            try:
                self.client = FirecrawlApp(api_key=config.api_key)
            except Exception as e:
                print(f"Warning: Failed to initialize Firecrawl client: {e}")

    async def connect(self) -> bool:
        """
        Test connection to Firecrawl API.

        Returns:
            bool: True if connection successful
        """
        try:
            # Test with a simple scrape
            test_response = await self.scrape("https://example.com")
            self._connected = test_response.success
            return self._connected
        except Exception as e:
            print(f"Firecrawl connection test failed: {e}")
            self._connected = False
            return False

    async def disconnect(self) -> None:
        """Close connection to Firecrawl API."""
        if self.session:
            await self.session.aclose()
        self._connected = False

    async def scrape(
        self,
        url: str,
        options: Optional[FirecrawlScrapeOptions] = None
    ) -> FirecrawlResponse:
        """
        Scrape a single URL.

        Args:
            url (str): URL to scrape
            options (Optional[FirecrawlScrapeOptions]): Scraping options

        Returns:
            FirecrawlResponse: Scraped content
        """
        try:
            # Use native client if available
            if FIRECRAWL_AVAILABLE and self.client:
                return await self._scrape_native(url, options)
            else:
                return await self._scrape_http(url, options)

        except Exception as e:
            return FirecrawlResponse(
                success=False,
                error=f"Scrape failed: {str(e)}"
            )

    async def _scrape_native(
        self,
        url: str,
        options: Optional[FirecrawlScrapeOptions] = None
    ) -> FirecrawlResponse:
        """Scrape using native Firecrawl client."""
        try:
            # Build scrape parameters
            scrape_params = {"url": url}

            if options:
                if options.formats:
                    scrape_params["formats"] = [fmt.value for fmt in options.formats]
                if options.onlyMainContent:
                    scrape_params["onlyMainContent"] = options.onlyMainContent
                if options.includeLinks:
                    scrape_params["includeLinks"] = options.includeLinks
                if options.includeTags:
                    scrape_params["includeTags"] = options.includeTags
                if options.excludeTags:
                    scrape_params["excludeTags"] = options.excludeTags
                if options.waitFor:
                    scrape_params["waitFor"] = options.waitFor
                if options.mobile:
                    scrape_params["mobile"] = options.mobile
                if options.removeBase64Images:
                    scrape_params["removeBase64Images"] = options.removeBase64Images

            # Execute scrape in executor to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, lambda: self.client.scrape_url(**scrape_params)
            )

            # Parse response
            page = FirecrawlPage(
                url=url,
                content=response.get("markdown", response.get("content", "")),
                title=response.get("metadata", {}).get("title"),
                description=response.get("metadata", {}).get("description"),
                markdown=response.get("markdown"),
                html=response.get("html"),
                screenshot=response.get("screenshot"),
                links=response.get("links"),
                metadata=response.get("metadata"),
                status_code=response.get("statusCode")
            )

            return FirecrawlResponse(
                success=True,
                data=page,
                message="Page scraped successfully",
                credits_used=1  # Basic scrape uses 1 credit
            )

        except Exception as e:
            return FirecrawlResponse(
                success=False,
                error=f"Native scrape failed: {str(e)}"
            )

    async def _scrape_http(
        self,
        url: str,
        options: Optional[FirecrawlScrapeOptions] = None
    ) -> FirecrawlResponse:
        """Scrape using HTTP API."""
        try:
            # Build request payload
            payload = {"url": url}

            if options:
                if options.formats:
                    payload["formats"] = [fmt.value for fmt in options.formats]
                if options.onlyMainContent:
                    payload["onlyMainContent"] = options.onlyMainContent
                if options.includeLinks:
                    payload["includeLinks"] = options.includeLinks
                if options.includeTags:
                    payload["includeTags"] = options.includeTags
                if options.excludeTags:
                    payload["excludeTags"] = options.excludeTags
                if options.waitFor:
                    payload["waitFor"] = options.waitFor
                if options.mobile:
                    payload["mobile"] = options.mobile
                if options.removeBase64Images:
                    payload["removeBase64Images"] = options.removeBase64Images

            # Make API request
            response = await self.session.post(
                f"{self.config.base_url}/v0/scrape",
                json=payload
            )

            response.raise_for_status()
            data = response.json()

            # Parse response
            page = FirecrawlPage(
                url=url,
                content=data.get("data", {}).get("markdown", data.get("data", {}).get("content", "")),
                title=data.get("data", {}).get("metadata", {}).get("title"),
                description=data.get("data", {}).get("metadata", {}).get("description"),
                markdown=data.get("data", {}).get("markdown"),
                html=data.get("data", {}).get("html"),
                screenshot=data.get("data", {}).get("screenshot"),
                links=data.get("data", {}).get("links"),
                metadata=data.get("data", {}).get("metadata"),
                status_code=data.get("data", {}).get("statusCode")
            )

            return FirecrawlResponse(
                success=data.get("success", True),
                data=page,
                message="Page scraped successfully",
                credits_used=1
            )

        except httpx.HTTPStatusError as e:
            return FirecrawlResponse(
                success=False,
                error=f"HTTP error {e.response.status_code}: {e.response.text}"
            )
        except Exception as e:
            return FirecrawlResponse(
                success=False,
                error=f"HTTP scrape failed: {str(e)}"
            )

    async def crawl(
        self,
        url: str,
        options: Optional[FirecrawlCrawlOptions] = None,
        scrape_options: Optional[FirecrawlScrapeOptions] = None
    ) -> FirecrawlResponse:
        """
        Crawl a website recursively.

        Args:
            url (str): Starting URL to crawl
            options (Optional[FirecrawlCrawlOptions]): Crawling options
            scrape_options (Optional[FirecrawlScrapeOptions]): Scraping options for each page

        Returns:
            FirecrawlResponse: Crawled pages data
        """
        try:
            # Use native client if available
            if FIRECRAWL_AVAILABLE and self.client:
                return await self._crawl_native(url, options, scrape_options)
            else:
                return await self._crawl_http(url, options, scrape_options)

        except Exception as e:
            return FirecrawlResponse(
                success=False,
                error=f"Crawl failed: {str(e)}"
            )

    async def _crawl_native(
        self,
        url: str,
        options: Optional[FirecrawlCrawlOptions] = None,
        scrape_options: Optional[FirecrawlScrapeOptions] = None
    ) -> FirecrawlResponse:
        """Crawl using native Firecrawl client."""
        try:
            # Build crawl parameters
            crawl_params = {"url": url}

            if options:
                if options.limit:
                    crawl_params["limit"] = options.limit
                if options.allowSubdomains:
                    crawl_params["allowSubdomains"] = options.allowSubdomains
                if options.crawlEntireDomain:
                    crawl_params["crawlEntireDomain"] = options.crawlEntireDomain
                if options.excludePaths:
                    crawl_params["excludePaths"] = options.excludePaths
                if options.includePaths:
                    crawl_params["includePaths"] = options.includePaths
                if options.maxDepth:
                    crawl_params["maxDepth"] = options.maxDepth
                if options.ignoreQueryParameters:
                    crawl_params["ignoreQueryParameters"] = options.ignoreQueryParameters
                if options.webhook:
                    crawl_params["webhook"] = options.webhook

            # Add scrape options
            if scrape_options:
                scrape_config = {}
                if scrape_options.formats:
                    scrape_config["formats"] = [fmt.value for fmt in scrape_options.formats]
                if scrape_options.onlyMainContent:
                    scrape_config["onlyMainContent"] = scrape_options.onlyMainContent
                if scrape_options.includeLinks:
                    scrape_config["includeLinks"] = scrape_options.includeLinks
                if scrape_options.includeTags:
                    scrape_config["includeTags"] = scrape_options.includeTags
                if scrape_options.excludeTags:
                    scrape_config["excludeTags"] = scrape_options.excludeTags

                crawl_params["scrapeOptions"] = scrape_config

            # Execute crawl in executor to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, lambda: self.client.crawl_url(**crawl_params)
            )

            # Parse response
            pages = []
            if "data" in response:
                for page_data in response["data"]:
                    page = FirecrawlPage(
                        url=page_data.get("url", ""),
                        content=page_data.get("markdown", page_data.get("content", "")),
                        title=page_data.get("metadata", {}).get("title"),
                        description=page_data.get("metadata", {}).get("description"),
                        markdown=page_data.get("markdown"),
                        html=page_data.get("html"),
                        screenshot=page_data.get("screenshot"),
                        links=page_data.get("links"),
                        metadata=page_data.get("metadata"),
                        status_code=page_data.get("statusCode")
                    )
                    pages.append(page)

            return FirecrawlResponse(
                success=response.get("success", True),
                data=pages,
                message=f"Crawled {len(pages)} pages successfully",
                credits_used=len(pages)  # Each page uses 1 credit
            )

        except Exception as e:
            return FirecrawlResponse(
                success=False,
                error=f"Native crawl failed: {str(e)}"
            )

    async def _crawl_http(
        self,
        url: str,
        options: Optional[FirecrawlCrawlOptions] = None,
        scrape_options: Optional[FirecrawlScrapeOptions] = None
    ) -> FirecrawlResponse:
        """Crawl using HTTP API."""
        try:
            # Build request payload
            payload = {"url": url}

            if options:
                if options.limit:
                    payload["limit"] = options.limit
                if options.allowSubdomains:
                    payload["allowSubdomains"] = options.allowSubdomains
                if options.crawlEntireDomain:
                    payload["crawlEntireDomain"] = options.crawlEntireDomain
                if options.excludePaths:
                    payload["excludePaths"] = options.excludePaths
                if options.includePaths:
                    payload["includePaths"] = options.includePaths
                if options.maxDepth:
                    payload["maxDepth"] = options.maxDepth
                if options.ignoreQueryParameters:
                    payload["ignoreQueryParameters"] = options.ignoreQueryParameters
                if options.webhook:
                    payload["webhook"] = options.webhook

            # Add scrape options
            if scrape_options:
                scrape_config = {}
                if scrape_options.formats:
                    scrape_config["formats"] = [fmt.value for fmt in scrape_options.formats]
                if scrape_options.onlyMainContent:
                    scrape_config["onlyMainContent"] = scrape_options.onlyMainContent
                if scrape_options.includeLinks:
                    scrape_config["includeLinks"] = scrape_options.includeLinks

                payload["scrapeOptions"] = scrape_config

            # Make API request
            response = await self.session.post(
                f"{self.config.base_url}/v0/crawl",
                json=payload
            )

            response.raise_for_status()
            data = response.json()

            # Parse response
            pages = []
            if "data" in data:
                for page_data in data["data"]:
                    page = FirecrawlPage(
                        url=page_data.get("url", ""),
                        content=page_data.get("markdown", page_data.get("content", "")),
                        title=page_data.get("metadata", {}).get("title"),
                        description=page_data.get("metadata", {}).get("description"),
                        markdown=page_data.get("markdown"),
                        html=page_data.get("html"),
                        screenshot=page_data.get("screenshot"),
                        links=page_data.get("links"),
                        metadata=page_data.get("metadata"),
                        status_code=page_data.get("statusCode")
                    )
                    pages.append(page)

            return FirecrawlResponse(
                success=data.get("success", True),
                data=pages,
                job_id=data.get("jobId"),
                status=data.get("status"),
                message=f"Crawled {len(pages)} pages successfully",
                credits_used=len(pages)
            )

        except httpx.HTTPStatusError as e:
            return FirecrawlResponse(
                success=False,
                error=f"HTTP error {e.response.status_code}: {e.response.text}"
            )
        except Exception as e:
            return FirecrawlResponse(
                success=False,
                error=f"HTTP crawl failed: {str(e)}"
            )

    async def batch_scrape(self, urls: List[str], options: Optional[FirecrawlScrapeOptions] = None) -> FirecrawlResponse:
        """
        Scrape multiple URLs in batch.

        Args:
            urls (List[str]): List of URLs to scrape
            options (Optional[FirecrawlScrapeOptions]): Scraping options

        Returns:
            FirecrawlResponse: Batch scraping results
        """
        try:
            pages = []
            total_credits = 0

            for url in urls:
                result = await self.scrape(url, options)
                if result.success and result.data:
                    pages.append(result.data)
                    total_credits += result.credits_used or 1
                else:
                    # Create error page entry
                    error_page = FirecrawlPage(
                        url=url,
                        content=f"Error: {result.error}",
                        status_code=0
                    )
                    pages.append(error_page)

            return FirecrawlResponse(
                success=True,
                data=pages,
                message=f"Batch scraped {len(pages)} URLs",
                credits_used=total_credits
            )

        except Exception as e:
            return FirecrawlResponse(
                success=False,
                error=f"Batch scrape failed: {str(e)}"
            )

    async def search_and_scrape(self, query: str, num_results: int = 10) -> FirecrawlResponse:
        """
        Search for URLs and scrape the results.

        Args:
            query (str): Search query
            num_results (int): Number of search results to scrape

        Returns:
            FirecrawlResponse: Search and scrape results
        """
        try:
            # This would typically integrate with a search API
            # For now, return a placeholder implementation
            return FirecrawlResponse(
                success=False,
                error="Search and scrape functionality requires additional search API integration"
            )

        except Exception as e:
            return FirecrawlResponse(
                success=False,
                error=f"Search and scrape failed: {str(e)}"
            )

    async def health_check(self) -> Dict[str, Any]:
        """
        Check Firecrawl service health and capabilities.

        Returns:
            Dict[str, Any]: Health status and capabilities
        """
        try:
            # Test basic scrape
            test_result = await self.scrape("https://example.com")

            capabilities = [
                "web_scraping",
                "website_crawling",
                "javascript_rendering",
                "stealth_mode",
                "markdown_extraction",
                "html_extraction",
                "screenshot_capture",
                "link_extraction",
                "batch_scraping",
                "webhook_support"
            ]

            return {
                "connected": test_result.success,
                "service": "firecrawl",
                "capabilities": capabilities,
                "native_client": FIRECRAWL_AVAILABLE,
                "api_key_configured": bool(self.config.api_key),
                "base_url": self.config.base_url,
                "last_test": datetime.now().isoformat(),
                "test_result": test_result.success
            }

        except Exception as e:
            return {
                "connected": False,
                "service": "firecrawl",
                "error": str(e),
                "capabilities": [],
                "native_client": FIRECRAWL_AVAILABLE,
                "api_key_configured": bool(self.config.api_key)
            }

    async def get_capabilities(self) -> Dict[str, Any]:
        """
        Get detailed service capabilities.

        Returns:
            Dict[str, Any]: Service capabilities and features
        """
        return {
            "service": "firecrawl",
            "provider": "Firecrawl",
            "version": "1.0.0",
            "capabilities": {
                "scraping": {
                    "single_page": True,
                    "javascript_rendering": True,
                    "stealth_mode": True,
                    "mobile_simulation": True,
                    "custom_wait_times": True,
                    "content_filtering": True
                },
                "crawling": {
                    "recursive_crawling": True,
                    "subdomain_support": True,
                    "path_filtering": True,
                    "depth_control": True,
                    "webhook_notifications": True
                },
                "output_formats": {
                    "markdown": True,
                    "html": True,
                    "raw_html": True,
                    "screenshot": True,
                    "links": True,
                    "summary": True
                },
                "advanced_features": {
                    "batch_processing": True,
                    "credit_tracking": True,
                    "metadata_extraction": True,
                    "link_extraction": True,
                    "tag_filtering": True
                }
            },
            "mcp_support": {
                "available": True,
                "server": "firecrawl",
                "command": "npx -y firecrawl-mcp",
                "description": "Production ready MCP server with real-time scraping, crawling, and data extraction"
            },
            "rate_limits": {
                "credits_per_operation": "1 credit per page",
                "concurrent_requests": "Varies by plan"
            },
            "authentication": {
                "type": "api_key",
                "required": True
            }
        }


def create_firecrawl_integration(api_key: Optional[str] = None) -> FirecrawlIntegration:
    """
    Create Firecrawl integration instance.

    Args:
        api_key (Optional[str]): Firecrawl API key, if not provided uses environment variable

    Returns:
        FirecrawlIntegration: Configured Firecrawl integration
    """
    if not api_key:
        api_key = os.getenv("FIRECRAWL_API_KEY")

    if not api_key:
        raise ValueError("Firecrawl API key is required")

    config = FirecrawlConfig(api_key=api_key)
    return FirecrawlIntegration(config)


# Export key classes
__all__ = [
    "FirecrawlIntegration",
    "FirecrawlConfig",
    "FirecrawlScrapeOptions",
    "FirecrawlCrawlOptions",
    "FirecrawlPage",
    "FirecrawlResponse",
    "FirecrawlFormat",
    "FirecrawlAction",
    "create_firecrawl_integration"
]