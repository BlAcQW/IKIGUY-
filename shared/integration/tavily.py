"""
Tavily AI Search Integration Service.

Provides comprehensive AI-powered search capabilities with real-time web access,
content extraction, image search, and intelligent answer generation.

MCP Support: Yes (tavily server available)
API Documentation: https://docs.tavily.com/documentation/api-reference/endpoint/search
"""

import asyncio
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum

import httpx

# Try to import tavily client, fall back to HTTP client
TAVILY_AVAILABLE = False
try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TavilyClient = None


class TavilySearchTopic(str, Enum):
    """Search topic categories for Tavily."""
    GENERAL = "general"
    NEWS = "news"
    FINANCE = "finance"


class TavilySearchDepth(str, Enum):
    """Search depth options for Tavily."""
    BASIC = "basic"
    ADVANCED = "advanced"


@dataclass
class TavilyConfig:
    """Configuration for Tavily AI Search integration."""
    api_key: str
    base_url: str = "https://api.tavily.com"
    timeout: int = 30
    max_retries: int = 3


@dataclass
class TavilySearchRequest:
    """Tavily search request parameters."""
    query: str
    topic: TavilySearchTopic = TavilySearchTopic.GENERAL
    search_depth: TavilySearchDepth = TavilySearchDepth.BASIC
    include_answer: bool = False
    include_raw_content: bool = False
    include_images: bool = False
    include_domains: Optional[List[str]] = None
    exclude_domains: Optional[List[str]] = None
    max_results: int = 5
    include_favicon: bool = False
    auto_parameters: bool = True


@dataclass
class TavilySearchResult:
    """Individual search result from Tavily."""
    title: str
    url: str
    content: str
    score: float
    published_date: Optional[str] = None
    favicon: Optional[str] = None
    raw_content: Optional[str] = None


@dataclass
class TavilyImageResult:
    """Image search result from Tavily."""
    url: str
    title: Optional[str] = None
    alt_text: Optional[str] = None


@dataclass
class TavilyResponse:
    """Response from Tavily search operation."""
    success: bool
    query: str
    answer: Optional[str] = None
    results: List[TavilySearchResult] = field(default_factory=list)
    images: List[TavilyImageResult] = field(default_factory=list)
    search_depth: Optional[str] = None
    search_time: Optional[float] = None
    response_time: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class TavilyIntegration:
    """
    Tavily AI Search integration service.

    Provides comprehensive search capabilities including real-time web search,
    content extraction, image search, and AI-powered answer generation.
    """

    def __init__(self, config: TavilyConfig):
        """
        Initialize Tavily integration.

        Args:
            config (TavilyConfig): Tavily configuration
        """
        self.config = config
        self._connected = False
        self.client = None
        self.session = httpx.AsyncClient(timeout=config.timeout)

        # Initialize native client if available
        if TAVILY_AVAILABLE and config.api_key:
            try:
                self.client = TavilyClient(api_key=config.api_key)
            except Exception as e:
                print(f"Warning: Failed to initialize Tavily client: {e}")

    async def connect(self) -> bool:
        """
        Test connection to Tavily API.

        Returns:
            bool: True if connection successful
        """
        try:
            # Test with a simple search
            test_response = await self.search(TavilySearchRequest(
                query="test connection",
                max_results=1
            ))
            self._connected = test_response.success
            return self._connected
        except Exception as e:
            print(f"Tavily connection test failed: {e}")
            self._connected = False
            return False

    async def disconnect(self) -> None:
        """Close connection to Tavily API."""
        if self.session:
            await self.session.aclose()
        self._connected = False

    async def search(self, request: TavilySearchRequest) -> TavilyResponse:
        """
        Perform AI-powered web search.

        Args:
            request (TavilySearchRequest): Search parameters

        Returns:
            TavilyResponse: Search results and metadata
        """
        try:
            # Use native client if available
            if TAVILY_AVAILABLE and self.client:
                return await self._search_native(request)
            else:
                return await self._search_http(request)

        except Exception as e:
            return TavilyResponse(
                success=False,
                query=request.query,
                error=f"Search failed: {str(e)}"
            )

    async def _search_native(self, request: TavilySearchRequest) -> TavilyResponse:
        """Search using native Tavily client."""
        try:
            # Build search parameters
            search_params = {
                "query": request.query,
                "topic": request.topic.value,
                "search_depth": request.search_depth.value,
                "include_answer": request.include_answer,
                "include_raw_content": request.include_raw_content,
                "include_images": request.include_images,
                "max_results": request.max_results,
                "include_favicon": request.include_favicon,
            }

            # Add optional parameters
            if request.include_domains:
                search_params["include_domains"] = request.include_domains
            if request.exclude_domains:
                search_params["exclude_domains"] = request.exclude_domains
            if request.auto_parameters:
                search_params["auto_parameters"] = True

            # Execute search
            start_time = datetime.now()

            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, lambda: self.client.search(**search_params)
            )

            search_time = (datetime.now() - start_time).total_seconds()

            # Parse results
            results = []
            if "results" in response:
                for result in response["results"]:
                    search_result = TavilySearchResult(
                        title=result.get("title", ""),
                        url=result.get("url", ""),
                        content=result.get("content", ""),
                        score=result.get("score", 0.0),
                        published_date=result.get("published_date"),
                        favicon=result.get("favicon") if request.include_favicon else None,
                        raw_content=result.get("raw_content") if request.include_raw_content else None
                    )
                    results.append(search_result)

            # Parse images
            images = []
            if request.include_images and "images" in response:
                for image in response["images"]:
                    image_result = TavilyImageResult(
                        url=image.get("url", ""),
                        title=image.get("title"),
                        alt_text=image.get("alt_text")
                    )
                    images.append(image_result)

            return TavilyResponse(
                success=True,
                query=request.query,
                answer=response.get("answer"),
                results=results,
                images=images,
                search_depth=request.search_depth.value,
                search_time=search_time,
                response_time=datetime.now().isoformat(),
                data=response
            )

        except Exception as e:
            return TavilyResponse(
                success=False,
                query=request.query,
                error=f"Native search failed: {str(e)}"
            )

    async def _search_http(self, request: TavilySearchRequest) -> TavilyResponse:
        """Search using HTTP API."""
        try:
            # Build request payload
            payload = {
                "api_key": self.config.api_key,
                "query": request.query,
                "topic": request.topic.value,
                "search_depth": request.search_depth.value,
                "include_answer": request.include_answer,
                "include_raw_content": request.include_raw_content,
                "include_images": request.include_images,
                "max_results": request.max_results,
                "include_favicon": request.include_favicon,
            }

            # Add optional parameters
            if request.include_domains:
                payload["include_domains"] = request.include_domains
            if request.exclude_domains:
                payload["exclude_domains"] = request.exclude_domains
            if request.auto_parameters:
                payload["auto_parameters"] = True

            # Make API request
            start_time = datetime.now()
            response = await self.session.post(
                f"{self.config.base_url}/search",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            search_time = (datetime.now() - start_time).total_seconds()

            response.raise_for_status()
            data = response.json()

            # Parse results
            results = []
            if "results" in data:
                for result in data["results"]:
                    search_result = TavilySearchResult(
                        title=result.get("title", ""),
                        url=result.get("url", ""),
                        content=result.get("content", ""),
                        score=result.get("score", 0.0),
                        published_date=result.get("published_date"),
                        favicon=result.get("favicon") if request.include_favicon else None,
                        raw_content=result.get("raw_content") if request.include_raw_content else None
                    )
                    results.append(search_result)

            # Parse images
            images = []
            if request.include_images and "images" in data:
                for image in data["images"]:
                    image_result = TavilyImageResult(
                        url=image.get("url", ""),
                        title=image.get("title"),
                        alt_text=image.get("alt_text")
                    )
                    images.append(image_result)

            return TavilyResponse(
                success=True,
                query=request.query,
                answer=data.get("answer"),
                results=results,
                images=images,
                search_depth=request.search_depth.value,
                search_time=search_time,
                response_time=datetime.now().isoformat(),
                data=data
            )

        except httpx.HTTPStatusError as e:
            return TavilyResponse(
                success=False,
                query=request.query,
                error=f"HTTP error {e.response.status_code}: {e.response.text}"
            )
        except Exception as e:
            return TavilyResponse(
                success=False,
                query=request.query,
                error=f"HTTP search failed: {str(e)}"
            )

    async def search_news(self, query: str, max_results: int = 5, include_answer: bool = True) -> TavilyResponse:
        """
        Search for news articles.

        Args:
            query (str): News search query
            max_results (int): Maximum results to return
            include_answer (bool): Generate AI answer

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
        return await self.search(request)

    async def search_financial(self, query: str, max_results: int = 5, include_answer: bool = True) -> TavilyResponse:
        """
        Search for financial information.

        Args:
            query (str): Financial search query
            max_results (int): Maximum results to return
            include_answer (bool): Generate AI answer

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
        return await self.search(request)

    async def search_with_content(self, query: str, max_results: int = 3) -> TavilyResponse:
        """
        Search with full content extraction.

        Args:
            query (str): Search query
            max_results (int): Maximum results to return

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
        return await self.search(request)

    async def search_with_images(self, query: str, max_results: int = 5) -> TavilyResponse:
        """
        Search including relevant images.

        Args:
            query (str): Search query
            max_results (int): Maximum results to return

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
        return await self.search(request)

    async def quick_answer(self, question: str) -> TavilyResponse:
        """
        Get a quick AI-generated answer to a question.

        Args:
            question (str): Question to answer

        Returns:
            TavilyResponse: Answer and supporting search results
        """
        request = TavilySearchRequest(
            query=question,
            search_depth=TavilySearchDepth.ADVANCED,
            include_answer=True,
            max_results=3,
            auto_parameters=True
        )
        return await self.search(request)

    async def health_check(self) -> Dict[str, Any]:
        """
        Check Tavily service health and capabilities.

        Returns:
            Dict[str, Any]: Health status and capabilities
        """
        try:
            # Test basic search
            test_result = await self.search(TavilySearchRequest(
                query="health check",
                max_results=1
            ))

            capabilities = [
                "real_time_search",
                "ai_answer_generation",
                "content_extraction",
                "image_search",
                "news_search",
                "financial_search",
                "domain_filtering",
                "relevance_scoring"
            ]

            return {
                "connected": test_result.success,
                "service": "tavily",
                "capabilities": capabilities,
                "native_client": TAVILY_AVAILABLE,
                "api_key_configured": bool(self.config.api_key),
                "base_url": self.config.base_url,
                "last_test": datetime.now().isoformat(),
                "test_result": test_result.success
            }

        except Exception as e:
            return {
                "connected": False,
                "service": "tavily",
                "error": str(e),
                "capabilities": [],
                "native_client": TAVILY_AVAILABLE,
                "api_key_configured": bool(self.config.api_key)
            }

    async def get_capabilities(self) -> Dict[str, Any]:
        """
        Get detailed service capabilities.

        Returns:
            Dict[str, Any]: Service capabilities and features
        """
        return {
            "service": "tavily",
            "provider": "Tavily AI",
            "version": "1.0.0",
            "capabilities": {
                "search": {
                    "real_time_search": True,
                    "ai_answer_generation": True,
                    "content_extraction": True,
                    "image_search": True,
                    "relevance_scoring": True,
                    "domain_filtering": True,
                    "auto_parameters": True
                },
                "topics": {
                    "general": True,
                    "news": True,
                    "finance": True
                },
                "search_depths": {
                    "basic": "1 API credit",
                    "advanced": "2 API credits"
                },
                "features": {
                    "include_answer": "AI-generated answer",
                    "include_raw_content": "Full webpage content",
                    "include_images": "Related images",
                    "include_favicon": "Website favicons",
                    "include_domains": "Domain whitelist",
                    "exclude_domains": "Domain blacklist"
                }
            },
            "mcp_support": {
                "available": True,
                "server": "tavily",
                "command": "npx -y mcp-server-tavily",
                "description": "Production ready MCP server with real-time search, extract, map & crawl"
            },
            "rate_limits": {
                "requests_per_minute": "Varies by plan",
                "api_credits": "Per search operation"
            },
            "authentication": {
                "type": "api_key",
                "required": True
            }
        }


def create_tavily_integration(api_key: Optional[str] = None) -> TavilyIntegration:
    """
    Create Tavily integration instance.

    Args:
        api_key (Optional[str]): Tavily API key, if not provided uses environment variable

    Returns:
        TavilyIntegration: Configured Tavily integration
    """
    if not api_key:
        api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        raise ValueError("Tavily API key is required")

    config = TavilyConfig(api_key=api_key)
    return TavilyIntegration(config)


# Export key classes
__all__ = [
    "TavilyIntegration",
    "TavilyConfig",
    "TavilySearchRequest",
    "TavilySearchResult",
    "TavilyImageResult",
    "TavilyResponse",
    "TavilySearchTopic",
    "TavilySearchDepth",
    "create_tavily_integration"
]