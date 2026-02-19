"""
Author Image Search Service.

Dynamically searches for author images using web search APIs.
Returns external URLs - no local storage.
"""

import logging
import httpx
import asyncio
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import os
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)


class AuthorImageResult(BaseModel):
    """Result from author image search."""

    query: str = Field(..., description="Search query used")
    image_urls: List[str] = Field(default_factory=list, description="Direct image URLs found")
    source_pages: List[str] = Field(default_factory=list, description="Source page URLs")
    thumbnail_urls: List[str] = Field(default_factory=list, description="Thumbnail URLs")
    primary_image_url: Optional[str] = Field(None, description="Best/primary image URL")
    status: str = Field("success", description="Search status")
    message: Optional[str] = Field(None, description="Additional message")


class AuthorImageSearchService:
    """
    Service for searching author images dynamically.

    Uses Brave Search API to find publicly available author images.
    Returns external URLs for dynamic loading - no local storage.
    """

    def __init__(self):
        """Initialize the author image search service."""
        self.brave_api_key = os.getenv("BRAVE_API_KEY")
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        self.timeout = 30.0

        # Brave Search API endpoints
        self.brave_image_url = "https://api.search.brave.com/res/v1/images/search"
        self.brave_web_url = "https://api.search.brave.com/res/v1/web/search"

        # Tavily API endpoint
        self.tavily_url = "https://api.tavily.com/search"

    async def search_author_image(
        self,
        author_name: str,
        context: Optional[str] = None,
        max_results: int = 5
    ) -> AuthorImageResult:
        """
        Search for author images dynamically.

        Searches across multiple sources to find the best author image.
        Returns external URLs for dynamic display.

        Args:
            author_name: Name of the author to search for
            context: Additional context (e.g., "book author", "religious leader")
            max_results: Maximum number of image URLs to return

        Returns:
            AuthorImageResult with image URLs and metadata
        """
        if not author_name or not author_name.strip():
            return AuthorImageResult(
                query="",
                status="error",
                message="Author name is required"
            )

        # Build search query
        search_queries = self._build_search_queries(author_name, context)

        # Try multiple search strategies
        all_results = []

        # Strategy 1: Brave Image Search (primary)
        if self.brave_api_key:
            for query in search_queries[:2]:  # Try top 2 queries
                try:
                    brave_results = await self._search_brave_images(query, max_results)
                    all_results.extend(brave_results)
                except Exception as e:
                    logger.warning(f"Brave image search failed for '{query}': {e}")

        # Strategy 2: Brave Web Search for author pages (fallback)
        if not all_results and self.brave_api_key:
            try:
                web_results = await self._search_brave_web(author_name, context)
                all_results.extend(web_results)
            except Exception as e:
                logger.warning(f"Brave web search failed: {e}")

        # Strategy 3: Tavily Search (secondary fallback)
        if not all_results and self.tavily_api_key:
            try:
                tavily_results = await self._search_tavily(author_name, context)
                all_results.extend(tavily_results)
            except Exception as e:
                logger.warning(f"Tavily search failed: {e}")

        # Deduplicate and rank results
        unique_images = self._deduplicate_and_rank(all_results)

        if not unique_images:
            return AuthorImageResult(
                query=author_name,
                status="not_found",
                message="No valid images found for this author"
            )

        # Select primary image (highest quality/most relevant)
        primary_image = unique_images[0]["url"] if unique_images else None

        return AuthorImageResult(
            query=author_name,
            image_urls=[img["url"] for img in unique_images[:max_results]],
            source_pages=[img.get("source", "") for img in unique_images[:max_results]],
            thumbnail_urls=[img.get("thumbnail", img["url"]) for img in unique_images[:max_results]],
            primary_image_url=primary_image,
            status="success"
        )

    def _build_search_queries(self, author_name: str, context: Optional[str] = None) -> List[str]:
        """
        Build optimized search queries for author images.

        Args:
            author_name: Author's name
            context: Additional context

        Returns:
            List of search queries to try
        """
        queries = []

        # Primary query with author name
        if context:
            queries.append(f"{author_name} {context} photo")
        queries.append(f"{author_name} author photo")
        queries.append(f"{author_name} official portrait")
        queries.append(f"{author_name} headshot")

        # Amazon author page (often has official photos)
        queries.append(f"{author_name} Amazon author")

        # Wikipedia (usually has verified images)
        queries.append(f"{author_name} Wikipedia")

        return queries

    async def _search_brave_images(
        self,
        query: str,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for images using Brave Image Search API.

        Args:
            query: Search query
            max_results: Maximum results to return

        Returns:
            List of image result dicts
        """
        if not self.brave_api_key:
            return []

        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.brave_api_key
        }

        params = {
            "q": query,
            "count": max_results,
            "safesearch": "moderate",
            "search_lang": "en",
            "country": "us"
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                self.brave_image_url,
                headers=headers,
                params=params
            )

            if response.status_code != 200:
                logger.warning(f"Brave image search returned {response.status_code}")
                return []

            data = response.json()
            results = []

            for item in data.get("results", []):
                # Get the best available image URL
                image_url = item.get("properties", {}).get("url") or item.get("url")
                thumbnail_url = item.get("thumbnail", {}).get("src") or image_url
                source_url = item.get("source") or item.get("page_fetched")

                if image_url and self._is_valid_image_url(image_url):
                    results.append({
                        "url": image_url,
                        "thumbnail": thumbnail_url,
                        "source": source_url,
                        "title": item.get("title", ""),
                        "width": item.get("properties", {}).get("width", 0),
                        "height": item.get("properties", {}).get("height", 0)
                    })

            logger.info(f"Brave image search found {len(results)} results for '{query}'")
            return results

    async def _search_brave_web(
        self,
        author_name: str,
        context: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search Brave Web for author pages that might have images.

        Targets Amazon author pages, Wikipedia, official websites.

        Args:
            author_name: Author name
            context: Additional context

        Returns:
            List of image URLs from web pages
        """
        if not self.brave_api_key:
            return []

        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.brave_api_key
        }

        # Search for author profile pages
        query = f"{author_name} author photo site:amazon.com OR site:wikipedia.org"

        params = {
            "q": query,
            "count": 10,
            "search_lang": "en",
            "country": "us"
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                self.brave_web_url,
                headers=headers,
                params=params
            )

            if response.status_code != 200:
                return []

            data = response.json()
            results = []

            # Extract images from web results
            for item in data.get("web", {}).get("results", []):
                # Check for thumbnail images
                if "thumbnail" in item:
                    thumbnail_url = item["thumbnail"].get("src")
                    if thumbnail_url and self._is_valid_image_url(thumbnail_url):
                        results.append({
                            "url": thumbnail_url,
                            "thumbnail": thumbnail_url,
                            "source": item.get("url", ""),
                            "title": item.get("title", "")
                        })

                # Check for profile image
                if "profile" in item and "img" in item["profile"]:
                    img_url = item["profile"]["img"]
                    if self._is_valid_image_url(img_url):
                        results.append({
                            "url": img_url,
                            "thumbnail": img_url,
                            "source": item.get("url", ""),
                            "title": item.get("title", "")
                        })

            return results

    async def _search_tavily(
        self,
        author_name: str,
        context: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search using Tavily API as fallback.

        Args:
            author_name: Author name
            context: Additional context

        Returns:
            List of image URLs
        """
        if not self.tavily_api_key:
            return []

        query = f"{author_name} author official photo portrait"
        if context:
            query = f"{author_name} {context} photo"

        payload = {
            "api_key": self.tavily_api_key,
            "query": query,
            "search_depth": "basic",
            "include_images": True,
            "include_answer": False,
            "max_results": 10
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.tavily_url,
                json=payload
            )

            if response.status_code != 200:
                return []

            data = response.json()
            results = []

            # Get images from Tavily response
            for img_url in data.get("images", []):
                if self._is_valid_image_url(img_url):
                    results.append({
                        "url": img_url,
                        "thumbnail": img_url,
                        "source": "",
                        "title": ""
                    })

            return results

    def _is_valid_image_url(self, url: str) -> bool:
        """
        Validate that a URL is a valid image URL.

        Args:
            url: URL to validate

        Returns:
            True if valid image URL
        """
        if not url or not url.startswith(("http://", "https://")):
            return False

        # Check for common image extensions
        image_extensions = (".jpg", ".jpeg", ".png", ".webp", ".gif")
        url_lower = url.lower().split("?")[0]  # Remove query params

        # Allow URLs that look like image URLs or CDN URLs
        if any(url_lower.endswith(ext) for ext in image_extensions):
            return True

        # Allow common image CDN patterns
        image_cdn_patterns = [
            "images.amazon.com",
            "upload.wikimedia.org",
            "gravatar.com",
            "googleusercontent.com",
            "cloudinary.com",
            "imgix.net",
            "githubusercontent.com",
            "twimg.com",
            "fbcdn.net"
        ]

        return any(pattern in url_lower for pattern in image_cdn_patterns)

    def _deduplicate_and_rank(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Deduplicate results and rank by quality/relevance.

        Args:
            results: Raw search results

        Returns:
            Deduplicated and ranked results
        """
        seen_urls = set()
        unique_results = []

        for result in results:
            url = result.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)

                # Calculate a simple quality score
                score = 0

                # Prefer larger images
                width = result.get("width", 0)
                height = result.get("height", 0)
                if width >= 400 and height >= 400:
                    score += 30
                elif width >= 200 and height >= 200:
                    score += 20
                elif width > 0 and height > 0:
                    score += 10

                # Prefer certain sources
                source = result.get("source", "").lower()
                if "amazon.com" in source:
                    score += 25  # Amazon author pages are usually high quality
                elif "wikipedia.org" in source:
                    score += 20  # Wikipedia images are verified
                elif "official" in source or "author" in source:
                    score += 15

                # Prefer HTTPS
                if url.startswith("https://"):
                    score += 5

                result["score"] = score
                unique_results.append(result)

        # Sort by score descending
        unique_results.sort(key=lambda x: x.get("score", 0), reverse=True)

        return unique_results

    async def get_author_image_for_book_upload(
        self,
        author_name: str,
        book_context: Optional[str] = None
    ) -> Optional[str]:
        """
        Convenience method for book upload flow.

        Returns the best single image URL for an author.

        Args:
            author_name: Author's name
            book_context: Book/genre context for better results

        Returns:
            Primary image URL or None
        """
        result = await self.search_author_image(
            author_name=author_name,
            context=book_context,
            max_results=3
        )

        return result.primary_image_url


# Global service instance
author_image_service = AuthorImageSearchService()


async def get_author_image_service() -> AuthorImageSearchService:
    """
    Get the author image search service instance.

    Returns:
        AuthorImageSearchService instance
    """
    return author_image_service
