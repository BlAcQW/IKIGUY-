"""
Conversation Pipeline Module

Provides multi-turn voice conversation capabilities for all apps.
Orchestrates ASR -> LLM -> TTS pipeline with context management.

Usage:
    from apps.shared.conversation import (
        ConversationPipeline,
        ConversationManager,
        ConversationTurn,
        ConversationState,
    )

    # Create pipeline with services
    pipeline = ConversationPipeline(
        asr_service=asr_service,
        llm_service=llm_service,
        tts_service=tts_service,
    )

    # Process a voice turn
    response = await pipeline.process_voice_turn(
        conversation_id="conv_123",
        audio_base64="...",
        context={"user_id": "user_456"}
    )

Author: KasaAI Team
Date: 2025-11-26
"""

from .models import (
    ConversationTurn,
    ConversationState,
    ConversationConfig,
    TurnResult,
)
from .manager import ConversationManager
from .pipeline import ConversationPipeline

__all__ = [
    "ConversationTurn",
    "ConversationState",
    "ConversationConfig",
    "TurnResult",
    "ConversationManager",
    "ConversationPipeline",
]
