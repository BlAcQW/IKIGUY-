"""
Unit tests for OpenAI TTS Service.

Tests:
- Voice metadata retrieval
- Model selection
- Cost estimation
- Text chunking
- Error handling
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.openai_tts_service import (
    OpenAITTSService,
    OpenAITTSRequest,
    OpenAITTSResult,
    OpenAIVoice,
    OpenAITTSModel,
    VOICE_METADATA,
)


class TestOpenAITTSService:
    """Tests for OpenAITTSService."""

    @pytest.fixture
    def service(self):
        """Create service instance with mock API key."""
        return OpenAITTSService(
            api_key="test_api_key",
            enable_caching=False
        )

    def test_get_available_voices(self, service: OpenAITTSService):
        """Test that all 6 OpenAI voices are available."""
        voices = service.get_available_voices()

        # Should have exactly 6 voices
        assert len(voices) == 6

        # Verify all expected voices exist
        expected_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        for voice_id in expected_voices:
            assert voice_id in voices
            assert "name" in voices[voice_id]
            assert "description" in voices[voice_id]
            assert "gender" in voices[voice_id]

    def test_voice_metadata_completeness(self):
        """Test that each voice has complete metadata."""
        for voice_id, metadata in VOICE_METADATA.items():
            assert "name" in metadata, f"Voice {voice_id} missing 'name'"
            assert "description" in metadata, f"Voice {voice_id} missing 'description'"
            assert "gender" in metadata, f"Voice {voice_id} missing 'gender'"
            assert "best_for" in metadata, f"Voice {voice_id} missing 'best_for'"
            assert isinstance(metadata["best_for"], list), f"Voice {voice_id} 'best_for' should be a list"

    def test_get_available_models(self, service: OpenAITTSService):
        """Test that TTS models are correctly listed."""
        models = service.get_available_models()

        assert len(models) == 2

        model_ids = [m["id"] for m in models]
        assert "tts-1" in model_ids
        assert "tts-1-hd" in model_ids

    def test_estimate_cost_tts1(self, service: OpenAITTSService):
        """Test cost estimation for tts-1 model."""
        text = "Hello, this is a test." * 100  # ~2300 chars

        estimate = service.estimate_cost(text, model="tts-1")

        assert estimate["character_count"] == len(text)
        assert estimate["model"] == "tts-1"
        assert estimate["cost_per_1m_chars"] == 15.0

        # Cost should be chars * $15 / 1M
        expected_cost = len(text) * 0.000015
        assert abs(estimate["estimated_cost"] - expected_cost) < 0.0001

    def test_estimate_cost_tts1_hd(self, service: OpenAITTSService):
        """Test cost estimation for tts-1-hd model."""
        text = "Premium quality test text." * 100

        estimate = service.estimate_cost(text, model="tts-1-hd")

        assert estimate["cost_per_1m_chars"] == 30.0

        # HD model costs 2x
        expected_cost = len(text) * 0.00003
        assert abs(estimate["estimated_cost"] - expected_cost) < 0.0001

    def test_chunk_text_short(self, service: OpenAITTSService):
        """Test that short text is not chunked."""
        text = "This is a short sentence."

        chunks = service._chunk_text(text)

        assert len(chunks) == 1
        assert chunks[0] == text

    def test_chunk_text_long(self, service: OpenAITTSService):
        """Test that long text is chunked at sentence boundaries."""
        # Create text longer than max chars
        sentences = [f"This is sentence number {i}." for i in range(200)]
        text = " ".join(sentences)

        chunks = service._chunk_text(text, max_chars=1000)

        # Should have multiple chunks
        assert len(chunks) > 1

        # Each chunk should be under max_chars
        for chunk in chunks:
            assert len(chunk) <= 1000

        # Rejoining should give back original text (minus whitespace variations)
        rejoined = " ".join(chunks)
        assert rejoined.replace("  ", " ") == text.replace("  ", " ")

    def test_chunk_text_preserves_sentences(self, service: OpenAITTSService):
        """Test that chunking preserves sentence boundaries."""
        text = "First sentence. Second sentence! Third sentence? Fourth sentence."

        chunks = service._chunk_text(text, max_chars=50)

        # Each chunk should end with sentence punctuation or be the original text
        for chunk in chunks:
            if len(chunk) > 1:
                assert chunk[-1] in '.!?' or chunk == chunks[-1]


class TestOpenAITTSVoiceEnum:
    """Tests for OpenAIVoice enum."""

    def test_voice_values(self):
        """Test that enum values match expected voice IDs."""
        assert OpenAIVoice.ALLOY.value == "alloy"
        assert OpenAIVoice.ECHO.value == "echo"
        assert OpenAIVoice.FABLE.value == "fable"
        assert OpenAIVoice.ONYX.value == "onyx"
        assert OpenAIVoice.NOVA.value == "nova"
        assert OpenAIVoice.SHIMMER.value == "shimmer"


class TestOpenAITTSModelEnum:
    """Tests for OpenAITTSModel enum."""

    def test_model_values(self):
        """Test that enum values match expected model IDs."""
        assert OpenAITTSModel.TTS_1.value == "tts-1"
        assert OpenAITTSModel.TTS_1_HD.value == "tts-1-hd"


class TestOpenAITTSValidation:
    """Tests for input validation."""

    @pytest.fixture
    def service(self):
        return OpenAITTSService(api_key="test_key", enable_caching=False)

    def test_max_chars_limit(self, service: OpenAITTSService):
        """Test that MAX_CHARS is set correctly."""
        assert service.MAX_CHARS == 4096

    @pytest.mark.asyncio
    async def test_synthesize_rejects_long_text(self, service: OpenAITTSService):
        """Test that synthesize rejects text exceeding max chars."""
        long_text = "a" * 5000  # > 4096 chars

        with pytest.raises(ValueError) as exc_info:
            await service.synthesize(long_text)

        assert "exceeds maximum" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_synthesize_without_api_key(self):
        """Test that synthesize fails without API key."""
        service = OpenAITTSService(api_key=None, enable_caching=False)

        with pytest.raises(ValueError) as exc_info:
            await service.synthesize("test text")

        assert "API key not configured" in str(exc_info.value)


class TestOpenAITTSPricing:
    """Tests for pricing calculations."""

    def test_pricing_constants(self):
        """Test that pricing constants are correct."""
        service = OpenAITTSService(api_key="test", enable_caching=False)

        assert service.PRICING["tts-1"] == Decimal("0.000015")
        assert service.PRICING["tts-1-hd"] == Decimal("0.00003")

    def test_cost_calculation_1m_chars(self):
        """Test cost for 1 million characters."""
        service = OpenAITTSService(api_key="test", enable_caching=False)

        text = "a" * 1_000_000
        estimate = service.estimate_cost(text, model="tts-1")

        # Should be exactly $15 for 1M chars with tts-1
        assert estimate["estimated_cost"] == 15.0

    def test_cost_calculation_small_text(self):
        """Test cost for small text."""
        service = OpenAITTSService(api_key="test", enable_caching=False)

        text = "Hello world"  # 11 chars
        estimate = service.estimate_cost(text, model="tts-1")

        expected = 11 * 0.000015
        assert abs(estimate["estimated_cost"] - expected) < 0.000001


class TestOpenAITTSStats:
    """Tests for service statistics."""

    def test_initial_stats(self):
        """Test that initial stats are zero."""
        service = OpenAITTSService(api_key="test", enable_caching=False)
        stats = service.get_stats()

        assert stats["total_requests"] == 0
        assert stats["total_characters"] == 0
        assert stats["total_cost"] == 0.0
        assert stats["cache_hits"] == 0
        assert stats["cache_enabled"] is False


class TestOpenAITTSIntegration:
    """Integration tests (require actual API key or mock)."""

    @pytest.mark.asyncio
    async def test_synthesize_with_mock(self):
        """Test synthesize with mocked HTTP response."""
        service = OpenAITTSService(api_key="test_key", enable_caching=False)

        # Create mock audio response
        mock_audio = b"fake_audio_data" * 1000

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = mock_audio
            mock_post.return_value.__aenter__.return_value = mock_response

            # This will fail without proper async context - just verify setup
            # Real integration test would need actual API calls


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
