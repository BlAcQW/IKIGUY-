"""
Geocoding API routes for location search and coordinate lookup.

This module provides a backend proxy for OpenStreetMap Nominatim API,
bypassing CORS restrictions and handling required headers.
"""

import asyncio
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Query, HTTPException, status
from pydantic import BaseModel, Field
import httpx
from app.core.config import settings

router = APIRouter(prefix="/geocoding", tags=["geocoding"])

# Rate limiting state
_last_request_time = 0.0
_rate_limit_lock = asyncio.Lock()


class GeocodingResult(BaseModel):
    """
    Geocoding search result model.

    Attributes:
        label: Human-readable address label
        x: Longitude coordinate
        y: Latitude coordinate
        bounds: Bounding box coordinates [[south, west], [north, east]]
        raw: Raw response from Nominatim API
    """
    label: str = Field(..., description="Human-readable address label")
    x: float = Field(..., description="Longitude coordinate")
    y: float = Field(..., description="Latitude coordinate")
    bounds: Optional[List[List[float]]] = Field(None, description="Bounding box [[south, west], [north, east]]")
    raw: Dict[str, Any] = Field(..., description="Raw Nominatim response")


class GeocodingSearchResponse(BaseModel):
    """
    Response model for geocoding search.

    Attributes:
        results: List of geocoding results
        count: Number of results returned
    """
    results: List[GeocodingResult] = Field(..., description="List of geocoding results")
    count: int = Field(..., description="Number of results returned")


async def _respect_rate_limit():
    """
    Ensure we respect Nominatim's rate limit (1 request per second).

    Uses async lock to prevent concurrent requests from violating the rate limit.
    """
    global _last_request_time

    async with _rate_limit_lock:
        current_time = asyncio.get_event_loop().time()
        time_since_last_request = current_time - _last_request_time

        # Reason: OSM requires at least 1 second between requests
        if time_since_last_request < settings.geocoding_rate_limit:
            await asyncio.sleep(settings.geocoding_rate_limit - time_since_last_request)

        _last_request_time = asyncio.get_event_loop().time()


def _format_nominatim_result(raw_result: Dict[str, Any]) -> GeocodingResult:
    """
    Format Nominatim API response to match frontend expectations.

    Args:
        raw_result: Raw result from Nominatim API

    Returns:
        Formatted GeocodingResult object
    """
    # Extract bounding box if available
    bounds = None
    if "boundingbox" in raw_result:
        bbox = raw_result["boundingbox"]
        # Nominatim returns [min_lat, max_lat, min_lon, max_lon]
        # Convert to [[south, west], [north, east]]
        bounds = [
            [float(bbox[0]), float(bbox[2])],  # [south, west]
            [float(bbox[1]), float(bbox[3])]   # [north, east]
        ]

    return GeocodingResult(
        label=raw_result.get("display_name", "Unknown location"),
        x=float(raw_result["lon"]),
        y=float(raw_result["lat"]),
        bounds=bounds,
        raw=raw_result
    )


@router.get(
    "/search",
    response_model=GeocodingSearchResponse,
    summary="Search for location by address",
    description="Forward geocoding: convert address/place name to coordinates using OpenStreetMap Nominatim"
)
async def search_location(
    q: str = Query(..., min_length=3, description="Search query (address, place name, etc.)"),
    countrycodes: Optional[str] = Query("gh", description="Limit results to specific countries (ISO 3166-1 alpha2, comma-separated)"),
    limit: int = Query(5, ge=1, le=20, description="Maximum number of results to return"),
    accept_language: str = Query("en", description="Preferred language for results")
) -> GeocodingSearchResponse:
    """
    Search for a location by address or place name.

    This endpoint proxies requests to OpenStreetMap Nominatim API,
    bypassing CORS restrictions and adding required headers.

    Args:
        q: Search query (e.g., "Accra", "Ridge Road, Accra", etc.)
        countrycodes: Limit to specific countries (default: "gh" for Ghana)
        limit: Maximum number of results (1-20, default: 5)
        accept_language: Preferred language for results (default: "en")

    Returns:
        GeocodingSearchResponse with list of matching locations

    Raises:
        HTTPException: If geocoding service is unavailable or request fails

    Example:
        GET /api/v1/geocoding/search?q=Accra
        GET /api/v1/geocoding/search?q=Ridge%20Road&countrycodes=gh&limit=10
    """
    # Respect rate limit (1 req/sec for Nominatim)
    await _respect_rate_limit()

    # Build request parameters
    params = {
        "q": q,
        "format": "json",
        "addressdetails": 1,
        "limit": limit,
        "accept-language": accept_language,
    }

    if countrycodes:
        params["countrycodes"] = countrycodes

    # Reason: OSM Nominatim requires User-Agent header to identify application
    headers = {
        "User-Agent": f"ChurchFlow/{settings.app_version} ({settings.nominatim_email})",
        "Accept": "application/json"
    }

    try:
        async with httpx.AsyncClient(timeout=settings.geocoding_timeout) as client:
            response = await client.get(
                f"{settings.nominatim_base_url}/search",
                params=params,
                headers=headers
            )
            response.raise_for_status()

            raw_results = response.json()

            # Format results to match frontend expectations
            results = [_format_nominatim_result(result) for result in raw_results]

            return GeocodingSearchResponse(
                results=results,
                count=len(results)
            )

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Geocoding service request timed out"
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Geocoding service returned error: {e.response.status_code}"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to connect to geocoding service: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Geocoding request failed: {str(e)}"
        )


@router.get(
    "/reverse",
    response_model=GeocodingResult,
    summary="Get address from coordinates",
    description="Reverse geocoding: convert latitude/longitude to human-readable address"
)
async def reverse_geocode(
    lat: float = Query(..., ge=-90, le=90, description="Latitude coordinate"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude coordinate"),
    accept_language: str = Query("en", description="Preferred language for results")
) -> GeocodingResult:
    """
    Get human-readable address from GPS coordinates.

    This endpoint proxies requests to OpenStreetMap Nominatim API,
    bypassing CORS restrictions and adding required headers.

    Args:
        lat: Latitude coordinate (-90 to 90)
        lon: Longitude coordinate (-180 to 180)
        accept_language: Preferred language for results (default: "en")

    Returns:
        GeocodingResult with address and location details

    Raises:
        HTTPException: If geocoding service is unavailable or request fails

    Example:
        GET /api/v1/geocoding/reverse?lat=5.6037&lon=-0.1870
    """
    # Respect rate limit (1 req/sec for Nominatim)
    await _respect_rate_limit()

    # Build request parameters
    params = {
        "lat": lat,
        "lon": lon,
        "format": "json",
        "addressdetails": 1,
        "accept-language": accept_language,
    }

    # Reason: OSM Nominatim requires User-Agent header to identify application
    headers = {
        "User-Agent": f"ChurchFlow/{settings.app_version} ({settings.nominatim_email})",
        "Accept": "application/json"
    }

    try:
        async with httpx.AsyncClient(timeout=settings.geocoding_timeout) as client:
            response = await client.get(
                f"{settings.nominatim_base_url}/reverse",
                params=params,
                headers=headers
            )
            response.raise_for_status()

            raw_result = response.json()

            # Format result to match frontend expectations
            return _format_nominatim_result(raw_result)

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Geocoding service request timed out"
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Geocoding service returned error: {e.response.status_code}"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to connect to geocoding service: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reverse geocoding request failed: {str(e)}"
        )
