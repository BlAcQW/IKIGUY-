"""
Shared Voice Conversation Components.

Provides reusable components for real-time voice conversations:
- ConversationStateMachine: Turn-taking and state management
- PCMVADHandler: PCM audio processing with VAD

Usage:
    from apps.shared.voice import (
        ConversationStateMachine,
        ConversationState,
        VADState,
        PCMVADHandler,
        pcm_to_wav,
    )

Author: AI Labs Africa
"""

from .conversation_state_machine import (
    ConversationStateMachine,
    ConversationState,
    VADState,
)
from .pcm_vad_handler import (
    PCMVADHandler,
    SimplePCMAccumulator,
    pcm_to_wav,
    pcm_base64_to_wav_base64,
)

__all__ = [
    # State machine
    "ConversationStateMachine",
    "ConversationState",
    "VADState",
    # PCM/VAD handling
    "PCMVADHandler",
    "SimplePCMAccumulator",
    "pcm_to_wav",
    "pcm_base64_to_wav_base64",
]
