"""
Unit tests for Voice Chat WebSocket Handler with VoiceAgent approach.

Tests for real-time voice interaction via WebSocket:
- Connection handling
- Message routing
- Server-side PCM VAD
- Conversation state machine
- RAG integration
- TTS streaming

Author: AI Labs Africa
Created: November 30, 2025
"""

import pytest
import asyncio
import json
import base64
import struct
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, '/opt/kasaai/apps')


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket connection."""
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    ws.receive_json = AsyncMock()
    ws.close = AsyncMock()
    # Mock client_state for is_websocket_open check
    ws.client_state = MagicMock()
    ws.client_state.name = 'CONNECTED'
    return ws


@pytest.fixture
def sample_pcm_audio():
    """Create sample 16-bit PCM audio data."""
    # Generate 0.5 seconds of silence at 16kHz (16000 samples)
    num_samples = 8000
    samples = struct.pack('<' + 'h' * num_samples, *([0] * num_samples))
    return base64.b64encode(samples).decode('utf-8')


@pytest.fixture
def sample_float32_pcm():
    """Create sample Float32 PCM audio data for VAD."""
    # Generate 0.5 seconds of silence at 16kHz
    num_samples = 8000
    samples = np.zeros(num_samples, dtype=np.float32)
    return base64.b64encode(samples.tobytes()).decode('utf-8')


class TestConversationStateMachine:
    """Test ConversationStateMachine class."""

    def test_initial_state(self):
        """Test initial state is IDLE."""
        from app.services.conversation_state_machine import (
            ConversationStateMachine, ConversationState
        )

        sm = ConversationStateMachine()

        assert sm.conversation_state == ConversationState.IDLE
        assert sm.hands_free_mode is True
        assert sm.can_record() is True

    def test_start_listening(self):
        """Test transition to LISTENING state."""
        from app.services.conversation_state_machine import (
            ConversationStateMachine, ConversationState
        )

        sm = ConversationStateMachine()
        sm.start_listening()

        assert sm.conversation_state == ConversationState.LISTENING

    def test_stop_listening(self):
        """Test transition to PROCESSING state."""
        from app.services.conversation_state_machine import (
            ConversationStateMachine, ConversationState
        )

        sm = ConversationStateMachine()
        sm.start_listening()
        sm.stop_listening()

        assert sm.conversation_state == ConversationState.PROCESSING

    def test_start_speaking(self):
        """Test transition to SPEAKING state."""
        from app.services.conversation_state_machine import (
            ConversationStateMachine, ConversationState
        )

        sm = ConversationStateMachine()
        sm.start_speaking()

        assert sm.conversation_state == ConversationState.SPEAKING
        assert sm.can_record() is False

    def test_stop_speaking(self):
        """Test transition back to IDLE state."""
        from app.services.conversation_state_machine import (
            ConversationStateMachine, ConversationState
        )

        sm = ConversationStateMachine()
        sm.start_speaking()
        sm.stop_speaking()

        assert sm.conversation_state == ConversationState.IDLE

    def test_interruption(self):
        """Test user interruption during speaking."""
        from app.services.conversation_state_machine import (
            ConversationStateMachine, ConversationState
        )

        sm = ConversationStateMachine()
        sm.start_speaking()

        # Simulate user starting to speak while assistant is speaking
        sm.start_listening()

        assert sm.conversation_state == ConversationState.INTERRUPTED
        assert sm.user_spoke_during_assistant is True

    def test_auto_resume_listening(self):
        """Test hands-free auto-resume logic."""
        from app.services.conversation_state_machine import (
            ConversationStateMachine, ConversationState
        )

        sm = ConversationStateMachine()
        sm.hands_free_mode = True

        # Complete a speaking turn
        sm.start_speaking()
        sm.stop_speaking()

        # Should auto-resume
        assert sm.should_auto_resume_listening() is True

    def test_no_auto_resume_after_interruption(self):
        """Test no auto-resume if user spoke during assistant."""
        from app.services.conversation_state_machine import (
            ConversationStateMachine, ConversationState
        )

        sm = ConversationStateMachine()
        sm.hands_free_mode = True

        sm.start_speaking()
        sm.user_spoke_during_assistant = True
        sm.stop_speaking()

        # Should not auto-resume
        assert sm.should_auto_resume_listening() is False

    def test_get_state_info(self):
        """Test state info dictionary."""
        from app.services.conversation_state_machine import (
            ConversationStateMachine, ConversationState
        )

        sm = ConversationStateMachine()
        info = sm.get_state_info()

        assert "conversation_state" in info
        assert "vad_state" in info
        assert "hands_free_mode" in info
        assert "can_record" in info
        assert info["conversation_state"] == "idle"

    def test_reset(self):
        """Test state machine reset."""
        from app.services.conversation_state_machine import (
            ConversationStateMachine, ConversationState
        )

        sm = ConversationStateMachine()
        sm.start_listening()
        sm.stop_listening()
        sm.reset()

        assert sm.conversation_state == ConversationState.IDLE
        assert sm.user_spoke_during_assistant is False


class TestPCMVADHandler:
    """Test PCMVADHandler class."""

    def test_pcm_to_wav(self):
        """Test PCM to WAV conversion."""
        from app.services.pcm_vad_handler import pcm_to_wav

        # Create sample PCM data (1 second of silence)
        num_samples = 16000
        pcm_samples = np.zeros(num_samples, dtype=np.float32)

        wav_bytes = pcm_to_wav(pcm_samples, sample_rate=16000)

        # Verify WAV header
        assert wav_bytes[:4] == b'RIFF'
        assert wav_bytes[8:12] == b'WAVE'
        assert wav_bytes[12:16] == b'fmt '
        assert wav_bytes[36:40] == b'data'

    def test_pcm_base64_to_wav_base64(self):
        """Test base64 PCM to base64 WAV conversion."""
        from app.services.pcm_vad_handler import pcm_base64_to_wav_base64

        # Create sample PCM data
        num_samples = 16000
        pcm_samples = np.zeros(num_samples, dtype=np.float32)
        pcm_base64 = base64.b64encode(pcm_samples.tobytes()).decode('utf-8')

        wav_base64 = pcm_base64_to_wav_base64(pcm_base64, sample_rate=16000)

        # Decode and verify
        wav_bytes = base64.b64decode(wav_base64)
        assert wav_bytes[:4] == b'RIFF'
        assert wav_bytes[8:12] == b'WAVE'


class TestVoiceChatSession:
    """Test VoiceChatSession class."""

    @pytest.mark.asyncio
    async def test_session_creation(self, mock_websocket):
        """Test creating a VoiceChatSession."""
        from app.api.websocket.voice_chat import VoiceChatSession

        session = VoiceChatSession(
            websocket=mock_websocket,
            book_id="test-book-123",
            user_id="test-user-456"
        )

        assert session.book_id == "test-book-123"
        assert session.user_id == "test-user-456"
        assert session.session_id is not None
        assert len(session.session_id) == 8

    @pytest.mark.asyncio
    async def test_session_default_voice_settings(self, mock_websocket):
        """Test default voice settings."""
        from app.api.websocket.voice_chat import VoiceChatSession

        session = VoiceChatSession(
            websocket=mock_websocket,
            book_id="test-book",
            user_id="test-user"
        )

        assert session.voice_settings["provider_id"] == "kokoro"
        assert session.voice_settings["voice_id"] == "am_adam"
        assert session.voice_settings["speed"] == 1.0
        assert session.voice_settings["language"] == "en"

    @pytest.mark.asyncio
    async def test_session_custom_voice_settings(self, mock_websocket):
        """Test custom voice settings."""
        from app.api.websocket.voice_chat import VoiceChatSession

        custom_settings = {
            "provider_id": "coqui_xtts",
            "voice_id": "en_female_1",
            "speed": 1.2,
            "language": "en"
        }

        session = VoiceChatSession(
            websocket=mock_websocket,
            book_id="test-book",
            user_id="test-user",
            voice_settings=custom_settings
        )

        assert session.voice_settings["provider_id"] == "coqui_xtts"
        assert session.voice_settings["voice_id"] == "en_female_1"
        assert session.voice_settings["speed"] == 1.2

    @pytest.mark.asyncio
    async def test_send_message(self, mock_websocket):
        """Test sending a message to the client."""
        from app.api.websocket.voice_chat import VoiceChatSession

        # Mock is_websocket_open
        with patch('app.api.websocket.voice_chat.is_websocket_open', return_value=True):
            session = VoiceChatSession(
                websocket=mock_websocket,
                book_id="test-book",
                user_id="test-user"
            )

            await session.send_message("status", "Connected")

            mock_websocket.send_json.assert_called_once_with({
                "type": "status",
                "data": "Connected"
            })

    @pytest.mark.asyncio
    async def test_handle_init(self, mock_websocket):
        """Test handling initialization message."""
        from app.api.websocket.voice_chat import VoiceChatSession

        with patch('app.api.websocket.voice_chat.is_websocket_open', return_value=True):
            session = VoiceChatSession(
                websocket=mock_websocket,
                book_id="test-book",
                user_id="test-user"
            )
            # Mock initialize to avoid VAD setup
            session.state_machine = MagicMock()
            session.state_machine.get_state_info.return_value = {"state": "idle"}

            init_data = {
                "voice_settings": {
                    "provider_id": "openai_tts",
                    "voice_id": "alloy"
                },
                "asr_settings": {
                    "model": "large"
                },
                "llm_settings": {
                    "model": "gemini-2.0-flash"
                },
                "hands_free": True
            }

            await session.handle_init(init_data)

            # Verify voice settings were updated
            assert session.voice_settings["provider_id"] == "openai_tts"
            assert session.voice_settings["voice_id"] == "alloy"
            assert session.asr_model == "large"
            assert session.llm_model == "gemini-2.0-flash"

    @pytest.mark.asyncio
    async def test_handle_barge_in(self, mock_websocket):
        """Test handling barge-in (interruption)."""
        from app.api.websocket.voice_chat import VoiceChatSession

        with patch('app.api.websocket.voice_chat.is_websocket_open', return_value=True):
            session = VoiceChatSession(
                websocket=mock_websocket,
                book_id="test-book",
                user_id="test-user"
            )
            session.state_machine = MagicMock()

            await session.handle_barge_in()

            # Verify state machine was notified
            session.state_machine.start_listening.assert_called_once()


class TestVoiceChatWebSocket:
    """Test WebSocket endpoint handler."""

    @pytest.mark.asyncio
    async def test_active_sessions_management(self, mock_websocket):
        """Test that active sessions are properly managed."""
        from app.api.websocket.voice_chat import VoiceChatSession, active_sessions

        # Clear existing sessions
        active_sessions.clear()

        session = VoiceChatSession(
            websocket=mock_websocket,
            book_id="test-book",
            user_id="test-user"
        )

        # Add session
        active_sessions[session.session_id] = session
        assert session.session_id in active_sessions

        # Remove session
        del active_sessions[session.session_id]
        assert session.session_id not in active_sessions


class TestMessageTypes:
    """Test various message type handling."""

    @pytest.mark.asyncio
    async def test_message_type_init(self, mock_websocket):
        """Test init message type."""
        from app.api.websocket.voice_chat import VoiceChatSession

        with patch('app.api.websocket.voice_chat.is_websocket_open', return_value=True):
            session = VoiceChatSession(
                websocket=mock_websocket,
                book_id="test-book",
                user_id="test-user"
            )
            session.state_machine = MagicMock()
            session.state_machine.get_state_info.return_value = {"state": "idle"}

            await session.handle_init({})

            # Should send status and conversation_state
            calls = mock_websocket.send_json.call_args_list
            msg_types = [call[0][0]["type"] for call in calls]

            assert "status" in msg_types
            assert "conversation_state" in msg_types
            assert "ready_to_listen" in msg_types

    @pytest.mark.asyncio
    async def test_handle_text_message(self, mock_websocket):
        """Test text message handling."""
        from app.api.websocket.voice_chat import VoiceChatSession

        with patch('app.api.websocket.voice_chat.is_websocket_open', return_value=True):
            session = VoiceChatSession(
                websocket=mock_websocket,
                book_id="test-book",
                user_id="test-user"
            )
            session.state_machine = MagicMock()
            session.state_machine.can_record.return_value = True

            # Mock the RAG service
            with patch.object(
                session, '_get_rag_response', new_callable=AsyncMock
            ) as mock_rag:
                mock_rag.return_value = "This is a test response."

                with patch.object(
                    session, '_stream_tts_audio', new_callable=AsyncMock
                ) as mock_tts:
                    mock_tts.return_value = 2.0  # 2 seconds duration

                    await session.handle_text("What is this book about?")

            # Verify RAG was called
            mock_rag.assert_called_once_with("What is this book about?")


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_stop_recording_no_audio(self, mock_websocket):
        """Test handling stop recording with no audio."""
        from app.api.websocket.voice_chat import VoiceChatSession

        with patch('app.api.websocket.voice_chat.is_websocket_open', return_value=True):
            session = VoiceChatSession(
                websocket=mock_websocket,
                book_id="test-book",
                user_id="test-user"
            )
            session.pcm_vad_handler = MagicMock()
            session.pcm_vad_handler.vad_session = MagicMock()
            session.pcm_vad_handler.vad_session.is_listening = True
            session.pcm_vad_handler.stop_listening.return_value = None

            await session.handle_stop_recording()

            # Should send error for no audio
            calls = mock_websocket.send_json.call_args_list
            error_calls = [c for c in calls if c[0][0]["type"] == "error"]
            assert len(error_calls) > 0

    @pytest.mark.asyncio
    async def test_cleanup(self, mock_websocket):
        """Test session cleanup."""
        from app.api.websocket.voice_chat import VoiceChatSession

        session = VoiceChatSession(
            websocket=mock_websocket,
            book_id="test-book",
            user_id="test-user"
        )
        session.pcm_vad_handler = MagicMock()

        session.cleanup()

        session.pcm_vad_handler.cleanup.assert_called_once()


class TestConversationHistory:
    """Test conversation history management."""

    @pytest.mark.asyncio
    async def test_conversation_history_update(self, mock_websocket):
        """Test that conversation history is updated."""
        from app.api.websocket.voice_chat import VoiceChatSession

        session = VoiceChatSession(
            websocket=mock_websocket,
            book_id="test-book",
            user_id="test-user"
        )

        # Initially empty
        assert len(session.conversation_history) == 0

        # Manually add to history (simulating successful Q&A)
        session.conversation_history.append({
            "role": "user",
            "content": "What is the main theme?"
        })
        session.conversation_history.append({
            "role": "assistant",
            "content": "The main theme is about growth and learning."
        })

        assert len(session.conversation_history) == 2
        assert session.conversation_history[0]["role"] == "user"
        assert session.conversation_history[1]["role"] == "assistant"


class TestVADSuppressionDuringTTS:
    """Test VAD suppression during TTS playback to prevent echo feedback."""

    @pytest.mark.asyncio
    async def test_tts_playback_active_flag_initialization(self, mock_websocket):
        """Test that TTS playback flag is initialized to False."""
        from app.api.websocket.voice_chat import VoiceChatSession

        session = VoiceChatSession(
            websocket=mock_websocket,
            book_id="test-book",
            user_id="test-user"
        )

        assert session._tts_playback_active is False
        assert session._is_speaking is False

    @pytest.mark.asyncio
    async def test_vad_suppressed_during_tts(self, mock_websocket, sample_float32_pcm):
        """Test that VAD processing is skipped when TTS is active."""
        from app.api.websocket.voice_chat import VoiceChatSession

        with patch('app.api.websocket.voice_chat.is_websocket_open', return_value=True):
            session = VoiceChatSession(
                websocket=mock_websocket,
                book_id="test-book",
                user_id="test-user"
            )
            session.pcm_vad_handler = MagicMock()
            session.state_machine = MagicMock()
            session.state_machine.can_record.return_value = True

            # Set TTS playback active
            session._tts_playback_active = True

            # Process PCM chunk - should be ignored due to TTS
            await session.handle_pcm_chunk(sample_float32_pcm)

            # VAD handler should NOT be called
            session.pcm_vad_handler.process_pcm_base64.assert_not_called()

    @pytest.mark.asyncio
    async def test_vad_suppressed_when_is_speaking(self, mock_websocket, sample_float32_pcm):
        """Test that VAD is also suppressed when _is_speaking is True."""
        from app.api.websocket.voice_chat import VoiceChatSession

        with patch('app.api.websocket.voice_chat.is_websocket_open', return_value=True):
            session = VoiceChatSession(
                websocket=mock_websocket,
                book_id="test-book",
                user_id="test-user"
            )
            session.pcm_vad_handler = MagicMock()
            session.state_machine = MagicMock()
            session.state_machine.can_record.return_value = True

            # Set is_speaking flag
            session._is_speaking = True

            # Process PCM chunk - should be ignored
            await session.handle_pcm_chunk(sample_float32_pcm)

            # VAD handler should NOT be called
            session.pcm_vad_handler.process_pcm_base64.assert_not_called()

    @pytest.mark.asyncio
    async def test_barge_in_clears_tts_flags(self, mock_websocket):
        """Test that barge-in clears TTS playback flags."""
        from app.api.websocket.voice_chat import VoiceChatSession

        with patch('app.api.websocket.voice_chat.is_websocket_open', return_value=True):
            session = VoiceChatSession(
                websocket=mock_websocket,
                book_id="test-book",
                user_id="test-user"
            )
            session.state_machine = MagicMock()
            session.pcm_vad_handler = MagicMock()
            session.pcm_vad_handler.start_listening = MagicMock()

            # Simulate TTS in progress
            session._tts_playback_active = True
            session._is_speaking = True
            session._tts_cancelled = False

            await session.handle_barge_in()

            # All TTS flags should be reset
            assert session._tts_cancelled is True
            assert session._is_speaking is False
            assert session._tts_playback_active is False

    @pytest.mark.asyncio
    async def test_barge_in_sends_stop_audio(self, mock_websocket):
        """Test that barge-in sends stop_audio message to frontend."""
        from app.api.websocket.voice_chat import VoiceChatSession

        with patch('app.api.websocket.voice_chat.is_websocket_open', return_value=True):
            session = VoiceChatSession(
                websocket=mock_websocket,
                book_id="test-book",
                user_id="test-user"
            )
            session.state_machine = MagicMock()
            session.pcm_vad_handler = MagicMock()
            session.pcm_vad_handler.start_listening = MagicMock()

            await session.handle_barge_in()

            # Verify stop_audio was sent
            calls = mock_websocket.send_json.call_args_list
            stop_audio_calls = [c for c in calls if c[0][0]["type"] == "stop_audio"]
            assert len(stop_audio_calls) > 0

            # Verify barge_in_ack was sent
            ack_calls = [c for c in calls if c[0][0]["type"] == "barge_in_ack"]
            assert len(ack_calls) > 0


class TestTextCleaningForTTS:
    """Test text cleaning for TTS to remove markdown/HTML."""

    def test_clean_markdown_headers(self):
        """Test removal of markdown headers."""
        from app.api.websocket.voice_chat import clean_text_for_tts

        text = "## Chapter 1\n\nThis is content."
        result = clean_text_for_tts(text)

        assert "##" not in result
        assert "Chapter 1" in result
        assert "This is content." in result

    def test_clean_bold_text(self):
        """Test removal of bold markers."""
        from app.api.websocket.voice_chat import clean_text_for_tts

        text = "This is **bold** and __also bold__ text."
        result = clean_text_for_tts(text)

        assert "**" not in result
        assert "__" not in result
        assert "bold" in result
        assert "also bold" in result

    def test_clean_italic_text(self):
        """Test removal of italic markers."""
        from app.api.websocket.voice_chat import clean_text_for_tts

        text = "This is *italic* and _also italic_ text."
        result = clean_text_for_tts(text)

        assert "*italic*" not in result
        assert "_also italic_" not in result
        assert "italic" in result

    def test_clean_markdown_links(self):
        """Test removal of markdown links, preserving text."""
        from app.api.websocket.voice_chat import clean_text_for_tts

        text = "Check out [this link](https://example.com) for more."
        result = clean_text_for_tts(text)

        assert "[" not in result
        assert "](" not in result
        assert "this link" in result
        assert "https://example.com" not in result

    def test_clean_html_tags(self):
        """Test removal of HTML tags."""
        from app.api.websocket.voice_chat import clean_text_for_tts

        text = "This is <b>bold</b> and <a href='#'>linked</a> text."
        result = clean_text_for_tts(text)

        assert "<" not in result
        assert ">" not in result
        assert "bold" in result
        assert "linked" in result

    def test_clean_code_blocks(self):
        """Test removal of code blocks."""
        from app.api.websocket.voice_chat import clean_text_for_tts

        text = "Here is code:\n```python\nprint('hello')\n```\nAnd more text."
        result = clean_text_for_tts(text)

        assert "```" not in result
        assert "And more text" in result

    def test_clean_inline_code(self):
        """Test removal of inline code markers."""
        from app.api.websocket.voice_chat import clean_text_for_tts

        text = "Use the `print()` function."
        result = clean_text_for_tts(text)

        assert "`" not in result
        assert "print()" in result

    def test_clean_bullet_points(self):
        """Test removal of bullet point markers."""
        from app.api.websocket.voice_chat import clean_text_for_tts

        text = "Items:\n- First item\n- Second item\n* Third item"
        result = clean_text_for_tts(text)

        assert "First item" in result
        assert "Second item" in result
        assert "Third item" in result

    def test_clean_empty_text(self):
        """Test handling of empty text."""
        from app.api.websocket.voice_chat import clean_text_for_tts

        assert clean_text_for_tts("") == ""
        assert clean_text_for_tts(None) == ""

    def test_clean_preserves_plain_text(self):
        """Test that plain text is preserved."""
        from app.api.websocket.voice_chat import clean_text_for_tts

        text = "This is plain text with no formatting."
        result = clean_text_for_tts(text)

        assert result == text


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
