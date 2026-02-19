"""
Conversation State Machine for Natural Voice Interactions.

Based on VAPI's approach to smooth, human-like conversations.
Manages conversation flow, turn-taking, and interruptions.

Usage:
    from apps.shared.voice import ConversationStateMachine, ConversationState

    state_machine = ConversationStateMachine()
    state_machine.on_interruption = handle_interruption
    state_machine.start_listening()

Author: AI Labs Africa
"""

import logging
import asyncio
import inspect
from enum import Enum
from typing import Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class ConversationState(Enum):
    """Conversation states for proper turn-taking."""
    IDLE = "idle"  # No activity
    LISTENING = "listening"  # Actively recording user speech
    PROCESSING = "processing"  # Transcribing/generating response
    SPEAKING = "speaking"  # Assistant is speaking
    INTERRUPTED = "interrupted"  # User interrupted assistant


class VADState(Enum):
    """Voice Activity Detection states (VAPI-style)."""
    QUIET = "quiet"  # No meaningful audio detected
    STARTING = "starting"  # Speech beginning detected, waiting for confirmation
    SPEAKING = "speaking"  # Active speech confirmed
    STOPPING = "stopping"  # Speech ending detected, waiting for confirmation


class ConversationStateMachine:
    """
    Manages conversation state for natural voice interactions.

    Implements VAPI-style state management with:
    - Proper VAD state machine
    - Greedy inference
    - Fast interruption handling (<100ms)
    - Hands-free continuous conversation

    Attributes:
        conversation_state: Current conversation state (IDLE, LISTENING, etc.)
        vad_state: Current VAD state (QUIET, SPEAKING, etc.)
        hands_free_mode: Whether to auto-resume listening after assistant speaks
        on_state_change: Callback for state transitions
        on_start_listening: Callback when listening starts
        on_stop_listening: Callback when listening stops
        on_start_speaking: Callback when assistant starts speaking
        on_stop_speaking: Callback when assistant stops speaking
        on_interruption: Callback when user interrupts assistant
    """

    def __init__(self):
        """Initialize conversation state machine."""
        self.conversation_state = ConversationState.IDLE
        self.vad_state = VADState.QUIET
        self.last_state_change = datetime.now()
        self.hands_free_mode = True  # Enable by default
        self.pending_llm_request_id: Optional[str] = None  # For cancellation
        self.assistant_speaking_start_time: Optional[datetime] = None
        self.user_spoke_during_assistant = False

        # Callbacks for state transitions
        self.on_state_change: Optional[Callable] = None
        self.on_start_listening: Optional[Callable] = None
        self.on_stop_listening: Optional[Callable] = None
        self.on_start_speaking: Optional[Callable] = None
        self.on_stop_speaking: Optional[Callable] = None
        self.on_interruption: Optional[Callable] = None

    def _safe_callback(self, callback: Optional[Callable], *args, **kwargs):
        """
        Safely invoke callback, handling both sync and async functions.

        Args:
            callback: The callback function to invoke
            *args: Positional arguments to pass to callback
            **kwargs: Keyword arguments to pass to callback
        """
        if callback:
            try:
                # Check if callback is a coroutine function
                if inspect.iscoroutinefunction(callback):
                    # Create task to run async callback without blocking
                    asyncio.create_task(callback(*args, **kwargs))
                else:
                    # Call sync callback directly
                    callback(*args, **kwargs)
            except Exception as e:
                logger.error(f"❌ Error in callback {callback.__name__}: {e}")

    def _change_state(self, new_state: ConversationState):
        """
        Change conversation state and notify callbacks.

        Args:
            new_state: The new conversation state to transition to
        """
        if self.conversation_state != new_state:
            old_state = self.conversation_state
            self.conversation_state = new_state
            self.last_state_change = datetime.now()

            logger.info(f"🔄 Conversation state: {old_state.value} → {new_state.value}")

            self._safe_callback(self.on_state_change, old_state, new_state)

    def _change_vad_state(self, new_vad_state: VADState):
        """
        Change VAD state.

        Args:
            new_vad_state: The new VAD state to transition to
        """
        if self.vad_state != new_vad_state:
            old_vad = self.vad_state
            self.vad_state = new_vad_state
            logger.debug(f"🎤 VAD state: {old_vad.value} → {new_vad_state.value}")

    def start_listening(self):
        """
        User wants to start speaking.

        Handles interruption if assistant is currently speaking.
        """
        if self.conversation_state == ConversationState.SPEAKING:
            # Interrupt assistant
            logger.info("🎤 User interrupting assistant speech")
            self.user_spoke_during_assistant = True
            self._change_state(ConversationState.INTERRUPTED)
            self._safe_callback(self.on_interruption)
        elif self.conversation_state != ConversationState.LISTENING:
            self._change_state(ConversationState.LISTENING)
            self._safe_callback(self.on_start_listening)

        self._change_vad_state(VADState.STARTING)

    def stop_listening(self):
        """User finished speaking."""
        if self.conversation_state == ConversationState.LISTENING:
            self._change_state(ConversationState.PROCESSING)
            self._safe_callback(self.on_stop_listening)

        self._change_vad_state(VADState.STOPPING)

    def start_processing(self, request_id: str):
        """
        Start processing user utterance (greedy inference).

        Args:
            request_id: Unique ID for this processing request (for cancellation)
        """
        self.pending_llm_request_id = request_id
        self._change_state(ConversationState.PROCESSING)
        logger.info(f"🧠 Processing request {request_id}")

    def cancel_processing(self) -> bool:
        """
        Cancel current processing (user continued speaking).

        Returns:
            True if processing was cancelled, False if nothing to cancel
        """
        if self.pending_llm_request_id:
            logger.info(f"❌ Canceling LLM request {self.pending_llm_request_id}")
            self.pending_llm_request_id = None
            return True
        return False

    def start_speaking(self):
        """Assistant starts speaking."""
        logger.info("🔊 start_speaking() called - setting user_spoke_during_assistant=False")
        self._change_state(ConversationState.SPEAKING)
        self.assistant_speaking_start_time = datetime.now()
        self.user_spoke_during_assistant = False
        self.pending_llm_request_id = None

        self._safe_callback(self.on_start_speaking)

    def stop_speaking(self):
        """Assistant finished speaking."""
        speaking_duration = None
        if self.assistant_speaking_start_time:
            speaking_duration = (datetime.now() - self.assistant_speaking_start_time).total_seconds()
            logger.info(f"🔊 Assistant spoke for {speaking_duration:.2f}s")

        # Always return to IDLE - websocket handler will manage hands-free transition
        logger.info(
            f"✅ stop_speaking() called - changing to IDLE. "
            f"Current user_spoke_during_assistant={self.user_spoke_during_assistant}"
        )
        self._change_state(ConversationState.IDLE)

        self._safe_callback(self.on_stop_speaking)

        self.assistant_speaking_start_time = None

    def handle_vad_speech_detected(self):
        """VAD detected speech start."""
        if self.vad_state == VADState.QUIET:
            self._change_vad_state(VADState.STARTING)
        elif self.vad_state == VADState.STARTING:
            # Confirmed speech after 200ms
            self._change_vad_state(VADState.SPEAKING)

    def handle_vad_silence_detected(self):
        """VAD detected silence."""
        if self.vad_state == VADState.SPEAKING:
            self._change_vad_state(VADState.STOPPING)
        elif self.vad_state == VADState.STOPPING:
            # Confirmed silence after 800ms
            self._change_vad_state(VADState.QUIET)

    def can_record(self) -> bool:
        """
        Check if recording is allowed in current state.

        Returns:
            True if recording is allowed, False otherwise
        """
        # Cannot record while assistant is speaking (unless interrupting)
        if self.conversation_state == ConversationState.SPEAKING:
            return False
        # Cannot record while processing (greedy inference in progress)
        if self.conversation_state == ConversationState.PROCESSING:
            return False
        return True

    def should_auto_resume_listening(self) -> bool:
        """
        Check if should automatically resume listening after speaking.

        Returns:
            True if should auto-resume, False otherwise
        """
        result = (
            self.hands_free_mode and
            self.conversation_state == ConversationState.IDLE and
            not self.user_spoke_during_assistant
        )
        logger.info(
            f"🔍 should_auto_resume_listening check: "
            f"hands_free={self.hands_free_mode}, "
            f"state={self.conversation_state.value}, "
            f"user_spoke_during={self.user_spoke_during_assistant} → result={result}"
        )
        return result

    def reset(self):
        """Reset state machine to initial state."""
        self._change_state(ConversationState.IDLE)
        self._change_vad_state(VADState.QUIET)
        self.pending_llm_request_id = None
        self.assistant_speaking_start_time = None
        self.user_spoke_during_assistant = False

    def get_state_info(self) -> dict:
        """
        Get current state information.

        Returns:
            Dictionary with current state details
        """
        return {
            "conversation_state": self.conversation_state.value,
            "vad_state": self.vad_state.value,
            "hands_free_mode": self.hands_free_mode,
            "can_record": self.can_record(),
            "time_in_current_state": (datetime.now() - self.last_state_change).total_seconds()
        }


__all__ = [
    'ConversationStateMachine',
    'ConversationState',
    'VADState',
]
