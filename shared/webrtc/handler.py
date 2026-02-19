"""
WebRTC Signaling Handler

Provides reusable WebSocket handler for WebRTC signaling endpoints.

Author: KasaAI Team
Date: 2025-11-26
"""

import logging
import json
from typing import Optional, Dict, Any, Callable, Awaitable
from fastapi import WebSocket, WebSocketDisconnect

from .models import (
    SignalingMessage,
    SignalingMessageType,
    ICECandidate,
    WebRTCOffer,
    WebRTCSessionState,
)
from .manager import SignalingManager, get_signaling_manager

logger = logging.getLogger(__name__)


class WebRTCSignalingHandler:
    """
    Reusable WebSocket handler for WebRTC signaling.

    Handles the signaling protocol for WebRTC connections:
    - SDP offer/answer exchange
    - ICE candidate exchange
    - Session lifecycle management
    - Audio control messages (start/stop recording, barge-in)
    """

    def __init__(
        self,
        manager: Optional[SignalingManager] = None,
        on_offer: Optional[Callable[[str, WebRTCOffer], Awaitable[str]]] = None,
        on_ice_candidate: Optional[Callable[[str, ICECandidate], Awaitable[None]]] = None,
        on_start_recording: Optional[Callable[[str], Awaitable[None]]] = None,
        on_stop_recording: Optional[Callable[[str], Awaitable[None]]] = None,
        on_barge_in: Optional[Callable[[str], Awaitable[None]]] = None,
        on_text_message: Optional[Callable[[str, str], Awaitable[None]]] = None,
        on_session_ready: Optional[Callable[[str], Awaitable[None]]] = None,
        on_session_closed: Optional[Callable[[str], Awaitable[None]]] = None,
    ):
        """
        Initialize the signaling handler.

        Args:
            manager: SignalingManager instance (uses global if not provided)
            on_offer: Callback to generate SDP answer from offer
            on_ice_candidate: Callback when ICE candidate received
            on_start_recording: Callback when recording starts
            on_stop_recording: Callback when recording stops
            on_barge_in: Callback for barge-in/interruption
            on_text_message: Callback for text messages
            on_session_ready: Callback when session is ready
            on_session_closed: Callback when session closes
        """
        self.manager = manager or get_signaling_manager()

        # Callbacks
        self._on_offer = on_offer
        self._on_ice_candidate = on_ice_candidate
        self._on_start_recording = on_start_recording
        self._on_stop_recording = on_stop_recording
        self._on_barge_in = on_barge_in
        self._on_text_message = on_text_message
        self._on_session_ready = on_session_ready
        self._on_session_closed = on_session_closed

    async def handle_connection(
        self,
        websocket: WebSocket,
        assistant_id: str,
        user_id: Optional[str] = None,
        auth_token: Optional[str] = None,
    ):
        """
        Handle a WebRTC signaling WebSocket connection.

        Args:
            websocket: FastAPI WebSocket connection
            assistant_id: Target assistant ID
            user_id: Optional user ID
            auth_token: Optional authentication token
        """
        # Accept the WebSocket connection
        await websocket.accept()

        # Create session
        session = await self.manager.create_session(
            assistant_id=assistant_id,
            user_id=user_id,
            metadata={
                "auth_token": auth_token,
                "transport": "websocket_signaling",
            }
        )

        session_id = session.session_id
        self.manager.register_websocket(session_id, websocket)

        logger.info(
            f"WebRTC signaling connection established: "
            f"session={session_id}, assistant={assistant_id}"
        )

        try:
            # Send session ready message with configuration
            await self._send_message(
                websocket,
                SignalingMessageType.SESSION_READY,
                {
                    "session_id": session_id,
                    "ice_servers": self.manager.config.ice_servers,
                }
            )

            if self._on_session_ready:
                await self._on_session_ready(session_id)

            # Main message loop
            while True:
                try:
                    raw_message = await websocket.receive_text()
                    message = json.loads(raw_message)
                    await self._handle_message(
                        websocket,
                        session_id,
                        message,
                    )
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON from {session_id}: {e}")
                    await self._send_error(websocket, "Invalid JSON format")

        except WebSocketDisconnect:
            logger.info(f"WebRTC signaling disconnected: {session_id}")
        except Exception as e:
            logger.error(f"Error in signaling handler {session_id}: {e}")
            await self._send_error(websocket, str(e))
        finally:
            # Cleanup
            self.manager.unregister_websocket(session_id)
            await self.manager.close_session(session_id)

            if self._on_session_closed:
                await self._on_session_closed(session_id)

    async def _handle_message(
        self,
        websocket: WebSocket,
        session_id: str,
        message: Dict[str, Any],
    ):
        """
        Handle an incoming signaling message.

        Args:
            websocket: WebSocket connection
            session_id: Session ID
            message: Parsed message dict
        """
        msg_type = message.get("type")
        data = message.get("data")

        logger.debug(f"Received message type={msg_type} for session={session_id}")

        session = self.manager.get_session(session_id)
        if session:
            session.update_activity()

        if msg_type == "offer":
            await self._handle_offer(websocket, session_id, data)

        elif msg_type == "ice_candidate":
            await self._handle_ice_candidate(session_id, data)

        elif msg_type == "start_recording":
            if self._on_start_recording:
                await self._on_start_recording(session_id)
            await self._send_message(
                websocket,
                SignalingMessageType.STATUS,
                "Recording started"
            )

        elif msg_type == "stop_recording":
            if self._on_stop_recording:
                await self._on_stop_recording(session_id)
            await self._send_message(
                websocket,
                SignalingMessageType.STATUS,
                "Recording stopped"
            )

        elif msg_type == "barge_in":
            if self._on_barge_in:
                await self._on_barge_in(session_id)
            await self._send_message(
                websocket,
                SignalingMessageType.STATUS,
                "Barge-in acknowledged"
            )

        elif msg_type == "text":
            if self._on_text_message:
                await self._on_text_message(session_id, data)

        elif msg_type == "ping":
            await self._send_message(
                websocket,
                SignalingMessageType.PONG,
                None
            )

        else:
            logger.warning(f"Unknown message type: {msg_type}")

    async def _handle_offer(
        self,
        websocket: WebSocket,
        session_id: str,
        data: Dict[str, Any],
    ):
        """
        Handle SDP offer and generate answer.

        Args:
            websocket: WebSocket connection
            session_id: Session ID
            data: Offer data
        """
        session = self.manager.get_session(session_id)
        if not session:
            await self._send_error(websocket, "Session not found")
            return

        # Store remote SDP
        sdp = data.get("sdp", "")
        session.remote_sdp = sdp
        session.state = WebRTCSessionState.CONNECTING

        # Generate answer if callback provided
        if self._on_offer:
            try:
                offer = WebRTCOffer(
                    sdp=sdp,
                    type=data.get("type", "offer"),
                    assistant_id=session.assistant_id,
                    user_id=session.user_id,
                    session_id=session_id,
                )
                answer_sdp = await self._on_offer(session_id, offer)

                # Store local SDP
                await self.manager.set_local_description(session_id, answer_sdp)

                # Send answer
                await self._send_message(
                    websocket,
                    SignalingMessageType.ANSWER,
                    {
                        "sdp": answer_sdp,
                        "type": "answer",
                        "session_id": session_id,
                    }
                )
            except Exception as e:
                logger.error(f"Error generating answer: {e}")
                await self._send_error(websocket, f"Failed to generate answer: {e}")
        else:
            # No callback - just acknowledge receipt
            logger.warning("No on_offer callback - cannot generate SDP answer")
            await self._send_message(
                websocket,
                SignalingMessageType.STATUS,
                "Offer received (no answer callback configured)"
            )

    async def _handle_ice_candidate(
        self,
        session_id: str,
        data: Dict[str, Any],
    ):
        """
        Handle incoming ICE candidate.

        Args:
            session_id: Session ID
            data: ICE candidate data
        """
        candidate = ICECandidate(
            candidate=data.get("candidate", ""),
            sdp_mid=data.get("sdpMid"),
            sdp_mline_index=data.get("sdpMLineIndex"),
            username_fragment=data.get("usernameFragment"),
        )

        await self.manager.add_ice_candidate(session_id, candidate)

        if self._on_ice_candidate:
            await self._on_ice_candidate(session_id, candidate)

    async def _send_message(
        self,
        websocket: WebSocket,
        msg_type: SignalingMessageType,
        data: Any,
    ):
        """
        Send a signaling message.

        Args:
            websocket: Target WebSocket
            msg_type: Message type
            data: Message data
        """
        message = SignalingMessage(
            type=msg_type,
            data=data,
        )
        await websocket.send_json(message.to_dict())

    async def _send_error(
        self,
        websocket: WebSocket,
        error: str,
    ):
        """
        Send an error message.

        Args:
            websocket: Target WebSocket
            error: Error message
        """
        await self._send_message(
            websocket,
            SignalingMessageType.ERROR,
            error,
        )

    # Helper methods for sending responses back to client

    async def send_transcription(
        self,
        session_id: str,
        text: str,
        is_final: bool = False,
    ):
        """
        Send transcription result to client.

        Args:
            session_id: Target session
            text: Transcribed text
            is_final: Whether this is final transcription
        """
        message = SignalingMessage(
            type=SignalingMessageType.TRANSCRIPTION,
            data={"text": text, "is_final": is_final},
            session_id=session_id,
        )
        await self.manager.send_to_session(session_id, message)

    async def send_text_response(
        self,
        session_id: str,
        text: str,
    ):
        """
        Send text response to client.

        Args:
            session_id: Target session
            text: Response text
        """
        message = SignalingMessage(
            type=SignalingMessageType.TEXT_RESPONSE,
            data=text,
            session_id=session_id,
        )
        await self.manager.send_to_session(session_id, message)

    async def send_audio_chunk(
        self,
        session_id: str,
        audio_base64: str,
    ):
        """
        Send audio chunk to client.

        Args:
            session_id: Target session
            audio_base64: Base64-encoded audio data
        """
        message = SignalingMessage(
            type=SignalingMessageType.AUDIO_CHUNK,
            data=audio_base64,
            session_id=session_id,
        )
        await self.manager.send_to_session(session_id, message)

    async def send_audio_complete(
        self,
        session_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Signal audio playback complete.

        Args:
            session_id: Target session
            metadata: Optional metadata
        """
        message = SignalingMessage(
            type=SignalingMessageType.AUDIO_COMPLETE,
            data=metadata or {},
            session_id=session_id,
        )
        await self.manager.send_to_session(session_id, message)

    async def send_status(
        self,
        session_id: str,
        status: str,
    ):
        """
        Send status update to client.

        Args:
            session_id: Target session
            status: Status message
        """
        message = SignalingMessage(
            type=SignalingMessageType.STATUS,
            data=status,
            session_id=session_id,
        )
        await self.manager.send_to_session(session_id, message)

    async def send_error(
        self,
        session_id: str,
        error: str,
    ):
        """
        Send error to client.

        Args:
            session_id: Target session
            error: Error message
        """
        message = SignalingMessage(
            type=SignalingMessageType.ERROR,
            data=error,
            session_id=session_id,
        )
        await self.manager.send_to_session(session_id, message)
