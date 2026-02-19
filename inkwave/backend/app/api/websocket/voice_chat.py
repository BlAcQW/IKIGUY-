"""
WebSocket Voice Chat Handler for InkWave.

Real-time voice conversation with books using VoiceAgent approach:
- Server-side PCM VAD for hands-free conversation
- Conversation state machine for proper turn-taking
- Streaming TTS for low-latency audio playback
- RAG (book embeddings) for context retrieval
- LLM (Gemini 2.5 Flash) for response generation

Author: AI Labs Africa
Created: November 30, 2025
"""

import asyncio
import base64
import json
import logging
import os
import re
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Query
import httpx
import numpy as np


def clean_text_for_tts(text: str) -> str:
    """
    Clean markdown, HTML, and formatting from text for TTS.

    Removes:
    - Markdown headers (##, ###, etc.)
    - Bold/italic markers (**text**, *text*, __text__, _text_)
    - Links [text](url) -> text
    - HTML tags <a>, </a>, <br>, etc.
    - Code blocks and inline code
    - Bullet points and numbered lists formatting
    - Extra whitespace

    Args:
        text: Raw text with potential markdown/HTML

    Returns:
        Clean text suitable for TTS
    """
    if not text:
        return ""

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Remove markdown headers (## Header -> Header)
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)

    # Remove markdown links [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)

    # Remove markdown images ![alt](url)
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', text)

    # Remove bold/italic markers
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **bold**
    text = re.sub(r'\*([^*]+)\*', r'\1', text)      # *italic*
    text = re.sub(r'__([^_]+)__', r'\1', text)      # __bold__
    text = re.sub(r'_([^_]+)_', r'\1', text)        # _italic_

    # Remove code blocks
    text = re.sub(r'```[\s\S]*?```', '', text)      # ```code blocks```
    text = re.sub(r'`([^`]+)`', r'\1', text)        # `inline code`

    # Remove bullet points and numbered lists markers
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)

    # Remove horizontal rules
    text = re.sub(r'^[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)

    # Remove blockquotes
    text = re.sub(r'^\s*>\s*', '', text, flags=re.MULTILINE)

    # Clean up extra whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)  # Multiple newlines -> double
    text = re.sub(r'[ \t]+', ' ', text)      # Multiple spaces -> single
    text = text.strip()

    return text

# Add shared services to path
sys.path.insert(0, '/opt/kasaai/apps')

from app.core.database import get_db
from app.services.rag_service import get_rag_service
from app.services.embedding_service import get_embedding_service
from app.services.tts_service import TTSService
from apps.shared.voice import (
    ConversationStateMachine,
    ConversationState,
    PCMVADHandler,
    pcm_to_wav
)
from apps.shared.services.tts_provider_service import SynthesisRequest

logger = logging.getLogger(__name__)

router = APIRouter()


def is_websocket_open(websocket: WebSocket) -> bool:
    """
    Check if WebSocket connection is still open.

    Args:
        websocket: WebSocket connection to check

    Returns:
        True if connection is open, False otherwise
    """
    try:
        if hasattr(websocket, 'client_state'):
            from starlette.websockets import WebSocketState
            return websocket.client_state == WebSocketState.CONNECTED
        return True
    except Exception:
        return False


class VoiceChatSession:
    """
    Manages a single voice chat session for a book.

    Implements VoiceAgent approach with:
    - Server-side PCM VAD for hands-free conversation
    - Conversation state machine for turn-taking
    - Streaming TTS for low-latency response
    - RAG-based book Q&A
    """

    def __init__(
        self,
        websocket: WebSocket,
        book_id: str,
        user_id: str,
        voice_settings: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize voice chat session.

        Args:
            websocket: WebSocket connection
            book_id: Book ID to chat about
            user_id: User ID for billing
            voice_settings: TTS voice settings
        """
        self.websocket = websocket
        self.book_id = book_id
        self.user_id = user_id
        self.session_id = str(uuid.uuid4())[:8]

        # Voice settings (TTS provider, voice, speed, etc.)
        self.voice_settings = voice_settings or {
            "provider_id": "kokoro",
            "voice_id": "am_adam",
            "speed": 1.0,
            "language": "en"
        }

        # ASR settings - use Groq Whisper (fast and free tier available)
        # Fallback order: groq_whisper_large_v3_turbo > openai_whisper > faster_whisper_large
        self.asr_provider = "groq_whisper_large_v3_turbo"
        self.asr_model = "whisper-large-v3-turbo"

        # LLM settings (configurable via init message or book settings)
        self.llm_provider = "gemini"
        self.llm_model = "gemini-2.5-flash"
        self.system_prompt: Optional[str] = None
        self.temperature = 0.7

        # Audio settings
        self.sample_rate = 16000

        # State management (VoiceAgent approach)
        self.state_machine = ConversationStateMachine()
        self.pcm_vad_handler: Optional[PCMVADHandler] = None

        # Conversation history
        self.conversation_history = []

        # TTS service
        self.tts_service: Optional[TTSService] = None

        # TTS cancellation flag for barge-in (stop speaking)
        self._tts_cancelled = False
        self._is_speaking = False

        # TTS playback flag - suppresses VAD during TTS to prevent echo
        # This is a backend-side safety layer in addition to frontend mic muting
        self._tts_playback_active = False

        logger.info(
            f"[{self.session_id}] VoiceChatSession created for book: {book_id}"
        )

    async def initialize(self):
        """Initialize session resources."""
        # Initialize PCM VAD handler for server-side voice detection
        self.pcm_vad_handler = PCMVADHandler(
            session_id=self.session_id,
            threshold=0.5,
            min_silence_duration_ms=1500,
            max_utterance_duration_s=30
        )

        # Initialize TTS service
        self.tts_service = TTSService()
        await self.tts_service.initialize(
            provider=self.voice_settings.get("provider_id", "kokoro")
        )

        # Set up state machine callbacks
        async def on_state_change(old_state, new_state):
            """Notify frontend of state changes."""
            await self.send_message("conversation_state", {
                "old_state": old_state.value,
                "new_state": new_state.value,
                "can_record": self.state_machine.can_record()
            })

        async def on_interruption():
            """Handle user interruption."""
            self.state_machine.cancel_processing()
            await self.send_message("interrupted", "User interrupted")

        self.state_machine.on_state_change = on_state_change
        self.state_machine.on_interruption = on_interruption

        logger.info(f"[{self.session_id}] Session initialized with PCM VAD")

    async def send_message(self, msg_type: str, data: Any):
        """
        Send a typed message to the client.

        Args:
            msg_type: Message type
            data: Message data
        """
        try:
            if is_websocket_open(self.websocket):
                await self.websocket.send_json({
                    "type": msg_type,
                    "data": data
                })
        except Exception as e:
            logger.error(f"[{self.session_id}] Failed to send message: {e}")

    async def handle_init(self, data: Dict[str, Any]):
        """
        Handle initialization message from client.

        Args:
            data: Init data with settings
        """
        # Update voice settings if provided
        if "voice_settings" in data:
            vs = data["voice_settings"]
            self.voice_settings = {
                "provider_id": vs.get("provider_id", self.voice_settings["provider_id"]),
                "voice_id": vs.get("voice_id", self.voice_settings["voice_id"]),
                "speed": vs.get("speed", self.voice_settings["speed"]),
                "language": vs.get("language", self.voice_settings["language"])
            }

        # Update ASR settings if provided
        if "asr_settings" in data:
            asr = data["asr_settings"]
            self.asr_model = asr.get("model", self.asr_model)

        # Update LLM settings if provided
        if "llm_settings" in data:
            llm = data["llm_settings"]
            self.llm_provider = llm.get("provider", self.llm_provider)
            self.llm_model = llm.get("model", self.llm_model)
            self.system_prompt = llm.get("system_prompt", self.system_prompt)
            self.temperature = llm.get("temperature", self.temperature)

        # Enable hands-free mode if requested
        if "hands_free" in data:
            self.state_machine.hands_free_mode = data["hands_free"]

        await self.send_message("status", "Initialized")
        await self.send_message("conversation_state", self.state_machine.get_state_info())
        await self.send_message("ready_to_listen", "Tap microphone or start speaking")

        logger.info(
            f"[{self.session_id}] Initialized - "
            f"TTS: {self.voice_settings['provider_id']}/{self.voice_settings['voice_id']}, "
            f"ASR: {self.asr_provider}/{self.asr_model}, "
            f"LLM: {self.llm_provider}/{self.llm_model} (temp={self.temperature}), "
            f"Hands-free: {self.state_machine.hands_free_mode}"
        )

    async def handle_pcm_chunk(self, data: str, sample_rate: int = 16000):
        """
        Handle incoming PCM audio chunk with server-side VAD.

        Args:
            data: Base64-encoded PCM audio data
            sample_rate: Sample rate of the audio
        """
        if not self.pcm_vad_handler:
            logger.error(f"[{self.session_id}] PCM VAD handler not initialized")
            return

        # Suppress VAD during TTS playback to prevent echo feedback
        # This is a backend safety layer - frontend should also mute mic during TTS
        if self._tts_playback_active or self._is_speaking:
            logger.debug(
                f"[{self.session_id}] Ignoring audio during TTS playback "
                f"(tts_active={self._tts_playback_active}, is_speaking={self._is_speaking})"
            )
            return

        # Check if recording is allowed by state machine
        if not self.state_machine.can_record():
            logger.warning(f"[{self.session_id}] Audio received while not allowed")
            await self.send_message("stop_recording", "Cannot record now")
            return

        # Start listening if not already
        if not self.pcm_vad_handler.vad_session.is_listening:
            self.pcm_vad_handler.start_listening()
            self.state_machine.start_listening()

        # Process PCM chunk with VAD
        is_speech, utterance_complete, complete_audio = (
            self.pcm_vad_handler.process_pcm_base64(data)
        )

        # Send VAD events to frontend
        # Note: Only check vad.is_speaking if VAD is enabled (SimplePCMAccumulator has no .vad)
        if is_speech:
            should_notify = True
            if self.pcm_vad_handler.vad_enabled:
                # Check if speech just started (VAD mode)
                should_notify = not self.pcm_vad_handler.vad_session.vad.is_speaking
            if should_notify:
                await self.send_message("vad_speech_start", "Speech detected")
                self.state_machine.handle_vad_speech_detected()

        if utterance_complete and complete_audio is not None:
            logger.info(
                f"[{self.session_id}] Utterance complete: "
                f"{len(complete_audio)} samples ({len(complete_audio)/16000:.2f}s)"
            )

            await self.send_message(
                "vad_utterance_complete",
                "Processing your question..."
            )

            # Stop listening while processing
            self.pcm_vad_handler.stop_listening()
            self.state_machine.stop_listening()

            # Process the complete utterance
            await self._process_utterance(complete_audio)

    async def _process_utterance(self, audio: np.ndarray):
        """
        Process a complete utterance: transcribe -> RAG -> TTS.

        Args:
            audio: PCM audio samples
        """
        try:
            # Convert PCM to WAV for transcription
            wav_bytes = pcm_to_wav(audio, sample_rate=16000)

            # Step 1: Transcribe
            await self.send_message("status", "Transcribing...")
            transcription = await self._transcribe_audio(wav_bytes)

            if not transcription or len(transcription.strip()) < 2:
                await self.send_message("error", "Could not understand audio")
                await self._resume_listening("I didn't catch that - please speak again")
                return

            # Send transcription to client
            await self.send_message("transcription", {
                "text": transcription,
                "is_final": True
            })

            logger.info(f"[{self.session_id}] Transcription: {transcription[:100]}...")

            # Step 2: Get RAG response
            await self.send_message("status", "Thinking...")
            request_id = str(uuid.uuid4())
            self.state_machine.start_processing(request_id)

            response_text = await self._get_rag_response(transcription)

            if not response_text:
                await self.send_message("error", "Failed to generate response")
                await self._resume_listening("Sorry, please try again")
                return

            # Send text response
            await self.send_message("text_response", response_text)
            logger.info(f"[{self.session_id}] Response: {response_text[:100]}...")

            # Step 3: Generate and stream TTS audio
            logger.info(f"[{self.session_id}] Starting TTS generation...")
            self.state_machine.start_speaking()
            await self.send_message("status", "Speaking...")

            try:
                audio_duration = await self._stream_tts_audio(response_text)
                logger.info(f"[{self.session_id}] TTS completed, duration: {audio_duration}")
            except Exception as tts_error:
                logger.error(f"[{self.session_id}] TTS ERROR: {tts_error}", exc_info=True)
                audio_duration = 0.0

            # Signal completion
            await self.send_message("audio_complete", {
                "duration": audio_duration,
                "text_length": len(response_text)
            })

            # Update conversation history
            self.conversation_history.append({
                "role": "user",
                "content": transcription
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": response_text
            })

            # Mark speaking complete
            self.state_machine.stop_speaking()

            # Hands-free mode: auto-resume listening
            if self.state_machine.should_auto_resume_listening():
                # Wait for audio to finish playing
                if audio_duration:
                    await asyncio.sleep(audio_duration + 0.3)
                else:
                    await asyncio.sleep(1.0)

                await self._resume_listening("Your turn - I'm listening")

        except Exception as e:
            logger.error(f"[{self.session_id}] Processing failed: {e}", exc_info=True)
            await self.send_message("error", f"Processing failed: {str(e)[:100]}")
            await self._resume_listening("Sorry, an error occurred")

    async def _resume_listening(self, message: str):
        """
        Resume listening for next utterance.

        Args:
            message: Message to display
        """
        self.pcm_vad_handler.start_listening()
        self.state_machine.start_listening()
        await self.send_message("ready_to_listen", message)
        await self.send_message("start_recording", "Listening...")

    async def handle_text(self, text: str):
        """
        Handle text input (typed question).

        Args:
            text: User's text question
        """
        if not self.state_machine.can_record():
            return

        await self.send_message("status", "Thinking...")

        try:
            # Generate unique request ID
            request_id = str(uuid.uuid4())
            self.state_machine.start_processing(request_id)

            # Get RAG response
            response_text = await self._get_rag_response(text)

            if not response_text:
                await self.send_message("error", "Failed to generate response")
                return

            # Send text response
            await self.send_message("text_response", response_text)

            # Generate and stream TTS audio
            self.state_machine.start_speaking()
            await self.send_message("status", "Speaking...")
            audio_duration = await self._stream_tts_audio(response_text)

            await self.send_message("audio_complete", {
                "duration": audio_duration,
                "text_length": len(response_text)
            })

            # Update history
            self.conversation_history.append({"role": "user", "content": text})
            self.conversation_history.append({
                "role": "assistant",
                "content": response_text
            })

            self.state_machine.stop_speaking()
            await self.send_message("ready_to_listen", "Type or speak")

        except Exception as e:
            logger.error(f"[{self.session_id}] Text processing failed: {e}")
            await self.send_message("error", str(e)[:100])

    async def handle_stop_recording(self):
        """Handle manual stop recording request."""
        if self.pcm_vad_handler and self.pcm_vad_handler.vad_session.is_listening:
            # Force complete and process
            complete_audio = self.pcm_vad_handler.stop_listening()

            if complete_audio is not None and len(complete_audio) > 1000:
                await self._process_utterance(complete_audio)
            else:
                await self.send_message("error", "Recording too short")
                await self._resume_listening("Please speak longer")

    async def handle_barge_in(self):
        """
        Handle user interruption - stop current TTS playback and resume listening.

        This allows the user to interrupt the AI while it's speaking to ask
        a follow-up question or correct themselves.
        """
        logger.info(f"[{self.session_id}] Barge-in received, is_speaking={self._is_speaking}")

        # Set cancellation flag to stop any in-progress TTS
        self._tts_cancelled = True
        self._is_speaking = False
        self._tts_playback_active = False  # Re-enable VAD for barge-in

        # Notify frontend to stop audio playback immediately
        await self.send_message("stop_audio", "Interrupted")

        # Update state machine
        self.state_machine.cancel_processing()
        self.state_machine.stop_speaking()

        # Acknowledge barge-in
        await self.send_message("barge_in_ack", "Stopped speaking")

        # Resume listening for next input
        await self._resume_listening("I'm listening - go ahead")

    async def _transcribe_audio(self, wav_bytes: bytes) -> Optional[str]:
        """
        Transcribe audio using ASR service.

        Args:
            wav_bytes: WAV audio bytes

        Returns:
            Transcribed text or None
        """
        try:
            asr_url = os.getenv(
                "ASR_SERVICE_URL",
                "http://localhost:30033/api/asr/transcribe/upload"
            )

            async with httpx.AsyncClient(timeout=30.0) as client:
                files = {"file": ("audio.wav", wav_bytes, "audio/wav")}
                data = {
                    "provider_id": self.asr_provider,
                    "language": "en",
                    "task": "transcribe",
                    "timestamps": "false"
                }

                response = await client.post(asr_url, files=files, data=data)

                if response.status_code == 200:
                    result = response.json()
                    return result.get("text", "")
                else:
                    logger.error(
                        f"[{self.session_id}] ASR failed: {response.status_code}"
                    )
                    return None

        except Exception as e:
            logger.error(f"[{self.session_id}] Transcription error: {e}")
            return None

    async def _get_rag_response(self, question: str) -> Optional[str]:
        """
        Get RAG-based response for the question.

        Args:
            question: User's question

        Returns:
            Response text or None
        """
        try:
            logger.warning(f"[WS RAG] Calling RAG service for book {self.book_id}, question: {question[:100]}")
            rag_service = await get_rag_service()
            logger.warning(f"[WS RAG] RAG service initialized")

            # Get streaming response and accumulate
            response_text = ""
            logger.warning(f"[WS RAG] Starting RAG stream query...")
            async for chunk in rag_service.query_book_stream(
                book_id=self.book_id,
                question=question,
                context_chunks=None,
                user_profile={"user_id": self.user_id},
                llm_provider=self.llm_provider,
                llm_model=self.llm_model,
                system_prompt=self.system_prompt,
                temperature=self.temperature
            ):
                response_text += chunk
                logger.warning(f"[WS RAG] Received chunk: {len(chunk)} chars")

            logger.warning(f"[WS RAG] Complete response: {len(response_text)} chars")
            return response_text or "I couldn't find relevant information in the book."

        except Exception as e:
            logger.error(f"[{self.session_id}] RAG query failed: {e}", exc_info=True)
            return None

    async def _stream_tts_audio(self, text: str) -> float:
        """
        Generate TTS audio and stream chunks to client.

        Args:
            text: Text to convert to speech

        Returns:
            Audio duration in seconds
        """
        chunk_count = 0
        audio_duration = 0.0

        # Reset cancellation flag and set playback active
        self._tts_cancelled = False
        self._is_speaking = True
        self._tts_playback_active = True  # Suppress VAD during TTS

        # Clean markdown/HTML from text before TTS
        clean_text = clean_text_for_tts(text)
        if not clean_text:
            logger.warning(f"[{self.session_id}] No text to speak after cleaning")
            self._is_speaking = False
            return 0.0

        logger.info(
            f"[{self.session_id}] TTS text cleaned: "
            f"{len(text)} chars -> {len(clean_text)} chars"
        )

        try:
            # Check if cancelled before starting
            if self._tts_cancelled:
                logger.info(f"[{self.session_id}] TTS cancelled before start")
                self._is_speaking = False
                return 0.0

            if not self.tts_service:
                self.tts_service = TTSService()
                await self.tts_service.initialize(
                    provider=self.voice_settings.get("provider_id", "kokoro")
                )

            provider_id = self.voice_settings.get("provider_id", "kokoro")

            # Ensure provider health check has run before first synthesis
            # This fixes race condition where background health check hasn't completed
            if self.tts_service.tts_provider.health_monitor:
                provider = self.tts_service.tts_provider.registry.get_provider(
                    provider_id
                )
                if provider and provider.status.value != "online":
                    logger.info(
                        f"[{self.session_id}] Running quick health check for "
                        f"{provider_id} (current status: {provider.status})"
                    )
                    check_result = await self.tts_service.tts_provider.health_monitor.check_provider_health(
                        provider
                    )
                    # Update provider status from check result
                    if check_result:
                        provider.status = check_result.status
                        logger.info(
                            f"[{self.session_id}] Health check result: "
                            f"{check_result.status.value}, healthy={check_result.healthy}"
                        )

            # Check cancellation again before TTS request
            if self._tts_cancelled:
                logger.info(f"[{self.session_id}] TTS cancelled before synthesis")
                self._is_speaking = False
                return 0.0

            # Create synthesis request with cleaned text
            request = SynthesisRequest(
                text=clean_text,
                provider_id=provider_id,
                voice_id=self.voice_settings.get("voice_id", "am_adam"),
                speed=self.voice_settings.get("speed", 1.0),
                language=self.voice_settings.get("language", "en"),
                output_format="wav"
            )

            # Synthesize audio
            result = await self.tts_service.tts_provider.synthesize(
                user_id=self.user_id or "anonymous",
                request=request,
                skip_billing=True
            )

            if result and result.audio_base64:
                # Check cancellation before sending
                if self._tts_cancelled:
                    logger.info(f"[{self.session_id}] TTS cancelled before sending")
                    self._is_speaking = False
                    return 0.0

                # Send complete audio as single chunk
                # Reason: WAV files cannot be split into arbitrary chunks as each chunk
                # needs a valid WAV header to be playable by the browser
                audio_duration = result.duration if hasattr(result, 'duration') else 0

                if is_websocket_open(self.websocket):
                    await self.send_message("audio_chunk", result.audio_base64)
                    chunk_count = 1

                logger.info(
                    f"[{self.session_id}] Sent TTS audio chunk, "
                    f"duration: {audio_duration:.2f}s, "
                    f"size: {len(result.audio_base64)} bytes"
                )
            else:
                logger.error(f"[{self.session_id}] TTS returned no audio")

        except Exception as e:
            logger.error(f"[{self.session_id}] TTS streaming failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self._is_speaking = False
            self._tts_playback_active = False  # Re-enable VAD after TTS

        return audio_duration

    def cleanup(self):
        """Cleanup session resources."""
        if self.pcm_vad_handler:
            self.pcm_vad_handler.cleanup()
        logger.info(f"[{self.session_id}] Session cleaned up")


# Active sessions
active_sessions: Dict[str, VoiceChatSession] = {}


@router.websocket("/voice-chat/{book_id}")
async def voice_chat_websocket(
    websocket: WebSocket,
    book_id: str,
    token: str = Query(None)
):
    """
    WebSocket endpoint for real-time voice chat with a book.

    Implements VoiceAgent approach with:
    - Server-side PCM VAD (hands-free conversation)
    - Conversation state machine
    - Streaming TTS

    Protocol:
    - Client sends: init, pcm_chunk, stop_recording, text, barge_in
    - Server sends: status, transcription, text_response, audio_chunk,
                    audio_complete, error, ready_to_listen, start_recording,
                    vad_speech_start, vad_utterance_complete, conversation_state

    Args:
        websocket: WebSocket connection
        book_id: Book ID to chat about
        token: Authentication token
    """
    await websocket.accept()

    # Validate token and get user ID
    user_id = "anonymous"
    if token:
        try:
            from app.core.auth import verify_token
            user_data = await verify_token(token)
            user_id = user_data.get("sub", "anonymous")
        except Exception as e:
            logger.warning(f"Token validation failed: {e}")

    # Create session
    session = VoiceChatSession(
        websocket=websocket,
        book_id=book_id,
        user_id=user_id
    )

    try:
        # Initialize session
        await session.initialize()
        active_sessions[session.session_id] = session

        logger.info(
            f"[{session.session_id}] Voice chat connected for "
            f"book: {book_id}, user: {user_id}"
        )

        # Send initial status
        await session.send_message("status", "Connected")
        await session.send_message(
            "conversation_state",
            session.state_machine.get_state_info()
        )

        # Message loop
        while True:
            try:
                message = await websocket.receive_json()
                msg_type = message.get("type", "")
                data = message.get("data")

                logger.debug(f"[{session.session_id}] Received: {msg_type}")

                if msg_type == "init":
                    await session.handle_init(data or {})

                elif msg_type == "pcm_chunk":
                    sample_rate = message.get("sample_rate", 16000)
                    await session.handle_pcm_chunk(data, sample_rate)

                elif msg_type == "stop_recording":
                    await session.handle_stop_recording()

                elif msg_type == "text":
                    await session.handle_text(data)

                elif msg_type == "barge_in":
                    await session.handle_barge_in()

                elif msg_type == "stop":
                    # Explicit stop button - same as barge_in
                    await session.handle_barge_in()

                elif msg_type == "ping":
                    await session.send_message("pong", data)

                else:
                    logger.warning(
                        f"[{session.session_id}] Unknown message type: {msg_type}"
                    )

            except json.JSONDecodeError:
                logger.warning(f"[{session.session_id}] Invalid JSON received")
                await session.send_message("error", "Invalid message format")

    except WebSocketDisconnect:
        logger.info(f"[{session.session_id}] Client disconnected")

    except Exception as e:
        logger.error(
            f"[{session.session_id}] WebSocket error: {e}",
            exc_info=True
        )

    finally:
        # Cleanup
        session.cleanup()
        if session.session_id in active_sessions:
            del active_sessions[session.session_id]
        logger.info(f"[{session.session_id}] Session cleaned up")
