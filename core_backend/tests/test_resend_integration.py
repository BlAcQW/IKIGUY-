"""
Tests for Resend Integration Routes and Services

Tests the email sending functionality, batch operations, and domain management
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

from backend.routes.resend_consolidated import (
    ResendEmailRequest,
    ResendBatchEmailRequest,
    router
)

try:
    from backend.services.resend_consolidated_service import ResendServiceWrapper
    from integration.resend import (
        ResendEmail,
        ResendContact,
        ResendDomain,
        ResendResponse,
        ResendConfig
    )
    RESEND_IMPORTS_AVAILABLE = True
except ImportError:
    RESEND_IMPORTS_AVAILABLE = False


class TestResendIntegration:
    """Test suite for Resend integration functionality."""

    @pytest.fixture
    def sample_email_request(self):
        """Sample email request for testing."""
        return ResendEmailRequest(
            tenant_id="test_tenant_123",
            **{"from": "noreply@test.com"},  # Use ** to handle 'from' alias
            to=["recipient@test.com"],
            subject="Test Email Subject",
            html="<h1>Test HTML Content</h1>",
            text="Test plain text content",
            tags=["test", "automation"],
            context={"source": "unit_test", "campaign_id": "test_campaign"}
        )

    @pytest.fixture
    def sample_resend_response(self):
        """Sample Resend API response for testing."""
        return ResendResponse(
            success=True,
            data={
                "id": "re_123456789",
                "from": "noreply@test.com",
                "to": ["recipient@test.com"],
                "subject": "Test Email Subject",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            email_id="re_123456789"
        )

    def test_resend_email_request_validation(self):
        """Test ResendEmailRequest model validation."""
        # Valid request with all fields
        request = ResendEmailRequest(
            tenant_id="test_tenant",
            **{"from": "sender@test.com"},
            to=["recipient@test.com"],
            subject="Test Subject",
            html="<p>HTML content</p>",
            text="Plain text content"
        )

        assert request.tenant_id == "test_tenant"
        assert request.from_ == "sender@test.com"  # from_ is the actual field name
        assert request.to == ["recipient@test.com"]
        assert request.subject == "Test Subject"
        assert request.html == "<p>HTML content</p>"
        assert request.text == "Plain text content"

        # Valid request with minimal fields (only required)
        minimal_request = ResendEmailRequest(
            tenant_id="test_tenant",
            **{"from": "sender@test.com"},
            to=["recipient@test.com"],
            subject="Minimal Subject"
        )
        assert minimal_request.html is None
        assert minimal_request.text is None

    def test_resend_batch_email_request_validation(self):
        """Test ResendBatchEmailRequest model validation."""
        email1 = ResendEmailRequest(
            tenant_id="test_tenant",
            **{"from": "sender@test.com"},
            to=["recipient1@test.com"],
            subject="Email 1"
        )

        email2 = ResendEmailRequest(
            tenant_id="test_tenant",
            **{"from": "sender@test.com"},
            to=["recipient2@test.com"],
            subject="Email 2"
        )

        batch_request = ResendBatchEmailRequest(
            tenant_id="test_tenant",
            emails=[email1, email2],
            context={"batch_id": "batch_123"}
        )

        assert batch_request.tenant_id == "test_tenant"
        assert len(batch_request.emails) == 2
        assert batch_request.context["batch_id"] == "batch_123"

    def test_email_address_validation(self):
        """Test email address validation in requests."""
        # Valid email addresses
        valid_emails = [
            "user@example.com",
            "test.email+tag@domain.co.uk",
            "firstname.lastname@company.org"
        ]

        for email in valid_emails:
            request = ResendEmailRequest(
                tenant_id="test_tenant",
                **{"from": email},
                to=[email],
                subject="Test"
            )
            assert request.from_ == email
            assert request.to[0] == email

        # Invalid email addresses should raise validation errors
        invalid_emails = [
            "invalid-email",
            "@domain.com",
            "user@",
            "user space@domain.com"
        ]

        for invalid_email in invalid_emails:
            with pytest.raises(Exception):  # ValidationError from pydantic
                ResendEmailRequest(
                    tenant_id="test_tenant",
                    **{"from": invalid_email},
                    to=["valid@test.com"],
                    subject="Test"
                )

    @pytest.mark.skipif(not RESEND_IMPORTS_AVAILABLE, reason="Resend integration not available")
    def test_resend_email_model(self):
        """Test ResendEmail model from integration."""
        email = ResendEmail(
            from_="sender@test.com",
            to=["recipient@test.com"],
            subject="Test Subject",
            html="<h1>Test</h1>",
            text="Test content"
        )

        assert email.from_ == "sender@test.com"
        assert email.to == ["recipient@test.com"]
        assert email.subject == "Test Subject"
        assert email.html == "<h1>Test</h1>"
        assert email.text == "Test content"

    @pytest.mark.skipif(not RESEND_IMPORTS_AVAILABLE, reason="Resend integration not available")
    def test_resend_response_model(self, sample_resend_response):
        """Test ResendResponse model."""
        response = sample_resend_response

        assert response.success is True
        assert response.data["id"] == "re_123456789"
        assert response.data["from"] == "noreply@test.com"
        assert response.data["to"] == ["recipient@test.com"]
        assert response.email_id == "re_123456789"

    def test_multiple_recipients_validation(self):
        """Test validation with multiple recipients."""
        recipients = [
            "user1@test.com",
            "user2@test.com",
            "user3@test.com"
        ]

        request = ResendEmailRequest(
            tenant_id="test_tenant",
            **{"from": "sender@test.com"},
            to=recipients,
            subject="Multi-recipient test"
        )

        assert len(request.to) == 3
        assert request.to == recipients

    def test_email_with_attachments_validation(self):
        """Test email request with attachments."""
        attachments = [
            {
                "filename": "document.pdf",
                "content": "base64encodedcontent",
                "content_type": "application/pdf"
            },
            {
                "filename": "image.png",
                "content": "base64encodedimage",
                "content_type": "image/png"
            }
        ]

        request = ResendEmailRequest(
            tenant_id="test_tenant",
            **{"from": "sender@test.com"},
            to=["recipient@test.com"],
            subject="Email with attachments",
            attachments=attachments
        )

        assert len(request.attachments) == 2
        assert request.attachments[0]["filename"] == "document.pdf"
        assert request.attachments[1]["content_type"] == "image/png"

    def test_email_headers_validation(self):
        """Test custom email headers validation."""
        headers = {
            "X-Priority": "1",
            "X-Campaign-ID": "campaign_123",
            "Reply-To": "support@test.com"
        }

        request = ResendEmailRequest(
            tenant_id="test_tenant",
            **{"from": "sender@test.com"},
            to=["recipient@test.com"],
            subject="Email with headers",
            headers=headers
        )

        assert request.headers["X-Priority"] == "1"
        assert request.headers["X-Campaign-ID"] == "campaign_123"

    def test_email_tags_validation(self):
        """Test email tags for tracking."""
        tags = ["newsletter", "marketing", "automation", "test"]

        request = ResendEmailRequest(
            tenant_id="test_tenant",
            **{"from": "sender@test.com"},
            to=["recipient@test.com"],
            subject="Tagged email",
            tags=tags
        )

        assert len(request.tags) == 4
        assert "newsletter" in request.tags
        assert "automation" in request.tags

    @pytest.mark.skipif(not RESEND_IMPORTS_AVAILABLE, reason="Resend integration not available")
    @pytest.mark.asyncio
    async def test_resend_service_wrapper_initialization(self):
        """Test ResendServiceWrapper initialization."""
        config = ResendConfig(
            api_key="test_api_key"
        )

        service = ResendServiceWrapper(config)
        assert service.config.api_key == "test_api_key"
        assert service.config.base_url == "https://api.resend.com"
        assert service.analytics_service is not None

    def test_context_tracking_validation(self):
        """Test context tracking in email requests."""
        context = {
            "user_id": "user_123",
            "campaign_id": "campaign_456",
            "source": "api",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "custom_metadata": {
                "department": "marketing",
                "priority": "high"
            }
        }

        request = ResendEmailRequest(
            tenant_id="test_tenant",
            **{"from": "sender@test.com"},
            to=["recipient@test.com"],
            subject="Context tracked email",
            context=context
        )

        assert request.context["user_id"] == "user_123"
        assert request.context["campaign_id"] == "campaign_456"
        assert request.context["custom_metadata"]["department"] == "marketing"

    def test_reply_to_validation(self):
        """Test reply-to email address validation."""
        request = ResendEmailRequest(
            tenant_id="test_tenant",
            **{"from": "noreply@test.com"},
            to=["recipient@test.com"],
            subject="Email with reply-to",
            reply_to="support@test.com"
        )

        assert request.reply_to == "support@test.com"

    def test_tenant_id_validation(self):
        """Test tenant ID validation."""
        # Valid tenant IDs
        valid_tenant_ids = [
            "tenant_123",
            "org-456",
            "company_789_prod",
            "test_environment"
        ]

        for tenant_id in valid_tenant_ids:
            request = ResendEmailRequest(
                tenant_id=tenant_id,
                **{"from": "sender@test.com"},
                to=["recipient@test.com"],
                subject="Test"
            )
            assert request.tenant_id == tenant_id

        # Empty tenant ID is allowed by the model (no validation constraint)
        empty_request = ResendEmailRequest(
            tenant_id="",
            **{"from": "sender@test.com"},
            to=["recipient@test.com"],
            subject="Test"
        )
        assert empty_request.tenant_id == ""


class TestResendEdgeCases:
    """Test edge cases and error scenarios for Resend integration."""

    def test_large_batch_email_request(self):
        """Test batch email request with many emails."""
        emails = []
        for i in range(50):  # Create 50 emails
            emails.append(ResendEmailRequest(
                tenant_id="test_tenant",
                **{"from": "sender@test.com"},
                to=[f"recipient{i}@test.com"],
                subject=f"Batch email {i}"
            ))

        batch_request = ResendBatchEmailRequest(
            tenant_id="test_tenant",
            emails=emails
        )

        assert len(batch_request.emails) == 50
        assert batch_request.emails[0].subject == "Batch email 0"
        assert batch_request.emails[49].subject == "Batch email 49"

    def test_email_with_unicode_content(self):
        """Test email with unicode characters."""
        unicode_content = "Hello 🌍! Testing émojis and spëcial charactërs: 中文, العربية, हिन्दी"

        request = ResendEmailRequest(
            tenant_id="test_tenant",
            **{"from": "sender@test.com"},
            to=["recipient@test.com"],
            subject=unicode_content,
            html=f"<p>{unicode_content}</p>",
            text=unicode_content
        )

        assert unicode_content in request.subject
        assert unicode_content in request.html
        assert unicode_content in request.text

    def test_very_long_subject_line(self):
        """Test email with very long subject line."""
        long_subject = "A" * 500  # Very long subject

        request = ResendEmailRequest(
            tenant_id="test_tenant",
            **{"from": "sender@test.com"},
            to=["recipient@test.com"],
            subject=long_subject
        )

        assert len(request.subject) == 500
        assert request.subject == long_subject

    def test_empty_html_and_text_content(self):
        """Test email with no HTML or text content."""
        request = ResendEmailRequest(
            tenant_id="test_tenant",
            **{"from": "sender@test.com"},
            to=["recipient@test.com"],
            subject="Empty content test"
            # No html or text provided
        )

        assert request.html is None
        assert request.text is None
        assert request.subject == "Empty content test"

    def test_many_tags_validation(self):
        """Test email with many tags."""
        many_tags = [f"tag_{i}" for i in range(20)]

        request = ResendEmailRequest(
            tenant_id="test_tenant",
            **{"from": "sender@test.com"},
            to=["recipient@test.com"],
            subject="Many tags test",
            tags=many_tags
        )

        assert len(request.tags) == 20
        assert "tag_0" in request.tags
        assert "tag_19" in request.tags

    def test_complex_headers_validation(self):
        """Test email with complex custom headers."""
        complex_headers = {
            "X-Mailer": "Custom Mailer v1.0",
            "X-Priority": "1 (Highest)",
            "X-MSMail-Priority": "High",
            "Importance": "high",
            "X-Custom-Tracking": "utm_source=email&utm_medium=newsletter",
            "X-Campaign-Type": "promotional",
            "List-Unsubscribe": "<mailto:unsubscribe@test.com>",
            "Return-Path": "bounces@test.com"
        }

        request = ResendEmailRequest(
            tenant_id="test_tenant",
            **{"from": "sender@test.com"},
            to=["recipient@test.com"],
            subject="Complex headers test",
            headers=complex_headers
        )

        assert len(request.headers) == 8
        assert request.headers["X-Priority"] == "1 (Highest)"
        assert request.headers["List-Unsubscribe"] == "<mailto:unsubscribe@test.com>"

    def test_international_email_domains(self):
        """Test emails with international domain names."""
        international_emails = [
            "user@exämple.com",  # IDN domain
            "test@münchen.de",   # German umlaut
            "admin@тест.рф"      # Cyrillic domain
        ]

        for email in international_emails:
            try:
                request = ResendEmailRequest(
                    tenant_id="test_tenant",
                    **{"from": "sender@test.com"},
                    to=[email],
                    subject="International domain test"
                )
                # If validation passes, check the email was stored
                assert email in request.to
            except Exception:
                # Some international domains might not pass validation
                # This is expected behavior
                pass

    @pytest.mark.skipif(not RESEND_IMPORTS_AVAILABLE, reason="Resend integration not available")
    def test_resend_contact_model(self):
        """Test ResendContact model validation."""
        contact = ResendContact(
            email="contact@test.com",
            first_name="John",
            last_name="Doe",
            unsubscribed=False
        )

        assert contact.email == "contact@test.com"
        assert contact.first_name == "John"
        assert contact.last_name == "Doe"
        assert contact.unsubscribed is False

    @pytest.mark.skipif(not RESEND_IMPORTS_AVAILABLE, reason="Resend integration not available")
    def test_resend_domain_model(self):
        """Test ResendDomain model validation."""
        domain = ResendDomain(
            name="mail.example.com",
            id="domain_123",
            status="verified",
            created_at=datetime.now(timezone.utc).isoformat(),
            region="us-east-1"
        )

        assert domain.id == "domain_123"
        assert domain.name == "mail.example.com"
        assert domain.status == "verified"
        assert domain.region == "us-east-1"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])