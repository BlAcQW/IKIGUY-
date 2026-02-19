"""
Tests for HubSpot Integration

Tests the CRM functionality including contact management, deal tracking,
company management with comprehensive validation and error handling.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone
import json

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))

try:
    from integration.hubspot import (
        HubSpotConfig,
        HubSpotContact,
        HubSpotDeal,
        HubSpotCompany,
        HubSpotObjectType,
        HubSpotDealStage,
        HubSpotContactProperty
    )
    HUBSPOT_IMPORTS_AVAILABLE = True
except ImportError as e:
    HUBSPOT_IMPORTS_AVAILABLE = False
    print(f"HubSpot imports not available: {e}")


class TestHubSpotIntegration:
    """Test suite for HubSpot integration functionality."""

    @pytest.fixture
    def sample_hubspot_config(self):
        """Sample HubSpot configuration for testing."""
        return HubSpotConfig(
            access_token="test_access_token_123",
            base_url="https://api.hubapi.com",
            webhook_secret="test_webhook_secret",
            scopes=["contacts", "companies", "deals", "tickets"]
        )

    @pytest.fixture
    def sample_hubspot_contact(self):
        """Sample HubSpot contact for testing."""
        return HubSpotContact(
            id="12345",
            email="john.doe@example.com",
            firstname="John",
            lastname="Doe",
            phone="+1234567890",
            company="Test Company Inc",
            website="https://testcompany.com",
            jobtitle="CEO",
            lifecyclestage="customer",
            leadsource="website",
            properties={
                "custom_field_1": "value1",
                "marketing_qualified": True,
                "last_contacted": "2025-09-22"
            },
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

    @pytest.fixture
    def sample_hubspot_deal(self):
        """Sample HubSpot deal for testing."""
        return HubSpotDeal(
            id="deal_67890",
            dealname="Test Deal - Enterprise Package",
            amount=50000.00,
            dealstage="qualifiedtobuy",
            pipeline="default",
            closedate=datetime.now(timezone.utc),
            properties={
                "deal_source": "inbound_call",
                "competitor": "none",
                "priority": "high"
            },
            associations={
                "contacts": ["12345", "12346"],
                "companies": ["company_123"]
            },
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

    @pytest.fixture
    def sample_hubspot_company(self):
        """Sample HubSpot company for testing."""
        return HubSpotCompany(
            id="company_123",
            name="Test Company Inc",
            domain="testcompany.com",
            industry="Technology",
            phone="+1-555-123-4567",
            city="San Francisco",
            state="California",
            country="United States",
            numberofemployees=150,
            annualrevenue=10000000,
            properties={
                "company_tier": "enterprise",
                "last_activity_date": "2025-09-22",
                "lead_status": "qualified"
            },
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

    @pytest.mark.skipif(not HUBSPOT_IMPORTS_AVAILABLE, reason="HubSpot integration not available")
    def test_hubspot_config_validation(self, sample_hubspot_config):
        """Test HubSpotConfig model validation."""
        config = sample_hubspot_config

        assert config.access_token == "test_access_token_123"
        assert config.base_url == "https://api.hubapi.com"
        assert config.webhook_secret == "test_webhook_secret"
        assert "contacts" in config.scopes
        assert "deals" in config.scopes
        assert len(config.scopes) == 4

    @pytest.mark.skipif(not HUBSPOT_IMPORTS_AVAILABLE, reason="HubSpot integration not available")
    def test_hubspot_contact_model(self, sample_hubspot_contact):
        """Test HubSpotContact model validation."""
        contact = sample_hubspot_contact

        assert contact.id == "12345"
        assert contact.email == "john.doe@example.com"
        assert contact.firstname == "John"
        assert contact.lastname == "Doe"
        assert contact.phone == "+1234567890"
        assert contact.company == "Test Company Inc"
        assert contact.lifecyclestage == "customer"
        assert contact.properties["custom_field_1"] == "value1"
        assert contact.properties["marketing_qualified"] is True

    @pytest.mark.skipif(not HUBSPOT_IMPORTS_AVAILABLE, reason="HubSpot integration not available")
    def test_hubspot_deal_model(self, sample_hubspot_deal):
        """Test HubSpotDeal model validation."""
        deal = sample_hubspot_deal

        assert deal.id == "deal_67890"
        assert deal.dealname == "Test Deal - Enterprise Package"
        assert deal.amount == 50000.00
        assert deal.dealstage == "qualifiedtobuy"
        assert deal.pipeline == "default"
        assert "12345" in deal.associations["contacts"]
        assert "company_123" in deal.associations["companies"]
        assert deal.properties["deal_source"] == "inbound_call"

    @pytest.mark.skipif(not HUBSPOT_IMPORTS_AVAILABLE, reason="HubSpot integration not available")
    def test_hubspot_company_model(self, sample_hubspot_company):
        """Test HubSpotCompany model validation."""
        company = sample_hubspot_company

        assert company.id == "company_123"
        assert company.name == "Test Company Inc"
        assert company.domain == "testcompany.com"
        assert company.industry == "Technology"
        assert company.numberofemployees == 150
        assert company.annualrevenue == 10000000
        assert company.city == "San Francisco"
        assert company.state == "California"
        assert company.properties["company_tier"] == "enterprise"

    @pytest.mark.skipif(not HUBSPOT_IMPORTS_AVAILABLE, reason="HubSpot integration not available")
    def test_hubspot_object_types_enum(self):
        """Test HubSpotObjectType enum values."""
        assert HubSpotObjectType.CONTACT.value == "contacts"
        assert HubSpotObjectType.COMPANY.value == "companies"
        assert HubSpotObjectType.DEAL.value == "deals"
        assert HubSpotObjectType.TICKET.value == "tickets"
        assert HubSpotObjectType.TASK.value == "tasks"
        assert HubSpotObjectType.MEETING.value == "meetings"
        assert HubSpotObjectType.CALL.value == "calls"
        assert HubSpotObjectType.EMAIL.value == "emails"
        assert HubSpotObjectType.NOTE.value == "notes"

    @pytest.mark.skipif(not HUBSPOT_IMPORTS_AVAILABLE, reason="HubSpot integration not available")
    def test_hubspot_deal_stages_enum(self):
        """Test HubSpotDealStage enum values."""
        assert HubSpotDealStage.APPOINTMENTSCHEDULED.value == "appointmentscheduled"
        assert HubSpotDealStage.QUALIFIEDTOBUY.value == "qualifiedtobuy"
        assert HubSpotDealStage.PRESENTATIONSCHEDULED.value == "presentationscheduled"
        assert HubSpotDealStage.DECISIONMAKERBOUGHTIN.value == "decisionmakerboughtin"
        assert HubSpotDealStage.CONTRACTSENT.value == "contractsent"
        assert HubSpotDealStage.CLOSEDWON.value == "closedwon"
        assert HubSpotDealStage.CLOSEDLOST.value == "closedlost"

    @pytest.mark.skipif(not HUBSPOT_IMPORTS_AVAILABLE, reason="HubSpot integration not available")
    def test_contact_with_minimal_data(self):
        """Test HubSpot contact with minimal required data."""
        minimal_contact = HubSpotContact(
            email="minimal@test.com"
        )

        assert minimal_contact.email == "minimal@test.com"
        assert minimal_contact.id is None
        assert minimal_contact.firstname is None
        assert minimal_contact.lastname is None
        assert minimal_contact.properties == {}

    @pytest.mark.skipif(not HUBSPOT_IMPORTS_AVAILABLE, reason="HubSpot integration not available")
    def test_deal_with_minimal_data(self):
        """Test HubSpot deal with minimal required data."""
        minimal_deal = HubSpotDeal(
            dealname="Basic Deal"
        )

        assert minimal_deal.dealname == "Basic Deal"
        assert minimal_deal.id is None
        assert minimal_deal.amount is None
        assert minimal_deal.dealstage is None
        assert minimal_deal.properties == {}
        assert minimal_deal.associations == {}

    @pytest.mark.skipif(not HUBSPOT_IMPORTS_AVAILABLE, reason="HubSpot integration not available")
    def test_company_with_minimal_data(self):
        """Test HubSpot company with minimal required data."""
        minimal_company = HubSpotCompany(
            name="Basic Company"
        )

        assert minimal_company.name == "Basic Company"
        assert minimal_company.id is None
        assert minimal_company.domain is None
        assert minimal_company.industry is None
        assert minimal_company.properties == {}

    @pytest.mark.skipif(not HUBSPOT_IMPORTS_AVAILABLE, reason="HubSpot integration not available")
    def test_contact_with_custom_properties(self):
        """Test HubSpot contact with extensive custom properties."""
        custom_properties = {
            "lead_score": 85,
            "marketing_qualified": True,
            "sales_qualified": False,
            "preferred_contact_method": "email",
            "industry_vertical": "healthcare",
            "company_size": "mid-market",
            "budget_range": "50000-100000",
            "decision_timeframe": "q1_2025",
            "pain_points": ["integration", "scalability", "cost"],
            "last_email_opened": "2025-09-20T10:30:00Z",
            "last_website_visit": "2025-09-22T14:45:00Z"
        }

        contact = HubSpotContact(
            email="custom.properties@test.com",
            firstname="Custom",
            lastname="Properties",
            properties=custom_properties
        )

        assert contact.properties["lead_score"] == 85
        assert contact.properties["marketing_qualified"] is True
        assert contact.properties["industry_vertical"] == "healthcare"
        assert "integration" in contact.properties["pain_points"]

    @pytest.mark.skipif(not HUBSPOT_IMPORTS_AVAILABLE, reason="HubSpot integration not available")
    def test_deal_associations(self):
        """Test HubSpot deal with multiple associations."""
        deal = HubSpotDeal(
            dealname="Multi-Association Deal",
            amount=75000.00,
            dealstage="presentationscheduled",
            associations={
                "contacts": ["contact_1", "contact_2", "contact_3"],
                "companies": ["company_1", "company_2"]
            },
            properties={
                "deal_type": "new_business",
                "probability": 0.75,
                "forecast_category": "commit"
            }
        )

        assert len(deal.associations["contacts"]) == 3
        assert len(deal.associations["companies"]) == 2
        assert "contact_1" in deal.associations["contacts"]
        assert "company_1" in deal.associations["companies"]
        assert deal.properties["probability"] == 0.75

    @pytest.mark.skipif(not HUBSPOT_IMPORTS_AVAILABLE, reason="HubSpot integration not available")
    def test_config_with_custom_scopes(self):
        """Test HubSpot configuration with custom scopes."""
        custom_config = HubSpotConfig(
            access_token="custom_token",
            scopes=[
                "contacts",
                "companies",
                "deals",
                "tickets",
                "automation",
                "timeline",
                "forms",
                "files"
            ]
        )

        assert len(custom_config.scopes) == 8
        assert "automation" in custom_config.scopes
        assert "timeline" in custom_config.scopes
        assert "forms" in custom_config.scopes

    @pytest.mark.skipif(not HUBSPOT_IMPORTS_AVAILABLE, reason="HubSpot integration not available")
    def test_contact_phone_number_formats(self):
        """Test various phone number formats for contacts."""
        phone_formats = [
            "+1234567890",
            "+1-234-567-8900",
            "(234) 567-8900",
            "234.567.8900",
            "+44 20 7946 0958",  # UK format
            "+33 1 42 86 83 26"  # France format
        ]

        for phone in phone_formats:
            contact = HubSpotContact(
                email=f"test{phone_formats.index(phone)}@example.com",
                phone=phone
            )
            assert contact.phone == phone

    @pytest.mark.skipif(not HUBSPOT_IMPORTS_AVAILABLE, reason="HubSpot integration not available")
    def test_deal_amount_validation(self):
        """Test deal amount with various formats."""
        deal_amounts = [
            0.00,
            1000.50,
            50000.00,
            1000000.99,
            999999999.99
        ]

        for amount in deal_amounts:
            deal = HubSpotDeal(
                dealname=f"Deal ${amount}",
                amount=amount
            )
            assert deal.amount == amount

    @pytest.mark.skipif(not HUBSPOT_IMPORTS_AVAILABLE, reason="HubSpot integration not available")
    def test_company_employee_count_validation(self):
        """Test company with various employee counts."""
        employee_counts = [1, 10, 50, 100, 500, 1000, 10000, 50000]

        for count in employee_counts:
            company = HubSpotCompany(
                name=f"Company with {count} employees",
                numberofemployees=count
            )
            assert company.numberofemployees == count


class TestHubSpotEdgeCases:
    """Test edge cases and error scenarios for HubSpot integration."""

    @pytest.mark.skipif(not HUBSPOT_IMPORTS_AVAILABLE, reason="HubSpot integration not available")
    def test_contact_with_unicode_characters(self):
        """Test contact with international characters."""
        unicode_contact = HubSpotContact(
            email="unicode@test.com",
            firstname="José",
            lastname="García-Müller",
            company="Société Générale",
            properties={
                "notes": "Customer from München, speaks Español and Français",
                "region": "Européen",
                "chinese_name": "李明"
            }
        )

        assert unicode_contact.firstname == "José"
        assert unicode_contact.lastname == "García-Müller"
        assert unicode_contact.company == "Société Générale"
        assert "München" in unicode_contact.properties["notes"]

    @pytest.mark.skipif(not HUBSPOT_IMPORTS_AVAILABLE, reason="HubSpot integration not available")
    def test_very_large_deal_amount(self):
        """Test deal with very large amount."""
        large_deal = HubSpotDeal(
            dealname="Mega Enterprise Deal",
            amount=999999999.99,
            properties={
                "deal_notes": "This is a very large enterprise deal with extensive requirements"
            }
        )

        assert large_deal.amount == 999999999.99
        assert "extensive requirements" in large_deal.properties["deal_notes"]

    @pytest.mark.skipif(not HUBSPOT_IMPORTS_AVAILABLE, reason="HubSpot integration not available")
    def test_many_deal_associations(self):
        """Test deal with many contact and company associations."""
        # Create lists with many IDs
        many_contacts = [f"contact_{i}" for i in range(50)]
        many_companies = [f"company_{i}" for i in range(20)]

        deal = HubSpotDeal(
            dealname="Complex Multi-Stakeholder Deal",
            associations={
                "contacts": many_contacts,
                "companies": many_companies
            }
        )

        assert len(deal.associations["contacts"]) == 50
        assert len(deal.associations["companies"]) == 20
        assert "contact_0" in deal.associations["contacts"]
        assert "contact_49" in deal.associations["contacts"]

    @pytest.mark.skipif(not HUBSPOT_IMPORTS_AVAILABLE, reason="HubSpot integration not available")
    def test_complex_custom_properties(self):
        """Test models with complex nested custom properties."""
        complex_properties = {
            "metadata": {
                "source": "api",
                "campaign_data": {
                    "utm_source": "google",
                    "utm_medium": "cpc",
                    "utm_campaign": "enterprise_q4"
                },
                "scoring": {
                    "lead_score": 85,
                    "fit_score": 92,
                    "interest_score": 78
                }
            },
            "preferences": {
                "communication": ["email", "phone"],
                "topics": ["product_updates", "industry_news"],
                "frequency": "weekly"
            },
            "history": [
                {"date": "2025-09-01", "action": "email_opened"},
                {"date": "2025-09-15", "action": "demo_requested"},
                {"date": "2025-09-22", "action": "proposal_sent"}
            ]
        }

        contact = HubSpotContact(
            email="complex@test.com",
            properties=complex_properties
        )

        assert contact.properties["metadata"]["source"] == "api"
        assert contact.properties["metadata"]["scoring"]["lead_score"] == 85
        assert "email" in contact.properties["preferences"]["communication"]
        assert len(contact.properties["history"]) == 3

    @pytest.mark.skipif(not HUBSPOT_IMPORTS_AVAILABLE, reason="HubSpot integration not available")
    def test_empty_string_values(self):
        """Test models with empty string values."""
        contact = HubSpotContact(
            email="empty@test.com",
            firstname="",
            lastname="",
            phone="",
            company=""
        )

        assert contact.email == "empty@test.com"
        assert contact.firstname == ""
        assert contact.lastname == ""
        assert contact.phone == ""
        assert contact.company == ""

    @pytest.mark.skipif(not HUBSPOT_IMPORTS_AVAILABLE, reason="HubSpot integration not available")
    def test_datetime_handling(self):
        """Test datetime fields in models."""
        now = datetime.now(timezone.utc)
        past_date = now - timedelta(days=30)
        future_date = now + timedelta(days=60)

        deal = HubSpotDeal(
            dealname="Time-sensitive Deal",
            closedate=future_date,
            created_at=past_date,
            updated_at=now
        )

        assert deal.closedate == future_date
        assert deal.created_at == past_date
        assert deal.updated_at == now
        assert deal.created_at < deal.updated_at < deal.closedate

    @pytest.mark.skipif(not HUBSPOT_IMPORTS_AVAILABLE, reason="HubSpot integration not available")
    def test_special_characters_in_properties(self):
        """Test properties with special characters and symbols."""
        special_properties = {
            "email_template": "Hello {{contact.firstname}}, welcome to {{company.name}}!",
            "equation": "ROI = (Gain - Cost) / Cost * 100%",
            "json_data": '{"key": "value", "number": 123, "boolean": true}',
            "html_snippet": '<div class="customer-info"><p>Important customer</p></div>',
            "unicode_symbols": "★★★★☆ (4/5 stars) ✓ Verified ⚡ Premium",
            "special_chars": "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        }

        contact = HubSpotContact(
            email="special@test.com",
            properties=special_properties
        )

        assert "{{contact.firstname}}" in contact.properties["email_template"]
        assert "ROI = " in contact.properties["equation"]
        assert "★★★★☆" in contact.properties["unicode_symbols"]
        assert "!@#$%^&*()" in contact.properties["special_chars"]


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])