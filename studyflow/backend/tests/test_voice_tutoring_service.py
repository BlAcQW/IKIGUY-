"""
Unit tests for Voice Tutoring Service enhancements.

Tests the material-aware voice tutoring functionality including:
- Material ID extraction from session metadata
- RAG filtering by material_id
- Custom prompts with material context
- Conversation history loading
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime
from bson import ObjectId

from app.services.voice_tutoring_service import VoiceTutoringService
from app.models.material import StudyMaterial, ProcessingStatus, MaterialType
from app.models.session import StudySession, SessionStatus


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_material():
    """Sample study material for testing."""
    return StudyMaterial(
        id="674f0a1234567890abcdef12",
        organization_id="org123",
        school_id="school123",
        title="Introduction to Algebra",
        description="Basic algebra concepts for Grade 9",
        file_name="algebra.pdf",
        file_path="/path/to/algebra.pdf",
        file_size=1024000,
        file_type=MaterialType.PDF,
        subject="Mathematics",
        topics=["Linear Equations", "Quadratic Equations", "Polynomials"],
        grade=9,
        uploaded_by="teacher123",
        status=ProcessingStatus.COMPLETED,
        chunks_count=50,
        embedding_collection="studyflow_org123_mathematics",
        metadata={},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def sample_session_with_material():
    """Sample session with material_id in metadata."""
    return StudySession(
        id="session123",
        organization_id="org123",
        school_id="school123",
        student_id="student123",
        subject="Mathematics",
        topics=["Linear Equations"],
        status=SessionStatus.ACTIVE,
        started_at=datetime.utcnow(),
        questions_asked=5,
        questions_answered=5,
        cost_incurred=0.05,
        metadata={
            "material_id": "674f0a1234567890abcdef12",
            "session_type": "voice_tutoring"
        }
    )


@pytest.fixture
def sample_session_without_material():
    """Sample session without material_id."""
    return StudySession(
        id="session456",
        organization_id="org123",
        school_id="school123",
        student_id="student123",
        subject="Science",
        topics=["Physics", "Motion"],
        status=SessionStatus.ACTIVE,
        started_at=datetime.utcnow(),
        questions_asked=2,
        questions_answered=2,
        cost_incurred=0.02,
        metadata={}
    )


@pytest.fixture
def sample_conversation_history():
    """Sample conversation history for testing."""
    return [
        {"role": "user", "content": "What is a linear equation?"},
        {"role": "assistant", "content": "A linear equation is an equation where the variable is raised to the power of 1."},
        {"role": "user", "content": "Can you give me an example?"},
        {"role": "assistant", "content": "Sure! An example is 2x + 3 = 7, where x is the variable."}
    ]


# ============================================================================
# Tests: get_material_by_id
# ============================================================================

class TestGetMaterialById:
    """Tests for get_material_by_id helper method."""

    @pytest.mark.asyncio
    async def test_get_material_by_id_success(self, sample_material):
        """Test successful material retrieval."""
        with patch("app.services.voice_tutoring_service.mongodb") as mock_mongo:
            mock_collection = AsyncMock()
            # Create a raw document as would be returned from MongoDB
            mock_material_doc = {
                "_id": ObjectId("674f0a1234567890abcdef12"),
                "organization_id": "org123",
                "school_id": "school123",
                "title": "Introduction to Algebra",
                "description": "Basic algebra concepts for Grade 9",
                "file_name": "algebra.pdf",
                "file_path": "/path/to/algebra.pdf",
                "file_size": 1024000,
                "file_type": "pdf",
                "subject": "Mathematics",
                "topics": ["Linear Equations", "Quadratic Equations", "Polynomials"],
                "grade": 9,
                "uploaded_by": "teacher123",
                "status": "completed",
                "chunks_count": 50,
                "embedding_collection": "studyflow_org123_mathematics",
                "metadata": {},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            mock_collection.find_one = AsyncMock(return_value=mock_material_doc)
            mock_mongo.get_collection.return_value = mock_collection

            result = await VoiceTutoringService.get_material_by_id(
                material_id="674f0a1234567890abcdef12",
                organization_id="org123"
            )

            assert result is not None
            assert result.title == "Introduction to Algebra"
            assert result.subject == "Mathematics"
            mock_collection.find_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_material_by_id_not_found(self):
        """Test material not found returns None."""
        with patch("app.services.voice_tutoring_service.mongodb") as mock_mongo:
            mock_collection = AsyncMock()
            mock_collection.find_one = AsyncMock(return_value=None)
            mock_mongo.get_collection.return_value = mock_collection

            result = await VoiceTutoringService.get_material_by_id(
                material_id="nonexistent123",
                organization_id="org123"
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_get_material_by_id_wrong_org(self):
        """Test material from different organization returns None."""
        with patch("app.services.voice_tutoring_service.mongodb") as mock_mongo:
            mock_collection = AsyncMock()
            # Returns None because organization_id doesn't match
            mock_collection.find_one = AsyncMock(return_value=None)
            mock_mongo.get_collection.return_value = mock_collection

            result = await VoiceTutoringService.get_material_by_id(
                material_id="674f0a1234567890abcdef12",
                organization_id="wrong_org"
            )

            assert result is None


# ============================================================================
# Tests: get_conversation_history
# ============================================================================

class TestGetConversationHistory:
    """Tests for get_conversation_history helper method."""

    @pytest.mark.asyncio
    async def test_get_conversation_history_success(self):
        """Test successful conversation history retrieval."""
        mock_questions = [
            {
                "_id": ObjectId(),
                "question_text": "What is algebra?",
                "answer_text": "Algebra is a branch of mathematics.",
                "created_at": datetime.utcnow()
            },
            {
                "_id": ObjectId(),
                "question_text": "What are variables?",
                "answer_text": "Variables represent unknown values.",
                "created_at": datetime.utcnow()
            }
        ]

        with patch("app.services.voice_tutoring_service.mongodb") as mock_mongo:
            mock_collection = MagicMock()

            # Create proper async iterator class with method chaining support
            class AsyncCursor:
                def __init__(self, items):
                    self.items = items
                    self.index = 0

                def sort(self, *args, **kwargs):
                    return self

                def limit(self, *args, **kwargs):
                    return self

                def __aiter__(self):
                    return self

                async def __anext__(self):
                    if self.index >= len(self.items):
                        raise StopAsyncIteration
                    item = self.items[self.index]
                    self.index += 1
                    return item

            mock_collection.find.return_value = AsyncCursor(mock_questions)
            mock_mongo.get_collection.return_value = mock_collection

            result = await VoiceTutoringService.get_conversation_history(
                session_id="session123",
                limit=10
            )

            assert isinstance(result, list)
            # Each question creates 2 entries (user + assistant)
            assert len(result) == 4
            # Check the content is correct
            assert result[0]["role"] == "user"
            assert result[0]["content"] == "What is algebra?"
            assert result[1]["role"] == "assistant"
            assert result[1]["content"] == "Algebra is a branch of mathematics."

    @pytest.mark.asyncio
    async def test_get_conversation_history_empty(self):
        """Test empty conversation history."""
        with patch("app.services.voice_tutoring_service.mongodb") as mock_mongo:
            mock_collection = MagicMock()

            # Create empty async cursor with method chaining support
            class EmptyAsyncCursor:
                def sort(self, *args, **kwargs):
                    return self

                def limit(self, *args, **kwargs):
                    return self

                def __aiter__(self):
                    return self

                async def __anext__(self):
                    raise StopAsyncIteration

            mock_collection.find.return_value = EmptyAsyncCursor()
            mock_mongo.get_collection.return_value = mock_collection

            result = await VoiceTutoringService.get_conversation_history(
                session_id="new_session",
                limit=10
            )

            assert result == []


# ============================================================================
# Tests: build_material_aware_prompt
# ============================================================================

class TestBuildMaterialAwarePrompt:
    """Tests for build_material_aware_prompt helper method."""

    def test_prompt_with_material(self, sample_material, sample_session_with_material):
        """Test prompt generation with material context."""
        prompt = VoiceTutoringService.build_material_aware_prompt(
            material=sample_material,
            session=sample_session_with_material
        )

        assert "Introduction to Algebra" in prompt
        assert "Basic algebra concepts for Grade 9" in prompt
        assert "Linear Equations" in prompt
        assert "Quadratic Equations" in prompt
        assert "Mathematics" in prompt
        assert "Grade level: 9" in prompt

    def test_prompt_without_material(self, sample_session_without_material):
        """Test prompt generation without material context."""
        prompt = VoiceTutoringService.build_material_aware_prompt(
            material=None,
            session=sample_session_without_material
        )

        assert "Science" in prompt
        assert "Physics" in prompt or "Motion" in prompt
        # Should not have material-specific content
        assert "Introduction to Algebra" not in prompt

    def test_prompt_contains_tutoring_guidelines(self, sample_material, sample_session_with_material):
        """Test that prompt contains tutoring guidelines."""
        prompt = VoiceTutoringService.build_material_aware_prompt(
            material=sample_material,
            session=sample_session_with_material
        )

        assert "educational" in prompt.lower()
        assert "step-by-step" in prompt
        assert "{context}" in prompt
        assert "{query}" in prompt


# ============================================================================
# Tests: process_voice_question (Integration)
# ============================================================================

class TestProcessVoiceQuestion:
    """Tests for process_voice_question with material enhancements."""

    @pytest.mark.asyncio
    async def test_process_voice_question_with_material(
        self,
        sample_material,
        sample_session_with_material
    ):
        """Test voice question processing with material context."""
        mock_voice_result = Mock()
        mock_voice_result.transcribed_text = "What is a linear equation?"
        mock_voice_result.response_text = "A linear equation is..."
        mock_voice_result.response_audio_base64 = "base64audio..."
        mock_voice_result.audio_duration = 5.0
        mock_voice_result.confidence_score = 0.9
        mock_voice_result.sources_used = ["page 5"]
        mock_voice_result.asr_cost = 0.01
        mock_voice_result.llm_cost = 0.02
        mock_voice_result.tts_cost = 0.01
        mock_voice_result.total_cost = 0.04
        mock_voice_result.detected_language = "en"
        mock_voice_result.asr_transaction_id = "asr123"
        mock_voice_result.tts_transaction_id = "tts123"
        mock_voice_result.asr_processing_time = 1.0
        mock_voice_result.rag_processing_time = 2.0
        mock_voice_result.tts_processing_time = 1.0
        mock_voice_result.total_processing_time = 4.0

        with patch.object(VoiceTutoringService, 'get_voice_service') as mock_get_service, \
             patch("app.services.voice_tutoring_service.TutoringService") as mock_tutoring, \
             patch.object(VoiceTutoringService, 'get_material_by_id') as mock_get_material, \
             patch.object(VoiceTutoringService, 'get_conversation_history') as mock_get_history, \
             patch("app.services.voice_tutoring_service.mongodb") as mock_mongo, \
             patch("app.services.voice_tutoring_service.ProgressService") as mock_progress:

            # Setup mocks
            mock_tutoring.get_session = AsyncMock(return_value=sample_session_with_material)
            mock_tutoring.get_collection_name_for_subject.return_value = "studyflow_org123_mathematics"
            mock_tutoring._update_session_stats = AsyncMock()
            mock_get_material.return_value = sample_material
            mock_get_history.return_value = []

            mock_voice_service = AsyncMock()
            mock_voice_service.process_voice_message = AsyncMock(return_value=mock_voice_result)
            mock_get_service.return_value = mock_voice_service

            mock_collection = AsyncMock()
            mock_collection.insert_one = AsyncMock(return_value=Mock(inserted_id=ObjectId()))
            mock_mongo.get_collection.return_value = mock_collection

            mock_progress.update_progress_after_question = AsyncMock()

            # Call the method
            result = await VoiceTutoringService.process_voice_question(
                session_id="session123",
                audio_base64="test_audio_base64",
                organization_id="org123",
                user_id="user123"
            )

            # Verify material was fetched
            mock_get_material.assert_called_once_with(
                material_id="674f0a1234567890abcdef12",
                organization_id="org123"
            )

            # Verify response contains material info
            assert "material" in result
            assert result["material"]["title"] == "Introduction to Algebra"
            assert result["material"]["subject"] == "Mathematics"

            # Verify RAG filters were passed
            call_args = mock_voice_service.process_voice_message.call_args
            request = call_args.kwargs.get("request") or call_args[1].get("request")
            assert request.rag_filters["material_id"] == "674f0a1234567890abcdef12"

    @pytest.mark.asyncio
    async def test_process_voice_question_without_material(
        self,
        sample_session_without_material
    ):
        """Test voice question processing without material context."""
        mock_voice_result = Mock()
        mock_voice_result.transcribed_text = "What is physics?"
        mock_voice_result.response_text = "Physics is the study of..."
        mock_voice_result.response_audio_base64 = "base64audio..."
        mock_voice_result.audio_duration = 4.0
        mock_voice_result.confidence_score = 0.85
        mock_voice_result.sources_used = []
        mock_voice_result.asr_cost = 0.01
        mock_voice_result.llm_cost = 0.02
        mock_voice_result.tts_cost = 0.01
        mock_voice_result.total_cost = 0.04
        mock_voice_result.detected_language = "en"
        mock_voice_result.asr_transaction_id = "asr456"
        mock_voice_result.tts_transaction_id = "tts456"
        mock_voice_result.asr_processing_time = 1.0
        mock_voice_result.rag_processing_time = 2.0
        mock_voice_result.tts_processing_time = 1.0
        mock_voice_result.total_processing_time = 4.0

        with patch.object(VoiceTutoringService, 'get_voice_service') as mock_get_service, \
             patch("app.services.voice_tutoring_service.TutoringService") as mock_tutoring, \
             patch.object(VoiceTutoringService, 'get_material_by_id') as mock_get_material, \
             patch.object(VoiceTutoringService, 'get_conversation_history') as mock_get_history, \
             patch("app.services.voice_tutoring_service.mongodb") as mock_mongo, \
             patch("app.services.voice_tutoring_service.ProgressService") as mock_progress:

            # Setup mocks
            mock_tutoring.get_session = AsyncMock(return_value=sample_session_without_material)
            mock_tutoring.get_collection_name_for_subject.return_value = "studyflow_org123_science"
            mock_tutoring._update_session_stats = AsyncMock()
            mock_get_history.return_value = []

            mock_voice_service = AsyncMock()
            mock_voice_service.process_voice_message = AsyncMock(return_value=mock_voice_result)
            mock_get_service.return_value = mock_voice_service

            mock_collection = AsyncMock()
            mock_collection.insert_one = AsyncMock(return_value=Mock(inserted_id=ObjectId()))
            mock_mongo.get_collection.return_value = mock_collection

            mock_progress.update_progress_after_question = AsyncMock()

            # Call the method
            result = await VoiceTutoringService.process_voice_question(
                session_id="session456",
                audio_base64="test_audio_base64",
                organization_id="org123",
                user_id="user123"
            )

            # Verify material was NOT fetched (no material_id in metadata)
            mock_get_material.assert_not_called()

            # Verify response does NOT contain material info
            assert "material" not in result

    @pytest.mark.asyncio
    async def test_process_voice_question_with_history(
        self,
        sample_session_without_material,
        sample_conversation_history
    ):
        """Test voice question processing with conversation history."""
        mock_voice_result = Mock()
        mock_voice_result.transcribed_text = "Can you explain more?"
        mock_voice_result.response_text = "Of course, let me elaborate..."
        mock_voice_result.response_audio_base64 = "base64audio..."
        mock_voice_result.audio_duration = 6.0
        mock_voice_result.confidence_score = 0.88
        mock_voice_result.sources_used = []
        mock_voice_result.asr_cost = 0.01
        mock_voice_result.llm_cost = 0.02
        mock_voice_result.tts_cost = 0.01
        mock_voice_result.total_cost = 0.04
        mock_voice_result.detected_language = "en"
        mock_voice_result.asr_transaction_id = "asr789"
        mock_voice_result.tts_transaction_id = "tts789"
        mock_voice_result.asr_processing_time = 1.0
        mock_voice_result.rag_processing_time = 2.0
        mock_voice_result.tts_processing_time = 1.0
        mock_voice_result.total_processing_time = 4.0

        with patch.object(VoiceTutoringService, 'get_voice_service') as mock_get_service, \
             patch("app.services.voice_tutoring_service.TutoringService") as mock_tutoring, \
             patch.object(VoiceTutoringService, 'get_conversation_history') as mock_get_history, \
             patch("app.services.voice_tutoring_service.mongodb") as mock_mongo, \
             patch("app.services.voice_tutoring_service.ProgressService") as mock_progress:

            # Setup mocks
            mock_tutoring.get_session = AsyncMock(return_value=sample_session_without_material)
            mock_tutoring.get_collection_name_for_subject.return_value = "studyflow_org123_science"
            mock_tutoring._update_session_stats = AsyncMock()
            mock_get_history.return_value = sample_conversation_history

            mock_voice_service = AsyncMock()
            mock_voice_service.process_voice_message = AsyncMock(return_value=mock_voice_result)
            mock_get_service.return_value = mock_voice_service

            mock_collection = AsyncMock()
            mock_collection.insert_one = AsyncMock(return_value=Mock(inserted_id=ObjectId()))
            mock_mongo.get_collection.return_value = mock_collection

            mock_progress.update_progress_after_question = AsyncMock()

            # Call the method
            result = await VoiceTutoringService.process_voice_question(
                session_id="session456",
                audio_base64="test_audio_base64",
                organization_id="org123",
                user_id="user123",
                include_history=True,
                history_limit=10
            )

            # Verify history was loaded
            mock_get_history.assert_called_once_with(
                session_id="session456",
                limit=10
            )

            # Verify response contains history_used count
            assert "history_used" in result
            assert result["history_used"] == 4

            # Verify conversation_history was passed to request
            call_args = mock_voice_service.process_voice_message.call_args
            request = call_args.kwargs.get("request") or call_args[1].get("request")
            assert request.conversation_history == sample_conversation_history

    @pytest.mark.asyncio
    async def test_process_voice_question_session_not_found(self):
        """Test error handling when session is not found."""
        with patch("app.services.voice_tutoring_service.TutoringService") as mock_tutoring:
            mock_tutoring.get_session = AsyncMock(return_value=None)

            with pytest.raises(ValueError) as excinfo:
                await VoiceTutoringService.process_voice_question(
                    session_id="nonexistent",
                    audio_base64="test_audio",
                    organization_id="org123",
                    user_id="user123"
                )

            assert "Session not found" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_process_voice_question_session_not_active(
        self,
        sample_session_without_material
    ):
        """Test error handling when session is not active."""
        sample_session_without_material.status = SessionStatus.COMPLETED

        with patch("app.services.voice_tutoring_service.TutoringService") as mock_tutoring:
            mock_tutoring.get_session = AsyncMock(return_value=sample_session_without_material)

            with pytest.raises(ValueError) as excinfo:
                await VoiceTutoringService.process_voice_question(
                    session_id="session456",
                    audio_base64="test_audio",
                    organization_id="org123",
                    user_id="user123"
                )

            assert "Session is not active" in str(excinfo.value)


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and error scenarios."""

    def test_prompt_with_material_no_topics(self, sample_session_with_material):
        """Test prompt when material has no topics."""
        material = StudyMaterial(
            id="material789",
            organization_id="org123",
            title="Empty Topics Document",
            file_name="empty.pdf",
            file_path="/path/to/empty.pdf",
            file_size=1024,
            file_type=MaterialType.PDF,
            subject="Mathematics",
            topics=[],  # Empty topics
            uploaded_by="teacher123",
            status=ProcessingStatus.COMPLETED
        )

        prompt = VoiceTutoringService.build_material_aware_prompt(
            material=material,
            session=sample_session_with_material
        )

        assert "Empty Topics Document" in prompt
        assert "Topics covered" not in prompt  # Should not appear if empty

    def test_prompt_with_material_no_grade(self, sample_session_with_material):
        """Test prompt when material has no grade level."""
        material = StudyMaterial(
            id="material789",
            organization_id="org123",
            title="No Grade Document",
            file_name="nograde.pdf",
            file_path="/path/to/nograde.pdf",
            file_size=1024,
            file_type=MaterialType.PDF,
            subject="General",
            topics=["Topic A"],
            grade=None,  # No grade
            uploaded_by="teacher123",
            status=ProcessingStatus.COMPLETED
        )

        prompt = VoiceTutoringService.build_material_aware_prompt(
            material=material,
            session=sample_session_with_material
        )

        assert "No Grade Document" in prompt
        assert "Grade level:" not in prompt  # Should not appear if None


# ============================================================================
# Tests: Voice Settings Integration
# ============================================================================

class TestVoiceSettingsIntegration:
    """Tests for Voice Settings page integration."""

    @pytest.fixture
    def mock_voice_settings(self):
        """Mock voice settings from Voice Settings page."""
        mock_settings = Mock()
        mock_settings.tts = Mock()
        mock_settings.tts.default_provider = "elevenlabs"
        mock_settings.tts.default_voice = "voice_123"
        mock_settings.tts.speed = 1.2
        mock_settings.tts.pitch = 0.5

        mock_settings.asr = Mock()
        mock_settings.asr.default_provider = "groq_whisper"
        mock_settings.asr.language = "es"

        mock_settings.llm = Mock()
        mock_settings.llm.temperature = 0.7
        mock_settings.llm.max_tokens = 400

        return mock_settings

    @pytest.mark.asyncio
    async def test_voice_settings_applied_to_request(
        self,
        sample_session_without_material,
        mock_voice_settings
    ):
        """Test that voice settings from Voice Settings page are applied to request."""
        mock_voice_result = Mock()
        mock_voice_result.transcribed_text = "Hola, que es fisica?"
        mock_voice_result.response_text = "La fisica es..."
        mock_voice_result.response_audio_base64 = "base64audio..."
        mock_voice_result.audio_duration = 4.0
        mock_voice_result.confidence_score = 0.85
        mock_voice_result.sources_used = []
        mock_voice_result.asr_cost = 0.01
        mock_voice_result.llm_cost = 0.02
        mock_voice_result.tts_cost = 0.01
        mock_voice_result.total_cost = 0.04
        mock_voice_result.detected_language = "es"
        mock_voice_result.asr_transaction_id = "asr_vs"
        mock_voice_result.tts_transaction_id = "tts_vs"
        mock_voice_result.asr_processing_time = 1.0
        mock_voice_result.rag_processing_time = 2.0
        mock_voice_result.tts_processing_time = 1.0
        mock_voice_result.total_processing_time = 4.0

        with patch.object(VoiceTutoringService, 'get_voice_service') as mock_get_service, \
             patch("app.services.voice_tutoring_service.TutoringService") as mock_tutoring, \
             patch.object(VoiceTutoringService, 'get_user_voice_settings') as mock_get_settings, \
             patch.object(VoiceTutoringService, 'get_conversation_history') as mock_get_history, \
             patch("app.services.voice_tutoring_service.mongodb") as mock_mongo, \
             patch("app.services.voice_tutoring_service.ProgressService") as mock_progress:

            # Setup mocks
            mock_tutoring.get_session = AsyncMock(return_value=sample_session_without_material)
            mock_tutoring.get_collection_name_for_subject.return_value = "studyflow_org123_science"
            mock_tutoring._update_session_stats = AsyncMock()
            mock_get_settings.return_value = mock_voice_settings
            mock_get_history.return_value = []

            mock_voice_service = AsyncMock()
            mock_voice_service.process_voice_message = AsyncMock(return_value=mock_voice_result)
            mock_get_service.return_value = mock_voice_service

            mock_collection = AsyncMock()
            mock_collection.insert_one = AsyncMock(return_value=Mock(inserted_id=ObjectId()))
            mock_mongo.get_collection.return_value = mock_collection
            mock_progress.update_progress_after_question = AsyncMock()

            # Call the method without explicit settings (should use Voice Settings)
            await VoiceTutoringService.process_voice_question(
                session_id="session456",
                audio_base64="test_audio_base64",
                organization_id="org123",
                user_id="user123"
            )

            # Verify voice settings were retrieved
            mock_get_settings.assert_called_once_with("user123", "org123")

            # Verify request was created with Voice Settings values
            call_args = mock_voice_service.process_voice_message.call_args
            request = call_args.kwargs.get("request") or call_args[1].get("request")

            # TTS settings from Voice Settings
            assert request.tts_provider_id == "elevenlabs"
            assert request.tts_voice_id == "voice_123"
            assert request.tts_speed == 1.2
            assert request.tts_pitch == 0.5

            # ASR settings from Voice Settings
            assert request.asr_provider_id == "groq_whisper"
            assert request.asr_language == "es"

            # LLM settings from Voice Settings
            assert request.temperature == 0.7
            # Max tokens should be capped at 500 for tutoring
            assert request.max_tokens == 400

    @pytest.mark.asyncio
    async def test_default_values_when_no_voice_settings(
        self,
        sample_session_without_material
    ):
        """Test that defaults are used when no voice settings exist."""
        mock_voice_result = Mock()
        mock_voice_result.transcribed_text = "What is physics?"
        mock_voice_result.response_text = "Physics is..."
        mock_voice_result.response_audio_base64 = "base64audio..."
        mock_voice_result.audio_duration = 4.0
        mock_voice_result.confidence_score = 0.85
        mock_voice_result.sources_used = []
        mock_voice_result.asr_cost = 0.01
        mock_voice_result.llm_cost = 0.02
        mock_voice_result.tts_cost = 0.01
        mock_voice_result.total_cost = 0.04
        mock_voice_result.detected_language = "en"
        mock_voice_result.asr_transaction_id = "asr_def"
        mock_voice_result.tts_transaction_id = "tts_def"
        mock_voice_result.asr_processing_time = 1.0
        mock_voice_result.rag_processing_time = 2.0
        mock_voice_result.tts_processing_time = 1.0
        mock_voice_result.total_processing_time = 4.0

        with patch.object(VoiceTutoringService, 'get_voice_service') as mock_get_service, \
             patch("app.services.voice_tutoring_service.TutoringService") as mock_tutoring, \
             patch.object(VoiceTutoringService, 'get_user_voice_settings') as mock_get_settings, \
             patch.object(VoiceTutoringService, 'get_conversation_history') as mock_get_history, \
             patch("app.services.voice_tutoring_service.mongodb") as mock_mongo, \
             patch("app.services.voice_tutoring_service.ProgressService") as mock_progress:

            # Setup mocks - NO voice settings
            mock_tutoring.get_session = AsyncMock(return_value=sample_session_without_material)
            mock_tutoring.get_collection_name_for_subject.return_value = "studyflow_org123_science"
            mock_tutoring._update_session_stats = AsyncMock()
            mock_get_settings.return_value = None  # No voice settings!
            mock_get_history.return_value = []

            mock_voice_service = AsyncMock()
            mock_voice_service.process_voice_message = AsyncMock(return_value=mock_voice_result)
            mock_get_service.return_value = mock_voice_service

            mock_collection = AsyncMock()
            mock_collection.insert_one = AsyncMock(return_value=Mock(inserted_id=ObjectId()))
            mock_mongo.get_collection.return_value = mock_collection
            mock_progress.update_progress_after_question = AsyncMock()

            # Call without settings
            await VoiceTutoringService.process_voice_question(
                session_id="session456",
                audio_base64="test_audio_base64",
                organization_id="org123",
                user_id="user123"
            )

            # Verify request was created with default values
            call_args = mock_voice_service.process_voice_message.call_args
            request = call_args.kwargs.get("request") or call_args[1].get("request")

            # Default TTS settings
            assert request.tts_provider_id == "coqui_xtts"
            assert request.tts_speed == 0.9
            assert request.tts_pitch == 0.0

            # Default ASR settings
            assert request.asr_provider_id == "whisper_large_v3"
            assert request.asr_language == "en"

            # Default LLM settings
            assert request.temperature == 0.1

    @pytest.mark.asyncio
    async def test_explicit_params_override_voice_settings(
        self,
        sample_session_without_material,
        mock_voice_settings
    ):
        """Test that explicit parameters override Voice Settings."""
        mock_voice_result = Mock()
        mock_voice_result.transcribed_text = "Test question"
        mock_voice_result.response_text = "Test response"
        mock_voice_result.response_audio_base64 = "base64audio..."
        mock_voice_result.audio_duration = 4.0
        mock_voice_result.confidence_score = 0.85
        mock_voice_result.sources_used = []
        mock_voice_result.asr_cost = 0.01
        mock_voice_result.llm_cost = 0.02
        mock_voice_result.tts_cost = 0.01
        mock_voice_result.total_cost = 0.04
        mock_voice_result.detected_language = "fr"
        mock_voice_result.asr_transaction_id = "asr_exp"
        mock_voice_result.tts_transaction_id = "tts_exp"
        mock_voice_result.asr_processing_time = 1.0
        mock_voice_result.rag_processing_time = 2.0
        mock_voice_result.tts_processing_time = 1.0
        mock_voice_result.total_processing_time = 4.0

        with patch.object(VoiceTutoringService, 'get_voice_service') as mock_get_service, \
             patch("app.services.voice_tutoring_service.TutoringService") as mock_tutoring, \
             patch.object(VoiceTutoringService, 'get_user_voice_settings') as mock_get_settings, \
             patch.object(VoiceTutoringService, 'get_conversation_history') as mock_get_history, \
             patch("app.services.voice_tutoring_service.mongodb") as mock_mongo, \
             patch("app.services.voice_tutoring_service.ProgressService") as mock_progress:

            # Setup mocks
            mock_tutoring.get_session = AsyncMock(return_value=sample_session_without_material)
            mock_tutoring.get_collection_name_for_subject.return_value = "studyflow_org123_science"
            mock_tutoring._update_session_stats = AsyncMock()
            mock_get_settings.return_value = mock_voice_settings
            mock_get_history.return_value = []

            mock_voice_service = AsyncMock()
            mock_voice_service.process_voice_message = AsyncMock(return_value=mock_voice_result)
            mock_get_service.return_value = mock_voice_service

            mock_collection = AsyncMock()
            mock_collection.insert_one = AsyncMock(return_value=Mock(inserted_id=ObjectId()))
            mock_mongo.get_collection.return_value = mock_collection
            mock_progress.update_progress_after_question = AsyncMock()

            # Call with explicit parameters (should override voice settings)
            await VoiceTutoringService.process_voice_question(
                session_id="session456",
                audio_base64="test_audio_base64",
                organization_id="org123",
                user_id="user123",
                tts_provider_id="azure_tts",  # Override
                tts_voice_id="azure_voice",   # Override
                tts_speed=0.8,                # Override
                asr_provider_id="openai_whisper",  # Override
                language="fr"                 # Override
            )

            # Verify explicit params override voice settings
            call_args = mock_voice_service.process_voice_message.call_args
            request = call_args.kwargs.get("request") or call_args[1].get("request")

            # Should use explicit params, not voice settings
            assert request.tts_provider_id == "azure_tts"
            assert request.tts_voice_id == "azure_voice"
            assert request.tts_speed == 0.8
            assert request.asr_provider_id == "openai_whisper"
            assert request.asr_language == "fr"

            # Pitch should still come from voice settings (not overridden)
            assert request.tts_pitch == 0.5
