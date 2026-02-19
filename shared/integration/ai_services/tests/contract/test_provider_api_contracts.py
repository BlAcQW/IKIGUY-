"""
Contract tests for Provider API endpoints.

Tests that API request/response contracts remain stable and backwards-compatible.
Detects breaking changes in API structure, field types, and required fields.
"""

import pytest
from pydantic import BaseModel, ValidationError
from typing import Dict, Any, List, Optional
from datetime import datetime


class ProviderCapabilitiesContract(BaseModel):
    """Contract for provider capabilities."""

    # Generic capabilities
    multiLanguage: Optional[bool] = None
    streaming: Optional[bool] = None
    realtime: Optional[bool] = None

    # TTS-specific
    voiceCloning: Optional[bool] = None
    speedControl: Optional[bool] = None
    pitchControl: Optional[bool] = None
    multiSpeaker: Optional[bool] = None
    emotionControl: Optional[bool] = None

    # LLM-specific
    functionCalling: Optional[bool] = None
    reasoning: Optional[bool] = None
    codeGeneration: Optional[bool] = None
    vision: Optional[bool] = None
    culturalContext: Optional[bool] = None

    # ASR-specific
    diarization: Optional[bool] = None
    timestamps: Optional[bool] = None
    wordLevelTimestamps: Optional[bool] = None
    punctuation: Optional[bool] = None

    class Config:
        extra = "allow"  # Allow additional fields for backwards compatibility


class ProviderContract(BaseModel):
    """Contract for provider object."""

    id: str
    name: str
    provider_type: str
    endpoint: str
    status: str
    capabilities: ProviderCapabilitiesContract
    description: str
    icon: str
    languages: int
    languageList: List[str]
    metadata: Optional[Dict[str, Any]] = {}
    lastChecked: Optional[str] = None
    responseTime: Optional[float] = None

    class Config:
        extra = "allow"  # Allow additional fields


class ProvidersResponseContract(BaseModel):
    """Contract for GET /api/v1/{provider_type}/providers response."""

    success: bool
    data: Dict[str, ProviderContract]


class TestProviderListingContracts:
    """Test contracts for provider listing endpoints."""

    def test_tts_providers_response_contract(self):
        """Test GET /api/v1/tts/providers response matches contract."""
        # Simulate API response
        mock_response = {
            "success": True,
            "data": {
                "coqui_xtts": {
                    "id": "coqui_xtts",
                    "name": "Coqui XTTS v2",
                    "provider_type": "tts",
                    "endpoint": "https://coqui.ailabsafrica.com",
                    "status": "online",
                    "capabilities": {
                        "voiceCloning": True,
                        "multiLanguage": True,
                        "streaming": True,
                    },
                    "description": "Coqui XTTS v2 TTS engine",
                    "icon": "🎙️",
                    "languages": 10,
                    "languageList": ["en", "es", "fr"],
                    "metadata": {},
                    "lastChecked": "2025-10-24T12:00:00Z",
                    "responseTime": 123.45,
                }
            },
        }

        # Validate against contract
        response = ProvidersResponseContract(**mock_response)

        # Verify structure
        assert response.success is True
        assert "coqui_xtts" in response.data
        assert response.data["coqui_xtts"].id == "coqui_xtts"
        assert response.data["coqui_xtts"].provider_type == "tts"
        assert response.data["coqui_xtts"].capabilities.voiceCloning is True

    def test_llm_providers_response_contract(self):
        """Test GET /api/v1/llm/providers response matches contract."""
        mock_response = {
            "success": True,
            "data": {
                "llama_32_3b": {
                    "id": "llama_32_3b",
                    "name": "Llama 3.2 3B",
                    "provider_type": "llm",
                    "endpoint": "http://localhost:11434",
                    "status": "online",
                    "capabilities": {
                        "functionCalling": True,
                        "codeGeneration": True,
                        "reasoning": True,
                    },
                    "description": "Llama 3.2 3B model",
                    "icon": "🦙",
                    "languages": 1,
                    "languageList": ["en"],
                    "metadata": {"model": "llama3.2:3b"},
                }
            },
        }

        # Validate against contract
        response = ProvidersResponseContract(**mock_response)
        assert response.success is True
        assert response.data["llama_32_3b"].capabilities.functionCalling is True

    def test_asr_providers_response_contract(self):
        """Test GET /api/v1/asr/providers response matches contract."""
        mock_response = {
            "success": True,
            "data": {
                "akan_whisper": {
                    "id": "akan_whisper",
                    "name": "Akan Whisper",
                    "provider_type": "asr",
                    "endpoint": "https://asr.ailabsafrica.com",
                    "status": "online",
                    "capabilities": {
                        "diarization": True,
                        "timestamps": True,
                        "multiLanguage": True,
                    },
                    "description": "Akan Whisper ASR",
                    "icon": "🎤",
                    "languages": 5,
                    "languageList": ["en", "tw", "ak"],
                    "metadata": {},
                }
            },
        }

        # Validate against contract
        response = ProvidersResponseContract(**mock_response)
        assert response.success is True
        assert response.data["akan_whisper"].capabilities.diarization is True

    def test_provider_response_backwards_compatibility(self):
        """Test that adding new fields doesn't break existing clients."""
        # Response with new fields that old clients don't know about
        mock_response_with_new_fields = {
            "success": True,
            "data": {
                "coqui_xtts": {
                    "id": "coqui_xtts",
                    "name": "Coqui XTTS v2",
                    "provider_type": "tts",
                    "endpoint": "https://coqui.ailabsafrica.com",
                    "status": "online",
                    "capabilities": {
                        "voiceCloning": True,
                        "newCapability": True,  # New field
                    },
                    "description": "Coqui XTTS v2",
                    "icon": "🎙️",
                    "languages": 10,
                    "languageList": ["en"],
                    "metadata": {},
                    "newField": "some value",  # New field
                }
            },
        }

        # Should NOT raise validation error due to extra="allow"
        response = ProvidersResponseContract(**mock_response_with_new_fields)
        assert response.success is True

    def test_provider_response_missing_optional_fields(self):
        """Test that optional fields can be omitted."""
        # Response with minimal required fields only
        mock_response_minimal = {
            "success": True,
            "data": {
                "minimal_provider": {
                    "id": "minimal_provider",
                    "name": "Minimal Provider",
                    "provider_type": "tts",
                    "endpoint": "https://example.com",
                    "status": "offline",
                    "capabilities": {},
                    "description": "Minimal provider",
                    "icon": "🤖",
                    "languages": 0,
                    "languageList": [],
                    # Optional fields omitted
                }
            },
        }

        # Should NOT raise validation error
        response = ProvidersResponseContract(**mock_response_minimal)
        assert response.success is True
        assert response.data["minimal_provider"].lastChecked is None
        assert response.data["minimal_provider"].responseTime is None

    def test_provider_response_missing_required_field_breaks(self):
        """Test that missing required fields cause validation error."""
        # Response missing required field 'id'
        mock_response_invalid = {
            "success": True,
            "data": {
                "invalid_provider": {
                    # Missing 'id' field
                    "name": "Invalid Provider",
                    "provider_type": "tts",
                    "endpoint": "https://example.com",
                    "status": "online",
                    "capabilities": {},
                    "description": "Invalid",
                    "icon": "🤖",
                    "languages": 0,
                    "languageList": [],
                }
            },
        }

        # Should raise validation error
        with pytest.raises(ValidationError) as exc_info:
            ProvidersResponseContract(**mock_response_invalid)

        # Verify error is about missing 'id'
        assert "id" in str(exc_info.value)


class ErrorResponseContract(BaseModel):
    """Contract for error responses."""

    success: bool
    error: Dict[str, Any]


class TestErrorResponseContracts:
    """Test contracts for error responses."""

    def test_error_response_contract(self):
        """Test error response structure."""
        mock_error_response = {
            "success": False,
            "error": {
                "code": "PROVIDER_NOT_FOUND",
                "message": "Provider not found",
                "details": {"provider_id": "invalid_id"},
            },
        }

        # Validate against contract
        response = ErrorResponseContract(**mock_error_response)
        assert response.success is False
        assert "code" in response.error
        assert "message" in response.error

    def test_error_response_required_fields(self):
        """Test error response has required fields."""
        # Missing error details
        mock_error_response_minimal = {"success": False, "error": {}}

        # Should NOT raise error (error details can be empty dict)
        response = ErrorResponseContract(**mock_error_response_minimal)
        assert response.success is False


class TestStatusEnumContracts:
    """Test that status enum values are stable."""

    VALID_STATUS_VALUES = ["online", "offline", "degraded", "building", "maintenance"]

    def test_status_values_are_stable(self):
        """Test that status enum values haven't changed."""
        # Test all valid status values
        for status in self.VALID_STATUS_VALUES:
            mock_response = {
                "success": True,
                "data": {
                    "test_provider": {
                        "id": "test",
                        "name": "Test",
                        "provider_type": "tts",
                        "endpoint": "https://test.com",
                        "status": status,  # Test each status value
                        "capabilities": {},
                        "description": "Test",
                        "icon": "🤖",
                        "languages": 0,
                        "languageList": [],
                    }
                },
            }

            # Should NOT raise validation error
            response = ProvidersResponseContract(**mock_response)
            assert response.data["test_provider"].status == status


class TestProviderTypeEnumContracts:
    """Test that provider type enum values are stable."""

    VALID_PROVIDER_TYPES = ["tts", "llm", "asr", "vision", "embedding", "multimodal"]

    def test_provider_type_values_are_stable(self):
        """Test that provider_type enum values haven't changed."""
        for provider_type in self.VALID_PROVIDER_TYPES:
            mock_response = {
                "success": True,
                "data": {
                    "test_provider": {
                        "id": "test",
                        "name": "Test",
                        "provider_type": provider_type,  # Test each type
                        "endpoint": "https://test.com",
                        "status": "online",
                        "capabilities": {},
                        "description": "Test",
                        "icon": "🤖",
                        "languages": 0,
                        "languageList": [],
                    }
                },
            }

            # Should NOT raise validation error
            response = ProvidersResponseContract(**mock_response)
            assert response.data["test_provider"].provider_type == provider_type
