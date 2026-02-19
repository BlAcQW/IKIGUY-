"""
Tests for Firecrawl Integration Routes and Services

Tests the web scraping, crawling, and data extraction functionality
with comprehensive validation and error handling.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone
import json

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from backend.routes.firecrawl_consolidated import (
    ScrapeRequest,
    CrawlRequest,
    BatchScrapeRequest,
    SmartScrapeRequest,
    MonitorCrawlRequest,
    ExtractContentRequest,
    router
)

try:
    from backend.services.firecrawl_consolidated_service import get_firecrawl_service
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))
    from integration.firecrawl import (
        FirecrawlConfig,
        FirecrawlScrapeOptions,
        FirecrawlCrawlOptions,
        FirecrawlPage,
        FirecrawlResponse,
        FirecrawlFormat,
        FirecrawlAction,
        FirecrawlIntegration
    )
    FIRECRAWL_IMPORTS_AVAILABLE = True
except ImportError as e:
    FIRECRAWL_IMPORTS_AVAILABLE = False
    print(f"Firecrawl imports not available: {e}")


class TestFirecrawlIntegration:
    """Test suite for Firecrawl integration functionality."""

    @pytest.fixture
    def sample_scrape_request(self):
        """Sample scrape request for testing."""
        return ScrapeRequest(
            url="https://example.com/article",
            formats=[FirecrawlFormat.MARKDOWN, FirecrawlFormat.HTML],
            onlyMainContent=True,
            removeBase64Images=True,
            includeLinks=False,
            excludeTags=["script", "style", "nav"],
            includeTags=["article", "main", "content"],
            waitFor=2000,
            context={"source": "unit_test", "test_id": "scrape_123"}
        )

    @pytest.fixture
    def sample_crawl_request(self):
        """Sample crawl request for testing."""
        return CrawlRequest(
            url="https://example.com",
            limit=50,
            allowSubdomains=False,
            crawlEntireDomain=False,
            ignoreQueryParameters=True,
            maxDepth=3,
            excludePaths=["/admin", "/api", "/private"],
            includePaths=["/blog", "/docs", "/help"],
            formats=[FirecrawlFormat.MARKDOWN],
            onlyMainContent=True,
            context={"source": "unit_test", "crawl_id": "crawl_456"}
        )

    @pytest.fixture
    def sample_batch_scrape_request(self):
        """Sample batch scrape request for testing."""
        return BatchScrapeRequest(
            urls=[
                "https://example.com/page1",
                "https://example.com/page2",
                "https://example.com/page3"
            ],
            formats=[FirecrawlFormat.MARKDOWN, FirecrawlFormat.LINKS],
            onlyMainContent=True,
            removeBase64Images=True,
            context={"source": "unit_test", "batch_id": "batch_789"}
        )

    @pytest.fixture
    def sample_firecrawl_page(self):
        """Sample Firecrawl page for testing."""
        return FirecrawlPage(
            url="https://example.com/article",
            content="# Sample Article\n\nThis is a sample article content...",
            title="Sample Article Title",
            description="This is a sample article for testing purposes",
            markdown="# Sample Article\n\nThis is a sample article content...",
            html="<h1>Sample Article</h1><p>This is a sample article content...</p>",
            screenshot="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
            links=["https://example.com/link1", "https://example.com/link2"],
            metadata={
                "title": "Sample Article Title",
                "description": "This is a sample article for testing purposes",
                "author": "Test Author",
                "publishedDate": "2025-09-22T10:00:00Z",
                "tags": ["test", "sample", "article"]
            },
            status_code=200
        )

    @pytest.fixture
    def sample_firecrawl_response(self, sample_firecrawl_page):
        """Sample Firecrawl response for testing."""
        return FirecrawlResponse(
            success=True,
            data=sample_firecrawl_page,
            job_id="job_123456789",
            status="completed",
            message="Page scraped successfully",
            credits_used=1,
            metadata={
                "processing_time": "2.5s",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

    def test_scrape_request_validation(self):
        """Test ScrapeRequest model validation."""
        # Valid request with all fields
        request = ScrapeRequest(
            url="https://test.com/page",
            formats=[FirecrawlFormat.MARKDOWN, FirecrawlFormat.HTML],
            onlyMainContent=True,
            removeBase64Images=True,
            includeLinks=False,
            excludeTags=["script", "style"],
            includeTags=["article", "main"],
            waitFor=3000,
            context={"test": "data"}
        )

        assert request.url == "https://test.com/page"
        assert FirecrawlFormat.MARKDOWN in request.formats
        assert FirecrawlFormat.HTML in request.formats
        assert request.onlyMainContent is True
        assert request.removeBase64Images is True
        assert request.includeLinks is False
        assert "script" in request.excludeTags
        assert "article" in request.includeTags
        assert request.waitFor == 3000
        assert request.context["test"] == "data"

        # Valid request with minimal fields (only required)
        minimal_request = ScrapeRequest(url="https://minimal.com")
        assert minimal_request.url == "https://minimal.com"
        assert minimal_request.formats == [FirecrawlFormat.MARKDOWN]  # Default value
        assert minimal_request.onlyMainContent is True  # Default value

    def test_crawl_request_validation(self):
        """Test CrawlRequest model validation."""
        request = CrawlRequest(
            url="https://test.com",
            limit=100,
            allowSubdomains=True,
            crawlEntireDomain=False,
            ignoreQueryParameters=False,
            maxDepth=5,
            excludePaths=["/admin", "/private"],
            includePaths=["/public", "/blog"],
            formats=[FirecrawlFormat.MARKDOWN, FirecrawlFormat.LINKS],
            onlyMainContent=False,
            context={"crawl_type": "comprehensive"}
        )

        assert request.url == "https://test.com"
        assert request.limit == 100
        assert request.allowSubdomains is True
        assert request.crawlEntireDomain is False
        assert request.ignoreQueryParameters is False
        assert request.maxDepth == 5
        assert "/admin" in request.excludePaths
        assert "/public" in request.includePaths
        assert FirecrawlFormat.MARKDOWN in request.formats
        assert request.onlyMainContent is False
        assert request.context["crawl_type"] == "comprehensive"

    def test_batch_scrape_request_validation(self):
        """Test BatchScrapeRequest model validation."""
        urls = [
            "https://site1.com/page",
            "https://site2.com/article",
            "https://site3.com/content"
        ]

        request = BatchScrapeRequest(
            urls=urls,
            formats=[FirecrawlFormat.MARKDOWN, FirecrawlFormat.HTML],
            onlyMainContent=True,
            removeBase64Images=False,
            context={"batch_type": "multi_site"}
        )

        assert len(request.urls) == 3
        assert "https://site1.com/page" in request.urls
        assert FirecrawlFormat.MARKDOWN in request.formats
        assert FirecrawlFormat.HTML in request.formats
        assert request.onlyMainContent is True
        assert request.removeBase64Images is False
        assert request.context["batch_type"] == "multi_site"

    def test_smart_scrape_request_validation(self):
        """Test SmartScrapeRequest model validation."""
        request = SmartScrapeRequest(
            url="https://news.com/article",
            extract_type="news_article",
            context={"smart_mode": "auto"}
        )

        assert request.url == "https://news.com/article"
        assert request.extract_type == "news_article"
        assert request.context["smart_mode"] == "auto"

        # Test with default extract_type
        default_request = SmartScrapeRequest(url="https://test.com")
        assert default_request.extract_type == "content"  # Default value

    def test_monitor_crawl_request_validation(self):
        """Test MonitorCrawlRequest model validation."""
        request = MonitorCrawlRequest(
            url="https://monitor.com",
            max_pages=25,
            include_subdomains=True,
            context={"monitor_id": "mon_123"}
        )

        assert request.url == "https://monitor.com"
        assert request.max_pages == 25
        assert request.include_subdomains is True
        assert request.context["monitor_id"] == "mon_123"

        # Test with default values
        default_request = MonitorCrawlRequest(url="https://default.com")
        assert default_request.max_pages == 50  # Default value
        assert default_request.include_subdomains is False  # Default value

    def test_extract_content_request_validation(self):
        """Test ExtractContentRequest model validation."""
        request = ExtractContentRequest(
            url="https://blog.com/post",
            content_type="blog_post",
            context={"extraction_mode": "detailed"}
        )

        assert request.url == "https://blog.com/post"
        assert request.content_type == "blog_post"
        assert request.context["extraction_mode"] == "detailed"

        # Test with default content_type
        default_request = ExtractContentRequest(url="https://test.com")
        assert default_request.content_type == "article"  # Default value

    @pytest.mark.skipif(not FIRECRAWL_IMPORTS_AVAILABLE, reason="Firecrawl integration not available")
    def test_firecrawl_config_validation(self):
        """Test FirecrawlConfig model validation."""
        config = FirecrawlConfig(
            api_key="fc-test_api_key_123",
            base_url="https://api.firecrawl.dev",
            timeout=120,
            max_retries=5
        )

        assert config.api_key == "fc-test_api_key_123"
        assert config.base_url == "https://api.firecrawl.dev"
        assert config.timeout == 120
        assert config.max_retries == 5

    @pytest.mark.skipif(not FIRECRAWL_IMPORTS_AVAILABLE, reason="Firecrawl integration not available")
    def test_firecrawl_scrape_options_validation(self):
        """Test FirecrawlScrapeOptions model validation."""
        options = FirecrawlScrapeOptions(
            formats=[FirecrawlFormat.MARKDOWN, FirecrawlFormat.HTML, FirecrawlFormat.SCREENSHOT],
            onlyMainContent=False,
            includeLinks=True,
            includeTags=["article", "main", "content"],
            excludeTags=["nav", "footer", "aside"],
            waitFor=5000,
            mobile=True,
            removeBase64Images=False
        )

        assert FirecrawlFormat.MARKDOWN in options.formats
        assert FirecrawlFormat.HTML in options.formats
        assert FirecrawlFormat.SCREENSHOT in options.formats
        assert options.onlyMainContent is False
        assert options.includeLinks is True
        assert "article" in options.includeTags
        assert "nav" in options.excludeTags
        assert options.waitFor == 5000
        assert options.mobile is True
        assert options.removeBase64Images is False

    @pytest.mark.skipif(not FIRECRAWL_IMPORTS_AVAILABLE, reason="Firecrawl integration not available")
    def test_firecrawl_crawl_options_validation(self):
        """Test FirecrawlCrawlOptions model validation."""
        options = FirecrawlCrawlOptions(
            limit=200,
            allowSubdomains=True,
            crawlEntireDomain=True,
            excludePaths=["/admin", "/api", "/private"],
            includePaths=["/blog", "/docs"],
            maxDepth=5,
            ignoreQueryParameters=False,
            webhook="https://example.com/webhook"
        )

        assert options.limit == 200
        assert options.allowSubdomains is True
        assert options.crawlEntireDomain is True
        assert "/admin" in options.excludePaths
        assert "/blog" in options.includePaths
        assert options.maxDepth == 5
        assert options.ignoreQueryParameters is False
        assert options.webhook == "https://example.com/webhook"

    @pytest.mark.skipif(not FIRECRAWL_IMPORTS_AVAILABLE, reason="Firecrawl integration not available")
    def test_firecrawl_page_model(self, sample_firecrawl_page):
        """Test FirecrawlPage model."""
        page = sample_firecrawl_page

        assert page.url == "https://example.com/article"
        assert "Sample Article" in page.content
        assert page.title == "Sample Article Title"
        assert "testing purposes" in page.description
        assert page.markdown.startswith("# Sample Article")
        assert page.html.startswith("<h1>Sample Article</h1>")
        assert page.screenshot.startswith("data:image/png;base64")
        assert len(page.links) == 2
        assert page.metadata["author"] == "Test Author"
        assert page.status_code == 200

    @pytest.mark.skipif(not FIRECRAWL_IMPORTS_AVAILABLE, reason="Firecrawl integration not available")
    def test_firecrawl_response_model(self, sample_firecrawl_response):
        """Test FirecrawlResponse model."""
        response = sample_firecrawl_response

        assert response.success is True
        assert isinstance(response.data, FirecrawlPage)
        assert response.job_id == "job_123456789"
        assert response.status == "completed"
        assert "successfully" in response.message
        assert response.credits_used == 1
        assert "processing_time" in response.metadata

    def test_url_validation(self):
        """Test URL validation in requests."""
        # Valid URLs
        valid_urls = [
            "https://example.com",
            "http://test.org/path",
            "https://subdomain.site.co.uk/page?param=value",
            "https://unicode-émojis.com/测试",
            "https://localhost:3000/dev"
        ]

        for url in valid_urls:
            request = ScrapeRequest(url=url)
            assert request.url == url

            crawl_request = CrawlRequest(url=url)
            assert crawl_request.url == url

    def test_format_combinations(self):
        """Test various format combinations."""
        format_combinations = [
            [FirecrawlFormat.MARKDOWN],
            [FirecrawlFormat.HTML],
            [FirecrawlFormat.RAW_HTML],
            [FirecrawlFormat.SCREENSHOT],
            [FirecrawlFormat.LINKS],
            [FirecrawlFormat.SUMMARY],
            [FirecrawlFormat.MARKDOWN, FirecrawlFormat.HTML],
            [FirecrawlFormat.MARKDOWN, FirecrawlFormat.LINKS],
            [FirecrawlFormat.HTML, FirecrawlFormat.SCREENSHOT],
            [FirecrawlFormat.MARKDOWN, FirecrawlFormat.HTML, FirecrawlFormat.LINKS]
        ]

        for formats in format_combinations:
            request = ScrapeRequest(
                url="https://test.com",
                formats=formats
            )
            assert request.formats == formats

    def test_crawl_limits_validation(self):
        """Test crawl limits and depth validation."""
        # Valid limit values
        valid_limits = [1, 10, 50, 100, 500, 1000]

        for limit in valid_limits:
            request = CrawlRequest(
                url="https://test.com",
                limit=limit
            )
            assert request.limit == limit

        # Valid depth values
        valid_depths = [1, 2, 3, 5, 10]

        for depth in valid_depths:
            request = CrawlRequest(
                url="https://test.com",
                maxDepth=depth
            )
            assert request.maxDepth == depth

    def test_path_filtering_validation(self):
        """Test path filtering for crawling."""
        exclude_paths = ["/admin", "/api", "/private", "/internal", "/test"]
        include_paths = ["/blog", "/docs", "/help", "/public", "/articles"]

        request = CrawlRequest(
            url="https://test.com",
            excludePaths=exclude_paths,
            includePaths=include_paths
        )

        assert all(path in request.excludePaths for path in exclude_paths)
        assert all(path in request.includePaths for path in include_paths)

    def test_tag_filtering_validation(self):
        """Test HTML tag filtering."""
        exclude_tags = ["script", "style", "nav", "footer", "aside", "ads"]
        include_tags = ["article", "main", "content", "section", "div", "p"]

        request = ScrapeRequest(
            url="https://test.com",
            excludeTags=exclude_tags,
            includeTags=include_tags
        )

        assert all(tag in request.excludeTags for tag in exclude_tags)
        assert all(tag in request.includeTags for tag in include_tags)

    def test_wait_time_validation(self):
        """Test wait time validation."""
        valid_wait_times = [0, 1000, 2000, 5000, 10000, 30000]

        for wait_time in valid_wait_times:
            request = ScrapeRequest(
                url="https://test.com",
                waitFor=wait_time
            )
            assert request.waitFor == wait_time

    def test_context_data_validation(self):
        """Test context data handling."""
        complex_context = {
            "user_id": "user_123",
            "session_id": "session_456",
            "source": "api_test",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {
                "scrape_type": "comprehensive",
                "priority": "high",
                "department": "data_science"
            },
            "filters": {
                "content_type": "article",
                "language": "en",
                "date_range": "last_month"
            },
            "options": {
                "include_images": True,
                "extract_tables": False,
                "follow_redirects": True
            }
        }

        request = ScrapeRequest(
            url="https://test.com",
            context=complex_context
        )

        assert request.context["user_id"] == "user_123"
        assert request.context["metadata"]["scrape_type"] == "comprehensive"
        assert request.context["filters"]["language"] == "en"
        assert request.context["options"]["include_images"] is True

    @pytest.mark.skipif(not FIRECRAWL_IMPORTS_AVAILABLE, reason="Firecrawl integration not available")
    @pytest.mark.asyncio
    async def test_firecrawl_integration_initialization(self):
        """Test FirecrawlIntegration initialization."""
        config = FirecrawlConfig(
            api_key="fc-test_api_key",
            base_url="https://api.firecrawl.dev",
            timeout=60
        )

        integration = FirecrawlIntegration(config)
        assert integration.config.api_key == "fc-test_api_key"
        assert integration.config.base_url == "https://api.firecrawl.dev"
        assert integration.config.timeout == 60
        assert integration.session is not None

    def test_extract_type_validation(self):
        """Test extract type validation for content extraction."""
        valid_extract_types = [
            "content", "article", "news_article", "blog_post",
            "product_page", "documentation", "forum_post", "recipe"
        ]

        for extract_type in valid_extract_types:
            request = SmartScrapeRequest(
                url="https://test.com",
                extract_type=extract_type
            )
            assert request.extract_type == extract_type

    def test_content_type_validation(self):
        """Test content type validation for extraction."""
        valid_content_types = [
            "article", "blog_post", "news", "documentation",
            "product", "review", "forum", "recipe", "tutorial"
        ]

        for content_type in valid_content_types:
            request = ExtractContentRequest(
                url="https://test.com",
                content_type=content_type
            )
            assert request.content_type == content_type

    def test_boolean_flags_validation(self):
        """Test boolean flag combinations."""
        flag_combinations = [
            (True, True, True, True),     # All flags enabled
            (False, False, False, False), # All flags disabled
            (True, False, True, False),   # Mixed flags
            (False, True, False, True)    # Mixed flags alternate
        ]

        for main_content, base64_images, links, subdomains in flag_combinations:
            scrape_request = ScrapeRequest(
                url="https://test.com",
                onlyMainContent=main_content,
                removeBase64Images=base64_images,
                includeLinks=links
            )

            assert scrape_request.onlyMainContent == main_content
            assert scrape_request.removeBase64Images == base64_images
            assert scrape_request.includeLinks == links

            crawl_request = CrawlRequest(
                url="https://test.com",
                allowSubdomains=subdomains,
                onlyMainContent=main_content
            )

            assert crawl_request.allowSubdomains == subdomains
            assert crawl_request.onlyMainContent == main_content


class TestFirecrawlEdgeCases:
    """Test edge cases and error scenarios for Firecrawl integration."""

    def test_empty_url_list_batch_scrape(self):
        """Test batch scrape with empty URL list."""
        request = BatchScrapeRequest(urls=[])
        assert len(request.urls) == 0

    def test_single_url_batch_scrape(self):
        """Test batch scrape with single URL."""
        request = BatchScrapeRequest(urls=["https://single.com"])
        assert len(request.urls) == 1
        assert request.urls[0] == "https://single.com"

    def test_many_urls_batch_scrape(self):
        """Test batch scrape with many URLs."""
        urls = [f"https://site{i}.com/page" for i in range(100)]
        request = BatchScrapeRequest(urls=urls)
        assert len(request.urls) == 100
        assert all(f"site{i}.com" in url for i, url in enumerate(request.urls))

    def test_duplicate_urls_batch_scrape(self):
        """Test batch scrape with duplicate URLs."""
        urls = [
            "https://example.com",
            "https://test.com",
            "https://example.com",  # Duplicate
            "https://another.com",
            "https://test.com"      # Duplicate
        ]

        request = BatchScrapeRequest(urls=urls)
        assert len(request.urls) == 5  # Duplicates are preserved in request
        assert request.urls.count("https://example.com") == 2

    def test_very_long_url(self):
        """Test scraping with very long URL."""
        long_url = "https://example.com/" + "very-long-path-segment/" * 50 + "final-page"
        request = ScrapeRequest(url=long_url)
        assert request.url == long_url
        assert len(request.url) > 1000

    def test_url_with_special_characters(self):
        """Test URLs with special characters."""
        special_urls = [
            "https://example.com/page?param=value&other=test",
            "https://test.org/path/with spaces",
            "https://unicode.com/中文/测试",
            "https://symbols.com/path/$special#section",
            "https://encoded.com/path%20with%20encoded%20spaces"
        ]

        for url in special_urls:
            request = ScrapeRequest(url=url)
            assert request.url == url

    def test_extreme_crawl_limits(self):
        """Test extreme crawl limit values."""
        extreme_limits = [1, 10000, 50000]  # Very small to very large

        for limit in extreme_limits:
            request = CrawlRequest(
                url="https://test.com",
                limit=limit
            )
            assert request.limit == limit

    def test_extreme_wait_times(self):
        """Test extreme wait time values."""
        extreme_waits = [0, 1, 60000, 300000]  # 0ms to 5 minutes

        for wait_time in extreme_waits:
            request = ScrapeRequest(
                url="https://test.com",
                waitFor=wait_time
            )
            assert request.waitFor == wait_time

    def test_many_tags_filtering(self):
        """Test with many include/exclude tags."""
        many_exclude_tags = [f"tag{i}" for i in range(50)]
        many_include_tags = [f"include{i}" for i in range(30)]

        request = ScrapeRequest(
            url="https://test.com",
            excludeTags=many_exclude_tags,
            includeTags=many_include_tags
        )

        assert len(request.excludeTags) == 50
        assert len(request.includeTags) == 30
        assert "tag0" in request.excludeTags
        assert "include29" in request.includeTags

    def test_many_path_filters(self):
        """Test with many include/exclude paths."""
        many_exclude_paths = [f"/exclude{i}" for i in range(100)]
        many_include_paths = [f"/include{i}" for i in range(75)]

        request = CrawlRequest(
            url="https://test.com",
            excludePaths=many_exclude_paths,
            includePaths=many_include_paths
        )

        assert len(request.excludePaths) == 100
        assert len(request.includePaths) == 75
        assert "/exclude0" in request.excludePaths
        assert "/include74" in request.includePaths

    def test_complex_path_patterns(self):
        """Test complex path patterns for filtering."""
        complex_exclude_paths = [
            "/admin/*",
            "/api/v*/private",
            "/user/*/settings",
            "/internal/**",
            "*.json",
            "*.xml"
        ]

        complex_include_paths = [
            "/blog/**",
            "/docs/*/public",
            "/help/en/*",
            "/content/articles/**"
        ]

        request = CrawlRequest(
            url="https://test.com",
            excludePaths=complex_exclude_paths,
            includePaths=complex_include_paths
        )

        assert "/admin/*" in request.excludePaths
        assert "/blog/**" in request.includePaths
        assert "*.json" in request.excludePaths

    def test_none_optional_fields(self):
        """Test handling of None values in optional fields."""
        request = ScrapeRequest(
            url="https://test.com",
            excludeTags=None,
            includeTags=None,
            waitFor=None,
            context=None
        )

        assert request.excludeTags is None
        assert request.includeTags is None
        assert request.waitFor is None
        assert request.context is None

    @pytest.mark.skipif(not FIRECRAWL_IMPORTS_AVAILABLE, reason="Firecrawl integration not available")
    def test_firecrawl_response_with_errors(self):
        """Test FirecrawlResponse with error scenarios."""
        error_response = FirecrawlResponse(
            success=False,
            error="API rate limit exceeded",
            status="failed",
            message="Request failed due to rate limiting",
            credits_used=0
        )

        assert error_response.success is False
        assert "rate limit" in error_response.error
        assert error_response.status == "failed"
        assert error_response.credits_used == 0

    @pytest.mark.skipif(not FIRECRAWL_IMPORTS_AVAILABLE, reason="Firecrawl integration not available")
    def test_firecrawl_response_partial_success(self):
        """Test FirecrawlResponse with partial success (some pages failed)."""
        # Simulate batch response where some pages succeeded, others failed
        pages = [
            FirecrawlPage(
                url="https://success1.com",
                content="Successfully scraped content",
                status_code=200
            ),
            FirecrawlPage(
                url="https://failed.com",
                content="Error: Page not found",
                status_code=404
            ),
            FirecrawlPage(
                url="https://success2.com",
                content="Another successful scrape",
                status_code=200
            )
        ]

        response = FirecrawlResponse(
            success=True,  # Overall success despite some failures
            data=pages,
            message="Batch completed with 2/3 pages successful",
            credits_used=3
        )

        assert response.success is True
        assert len(response.data) == 3
        assert response.data[0].status_code == 200
        assert response.data[1].status_code == 404
        assert response.credits_used == 3

    @pytest.mark.skipif(not FIRECRAWL_IMPORTS_AVAILABLE, reason="Firecrawl integration not available")
    def test_firecrawl_page_with_minimal_data(self):
        """Test FirecrawlPage with minimal required data."""
        minimal_page = FirecrawlPage(
            url="https://minimal.com",
            content="Minimal content"
        )

        assert minimal_page.url == "https://minimal.com"
        assert minimal_page.content == "Minimal content"
        assert minimal_page.title is None
        assert minimal_page.description is None
        assert minimal_page.metadata is None
        assert minimal_page.status_code is None

    @pytest.mark.skipif(not FIRECRAWL_IMPORTS_AVAILABLE, reason="Firecrawl integration not available")
    def test_firecrawl_action_enum_values(self):
        """Test FirecrawlAction enum values."""
        assert FirecrawlAction.WAIT.value == "wait"
        assert FirecrawlAction.CLICK.value == "click"
        assert FirecrawlAction.SCREENSHOT.value == "screenshot"
        assert FirecrawlAction.WRITE.value == "write"
        assert FirecrawlAction.PRESS.value == "press"
        assert FirecrawlAction.SCROLL.value == "scroll"
        assert FirecrawlAction.SCRAPE.value == "scrape"

    @pytest.mark.skipif(not FIRECRAWL_IMPORTS_AVAILABLE, reason="Firecrawl integration not available")
    def test_firecrawl_format_enum_values(self):
        """Test FirecrawlFormat enum values."""
        assert FirecrawlFormat.MARKDOWN.value == "markdown"
        assert FirecrawlFormat.HTML.value == "html"
        assert FirecrawlFormat.RAW_HTML.value == "rawHtml"
        assert FirecrawlFormat.SCREENSHOT.value == "screenshot"
        assert FirecrawlFormat.LINKS.value == "links"
        assert FirecrawlFormat.SUMMARY.value == "summary"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])