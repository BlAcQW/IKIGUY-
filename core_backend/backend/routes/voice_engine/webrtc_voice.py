#!/usr/bin/env python3
"""
WebRTC Voice Chat Handler using FastRTC
Provides low-latency voice conversations with streaming TTS

Uses the actual FastRTC API (Stream + ReplyOnPause).
"""

import logging
import asyncio
import numpy as np
import tempfile
import os
from typing import Optional, Tuple
from fastapi import FastAPI
from fastrtc import Stream, ReplyOnPause

# Import VoicePipeline for unified conversation flow
from apps.shared.integration.voice_pipeline import VoicePipeline
from apps.core_backend.backend.services.pcm_vad_handler import pcm_to_wav

logger = logging.getLogger(__name__)


class WebRTCVoiceAgent:
    """
    WebRTC Voice Agent using VoicePipeline.

    Integrates with FastRTC's ReplyOnPause to provide voice conversations.
    """

    def __init__(self, assistant_id: str, pause_threshold_ms: int = 1500):
        """
        Initialize WebRTC voice agent.

        Args:
            assistant_id: ID of assistant to use
            pause_threshold_ms: Pause threshold for VAD
        """
        self.assistant_id = assistant_id
        self.pause_threshold_ms = pause_threshold_ms
        self.pipeline = None
        logger.info(f"🎙️  WebRTC Voice Agent initialized for assistant: {assistant_id}")

    def __call__(self, audio: Tuple[int, np.ndarray]):
        """
        Handle incoming audio from WebRTC client.

        This is called by FastRTC's ReplyOnPause when the user pauses speaking.

        Args:
            audio: Tuple of (sample_rate, audio_data)

        Yields:
            Tuple of (sample_rate, response_audio_data)
        """
        sample_rate, audio_data = audio

        logger.info(f"🎤 Received WebRTC audio: {len(audio_data)} samples at {sample_rate}Hz")

        try:
            # Process audio synchronously using asyncio.run
            # (FastRTC ReplyOnPause expects sync generator)
            response_audio_chunks = asyncio.run(self._process_audio(audio_data, sample_rate))

            # Yield each response audio chunk
            for chunk in response_audio_chunks:
                yield (sample_rate, chunk)

        except Exception as e:
            logger.error(f"❌ Error processing WebRTC audio: {e}")
            import traceback
            traceback.print_exc()
            # Yield silence on error
            yield (sample_rate, np.zeros(sample_rate, dtype=np.float32))

    async def _process_audio(
        self,
        audio_data: np.ndarray,
        sample_rate: int
    ) -> list:
        """
        Process audio through VoicePipeline.

        Args:
            audio_data: Audio samples as numpy array
            sample_rate: Sample rate (usually 16000)

        Returns:
            List of response audio chunks
        """
        # Create pipeline if not exists
        if not self.pipeline:
            self.pipeline = VoicePipeline(
                assistant_id=self.assistant_id,
                pause_threshold_ms=self.pause_threshold_ms,
                sample_rate=sample_rate
            )

        # Create audio stream generator from single audio chunk
        async def audio_stream():
            # Convert numpy array to bytes
            audio_bytes = audio_data.tobytes()
            yield audio_bytes

        # Collect response audio chunks
        response_chunks = []

        async for message in self.pipeline.process_turn(audio_stream()):
            if message["type"] == "audio_chunk":
                # Decode base64 WAV to PCM
                import base64
                wav_bytes = base64.b64decode(message["data"])

                # For simplicity, extract PCM from WAV
                # WAV header is 44 bytes for standard PCM WAV
                if len(wav_bytes) > 44:
                    pcm_bytes = wav_bytes[44:]  # Skip WAV header
                    pcm_array = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0
                    response_chunks.append(pcm_array)

        return response_chunks


def create_webrtc_stream(assistant_id: str) -> Stream:
    """
    Create a FastRTC Stream for WebRTC voice chat.

    Args:
        assistant_id: ID of assistant to use for conversations

    Returns:
        FastRTC Stream instance
    """
    from fastrtc.reply_on_pause import AlgoOptions

    logger.info(f"📡 Creating WebRTC stream for assistant: {assistant_id}")

    # Create voice agent
    agent = WebRTCVoiceAgent(assistant_id=assistant_id)

    # Configure pause detection algorithm
    algo_options = AlgoOptions(
        audio_chunk_duration=0.6,  # Process audio in 600ms chunks
        started_talking_threshold=0.2,  # Pause threshold (200ms)
        speech_threshold=0.1  # Speech detection threshold
    )

    # Create FastRTC Stream with ReplyOnPause
    stream = Stream(
        handler=ReplyOnPause(
            agent,
            algo_options=algo_options
        ),
        modality="audio",
        mode="send-receive",
        ui_args={
            "title": "KasaAI Voice Assistant",
            "subtitle": "Speak naturally - I'll respond when you pause",
            "hide_title": False
        }
    )

    logger.info("✅ WebRTC stream created successfully")
    return stream


def setup_webrtc(app: FastAPI, assistant_id: str = None):
    """
    Setup WebRTC voice routes on FastAPI app.

    Args:
        app: FastAPI application instance
        assistant_id: Optional assistant ID (defaults to env var or first assistant)
    """
    logger.info("🚀 Setting up WebRTC voice routes...")

    # Get assistant ID from parameter or use default
    if not assistant_id:
        # In production, this would be configurable
        assistant_id = os.environ.get("DEFAULT_ASSISTANT_ID", "default-assistant")
        logger.warning(f"⚠️  No assistant_id provided, using: {assistant_id}")

    # Create WebRTC stream
    stream = create_webrtc_stream(assistant_id)

    # Mount stream on FastAPI app
    stream.mount(app, path="/voice/webrtc")

    logger.info("✅ WebRTC routes mounted at /voice/webrtc")
    logger.info("📝 WebRTC UI available at: /voice/webrtc")
    logger.info("📝 WebRTC offer endpoint: /voice/webrtc/offer (POST)")


# Export for use in main app
__all__ = [
    'setup_webrtc',
    'create_webrtc_stream',
    'WebRTCVoiceAgent'
]
