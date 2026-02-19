"""
Web Scraper API Routes

Provides endpoints for web content extraction.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from typing import Optional, List
from pydantic import BaseModel, HttpUrl, Field

from apps.shared.services.web_scraper_service import (
    WebScraperService,
    ScraperConfig,
    ScraperResult,
    get_scraper_service
)
from backend.models.shared_models import StandardResponse


router = APIRouter(prefix="/scraper", tags=["scraper"])


# Request/Response Models
class ExtractRequest(BaseModel):
    """Request to extract content from a URL"""

    url: str = Field(..., description="URL to scrape")
    mode: str = Field(
        default="main-content",
        description="Extraction mode: main-content, full-page, article-body, custom-selector"
    )
    remove_ads: bool = Field(default=True, description="Remove advertisements and popups")
    wait_for_js: bool = Field(default=False, description="Wait for JavaScript to load")
    custom_selector: Optional[str] = Field(default=None, description="Custom CSS selector")
    timeout: int = Field(default=30, description="Request timeout in seconds", ge=5, le=120)


class BatchExtractRequest(BaseModel):
    """Request to extract content from multiple URLs"""

    urls: List[str] = Field(..., description="List of URLs to scrape", min_items=1, max_items=10)
    mode: str = Field(default="main-content", description="Extraction mode")
    remove_ads: bool = Field(default=True, description="Remove advertisements and popups")
    wait_for_js: bool = Field(default=False, description="Wait for JavaScript to load")
    timeout: int = Field(default=30, description="Request timeout in seconds", ge=5, le=120)


class HealthResponse(BaseModel):
    """Scraper service health check response"""

    status: str = Field(..., description="Service status: healthy or unhealthy")
    crawl4ai_url: str = Field(..., description="Crawl4AI service URL")
    response_time_ms: Optional[float] = Field(default=None, description="Response time in milliseconds")
    error: Optional[str] = Field(default=None, description="Error message if unhealthy")


# Dependency to get scraper service
async def get_web_scraper_service() -> WebScraperService:
    """Get the web scraper service instance"""
    return get_scraper_service()


# Routes
@router.post("/extract", response_model=StandardResponse[ScraperResult])
async def extract_content(
    request_data: ExtractRequest,
    scraper_service: WebScraperService = Depends(get_web_scraper_service)
):
    """
    Extract content from a web page.

    **Parameters:**
    - **url**: URL to scrape (required)
    - **mode**: Extraction mode - one of:
        - `main-content`: Extract main content only (default)
        - `full-page`: Extract all text from the page
        - `article-body`: Extract article body content
        - `custom-selector`: Use custom CSS selector
    - **remove_ads**: Remove advertisements and popups (default: true)
    - **wait_for_js**: Wait for JavaScript to load (default: false)
    - **custom_selector**: CSS selector when mode is 'custom-selector'
    - **timeout**: Request timeout in seconds (5-120, default: 30)

    **Returns:**
    - Extracted content with metadata (word count, character count, extraction time)

    **Example:**
    ```json
    {
        "url": "https://example.com/article",
        "mode": "main-content",
        "remove_ads": true,
        "wait_for_js": false,
        "timeout": 30
    }
    ```
    """
    try:
        # Create scraper config
        config = ScraperConfig(
            mode=request_data.mode,
            remove_ads=request_data.remove_ads,
            wait_for_js=request_data.wait_for_js,
            custom_selector=request_data.custom_selector,
            timeout=request_data.timeout
        )

        # Extract content
        result = await scraper_service.extract_content(
            url=request_data.url,
            config=config
        )

        return StandardResponse(
            success=True,
            data=result,
            message="Content extracted successfully"
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Extraction failed: {str(e)}"
        )


@router.post("/extract/batch", response_model=StandardResponse[List[ScraperResult]])
async def extract_batch(
    request_data: BatchExtractRequest,
    scraper_service: WebScraperService = Depends(get_web_scraper_service)
):
    """
    Extract content from multiple URLs concurrently.

    **Parameters:**
    - **urls**: List of URLs to scrape (1-10 URLs)
    - **mode**: Extraction mode (applies to all URLs)
    - **remove_ads**: Remove advertisements (applies to all URLs)
    - **wait_for_js**: Wait for JavaScript (applies to all URLs)
    - **timeout**: Request timeout in seconds (applies to all URLs)

    **Returns:**
    - List of extracted content results

    **Note:**
    - Failed extractions will be skipped
    - Check the result count to see if all URLs were successful

    **Example:**
    ```json
    {
        "urls": [
            "https://example.com/article1",
            "https://example.com/article2"
        ],
        "mode": "main-content",
        "remove_ads": true,
        "wait_for_js": false,
        "timeout": 30
    }
    ```
    """
    try:
        # Create scraper config
        config = ScraperConfig(
            mode=request_data.mode,
            remove_ads=request_data.remove_ads,
            wait_for_js=request_data.wait_for_js,
            timeout=request_data.timeout
        )

        # Extract content from all URLs
        results = await scraper_service.extract_batch(
            urls=request_data.urls,
            config=config
        )

        # Calculate success rate
        success_count = len(results)
        total_count = len(request_data.urls)

        message = f"Extracted {success_count}/{total_count} URLs successfully"

        return StandardResponse(
            success=True,
            data=results,
            message=message
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch extraction failed: {str(e)}"
        )


@router.get("/health", response_model=StandardResponse[HealthResponse])
async def check_health(
    scraper_service: WebScraperService = Depends(get_web_scraper_service)
):
    """
    Check the health of the web scraper service.

    **Returns:**
    - Service health status
    - Crawl4AI URL
    - Response time (if healthy)
    - Error message (if unhealthy)

    **Example Response:**
    ```json
    {
        "success": true,
        "data": {
            "status": "healthy",
            "crawl4ai_url": "https://crawl4ai.ailabsafrica.com",
            "response_time_ms": 45.2
        },
        "message": "Scraper service is healthy"
    }
    ```
    """
    try:
        health_status = await scraper_service.check_health()

        is_healthy = health_status["status"] == "healthy"
        message = "Scraper service is healthy" if is_healthy else "Scraper service is unhealthy"

        return StandardResponse(
            success=is_healthy,
            data=HealthResponse(**health_status),
            message=message
        )

    except Exception as e:
        return StandardResponse(
            success=False,
            data=HealthResponse(
                status="unhealthy",
                crawl4ai_url="unknown",
                error=str(e)
            ),
            message="Failed to check scraper service health"
        )


@router.get("/modes")
async def get_extraction_modes():
    """
    Get available extraction modes and their descriptions.

    **Returns:**
    - List of available extraction modes with descriptions

    **Example Response:**
    ```json
    {
        "success": true,
        "data": {
            "modes": [
                {
                    "id": "main-content",
                    "name": "Main Content Only",
                    "description": "Extract the main content area, removing navigation, ads, and sidebars"
                },
                ...
            ]
        },
        "message": "Available extraction modes"
    }
    ```
    """
    modes = [
        {
            "id": "main-content",
            "name": "Main Content Only",
            "description": "Extract the main content area, removing navigation, ads, and sidebars",
            "recommended_for": ["articles", "blog posts", "news"]
        },
        {
            "id": "full-page",
            "name": "Full Page Text",
            "description": "Extract all text content from the page",
            "recommended_for": ["documentation", "reference pages", "wikis"]
        },
        {
            "id": "article-body",
            "name": "Article Body",
            "description": "Extract article body content using semantic HTML detection",
            "recommended_for": ["news articles", "blog posts", "publications"]
        },
        {
            "id": "custom-selector",
            "name": "Custom Selector",
            "description": "Use a custom CSS selector to extract specific content",
            "recommended_for": ["specific elements", "structured data", "custom layouts"]
        }
    ]

    return StandardResponse(
        success=True,
        data={"modes": modes},
        message="Available extraction modes"
    )


@router.get("/info")
async def get_scraper_info():
    """
    Get information about the web scraper service.

    **Returns:**
    - Service capabilities
    - Supported features
    - Usage limits

    **Example Response:**
    ```json
    {
        "success": true,
        "data": {
            "name": "Web Content Scraper",
            "version": "1.0.0",
            "capabilities": [...],
            "limits": {...}
        },
        "message": "Scraper service information"
    }
    ```
    """
    info = {
        "name": "Web Content Scraper",
        "version": "1.0.0",
        "powered_by": "Crawl4AI",
        "capabilities": [
            "Main content extraction",
            "Full page text extraction",
            "Article body detection",
            "Custom CSS selector support",
            "JavaScript rendering",
            "Advertisement removal",
            "Link extraction",
            "Image extraction",
            "Batch processing"
        ],
        "limits": {
            "max_timeout_seconds": 120,
            "min_timeout_seconds": 5,
            "max_batch_size": 10,
            "default_timeout": 30
        },
        "features": {
            "javascript_rendering": True,
            "ad_removal": True,
            "custom_selectors": True,
            "batch_extraction": True,
            "metadata_extraction": True
        }
    }

    return StandardResponse(
        success=True,
        data=info,
        message="Scraper service information"
    )
