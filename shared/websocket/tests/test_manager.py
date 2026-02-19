"""
Tests for WebSocket manager.

Tests connection management and broadcasting.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from apps.shared.websocket.manager import (
    WebSocketManager,
    get_websocket_manager,
)
from apps.shared.websocket.models import (
    WebSocketMessage,
    WebSocketStatus,
)


@pytest_asyncio.fixture
async def manager():
    """Create a fresh WebSocket manager for each test."""
    return WebSocketManager()


@pytest_asyncio.fixture
async def mock_websocket():
    """Create a mock WebSocket."""
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    ws.close = AsyncMock()
    return ws


class TestWebSocketManager:
    """Tests for WebSocketManager class."""

    @pytest.mark.asyncio
    async def test_connect(self, manager, mock_websocket):
        """Test connecting a WebSocket."""
        info = await manager.connect(
            websocket=mock_websocket,
            connection_id="conn_123",
            user_id="user_456",
            assistant_id="asst_789",
        )

        assert info.connection_id == "conn_123"
        assert info.user_id == "user_456"
        assert info.assistant_id == "asst_789"
        assert info.status == WebSocketStatus.CONNECTED
        assert manager.connection_count == 1
        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect(self, manager, mock_websocket):
        """Test disconnecting a WebSocket."""
        await manager.connect(
            websocket=mock_websocket,
            connection_id="conn_123",
        )

        await manager.disconnect("conn_123")

        assert manager.connection_count == 0
        assert manager.get_connection("conn_123") is None

    @pytest.mark.asyncio
    async def test_send_message(self, manager, mock_websocket):
        """Test sending a message."""
        await manager.connect(
            websocket=mock_websocket,
            connection_id="conn_123",
        )

        msg = WebSocketMessage(type="test", data="hello")
        result = await manager.send_message("conn_123", msg)

        assert result is True
        mock_websocket.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_not_connected(self, manager):
        """Test sending message to non-existent connection."""
        msg = WebSocketMessage(type="test")
        result = await manager.send_message("nonexistent", msg)

        assert result is False

    @pytest.mark.asyncio
    async def test_send_json(self, manager, mock_websocket):
        """Test sending raw JSON."""
        await manager.connect(
            websocket=mock_websocket,
            connection_id="conn_123",
        )

        result = await manager.send_json("conn_123", {"type": "ping"})

        assert result is True
        mock_websocket.send_json.assert_called_with({"type": "ping"})

    @pytest.mark.asyncio
    async def test_broadcast(self, manager):
        """Test broadcasting to all connections."""
        ws1 = AsyncMock()
        ws1.accept = AsyncMock()
        ws1.send_json = AsyncMock()

        ws2 = AsyncMock()
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock()

        await manager.connect(ws1, "conn_1")
        await manager.connect(ws2, "conn_2")

        msg = WebSocketMessage(type="broadcast", data="hello all")
        await manager.broadcast(msg)

        ws1.send_json.assert_called()
        ws2.send_json.assert_called()

    @pytest.mark.asyncio
    async def test_broadcast_with_exclude(self, manager):
        """Test broadcasting with exclusion."""
        ws1 = AsyncMock()
        ws1.accept = AsyncMock()
        ws1.send_json = AsyncMock()

        ws2 = AsyncMock()
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock()

        await manager.connect(ws1, "conn_1")
        await manager.connect(ws2, "conn_2")

        msg = WebSocketMessage(type="broadcast")
        await manager.broadcast(msg, exclude={"conn_1"})

        ws1.send_json.assert_not_called()
        ws2.send_json.assert_called()

    @pytest.mark.asyncio
    async def test_groups(self, manager, mock_websocket):
        """Test group management."""
        await manager.connect(mock_websocket, "conn_1")

        await manager.join_group("conn_1", "room_1")

        # Verify connection is in group (indirect test via broadcast)
        ws2 = AsyncMock()
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock()
        await manager.connect(ws2, "conn_2")

        msg = WebSocketMessage(type="group_msg")
        await manager.broadcast_to_group("room_1", msg)

        mock_websocket.send_json.assert_called()
        ws2.send_json.assert_not_called()  # Not in group

    @pytest.mark.asyncio
    async def test_leave_group(self, manager, mock_websocket):
        """Test leaving a group."""
        await manager.connect(mock_websocket, "conn_1")
        await manager.join_group("conn_1", "room_1")
        await manager.leave_group("conn_1", "room_1")

        msg = WebSocketMessage(type="test")
        await manager.broadcast_to_group("room_1", msg)

        # Should not receive message after leaving
        mock_websocket.send_json.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_connection(self, manager, mock_websocket):
        """Test getting a connection."""
        await manager.connect(mock_websocket, "conn_123")

        ws = manager.get_connection("conn_123")
        assert ws is mock_websocket

        ws_none = manager.get_connection("nonexistent")
        assert ws_none is None

    @pytest.mark.asyncio
    async def test_get_connection_info(self, manager, mock_websocket):
        """Test getting connection info."""
        await manager.connect(
            mock_websocket,
            "conn_123",
            user_id="user_456",
        )

        info = manager.get_connection_info("conn_123")
        assert info is not None
        assert info.user_id == "user_456"

    @pytest.mark.asyncio
    async def test_get_connections_by_user(self, manager):
        """Test getting connections by user."""
        ws1 = AsyncMock()
        ws1.accept = AsyncMock()
        ws2 = AsyncMock()
        ws2.accept = AsyncMock()

        await manager.connect(ws1, "conn_1", user_id="user_A")
        await manager.connect(ws2, "conn_2", user_id="user_A")

        connections = manager.get_connections_by_user("user_A")
        assert len(connections) == 2
        assert "conn_1" in connections
        assert "conn_2" in connections

    @pytest.mark.asyncio
    async def test_get_connections_by_assistant(self, manager):
        """Test getting connections by assistant."""
        ws1 = AsyncMock()
        ws1.accept = AsyncMock()

        await manager.connect(
            ws1,
            "conn_1",
            assistant_id="asst_X",
        )

        connections = manager.get_connections_by_assistant("asst_X")
        assert len(connections) == 1
        assert "conn_1" in connections

    @pytest.mark.asyncio
    async def test_update_status(self, manager, mock_websocket):
        """Test updating connection status."""
        await manager.connect(mock_websocket, "conn_123")

        await manager.update_status("conn_123", WebSocketStatus.PROCESSING)

        info = manager.get_connection_info("conn_123")
        assert info.status == WebSocketStatus.PROCESSING

    @pytest.mark.asyncio
    async def test_connection_count(self, manager):
        """Test connection count property."""
        ws1 = AsyncMock()
        ws1.accept = AsyncMock()
        ws2 = AsyncMock()
        ws2.accept = AsyncMock()

        assert manager.connection_count == 0

        await manager.connect(ws1, "conn_1")
        assert manager.connection_count == 1

        await manager.connect(ws2, "conn_2")
        assert manager.connection_count == 2

        await manager.disconnect("conn_1")
        assert manager.connection_count == 1

    @pytest.mark.asyncio
    async def test_active_connections(self, manager):
        """Test active connections property."""
        ws1 = AsyncMock()
        ws1.accept = AsyncMock()
        ws2 = AsyncMock()
        ws2.accept = AsyncMock()

        await manager.connect(ws1, "conn_1")
        await manager.connect(ws2, "conn_2")

        active = manager.active_connections
        assert "conn_1" in active
        assert "conn_2" in active


class TestGlobalManager:
    """Tests for global manager singleton."""

    def test_get_websocket_manager_singleton(self):
        """Test that get_websocket_manager returns singleton."""
        # Reset global manager
        import apps.shared.websocket.manager as manager_module
        manager_module._manager = None

        manager1 = get_websocket_manager()
        manager2 = get_websocket_manager()

        assert manager1 is manager2
