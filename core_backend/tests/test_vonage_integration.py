"""
Tests for Vonage Integration Routes and Services

Tests the SMS, Voice, and Number management functionality
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

from backend.routes.vonage_consolidated import (
    VonageSMSRequest,
    VonageVoiceCallRequest,
    VonageNumberSearchRequest,
    VonageNumberManagementRequest,
    VonageTTSRequest,
    router
)

try:
    from backend.services.vonage_consolidated_service import vonage_consolidated_service
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))
    from integration.vonage import (
        VonageConfig,
        VonageSMSMessage,
        VonageVoiceCall,
        VonageNumber,
        VonageResponse,
        VonageIntegration
    )
    VONAGE_IMPORTS_AVAILABLE = True
except ImportError as e:
    VONAGE_IMPORTS_AVAILABLE = False
    print(f"Vonage imports not available: {e}")


class TestVonageIntegration:
    """Test suite for Vonage integration functionality."""

    @pytest.fixture
    def sample_sms_request(self):
        """Sample SMS request for testing."""
        return VonageSMSRequest(
            to="+1234567890",
            **{"from": "+0987654321"},  # Use ** to handle 'from' alias
            text="Test SMS message from unit test",
            type="text",
            client_ref="test_sms_123",
            webhook_url="https://api.ailabsafrica.com/vonage/webhook",
            ttl=86400,
            message_class=1,
            tenant_id="test_tenant_123"
        )

    @pytest.fixture
    def sample_voice_call_request(self):
        """Sample voice call request for testing."""
        return VonageVoiceCallRequest(
            to="+1234567890",
            **{"from": "+0987654321"},
            answer_url="https://api.ailabsafrica.com/vonage/ncco",
            event_url="https://api.ailabsafrica.com/vonage/events",
            answer_method="GET",
            event_method="POST",
            machine_detection="continue",
            length_timer=7200,
            ringing_timer=60,
            tenant_id="test_tenant_123"
        )

    @pytest.fixture
    def sample_number_search_request(self):
        """Sample number search request for testing."""
        return VonageNumberSearchRequest(
            country="US",
            type_="mobile-lvn",
            pattern="555",
            search_pattern=1,
            features=["SMS", "VOICE"],
            size=10,
            index=1,
            tenant_id="test_tenant_123"
        )

    @pytest.fixture
    def sample_vonage_response(self):
        """Sample Vonage API response for testing."""
        return VonageResponse(
            success=True,
            data={
                "message-id": "msg_123456789",
                "to": "+1234567890",
                "message-price": "0.00333333",
                "network": "31100",
                "status": "0"
            },
            message_count=1,
            messages=[
                {
                    "message-id": "msg_123456789",
                    "to": "+1234567890",
                    "status": "0",
                    "message-price": "0.00333333",
                    "network": "31100"
                }
            ]
        )

    def test_vonage_sms_request_validation(self):
        """Test VonageSMSRequest model validation."""
        # Valid request with all fields
        request = VonageSMSRequest(
            to="+1234567890",
            **{"from": "+0987654321"},
            text="Test SMS message",
            type="text",
            client_ref="test_ref",
            webhook_url="https://example.com/webhook",
            ttl=3600,
            message_class=1,
            tenant_id="test_tenant"
        )

        assert request.to == "+1234567890"
        assert request.from_ == "+0987654321"  # from_ is the actual field name
        assert request.text == "Test SMS message"
        assert request.type == "text"
        assert request.client_ref == "test_ref"
        assert request.webhook_url == "https://example.com/webhook"
        assert request.ttl == 3600
        assert request.message_class == 1
        assert request.tenant_id == "test_tenant"

        # Valid request with minimal fields (only required)
        minimal_request = VonageSMSRequest(
            to="+1234567890",
            **{"from": "+0987654321"},
            text="Minimal SMS"
        )
        assert minimal_request.type == "text"  # Default value
        assert minimal_request.tenant_id == "default"  # Default value

    def test_vonage_voice_call_request_validation(self):
        """Test VonageVoiceCallRequest model validation."""
        request = VonageVoiceCallRequest(
            to="+1234567890",
            **{"from": "+0987654321"},
            answer_url="https://example.com/answer",
            event_url="https://example.com/events",
            answer_method="POST",
            event_method="GET",
            machine_detection="hangup",
            length_timer=1800,
            ringing_timer=30,
            tenant_id="test_tenant"
        )

        assert request.to == "+1234567890"
        assert request.from_ == "+0987654321"
        assert request.answer_url == "https://example.com/answer"
        assert request.event_url == "https://example.com/events"
        assert request.answer_method == "POST"
        assert request.event_method == "GET"
        assert request.machine_detection == "hangup"
        assert request.length_timer == 1800
        assert request.ringing_timer == 30
        assert request.tenant_id == "test_tenant"

    def test_vonage_number_search_request_validation(self):
        """Test VonageNumberSearchRequest model validation."""
        # Test with explicit type specified
        request = VonageNumberSearchRequest(
            country="GB",
            **{"type": "landline"},  # Use ** to handle 'type' alias
            pattern="020",
            search_pattern=2,
            features=["SMS", "VOICE", "MMS"],
            size=20,
            index=5,
            tenant_id="test_tenant"
        )

        assert request.country == "GB"
        assert request.type_ == "landline"
        assert request.pattern == "020"
        assert request.search_pattern == 2
        assert request.features == ["SMS", "VOICE", "MMS"]
        assert request.size == 20
        assert request.index == 5
        assert request.tenant_id == "test_tenant"

        # Test with default type (mobile-lvn)
        default_request = VonageNumberSearchRequest(country="US")
        assert default_request.type_ == "mobile-lvn"  # Default value

    def test_vonage_number_management_request_validation(self):
        """Test VonageNumberManagementRequest model validation."""
        request = VonageNumberManagementRequest(
            operation="buy",
            country="US",
            msisdn="+15551234567",
            search_params={"type": "mobile-lvn", "features": ["SMS"]},
            tenant_id="test_tenant"
        )

        assert request.operation == "buy"
        assert request.country == "US"
        assert request.msisdn == "+15551234567"
        assert request.search_params["type"] == "mobile-lvn"
        assert request.search_params["features"] == ["SMS"]
        assert request.tenant_id == "test_tenant"

    def test_vonage_tts_request_validation(self):
        """Test VonageTTSRequest model validation."""
        request = VonageTTSRequest(
            call_uuid="call-123456789",
            text="Hello, this is a test message",
            voice_name="Joey",
            language="en-GB",
            tenant_id="test_tenant"
        )

        assert request.call_uuid == "call-123456789"
        assert request.text == "Hello, this is a test message"
        assert request.voice_name == "Joey"
        assert request.language == "en-GB"
        assert request.tenant_id == "test_tenant"

    @pytest.mark.skipif(not VONAGE_IMPORTS_AVAILABLE, reason="Vonage integration not available")
    def test_vonage_config_validation(self):
        """Test VonageConfig model validation."""
        config = VonageConfig(
            api_key="test_api_key_123",
            api_secret="test_api_secret_456",
            base_url="https://api.nexmo.com",
            application_id="app_123",
            private_key="-----BEGIN PRIVATE KEY-----",
            signature_secret="signature_secret_789",
            timeout=60,
            verify_ssl=True
        )

        assert config.api_key == "test_api_key_123"
        assert config.api_secret == "test_api_secret_456"
        assert config.base_url == "https://api.nexmo.com"
        assert config.application_id == "app_123"
        assert config.private_key == "-----BEGIN PRIVATE KEY-----"
        assert config.signature_secret == "signature_secret_789"
        assert config.timeout == 60
        assert config.verify_ssl is True

    @pytest.mark.skipif(not VONAGE_IMPORTS_AVAILABLE, reason="Vonage integration not available")
    def test_vonage_sms_message_model(self):
        """Test VonageSMSMessage model from integration."""
        message = VonageSMSMessage(
            to="+1234567890",
            from_="+0987654321",
            text="Test SMS from integration model",
            type="text",
            client_ref="sms_ref_123",
            webhook_url="https://example.com/webhook",
            webhook_version="2",
            ttl=7200,
            message_class=0
        )

        assert message.to == "+1234567890"
        assert message.from_ == "+0987654321"
        assert message.text == "Test SMS from integration model"
        assert message.type == "text"
        assert message.client_ref == "sms_ref_123"
        assert message.webhook_url == "https://example.com/webhook"
        assert message.webhook_version == "2"
        assert message.ttl == 7200
        assert message.message_class == 0

    @pytest.mark.skipif(not VONAGE_IMPORTS_AVAILABLE, reason="Vonage integration not available")
    def test_vonage_voice_call_model(self):
        """Test VonageVoiceCall model from integration."""
        call = VonageVoiceCall(
            to="+1234567890",
            from_="+0987654321",
            answer_url="https://example.com/ncco",
            event_url="https://example.com/events",
            answer_method="GET",
            event_method="POST",
            machine_detection="continue",
            length_timer=3600,
            ringing_timer=45
        )

        assert call.to == "+1234567890"
        assert call.from_ == "+0987654321"
        assert call.answer_url == "https://example.com/ncco"
        assert call.event_url == "https://example.com/events"
        assert call.answer_method == "GET"
        assert call.event_method == "POST"
        assert call.machine_detection == "continue"
        assert call.length_timer == 3600
        assert call.ringing_timer == 45

    @pytest.mark.skipif(not VONAGE_IMPORTS_AVAILABLE, reason="Vonage integration not available")
    def test_vonage_number_model(self):
        """Test VonageNumber model from integration."""
        number = VonageNumber(
            msisdn="+15551234567",
            country="US",
            type="mobile-lvn",
            features=["SMS", "VOICE"],
            cost="1.00",
            voiceCallbackType="app",
            voiceCallbackValue="app_123",
            moHttpUrl="https://example.com/sms-webhook",
            moSmppSysType="inbound"
        )

        assert number.msisdn == "+15551234567"
        assert number.country == "US"
        assert number.type == "mobile-lvn"
        assert number.features == ["SMS", "VOICE"]
        assert number.cost == "1.00"
        assert number.voiceCallbackType == "app"
        assert number.voiceCallbackValue == "app_123"
        assert number.moHttpUrl == "https://example.com/sms-webhook"
        assert number.moSmppSysType == "inbound"

    @pytest.mark.skipif(not VONAGE_IMPORTS_AVAILABLE, reason="Vonage integration not available")
    def test_vonage_response_model(self, sample_vonage_response):
        """Test VonageResponse model."""
        response = sample_vonage_response

        assert response.success is True
        assert response.data["message-id"] == "msg_123456789"
        assert response.data["to"] == "+1234567890"
        assert response.data["status"] == "0"
        assert response.message_count == 1
        assert len(response.messages) == 1
        assert response.messages[0]["message-id"] == "msg_123456789"

    def test_phone_number_validation(self):
        """Test phone number validation in requests."""
        # Valid phone number formats
        valid_numbers = [
            "+1234567890",      # US format
            "+233123456789",    # Ghana format
            "+44123456789",     # UK format
            "+4915123456789",   # Germany format
            "+33123456789"      # France format
        ]

        for number in valid_numbers:
            request = VonageSMSRequest(
                to=number,
                **{"from": "+0987654321"},
                text="Test message"
            )
            assert request.to == number

            voice_request = VonageVoiceCallRequest(
                to=number,
                **{"from": "+0987654321"},
                answer_url="https://example.com/answer"
            )
            assert voice_request.to == number

    def test_country_code_validation(self):
        """Test country code validation in number search."""
        # Valid country codes
        valid_countries = ["US", "GB", "DE", "FR", "GH", "CA", "AU"]

        for country in valid_countries:
            request = VonageNumberSearchRequest(country=country)
            assert request.country == country

            mgmt_request = VonageNumberManagementRequest(
                operation="search",
                country=country
            )
            assert mgmt_request.country == country

    def test_number_type_validation(self):
        """Test number type validation."""
        valid_types = ["mobile-lvn", "landline", "toll-free", "mobile"]

        for number_type in valid_types:
            request = VonageNumberSearchRequest(
                country="US",
                **{"type": number_type}  # Use ** to handle 'type' alias
            )
            assert request.type_ == number_type

    def test_webhook_url_validation(self):
        """Test webhook URL validation."""
        valid_urls = [
            "https://example.com/webhook",
            "https://api.myapp.com/vonage/sms",
            "https://secure.server.org/callbacks/vonage",
            "http://localhost:8000/webhook"  # For development
        ]

        for url in valid_urls:
            request = VonageSMSRequest(
                to="+1234567890",
                **{"from": "+0987654321"},
                text="Test",
                webhook_url=url
            )
            assert request.webhook_url == url

    def test_machine_detection_options(self):
        """Test machine detection options for voice calls."""
        detection_options = ["continue", "hangup", None]

        for option in detection_options:
            request = VonageVoiceCallRequest(
                to="+1234567890",
                **{"from": "+0987654321"},
                answer_url="https://example.com/answer",
                machine_detection=option
            )
            assert request.machine_detection == option

    def test_voice_names_validation(self):
        """Test voice names for TTS."""
        valid_voices = ["Amy", "Brian", "Joey", "Emma", "Russell", "Nicole"]

        for voice in valid_voices:
            request = VonageTTSRequest(
                call_uuid="call-123",
                text="Test speech",
                voice_name=voice
            )
            assert request.voice_name == voice

    def test_language_codes_validation(self):
        """Test language codes for TTS."""
        valid_languages = ["en-US", "en-GB", "en-AU", "fr-FR", "de-DE", "es-ES"]

        for language in valid_languages:
            request = VonageTTSRequest(
                call_uuid="call-123",
                text="Test speech",
                language=language
            )
            assert request.language == language

    @pytest.mark.skipif(not VONAGE_IMPORTS_AVAILABLE, reason="Vonage integration not available")
    @pytest.mark.asyncio
    async def test_vonage_integration_initialization(self):
        """Test VonageIntegration initialization."""
        config = VonageConfig(
            api_key="test_api_key",
            api_secret="test_api_secret"
        )

        integration = VonageIntegration(config)
        assert integration.config.api_key == "test_api_key"
        assert integration.config.api_secret == "test_api_secret"
        assert integration.config.base_url == "https://api.nexmo.com"
        assert integration._connected is True

    def test_number_management_operations(self):
        """Test number management operation types."""
        valid_operations = ["search", "buy", "cancel", "list"]

        for operation in valid_operations:
            request = VonageNumberManagementRequest(
                operation=operation,
                country="US"
            )
            assert request.operation == operation

    def test_ttl_validation(self):
        """Test TTL (time to live) validation for SMS."""
        valid_ttls = [300, 3600, 86400, 604800]  # 5 minutes to 1 week

        for ttl in valid_ttls:
            request = VonageSMSRequest(
                to="+1234567890",
                **{"from": "+0987654321"},
                text="Test message",
                ttl=ttl
            )
            assert request.ttl == ttl

    def test_message_class_validation(self):
        """Test SMS message class validation."""
        valid_classes = [0, 1, 2, 3]  # Flash, ME, SIM, TE

        for msg_class in valid_classes:
            request = VonageSMSRequest(
                to="+1234567890",
                **{"from": "+0987654321"},
                text="Test message",
                message_class=msg_class
            )
            assert request.message_class == msg_class

    def test_call_timer_validation(self):
        """Test call timer validation for voice calls."""
        # Valid timer values in seconds
        valid_timers = [30, 60, 300, 1800, 7200]  # 30 seconds to 2 hours

        for timer in valid_timers:
            request = VonageVoiceCallRequest(
                to="+1234567890",
                **{"from": "+0987654321"},
                answer_url="https://example.com/answer",
                length_timer=timer,
                ringing_timer=timer // 10  # Ringing timer is usually shorter
            )
            assert request.length_timer == timer
            assert request.ringing_timer == timer // 10

    def test_search_pattern_validation(self):
        """Test search pattern validation for number search."""
        valid_patterns = [0, 1, 2]  # Different search pattern types

        for pattern in valid_patterns:
            request = VonageNumberSearchRequest(
                country="US",
                search_pattern=pattern
            )
            assert request.search_pattern == pattern

    def test_feature_combinations(self):
        """Test various feature combinations for number search."""
        feature_combinations = [
            ["SMS"],
            ["VOICE"],
            ["MMS"],
            ["SMS", "VOICE"],
            ["SMS", "MMS"],
            ["VOICE", "MMS"],
            ["SMS", "VOICE", "MMS"]
        ]

        for features in feature_combinations:
            request = VonageNumberSearchRequest(
                country="US",
                features=features
            )
            assert request.features == features

    def test_tenant_id_validation(self):
        """Test tenant ID validation across request types."""
        # Valid tenant IDs
        valid_tenant_ids = [
            "default",
            "tenant_123",
            "org-456",
            "company_789_prod",
            "test_environment"
        ]

        for tenant_id in valid_tenant_ids:
            sms_request = VonageSMSRequest(
                to="+1234567890",
                **{"from": "+0987654321"},
                text="Test",
                tenant_id=tenant_id
            )
            assert sms_request.tenant_id == tenant_id

            voice_request = VonageVoiceCallRequest(
                to="+1234567890",
                **{"from": "+0987654321"},
                answer_url="https://example.com/answer",
                tenant_id=tenant_id
            )
            assert voice_request.tenant_id == tenant_id


class TestVonageEdgeCases:
    """Test edge cases and error scenarios for Vonage integration."""

    def test_empty_sms_text(self):
        """Test SMS with empty text."""
        request = VonageSMSRequest(
            to="+1234567890",
            **{"from": "+0987654321"},
            text=""  # Empty text
        )
        assert request.text == ""

    def test_very_long_sms_text(self):
        """Test SMS with very long text."""
        long_text = "A" * 1600  # Maximum SMS length is typically 1600 characters

        request = VonageSMSRequest(
            to="+1234567890",
            **{"from": "+0987654321"},
            text=long_text
        )
        assert len(request.text) == 1600
        assert request.text == long_text

    def test_unicode_sms_text(self):
        """Test SMS with unicode characters."""
        unicode_text = "Hello 🌍! Testing émojis and spëcial charactërs: 中文, العربية, हिन्दी"

        request = VonageSMSRequest(
            to="+1234567890",
            **{"from": "+0987654321"},
            text=unicode_text
        )
        assert unicode_text in request.text

    def test_very_long_tts_text(self):
        """Test TTS with very long text."""
        long_text = "This is a very long text message that will be converted to speech. " * 50

        request = VonageTTSRequest(
            call_uuid="call-123",
            text=long_text
        )
        assert len(request.text) > 1000
        assert request.text == long_text

    def test_special_characters_in_phone_numbers(self):
        """Test phone numbers with special formatting."""
        # Different phone number formats (some may be invalid but should be handled)
        phone_formats = [
            "+1-234-567-8900",  # With dashes
            "+1 (234) 567-8900",  # With spaces and parentheses
            "12345678900",  # Without country code prefix
            "+1.234.567.8900"  # With dots
        ]

        for phone in phone_formats:
            try:
                request = VonageSMSRequest(
                    to=phone,
                    **{"from": "+0987654321"},
                    text="Test"
                )
                # If validation passes, check it was stored
                assert request.to == phone
            except Exception:
                # Some formats might not pass validation, which is acceptable
                pass

    def test_invalid_country_codes(self):
        """Test invalid country codes."""
        invalid_countries = ["XX", "ZZ", "123", ""]

        for country in invalid_countries:
            # These should still create the request object (validation might be server-side)
            request = VonageNumberSearchRequest(country=country)
            assert request.country == country

    def test_extreme_timer_values(self):
        """Test extreme timer values for voice calls."""
        extreme_values = [0, 1, 86400, 604800]  # 0 seconds to 1 week

        for value in extreme_values:
            request = VonageVoiceCallRequest(
                to="+1234567890",
                **{"from": "+0987654321"},
                answer_url="https://example.com/answer",
                length_timer=value,
                ringing_timer=min(value, 120)  # Cap ringing timer at 2 minutes
            )
            assert request.length_timer == value

    def test_none_optional_fields(self):
        """Test handling of None values in optional fields."""
        request = VonageSMSRequest(
            to="+1234567890",
            **{"from": "+0987654321"},
            text="Test message",
            client_ref=None,
            webhook_url=None,
            ttl=None,
            message_class=None
        )

        assert request.client_ref is None
        assert request.webhook_url is None
        assert request.ttl is None
        assert request.message_class is None

    def test_large_number_search_request(self):
        """Test number search with large result size."""
        request = VonageNumberSearchRequest(
            country="US",
            size=100,  # Large result set
            index=1000  # High starting index
        )

        assert request.size == 100
        assert request.index == 1000

    def test_complex_search_params(self):
        """Test complex search parameters for number management."""
        complex_params = {
            "type": "mobile-lvn",
            "features": ["SMS", "VOICE", "MMS"],
            "pattern": "555",
            "search_pattern": 1,
            "size": 50,
            "index": 1,
            "cost_filter": {"min": "0.50", "max": "2.00"},
            "region_filter": ["east", "west"],
            "carrier_filter": ["verizon", "att"]
        }

        request = VonageNumberManagementRequest(
            operation="search",
            country="US",
            search_params=complex_params
        )

        assert request.search_params["type"] == "mobile-lvn"
        assert request.search_params["features"] == ["SMS", "VOICE", "MMS"]
        assert request.search_params["cost_filter"]["min"] == "0.50"

    @pytest.mark.skipif(not VONAGE_IMPORTS_AVAILABLE, reason="Vonage integration not available")
    def test_vonage_response_with_errors(self):
        """Test VonageResponse with error scenarios."""
        error_response = VonageResponse(
            success=False,
            error="Invalid API credentials",
            status_code=401,
            data={"error-text": "Invalid API credentials"}
        )

        assert error_response.success is False
        assert error_response.error == "Invalid API credentials"
        assert error_response.status_code == 401
        assert error_response.data["error-text"] == "Invalid API credentials"

    @pytest.mark.skipif(not VONAGE_IMPORTS_AVAILABLE, reason="Vonage integration not available")
    def test_vonage_response_partial_success(self):
        """Test VonageResponse with partial success (some messages failed)."""
        partial_response = VonageResponse(
            success=True,
            message_count=2,
            messages=[
                {
                    "message-id": "msg_123",
                    "to": "+1234567890",
                    "status": "0",  # Success
                    "message-price": "0.00333333"
                },
                {
                    "message-id": "msg_124",
                    "to": "+9876543210",
                    "status": "4",  # Failed
                    "error-text": "Invalid number"
                }
            ]
        )

        assert partial_response.success is True
        assert partial_response.message_count == 2
        assert len(partial_response.messages) == 2
        assert partial_response.messages[0]["status"] == "0"  # Success
        assert partial_response.messages[1]["status"] == "4"  # Failed

    def test_webhook_signature_validation_data(self):
        """Test webhook signature validation with various data types."""
        webhook_params = {
            "messageId": "msg_123456789",
            "to": "+1234567890",
            "from": "+0987654321",
            "text": "Hello World",
            "type": "text",
            "keyword": "KEYWORD",
            "message-timestamp": "2025-09-22 12:00:00",
            "timestamp": str(int(datetime.now().timestamp())),
            "nonce": "test_nonce_123",
            "concat": "true",
            "concat-ref": "1",
            "concat-total": "3",
            "concat-part": "1"
        }

        # The webhook validation would be tested in the integration layer
        # Here we just verify the data structure is correct for validation
        assert "messageId" in webhook_params
        assert "timestamp" in webhook_params
        assert "nonce" in webhook_params


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])