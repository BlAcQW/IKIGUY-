#!/usr/bin/env python3
"""
Unified Voice Pipeline
Handles: VAD → STT → LLM → TTS streaming

Inspired by HuggingFace speech-to-speech + FastRTC patterns.
Provides a clean, modular interface for voice conversations.
"""

import logging
import asyncio
import numpy as np
import base64
import tempfile
import os
from typing import AsyncGenerator, Optional, Dict, Any
from pathlib import Path

# Import shared services
from apps.shared.integration.ai_services import (
    get_streaming_tts_service,
    VADSession,
    create_vad_session
)

logger = logging.getLogger(__name__)


class VoicePipeline:
    """
    Unified voice conversation pipeline.

    Handles the complete voice conversation flow:
    1. Audio collection with VAD (Voice Activity Detection)
    2. STT (Speech-to-Text) transcription
    3. LLM (Large Language Model) response generation
    4. TTS (Text-to-Speech) streaming

    This provides a cleaner, more maintainable architecture compared to
    manual state machines.
    """

    def __init__(
        self,
        assistant_id: str,
        pause_threshold_ms: int = 1500,
        sample_rate: int = 16000,
        # Provider overrides from voice settings
        llm_provider: Optional[str] = None,
        llm_model: Optional[str] = None,
        tts_provider: Optional[str] = None,
        stt_provider: Optional[str] = None,
        language: Optional[str] = None
    ):
        """
        Initialize voice pipeline.

        Args:
            assistant_id: ID of assistant to use
            pause_threshold_ms: Milliseconds of silence to trigger turn completion
            sample_rate: Audio sample rate (default 16000 Hz)
            llm_provider: Optional LLM provider override from voice settings
            llm_model: Optional LLM model override from voice settings
            tts_provider: Optional TTS provider override from voice settings
            stt_provider: Optional STT provider override from voice settings
            language: Optional language override from voice settings
        """
        self.assistant_id = assistant_id
        self.pause_threshold = pause_threshold_ms
        self.sample_rate = sample_rate
        # Store provider overrides
        self.llm_provider_override = llm_provider
        self.llm_model_override = llm_model
        self.tts_provider_override = tts_provider
        self.stt_provider_override = stt_provider
        self.language_override = language

        # Lazy-loaded components
        self.assistant = None
        self.vad_session = None
        self.whisper_service = None
        self.streaming_tts = None

        # Conversation tracking
        self.turn_count = 0

        logger.info(f"🎵 VoicePipeline initialized for assistant: {assistant_id}")

    async def process_turn(
        self,
        audio_stream: AsyncGenerator[bytes, None],
        user_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process a complete conversation turn.

        This is the main entry point for the pipeline. It:
        1. Collects audio until pause detected
        2. Transcribes to text
        3. Generates LLM response
        4. Streams TTS audio

        Args:
            audio_stream: Generator yielding PCM audio chunks (bytes)
            user_id: Optional user ID for conversation tracking

        Yields:
            Messages with type and data:
            - {"type": "transcription", "data": {"text": "...", "is_final": bool}}
            - {"type": "text_response", "data": "..."}
            - {"type": "audio_chunk", "data": "base64..."}
            - {"type": "audio_complete", "data": {...}}
        """
        try:
            self.turn_count += 1
            logger.info(f"🔄 Processing turn {self.turn_count}")

            # 1. Collect audio until pause detected (VAD)
            logger.info("🎤 Collecting audio with VAD...")
            utterance_audio = await self._collect_utterance(audio_stream)

            if utterance_audio is None or len(utterance_audio) == 0:
                logger.warning("⚠️ No audio collected, skipping turn")
                return

            logger.info(f"✅ Collected {len(utterance_audio)} audio samples")

            # 2. Transcribe (STT)
            logger.info("📝 Transcribing audio...")
            transcription = await self._transcribe(utterance_audio)

            if not transcription or len(transcription.strip()) == 0:
                logger.warning("⚠️ Empty transcription, skipping turn")
                return

            logger.info(f"✅ Transcription: '{transcription}'")

            # Yield transcription
            yield {
                "type": "transcription",
                "data": {"text": transcription, "is_final": True}
            }

            # 3. Generate response (LLM)
            logger.info("🤖 Generating LLM response...")
            response_text = await self._generate_response(transcription)

            if not response_text or len(response_text.strip()) == 0:
                logger.warning("⚠️ Empty LLM response, skipping turn")
                return

            logger.info(f"✅ Response: '{response_text[:100]}...'")

            # Yield text response
            yield {
                "type": "text_response",
                "data": response_text
            }

            # 4. Stream TTS
            logger.info("🔊 Streaming TTS...")
            chunk_count = 0
            first_chunk_latency = None
            import time
            tts_start = time.time()

            async for audio_chunk in self._stream_tts(response_text):
                chunk_count += 1

                if chunk_count == 1:
                    first_chunk_latency = time.time() - tts_start
                    logger.info(f"⚡ First TTS chunk in {first_chunk_latency:.3f}s")

                # Convert numpy array to base64 WAV
                from apps.core_backend.backend.services.pcm_vad_handler import pcm_to_wav
                wav_bytes = pcm_to_wav(audio_chunk, sample_rate=self.sample_rate)
                audio_base64 = base64.b64encode(wav_bytes).decode('utf-8')

                # Yield audio chunk
                yield {
                    "type": "audio_chunk",
                    "data": audio_base64
                }

            # Yield completion
            yield {
                "type": "audio_complete",
                "data": {
                    "chunks": chunk_count,
                    "first_chunk_latency": first_chunk_latency,
                    "streaming": True
                }
            }

            logger.info(f"✅ Turn {self.turn_count} complete: {chunk_count} audio chunks")

        except Exception as e:
            logger.error(f"❌ Error in pipeline turn {self.turn_count}: {e}")
            import traceback
            traceback.print_exc()

            # Yield error
            yield {
                "type": "error",
                "data": str(e)
            }

    async def send_first_message(
        self,
        user_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Send first message without requiring user audio input.

        Handles three modes based on assistant configuration:
        - "assistant_waits": Skip first message, return immediately
        - "assistant_speaks_first": Use predefined first_message with TTS
        - "assistant_speaks_first_with_model_message": Generate greeting with LLM, then TTS

        Args:
            user_id: Optional user ID for conversation tracking

        Yields:
            Messages with type and data:
            - {"type": "text_response", "data": "..."}
            - {"type": "audio_chunk", "data": "base64..."}
            - {"type": "audio_complete", "data": {...}}
        """
        try:
            # Load assistant configuration
            assistant = await self._get_assistant()

            # Get first message mode (default to "assistant_speaks_first" for backward compatibility)
            mode = getattr(assistant, 'first_message_mode', 'assistant_speaks_first')

            logger.info(f"🎬 First message mode: {mode}")

            if mode == "assistant_waits":
                logger.info("🤫 Assistant waiting for user to speak first")
                # Return immediately - no first message
                return

            elif mode == "assistant_speaks_first":
                first_message = getattr(assistant, 'first_message', '')
                if not first_message:
                    # FAIL LOUDLY - no silent fallbacks
                    error_msg = "first_message_mode is 'assistant_speaks_first' but first_message is empty"
                    logger.error(f"❌ CRITICAL: {error_msg}")
                    raise ValueError(error_msg)

                logger.info(f"👋 Sending predefined first message: '{first_message[:50]}...'")

                # Yield text response
                yield {
                    "type": "text_response",
                    "data": first_message
                }

                # Stream TTS audio
                try:
                    # Get actual sample rate from TTS model
                    tts_service = await self._get_tts_service()
                    actual_sample_rate = tts_service.get_native_sample_rate()
                    logger.info(f"🎵 Using TTS native sample rate: {actual_sample_rate} Hz")

                    chunk_count = 0
                    async for audio_chunk in self._stream_tts(first_message):
                        # audio_chunk is numpy array, convert to base64 WAV for transmission
                        # Convert to int16 PCM
                        pcm_int16 = (audio_chunk * 32767).astype(np.int16)

                        # Create WAV header with ACTUAL sample rate from model
                        import io
                        import wave
                        wav_io = io.BytesIO()
                        with wave.open(wav_io, 'wb') as wav_file:
                            wav_file.setnchannels(1)  # Mono
                            wav_file.setsampwidth(2)  # 16-bit
                            wav_file.setframerate(actual_sample_rate)  # Use model's native rate!
                            wav_file.writeframes(pcm_int16.tobytes())

                        # Encode to base64
                        wav_io.seek(0)
                        wav_bytes = wav_io.read()
                        audio_base64 = base64.b64encode(wav_bytes).decode('utf-8')

                        chunk_count += 1
                        yield {
                            "type": "audio_chunk",
                            "data": audio_base64
                        }

                    logger.info(f"✅ First message TTS completed: {chunk_count} chunks")

                    # Yield completion
                    yield {
                        "type": "audio_complete",
                        "data": {
                            "chunks": chunk_count,
                            "text": first_message
                        }
                    }

                except Exception as e:
                    # FAIL LOUDLY - no silent fallbacks
                    error_msg = f"First message TTS failed: {str(e)}"
                    logger.error(f"❌ CRITICAL: {error_msg}", exc_info=True)
                    raise

            elif mode == "assistant_speaks_first_with_model_message":
                logger.info("🤖 Generating first message with LLM...")

                # Get guidance from first_message field (optional)
                first_message_guidance = getattr(assistant, 'first_message', '')

                if first_message_guidance:
                    # User provided guidance for the greeting
                    greeting_prompt = first_message_guidance
                else:
                    # Use default greeting prompt
                    greeting_prompt = "Generate a brief, friendly greeting message. Introduce yourself and ask how you can help."

                try:
                    # Generate greeting using LLM
                    greeting = await self._generate_response(greeting_prompt)

                    if not greeting:
                        # FAIL LOUDLY - no silent fallbacks
                        error_msg = "LLM returned empty greeting for first message"
                        logger.error(f"❌ CRITICAL: {error_msg}")
                        raise ValueError(error_msg)

                    logger.info(f"👋 Generated greeting: '{greeting[:50]}...'")

                    # Yield text response
                    yield {
                        "type": "text_response",
                        "data": greeting
                    }

                    # Stream TTS audio
                    try:
                        # Get actual sample rate from TTS model
                        tts_service = await self._get_tts_service()
                        actual_sample_rate = tts_service.get_native_sample_rate()
                        logger.info(f"🎵 Using TTS native sample rate: {actual_sample_rate} Hz")

                        chunk_count = 0
                        async for audio_chunk in self._stream_tts(greeting):
                            # audio_chunk is numpy array, convert to base64 WAV
                            pcm_int16 = (audio_chunk * 32767).astype(np.int16)

                            # Create WAV with ACTUAL sample rate from model
                            import io
                            import wave
                            wav_io = io.BytesIO()
                            with wave.open(wav_io, 'wb') as wav_file:
                                wav_file.setnchannels(1)
                                wav_file.setsampwidth(2)
                                wav_file.setframerate(actual_sample_rate)  # Use model's native rate!
                                wav_file.writeframes(pcm_int16.tobytes())

                            # Encode to base64
                            wav_io.seek(0)
                            wav_bytes = wav_io.read()
                            audio_base64 = base64.b64encode(wav_bytes).decode('utf-8')

                            chunk_count += 1
                            yield {
                                "type": "audio_chunk",
                                "data": audio_base64
                            }

                        logger.info(f"✅ Model-generated first message TTS completed: {chunk_count} chunks")

                        # Yield completion
                        yield {
                            "type": "audio_complete",
                            "data": {
                                "chunks": chunk_count,
                                "text": greeting
                            }
                        }

                    except Exception as e:
                        # FAIL LOUDLY - no silent fallbacks
                        error_msg = f"Model-generated first message TTS failed: {str(e)}"
                        logger.error(f"❌ CRITICAL: {error_msg}", exc_info=True)
                        raise

                except Exception as e:
                    # FAIL LOUDLY - no silent fallbacks
                    error_msg = f"Failed to generate model-based first message: {str(e)}"
                    logger.error(f"❌ CRITICAL: {error_msg}", exc_info=True)
                    raise

            else:
                # FAIL LOUDLY - no silent fallbacks
                error_msg = f"Unknown first_message_mode: {mode}"
                logger.error(f"❌ CRITICAL: {error_msg}")
                raise ValueError(error_msg)

        except Exception as e:
            # Re-raise the exception to fail loudly
            logger.error(f"❌ CRITICAL Error in send_first_message: {e}", exc_info=True)
            raise

    async def _collect_utterance(
        self,
        audio_stream: AsyncGenerator[bytes, None]
    ) -> Optional[np.ndarray]:
        """
        Collect audio until VAD detects pause.

        Args:
            audio_stream: Generator yielding PCM audio chunks

        Returns:
            Complete utterance as numpy array, or None if no speech detected
        """
        try:
            # Initialize VAD session if not exists
            if not self.vad_session:
                self.vad_session = create_vad_session(
                    session_id=f"pipeline-{self.assistant_id}-{self.turn_count}",
                    min_silence_duration_ms=self.pause_threshold
                )
                self.vad_session.start_listening()
                logger.info(f"🎧 VAD session started (pause threshold: {self.pause_threshold}ms)")

            # Collect audio chunks
            async for pcm_bytes in audio_stream:
                # Decode PCM bytes to float32 array
                if isinstance(pcm_bytes, str):
                    # If base64 encoded
                    pcm_bytes = base64.b64decode(pcm_bytes)

                # Convert bytes to numpy array
                pcm_array = np.frombuffer(pcm_bytes, dtype=np.float32)

                # Process with VAD
                is_speech, complete, utterance_audio = self.vad_session.process_chunk(pcm_array)

                if complete and utterance_audio is not None:
                    logger.info(f"🎤 Utterance complete: {len(utterance_audio)} samples")
                    # Reset VAD for next turn
                    self.vad_session = None
                    return utterance_audio

            return None

        except Exception as e:
            logger.error(f"❌ Error collecting utterance: {e}")
            return None

    async def _transcribe(self, audio: np.ndarray) -> str:
        """
        Transcribe audio to text using Whisper.

        Args:
            audio: Audio samples as numpy array

        Returns:
            Transcription text
        """
        try:
            # Get Whisper service
            if not self.whisper_service:
                from apps.core_backend.backend.services.faster_whisper_service import get_faster_whisper_service
                self.whisper_service = get_faster_whisper_service()

            # Get assistant config
            assistant = await self._get_assistant()

            # Convert to WAV
            from apps.core_backend.backend.services.pcm_vad_handler import pcm_to_wav
            wav_bytes = pcm_to_wav(audio, sample_rate=self.sample_rate)

            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_file.write(wav_bytes)
                tmp_path = tmp_file.name

            try:
                # Transcribe
                language = getattr(assistant, 'language', 'auto')
                result = await self.whisper_service.transcribe_audio(
                    audio_path=tmp_path,
                    language=language,
                    model_size="base"
                )

                return result.text.strip()

            finally:
                # Clean up temp file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        except Exception as e:
            logger.error(f"❌ Transcription error: {e}")
            return ""

    async def _generate_response(self, text: str) -> str:
        """
        Generate LLM response.

        Args:
            text: User's transcribed text

        Returns:
            LLM response text
        """
        try:
            # Get assistant config
            assistant = await self._get_assistant()

            # Import LLM service
            from apps.core_backend.backend.services.llm_service import generate_llm_response

            # Get LLM configuration
            llm_provider = getattr(assistant, 'llm_provider', 'openai')
            llm_model = getattr(assistant, 'llm_model', 'gpt-4o-mini')
            system_prompt = getattr(assistant, 'system_prompt', 'You are a helpful assistant.')

            # Generate response
            response = await generate_llm_response(
                text,
                system_prompt,
                llm_provider,
                llm_model
            )

            return response

        except Exception as e:
            logger.error(f"❌ LLM generation error: {e}")
            return "I'm sorry, I encountered an error generating a response."

    async def _get_tts_service(self):
        """
        Lazy load TTS service.

        Returns:
            StreamingTTSService instance
        """
        if not self.streaming_tts:
            self.streaming_tts = get_streaming_tts_service()
        return self.streaming_tts

    async def _stream_tts(self, text: str) -> AsyncGenerator[np.ndarray, None]:
        """
        Stream TTS audio.

        Args:
            text: Text to synthesize

        Yields:
            Audio chunks as numpy arrays
        """
        try:
            # Get streaming TTS service
            tts_service = await self._get_tts_service()

            # Get assistant config
            assistant = await self._get_assistant()

            # Get voice description
            voice_description = getattr(assistant, 'voice_description', None)
            if not voice_description:
                voice_description = "A clear, neutral voice"

            # Stream audio chunks
            async for audio_chunk in tts_service.stream_tts(
                text=text,
                voice_description=voice_description,
                sample_rate=self.sample_rate
            ):
                yield audio_chunk

        except Exception as e:
            logger.error(f"❌ TTS streaming error: {e}")
            # Yield silence on error
            yield np.zeros(self.sample_rate, dtype=np.float32)

    async def _get_assistant(self):
        """
        Lazy load assistant configuration from MongoDB.

        Returns:
            Assistant configuration object

        Raises:
            ValueError: If assistant not found or missing required fields
        """
        if not self.assistant:
            from apps.core_backend.backend.services.assistant_service import assistant_service
            self.assistant = assistant_service.get_assistant(self.assistant_id)

            if not self.assistant:
                raise ValueError(f"Assistant {self.assistant_id} not found")

            # Validate assistant has required fields (defensive check)
            assistant_name = getattr(self.assistant, 'name', 'Unknown')
            logger.info(f"📋 Loaded assistant: {assistant_name}")

            # Check for critical fields (warn but don't fail - use defaults)
            if not hasattr(self.assistant, 'language'):
                logger.warning(f"⚠️ Assistant {assistant_name} missing 'language' field, will use defaults")

            if not hasattr(self.assistant, 'tts_provider'):
                logger.warning(f"⚠️ Assistant {assistant_name} missing 'tts_provider' field, will use defaults")

        return self.assistant

    def reset(self):
        """Reset pipeline for new conversation."""
        self.vad_session = None
        self.turn_count = 0
        logger.info("🔄 Pipeline reset")


# Convenience function
def create_voice_pipeline(
    assistant_id: str,
    pause_threshold_ms: int = 1500,
    sample_rate: int = 16000
) -> VoicePipeline:
    """
    Create a voice pipeline instance.

    Args:
        assistant_id: ID of assistant to use
        pause_threshold_ms: VAD pause threshold
        sample_rate: Audio sample rate

    Returns:
        VoicePipeline instance
    """
    return VoicePipeline(
        assistant_id=assistant_id,
        pause_threshold_ms=pause_threshold_ms,
        sample_rate=sample_rate
    )


__all__ = [
    'VoicePipeline',
    'create_voice_pipeline'
]
