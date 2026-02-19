"""
Unit tests for Firecrawl and AI extraction integration with AI prompt generator.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.routes.ai_prompt_generator import (
    _extract_company_name_from_content,
    _analyze_business_type_from_content,
    _extract_services_from_content,
    _extract_contact_from_content,
    _extract_key_content_from_text,
    _analyze_tone_from_content,
    _analyze_audience_from_content,
    _process_single_page,
    _process_crawled_pages,
    analyze_website_content_firecrawl,
    analyze_multiple_websites_firecrawl,
    analyze_website_content_ai,
    analyze_multiple_websites_ai,
    _extract_content_with_ai,
    _parse_ai_extraction_response,
    _fallback_rule_based_extraction,
    _extract_websites_with_priority
)


class TestContentProcessingFunctions:
    """Test content processing helper functions."""

    def test_extract_company_name_from_title(self):
        """Test company name extraction from title."""
        title = "Acme Corp - Software Solutions"
        content = "Some content"
        result = _extract_company_name_from_content(title, content)
        assert result == "Acme Corp - Software Solutions"

    def test_extract_company_name_with_suffix_removal(self):
        """Test company name extraction with suffix removal."""
        title = "TechCorp | Home"
        content = "Welcome to TechCorp"
        result = _extract_company_name_from_content(title, content)
        assert result == "TechCorp"

    def test_extract_company_name_from_content_fallback(self):
        """Test company name extraction from content when title is empty."""
        title = ""
        content = "Innovative Solutions Inc\nWelcome to our website"
        result = _extract_company_name_from_content(title, content)
        assert result == "Innovative Solutions Inc"

    def test_analyze_business_type_technology(self):
        """Test business type analysis for technology companies."""
        content = "We develop software applications and digital platforms using modern tech"
        result = _analyze_business_type_from_content(content)
        assert result == "technology"

    def test_analyze_business_type_healthcare(self):
        """Test business type analysis for healthcare companies."""
        content = "Our medical clinic provides health services to patients"
        result = _analyze_business_type_from_content(content)
        assert result == "healthcare"

    def test_analyze_business_type_education(self):
        """Test business type analysis for education companies."""
        content = "Our university offers courses and learning programs for students"
        result = _analyze_business_type_from_content(content)
        assert result == "education"

    def test_extract_services_from_content(self):
        """Test service extraction from content."""
        content = """
        Our Services:
        - Professional consulting services for businesses
        - Software development solutions
        - Product design and development
        """
        result = _extract_services_from_content(content)
        assert len(result) >= 1
        assert any("consulting services" in service.lower() for service in result)

    def test_extract_contact_email(self):
        """Test email extraction from content."""
        content = "Contact us at info@example.com for more information"
        result = _extract_contact_from_content(content)
        assert result.get("email") == "info@example.com"

    def test_extract_contact_phone_us_format(self):
        """Test US phone number extraction."""
        content = "Call us at (555) 123-4567 for support"
        result = _extract_contact_from_content(content)
        assert result.get("phone") == "(555) 123-4567"

    def test_extract_contact_phone_international(self):
        """Test international phone number extraction."""
        content = "Call us at +1-555-123-4567 for support"
        result = _extract_contact_from_content(content)
        # The regex captures the phone number, but may not include all parts
        assert result.get("phone") in ["1-555-123-4567", "555-123-4567", "+1-555-123-4567"]

    def test_extract_key_content(self):
        """Test key content extraction."""
        content = """
        Welcome to our site
        About our company: We are a leading provider of innovative solutions
        Our mission is to deliver excellence in everything we do
        Contact us for more information
        """
        result = _extract_key_content_from_text(content)
        assert len(result) >= 1
        assert any("about" in content.lower() or "mission" in content.lower() for content in result)

    def test_analyze_tone_professional(self):
        """Test professional tone analysis."""
        content = "Our professional corporate solutions for enterprise business needs"
        result = _analyze_tone_from_content(content)
        assert result == "professional"

    def test_analyze_tone_friendly(self):
        """Test friendly tone analysis."""
        content = "We're a fun and creative team with innovative exciting ideas"
        result = _analyze_tone_from_content(content)
        assert result == "friendly"

    def test_analyze_tone_supportive(self):
        """Test supportive tone analysis."""
        content = "We care about our community and provide compassionate support"
        result = _analyze_tone_from_content(content)
        assert result == "supportive"

    def test_analyze_audience_business(self):
        """Test business audience analysis."""
        content = "Enterprise solutions for corporate business clients"
        result = _analyze_audience_from_content(content)
        assert result == "business"

    def test_analyze_audience_consumer(self):
        """Test consumer audience analysis."""
        content = "Personal solutions for individual customers and consumers"
        result = _analyze_audience_from_content(content)
        assert result == "consumer"


class TestFirecrawlPageProcessing:
    """Test Firecrawl page processing functions."""

    def test_process_single_page(self):
        """Test processing a single Firecrawl page."""
        # Mock Firecrawl page object
        mock_page = MagicMock()
        mock_page.title = "Test Company - Home"
        mock_page.description = "We are a test company"
        mock_page.content = "Test Company provides software solutions"
        mock_page.markdown = "# Test Company\nSoftware solutions"
        mock_page.metadata = {"title": "Test Company", "description": "Test description"}

        result = _process_single_page(mock_page, "https://test.com")

        assert result["url"] == "https://test.com"
        assert result["title"] == "Test Company - Home"
        assert "Test Company" in result["company_info"]["name"]
        assert result["business_type"] == "technology"  # Should detect "software"
        assert result["extraction_method"] == "firecrawl_single"

    def test_process_crawled_pages(self):
        """Test processing multiple crawled pages."""
        # Mock multiple Firecrawl page objects
        mock_page1 = MagicMock()
        mock_page1.url = "https://test.com"
        mock_page1.title = "Test Company"
        mock_page1.description = "Main page"
        mock_page1.content = "Test Company main content"
        mock_page1.markdown = "# Test Company"
        mock_page1.metadata = {}

        mock_page2 = MagicMock()
        mock_page2.url = "https://test.com/about"
        mock_page2.title = "About Us"
        mock_page2.description = "About page"
        mock_page2.content = "About Test Company - we provide services"
        mock_page2.markdown = "# About Us"
        mock_page2.metadata = {}

        pages = [mock_page1, mock_page2]
        result = _process_crawled_pages(pages, "https://test.com")

        assert result["url"] == "https://test.com"
        assert result["pages_crawled"] == 2
        assert result["extraction_method"] == "firecrawl_crawl"
        assert len(result["crawled_urls"]) == 2
        assert "Page 1:" in result["company_info"]["full_content"]
        assert "Page 2:" in result["company_info"]["full_content"]


class TestFirecrawlIntegration:
    """Test Firecrawl integration functions."""

    @pytest.mark.asyncio
    @patch('backend.services.firecrawl_consolidated_service.get_firecrawl_service')
    async def test_analyze_website_content_firecrawl_single_page(self, mock_get_service):
        """Test single page analysis with Firecrawl."""
        # Mock Firecrawl service
        mock_service = AsyncMock()
        mock_get_service.return_value = mock_service

        # Mock successful response
        mock_page = MagicMock()
        mock_page.title = "Test Company"
        mock_page.content = "Test Company provides software solutions"
        mock_page.metadata = {}

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.data = mock_page

        mock_service.smart_scrape_for_tenant.return_value = mock_result

        result = await analyze_website_content_firecrawl(
            website_url="https://test.com",
            enable_crawling=False,
            max_crawl_pages=1
        )

        assert result["url"] == "https://test.com"
        assert result["extraction_method"] == "firecrawl_single"
        mock_service.smart_scrape_for_tenant.assert_called_once()

    @pytest.mark.asyncio
    @patch('backend.services.firecrawl_consolidated_service.get_firecrawl_service')
    async def test_analyze_website_content_firecrawl_crawling(self, mock_get_service):
        """Test website crawling with Firecrawl."""
        # Mock Firecrawl service
        mock_service = AsyncMock()
        mock_get_service.return_value = mock_service

        # Mock successful crawling response
        mock_page1 = MagicMock()
        mock_page1.url = "https://test.com"
        mock_page1.content = "Test Company main page"
        mock_page1.metadata = {}

        mock_page2 = MagicMock()
        mock_page2.url = "https://test.com/about"
        mock_page2.content = "About Test Company"
        mock_page2.metadata = {}

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.data = [mock_page1, mock_page2]

        mock_service.monitor_crawl_for_tenant.return_value = mock_result

        result = await analyze_website_content_firecrawl(
            website_url="https://test.com",
            enable_crawling=True,
            max_crawl_pages=5
        )

        assert result["url"] == "https://test.com"
        assert result["extraction_method"] == "firecrawl_crawl"
        assert result["pages_crawled"] == 2
        mock_service.monitor_crawl_for_tenant.assert_called_once()

    @pytest.mark.asyncio
    @patch('backend.services.firecrawl_consolidated_service.get_firecrawl_service')
    async def test_analyze_multiple_websites_firecrawl_batch(self, mock_get_service):
        """Test batch website analysis with Firecrawl."""
        # Mock Firecrawl service
        mock_service = AsyncMock()
        mock_get_service.return_value = mock_service

        # Mock successful batch response
        mock_page1 = MagicMock()
        mock_page1.content = "Test Company 1 content"
        mock_page1.title = "Test Company 1"
        mock_page1.description = "Test company 1 description"
        mock_page1.metadata = {}

        mock_page2 = MagicMock()
        mock_page2.content = "Test Company 2 content"
        mock_page2.title = "Test Company 2"
        mock_page2.description = "Test company 2 description"
        mock_page2.metadata = {}

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.data = [mock_page1, mock_page2]

        mock_service.batch_scrape_for_tenant.return_value = mock_result

        urls = ["https://test1.com", "https://test2.com"]
        result = await analyze_multiple_websites_firecrawl(
            urls=urls,
            enable_crawling=False
        )

        assert result["extraction_method"] == "firecrawl_batch"
        assert len(result["urls"]) == 2
        mock_service.batch_scrape_for_tenant.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_website_content_firecrawl_error_handling(self):
        """Test error handling in Firecrawl analysis."""
        with patch('backend.services.firecrawl_consolidated_service.get_firecrawl_service') as mock_get_service:
            mock_get_service.side_effect = Exception("Firecrawl service unavailable")

            with pytest.raises(Exception) as exc_info:
                await analyze_website_content_firecrawl("https://test.com")

            assert "Firecrawl service unavailable" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_analyze_multiple_websites_empty_urls(self):
        """Test handling of empty URL list."""
        result = await analyze_multiple_websites_firecrawl([])

        assert result["urls"] == []
        assert result["extraction_method"] == "firecrawl_batch"
        assert result["company_info"]["name"] == ""


class TestAIExtraction:
    """Test AI-powered content extraction functions."""

    def test_parse_ai_extraction_response_valid_json(self):
        """Test parsing valid AI response JSON."""
        ai_response = '''
        {
            "company_name": "Test Corp",
            "title": "Test Title",
            "business_type": "technology",
            "services_products": ["Software", "Consulting"],
            "contact_info": {"email": "test@example.com"}
        }
        '''
        result = _parse_ai_extraction_response(ai_response)

        assert result["company_name"] == "Test Corp"
        assert result["title"] == "Test Title"
        assert result["business_type"] == "technology"
        assert "Software" in result["services_products"]
        assert result["contact_info"]["email"] == "test@example.com"

    def test_parse_ai_extraction_response_with_defaults(self):
        """Test parsing AI response with missing fields filled by defaults."""
        ai_response = '{"company_name": "Test Corp"}'
        result = _parse_ai_extraction_response(ai_response)

        assert result["company_name"] == "Test Corp"
        assert result["business_type"] == "general"
        assert result["services_products"] == []
        assert result["tone_style"] == "professional"

    def test_parse_ai_extraction_response_invalid_json(self):
        """Test handling of invalid JSON response."""
        ai_response = "This is not valid JSON"

        with pytest.raises(Exception) as exc_info:
            _parse_ai_extraction_response(ai_response)

        assert "Failed to parse AI response" in str(exc_info.value)

    def test_fallback_rule_based_extraction(self):
        """Test rule-based extraction fallback."""
        raw_content = """Test Company
        We are a technology company providing software solutions.
        Contact us at info@test.com or (555) 123-4567.
        Our mission is to innovate and serve our customers."""

        result = _fallback_rule_based_extraction(raw_content, "https://test.com")

        assert result["company_name"] == "Test Company"
        assert result["business_type"] == "technology"
        assert result["contact_info"]["email"] == "info@test.com"
        assert result["contact_info"]["phone"] == "(555) 123-4567"

    @pytest.mark.asyncio
    @patch('backend.routes.ai_prompt_generator.openai.AsyncOpenAI')
    async def test_extract_content_with_ai_openai_success(self, mock_openai):
        """Test successful AI content extraction using OpenAI."""
        # Mock OpenAI client and response
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices[0].message.content = '''
        {
            "company_name": "AI Test Corp",
            "business_type": "technology",
            "description": "AI-powered testing company"
        }
        '''
        mock_client.chat.completions.create.return_value = mock_response

        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            result = await _extract_content_with_ai(
                "Test content for AI analysis",
                "https://test.com",
                "openai"
            )

        assert result["company_name"] == "AI Test Corp"
        assert result["business_type"] == "technology"
        mock_client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_content_with_ai_fallback_to_rule_based(self):
        """Test AI extraction fallback to rule-based when no API keys available."""
        with patch.dict('os.environ', {}, clear=True):
            # No API keys set, should fallback to rule-based extraction
            # Format content like a real webpage with title as first line
            content = """Acme Corporation
Our company specializes in technology solutions.
We provide software development services."""

            result = await _extract_content_with_ai(
                content,
                "https://test.com",
                "gemini"
            )

        # Should return rule-based extraction with detected company name
        assert "company_name" in result
        assert "business_type" in result
        # Rule-based should extract "Acme Corporation" from the first line
        assert "Acme" in result["company_name"]

    @pytest.mark.asyncio
    @patch('backend.services.firecrawl_consolidated_service.get_firecrawl_service')
    async def test_analyze_website_content_ai_with_firecrawl_content(self, mock_get_service):
        """Test AI analysis using Firecrawl for content extraction."""
        # Mock Firecrawl service
        mock_service = AsyncMock()
        mock_get_service.return_value = mock_service

        mock_page = MagicMock()
        mock_page.content = "AI Firecrawl Test Company\nWe are a technology company that provides AI solutions and web scraping services.\nContact us for more information about our innovative products."
        mock_page.markdown = ""

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.data = mock_page

        mock_service.smart_scrape_for_tenant.return_value = mock_result

        # Mock AI extraction
        with patch('backend.routes.ai_prompt_generator._extract_content_with_ai') as mock_ai:
            mock_ai.return_value = {
                "company_name": "AI Firecrawl Test",
                "business_type": "technology",
                "description": "Test description",
                "services_products": ["AI", "Web Scraping"],
                "contact_info": {},
                "key_content": [],
                "tone_style": "professional",
                "target_audience": "business",
                "mission": "",
                "values": []
            }

            result = await analyze_website_content_ai(
                "https://test.com",
                ai_provider="openai"
            )

        assert result["url"] == "https://test.com"
        assert result["company_info"]["name"] == "AI Firecrawl Test"
        assert result["extraction_method"] == "ai_extraction_firecrawl"
        assert result["ai_provider_used"] == "openai"

    @pytest.mark.asyncio
    async def test_extract_websites_with_priority_ai_first(self):
        """Test priority-based extraction with AI first."""
        urls = ["https://test.com"]

        with patch('backend.routes.ai_prompt_generator.analyze_website_content_ai') as mock_ai:
            mock_ai.return_value = {
                "url": "https://test.com",
                "extraction_method": "ai_extraction",
                "ai_provider_used": "openai",
                "company_info": {"name": "AI First Test"},
                "business_type": "technology"
            }

            result = await _extract_websites_with_priority(
                urls=urls,
                extraction_priority="ai_first",
                use_ai_extraction=True,
                use_firecrawl=True,
                ai_extraction_provider="openai"
            )

        assert result["extraction_method"] == "ai_extraction"
        assert result["ai_provider_used"] == "openai"
        mock_ai.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_websites_with_priority_fallback_to_basic(self):
        """Test priority-based extraction fallback to basic when others fail."""
        urls = ["https://test.com"]

        with patch('backend.routes.ai_prompt_generator.analyze_website_content_ai') as mock_ai, \
             patch('backend.routes.ai_prompt_generator.analyze_website_content_firecrawl') as mock_firecrawl, \
             patch('backend.routes.ai_prompt_generator.analyze_website_content') as mock_basic:

            # Make AI and Firecrawl fail
            mock_ai.side_effect = Exception("AI failed")
            mock_firecrawl.side_effect = Exception("Firecrawl failed")

            # Mock basic analysis success
            mock_basic.return_value = {
                "url": "https://test.com",
                "extraction_method": "basic",
                "company_info": {"name": "Basic Fallback Test"}
            }

            result = await _extract_websites_with_priority(
                urls=urls,
                extraction_priority="ai_first",
                use_ai_extraction=True,
                use_firecrawl=True
            )

        assert result["extraction_method"] == "basic"
        mock_basic.assert_called_once()

    @pytest.mark.asyncio
    async def test_ai_only_extraction_mode(self):
        """Test AI-only extraction mode without fallbacks."""
        urls = ["https://test.com"]

        with patch('backend.routes.ai_prompt_generator.analyze_website_content_ai') as mock_ai:
            mock_ai.return_value = {
                "url": "https://test.com",
                "extraction_method": "ai_extraction",
                "ai_provider_used": "gemini",
                "company_info": {"name": "AI Only Test"}
            }

            result = await _extract_websites_with_priority(
                urls=urls,
                extraction_priority="ai_only",
                use_ai_extraction=True,
                ai_extraction_provider="gemini"
            )

        assert result["extraction_method"] == "ai_extraction"
        assert result["ai_provider_used"] == "gemini"
        mock_ai.assert_called_once()

    @pytest.mark.asyncio
    async def test_firecrawl_only_extraction_mode(self):
        """Test Firecrawl-only extraction mode without AI."""
        urls = ["https://test.com"]

        with patch('backend.routes.ai_prompt_generator.analyze_website_content_firecrawl') as mock_firecrawl:
            mock_firecrawl.return_value = {
                "url": "https://test.com",
                "extraction_method": "firecrawl",
                "company_info": {"name": "Firecrawl Only Test"}
            }

            result = await _extract_websites_with_priority(
                urls=urls,
                extraction_priority="firecrawl_only",
                use_firecrawl=True
            )

        assert result["extraction_method"] == "firecrawl"
        mock_firecrawl.assert_called_once()

    @pytest.mark.asyncio
    async def test_ai_extraction_with_invalid_provider(self):
        """Test AI extraction with invalid provider falls back to rule-based."""
        content = """TechCorp Industries
We are a manufacturing company that produces widgets.
Our manufacturing facility is located in Detroit."""

        result = await _extract_content_with_ai(
            content,
            "https://test.com",
            "invalid_provider"
        )

        # Should return rule-based extraction
        assert "company_name" in result
        assert "business_type" in result
        # Rule-based should detect company name from first line
        assert "TechCorp" in result["company_name"]

    @pytest.mark.asyncio
    async def test_rule_based_extraction_fallback(self):
        """Test that rule-based extraction works when AI providers fail."""
        # Test without any environment variables for AI providers
        with patch.dict('os.environ', {}, clear=True):
            content = """Software Solutions Inc
We are a software development company specializing in enterprise solutions.
Contact us at info@acme.com or call 555-1234.
Our services include custom software development."""

            result = await _extract_content_with_ai(
                content,
                "https://acme.com",
                "openai"
            )

        # Should return rule-based extraction results
        assert "company_name" in result
        assert "business_type" in result
        assert "contact_info" in result
        # Rule-based extraction should detect company name from title
        assert "Software Solutions" in result["company_name"]

    @pytest.mark.asyncio
    async def test_ai_extraction_with_crawling_enabled(self):
        """Test AI extraction combined with website crawling."""
        with patch('backend.services.firecrawl_consolidated_service.get_firecrawl_service') as mock_get_service, \
             patch('backend.routes.ai_prompt_generator._extract_content_with_ai') as mock_ai:

            # Mock Firecrawl service for crawling
            mock_service = AsyncMock()
            mock_get_service.return_value = mock_service

            mock_page1 = MagicMock()
            mock_page1.content = "Page 1 content"
            mock_page1.url = "https://example.com/page1"

            mock_page2 = MagicMock()
            mock_page2.content = "Page 2 content"
            mock_page2.url = "https://example.com/page2"

            mock_result = MagicMock()
            mock_result.success = True
            mock_result.data = [mock_page1, mock_page2]

            mock_service.monitor_crawl_for_tenant.return_value = mock_result

            # Mock AI extraction
            mock_ai.return_value = {
                "company_name": "Crawled Company",
                "business_type": "technology",
                "description": "AI analyzed content from multiple pages"
            }

            result = await analyze_website_content_ai(
                "https://example.com",
                ai_provider="openai",
                enable_crawling=True,
                max_crawl_pages=3
            )

        assert result["url"] == "https://example.com"
        assert result["company_info"]["name"] == "Crawled Company"
        assert result["extraction_method"] == "ai_extraction_firecrawl_crawl"
        mock_service.monitor_crawl_for_tenant.assert_called_once()
        mock_ai.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])