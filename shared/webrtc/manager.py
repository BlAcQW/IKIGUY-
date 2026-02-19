"""
WebRTC Signaling Manager

Manages WebRTC peer connections, SDP exchange, and ICE candidates.

Author: KasaAI Team
Date: 2025-11-26
"""

import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, List, Set, Any, Callable, Awaitable
from fastapi import WebSocket

from .models import (
    WebRTCSessionInfo,
    WebRTCSessionState,
    ICECandidate,
    SignalingMessage,
    SignalingMessageType,
    WebRTCConfig,
    WebRTCOffer,
    WebRTCAnswer,
)

logger = logging.getLogger(__name__)


class SignalingManager:
    """
    Manages WebRTC signaling for peer connections.

    Handles:
    - Session creation and lifecycle
    - SDP offer/answer exchange
    - ICE candidate gathering and exchange
    - Connection state tracking
    """

    def __init__(self, config: Optional[WebRTCConfig] = None):
        """
        Initialize signaling manager.

        Args:
            config: WebRTC configuration
        """
        self.config = config or WebRTCConfig()
        self._sessions: Dict[str, WebRTCSessionInfo] = {}
        self._websockets: Dict[str, WebSocket] = {}
        self._assistant_sessions: Dict[str, Set[str]] = {}  # assistant_id -> session_ids
        self._user_sessions: Dict[str, Set[str]] = {}  # user_id -> session_ids

        # Callbacks for session events
        self._on_session_created: Optional[Callable[[WebRTCSessionInfo], Awaitable[None]]] = None
        self._on_session_connected: Optional[Callable[[WebRTCSessionInfo], Awaitable[None]]] = None
        self._on_session_closed: Optional[Callable[[WebRTCSessionInfo], Awaitable[None]]] = None

    def set_callbacks(
        self,
        on_created: Optional[Callable[[WebRTCSessionInfo], Awaitable[None]]] = None,
        on_connected: Optional[Callable[[WebRTCSessionInfo], Awaitable[None]]] = None,
        on_closed: Optional[Callable[[WebRTCSessionInfo], Awaitable[None]]] = None,
    ):
        """
        Set callbacks for session lifecycle events.

        Args:
            on_created: Called when session is created
            on_connected: Called when session connects
            on_closed: Called when session closes
        """
        self._on_session_created = on_created
        self._on_session_connected = on_connected
        self._on_session_closed = on_closed

    async def create_session(
        self,
        assistant_id: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WebRTCSessionInfo:
        """
        Create a new WebRTC session.

        Args:
            assistant_id: Target assistant ID
            user_id: Optional user ID
            metadata: Additional session metadata

        Returns:
            WebRTCSessionInfo for the new session
        """
        session_id = str(uuid.uuid4())

        session = WebRTCSessionInfo(
            session_id=session_id,
            assistant_id=assistant_id,
            user_id=user_id,
            state=WebRTCSessionState.NEW,
            metadata=metadata or {},
        )

        self._sessions[session_id] = session

        # Track by assistant
        if assistant_id not in self._assistant_sessions:
            self._assistant_sessions[assistant_id] = set()
        self._assistant_sessions[assistant_id].add(session_id)

        # Track by user
        if user_id:
            if user_id not in self._user_sessions:
                self._user_sessions[user_id] = set()
            self._user_sessions[user_id].add(session_id)

        logger.info(
            f"Created WebRTC session {session_id} for assistant {assistant_id}"
        )

        if self._on_session_created:
            await self._on_session_created(session)

        return session

    async def process_offer(
        self,
        offer: WebRTCOffer,
    ) -> WebRTCAnswer:
        """
        Process an SDP offer and generate an answer.

        This is a signaling-only method. The actual WebRTC peer connection
        is handled by the application layer (e.g., aiortc or browser).

        Args:
            offer: WebRTC offer from client

        Returns:
            WebRTCAnswer to send back to client
        """
        # Create or get session
        if offer.session_id and offer.session_id in self._sessions:
            session = self._sessions[offer.session_id]
        else:
            session = await self.create_session(
                assistant_id=offer.assistant_id,
                user_id=offer.user_id,
                metadata=offer.metadata,
            )

        # Store remote SDP
        session.remote_sdp = offer.sdp
        session.state = WebRTCSessionState.CONNECTING
        session.update_activity()

        logger.info(f"Processing offer for session {session.session_id}")

        # Note: In a real implementation, the SDP answer would be generated
        # by the WebRTC peer connection (e.g., using aiortc).
        # This manager only handles signaling coordination.
        # The actual answer SDP must be provided by the caller after
        # creating their RTCPeerConnection.

        return WebRTCAnswer(
            sdp="",  # To be filled by application layer
            type="answer",
            session_id=session.session_id,
            ice_servers=self.config.ice_servers,
        )

    async def set_local_description(
        self,
        session_id: str,
        sdp: str,
    ):
        """
        Set the local SDP description for a session.

        Args:
            session_id: Session ID
            sdp: Local SDP content
        """
        session = self.get_session(session_id)
        if session:
            session.local_sdp = sdp
            session.update_activity()
            logger.debug(f"Set local SDP for session {session_id}")

    async def add_ice_candidate(
        self,
        session_id: str,
        candidate: ICECandidate,
    ):
        """
        Add an ICE candidate for a session.

        Args:
            session_id: Session ID
            candidate: ICE candidate to add
        """
        session = self.get_session(session_id)
        if session:
            session.ice_candidates.append(candidate)
            session.update_activity()
            logger.debug(
                f"Added ICE candidate for session {session_id}: "
                f"{candidate.candidate[:50]}..."
            )

    async def mark_connected(self, session_id: str):
        """
        Mark a session as connected.

        Args:
            session_id: Session ID
        """
        session = self.get_session(session_id)
        if session:
            session.mark_connected()
            logger.info(f"Session {session_id} connected")

            if self._on_session_connected:
                await self._on_session_connected(session)

    async def update_ice_state(
        self,
        session_id: str,
        ice_state: str,
    ):
        """
        Update ICE connection state for a session.

        Args:
            session_id: Session ID
            ice_state: New ICE connection state
        """
        session = self.get_session(session_id)
        if session:
            session.ice_connection_state = ice_state
            session.update_activity()

            # Handle state transitions
            if ice_state == "connected" or ice_state == "completed":
                await self.mark_connected(session_id)
            elif ice_state == "failed":
                session.state = WebRTCSessionState.FAILED
                logger.warning(f"Session {session_id} ICE connection failed")
            elif ice_state == "disconnected":
                session.state = WebRTCSessionState.DISCONNECTED
                logger.info(f"Session {session_id} ICE disconnected")

    async def close_session(self, session_id: str):
        """
        Close a WebRTC session.

        Args:
            session_id: Session ID to close
        """
        session = self._sessions.get(session_id)
        if not session:
            return

        session.mark_disconnected()
        session.state = WebRTCSessionState.CLOSED

        # Remove from tracking
        if session.assistant_id in self._assistant_sessions:
            self._assistant_sessions[session.assistant_id].discard(session_id)

        if session.user_id and session.user_id in self._user_sessions:
            self._user_sessions[session.user_id].discard(session_id)

        # Remove WebSocket if registered
        self._websockets.pop(session_id, None)

        # Keep session info for a while (for stats/debugging)
        # In production, you might want to archive or delete after a delay

        logger.info(
            f"Closed session {session_id} "
            f"(duration: {session.duration_ms:.0f}ms)"
        )

        if self._on_session_closed:
            await self._on_session_closed(session)

    async def cleanup_session(self, session_id: str):
        """
        Fully remove a session from memory.

        Args:
            session_id: Session ID to cleanup
        """
        await self.close_session(session_id)
        self._sessions.pop(session_id, None)
        logger.debug(f"Cleaned up session {session_id}")

    def register_websocket(
        self,
        session_id: str,
        websocket: WebSocket,
    ):
        """
        Register a WebSocket for signaling messages.

        Args:
            session_id: Session ID
            websocket: WebSocket connection
        """
        self._websockets[session_id] = websocket
        logger.debug(f"Registered WebSocket for session {session_id}")

    def unregister_websocket(self, session_id: str):
        """
        Unregister a WebSocket.

        Args:
            session_id: Session ID
        """
        self._websockets.pop(session_id, None)
        logger.debug(f"Unregistered WebSocket for session {session_id}")

    async def send_to_session(
        self,
        session_id: str,
        message: SignalingMessage,
    ) -> bool:
        """
        Send a signaling message to a session's WebSocket.

        Args:
            session_id: Target session ID
            message: Message to send

        Returns:
            True if sent successfully
        """
        websocket = self._websockets.get(session_id)
        if not websocket:
            logger.warning(f"No WebSocket for session {session_id}")
            return False

        try:
            await websocket.send_json(message.to_dict())
            return True
        except Exception as e:
            logger.error(f"Error sending to session {session_id}: {e}")
            return False

    async def broadcast_to_assistant(
        self,
        assistant_id: str,
        message: SignalingMessage,
        exclude: Optional[Set[str]] = None,
    ):
        """
        Broadcast a message to all sessions for an assistant.

        Args:
            assistant_id: Target assistant ID
            message: Message to broadcast
            exclude: Session IDs to exclude
        """
        session_ids = self._assistant_sessions.get(assistant_id, set())
        exclude = exclude or set()

        for session_id in session_ids:
            if session_id not in exclude:
                await self.send_to_session(session_id, message)

    def get_session(self, session_id: str) -> Optional[WebRTCSessionInfo]:
        """
        Get session info by ID.

        Args:
            session_id: Session ID

        Returns:
            WebRTCSessionInfo or None
        """
        return self._sessions.get(session_id)

    def get_sessions_by_assistant(
        self,
        assistant_id: str,
    ) -> List[WebRTCSessionInfo]:
        """
        Get all sessions for an assistant.

        Args:
            assistant_id: Assistant ID

        Returns:
            List of session info
        """
        session_ids = self._assistant_sessions.get(assistant_id, set())
        return [
            self._sessions[sid]
            for sid in session_ids
            if sid in self._sessions
        ]

    def get_sessions_by_user(
        self,
        user_id: str,
    ) -> List[WebRTCSessionInfo]:
        """
        Get all sessions for a user.

        Args:
            user_id: User ID

        Returns:
            List of session info
        """
        session_ids = self._user_sessions.get(user_id, set())
        return [
            self._sessions[sid]
            for sid in session_ids
            if sid in self._sessions
        ]

    def get_active_sessions(self) -> List[WebRTCSessionInfo]:
        """
        Get all active (connected) sessions.

        Returns:
            List of active sessions
        """
        return [
            s for s in self._sessions.values()
            if s.state == WebRTCSessionState.CONNECTED
        ]

    @property
    def session_count(self) -> int:
        """Get total number of sessions."""
        return len(self._sessions)

    @property
    def active_session_count(self) -> int:
        """Get number of active sessions."""
        return len(self.get_active_sessions())

    def update_stats(
        self,
        session_id: str,
        bytes_sent: int = 0,
        bytes_received: int = 0,
        packets_sent: int = 0,
        packets_received: int = 0,
    ):
        """
        Update session statistics.

        Args:
            session_id: Session ID
            bytes_sent: Additional bytes sent
            bytes_received: Additional bytes received
            packets_sent: Additional packets sent
            packets_received: Additional packets received
        """
        session = self.get_session(session_id)
        if session:
            session.bytes_sent += bytes_sent
            session.bytes_received += bytes_received
            session.packets_sent += packets_sent
            session.packets_received += packets_received
            session.update_activity()


# Global signaling manager instance
_manager: Optional[SignalingManager] = None


def get_signaling_manager() -> SignalingManager:
    """
    Get the global signaling manager instance.

    Returns:
        SignalingManager singleton
    """
    global _manager
    if _manager is None:
        _manager = SignalingManager()
    return _manager
