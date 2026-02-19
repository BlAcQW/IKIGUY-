"""
Conversation State Machine for Core Backend Voice Chat.

DEPRECATED: This module is deprecated. Please use the shared library instead:
    from apps.shared.voice import ConversationStateMachine, ConversationState, VADState

This module re-exports from apps.shared.voice for backwards compatibility.
"""

import warnings
import sys

# Add shared to path
sys.path.insert(0, '/opt/kasaai/apps')

warnings.warn(
    "core_backend.services.conversation_state_machine is deprecated. "
    "Use apps.shared.voice instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from shared for backwards compatibility
from apps.shared.voice import (
    ConversationStateMachine,
    ConversationState,
    VADState,
)

__all__ = ['ConversationStateMachine', 'ConversationState', 'VADState']
