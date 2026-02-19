"""
Shared WebSocket Module

Provides reusable WebSocket utilities for real-time voice conversations.

Usage:
    from apps.shared.websocket import (
        WebSocketManager,
        VoiceWebSocketHandler,
        WebSocketMessage,
    )

    # Create handler for voice conversations
    handler = VoiceWebSocketHandler(
        voice_pipeline=pipeline,
        on_message=on_message_callback,
    )

    # Use in FastAPI endpoint
    @router.websocket("/voice-chat/{assistant_id}")
    async def voice_chat(websocket: WebSocket, assistant_id: str):
        await handler.handle_connection(websocket, assistant_id)

Author: KasaAI Team
Date: 2025-11-26
"""

from .manager import WebSocketManager
from .handler import VoiceWebSocketHandler
from .models import WebSocketMessage, WebSocketStatus, AudioFormat
from .audio_processor import AudioProcessor, AudioBuffer

__all__ = [
    "WebSocketManager",
    "VoiceWebSocketHandler",
    "WebSocketMessage",
    "WebSocketStatus",
    "AudioFormat",
    "AudioProcessor",
    "AudioBuffer",
]
