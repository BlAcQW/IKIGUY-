"""
VoiceAgent WebSocket Handler for StudyFlow.

Real-time voice tutoring with VoiceAgent approach:
- Server-side PCM VAD for hands-free conversation
- Conversation state machine for proper turn-taking
- Streaming TTS for low-latency audio playback
- RAG integration for material-aware tutoring
- LLM (Gemini) for response generation

Author: AI Labs Africa
"""

import asyncio
import base64
import json
import logging
import os
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Query
import httpx
import numpy as np

# Add shared services to path
sys.path.insert(0, '/opt/kasaai/apps')

from apps.shared.voice import (
    ConversationStateMachine,
    ConversationState,
    PCMVADHandler,
    pcm_to_wav
)
from apps.shared.services.tts_provider_service import (
    TTSProviderService,
    SynthesisRequest
)
from apps.shared.services.voice_settings_service import VoiceSettingsService

from app.core.auth import SupabaseAuth
from app.core.database import mongodb, MongoDB
from app.services.user_service import UserService
from app.services.voice_tutoring_service import VoiceTutoringService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice-agent", tags=["Voice Agent"])


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


class VoiceAgentSession:
    """
    Manages a single VoiceAgent session for tutoring.

    Implements VoiceAgent approach with:
    - Server-side PCM VAD for hands-free conversation
    - Conversation state machine for turn-taking
    - Streaming TTS for low-latency response
    - RAG-based tutoring with material context
    """

    def __init__(
        self,
        websocket: WebSocket,
        session_id: str,
        user_id: str,
        organization_id: str,
        material_id: Optional[str] = None,
        voice_settings: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize voice agent session.

        Args:
            websocket: WebSocket connection
            session_id: Study session ID (for tutoring context)
            user_id: User ID for billing and settings
            organization_id: Organization ID for RAG scoping
            material_id: Optional material ID for context
            voice_settings: TTS voice settings override
        """
        self.websocket = websocket
        self.study_session_id = session_id
        self.user_id = user_id
        self.organization_id = organization_id
        self.material_id = material_id
        self.ws_session_id = str(uuid.uuid4())[:8]

        # Default voice settings (will be overridden by user settings)
        self.voice_settings = voice_settings or {
            "provider_id": "kokoro",
            "voice_id": "am_adam",
            "speed": 1.0,
            "language": "en"
        }

        # ASR settings
        self.asr_provider = "faster_whisper"
        self.asr_model = "medium"

        # LLM settings
        self.llm_model = "gemini-2.5-flash"

        # Audio settings
        self.sample_rate = 16000

        # State management (VoiceAgent approach)
        self.state_machine = ConversationStateMachine()
        self.pcm_vad_handler: Optional[PCMVADHandler] = None

        # Conversation history
        self.conversation_history = []

        # TTS service
        self.tts_provider: Optional[TTSProviderService] = None

        logger.info(
            f"[{self.ws_session_id}] VoiceAgentSession created for "
            f"session: {session_id}, material: {material_id}"
        )

    async def initialize(self):
        """Initialize session resources (fast path - defers heavy operations)."""
        # Load user voice settings
        await self._load_user_voice_settings()

        # Initialize PCM VAD handler for server-side voice detection
        self.pcm_vad_handler = PCMVADHandler(
            session_id=self.ws_session_id,
            threshold=0.5,
            min_silence_duration_ms=1500,
            max_utterance_duration_s=30
        )

        # TTS provider is initialized lazily on first use to avoid blocking
        # the WebSocket connection during health checks
        self.tts_provider = None

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

        logger.info(f"[{self.ws_session_id}] Session initialized with PCM VAD")

    async def _load_user_voice_settings(self):
        """Load user's voice settings from database."""
        try:
            user_settings = await VoiceTutoringService.get_user_voice_settings(
                self.user_id,
                self.organization_id
            )
            if user_settings:
                # Update TTS settings
                if user_settings.tts:
                    tts = user_settings.tts
                    self.voice_settings = {
                        "provider_id": tts.default_provider or "kokoro",
                        "voice_id": tts.default_voice or "am_adam",
                        "speed": tts.speed or 1.0,
                        "language": "en"
                    }
                # Update ASR settings
                if user_settings.asr:
                    asr = user_settings.asr
                    self.asr_provider = asr.default_provider or "faster_whisper"
                    # Note: model selection may depend on provider
                logger.info(
                    f"[{self.ws_session_id}] Loaded user voice settings: "
                    f"TTS={self.voice_settings['provider_id']}/{self.voice_settings['voice_id']}"
                )
        except Exception as e:
            logger.warning(f"[{self.ws_session_id}] Failed to load voice settings: {e}")

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
            logger.error(f"[{self.ws_session_id}] Failed to send message: {e}")

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
            self.llm_model = llm.get("model", self.llm_model)

        # Enable hands-free mode if requested
        if "hands_free" in data:
            self.state_machine.hands_free_mode = data["hands_free"]

        # Update material ID if provided
        if "material_id" in data:
            self.material_id = data["material_id"]

        await self.send_message("status", "Initialized")
        await self.send_message("conversation_state", self.state_machine.get_state_info())
        await self.send_message("ready_to_listen", "Tap microphone or start speaking")

        logger.info(
            f"[{self.ws_session_id}] Initialized - "
            f"TTS: {self.voice_settings['provider_id']}/{self.voice_settings['voice_id']}, "
            f"ASR: {self.asr_provider}/{self.asr_model}, "
            f"LLM: {self.llm_model}, "
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
            logger.error(f"[{self.ws_session_id}] PCM VAD handler not initialized")
            return

        # Check if recording is allowed
        if not self.state_machine.can_record():
            logger.warning(f"[{self.ws_session_id}] Audio received while not allowed")
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
        # Note: SimplePCMAccumulator doesn't have vad attribute
        if is_speech and hasattr(self.pcm_vad_handler.vad_session, 'vad'):
            if not self.pcm_vad_handler.vad_session.vad.is_speaking:
                await self.send_message("vad_speech_start", "Speech detected")
                self.state_machine.handle_vad_speech_detected()
        elif is_speech:
            # Fallback mode without full VAD
            await self.send_message("vad_speech_start", "Recording...")

        if utterance_complete and complete_audio is not None:
            logger.info(
                f"[{self.ws_session_id}] Utterance complete: "
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

            logger.info(f"[{self.ws_session_id}] Transcription: {transcription[:100]}...")

            # Step 2: Get tutoring response
            await self.send_message("status", "Thinking...")
            request_id = str(uuid.uuid4())
            self.state_machine.start_processing(request_id)

            response_text = await self._get_tutoring_response(transcription)

            if not response_text:
                await self.send_message("error", "Failed to generate response")
                await self._resume_listening("Sorry, please try again")
                return

            # Send text response
            await self.send_message("text_response", response_text)
            logger.info(f"[{self.ws_session_id}] Response: {response_text[:100]}...")

            # Step 3: Generate and stream TTS audio
            self.state_machine.start_speaking()
            await self.send_message("status", "Speaking...")

            audio_duration = await self._stream_tts_audio(response_text)

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
            logger.error(f"[{self.ws_session_id}] Processing failed: {e}", exc_info=True)
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

            # Get tutoring response
            response_text = await self._get_tutoring_response(text)

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
            logger.error(f"[{self.ws_session_id}] Text processing failed: {e}")
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
        """Handle user interruption - stop current TTS playback."""
        logger.info(f"[{self.ws_session_id}] Barge-in received")
        self.state_machine.start_listening()
        await self.send_message("barge_in_ack", "Stopped speaking")

    async def _transcribe_audio(self, wav_bytes: bytes) -> Optional[str]:
        """
        Transcribe audio using ASR service.

        Args:
            wav_bytes: WAV audio bytes

        Returns:
            Transcribed text or None
        """
        try:
            # Use StudyFlow's ASR endpoint
            asr_url = os.getenv(
                "ASR_SERVICE_URL",
                "http://localhost:30031/api/asr/transcribe"
            )

            async with httpx.AsyncClient(timeout=30.0) as client:
                files = {"file": ("audio.wav", wav_bytes, "audio/wav")}
                data = {
                    "provider": self.asr_provider,
                    "model": self.asr_model,
                    "language": "en"
                }

                response = await client.post(asr_url, files=files, data=data)

                if response.status_code == 200:
                    result = response.json()
                    return result.get("text", "")
                else:
                    logger.error(
                        f"[{self.ws_session_id}] ASR failed: {response.status_code}"
                    )
                    return None

        except Exception as e:
            logger.error(f"[{self.ws_session_id}] Transcription error: {e}")
            return None

    async def _get_tutoring_response(self, question: str) -> Optional[str]:
        """
        Get tutoring response using VoiceTutoringService.

        Args:
            question: User's question

        Returns:
            Response text or None
        """
        try:
            # Use the shared ConversationalVoiceService through VoiceTutoringService
            voice_service = VoiceTutoringService.get_voice_service()

            # Build conversation history for context
            history = self.conversation_history[-10:]  # Last 5 exchanges

            # Get response using RAG
            response = await voice_service.get_rag_response(
                question=question,
                organization_id=self.organization_id,
                rag_filters={"material_id": self.material_id} if self.material_id else None,
                conversation_history=history,
                system_prompt=self._build_system_prompt()
            )

            return response or "I'm not sure how to help with that. Could you rephrase your question?"

        except Exception as e:
            logger.error(f"[{self.ws_session_id}] Tutoring response failed: {e}")
            return None

    def _build_system_prompt(self) -> str:
        """Build system prompt for tutoring context."""
        return """You are a helpful AI tutor for StudyFlow. Your role is to:
1. Answer questions about the study material clearly and concisely
2. Explain concepts in an easy-to-understand way
3. Provide examples when helpful
4. Encourage the student and keep responses positive
5. Keep responses brief (2-3 sentences) for voice interaction

Always be encouraging and supportive. If you don't know something, say so honestly."""

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

        try:
            if not self.tts_provider:
                self.tts_provider = TTSProviderService()
                await self.tts_provider.initialize()

            provider_id = self.voice_settings.get("provider_id", "kokoro")

            # Ensure provider health check has run
            if self.tts_provider.health_monitor:
                provider = self.tts_provider.registry.get_provider(provider_id)
                if provider and provider.status.value != "online":
                    logger.info(
                        f"[{self.ws_session_id}] Running quick health check for "
                        f"{provider_id} (current status: {provider.status})"
                    )
                    check_result = await self.tts_provider.health_monitor.check_provider_health(
                        provider
                    )
                    if check_result:
                        provider.status = check_result.status

            # Create synthesis request
            request = SynthesisRequest(
                text=text,
                provider_id=provider_id,
                voice_id=self.voice_settings.get("voice_id", "am_adam"),
                speed=self.voice_settings.get("speed", 1.0),
                language=self.voice_settings.get("language", "en"),
                output_format="wav"
            )

            # Synthesize audio
            result = await self.tts_provider.synthesize(
                user_id=self.user_id or "anonymous",
                request=request,
                skip_billing=True
            )

            if result and result.audio_base64:
                # Decode base64 to bytes
                audio_data = base64.b64decode(result.audio_base64)
                audio_duration = result.duration if hasattr(result, 'duration') else 0
                chunk_size = 4096

                # Stream in chunks for smooth playback
                for i in range(0, len(audio_data), chunk_size):
                    chunk = audio_data[i:i + chunk_size]
                    chunk_b64 = base64.b64encode(chunk).decode('utf-8')

                    if is_websocket_open(self.websocket):
                        await self.send_message("audio_chunk", chunk_b64)
                        chunk_count += 1
                        await asyncio.sleep(0.01)
                    else:
                        break

                logger.info(
                    f"[{self.ws_session_id}] Streamed {chunk_count} TTS chunks, "
                    f"duration: {audio_duration:.2f}s"
                )
            else:
                logger.error(f"[{self.ws_session_id}] TTS returned no audio")

        except Exception as e:
            logger.error(f"[{self.ws_session_id}] TTS streaming failed: {e}")
            import traceback
            traceback.print_exc()

        return audio_duration

    def cleanup(self):
        """Cleanup session resources."""
        if self.pcm_vad_handler:
            self.pcm_vad_handler.cleanup()
        logger.info(f"[{self.ws_session_id}] Session cleaned up")


# Active sessions
active_sessions: Dict[str, VoiceAgentSession] = {}


@router.websocket("/ws/{session_id}")
async def voice_agent_websocket(
    websocket: WebSocket,
    session_id: str,
    token: str = Query(None),
    material_id: str = Query(None)
):
    """
    WebSocket endpoint for real-time voice agent tutoring.

    Implements VoiceAgent approach with:
    - Server-side PCM VAD (hands-free conversation)
    - Conversation state machine
    - Streaming TTS

    Protocol:
    - Client sends: init, pcm_chunk, stop_recording, text, barge_in, ping
    - Server sends: status, transcription, text_response, audio_chunk,
                    audio_complete, error, ready_to_listen, start_recording,
                    vad_speech_start, vad_utterance_complete, conversation_state,
                    interrupted, barge_in_ack, pong

    Args:
        websocket: WebSocket connection
        session_id: Study session ID for tutoring context
        token: JWT authentication token
        material_id: Optional material ID for context
    """
    await websocket.accept()

    # Authenticate using JWT token
    user_id = "anonymous"
    organization_id = "default"

    if token:
        try:
            supabase_auth = SupabaseAuth()
            token_payload = supabase_auth.verify_token(token)
            supabase_user_id = token_payload.get("sub")

            if supabase_user_id:
                user = await UserService.get_user_by_supabase_id(supabase_user_id)
                if user:
                    user_id = user.id
                    organization_id = user.organization_id
                    logger.info(
                        f"WebSocket authenticated: user={user_id}, org={organization_id}"
                    )
        except Exception as e:
            logger.warning(f"Token validation failed: {e}")

    # Create session
    session = VoiceAgentSession(
        websocket=websocket,
        session_id=session_id,
        user_id=user_id,
        organization_id=organization_id,
        material_id=material_id
    )

    try:
        # Send immediate acknowledgment to prevent frontend timeout
        await session.send_message("status", "Connected")

        logger.info(
            f"[{session.ws_session_id}] Voice agent connected for "
            f"session: {session_id}, user: {user_id}"
        )

        # Initialize session (now fast since TTS is lazy)
        await session.initialize()
        active_sessions[session.ws_session_id] = session

        # Send ready status after initialization
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

                logger.debug(f"[{session.ws_session_id}] Received: {msg_type}")

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

                elif msg_type == "ping":
                    await session.send_message("pong", data)

                else:
                    logger.warning(
                        f"[{session.ws_session_id}] Unknown message type: {msg_type}"
                    )

            except json.JSONDecodeError:
                logger.warning(f"[{session.ws_session_id}] Invalid JSON received")
                await session.send_message("error", "Invalid message format")

    except WebSocketDisconnect:
        logger.info(f"[{session.ws_session_id}] Client disconnected")

    except Exception as e:
        logger.error(
            f"[{session.ws_session_id}] WebSocket error: {e}",
            exc_info=True
        )

    finally:
        # Cleanup
        session.cleanup()
        if session.ws_session_id in active_sessions:
            del active_sessions[session.ws_session_id]
        logger.info(f"[{session.ws_session_id}] Session cleaned up")
