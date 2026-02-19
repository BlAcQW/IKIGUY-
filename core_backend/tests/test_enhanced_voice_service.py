#!/usr/bin/env python3
"""
Unit tests for Enhanced Voice Service

Tests:
- Unified service integration
- Shared service fallback
- Cost tracking
- Error handling with fallback chains
- Performance metrics

Author: AI Labs Africa
Created: 2025-11-07
"""

import pytest
import asyncio
import numpy as np
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path

# Test fixtures - Real audio paths
REAL_AUDIO_DIR = Path("/opt/kasaai/apps/voice-lab/test_audio")
TWI_AUDIO_PATH = REAL_AUDIO_DIR / "COL_001_Verse_001.wav"


@pytest.fixture
def real_twi_audio():
    """Load real Twi audio sample as numpy array."""
    if not TWI_AUDIO_PATH.exists():
        pytest.skip(f"Real Twi audio not found at {TWI_AUDIO_PATH}")

    import soundfile as sf
    audio_data, sample_rate = sf.read(TWI_AUDIO_PATH)
    return audio_data, sample_rate


@pytest.fixture
def sample_audio_array():
    """Generate sample audio array for testing."""
    # 1 second of 16kHz audio
    duration = 1.0
    sample_rate = 16000
    samples = int(duration * sample_rate)

    # Generate sine wave (440 Hz)
    t = np.linspace(0, duration, samples)
    audio = np.sin(2 * np.pi * 440 * t) * 0.3

    return audio.astype(np.float32), sample_rate


class TestEnhancedVoiceService:
    """Test Enhanced Voice Service with real integration."""

    def test_service_initialization(self):
        """Test service initialization with different modes."""
        from backend.services.enhanced_voice_service import (
            EnhancedVoiceService,
            VoiceServiceConfig,
            ServiceMode,
            ASRModel,
            TTSModel
        )

        # Test UNIFIED_ONLY mode
        config = VoiceServiceConfig(
            mode=ServiceMode.UNIFIED_ONLY,
            primary_stt_model=ASRModel.AKAN_WHISPER,
            primary_tts_model=TTSModel.AKAN_MMS
        )
        service = EnhancedVoiceService(config)

        assert service.config.mode == ServiceMode.UNIFIED_ONLY
        assert service.unified_asr is not None
        assert service.unified_tts is not None
        assert service.stats["total_stt_requests"] == 0
        assert service.stats["total_tts_requests"] == 0

    def test_service_initialization_hybrid_mode(self):
        """Test service initialization in hybrid mode."""
        from backend.services.enhanced_voice_service import (
            EnhancedVoiceService,
            VoiceServiceConfig,
            ServiceMode
        )

        config = VoiceServiceConfig(mode=ServiceMode.HYBRID)
        service = EnhancedVoiceService(config)

        assert service.config.mode == ServiceMode.HYBRID
        assert service.config.enable_fallback is True

    @pytest.mark.asyncio
    async def test_transcribe_with_unified_service(self, sample_audio_array):
        """Test transcription using unified service."""
        from backend.services.enhanced_voice_service import (
            EnhancedVoiceService,
            VoiceServiceConfig,
            ServiceMode,
            ASRModel
        )

        audio_data, sample_rate = sample_audio_array

        # Test with FASTER_WHISPER (more reliable for test audio)
        config = VoiceServiceConfig(
            mode=ServiceMode.UNIFIED_ONLY,
            primary_stt_model=ASRModel.FASTER_WHISPER
        )
        service = EnhancedVoiceService(config)

        # Transcribe
        result = await service.transcribe(
            audio_data=audio_data,
            sample_rate=sample_rate,
            language="en"
        )

        # Verify result
        assert result is not None
        assert isinstance(result.text, str)
        assert result.provider == "unified"
        assert result.model == "faster-whisper"
        assert result.confidence >= 0.0
        assert result.processing_time > 0
        assert result.fallback_used is False

        # Verify stats updated
        assert service.stats["total_stt_requests"] == 1
        assert service.stats["unified_stt_success"] == 1

    @pytest.mark.asyncio
    async def test_transcribe_with_real_twi_audio(self, real_twi_audio):
        """Test transcription with real Twi audio."""
        from backend.services.enhanced_voice_service import (
            EnhancedVoiceService,
            VoiceServiceConfig,
            ASRModel
        )

        audio_data, sample_rate = real_twi_audio

        config = VoiceServiceConfig(primary_stt_model=ASRModel.AKAN_WHISPER)
        service = EnhancedVoiceService(config)

        result = await service.transcribe(
            audio_data=audio_data,
            sample_rate=sample_rate,
            language="tw",
            dialect="asante"
        )

        # Verify Twi transcription
        assert result is not None
        assert len(result.text) > 0
        assert result.language == "tw"
        assert result.model == "akan-whisper"
        print(f"✅ Akan Whisper transcription: '{result.text}'")

    @pytest.mark.asyncio
    async def test_transcribe_fallback_to_shared(self, sample_audio_array):
        """Test fallback from unified to shared service."""
        from backend.services.enhanced_voice_service import (
            EnhancedVoiceService,
            VoiceServiceConfig,
            ServiceMode,
            ASRModel
        )

        audio_data, sample_rate = sample_audio_array

        config = VoiceServiceConfig(
            mode=ServiceMode.HYBRID,
            enable_fallback=True
        )
        service = EnhancedVoiceService(config)

        # Mock unified service to fail
        async def mock_transcribe_fail(*args, **kwargs):
            raise Exception("Unified service temporarily unavailable")

        service.unified_asr.transcribe = mock_transcribe_fail

        # If shared service is available, should fallback
        if service.shared_stt:
            result = await service.transcribe(
                audio_data=audio_data,
                sample_rate=sample_rate,
                language="en"
            )

            assert result is not None
            assert result.provider == "shared"
            assert result.fallback_used is True
            assert service.stats["shared_stt_fallback"] == 1
            print("✅ Fallback to shared STT service successful")
        else:
            # Expect failure if no shared service
            with pytest.raises(Exception, match="failed"):
                await service.transcribe(
                    audio_data=audio_data,
                    sample_rate=sample_rate,
                    language="en"
                )
            print("⚠️ No shared service available, fallback test skipped")

    def test_synthesize_with_unified_service(self):
        """Test speech synthesis using unified service."""
        from backend.services.enhanced_voice_service import (
            EnhancedVoiceService,
            VoiceServiceConfig,
            TTSModel
        )

        config = VoiceServiceConfig(primary_tts_model=TTSModel.AKAN_MMS)
        service = EnhancedVoiceService(config)

        # Synthesize
        result = service.synthesize(
            text="Maakye! Me din de Abena.",
            language="tw",
            dialect="asante"
        )

        # Verify result
        assert result is not None
        assert isinstance(result.audio_base64, str)
        assert len(result.audio_base64) > 0
        assert result.provider == "unified"
        assert result.model == "akan-mms"
        assert result.duration > 0
        assert result.processing_time > 0
        assert result.fallback_used is False

        # Verify stats
        assert service.stats["total_tts_requests"] == 1
        assert service.stats["unified_tts_success"] == 1

    def test_synthesize_english_with_xtts(self):
        """Test English synthesis with XTTS model."""
        from backend.services.enhanced_voice_service import (
            EnhancedVoiceService,
            VoiceServiceConfig,
            TTSModel
        )

        config = VoiceServiceConfig(primary_tts_model=TTSModel.XTTS_V2)
        service = EnhancedVoiceService(config)

        result = service.synthesize(
            text="Hello! This is a test of the English voice synthesis system.",
            language="en",
            model=TTSModel.XTTS_V2
        )

        assert result is not None
        assert len(result.audio_base64) > 0
        assert result.model == "xtts-v2"
        print(f"✅ XTTS synthesis successful: {result.duration:.2f}s audio")

    def test_synthesize_fallback_to_shared(self):
        """Test fallback from unified to shared TTS service."""
        from backend.services.enhanced_voice_service import (
            EnhancedVoiceService,
            VoiceServiceConfig,
            ServiceMode
        )

        config = VoiceServiceConfig(
            mode=ServiceMode.HYBRID,
            enable_fallback=True
        )
        service = EnhancedVoiceService(config)

        # Mock unified service to fail
        def mock_synthesize_fail(*args, **kwargs):
            raise Exception("Unified TTS temporarily unavailable")

        service.unified_tts.synthesize = mock_synthesize_fail

        # If shared service is available, should fallback
        if service.shared_tts:
            result = service.synthesize(text="Test fallback")

            assert result is not None
            assert result.provider == "shared"
            assert result.fallback_used is True
            assert service.stats["shared_tts_fallback"] == 1
            print("✅ Fallback to shared TTS service successful")
        else:
            # Expect failure if no shared service
            with pytest.raises(Exception, match="failed"):
                service.synthesize(text="Test fallback")
            print("⚠️ No shared service available, fallback test skipped")

    def test_cost_estimation_stt(self):
        """Test STT cost estimation."""
        from backend.services.enhanced_voice_service import EnhancedVoiceService

        service = EnhancedVoiceService()

        # Test different models
        cost_whisper = service._estimate_stt_cost(60.0, "akan-whisper")
        cost_openai = service._estimate_stt_cost(60.0, "openai")

        assert cost_whisper == 0.0  # Self-hosted
        assert cost_openai == 0.006  # $0.006 per minute
        print(f"✅ Cost estimation: Akan={cost_whisper}, OpenAI={cost_openai}")

    def test_cost_estimation_tts(self):
        """Test TTS cost estimation."""
        from backend.services.enhanced_voice_service import EnhancedVoiceService

        service = EnhancedVoiceService()

        # Test different models
        cost_akan = service._estimate_tts_cost(1000, "akan-mms")
        cost_openai = service._estimate_tts_cost(1000, "openai")

        assert cost_akan == 0.0  # Self-hosted
        assert cost_openai == 0.015  # $0.015 per 1K chars
        print(f"✅ Cost estimation: Akan={cost_akan}, OpenAI={cost_openai}")

    @pytest.mark.asyncio
    async def test_multiple_requests_stats(self, sample_audio_array):
        """Test statistics tracking across multiple requests."""
        from backend.services.enhanced_voice_service import (
            EnhancedVoiceService,
            VoiceServiceConfig,
            ASRModel,
            TTSModel
        )

        audio_data, sample_rate = sample_audio_array

        config = VoiceServiceConfig(
            primary_stt_model=ASRModel.FASTER_WHISPER,
            primary_tts_model=TTSModel.AKAN_MMS
        )
        service = EnhancedVoiceService(config)

        # Make multiple requests
        for i in range(3):
            await service.transcribe(
                audio_data=audio_data,
                sample_rate=sample_rate,
                language="en"
            )
            service.synthesize(text=f"Test message {i}")

        # Check stats
        stats = service.get_stats()

        assert stats["total_stt_requests"] == 3
        assert stats["total_tts_requests"] == 3
        assert stats["total_requests"] == 6
        assert stats["unified_success_rate"] > 0
        print(f"✅ Stats after 6 requests: {stats}")

    def test_get_stats_structure(self):
        """Test statistics structure and calculation."""
        from backend.services.enhanced_voice_service import EnhancedVoiceService

        service = EnhancedVoiceService()
        stats = service.get_stats()

        # Verify structure
        assert "total_stt_requests" in stats
        assert "total_tts_requests" in stats
        assert "unified_stt_success" in stats
        assert "unified_tts_success" in stats
        assert "shared_stt_fallback" in stats
        assert "shared_tts_fallback" in stats
        assert "total_cost_usd" in stats
        assert "errors" in stats
        assert "total_requests" in stats
        assert "unified_success_rate" in stats
        assert "fallback_rate" in stats
        assert "average_cost_per_request" in stats

    @pytest.mark.asyncio
    async def test_error_tracking(self, sample_audio_array):
        """Test error tracking in stats."""
        from backend.services.enhanced_voice_service import (
            EnhancedVoiceService,
            VoiceServiceConfig,
            ServiceMode
        )

        audio_data, sample_rate = sample_audio_array

        config = VoiceServiceConfig(
            mode=ServiceMode.UNIFIED_ONLY,
            enable_fallback=False
        )
        service = EnhancedVoiceService(config)

        # Mock to force error
        async def mock_fail(*args, **kwargs):
            raise Exception("Intentional test error")

        service.unified_asr.transcribe = mock_fail

        # Attempt transcription (should fail)
        with pytest.raises(Exception):
            await service.transcribe(
                audio_data=audio_data,
                sample_rate=sample_rate,
                language="en"
            )

        # Verify error was tracked
        assert len(service.stats["errors"]) > 0
        error = service.stats["errors"][0]
        assert "service" in error
        assert "error" in error
        assert "timestamp" in error
        print(f"✅ Error tracked: {error}")


class TestEnhancedVoiceServiceIntegration:
    """Integration tests with real services."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_voice_conversation_flow(self, real_twi_audio):
        """Test complete voice conversation flow with real audio."""
        from backend.services.enhanced_voice_service import (
            EnhancedVoiceService,
            VoiceServiceConfig,
            ASRModel,
            TTSModel
        )

        audio_data, sample_rate = real_twi_audio

        # Initialize service
        config = VoiceServiceConfig(
            primary_stt_model=ASRModel.AKAN_WHISPER,
            primary_tts_model=TTSModel.AKAN_MMS,
            enable_cost_tracking=True
        )
        service = EnhancedVoiceService(config)

        # 1. Transcribe user audio
        stt_result = await service.transcribe(
            audio_data=audio_data,
            sample_rate=sample_rate,
            language="tw",
            dialect="asante",
            user_id="test_user_123"
        )

        assert len(stt_result.text) > 0
        print(f"🎤 User said: '{stt_result.text}'")

        # 2. Generate response (mock LLM)
        response_text = f"Me tee wo. Wo kaa sɛ: {stt_result.text}"

        # 3. Synthesize response
        tts_result = service.synthesize(
            text=response_text,
            language="tw",
            dialect="asante",
            user_id="test_user_123"
        )

        assert len(tts_result.audio_base64) > 0
        print(f"🔊 Assistant responds: {len(tts_result.audio_base64)} bytes audio")

        # 4. Check total cost
        stats = service.get_stats()
        total_cost = stats["total_cost_usd"]
        print(f"💰 Total cost: ${total_cost:.4f}")

        assert total_cost >= 0  # Should track costs (even if 0 for self-hosted)

    @pytest.mark.integration
    def test_service_performance_benchmark(self):
        """Benchmark service performance with multiple requests."""
        import time
        from backend.services.enhanced_voice_service import (
            EnhancedVoiceService,
            TTSModel
        )

        service = EnhancedVoiceService()

        # Test TTS performance
        start_time = time.time()

        for i in range(5):
            result = service.synthesize(
                text=f"Twi test message number {i}. Maakye!",
                model=TTSModel.AKAN_MMS
            )
            assert len(result.audio_base64) > 0

        elapsed = time.time() - start_time
        avg_time = elapsed / 5

        print(f"✅ TTS Benchmark: {avg_time:.3f}s per request (5 requests in {elapsed:.2f}s)")
        assert avg_time < 5.0  # Should be under 5 seconds per request


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
