"""
Tests for WebRTC signaling manager.

Tests session management and signaling coordination.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from apps.shared.webrtc.manager import (
    SignalingManager,
    get_signaling_manager,
)
from apps.shared.webrtc.models import (
    WebRTCSessionState,
    ICECandidate,
    SignalingMessage,
    SignalingMessageType,
    WebRTCOffer,
    WebRTCConfig,
)


@pytest_asyncio.fixture
async def manager():
    """Create a fresh signaling manager for each test."""
    return SignalingManager()


@pytest_asyncio.fixture
async def mock_websocket():
    """Create a mock WebSocket."""
    ws = AsyncMock()
    ws.send_json = AsyncMock()
    return ws


class TestSignalingManager:
    """Tests for SignalingManager class."""

    @pytest.mark.asyncio
    async def test_create_session(self, manager):
        """Test creating a WebRTC session."""
        session = await manager.create_session(
            assistant_id="asst_123",
            user_id="user_456",
            metadata={"language": "en"},
        )

        assert session.session_id is not None
        assert session.assistant_id == "asst_123"
        assert session.user_id == "user_456"
        assert session.state == WebRTCSessionState.NEW
        assert session.metadata["language"] == "en"
        assert manager.session_count == 1

    @pytest.mark.asyncio
    async def test_create_session_without_user(self, manager):
        """Test creating session without user ID."""
        session = await manager.create_session(
            assistant_id="asst_789",
        )

        assert session.user_id is None
        assert manager.session_count == 1

    @pytest.mark.asyncio
    async def test_process_offer(self, manager):
        """Test processing an SDP offer."""
        offer = WebRTCOffer(
            sdp="v=0\r\no=- 123 456 IN IP4 127.0.0.1\r\n",
            assistant_id="asst_123",
            user_id="user_456",
        )

        answer = await manager.process_offer(offer)

        assert answer.session_id is not None
        assert answer.type == "answer"
        assert answer.ice_servers is not None

        # Verify session was created
        session = manager.get_session(answer.session_id)
        assert session is not None
        assert session.remote_sdp == offer.sdp
        assert session.state == WebRTCSessionState.CONNECTING

    @pytest.mark.asyncio
    async def test_process_offer_existing_session(self, manager):
        """Test processing offer with existing session ID."""
        # Create session first
        session = await manager.create_session(assistant_id="asst_123")

        offer = WebRTCOffer(
            sdp="v=0...",
            assistant_id="asst_123",
            session_id=session.session_id,
        )

        answer = await manager.process_offer(offer)

        # Should use existing session
        assert answer.session_id == session.session_id
        assert manager.session_count == 1

    @pytest.mark.asyncio
    async def test_set_local_description(self, manager):
        """Test setting local SDP description."""
        session = await manager.create_session(assistant_id="asst_123")

        await manager.set_local_description(
            session.session_id,
            "v=0\r\no=local...\r\n"
        )

        updated = manager.get_session(session.session_id)
        assert updated.local_sdp == "v=0\r\no=local...\r\n"

    @pytest.mark.asyncio
    async def test_add_ice_candidate(self, manager):
        """Test adding ICE candidate."""
        session = await manager.create_session(assistant_id="asst_123")

        candidate = ICECandidate(
            candidate="candidate:1 1 UDP 2130706431 192.168.1.1 54321 typ host",
            sdp_mid="audio",
            sdp_mline_index=0,
        )

        await manager.add_ice_candidate(session.session_id, candidate)

        updated = manager.get_session(session.session_id)
        assert len(updated.ice_candidates) == 1
        assert updated.ice_candidates[0].sdp_mid == "audio"

    @pytest.mark.asyncio
    async def test_mark_connected(self, manager):
        """Test marking session as connected."""
        session = await manager.create_session(assistant_id="asst_123")

        await manager.mark_connected(session.session_id)

        updated = manager.get_session(session.session_id)
        assert updated.state == WebRTCSessionState.CONNECTED
        assert updated.connected_at is not None

    @pytest.mark.asyncio
    async def test_mark_connected_with_callback(self, manager):
        """Test mark connected triggers callback."""
        callback_called = False
        callback_session = None

        async def on_connected(session):
            nonlocal callback_called, callback_session
            callback_called = True
            callback_session = session

        manager.set_callbacks(on_connected=on_connected)
        session = await manager.create_session(assistant_id="asst_123")
        await manager.mark_connected(session.session_id)

        assert callback_called
        assert callback_session.session_id == session.session_id

    @pytest.mark.asyncio
    async def test_update_ice_state_connected(self, manager):
        """Test ICE state update to connected."""
        session = await manager.create_session(assistant_id="asst_123")

        await manager.update_ice_state(session.session_id, "connected")

        updated = manager.get_session(session.session_id)
        assert updated.ice_connection_state == "connected"
        assert updated.state == WebRTCSessionState.CONNECTED

    @pytest.mark.asyncio
    async def test_update_ice_state_failed(self, manager):
        """Test ICE state update to failed."""
        session = await manager.create_session(assistant_id="asst_123")

        await manager.update_ice_state(session.session_id, "failed")

        updated = manager.get_session(session.session_id)
        assert updated.state == WebRTCSessionState.FAILED

    @pytest.mark.asyncio
    async def test_close_session(self, manager):
        """Test closing a session."""
        session = await manager.create_session(
            assistant_id="asst_123",
            user_id="user_456",
        )
        await manager.mark_connected(session.session_id)

        await manager.close_session(session.session_id)

        updated = manager.get_session(session.session_id)
        assert updated.state == WebRTCSessionState.CLOSED

    @pytest.mark.asyncio
    async def test_close_session_with_callback(self, manager):
        """Test close session triggers callback."""
        callback_called = False

        async def on_closed(session):
            nonlocal callback_called
            callback_called = True

        manager.set_callbacks(on_closed=on_closed)
        session = await manager.create_session(assistant_id="asst_123")
        await manager.close_session(session.session_id)

        assert callback_called

    @pytest.mark.asyncio
    async def test_cleanup_session(self, manager):
        """Test fully removing a session."""
        session = await manager.create_session(assistant_id="asst_123")

        await manager.cleanup_session(session.session_id)

        assert manager.get_session(session.session_id) is None
        assert manager.session_count == 0

    @pytest.mark.asyncio
    async def test_register_websocket(self, manager, mock_websocket):
        """Test registering a WebSocket."""
        session = await manager.create_session(assistant_id="asst_123")

        manager.register_websocket(session.session_id, mock_websocket)

        # No direct way to check, but send_to_session should work
        message = SignalingMessage(type=SignalingMessageType.PING, data=None)
        result = await manager.send_to_session(session.session_id, message)

        assert result is True
        mock_websocket.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_unregister_websocket(self, manager, mock_websocket):
        """Test unregistering a WebSocket."""
        session = await manager.create_session(assistant_id="asst_123")
        manager.register_websocket(session.session_id, mock_websocket)
        manager.unregister_websocket(session.session_id)

        message = SignalingMessage(type=SignalingMessageType.PING, data=None)
        result = await manager.send_to_session(session.session_id, message)

        assert result is False

    @pytest.mark.asyncio
    async def test_send_to_session_not_found(self, manager):
        """Test sending to non-existent session."""
        message = SignalingMessage(type=SignalingMessageType.PING, data=None)
        result = await manager.send_to_session("nonexistent", message)

        assert result is False

    @pytest.mark.asyncio
    async def test_broadcast_to_assistant(self, manager):
        """Test broadcasting to assistant sessions."""
        ws1 = AsyncMock()
        ws1.send_json = AsyncMock()
        ws2 = AsyncMock()
        ws2.send_json = AsyncMock()

        session1 = await manager.create_session(assistant_id="asst_123")
        session2 = await manager.create_session(assistant_id="asst_123")

        manager.register_websocket(session1.session_id, ws1)
        manager.register_websocket(session2.session_id, ws2)

        message = SignalingMessage(type=SignalingMessageType.STATUS, data="Hello")
        await manager.broadcast_to_assistant("asst_123", message)

        ws1.send_json.assert_called()
        ws2.send_json.assert_called()

    @pytest.mark.asyncio
    async def test_broadcast_with_exclude(self, manager):
        """Test broadcasting with exclusion."""
        ws1 = AsyncMock()
        ws1.send_json = AsyncMock()
        ws2 = AsyncMock()
        ws2.send_json = AsyncMock()

        session1 = await manager.create_session(assistant_id="asst_123")
        session2 = await manager.create_session(assistant_id="asst_123")

        manager.register_websocket(session1.session_id, ws1)
        manager.register_websocket(session2.session_id, ws2)

        message = SignalingMessage(type=SignalingMessageType.STATUS, data="Hello")
        await manager.broadcast_to_assistant(
            "asst_123",
            message,
            exclude={session1.session_id}
        )

        ws1.send_json.assert_not_called()
        ws2.send_json.assert_called()

    @pytest.mark.asyncio
    async def test_get_sessions_by_assistant(self, manager):
        """Test getting sessions by assistant."""
        await manager.create_session(assistant_id="asst_A")
        await manager.create_session(assistant_id="asst_A")
        await manager.create_session(assistant_id="asst_B")

        sessions = manager.get_sessions_by_assistant("asst_A")

        assert len(sessions) == 2
        assert all(s.assistant_id == "asst_A" for s in sessions)

    @pytest.mark.asyncio
    async def test_get_sessions_by_user(self, manager):
        """Test getting sessions by user."""
        await manager.create_session(
            assistant_id="asst_123",
            user_id="user_A"
        )
        await manager.create_session(
            assistant_id="asst_456",
            user_id="user_A"
        )
        await manager.create_session(
            assistant_id="asst_789",
            user_id="user_B"
        )

        sessions = manager.get_sessions_by_user("user_A")

        assert len(sessions) == 2
        assert all(s.user_id == "user_A" for s in sessions)

    @pytest.mark.asyncio
    async def test_get_active_sessions(self, manager):
        """Test getting active sessions."""
        session1 = await manager.create_session(assistant_id="asst_123")
        session2 = await manager.create_session(assistant_id="asst_456")

        await manager.mark_connected(session1.session_id)
        # session2 stays in NEW state

        active = manager.get_active_sessions()

        assert len(active) == 1
        assert active[0].session_id == session1.session_id

    @pytest.mark.asyncio
    async def test_session_count(self, manager):
        """Test session count property."""
        assert manager.session_count == 0

        await manager.create_session(assistant_id="asst_1")
        assert manager.session_count == 1

        await manager.create_session(assistant_id="asst_2")
        assert manager.session_count == 2

    @pytest.mark.asyncio
    async def test_active_session_count(self, manager):
        """Test active session count property."""
        session1 = await manager.create_session(assistant_id="asst_1")
        session2 = await manager.create_session(assistant_id="asst_2")

        assert manager.active_session_count == 0

        await manager.mark_connected(session1.session_id)
        assert manager.active_session_count == 1

        await manager.mark_connected(session2.session_id)
        assert manager.active_session_count == 2

    @pytest.mark.asyncio
    async def test_update_stats(self, manager):
        """Test updating session statistics."""
        session = await manager.create_session(assistant_id="asst_123")

        manager.update_stats(
            session.session_id,
            bytes_sent=1000,
            bytes_received=2000,
            packets_sent=10,
            packets_received=20,
        )

        updated = manager.get_session(session.session_id)
        assert updated.bytes_sent == 1000
        assert updated.bytes_received == 2000
        assert updated.packets_sent == 10
        assert updated.packets_received == 20

    @pytest.mark.asyncio
    async def test_update_stats_cumulative(self, manager):
        """Test stats accumulate over multiple updates."""
        session = await manager.create_session(assistant_id="asst_123")

        manager.update_stats(session.session_id, bytes_sent=100)
        manager.update_stats(session.session_id, bytes_sent=200)

        updated = manager.get_session(session.session_id)
        assert updated.bytes_sent == 300

    @pytest.mark.asyncio
    async def test_custom_config(self):
        """Test manager with custom config."""
        config = WebRTCConfig(
            ice_servers=[{"urls": "turn:turn.example.com"}],
            ice_gathering_timeout_ms=10000,
        )
        manager = SignalingManager(config=config)

        assert len(manager.config.ice_servers) == 1
        assert manager.config.ice_gathering_timeout_ms == 10000


class TestGlobalManager:
    """Tests for global manager singleton."""

    def test_get_signaling_manager_singleton(self):
        """Test that get_signaling_manager returns singleton."""
        # Reset global manager
        import apps.shared.webrtc.manager as manager_module
        manager_module._manager = None

        manager1 = get_signaling_manager()
        manager2 = get_signaling_manager()

        assert manager1 is manager2
