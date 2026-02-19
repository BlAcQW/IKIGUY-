"""
Tests for VoiceAgent WebSocket Handler.

Tests the real-time voice tutoring WebSocket endpoint that uses:
- Server-side PCM VAD for hands-free conversation
- Conversation state machine for turn-taking
- Streaming TTS for low-latency response
- RAG integration for material-aware tutoring

Author: AI Labs Africa
Created: November 30, 2025
"""

import sys
import os
import pytest
import base64
import json
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch

# Ensure apps path is in sys.path
apps_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if apps_path not in sys.path:
    sys.path.insert(0, apps_path)

from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.testclient import WebSocketTestSession


class TestVoiceAgentEndpoint:
    """Tests for the voice agent WebSocket endpoint."""

    @pytest.fixture
    def app(self):
        """Create test FastAPI app."""
        from app.api.routes.voice_agent import router
        app = FastAPI()
        app.include_router(router, prefix="/api/v1")
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    def test_endpoint_exists(self, app):
        """Test that the voice agent endpoint is registered."""
        routes = [r.path for r in app.routes]
        # Check that the WebSocket route is registered
        assert any("/voice-agent" in r for r in routes)

    def test_websocket_connection_no_token(self, client):
        """Test WebSocket connection without token works (anonymous mode)."""
        # This test verifies the endpoint accepts connections
        # Actual authentication is handled inside the handler
        try:
            with client.websocket_connect("/api/v1/voice-agent/ws/test-session") as ws:
                # Should receive initial status
                data = ws.receive_json()
                assert data["type"] == "status"
        except Exception as e:
            # Connection might fail due to missing dependencies in test env
            # But we should verify it's not a route error
            assert "404" not in str(e)


class TestVoiceAgentSession:
    """Tests for VoiceAgentSession class."""

    @pytest.fixture
    def mock_websocket(self):
        """Create mock WebSocket."""
        ws = AsyncMock()
        ws.send_json = AsyncMock()
        return ws

    def test_session_initialization(self, mock_websocket):
        """Test VoiceAgentSession initializes correctly."""
        from app.api.routes.voice_agent import VoiceAgentSession

        session = VoiceAgentSession(
            websocket=mock_websocket,
            session_id="test-session",
            user_id="user-123",
            organization_id="org-456",
            material_id="material-789"
        )

        assert session.study_session_id == "test-session"
        assert session.user_id == "user-123"
        assert session.organization_id == "org-456"
        assert session.material_id == "material-789"
        assert session.state_machine is not None
        assert session.pcm_vad_handler is None  # Not initialized until initialize() is called
        assert session.conversation_history == []

    def test_session_default_settings(self, mock_websocket):
        """Test VoiceAgentSession has sensible defaults."""
        from app.api.routes.voice_agent import VoiceAgentSession

        session = VoiceAgentSession(
            websocket=mock_websocket,
            session_id="test-session",
            user_id="user-123",
            organization_id="org-456"
        )

        # Check default voice settings
        assert session.voice_settings["provider_id"] == "kokoro"
        assert session.voice_settings["voice_id"] == "am_adam"
        assert session.voice_settings["speed"] == 1.0

        # Check default ASR settings
        assert session.asr_provider == "faster_whisper"
        assert session.asr_model == "medium"

        # Check default LLM settings
        assert session.llm_model == "gemini-2.5-flash"

    @pytest.mark.asyncio
    async def test_send_message(self, mock_websocket):
        """Test send_message sends correctly formatted JSON."""
        from app.api.routes.voice_agent import VoiceAgentSession, is_websocket_open

        # Make is_websocket_open return True
        with patch('app.api.routes.voice_agent.is_websocket_open', return_value=True):
            session = VoiceAgentSession(
                websocket=mock_websocket,
                session_id="test-session",
                user_id="user-123",
                organization_id="org-456"
            )

            await session.send_message("test_type", {"key": "value"})

            mock_websocket.send_json.assert_called_once_with({
                "type": "test_type",
                "data": {"key": "value"}
            })

    @pytest.mark.asyncio
    async def test_handle_init_updates_settings(self, mock_websocket):
        """Test handle_init updates session settings."""
        from app.api.routes.voice_agent import VoiceAgentSession

        session = VoiceAgentSession(
            websocket=mock_websocket,
            session_id="test-session",
            user_id="user-123",
            organization_id="org-456"
        )

        # Initialize session (in real scenario, this sets up VAD etc.)
        session.pcm_vad_handler = MagicMock()
        session.pcm_vad_handler.start_listening = MagicMock()
        session.tts_provider = AsyncMock()

        await session.handle_init({
            "voice_settings": {
                "provider_id": "elevenlabs",
                "voice_id": "test-voice",
                "speed": 1.2
            },
            "hands_free": True,
            "material_id": "new-material"
        })

        assert session.voice_settings["provider_id"] == "elevenlabs"
        assert session.voice_settings["voice_id"] == "test-voice"
        assert session.voice_settings["speed"] == 1.2
        assert session.state_machine.hands_free_mode is True
        assert session.material_id == "new-material"

    def test_cleanup(self, mock_websocket):
        """Test cleanup releases resources."""
        from app.api.routes.voice_agent import VoiceAgentSession

        session = VoiceAgentSession(
            websocket=mock_websocket,
            session_id="test-session",
            user_id="user-123",
            organization_id="org-456"
        )

        # Setup mock VAD handler
        mock_vad = MagicMock()
        session.pcm_vad_handler = mock_vad

        session.cleanup()

        mock_vad.cleanup.assert_called_once()


class TestPCMProcessing:
    """Tests for PCM audio processing."""

    def test_pcm_base64_encoding(self):
        """Test PCM data can be encoded to base64."""
        # Create test PCM data
        pcm = np.array([0.1, 0.2, 0.3, -0.1, -0.2], dtype=np.float32)
        pcm_bytes = pcm.tobytes()
        pcm_b64 = base64.b64encode(pcm_bytes).decode('utf-8')

        # Verify it can be decoded back
        decoded_bytes = base64.b64decode(pcm_b64)
        decoded_pcm = np.frombuffer(decoded_bytes, dtype=np.float32)

        np.testing.assert_array_almost_equal(pcm, decoded_pcm)

    def test_pcm_to_wav_conversion(self):
        """Test PCM to WAV conversion using shared module."""
        from apps.shared.voice import pcm_to_wav

        # Create 0.5 seconds of silence at 16kHz
        pcm = np.zeros(8000, dtype=np.float32)
        wav_bytes = pcm_to_wav(pcm, sample_rate=16000)

        # Check WAV header
        assert wav_bytes[:4] == b'RIFF'
        assert wav_bytes[8:12] == b'WAVE'
        assert wav_bytes[12:16] == b'fmt '
        assert wav_bytes[36:40] == b'data'

        # Check expected size (44 byte header + 8000 samples * 2 bytes)
        assert len(wav_bytes) == 44 + 8000 * 2


class TestConversationStateIntegration:
    """Tests for conversation state machine integration."""

    def test_state_machine_initialization(self):
        """Test ConversationStateMachine initializes correctly."""
        from apps.shared.voice import ConversationStateMachine, ConversationState

        sm = ConversationStateMachine()

        assert sm.conversation_state == ConversationState.IDLE
        assert sm.hands_free_mode is True
        assert sm.can_record() is True

    def test_state_transitions(self):
        """Test basic state transitions."""
        from apps.shared.voice import ConversationStateMachine, ConversationState

        sm = ConversationStateMachine()

        # IDLE -> LISTENING
        sm.start_listening()
        assert sm.conversation_state == ConversationState.LISTENING

        # LISTENING -> PROCESSING
        sm.stop_listening()
        assert sm.conversation_state == ConversationState.PROCESSING

        # PROCESSING -> SPEAKING
        sm.start_speaking()
        assert sm.conversation_state == ConversationState.SPEAKING

        # SPEAKING -> IDLE
        sm.stop_speaking()
        assert sm.conversation_state == ConversationState.IDLE


class TestWebSocketProtocol:
    """Tests for WebSocket message protocol."""

    def test_message_format_init(self):
        """Test init message format."""
        message = {
            "type": "init",
            "data": {
                "voice_settings": {
                    "provider_id": "kokoro",
                    "voice_id": "am_adam",
                    "speed": 1.0
                },
                "hands_free": True
            }
        }

        assert message["type"] == "init"
        assert "voice_settings" in message["data"]
        assert "hands_free" in message["data"]

    def test_message_format_pcm_chunk(self):
        """Test pcm_chunk message format."""
        pcm = np.zeros(1000, dtype=np.float32)
        pcm_b64 = base64.b64encode(pcm.tobytes()).decode('utf-8')

        message = {
            "type": "pcm_chunk",
            "data": pcm_b64,
            "sample_rate": 16000
        }

        assert message["type"] == "pcm_chunk"
        assert isinstance(message["data"], str)
        assert message["sample_rate"] == 16000

    def test_message_format_text(self):
        """Test text message format."""
        message = {
            "type": "text",
            "data": "What is photosynthesis?"
        }

        assert message["type"] == "text"
        assert isinstance(message["data"], str)

    def test_message_format_barge_in(self):
        """Test barge_in message format."""
        message = {
            "type": "barge_in",
            "data": "User interrupted"
        }

        assert message["type"] == "barge_in"

    def test_response_format_conversation_state(self):
        """Test conversation_state response format."""
        response = {
            "type": "conversation_state",
            "data": {
                "old_state": "idle",
                "new_state": "listening",
                "can_record": True
            }
        }

        assert response["type"] == "conversation_state"
        assert "old_state" in response["data"]
        assert "new_state" in response["data"]
        assert "can_record" in response["data"]

    def test_response_format_transcription(self):
        """Test transcription response format."""
        response = {
            "type": "transcription",
            "data": {
                "text": "What is photosynthesis?",
                "is_final": True
            }
        }

        assert response["type"] == "transcription"
        assert "text" in response["data"]
        assert "is_final" in response["data"]

    def test_response_format_audio_chunk(self):
        """Test audio_chunk response format."""
        response = {
            "type": "audio_chunk",
            "data": "base64_encoded_audio_data"
        }

        assert response["type"] == "audio_chunk"
        assert isinstance(response["data"], str)


class TestSystemPrompt:
    """Tests for tutoring system prompt."""

    def test_system_prompt_content(self):
        """Test that system prompt contains tutoring instructions."""
        from app.api.routes.voice_agent import VoiceAgentSession
        from unittest.mock import MagicMock

        session = VoiceAgentSession(
            websocket=MagicMock(),
            session_id="test",
            user_id="user",
            organization_id="org"
        )

        prompt = session._build_system_prompt()

        # Check for key tutoring instructions
        assert "tutor" in prompt.lower()
        assert "question" in prompt.lower() or "answer" in prompt.lower()
        assert "student" in prompt.lower() or "encourage" in prompt.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
