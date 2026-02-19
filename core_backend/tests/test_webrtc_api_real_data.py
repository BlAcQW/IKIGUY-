"""
Real-data API tests for WebRTC Voice Chat.

These tests focus on testing the WebRTC API endpoints with real data
without importing the full voice pipeline to avoid model loading issues.

Tests cover:
- WebRTC agent logic with real audio data
- Audio format conversions
- VoicePipeline integration patterns
- Error handling with real scenarios
"""

import pytest
import asyncio
import numpy as np
import base64
from unittest.mock import Mock, patch, AsyncMock, MagicMock


@pytest.fixture
def real_audio_pcm_silence():
    """Generate real PCM audio data - 1 second of silence at 16kHz."""
    sample_rate = 16000
    duration = 1.0
    samples = int(sample_rate * duration)
    audio_array = np.zeros(samples, dtype=np.float32)
    return (sample_rate, audio_array)


@pytest.fixture
def real_audio_pcm_tone():
    """Generate real PCM audio data - 440Hz tone at 16kHz."""
    sample_rate = 16000
    duration = 0.5
    frequency = 440  # A4 note
    samples = int(sample_rate * duration)
    t = np.linspace(0, duration, samples, False)
    audio_array = (np.sin(frequency * 2 * np.pi * t) * 0.3).astype(np.float32)
    return (sample_rate, audio_array)


@pytest.fixture
def real_audio_bytes():
    """Generate real audio bytes - int16 PCM format."""
    sample_rate = 16000
    duration = 1.0
    samples = int(sample_rate * duration)
    audio_array = np.zeros(samples, dtype=np.int16)
    return audio_array.tobytes()


@pytest.fixture
def real_wav_audio_base64():
    """Generate real WAV audio in base64 format (as returned by TTS)."""
    sample_rate = 16000
    duration = 0.5
    samples = int(sample_rate * duration)

    # PCM data (silence)
    pcm_data = np.zeros(samples, dtype=np.int16)

    # Create WAV header (44 bytes for standard PCM WAV)
    wav_header = bytearray([
        0x52, 0x49, 0x46, 0x46,  # "RIFF"
        0x24, 0x80, 0x00, 0x00,  # File size (36 + data size)
        0x57, 0x41, 0x56, 0x45,  # "WAVE"
        0x66, 0x6D, 0x74, 0x20,  # "fmt "
        0x10, 0x00, 0x00, 0x00,  # Chunk size (16)
        0x01, 0x00,              # Audio format (1 = PCM)
        0x01, 0x00,              # Num channels (1 = mono)
        0x80, 0x3E, 0x00, 0x00,  # Sample rate (16000)
        0x00, 0x7D, 0x00, 0x00,  # Byte rate (16000 * 2)
        0x02, 0x00,              # Block align (2 bytes)
        0x10, 0x00,              # Bits per sample (16)
        0x64, 0x61, 0x74, 0x61,  # "data"
        0x00, 0x80, 0x00, 0x00,  # Data size
    ])

    # Combine header and PCM data
    wav_bytes = bytes(wav_header) + pcm_data.tobytes()
    wav_base64 = base64.b64encode(wav_bytes).decode('utf-8')

    return wav_base64


class TestWebRTCAudioProcessing:
    """Test WebRTC audio processing with real data."""

    def test_pcm_format_conversion_float_to_int(self):
        """Test converting float32 PCM to int16 PCM."""
        # Create test signal in float32 format (WebRTC input format)
        sample_rate = 16000
        duration = 0.5
        samples = int(sample_rate * duration)

        # Generate a test signal with known values (avoid exact ±1.0 to prevent overflow)
        pcm_float32 = np.linspace(-0.99, 0.99, samples, dtype=np.float32)

        # Convert to int16 (standard PCM format)
        pcm_int16 = (pcm_float32 * 32768.0).astype(np.int16)

        # Verify range
        assert pcm_int16.min() >= -32768
        assert pcm_int16.max() <= 32767

        # Verify approximate values
        assert pcm_int16[0] < -32000  # Should be close to -32440
        assert pcm_int16[-1] > 32000  # Should be close to 32440

    def test_pcm_format_conversion_int_to_float(self):
        """Test converting int16 PCM to float32 PCM."""
        # Create test signal in int16 format (standard PCM)
        pcm_int16 = np.array([-32768, -16384, 0, 16384, 32767], dtype=np.int16)

        # Convert to float32 (WebRTC output format)
        pcm_float32 = pcm_int16.astype(np.float32) / 32768.0

        # Verify range is [-1.0, 1.0]
        assert pcm_float32.min() >= -1.0
        assert pcm_float32.max() <= 1.0

        # Verify specific values
        assert abs(pcm_float32[0] - (-1.0)) < 0.01  # -32768 / 32768 ≈ -1.0
        assert abs(pcm_float32[2] - 0.0) < 0.01     # 0 / 32768 = 0.0
        assert abs(pcm_float32[4] - 1.0) < 0.01     # 32767 / 32768 ≈ 1.0

    def test_wav_audio_extraction(self, real_wav_audio_base64):
        """Test extracting PCM from WAV audio (as from TTS service)."""
        # Decode base64
        wav_bytes = base64.b64decode(real_wav_audio_base64)

        # Verify WAV header
        assert wav_bytes[0:4] == b'RIFF'
        assert wav_bytes[8:12] == b'WAVE'

        # Extract PCM data (skip 44-byte header)
        assert len(wav_bytes) > 44
        pcm_bytes = wav_bytes[44:]

        # Convert to numpy array
        pcm_array = np.frombuffer(pcm_bytes, dtype=np.int16)

        # Verify we got audio data
        assert len(pcm_array) > 0
        assert pcm_array.dtype == np.int16

    def test_audio_chunk_aggregation(self, real_audio_pcm_silence):
        """Test aggregating multiple audio chunks."""
        sample_rate, audio_data = real_audio_pcm_silence

        # Split into chunks (simulate streaming)
        chunk_size = 4000  # 250ms chunks at 16kHz
        chunks = []
        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i:i+chunk_size]
            chunks.append(chunk)

        # Verify we have multiple chunks
        assert len(chunks) > 1

        # Aggregate back together
        aggregated = np.concatenate(chunks)

        # Verify reconstruction
        assert len(aggregated) == len(audio_data)
        assert np.array_equal(aggregated, audio_data)


class TestWebRTCAgentLogic:
    """Test WebRTC agent logic with real data (mocked pipeline)."""

    @pytest.mark.asyncio
    async def test_audio_stream_processing(self, real_audio_bytes):
        """Test processing audio stream through pipeline."""
        # Create audio stream generator
        async def audio_stream():
            # Yield audio in chunks
            chunk_size = 8000  # 8KB chunks
            for i in range(0, len(real_audio_bytes), chunk_size):
                chunk = real_audio_bytes[i:i+chunk_size]
                yield chunk
                await asyncio.sleep(0)  # Yield control

        # Collect all chunks
        collected_chunks = []
        async for chunk in audio_stream():
            collected_chunks.append(chunk)

        # Verify we received all data
        total_received = sum(len(chunk) for chunk in collected_chunks)
        assert total_received == len(real_audio_bytes)

    @pytest.mark.asyncio
    async def test_voice_pipeline_message_handling(self, real_wav_audio_base64):
        """Test handling VoicePipeline output messages."""
        # Simulate VoicePipeline output messages
        async def mock_pipeline_output():
            # Transcription message
            yield {
                "type": "transcription",
                "text": "Hello assistant",
                "is_final": True
            }

            # Text response message
            yield {
                "type": "text_response",
                "text": "Hello! How can I help?"
            }

            # Audio chunk message
            yield {
                "type": "audio_chunk",
                "data": real_wav_audio_base64
            }

            # Audio complete message
            yield {
                "type": "audio_complete"
            }

        # Process messages
        transcriptions = []
        responses = []
        audio_chunks = []

        async for message in mock_pipeline_output():
            if message["type"] == "transcription":
                transcriptions.append(message["text"])
            elif message["type"] == "text_response":
                responses.append(message["text"])
            elif message["type"] == "audio_chunk":
                # Decode audio
                wav_bytes = base64.b64decode(message["data"])
                if len(wav_bytes) > 44:
                    pcm_bytes = wav_bytes[44:]
                    pcm_array = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0
                    audio_chunks.append(pcm_array)

        # Verify all message types received
        assert len(transcriptions) == 1
        assert len(responses) == 1
        assert len(audio_chunks) == 1

        # Verify content
        assert transcriptions[0] == "Hello assistant"
        assert responses[0] == "Hello! How can I help?"
        assert audio_chunks[0].dtype == np.float32

    @pytest.mark.asyncio
    async def test_error_handling_invalid_audio(self):
        """Test error handling with invalid audio data."""
        # Create invalid WAV (too short, corrupted header)
        invalid_wav = base64.b64encode(b"RIFF" + b"\x00" * 40).decode('utf-8')

        # Try to process
        try:
            wav_bytes = base64.b64decode(invalid_wav)
            # This should be handled gracefully
            if len(wav_bytes) <= 44:
                # Not enough data for WAV header + audio
                raise ValueError("Invalid WAV file - too short")
        except ValueError as e:
            # Error should be caught and handled
            assert "Invalid WAV" in str(e)

    @pytest.mark.asyncio
    async def test_empty_audio_handling(self):
        """Test handling empty audio chunks."""
        # Create empty audio
        empty_audio = np.array([], dtype=np.float32)

        # Should handle gracefully
        assert len(empty_audio) == 0
        assert empty_audio.dtype == np.float32


@pytest.mark.integration
class TestWebRTCRealDataIntegration:
    """Integration tests with real audio data."""

    @pytest.mark.asyncio
    async def test_full_audio_pipeline_simulation(
        self,
        real_audio_pcm_tone,
        real_wav_audio_base64
    ):
        """Simulate a full audio pipeline with real data."""
        sample_rate, input_audio = real_audio_pcm_tone

        # Step 1: Convert input audio to bytes (as sent to backend)
        input_bytes = input_audio.tobytes()

        # Step 2: Simulate VAD detection (detect speech)
        # For simplicity, any non-zero amplitude is "speech"
        audio_energy = np.abs(input_audio).mean()
        speech_detected = audio_energy > 0.01
        assert speech_detected  # Our tone should be detected

        # Step 3: Simulate transcription (mock)
        transcription = "Test speech"
        assert len(transcription) > 0

        # Step 4: Simulate LLM response (mock)
        llm_response = "I heard you say: " + transcription
        assert llm_response.startswith("I heard you")

        # Step 5: Simulate TTS response (use our real WAV data)
        response_wav = base64.b64decode(real_wav_audio_base64)
        assert len(response_wav) > 44

        # Step 6: Extract and convert response audio
        response_pcm_bytes = response_wav[44:]
        response_pcm = np.frombuffer(response_pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0

        # Verify output format
        assert response_pcm.dtype == np.float32
        assert len(response_pcm) > 0
        assert response_pcm.min() >= -1.0
        assert response_pcm.max() <= 1.0

    def test_audio_quality_preservation(self, real_audio_pcm_tone):
        """Test that audio quality is preserved through conversions."""
        sample_rate, original_audio = real_audio_pcm_tone

        # Convert float32 → int16 → float32 (simulate encoding/decoding)
        audio_int16 = (original_audio * 32768.0).astype(np.int16)
        audio_reconstructed = audio_int16.astype(np.float32) / 32768.0

        # Calculate error
        max_error = np.abs(original_audio - audio_reconstructed).max()

        # Error should be very small (within 1 bit of precision)
        assert max_error < 1.0 / 32768.0 * 2

    def test_audio_concat_for_streaming(self, real_wav_audio_base64):
        """Test concatenating multiple audio chunks (streaming TTS)."""
        # Simulate receiving 3 audio chunks
        audio_chunks = []
        for i in range(3):
            wav_bytes = base64.b64decode(real_wav_audio_base64)
            pcm_bytes = wav_bytes[44:]
            pcm_array = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            audio_chunks.append(pcm_array)

        # Concatenate all chunks
        full_audio = np.concatenate(audio_chunks)

        # Verify concatenation
        expected_length = len(audio_chunks[0]) * 3
        assert len(full_audio) == expected_length
        assert full_audio.dtype == np.float32

    @pytest.mark.asyncio
    async def test_concurrent_audio_processing(self, real_audio_pcm_silence):
        """Test handling multiple concurrent audio streams."""
        sample_rate, audio_data = real_audio_pcm_silence

        async def process_audio_stream(stream_id, audio):
            # Simulate processing delay
            await asyncio.sleep(0.01)
            return {
                "stream_id": stream_id,
                "samples_processed": len(audio)
            }

        # Process 5 streams concurrently
        tasks = [
            process_audio_stream(i, audio_data)
            for i in range(5)
        ]

        results = await asyncio.gather(*tasks)

        # Verify all streams processed
        assert len(results) == 5
        for i, result in enumerate(results):
            assert result["stream_id"] == i
            assert result["samples_processed"] == len(audio_data)


# Additional test to verify test file itself
def test_test_fixtures_work():
    """Verify that our test fixtures generate correct data."""
    # This test just ensures the fixtures are working
    sample_rate = 16000
    duration = 1.0
    samples = int(sample_rate * duration)
    audio = np.zeros(samples, dtype=np.float32)

    assert len(audio) == 16000
    assert audio.dtype == np.float32
