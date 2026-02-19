"""
Assessment Models for Conversational Assessment System.

Shared models for interactive learning assessments across all apps.
Used by ConversationalAssessmentService.

Author: KasaAI
Created: 2025-11-07
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class AssessmentType(str, Enum):
    """Type of assessment."""
    FORMATIVE = "formative"  # Ongoing learning assessment
    SUMMATIVE = "summative"  # Final/graded assessment
    DIAGNOSTIC = "diagnostic"  # Initial knowledge check
    ADAPTIVE = "adaptive"  # Difficulty adjusts based on performance


class QuestionDifficulty(str, Enum):
    """Question difficulty levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class UnderstandingLevel(str, Enum):
    """Student understanding levels."""
    NO_UNDERSTANDING = "no_understanding"  # 0-20%
    MINIMAL = "minimal"  # 21-40%
    PARTIAL = "partial"  # 41-60%
    GOOD = "good"  # 61-80%
    EXCELLENT = "excellent"  # 81-100%


class AssessmentStatus(str, Enum):
    """Assessment session status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class QuestionResponse(BaseModel):
    """Student's response to an assessment question."""
    question_id: str
    question_text: str
    student_answer: str
    expected_answer: Optional[str] = None

    # Scoring
    score: float = Field(0.0, ge=0.0, le=1.0)  # 0-1 score
    understanding_level: UnderstandingLevel = UnderstandingLevel.NO_UNDERSTANDING
    is_correct: bool = False

    # Analysis
    key_concepts_identified: List[str] = Field(default_factory=list)
    missing_concepts: List[str] = Field(default_factory=list)
    feedback: Optional[str] = None

    # Metadata
    response_time_seconds: float = 0.0
    confidence_score: float = 0.0
    difficulty: QuestionDifficulty = QuestionDifficulty.INTERMEDIATE
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic configuration."""
        json_encoders = {datetime: lambda v: v.isoformat()}


class AssessmentQuestion(BaseModel):
    """Assessment question with expected answer and rubric."""
    id: str
    question_text: str
    expected_answer: Optional[str] = None
    key_concepts: List[str] = Field(default_factory=list)
    difficulty: QuestionDifficulty = QuestionDifficulty.INTERMEDIATE

    # Question metadata
    topic: Optional[str] = None
    subject: Optional[str] = None
    max_score: float = 1.0
    time_limit_seconds: Optional[int] = None

    # RAG context
    relevant_documents: List[str] = Field(default_factory=list)
    context_snippet: Optional[str] = None

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class AssessmentSession(BaseModel):
    """Conversational assessment session."""
    id: Optional[str] = Field(default=None, alias="_id")
    organization_id: str
    user_id: str

    # Session info
    assessment_type: AssessmentType = AssessmentType.FORMATIVE
    status: AssessmentStatus = AssessmentStatus.NOT_STARTED

    # Content scope
    subject: str
    topics: List[str] = Field(default_factory=list)
    collection_name: str  # RAG collection for knowledge base

    # Questions and responses
    questions: List[AssessmentQuestion] = Field(default_factory=list)
    responses: List[QuestionResponse] = Field(default_factory=list)

    # Current state
    current_question_index: int = 0
    total_questions: int = 5  # Default

    # Scoring
    overall_score: float = 0.0  # 0-1 scale
    overall_understanding: UnderstandingLevel = UnderstandingLevel.NO_UNDERSTANDING

    # Performance analytics
    strong_areas: List[str] = Field(default_factory=list)
    weak_areas: List[str] = Field(default_factory=list)
    recommended_topics: List[str] = Field(default_factory=list)

    # Feedback
    final_feedback: Optional[str] = None
    encouragement_message: Optional[str] = None

    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_time_seconds: float = 0.0

    # Cost tracking
    total_cost: float = 0.0
    llm_tokens_used: int = 0

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic configuration."""
        populate_by_name = True
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class AssessmentEvaluation(BaseModel):
    """Evaluation result for a student answer."""
    score: float = Field(..., ge=0.0, le=1.0)
    understanding_level: UnderstandingLevel
    is_correct: bool

    # Analysis details
    key_concepts_identified: List[str] = Field(default_factory=list)
    missing_concepts: List[str] = Field(default_factory=list)
    partial_credit_areas: List[str] = Field(default_factory=list)

    # Feedback
    feedback: str
    explanation: Optional[str] = None
    hints_for_improvement: List[str] = Field(default_factory=list)

    # Metadata
    evaluation_method: str = "llm"  # llm, semantic, keyword, hybrid
    confidence: float = 0.0
    processing_time_seconds: float = 0.0

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class AssessmentSummary(BaseModel):
    """Summary of assessment results."""
    session_id: str
    user_id: str
    organization_id: str

    # Basic info
    subject: str
    topics: List[str]
    assessment_type: AssessmentType

    # Performance metrics
    total_questions: int
    questions_answered: int
    overall_score: float  # 0-1
    overall_percentage: float  # 0-100
    understanding_level: UnderstandingLevel

    # Detailed breakdown
    score_by_topic: Dict[str, float] = Field(default_factory=dict)
    score_by_difficulty: Dict[str, float] = Field(default_factory=dict)

    # Analysis
    strong_areas: List[str]
    weak_areas: List[str]
    recommended_next_steps: List[str]

    # Timing
    total_time_seconds: float
    average_time_per_question: float

    # Feedback
    final_feedback: str
    encouragement_message: str

    # Timestamp
    completed_at: datetime

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class AssessmentRequest(BaseModel):
    """Request to create a new assessment session."""
    organization_id: str
    user_id: str
    subject: str
    topics: List[str]
    collection_name: str

    # Configuration
    assessment_type: AssessmentType = AssessmentType.FORMATIVE
    num_questions: int = Field(5, ge=1, le=20)
    difficulty_range: List[QuestionDifficulty] = Field(
        default_factory=lambda: [
            QuestionDifficulty.BEGINNER,
            QuestionDifficulty.INTERMEDIATE
        ]
    )

    # Optional customization
    custom_instructions: Optional[str] = None
    time_limit_seconds: Optional[int] = None

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class AnswerSubmission(BaseModel):
    """Submission of answer to assessment question."""
    session_id: str
    question_id: str
    answer_text: str
    audio_base64: Optional[str] = None  # If submitted via voice
    response_time_seconds: float = 0.0

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
