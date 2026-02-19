"""
Conversation Data Models

Defines data structures for conversation state and turns.

Author: KasaAI Team
Date: 2025-11-26
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class TurnRole(str, Enum):
    """Role in conversation turn."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationStatus(str, Enum):
    """Status of a conversation."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class ConversationTurn(BaseModel):
    """
    A single turn in a conversation.

    Represents one exchange (user input + assistant response).
    """
    id: str = Field(..., description="Unique turn ID")
    conversation_id: str = Field(..., description="Parent conversation ID")
    role: TurnRole = Field(..., description="Who made this turn")
    content: str = Field(..., description="Text content of the turn")

    # Input metadata (for user turns)
    audio_duration: Optional[float] = Field(None, description="Audio duration in seconds")
    language: Optional[str] = Field(None, description="Detected/specified language")
    asr_provider: Optional[str] = Field(None, description="ASR provider used")
    asr_confidence: Optional[float] = Field(None, description="ASR confidence score")

    # Output metadata (for assistant turns)
    llm_model: Optional[str] = Field(None, description="LLM model used")
    llm_tokens: Optional[Dict[str, int]] = Field(None, description="Token usage")
    tts_provider: Optional[str] = Field(None, description="TTS provider used")
    audio_url: Optional[str] = Field(None, description="URL to generated audio")

    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: Optional[float] = Field(None, description="Processing time")

    # Cost tracking
    cost_usd: float = Field(default=0.0, description="Cost of this turn")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ConversationConfig(BaseModel):
    """
    Configuration for a conversation.

    Defines provider preferences and behavior settings.
    """
    # Provider settings
    asr_provider: str = Field(
        default="faster_whisper_large",
        description="ASR provider to use"
    )
    asr_language: Optional[str] = Field(
        None,
        description="Language for ASR (None = auto-detect)"
    )
    llm_model: str = Field(
        default="gemini-2.5-flash",
        description="LLM model to use"
    )
    llm_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="LLM temperature"
    )
    llm_max_tokens: int = Field(
        default=500,
        ge=1,
        le=4000,
        description="Max tokens for LLM response"
    )
    tts_provider: str = Field(
        default="coqui_xtts",
        description="TTS provider to use"
    )
    tts_voice: Optional[str] = Field(
        None,
        description="TTS voice ID"
    )
    tts_speed: float = Field(
        default=1.0,
        ge=0.5,
        le=2.0,
        description="TTS speech speed"
    )

    # Behavior settings
    system_prompt: Optional[str] = Field(
        None,
        description="System prompt for LLM"
    )
    max_history_turns: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Max turns to include in context"
    )
    auto_respond_with_audio: bool = Field(
        default=True,
        description="Generate TTS for responses"
    )

    # Cultural context
    cultural_context: Optional[str] = Field(
        None,
        description="Cultural context hint (e.g., 'ghana', 'nigeria')"
    )


class ConversationState(BaseModel):
    """
    State of a conversation.

    Tracks conversation history, metadata, and status.
    """
    id: str = Field(..., description="Unique conversation ID")
    user_id: str = Field(..., description="User who owns this conversation")
    organization_id: str = Field(
        default="default",
        description="Organization context"
    )

    # Configuration
    config: ConversationConfig = Field(
        default_factory=ConversationConfig,
        description="Conversation configuration"
    )

    # Status
    status: ConversationStatus = Field(
        default=ConversationStatus.ACTIVE,
        description="Conversation status"
    )

    # History
    turns: List[ConversationTurn] = Field(
        default_factory=list,
        description="Conversation turns"
    )

    # Metadata
    title: Optional[str] = Field(None, description="Conversation title")
    tags: List[str] = Field(default_factory=list, description="Tags for organization")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_turn_at: Optional[datetime] = Field(None, description="Time of last turn")

    # Cost tracking
    total_cost_usd: float = Field(default=0.0, description="Total cost")
    total_turns: int = Field(default=0, description="Total number of turns")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def add_turn(self, turn: ConversationTurn) -> None:
        """Add a turn to the conversation."""
        self.turns.append(turn)
        self.total_turns += 1
        self.total_cost_usd += turn.cost_usd
        self.last_turn_at = turn.created_at
        self.updated_at = datetime.utcnow()

    def get_history_for_llm(self) -> List[Dict[str, str]]:
        """
        Get conversation history formatted for LLM.

        Returns last N turns as messages list.
        """
        history = []

        # Add system prompt if configured
        if self.config.system_prompt:
            history.append({
                "role": "system",
                "content": self.config.system_prompt
            })

        # Get last N turns
        recent_turns = self.turns[-self.config.max_history_turns:]

        for turn in recent_turns:
            history.append({
                "role": turn.role.value,
                "content": turn.content
            })

        return history


class TurnResult(BaseModel):
    """
    Result from processing a conversation turn.

    Contains transcription, response, and optional audio.
    """
    conversation_id: str = Field(..., description="Conversation ID")
    turn_id: str = Field(..., description="New turn ID")

    # Transcription
    user_text: str = Field(..., description="Transcribed user input")
    detected_language: Optional[str] = Field(None, description="Detected language")

    # Response
    assistant_text: str = Field(..., description="Assistant response text")

    # Audio (if generated)
    audio_base64: Optional[str] = Field(None, description="Response audio")
    audio_format: str = Field(default="wav", description="Audio format")
    audio_duration: Optional[float] = Field(None, description="Audio duration")

    # Costs
    asr_cost: float = Field(default=0.0)
    llm_cost: float = Field(default=0.0)
    tts_cost: float = Field(default=0.0)
    total_cost: float = Field(default=0.0)

    # Timing
    processing_time_ms: float = Field(..., description="Total processing time")
    asr_time_ms: Optional[float] = Field(None)
    llm_time_ms: Optional[float] = Field(None)
    tts_time_ms: Optional[float] = Field(None)

    # Metadata
    providers_used: Dict[str, Optional[str]] = Field(
        default_factory=dict,
        description="Providers used for each step"
    )
