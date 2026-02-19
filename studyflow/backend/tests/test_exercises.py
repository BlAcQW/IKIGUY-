"""
Unit tests for Exercise Generation System.

Tests exercise generation, submission, scoring, and adaptive difficulty.
"""

import pytest
import sys
import os
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

# Add paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, "/opt/kasaai/apps")

from app.models.exercise import (
    Exercise,
    ExerciseQuestion,
    ExerciseSubmission,
    StudentPerformance,
    DifficultyLevel,
    QuestionType,
    ExerciseStatus,
    MCQOption,
    StudentAnswer,
    ExerciseGenerateRequest,
)
from app.services.exercise_service import ExerciseService


class TestExerciseModels:
    """Test exercise model validation and structure."""

    def test_mcq_option_creation(self):
        """Test MCQ option model."""
        option = MCQOption(
            label="A",
            text="Test option",
            is_correct=True
        )
        assert option.label == "A"
        assert option.is_correct is True

    def test_exercise_question_creation(self):
        """Test exercise question model."""
        question = ExerciseQuestion(
            question_type=QuestionType.MULTIPLE_CHOICE,
            question_text="What is 2+2?",
            options=[
                MCQOption(label="A", text="3", is_correct=False),
                MCQOption(label="B", text="4", is_correct=True),
                MCQOption(label="C", text="5", is_correct=False),
                MCQOption(label="D", text="6", is_correct=False),
            ],
            correct_answer="B",
            explanation="2+2 equals 4",
            topic="Basic Math",
            difficulty=DifficultyLevel.EASY,
            points=1
        )
        assert question.question_type == QuestionType.MULTIPLE_CHOICE
        assert len(question.options) == 4
        assert question.correct_answer == "B"

    def test_exercise_creation(self):
        """Test exercise model with multiple questions."""
        questions = [
            ExerciseQuestion(
                question_type=QuestionType.MULTIPLE_CHOICE,
                question_text="Question 1",
                correct_answer="A",
                explanation="Explanation 1",
                topic="Topic 1",
                difficulty=DifficultyLevel.EASY
            ),
            ExerciseQuestion(
                question_type=QuestionType.SHORT_ANSWER,
                question_text="Question 2",
                correct_answer="Answer 2",
                explanation="Explanation 2",
                topic="Topic 2",
                difficulty=DifficultyLevel.MEDIUM
            )
        ]

        exercise = Exercise(
            organization_id="org123",
            title="Test Exercise",
            subject="Mathematics",
            topics=["Topic 1", "Topic 2"],
            questions=questions,
            total_points=2,
            difficulty=DifficultyLevel.MEDIUM,
            created_by="user123"
        )

        assert exercise.title == "Test Exercise"
        assert len(exercise.questions) == 2
        assert exercise.total_points == 2
        assert exercise.status == ExerciseStatus.READY


class TestExerciseGeneration:
    """Test exercise generation with RAG."""

    @pytest.mark.asyncio
    async def test_build_generation_prompt(self):
        """Test prompt building for exercise generation."""
        material_content = "Test material about mathematics"
        topic = "Algebra"
        difficulty = DifficultyLevel.MEDIUM
        num_questions = 5
        question_types = [QuestionType.MULTIPLE_CHOICE]

        prompt = ExerciseService._build_generation_prompt(
            material_content=material_content,
            topic=topic,
            difficulty=difficulty,
            num_questions=num_questions,
            question_types=question_types
        )

        assert "5" in prompt
        assert "medium" in prompt.lower()
        assert "algebra" in prompt.lower()
        assert "multiple_choice" in prompt

    def test_parse_generated_questions_valid_json(self):
        """Test parsing valid AI response."""
        ai_response = """
        [
          {
            "question_type": "multiple_choice",
            "question_text": "What is 2+2?",
            "options": [
              {"label": "A", "text": "3", "is_correct": false},
              {"label": "B", "text": "4", "is_correct": true}
            ],
            "correct_answer": "B",
            "acceptable_answers": ["4", "four"],
            "explanation": "Basic addition",
            "topic": "Arithmetic",
            "points": 1
          }
        ]
        """

        questions = ExerciseService._parse_generated_questions(
            ai_response=ai_response,
            difficulty=DifficultyLevel.EASY,
            source_material_id="mat123"
        )

        assert len(questions) == 1
        assert questions[0].question_type == QuestionType.MULTIPLE_CHOICE
        assert questions[0].correct_answer == "B"
        assert len(questions[0].acceptable_answers) == 2

    def test_parse_generated_questions_invalid_json(self):
        """Test parsing invalid AI response."""
        ai_response = "This is not valid JSON"

        with pytest.raises(ValueError, match="No JSON array found"):
            ExerciseService._parse_generated_questions(
                ai_response=ai_response,
                difficulty=DifficultyLevel.EASY,
                source_material_id="mat123"
            )


class TestExerciseSubmission:
    """Test exercise submission and scoring."""

    def test_student_answer_creation(self):
        """Test student answer model."""
        answer = StudentAnswer(
            question_id="q123",
            answer="B",
            is_correct=True,
            points_earned=1.0,
            time_spent_seconds=30
        )

        assert answer.question_id == "q123"
        assert answer.is_correct is True
        assert answer.points_earned == 1.0

    def test_submission_creation(self):
        """Test exercise submission model."""
        answers = [
            StudentAnswer(question_id="q1", answer="B", is_correct=True, points_earned=1.0),
            StudentAnswer(question_id="q2", answer="Wrong", is_correct=False, points_earned=0.0),
        ]

        submission = ExerciseSubmission(
            exercise_id="ex123",
            student_id="student123",
            organization_id="org123",
            answers=answers,
            score=1.0,
            max_score=2.0,
            percentage=50.0,
            passed=False,
            time_taken_seconds=120,
            questions_correct=1,
            questions_total=2,
            difficulty_level=DifficultyLevel.MEDIUM,
            weak_topics=["Topic 2"],
            strong_topics=["Topic 1"],
            started_at=datetime.utcnow()
        )

        assert submission.score == 1.0
        assert submission.percentage == 50.0
        assert submission.passed is False
        assert submission.questions_correct == 1


class TestAdaptiveDifficulty:
    """Test adaptive difficulty logic."""

    @pytest.mark.asyncio
    async def test_difficulty_increase_high_score(self):
        """Test difficulty increases when score >= 80%."""
        next_difficulty = await ExerciseService._calculate_next_difficulty(
            student_id="student123",
            subject="Math",
            score_percentage=85.0,
            current_difficulty=DifficultyLevel.EASY
        )

        assert next_difficulty == DifficultyLevel.MEDIUM

    @pytest.mark.asyncio
    async def test_difficulty_decrease_low_score(self):
        """Test difficulty decreases when score < 60%."""
        next_difficulty = await ExerciseService._calculate_next_difficulty(
            student_id="student123",
            subject="Math",
            score_percentage=50.0,
            current_difficulty=DifficultyLevel.MEDIUM
        )

        assert next_difficulty == DifficultyLevel.EASY

    @pytest.mark.asyncio
    async def test_difficulty_same_moderate_score(self):
        """Test difficulty stays same for moderate scores."""
        next_difficulty = await ExerciseService._calculate_next_difficulty(
            student_id="student123",
            subject="Math",
            score_percentage=70.0,
            current_difficulty=DifficultyLevel.MEDIUM
        )

        assert next_difficulty == DifficultyLevel.MEDIUM

    @pytest.mark.asyncio
    async def test_difficulty_at_max_level(self):
        """Test difficulty doesn't increase beyond expert."""
        next_difficulty = await ExerciseService._calculate_next_difficulty(
            student_id="student123",
            subject="Math",
            score_percentage=90.0,
            current_difficulty=DifficultyLevel.EXPERT
        )

        assert next_difficulty == DifficultyLevel.EXPERT

    @pytest.mark.asyncio
    async def test_difficulty_at_min_level(self):
        """Test difficulty doesn't decrease below beginner."""
        next_difficulty = await ExerciseService._calculate_next_difficulty(
            student_id="student123",
            subject="Math",
            score_percentage=40.0,
            current_difficulty=DifficultyLevel.BEGINNER
        )

        assert next_difficulty == DifficultyLevel.BEGINNER


class TestPerformanceTracking:
    """Test student performance tracking."""

    def test_performance_model(self):
        """Test student performance model."""
        perf = StudentPerformance(
            student_id="student123",
            subject="Mathematics",
            total_exercises=10,
            total_questions=100,
            correct_answers=75,
            accuracy_percentage=75.0,
            current_difficulty=DifficultyLevel.MEDIUM,
            exercises_by_difficulty={
                "easy": 5,
                "medium": 5
            },
            topic_scores={
                "Algebra": 80.0,
                "Geometry": 60.0
            },
            weak_topics=["Geometry"],
            mastered_topics=["Algebra"],
            recent_scores=[70.0, 75.0, 80.0, 75.0, 85.0],
            average_recent_score=77.0
        )

        assert perf.total_exercises == 10
        assert perf.accuracy_percentage == 75.0
        assert len(perf.weak_topics) == 1
        assert perf.weak_topics[0] == "Geometry"


class TestExerciseAPI:
    """Test exercise API endpoints (integration tests)."""

    @pytest.mark.asyncio
    async def test_generate_exercise_request(self):
        """Test exercise generation request validation."""
        request = ExerciseGenerateRequest(
            material_id="mat123",
            topic="Algebra",
            difficulty=DifficultyLevel.MEDIUM,
            num_questions=10,
            question_types=[QuestionType.MULTIPLE_CHOICE],
            time_limit_minutes=30
        )

        assert request.material_id == "mat123"
        assert request.num_questions == 10
        assert request.difficulty == DifficultyLevel.MEDIUM

    @pytest.mark.asyncio
    async def test_generate_exercise_validates_num_questions(self):
        """Test num_questions validation."""
        # Should allow 1-50 questions
        valid_request = ExerciseGenerateRequest(
            material_id="mat123",
            num_questions=10
        )
        assert valid_request.num_questions == 10

        # Test boundary: 1 question is valid
        min_request = ExerciseGenerateRequest(
            material_id="mat123",
            num_questions=1
        )
        assert min_request.num_questions == 1

        # Test boundary: 50 questions is valid
        max_request = ExerciseGenerateRequest(
            material_id="mat123",
            num_questions=50
        )
        assert max_request.num_questions == 50


# Test fixtures
@pytest.fixture
def sample_exercise():
    """Create a sample exercise for testing."""
    questions = [
        ExerciseQuestion(
            question_type=QuestionType.MULTIPLE_CHOICE,
            question_text="What is the capital of France?",
            options=[
                MCQOption(label="A", text="London", is_correct=False),
                MCQOption(label="B", text="Paris", is_correct=True),
                MCQOption(label="C", text="Berlin", is_correct=False),
                MCQOption(label="D", text="Madrid", is_correct=False),
            ],
            correct_answer="B",
            explanation="Paris is the capital of France",
            topic="Geography",
            difficulty=DifficultyLevel.EASY
        )
    ]

    return Exercise(
        organization_id="org123",
        title="Geography Quiz",
        subject="Geography",
        topics=["European Capitals"],
        questions=questions,
        total_points=1,
        difficulty=DifficultyLevel.EASY,
        created_by="teacher123"
    )


@pytest.fixture
def sample_student_answers():
    """Create sample student answers."""
    return [
        StudentAnswer(
            question_id="q1",
            answer="B",
            time_spent_seconds=15
        )
    ]


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
