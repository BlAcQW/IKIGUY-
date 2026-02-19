"""
Tests for WebSocket models.

Tests data structures for WebSocket communication.
"""

import pytest
from datetime import datetime
from apps.shared.websocket.models import (
    WebSocketStatus,
    AudioFormat,
    WebSocketMessage,
    AudioChunkMessage,
    TranscriptionMessage,
    TextResponseMessage,
    StatusMessage,
    ErrorMessage,
    ConnectionInfo,
)


class TestWebSocketStatus:
    """Tests for WebSocketStatus enum."""

    def test_status_values(self):
        """Test all status values exist."""
        assert WebSocketStatus.CONNECTING.value == "connecting"
        assert WebSocketStatus.CONNECTED.value == "connected"
        assert WebSocketStatus.AUTHENTICATED.value == "authenticated"
        assert WebSocketStatus.PROCESSING.value == "processing"
        assert WebSocketStatus.READY.value == "ready"
        assert WebSocketStatus.DISCONNECTED.value == "disconnected"
        assert WebSocketStatus.ERROR.value == "error"


class TestAudioFormat:
    """Tests for AudioFormat enum."""

    def test_audio_format_values(self):
        """Test all audio format values exist."""
        assert AudioFormat.PCM.value == "pcm"
        assert AudioFormat.WAV.value == "wav"
        assert AudioFormat.WEBM.value == "webm"
        assert AudioFormat.MP3.value == "mp3"
        assert AudioFormat.OGG.value == "ogg"


class TestWebSocketMessage:
    """Tests for WebSocketMessage model."""

    def test_create_message(self):
        """Test creating a basic message."""
        msg = WebSocketMessage(
            type="test",
            data={"key": "value"},
            session_id="session_123",
            sequence=1,
        )

        assert msg.type == "test"
        assert msg.data == {"key": "value"}
        assert msg.session_id == "session_123"
        assert msg.sequence == 1
        assert isinstance(msg.timestamp, datetime)

    def test_message_defaults(self):
        """Test message default values."""
        msg = WebSocketMessage(type="ping")

        assert msg.type == "ping"
        assert msg.data is None
        assert msg.session_id is None
        assert msg.sequence is None

    def test_to_dict(self):
        """Test converting message to dict."""
        msg = WebSocketMessage(
            type="audio",
            data="base64data",
            sequence=5,
        )

        d = msg.to_dict()

        assert d["type"] == "audio"
        assert d["data"] == "base64data"
        assert d["sequence"] == 5
        assert "timestamp" in d


class TestAudioChunkMessage:
    """Tests for AudioChunkMessage model."""

    def test_create_audio_chunk(self):
        """Test creating audio chunk message."""
        msg = AudioChunkMessage(
            data="SGVsbG8gV29ybGQ=",  # "Hello World" base64
            format=AudioFormat.WAV,
            sample_rate=16000,
            duration_ms=100.5,
        )

        assert msg.type == "audio_chunk"
        assert msg.data == "SGVsbG8gV29ybGQ="
        assert msg.format == AudioFormat.WAV
        assert msg.sample_rate == 16000
        assert msg.duration_ms == 100.5

    def test_audio_chunk_defaults(self):
        """Test audio chunk defaults."""
        msg = AudioChunkMessage(data="test")

        assert msg.format == AudioFormat.WAV
        assert msg.sample_rate == 16000
        assert msg.duration_ms is None


class TestTranscriptionMessage:
    """Tests for TranscriptionMessage model."""

    def test_create_transcription(self):
        """Test creating transcription message."""
        msg = TranscriptionMessage(
            text="Hello, how are you?",
            is_final=True,
            language="en",
            confidence=0.95,
        )

        assert msg.type == "transcription"
        assert msg.text == "Hello, how are you?"
        assert msg.is_final is True
        assert msg.language == "en"
        assert msg.confidence == 0.95

    def test_partial_transcription(self):
        """Test partial transcription."""
        msg = TranscriptionMessage(
            text="Hello",
            is_final=False,
        )

        assert msg.is_final is False
        assert msg.language is None


class TestTextResponseMessage:
    """Tests for TextResponseMessage model."""

    def test_create_response(self):
        """Test creating text response."""
        msg = TextResponseMessage(
            text="I'm doing well, thank you!",
            model="gemini-2.5-flash",
            tokens_used={"input": 10, "output": 8},
        )

        assert msg.type == "text_response"
        assert msg.text == "I'm doing well, thank you!"
        assert msg.is_final is True
        assert msg.model == "gemini-2.5-flash"
        assert msg.tokens_used == {"input": 10, "output": 8}


class TestStatusMessage:
    """Tests for StatusMessage model."""

    def test_create_status(self):
        """Test creating status message."""
        msg = StatusMessage(
            status=WebSocketStatus.PROCESSING,
            message="Transcribing audio...",
        )

        assert msg.type == "status"
        assert msg.status == WebSocketStatus.PROCESSING
        assert msg.message == "Transcribing audio..."


class TestErrorMessage:
    """Tests for ErrorMessage model."""

    def test_create_error(self):
        """Test creating error message."""
        msg = ErrorMessage(
            error="Connection timeout",
            code="TIMEOUT",
            recoverable=True,
        )

        assert msg.type == "error"
        assert msg.error == "Connection timeout"
        assert msg.code == "TIMEOUT"
        assert msg.recoverable is True

    def test_non_recoverable_error(self):
        """Test non-recoverable error."""
        msg = ErrorMessage(
            error="Authentication failed",
            recoverable=False,
        )

        assert msg.recoverable is False


class TestConnectionInfo:
    """Tests for ConnectionInfo model."""

    def test_create_connection_info(self):
        """Test creating connection info."""
        info = ConnectionInfo(
            connection_id="conn_123",
            session_id="sess_456",
            user_id="user_789",
            assistant_id="asst_abc",
        )

        assert info.connection_id == "conn_123"
        assert info.session_id == "sess_456"
        assert info.user_id == "user_789"
        assert info.assistant_id == "asst_abc"
        assert info.status == WebSocketStatus.CONNECTING
        assert info.message_count == 0

    def test_update_activity(self):
        """Test updating activity timestamp."""
        info = ConnectionInfo(connection_id="conn_123")
        old_time = info.last_activity

        import time
        time.sleep(0.01)
        info.update_activity()

        assert info.last_activity > old_time

    def test_increment_message_count(self):
        """Test incrementing message counter."""
        info = ConnectionInfo(connection_id="conn_123")

        assert info.message_count == 0

        info.increment_message_count()
        assert info.message_count == 1

        info.increment_message_count()
        assert info.message_count == 2
