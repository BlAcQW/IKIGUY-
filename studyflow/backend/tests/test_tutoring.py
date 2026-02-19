"""
Unit tests for tutoring routes.

Tests session creation, question answering, and session management.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from bson import ObjectId

from app.models.session import SessionStatus
from app.models.question import QuestionType


class TestTutoringRoutes:
    """Test tutoring API endpoints."""

    @pytest.mark.asyncio
    async def test_create_session_success(self, client, mock_supabase_auth, mock_mongodb):
        """
        Test successful session creation.

        Expected: 201 status, session data returned
        """
        # Mock MongoDB insert
        mock_result = MagicMock()
        mock_result.inserted_id = ObjectId()
        mock_mongodb.insert_one = AsyncMock(return_value=mock_result)

        session_data = {
            "student_id": "student-123",
            "subject": "Mathematics",
            "topics": ["algebra", "equations"],
            "metadata": {}
        }

        response = client.post(
            "/api/v1/tutoring/sessions",
            json=session_data,
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["subject"] == "Mathematics"
        assert data["status"] == SessionStatus.ACTIVE.value
        assert data["questions_asked"] == 0

    @pytest.mark.asyncio
    async def test_create_session_missing_required_fields(self, client, mock_supabase_auth):
        """
        Test session creation with missing required fields.

        Expected: 422 validation error
        """
        session_data = {
            "student_id": "student-123"
            # Missing subject
        }

        response = client.post(
            "/api/v1/tutoring/sessions",
            json=session_data,
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_ask_question_success(self, client, mock_supabase_auth, mock_mongodb):
        """
        Test asking question and getting AI answer.

        Expected: 200 status, answer with confidence and sources
        """
        # Mock session exists
        session_data = {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "student_id": "student-123",
            "subject": "Mathematics",
            "status": SessionStatus.ACTIVE.value
        }

        # Mock RAG response
        rag_response = {
            "response": "The quadratic formula is x = (-b ± √(b²-4ac)) / 2a",
            "confidence_score": 0.95,
            "sources": ["algebra_textbook.pdf", "math_formulas.pdf"],
            "tokens_used": 150,
            "cost": 0.002
        }

        # Mock question insert
        mock_result = MagicMock()
        mock_result.inserted_id = ObjectId()

        def find_one_side_effect(*args, **kwargs):
            query = args[0] if args else kwargs.get("filter")
            if "_id" in query:
                return session_data
            return None

        mock_mongodb.find_one = AsyncMock(side_effect=find_one_side_effect)
        mock_mongodb.insert_one = AsyncMock(return_value=mock_result)
        mock_mongodb.update_one = AsyncMock()

        # Mock RAG service
        with patch("app.services.tutoring_service.TutoringService.get_rag_service") as mock_rag:
            mock_rag_instance = MagicMock()
            mock_rag_instance.query_knowledge_base = AsyncMock(return_value=rag_response)
            mock_rag.return_value = mock_rag_instance

            question_data = {
                "session_id": "507f1f77bcf86cd799439011",
                "subject": "Mathematics",
                "topic": "algebra",
                "question_text": "What is the quadratic formula?",
                "question_type": "text"
            }

            response = client.post(
                "/api/v1/tutoring/ask",
                json=question_data,
                headers={"Authorization": "Bearer test-token"}
            )

        assert response.status_code == 200
        data = response.json()
        assert "quadratic formula" in data["answer"].lower()
        assert data["confidence_score"] >= 0.9
        assert len(data["sources"]) > 0
        assert data["cost"] > 0

    @pytest.mark.asyncio
    async def test_ask_question_session_not_found(self, client, mock_supabase_auth, mock_mongodb):
        """
        Test asking question for non-existent session.

        Expected: 404 status
        """
        mock_mongodb.find_one = AsyncMock(return_value=None)

        question_data = {
            "session_id": "nonexistent-session-id",
            "subject": "Mathematics",
            "question_text": "What is 2+2?",
            "question_type": "text"
        }

        response = client.post(
            "/api/v1/tutoring/ask",
            json=question_data,
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 404
        assert "Session not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_ask_question_rag_error(self, client, mock_supabase_auth, mock_mongodb):
        """
        Test question answering when RAG service fails.

        Expected: Still returns 200, but with error message in answer
        """
        # Mock session exists
        session_data = {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "student_id": "student-123",
            "subject": "Mathematics",
            "status": SessionStatus.ACTIVE.value
        }

        mock_result = MagicMock()
        mock_result.inserted_id = ObjectId()

        mock_mongodb.find_one = AsyncMock(return_value=session_data)
        mock_mongodb.insert_one = AsyncMock(return_value=mock_result)
        mock_mongodb.update_one = AsyncMock()

        # Mock RAG service to raise exception
        with patch("app.services.tutoring_service.TutoringService.get_rag_service") as mock_rag:
            mock_rag_instance = MagicMock()
            mock_rag_instance.query_knowledge_base = AsyncMock(
                side_effect=Exception("RAG service unavailable")
            )
            mock_rag.return_value = mock_rag_instance

            question_data = {
                "session_id": "507f1f77bcf86cd799439011",
                "subject": "Mathematics",
                "question_text": "What is 2+2?",
                "question_type": "text"
            }

            response = client.post(
                "/api/v1/tutoring/ask",
                json=question_data,
                headers={"Authorization": "Bearer test-token"}
            )

        assert response.status_code == 200
        data = response.json()
        assert "error" in data["answer"].lower()
        assert data["confidence_score"] == 0.0

    @pytest.mark.asyncio
    async def test_get_session_success(self, client, mock_supabase_auth, mock_mongodb):
        """
        Test getting session details.

        Expected: 200 status, session data
        """
        session_id = str(ObjectId())
        session_data = {
            "_id": ObjectId(session_id),
            "student_id": "student-123",
            "subject": "Mathematics",
            "topics": ["algebra"],
            "status": SessionStatus.ACTIVE.value,
            "started_at": datetime.utcnow(),
            "questions_asked": 5,
            "questions_answered": 5,
            "cost_incurred": 0.01
        }

        mock_mongodb.find_one = AsyncMock(return_value=session_data)

        response = client.get(
            f"/api/v1/tutoring/sessions/{session_id}",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["subject"] == "Mathematics"
        assert data["questions_asked"] == 5

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, client, mock_supabase_auth, mock_mongodb):
        """
        Test getting non-existent session.

        Expected: 404 status
        """
        session_id = str(ObjectId())
        mock_mongodb.find_one = AsyncMock(return_value=None)

        response = client.get(
            f"/api/v1/tutoring/sessions/{session_id}",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_end_session_success(self, client, mock_supabase_auth, mock_mongodb):
        """
        Test ending active session.

        Expected: 200 status, session marked as completed
        """
        session_id = str(ObjectId())
        session_data = {
            "_id": ObjectId(session_id),
            "student_id": "student-123",
            "subject": "Mathematics",
            "status": SessionStatus.ACTIVE.value,
            "started_at": datetime.utcnow(),
            "questions_asked": 10,
            "cost_incurred": 0.05
        }

        updated_session = session_data.copy()
        updated_session["status"] = SessionStatus.COMPLETED.value
        updated_session["ended_at"] = datetime.utcnow()
        updated_session["duration_minutes"] = 15.5

        def find_one_side_effect(*args, **kwargs):
            # First call returns active session, second returns updated
            return updated_session

        mock_mongodb.find_one = AsyncMock(side_effect=find_one_side_effect)
        mock_mongodb.update_one = AsyncMock()

        response = client.post(
            f"/api/v1/tutoring/sessions/{session_id}/end",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == SessionStatus.COMPLETED.value

    @pytest.mark.asyncio
    async def test_get_session_questions_success(self, client, mock_supabase_auth, mock_mongodb):
        """
        Test getting all questions from a session.

        Expected: 200 status, list of questions
        """
        session_id = str(ObjectId())

        # Mock session exists
        session_data = {
            "_id": ObjectId(session_id),
            "student_id": "student-123"
        }

        # Mock questions
        questions = [
            {
                "_id": ObjectId(),
                "session_id": session_id,
                "student_id": "student-123",
                "subject": "Mathematics",
                "question_text": "What is 2+2?",
                "answer_text": "2+2 equals 4",
                "question_type": QuestionType.TEXT.value,
                "confidence_score": 0.99,
                "sources_used": [],
                "cost": 0.001,
                "created_at": datetime.utcnow()
            },
            {
                "_id": ObjectId(),
                "session_id": session_id,
                "student_id": "student-123",
                "subject": "Mathematics",
                "question_text": "What is the quadratic formula?",
                "answer_text": "The quadratic formula is...",
                "question_type": QuestionType.TEXT.value,
                "confidence_score": 0.95,
                "sources_used": ["algebra.pdf"],
                "cost": 0.002,
                "created_at": datetime.utcnow()
            }
        ]

        mock_mongodb.find_one = AsyncMock(return_value=session_data)

        # Mock cursor for questions
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__aiter__.return_value = iter(questions)

        mock_mongodb.find.return_value = mock_cursor

        response = client.get(
            f"/api/v1/tutoring/sessions/{session_id}/questions",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["question_text"] == "What is 2+2?"
        assert data[1]["confidence_score"] == 0.95

    @pytest.mark.asyncio
    async def test_get_session_questions_empty(self, client, mock_supabase_auth, mock_mongodb):
        """
        Test getting questions from session with no questions.

        Expected: 200 status, empty list
        """
        session_id = str(ObjectId())

        # Mock session exists
        session_data = {
            "_id": ObjectId(session_id),
            "student_id": "student-123"
        }

        mock_mongodb.find_one = AsyncMock(return_value=session_data)

        # Mock empty questions cursor
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__aiter__.return_value = iter([])

        mock_mongodb.find.return_value = mock_cursor

        response = client.get(
            f"/api/v1/tutoring/sessions/{session_id}/questions",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_get_questions_session_not_found(self, client, mock_supabase_auth, mock_mongodb):
        """
        Test getting questions for non-existent session.

        Expected: 404 status
        """
        session_id = str(ObjectId())
        mock_mongodb.find_one = AsyncMock(return_value=None)

        response = client.get(
            f"/api/v1/tutoring/sessions/{session_id}/questions",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 404
