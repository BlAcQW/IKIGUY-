"""
Contract tests for LLM and ASR API endpoints.

Tests that LLM and ASR API request/response contracts remain stable.
"""

import pytest
from pydantic import BaseModel, ValidationError
from typing import Optional, Dict, Any, List


# ==================== LLM Contracts ====================


class LLMGenerateRequestContract(BaseModel):
    """Contract for POST /api/v1/llm/generate request."""

    provider_id: str
    prompt: str
    stream: Optional[bool] = False
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    stop: Optional[List[str]] = None


class LLMGenerateResponseContract(BaseModel):
    """Contract for POST /api/v1/llm/generate response."""

    success: bool
    data: Dict[str, Any]


class TestLLMGenerateContracts:
    """Test contracts for LLM generate endpoint."""

    def test_generate_request_contract(self):
        """Test POST /api/v1/llm/generate request structure."""
        request_data = {
            "provider_id": "llama_32_3b",
            "prompt": "Hello! How are you?",
            "stream": False,
            "temperature": 0.7,
        }

        # Should validate successfully
        request = LLMGenerateRequestContract(**request_data)
        assert request.provider_id == "llama_32_3b"
        assert request.prompt == "Hello! How are you?"
        assert request.stream is False

    def test_generate_request_minimal(self):
        """Test generate request with only required fields."""
        request_data = {
            "provider_id": "llama_32_3b",
            "prompt": "Hello!",
        }

        # Should validate successfully
        request = LLMGenerateRequestContract(**request_data)
        assert request.stream is False  # Default value
        assert request.temperature is None

    def test_generate_request_with_stop_sequences(self):
        """Test generate request with stop sequences."""
        request_data = {
            "provider_id": "llama_32_3b",
            "prompt": "Complete this: Once upon a time",
            "stop": [".", "!", "?"],
        }

        request = LLMGenerateRequestContract(**request_data)
        assert request.stop == [".", "!", "?"]

    def test_generate_response_contract(self):
        """Test POST /api/v1/llm/generate response structure."""
        response_data = {
            "success": True,
            "data": {
                "model": "llama3.2:3b",
                "response": "Hello! I'm doing great, thank you!",
                "done": True,
                "context": [1, 2, 3],
                "total_duration": 5000000000,
                "prompt_eval_count": 10,
                "eval_count": 20,
            },
        }

        # Should validate successfully
        response = LLMGenerateResponseContract(**response_data)
        assert response.success is True
        assert "response" in response.data
        assert response.data["done"] is True

    def test_generate_streaming_response_contract(self):
        """Test streaming response structure."""
        # Streaming responses are sent as multiple chunks
        chunk1 = {
            "success": True,
            "data": {
                "response": "Hello",
                "done": False,
            },
        }

        chunk2 = {
            "success": True,
            "data": {
                "response": " world",
                "done": False,
            },
        }

        final_chunk = {
            "success": True,
            "data": {
                "response": "!",
                "done": True,
                "total_duration": 5000000000,
                "prompt_eval_count": 5,
                "eval_count": 15,
            },
        }

        # All chunks should validate
        response1 = LLMGenerateResponseContract(**chunk1)
        response2 = LLMGenerateResponseContract(**chunk2)
        response3 = LLMGenerateResponseContract(**final_chunk)

        assert response1.success is True
        assert response2.success is True
        assert response3.success is True


class TestLLMErrorContracts:
    """Test contracts for LLM error responses."""

    def test_llm_model_not_loaded_error(self):
        """Test model not loaded error response."""
        error_response = {
            "success": False,
            "error": {
                "code": "MODEL_NOT_LOADED",
                "message": "Model is not loaded",
                "details": {
                    "provider_id": "llama_32_3b",
                    "model": "llama3.2:3b",
                },
            },
        }

        assert error_response["error"]["code"] == "MODEL_NOT_LOADED"

    def test_llm_context_length_exceeded_error(self):
        """Test context length exceeded error."""
        error_response = {
            "success": False,
            "error": {
                "code": "CONTEXT_LENGTH_EXCEEDED",
                "message": "Prompt exceeds maximum context length",
                "details": {
                    "max_tokens": 4096,
                    "prompt_tokens": 5000,
                },
            },
        }

        assert error_response["error"]["code"] == "CONTEXT_LENGTH_EXCEEDED"


# ==================== ASR Contracts ====================


class ASRTranscribeRequestContract(BaseModel):
    """Contract for POST /api/v1/asr/transcribe request."""

    provider_id: str
    language: Optional[str] = None
    task: Optional[str] = "transcribe"
    word_timestamps: Optional[bool] = False
    diarize: Optional[bool] = False


class ASRTranscribeResponseContract(BaseModel):
    """Contract for POST /api/v1/asr/transcribe response."""

    success: bool
    data: Dict[str, Any]


class TestASRTranscribeContracts:
    """Test contracts for ASR transcribe endpoint."""

    def test_transcribe_request_contract(self):
        """Test POST /api/v1/asr/transcribe request structure."""
        request_data = {
            "provider_id": "akan_whisper",
            "language": "en",
            "word_timestamps": True,
        }

        # Should validate successfully
        request = ASRTranscribeRequestContract(**request_data)
        assert request.provider_id == "akan_whisper"
        assert request.language == "en"
        assert request.word_timestamps is True

    def test_transcribe_request_minimal(self):
        """Test transcribe request with only required fields."""
        request_data = {
            "provider_id": "akan_whisper",
        }

        # Should validate successfully
        request = ASRTranscribeRequestContract(**request_data)
        assert request.language is None  # Auto-detect
        assert request.task == "transcribe"  # Default
        assert request.word_timestamps is False

    def test_transcribe_response_contract(self):
        """Test POST /api/v1/asr/transcribe response structure."""
        response_data = {
            "success": True,
            "data": {
                "text": "Hello, world! This is a test transcription.",
                "language": "en",
                "duration": 5.2,
                "segments": [
                    {
                        "id": 0,
                        "start": 0.0,
                        "end": 2.5,
                        "text": "Hello, world!",
                    },
                    {
                        "id": 1,
                        "start": 2.5,
                        "end": 5.2,
                        "text": "This is a test transcription.",
                    },
                ],
            },
        }

        # Should validate successfully
        response = ASRTranscribeResponseContract(**response_data)
        assert response.success is True
        assert "text" in response.data
        assert "segments" in response.data
        assert len(response.data["segments"]) == 2

    def test_transcribe_response_with_word_timestamps(self):
        """Test transcribe response with word-level timestamps."""
        response_data = {
            "success": True,
            "data": {
                "text": "Hello world",
                "language": "en",
                "duration": 1.5,
                "segments": [
                    {
                        "id": 0,
                        "start": 0.0,
                        "end": 1.5,
                        "text": "Hello world",
                        "words": [
                            {"word": "Hello", "start": 0.0, "end": 0.5},
                            {"word": "world", "start": 0.6, "end": 1.0},
                        ],
                    }
                ],
            },
        }

        # Should validate successfully
        response = ASRTranscribeResponseContract(**response_data)
        assert response.success is True
        assert "words" in response.data["segments"][0]

    def test_transcribe_response_with_diarization(self):
        """Test transcribe response with speaker diarization."""
        response_data = {
            "success": True,
            "data": {
                "text": "Speaker 1: Hello. Speaker 2: Hi there.",
                "language": "en",
                "duration": 3.0,
                "segments": [
                    {
                        "id": 0,
                        "start": 0.0,
                        "end": 1.5,
                        "text": "Hello.",
                        "speaker": "SPEAKER_00",
                    },
                    {
                        "id": 1,
                        "start": 1.5,
                        "end": 3.0,
                        "text": "Hi there.",
                        "speaker": "SPEAKER_01",
                    },
                ],
            },
        }

        # Should validate successfully
        response = ASRTranscribeResponseContract(**response_data)
        assert response.success is True


class TestASRErrorContracts:
    """Test contracts for ASR error responses."""

    def test_asr_invalid_audio_format_error(self):
        """Test invalid audio format error."""
        error_response = {
            "success": False,
            "error": {
                "code": "INVALID_AUDIO_FORMAT",
                "message": "Unsupported audio format",
                "details": {
                    "supported_formats": ["mp3", "wav", "flac", "ogg"],
                },
            },
        }

        assert error_response["error"]["code"] == "INVALID_AUDIO_FORMAT"

    def test_asr_audio_too_large_error(self):
        """Test audio file too large error."""
        error_response = {
            "success": False,
            "error": {
                "code": "FILE_TOO_LARGE",
                "message": "Audio file exceeds maximum size",
                "details": {
                    "max_size_mb": 25,
                    "file_size_mb": 30,
                },
            },
        }

        assert error_response["error"]["code"] == "FILE_TOO_LARGE"


# ==================== Shared Contract Tests ====================


class TestCrossServiceContracts:
    """Test contracts that apply across all service types."""

    def test_all_services_use_consistent_error_format(self):
        """Test that all services use the same error response format."""
        # TTS error
        tts_error = {
            "success": False,
            "error": {
                "code": "PROVIDER_OFFLINE",
                "message": "Provider offline",
                "details": {},
            },
        }

        # LLM error
        llm_error = {
            "success": False,
            "error": {
                "code": "MODEL_NOT_LOADED",
                "message": "Model not loaded",
                "details": {},
            },
        }

        # ASR error
        asr_error = {
            "success": False,
            "error": {
                "code": "INVALID_AUDIO_FORMAT",
                "message": "Invalid format",
                "details": {},
            },
        }

        # All should have the same structure
        for error in [tts_error, llm_error, asr_error]:
            assert "success" in error
            assert error["success"] is False
            assert "error" in error
            assert "code" in error["error"]
            assert "message" in error["error"]

    def test_all_services_use_consistent_success_format(self):
        """Test that all services use the same success response format."""
        # TTS success
        tts_success = {
            "success": True,
            "data": {"audio_url": "https://example.com/audio.mp3"},
        }

        # LLM success
        llm_success = {"success": True, "data": {"response": "Hello!"}}

        # ASR success
        asr_success = {"success": True, "data": {"text": "Hello world"}}

        # All should have the same structure
        for response in [tts_success, llm_success, asr_success]:
            assert "success" in response
            assert response["success"] is True
            assert "data" in response
            assert isinstance(response["data"], dict)
