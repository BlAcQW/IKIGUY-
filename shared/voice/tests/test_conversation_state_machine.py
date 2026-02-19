"""
Tests for ConversationStateMachine.

Tests state transitions, callbacks, and turn-taking logic.
"""

import sys
import os

# Ensure apps path is in sys.path
apps_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
if apps_path not in sys.path:
    sys.path.insert(0, apps_path)

import pytest
from apps.shared.voice import ConversationStateMachine, ConversationState, VADState


class TestConversationStateMachine:
    """Tests for ConversationStateMachine."""

    def test_initial_state(self):
        """Test initial state is IDLE."""
        sm = ConversationStateMachine()
        assert sm.conversation_state == ConversationState.IDLE
        assert sm.vad_state == VADState.QUIET
        assert sm.hands_free_mode is True
        assert sm.can_record() is True

    def test_start_listening(self):
        """Test transition to LISTENING state."""
        sm = ConversationStateMachine()
        sm.start_listening()

        assert sm.conversation_state == ConversationState.LISTENING
        assert sm.vad_state == VADState.STARTING

    def test_stop_listening_transitions_to_processing(self):
        """Test stop_listening transitions from LISTENING to PROCESSING."""
        sm = ConversationStateMachine()
        sm.start_listening()
        sm.stop_listening()

        assert sm.conversation_state == ConversationState.PROCESSING
        assert sm.vad_state == VADState.STOPPING

    def test_start_speaking(self):
        """Test assistant speaking state."""
        sm = ConversationStateMachine()
        sm.start_speaking()

        assert sm.conversation_state == ConversationState.SPEAKING
        assert sm.user_spoke_during_assistant is False
        assert sm.assistant_speaking_start_time is not None

    def test_stop_speaking_returns_to_idle(self):
        """Test stop_speaking returns to IDLE."""
        sm = ConversationStateMachine()
        sm.start_speaking()
        sm.stop_speaking()

        assert sm.conversation_state == ConversationState.IDLE
        assert sm.assistant_speaking_start_time is None

    def test_interruption_during_speaking(self):
        """Test user interruption while assistant is speaking."""
        sm = ConversationStateMachine()
        sm.start_speaking()

        # User starts speaking - should trigger interruption
        sm.start_listening()

        assert sm.conversation_state == ConversationState.INTERRUPTED
        assert sm.user_spoke_during_assistant is True

    def test_cannot_record_while_speaking(self):
        """Test that recording is blocked while assistant is speaking."""
        sm = ConversationStateMachine()
        sm.start_speaking()

        assert sm.can_record() is False

    def test_cannot_record_while_processing(self):
        """Test that recording is blocked while processing."""
        sm = ConversationStateMachine()
        sm.start_listening()
        sm.stop_listening()  # Transitions to PROCESSING

        assert sm.can_record() is False

    def test_reset(self):
        """Test reset returns to initial state."""
        sm = ConversationStateMachine()
        sm.start_listening()
        sm.stop_listening()
        sm.start_speaking()

        sm.reset()

        assert sm.conversation_state == ConversationState.IDLE
        assert sm.vad_state == VADState.QUIET
        assert sm.pending_llm_request_id is None
        assert sm.user_spoke_during_assistant is False

    def test_should_auto_resume_listening_hands_free(self):
        """Test auto-resume logic in hands-free mode."""
        sm = ConversationStateMachine()
        sm.hands_free_mode = True
        sm.conversation_state = ConversationState.IDLE
        sm.user_spoke_during_assistant = False

        assert sm.should_auto_resume_listening() is True

    def test_should_not_auto_resume_if_user_spoke(self):
        """Test auto-resume is disabled if user spoke during assistant."""
        sm = ConversationStateMachine()
        sm.hands_free_mode = True
        sm.conversation_state = ConversationState.IDLE
        sm.user_spoke_during_assistant = True

        assert sm.should_auto_resume_listening() is False

    def test_should_not_auto_resume_if_hands_free_disabled(self):
        """Test auto-resume is disabled when hands-free mode is off."""
        sm = ConversationStateMachine()
        sm.hands_free_mode = False
        sm.conversation_state = ConversationState.IDLE
        sm.user_spoke_during_assistant = False

        assert sm.should_auto_resume_listening() is False

    def test_start_processing(self):
        """Test start_processing sets request ID."""
        sm = ConversationStateMachine()
        sm.start_processing("req-123")

        assert sm.pending_llm_request_id == "req-123"
        assert sm.conversation_state == ConversationState.PROCESSING

    def test_cancel_processing(self):
        """Test cancel_processing clears request ID."""
        sm = ConversationStateMachine()
        sm.start_processing("req-123")

        result = sm.cancel_processing()

        assert result is True
        assert sm.pending_llm_request_id is None

    def test_cancel_processing_no_pending(self):
        """Test cancel_processing returns False when no pending request."""
        sm = ConversationStateMachine()

        result = sm.cancel_processing()

        assert result is False

    def test_get_state_info(self):
        """Test get_state_info returns correct structure."""
        sm = ConversationStateMachine()
        info = sm.get_state_info()

        assert "conversation_state" in info
        assert "vad_state" in info
        assert "hands_free_mode" in info
        assert "can_record" in info
        assert "time_in_current_state" in info

        assert info["conversation_state"] == "idle"
        assert info["vad_state"] == "quiet"
        assert info["hands_free_mode"] is True
        assert info["can_record"] is True

    def test_vad_state_transitions(self):
        """Test VAD state machine transitions."""
        sm = ConversationStateMachine()

        # QUIET -> STARTING
        sm.handle_vad_speech_detected()
        assert sm.vad_state == VADState.STARTING

        # STARTING -> SPEAKING
        sm.handle_vad_speech_detected()
        assert sm.vad_state == VADState.SPEAKING

        # SPEAKING -> STOPPING
        sm.handle_vad_silence_detected()
        assert sm.vad_state == VADState.STOPPING

        # STOPPING -> QUIET
        sm.handle_vad_silence_detected()
        assert sm.vad_state == VADState.QUIET

    def test_callback_on_state_change(self):
        """Test callback is invoked on state change."""
        sm = ConversationStateMachine()
        callback_called = []

        def on_change(old_state, new_state):
            callback_called.append((old_state, new_state))

        sm.on_state_change = on_change
        sm.start_listening()

        assert len(callback_called) == 1
        assert callback_called[0][0] == ConversationState.IDLE
        assert callback_called[0][1] == ConversationState.LISTENING

    def test_callback_on_interruption(self):
        """Test interruption callback is invoked."""
        sm = ConversationStateMachine()
        interruption_called = []

        def on_interrupt():
            interruption_called.append(True)

        sm.on_interruption = on_interrupt
        sm.start_speaking()
        sm.start_listening()  # Interrupt

        assert len(interruption_called) == 1


class TestConversationStateEnum:
    """Tests for ConversationState enum."""

    def test_enum_values(self):
        """Test enum has expected values."""
        assert ConversationState.IDLE.value == "idle"
        assert ConversationState.LISTENING.value == "listening"
        assert ConversationState.PROCESSING.value == "processing"
        assert ConversationState.SPEAKING.value == "speaking"
        assert ConversationState.INTERRUPTED.value == "interrupted"


class TestVADStateEnum:
    """Tests for VADState enum."""

    def test_enum_values(self):
        """Test enum has expected values."""
        assert VADState.QUIET.value == "quiet"
        assert VADState.STARTING.value == "starting"
        assert VADState.SPEAKING.value == "speaking"
        assert VADState.STOPPING.value == "stopping"
