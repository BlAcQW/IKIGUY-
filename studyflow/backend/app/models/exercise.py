"""
Exercise models for StudyFlow.

Handles exercise generation, questions (MCQ, short answer, essay),
and student submissions with adaptive difficulty.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId


class DifficultyLevel(str, Enum):
    """Exercise difficulty levels for adaptive learning."""
    BEGINNER = "beginner"
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


class QuestionType(str, Enum):
    """Type of exercise question."""
    MULTIPLE_CHOICE = "multiple_choice"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"
    TRUE_FALSE = "true_false"


class ExerciseStatus(str, Enum):
    """Exercise generation and completion status."""
    GENERATING = "generating"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# Exercise Question Models

class MCQOption(BaseModel):
    """Multiple choice question option."""
    label: str  # A, B, C, D
    text: str
    is_correct: bool = False


class ExerciseQuestion(BaseModel):
    """
    Individual question within an exercise.

    Supports multiple question types with explanations.
    """
    question_id: str = Field(default_factory=lambda: str(ObjectId()))
    question_type: QuestionType
    question_text: str

    # MCQ specific
    options: Optional[List[MCQOption]] = None

    # Correct answer(s)
    correct_answer: str  # For MCQ: option label (A,B,C,D), for others: text answer
    acceptable_answers: List[str] = Field(default_factory=list)  # Alternative correct answers

    # Explanation and learning
    explanation: str
    topic: str
    difficulty: DifficultyLevel

    # Metadata
    points: int = 1
    time_limit_seconds: Optional[int] = None
    hints: List[str] = Field(default_factory=list)

    # Source tracking
    source_material_id: Optional[str] = None
    source_chunk_ids: List[str] = Field(default_factory=list)


class StudentAnswer(BaseModel):
    """Student's answer to a question."""
    question_id: str
    answer: str
    is_correct: Optional[bool] = None
    points_earned: float = 0.0
    time_spent_seconds: Optional[int] = None
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)  # For AI feedback and other data


# Main Exercise Models

class Exercise(BaseModel):
    """
    Exercise/Quiz model containing multiple questions.

    Generated from study materials using RAG.
    """
    id: Optional[str] = Field(default=None, alias="_id")
    organization_id: str
    school_id: Optional[str] = None

    # Exercise metadata
    title: str
    description: Optional[str] = None
    subject: str
    topics: List[str] = Field(default_factory=list)

    # Content
    questions: List[ExerciseQuestion]
    total_points: int

    # Difficulty and targeting
    difficulty: DifficultyLevel
    recommended_for_grades: List[int] = Field(default_factory=list)

    # Generation metadata
    generated_from_material_id: Optional[str] = None
    generation_prompt: Optional[str] = None
    generation_cost: float = 0.0
    tokens_used: int = 0

    # Settings
    time_limit_minutes: Optional[int] = None
    passing_score_percentage: float = 70.0
    allow_review: bool = True
    shuffle_questions: bool = False
    shuffle_options: bool = True

    # Access control
    created_by: str  # User ID
    is_public: bool = False
    assigned_to: List[str] = Field(default_factory=list)  # Student IDs

    # Status
    status: ExerciseStatus = ExerciseStatus.READY

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        """Pydantic configuration."""
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: lambda v: str(v)
        }


class ExerciseSubmission(BaseModel):
    """
    Student's submission for an exercise.

    Tracks answers, scoring, and performance.
    """
    id: Optional[str] = Field(default=None, alias="_id")
    exercise_id: str
    student_id: str
    organization_id: str

    # Answers
    answers: List[StudentAnswer]

    # Scoring
    score: float  # Points earned
    max_score: float  # Total possible points
    percentage: float
    passed: bool

    # Performance metrics
    time_taken_seconds: int
    questions_correct: int
    questions_total: int

    # Adaptive learning data
    difficulty_level: DifficultyLevel
    recommended_next_difficulty: Optional[DifficultyLevel] = None
    weak_topics: List[str] = Field(default_factory=list)
    strong_topics: List[str] = Field(default_factory=list)

    # Status
    started_at: datetime
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic configuration."""
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: lambda v: str(v)
        }


class StudentPerformance(BaseModel):
    """
    Aggregate performance data for adaptive difficulty.

    Used to track student progress and recommend appropriate exercises.
    """
    student_id: str
    subject: str
    topic: Optional[str] = None

    # Performance metrics
    total_exercises: int = 0
    total_questions: int = 0
    correct_answers: int = 0
    accuracy_percentage: float = 0.0

    # Difficulty progression
    current_difficulty: DifficultyLevel = DifficultyLevel.EASY
    exercises_by_difficulty: Dict[str, int] = Field(default_factory=dict)

    # Topic mastery
    topic_scores: Dict[str, float] = Field(default_factory=dict)  # topic -> avg score
    weak_topics: List[str] = Field(default_factory=list)
    mastered_topics: List[str] = Field(default_factory=list)

    # Recent performance (last 5 exercises)
    recent_scores: List[float] = Field(default_factory=list)
    average_recent_score: float = 0.0

    # Timestamps
    last_exercise_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Request/Response Schemas

class ExerciseGenerateRequest(BaseModel):
    """Request schema for generating exercises."""
    material_id: str
    topic: Optional[str] = None
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    num_questions: int = Field(default=10, ge=1, le=50)
    question_types: List[QuestionType] = Field(
        default_factory=lambda: [QuestionType.MULTIPLE_CHOICE]
    )
    time_limit_minutes: Optional[int] = None


class ExerciseCreate(BaseModel):
    """Schema for manually creating an exercise."""
    title: str
    description: Optional[str] = None
    subject: str
    topics: List[str]
    questions: List[ExerciseQuestion]
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    time_limit_minutes: Optional[int] = None
    passing_score_percentage: float = 70.0


class ExerciseUpdate(BaseModel):
    """Schema for updating an exercise."""
    title: Optional[str] = None
    description: Optional[str] = None
    topics: Optional[List[str]] = None
    time_limit_minutes: Optional[int] = None
    passing_score_percentage: Optional[float] = None
    is_public: Optional[bool] = None
    assigned_to: Optional[List[str]] = None


class ExerciseResponse(BaseModel):
    """API response for exercise details."""
    id: str
    title: str
    description: Optional[str]
    subject: str
    topics: List[str]
    difficulty: DifficultyLevel
    total_points: int
    num_questions: int
    time_limit_minutes: Optional[int]
    passing_score_percentage: float
    created_by: str
    created_at: datetime
    status: ExerciseStatus

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ExerciseDetailResponse(ExerciseResponse):
    """Detailed exercise response including questions."""
    questions: List[ExerciseQuestion]


class SubmissionCreate(BaseModel):
    """Schema for submitting exercise answers."""
    answers: List[StudentAnswer]
    time_taken_seconds: int


class SubmissionResponse(BaseModel):
    """API response for exercise submission result."""
    id: str
    exercise_id: str
    student_id: str
    score: float
    max_score: float
    percentage: float
    passed: bool
    questions_correct: int
    questions_total: int
    time_taken_seconds: int
    recommended_next_difficulty: Optional[DifficultyLevel]
    weak_topics: List[str]
    submitted_at: datetime

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PerformanceRecommendation(BaseModel):
    """Recommendation for next exercise based on performance."""
    recommended_difficulty: DifficultyLevel
    recommended_topics: List[str]
    reason: str
    focus_areas: List[str]


# Story 4.2: Enhanced Feedback Models

class QuestionFeedback(BaseModel):
    """
    Detailed feedback for a single question.

    Includes correct answer, explanation, and student performance.
    """
    question_id: str
    question_number: int
    question_text: str
    question_type: QuestionType

    # Student's answer
    student_answer: str
    is_correct: bool
    points_earned: float
    max_points: float

    # Correct answer and explanation
    correct_answer: str
    explanation: str

    # Additional feedback (for AI-graded answers)
    ai_feedback: Optional[str] = None
    alternative_correct_answers: List[str] = Field(default_factory=list)

    # Learning support
    topic: str
    hints_if_incorrect: List[str] = Field(default_factory=list)


class PerformanceSummary(BaseModel):
    """
    Performance summary for a submission.

    Provides insights and actionable recommendations.
    """
    # Score metrics
    total_score: float
    max_score: float
    percentage: float
    grade: str  # A, B, C, D, F
    passed: bool

    # Question breakdown
    questions_total: int
    questions_correct: int
    questions_incorrect: int

    # Performance analysis
    strong_topics: List[str]
    weak_topics: List[str]
    accuracy_by_topic: Dict[str, float]

    # Time analysis
    time_taken_seconds: int
    average_time_per_question: float

    # Next steps
    recommended_next_difficulty: Optional[DifficultyLevel]
    recommendations: List[str]
    focus_areas: List[str]


class SubmissionFeedbackResponse(BaseModel):
    """
    Complete feedback response for an exercise submission.

    Includes per-question feedback, performance summary, and recommendations.
    """
    submission_id: str
    exercise_id: str
    student_id: str

    # Per-question feedback
    question_feedback: List[QuestionFeedback]

    # Performance summary
    performance: PerformanceSummary

    # Submitted at
    submitted_at: datetime

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
