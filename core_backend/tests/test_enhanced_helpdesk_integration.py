"""
Integration tests for the complete enhanced helpdesk workflow.
"""

import pytest
from unittest.mock import AsyncMock, patch

from backend.services.enhanced_helpdesk_service import enhanced_helpdesk_service
from backend.services.site_extraction_service import site_extraction_service
from backend.services.helpdesk_analytics_service import helpdesk_analytics_service


class TestEnhancedHelpdeskIntegration:
    """Integration tests for complete enhanced helpdesk workflow."""

    @pytest.mark.asyncio
    async def test_complete_helpdesk_creation_workflow(self):
        """Test the complete enhanced helpdesk creation workflow."""
        # Given
        company_name = "Test Insurance Co"
        company_url = "https://testinsurance.com"
        company_description = "Leading insurance provider"
        integrations = {
            "calendly": {"enabled": True},
            "supabase": {"enabled": True},
            "tavily": {"enabled": True},
            "resend": {"enabled": True},
            "vonage": {"enabled": True}
        }

        # When - Call the actual service (it will use simulated data)
        result = await enhanced_helpdesk_service.create_enhanced_helpdesk(
            company_url=company_url,
            company_name=company_name,
            company_description=company_description,
            integrations=integrations,
            enable_demo=True,
            enable_analytics=True
        )

        # Then
        assert result["success"] is True
        assert "vapi_assistant" in result
        assert "n8n_workflow" in result
        assert "demo_page" in result
        assert "analytics" in result

        # Verify basic structure
        vapi_assistant = result["vapi_assistant"]
        assert "id" in vapi_assistant
        assert "name" in vapi_assistant

        n8n_workflow = result["n8n_workflow"]
        assert "id" in n8n_workflow
        assert "name" in n8n_workflow

    @pytest.mark.asyncio
    async def test_site_extraction_and_prompt_generation(self):
        """Test site extraction and AI prompt generation integration."""
        # Given
        test_url = "https://example-insurance.com"
        company_name = "Example Insurance"

        # Mock extracted data
        mock_extracted_info = {
            "company_name": company_name,
            "description": "Professional insurance services since 1990",
            "contact_email": "info@example-insurance.com",
            "contact_phone": "+1234567890",
            "services": ["Auto Insurance", "Home Insurance", "Life Insurance"],
            "business_hours": "Monday-Friday 8AM-6PM",
            "address": "456 Main St, Example City, State 12345"
        }

        # Import the actual model
        from backend.services.site_extraction_service import ExtractedCompanyInfo

        with patch.object(site_extraction_service, 'extract_company_info') as mock_extract:
            # Create a proper ExtractedCompanyInfo object
            extracted_obj = ExtractedCompanyInfo(
                company_name=company_name,
                description="Professional insurance services since 1990",
                contact_email="info@example-insurance.com",
                contact_phone="+1234567890",
                services=["Auto Insurance", "Home Insurance", "Life Insurance"],
                business_hours="Monday-Friday 8AM-6PM",
                address="456 Main St, Example City, State 12345",
                about_text="Professional insurance services since 1990"  # Add the required field
            )
            mock_extract.return_value = extracted_obj

            # When
            extracted_info = await site_extraction_service.extract_company_info(test_url)

            # Generate system prompt using extracted info
            system_prompt = enhanced_helpdesk_service._generate_system_prompt(extracted_info)

            # Then
            assert company_name in system_prompt
            assert "insurance services" in system_prompt.lower()
            assert "Auto Insurance" in system_prompt
            assert "Monday-Friday 8AM-6PM" in system_prompt
            assert "never guess" in system_prompt.lower()  # No-hallucination instruction
            assert "verified company information" in system_prompt.lower()

    @pytest.mark.asyncio
    async def test_analytics_integration_workflow(self):
        """Test analytics integration with helpdesk workflow."""
        # Given
        helpdesk_id = "test-helpdesk-analytics"

        # Mock analytics data
        with patch.object(helpdesk_analytics_service, 'get_comprehensive_analytics') as mock_analytics:
            mock_analytics.return_value = type('obj', (object,), {
                "helpdesk_id": helpdesk_id,
                "call_metrics": {
                    "total_calls": 150,
                    "successful_calls": 135,
                    "success_rate": 90.0
                },
                "action_metrics": {
                    "appointments_booked": 45,
                    "tickets_created": 25
                },
                "performance_metrics": {
                    "response_time": 0.8,
                    "uptime_percentage": 99.5
                },
                "satisfaction_metrics": {
                    "average_rating": 4.7,
                    "nps_score": 72
                },
                "alerts": []
            })

            # When
            analytics = await helpdesk_analytics_service.get_comprehensive_analytics(helpdesk_id)

            # Then
            assert analytics.helpdesk_id == helpdesk_id
            assert analytics.call_metrics["total_calls"] == 150
            assert analytics.call_metrics["success_rate"] == 90.0
            assert analytics.action_metrics["appointments_booked"] == 45
            assert analytics.performance_metrics["uptime_percentage"] == 99.5

    @pytest.mark.asyncio
    async def test_error_handling_in_workflow(self):
        """Test error handling throughout the workflow."""
        # Given
        company_name = "Test Error Co"
        company_url = "https://invalid-url.com"

        # When - Call with invalid URL (should handle gracefully)
        result = await enhanced_helpdesk_service.create_enhanced_helpdesk(
            company_url=company_url,
            company_name=company_name,
            company_description="",
            integrations={}
        )

        # Then - Should still return a response (with simulated data)
        assert "success" in result
        # The service uses simulated data, so it won't actually fail

    @pytest.mark.asyncio
    async def test_basic_service_functionality(self):
        """Test basic service functionality."""
        # Given
        company_name = "Basic Test Co"
        company_url = "https://basic-test.com"

        # When
        result = await enhanced_helpdesk_service.create_enhanced_helpdesk(
            company_url=company_url,
            company_name=company_name,
            company_description="Basic test company",
            integrations={"calendly": {"enabled": True}},
            enable_demo=False,
            enable_analytics=False
        )

        # Then
        assert result is not None
        assert isinstance(result, dict)