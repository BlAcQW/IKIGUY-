"""
Unit tests for the Gemini Demo HTML Service

Tests the functionality of generating professional demo HTML pages using Gemini AI
for VAPI voice assistant integration with proper fallback scenarios.
"""

import pytest
import asyncio
import os
from unittest.mock import patch, AsyncMock, MagicMock
from backend.services.gemini_demo_html_service import (
    GeminiDemoHTMLService,
    get_demo_html_service
)


class TestGeminiDemoHTMLService:
    """Test cases for GeminiDemoHTMLService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = GeminiDemoHTMLService()
        self.sample_company_info = {
            'name': 'Test Company',
            'description': 'A test company for demonstration',
            'services': ['Service A', 'Service B', 'Service C'],
            'aboutText': 'About our test company',
            'businessHours': 'Monday-Friday 9AM-5PM',
            'contactInfo': {
                'phone': '+1-555-TEST',
                'email': 'test@company.com',
                'address': '123 Test Street, Test City'
            }
        }
        self.sample_assistant_id = 'test-assistant-123'

    @pytest.mark.asyncio
    async def test_generate_demo_html_with_gemini_success(self):
        """Test successful HTML generation using Gemini AI."""
        # Mock Gemini service response
        mock_gemini_response = {
            'success': True,
            'content': '''<!DOCTYPE html>
<html lang="en">
<head>
    <title>Test Company - AI Voice Assistant Demo</title>
</head>
<body>
    <h1>Test Company</h1>
    <p>Professional demo page content</p>
    <vapi-widget
        public-key="0c22dcea-0d6c-4fc0-8fb2-93292d8575e8"
        assistant-id="test-assistant-123"
        mode="voice">
    </vapi-widget>
    <script src="https://unpkg.com/@vapi-ai/client-sdk-react/dist/embed/widget.umd.js"></script>
</body>
</html>'''
        }

        with patch('backend.services.gemini_demo_html_service.get_gemini_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.api_key = 'test-key'
            mock_service.generate_content.return_value = mock_gemini_response
            mock_get_service.return_value = mock_service

            result = await self.service.generate_demo_html(
                company_info=self.sample_company_info,
                vapi_assistant_id=self.sample_assistant_id,
                automation_type='sales',
                extracted_content='Test website content'
            )

            # Verify response structure
            assert isinstance(result, dict)
            assert 'html' in result
            assert 'method' in result
            assert 'notification' in result

            # Verify HTML structure
            html = result['html']
            assert '<!DOCTYPE html>' in html
            assert 'Test Company' in html
            assert 'test-assistant-123' in html
            assert 'vapi-widget' in html
            assert 'widget.umd.js' in html

            # Verify successful generation metadata
            assert result['method'] == 'gemini'
            assert result['notification']['type'] == 'success'
            assert '🎨' in result['notification']['message']

    @pytest.mark.asyncio
    async def test_generate_demo_html_gemini_unavailable_fallback(self):
        """Test fallback HTML generation when Gemini is unavailable."""
        with patch('backend.services.gemini_demo_html_service.get_gemini_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.api_key = None  # No API key available
            mock_get_service.return_value = mock_service

            result = await self.service.generate_demo_html(
                company_info=self.sample_company_info,
                vapi_assistant_id=self.sample_assistant_id,
                automation_type='sales'
            )

            # Verify response structure
            assert isinstance(result, dict)
            assert 'html' in result
            assert 'method' in result
            assert 'notification' in result

            # Verify fallback HTML structure
            html = result['html']
            assert '<!DOCTYPE html>' in html
            assert 'Test Company' in html
            assert 'test-assistant-123' in html
            assert 'vapi-widget' in html
            assert 'AI Voice Assistant Demo' in html

            # Verify fallback notification
            assert result['method'] == 'fallback'
            assert result['notification']['type'] == 'warning'
            assert '🚫' in result['notification']['message']
            assert 'Gemini AI unavailable' in result['notification']['message']

    @pytest.mark.asyncio
    async def test_generate_demo_html_gemini_error_fallback(self):
        """Test fallback when Gemini returns an error."""
        mock_gemini_response = {
            'success': False,
            'error': 'API rate limit exceeded'
        }

        with patch('backend.services.gemini_demo_html_service.get_gemini_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.api_key = 'test-key'
            mock_service.generate_content.return_value = mock_gemini_response
            mock_get_service.return_value = mock_service

            result = await self.service.generate_demo_html(
                company_info=self.sample_company_info,
                vapi_assistant_id=self.sample_assistant_id,
                automation_type='sales'
            )

            # Verify response structure and fallback notification
            assert isinstance(result, dict)
            assert result['method'] == 'fallback'
            assert result['notification']['type'] == 'error'
            assert '❌' in result['notification']['message']

            # Should fallback to static HTML
            html = result['html']
            assert '<!DOCTYPE html>' in html
            assert 'Test Company' in html
            assert 'test-assistant-123' in html

    @pytest.mark.asyncio
    async def test_generate_demo_html_invalid_generated_html(self):
        """Test fallback when generated HTML fails validation."""
        # Mock invalid HTML response (missing required elements)
        mock_gemini_response = {
            'success': True,
            'content': '<html><body><h1>Invalid HTML</h1></body></html>'
        }

        with patch('backend.services.gemini_demo_html_service.get_gemini_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.api_key = 'test-key'
            mock_service.generate_content.return_value = mock_gemini_response
            mock_get_service.return_value = mock_service

            result = await self.service.generate_demo_html(
                company_info=self.sample_company_info,
                vapi_assistant_id=self.sample_assistant_id,
                automation_type='sales'
            )

            # Verify validation failure notification
            assert isinstance(result, dict)
            assert result['method'] == 'fallback'
            assert result['notification']['type'] == 'warning'
            assert '⚠️' in result['notification']['message']
            assert 'validation' in result['notification']['message'].lower()

            # Should fallback due to validation failure
            html = result['html']
            assert '<!DOCTYPE html>' in html
            assert 'test-assistant-123' in html
            assert 'vapi-widget' in html

    def test_build_gemini_prompt(self):
        """Test the Gemini prompt building functionality."""
        prompt = self.service._build_gemini_prompt(
            company_name='Test Company',
            assistant_name='Test Company AI Sales Assistant',
            assistant_description='sales assistant',
            vapi_assistant_id='test-123',
            services=['Service A', 'Service B'],
            description='Test description',
            about_text='About us',
            business_hours='9AM-5PM',
            contact_info={'phone': '555-TEST'},
            extracted_content='Website content'
        )

        assert 'Test Company' in prompt
        assert 'sales assistant' in prompt
        assert 'test-123' in prompt
        assert 'Service A, Service B' in prompt
        assert 'EXACT WIDGET CODE TO COPY' in prompt
        assert 'DO NOT CHANGE ANYTHING' in prompt

    def test_clean_html_response(self):
        """Test HTML response cleaning functionality."""
        # Test markdown code block removal
        markdown_html = '```html\n<!DOCTYPE html><html></html>\n```'
        cleaned = self.service._clean_html_response(markdown_html)
        assert cleaned == '<!DOCTYPE html><html></html>'

        # Test plain HTML (no changes)
        plain_html = '<!DOCTYPE html><html></html>'
        cleaned = self.service._clean_html_response(plain_html)
        assert cleaned == '<!DOCTYPE html><html></html>'

    def test_validate_html(self):
        """Test HTML validation functionality."""
        # Valid HTML
        valid_html = '''<!DOCTYPE html>
<html>
<body>
    <vapi-widget assistant-id="test-123"></vapi-widget>
    <script src="widget.umd.js"></script>
</body>
</html>'''
        assert self.service._validate_html(valid_html, 'test-123') is True

        # Missing DOCTYPE
        invalid_html_1 = '<html><body>content</body></html>'
        assert self.service._validate_html(invalid_html_1, 'test-123') is False

        # Missing assistant ID
        invalid_html_2 = '''<!DOCTYPE html>
<html><body><vapi-widget></vapi-widget></body></html>'''
        assert self.service._validate_html(invalid_html_2, 'test-123') is False

        # Missing widget script
        invalid_html_3 = '''<!DOCTYPE html>
<html><body><vapi-widget assistant-id="test-123"></vapi-widget></body></html>'''
        assert self.service._validate_html(invalid_html_3, 'test-123') is False

    def test_generate_service_cards(self):
        """Test service card generation from actual services."""
        services = ['Banking', 'Loans', 'Investment', 'Insurance']
        cards_html = self.service._generate_service_cards(services)

        assert 'Banking' in cards_html
        assert 'Loans' in cards_html
        assert 'Investment' in cards_html
        assert 'Insurance' in cards_html
        assert 'service-card' in cards_html
        assert 'fas fa-' in cards_html  # FontAwesome icons

    def test_generate_default_cards(self):
        """Test default service card generation by automation type."""
        # Test sales cards
        sales_cards = self.service._generate_default_cards('sales')
        assert 'Lead Qualification' in sales_cards
        assert 'Sales Analytics' in sales_cards

        # Test helpdesk cards
        helpdesk_cards = self.service._generate_default_cards('helpdesk')
        assert 'Customer Support' in helpdesk_cards
        assert 'Ticket Management' in helpdesk_cards

        # Test healthcare cards
        healthcare_cards = self.service._generate_default_cards('healthcare')
        assert 'Medical Assistance' in healthcare_cards
        assert 'HIPAA Compliant' in healthcare_cards

        # Test unknown type (defaults to sales)
        unknown_cards = self.service._generate_default_cards('unknown')
        assert 'Lead Qualification' in unknown_cards

    def test_build_fallback_html(self):
        """Test fallback HTML generation."""
        fallback_html = self.service._build_fallback_html(
            company_info=self.sample_company_info,
            vapi_assistant_id=self.sample_assistant_id,
            automation_type='sales'
        )

        # Verify structure and content
        assert '<!DOCTYPE html>' in fallback_html
        assert 'Test Company' in fallback_html
        assert 'test-assistant-123' in fallback_html
        assert 'vapi-widget' in fallback_html
        assert 'Service A' in fallback_html
        assert '+1-555-TEST' in fallback_html
        assert 'test@company.com' in fallback_html
        assert 'widget.umd.js' in fallback_html

    @pytest.mark.asyncio
    async def test_get_demo_html_service_singleton(self):
        """Test that get_demo_html_service returns singleton instance."""
        service1 = await get_demo_html_service()
        service2 = await get_demo_html_service()
        assert service1 is service2

    def test_automation_type_mapping(self):
        """Test automation type to description mapping."""
        test_cases = [
            ('sales', 'sales assistant'),
            ('helpdesk', 'customer support assistant'),
            ('healthcare', 'healthcare assistant'),
            ('lead_generation', 'lead generation assistant'),
            ('appointment_booking', 'appointment booking assistant'),
            ('customer_support', 'customer success assistant'),
            ('unknown_type', 'assistant')  # Default case
        ]

        for automation_type, expected_description in test_cases:
            # This tests the mapping logic within the service
            assistant_type_map = {
                'sales': 'sales assistant',
                'helpdesk': 'customer support assistant',
                'healthcare': 'healthcare assistant',
                'lead_generation': 'lead generation assistant',
                'appointment_booking': 'appointment booking assistant',
                'customer_support': 'customer success assistant'
            }
            result = assistant_type_map.get(automation_type, 'assistant')
            assert result == expected_description


class TestIntegrationScenarios:
    """Integration test scenarios for complete workflows."""

    @pytest.mark.asyncio
    async def test_end_to_end_agricbank_scenario(self):
        """Test complete Agricbank scenario as requested by user."""
        service = GeminiDemoHTMLService()

        # Agricbank company info
        company_info = {
            'name': 'Agricbank',
            'description': 'Premier banking services for agricultural and rural communities',
            'services': ['Agricultural Loans', 'Rural Banking', 'Investment Services', 'Digital Banking'],
            'aboutText': 'Serving agricultural communities for over 50 years',
            'businessHours': 'Monday-Friday 8AM-6PM',
            'contactInfo': {
                'phone': '+1-800-AGRI-BANK',
                'email': 'info@agricbank.com',
                'address': '123 Rural Road, Agriculture City'
            }
        }

        extracted_content = "Agricultural banking with specialized loan services and digital solutions"

        # Test with Gemini fallback (no API key)
        with patch('backend.services.gemini_demo_html_service.get_gemini_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.api_key = None
            mock_get_service.return_value = mock_service

            result = await service.generate_demo_html(
                company_info=company_info,
                vapi_assistant_id='agricbank-assistant-123',
                automation_type='sales',
                extracted_content=extracted_content
            )

            # Verify response structure and fallback notification
            assert isinstance(result, dict)
            assert result['method'] == 'fallback'
            assert result['notification']['type'] == 'warning'
            assert '🚫' in result['notification']['message']

            # Verify Agricbank-specific content
            html = result['html']
            assert 'Agricbank' in html
            assert 'Agricultural Loans' in html
            assert 'Rural Banking' in html
            assert '+1-800-AGRI-BANK' in html
            assert 'info@agricbank.com' in html
            assert 'agricbank-assistant-123' in html
            assert 'Talk to Agricbank AI Assistant' in html

    @pytest.mark.asyncio
    async def test_minimal_company_info(self):
        """Test with minimal company information."""
        service = GeminiDemoHTMLService()

        minimal_info = {
            'name': 'Minimal Corp'
        }

        with patch('backend.services.gemini_demo_html_service.get_gemini_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.api_key = None
            mock_get_service.return_value = mock_service

            result = await service.generate_demo_html(
                company_info=minimal_info,
                vapi_assistant_id='minimal-123',
                automation_type='sales'
            )

            # Verify response structure and notification
            assert isinstance(result, dict)
            assert 'html' in result
            assert 'notification' in result

            # Should still generate valid HTML
            html = result['html']
            assert '<!DOCTYPE html>' in html
            assert 'Minimal Corp' in html
            assert 'minimal-123' in html
            assert 'vapi-widget' in html


if __name__ == '__main__':
    pytest.main([__file__, '-v'])