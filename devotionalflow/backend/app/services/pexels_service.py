"""
Pexels API service for searching and retrieving stock photos.
Provides free high-quality images for devotional covers.
"""

import httpx
import logging
from typing import List, Dict, Optional
from app.config import settings

logger = logging.getLogger(__name__)


class PexelsImage:
    """Represents a Pexels image result."""

    def __init__(self, data: dict):
        """
        Initialize from Pexels API response.

        Args:
            data (dict): Image data from Pexels API.
        """
        self.id = data.get("id")
        self.width = data.get("width")
        self.height = data.get("height")
        self.url = data.get("url")  # Pexels page URL
        self.photographer = data.get("photographer")
        self.photographer_url = data.get("photographer_url")
        self.avg_color = data.get("avg_color")
        self.alt = data.get("alt", "")

        # Image source URLs
        src = data.get("src", {})
        self.original = src.get("original")
        self.large2x = src.get("large2x")
        self.large = src.get("large")
        self.medium = src.get("medium")
        self.small = src.get("small")
        self.portrait = src.get("portrait")
        self.landscape = src.get("landscape")
        self.tiny = src.get("tiny")

    def to_dict(self) -> dict:
        """
        Convert to dictionary for API response.

        Returns:
            dict: Image data as dictionary.
        """
        return {
            "id": self.id,
            "width": self.width,
            "height": self.height,
            "url": self.url,
            "photographer": self.photographer,
            "photographer_url": self.photographer_url,
            "avg_color": self.avg_color,
            "alt": self.alt,
            "src": {
                "original": self.original,
                "large2x": self.large2x,
                "large": self.large,
                "medium": self.medium,
                "small": self.small,
                "portrait": self.portrait,
                "landscape": self.landscape,
                "tiny": self.tiny,
            }
        }


async def search_photos(
    query: str,
    per_page: int = 20,
    page: int = 1,
    orientation: Optional[str] = None
) -> Dict:
    """
    Search Pexels for photos matching the query.

    Args:
        query (str): Search query (e.g., "faith", "prayer", "nature").
        per_page (int): Number of results per page (max 80).
        page (int): Page number for pagination.
        orientation (Optional[str]): Filter by orientation ("landscape", "portrait", "square").

    Returns:
        Dict: Search results with photos and pagination info.
            {
                "page": 1,
                "per_page": 20,
                "total_results": 1000,
                "next_page": "https://...",
                "photos": [PexelsImage, ...]
            }

    Raises:
        Exception: If API request fails.
    """
    if not settings.PEXELS_API_KEY:
        logger.error("PEXELS_API_KEY not configured")
        raise ValueError("Pexels API key not configured")

    # Validate per_page
    if per_page > 80:
        per_page = 80
    if per_page < 1:
        per_page = 1

    # Build request URL
    base_url = "https://api.pexels.com/v1/search"
    params = {
        "query": query,
        "per_page": per_page,
        "page": page,
    }

    if orientation:
        params["orientation"] = orientation

    # Make request
    headers = {
        "Authorization": settings.PEXELS_API_KEY
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(base_url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

        # Parse results
        photos = [PexelsImage(photo) for photo in data.get("photos", [])]

        result = {
            "page": data.get("page", page),
            "per_page": data.get("per_page", per_page),
            "total_results": data.get("total_results", 0),
            "next_page": data.get("next_page"),
            "photos": [photo.to_dict() for photo in photos],
        }

        logger.info(f"Pexels search: query='{query}', results={len(photos)}")
        return result

    except httpx.HTTPStatusError as e:
        logger.error(f"Pexels API error: {e.response.status_code} - {e.response.text}")
        raise Exception(f"Pexels API error: {e.response.status_code}")
    except Exception as e:
        logger.error(f"Error searching Pexels: {str(e)}", exc_info=True)
        raise


async def get_curated_photos(per_page: int = 20, page: int = 1) -> Dict:
    """
    Get curated photos from Pexels.
    These are high-quality photos hand-picked by Pexels.

    Args:
        per_page (int): Number of results per page (max 80).
        page (int): Page number for pagination.

    Returns:
        Dict: Curated photos with pagination info.

    Raises:
        Exception: If API request fails.
    """
    if not settings.PEXELS_API_KEY:
        logger.error("PEXELS_API_KEY not configured")
        raise ValueError("Pexels API key not configured")

    # Validate per_page
    if per_page > 80:
        per_page = 80
    if per_page < 1:
        per_page = 1

    # Build request URL
    base_url = "https://api.pexels.com/v1/curated"
    params = {
        "per_page": per_page,
        "page": page,
    }

    headers = {
        "Authorization": settings.PEXELS_API_KEY
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(base_url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

        # Parse results
        photos = [PexelsImage(photo) for photo in data.get("photos", [])]

        result = {
            "page": data.get("page", page),
            "per_page": data.get("per_page", per_page),
            "total_results": data.get("total_results", 0),
            "next_page": data.get("next_page"),
            "photos": [photo.to_dict() for photo in photos],
        }

        logger.info(f"Pexels curated: page={page}, results={len(photos)}")
        return result

    except httpx.HTTPStatusError as e:
        logger.error(f"Pexels API error: {e.response.status_code} - {e.response.text}")
        raise Exception(f"Pexels API error: {e.response.status_code}")
    except Exception as e:
        logger.error(f"Error getting curated photos: {str(e)}", exc_info=True)
        raise


async def get_photo_by_id(photo_id: int) -> Optional[PexelsImage]:
    """
    Get a specific photo by ID from Pexels.

    Args:
        photo_id (int): Pexels photo ID.

    Returns:
        Optional[PexelsImage]: Photo data if found, None otherwise.

    Raises:
        Exception: If API request fails.
    """
    if not settings.PEXELS_API_KEY:
        logger.error("PEXELS_API_KEY not configured")
        raise ValueError("Pexels API key not configured")

    base_url = f"https://api.pexels.com/v1/photos/{photo_id}"
    headers = {
        "Authorization": settings.PEXELS_API_KEY
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(base_url, headers=headers)
            response.raise_for_status()
            data = response.json()

        photo = PexelsImage(data)
        logger.info(f"Retrieved Pexels photo: {photo_id}")
        return photo

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.warning(f"Pexels photo not found: {photo_id}")
            return None
        logger.error(f"Pexels API error: {e.response.status_code} - {e.response.text}")
        raise Exception(f"Pexels API error: {e.response.status_code}")
    except Exception as e:
        logger.error(f"Error getting photo by ID: {str(e)}", exc_info=True)
        raise
