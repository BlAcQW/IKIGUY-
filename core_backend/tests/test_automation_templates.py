"""
Tests for automation templates functionality
"""
import pytest
from unittest.mock import MagicMock
from backend.models.automation_template import (
    AutomationTemplate,
    TemplateIndustry,
    TemplateCategory,
    get_integrations_for_template,
    create_system_prompt,
    INTEGRATION_TEMPLATES
)
from backend.routes.automation_templates import (
    create_default_templates,
    get_custom_tools_for_category,
    get_vapi_config_for_industry,
    get_n8n_config_for_category
)


class TestAutomationTemplateModel:
    """Test automation template model functionality."""

    def test_template_creation(self):
        """Test creating a template with valid data."""
        template = AutomationTemplate(
            template_name="Test Template",
            industry=TemplateIndustry.HEALTHCARE,
            category=TemplateCategory.HELPDESK,
            description="Test description",
            company_name="Test Company",
            system_prompt="Test prompt",
            integrations=get_integrations_for_template(TemplateCategory.HELPDESK, TemplateIndustry.HEALTHCARE),
            vapi_config=get_vapi_config_for_industry(TemplateIndustry.HEALTHCARE, "Test Company"),
            n8n_config=get_n8n_config_for_category(TemplateCategory.HELPDESK),
            demo_config={"theme": "healthcare"},
            monitoring_config={"enabled": True}
        )

        assert template.template_name == "Test Template"
        assert template.industry == TemplateIndustry.HEALTHCARE
        assert template.category == TemplateCategory.HELPDESK
        assert template.company_name == "Test Company"
        assert len(template.integrations) > 0

    def test_integration_templates_exist(self):
        """Test that all required integration templates exist."""
        required_integrations = [
            "openai", "vapi", "supabase", "resend", "anthropic",
            "gemini", "tavily", "firecrawl", "brave", "pinecone",
            "calendly", "freshdesk", "vonage"
        ]

        for integration_name in required_integrations:
            assert integration_name in INTEGRATION_TEMPLATES
            integration = INTEGRATION_TEMPLATES[integration_name]
            assert integration.name
            assert integration.api_key is not None  # Should have a key (even if empty)


class TestIntegrationAssignment:
    """Test integration assignment based on industry and category."""

    def test_healthcare_integrations(self):
        """Test healthcare industry gets correct integrations."""
        integrations = get_integrations_for_template(
            TemplateCategory.PROVIDER_LOCATOR,
            TemplateIndustry.HEALTHCARE
        )

        integration_names = [i.name for i in integrations]
        assert "OpenAI GPT" in integration_names
        assert "VAPI Voice AI" in integration_names
        assert "Calendly Scheduling" in integration_names
        assert "Freshdesk Support" in integration_names

    def test_generic_integrations(self):
        """Test generic industry gets basic integrations."""
        integrations = get_integrations_for_template(
            TemplateCategory.HELPDESK,
            TemplateIndustry.GENERIC
        )

        integration_names = [i.name for i in integrations]
        assert "OpenAI GPT" in integration_names
        assert "VAPI Voice AI" in integration_names
        assert "Supabase Database" in integration_names
        assert len(integrations) >= 4

    def test_insurance_integrations(self):
        """Test insurance industry gets SOX compliance integrations."""
        integrations = get_integrations_for_template(
            TemplateCategory.CLAIMS_PROCESSING,
            TemplateIndustry.INSURANCE
        )

        integration_names = [i.name for i in integrations]
        assert "OpenAI GPT" in integration_names
        assert "Freshdesk Support" in integration_names
        assert "Vonage SMS" in integration_names


class TestSystemPromptGeneration:
    """Test system prompt generation for different industries."""

    def test_healthcare_prompt(self):
        """Test healthcare-specific prompt generation."""
        prompt = create_system_prompt(
            TemplateCategory.PROVIDER_LOCATOR,
            TemplateIndustry.HEALTHCARE,
            "Test Health"
        )

        assert "Test Health" in prompt
        assert "HIPAA" in prompt
        assert "medical advice" in prompt
        assert "emergency" in prompt
        assert "Provider Locator" in prompt

    def test_insurance_prompt(self):
        """Test insurance-specific prompt generation."""
        prompt = create_system_prompt(
            TemplateCategory.CLAIMS_PROCESSING,
            TemplateIndustry.INSURANCE,
            "Test Insurance"
        )

        assert "Test Insurance" in prompt
        assert "policy" in prompt
        assert "claim" in prompt
        assert "coverage" in prompt

    def test_generic_prompt(self):
        """Test generic prompt generation."""
        prompt = create_system_prompt(
            TemplateCategory.HELPDESK,
            TemplateIndustry.GENERIC,
            "Test Company"
        )

        assert "Test Company" in prompt
        assert "customer support" in prompt
        assert "professional" in prompt


class TestToolAssignment:
    """Test custom tool assignment for different categories."""

    def test_helpdesk_tools(self):
        """Test helpdesk category gets appropriate tools."""
        tools = get_custom_tools_for_category(TemplateCategory.HELPDESK)

        expected_tools = [
            "search_knowledge_base",
            "create_support_ticket",
            "escalate_to_human",
            "book_appointment",
            "send_email_summary"
        ]

        for tool in expected_tools:
            assert tool in tools

    def test_provider_locator_tools(self):
        """Test provider locator gets healthcare-specific tools."""
        tools = get_custom_tools_for_category(TemplateCategory.PROVIDER_LOCATOR)

        expected_tools = [
            "search_healthcare_providers",
            "get_provider_details",
            "book_appointment",
            "verify_insurance_coverage",
            "get_emergency_providers"
        ]

        for tool in expected_tools:
            assert tool in tools

    def test_sales_tools(self):
        """Test sales category gets sales-specific tools."""
        tools = get_custom_tools_for_category(TemplateCategory.SALES)

        expected_tools = [
            "qualify_lead",
            "schedule_demo",
            "send_product_info",
            "calculate_pricing",
            "create_proposal"
        ]

        for tool in expected_tools:
            assert tool in tools


class TestVAPIConfiguration:
    """Test VAPI configuration generation."""

    def test_healthcare_vapi_config(self):
        """Test healthcare VAPI configuration."""
        config = get_vapi_config_for_industry(TemplateIndustry.HEALTHCARE, "Test Health")

        assert config.compliance_level == "HIPAA"
        assert config.temperature == 0.3
        assert config.max_duration == 900
        assert "Test Health" in config.first_message
        assert "healthcare" in config.first_message.lower()

    def test_insurance_vapi_config(self):
        """Test insurance VAPI configuration."""
        config = get_vapi_config_for_industry(TemplateIndustry.INSURANCE, "Test Insurance")

        assert config.compliance_level == "SOX"
        assert config.temperature == 0.2
        assert "Test Insurance" in config.first_message
        assert "insurance" in config.first_message.lower()

    def test_generic_vapi_config(self):
        """Test generic VAPI configuration."""
        config = get_vapi_config_for_industry(TemplateIndustry.GENERIC, "Test Company")

        assert config.compliance_level == "Standard"
        assert "Test Company" in config.first_message


class TestN8NConfiguration:
    """Test N8N workflow configuration."""

    def test_provider_locator_n8n_config(self):
        """Test provider locator N8N configuration."""
        config = get_n8n_config_for_category(TemplateCategory.PROVIDER_LOCATOR)

        assert config.workflow_id == "healthcare_provider_search"
        assert "/search-providers" in config.endpoints.values()
        assert "/emergency-providers" in config.endpoints.values()
        assert "/book-appointment" in config.endpoints.values()

    def test_helpdesk_n8n_config(self):
        """Test helpdesk N8N configuration."""
        config = get_n8n_config_for_category(TemplateCategory.HELPDESK)

        assert config.workflow_id == "customer_support_helpdesk"
        assert "/create-ticket" in config.endpoints.values()
        assert "/search-kb" in config.endpoints.values()

    def test_claims_processing_n8n_config(self):
        """Test claims processing N8N configuration."""
        config = get_n8n_config_for_category(TemplateCategory.CLAIMS_PROCESSING)

        assert config.workflow_id == "insurance_claims_processing"
        assert "/file-claim" in config.endpoints.values()
        assert "/claim-status" in config.endpoints.values()


class TestDefaultTemplates:
    """Test default template creation."""

    def test_create_default_templates(self):
        """Test creating all default templates."""
        templates = create_default_templates()

        assert len(templates) >= 10  # Should have multiple templates

        # Check for generic templates (Campaign page)
        generic_templates = [t for t in templates if t.industry == TemplateIndustry.GENERIC]
        assert len(generic_templates) >= 4

        # Check for industry-specific templates (Automations page)
        industry_templates = [t for t in templates if t.industry != TemplateIndustry.GENERIC]
        assert len(industry_templates) >= 6

    def test_template_completeness(self):
        """Test that all templates have required fields."""
        templates = create_default_templates()

        for template in templates:
            # Basic fields
            assert template.template_name
            assert template.industry
            assert template.category
            assert template.description
            assert template.company_name
            assert template.system_prompt

            # Configurations
            assert template.vapi_config
            assert template.n8n_config
            assert template.demo_config
            assert template.monitoring_config

            # Integration and tools
            assert len(template.integrations) > 0
            assert len(template.custom_tool_names) > 0

            # Metadata
            assert template.id
            assert template.created_by == "system"
            assert template.is_active is True

    def test_industry_distribution(self):
        """Test that templates cover different industries."""
        templates = create_default_templates()

        industries = {t.industry for t in templates}
        expected_industries = {
            TemplateIndustry.GENERIC,
            TemplateIndustry.HEALTHCARE,
            TemplateIndustry.INSURANCE,
            TemplateIndustry.RETAIL,
            TemplateIndustry.FINANCE
        }

        assert expected_industries.issubset(industries)

    def test_category_distribution(self):
        """Test that templates cover different categories."""
        templates = create_default_templates()

        categories = {t.category for t in templates}
        expected_categories = {
            TemplateCategory.HELPDESK,
            TemplateCategory.SALES,
            TemplateCategory.APPOINTMENT_BOOKING,
            TemplateCategory.PROVIDER_LOCATOR,
            TemplateCategory.CUSTOMER_SERVICE
        }

        assert expected_categories.issubset(categories)


if __name__ == "__main__":
    pytest.main([__file__])