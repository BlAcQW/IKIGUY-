"""
WebRTC Signaling Models

Data structures for WebRTC signaling, including SDP, ICE candidates,
and session management.

Author: KasaAI Team
Date: 2025-11-26
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class SDPType(str, Enum):
    """SDP message types."""
    OFFER = "offer"
    ANSWER = "answer"
    PRANSWER = "pranswer"  # Provisional answer
    ROLLBACK = "rollback"


class WebRTCSessionState(str, Enum):
    """WebRTC session states."""
    NEW = "new"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    FAILED = "failed"
    CLOSED = "closed"


class SignalingMessageType(str, Enum):
    """Signaling message types."""
    OFFER = "offer"
    ANSWER = "answer"
    ICE_CANDIDATE = "ice_candidate"
    SESSION_READY = "session_ready"
    SESSION_CLOSED = "session_closed"
    ERROR = "error"
    PING = "ping"
    PONG = "pong"
    # Audio control messages
    START_RECORDING = "start_recording"
    STOP_RECORDING = "stop_recording"
    BARGE_IN = "barge_in"
    # Response messages
    TRANSCRIPTION = "transcription"
    TEXT_RESPONSE = "text_response"
    AUDIO_CHUNK = "audio_chunk"
    AUDIO_COMPLETE = "audio_complete"
    STATUS = "status"


class SDPMessage(BaseModel):
    """
    Session Description Protocol message.

    Used for WebRTC offer/answer exchange.
    """
    sdp: str = Field(..., description="SDP content")
    type: SDPType = Field(..., description="SDP type (offer/answer)")

    class Config:
        use_enum_values = True


class ICECandidate(BaseModel):
    """
    ICE (Interactive Connectivity Establishment) candidate.

    Represents a potential network path for WebRTC connection.
    """
    candidate: str = Field(..., description="ICE candidate string")
    sdp_mid: Optional[str] = Field(None, description="Media stream ID", alias="sdpMid")
    sdp_mline_index: Optional[int] = Field(
        None,
        description="Media line index",
        alias="sdpMLineIndex"
    )
    username_fragment: Optional[str] = Field(
        None,
        description="ICE username fragment",
        alias="usernameFragment"
    )

    class Config:
        populate_by_name = True


class SignalingMessage(BaseModel):
    """
    Generic signaling message for WebRTC coordination.
    """
    type: SignalingMessageType = Field(..., description="Message type")
    data: Optional[Any] = Field(None, description="Message payload")
    session_id: Optional[str] = Field(None, description="Session identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sequence: Optional[int] = Field(None, description="Message sequence number")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type.value if isinstance(self.type, Enum) else self.type,
            "data": self.data,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "sequence": self.sequence,
        }

    class Config:
        use_enum_values = True


class MediaConstraints(BaseModel):
    """
    Media constraints for WebRTC streams.
    """
    audio: bool = Field(True, description="Enable audio")
    video: bool = Field(False, description="Enable video")

    # Audio constraints
    echo_cancellation: bool = Field(True, description="Enable echo cancellation")
    noise_suppression: bool = Field(True, description="Enable noise suppression")
    auto_gain_control: bool = Field(True, description="Enable auto gain control")
    sample_rate: int = Field(16000, description="Audio sample rate")
    channel_count: int = Field(1, description="Number of audio channels")


class WebRTCConfig(BaseModel):
    """
    WebRTC configuration for peer connections.
    """
    ice_servers: List[Dict[str, Any]] = Field(
        default_factory=lambda: [
            {"urls": "stun:stun.l.google.com:19302"},
            {"urls": "stun:stun1.l.google.com:19302"},
        ],
        description="ICE servers for STUN/TURN"
    )
    ice_transport_policy: str = Field(
        "all",
        description="ICE transport policy (all/relay)"
    )
    bundle_policy: str = Field(
        "balanced",
        description="Bundle policy for media"
    )
    rtcp_mux_policy: str = Field(
        "require",
        description="RTCP mux policy"
    )

    # Timeouts
    ice_gathering_timeout_ms: int = Field(
        5000,
        description="ICE gathering timeout in milliseconds"
    )
    connection_timeout_ms: int = Field(
        10000,
        description="Connection timeout in milliseconds"
    )


class WebRTCOffer(BaseModel):
    """
    WebRTC offer request from client.
    """
    sdp: str = Field(..., description="SDP offer content")
    type: str = Field("offer", description="SDP type")
    assistant_id: str = Field(..., description="Target assistant ID")
    user_id: Optional[str] = Field(None, description="User ID")
    session_id: Optional[str] = Field(None, description="Existing session ID")
    media_constraints: Optional[MediaConstraints] = Field(
        None,
        description="Media constraints"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata"
    )


class WebRTCAnswer(BaseModel):
    """
    WebRTC answer response from server.
    """
    sdp: str = Field(..., description="SDP answer content")
    type: str = Field("answer", description="SDP type")
    session_id: str = Field(..., description="Session identifier")
    ice_servers: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="ICE servers configuration"
    )


class WebRTCSessionInfo(BaseModel):
    """
    Information about a WebRTC session.
    """
    session_id: str = Field(..., description="Unique session identifier")
    assistant_id: str = Field(..., description="Assistant ID")
    user_id: Optional[str] = Field(None, description="User ID")
    state: WebRTCSessionState = Field(
        WebRTCSessionState.NEW,
        description="Session state"
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    connected_at: Optional[datetime] = Field(None, description="Connection time")
    last_activity: datetime = Field(default_factory=datetime.utcnow)

    # ICE state
    local_sdp: Optional[str] = Field(None, description="Local SDP")
    remote_sdp: Optional[str] = Field(None, description="Remote SDP")
    ice_candidates: List[ICECandidate] = Field(
        default_factory=list,
        description="Gathered ICE candidates"
    )
    ice_connection_state: str = Field("new", description="ICE connection state")

    # Statistics
    bytes_sent: int = Field(0, description="Bytes sent")
    bytes_received: int = Field(0, description="Bytes received")
    packets_sent: int = Field(0, description="Packets sent")
    packets_received: int = Field(0, description="Packets received")

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()

    def mark_connected(self):
        """Mark session as connected."""
        self.state = WebRTCSessionState.CONNECTED
        self.connected_at = datetime.utcnow()
        self.update_activity()

    def mark_disconnected(self):
        """Mark session as disconnected."""
        self.state = WebRTCSessionState.DISCONNECTED
        self.update_activity()

    @property
    def duration_ms(self) -> float:
        """Get session duration in milliseconds."""
        if not self.connected_at:
            return 0.0
        end_time = self.last_activity if self.state == WebRTCSessionState.DISCONNECTED else datetime.utcnow()
        return (end_time - self.connected_at).total_seconds() * 1000

    class Config:
        use_enum_values = True
