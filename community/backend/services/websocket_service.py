"""
WebSocket service for African Language Community Platform.

Handles real-time communication for collaborative features.
"""

from typing import Dict, List, Set
from fastapi import WebSocket
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manager for WebSocket connections and real-time communication.

    Handles connection management, message broadcasting, and room-based communication.
    """

    def __init__(self):
        """Initialize WebSocket manager."""
        # Store active connections by user ID
        self.active_connections: Dict[str, WebSocket] = {}

        # Store connections by room/channel
        self.rooms: Dict[str, Set[str]] = {}

        # Store user information for connections
        self.user_info: Dict[str, Dict] = {}

    async def connect(self, websocket: WebSocket, user_id: str, user_info: Dict = None):
        """
        Connect a new WebSocket client.

        Args:
            websocket: WebSocket connection
            user_id: User ID
            user_info: Optional user information
        """
        await websocket.accept()

        # Disconnect existing connection for this user
        if user_id in self.active_connections:
            await self.disconnect(user_id)

        self.active_connections[user_id] = websocket
        self.user_info[user_id] = user_info or {}

        logger.info(f"WebSocket connected for user: {user_id}")

        # Send connection confirmation
        await self.send_personal_message(user_id, {
            "type": "connection_established",
            "message": "Connected to African Language Community Platform",
            "timestamp": datetime.utcnow().isoformat()
        })

    async def disconnect(self, user_id: str):
        """
        Disconnect a WebSocket client.

        Args:
            user_id: User ID to disconnect
        """
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]

            try:
                await websocket.close()
            except Exception as e:
                logger.warning(f"Error closing WebSocket for user {user_id}: {str(e)}")

            # Remove from active connections
            del self.active_connections[user_id]

            # Remove from all rooms
            for room_id in list(self.rooms.keys()):
                if user_id in self.rooms[room_id]:
                    await self.leave_room(user_id, room_id)

            # Remove user info
            if user_id in self.user_info:
                del self.user_info[user_id]

            logger.info(f"WebSocket disconnected for user: {user_id}")

    async def send_personal_message(self, user_id: str, message: Dict):
        """
        Send message to specific user.

        Args:
            user_id: Target user ID
            message: Message to send
        """
        if user_id in self.active_connections:
            try:
                websocket = self.active_connections[user_id]
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {str(e)}")
                # Remove broken connection
                await self.disconnect(user_id)

    async def broadcast_message(self, message: Dict, exclude_user: str = None):
        """
        Broadcast message to all connected users.

        Args:
            message: Message to broadcast
            exclude_user: Optional user ID to exclude from broadcast
        """
        disconnected_users = []

        for user_id, websocket in self.active_connections.items():
            if exclude_user and user_id == exclude_user:
                continue

            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting to user {user_id}: {str(e)}")
                disconnected_users.append(user_id)

        # Clean up broken connections
        for user_id in disconnected_users:
            await self.disconnect(user_id)

    async def join_room(self, user_id: str, room_id: str):
        """
        Add user to a room for targeted messaging.

        Args:
            user_id: User ID
            room_id: Room/channel ID
        """
        if room_id not in self.rooms:
            self.rooms[room_id] = set()

        self.rooms[room_id].add(user_id)

        # Notify user they joined the room
        await self.send_personal_message(user_id, {
            "type": "room_joined",
            "room_id": room_id,
            "message": f"Joined room: {room_id}",
            "timestamp": datetime.utcnow().isoformat()
        })

        # Notify other room members
        await self.broadcast_to_room(room_id, {
            "type": "user_joined_room",
            "user_id": user_id,
            "user_info": self.user_info.get(user_id, {}),
            "room_id": room_id,
            "timestamp": datetime.utcnow().isoformat()
        }, exclude_user=user_id)

        logger.info(f"User {user_id} joined room: {room_id}")

    async def leave_room(self, user_id: str, room_id: str):
        """
        Remove user from a room.

        Args:
            user_id: User ID
            room_id: Room/channel ID
        """
        if room_id in self.rooms and user_id in self.rooms[room_id]:
            self.rooms[room_id].remove(user_id)

            # Remove empty rooms
            if not self.rooms[room_id]:
                del self.rooms[room_id]
            else:
                # Notify other room members
                await self.broadcast_to_room(room_id, {
                    "type": "user_left_room",
                    "user_id": user_id,
                    "room_id": room_id,
                    "timestamp": datetime.utcnow().isoformat()
                })

            # Notify user they left the room
            await self.send_personal_message(user_id, {
                "type": "room_left",
                "room_id": room_id,
                "message": f"Left room: {room_id}",
                "timestamp": datetime.utcnow().isoformat()
            })

            logger.info(f"User {user_id} left room: {room_id}")

    async def broadcast_to_room(self, room_id: str, message: Dict, exclude_user: str = None):
        """
        Broadcast message to all users in a specific room.

        Args:
            room_id: Target room ID
            message: Message to broadcast
            exclude_user: Optional user ID to exclude from broadcast
        """
        if room_id not in self.rooms:
            return

        disconnected_users = []

        for user_id in self.rooms[room_id]:
            if exclude_user and user_id == exclude_user:
                continue

            if user_id in self.active_connections:
                try:
                    websocket = self.active_connections[user_id]
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error broadcasting to user {user_id} in room {room_id}: {str(e)}")
                    disconnected_users.append(user_id)

        # Clean up broken connections
        for user_id in disconnected_users:
            await self.disconnect(user_id)

    async def handle_message(self, user_id: str, message: Dict):
        """
        Handle incoming WebSocket message from user.

        Args:
            user_id: Sender user ID
            message: Received message
        """
        try:
            message_type = message.get("type")

            if message_type == "join_room":
                room_id = message.get("room_id")
                if room_id:
                    await self.join_room(user_id, room_id)

            elif message_type == "leave_room":
                room_id = message.get("room_id")
                if room_id:
                    await self.leave_room(user_id, room_id)

            elif message_type == "room_message":
                room_id = message.get("room_id")
                content = message.get("content")
                if room_id and content:
                    await self.broadcast_to_room(room_id, {
                        "type": "room_message",
                        "room_id": room_id,
                        "sender_id": user_id,
                        "sender_info": self.user_info.get(user_id, {}),
                        "content": content,
                        "timestamp": datetime.utcnow().isoformat()
                    }, exclude_user=user_id)

            elif message_type == "direct_message":
                target_user_id = message.get("target_user_id")
                content = message.get("content")
                if target_user_id and content:
                    await self.send_personal_message(target_user_id, {
                        "type": "direct_message",
                        "sender_id": user_id,
                        "sender_info": self.user_info.get(user_id, {}),
                        "content": content,
                        "timestamp": datetime.utcnow().isoformat()
                    })

            elif message_type == "ping":
                await self.send_personal_message(user_id, {
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })

            else:
                logger.warning(f"Unknown message type from user {user_id}: {message_type}")

        except Exception as e:
            logger.error(f"Error handling message from user {user_id}: {str(e)}")

    async def notify_submission_update(self, submission_id: str, submission_type: str, update_type: str, data: Dict = None):
        """
        Notify users about submission updates.

        Args:
            submission_id: Submission ID
            submission_type: Type of submission
            update_type: Type of update (created, validated, approved, etc.)
            data: Additional data
        """
        message = {
            "type": "submission_update",
            "submission_id": submission_id,
            "submission_type": submission_type,
            "update_type": update_type,
            "data": data or {},
            "timestamp": datetime.utcnow().isoformat()
        }

        await self.broadcast_message(message)

    async def notify_validation_update(self, validation_data: Dict):
        """
        Notify users about validation updates.

        Args:
            validation_data: Validation data
        """
        message = {
            "type": "validation_update",
            "data": validation_data,
            "timestamp": datetime.utcnow().isoformat()
        }

        await self.broadcast_message(message)

    async def notify_achievement_earned(self, user_id: str, achievement_data: Dict):
        """
        Notify user about earned achievement.

        Args:
            user_id: User who earned achievement
            achievement_data: Achievement data
        """
        message = {
            "type": "achievement_earned",
            "achievement": achievement_data,
            "timestamp": datetime.utcnow().isoformat()
        }

        await self.send_personal_message(user_id, message)

    def get_room_users(self, room_id: str) -> List[str]:
        """
        Get list of users in a room.

        Args:
            room_id: Room ID

        Returns:
            List[str]: List of user IDs in the room
        """
        return list(self.rooms.get(room_id, set()))

    def get_active_users(self) -> List[str]:
        """
        Get list of all active users.

        Returns:
            List[str]: List of active user IDs
        """
        return list(self.active_connections.keys())

    def get_room_count(self) -> int:
        """
        Get number of active rooms.

        Returns:
            int: Number of active rooms
        """
        return len(self.rooms)

    def get_connection_count(self) -> int:
        """
        Get number of active connections.

        Returns:
            int: Number of active connections
        """
        return len(self.active_connections)