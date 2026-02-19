"""
Unit tests for exercise submission and grading.

Tests Story 4.2: Exercise Submission & Grading implementation.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from bson import ObjectId

from app.models.exercise import (
    Exercise,
    ExerciseQuestion,
    StudentAnswer,
    ExerciseSubmission,
    DifficultyLevel,
    QuestionType,
    ExerciseStatus,
    MCQOption,
    QuestionFeedback,
    PerformanceSummary,
    SubmissionFeedbackResponse,
)
from app.services.exercise_service import ExerciseService


class TestExerciseSubmission:
    """Test exercise submission functionality."""

    @pytest.fixture
    def sample_mcq_exercise(self):
        """Create sample MCQ exercise."""
        questions = [
            ExerciseQuestion(
                question_type=QuestionType.MULTIPLE_CHOICE,
                question_text="What is 2 + 2?",
                options=[
                    MCQOption(label="A", text="3", is_correct=False),
                    MCQOption(label="B", text="4", is_correct=True),
                    MCQOption(label="C", text="5", is_correct=False),
                    MCQOption(label="D", text="6", is_correct=False),
                ],
                correct_answer="B",
                acceptable_answers=[],
                explanation="2 + 2 equals 4",
                topic="Basic Arithmetic",
                difficulty=DifficultyLevel.EASY,
                points=1
            ),
            ExerciseQuestion(
                question_type=QuestionType.MULTIPLE_CHOICE,
                question_text="What is 5 * 3?",
                options=[
                    MCQOption(label="A", text="8", is_correct=False),
                    MCQOption(label="B", text="12", is_correct=False),
                    MCQOption(label="C", text="15", is_correct=True),
                    MCQOption(label="D", text="18", is_correct=False),
                ],
                correct_answer="C",
                acceptable_answers=[],
                explanation="5 multiplied by 3 equals 15",
                topic="Basic Arithmetic",
                difficulty=DifficultyLevel.EASY,
                points=1
            ),
        ]

        return Exercise(
            id=str(ObjectId()),
            organization_id=str(ObjectId()),
            title="Basic Math Quiz",
            subject="Mathematics",
            topics=["Basic Arithmetic"],
            questions=questions,
            total_points=2,
            difficulty=DifficultyLevel.EASY,
            created_by=str(ObjectId()),
            status=ExerciseStatus.READY
        )

    @pytest.fixture
    def sample_short_answer_exercise(self):
        """Create sample short answer exercise."""
        questions = [
            ExerciseQuestion(
                question_type=QuestionType.SHORT_ANSWER,
                question_text="What is the capital of France?",
                options=None,
                correct_answer="Paris",
                acceptable_answers=["paris", "Paris, France"],
                explanation="Paris is the capital and largest city of France.",
                topic="Geography",
                difficulty=DifficultyLevel.EASY,
                points=1
            ),
        ]

        return Exercise(
            id=str(ObjectId()),
            organization_id=str(ObjectId()),
            title="Geography Quiz",
            subject="Geography",
            topics=["World Capitals"],
            questions=questions,
            total_points=1,
            difficulty=DifficultyLevel.EASY,
            created_by=str(ObjectId()),
            status=ExerciseStatus.READY
        )

    @pytest.mark.asyncio
    async def test_submit_mcq_exercise_all_correct(self, sample_mcq_exercise):
        """Test submitting MCQ exercise with all correct answers."""
        # Create correct answers
        answers = [
            StudentAnswer(
                question_id=sample_mcq_exercise.questions[0].question_id,
                answer="B"
            ),
            StudentAnswer(
                question_id=sample_mcq_exercise.questions[1].question_id,
                answer="C"
            ),
        ]

        # Mock database operations
        with patch.object(ExerciseService, 'get_exercise', return_value=sample_mcq_exercise):
            with patch('app.services.exercise_service.mongodb') as mock_db:
                mock_collection = Mock()
                mock_collection.insert_one = AsyncMock(return_value=Mock(inserted_id=ObjectId()))
                mock_collection.find_one = AsyncMock(return_value=None)
                mock_db.get_collection.return_value = mock_collection

                # Submit exercise
                submission = await ExerciseService.submit_exercise(
                    exercise_id=sample_mcq_exercise.id,
                    student_id=str(ObjectId()),
                    answers=answers,
                    time_taken_seconds=60,
                    organization_id=sample_mcq_exercise.organization_id
                )

                # Verify results
                assert submission.score == 2.0
                assert submission.max_score == 2.0
                assert submission.percentage == 100.0
                assert submission.passed is True
                assert submission.questions_correct == 2
                assert submission.questions_total == 2

    @pytest.mark.asyncio
    async def test_submit_mcq_exercise_partial_correct(self, sample_mcq_exercise):
        """Test submitting MCQ exercise with partial correct answers."""
        # Create mixed answers
        answers = [
            StudentAnswer(
                question_id=sample_mcq_exercise.questions[0].question_id,
                answer="B"  # Correct
            ),
            StudentAnswer(
                question_id=sample_mcq_exercise.questions[1].question_id,
                answer="A"  # Incorrect
            ),
        ]

        # Mock database operations
        with patch.object(ExerciseService, 'get_exercise', return_value=sample_mcq_exercise):
            with patch('app.services.exercise_service.mongodb') as mock_db:
                mock_collection = Mock()
                mock_collection.insert_one = AsyncMock(return_value=Mock(inserted_id=ObjectId()))
                mock_collection.find_one = AsyncMock(return_value=None)
                mock_db.get_collection.return_value = mock_collection

                # Submit exercise
                submission = await ExerciseService.submit_exercise(
                    exercise_id=sample_mcq_exercise.id,
                    student_id=str(ObjectId()),
                    answers=answers,
                    time_taken_seconds=60,
                    organization_id=sample_mcq_exercise.organization_id
                )

                # Verify results
                assert submission.score == 1.0
                assert submission.max_score == 2.0
                assert submission.percentage == 50.0
                assert submission.questions_correct == 1
                assert submission.questions_total == 2


class TestAIGrading:
    """Test AI-powered grading for short answers."""

    @pytest.fixture
    def sample_question(self):
        """Create sample short answer question."""
        return ExerciseQuestion(
            question_type=QuestionType.SHORT_ANSWER,
            question_text="What is photosynthesis?",
            options=None,
            correct_answer="The process by which plants convert light energy into chemical energy",
            acceptable_answers=[
                "Plants making food from sunlight",
                "How plants use sunlight to make energy"
            ],
            explanation="Photosynthesis is the process where plants use sunlight to convert CO2 and water into glucose and oxygen.",
            topic="Biology",
            difficulty=DifficultyLevel.MEDIUM,
            points=2
        )

    @pytest.mark.asyncio
    async def test_ai_grading_correct_answer(self, sample_question):
        """Test AI grading with correct answer."""
        # Mock RAG service
        mock_rag = Mock()
        mock_rag.generate = AsyncMock(return_value={
            "response": '{"is_correct": true, "points_earned": 2.0, "feedback": "Excellent! You correctly identified the key concept of photosynthesis.", "key_concepts_identified": ["light energy", "chemical energy"]}'
        })

        with patch.object(ExerciseService, 'get_rag_service', return_value=mock_rag):
            is_correct, points, feedback = await ExerciseService.grade_short_answer_with_ai(
                question=sample_question,
                student_answer="Photosynthesis is the process where plants convert light energy into chemical energy using sunlight.",
                use_rubric=True
            )

            assert is_correct is True
            assert points == 2.0
            assert "Excellent" in feedback

    @pytest.mark.asyncio
    async def test_ai_grading_partial_credit(self, sample_question):
        """Test AI grading with partial credit."""
        # Mock RAG service
        mock_rag = Mock()
        mock_rag.generate = AsyncMock(return_value={
            "response": '{"is_correct": false, "points_earned": 1.0, "feedback": "Your answer shows some understanding but is incomplete. You mentioned sunlight but didn\'t explain the energy conversion.", "key_concepts_identified": ["sunlight"]}'
        })

        with patch.object(ExerciseService, 'get_rag_service', return_value=mock_rag):
            is_correct, points, feedback = await ExerciseService.grade_short_answer_with_ai(
                question=sample_question,
                student_answer="Plants use sunlight",
                use_rubric=True
            )

            assert is_correct is False
            assert points == 1.0
            assert "partial" in feedback.lower() or "some understanding" in feedback.lower()

    @pytest.mark.asyncio
    async def test_ai_grading_fallback_on_error(self, sample_question):
        """Test AI grading falls back to simple matching on error."""
        # Mock RAG service that raises exception
        mock_rag = Mock()
        mock_rag.generate = AsyncMock(side_effect=Exception("API error"))

        with patch.object(ExerciseService, 'get_rag_service', return_value=mock_rag):
            is_correct, points, feedback = await ExerciseService.grade_short_answer_with_ai(
                question=sample_question,
                student_answer="The process by which plants convert light energy into chemical energy",
                use_rubric=True
            )

            # Should fall back to simple matching
            assert is_correct is True  # Matches correct_answer
            assert points == 2.0


class TestFeedbackGeneration:
    """Test feedback generation functionality."""

    @pytest.mark.asyncio
    async def test_get_submission_feedback(self):
        """Test getting detailed submission feedback."""
        # Create sample data
        exercise_id = str(ObjectId())
        student_id = str(ObjectId())
        submission_id = str(ObjectId())

        question = ExerciseQuestion(
            question_type=QuestionType.MULTIPLE_CHOICE,
            question_text="What is 2 + 2?",
            options=[
                MCQOption(label="A", text="3", is_correct=False),
                MCQOption(label="B", text="4", is_correct=True),
            ],
            correct_answer="B",
            acceptable_answers=[],
            explanation="2 + 2 equals 4",
            topic="Arithmetic",
            difficulty=DifficultyLevel.EASY,
            points=1,
            hints=["Think about counting"]
        )

        exercise = Exercise(
            id=exercise_id,
            organization_id=str(ObjectId()),
            title="Math Quiz",
            subject="Mathematics",
            topics=["Arithmetic"],
            questions=[question],
            total_points=1,
            difficulty=DifficultyLevel.EASY,
            created_by=str(ObjectId()),
            status=ExerciseStatus.READY
        )

        submission = ExerciseSubmission(
            id=submission_id,
            exercise_id=exercise_id,
            student_id=student_id,
            organization_id=exercise.organization_id,
            answers=[
                StudentAnswer(
                    question_id=question.question_id,
                    answer="B",
                    is_correct=True,
                    points_earned=1.0
                )
            ],
            score=1.0,
            max_score=1.0,
            percentage=100.0,
            passed=True,
            time_taken_seconds=30,
            questions_correct=1,
            questions_total=1,
            difficulty_level=DifficultyLevel.EASY,
            recommended_next_difficulty=DifficultyLevel.MEDIUM,
            weak_topics=[],
            strong_topics=["Arithmetic"],
            started_at=datetime.utcnow()
        )

        # Mock database operations
        with patch('app.services.exercise_service.mongodb') as mock_db:
            mock_collection = Mock()
            submission_dict = submission.model_dump(by_alias=True)
            submission_dict["_id"] = ObjectId(submission_id)
            mock_collection.find_one = AsyncMock(return_value=submission_dict)
            mock_db.get_collection.return_value = mock_collection

            with patch.object(ExerciseService, 'get_exercise', return_value=exercise):
                feedback = await ExerciseService.get_submission_feedback(
                    submission_id=submission_id
                )

                # Verify feedback structure
                assert feedback is not None
                assert feedback.submission_id == submission_id
                assert feedback.exercise_id == exercise_id
                assert len(feedback.question_feedback) == 1

                # Verify question feedback
                q_feedback = feedback.question_feedback[0]
                assert q_feedback.question_number == 1
                assert q_feedback.is_correct is True
                assert q_feedback.correct_answer == "B"
                assert q_feedback.explanation == "2 + 2 equals 4"

                # Verify performance summary
                perf = feedback.performance
                assert perf.percentage == 100.0
                assert perf.grade == "A"
                assert perf.passed is True
                assert len(perf.recommendations) > 0


class TestPerformanceSummary:
    """Test performance summary generation."""

    def test_calculate_grade_a(self):
        """Test grade calculation for A."""
        grade = ExerciseService._calculate_grade(95.0)
        assert grade == "A"

    def test_calculate_grade_b(self):
        """Test grade calculation for B."""
        grade = ExerciseService._calculate_grade(85.0)
        assert grade == "B"

    def test_calculate_grade_c(self):
        """Test grade calculation for C."""
        grade = ExerciseService._calculate_grade(75.0)
        assert grade == "C"

    def test_calculate_grade_d(self):
        """Test grade calculation for D."""
        grade = ExerciseService._calculate_grade(65.0)
        assert grade == "D"

    def test_calculate_grade_f(self):
        """Test grade calculation for F."""
        grade = ExerciseService._calculate_grade(45.0)
        assert grade == "F"

    def test_generate_recommendations_excellent(self):
        """Test recommendations for excellent performance."""
        recommendations = ExerciseService._generate_recommendations(
            percentage=95.0,
            weak_topics=[],
            strong_topics=["Algebra", "Geometry"],
            difficulty=DifficultyLevel.MEDIUM,
            recommended_next_difficulty=DifficultyLevel.HARD
        )

        assert len(recommendations) > 0
        assert any("Excellent" in rec or "mastered" in rec for rec in recommendations)
        assert any("hard" in rec.lower() for rec in recommendations)

    def test_generate_recommendations_needs_improvement(self):
        """Test recommendations for performance needing improvement."""
        recommendations = ExerciseService._generate_recommendations(
            percentage=55.0,
            weak_topics=["Fractions", "Decimals"],
            strong_topics=[],
            difficulty=DifficultyLevel.MEDIUM,
            recommended_next_difficulty=DifficultyLevel.EASY
        )

        assert len(recommendations) > 0
        assert any("practice" in rec.lower() or "study" in rec.lower() for rec in recommendations)
        assert any("Fractions" in rec or "Decimals" in rec for rec in recommendations)


class TestAdaptiveDifficulty:
    """Test adaptive difficulty calculation."""

    @pytest.mark.asyncio
    async def test_recommend_increase_difficulty(self):
        """Test recommending harder difficulty for high scores."""
        next_difficulty = await ExerciseService._calculate_next_difficulty(
            student_id=str(ObjectId()),
            subject="Mathematics",
            score_percentage=85.0,
            current_difficulty=DifficultyLevel.EASY
        )

        assert next_difficulty == DifficultyLevel.MEDIUM

    @pytest.mark.asyncio
    async def test_recommend_decrease_difficulty(self):
        """Test recommending easier difficulty for low scores."""
        next_difficulty = await ExerciseService._calculate_next_difficulty(
            student_id=str(ObjectId()),
            subject="Mathematics",
            score_percentage=55.0,
            current_difficulty=DifficultyLevel.MEDIUM
        )

        assert next_difficulty == DifficultyLevel.EASY

    @pytest.mark.asyncio
    async def test_keep_same_difficulty(self):
        """Test keeping same difficulty for moderate scores."""
        next_difficulty = await ExerciseService._calculate_next_difficulty(
            student_id=str(ObjectId()),
            subject="Mathematics",
            score_percentage=70.0,
            current_difficulty=DifficultyLevel.MEDIUM
        )

        assert next_difficulty == DifficultyLevel.MEDIUM


class TestUserSubmissions:
    """Test user submissions retrieval."""

    @pytest.mark.asyncio
    async def test_get_user_submissions(self):
        """Test getting user's submission history."""
        user_id = str(ObjectId())
        exercise_id = str(ObjectId())
        submission_id = str(ObjectId())

        # Create sample submission document (as stored in MongoDB)
        submission_doc = {
            "_id": ObjectId(submission_id),
            "exercise_id": exercise_id,
            "student_id": user_id,
            "score": 8.0,
            "max_score": 10.0,
            "percentage": 80.0,
            "passed": True,
            "questions_correct": 8,
            "questions_total": 10,
            "time_taken_seconds": 300,
            "recommended_next_difficulty": DifficultyLevel.MEDIUM.value,
            "weak_topics": ["Fractions"],
            "submitted_at": datetime.utcnow()
        }

        # Mock database operations
        with patch('app.services.exercise_service.mongodb') as mock_db:
            mock_submissions_collection = Mock()
            mock_cursor = Mock()
            mock_cursor.sort = Mock(return_value=mock_cursor)
            mock_cursor.skip = Mock(return_value=mock_cursor)
            mock_cursor.limit = Mock(return_value=mock_cursor)
            mock_cursor.to_list = AsyncMock(return_value=[submission_doc])
            mock_submissions_collection.find = Mock(return_value=mock_cursor)

            mock_db.get_collection.return_value = mock_submissions_collection

            # Get user submissions
            submissions = await ExerciseService.get_user_submissions(
                user_id=user_id,
                limit=100,
                skip=0
            )

            # Verify results
            assert len(submissions) == 1
            submission = submissions[0]
            assert submission.id == submission_id
            assert submission.exercise_id == exercise_id
            assert submission.student_id == user_id
            assert submission.score == 8.0
            assert submission.max_score == 10.0
            assert submission.percentage == 80.0
            assert submission.passed is True
            assert submission.questions_correct == 8
            assert submission.questions_total == 10
            assert submission.time_taken_seconds == 300
            assert submission.recommended_next_difficulty == DifficultyLevel.MEDIUM
            assert submission.weak_topics == ["Fractions"]

    @pytest.mark.asyncio
    async def test_get_user_submissions_empty(self):
        """Test getting submissions when user has none."""
        user_id = str(ObjectId())

        # Mock empty results
        with patch('app.services.exercise_service.mongodb') as mock_db:
            mock_submissions_collection = Mock()
            mock_cursor = Mock()
            mock_cursor.sort = Mock(return_value=mock_cursor)
            mock_cursor.skip = Mock(return_value=mock_cursor)
            mock_cursor.limit = Mock(return_value=mock_cursor)
            mock_cursor.to_list = AsyncMock(return_value=[])
            mock_submissions_collection.find = Mock(return_value=mock_cursor)

            mock_db.get_collection.return_value = mock_submissions_collection

            # Get user submissions
            submissions = await ExerciseService.get_user_submissions(
                user_id=user_id,
                limit=100,
                skip=0
            )

            # Verify empty results
            assert len(submissions) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
