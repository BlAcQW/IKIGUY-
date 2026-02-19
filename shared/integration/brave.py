"""
Brave Search Integration Service.

Provides comprehensive web search, local search, and news search capabilities
using the Brave Search API with MCP server support.

MCP Support: Yes (brave-search MCP server available)
API Documentation: https://brave.com/search/api/
GitHub: https://github.com/brave/brave-search-api
"""

import asyncio
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum

import httpx


class BraveSearchType(str, Enum):
    """Search type options for Brave Search."""
    WEB = "web"
    NEWS = "news"
    IMAGES = "images"
    VIDEOS = "videos"
    LOCAL = "local"


class BraveFreshness(str, Enum):
    """Freshness options for search results."""
    ALL = "all"
    PAST_DAY = "pd"
    PAST_WEEK = "pw"
    PAST_MONTH = "pm"
    PAST_YEAR = "py"


class BraveSafeSearch(str, Enum):
    """Safe search filtering options."""
    OFF = "off"
    MODERATE = "moderate"
    STRICT = "strict"


@dataclass
class BraveConfig:
    """Configuration for Brave Search integration."""
    api_key: str
    base_url: str = "https://api.search.brave.com/res/v1"
    timeout: int = 30
    max_retries: int = 3


@dataclass
class BraveSearchOptions:
    """Options for search operations."""
    count: int = 10
    offset: int = 0
    freshness: BraveFreshness = BraveFreshness.ALL
    safe_search: BraveSafeSearch = BraveSafeSearch.MODERATE
    search_lang: str = "en"
    country: str = "US"
    extra_snippets: bool = False
    result_filter: Optional[str] = None


@dataclass
class BraveLocalSearchOptions:
    """Options for local search operations."""
    count: int = 5
    search_lang: str = "en"
    country: str = "US"
    units: str = "metric"  # metric or imperial


@dataclass
class BraveResult:
    """Represents a search result."""
    title: str
    url: str
    description: str
    published: Optional[str] = None
    thumbnail: Optional[str] = None
    language: Optional[str] = None
    family_friendly: Optional[bool] = None
    type: Optional[str] = None
    subtype: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None


@dataclass
class BraveLocalResult:
    """Represents a local search result."""
    title: str
    url: str
    description: str
    phone: Optional[str] = None
    address: str = ""
    rating: Optional[float] = None
    rating_count: Optional[int] = None
    hours: Optional[Dict[str, Any]] = None
    category: Optional[str] = None
    price_range: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None


@dataclass
class BraveResponse:
    """Response from Brave Search operation."""
    success: bool
    query: str
    search_type: BraveSearchType
    results: Optional[List[Union[BraveResult, BraveLocalResult]]] = None
    total_results: Optional[int] = None
    has_more: Optional[bool] = None
    suggestions: Optional[List[str]] = None
    locations: Optional[List[Dict[str, Any]]] = None
    message: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BraveIntegration:
    """
    Brave Search integration service.

    Provides comprehensive web search, local search, and news search
    with advanced filtering and location-based capabilities.
    """

    def __init__(self, config: BraveConfig):
        """
        Initialize Brave Search integration.

        Args:
            config (BraveConfig): Brave Search configuration
        """
        self.config = config
        self._connected = False
        self.session = httpx.AsyncClient(
            timeout=config.timeout,
            headers={
                "X-Subscription-Token": config.api_key,
                "Accept": "application/json",
                "Accept-Encoding": "gzip"
            }
        )

    async def connect(self) -> bool:
        """
        Test connection to Brave Search API.

        Returns:
            bool: True if connection successful
        """
        try:
            # Test with a simple search
            test_response = await self.web_search("test query", BraveSearchOptions(count=1))
            self._connected = test_response.success
            return self._connected
        except Exception as e:
            print(f"Brave Search connection test failed: {e}")
            self._connected = False
            return False

    async def disconnect(self) -> None:
        """Close connection to Brave Search API."""
        if self.session:
            await self.session.aclose()
        self._connected = False

    async def web_search(
        self,
        query: str,
        options: Optional[BraveSearchOptions] = None
    ) -> BraveResponse:
        """
        Perform web search.

        Args:
            query (str): Search query
            options (Optional[BraveSearchOptions]): Search options

        Returns:
            BraveResponse: Search results
        """
        try:
            return await self._search_http(query, BraveSearchType.WEB, options)
        except Exception as e:
            return BraveResponse(
                success=False,
                query=query,
                search_type=BraveSearchType.WEB,
                error=f"Web search failed: {str(e)}"
            )

    async def news_search(
        self,
        query: str,
        options: Optional[BraveSearchOptions] = None
    ) -> BraveResponse:
        """
        Perform news search.

        Args:
            query (str): Search query
            options (Optional[BraveSearchOptions]): Search options

        Returns:
            BraveResponse: News search results
        """
        try:
            return await self._search_http(query, BraveSearchType.NEWS, options)
        except Exception as e:
            return BraveResponse(
                success=False,
                query=query,
                search_type=BraveSearchType.NEWS,
                error=f"News search failed: {str(e)}"
            )

    async def local_search(
        self,
        query: str,
        options: Optional[BraveLocalSearchOptions] = None
    ) -> BraveResponse:
        """
        Perform local search.

        Args:
            query (str): Search query (e.g., "pizza near me")
            options (Optional[BraveLocalSearchOptions]): Local search options

        Returns:
            BraveResponse: Local search results
        """
        try:
            # Build query parameters for local search
            params = {
                "q": query,
                "count": options.count if options else 5,
                "search_lang": options.search_lang if options else "en",
                "country": options.country if options else "US",
                "units": options.units if options else "metric"
            }

            response = await self.session.get(
                f"{self.config.base_url}/local/search",
                params=params
            )

            response.raise_for_status()
            data = response.json()

            # Parse local results
            results = []
            if "locations" in data:
                for location in data["locations"]:
                    result = BraveLocalResult(
                        title=location.get("name", ""),
                        url=location.get("url", ""),
                        description=location.get("description", ""),
                        phone=location.get("phone"),
                        address=location.get("address", ""),
                        rating=location.get("rating"),
                        rating_count=location.get("rating_count"),
                        hours=location.get("hours"),
                        category=location.get("category"),
                        price_range=location.get("price_range"),
                        coordinates=location.get("coordinates")
                    )
                    results.append(result)

            return BraveResponse(
                success=True,
                query=query,
                search_type=BraveSearchType.LOCAL,
                results=results,
                total_results=len(results),
                locations=data.get("locations", []),
                message="Local search completed successfully"
            )

        except httpx.HTTPStatusError as e:
            return BraveResponse(
                success=False,
                query=query,
                search_type=BraveSearchType.LOCAL,
                error=f"HTTP error {e.response.status_code}: {e.response.text}"
            )
        except Exception as e:
            return BraveResponse(
                success=False,
                query=query,
                search_type=BraveSearchType.LOCAL,
                error=f"Local search failed: {str(e)}"
            )

    async def _search_http(
        self,
        query: str,
        search_type: BraveSearchType,
        options: Optional[BraveSearchOptions] = None
    ) -> BraveResponse:
        """Perform search using HTTP API."""
        try:
            # Build query parameters
            params = {"q": query}

            if options:
                params.update({
                    "count": options.count,
                    "offset": options.offset,
                    "freshness": options.freshness.value,
                    "safesearch": options.safe_search.value,
                    "search_lang": options.search_lang,
                    "country": options.country,
                    "extra_snippets": str(options.extra_snippets).lower()
                })

                if options.result_filter:
                    params["result_filter"] = options.result_filter
            else:
                # Default options
                params.update({
                    "count": 10,
                    "offset": 0,
                    "safesearch": "moderate",
                    "search_lang": "en",
                    "country": "US"
                })

            # Choose endpoint based on search type
            endpoint_map = {
                BraveSearchType.WEB: "web/search",
                BraveSearchType.NEWS: "news/search",
                BraveSearchType.IMAGES: "images/search",
                BraveSearchType.VIDEOS: "videos/search"
            }

            endpoint = endpoint_map.get(search_type, "web/search")

            # Make API request
            response = await self.session.get(
                f"{self.config.base_url}/{endpoint}",
                params=params
            )

            response.raise_for_status()
            data = response.json()

            # Parse results based on search type
            results = []
            results_key = "web" if search_type == BraveSearchType.WEB else search_type.value

            if results_key in data and "results" in data[results_key]:
                for result_data in data[results_key]["results"]:
                    result = BraveResult(
                        title=result_data.get("title", ""),
                        url=result_data.get("url", ""),
                        description=result_data.get("description", ""),
                        published=result_data.get("age"),
                        thumbnail=result_data.get("thumbnail", {}).get("src") if result_data.get("thumbnail") else None,
                        language=result_data.get("language"),
                        family_friendly=result_data.get("family_friendly"),
                        type=result_data.get("type"),
                        subtype=result_data.get("subtype"),
                        meta_data=result_data.get("meta_data")
                    )
                    results.append(result)

            # Extract suggestions
            suggestions = []
            if "query" in data and "altered" in data["query"]:
                suggestions.append(data["query"]["altered"])

            return BraveResponse(
                success=True,
                query=query,
                search_type=search_type,
                results=results,
                total_results=data.get(results_key, {}).get("total_count"),
                has_more=data.get(results_key, {}).get("has_more"),
                suggestions=suggestions,
                message=f"{search_type.value.title()} search completed successfully",
                metadata={
                    "spellcheck": data.get("query", {}).get("spellcheck_off"),
                    "location": data.get("query", {}).get("location"),
                    "safesearch": data.get("query", {}).get("safesearch")
                }
            )

        except httpx.HTTPStatusError as e:
            return BraveResponse(
                success=False,
                query=query,
                search_type=search_type,
                error=f"HTTP error {e.response.status_code}: {e.response.text}"
            )
        except Exception as e:
            return BraveResponse(
                success=False,
                query=query,
                search_type=search_type,
                error=f"HTTP search failed: {str(e)}"
            )

    async def batch_search(
        self,
        queries: List[str],
        search_type: BraveSearchType = BraveSearchType.WEB,
        options: Optional[BraveSearchOptions] = None
    ) -> List[BraveResponse]:
        """
        Perform batch search for multiple queries.

        Args:
            queries (List[str]): List of search queries
            search_type (BraveSearchType): Type of search to perform
            options (Optional[BraveSearchOptions]): Search options

        Returns:
            List[BraveResponse]: List of search results
        """
        try:
            tasks = []
            for query in queries:
                if search_type == BraveSearchType.LOCAL:
                    local_options = BraveLocalSearchOptions(
                        count=options.count if options else 5,
                        search_lang=options.search_lang if options else "en",
                        country=options.country if options else "US"
                    )
                    task = self.local_search(query, local_options)
                else:
                    task = self._search_http(query, search_type, options)
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Convert exceptions to error responses
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    error_response = BraveResponse(
                        success=False,
                        query=queries[i],
                        search_type=search_type,
                        error=f"Batch search failed: {str(result)}"
                    )
                    processed_results.append(error_response)
                else:
                    processed_results.append(result)

            return processed_results

        except Exception as e:
            # Return error responses for all queries
            return [
                BraveResponse(
                    success=False,
                    query=query,
                    search_type=search_type,
                    error=f"Batch search failed: {str(e)}"
                )
                for query in queries
            ]

    async def health_check(self) -> Dict[str, Any]:
        """
        Check Brave Search service health and capabilities.

        Returns:
            Dict[str, Any]: Health status and capabilities
        """
        try:
            # Test basic search
            test_result = await self.web_search("test", BraveSearchOptions(count=1))

            capabilities = [
                "web_search",
                "news_search",
                "local_search",
                "image_search",
                "video_search",
                "batch_search",
                "safe_search_filtering",
                "freshness_filtering",
                "location_based_search",
                "multi_language_support",
                "suggestion_generation"
            ]

            return {
                "connected": test_result.success,
                "service": "brave_search",
                "capabilities": capabilities,
                "api_key_configured": bool(self.config.api_key),
                "base_url": self.config.base_url,
                "supported_search_types": [t.value for t in BraveSearchType],
                "supported_languages": ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "zh"],
                "last_test": datetime.now().isoformat(),
                "test_result": test_result.success
            }

        except Exception as e:
            return {
                "connected": False,
                "service": "brave_search",
                "error": str(e),
                "capabilities": [],
                "api_key_configured": bool(self.config.api_key)
            }

    async def get_capabilities(self) -> Dict[str, Any]:
        """
        Get detailed service capabilities.

        Returns:
            Dict[str, Any]: Service capabilities and features
        """
        return {
            "service": "brave_search",
            "provider": "Brave Software",
            "version": "1.0.0",
            "capabilities": {
                "search_types": {
                    "web_search": True,
                    "news_search": True,
                    "local_search": True,
                    "image_search": True,
                    "video_search": True
                },
                "filtering": {
                    "safe_search": True,
                    "freshness_filtering": True,
                    "language_filtering": True,
                    "country_filtering": True,
                    "result_filtering": True
                },
                "advanced_features": {
                    "batch_processing": True,
                    "suggestion_generation": True,
                    "location_based_search": True,
                    "spellcheck": True,
                    "extra_snippets": True
                }
            },
            "mcp_support": {
                "available": True,
                "server": "brave-search",
                "command": "npx -y @modelcontextprotocol/server-brave-search",
                "description": "Production ready MCP server with web, news, and local search capabilities"
            },
            "rate_limits": {
                "requests_per_month": "Varies by plan",
                "concurrent_requests": "Rate limited"
            },
            "authentication": {
                "type": "api_key",
                "required": True
            },
            "supported_countries": ["US", "GB", "CA", "AU", "DE", "FR", "ES", "IT", "NL", "JP"],
            "supported_languages": ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "zh", "ko"],
            "search_limits": {
                "max_count_per_request": 20,
                "max_offset": 9,
                "max_query_length": 400
            }
        }


def create_brave_integration(api_key: Optional[str] = None) -> BraveIntegration:
    """
    Create Brave Search integration instance.

    Args:
        api_key (Optional[str]): Brave Search API key, if not provided uses environment variable

    Returns:
        BraveIntegration: Configured Brave Search integration
    """
    if not api_key:
        api_key = os.getenv("BRAVE_API_KEY")

    if not api_key:
        raise ValueError("Brave Search API key is required")

    config = BraveConfig(api_key=api_key)
    return BraveIntegration(config)


# Export key classes
__all__ = [
    "BraveIntegration",
    "BraveConfig",
    "BraveSearchOptions",
    "BraveLocalSearchOptions",
    "BraveResult",
    "BraveLocalResult",
    "BraveResponse",
    "BraveSearchType",
    "BraveFreshness",
    "BraveSafeSearch",
    "create_brave_integration"
]