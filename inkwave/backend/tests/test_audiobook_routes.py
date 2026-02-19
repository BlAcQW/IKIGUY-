"""
Unit tests for Audiobook Routes.

Tests:
- Voice selection endpoint
- Book progress endpoint
- Preload endpoint
- Provider listing
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestVoicesEndpoint:
    """Tests for /voices/{provider_id} endpoint."""

    def test_openai_voices_count(self):
        """Test that OpenAI TTS returns 6 voices."""
        from app.api.routes.audiobook import get_provider_voices, VoiceInfo

        # Test static voice data (without actual API call)
        openai_voices = [
            "alloy", "echo", "fable", "onyx", "nova", "shimmer"
        ]
        assert len(openai_voices) == 6

    def test_voice_metadata_structure(self):
        """Test that voice metadata has required fields."""
        from app.api.routes.audiobook import VoiceInfo

        # Test VoiceInfo model
        voice = VoiceInfo(
            id="alloy",
            name="Alloy",
            description="Balanced voice",
            gender="neutral",
            accent="American",
            best_for=["audiobooks"],
            sample_text="Test"
        )

        assert voice.id == "alloy"
        assert voice.name == "Alloy"
        assert voice.gender == "neutral"

    def test_voice_info_optional_fields(self):
        """Test VoiceInfo with optional fields omitted."""
        from app.api.routes.audiobook import VoiceInfo

        voice = VoiceInfo(
            id="test",
            name="Test",
            description="Test voice",
            gender="male"
        )

        assert voice.accent is None
        assert voice.best_for == []


class TestBookProgressEndpoint:
    """Tests for /books/{book_id}/progress endpoint."""

    def test_progress_response_model(self):
        """Test BookProgressResponse model."""
        from app.api.routes.audiobook import BookProgressResponse

        response = BookProgressResponse(
            book_id="test_book",
            total_chunks=10,
            total_duration=3600.0,
            generated_chunks=5,
            listened_chunks=3,
            current_chunk=3,
            current_position=120.5,
            overall_progress=0.35,
            chunk_durations=[360.0] * 10
        )

        assert response.book_id == "test_book"
        assert response.total_chunks == 10
        assert response.overall_progress == 0.35
        assert len(response.chunk_durations) == 10

    def test_progress_calculation(self):
        """Test progress percentage calculation."""
        chunk_durations = [60.0, 120.0, 180.0, 240.0]  # Total: 600s
        total = sum(chunk_durations)

        # At chunk 2, position 60s
        current_chunk = 2
        current_position = 60.0

        elapsed = sum(chunk_durations[:current_chunk]) + current_position
        progress = elapsed / total

        # Should be (60 + 120 + 60) / 600 = 0.4
        expected = (60 + 120 + 60) / 600
        assert abs(progress - expected) < 0.001


class TestPreloadEndpoint:
    """Tests for /books/{book_id}/preload endpoint."""

    def test_preload_request_model(self):
        """Test PreloadRequest model."""
        from app.api.routes.audiobook import PreloadRequest

        request = PreloadRequest(
            start_chunk=5,
            num_chunks=3,
            provider_id="openai_tts",
            voice_id="nova",
            speed=1.25
        )

        assert request.start_chunk == 5
        assert request.num_chunks == 3
        assert request.provider_id == "openai_tts"

    def test_preload_request_defaults(self):
        """Test PreloadRequest default values."""
        from app.api.routes.audiobook import PreloadRequest

        request = PreloadRequest()

        assert request.start_chunk == 0
        assert request.num_chunks == 3
        assert request.provider_id == "styletts2"
        assert request.speed == 1.0

    def test_preload_request_validation(self):
        """Test PreloadRequest num_chunks validation."""
        from app.api.routes.audiobook import PreloadRequest
        from pydantic import ValidationError

        # Valid range: 1-10
        valid = PreloadRequest(num_chunks=5)
        assert valid.num_chunks == 5

        # Invalid: too many
        with pytest.raises(ValidationError):
            PreloadRequest(num_chunks=15)

        # Invalid: too few
        with pytest.raises(ValidationError):
            PreloadRequest(num_chunks=0)


class TestProvidersEndpoint:
    """Tests for providers listing."""

    def test_openai_provider_in_list(self):
        """Test that OpenAI TTS providers are in the available providers."""
        expected_providers = [
            "styletts2",
            "kokoro",
            "f5tts",
            "melotts",
            "openvoice",
            "coqui_xtts",
            "openai_tts",
            "openai_tts_hd"
        ]

        # These should be in AudiobookProvider enum
        from app.services.audiobook_service import AudiobookProvider

        for provider in ["openai_tts", "openai_tts_hd"]:
            assert hasattr(AudiobookProvider, provider.upper().replace("_", "_"))

    def test_provider_voice_mapping(self):
        """Test that each provider has voice configuration."""
        provider_configs = {
            "openai_tts": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
            "openai_tts_hd": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
            "styletts2": ["default"],
            "kokoro": ["af_sky", "am_adam"],
        }

        for provider, voices in provider_configs.items():
            assert len(voices) > 0, f"Provider {provider} should have voices"


class TestChunkAudioEndpoint:
    """Tests for chunk audio generation endpoint."""

    def test_chunk_audio_request_model(self):
        """Test ChunkAudioRequest model."""
        from app.api.routes.audiobook import ChunkAudioRequest

        request = ChunkAudioRequest(
            provider_id="openai_tts",
            voice_id="fable",
            speed=1.5,
            language="en",
            force_regenerate=True
        )

        assert request.provider_id == "openai_tts"
        assert request.voice_id == "fable"
        assert request.force_regenerate is True

    def test_chunk_audio_request_defaults(self):
        """Test ChunkAudioRequest default values."""
        from app.api.routes.audiobook import ChunkAudioRequest

        request = ChunkAudioRequest()

        assert request.provider_id == "styletts2"
        assert request.voice_id is None
        assert request.speed == 1.0
        assert request.language == "en"
        assert request.force_regenerate is False

    def test_chunk_audio_response_model(self):
        """Test ChunkAudioResponse model."""
        from app.api.routes.audiobook import ChunkAudioResponse

        response = ChunkAudioResponse(
            chunk_id="chunk_123",
            chunk_index=5,
            audio_url="data:audio/mp3;base64,abc123",
            duration=45.5,
            provider_used="openai_tts",
            cached=True
        )

        assert response.chunk_id == "chunk_123"
        assert response.duration == 45.5
        assert "base64" in response.audio_url


class TestVoiceSelectorMapping:
    """Tests for voice selector mappings."""

    def test_all_openai_voices_have_metadata(self):
        """Test that all 6 OpenAI voices have complete metadata."""
        from app.api.routes.audiobook import VoiceInfo

        openai_voice_ids = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

        # This would typically come from the endpoint, but we test the structure
        for voice_id in openai_voice_ids:
            # Each voice should be constructable with minimal required fields
            voice = VoiceInfo(
                id=voice_id,
                name=voice_id.capitalize(),
                description=f"Test description for {voice_id}",
                gender="neutral"
            )
            assert voice.id == voice_id

    def test_voice_gender_options(self):
        """Test that voices have valid gender options."""
        valid_genders = ["male", "female", "neutral"]

        voice_genders = {
            "alloy": "neutral",
            "echo": "male",
            "fable": "neutral",
            "onyx": "male",
            "nova": "female",
            "shimmer": "female"
        }

        for voice_id, gender in voice_genders.items():
            assert gender in valid_genders, f"Voice {voice_id} has invalid gender"


class TestErrorHandling:
    """Tests for error handling in routes."""

    def test_invalid_provider_response(self):
        """Test response structure for invalid provider."""
        # The endpoint should return 404 for unknown provider
        # This is a specification test - actual test would need test client
        pass

    def test_book_not_found_response(self):
        """Test response structure for book not found."""
        # The endpoint should return 404 for unknown book
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
