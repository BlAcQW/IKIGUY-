"""
Web Scraper Service

Provides web content extraction functionality using crawl4ai.
Supports multiple extraction modes, JavaScript rendering, and content cleaning.
"""

import asyncio
import httpx
import os
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
import time


class ScraperConfig(BaseModel):
    """Configuration for web scraping"""

    mode: str = Field(default="main-content", description="Extraction mode")
    remove_ads: bool = Field(default=True, description="Remove advertisements")
    wait_for_js: bool = Field(default=False, description="Wait for JavaScript to load")
    custom_selector: Optional[str] = Field(default=None, description="Custom CSS selector")
    timeout: int = Field(default=30, description="Request timeout in seconds")


class ScraperMetadata(BaseModel):
    """Metadata about the scraping result"""

    word_count: int = Field(..., description="Number of words in content")
    char_count: int = Field(..., description="Number of characters in content")
    extraction_time: float = Field(..., description="Time taken to extract content (seconds)")
    url: str = Field(..., description="URL that was scraped")
    title: Optional[str] = Field(default=None, description="Page title if available")


class ScraperResult(BaseModel):
    """Result of web scraping operation"""

    url: str = Field(..., description="Scraped URL")
    title: Optional[str] = Field(default=None, description="Page title")
    content: str = Field(..., description="Extracted text content")
    metadata: ScraperMetadata = Field(..., description="Extraction metadata")
    links: Optional[List[str]] = Field(default=None, description="Extracted links")
    images: Optional[List[str]] = Field(default=None, description="Extracted images")


class WebScraperService:
    """Service for web content extraction using crawl4ai"""

    def __init__(
        self,
        crawl4ai_url: Optional[str] = None,
        default_config: Optional[ScraperConfig] = None
    ):
        """
        Initialize the web scraper service.

        Args:
            crawl4ai_url: URL of the crawl4ai service (defaults to env var)
            default_config: Default scraper configuration
        """
        self.crawl4ai_url = crawl4ai_url or os.getenv(
            "CRAWL4AI_URL",
            "https://crawl4ai.ailabsafrica.com"
        )
        self.default_config = default_config or ScraperConfig()

        # HTTP client with connection pooling
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0),
            follow_redirects=True,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

    async def extract_content(
        self,
        url: str,
        config: Optional[ScraperConfig] = None
    ) -> ScraperResult:
        """
        Extract content from a web page.

        Args:
            url: URL to scrape
            config: Scraper configuration (uses default if not provided)

        Returns:
            ScraperResult with extracted content and metadata

        Raises:
            httpx.HTTPError: If the request fails
            ValueError: If the URL is invalid or extraction fails
        """
        start_time = time.time()
        config = config or self.default_config

        # Validate URL
        try:
            validated_url = HttpUrl(url)
            url_str = str(validated_url)
        except Exception as e:
            raise ValueError(f"Invalid URL: {e}")

        # Prepare request payload
        payload = {
            "url": url_str,
            "mode": config.mode,
            "remove_ads": config.remove_ads,
            "wait_for_js": config.wait_for_js
        }

        if config.custom_selector:
            payload["selector"] = config.custom_selector

        try:
            # Call crawl4ai API
            response = await self.client.post(
                f"{self.crawl4ai_url}/extract",
                json=payload,
                timeout=config.timeout
            )
            response.raise_for_status()
            data = response.json()

            # Extract content
            content = data.get("content", "")
            title = data.get("title", "")
            links = data.get("links", [])
            images = data.get("images", [])

            # Calculate metadata
            word_count = len(content.split())
            char_count = len(content)
            extraction_time = time.time() - start_time

            metadata = ScraperMetadata(
                word_count=word_count,
                char_count=char_count,
                extraction_time=extraction_time,
                url=url_str,
                title=title
            )

            return ScraperResult(
                url=url_str,
                title=title,
                content=content,
                metadata=metadata,
                links=links,
                images=images
            )

        except httpx.HTTPStatusError as e:
            raise ValueError(f"Scraping failed: {e.response.text}")
        except httpx.HTTPError as e:
            raise ValueError(f"Network error: {str(e)}")
        except Exception as e:
            raise ValueError(f"Extraction error: {str(e)}")

    async def extract_batch(
        self,
        urls: List[str],
        config: Optional[ScraperConfig] = None
    ) -> List[ScraperResult]:
        """
        Extract content from multiple URLs concurrently.

        Args:
            urls: List of URLs to scrape
            config: Scraper configuration (uses default if not provided)

        Returns:
            List of ScraperResult objects

        Note:
            Failed extractions will not be included in the result.
            Check the length of the returned list against input.
        """
        tasks = [
            self.extract_content(url, config)
            for url in urls
        ]

        results = []
        for task in asyncio.as_completed(tasks):
            try:
                result = await task
                results.append(result)
            except Exception as e:
                # Log error but continue with other URLs
                print(f"Failed to extract URL: {e}")
                continue

        return results

    async def check_health(self) -> Dict[str, Any]:
        """
        Check if the crawl4ai service is healthy.

        Returns:
            Dictionary with health status information
        """
        try:
            response = await self.client.get(
                f"{self.crawl4ai_url}/health",
                timeout=5.0
            )
            response.raise_for_status()

            return {
                "status": "healthy",
                "crawl4ai_url": self.crawl4ai_url,
                "response_time_ms": response.elapsed.total_seconds() * 1000
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "crawl4ai_url": self.crawl4ai_url,
                "error": str(e)
            }


# Global service instance
_scraper_service: Optional[WebScraperService] = None


def get_scraper_service() -> WebScraperService:
    """
    Get or create the global web scraper service instance.

    Returns:
        WebScraperService instance
    """
    global _scraper_service
    if _scraper_service is None:
        _scraper_service = WebScraperService()
    return _scraper_service
