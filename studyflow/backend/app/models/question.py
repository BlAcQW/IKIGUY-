"""
Question models for StudyFlow.

Tracks questions asked by students and AI-generated responses.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId


class QuestionDifficulty(str, Enum):
    """Question difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    UNKNOWN = "unknown"


class QuestionType(str, Enum):
    """Type of question."""
    TEXT = "text"
    VOICE = "voice"
    IMAGE = "image"


class Question(BaseModel):
    """
    Question model for tracking student questions and AI responses.

    Attributes:
        id: MongoDB ObjectId as string
        session_id: Study session ID
        student_id: Student user ID
        subject: Subject area
        topic: Specific topic
        question_text: The question asked
        question_type: Type of question (text, voice, image)
        answer_text: AI-generated answer
        confidence_score: AI confidence in answer (0-1)
        sources_used: List of source materials used
        difficulty: Question difficulty level
        tokens_used: Total tokens consumed
        cost: Cost in GHS
        response_time_ms: Time to generate response
        feedback_rating: Student rating (1-5)
        feedback_text: Student feedback text
        metadata: Additional question data
        created_at: Question timestamp
    """
    id: Optional[str] = Field(default=None, alias="_id")
    session_id: str
    student_id: str
    subject: str
    topic: Optional[str] = None

    question_text: str
    question_type: QuestionType = QuestionType.TEXT
    answer_text: Optional[str] = None

    confidence_score: float = 0.0
    sources_used: List[str] = Field(default_factory=list)
    difficulty: QuestionDifficulty = QuestionDifficulty.UNKNOWN

    tokens_used: int = 0
    cost: float = 0.0
    response_time_ms: int = 0

    # Audio/TTS fields
    audio_generated: bool = False
    audio_cost: Optional[float] = None
    audio_transaction_id: Optional[str] = None
    audio_provider: Optional[str] = None

    # Student feedback
    feedback_rating: Optional[int] = None  # 1-5 stars
    feedback_text: Optional[str] = None

    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        """Pydantic configuration."""
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: lambda v: str(v)
        }


class QuestionCreate(BaseModel):
    """
    Schema for creating a new question.

    Attributes:
        session_id: Study session ID
        student_id: Student user ID
        subject: Subject area
        topic: Specific topic (optional)
        question_text: The question being asked
        question_type: Type of question
    """
    session_id: str
    student_id: str
    subject: str
    topic: Optional[str] = None
    question_text: str
    question_type: QuestionType = QuestionType.TEXT
    metadata: dict = Field(default_factory=dict)


class QuestionUpdate(BaseModel):
    """
    Schema for updating a question (mainly for adding answer/feedback).

    All fields are optional for partial updates.
    """
    answer_text: Optional[str] = None
    confidence_score: Optional[float] = None
    sources_used: Optional[List[str]] = None
    difficulty: Optional[QuestionDifficulty] = None
    tokens_used: Optional[int] = None
    cost: Optional[float] = None
    response_time_ms: Optional[int] = None
    feedback_rating: Optional[int] = None
    feedback_text: Optional[str] = None
    metadata: Optional[dict] = None


class QuestionResponse(BaseModel):
    """
    Question response model for API responses.
    """
    id: str
    session_id: str
    student_id: str
    subject: str
    topic: Optional[str]
    question_text: str
    question_type: QuestionType
    answer_text: Optional[str]
    confidence_score: float
    sources_used: List[str]
    cost: float
    created_at: datetime

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class QuestionFeedback(BaseModel):
    """
    Schema for submitting feedback on a question/answer.

    Attributes:
        rating: Rating from 1-5
        feedback_text: Optional text feedback
    """
    rating: int = Field(..., ge=1, le=5)
    feedback_text: Optional[str] = None


class QuestionStats(BaseModel):
    """
    Statistics about questions for a student/subject.

    Used for analytics and progress tracking.
    """
    total_questions: int
    by_subject: Dict[str, int] = Field(default_factory=dict)
    by_difficulty: Dict[str, int] = Field(default_factory=dict)
    average_confidence: float = 0.0
    total_cost: float = 0.0
    average_rating: Optional[float] = None
    period_start: datetime
    period_end: datetime

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
