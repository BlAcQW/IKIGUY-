"""
WebSocket Connection Manager

Manages WebSocket connections across the application.
Tracks active connections and provides broadcasting capabilities.

Author: KasaAI Team
Date: 2025-11-26
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from fastapi import WebSocket

from .models import ConnectionInfo, WebSocketMessage, WebSocketStatus

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections.

    Provides connection tracking, broadcasting, and cleanup.
    Thread-safe for concurrent access.
    """

    def __init__(self):
        """Initialize the manager."""
        # Active connections: connection_id -> WebSocket
        self._connections: Dict[str, WebSocket] = {}
        # Connection info: connection_id -> ConnectionInfo
        self._connection_info: Dict[str, ConnectionInfo] = {}
        # Group memberships: group_name -> set of connection_ids
        self._groups: Dict[str, Set[str]] = {}
        # Lock for thread safety
        self._lock = asyncio.Lock()

    async def connect(
        self,
        websocket: WebSocket,
        connection_id: str,
        user_id: Optional[str] = None,
        assistant_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConnectionInfo:
        """
        Register a new WebSocket connection.

        Args:
            websocket: WebSocket connection
            connection_id: Unique connection identifier
            user_id: Optional user ID
            assistant_id: Optional assistant ID
            metadata: Optional additional metadata

        Returns:
            ConnectionInfo for the new connection
        """
        async with self._lock:
            # Accept the connection
            await websocket.accept()

            # Create connection info
            info = ConnectionInfo(
                connection_id=connection_id,
                user_id=user_id,
                assistant_id=assistant_id,
                status=WebSocketStatus.CONNECTED,
                metadata=metadata or {},
            )

            # Store connection
            self._connections[connection_id] = websocket
            self._connection_info[connection_id] = info

            logger.info(f"WebSocket connected: {connection_id}")
            return info

    async def disconnect(self, connection_id: str):
        """
        Disconnect and cleanup a WebSocket connection.

        Args:
            connection_id: Connection to disconnect
        """
        async with self._lock:
            # Remove from groups
            for group_members in self._groups.values():
                group_members.discard(connection_id)

            # Remove connection
            if connection_id in self._connections:
                del self._connections[connection_id]

            if connection_id in self._connection_info:
                self._connection_info[connection_id].status = WebSocketStatus.DISCONNECTED
                del self._connection_info[connection_id]

            logger.info(f"WebSocket disconnected: {connection_id}")

    async def send_message(
        self,
        connection_id: str,
        message: WebSocketMessage,
    ) -> bool:
        """
        Send a message to a specific connection.

        Args:
            connection_id: Target connection
            message: Message to send

        Returns:
            True if sent successfully, False otherwise
        """
        websocket = self._connections.get(connection_id)
        if not websocket:
            logger.warning(f"Connection not found: {connection_id}")
            return False

        try:
            await websocket.send_json(message.to_dict())

            # Update stats
            if connection_id in self._connection_info:
                self._connection_info[connection_id].increment_message_count()

            return True

        except Exception as e:
            logger.error(f"Error sending message to {connection_id}: {e}")
            return False

    async def send_json(
        self,
        connection_id: str,
        data: Dict[str, Any],
    ) -> bool:
        """
        Send raw JSON data to a connection.

        Args:
            connection_id: Target connection
            data: JSON data to send

        Returns:
            True if sent successfully
        """
        websocket = self._connections.get(connection_id)
        if not websocket:
            return False

        try:
            await websocket.send_json(data)
            return True
        except Exception as e:
            logger.error(f"Error sending JSON to {connection_id}: {e}")
            return False

    async def broadcast(
        self,
        message: WebSocketMessage,
        exclude: Optional[Set[str]] = None,
    ):
        """
        Broadcast a message to all connections.

        Args:
            message: Message to broadcast
            exclude: Optional set of connection IDs to exclude
        """
        exclude = exclude or set()
        tasks = []

        for conn_id in self._connections:
            if conn_id not in exclude:
                tasks.append(self.send_message(conn_id, message))

        await asyncio.gather(*tasks, return_exceptions=True)

    async def broadcast_to_group(
        self,
        group_name: str,
        message: WebSocketMessage,
        exclude: Optional[Set[str]] = None,
    ):
        """
        Broadcast a message to a group of connections.

        Args:
            group_name: Target group
            message: Message to broadcast
            exclude: Optional set of connection IDs to exclude
        """
        exclude = exclude or set()
        group_members = self._groups.get(group_name, set())

        tasks = []
        for conn_id in group_members:
            if conn_id not in exclude:
                tasks.append(self.send_message(conn_id, message))

        await asyncio.gather(*tasks, return_exceptions=True)

    async def join_group(self, connection_id: str, group_name: str):
        """
        Add a connection to a group.

        Args:
            connection_id: Connection to add
            group_name: Target group
        """
        async with self._lock:
            if group_name not in self._groups:
                self._groups[group_name] = set()
            self._groups[group_name].add(connection_id)

    async def leave_group(self, connection_id: str, group_name: str):
        """
        Remove a connection from a group.

        Args:
            connection_id: Connection to remove
            group_name: Target group
        """
        async with self._lock:
            if group_name in self._groups:
                self._groups[group_name].discard(connection_id)

    def get_connection(self, connection_id: str) -> Optional[WebSocket]:
        """
        Get a WebSocket connection by ID.

        Args:
            connection_id: Connection ID

        Returns:
            WebSocket or None
        """
        return self._connections.get(connection_id)

    def get_connection_info(self, connection_id: str) -> Optional[ConnectionInfo]:
        """
        Get connection info by ID.

        Args:
            connection_id: Connection ID

        Returns:
            ConnectionInfo or None
        """
        return self._connection_info.get(connection_id)

    def get_connections_by_user(self, user_id: str) -> List[str]:
        """
        Get all connections for a user.

        Args:
            user_id: User ID

        Returns:
            List of connection IDs
        """
        return [
            conn_id
            for conn_id, info in self._connection_info.items()
            if info.user_id == user_id
        ]

    def get_connections_by_assistant(self, assistant_id: str) -> List[str]:
        """
        Get all connections for an assistant.

        Args:
            assistant_id: Assistant ID

        Returns:
            List of connection IDs
        """
        return [
            conn_id
            for conn_id, info in self._connection_info.items()
            if info.assistant_id == assistant_id
        ]

    @property
    def connection_count(self) -> int:
        """Get total number of active connections."""
        return len(self._connections)

    @property
    def active_connections(self) -> List[str]:
        """Get list of active connection IDs."""
        return list(self._connections.keys())

    async def update_status(
        self,
        connection_id: str,
        status: WebSocketStatus,
    ):
        """
        Update connection status.

        Args:
            connection_id: Connection to update
            status: New status
        """
        if connection_id in self._connection_info:
            self._connection_info[connection_id].status = status
            self._connection_info[connection_id].update_activity()


# Global manager instance
_manager: Optional[WebSocketManager] = None


def get_websocket_manager() -> WebSocketManager:
    """
    Get the global WebSocket manager instance.

    Returns:
        WebSocketManager singleton
    """
    global _manager
    if _manager is None:
        _manager = WebSocketManager()
    return _manager
