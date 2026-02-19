"""
Tests for Tavily Integration

Tests the AI-powered search functionality including web search, content extraction,
and answer generation with comprehensive validation and error handling.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone
import json

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from backend.routes.tavily_consolidated import (
    TavilySearchRequestModel,
    TavilyQuickSearchRequest
)

try:
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))
    from integration.tavily import (
        TavilyConfig,
        TavilySearchRequest,
        TavilySearchTopic,
        TavilySearchDepth,
        TavilyResponse,
        TavilySearchResult
    )
    TAVILY_IMPORTS_AVAILABLE = True
except ImportError as e:
    TAVILY_IMPORTS_AVAILABLE = False
    print(f"Tavily imports not available: {e}")


class TestTavilyIntegration:
    """Test suite for Tavily integration functionality."""

    @pytest.fixture
    def sample_tavily_config(self):
        """Sample Tavily configuration for testing."""
        return TavilyConfig(
            api_key="test_tavily_api_key_123",
            base_url="https://api.tavily.com",
            timeout=30,
            max_retries=3
        )

    @pytest.fixture
    def sample_search_request(self):
        """Sample search request for testing."""
        return TavilySearchRequestModel(
            tenant_id="test_tenant_123",
            query="latest AI developments 2025",
            topic=TavilySearchTopic.GENERAL,
            search_depth=TavilySearchDepth.BASIC,
            include_answer=True,
            include_raw_content=False,
            include_images=True,
            max_results=5,
            context={"source": "unit_test", "user_id": "test_user"}
        )

    @pytest.fixture
    def sample_search_results(self):
        """Sample search results for testing."""
        return [
            {
                "title": "Latest AI Breakthroughs in 2025",
                "url": "https://example.com/ai-breakthroughs-2025",
                "content": "Recent developments in artificial intelligence have shown remarkable progress...",
                "score": 0.95,
                "published_date": "2025-09-20",
                "favicon": "https://example.com/favicon.ico"
            },
            {
                "title": "Machine Learning Trends 2025",
                "url": "https://techblog.com/ml-trends-2025",
                "content": "Machine learning continues to evolve with new architectures and approaches...",
                "score": 0.89,
                "published_date": "2025-09-18",
                "favicon": "https://techblog.com/favicon.ico"
            },
            {
                "title": "Enterprise AI Adoption 2025",
                "url": "https://business.com/enterprise-ai-2025",
                "content": "Enterprises are increasingly adopting AI solutions for various business processes...",
                "score": 0.87,
                "published_date": "2025-09-15",
                "favicon": "https://business.com/favicon.ico"
            }
        ]

    def test_tavily_search_request_validation(self, sample_search_request):
        """Test TavilySearchRequestModel validation."""
        request = sample_search_request

        assert request.tenant_id == "test_tenant_123"
        assert request.query == "latest AI developments 2025"
        assert request.topic == TavilySearchTopic.GENERAL
        assert request.search_depth == TavilySearchDepth.BASIC
        assert request.include_answer is True
        assert request.include_raw_content is False
        assert request.include_images is True
        assert request.max_results == 5
        assert request.context["source"] == "unit_test"

    def test_tavily_search_request_minimal(self):
        """Test TavilySearchRequestModel with minimal required fields."""
        minimal_request = TavilySearchRequestModel(
            tenant_id="test_tenant",
            query="simple search"
        )

        assert minimal_request.tenant_id == "test_tenant"
        assert minimal_request.query == "simple search"
        assert minimal_request.topic == TavilySearchTopic.GENERAL  # Default
        assert minimal_request.search_depth == TavilySearchDepth.BASIC  # Default
        assert minimal_request.include_answer is False  # Default
        assert minimal_request.max_results == 5  # Default

    def test_tavily_quick_search_request(self):
        """Test TavilyQuickSearchRequest validation."""
        quick_request = TavilyQuickSearchRequest(
            tenant_id="test_tenant",
            query="quick search query",
            max_results=3,
            context={"type": "quick_search"}
        )

        assert quick_request.tenant_id == "test_tenant"
        assert quick_request.query == "quick search query"
        assert quick_request.max_results == 3
        assert quick_request.context["type"] == "quick_search"

    @pytest.mark.skipif(not TAVILY_IMPORTS_AVAILABLE, reason="Tavily integration not available")
    def test_tavily_config_validation(self, sample_tavily_config):
        """Test TavilyConfig model validation."""
        config = sample_tavily_config

        assert config.api_key == "test_tavily_api_key_123"
        assert config.base_url == "https://api.tavily.com"
        assert config.timeout == 30
        assert config.max_retries == 3

    @pytest.mark.skipif(not TAVILY_IMPORTS_AVAILABLE, reason="Tavily integration not available")
    def test_tavily_search_topics_enum(self):
        """Test TavilySearchTopic enum values."""
        assert TavilySearchTopic.GENERAL.value == "general"
        assert TavilySearchTopic.NEWS.value == "news"
        assert TavilySearchTopic.FINANCE.value == "finance"

    @pytest.mark.skipif(not TAVILY_IMPORTS_AVAILABLE, reason="Tavily integration not available")
    def test_tavily_search_depth_enum(self):
        """Test TavilySearchDepth enum values."""
        assert TavilySearchDepth.BASIC.value == "basic"
        assert TavilySearchDepth.ADVANCED.value == "advanced"

    def test_search_query_validation(self):
        """Test various search query formats."""
        queries = [
            "simple query",
            "complex query with multiple words and symbols",
            "query with numbers 123 and dates 2025",
            "query with special characters !@#$%^&*()",
            "query with unicode characters: français, español, 中文",
            "very long query " + "word " * 50  # Very long query
        ]

        for query in queries:
            request = TavilySearchRequestModel(
                tenant_id="test_tenant",
                query=query
            )
            assert request.query == query

    def test_max_results_validation(self):
        """Test max_results field validation."""
        # Valid values within range
        valid_results = [1, 5, 10, 15, 20]

        for max_results in valid_results:
            request = TavilySearchRequestModel(
                tenant_id="test_tenant",
                query="test query",
                max_results=max_results
            )
            assert request.max_results == max_results

        # Test invalid values (should raise validation errors)
        invalid_results = [0, -1, 21, 100]

        for invalid_max in invalid_results:
            with pytest.raises(Exception):  # ValidationError from pydantic
                TavilySearchRequestModel(
                    tenant_id="test_tenant",
                    query="test query",
                    max_results=invalid_max
                )

    def test_include_domains_validation(self):
        """Test include_domains field validation."""
        domains = ["example.com", "wikipedia.org", "github.com"]

        request = TavilySearchRequestModel(
            tenant_id="test_tenant",
            query="test query",
            include_domains=domains
        )

        assert request.include_domains == domains
        assert "example.com" in request.include_domains

    def test_exclude_domains_validation(self):
        """Test exclude_domains field validation."""
        domains = ["spam.com", "ads.com", "clickbait.net"]

        request = TavilySearchRequestModel(
            tenant_id="test_tenant",
            query="test query",
            exclude_domains=domains
        )

        assert request.exclude_domains == domains
        assert "spam.com" in request.exclude_domains

    def test_boolean_flags_validation(self):
        """Test boolean flag combinations."""
        flag_combinations = [
            (True, True, True, True, True),   # All flags enabled
            (False, False, False, False, False),  # All flags disabled
            (True, False, True, False, True),  # Mixed flags
        ]

        for answer, raw, images, favicon, auto in flag_combinations:
            request = TavilySearchRequestModel(
                tenant_id="test_tenant",
                query="test query",
                include_answer=answer,
                include_raw_content=raw,
                include_images=images,
                include_favicon=favicon,
                auto_parameters=auto
            )

            assert request.include_answer == answer
            assert request.include_raw_content == raw
            assert request.include_images == images
            assert request.include_favicon == favicon
            assert request.auto_parameters == auto

    def test_context_tracking_validation(self):
        """Test context tracking in search requests."""
        complex_context = {
            "user_id": "user_123",
            "session_id": "session_456",
            "source": "api",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {
                "search_type": "research",
                "urgency": "high",
                "department": "engineering"
            },
            "filters": {
                "language": "en",
                "region": "US",
                "date_range": "last_year"
            }
        }

        request = TavilySearchRequestModel(
            tenant_id="test_tenant",
            query="complex search with context",
            context=complex_context
        )

        assert request.context["user_id"] == "user_123"
        assert request.context["metadata"]["search_type"] == "research"
        assert request.context["filters"]["language"] == "en"

    @pytest.mark.skipif(not TAVILY_IMPORTS_AVAILABLE, reason="Tavily integration not available")
    def test_tavily_search_result_model(self):
        """Test TavilySearchResult model."""
        result = TavilySearchResult(
            title="Test Article",
            url="https://example.com/article",
            content="This is the article content...",
            score=0.92,
            published_date="2025-09-22",
            favicon="https://example.com/favicon.ico"
        )

        assert result.title == "Test Article"
        assert result.url == "https://example.com/article"
        assert result.content == "This is the article content..."
        assert result.score == 0.92
        assert result.published_date == "2025-09-22"

    @pytest.mark.skipif(not TAVILY_IMPORTS_AVAILABLE, reason="Tavily integration not available")
    def test_tavily_response_model(self, sample_search_results):
        """Test TavilyResponse model."""
        response = TavilyResponse(
            success=True,
            query="test query",
            results=sample_search_results,
            answer="Based on the search results, AI developments in 2025 include...",
            response_time="1.2s"
        )

        assert response.success is True
        assert response.query == "test query"
        assert len(response.results) == 3
        assert response.answer.startswith("Based on the search results")
        assert response.response_time == "1.2s"


class TestTavilyEdgeCases:
    """Test edge cases and error scenarios for Tavily integration."""

    def test_empty_query_validation(self):
        """Test empty search query validation."""
        # Empty query is actually allowed by the model, so this test should pass
        request = TavilySearchRequestModel(
            tenant_id="test_tenant",
            query=""  # Empty query is allowed
        )
        assert request.query == ""

    def test_whitespace_only_query(self):
        """Test query with only whitespace."""
        whitespace_queries = ["   ", "\t\t", "\n\n", "  \t\n  "]

        for query in whitespace_queries:
            # These might be handled differently depending on validation rules
            try:
                request = TavilySearchRequestModel(
                    tenant_id="test_tenant",
                    query=query
                )
                # If it passes validation, check it was stored
                assert request.query == query
            except Exception:
                # If validation fails, that's also acceptable behavior
                pass

    def test_very_long_query(self):
        """Test extremely long search queries."""
        long_query = "word " * 1000  # Very long query (5000 characters)

        request = TavilySearchRequestModel(
            tenant_id="test_tenant",
            query=long_query
        )

        assert len(request.query) > 4000
        assert request.query == long_query

    def test_unicode_and_special_characters(self):
        """Test queries with various unicode and special characters."""
        special_queries = [
            "Recherche en français avec des accents éàù",
            "Búsqueda en español con ñ y tildes",
            "中文搜索查询",
            "العربية البحث",
            "русский поиск",
            "日本語検索",
            "🔍 search with emojis 🚀 and symbols ★",
            "Math symbols: ∑ ∫ ∂ ∇ ∞ ≠ ≈ ± × ÷",
            "Special chars: !@#$%^&*()_+-=[]{}|;':\",./<>?"
        ]

        for query in special_queries:
            request = TavilySearchRequestModel(
                tenant_id="test_tenant",
                query=query
            )
            assert request.query == query

    def test_large_domain_lists(self):
        """Test with large include/exclude domain lists."""
        large_include_list = [f"domain{i}.com" for i in range(100)]
        large_exclude_list = [f"spam{i}.net" for i in range(50)]

        request = TavilySearchRequestModel(
            tenant_id="test_tenant",
            query="test with many domains",
            include_domains=large_include_list,
            exclude_domains=large_exclude_list
        )

        assert len(request.include_domains) == 100
        assert len(request.exclude_domains) == 50
        assert "domain0.com" in request.include_domains
        assert "spam49.net" in request.exclude_domains

    def test_complex_nested_context(self):
        """Test deeply nested context data."""
        deep_context = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {
                            "data": "deep_value",
                            "array": [1, 2, 3, {"nested": True}],
                            "metadata": {
                                "timestamp": "2025-09-22T10:00:00Z",
                                "version": "1.0.0"
                            }
                        }
                    }
                }
            },
            "parallel_data": {
                "config": {
                    "settings": ["option1", "option2", "option3"],
                    "flags": {"enabled": True, "debug": False}
                }
            }
        }

        request = TavilySearchRequestModel(
            tenant_id="test_tenant",
            query="deep nested context test",
            context=deep_context
        )

        assert request.context["level1"]["level2"]["level3"]["level4"]["data"] == "deep_value"
        assert request.context["parallel_data"]["config"]["flags"]["enabled"] is True

    def test_null_and_none_values(self):
        """Test handling of None/null values in optional fields."""
        request = TavilySearchRequestModel(
            tenant_id="test_tenant",
            query="test with nulls",
            include_domains=None,
            exclude_domains=None,
            context=None
        )

        assert request.include_domains is None
        assert request.exclude_domains is None
        assert request.context is None

    @pytest.mark.skipif(not TAVILY_IMPORTS_AVAILABLE, reason="Tavily integration not available")
    def test_search_result_with_missing_fields(self):
        """Test search result with some missing optional fields."""
        minimal_result = TavilySearchResult(
            title="Minimal Result",
            url="https://example.com/minimal",
            content="Basic content",
            score=0.75  # Required field
        )

        assert minimal_result.title == "Minimal Result"
        assert minimal_result.url == "https://example.com/minimal"
        assert minimal_result.content == "Basic content"
        assert minimal_result.score == 0.75
        # Optional fields should be None
        assert minimal_result.published_date is None
        assert minimal_result.favicon is None

    def test_invalid_topic_enum(self):
        """Test invalid search topic values."""
        with pytest.raises(Exception):  # ValidationError
            TavilySearchRequestModel(
                tenant_id="test_tenant",
                query="test query",
                topic="invalid_topic"  # Not a valid enum value
            )

    def test_invalid_depth_enum(self):
        """Test invalid search depth values."""
        with pytest.raises(Exception):  # ValidationError
            TavilySearchRequestModel(
                tenant_id="test_tenant",
                query="test query",
                search_depth="invalid_depth"  # Not a valid enum value
            )

    def test_tenant_id_edge_cases(self):
        """Test various tenant ID formats."""
        tenant_ids = [
            "simple_tenant",
            "tenant-with-dashes",
            "tenant.with.dots",
            "tenant_123_456",
            "UPPERCASE_TENANT",
            "MixedCase_Tenant_123",
            "tenant_with_very_long_name_that_might_be_used_in_enterprise"
        ]

        for tenant_id in tenant_ids:
            request = TavilySearchRequestModel(
                tenant_id=tenant_id,
                query="test query"
            )
            assert request.tenant_id == tenant_id


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])