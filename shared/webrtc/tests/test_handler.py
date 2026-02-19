"""
Tests for WebRTC signaling handler.

Tests WebSocket handling for WebRTC signaling.
"""

import pytest
import pytest_asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from apps.shared.webrtc.handler import WebRTCSignalingHandler
from apps.shared.webrtc.manager import SignalingManager
from apps.shared.webrtc.models import (
    SignalingMessageType,
    ICECandidate,
    WebRTCOffer,
    WebRTCSessionState,
)


@pytest_asyncio.fixture
async def manager():
    """Create a fresh signaling manager for each test."""
    return SignalingManager()


@pytest_asyncio.fixture
async def handler(manager):
    """Create a handler with the test manager."""
    return WebRTCSignalingHandler(manager=manager)


@pytest_asyncio.fixture
async def mock_websocket():
    """Create a mock WebSocket."""
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    ws.close = AsyncMock()
    return ws


class TestWebRTCSignalingHandler:
    """Tests for WebRTCSignalingHandler class."""

    @pytest.mark.asyncio
    async def test_create_handler_default_manager(self):
        """Test creating handler with default manager."""
        handler = WebRTCSignalingHandler()
        assert handler.manager is not None

    @pytest.mark.asyncio
    async def test_create_handler_custom_manager(self, manager):
        """Test creating handler with custom manager."""
        handler = WebRTCSignalingHandler(manager=manager)
        assert handler.manager is manager

    @pytest.mark.asyncio
    async def test_create_handler_with_callbacks(self, manager):
        """Test creating handler with callbacks."""
        on_offer_called = False

        async def on_offer(session_id, offer):
            nonlocal on_offer_called
            on_offer_called = True
            return "v=0\r\nanswer..."

        handler = WebRTCSignalingHandler(
            manager=manager,
            on_offer=on_offer,
        )

        assert handler._on_offer is not None

    @pytest.mark.asyncio
    async def test_send_transcription(self, handler, manager, mock_websocket):
        """Test sending transcription to client."""
        # Create session and register websocket
        session = await manager.create_session(assistant_id="asst_123")
        manager.register_websocket(session.session_id, mock_websocket)

        await handler.send_transcription(
            session.session_id,
            "Hello world",
            is_final=True,
        )

        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "transcription"
        assert call_args["data"]["text"] == "Hello world"
        assert call_args["data"]["is_final"] is True

    @pytest.mark.asyncio
    async def test_send_transcription_partial(self, handler, manager, mock_websocket):
        """Test sending partial transcription."""
        session = await manager.create_session(assistant_id="asst_123")
        manager.register_websocket(session.session_id, mock_websocket)

        await handler.send_transcription(
            session.session_id,
            "Hel",
            is_final=False,
        )

        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["data"]["is_final"] is False

    @pytest.mark.asyncio
    async def test_send_text_response(self, handler, manager, mock_websocket):
        """Test sending text response to client."""
        session = await manager.create_session(assistant_id="asst_123")
        manager.register_websocket(session.session_id, mock_websocket)

        await handler.send_text_response(
            session.session_id,
            "I'm doing well, thank you!"
        )

        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "text_response"
        assert call_args["data"] == "I'm doing well, thank you!"

    @pytest.mark.asyncio
    async def test_send_audio_chunk(self, handler, manager, mock_websocket):
        """Test sending audio chunk to client."""
        session = await manager.create_session(assistant_id="asst_123")
        manager.register_websocket(session.session_id, mock_websocket)

        await handler.send_audio_chunk(
            session.session_id,
            "SGVsbG8gV29ybGQ="  # Base64 "Hello World"
        )

        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "audio_chunk"
        assert call_args["data"] == "SGVsbG8gV29ybGQ="

    @pytest.mark.asyncio
    async def test_send_audio_complete(self, handler, manager, mock_websocket):
        """Test sending audio complete signal."""
        session = await manager.create_session(assistant_id="asst_123")
        manager.register_websocket(session.session_id, mock_websocket)

        await handler.send_audio_complete(
            session.session_id,
            {"duration_ms": 1500, "provider": "kokoro"}
        )

        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "audio_complete"
        assert call_args["data"]["duration_ms"] == 1500

    @pytest.mark.asyncio
    async def test_send_status(self, handler, manager, mock_websocket):
        """Test sending status update."""
        session = await manager.create_session(assistant_id="asst_123")
        manager.register_websocket(session.session_id, mock_websocket)

        await handler.send_status(session.session_id, "Processing...")

        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "status"
        assert call_args["data"] == "Processing..."

    @pytest.mark.asyncio
    async def test_send_error(self, handler, manager, mock_websocket):
        """Test sending error message."""
        session = await manager.create_session(assistant_id="asst_123")
        manager.register_websocket(session.session_id, mock_websocket)

        await handler.send_error(session.session_id, "Connection timeout")

        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "error"
        assert call_args["data"] == "Connection timeout"

    @pytest.mark.asyncio
    async def test_send_to_nonexistent_session(self, handler, manager):
        """Test sending to non-existent session doesn't raise."""
        # Should not raise, just log warning
        await handler.send_status("nonexistent", "test")

    @pytest.mark.asyncio
    async def test_handle_ice_candidate(self, manager):
        """Test handling ICE candidate via callback."""
        received_candidate = None

        async def on_ice_candidate(session_id, candidate):
            nonlocal received_candidate
            received_candidate = candidate

        handler = WebRTCSignalingHandler(
            manager=manager,
            on_ice_candidate=on_ice_candidate,
        )

        session = await manager.create_session(assistant_id="asst_123")

        # Simulate handling ICE candidate
        await handler._handle_ice_candidate(
            session.session_id,
            {
                "candidate": "candidate:1 1 UDP 2130706431 192.168.1.1 54321 typ host",
                "sdpMid": "audio",
                "sdpMLineIndex": 0,
            }
        )

        assert received_candidate is not None
        assert received_candidate.sdp_mid == "audio"

    @pytest.mark.asyncio
    async def test_handle_offer_with_callback(self, manager, mock_websocket):
        """Test handling offer with answer generation callback."""
        async def on_offer(session_id, offer):
            return "v=0\r\no=answer...\r\n"

        handler = WebRTCSignalingHandler(
            manager=manager,
            on_offer=on_offer,
        )

        session = await manager.create_session(assistant_id="asst_123")

        await handler._handle_offer(
            mock_websocket,
            session.session_id,
            {
                "sdp": "v=0\r\no=offer...\r\n",
                "type": "offer",
            }
        )

        # Should send answer back
        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "answer"
        assert "answer" in call_args["data"]["sdp"]

    @pytest.mark.asyncio
    async def test_handle_offer_without_callback(self, manager, mock_websocket):
        """Test handling offer without callback."""
        handler = WebRTCSignalingHandler(manager=manager)

        session = await manager.create_session(assistant_id="asst_123")

        await handler._handle_offer(
            mock_websocket,
            session.session_id,
            {
                "sdp": "v=0\r\no=offer...\r\n",
                "type": "offer",
            }
        )

        # Should send status acknowledgment
        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "status"

    @pytest.mark.asyncio
    async def test_handle_start_recording_callback(self, manager, mock_websocket):
        """Test start recording callback is triggered."""
        recording_started = False
        recording_session = None

        async def on_start_recording(session_id):
            nonlocal recording_started, recording_session
            recording_started = True
            recording_session = session_id

        handler = WebRTCSignalingHandler(
            manager=manager,
            on_start_recording=on_start_recording,
        )

        session = await manager.create_session(assistant_id="asst_123")

        await handler._handle_message(
            mock_websocket,
            session.session_id,
            {"type": "start_recording", "data": None}
        )

        assert recording_started
        assert recording_session == session.session_id

    @pytest.mark.asyncio
    async def test_handle_stop_recording_callback(self, manager, mock_websocket):
        """Test stop recording callback is triggered."""
        recording_stopped = False

        async def on_stop_recording(session_id):
            nonlocal recording_stopped
            recording_stopped = True

        handler = WebRTCSignalingHandler(
            manager=manager,
            on_stop_recording=on_stop_recording,
        )

        session = await manager.create_session(assistant_id="asst_123")

        await handler._handle_message(
            mock_websocket,
            session.session_id,
            {"type": "stop_recording", "data": None}
        )

        assert recording_stopped

    @pytest.mark.asyncio
    async def test_handle_barge_in_callback(self, manager, mock_websocket):
        """Test barge-in callback is triggered."""
        barge_in_triggered = False

        async def on_barge_in(session_id):
            nonlocal barge_in_triggered
            barge_in_triggered = True

        handler = WebRTCSignalingHandler(
            manager=manager,
            on_barge_in=on_barge_in,
        )

        session = await manager.create_session(assistant_id="asst_123")

        await handler._handle_message(
            mock_websocket,
            session.session_id,
            {"type": "barge_in", "data": "User interrupted"}
        )

        assert barge_in_triggered

    @pytest.mark.asyncio
    async def test_handle_text_message_callback(self, manager, mock_websocket):
        """Test text message callback is triggered."""
        received_text = None

        async def on_text_message(session_id, text):
            nonlocal received_text
            received_text = text

        handler = WebRTCSignalingHandler(
            manager=manager,
            on_text_message=on_text_message,
        )

        session = await manager.create_session(assistant_id="asst_123")

        await handler._handle_message(
            mock_websocket,
            session.session_id,
            {"type": "text", "data": "Hello, how are you?"}
        )

        assert received_text == "Hello, how are you?"

    @pytest.mark.asyncio
    async def test_handle_ping_pong(self, manager, mock_websocket):
        """Test ping/pong handling."""
        handler = WebRTCSignalingHandler(manager=manager)

        session = await manager.create_session(assistant_id="asst_123")

        await handler._handle_message(
            mock_websocket,
            session.session_id,
            {"type": "ping", "data": None}
        )

        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "pong"

    @pytest.mark.asyncio
    async def test_handle_unknown_message_type(self, manager, mock_websocket):
        """Test handling unknown message type."""
        handler = WebRTCSignalingHandler(manager=manager)

        session = await manager.create_session(assistant_id="asst_123")

        # Should not raise
        await handler._handle_message(
            mock_websocket,
            session.session_id,
            {"type": "unknown_type", "data": None}
        )

    @pytest.mark.asyncio
    async def test_session_activity_updated(self, manager, mock_websocket):
        """Test session activity is updated on message handling."""
        handler = WebRTCSignalingHandler(manager=manager)

        session = await manager.create_session(assistant_id="asst_123")
        original_activity = session.last_activity

        import time
        time.sleep(0.01)

        await handler._handle_message(
            mock_websocket,
            session.session_id,
            {"type": "ping", "data": None}
        )

        updated = manager.get_session(session.session_id)
        assert updated.last_activity > original_activity


class TestHandlerIntegration:
    """Integration tests for handler with full message flow."""

    @pytest.mark.asyncio
    async def test_full_offer_answer_flow(self, manager, mock_websocket):
        """Test complete offer-answer flow."""
        async def on_offer(session_id, offer):
            # Simulate generating SDP answer
            return f"v=0\r\no=- 1 1 IN IP4 127.0.0.1\r\nsession-id={session_id}\r\n"

        handler = WebRTCSignalingHandler(
            manager=manager,
            on_offer=on_offer,
        )

        session = await manager.create_session(assistant_id="asst_123")

        # Handle offer
        await handler._handle_offer(
            mock_websocket,
            session.session_id,
            {
                "sdp": "v=0\r\no=offer...",
                "type": "offer",
            }
        )

        # Verify session state
        updated = manager.get_session(session.session_id)
        assert updated.remote_sdp == "v=0\r\no=offer..."
        assert updated.local_sdp is not None
        assert session.session_id in updated.local_sdp

    @pytest.mark.asyncio
    async def test_multiple_audio_chunks(self, handler, manager, mock_websocket):
        """Test sending multiple audio chunks."""
        session = await manager.create_session(assistant_id="asst_123")
        manager.register_websocket(session.session_id, mock_websocket)

        # Send multiple chunks
        for i in range(3):
            await handler.send_audio_chunk(
                session.session_id,
                f"chunk_{i}_base64"
            )

        assert mock_websocket.send_json.call_count == 3

    @pytest.mark.asyncio
    async def test_conversation_flow(self, manager, mock_websocket):
        """Test simulated conversation flow."""
        transcriptions = []
        responses = []

        async def on_start_recording(session_id):
            pass

        async def on_stop_recording(session_id):
            # Simulate transcription result
            await handler.send_transcription(session_id, "Hello", is_final=True)

        async def on_text_message(session_id, text):
            # Simulate response
            await handler.send_text_response(session_id, f"You said: {text}")

        handler = WebRTCSignalingHandler(
            manager=manager,
            on_start_recording=on_start_recording,
            on_stop_recording=on_stop_recording,
            on_text_message=on_text_message,
        )

        session = await manager.create_session(assistant_id="asst_123")
        manager.register_websocket(session.session_id, mock_websocket)

        # Simulate recording flow
        await handler._handle_message(
            mock_websocket,
            session.session_id,
            {"type": "start_recording", "data": None}
        )

        await handler._handle_message(
            mock_websocket,
            session.session_id,
            {"type": "stop_recording", "data": None}
        )

        # Verify transcription was sent
        # (status for start + transcription for stop)
        assert mock_websocket.send_json.call_count >= 2
