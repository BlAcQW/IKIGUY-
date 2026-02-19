"""
Student progress models for StudyFlow.

Tracks learning progress, topic mastery, and performance metrics.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId


class TopicMastery(BaseModel):
    """
    Topic mastery tracking.

    Attributes:
        topic: Topic name
        questions_asked: Number of questions on this topic
        correct_answers: Number of correct answers (from exercises)
        total_attempts: Total exercise attempts
        mastery_score: Mastery score (0-100)
        last_practiced: Last practice timestamp
    """
    topic: str
    questions_asked: int = 0
    correct_answers: int = 0
    total_attempts: int = 0
    mastery_score: float = 0.0  # 0-100
    last_practiced: Optional[datetime] = None

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SubjectProgress(BaseModel):
    """
    Progress tracking for a specific subject.

    Attributes:
        subject: Subject name
        total_time_minutes: Total time spent on subject
        questions_asked: Total questions asked
        exercises_completed: Total exercises completed
        average_score: Average exercise score (0-100)
        topics_mastered: List of mastered topics
        topics_in_progress: Topics currently being learned
        topics_struggling: Topics needing improvement
        last_activity: Last activity timestamp
    """
    subject: str
    total_time_minutes: float = 0.0
    questions_asked: int = 0
    exercises_completed: int = 0
    average_score: float = 0.0
    topics_mastered: List[str] = Field(default_factory=list)
    topics_in_progress: List[str] = Field(default_factory=list)
    topics_struggling: List[str] = Field(default_factory=list)
    last_activity: Optional[datetime] = None

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StudentProgress(BaseModel):
    """
    Overall student progress model.

    Tracks all learning metrics for a student across subjects.

    Attributes:
        id: MongoDB ObjectId as string
        organization_id: Organization ID for multi-tenancy
        school_id: School ID (optional)
        student_id: Student user ID
        total_sessions: Total study sessions
        total_time_minutes: Total time spent learning
        total_questions: Total questions asked
        total_exercises: Total exercises completed
        current_streak_days: Current learning streak
        longest_streak_days: Longest learning streak
        subjects_progress: Progress per subject
        topic_mastery: Mastery per topic
        weekly_summary: Last 7 days summary
        metadata: Additional progress data
        updated_at: Last update timestamp
    """
    id: Optional[str] = Field(default=None, alias="_id")
    organization_id: str
    school_id: Optional[str] = None
    student_id: str

    # Overall metrics
    total_sessions: int = 0
    total_time_minutes: float = 0.0
    total_questions: int = 0
    total_exercises: int = 0

    # Streaks
    current_streak_days: int = 0
    longest_streak_days: int = 0
    last_activity_date: Optional[datetime] = None

    # Subject-level progress
    subjects_progress: List[SubjectProgress] = Field(default_factory=list)

    # Topic-level mastery
    topic_mastery: List[TopicMastery] = Field(default_factory=list)

    # Weekly summary (last 7 days)
    weekly_summary: Dict[str, Any] = Field(default_factory=dict)

    metadata: dict = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic configuration."""
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: lambda v: str(v)
        }


class ProgressUpdate(BaseModel):
    """
    Schema for updating student progress.

    Used to increment counters after activities.
    """
    student_id: str
    session_completed: bool = False
    session_duration_minutes: float = 0.0
    question_asked: bool = False
    exercise_completed: bool = False
    exercise_score: Optional[float] = None
    subject: Optional[str] = None
    topic: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ProgressResponse(BaseModel):
    """
    Progress response model for API responses.
    """
    organization_id: str
    school_id: Optional[str]
    student_id: str
    total_sessions: int
    total_time_minutes: float
    total_questions: int
    total_exercises: int
    current_streak_days: int
    subjects_progress: List[SubjectProgress]
    updated_at: datetime

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WeeklyReport(BaseModel):
    """
    Weekly progress report for parents.

    AI-generated summary of student performance.
    """
    student_id: str
    student_name: str
    week_start: datetime
    week_end: datetime

    # Summary stats
    total_time_minutes: float
    total_questions: int
    total_exercises: int
    average_score: float

    # Subject breakdown
    subjects_studied: List[str]
    top_subject: Optional[str] = None
    struggling_subject: Optional[str] = None

    # AI insights
    strengths: List[str] = Field(default_factory=list)
    areas_for_improvement: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)

    # Engagement
    learning_streak: int
    most_active_day: Optional[str] = None
    most_active_time: Optional[str] = None

    generated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
