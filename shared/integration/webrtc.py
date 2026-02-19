#!/usr/bin/env python3
"""
WebRTC Integration for Voice Conversations using FastRTC
Provides low-latency voice chat with automatic turn-taking

Integrates:
- Gradio FastRTC (https://github.com/gradio-app/fastrtc)
- HF Speech-to-Speech pattern (VAD → STT → LLM → TTS)
- VoicePipeline for unified conversation flow

This module can be used by any KasaAI app for WebRTC voice functionality.
"""

import logging
import asyncio
import numpy as np
import time
import json
from typing import Optional, Tuple, Callable, Dict, Any
from fastapi import FastAPI

try:
    from fastrtc import Stream, ReplyOnPause
    from fastrtc.reply_on_pause import AlgoOptions
    FASTRTC_AVAILABLE = True
except ImportError:
    FASTRTC_AVAILABLE = False
    logging.warning("⚠️ fastrtc not installed. Install with: pip install 'fastrtc[vad,tts]'")

# Import VoicePipeline for unified conversation flow
from apps.shared.integration.voice_pipeline import VoicePipeline

logger = logging.getLogger(__name__)


class WebRTCVoiceAgent:
    """
    WebRTC Voice Agent using VoicePipeline and FastRTC.

    Implements the HF speech-to-speech pattern:
    1. VAD (Voice Activity Detection) - Detects when user stops speaking
    2. STT (Speech-to-Text) - Transcribes audio using Whisper
    3. LLM - Generates intelligent responses
    4. TTS (Text-to-Speech) - Streams audio response

    This agent integrates with FastRTC's ReplyOnPause for automatic turn-taking.
    """

    def __init__(
        self,
        assistant_id: str,
        pause_threshold_ms: int = 1500,
        sample_rate: int = 16000,
        on_transcription: Optional[Callable] = None,
        on_response: Optional[Callable] = None
    ):
        """
        Initialize WebRTC voice agent.

        Args:
            assistant_id: ID of assistant to use for conversations
            pause_threshold_ms: Pause threshold for VAD (default 1500ms)
            sample_rate: Audio sample rate (default 16000 Hz)
            on_transcription: Optional callback when transcription completes
            on_response: Optional callback when LLM responds
        """
        self.assistant_id = assistant_id
        self.pause_threshold_ms = pause_threshold_ms
        self.sample_rate = sample_rate
        self.pipeline = None
        self.on_transcription = on_transcription
        self.on_response = on_response

        logger.info(
            f"🎙️ WebRTC Voice Agent initialized | "
            f"Assistant: {assistant_id} | "
            f"Pause: {pause_threshold_ms}ms | "
            f"Sample Rate: {sample_rate}Hz"
        )

    def __call__(self, audio: Tuple[int, np.ndarray]):
        """
        Handle incoming audio from WebRTC client.

        This is called by FastRTC's ReplyOnPause when the user pauses speaking.
        Implements the full speech-to-speech pipeline.

        Args:
            audio: Tuple of (sample_rate, audio_data as numpy array)

        Yields:
            Tuple of (sample_rate, response_audio_data as numpy array)
        """
        sample_rate, audio_data = audio

        logger.info(
            f"🎤 Received WebRTC audio | "
            f"Samples: {len(audio_data):,} | "
            f"Rate: {sample_rate}Hz | "
            f"Duration: {len(audio_data)/sample_rate:.2f}s"
        )

        try:
            # Process audio synchronously using asyncio.run
            # (FastRTC ReplyOnPause expects sync generator)
            response_audio_chunks = asyncio.run(
                self._process_audio(audio_data, sample_rate)
            )

            # Yield each response audio chunk
            for chunk in response_audio_chunks:
                yield (sample_rate, chunk)

        except Exception as e:
            logger.error(f"❌ Error processing WebRTC audio: {e}", exc_info=True)
            # Yield silence on error to avoid breaking the stream
            yield (sample_rate, np.zeros(sample_rate, dtype=np.float32))

    async def _process_audio(
        self,
        audio_data: np.ndarray,
        sample_rate: int
    ) -> list:
        """
        Process audio through VoicePipeline (HF speech-to-speech pattern).

        Pipeline stages:
        1. VAD - Voice activity detection (built into VoicePipeline)
        2. STT - Speech-to-text transcription
        3. LLM - Language model response generation
        4. TTS - Text-to-speech synthesis

        Args:
            audio_data: Audio samples as numpy array (float32)
            sample_rate: Sample rate (usually 16000 Hz)

        Returns:
            List of response audio chunks as numpy arrays
        """
        # Create pipeline if not exists (lazy initialization)
        if not self.pipeline:
            self.pipeline = VoicePipeline(
                assistant_id=self.assistant_id,
                pause_threshold_ms=self.pause_threshold_ms,
                sample_rate=sample_rate
            )
            logger.info("✅ VoicePipeline initialized")

        # Create audio stream generator from single audio chunk
        async def audio_stream():
            """Convert numpy array to bytes stream"""
            audio_bytes = audio_data.tobytes()
            yield audio_bytes

        # Collect response audio chunks
        response_chunks = []
        transcription_text = ""
        response_text = ""

        # Process through pipeline
        async for message in self.pipeline.process_turn(audio_stream()):
            message_type = message["type"]

            if message_type == "transcription":
                transcription_text = message["data"]["text"]
                logger.info(f"📝 Transcription: '{transcription_text}'")

                # Call transcription callback if provided
                if self.on_transcription:
                    try:
                        self.on_transcription(transcription_text)
                    except Exception as e:
                        logger.error(f"Error in transcription callback: {e}")

            elif message_type == "text_response":
                response_text = message["data"]
                logger.info(f"💬 LLM Response: '{response_text[:100]}...'")

                # Call response callback if provided
                if self.on_response:
                    try:
                        self.on_response(response_text)
                    except Exception as e:
                        logger.error(f"Error in response callback: {e}")

            elif message_type == "audio_chunk":
                # Decode base64 WAV to PCM
                import base64
                wav_bytes = base64.b64decode(message["data"])

                # Extract PCM from WAV (skip 44-byte header)
                if len(wav_bytes) > 44:
                    pcm_bytes = wav_bytes[44:]
                    # Convert int16 PCM to float32 normalized [-1.0, 1.0]
                    pcm_array = np.frombuffer(
                        pcm_bytes,
                        dtype=np.int16
                    ).astype(np.float32) / 32768.0
                    response_chunks.append(pcm_array)

            elif message_type == "audio_complete":
                metadata = message["data"]
                logger.info(
                    f"🔊 Audio complete | "
                    f"Chunks: {metadata.get('chunks', 0)} | "
                    f"First chunk: {metadata.get('first_chunk_latency', 0):.3f}s"
                )

            elif message_type == "error":
                logger.error(f"❌ Pipeline error: {message['data']}")

        logger.info(
            f"✅ Processing complete | "
            f"Audio chunks: {len(response_chunks)} | "
            f"Input: '{transcription_text}' | "
            f"Output: '{response_text[:50]}...'"
        )

        return response_chunks

    async def send_first_message(self) -> list:
        """
        Send first message on connection initialization (before user speaks).

        Uses VoicePipeline.send_first_message() to generate greeting based on
        assistant's first_message_mode configuration.

        Returns:
            List of audio chunks as numpy arrays ready for WebRTC streaming
        """
        logger.info("🎬 Sending first message...")

        try:
            # Create pipeline if not exists
            if not self.pipeline:
                self.pipeline = VoicePipeline(
                    assistant_id=self.assistant_id,
                    pause_threshold_ms=self.pause_threshold_ms,
                    sample_rate=self.sample_rate
                )
                logger.info("✅ VoicePipeline initialized for first message")

            # Collect response audio chunks
            response_chunks = []
            response_text = ""

            # Process first message through pipeline
            async for message in self.pipeline.send_first_message():
                message_type = message["type"]

                if message_type == "text_response":
                    response_text = message["data"]
                    logger.info(f"👋 First message text: '{response_text[:100]}...'")

                    # Call response callback if provided
                    if self.on_response:
                        try:
                            self.on_response(response_text)
                        except Exception as e:
                            logger.error(f"Error in response callback: {e}")

                elif message_type == "audio_chunk":
                    # Decode base64 WAV to PCM
                    import base64
                    wav_bytes = base64.b64decode(message["data"])

                    # Extract PCM from WAV (skip 44-byte header)
                    if len(wav_bytes) > 44:
                        pcm_bytes = wav_bytes[44:]
                        # Convert int16 PCM to float32 normalized [-1.0, 1.0]
                        pcm_array = np.frombuffer(
                            pcm_bytes,
                            dtype=np.int16
                        ).astype(np.float32) / 32768.0
                        response_chunks.append(pcm_array)

                elif message_type == "audio_complete":
                    metadata = message["data"]
                    logger.info(
                        f"✅ First message complete | "
                        f"Chunks: {metadata.get('chunks', 0)} | "
                        f"Text: '{response_text[:50]}...'"
                    )

            logger.info(f"🔊 First message ready: {len(response_chunks)} audio chunks")
            return response_chunks

        except Exception as e:
            logger.error(f"❌ Error sending first message: {e}", exc_info=True)
            return []  # Return empty list on error

    def reset(self):
        """Reset the pipeline for a new conversation"""
        if self.pipeline:
            self.pipeline.reset()
        logger.info("🔄 WebRTC Voice Agent reset")


def create_webrtc_stream(
    assistant_id: str,
    pause_threshold_ms: int = 1500,
    sample_rate: int = 16000,
    ui_title: str = "KasaAI Voice Assistant",
    ui_subtitle: str = "Speak naturally - I'll respond when you pause",
    on_transcription: Optional[Callable] = None,
    on_response: Optional[Callable] = None
) -> Optional[Stream]:
    """
    Create a FastRTC Stream for WebRTC voice chat.

    This creates a complete WebRTC stream that can be mounted on a FastAPI app.
    Uses the HF speech-to-speech pattern with automatic turn-taking.

    Args:
        assistant_id: ID of assistant to use for conversations
        pause_threshold_ms: Milliseconds of silence to trigger turn (default 1500)
        sample_rate: Audio sample rate in Hz (default 16000)
        ui_title: Title for the Gradio UI (if using .ui.launch())
        ui_subtitle: Subtitle for the Gradio UI
        on_transcription: Optional callback(text: str) when transcription completes
        on_response: Optional callback(text: str) when LLM responds

    Returns:
        FastRTC Stream instance, or None if fastrtc not available

    Example:
        ```python
        stream = create_webrtc_stream(
            assistant_id="my-assistant-id",
            pause_threshold_ms=1500
        )
        stream.mount(app, path="/voice/webrtc")
        ```
    """
    if not FASTRTC_AVAILABLE:
        logger.error("❌ Cannot create WebRTC stream - fastrtc not installed")
        return None

    logger.info(
        f"📡 Creating WebRTC stream | "
        f"Assistant: {assistant_id} | "
        f"Pause: {pause_threshold_ms}ms"
    )

    # Create voice agent
    agent = WebRTCVoiceAgent(
        assistant_id=assistant_id,
        pause_threshold_ms=pause_threshold_ms,
        sample_rate=sample_rate,
        on_transcription=on_transcription,
        on_response=on_response
    )

    # Configure pause detection algorithm
    # These settings control when FastRTC triggers the agent callback
    algo_options = AlgoOptions(
        audio_chunk_duration=0.6,  # Process audio in 600ms chunks
        started_talking_threshold=0.2,  # Detect pause after 200ms silence
        speech_threshold=0.1  # Minimum amplitude to consider as speech
    )

    async def stream_first_message():
        """
        Stream first message via data channel when WebRTC connection opens.

        This is the PROPER implementation using FastRTC's startup_fn lifecycle hook.
        NO HTTP endpoints - streams audio chunks in real-time as they're generated.
        FAILS LOUDLY - no silent fallbacks.
        """
        from fastrtc.utils import current_channel

        channel = current_channel.get()
        if not channel:
            # FAIL LOUDLY - no fallback
            error_msg = "Data channel not available for first message streaming"
            logger.error(f"❌ CRITICAL: {error_msg}")
            raise RuntimeError(error_msg)

        logger.info(f"🎬 Streaming first message for assistant: {assistant_id}")

        chunk_count = 0
        start_time = time.time()
        first_chunk_time = None

        try:
            # Stream chunks in real-time as they're generated
            async for message in agent.pipeline.send_first_message():
                message_type = message["type"]

                if message_type == "text_response":
                    # Send text response to frontend
                    channel.send(json.dumps({
                        "type": "text_response",
                        "data": message["data"]
                    }))
                    logger.info(f"💬 First message text sent: '{message['data'][:50]}...'")

                elif message_type == "audio_chunk":
                    chunk_count += 1

                    # Record first chunk latency
                    if first_chunk_time is None:
                        first_chunk_time = time.time() - start_time
                        logger.info(f"⚡ First audio chunk latency: {first_chunk_time:.3f}s")

                    # Send audio chunk immediately via data channel (real-time streaming!)
                    channel.send(json.dumps({
                        "type": "audio_chunk",
                        "data": message["data"]
                    }))
                    logger.debug(f"🔊 Streamed audio chunk #{chunk_count}")

                elif message_type == "audio_complete":
                    # Notify completion
                    total_time = time.time() - start_time
                    channel.send(json.dumps({
                        "type": "audio_complete",
                        "data": {
                            "chunks": chunk_count,
                            "first_chunk_latency": first_chunk_time,
                            "total_duration": total_time
                        }
                    }))
                    logger.info(
                        f"✅ First message streaming complete | "
                        f"Chunks: {chunk_count} | "
                        f"First chunk: {first_chunk_time:.3f}s | "
                        f"Total: {total_time:.3f}s"
                    )

            # Signal ready for user input
            channel.send(json.dumps({
                "type": "ready_to_listen",
                "data": "Your turn - speak now"
            }))

        except Exception as e:
            # FAIL LOUDLY - no silent fallbacks
            error_msg = f"First message streaming failed: {str(e)}"
            logger.error(f"❌ CRITICAL: {error_msg}", exc_info=True)

            # Send error to frontend so user sees it
            try:
                channel.send(json.dumps({
                    "type": "error",
                    "data": error_msg
                }))
            except:
                pass  # Channel might be dead

            raise  # Re-raise to fail loudly

    # Create FastRTC Stream with ReplyOnPause
    # This automatically handles:
    # - Voice activity detection (VAD)
    # - Automatic turn-taking
    # - Audio streaming and buffering
    # startup_fn streams first message via data channel when connection opens
    stream = Stream(
        handler=ReplyOnPause(
            agent,
            algo_options=algo_options,
            startup_fn=stream_first_message  # ← PROPER IMPLEMENTATION: Real-time streaming
        ),
        modality="audio",
        mode="send-receive",
        ui_args={
            "title": ui_title,
            "subtitle": ui_subtitle,
            "hide_title": False
        }
    )

    logger.info("✅ WebRTC stream created successfully")
    return stream


def setup_webrtc(
    app: FastAPI,
    assistant_id: str,
    mount_path: str = "/voice/webrtc",
    pause_threshold_ms: int = 1500,
    ui_title: str = "KasaAI Voice Assistant",
    ui_subtitle: str = "Speak naturally - I'll respond when you pause",
    on_transcription: Optional[Callable] = None,
    on_response: Optional[Callable] = None
) -> bool:
    """
    Setup WebRTC voice routes on a FastAPI application.

    This is the main entry point for adding WebRTC voice functionality
    to any KasaAI app.

    Args:
        app: FastAPI application instance
        assistant_id: ID of assistant to use for conversations
        mount_path: URL path to mount WebRTC endpoints (default "/voice/webrtc")
        pause_threshold_ms: Pause detection threshold (default 1500ms)
        ui_title: Title for the Gradio UI
        ui_subtitle: Subtitle for the Gradio UI
        on_transcription: Optional callback when transcription completes
        on_response: Optional callback when LLM responds

    Returns:
        True if setup successful, False otherwise

    Example:
        ```python
        from fastapi import FastAPI
        from apps.shared.integration.webrtc import setup_webrtc

        app = FastAPI()

        setup_webrtc(
            app=app,
            assistant_id="default-assistant",
            mount_path="/voice/webrtc"
        )
        ```

    Endpoints created:
        - GET {mount_path}/ - Gradio UI for testing
        - POST {mount_path}/offer - WebRTC SDP offer endpoint
        - GET {mount_path}/answer - WebRTC SDP answer endpoint
    """
    if not FASTRTC_AVAILABLE:
        logger.error("❌ Cannot setup WebRTC - fastrtc not installed")
        logger.error("💡 Install with: pip install 'fastrtc[vad,tts]'")
        return False

    logger.info(f"🚀 Setting up WebRTC voice routes at '{mount_path}'...")

    try:
        # Create WebRTC stream
        stream = create_webrtc_stream(
            assistant_id=assistant_id,
            pause_threshold_ms=pause_threshold_ms,
            ui_title=ui_title,
            ui_subtitle=ui_subtitle,
            on_transcription=on_transcription,
            on_response=on_response
        )

        if not stream:
            return False

        # Mount stream on FastAPI app
        stream.mount(app, path=mount_path)

        # First message is now handled via startup_fn in create_webrtc_stream()
        # NO HTTP endpoints - everything streams via data channel in real-time

        logger.info(f"✅ WebRTC routes mounted at '{mount_path}'")
        logger.info(f"📝 WebRTC UI: {mount_path}/")
        logger.info(f"📝 WebRTC offer endpoint: {mount_path}/offer (POST)")
        logger.info("🎉 WebRTC integration ready!")

        return True

    except Exception as e:
        logger.error(f"❌ Failed to setup WebRTC: {e}", exc_info=True)
        return False


def generate_test_phone(
    assistant_id: str,
    hf_token: str,
    pause_threshold_ms: int = 1500,
    sample_rate: int = 16000,
    ui_title: Optional[str] = None,
    ui_subtitle: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Generate a temporary test phone number for an assistant using FastRTC's .fastphone().

    This creates a free temporary phone number that users can call to test the assistant.
    Powered by HuggingFace. Perfect for demos and testing.

    Args:
        assistant_id: Assistant identifier
        hf_token: HuggingFace API token (from environment)
        pause_threshold_ms: Silence duration to trigger response (default: 1500ms)
        sample_rate: Audio sample rate (default: 16000 Hz)
        ui_title: Optional UI title
        ui_subtitle: Optional UI subtitle

    Returns:
        dict: {
            'number': '+1234567890',        # Phone number to call
            'country': 'US',                # Country code
            'expires_at': '2024-01-01...',  # ISO timestamp
            'success': True,
            'message': 'Phone number generated'
        } or None if failed

    Example:
        ```python
        phone_info = generate_test_phone(
            assistant_id="my-assistant",
            hf_token=os.getenv('HUGGINGFACE_TOKEN')
        )
        if phone_info:
            print(f"📞 Call: {phone_info['number']}")
        ```

    Note:
        - Numbers are temporary (expire after period)
        - Only for testing/demos, not production
        - Requires valid HuggingFace token
        - May have geographic limitations
    """
    if not FASTRTC_AVAILABLE:
        logger.error("❌ Cannot generate phone - fastrtc not installed")
        return None

    if not hf_token:
        logger.error("❌ HuggingFace token required for .fastphone()")
        return None

    try:
        logger.info(f"📞 Generating temporary phone number for assistant: {assistant_id}")

        # Create WebRTC stream
        stream = create_webrtc_stream(
            assistant_id=assistant_id,
            pause_threshold_ms=pause_threshold_ms,
            sample_rate=sample_rate,
            ui_title=ui_title or f"Test Phone - {assistant_id}",
            ui_subtitle=ui_subtitle or "Call the number below to test"
        )

        if not stream:
            return None

        # Generate phone number using FastRTC
        phone_info = stream.fastphone(hf_token=hf_token)

        result = {
            'number': phone_info.number,
            'country': phone_info.country,
            'expires_at': phone_info.expires_at,
            'success': True,
            'message': 'Temporary phone number generated successfully'
        }

        logger.info(f"✅ Phone generated: {phone_info.number} (expires: {phone_info.expires_at})")
        return result

    except Exception as e:
        logger.error(f"❌ Failed to generate phone number: {e}", exc_info=True)
        return {
            'success': False,
            'message': f'Failed to generate phone: {str(e)}'
        }


def launch_shareable_ui(
    assistant_id: str,
    pause_threshold_ms: int = 1500,
    sample_rate: int = 16000,
    ui_title: Optional[str] = None,
    ui_subtitle: Optional[str] = None,
    share: bool = True,
    server_port: int = 7860,
    server_name: str = "0.0.0.0"
) -> Optional[Dict[str, Any]]:
    """
    Launch a shareable Gradio UI for testing an assistant using FastRTC's .ui.launch().

    Creates a public shareable link (e.g., https://random-id.gradio.live) that can be
    shared with team members or clients for quick testing without deployment.

    Args:
        assistant_id: Assistant identifier
        pause_threshold_ms: Silence duration to trigger response (default: 1500ms)
        sample_rate: Audio sample rate (default: 16000 Hz)
        ui_title: Optional UI title
        ui_subtitle: Optional UI subtitle
        share: Create public shareable link (default: True)
        server_port: Port to run on (default: 7860)
        server_name: Server name (default: "0.0.0.0" for all interfaces)

    Returns:
        dict: {
            'url': 'https://random-id.gradio.live',  # Shareable URL
            'local_url': 'http://localhost:7860',     # Local URL
            'success': True,
            'message': 'UI launched successfully'
        } or None if failed

    Example:
        ```python
        ui_info = launch_shareable_ui(
            assistant_id="my-assistant",
            ui_title="Test My Assistant",
            share=True
        )
        if ui_info:
            print(f"🔗 Share this: {ui_info['url']}")
        ```

    Note:
        - Shareable links expire after 72 hours
        - Perfect for demos and quick testing
        - Runs in separate thread, doesn't block
        - Requires internet connection for sharing
    """
    if not FASTRTC_AVAILABLE:
        logger.error("❌ Cannot launch UI - fastrtc not installed")
        return None

    try:
        logger.info(f"🚀 Launching shareable UI for assistant: {assistant_id}")

        # Create WebRTC stream
        stream = create_webrtc_stream(
            assistant_id=assistant_id,
            pause_threshold_ms=pause_threshold_ms,
            sample_rate=sample_rate,
            ui_title=ui_title or f"Test {assistant_id}",
            ui_subtitle=ui_subtitle or "Click 'Start' to begin testing"
        )

        if not stream:
            return None

        # Launch UI (this creates shareable link)
        # Note: This runs in background, doesn't block
        app_info = stream.ui.launch(
            share=share,
            server_port=server_port,
            server_name=server_name,
            prevent_thread_lock=True  # Don't block the main thread
        )

        # Get URLs from the app
        local_url = f"http://localhost:{server_port}"
        share_url = app_info.share_url if share and hasattr(app_info, 'share_url') else None

        result = {
            'local_url': local_url,
            'url': share_url or local_url,
            'share_url': share_url,
            'success': True,
            'message': 'Shareable UI launched successfully'
        }

        logger.info(f"✅ UI launched!")
        logger.info(f"   Local:  {local_url}")
        if share_url:
            logger.info(f"   Share:  {share_url}")

        return result

    except Exception as e:
        logger.error(f"❌ Failed to launch UI: {e}", exc_info=True)
        return {
            'success': False,
            'message': f'Failed to launch UI: {str(e)}'
        }


# Export public API
__all__ = [
    'WebRTCVoiceAgent',
    'create_webrtc_stream',
    'setup_webrtc',
    'generate_test_phone',
    'launch_shareable_ui',
    'FASTRTC_AVAILABLE'
]
