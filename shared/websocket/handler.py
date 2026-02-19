"""
Voice WebSocket Handler

Provides a reusable handler for voice conversation WebSocket endpoints.
Integrates with the conversation pipeline for ASR -> LLM -> TTS processing.

Author: KasaAI Team
Date: 2025-11-26
"""

import logging
import base64
import asyncio
import uuid
from typing import Optional, Callable, Dict, Any, AsyncGenerator
from fastapi import WebSocket, WebSocketDisconnect

from .manager import WebSocketManager, get_websocket_manager
from .models import (
    WebSocketMessage,
    WebSocketStatus,
    ConnectionInfo,
    AudioFormat,
)
from .audio_processor import AudioBuffer, AudioProcessor

logger = logging.getLogger(__name__)


class VoiceWebSocketHandler:
    """
    Handler for voice conversation WebSocket connections.

    Provides a clean interface for handling voice chat WebSocket endpoints.
    Manages connection lifecycle, audio buffering, and message routing.
    """

    def __init__(
        self,
        voice_pipeline: Optional[Any] = None,
        manager: Optional[WebSocketManager] = None,
        on_connect: Optional[Callable] = None,
        on_disconnect: Optional[Callable] = None,
        on_message: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
        pause_threshold_ms: int = 1500,
        sample_rate: int = 16000,
    ):
        """
        Initialize the handler.

        Args:
            voice_pipeline: Optional voice pipeline for processing
            manager: Optional WebSocket manager (uses global if not provided)
            on_connect: Callback when client connects
            on_disconnect: Callback when client disconnects
            on_message: Callback for incoming messages
            on_error: Callback for errors
            pause_threshold_ms: Silence threshold for turn detection
            sample_rate: Audio sample rate
        """
        self.voice_pipeline = voice_pipeline
        self.manager = manager or get_websocket_manager()
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.on_message = on_message
        self.on_error = on_error
        self.pause_threshold_ms = pause_threshold_ms
        self.sample_rate = sample_rate

    async def handle_connection(
        self,
        websocket: WebSocket,
        assistant_id: str,
        user_id: Optional[str] = None,
        auth_token: Optional[str] = None,
    ):
        """
        Handle a WebSocket connection for voice chat.

        This is the main entry point for WebSocket endpoints.

        Args:
            websocket: WebSocket connection
            assistant_id: ID of assistant to use
            user_id: Optional user ID
            auth_token: Optional authentication token
        """
        connection_id = f"{assistant_id}_{uuid.uuid4().hex[:8]}"

        try:
            # Connect
            info = await self.manager.connect(
                websocket=websocket,
                connection_id=connection_id,
                user_id=user_id,
                assistant_id=assistant_id,
            )

            logger.info(f"Voice WebSocket connected: {connection_id}")

            # Trigger connect callback
            if self.on_connect:
                await self._safe_callback(self.on_connect, info)

            # Send welcome message
            await self._send_status(connection_id, "Connected - Ready for voice input")

            # Create audio buffer for this connection
            audio_buffer = AudioBuffer(sample_rate=self.sample_rate)
            turn_in_progress = False

            # Main message loop
            while True:
                try:
                    message = await websocket.receive_json()
                    await self._handle_message(
                        connection_id=connection_id,
                        message=message,
                        assistant_id=assistant_id,
                        audio_buffer=audio_buffer,
                        turn_in_progress=turn_in_progress,
                    )

                except WebSocketDisconnect:
                    logger.info(f"WebSocket disconnected: {connection_id}")
                    break

                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    await self._send_error(connection_id, str(e))

        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            if self.on_error:
                await self._safe_callback(self.on_error, connection_id, e)

        finally:
            # Cleanup
            await self.manager.disconnect(connection_id)
            if self.on_disconnect:
                await self._safe_callback(self.on_disconnect, connection_id)

    async def _handle_message(
        self,
        connection_id: str,
        message: Dict[str, Any],
        assistant_id: str,
        audio_buffer: AudioBuffer,
        turn_in_progress: bool,
    ):
        """
        Handle an incoming WebSocket message.

        Args:
            connection_id: Connection ID
            message: Incoming message
            assistant_id: Assistant ID
            audio_buffer: Audio buffer for this connection
            turn_in_progress: Whether a turn is being processed
        """
        msg_type = message.get("type")
        msg_data = message.get("data")

        # Trigger message callback
        if self.on_message:
            await self._safe_callback(self.on_message, connection_id, message)

        if msg_type == "pcm_chunk":
            # Add audio to buffer
            audio_buffer.add_base64(msg_data)
            logger.debug(f"Received PCM chunk, buffer: {audio_buffer.duration_ms:.0f}ms")

        elif msg_type == "turn_complete":
            # Process complete turn
            if audio_buffer.size > 0 and not turn_in_progress:
                await self._process_turn(
                    connection_id=connection_id,
                    assistant_id=assistant_id,
                    audio_buffer=audio_buffer,
                )

        elif msg_type == "text":
            # Handle text input
            await self._process_text_input(
                connection_id=connection_id,
                assistant_id=assistant_id,
                text=msg_data,
            )

        elif msg_type == "reset":
            # Reset conversation
            audio_buffer.clear()
            await self._send_status(connection_id, "Conversation reset")

        elif msg_type == "ping":
            # Keep-alive ping
            await self.manager.send_json(connection_id, {
                "type": "pong",
                "data": "alive"
            })

    async def _process_turn(
        self,
        connection_id: str,
        assistant_id: str,
        audio_buffer: AudioBuffer,
    ):
        """
        Process a complete voice turn.

        Args:
            connection_id: Connection ID
            assistant_id: Assistant ID
            audio_buffer: Audio buffer with collected audio
        """
        # Get all audio data
        audio_data = audio_buffer.drain()

        if not audio_data:
            return

        logger.info(f"Processing turn: {len(audio_data)} bytes")

        # Update status
        await self._send_status(connection_id, "Processing...")

        try:
            if self.voice_pipeline:
                # Create audio stream generator
                async def audio_stream():
                    # Split into chunks for processing
                    for chunk in AudioProcessor.split_into_chunks(audio_data):
                        yield chunk

                # Process through pipeline
                async for pipeline_msg in self.voice_pipeline.process_turn(audio_stream()):
                    # Forward pipeline messages to client
                    await self.manager.send_json(connection_id, pipeline_msg)

            else:
                # No pipeline - just acknowledge
                await self.manager.send_json(connection_id, {
                    "type": "status",
                    "data": "Audio received (no pipeline configured)"
                })

        except Exception as e:
            logger.error(f"Turn processing error: {e}")
            await self._send_error(connection_id, str(e))

        finally:
            # Ready for next turn
            await self.manager.send_json(connection_id, {
                "type": "ready_for_turn",
                "data": "Ready for next utterance"
            })

    async def _process_text_input(
        self,
        connection_id: str,
        assistant_id: str,
        text: str,
    ):
        """
        Process text input (non-voice).

        Args:
            connection_id: Connection ID
            assistant_id: Assistant ID
            text: User's text input
        """
        logger.info(f"Processing text input: {text[:50]}...")

        await self._send_status(connection_id, "Processing text...")

        try:
            if self.voice_pipeline:
                # Process text through pipeline if supported
                # This depends on pipeline implementation
                pass
            else:
                await self.manager.send_json(connection_id, {
                    "type": "text_response",
                    "data": "Text processing not configured"
                })

        except Exception as e:
            logger.error(f"Text processing error: {e}")
            await self._send_error(connection_id, str(e))

    async def _send_status(self, connection_id: str, status: str):
        """Send status message to client."""
        await self.manager.send_json(connection_id, {
            "type": "status",
            "data": status
        })

    async def _send_error(self, connection_id: str, error: str):
        """Send error message to client."""
        await self.manager.send_json(connection_id, {
            "type": "error",
            "data": error
        })

    async def _safe_callback(self, callback: Callable, *args, **kwargs):
        """Safely execute a callback."""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(*args, **kwargs)
            else:
                callback(*args, **kwargs)
        except Exception as e:
            logger.error(f"Callback error: {e}")


def create_voice_websocket_handler(
    voice_pipeline: Optional[Any] = None,
    **kwargs,
) -> VoiceWebSocketHandler:
    """
    Factory function to create a voice WebSocket handler.

    Args:
        voice_pipeline: Voice pipeline instance
        **kwargs: Additional handler options

    Returns:
        Configured VoiceWebSocketHandler
    """
    return VoiceWebSocketHandler(
        voice_pipeline=voice_pipeline,
        **kwargs,
    )
