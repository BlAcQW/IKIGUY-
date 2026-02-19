"""
Contract tests for TTS API endpoints.

Tests that TTS API request/response contracts remain stable.
"""

import pytest
from pydantic import BaseModel, ValidationError
from typing import Optional, Dict, Any


class TTSSynthesizeRequestContract(BaseModel):
    """Contract for POST /api/v1/tts/synthesize request."""

    provider_id: str
    text: str
    language: Optional[str] = "en"
    speaker: Optional[str] = None
    speed: Optional[float] = None
    pitch: Optional[float] = None


class TTSSynthesizeResponseContract(BaseModel):
    """Contract for POST /api/v1/tts/synthesize response."""

    success: bool
    data: Dict[str, Any]

    class Config:
        extra = "allow"


class TTSVoiceCloneRequestContract(BaseModel):
    """Contract for POST /api/v1/tts/clone request."""

    provider_id: str
    text: str
    language: Optional[str] = "en"
    # Note: audio_file is sent as multipart/form-data


class TTSVoiceCloneResponseContract(BaseModel):
    """Contract for POST /api/v1/tts/clone response."""

    success: bool
    data: Dict[str, Any]


class TestTTSSynthesizeContracts:
    """Test contracts for TTS synthesize endpoint."""

    def test_synthesize_request_contract(self):
        """Test POST /api/v1/tts/synthesize request structure."""
        # Valid request
        request_data = {
            "provider_id": "coqui_xtts",
            "text": "Hello, world!",
            "language": "en",
            "speaker": "default",
        }

        # Should validate successfully
        request = TTSSynthesizeRequestContract(**request_data)
        assert request.provider_id == "coqui_xtts"
        assert request.text == "Hello, world!"

    def test_synthesize_request_minimal(self):
        """Test synthesize request with only required fields."""
        request_data = {
            "provider_id": "coqui_xtts",
            "text": "Hello!",
        }

        # Should validate successfully
        request = TTSSynthesizeRequestContract(**request_data)
        assert request.language == "en"  # Default value
        assert request.speaker is None

    def test_synthesize_request_missing_required_field(self):
        """Test that missing required fields cause validation error."""
        request_data = {
            # Missing 'provider_id'
            "text": "Hello!",
        }

        with pytest.raises(ValidationError) as exc_info:
            TTSSynthesizeRequestContract(**request_data)

        assert "provider_id" in str(exc_info.value)

    def test_synthesize_response_contract(self):
        """Test POST /api/v1/tts/synthesize response structure."""
        response_data = {
            "success": True,
            "data": {
                "audio_url": "https://cdn.ailabsafrica.com/audio/123.mp3",
                "duration_ms": 2340,
                "format": "mp3",
                "provider_id": "coqui_xtts",
            },
        }

        # Should validate successfully
        response = TTSSynthesizeResponseContract(**response_data)
        assert response.success is True
        assert "audio_url" in response.data
        assert response.data["audio_url"].endswith(".mp3")

    def test_synthesize_response_backwards_compatibility(self):
        """Test that adding new response fields doesn't break clients."""
        response_data = {
            "success": True,
            "data": {
                "audio_url": "https://cdn.ailabsafrica.com/audio/123.mp3",
                "duration_ms": 2340,
                "format": "mp3",
                "new_field": "new value",  # New field
                "cost": 0.015,  # New field
            },
        }

        # Should NOT raise validation error
        response = TTSSynthesizeResponseContract(**response_data)
        assert response.success is True


class TestTTSVoiceCloneContracts:
    """Test contracts for TTS voice cloning endpoint."""

    def test_voice_clone_request_contract(self):
        """Test POST /api/v1/tts/clone request structure."""
        request_data = {
            "provider_id": "coqui_xtts",
            "text": "Hello, this is a cloned voice!",
            "language": "en",
        }

        # Should validate successfully
        request = TTSVoiceCloneRequestContract(**request_data)
        assert request.provider_id == "coqui_xtts"

    def test_voice_clone_response_contract(self):
        """Test POST /api/v1/tts/clone response structure."""
        response_data = {
            "success": True,
            "data": {
                "audio_url": "https://cdn.ailabsafrica.com/audio/cloned_123.mp3",
                "duration_ms": 3500,
                "voice_id": "custom_voice_123",
                "format": "mp3",
            },
        }

        # Should validate successfully
        response = TTSVoiceCloneResponseContract(**response_data)
        assert response.success is True
        assert "voice_id" in response.data


class TestTTSErrorContracts:
    """Test contracts for TTS error responses."""

    def test_tts_validation_error_response(self):
        """Test validation error response structure."""
        error_response = {
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request data",
                "details": {
                    "field": "text",
                    "error": "Field required",
                },
            },
        }

        # Should have correct structure
        assert error_response["success"] is False
        assert error_response["error"]["code"] == "VALIDATION_ERROR"

    def test_tts_provider_offline_error(self):
        """Test provider offline error response."""
        error_response = {
            "success": False,
            "error": {
                "code": "PROVIDER_OFFLINE",
                "message": "Provider is currently offline",
                "details": {
                    "provider_id": "coqui_xtts",
                    "status": "offline",
                },
            },
        }

        assert error_response["error"]["code"] == "PROVIDER_OFFLINE"


class TestTTSProviderSpecificContracts:
    """Test provider-specific TTS contracts."""

    def test_coqui_xtts_specific_parameters(self):
        """Test Coqui XTTS specific parameters."""
        request_data = {
            "provider_id": "coqui_xtts",
            "text": "Hello!",
            "language": "en",
            "speaker": "custom_speaker",
            "speed": 1.2,
        }

        request = TTSSynthesizeRequestContract(**request_data)
        assert request.speed == 1.2

    def test_melotts_specific_parameters(self):
        """Test MeloTTS specific parameters."""
        request_data = {
            "provider_id": "melotts",
            "text": "Hello!",
            "language": "en",
            "speed": 1.5,
        }

        request = TTSSynthesizeRequestContract(**request_data)
        assert request.speed == 1.5
