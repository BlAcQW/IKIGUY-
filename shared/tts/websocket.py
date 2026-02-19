"""
WebSocket Client for Real-time TTS
Specialized client for Moshi and other WebSocket-based TTS services.
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Any, Callable, AsyncGenerator
from datetime import datetime
import aiohttp

from .models import WebSocketMessage, AudioFormat
from .exceptions import WebSocketError, ConnectionError
from .utils import AudioUtils, AudioStreamer

logger = logging.getLogger(__name__)


class MoshiWebSocketClient:
    """WebSocket client for Moshi real-time conversation."""

    def __init__(
        self,
        url: str = "wss://moshi.ailabsafrica.com/ws/conversation",
        sample_rate: int = 24000,
        chunk_size: int = 480,  # 20ms chunks at 24kHz
    ):
        """Initialize Moshi WebSocket client.

        Args:
            url: WebSocket URL
            sample_rate: Audio sample rate
            chunk_size: Audio chunk size in samples
        """
        self.url = url
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.session: Optional[aiohttp.ClientSession] = None
        self.ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self.session_id: Optional[str] = None
        self._connected = False
        self._sequence = 0

        # Audio buffers
        self.input_streamer = AudioStreamer(chunk_size, sample_rate)
        self.output_streamer = AudioStreamer(chunk_size, sample_rate)

        # Callbacks
        self.on_connected: Optional[Callable] = None
        self.on_disconnected: Optional[Callable] = None
        self.on_audio_received: Optional[Callable[[bytes], None]] = None
        self.on_text_received: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

    async def connect(self):
        """Connect to Moshi WebSocket endpoint.

        Raises:
            ConnectionError: If connection fails
        """
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()

            self.ws = await self.session.ws_connect(
                self.url,
                heartbeat=30,
                autoping=True
            )

            self._connected = True
            logger.info(f"Connected to Moshi WebSocket at {self.url}")

            # Trigger connected callback
            if self.on_connected:
                await self._safe_callback(self.on_connected)

            # Wait for initial handshake
            msg = await self.ws.receive_json()
            if msg.get("type") == "connected":
                self.session_id = msg.get("session_id")
                logger.info(f"Moshi session established: {self.session_id}")

        except Exception as e:
            self._connected = False
            raise ConnectionError("moshi", self.url, str(e))

    async def disconnect(self):
        """Disconnect from WebSocket."""
        self._connected = False

        if self.ws:
            await self.ws.close()
            self.ws = None

        if self.session:
            await self.session.close()
            self.session = None

        logger.info("Disconnected from Moshi WebSocket")

        if self.on_disconnected:
            await self._safe_callback(self.on_disconnected)

    async def send_audio(self, audio_data: bytes):
        """Send audio data to Moshi.

        Args:
            audio_data: PCM audio data (16-bit, mono)

        Raises:
            WebSocketError: If send fails
        """
        if not self._connected or not self.ws:
            raise WebSocketError("Not connected to WebSocket")

        try:
            # Add to input buffer
            self.input_streamer.add_chunk(audio_data)

            # Send in chunks
            while True:
                chunk = self._get_audio_chunk()
                if not chunk:
                    break

                message = WebSocketMessage(
                    type="audio",
                    data=AudioUtils.encode_base64(chunk),
                    session_id=self.session_id,
                    sequence=self._next_sequence()
                )

                await self.ws.send_json(message.dict())

        except Exception as e:
            raise WebSocketError(f"Failed to send audio: {e}", provider="moshi")

    async def send_text(self, text: str):
        """Send text message to Moshi.

        Args:
            text: Text message

        Raises:
            WebSocketError: If send fails
        """
        if not self._connected or not self.ws:
            raise WebSocketError("Not connected to WebSocket")

        try:
            message = WebSocketMessage(
                type="text",
                data=text,
                session_id=self.session_id,
                sequence=self._next_sequence()
            )

            await self.ws.send_json(message.dict())
            logger.debug(f"Sent text: {text[:50]}...")

        except Exception as e:
            raise WebSocketError(f"Failed to send text: {e}", provider="moshi")

    async def receive_messages(self) -> AsyncGenerator[WebSocketMessage, None]:
        """Receive messages from WebSocket.

        Yields:
            WebSocket messages

        Raises:
            WebSocketError: If receive fails
        """
        if not self._connected or not self.ws:
            raise WebSocketError("Not connected to WebSocket")

        try:
            async for msg in self.ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    message = WebSocketMessage(**data)

                    # Process message based on type
                    if message.type == "audio":
                        # Decode audio
                        audio_data = AudioUtils.decode_base64(message.data)
                        self.output_streamer.add_chunk(audio_data)

                        if self.on_audio_received:
                            await self._safe_callback(self.on_audio_received, audio_data)

                    elif message.type == "text":
                        if self.on_text_received:
                            await self._safe_callback(self.on_text_received, message.data)

                    elif message.type == "error":
                        logger.error(f"Moshi error: {message.data}")
                        if self.on_error:
                            await self._safe_callback(self.on_error, message.data)

                    yield message

                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {self.ws.exception()}")
                    break

                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    logger.info("WebSocket connection closed")
                    break

        except Exception as e:
            raise WebSocketError(f"Failed to receive messages: {e}", provider="moshi")

    async def conversation_loop(
        self,
        audio_input_callback: Optional[Callable[[], bytes]] = None,
        audio_output_callback: Optional[Callable[[bytes], None]] = None,
        text_callback: Optional[Callable[[str], None]] = None,
    ):
        """Run full-duplex conversation loop.

        Args:
            audio_input_callback: Callback to get input audio
            audio_output_callback: Callback to handle output audio
            text_callback: Callback to handle text messages
        """
        # Set callbacks
        if audio_output_callback:
            self.on_audio_received = audio_output_callback
        if text_callback:
            self.on_text_received = text_callback

        try:
            # Start receive task
            receive_task = asyncio.create_task(self._receive_loop())

            # Start send task if input callback provided
            send_task = None
            if audio_input_callback:
                send_task = asyncio.create_task(self._send_loop(audio_input_callback))

            # Wait for tasks
            tasks = [receive_task]
            if send_task:
                tasks.append(send_task)

            await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            logger.error(f"Conversation loop error: {e}")
            raise WebSocketError(f"Conversation failed: {e}", provider="moshi")

    async def _receive_loop(self):
        """Internal receive loop."""
        async for message in self.receive_messages():
            # Messages are handled by callbacks in receive_messages
            pass

    async def _send_loop(self, audio_callback: Callable[[], bytes]):
        """Internal send loop.

        Args:
            audio_callback: Callback to get audio input
        """
        while self._connected:
            try:
                # Get audio from callback
                audio_data = await asyncio.get_event_loop().run_in_executor(
                    None, audio_callback
                )

                if audio_data:
                    await self.send_audio(audio_data)

                # Small delay to prevent busy loop
                await asyncio.sleep(0.01)

            except Exception as e:
                logger.error(f"Send loop error: {e}")
                break

    def _get_audio_chunk(self) -> Optional[bytes]:
        """Get next audio chunk from input buffer.

        Returns:
            Audio chunk or None if buffer is empty
        """
        data = self.input_streamer.get_chunks()
        if len(data) >= self.chunk_size * 2:  # 2 bytes per sample
            chunk = data[:self.chunk_size * 2]
            # Put remaining back in buffer
            if len(data) > self.chunk_size * 2:
                self.input_streamer.add_chunk(data[self.chunk_size * 2:])
            return chunk
        return None

    def _next_sequence(self) -> int:
        """Get next sequence number.

        Returns:
            Sequence number
        """
        self._sequence += 1
        return self._sequence

    async def _safe_callback(self, callback: Callable, *args, **kwargs):
        """Safely execute callback.

        Args:
            callback: Callback function
            *args: Positional arguments
            **kwargs: Keyword arguments
        """
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(*args, **kwargs)
            else:
                await asyncio.get_event_loop().run_in_executor(
                    None, callback, *args, **kwargs
                )
        except Exception as e:
            logger.error(f"Callback error: {e}")


class ConversationManager:
    """High-level conversation manager for Moshi."""

    def __init__(self, url: Optional[str] = None):
        """Initialize conversation manager.

        Args:
            url: WebSocket URL (uses default if not provided)
        """
        self.url = url or "wss://moshi.ailabsafrica.com/ws/conversation"
        self.client: Optional[MoshiWebSocketClient] = None
        self.is_active = False

    async def start_conversation(
        self,
        initial_text: Optional[str] = None,
        on_audio: Optional[Callable[[bytes], None]] = None,
        on_text: Optional[Callable[[str], None]] = None,
    ):
        """Start a conversation with Moshi.

        Args:
            initial_text: Initial text to send
            on_audio: Callback for received audio
            on_text: Callback for received text

        Returns:
            Conversation client
        """
        self.client = MoshiWebSocketClient(self.url)

        # Set callbacks
        self.client.on_audio_received = on_audio
        self.client.on_text_received = on_text

        # Connect
        await self.client.connect()
        self.is_active = True

        # Send initial text if provided
        if initial_text:
            await self.client.send_text(initial_text)

        return self.client

    async def send_audio_stream(self, audio_stream: AsyncGenerator[bytes, None]):
        """Send audio stream to Moshi.

        Args:
            audio_stream: Async generator of audio chunks
        """
        if not self.client or not self.is_active:
            raise WebSocketError("Conversation not started")

        async for chunk in audio_stream:
            await self.client.send_audio(chunk)

    async def stop_conversation(self):
        """Stop the active conversation."""
        if self.client:
            await self.client.disconnect()
            self.client = None
        self.is_active = False