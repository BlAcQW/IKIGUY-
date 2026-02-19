"""
WebSocket endpoints for real-time voice chat with streaming audio.
"""

import asyncio
import json
import logging
import base64
import numpy as np
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
import wave
import io

from ...services.assistant_service import assistant_service
from ...services.meta_mms_service import MetaMMSService
from ...services.unified_whisper_service import UnifiedWhisperService
from ...services.unified_asr_service import get_unified_asr_service, ASRModel
from ...services.gemini_service import get_gemini_service
# MIGRATED: Using comprehensive TTS Provider Service instead of unified_tts_service
from apps.shared.services.tts_provider_service import (
    TTSProviderService,
    SynthesisRequest,
    SynthesisResult
)
# NOTE: tts_provider_service is accessed at runtime to avoid circular import
from ...services.unified_llm_service import unified_llm_service
from ...services.conversation_state_machine import ConversationStateMachine, ConversationState
from ...services.pcm_vad_handler import PCMVADHandler, pcm_to_wav

# 🚀 HuggingFace-inspired Streaming TTS (Phase 1: 40-60% latency reduction)
from apps.shared.integration.ai_services import get_streaming_tts_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])

# Active WebSocket connections
active_connections: Dict[str, WebSocket] = {}

# Initialize services - Use local models by default for reliability
mms_service = MetaMMSService()
whisper_service = UnifiedWhisperService(use_faster_whisper=True)  # Use local Faster Whisper
gemini_service = get_gemini_service()  # Use Gemini 2.5 for LLM
# MIGRATED: unified_tts_service replaced by tts_provider_service (initialized in main.py)

# Provider ID mapping: Map assistant.tts_provider → comprehensive service provider_id
# Reason: Assistant configs use old naming conventions, this maps them to provider registry IDs
PROVIDER_ID_MAPPING = {
    # Meta MMS variants
    "meta_mms": "melotts",  # Default mapping
    "meta_tts_aka": "coqui_xtts",  # Akan → Coqui XTTS
    "akan_mms": "coqui_xtts",
    "akan-mms": "coqui_xtts",

    # XTTS variants
    "xtts-twi-v1": "coqui_xtts",
    "xtts_twi_v1": "coqui_xtts",
    "xtts": "coqui_xtts",

    # Direct mappings (already use registry naming)
    "melotts": "melotts",
    "melo": "melotts",
    "openvoice": "openvoice",
    "open-voice": "openvoice",
    "styletts2": "styletts2",
    "style-tts2": "styletts2",
    "f5tts": "f5tts",
    "f5-tts": "f5tts",
    "f5": "f5tts",
    "kokoro": "kokoro",
    "kokoro-82m": "kokoro",
    "coqui": "coqui_xtts",
    "coqui-tts": "coqui_xtts",
    "coqui_xtts": "coqui_xtts",  # Already correct
}


def get_provider_id(tts_provider: str) -> str:
    """
    Map assistant TTS provider to comprehensive service provider_id.

    Args:
        tts_provider: Provider string from assistant config

    Returns:
        Provider ID for comprehensive TTS service (defaults to melotts)
    """
    return PROVIDER_ID_MAPPING.get(tts_provider.lower(), "melotts")


def is_websocket_open(websocket: WebSocket) -> bool:
    """
    Check if WebSocket connection is still open.

    Args:
        websocket: WebSocket connection to check

    Returns:
        True if connection is open, False otherwise
    """
    try:
        # Check if WebSocket has client_state attribute (Starlette WebSocket)
        if hasattr(websocket, 'client_state'):
            from starlette.websockets import WebSocketState
            return websocket.client_state == WebSocketState.CONNECTED
        # Fallback: assume open if no state attribute
        return True
    except Exception:
        return False


class AudioChunk(BaseModel):
    """Audio chunk for streaming."""
    audio: str  # Base64 encoded audio
    sample_rate: int = 16000
    format: str = "wav"


class TranscriptionResult(BaseModel):
    """Transcription result."""
    text: str
    confidence: float
    language: str
    is_final: bool = False


def detect_response_language(text: str) -> str:
    """
    Detect the language of a text response.

    Uses simple heuristics to detect Twi/Akan vs English:
    - Checks for Twi-specific characters (ɛ, ɔ, Ɛ, Ɔ)
    - Checks for common Twi words
    - Calculates ratio of Twi words

    Args:
        text: Text to analyze

    Returns:
        Language code: "tw" for Twi/Akan, "en" for English, "mixed" for mixed
    """
    # Twi-specific characters
    twi_chars = set("ɛɔƐƆ")

    # Common Twi words (expanded list for better detection)
    twi_words = set([
        # Basic words
        "ne", "na", "no", "deɛ", "sɛ", "wɔ", "yɛ", "me", "wo", "ɔ",
        # Greetings and common phrases
        "maakye", "maaha", "mema", "medaase", "aane", "dabi", "ɛyɛ",
        # Verbs and actions
        "kɔ", "ba", "di", "to", "nom", "ka", "gye", "kyerɛ",
        # Pronouns and articles
        "m", "w", "ɔno", "yɛn", "mo", "wɔn",
        # Question words
        "ɛdeɛn", "hwan", "ɛhe", "ɛberɛ"
    ])

    text_lower = text.lower()
    words = text_lower.split()

    # Check for Twi characters
    has_twi_chars = any(char in text for char in twi_chars)

    # Check for Twi words
    twi_word_count = sum(1 for word in words if word in twi_words)
    twi_ratio = twi_word_count / len(words) if words else 0

    logger.debug(f"🔍 Language detection - Twi chars: {has_twi_chars}, Twi ratio: {twi_ratio:.2f}")

    # Decision logic
    if has_twi_chars or twi_ratio > 0.3:
        return "tw"
    elif twi_ratio > 0.1:
        return "mixed"  # Treat mixed as Twi for safety
    else:
        return "en"


async def handle_first_message(
    websocket: WebSocket,
    assistant: Optional[Any],
    state_machine: Optional[ConversationStateMachine] = None,
    user_id: str = "anonymous"
):
    """
    Handle first message based on assistant configuration.

    Modes:
    - "assistant_speaks_first": Use predefined first_message with TTS
    - "assistant_waits": Skip first message, wait for user input
    - "assistant_speaks_first_with_model_message": Generate greeting with LLM, then TTS

    Args:
        websocket: WebSocket connection
        assistant: Assistant configuration object
        state_machine: Conversation state machine for state management
        user_id: User ID for billing tracking
    """
    if not assistant:
        logger.warning("⚠️ No assistant provided to handle_first_message")
        return

    # Get first message mode (default to "assistant_speaks_first" for backward compatibility)
    mode = getattr(assistant, 'first_message_mode', 'assistant_speaks_first')

    logger.info(f"🎬 First message mode: {mode}")

    if mode == "assistant_waits":
        logger.info("🤫 Assistant waiting for user to speak first")
        # Send ready indicator
        await websocket.send_json({
            "type": "ready_to_listen",
            "data": "Your turn - speak now"
        })
        # Ensure state machine is in listening state
        if state_machine:
            state_machine.start_listening()
        return

    elif mode == "assistant_speaks_first":
        first_message = getattr(assistant, 'first_message', '')
        if not first_message:
            logger.warning("⚠️ first_message_mode is 'assistant_speaks_first' but first_message is empty")
            # Fall back to waiting
            await websocket.send_json({
                "type": "ready_to_listen",
                "data": "Your turn - speak now"
            })
            if state_machine:
                state_machine.start_listening()
            return

        logger.info(f"👋 Sending predefined first message: '{first_message[:50]}...'")

        # Send text response to UI
        await websocket.send_json({
            "type": "text_response",
            "data": first_message
        })

        # Mark as speaking
        if state_machine:
            state_machine.start_speaking()

        try:
            # Generate and stream TTS
            audio_duration = await stream_tts_audio(
                websocket,
                first_message,
                assistant.tts_provider,
                assistant.tts_model,
                assistant.tts_voice,
                assistant.language,
                assistant,
                user_id=user_id
            )

            logger.info(f"✅ First message TTS completed: {audio_duration}s")
        except Exception as e:
            # FAIL LOUDLY - no silent fallbacks
            error_msg = f"First message TTS failed: {str(e)}"
            logger.error(f"❌ CRITICAL: {error_msg}", exc_info=True)

            # Send error to frontend so user sees it (if websocket still open)
            if is_websocket_open(websocket):
                await websocket.send_json({
                    "type": "error",
                    "data": error_msg
                })

            # Mark as done speaking
            if state_machine:
                state_machine.stop_speaking()
                state_machine.start_listening()

            # Re-raise to fail loudly
            raise
        else:
            # Only send success messages if no exception occurred
            # Mark as done speaking
            if state_machine:
                state_machine.stop_speaking()
                state_machine.start_listening()

            # Send ready indicator for user's turn
            if is_websocket_open(websocket):
                await websocket.send_json({
                    "type": "ready_to_listen",
                    "data": "Your turn - speak now"
                })

    elif mode == "assistant_speaks_first_with_model_message":
        logger.info("🤖 Generating first message with LLM...")

        # Build prompt for greeting generation
        system_prompt = getattr(assistant, 'system_prompt', '')
        first_message_guidance = getattr(assistant, 'first_message', '')

        if first_message_guidance:
            # User provided guidance for the greeting
            greeting_prompt = first_message_guidance
        else:
            # Use default greeting prompt
            greeting_prompt = "Generate a brief, friendly greeting message. Introduce yourself and ask how you can help."

        try:
            # Generate greeting using LLM
            llm_provider = getattr(assistant, 'llm_provider', 'gemini')
            llm_model = getattr(assistant, 'llm_model', 'gemini-2.0-flash-exp')

            # Call unified LLM service
            greeting_response = await unified_llm_service.generate_response(
                prompt=greeting_prompt,
                system_prompt=system_prompt if system_prompt else "You are a helpful AI assistant.",
                provider=llm_provider,
                model=llm_model
            )

            greeting = greeting_response.get('content', 'Hello! How can I help you today?')

            logger.info(f"👋 Generated greeting: '{greeting[:50]}...'")

            # Send text response to UI
            await websocket.send_json({
                "type": "text_response",
                "data": greeting
            })

            # Mark as speaking
            if state_machine:
                state_machine.start_speaking()

            try:
                # Generate and stream TTS
                audio_duration = await stream_tts_audio(
                    websocket,
                    greeting,
                    assistant.tts_provider,
                    assistant.tts_model,
                    assistant.tts_voice,
                    assistant.language,
                    assistant,
                    user_id=user_id
                )

                logger.info(f"✅ Model-generated first message TTS completed: {audio_duration}s")
            except Exception as e:
                # FAIL LOUDLY - no silent fallbacks
                error_msg = f"Model-generated first message TTS failed: {str(e)}"
                logger.error(f"❌ CRITICAL: {error_msg}", exc_info=True)

                # Send error to frontend so user sees it (if websocket still open)
                if is_websocket_open(websocket):
                    await websocket.send_json({
                        "type": "error",
                        "data": error_msg
                    })

                # Mark as done speaking
                if state_machine:
                    state_machine.stop_speaking()
                    state_machine.start_listening()

                # Re-raise to fail loudly
                raise
            else:
                # Only send success messages if no exception occurred
                # Mark as done speaking
                if state_machine:
                    state_machine.stop_speaking()
                    state_machine.start_listening()

                # Send ready indicator for user's turn
                if is_websocket_open(websocket):
                    await websocket.send_json({
                        "type": "ready_to_listen",
                        "data": "Your turn - speak now"
                    })

        except Exception as e:
            # FAIL LOUDLY - no silent fallbacks
            error_msg = f"Failed to generate model-based first message: {str(e)}"
            logger.error(f"❌ CRITICAL: {error_msg}", exc_info=True)

            # Send error to frontend so user sees it
            await websocket.send_json({
                "type": "error",
                "data": error_msg
            })

            # Re-raise to fail loudly
            raise

    else:
        # FAIL LOUDLY - no silent fallbacks
        error_msg = f"Unknown first_message_mode: {mode}"
        logger.error(f"❌ CRITICAL: {error_msg}")

        # Send error to frontend so user sees it
        await websocket.send_json({
            "type": "error",
            "data": error_msg
        })

        # Raise exception to fail loudly
        raise ValueError(error_msg)


@router.websocket("/voice-chat/{assistant_id}")
async def voice_chat_websocket(websocket: WebSocket, assistant_id: str):
    """
    WebSocket endpoint for real-time voice chat with streaming audio.
    
    Protocol:
    - Client sends: 
        - {"type": "audio", "data": "base64_audio_chunk"}
        - {"type": "text", "data": "user_message"}
        - {"type": "config", "data": {...assistant_config...}}
    
    - Server sends:
        - {"type": "transcription", "data": {...transcription_result...}}
        - {"type": "text_response", "data": "assistant_response"}
        - {"type": "audio_chunk", "data": "base64_audio"}
        - {"type": "audio_complete", "data": {...metadata...}}
        - {"type": "error", "data": "error_message"}
    """
    
    connection_id = f"{assistant_id}_{id(websocket)}"
    
    try:
        await websocket.accept()
        active_connections[connection_id] = websocket
        
        logger.info(f"WebSocket connection established for assistant {assistant_id}")

        # Extract user_id from query params for billing
        # TODO: Implement proper JWT authentication for user_id extraction
        user_id = websocket.query_params.get("user_id", "anonymous")
        logger.info(f"User ID for billing: {user_id}")

        # Get assistant configuration
        assistant = assistant_service.get_assistant(assistant_id) if assistant_id != "test" else None

        # Initialize conversation state machine
        state_machine = ConversationStateMachine()

        # Set up state machine callbacks
        async def on_state_change(old_state, new_state):
            """Notify frontend of state changes."""
            await websocket.send_json({
                "type": "conversation_state",
                "data": {
                    "old_state": old_state.value,
                    "new_state": new_state.value,
                    "can_record": state_machine.can_record()
                }
            })

        async def on_interruption():
            """Handle user interruption of assistant."""
            # Cancel any pending TTS/LLM
            state_machine.cancel_processing()
            await websocket.send_json({
                "type": "interrupted",
                "data": "Assistant interrupted"
            })

        state_machine.on_state_change = on_state_change
        state_machine.on_interruption = on_interruption

        # Send initial greeting
        await websocket.send_json({
            "type": "status",
            "data": "Connected - Ready for hands-free conversation"
        })

        # Send state info
        await websocket.send_json({
            "type": "conversation_state",
            "data": state_machine.get_state_info()
        })

        # Handle first message based on assistant configuration
        await handle_first_message(
            websocket,
            assistant,
            state_machine,
            user_id
        )

        # Initialize audio buffer and conversation state
        audio_buffer = []
        silence_counter = [0]  # Use list to maintain state across function calls
        last_transcription = [""]  # Track last transcription to avoid duplicates

        # Initialize PCM VAD handler for server-side voice activity detection
        pcm_vad_handler = PCMVADHandler(
            session_id=connection_id,
            threshold=0.5,  # Speech probability threshold
            min_silence_duration_ms=1500,  # 1.5s silence to end utterance
            max_utterance_duration_s=30  # Max 30s utterance
        )
        logger.info(f"✅ PCM VAD handler initialized for session: {connection_id}")

        # Main message loop
        while True:
            try:
                # Receive message from client
                message = await websocket.receive_json()
                message_type = message.get("type")
                message_data = message.get("data")

                if message_type == "audio":
                    # Check if recording is allowed (prevent overlap with assistant speech)
                    if not state_machine.can_record():
                        logger.warning("⚠️ Audio received while assistant speaking - rejecting")
                        await websocket.send_json({
                            "type": "stop_recording",
                            "data": "Cannot record while assistant is speaking"
                        })
                        continue

                    # Mark as listening if not already
                    if state_machine.conversation_state != ConversationState.LISTENING:
                        state_machine.start_listening()

                    # Handle audio chunk with persistent state
                    await handle_audio_chunk(
                        websocket,
                        message_data,
                        audio_buffer,
                        assistant,
                        silence_counter,
                        last_transcription,
                        state_machine
                    )

                elif message_type == "pcm_chunk":
                    # NEW: Handle PCM chunk with server-side VAD
                    logger.debug(f"🎤 PCM chunk received")

                    # Start listening if not already
                    if not pcm_vad_handler.vad_session.is_listening:
                        pcm_vad_handler.start_listening()
                        state_machine.start_listening()

                    # Process PCM chunk with VAD
                    is_speech, utterance_complete, complete_audio = pcm_vad_handler.process_pcm_base64(message_data)

                    # Send VAD events to frontend
                    if is_speech and not pcm_vad_handler.vad_session.vad.is_speaking:
                        # Speech just started
                        await websocket.send_json({
                            "type": "vad_speech_start",
                            "data": "Speech detected"
                        })
                        state_machine.handle_vad_speech_detected()

                    if utterance_complete and complete_audio is not None:
                        # Utterance finished - transcribe
                        logger.info(f"🎯 Utterance complete: {len(complete_audio)} samples ({len(complete_audio)/16000:.2f}s)")

                        await websocket.send_json({
                            "type": "vad_utterance_complete",
                            "data": "Processing your message..."
                        })

                        # Stop listening while processing
                        pcm_vad_handler.stop_listening()
                        state_machine.stop_listening()

                        # Convert PCM to WAV for Whisper
                        try:
                            wav_bytes = pcm_to_wav(complete_audio, sample_rate=16000)

                            # Transcribe
                            transcription_result = await perform_stt(wav_bytes, assistant)
                            transcription_text = transcription_result.get("text", "")

                            if transcription_text and transcription_text != "No speech detected":
                                # Send transcription with full metadata
                                await websocket.send_json({
                                    "type": "transcription",
                                    "data": {
                                        "text": transcription_text,
                                        "confidence": transcription_result.get("confidence", 0.0),
                                        "language": transcription_result.get("language", "en"),
                                        "is_final": True
                                    }
                                })

                                # Detect language and generate response
                                detected_language = detect_language_from_text(transcription_text)
                                logger.info(f"🌍 Transcription language detected: {detected_language}")

                                # Generate and stream response
                                await generate_and_stream_response(
                                    websocket,
                                    transcription_text,
                                    assistant,
                                    detected_language=detected_language,
                                    state_machine=state_machine,
                                    user_id=user_id  # Pass user_id for TTS billing
                                )
                            else:
                                # No speech - resume listening
                                logger.info("No speech detected, resuming listening...")
                                pcm_vad_handler.start_listening()
                                state_machine.start_listening()
                                await websocket.send_json({
                                    "type": "ready_to_listen",
                                    "data": "I didn't catch that - please speak again"
                                })
                                await websocket.send_json({
                                    "type": "start_recording",
                                    "data": "Listening..."
                                })

                        except Exception as e:
                            logger.error(f"❌ Error processing PCM utterance: {e}")
                            # Resume listening on error
                            pcm_vad_handler.start_listening()
                            state_machine.start_listening()
                            await websocket.send_json({
                                "type": "error",
                                "data": f"Processing error: {str(e)}"
                            })
                            await websocket.send_json({
                                "type": "start_recording",
                                "data": "Listening..."
                            })

                elif message_type == "text":
                    # Handle text message
                    await handle_text_message(
                        websocket,
                        message_data,
                        assistant
                    )
                    
                elif message_type == "config":
                    # Update assistant configuration
                    assistant = await handle_config_update(
                        websocket,
                        message_data,
                        assistant_id
                    )
                    
                elif message_type == "end_audio":
                    # Process complete audio buffer
                    logger.info(f"⏹️  end_audio received - buffer has {len(audio_buffer)} chunks")
                    if audio_buffer:
                        await process_complete_audio(
                            websocket,
                            audio_buffer,
                            assistant,
                            state_machine=state_machine
                        )
                        audio_buffer.clear()
                        silence_counter[0] = 0
                        last_transcription[0] = ""
                        logger.info("✅ Audio processed and state reset for next recording")

                elif message_type == "barge_in":
                    # User interrupted - acknowledge and stop any ongoing TTS
                    logger.info("🎤 Barge-in detected - user interrupting")
                    await websocket.send_json({
                        "type": "barge_in_ack",
                        "data": "Barge-in acknowledged, stopped speaking"
                    })
                    # Clear audio buffer to stop processing current audio
                    audio_buffer.clear()
                    silence_counter[0] = 0

                elif message_type == "ping":
                    # Respond to ping
                    await websocket.send_json({
                        "type": "pong",
                        "data": message_data
                    })
                    
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received: {e}")
                await websocket.send_json({
                    "type": "error",
                    "data": "Invalid JSON format"
                })
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await websocket.send_json({
                    "type": "error",
                    "data": str(e)
                })
                
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        
    finally:
        # Clean up connection
        if connection_id in active_connections:
            del active_connections[connection_id]

        # Clean up PCM VAD handler
        try:
            pcm_vad_handler.cleanup()
        except Exception as e:
            logger.error(f"❌ Error cleaning up PCM VAD handler: {e}")

        logger.info(f"WebSocket connection closed for assistant {assistant_id}")


async def handle_audio_chunk(
    websocket: WebSocket,
    audio_data: str,
    audio_buffer: List[bytes],
    assistant: Optional[Any],
    silence_counter: Optional[List[int]] = None,
    last_transcription: Optional[List[str]] = None,
    state_machine: Optional[ConversationStateMachine] = None
):
    """Handle incoming audio chunk for real-time transcription."""

    # Initialize state lists if not provided
    if silence_counter is None:
        silence_counter = [0]
    if last_transcription is None:
        last_transcription = [""]

    try:
        # Decode base64 audio
        audio_bytes = base64.b64decode(audio_data)
        audio_buffer.append(audio_bytes)

        # Check for silence (simple energy-based detection)
        import numpy as np

        # Ensure buffer size is a multiple of 2 (for int16)
        # Truncate any odd bytes to avoid alignment issues
        if len(audio_bytes) % 2 != 0:
            logger.warning(f"⚠️ Audio chunk size {len(audio_bytes)} not aligned to int16, truncating 1 byte")
            audio_bytes = audio_bytes[:-1]

        if len(audio_bytes) > 0:
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
            energy = np.sqrt(np.mean(audio_array.astype(np.float32) ** 2))
        else:
            energy = 0  # Empty buffer has no energy

        # Language-specific silence thresholds
        # Now using proper PCM/WAV audio from frontend, energy will be in normal range (500-5000)
        is_akan_language = assistant and hasattr(assistant, 'language') and assistant.language and assistant.language.lower() in ["tw", "twi", "akan", "asante", "akuapem", "fante"]

        silence_threshold = 500 if is_akan_language else 400  # Proper thresholds for PCM audio
        silence_chunks_needed = 2 if is_akan_language else 2  # Require 2 seconds of silence for reliability

        # Log energy levels for debugging VAD
        logger.info(f"🎚️  Audio energy: {energy:.1f} | Threshold: {silence_threshold} | Silence count: {silence_counter[0]}/{silence_chunks_needed} | Buffer size: {len(audio_buffer)}")

        # Smart silence detection - different thresholds for different utterance lengths
        if energy < silence_threshold:
            silence_counter[0] += 1
            logger.info(f"🔇 SILENCE detected! Count: {silence_counter[0]}/{silence_chunks_needed} needed | Buffer: {len(audio_buffer)} chunks")

            # SMART ENDPOINTING: Faster for short utterances, standard for longer ones
            # Short utterances (greetings, yes/no) - process after specified silence
            if len(audio_buffer) <= 3 and silence_counter[0] >= silence_chunks_needed:
                logger.info("🔇 Short utterance detected, processing immediately...")
                if state_machine:
                    state_machine.stop_listening()

                await websocket.send_json({
                    "type": "stop_recording",
                    "data": "Processing..."
                })

                await process_audio_buffer(websocket, audio_buffer, assistant, partial=False, state_machine=state_machine)
                audio_buffer.clear()
                silence_counter[0] = 0
                last_transcription[0] = ""

            # Medium utterances - process after specified silence
            elif len(audio_buffer) > 3 and len(audio_buffer) <= 8 and silence_counter[0] >= silence_chunks_needed:
                logger.info("🔇 Medium utterance detected, processing...")
                if state_machine:
                    state_machine.stop_listening()

                await websocket.send_json({
                    "type": "stop_recording",
                    "data": "Processing..."
                })

                await process_audio_buffer(websocket, audio_buffer, assistant, partial=False, state_machine=state_machine)
                audio_buffer.clear()
                silence_counter[0] = 0
                last_transcription[0] = ""

            # Long utterances - process after specified silence, minimum 2 chunks
            elif len(audio_buffer) > 8 and silence_counter[0] >= silence_chunks_needed and len(audio_buffer) > 2:
                logger.info("🔇 Long utterance detected, processing...")
                if state_machine:
                    state_machine.stop_listening()

                await websocket.send_json({
                    "type": "stop_recording",
                    "data": "Processing..."
                })

                await process_audio_buffer(websocket, audio_buffer, assistant, partial=False, state_machine=state_machine)
                audio_buffer.clear()
                silence_counter[0] = 0
                last_transcription[0] = ""
        else:
            # Speech detected - reset silence counter
            if silence_counter[0] > 0:
                logger.info(f"🗣️  SPEECH detected (energy: {energy:.1f}), resetting silence counter from {silence_counter[0]} to 0")
            silence_counter[0] = 0  # Reset silence counter on speech
            # Notify VAD of speech activity
            if state_machine:
                state_machine.handle_vad_speech_detected()

        # Show partial transcriptions for better user feedback
        # Process at 3 chunks, then every 2 chunks after (3, 5, 7, 9...)
        buffer_len = len(audio_buffer)
        should_process = buffer_len == 3 or (buffer_len > 3 and buffer_len % 2 == 1)

        if should_process:
            logger.info(f"📝 Processing partial transcription ({buffer_len} chunks in buffer)")
            transcription_result = await process_audio_buffer(websocket, audio_buffer.copy(), assistant, partial=True)
            if transcription_result and transcription_result != last_transcription[0]:
                logger.info(f"📤 Sending partial transcription: '{transcription_result[:50]}...'")
                last_transcription[0] = transcription_result

    except Exception as e:
        logger.error(f"Error handling audio chunk: {e}")
        await websocket.send_json({
            "type": "error",
            "data": f"Audio processing error: {str(e)}"
        })


async def process_audio_buffer(
    websocket: WebSocket,
    audio_buffer: List[bytes],
    assistant: Optional[Any],
    partial: bool = True,
    state_machine: Optional[ConversationStateMachine] = None
):
    """Process accumulated audio buffer for transcription."""

    try:
        # Combine audio chunks
        combined_audio = b''.join(audio_buffer)

        # Check if we have enough audio data
        # Reduced minimum for short utterances like "hello", "hi", "yes", "no"
        min_audio_size = 8000  # ~0.25 seconds at 16kHz mono 16-bit = 8000 bytes (reduced from 16000)
        if len(combined_audio) < min_audio_size:
            logger.debug(f"Audio buffer too small ({len(combined_audio)} bytes), waiting for more data...")
            return None

        # For partial transcription, we can still process WebM chunks
        # Faster Whisper can handle incomplete audio files
        logger.info(f"🎤 Processing audio buffer: {len(combined_audio)} bytes, partial={partial}")

        # Perform STT with the combined audio bytes
        transcription = await perform_stt(combined_audio, assistant)

        # Only send transcription if we got actual text
        if transcription["text"]:
            # Send transcription result
            await websocket.send_json({
                "type": "transcription",
                "data": {
                    "text": transcription["text"],
                    "confidence": transcription["confidence"],
                    "language": transcription["language"],
                    "is_final": not partial
                }
            })

            # If final transcription, generate response
            if not partial:
                # Pass detected language and state machine to response generation
                await generate_and_stream_response(
                    websocket,
                    transcription["text"],
                    assistant,
                    detected_language=transcription["language"],  # Use detected language!
                    state_machine=state_machine,
                    user_id=user_id  # Pass user_id for TTS billing
                )
            return transcription["text"]
        else:
            # Send status update if no text detected
            if not partial:
                await websocket.send_json({
                    "type": "status",
                    "data": "No speech detected"
                })
            return None

    except Exception as e:
        logger.error(f"❌ Error processing audio buffer: {e}")
        await websocket.send_json({
            "type": "error",
            "data": f"Transcription error: {str(e)}"
        })
        return None


async def process_complete_audio(
    websocket: WebSocket,
    audio_buffer: List[bytes],
    assistant: Optional[Any],
    state_machine: Optional[ConversationStateMachine] = None
):
    """Process complete audio recording."""
    logger.info(f"🎯 process_complete_audio called with {len(audio_buffer)} chunks")
    await process_audio_buffer(websocket, audio_buffer, assistant, partial=False, state_machine=state_machine)


async def handle_text_message(
    websocket: WebSocket,
    text: str,
    assistant: Optional[Any]
):
    """Handle text message and generate response."""

    try:
        # Send acknowledgment
        await websocket.send_json({
            "type": "status",
            "data": "Processing message..."
        })

        # Detect language from text content using simple heuristics
        detected_language = detect_language_from_text(text)
        logger.info(f"🌍 Text language detected: {detected_language}")

        # Generate and stream response with detected language
        await generate_and_stream_response(
            websocket,
            text,
            assistant,
            detected_language=detected_language,
            user_id=user_id  # Pass user_id for TTS billing
        )

    except Exception as e:
        logger.error(f"Error handling text message: {e}")
        await websocket.send_json({
            "type": "error",
            "data": f"Message processing error: {str(e)}"
        })


async def generate_and_stream_response(
    websocket: WebSocket,
    user_text: str,
    assistant: Optional[Any],
    detected_language: Optional[str] = None,
    state_machine: Optional[ConversationStateMachine] = None,
    user_id: str = "anonymous"  # NEW: For billing in comprehensive TTS service
):
    """Generate LLM response and stream TTS audio.

    MIGRATED: Now passes user_id to TTS service for billing tracking.
    """

    try:
        # Generate unique request ID for greedy inference
        import uuid
        request_id = str(uuid.uuid4())

        # Notify state machine we're processing
        if state_machine:
            state_machine.start_processing(request_id)
        # Get assistant configuration
        if assistant:
            llm_provider = assistant.llm_provider
            llm_model = assistant.llm_model
            system_prompt = assistant.system_prompt
            tts_provider = assistant.tts_provider
            tts_model = getattr(assistant, 'tts_model', 'meta_mms')  # Get tts_model with fallback
            # Use detected language if available, otherwise fallback to assistant language
            language = detected_language or assistant.language

            # Auto-select appropriate TTS provider, model and voice based on detected language
            if detected_language:
                if detected_language.lower().startswith('en'):
                    # English detected - switch to English-capable TTS provider
                    tts_provider = "melotts"
                    tts_model = "melotts"
                    tts_voice = "EN-US"
                    logger.info(f"🔊 English detected - switching to MeloTTS (provider: {tts_provider}, voice: {tts_voice})")
                elif detected_language.lower() in ['tw', 'twi', 'akan']:
                    # Twi/Akan detected - use Twi-capable TTS provider
                    tts_provider = "meta_mms"
                    tts_model = "meta_mms"
                    tts_voice = assistant.tts_voice or "mms-tts-aka"
                    logger.info(f"🔊 Twi detected - using Meta MMS (provider: {tts_provider}, voice: {tts_voice})")
                else:
                    # Other language - use assistant's configured voice
                    tts_voice = assistant.tts_voice
            else:
                # No detected language - use assistant's configured voice
                tts_voice = assistant.tts_voice

            logger.info(f"🌍 Using language: {language} (detected: {detected_language}, assistant default: {assistant.language})")
        else:
            # Default configuration
            llm_provider = "openai"
            llm_model = "gpt-4o-mini"
            system_prompt = "You are a helpful assistant."
            tts_provider = "meta_mms"
            tts_model = "meta_mms"
            # Use detected language if available, otherwise default to English
            language = detected_language or "en"
            # Auto-select voice based on language
            if language.lower().startswith('en'):
                tts_voice = "EN-US"
            else:
                tts_voice = "mms-tts-aka"
            logger.info(f"🌍 Using language: {language} (detected: {detected_language})")

        # Enhance system prompt with language switching instructions
        # Use detected language to enforce response language
        # IMPORTANT: Prepend instruction to beginning for better LLM attention
        if detected_language and detected_language.lower() in ['en', 'english']:
            language_instruction = """<<< CRITICAL LANGUAGE RULE >>>
The user is speaking ENGLISH to you right now.
YOU MUST RESPOND ONLY IN ENGLISH.
DO NOT USE ANY Twi/Akan words or phrases in your response.
Use clear, simple English.

Only switch to Twi if the user explicitly requests it in their message.
<<< END CRITICAL RULE >>>

"""
        elif detected_language and detected_language.lower() in ['tw', 'twi', 'akan']:
            language_instruction = """<<< CRITICAL LANGUAGE RULE >>>
The user is speaking TWI/AKAN to you right now.
YOU MUST RESPOND ONLY IN TWI/AKAN with proper Twi characters (ɛ, ɔ).
DO NOT USE ENGLISH unless the user explicitly requests it in their message.

Only switch to English if the user explicitly requests it.
<<< END CRITICAL RULE >>>

"""
        else:
            # Fallback - multilingual mode
            language_instruction = """<<< LANGUAGE INSTRUCTION >>>
You are multilingual (English and Twi/Akan).
MATCH THE LANGUAGE the user is currently using:
- If they speak English → respond in English
- If they speak Twi → respond in Twi with proper characters (ɛ, ɔ)
Stay in that language until they explicitly ask you to switch.
<<< END INSTRUCTION >>>

"""
        # Prepend language instruction to system prompt for higher LLM attention
        system_prompt = language_instruction + system_prompt

        # Generate LLM response (mock for now)
        # In production, use actual LLM service
        assistant_response = await generate_llm_response(
            user_text,
            system_prompt,
            llm_provider,
            llm_model
        )

        # Detect language of response and validate against expected language
        response_language = detect_response_language(assistant_response)
        logger.info(f"🌐 Detected response language: {response_language} (expected: {language})")

        # Validate that LLM responded in the correct language
        # If user spoke English, we expect English response
        # If user spoke Twi, we expect Twi response
        if detected_language:
            expected_lang_category = "en" if detected_language.lower() in ['en', 'english'] else "tw"

            # Check if response matches expected language
            if expected_lang_category == "en" and response_language not in ["en", "english"]:
                logger.warning(f"⚠️ Language mismatch! User spoke English but LLM responded in {response_language}")
                logger.warning(f"⚠️ Response text: {assistant_response[:100]}")
                # Force English TTS regardless
                response_language = "en"
            elif expected_lang_category == "tw" and response_language in ["en", "english"]:
                logger.warning(f"⚠️ Language mismatch! User spoke Twi but LLM responded in {response_language}")
                logger.warning(f"⚠️ Response text: {assistant_response[:100]}")
                # Force Twi TTS regardless
                response_language = "tw"

        # Normalize detected language
        if response_language == "mixed":
            # For mixed language, prefer the user's input language
            if detected_language and detected_language.lower() in ['en', 'english']:
                response_language = "en"
                logger.info("🔀 Mixed language detected, using English TTS to match user input")
            else:
                response_language = "tw"
                logger.info("🔀 Mixed language detected, using Twi TTS to match user input")

        # Adjust TTS settings based on validated response language
        if response_language != language:
            logger.info(f"🔄 Adjusting TTS for detected response language: {language} → {response_language}")
            # Update language for TTS
            language = response_language

            # Adjust TTS model/voice for the detected language
            if response_language in ["tw", "twi", "akan"]:
                # Switch to Akan TTS
                if tts_model not in ["meta_mms", "akan_mms", "akan-mms"]:
                    logger.info("🔄 Switching TTS model to Akan MMS for Twi response")
                    tts_model = "akan_mms"
                    tts_voice = "mms-tts-aka"
            elif response_language == "en":
                # Switch to English TTS if currently using Akan
                if tts_model in ["meta_mms", "akan_mms", "akan-mms"]:
                    logger.info("🔄 Switching TTS model to MeloTTS for English response")
                    tts_model = "melotts"
                    tts_voice = "EN-US"

        # Send text response
        await websocket.send_json({
            "type": "text_response",
            "data": assistant_response
        })

        # Notify state machine assistant is speaking
        if state_machine:
            state_machine.start_speaking()

        # Signal that assistant is about to speak
        await websocket.send_json({
            "type": "assistant_speaking_start",
            "data": "Assistant is speaking"
        })

        # Check if speed control is needed (speed != 1.0)
        # If yes, use regular TTS service for accurate speed control
        # Otherwise, use Parler-TTS streaming for faster latency
        use_speed_control = assistant and hasattr(assistant, 'speed') and assistant.speed != 1.0

        if use_speed_control:
            logger.info(f"🎚️  Using regular TTS with speed control: {assistant.speed}x")
            # Use regular TTS service with speed control
            audio_duration = await stream_tts_audio(
                websocket,
                assistant_response,
                tts_provider,
                tts_model,
                tts_voice,
                language,
                assistant,
                user_id  # Pass user_id for billing
            )
        else:
            logger.info("🚀 Using Parler-TTS streaming for optimal latency")
            # 🚀 Generate TTS audio with Parler-TTS streaming (40-60% faster)
            audio_duration = await stream_tts_parler(
                websocket,
                assistant_response,
                assistant,
                voice_description=None  # Auto-extracted from assistant
            )

        # Notify state machine assistant finished
        if state_machine:
            state_machine.stop_speaking()

        # Signal that assistant finished speaking
        await websocket.send_json({
            "type": "assistant_speaking_end",
            "data": "Assistant finished speaking"
        })

        # Hands-free mode: Auto-resume listening with natural pause
        logger.info(f"🔍 Checking hands-free mode - state_machine: {state_machine is not None}, should_auto_resume: {state_machine.should_auto_resume_listening() if state_machine else False}")
        logger.info(f"🔍 DEBUG: About to check conditional - state_machine type: {type(state_machine)}, bool value: {bool(state_machine)}")

        # Store result to avoid multiple calls
        should_resume = state_machine.should_auto_resume_listening() if state_machine else False
        logger.info(f"🔍 DEBUG: Stored should_resume = {should_resume}")

        if state_machine and should_resume:
            logger.info("🎤 ✅ Hands-free mode ENABLED: Auto-resuming listening after assistant spoke")
            logger.info(f"🔍 DEBUG: Entered hands-free block, audio_duration = {audio_duration}")

            # Wait for audio to finish playing on frontend
            # Use actual audio duration + small buffer for network delay
            logger.info(f"🔍 DEBUG: Checking audio_duration: {audio_duration}")
            if audio_duration:
                pause_duration = audio_duration + 0.3  # Audio duration + 300ms buffer
                logger.info(f"⏱️  Pausing {pause_duration:.2f}s (audio: {audio_duration:.2f}s + 0.3s buffer) for playback to complete...")
            else:
                # Fallback if duration not available
                is_akan = assistant and hasattr(assistant, 'language') and assistant.language and assistant.language.lower() in ["tw", "twi", "akan", "asante", "akuapem", "fante"]
                pause_duration = 1.2 if is_akan else 1.0
                logger.info(f"⏱️  Pausing {pause_duration}s before resuming listening (fallback - no audio duration)...")

            logger.info(f"🔍 DEBUG: About to sleep for {pause_duration}s")
            await asyncio.sleep(pause_duration)
            logger.info("🔍 DEBUG: Sleep completed")

            # Send "ready to listen" signal with audio cue
            logger.info("📤 Sending 'ready_to_listen' message to frontend")
            await websocket.send_json({
                "type": "ready_to_listen",
                "data": "Your turn - I'm listening"
            })
            logger.info("🔍 DEBUG: ready_to_listen sent")

            # Now start listening (audio has finished, ready for next turn)
            logger.info("🎤 Calling state_machine.start_listening()...")
            state_machine.start_listening()
            logger.info("🔍 DEBUG: start_listening() completed")

            logger.info("📤 Sending 'start_recording' message to frontend to trigger auto-recording")
            await websocket.send_json({
                "type": "start_recording",
                "data": "Listening... (speak naturally)"
            })
            logger.info("✅ Hands-free mode: Messages sent, frontend should now auto-start recording")
        else:
            logger.info(f"⏭️  Hands-free mode skipped - Reason: state_machine={state_machine is not None}, should_auto_resume={state_machine.should_auto_resume_listening() if state_machine else False}")
        
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        await websocket.send_json({
            "type": "error",
            "data": f"Response generation error: {str(e)}"
        })


async def stream_tts_audio(
    websocket: WebSocket,
    text: str,
    tts_provider: str,
    tts_model: str,
    tts_voice: str,
    language: str,
    assistant=None,
    user_id: str = "anonymous"  # NEW: Required for billing in comprehensive service
):
    """Generate and stream TTS audio using Comprehensive TTS Provider Service.

    MIGRATED from unified_tts_service to comprehensive TTSProviderService.
    Now includes automatic billing, health monitoring, and provider failover.
    """

    try:
        logger.info(f"🔊 Generating TTS with {tts_provider}/{tts_model} (language: {language}, text: '{text[:50]}...')")

        # Map provider to comprehensive service provider_id
        provider_id = get_provider_id(tts_provider)
        logger.info(f"📢 Mapped provider: {tts_provider} → {provider_id}")

        # Map language codes
        language_map = {
            "twi": "tw",
            "tw": "tw",
            "multi": "tw",  # For multilingual, default to Twi
            "ga": "ga",
            "gaa": "ga",
            "ewe": "ewe",
            "ee": "ewe",
            "en": "en",
            "eng": "en",
            "hausa": "hau",
            "hau": "hau",
            "yoruba": "yor",
            "yor": "yor"
        }
        mapped_language = language_map.get(language.lower(), "en")

        # Get speed from assistant config (default: 1.0, range: 0.5-2.0)
        speed = getattr(assistant, 'speed', 1.0) if assistant else 1.0
        logger.info(f"🎚️  TTS speed: {speed} (from assistant config)")

        # Get TTS service from main module (avoid circular import)
        from ...main import tts_provider_service
        if not tts_provider_service:
            raise RuntimeError("TTS Provider Service not initialized. Check application startup.")

        # Create synthesis request for comprehensive service
        synthesis_request = SynthesisRequest(
            provider_id=provider_id,
            text=text,
            language=mapped_language,
            voice_id=tts_voice if tts_voice else None,
            speed=speed,
            output_format="wav"
        )

        # Synthesize with automatic billing and health checking
        # Note: skip_billing=True for now during testing phase
        result: SynthesisResult = await tts_provider_service.synthesize(
            user_id=user_id,
            request=synthesis_request,
            skip_billing=True  # TODO: Set to False after testing to enable billing
        )

        # Check WebSocket is still open before sending
        if not is_websocket_open(websocket):
            logger.warning("⚠️ WebSocket closed before sending audio")
            return

        # Send complete audio as single base64 chunk
        await websocket.send_json({
            "type": "audio_chunk",
            "data": result.audio_base64
        })

        logger.info(
            f"✅ TTS audio sent: {len(result.audio_base64)} bytes, "
            f"duration: {result.duration:.2f}s, cost: ${result.cost:.4f}, "
            f"tx_id: {result.transaction_id or 'N/A (skip_billing=True)'}"
        )

        # Send completion message with comprehensive metadata
        if is_websocket_open(websocket):
            await websocket.send_json({
                "type": "audio_complete",
                "data": {
                    "duration": result.duration,
                    "sample_rate": result.sample_rate,
                    "format": result.format,
                    "provider": result.provider_id,
                    "cost": result.cost,
                    "transaction_id": result.transaction_id,
                    "processing_time": result.processing_time
                }
            })

        # Return duration for hands-free timing
        return result.duration

    except Exception as e:
        logger.error(f"❌ Error streaming TTS audio: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Only send error if WebSocket is still open
        if is_websocket_open(websocket):
            try:
                await websocket.send_json({
                    "type": "error",
                    "data": f"TTS streaming error: {str(e)}"
                })
            except Exception as send_error:
                logger.error(f"Failed to send error message (WebSocket may be closed): {send_error}")


async def stream_tts_parler(
    websocket: WebSocket,
    text: str,
    assistant: Optional[Any] = None,
    voice_description: Optional[str] = None
) -> float:
    """
    🚀 NEW: Stream TTS audio using Parler-TTS for 40-60% latency reduction.

    Uses HuggingFace Parler-TTS with sentence-level streaming for immediate audio feedback.
    First audio chunk arrives in <1s vs 2-4s with blocking TTS.

    Args:
        websocket: WebSocket connection
        text: Text to synthesize
        assistant: Assistant configuration (optional)
        voice_description: Parler-TTS voice description (optional)

    Returns:
        Estimated total audio duration in seconds
    """
    try:
        logger.info(f"🎙️  Streaming TTS with Parler-TTS: '{text[:50]}...'")

        # Get voice description from assistant or use default
        if not voice_description:
            if assistant and hasattr(assistant, 'voice_description'):
                voice_description = assistant.voice_description
            else:
                # Default voice descriptions based on language/context
                voice_description = "A clear, friendly voice with natural intonation"

        logger.info(f"🎨 Voice description: {voice_description}")

        # Get streaming TTS service (singleton)
        streaming_tts = get_streaming_tts_service()

        # Get actual sample rate from TTS model
        actual_sample_rate = streaming_tts.get_native_sample_rate()
        logger.info(f"🎵 Using TTS native sample rate: {actual_sample_rate} Hz")

        # Track metrics
        import time
        start_time = time.time()
        chunk_count = 0
        total_samples = 0
        first_chunk_latency = None

        # Stream audio chunks
        async for audio_chunk in streaming_tts.stream_tts(
            text=text,
            voice_description=voice_description,
            sample_rate=16000  # Note: This param is ignored by the service, it returns native rate
        ):
            chunk_count += 1
            total_samples += len(audio_chunk)

            # Track first chunk latency
            if chunk_count == 1:
                first_chunk_latency = time.time() - start_time
                logger.info(f"⚡ First chunk delivered in {first_chunk_latency:.3f}s (vs 2-4s blocking)")

            # Check WebSocket is still open
            if not is_websocket_open(websocket):
                logger.warning("⚠️  WebSocket closed during streaming")
                break

            # Convert numpy array to base64
            try:
                # Ensure audio is in correct format
                if audio_chunk.dtype != np.float32:
                    audio_chunk = audio_chunk.astype(np.float32)

                # Normalize to [-1, 1] range if needed
                if audio_chunk.max() > 1.0:
                    audio_chunk = audio_chunk / 32768.0

                # Convert to WAV format with ACTUAL sample rate from model
                wav_bytes = pcm_to_wav(audio_chunk, sample_rate=actual_sample_rate)
                audio_base64 = base64.b64encode(wav_bytes).decode('utf-8')

                # Send audio chunk
                await websocket.send_json({
                    "type": "audio_chunk",
                    "data": audio_base64
                })

                logger.debug(f"📤 Chunk {chunk_count}: {len(audio_chunk)} samples ({len(wav_bytes)} bytes WAV)")

            except Exception as e:
                logger.error(f"❌ Error encoding audio chunk {chunk_count}: {e}")
                continue

        # Calculate total duration
        duration = total_samples / 16000.0

        # Send completion message
        if is_websocket_open(websocket):
            await websocket.send_json({
                "type": "audio_complete",
                "data": {
                    "duration": duration,
                    "sample_rate": 16000,
                    "format": "wav",
                    "model": "parler-tts",
                    "chunks": chunk_count,
                    "first_chunk_latency": first_chunk_latency,
                    "streaming": True
                }
            })

        total_time = time.time() - start_time
        logger.info(
            f"✅ Streaming TTS complete: {chunk_count} chunks, "
            f"{duration:.2f}s audio in {total_time:.2f}s wall time "
            f"(first chunk: {first_chunk_latency:.3f}s)"
        )

        return duration

    except Exception as e:
        logger.error(f"❌ Error in streaming TTS: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

        # Send error if WebSocket is still open
        if is_websocket_open(websocket):
            try:
                await websocket.send_json({
                    "type": "error",
                    "data": f"Streaming TTS error: {str(e)}"
                })
            except Exception as send_error:
                logger.error(f"Failed to send error: {send_error}")

        return 0.0


async def perform_stt(audio_data: bytes, assistant: Optional[Any], preferred_language: Optional[str] = None) -> Dict[str, Any]:
    """
    Perform speech-to-text using appropriate ASR model.
    Uses Akan Whisper for Twi, Faster Whisper for other languages.

    Args:
        audio_data: Raw audio bytes
        assistant: Assistant configuration
        preferred_language: Override language detection (e.g., from conversation context)
    """
    import tempfile
    import os
    import soundfile as sf
    import numpy as np

    try:
        # Determine audio format and file extension
        # Check for WebM/Opus magic bytes
        if audio_data[:4] == b'\x1aE\xdf\xa3':
            file_ext = '.webm'
        # Check for WAV magic bytes
        elif audio_data[:4] == b'RIFF':
            file_ext = '.wav'
        # Check for Ogg magic bytes
        elif audio_data[:4] == b'OggS':
            file_ext = '.ogg'
        else:
            # Default to webm for browser audio
            file_ext = '.webm'
            logger.warning(f"Unknown audio format, assuming WebM. First 4 bytes: {audio_data[:4]}")

        # Save audio to temporary file
        with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as tmp_file:
            tmp_file.write(audio_data)
            tmp_file_path = tmp_file.name

        # Convert WebM to WAV if needed (soundfile doesn't support WebM)
        if file_ext == '.webm':
            logger.info(f"🔄 Converting WebM to WAV for processing...")
            wav_path = tmp_file_path.replace('.webm', '.wav')
            try:
                import subprocess
                # Use ffmpeg to convert WebM to WAV
                result = subprocess.run(
                    ['ffmpeg', '-i', tmp_file_path, '-ar', '16000', '-ac', '1', '-y', wav_path],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    # Clean up original WebM file
                    os.unlink(tmp_file_path)
                    tmp_file_path = wav_path
                    logger.info(f"✅ Converted WebM to WAV successfully")
                else:
                    logger.error(f"❌ ffmpeg conversion failed: {result.stderr}")
                    # Fall back to treating as raw audio
                    logger.warning("⚠️ Falling back to raw audio interpretation")
            except FileNotFoundError:
                logger.error("❌ ffmpeg not found. Install with: apt-get install ffmpeg")
                # Fall back to treating as raw audio
            except subprocess.TimeoutExpired:
                logger.error("❌ ffmpeg conversion timeout")
            except Exception as conv_error:
                logger.error(f"❌ Conversion error: {conv_error}")

        try:
            # Determine language and model
            language = "tw"  # Default to Twi
            asr_model = ASRModel.AKAN_WHISPER  # Default to Akan Whisper

            # DYNAMIC STT SWITCHING: Check if preferred_language is provided (from conversation context)
            if preferred_language:
                lang_lower = preferred_language.lower()
                if lang_lower in ["tw", "twi", "akan", "asante", "akuapem", "fante"]:
                    language = "tw"
                    asr_model = ASRModel.AKAN_WHISPER
                    logger.info(f"🎤 Dynamic STT: Switching to Akan Whisper for detected Twi conversation")
                elif lang_lower in ["en", "english"]:
                    language = "auto"  # Let Whisper auto-detect English variants
                    asr_model = ASRModel.FASTER_WHISPER
                    logger.info(f"🎤 Dynamic STT: Switching to Faster Whisper for detected English conversation")
                else:
                    # Unknown language, use Faster Whisper as fallback
                    language = "auto"
                    asr_model = ASRModel.FASTER_WHISPER
                    logger.info(f"🎤 Dynamic STT: Using Faster Whisper for language: {preferred_language}")
            # Check if assistant has explicit stt_model selection (only if no preferred_language)
            elif assistant and hasattr(assistant, 'stt_model') and assistant.stt_model:
                stt_model_str = assistant.stt_model.lower()

                # Map stt_model string to ASRModel enum
                model_map = {
                    # Akan/Twi specific models
                    "akan-whisper": ASRModel.AKAN_WHISPER,
                    "akan_whisper": ASRModel.AKAN_WHISPER,
                    "giftmark-akan": ASRModel.AKAN_WHISPER,

                    # Faster Whisper (real-time)
                    "faster-whisper": ASRModel.FASTER_WHISPER,
                    "faster_whisper": ASRModel.FASTER_WHISPER,
                    "faster-whisper-medium": ASRModel.FASTER_WHISPER,
                    "faster_whisper_medium": ASRModel.FASTER_WHISPER,
                    "whisper-1": ASRModel.FASTER_WHISPER,

                    # Whisper Large v3 (high accuracy)
                    "whisper-large-v3": ASRModel.WHISPER_LARGE_V3,
                    "whisper_large_v3": ASRModel.WHISPER_LARGE_V3,
                    "whisper-large": ASRModel.WHISPER_LARGE_V3,
                    "large-v3": ASRModel.WHISPER_LARGE_V3,

                    # African Whisper (multi-dialect)
                    "african-whisper": ASRModel.AFRICAN_WHISPER,
                    "african_whisper": ASRModel.AFRICAN_WHISPER,

                    # Meta MMS
                    "mms-1b-all": ASRModel.META_MMS,
                    "mms-1b-aka": ASRModel.META_MMS,
                    "mms-1b-ewe": ASRModel.META_MMS,
                    "meta-mms": ASRModel.META_MMS,
                    "mms": ASRModel.META_MMS,

                    # Wav2Vec2
                    "wav2vec2-akan": ASRModel.WAV2VEC2_AKAN,
                    "wav2vec2_akan": ASRModel.WAV2VEC2_AKAN,

                    # Moshi (conversational)
                    "moshi": ASRModel.MOSHI,
                }

                if stt_model_str in model_map:
                    asr_model = model_map[stt_model_str]
                    logger.info(f"🎤 Using explicit STT model selection: {stt_model_str} → {asr_model.value}")

            # Determine language (use assistant language if available)
            if assistant and assistant.language:
                lang = assistant.language.lower()
                if lang in ["tw", "twi", "akan", "asante", "akuapem", "fante"]:
                    language = "tw"
                    # Only auto-select Akan Whisper if no explicit model was chosen
                    if not (assistant and hasattr(assistant, 'stt_model') and assistant.stt_model):
                        asr_model = ASRModel.AKAN_WHISPER
                        logger.info(f"🎤 Auto-selected Akan Whisper for Twi language")
                else:
                    # FIXED: Keep the actual language code for English and other languages
                    # Don't convert "en" to "auto" - this breaks language detection downstream
                    language = lang
                    # Only auto-select Faster Whisper if no explicit model was chosen
                    if not (assistant and hasattr(assistant, 'stt_model') and assistant.stt_model):
                        asr_model = ASRModel.FASTER_WHISPER
                        logger.info(f"🎤 Auto-selected Faster Whisper for {language} language")

            # Load audio file to numpy array for unified ASR service
            audio_array, sample_rate = sf.read(tmp_file_path)

            logger.info(f"🎤 Transcribing audio (language: {language}, model: {asr_model.value}, size: {len(audio_data)} bytes)")

            # Use unified ASR service
            asr_service = get_unified_asr_service()
            result = await asr_service.transcribe(
                audio_data=audio_array,
                sample_rate=sample_rate,
                model=asr_model,
                language=language,
                return_timestamps=False
            )

            logger.info(f"✅ Transcription complete: '{result.text[:50]}...' (confidence: {result.confidence:.2f}, detected language: {result.language})")

            # IMPORTANT: Return the actual detected language from STT, not the configured language
            # This ensures downstream language validation works correctly
            detected_lang = result.language if result.language else language

            return {
                "text": result.text,
                "confidence": result.confidence,
                "language": detected_lang  # Use detected language for accurate downstream processing
            }

        finally:
            # Clean up temp file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

    except Exception as e:
        logger.error(f"❌ STT error: {e}")
        return {
            "text": "",
            "confidence": 0.0,
            "language": "en"
        }


async def generate_llm_response(
    user_text: str,
    system_prompt: str,
    llm_provider: str,
    llm_model: str
) -> str:
    """
    Generate LLM response using multiple providers via unified service.
    Supports: Gemini, OpenAI, Anthropic, Ollama, and fallback providers.
    """

    try:
        # Normalize provider name
        llm_provider = llm_provider or "gemini"
        llm_provider = llm_provider.lower()

        logger.info(f"🤖 Generating response with {llm_provider}/{llm_model} for: '{user_text[:50]}...'")

        # Build messages array
        messages = [
            {"role": "user", "content": user_text}
        ]

        # Check if provider is supported by unified service
        if llm_provider in ["openai", "anthropic", "ollama", "gemini"]:
            try:
                # Use unified LLM service
                response = await unified_llm_service.chat_completion(
                    messages=messages,
                    provider=llm_provider,
                    model=llm_model,
                    temperature=0.7,
                    max_tokens=1000,
                    system_prompt=system_prompt
                )

                response_text = response["content"]
                logger.info(f"✅ {llm_provider} response generated: '{response_text[:50]}...'")
                return response_text

            except Exception as provider_error:
                logger.error(f"❌ {llm_provider} error: {provider_error}")

                # Fallback to Gemini if available
                if llm_provider != "gemini" and gemini_service.is_available():
                    logger.info(f"🔄 Falling back to Gemini due to {llm_provider} error")
                    full_prompt = f"{system_prompt}\n\nUser: {user_text}\nAssistant:"
                    result = await gemini_service.generate_content(
                        prompt=full_prompt,
                        temperature=0.7,
                        max_output_tokens=1000
                    )
                    return result["content"]
                else:
                    raise provider_error

        # Placeholder providers - use Gemini fallback
        elif llm_provider in ["ghananlp", "abena_ai", "meta_mms"]:
            logger.info(f"🔄 {llm_provider} not yet implemented, using Gemini fallback")

            if gemini_service.is_available():
                full_prompt = f"{system_prompt}\n\nUser: {user_text}\nAssistant:"
                result = await gemini_service.generate_content(
                    prompt=full_prompt,
                    temperature=0.7,
                    max_output_tokens=1000
                )
                return result["content"]
            else:
                return f"I received your message: '{user_text}'. However, {llm_provider} integration is pending and Gemini fallback is not available."

        # Unknown provider
        else:
            logger.warning(f"⚠️ Unknown provider '{llm_provider}', using Gemini")

            if gemini_service.is_available():
                full_prompt = f"{system_prompt}\n\nUser: {user_text}\nAssistant:"
                result = await gemini_service.generate_content(
                    prompt=full_prompt,
                    temperature=0.7,
                    max_output_tokens=1000
                )
                return result["content"]
            else:
                return f"I received your message: '{user_text}'. However, the LLM service is not configured."

    except Exception as e:
        logger.error(f"❌ LLM generation error: {e}")
        return f"I apologize, but I encountered an error processing your message. Please try again."


def detect_language_from_text(text: str) -> str:
    """
    Detect language from text using simple heuristics.
    Returns language code: 'en' for English, 'tw' for Twi, etc.
    """
    import re

    # Simple heuristic: check for common English words vs Twi words
    english_common_words = set(['the', 'is', 'are', 'was', 'were', 'have', 'has', 'had', 'do', 'does',
                                 'can', 'could', 'will', 'would', 'should', 'may', 'might', 'must',
                                 'hello', 'hi', 'how', 'what', 'where', 'when', 'who', 'why', 'which',
                                 'this', 'that', 'these', 'those', 'my', 'your', 'his', 'her', 'our',
                                 'please', 'thank', 'thanks', 'yes', 'no', 'ok', 'okay'])

    twi_common_words = set(['mepaakyɛw', 'me', 'wo', 'ɛ', 'ne', 'da', 'yɛ', 'na', 'no', 'asɛm', 'sɛ',
                            'yɛn', 'wɔn', 'mo', 'aka', 'yi', 'ho', 'mu', 'te', 'kɔ', 'ba', 'di',
                            'maakye', 'medaase', 'aane', 'daabi', 'ɔkyerɛ', 'te sɛn', 'sen'])

    # Normalize text to lowercase and split into words
    words = re.findall(r'\w+', text.lower())

    # Count matches
    english_count = sum(1 for word in words if word in english_common_words)
    twi_count = sum(1 for word in words if word in twi_common_words)

    # If mostly ASCII characters and has English words, likely English
    ascii_ratio = sum(1 for c in text if ord(c) < 128) / max(len(text), 1)

    if english_count > twi_count or (ascii_ratio > 0.9 and english_count > 0):
        return "en"
    elif twi_count > 0:
        return "tw"
    else:
        # Default to English if can't determine
        return "en"


async def handle_config_update(
    websocket: WebSocket,
    config_data: Dict[str, Any],
    assistant_id: str
) -> Optional[Any]:
    """Handle configuration update from client."""
    
    try:
        # Update assistant configuration
        if assistant_id and assistant_id != "test":
            # Update existing assistant
            assistant = assistant_service.update_assistant(assistant_id, config_data)
        else:
            # Create temporary assistant config
            assistant = type('Assistant', (), config_data)()
        
        # Send confirmation
        await websocket.send_json({
            "type": "config_updated",
            "data": "Configuration updated successfully"
        })
        
        return assistant
        
    except Exception as e:
        logger.error(f"Error updating configuration: {e}")
        await websocket.send_json({
            "type": "error",
            "data": f"Configuration update error: {str(e)}"
        })
        return None


@router.websocket("/audio-stream/{session_id}")
async def audio_stream_websocket(websocket: WebSocket, session_id: str):
    """
    Simplified WebSocket endpoint for audio streaming only.
    Used for real-time audio playback.
    """
    
    try:
        await websocket.accept()
        logger.info(f"Audio stream WebSocket connected: {session_id}")
        
        while True:
            # Wait for audio generation requests
            message = await websocket.receive_json()
            
            if message.get("type") == "generate_audio":
                text = message.get("text", "")
                model = message.get("model", "meta_mms")
                voice = message.get("voice", "mms-tts-aka")
                language = message.get("language", "en")

                # 🚀 Generate and stream audio with Parler-TTS (40-60% faster)
                voice_desc = f"A clear, neutral voice speaking in {language}"
                await stream_tts_parler(
                    websocket,
                    text,
                    assistant=None,  # Direct generation without assistant
                    voice_description=voice_desc
                )
                
    except WebSocketDisconnect:
        logger.info(f"Audio stream WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"Audio stream error: {e}")