"""
Unit tests for audiobook service.

Tests chunk ID parsing, caching, and audio generation.
"""

import pytest
import os
import json
import base64
from unittest.mock import Mock, patch, AsyncMock
from app.services.audiobook_service import AudiobookService, AudioChunk


class TestAudiobookService:
    """Test suite for AudiobookService."""

    @pytest.fixture
    def audiobook_service(self, tmp_path):
        """Create audiobook service instance with temp storage."""
        storage_path = str(tmp_path / "audiobooks")
        os.makedirs(storage_path, exist_ok=True)

        service = AudiobookService()
        service.storage_path = storage_path
        return service

    @pytest.mark.asyncio
    async def test_get_cached_audio_with_voice_settings(self, audiobook_service):
        """
        Test loading cached audio with voice settings in chunk ID.

        This tests the fix for the chunk index parsing bug where
        chunk IDs like "book_5bb65ca24e10_chunk_2_kokoro_am_michael_1.0"
        were failing because the code tried to parse "1.0" as an integer.
        """
        # Setup: Create a cached audio file with voice settings in chunk ID
        chunk_id = "book_5bb65ca24e10_chunk_2_kokoro_am_michael_1.0"
        cache_path = os.path.join(audiobook_service.storage_path, f"{chunk_id}.mp3")
        meta_path = cache_path + ".meta"

        # Create dummy audio file
        dummy_audio = b"fake audio data"
        with open(cache_path, "wb") as f:
            f.write(dummy_audio)

        # Create metadata file
        meta = {
            "duration": 10.5,
            "provider_used": "kokoro_tts"
        }
        with open(meta_path, "w") as f:
            json.dump(meta, f)

        # Execute: Load cached audio
        result = await audiobook_service._get_cached_audio(chunk_id)

        # Assert: Should successfully load and parse chunk_index=2
        assert result is not None
        assert result.chunk_id == chunk_id
        assert result.chunk_index == 2  # Should extract "2" from "chunk_2"
        assert result.duration == 10.5
        assert result.provider_used == "kokoro_tts"
        assert result.audio_base64 == base64.b64encode(dummy_audio).decode("utf-8")

    @pytest.mark.asyncio
    async def test_get_cached_audio_old_format(self, audiobook_service):
        """
        Test loading cached audio with old format (no voice settings).

        Ensures backward compatibility with chunk IDs like
        "book_010d2d3550ad_chunk_0" without provider/voice/speed.
        """
        # Setup: Create cached audio with old format
        chunk_id = "book_010d2d3550ad_chunk_0"
        cache_path = os.path.join(audiobook_service.storage_path, f"{chunk_id}.mp3")
        meta_path = cache_path + ".meta"

        dummy_audio = b"old format audio"
        with open(cache_path, "wb") as f:
            f.write(dummy_audio)

        meta = {
            "duration": 5.0,
            "provider_used": "openai_tts"
        }
        with open(meta_path, "w") as f:
            json.dump(meta, f)

        # Execute
        result = await audiobook_service._get_cached_audio(chunk_id)

        # Assert
        assert result is not None
        assert result.chunk_index == 0
        assert result.duration == 5.0

    @pytest.mark.asyncio
    async def test_get_cached_audio_various_chunk_indices(self, audiobook_service):
        """Test parsing chunk indices from various chunk ID formats."""
        test_cases = [
            # (chunk_id, expected_index)
            ("book_abc123_chunk_0_openai_alloy_1.0", 0),
            ("book_abc123_chunk_5_kokoro_am_michael_1.0", 5),
            ("book_abc123_chunk_99_edge_en-US-JennyNeural_1.5", 99),
            ("book_abc123_chunk_10", 10),  # Old format
            ("book_abc123_chunk_123_provider_voice_0.5", 123),  # Different speed
        ]

        for chunk_id, expected_index in test_cases:
            # Setup
            cache_path = os.path.join(audiobook_service.storage_path, f"{chunk_id}.mp3")
            meta_path = cache_path + ".meta"

            with open(cache_path, "wb") as f:
                f.write(b"audio")

            with open(meta_path, "w") as f:
                json.dump({"duration": 1.0, "provider_used": "test"}, f)

            # Execute
            result = await audiobook_service._get_cached_audio(chunk_id)

            # Assert
            assert result is not None, f"Failed to load {chunk_id}"
            assert result.chunk_index == expected_index, \
                f"Wrong index for {chunk_id}: got {result.chunk_index}, expected {expected_index}"

            # Cleanup
            os.remove(cache_path)
            os.remove(meta_path)

    @pytest.mark.asyncio
    async def test_get_cached_audio_missing_file(self, audiobook_service):
        """Test that missing cache files return None."""
        result = await audiobook_service._get_cached_audio("nonexistent_chunk_id")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_cached_audio_invalid_chunk_id_format(self, audiobook_service):
        """Test handling of malformed chunk IDs."""
        # Setup: Create file with invalid format
        chunk_id = "invalid_format_no_chunk_keyword"
        cache_path = os.path.join(audiobook_service.storage_path, f"{chunk_id}.mp3")
        meta_path = cache_path + ".meta"

        with open(cache_path, "wb") as f:
            f.write(b"audio")

        with open(meta_path, "w") as f:
            json.dump({"duration": 1.0}, f)

        # Execute
        result = await audiobook_service._get_cached_audio(chunk_id)

        # Assert: Should still load but with chunk_index=0 as fallback
        assert result is not None
        assert result.chunk_index == 0

    @pytest.mark.asyncio
    async def test_get_cached_audio_non_numeric_index(self, audiobook_service):
        """Test handling when chunk index part is not numeric."""
        # Setup
        chunk_id = "book_abc_chunk_abc_provider"  # "abc" instead of number
        cache_path = os.path.join(audiobook_service.storage_path, f"{chunk_id}.mp3")
        meta_path = cache_path + ".meta"

        with open(cache_path, "wb") as f:
            f.write(b"audio")

        with open(meta_path, "w") as f:
            json.dump({"duration": 1.0}, f)

        # Execute
        result = await audiobook_service._get_cached_audio(chunk_id)

        # Assert: Should handle gracefully and use 0 as fallback
        assert result is not None
        assert result.chunk_index == 0
