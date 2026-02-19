"""
Database models for StudyFlow.

All models use Pydantic for validation and MongoDB for storage.
"""

from .user import User, UserRole, UserCreate, UserUpdate
from .session import StudySession, SessionStatus, SessionCreate
from .question import Question, QuestionDifficulty, QuestionCreate
from .progress import StudentProgress, ProgressUpdate
from .wallet import Wallet, Transaction, TransactionType
from .material import StudyMaterial, MaterialType, ProcessingStatus, MaterialCreate, MaterialUpdate
from .exercise import (
    Exercise,
    ExerciseQuestion,
    ExerciseSubmission,
    StudentPerformance,
    DifficultyLevel,
    QuestionType as ExerciseQuestionType,
    ExerciseStatus,
    ExerciseGenerateRequest,
    ExerciseCreate,
    ExerciseUpdate,
    ExerciseResponse,
    ExerciseDetailResponse,
    SubmissionCreate,
    SubmissionResponse,
    PerformanceRecommendation,
)

__all__ = [
    "User",
    "UserRole",
    "UserCreate",
    "UserUpdate",
    "StudySession",
    "SessionStatus",
    "SessionCreate",
    "Question",
    "QuestionDifficulty",
    "QuestionCreate",
    "StudentProgress",
    "ProgressUpdate",
    "Wallet",
    "Transaction",
    "TransactionType",
    "StudyMaterial",
    "MaterialType",
    "ProcessingStatus",
    "MaterialCreate",
    "MaterialUpdate",
    "Exercise",
    "ExerciseQuestion",
    "ExerciseSubmission",
    "StudentPerformance",
    "DifficultyLevel",
    "ExerciseQuestionType",
    "ExerciseStatus",
    "ExerciseGenerateRequest",
    "ExerciseCreate",
    "ExerciseUpdate",
    "ExerciseResponse",
    "ExerciseDetailResponse",
    "SubmissionCreate",
    "SubmissionResponse",
    "PerformanceRecommendation",
]
