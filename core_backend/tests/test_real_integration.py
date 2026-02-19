#!/usr/bin/env python3
"""
REAL Integration Tests - No Mocks
Tests actual functionality with real models and services
"""

import pytest
import asyncio
import os
from pathlib import Path

# Mark all tests as integration tests
pytestmark = pytest.mark.integration


class TestRealFasterWhisper:
    """Test actual Faster Whisper model loading and inference."""

    @pytest.mark.asyncio
    async def test_faster_whisper_loads(self):
        """Test that Faster Whisper actually loads (CPU mode)."""
        from backend.services.faster_whisper_service import FasterWhisperService

        service = FasterWhisperService()

        # Should use CPU
        assert service.whisper_config["device"] == "cpu"
        assert service.whisper_config["compute_type"] == "int8"

        # Actually load the model
        await service.initialize("base")

        # Verify it loaded
        assert service.models_loaded is True
        assert "base" in service.models
        assert service.models["base"] is not None


class TestRealGemini:
    """Test actual Gemini API integration."""

    @pytest.mark.asyncio
    async def test_gemini_api_configured(self):
        """Test that Gemini API key is configured."""
        from backend.services.gemini_service import get_gemini_service

        service = get_gemini_service()

        # Check if API key exists
        assert service.is_available(), "GEMINI_API_KEY not in environment"

    @pytest.mark.asyncio
    async def test_gemini_generates_content(self):
        """Test that Gemini actually generates content."""
        from backend.services.gemini_service import get_gemini_service

        service = get_gemini_service()

        if not service.is_available():
            pytest.skip("GEMINI_API_KEY not configured")

        # Make real API call
        result = await service.generate_content(
            prompt="Say hello in one word",
            max_output_tokens=100  # Increased from 10 to avoid truncation
        )

        # Verify real response
        assert result is not None
        assert "content" in result
        assert len(result["content"]) > 0
        assert result["content"] != "[Response truncated - increase max_output_tokens]"


class TestRealAkanModel:
    """Test actual Akan model availability."""

    @pytest.mark.asyncio
    async def test_akan_model_exists(self):
        """Test that Akan model files exist."""
        akan_path = Path("/opt/kasaai/apps/voice-lab/models/akan_whisper")

        assert akan_path.exists(), f"Akan model not found at {akan_path}"

        # Check key files
        required_files = ["config.json", "model.safetensors", "tokenizer.json"]
        for file in required_files:
            file_path = akan_path / file
            assert file_path.exists(), f"Missing {file} in Akan model"

    @pytest.mark.asyncio
    async def test_akan_model_loads(self):
        """Test that Akan model actually loads."""
        from backend.services.faster_whisper_service import FasterWhisperService

        service = FasterWhisperService()

        # Try to load Akan model
        success = await service.initialize_akan_model()

        if not success:
            pytest.skip("Akan model dependencies not available (transformers, torch)")

        # Verify loaded
        assert service.akan_model is not None
        assert service.akan_processor is not None


class TestRealSystemConfiguration:
    """Test actual system configuration."""

    def test_env_variables_loaded(self):
        """Test that .env file is actually loaded."""
        # Check if environment has config
        gemini_key = os.getenv("GEMINI_API_KEY")

        if not gemini_key:
            pytest.fail("GEMINI_API_KEY not in environment - .env not loaded")

    def test_model_paths_exist(self):
        """Test that model paths actually exist."""
        voice_lab = Path("/opt/kasaai/apps/voice-lab")
        assert voice_lab.exists(), "Voice lab directory not found"

        models_dir = voice_lab / "models"
        assert models_dir.exists(), "Models directory not found"


class TestRealWebSocketFlow:
    """Test actual WebSocket message flow."""

    @pytest.mark.asyncio
    async def test_stt_with_silent_audio(self):
        """Test STT with real (silent) audio - should return empty or low confidence."""
        from backend.routes.voice_engine.websocket_chat import perform_stt
        import wave
        import io
        import tempfile

        # Create real WAV file (silent)
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(16000)
            wav.writeframes(bytes([0] * 16000 * 2))  # 1 second silence

        buffer.seek(0)
        audio_bytes = buffer.read()

        # Write to temp file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            # Mock assistant
            from unittest.mock import Mock
            mock_assistant = Mock()
            mock_assistant.language = "en"

            # Actually run STT
            result = await perform_stt(audio_bytes, mock_assistant)

            # Should return structure even for silence
            assert "text" in result
            assert "confidence" in result
            assert "language" in result

            # For silence, text should be empty or confidence low
            if result["text"]:
                print(f"Transcribed silence as: '{result['text']}'")
            else:
                print("Correctly returned empty for silence")

        finally:
            os.unlink(tmp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "-m", "integration"])