"""
Unit tests for VAPI Document Tutoring Service.

Tests the VAPI-based conversational voice tutoring functionality.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from app.services.vapi_document_tutoring_service import VAPIDocumentTutoringService
from app.models.material import StudyMaterial, ProcessingStatus, MaterialType
from app.models.session import StudySession, SessionStatus


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_material():
    """Sample study material."""
    return StudyMaterial(
        id="material123",
        organization_id="org123",
        school_id="school123",
        title="Introduction to Algebra",
        description="Basic algebra concepts",
        file_name="algebra.pdf",
        file_path="/path/to/algebra.pdf",
        file_size=1024000,
        file_type=MaterialType.PDF,
        subject="Mathematics",
        topics=["Linear Equations", "Quadratic Equations"],
        grade=9,
        uploaded_by="user123",
        status=ProcessingStatus.COMPLETED,
        chunks_count=50,
        embedding_collection="studyflow_org123_mathematics",
        metadata={},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def sample_session():
    """Sample study session."""
    return StudySession(
        id="session123",
        organization_id="org123",
        school_id="school123",
        student_id="student123",
        subject="Mathematics",
        topics=["Linear Equations"],
        status=SessionStatus.ACTIVE,
        started_at=datetime.utcnow(),
        questions_asked=0,
        questions_answered=0,
        cost_incurred=0.0,
        metadata={
            "material_id": "material123",
            "vapi_assistant_id": "assistant123",
            "session_type": "vapi_voice"
        }
    )


@pytest.fixture
def mock_vapi_service():
    """Mock VAPI service."""
    service = AsyncMock()
    service.create_agent = AsyncMock(return_value={
        "success": True,
        "assistant_id": "assistant123",
        "name": "Test Tutor",
        "voice": "jennifer",
        "created_at": datetime.utcnow().isoformat()
    })
    service.initiate_call = AsyncMock(return_value={
        "success": True,
        "call_id": "call123",
        "status": "initiated",
        "to_number": "+1234567890",
        "assistant_id": "assistant123"
    })
    return service


@pytest.fixture
def mock_rag_service():
    """Mock RAG service."""
    service = AsyncMock()
    service.query_knowledge_base = AsyncMock(return_value={
        "response": "Linear equations are equations with variables raised to the power of 1.",
        "confidence_score": 0.85,
        "sources": [
            {"page": 5, "content": "...linear equations..."}
        ],
        "tokens_used": 500,
        "cost": 0.01
    })
    return service


# ============================================================================
# Test Create Document Assistant
# ============================================================================

@pytest.mark.asyncio
async def test_create_document_assistant_success(sample_material, mock_vapi_service):
    """Test successful creation of VAPI assistant for document."""
    with patch.object(VAPIDocumentTutoringService, 'get_vapi_service', return_value=mock_vapi_service), \
         patch('app.services.material_service.MaterialService.get_material_by_id', return_value=sample_material), \
         patch('app.services.material_service.MaterialService.update_material', return_value=sample_material):

        result = await VAPIDocumentTutoringService.create_document_assistant(
            material_id="material123",
            organization_id="org123",
            user_id="user123",
            voice_id="jennifer",
            language="en"
        )

        assert result["success"] is True
        assert result["assistant_id"] == "assistant123"
        assert result["material"]["id"] == "material123"
        assert result["voice"] == "jennifer"
        assert result["language"] == "en"

        # Verify VAPI agent was created
        mock_vapi_service.create_agent.assert_called_once()
        agent_arg = mock_vapi_service.create_agent.call_args[0][0]
        assert "Tutor" in agent_arg.name
        assert agent_arg.voice == "jennifer"
        assert "Mathematics" in agent_arg.system_prompt


@pytest.mark.asyncio
async def test_create_document_assistant_material_not_found():
    """Test creating assistant when material not found."""
    with patch('app.services.material_service.MaterialService.get_material_by_id', return_value=None):
        with pytest.raises(ValueError, match="Material not found"):
            await VAPIDocumentTutoringService.create_document_assistant(
                material_id="nonexistent",
                organization_id="org123",
                user_id="user123"
            )


@pytest.mark.asyncio
async def test_create_document_assistant_material_not_processed(sample_material):
    """Test creating assistant when material not processed."""
    sample_material.status = ProcessingStatus.PENDING

    with patch('app.services.material_service.MaterialService.get_material_by_id', return_value=sample_material):
        with pytest.raises(ValueError, match="Material not processed yet"):
            await VAPIDocumentTutoringService.create_document_assistant(
                material_id="material123",
                organization_id="org123",
                user_id="user123"
            )


# ============================================================================
# Test Start Voice Session
# ============================================================================

@pytest.mark.asyncio
async def test_start_voice_session_success(sample_material, sample_session, mock_vapi_service):
    """Test successful voice session start."""
    sample_material.metadata = {"vapi_assistant_id": "assistant123"}

    with patch.object(VAPIDocumentTutoringService, 'get_vapi_service', return_value=mock_vapi_service), \
         patch('app.services.material_service.MaterialService.get_material_by_id', return_value=sample_material), \
         patch('app.services.tutoring_service.TutoringService.create_session', return_value=sample_session):

        result = await VAPIDocumentTutoringService.start_voice_session(
            material_id="material123",
            student_id="student123",
            organization_id="org123",
            phone_number="+1234567890"
        )

        assert result["success"] is True
        assert result["session_id"] == "session123"
        assert result["call_id"] == "call123"
        assert result["status"] == "initiated"
        assert result["material"]["id"] == "material123"

        # Verify call was initiated
        mock_vapi_service.initiate_call.assert_called_once()
        call_args = mock_vapi_service.initiate_call.call_args[1]
        assert call_args["to_number"] == "+1234567890"
        assert call_args["assistant_id"] == "assistant123"


@pytest.mark.asyncio
async def test_start_voice_session_no_assistant(sample_material):
    """Test starting session when no assistant configured."""
    sample_material.metadata = {}

    with patch('app.services.material_service.MaterialService.get_material_by_id', return_value=sample_material):
        with pytest.raises(ValueError, match="No VAPI assistant found"):
            await VAPIDocumentTutoringService.start_voice_session(
                material_id="material123",
                student_id="student123",
                organization_id="org123",
                phone_number="+1234567890"
            )


# ============================================================================
# Test Function Calling
# ============================================================================

@pytest.mark.asyncio
async def test_answer_from_knowledge_base(sample_session, mock_rag_service):
    """Test answering question from knowledge base."""
    with patch.object(VAPIDocumentTutoringService, 'get_rag_service', return_value=mock_rag_service), \
         patch('app.services.tutoring_service.TutoringService.get_session', return_value=sample_session), \
         patch('app.services.tutoring_service.TutoringService._update_session_stats'):

        result = await VAPIDocumentTutoringService._answer_from_knowledge_base(
            question="What are linear equations?",
            topic="Linear Equations",
            session_id="session123",
            organization_id="org123"
        )

        assert result["success"] is True
        assert "linear equations" in result["answer"].lower()
        assert result["confidence"] == 0.85
        assert len(result["sources"]) > 0

        # Verify RAG was queried
        mock_rag_service.query_knowledge_base.assert_called_once()


@pytest.mark.asyncio
async def test_generate_exercise(sample_session):
    """Test generating practice exercise."""
    mock_exercise = Mock()
    mock_exercise.id = "exercise123"
    mock_exercise.questions = [
        Mock(question_text="Q1", options=["A", "B", "C", "D"]),
        Mock(question_text="Q2", options=["A", "B", "C", "D"]),
        Mock(question_text="Q3", options=["A", "B", "C", "D"])
    ]

    with patch('app.services.tutoring_service.TutoringService.get_session', return_value=sample_session), \
         patch('app.services.exercise_service.ExerciseService.generate_exercise', return_value=mock_exercise):

        result = await VAPIDocumentTutoringService._generate_exercise(
            topic="Linear Equations",
            difficulty="medium",
            session_id="session123",
            organization_id="org123"
        )

        assert result["success"] is True
        assert result["exercise_id"] == "exercise123"
        assert result["topic"] == "Linear Equations"
        assert result["difficulty"] == "medium"
        assert result["num_questions"] == 3
        assert "Q1" in result["questions"]


@pytest.mark.asyncio
async def test_evaluate_answer(sample_session, mock_rag_service):
    """Test evaluating student answer."""
    mock_rag_service.query_knowledge_base = AsyncMock(return_value={
        "response": "The student's answer is correct! They understood the concept.",
        "confidence_score": 0.9
    })

    with patch.object(VAPIDocumentTutoringService, 'get_rag_service', return_value=mock_rag_service), \
         patch('app.services.tutoring_service.TutoringService.get_session', return_value=sample_session):

        result = await VAPIDocumentTutoringService._evaluate_answer(
            question="What is 2x + 4 = 10?",
            student_answer="x = 3",
            correct_answer="x = 3",
            session_id="session123",
            organization_id="org123"
        )

        assert result["success"] is True
        assert result["is_correct"] is True
        assert "correct" in result["feedback"].lower()
        assert len(result["encouragement"]) > 0


@pytest.mark.asyncio
async def test_handle_function_call_unsupported():
    """Test handling unsupported function call."""
    with pytest.raises(ValueError, match="Unsupported function"):
        await VAPIDocumentTutoringService.handle_function_call(
            function_name="unsupported_function",
            arguments={},
            session_id="session123",
            organization_id="org123"
        )


# ============================================================================
# Test Service Initialization
# ============================================================================

def test_get_vapi_service():
    """Test VAPI service singleton initialization."""
    service1 = VAPIDocumentTutoringService.get_vapi_service()
    service2 = VAPIDocumentTutoringService.get_vapi_service()

    assert service1 is service2  # Same instance
    assert service1 is not None


def test_get_rag_service():
    """Test RAG service singleton initialization."""
    with patch('app.services.tutoring_service.TutoringService.get_rag_service') as mock:
        mock_rag = Mock()
        mock.return_value = mock_rag

        service1 = VAPIDocumentTutoringService.get_rag_service()
        service2 = VAPIDocumentTutoringService.get_rag_service()

        assert service1 is service2  # Same instance
        mock.assert_called_once()  # Only initialized once


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_full_voice_tutoring_flow(sample_material, mock_vapi_service, mock_rag_service):
    """Test complete voice tutoring flow from assistant creation to function calling."""
    sample_material.metadata = {}

    with patch.object(VAPIDocumentTutoringService, 'get_vapi_service', return_value=mock_vapi_service), \
         patch.object(VAPIDocumentTutoringService, 'get_rag_service', return_value=mock_rag_service), \
         patch('app.services.material_service.MaterialService.get_material_by_id', return_value=sample_material), \
         patch('app.services.material_service.MaterialService.update_material', return_value=sample_material):

        # Step 1: Create assistant
        assistant_result = await VAPIDocumentTutoringService.create_document_assistant(
            material_id="material123",
            organization_id="org123",
            user_id="user123"
        )

        assert assistant_result["success"] is True
        assistant_id = assistant_result["assistant_id"]

        # Step 2: Simulate function call from VAPI (answer question)
        sample_session = StudySession(
            id="session123",
            organization_id="org123",
            school_id="school123",
            student_id="student123",
            subject="Mathematics",
            topics=["Linear Equations"],
            status=SessionStatus.ACTIVE,
            started_at=datetime.utcnow(),
            questions_asked=0,
            questions_answered=0,
            cost_incurred=0.0,
            metadata={"material_id": "material123", "vapi_assistant_id": assistant_id}
        )

        with patch('app.services.tutoring_service.TutoringService.get_session', return_value=sample_session), \
             patch('app.services.tutoring_service.TutoringService._update_session_stats'):

            function_result = await VAPIDocumentTutoringService.handle_function_call(
                function_name="answer_from_knowledge_base",
                arguments={"question": "What are linear equations?", "topic": "Linear Equations"},
                session_id="session123",
                organization_id="org123"
            )

            assert function_result["success"] is True
            assert len(function_result["answer"]) > 0
            assert function_result["confidence"] > 0
