"""
Tests for WebRTC signaling models.

Tests SDP, ICE candidates, and session info models.
"""

import pytest
from datetime import datetime
from apps.shared.webrtc.models import (
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


class TestSDPType:
    """Tests for SDPType enum."""

    def test_sdp_type_values(self):
        """Test all SDP type values exist."""
        assert SDPType.OFFER.value == "offer"
        assert SDPType.ANSWER.value == "answer"
        assert SDPType.PRANSWER.value == "pranswer"
        assert SDPType.ROLLBACK.value == "rollback"


class TestWebRTCSessionState:
    """Tests for WebRTCSessionState enum."""

    def test_session_state_values(self):
        """Test all session state values exist."""
        assert WebRTCSessionState.NEW.value == "new"
        assert WebRTCSessionState.CONNECTING.value == "connecting"
        assert WebRTCSessionState.CONNECTED.value == "connected"
        assert WebRTCSessionState.DISCONNECTED.value == "disconnected"
        assert WebRTCSessionState.FAILED.value == "failed"
        assert WebRTCSessionState.CLOSED.value == "closed"


class TestSignalingMessageType:
    """Tests for SignalingMessageType enum."""

    def test_signaling_message_types(self):
        """Test all signaling message types exist."""
        assert SignalingMessageType.OFFER.value == "offer"
        assert SignalingMessageType.ANSWER.value == "answer"
        assert SignalingMessageType.ICE_CANDIDATE.value == "ice_candidate"
        assert SignalingMessageType.START_RECORDING.value == "start_recording"
        assert SignalingMessageType.STOP_RECORDING.value == "stop_recording"
        assert SignalingMessageType.BARGE_IN.value == "barge_in"
        assert SignalingMessageType.TRANSCRIPTION.value == "transcription"
        assert SignalingMessageType.AUDIO_CHUNK.value == "audio_chunk"


class TestSDPMessage:
    """Tests for SDPMessage model."""

    def test_create_offer(self):
        """Test creating an SDP offer."""
        sdp = SDPMessage(
            sdp="v=0\r\no=- 123 456 IN IP4 127.0.0.1\r\n...",
            type=SDPType.OFFER,
        )

        assert sdp.sdp.startswith("v=0")
        assert sdp.type == SDPType.OFFER

    def test_create_answer(self):
        """Test creating an SDP answer."""
        sdp = SDPMessage(
            sdp="v=0\r\no=- 789 012 IN IP4 127.0.0.1\r\n...",
            type=SDPType.ANSWER,
        )

        assert sdp.type == SDPType.ANSWER


class TestICECandidate:
    """Tests for ICECandidate model."""

    def test_create_ice_candidate(self):
        """Test creating an ICE candidate."""
        candidate = ICECandidate(
            candidate="candidate:1 1 UDP 2130706431 192.168.1.1 54321 typ host",
            sdp_mid="audio",
            sdp_mline_index=0,
        )

        assert "candidate:1" in candidate.candidate
        assert candidate.sdp_mid == "audio"
        assert candidate.sdp_mline_index == 0

    def test_ice_candidate_alias(self):
        """Test ICE candidate with camelCase aliases."""
        candidate = ICECandidate(
            candidate="candidate:1 1 UDP 2130706431 192.168.1.1 54321 typ host",
            sdpMid="video",
            sdpMLineIndex=1,
        )

        assert candidate.sdp_mid == "video"
        assert candidate.sdp_mline_index == 1


class TestSignalingMessage:
    """Tests for SignalingMessage model."""

    def test_create_message(self):
        """Test creating a signaling message."""
        msg = SignalingMessage(
            type=SignalingMessageType.OFFER,
            data={"sdp": "v=0...", "type": "offer"},
            session_id="session_123",
            sequence=1,
        )

        assert msg.type == SignalingMessageType.OFFER
        assert msg.data["type"] == "offer"
        assert msg.session_id == "session_123"
        assert msg.sequence == 1
        assert isinstance(msg.timestamp, datetime)

    def test_message_defaults(self):
        """Test message default values."""
        msg = SignalingMessage(type=SignalingMessageType.PING)

        assert msg.data is None
        assert msg.session_id is None
        assert msg.sequence is None

    def test_to_dict(self):
        """Test converting message to dict."""
        msg = SignalingMessage(
            type=SignalingMessageType.STATUS,
            data="Connected",
            session_id="sess_456",
        )

        d = msg.to_dict()

        assert d["type"] == "status"
        assert d["data"] == "Connected"
        assert d["session_id"] == "sess_456"
        assert "timestamp" in d


class TestMediaConstraints:
    """Tests for MediaConstraints model."""

    def test_default_constraints(self):
        """Test default media constraints."""
        constraints = MediaConstraints()

        assert constraints.audio is True
        assert constraints.video is False
        assert constraints.echo_cancellation is True
        assert constraints.noise_suppression is True
        assert constraints.sample_rate == 16000

    def test_custom_constraints(self):
        """Test custom media constraints."""
        constraints = MediaConstraints(
            video=True,
            sample_rate=48000,
            channel_count=2,
        )

        assert constraints.video is True
        assert constraints.sample_rate == 48000
        assert constraints.channel_count == 2


class TestWebRTCConfig:
    """Tests for WebRTCConfig model."""

    def test_default_config(self):
        """Test default WebRTC config."""
        config = WebRTCConfig()

        assert len(config.ice_servers) == 2
        assert "stun:stun.l.google.com:19302" in config.ice_servers[0]["urls"]
        assert config.ice_transport_policy == "all"
        assert config.bundle_policy == "balanced"

    def test_custom_config(self):
        """Test custom WebRTC config."""
        config = WebRTCConfig(
            ice_servers=[{"urls": "turn:turn.example.com"}],
            ice_transport_policy="relay",
            connection_timeout_ms=30000,
        )

        assert len(config.ice_servers) == 1
        assert config.ice_transport_policy == "relay"
        assert config.connection_timeout_ms == 30000


class TestWebRTCOffer:
    """Tests for WebRTCOffer model."""

    def test_create_offer(self):
        """Test creating WebRTC offer."""
        offer = WebRTCOffer(
            sdp="v=0\r\no=- 123 456 IN IP4 127.0.0.1\r\n",
            assistant_id="asst_123",
            user_id="user_456",
        )

        assert offer.type == "offer"
        assert offer.assistant_id == "asst_123"
        assert offer.user_id == "user_456"

    def test_offer_with_constraints(self):
        """Test offer with media constraints."""
        constraints = MediaConstraints(sample_rate=24000)
        offer = WebRTCOffer(
            sdp="v=0...",
            assistant_id="asst_789",
            media_constraints=constraints,
        )

        assert offer.media_constraints.sample_rate == 24000


class TestWebRTCAnswer:
    """Tests for WebRTCAnswer model."""

    def test_create_answer(self):
        """Test creating WebRTC answer."""
        answer = WebRTCAnswer(
            sdp="v=0\r\no=- 789 012 IN IP4 127.0.0.1\r\n",
            session_id="session_xyz",
        )

        assert answer.type == "answer"
        assert answer.session_id == "session_xyz"

    def test_answer_with_ice_servers(self):
        """Test answer with ICE servers."""
        answer = WebRTCAnswer(
            sdp="v=0...",
            session_id="session_abc",
            ice_servers=[{"urls": "stun:stun.example.com"}],
        )

        assert len(answer.ice_servers) == 1


class TestWebRTCSessionInfo:
    """Tests for WebRTCSessionInfo model."""

    def test_create_session_info(self):
        """Test creating session info."""
        info = WebRTCSessionInfo(
            session_id="sess_123",
            assistant_id="asst_456",
            user_id="user_789",
        )

        assert info.session_id == "sess_123"
        assert info.assistant_id == "asst_456"
        assert info.user_id == "user_789"
        assert info.state == WebRTCSessionState.NEW
        assert info.bytes_sent == 0
        assert info.bytes_received == 0

    def test_update_activity(self):
        """Test updating activity timestamp."""
        info = WebRTCSessionInfo(
            session_id="sess_123",
            assistant_id="asst_456",
        )
        old_time = info.last_activity

        import time
        time.sleep(0.01)
        info.update_activity()

        assert info.last_activity > old_time

    def test_mark_connected(self):
        """Test marking session as connected."""
        info = WebRTCSessionInfo(
            session_id="sess_123",
            assistant_id="asst_456",
        )

        info.mark_connected()

        assert info.state == WebRTCSessionState.CONNECTED
        assert info.connected_at is not None

    def test_mark_disconnected(self):
        """Test marking session as disconnected."""
        info = WebRTCSessionInfo(
            session_id="sess_123",
            assistant_id="asst_456",
        )
        info.mark_connected()
        info.mark_disconnected()

        assert info.state == WebRTCSessionState.DISCONNECTED

    def test_duration_calculation(self):
        """Test session duration calculation."""
        info = WebRTCSessionInfo(
            session_id="sess_123",
            assistant_id="asst_456",
        )

        # Not connected yet
        assert info.duration_ms == 0.0

        # Mark connected and wait
        info.mark_connected()
        import time
        time.sleep(0.01)
        info.update_activity()

        assert info.duration_ms > 0

    def test_ice_candidates_list(self):
        """Test adding ICE candidates."""
        info = WebRTCSessionInfo(
            session_id="sess_123",
            assistant_id="asst_456",
        )

        candidate = ICECandidate(
            candidate="candidate:1...",
            sdp_mid="audio",
        )
        info.ice_candidates.append(candidate)

        assert len(info.ice_candidates) == 1
        assert info.ice_candidates[0].sdp_mid == "audio"
