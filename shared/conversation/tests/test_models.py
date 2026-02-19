"""
Tests for conversation models.

Tests data structures for conversation state and turns.
"""

import pytest
from datetime import datetime
from apps.shared.conversation.models import (
    TurnRole,
    ConversationStatus,
    ConversationTurn,
    ConversationConfig,
    ConversationState,
    TurnResult,
)


class TestTurnRole:
    """Tests for TurnRole enum."""

    def test_turn_role_values(self):
        """Test turn role enum values."""
        assert TurnRole.USER.value == "user"
        assert TurnRole.ASSISTANT.value == "assistant"
        assert TurnRole.SYSTEM.value == "system"

    def test_turn_role_from_string(self):
        """Test creating turn role from string."""
        assert TurnRole("user") == TurnRole.USER
        assert TurnRole("assistant") == TurnRole.ASSISTANT


class TestConversationStatus:
    """Tests for ConversationStatus enum."""

    def test_status_values(self):
        """Test conversation status values."""
        assert ConversationStatus.ACTIVE.value == "active"
        assert ConversationStatus.PAUSED.value == "paused"
        assert ConversationStatus.COMPLETED.value == "completed"
        assert ConversationStatus.FAILED.value == "failed"


class TestConversationTurn:
    """Tests for ConversationTurn model."""

    def test_create_user_turn(self):
        """Test creating a user turn."""
        turn = ConversationTurn(
            id="turn_001",
            conversation_id="conv_001",
            role=TurnRole.USER,
            content="Hello, how are you?",
            audio_duration=2.5,
            language="en",
            asr_provider="faster_whisper_large",
            asr_confidence=0.95,
        )

        assert turn.id == "turn_001"
        assert turn.role == TurnRole.USER
        assert turn.content == "Hello, how are you?"
        assert turn.audio_duration == 2.5
        assert turn.asr_provider == "faster_whisper_large"
        assert turn.cost_usd == 0.0

    def test_create_assistant_turn(self):
        """Test creating an assistant turn."""
        turn = ConversationTurn(
            id="turn_002",
            conversation_id="conv_001",
            role=TurnRole.ASSISTANT,
            content="I'm doing well, thank you!",
            llm_model="gemini-2.5-flash",
            llm_tokens={"input": 10, "output": 8},
            tts_provider="coqui_xtts",
            cost_usd=0.001,
        )

        assert turn.role == TurnRole.ASSISTANT
        assert turn.llm_model == "gemini-2.5-flash"
        assert turn.llm_tokens == {"input": 10, "output": 8}
        assert turn.cost_usd == 0.001

    def test_turn_default_values(self):
        """Test turn default values."""
        turn = ConversationTurn(
            id="turn_003",
            conversation_id="conv_001",
            role=TurnRole.USER,
            content="Test",
        )

        assert turn.audio_duration is None
        assert turn.language is None
        assert turn.llm_model is None
        assert turn.cost_usd == 0.0
        assert isinstance(turn.created_at, datetime)


class TestConversationConfig:
    """Tests for ConversationConfig model."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ConversationConfig()

        assert config.asr_provider == "faster_whisper_large"
        assert config.asr_language is None
        assert config.llm_model == "gemini-2.5-flash"
        assert config.llm_temperature == 0.7
        assert config.llm_max_tokens == 500
        assert config.tts_provider == "coqui_xtts"
        assert config.tts_voice is None
        assert config.tts_speed == 1.0
        assert config.max_history_turns == 10
        assert config.auto_respond_with_audio is True

    def test_custom_config(self):
        """Test custom configuration."""
        config = ConversationConfig(
            asr_provider="openai_whisper",
            llm_model="gemini-1.5-pro",
            llm_temperature=0.5,
            tts_provider="openai",
            tts_voice="alloy",
            system_prompt="You are a helpful assistant.",
            cultural_context="ghana",
        )

        assert config.asr_provider == "openai_whisper"
        assert config.llm_model == "gemini-1.5-pro"
        assert config.system_prompt == "You are a helpful assistant."
        assert config.cultural_context == "ghana"

    def test_config_validation(self):
        """Test configuration validation."""
        # Temperature out of range
        with pytest.raises(ValueError):
            ConversationConfig(llm_temperature=3.0)

        # Speed out of range
        with pytest.raises(ValueError):
            ConversationConfig(tts_speed=3.0)

        # Max tokens out of range
        with pytest.raises(ValueError):
            ConversationConfig(llm_max_tokens=5000)


class TestConversationState:
    """Tests for ConversationState model."""

    def test_create_conversation_state(self):
        """Test creating conversation state."""
        state = ConversationState(
            id="conv_001",
            user_id="user_123",
            organization_id="org_456",
            title="Test Conversation",
        )

        assert state.id == "conv_001"
        assert state.user_id == "user_123"
        assert state.organization_id == "org_456"
        assert state.title == "Test Conversation"
        assert state.status == ConversationStatus.ACTIVE
        assert state.turns == []
        assert state.total_cost_usd == 0.0
        assert state.total_turns == 0

    def test_add_turn_method(self):
        """Test adding turns to conversation."""
        state = ConversationState(
            id="conv_001",
            user_id="user_123",
        )

        turn1 = ConversationTurn(
            id="turn_001",
            conversation_id="conv_001",
            role=TurnRole.USER,
            content="Hello",
            cost_usd=0.001,
        )

        state.add_turn(turn1)

        assert len(state.turns) == 1
        assert state.total_turns == 1
        assert state.total_cost_usd == 0.001
        assert state.last_turn_at is not None

    def test_get_history_for_llm(self):
        """Test getting conversation history for LLM."""
        state = ConversationState(
            id="conv_001",
            user_id="user_123",
            config=ConversationConfig(
                system_prompt="You are a helpful tutor.",
                max_history_turns=5,
            ),
        )

        # Add some turns
        state.add_turn(ConversationTurn(
            id="turn_001",
            conversation_id="conv_001",
            role=TurnRole.USER,
            content="What is Python?",
        ))

        state.add_turn(ConversationTurn(
            id="turn_002",
            conversation_id="conv_001",
            role=TurnRole.ASSISTANT,
            content="Python is a programming language.",
        ))

        history = state.get_history_for_llm()

        assert len(history) == 3  # system + 2 turns
        assert history[0]["role"] == "system"
        assert history[0]["content"] == "You are a helpful tutor."
        assert history[1]["role"] == "user"
        assert history[2]["role"] == "assistant"

    def test_history_truncation(self):
        """Test that history is truncated to max_history_turns."""
        state = ConversationState(
            id="conv_001",
            user_id="user_123",
            config=ConversationConfig(max_history_turns=2),
        )

        # Add more turns than max
        for i in range(5):
            state.add_turn(ConversationTurn(
                id=f"turn_{i}",
                conversation_id="conv_001",
                role=TurnRole.USER if i % 2 == 0 else TurnRole.ASSISTANT,
                content=f"Message {i}",
            ))

        history = state.get_history_for_llm()

        # Should only have last 2 turns
        assert len(history) == 2
        assert "Message 3" in history[0]["content"]
        assert "Message 4" in history[1]["content"]


class TestTurnResult:
    """Tests for TurnResult model."""

    def test_create_turn_result(self):
        """Test creating turn result."""
        result = TurnResult(
            conversation_id="conv_001",
            turn_id="turn_002",
            user_text="What is AI?",
            detected_language="en",
            assistant_text="AI stands for Artificial Intelligence.",
            asr_cost=0.001,
            llm_cost=0.002,
            tts_cost=0.003,
            total_cost=0.006,
            processing_time_ms=1500.0,
            asr_time_ms=300.0,
            llm_time_ms=800.0,
            tts_time_ms=400.0,
            providers_used={
                "asr": "faster_whisper_large",
                "llm": "gemini-2.5-flash",
                "tts": "coqui_xtts",
            },
        )

        assert result.conversation_id == "conv_001"
        assert result.user_text == "What is AI?"
        assert result.assistant_text == "AI stands for Artificial Intelligence."
        assert result.total_cost == 0.006
        assert result.processing_time_ms == 1500.0

    def test_turn_result_with_audio(self):
        """Test turn result with audio response."""
        result = TurnResult(
            conversation_id="conv_001",
            turn_id="turn_002",
            user_text="Hello",
            assistant_text="Hi there!",
            audio_base64="SGVsbG8gV29ybGQ=",
            audio_format="wav",
            audio_duration=1.5,
            processing_time_ms=500.0,
        )

        assert result.audio_base64 is not None
        assert result.audio_format == "wav"
        assert result.audio_duration == 1.5

    def test_turn_result_defaults(self):
        """Test turn result default values."""
        result = TurnResult(
            conversation_id="conv_001",
            turn_id="turn_001",
            user_text="Test",
            assistant_text="Response",
            processing_time_ms=100.0,
        )

        assert result.audio_base64 is None
        assert result.audio_format == "wav"
        assert result.asr_cost == 0.0
        assert result.llm_cost == 0.0
        assert result.tts_cost == 0.0
        assert result.total_cost == 0.0
