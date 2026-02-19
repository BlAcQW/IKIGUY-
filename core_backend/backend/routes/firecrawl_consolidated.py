"""
Firecrawl Consolidated API Routes.

Provides comprehensive endpoints for web scraping and crawling operations
with tenant-specific context and analytics tracking.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from ..services.firecrawl_consolidated_service import get_firecrawl_service
from ..auth import get_current_user_mongo

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../shared"))

from integration.firecrawl import (
    FirecrawlScrapeOptions,
    FirecrawlCrawlOptions,
    FirecrawlFormat
)

router = APIRouter(prefix="/firecrawl", tags=["firecrawl"])


class ScrapeRequest(BaseModel):
    """Request model for single page scraping."""
    url: str = Field(..., description="URL to scrape")
    formats: Optional[List[FirecrawlFormat]] = Field(default=[FirecrawlFormat.MARKDOWN], description="Output formats")
    onlyMainContent: Optional[bool] = Field(default=True, description="Extract only main content")
    removeBase64Images: Optional[bool] = Field(default=True, description="Remove base64 images")
    includeLinks: Optional[bool] = Field(default=False, description="Include links in output")
    excludeTags: Optional[List[str]] = Field(default=None, description="HTML tags to exclude")
    includeTags: Optional[List[str]] = Field(default=None, description="HTML tags to include")
    waitFor: Optional[int] = Field(default=None, description="Wait time in milliseconds")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")


class CrawlRequest(BaseModel):
    """Request model for website crawling."""
    url: str = Field(..., description="Starting URL to crawl")
    limit: Optional[int] = Field(default=100, description="Maximum pages to crawl")
    allowSubdomains: Optional[bool] = Field(default=False, description="Allow crawling subdomains")
    crawlEntireDomain: Optional[bool] = Field(default=False, description="Crawl entire domain")
    ignoreQueryParameters: Optional[bool] = Field(default=True, description="Ignore query parameters")
    maxDepth: Optional[int] = Field(default=3, description="Maximum crawl depth")
    excludePaths: Optional[List[str]] = Field(default=None, description="Paths to exclude")
    includePaths: Optional[List[str]] = Field(default=None, description="Paths to include")
    formats: Optional[List[FirecrawlFormat]] = Field(default=[FirecrawlFormat.MARKDOWN], description="Output formats")
    onlyMainContent: Optional[bool] = Field(default=True, description="Extract only main content")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")


class BatchScrapeRequest(BaseModel):
    """Request model for batch scraping."""
    urls: List[str] = Field(..., description="List of URLs to scrape")
    formats: Optional[List[FirecrawlFormat]] = Field(default=[FirecrawlFormat.MARKDOWN], description="Output formats")
    onlyMainContent: Optional[bool] = Field(default=True, description="Extract only main content")
    removeBase64Images: Optional[bool] = Field(default=True, description="Remove base64 images")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")


class SmartScrapeRequest(BaseModel):
    """Request model for smart scraping with optimized settings."""
    url: str = Field(..., description="URL to scrape")
    extract_type: str = Field(default="content", description="Type of content to extract")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")


class MonitorCrawlRequest(BaseModel):
    """Request model for monitored crawling."""
    url: str = Field(..., description="Starting URL to crawl")
    max_pages: int = Field(default=50, description="Maximum pages to crawl")
    include_subdomains: bool = Field(default=False, description="Whether to include subdomains")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")


class ExtractContentRequest(BaseModel):
    """Request model for content extraction."""
    url: str = Field(..., description="URL to extract content from")
    content_type: str = Field(default="article", description="Type of content to extract")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")


@router.get("/health")
async def health_check():
    """Check Firecrawl service health."""
    try:
        service = await get_firecrawl_service()
        capabilities = await service.get_capabilities()
        return {
            "status": "healthy",
            "service": "firecrawl",
            "capabilities": capabilities,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Firecrawl service unavailable: {str(e)}")


@router.post("/scrape")
async def scrape_url(
    request: ScrapeRequest,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Scrape a single URL with specified options.

    Returns scraped content in requested formats with analytics tracking.
    """
    try:
        service = await get_firecrawl_service()

        options = FirecrawlScrapeOptions(
            formats=request.formats,
            onlyMainContent=request.onlyMainContent,
            removeBase64Images=request.removeBase64Images,
            includeLinks=request.includeLinks,
            excludeTags=request.excludeTags,
            includeTags=request.includeTags,
            waitFor=request.waitFor
        )

        result = await service.scrape_for_tenant(
            tenant_id=current_user.id,
            url=request.url,
            options=options,
            context=request.context
        )

        return result.dict()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")


@router.post("/crawl")
async def crawl_website(
    request: CrawlRequest,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Crawl a website starting from the specified URL.

    Returns crawled content from multiple pages with analytics tracking.
    """
    try:
        service = await get_firecrawl_service()

        crawl_options = FirecrawlCrawlOptions(
            limit=request.limit,
            allowSubdomains=request.allowSubdomains,
            crawlEntireDomain=request.crawlEntireDomain,
            ignoreQueryParameters=request.ignoreQueryParameters,
            maxDepth=request.maxDepth,
            excludePaths=request.excludePaths,
            includePaths=request.includePaths
        )

        scrape_options = FirecrawlScrapeOptions(
            formats=request.formats,
            onlyMainContent=request.onlyMainContent
        )

        result = await service.crawl_for_tenant(
            tenant_id=current_user.id,
            url=request.url,
            crawl_options=crawl_options,
            scrape_options=scrape_options,
            context=request.context
        )

        return result.dict()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Crawling failed: {str(e)}")


@router.post("/batch-scrape")
async def batch_scrape_urls(
    request: BatchScrapeRequest,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Scrape multiple URLs in batch.

    Returns scraped content from all URLs with analytics tracking.
    """
    try:
        service = await get_firecrawl_service()

        options = FirecrawlScrapeOptions(
            formats=request.formats,
            onlyMainContent=request.onlyMainContent,
            removeBase64Images=request.removeBase64Images
        )

        result = await service.batch_scrape_for_tenant(
            tenant_id=current_user.id,
            urls=request.urls,
            options=options,
            context=request.context
        )

        return result.dict()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch scraping failed: {str(e)}")


@router.post("/smart-scrape")
async def smart_scrape_url(
    request: SmartScrapeRequest,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Smart scraping with optimized settings based on extract type.

    Automatically configures scraping options based on content type.
    """
    try:
        service = await get_firecrawl_service()

        result = await service.smart_scrape_for_tenant(
            tenant_id=current_user.id,
            url=request.url,
            extract_type=request.extract_type,
            context=request.context
        )

        return result.dict()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Smart scraping failed: {str(e)}")


@router.post("/monitor-crawl")
async def monitor_crawl_website(
    request: MonitorCrawlRequest,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Monitor and crawl website with reasonable limits.

    Provides controlled crawling with monitoring and limits.
    """
    try:
        service = await get_firecrawl_service()

        result = await service.monitor_crawl_for_tenant(
            tenant_id=current_user.id,
            url=request.url,
            max_pages=request.max_pages,
            include_subdomains=request.include_subdomains,
            context=request.context
        )

        return result.dict()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Monitor crawling failed: {str(e)}")


@router.post("/extract-content")
async def extract_content(
    request: ExtractContentRequest,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Extract structured content optimized for specific content types.

    Returns structured content extraction with metadata.
    """
    try:
        service = await get_firecrawl_service()

        result = await service.extract_content_for_tenant(
            tenant_id=current_user.id,
            url=request.url,
            content_type=request.content_type,
            context=request.context
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content extraction failed: {str(e)}")


@router.get("/analytics/{tenant_id}")
async def get_analytics(
    tenant_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get Firecrawl analytics for a specific tenant.

    Returns usage analytics and metrics for the specified time period.
    """
    try:
        service = await get_firecrawl_service()

        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None

        analytics = await service.get_tenant_analytics(
            tenant_id=tenant_id,
            start_date=start_dt,
            end_date=end_dt
        )

        return analytics

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics retrieval failed: {str(e)}")


@router.get("/usage/{tenant_id}")
async def get_usage_summary(
    tenant_id: str,
    period_days: int = 30,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get usage summary for tenant including credit consumption.

    Returns comprehensive usage metrics and credit tracking.
    """
    try:
        service = await get_firecrawl_service()

        usage = await service.get_tenant_usage_summary(
            tenant_id=tenant_id,
            period_days=period_days
        )

        return usage

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Usage summary retrieval failed: {str(e)}")


@router.get("/capabilities")
async def get_capabilities():
    """
    Get Firecrawl service capabilities.

    Returns available features and configuration options.
    """
    try:
        service = await get_firecrawl_service()
        capabilities = await service.get_capabilities()

        return {
            "service": "firecrawl",
            "capabilities": capabilities,
            "supported_formats": [format.value for format in FirecrawlFormat],
            "features": {
                "single_page_scraping": True,
                "website_crawling": True,
                "batch_scraping": True,
                "smart_scraping": True,
                "monitor_crawling": True,
                "content_extraction": True,
                "analytics_tracking": True,
                "credit_tracking": True,
                "tenant_isolation": True,
                "mcp_support": True
            },
            "limits": {
                "max_crawl_pages": 100,
                "max_batch_urls": 50,
                "max_crawl_depth": 10
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Capabilities retrieval failed: {str(e)}")