"""
Tests for conversation pipeline.

Tests the ASR -> LLM -> TTS orchestration.
"""

import pytest
import pytest_asyncio
import base64
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from apps.shared.conversation.pipeline import ConversationPipeline
from apps.shared.conversation.manager import ConversationManager
from apps.shared.conversation.models import (
    ConversationState,
    ConversationTurn,
    ConversationConfig,
    ConversationStatus,
    TurnRole,
)


@pytest_asyncio.fixture
async def mock_manager():
    """Create a mock conversation manager."""
    manager = AsyncMock(spec=ConversationManager)

    # Default conversation state
    conversation = ConversationState(
        id="conv_test123",
        user_id="user_123",
        config=ConversationConfig(
            system_prompt="You are a helpful assistant.",
            auto_respond_with_audio=True,
        ),
    )

    manager.get_conversation = AsyncMock(return_value=conversation)
    manager.add_turn = AsyncMock(return_value=conversation)
    manager.create_conversation = AsyncMock(return_value=conversation)
    manager.end_conversation = AsyncMock(return_value=conversation)

    return manager


@pytest_asyncio.fixture
async def mock_asr_service():
    """Create a mock ASR service."""
    service = AsyncMock()
    service.transcribe = AsyncMock(return_value={
        "text": "Hello, how are you?",
        "language": "en",
        "confidence": 0.95,
        "cost": 0.001,
    })
    return service


@pytest_asyncio.fixture
async def mock_llm_service():
    """Create a mock LLM service."""
    service = AsyncMock()
    service.chat = AsyncMock(return_value={
        "response": "I'm doing well, thank you for asking!",
        "tokens": {"input": 10, "output": 12},
        "cost": 0.002,
    })

    async def stream_mock(messages, **kwargs):
        chunks = ["I'm ", "doing ", "well!"]
        for chunk in chunks:
            yield chunk

    service.stream_chat = stream_mock
    return service


@pytest_asyncio.fixture
async def mock_tts_client():
    """Create a mock TTS client."""
    client = AsyncMock()
    # Return raw bytes
    client.synthesize = AsyncMock(return_value={
        "audio": b"fake_audio_data",
        "duration": 1.5,
        "cost": 0.003,
    })
    return client


@pytest_asyncio.fixture
async def pipeline(mock_manager, mock_asr_service, mock_llm_service, mock_tts_client):
    """Create a conversation pipeline with mock services."""
    return ConversationPipeline(
        conversation_manager=mock_manager,
        asr_service=mock_asr_service,
        llm_service=mock_llm_service,
        tts_client=mock_tts_client,
    )


class TestConversationPipeline:
    """Tests for ConversationPipeline class."""

    @pytest.mark.asyncio
    async def test_process_voice_turn_success(
        self,
        pipeline,
        mock_manager,
        mock_asr_service,
        mock_llm_service,
        mock_tts_client,
    ):
        """Test successful voice turn processing."""
        # Create fake audio
        audio_base64 = base64.b64encode(b"fake_audio").decode("utf-8")

        result = await pipeline.process_voice_turn(
            conversation_id="conv_test123",
            audio_base64=audio_base64,
            user_id="user_123",
        )

        # Verify result
        assert result.conversation_id == "conv_test123"
        assert result.user_text == "Hello, how are you?"
        assert result.detected_language == "en"
        assert result.assistant_text == "I'm doing well, thank you for asking!"
        assert result.audio_base64 is not None
        assert result.processing_time_ms > 0

        # Verify services were called
        mock_asr_service.transcribe.assert_called_once()
        mock_llm_service.chat.assert_called_once()
        mock_tts_client.synthesize.assert_called_once()

        # Verify turns were added
        assert mock_manager.add_turn.call_count == 2  # user + assistant

    @pytest.mark.asyncio
    async def test_process_voice_turn_no_audio_generation(
        self,
        pipeline,
        mock_manager,
        mock_tts_client,
    ):
        """Test voice turn without audio generation."""
        audio_base64 = base64.b64encode(b"fake_audio").decode("utf-8")

        result = await pipeline.process_voice_turn(
            conversation_id="conv_test123",
            audio_base64=audio_base64,
            generate_audio=False,
        )

        assert result.audio_base64 is None
        mock_tts_client.synthesize.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_voice_turn_conversation_not_found(
        self,
        pipeline,
        mock_manager,
    ):
        """Test voice turn with non-existent conversation."""
        mock_manager.get_conversation = AsyncMock(return_value=None)
        audio_base64 = base64.b64encode(b"fake_audio").decode("utf-8")

        with pytest.raises(ValueError, match="not found"):
            await pipeline.process_voice_turn(
                conversation_id="conv_invalid",
                audio_base64=audio_base64,
            )

    @pytest.mark.asyncio
    async def test_process_voice_turn_empty_transcription(
        self,
        pipeline,
        mock_asr_service,
    ):
        """Test voice turn with empty transcription."""
        mock_asr_service.transcribe = AsyncMock(return_value={
            "text": "",
            "language": None,
            "confidence": 0.0,
            "cost": 0.0,
        })
        audio_base64 = base64.b64encode(b"fake_audio").decode("utf-8")

        with pytest.raises(ValueError, match="No speech detected"):
            await pipeline.process_voice_turn(
                conversation_id="conv_test123",
                audio_base64=audio_base64,
            )

    @pytest.mark.asyncio
    async def test_process_text_turn_success(
        self,
        pipeline,
        mock_manager,
        mock_llm_service,
    ):
        """Test successful text turn processing."""
        result = await pipeline.process_text_turn(
            conversation_id="conv_test123",
            user_text="What is Python?",
            user_id="user_123",
        )

        assert result.conversation_id == "conv_test123"
        assert result.user_text == "What is Python?"
        assert result.assistant_text == "I'm doing well, thank you for asking!"
        assert result.asr_cost == 0.0
        assert result.audio_base64 is None

        mock_llm_service.chat.assert_called_once()
        assert mock_manager.add_turn.call_count == 2

    @pytest.mark.asyncio
    async def test_process_text_turn_with_audio(
        self,
        pipeline,
        mock_tts_client,
    ):
        """Test text turn with audio generation."""
        result = await pipeline.process_text_turn(
            conversation_id="conv_test123",
            user_text="Tell me a story",
            generate_audio=True,
        )

        assert result.audio_base64 is not None
        mock_tts_client.synthesize.assert_called_once()

    @pytest.mark.asyncio
    async def test_stream_response(
        self,
        pipeline,
        mock_manager,
        mock_llm_service,
    ):
        """Test streaming response generation."""
        chunks = []
        async for chunk in pipeline.stream_response(
            conversation_id="conv_test123",
            user_text="Tell me about AI",
        ):
            chunks.append(chunk)

        assert len(chunks) == 3
        assert "".join(chunks) == "I'm doing well!"

    @pytest.mark.asyncio
    async def test_create_conversation_via_pipeline(
        self,
        pipeline,
        mock_manager,
    ):
        """Test creating conversation through pipeline."""
        config = ConversationConfig(
            llm_model="gemini-1.5-pro",
            system_prompt="You are a tutor.",
        )

        result = await pipeline.create_conversation(
            user_id="user_123",
            organization_id="org_456",
            config=config,
            title="New Chat",
        )

        assert result is not None
        mock_manager.create_conversation.assert_called_once_with(
            user_id="user_123",
            organization_id="org_456",
            config=config,
            title="New Chat",
            metadata=None,
        )

    @pytest.mark.asyncio
    async def test_end_conversation_via_pipeline(
        self,
        pipeline,
        mock_manager,
    ):
        """Test ending conversation through pipeline."""
        result = await pipeline.end_conversation(
            conversation_id="conv_test123",
            user_id="user_123",
        )

        assert result is not None
        mock_manager.end_conversation.assert_called_once()


class TestPipelineWithoutServices:
    """Tests for pipeline behavior without services configured."""

    @pytest.mark.asyncio
    async def test_pipeline_without_asr_service(self, mock_manager):
        """Test pipeline handles missing ASR service."""
        pipeline = ConversationPipeline(
            conversation_manager=mock_manager,
            asr_service=None,
            llm_service=AsyncMock(),
            tts_client=AsyncMock(),
        )

        audio_base64 = base64.b64encode(b"fake_audio").decode("utf-8")

        # Should raise due to empty transcription
        with pytest.raises(ValueError, match="No speech detected"):
            await pipeline.process_voice_turn(
                conversation_id="conv_test123",
                audio_base64=audio_base64,
            )

    @pytest.mark.asyncio
    async def test_pipeline_without_llm_service(self, mock_manager):
        """Test pipeline handles missing LLM service."""
        pipeline = ConversationPipeline(
            conversation_manager=mock_manager,
            asr_service=AsyncMock(transcribe=AsyncMock(return_value={
                "text": "Hello",
                "language": "en",
                "confidence": 0.9,
                "cost": 0.0,
            })),
            llm_service=None,
            tts_client=None,
        )

        audio_base64 = base64.b64encode(b"fake_audio").decode("utf-8")

        result = await pipeline.process_voice_turn(
            conversation_id="conv_test123",
            audio_base64=audio_base64,
            generate_audio=False,
        )

        # Should use default response
        assert "How can I help you" in result.assistant_text

    @pytest.mark.asyncio
    async def test_pipeline_without_tts_client(self, mock_manager):
        """Test pipeline handles missing TTS client."""
        pipeline = ConversationPipeline(
            conversation_manager=mock_manager,
            asr_service=AsyncMock(transcribe=AsyncMock(return_value={
                "text": "Hello",
                "language": "en",
                "confidence": 0.9,
                "cost": 0.0,
            })),
            llm_service=AsyncMock(chat=AsyncMock(return_value={
                "response": "Hi there!",
                "tokens": {},
                "cost": 0.0,
            })),
            tts_client=None,
        )

        audio_base64 = base64.b64encode(b"fake_audio").decode("utf-8")

        result = await pipeline.process_voice_turn(
            conversation_id="conv_test123",
            audio_base64=audio_base64,
            generate_audio=True,  # Request audio but no client
        )

        # Should return None for audio
        assert result.audio_base64 is None


class TestCostTracking:
    """Tests for cost tracking in pipeline."""

    @pytest.mark.asyncio
    async def test_voice_turn_cost_aggregation(
        self,
        pipeline,
    ):
        """Test that costs are properly aggregated."""
        audio_base64 = base64.b64encode(b"fake_audio").decode("utf-8")

        result = await pipeline.process_voice_turn(
            conversation_id="conv_test123",
            audio_base64=audio_base64,
        )

        # Costs from mocks: ASR=0.001, LLM=0.002, TTS=0.003
        assert result.asr_cost == 0.001
        assert result.llm_cost == 0.002
        assert result.tts_cost == 0.003
        assert result.total_cost == 0.006

    @pytest.mark.asyncio
    async def test_text_turn_cost_no_asr(
        self,
        pipeline,
    ):
        """Test text turn has no ASR cost."""
        result = await pipeline.process_text_turn(
            conversation_id="conv_test123",
            user_text="Hello",
            generate_audio=False,
        )

        assert result.asr_cost == 0.0
        # Only LLM cost
        assert result.llm_cost == 0.002
        assert result.total_cost == 0.002

    @pytest.mark.asyncio
    async def test_providers_used_tracking(
        self,
        pipeline,
    ):
        """Test that providers used are tracked."""
        audio_base64 = base64.b64encode(b"fake_audio").decode("utf-8")

        result = await pipeline.process_voice_turn(
            conversation_id="conv_test123",
            audio_base64=audio_base64,
        )

        assert "asr" in result.providers_used
        assert "llm" in result.providers_used
        assert "tts" in result.providers_used
        assert result.providers_used["asr"] == "faster_whisper_large"
        assert result.providers_used["llm"] == "gemini-2.5-flash"
        assert result.providers_used["tts"] == "coqui_xtts"


class TestTimingTracking:
    """Tests for timing tracking in pipeline."""

    @pytest.mark.asyncio
    async def test_voice_turn_timing(
        self,
        pipeline,
    ):
        """Test that timing is tracked for each step."""
        audio_base64 = base64.b64encode(b"fake_audio").decode("utf-8")

        result = await pipeline.process_voice_turn(
            conversation_id="conv_test123",
            audio_base64=audio_base64,
        )

        # All timings should be positive
        assert result.asr_time_ms >= 0
        assert result.llm_time_ms >= 0
        assert result.tts_time_ms >= 0
        assert result.processing_time_ms >= 0

        # Total should be at least sum of parts
        assert result.processing_time_ms >= (
            result.asr_time_ms + result.llm_time_ms + result.tts_time_ms
        )

    @pytest.mark.asyncio
    async def test_text_turn_no_asr_timing(
        self,
        pipeline,
    ):
        """Test text turn has zero ASR timing."""
        result = await pipeline.process_text_turn(
            conversation_id="conv_test123",
            user_text="Hello",
        )

        assert result.asr_time_ms == 0.0
        assert result.llm_time_ms >= 0
