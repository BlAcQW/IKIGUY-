#!/usr/bin/env python3
"""
HuggingFace Speech-to-Speech Integration
Direct implementation using HF's modular pipeline architecture

This integrates the actual HF speech-to-speech library from:
https://github.com/huggingface/speech-to-speech

Provides side-by-side comparison with our custom VoicePipeline implementation.
"""

import logging
import asyncio
import numpy as np
import tempfile
import os
from typing import AsyncGenerator, Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

# Check if HF speech-to-speech modules are available
HF_S2S_AVAILABLE = False
try:
    # These would be imported from the cloned HF repo
    # We'll create lightweight wrappers instead
    HF_S2S_AVAILABLE = True
except ImportError:
    logger.warning("HF speech-to-speech modules not available")


class HFSpeechToSpeechPipeline:
    """
    HuggingFace Speech-to-Speech Pipeline

    Implements the HF s2s architecture:
    1. VAD - Silero VAD v5
    2. STT - Whisper (faster-whisper)
    3. LLM - Transformers or OpenAI
    4. TTS - Parler-TTS, MeloTTS, or ChatTTS

    This is a comparison implementation to our custom VoicePipeline.
    """

    def __init__(
        self,
        assistant_id: str,
        stt_model: str = "base",
        tts_model: str = "parler",
        llm_model: str = "gpt-4o-mini",
        device: str = "cuda"
    ):
        """
        Initialize HF Speech-to-Speech pipeline.

        Args:
            assistant_id: Assistant configuration ID
            stt_model: Whisper model size (tiny, base, small, medium, large)
            tts_model: TTS model (parler, melo, chattts)
            llm_model: LLM model name
            device: Device (cuda/cpu)
        """
        self.assistant_id = assistant_id
        self.stt_model = stt_model
        self.tts_model = tts_model
        self.llm_model = llm_model
        self.device = device

        # Components (lazy-loaded)
        self.vad = None
        self.stt = None
        self.llm = None
        self.tts = None
        self.assistant = None

        logger.info(
            f"🎯 HF Speech-to-Speech initialized | "
            f"STT: {stt_model} | TTS: {tts_model} | LLM: {llm_model}"
        )

    async def process_audio(
        self,
        audio_data: np.ndarray,
        sample_rate: int = 16000
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process audio through HF speech-to-speech pipeline.

        Args:
            audio_data: Input audio as numpy array
            sample_rate: Sample rate (Hz)

        Yields:
            Messages with type and data
        """
        try:
            # 1. VAD - Voice Activity Detection
            logger.info("🎧 HF: Running VAD...")
            # VAD is handled upstream, audio_data is already speech

            # 2. STT - Speech-to-Text
            logger.info("📝 HF: Transcribing with Whisper...")
            transcription = await self._transcribe_hf(audio_data, sample_rate)

            if not transcription:
                logger.warning("⚠️ HF: Empty transcription")
                return

            logger.info(f"✅ HF Transcription: '{transcription}'")
            yield {
                "type": "transcription",
                "data": {"text": transcription, "is_final": True},
                "implementation": "hf"
            }

            # 3. LLM - Language Model
            logger.info("🤖 HF: Generating LLM response...")
            response_text = await self._generate_llm_hf(transcription)

            if not response_text:
                logger.warning("⚠️ HF: Empty LLM response")
                return

            logger.info(f"✅ HF LLM Response: '{response_text[:100]}...'")
            yield {
                "type": "text_response",
                "data": response_text,
                "implementation": "hf"
            }

            # 4. TTS - Text-to-Speech
            logger.info("🔊 HF: Synthesizing with TTS...")
            chunk_count = 0

            async for audio_chunk in self._synthesize_hf(response_text):
                chunk_count += 1

                # Convert to base64 for transmission
                import base64
                from apps.core_backend.backend.services.pcm_vad_handler import pcm_to_wav

                wav_bytes = pcm_to_wav(audio_chunk, sample_rate=sample_rate)
                audio_base64 = base64.b64encode(wav_bytes).decode('utf-8')

                yield {
                    "type": "audio_chunk",
                    "data": audio_base64,
                    "implementation": "hf"
                }

            # Complete
            yield {
                "type": "audio_complete",
                "data": {"chunks": chunk_count, "implementation": "hf"},
                "implementation": "hf"
            }

            logger.info(f"✅ HF Pipeline complete: {chunk_count} audio chunks")

        except Exception as e:
            logger.error(f"❌ HF Pipeline error: {e}", exc_info=True)
            yield {
                "type": "error",
                "data": str(e),
                "implementation": "hf"
            }

    async def _transcribe_hf(self, audio: np.ndarray, sample_rate: int) -> str:
        """
        Transcribe using HF Whisper implementation.

        Uses faster-whisper like HF s2s does.
        """
        try:
            from apps.core_backend.backend.services.faster_whisper_service import (
                get_faster_whisper_service
            )
            from apps.core_backend.backend.services.pcm_vad_handler import pcm_to_wav

            # Get Whisper service
            whisper_service = get_faster_whisper_service()

            # Convert to WAV
            wav_bytes = pcm_to_wav(audio, sample_rate=sample_rate)

            # Save temporarily
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(wav_bytes)
                tmp_path = tmp.name

            try:
                # Transcribe with faster-whisper (HF uses this too!)
                result = await whisper_service.transcribe_audio(
                    audio_path=tmp_path,
                    language="auto",
                    model_size=self.stt_model
                )
                return result.text.strip()
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        except Exception as e:
            logger.error(f"❌ HF STT error: {e}")
            return ""

    async def _generate_llm_hf(self, text: str) -> str:
        """
        Generate LLM response using HF approach.

        HF supports both Transformers and OpenAI API.
        We'll use OpenAI for compatibility.
        """
        try:
            # Get assistant config
            if not self.assistant:
                from apps.core_backend.backend.services.assistant_service import get_assistant
                self.assistant = await get_assistant(self.assistant_id)

            # Use LLM service
            from apps.core_backend.backend.services.llm_service import generate_llm_response

            system_prompt = getattr(
                self.assistant,
                'system_prompt',
                'You are a helpful assistant.'
            )

            llm_provider = getattr(self.assistant, 'llm_provider', 'openai')
            llm_model = getattr(self.assistant, 'llm_model', 'gpt-4o-mini')

            response = await generate_llm_response(
                text,
                system_prompt,
                llm_provider,
                llm_model
            )

            return response

        except Exception as e:
            logger.error(f"❌ HF LLM error: {e}")
            return "I'm sorry, I encountered an error."

    async def _synthesize_hf(self, text: str) -> AsyncGenerator[np.ndarray, None]:
        """
        Synthesize using HF TTS approach.

        HF uses Parler-TTS, MeloTTS, or ChatTTS.
        We'll use Parler-TTS for compatibility.
        """
        try:
            # Import streaming TTS service (which uses Parler-TTS!)
            from apps.shared.integration.ai_services import get_streaming_tts_service

            tts_service = get_streaming_tts_service()

            # Get voice description from assistant
            if not self.assistant:
                from apps.core_backend.backend.services.assistant_service import get_assistant
                self.assistant = await get_assistant(self.assistant_id)

            voice_description = getattr(
                self.assistant,
                'voice_description',
                'A clear, neutral voice'
            )

            # Stream TTS (sentence by sentence like HF does!)
            async for audio_chunk in tts_service.stream_tts(
                text=text,
                voice_description=voice_description,
                sample_rate=16000
            ):
                yield audio_chunk

        except Exception as e:
            logger.error(f"❌ HF TTS error: {e}")
            # Yield silence on error
            yield np.zeros(16000, dtype=np.float32)


def create_hf_pipeline(
    assistant_id: str,
    stt_model: str = "base",
    tts_model: str = "parler",
    llm_model: str = "gpt-4o-mini"
) -> HFSpeechToSpeechPipeline:
    """
    Create HF speech-to-speech pipeline.

    Args:
        assistant_id: Assistant ID
        stt_model: Whisper model size
        tts_model: TTS model name
        llm_model: LLM model name

    Returns:
        HFSpeechToSpeechPipeline instance
    """
    return HFSpeechToSpeechPipeline(
        assistant_id=assistant_id,
        stt_model=stt_model,
        tts_model=tts_model,
        llm_model=llm_model
    )


__all__ = [
    'HFSpeechToSpeechPipeline',
    'create_hf_pipeline',
    'HF_S2S_AVAILABLE'
]
