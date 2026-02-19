"""
WebRTC Signaling Handler for InkWave.

Handles WebRTC peer connection setup for low-latency voice chat:
- SDP offer/answer exchange
- ICE candidate exchange
- Data channel for control messages

Author: AI Labs Africa
Created: November 30, 2025
"""

import asyncio
import json
import logging
import os
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, Optional, Set

from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Query

# Add shared services to path
sys.path.insert(0, '/opt/kasaai/apps')

logger = logging.getLogger(__name__)

router = APIRouter()


class WebRTCPeer:
    """
    Represents a WebRTC peer in a signaling session.

    Manages:
    - SDP offer/answer exchange
    - ICE candidate gathering
    - Connection state
    """

    def __init__(
        self,
        websocket: WebSocket,
        book_id: str,
        user_id: str
    ):
        self.websocket = websocket
        self.book_id = book_id
        self.user_id = user_id
        self.peer_id = str(uuid.uuid4())[:8]
        self.is_connected = False
        self.ice_candidates: list = []
        self.local_description: Optional[Dict] = None
        self.remote_description: Optional[Dict] = None

        logger.info(f"[{self.peer_id}] WebRTC peer created for book: {book_id}")

    async def send_message(self, msg_type: str, data: Any):
        """Send a typed message to the peer."""
        try:
            await self.websocket.send_json({
                "type": msg_type,
                "data": data
            })
        except Exception as e:
            logger.error(f"[{self.peer_id}] Failed to send message: {e}")


class WebRTCSignalingSession:
    """
    Manages WebRTC signaling for a book voice chat session.

    In a client-server WebRTC model:
    - Client initiates with SDP offer
    - Server responds with SDP answer
    - Both exchange ICE candidates
    - Server handles audio processing via data channel
    """

    def __init__(self, book_id: str):
        self.book_id = book_id
        self.session_id = str(uuid.uuid4())[:8]
        self.peers: Dict[str, WebRTCPeer] = {}
        self.created_at = datetime.utcnow()

        logger.info(f"[{self.session_id}] WebRTC signaling session created for book: {book_id}")

    async def add_peer(self, peer: WebRTCPeer):
        """Add a peer to the session."""
        self.peers[peer.peer_id] = peer
        logger.info(f"[{self.session_id}] Peer {peer.peer_id} joined")

    async def remove_peer(self, peer_id: str):
        """Remove a peer from the session."""
        if peer_id in self.peers:
            del self.peers[peer_id]
            logger.info(f"[{self.session_id}] Peer {peer_id} left")

    async def broadcast(self, msg_type: str, data: Any, exclude: Optional[str] = None):
        """Broadcast message to all peers except excluded."""
        for peer_id, peer in self.peers.items():
            if peer_id != exclude:
                await peer.send_message(msg_type, data)


# Active signaling sessions by book_id
active_sessions: Dict[str, WebRTCSignalingSession] = {}


async def get_or_create_session(book_id: str) -> WebRTCSignalingSession:
    """Get or create a signaling session for a book."""
    if book_id not in active_sessions:
        active_sessions[book_id] = WebRTCSignalingSession(book_id)
    return active_sessions[book_id]


@router.websocket("/webrtc-signaling/{book_id}")
async def webrtc_signaling_websocket(
    websocket: WebSocket,
    book_id: str,
    token: str = Query(None)
):
    """
    WebSocket endpoint for WebRTC signaling.

    Protocol:
    - Client sends: offer, answer, ice_candidate, ready
    - Server sends: offer, answer, ice_candidate, peer_joined, peer_left, error

    STUN servers for NAT traversal:
    - stun:stun.l.google.com:19302
    - stun:stun1.l.google.com:19302

    Args:
        websocket: WebSocket connection
        book_id: Book ID for the voice chat
        token: Authentication token
    """
    await websocket.accept()

    # Validate token and get user ID
    user_id = "anonymous"
    if token:
        try:
            from app.core.auth import verify_token
            user_data = await verify_token(token)
            user_id = user_data.get("sub", "anonymous")
        except Exception as e:
            logger.warning(f"Token validation failed: {e}")

    # Create peer
    peer = WebRTCPeer(
        websocket=websocket,
        book_id=book_id,
        user_id=user_id
    )

    # Get or create signaling session
    session = await get_or_create_session(book_id)
    await session.add_peer(peer)

    logger.info(f"[{peer.peer_id}] WebRTC signaling connected for book: {book_id}")

    try:
        # Send initial config (STUN servers, etc.)
        await peer.send_message("config", {
            "ice_servers": [
                {"urls": "stun:stun.l.google.com:19302"},
                {"urls": "stun:stun1.l.google.com:19302"},
                {"urls": "stun:stun2.l.google.com:19302"}
            ],
            "peer_id": peer.peer_id,
            "session_id": session.session_id
        })

        # Notify other peers
        await session.broadcast(
            "peer_joined",
            {"peer_id": peer.peer_id, "user_id": user_id},
            exclude=peer.peer_id
        )

        # Message loop
        while True:
            try:
                message = await websocket.receive_json()
                msg_type = message.get("type", "")
                data = message.get("data")
                target_peer = message.get("target")

                logger.debug(f"[{peer.peer_id}] Received: {msg_type}")

                if msg_type == "offer":
                    # SDP offer from client
                    peer.local_description = data
                    logger.info(f"[{peer.peer_id}] Received SDP offer")

                    # In client-server model, server would generate answer here
                    # For peer-to-peer, forward to other peer
                    if target_peer and target_peer in session.peers:
                        await session.peers[target_peer].send_message("offer", {
                            "sdp": data,
                            "from": peer.peer_id
                        })
                    else:
                        # Broadcast to all peers if no target specified
                        await session.broadcast(
                            "offer",
                            {"sdp": data, "from": peer.peer_id},
                            exclude=peer.peer_id
                        )

                elif msg_type == "answer":
                    # SDP answer
                    peer.remote_description = data
                    logger.info(f"[{peer.peer_id}] Received SDP answer")

                    if target_peer and target_peer in session.peers:
                        await session.peers[target_peer].send_message("answer", {
                            "sdp": data,
                            "from": peer.peer_id
                        })
                    else:
                        await session.broadcast(
                            "answer",
                            {"sdp": data, "from": peer.peer_id},
                            exclude=peer.peer_id
                        )

                elif msg_type == "ice_candidate":
                    # ICE candidate
                    peer.ice_candidates.append(data)
                    logger.debug(f"[{peer.peer_id}] Received ICE candidate")

                    if target_peer and target_peer in session.peers:
                        await session.peers[target_peer].send_message("ice_candidate", {
                            "candidate": data,
                            "from": peer.peer_id
                        })
                    else:
                        await session.broadcast(
                            "ice_candidate",
                            {"candidate": data, "from": peer.peer_id},
                            exclude=peer.peer_id
                        )

                elif msg_type == "ready":
                    # Peer is ready to start
                    peer.is_connected = True
                    logger.info(f"[{peer.peer_id}] Peer ready")

                    await session.broadcast(
                        "peer_ready",
                        {"peer_id": peer.peer_id},
                        exclude=peer.peer_id
                    )

                elif msg_type == "data_channel":
                    # Data channel message (control messages, etc.)
                    channel_data = data.get("data")
                    channel_name = data.get("channel", "default")

                    logger.debug(f"[{peer.peer_id}] Data channel '{channel_name}': {channel_data}")

                    # Process data channel messages
                    await handle_data_channel_message(peer, session, channel_name, channel_data)

                else:
                    logger.warning(f"[{peer.peer_id}] Unknown message type: {msg_type}")

            except json.JSONDecodeError:
                logger.warning(f"[{peer.peer_id}] Invalid JSON received")
                await peer.send_message("error", "Invalid message format")

    except WebSocketDisconnect:
        logger.info(f"[{peer.peer_id}] Client disconnected")

    except Exception as e:
        logger.error(f"[{peer.peer_id}] WebSocket error: {e}", exc_info=True)

    finally:
        # Cleanup
        await session.remove_peer(peer.peer_id)

        # Notify other peers
        await session.broadcast(
            "peer_left",
            {"peer_id": peer.peer_id},
            exclude=peer.peer_id
        )

        # Remove empty session
        if len(session.peers) == 0 and book_id in active_sessions:
            del active_sessions[book_id]
            logger.info(f"[{session.session_id}] Session cleaned up (no more peers)")


async def handle_data_channel_message(
    peer: WebRTCPeer,
    session: WebRTCSignalingSession,
    channel: str,
    data: Any
):
    """
    Handle data channel messages for control and signaling.

    In WebRTC mode, audio is streamed directly via media track,
    but control messages come through data channel.
    """
    if channel == "control":
        msg_type = data.get("type") if isinstance(data, dict) else None

        if msg_type == "start_recording":
            await peer.send_message("data_channel", {
                "channel": "control",
                "data": {"type": "recording_started"}
            })

        elif msg_type == "stop_recording":
            await peer.send_message("data_channel", {
                "channel": "control",
                "data": {"type": "processing"}
            })

        elif msg_type == "barge_in":
            await peer.send_message("data_channel", {
                "channel": "control",
                "data": {"type": "stopped"}
            })

    elif channel == "chat":
        # Text chat through data channel
        if isinstance(data, dict) and data.get("type") == "text":
            text = data.get("text", "")
            # This would trigger RAG processing
            # For now, echo back
            await peer.send_message("data_channel", {
                "channel": "chat",
                "data": {"type": "text_received", "text": text}
            })
