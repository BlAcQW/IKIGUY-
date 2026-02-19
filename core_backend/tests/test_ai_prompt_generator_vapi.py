"""
Unit tests for the enhanced VAPI system prompt generator with MASTER_TEMPLATE.md integration.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
import sys
import os

# Add the backend directory to Python path
sys.path.append('/opt/kasaai/apps/core_backend')

from backend.routes.ai_prompt_generator import (
    router,
    generate_vapi_optimized_prompt,
    generate_vapi_template_fallback,
    generate_vapi_agent_description,
    VAPISystemPromptGenerate,
    MASTER_TEMPLATE
)
from backend.main import app

# Create test client
client = TestClient(app)


class TestVAPIPromptGenerator:
    """Test suite for VAPI-specific prompt generation."""

    @pytest.fixture
    def sample_website_analysis(self):
        """Sample website analysis data for testing."""
        return {
            "company_info": {
                "name": "TechCorp Solutions",
                "description": "Leading technology consulting firm",
                "full_content": "TechCorp Solutions provides comprehensive technology consulting services..."
            },
            "business_type": "technology consulting",
            "services_products": ["Software Development", "Cloud Migration", "Data Analytics"],
            "tone_style": "professional and innovative",
            "target_audience": "enterprise clients",
            "contact_info": {
                "phone": "+1-555-0123",
                "email": "contact@techcorp.com"
            },
            "key_content": ["innovation", "enterprise", "solutions"]
        }

    @pytest.fixture
    def vapi_request_data(self):
        """Sample VAPI system prompt generation request."""
        return {
            "website_url": "https://techcorp.com",
            "company_name": "TechCorp Solutions",
            "business_type": "technology consulting",
            "language": "en",
            "enable_crawling": True,
            "max_crawl_pages": 3
        }

    def test_master_template_loaded(self):
        """Test that MASTER_TEMPLATE.md is loaded successfully."""
        assert MASTER_TEMPLATE is not None
        assert len(MASTER_TEMPLATE) > 0
        assert "MASTER VAPI PROMPT TEMPLATE" in MASTER_TEMPLATE
        assert "[AGENT_NAME]" in MASTER_TEMPLATE
        assert "[ORGANIZATION_NAME]" in MASTER_TEMPLATE

    def test_generate_vapi_agent_description(self):
        """Test VAPI agent description generation."""
        company_info = {
            "name": "TechCorp Solutions",
            "description": "Leading technology consulting firm specializing in enterprise solutions"
        }
        business_type = "technology consulting"

        description = generate_vapi_agent_description(company_info, business_type)

        assert "TechCorp Solutions" in description
        assert "technology consulting" in description
        assert "VAPI optimization" in description
        assert len(description) > 50

    def test_generate_vapi_template_fallback(self, sample_website_analysis):
        """Test VAPI template fallback generation."""
        additional_context = "Focus on enterprise clients and data privacy"

        prompt = generate_vapi_template_fallback(
            sample_website_analysis,
            additional_context
        )

        assert "TechCorp Solutions" in prompt
        assert "technology consulting" in prompt
        assert additional_context in prompt
        assert len(prompt) > 500

        # Should contain MASTER_TEMPLATE content if available
        if MASTER_TEMPLATE:
            assert "TechCorp Solutions Assistant" in prompt
        else:
            assert "AI voice assistant" in prompt

    @pytest.mark.asyncio
    async def test_generate_vapi_optimized_prompt_template_fallback(self, sample_website_analysis):
        """Test VAPI optimized prompt generation when AI providers fail."""

        # Mock all AI providers to fail
        with patch.dict(os.environ, {}, clear=True):  # Clear all env vars to simulate no API keys
            prompt = await generate_vapi_optimized_prompt(
                website_analysis=sample_website_analysis,
                language="en",
                additional_context="Enterprise focus"
            )

            assert prompt is not None
            assert len(prompt) > 500
            assert "TechCorp Solutions" in prompt

            # Should fall back to template-based generation
            if MASTER_TEMPLATE:
                assert "TechCorp Solutions Assistant" in prompt

    @pytest.mark.asyncio
    async def test_generate_vapi_optimized_prompt_with_openai(self, sample_website_analysis):
        """Test VAPI optimized prompt generation with OpenAI."""

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Generated VAPI system prompt for TechCorp Solutions..."

        with patch('openai.AsyncOpenAI') as mock_openai, \
             patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):

            mock_client = AsyncMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            prompt = await generate_vapi_optimized_prompt(
                website_analysis=sample_website_analysis,
                language="en"
            )

            assert prompt == "Generated VAPI system prompt for TechCorp Solutions..."
            mock_client.chat.completions.create.assert_called_once()

    def test_vapi_system_prompt_request_model_validation(self):
        """Test VAPISystemPromptGenerate model validation."""

        # Valid request
        valid_data = {
            "website_url": "https://example.com",
            "language": "en",
            "company_name": "Test Company"
        }
        request = VAPISystemPromptGenerate(**valid_data)
        assert str(request.website_url) == "https://example.com/"
        assert request.language == "en"
        assert request.company_name == "Test Company"

        # Test defaults
        minimal_data = {"website_url": "https://example.com"}
        request = VAPISystemPromptGenerate(**minimal_data)
        assert request.language == "en"
        assert request.enable_crawling is False
        assert request.max_crawl_pages == 5

    @pytest.mark.asyncio
    async def test_vapi_endpoint_success(self, vapi_request_data):
        """Test VAPI system prompt generation endpoint success."""

        # Mock the website analysis functions
        mock_analysis = {
            "company_info": {
                "name": "TechCorp Solutions",
                "description": "Technology consulting",
                "full_content": "Company content here"
            },
            "business_type": "technology",
            "services_products": ["Consulting"],
            "tone_style": "professional",
            "target_audience": "businesses",
            "contact_info": {},
            "key_content": []
        }

        with patch('backend.routes.ai_prompt_generator._extract_websites_with_priority') as mock_extract, \
             patch('backend.routes.ai_prompt_generator.generate_vapi_optimized_prompt') as mock_generate:

            mock_extract.return_value = mock_analysis
            mock_generate.return_value = "Generated VAPI prompt for TechCorp Solutions..."

            response = client.post(
                "/ai/generate-vapi-system-prompt",
                json=vapi_request_data
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert data["vapi_optimized"] is True
            assert data["master_template_integrated"] is True
            assert "TechCorp Solutions" in data["system_prompt"]
            assert len(data["suggested_description"]) > 0

    @pytest.mark.asyncio
    async def test_vapi_endpoint_minimal_request(self):
        """Test VAPI endpoint with minimal request data."""

        minimal_request = {
            "company_name": "Test Company",
            "business_type": "retail"
        }

        with patch('backend.routes.ai_prompt_generator.generate_vapi_optimized_prompt') as mock_generate:
            mock_generate.return_value = "Generated prompt for Test Company..."

            response = client.post(
                "/ai/generate-vapi-system-prompt",
                json=minimal_request
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert data["vapi_optimized"] is True
            assert "Test Company" in data["analyzed_content"]["company_info"]["name"]

    @pytest.mark.asyncio
    async def test_vapi_endpoint_error_handling(self):
        """Test VAPI endpoint error handling."""

        with patch('backend.routes.ai_prompt_generator.generate_vapi_optimized_prompt') as mock_generate:
            mock_generate.side_effect = Exception("Generation failed")

            response = client.post(
                "/ai/generate-vapi-system-prompt",
                json={"company_name": "Test Company"}
            )

            assert response.status_code == 500
            assert "Failed to generate VAPI system prompt" in response.json()["detail"]

    def test_master_template_integration_completeness(self):
        """Test that MASTER_TEMPLATE integration includes all required sections."""
        if not MASTER_TEMPLATE:
            pytest.skip("MASTER_TEMPLATE not available")

        # Check for key sections that should be in the template
        required_sections = [
            "BASE SYSTEM PROMPT",
            "NO-HALLUCINATION POLICY",
            "TOOL ACCESS INSTRUCTIONS",
            "AVAILABLE TOOLS DOCUMENTATION",
            "ERROR HANDLING & ESCALATION",
            "CONVERSATION FLOW EXAMPLES"
        ]

        for section in required_sections:
            assert section in MASTER_TEMPLATE, f"Missing required section: {section}"

        # Check for placeholder replacement targets
        assert "[AGENT_NAME]" in MASTER_TEMPLATE
        assert "[ORGANIZATION_NAME]" in MASTER_TEMPLATE

    def test_vapi_template_fallback_customization(self, sample_website_analysis):
        """Test that template fallback properly customizes MASTER_TEMPLATE."""
        if not MASTER_TEMPLATE:
            pytest.skip("MASTER_TEMPLATE not available")

        prompt = generate_vapi_template_fallback(
            sample_website_analysis,
            "Custom context about enterprise solutions"
        )

        # Should replace placeholders
        assert "[AGENT_NAME]" not in prompt
        assert "[ORGANIZATION_NAME]" not in prompt

        # Should contain company-specific information
        assert "TechCorp Solutions Assistant" in prompt
        assert "TechCorp Solutions" in prompt
        assert "technology consulting" in prompt
        assert "Custom context about enterprise solutions" in prompt

    @pytest.mark.asyncio
    async def test_concurrent_vapi_prompt_generation(self, sample_website_analysis):
        """Test concurrent VAPI prompt generation."""

        async def generate_prompt():
            return await generate_vapi_optimized_prompt(
                website_analysis=sample_website_analysis,
                language="en"
            )

        # Generate multiple prompts concurrently
        tasks = [generate_prompt() for _ in range(3)]
        results = await asyncio.gather(*tasks)

        # All should succeed
        assert len(results) == 3
        for result in results:
            assert result is not None
            assert len(result) > 500
            assert "TechCorp Solutions" in result


if __name__ == "__main__":
    pytest.main([__file__])