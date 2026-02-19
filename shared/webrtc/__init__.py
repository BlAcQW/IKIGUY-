"""
WebRTC Signaling Module

Provides server-side WebRTC signaling utilities for peer connection management.

Components:
- SignalingManager: Manages peer connections and ICE candidates
- WebRTCSession: Represents an active WebRTC session
- Models: SDP, ICE candidates, signaling messages

Author: KasaAI Team
Date: 2025-11-26
"""

from .models import (
    SDPType,
    SDPMessage,
    ICECandidate,
    SignalingMessage,
    SignalingMessageType,
    WebRTCSessionState,
    WebRTCSessionInfo,
    WebRTCOffer,
    WebRTCAnswer,
    WebRTCConfig,
    MediaConstraints,
)
from .manager import (
    SignalingManager,
    get_signaling_manager,
)
from .handler import WebRTCSignalingHandler

__all__ = [
    # Models
    "SDPType",
    "SDPMessage",
    "ICECandidate",
    "SignalingMessage",
    "SignalingMessageType",
    "WebRTCSessionState",
    "WebRTCSessionInfo",
    "WebRTCOffer",
    "WebRTCAnswer",
    "WebRTCConfig",
    "MediaConstraints",
    # Manager
    "SignalingManager",
    "get_signaling_manager",
    # Handler
    "WebRTCSignalingHandler",
]
