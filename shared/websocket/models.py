"""
WebSocket Data Models

Defines data structures for WebSocket communication.

Author: KasaAI Team
Date: 2025-11-26
"""

from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class WebSocketStatus(str, Enum):
    """WebSocket connection status."""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"
    PROCESSING = "processing"
    READY = "ready"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class AudioFormat(str, Enum):
    """Supported audio formats."""
    PCM = "pcm"  # Raw PCM 16-bit
    WAV = "wav"
    WEBM = "webm"
    MP3 = "mp3"
    OGG = "ogg"


class WebSocketMessage(BaseModel):
    """
    Standard WebSocket message format.

    Used for both incoming and outgoing messages.
    """
    type: str = Field(..., description="Message type")
    data: Any = Field(default=None, description="Message payload")
    session_id: Optional[str] = Field(None, description="Session ID")
    sequence: Optional[int] = Field(None, description="Message sequence number")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type,
            "data": self.data,
            "session_id": self.session_id,
            "sequence": self.sequence,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


class AudioChunkMessage(BaseModel):
    """Audio chunk message."""
    type: str = "audio_chunk"
    data: str = Field(..., description="Base64-encoded audio data")
    format: AudioFormat = Field(default=AudioFormat.WAV)
    sample_rate: int = Field(default=16000)
    duration_ms: Optional[float] = None


class TranscriptionMessage(BaseModel):
    """Transcription result message."""
    type: str = "transcription"
    text: str = Field(..., description="Transcribed text")
    is_final: bool = Field(default=False)
    language: Optional[str] = None
    confidence: Optional[float] = None


class TextResponseMessage(BaseModel):
    """LLM text response message."""
    type: str = "text_response"
    text: str = Field(..., description="Response text")
    is_final: bool = Field(default=True)
    model: Optional[str] = None
    tokens_used: Optional[Dict[str, int]] = None


class StatusMessage(BaseModel):
    """Status update message."""
    type: str = "status"
    status: WebSocketStatus
    message: Optional[str] = None


class ErrorMessage(BaseModel):
    """Error message."""
    type: str = "error"
    error: str = Field(..., description="Error message")
    code: Optional[str] = None
    recoverable: bool = Field(default=True)


class ConnectionInfo(BaseModel):
    """WebSocket connection information."""
    connection_id: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    assistant_id: Optional[str] = None
    connected_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    status: WebSocketStatus = WebSocketStatus.CONNECTING
    message_count: int = 0
    audio_chunks_sent: int = 0
    audio_chunks_received: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()

    def increment_message_count(self):
        """Increment message counter."""
        self.message_count += 1
        self.update_activity()
