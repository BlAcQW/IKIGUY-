"""
Progress tracking service for StudyFlow.

Handles student progress calculations, streak tracking, and reporting.
"""

import logging
from typing import Optional, List
from datetime import datetime, timedelta
from bson import ObjectId

from app.models.progress import (
    StudentProgress,
    SubjectProgress,
    TopicMastery,
    ProgressUpdate,
    WeeklyReport
)
from app.models.session import StudySession
from app.models.question import Question
from app.core.database import mongodb, COLLECTION_PROGRESS, COLLECTION_SESSIONS, COLLECTION_QUESTIONS
from app.config import settings

logger = logging.getLogger(__name__)


class ProgressService:
    """
    Service for tracking and analyzing student progress.

    Tracks learning metrics, streaks, and subject/topic mastery.
    """

    @staticmethod
    async def get_or_create_progress(
        student_id: str,
        organization_id: Optional[str] = None,
        school_id: Optional[str] = None
    ) -> StudentProgress:
        """
        Get existing progress or create new record with organization scoping.

        Args:
            student_id: Student user ID
            organization_id: Organization ID for scoping (required for creation)
            school_id: School ID (optional)

        Returns:
            StudentProgress instance
        """
        collection = mongodb.get_collection(COLLECTION_PROGRESS)

        # Build query
        query = {"student_id": student_id}
        if organization_id:
            query["organization_id"] = organization_id

        progress_doc = await collection.find_one(query)

        if progress_doc:
            progress_doc["id"] = str(progress_doc["_id"])
            return StudentProgress(**progress_doc)

        # Create new progress record (requires organization_id)
        if not organization_id:
            # Reason: Cannot create progress without organization context
            logger.warning(f"Cannot create progress for {student_id} without organization_id")
            # Return empty progress object for backward compatibility
            return StudentProgress(
                student_id=student_id,
                organization_id="",  # Will fail validation if saved
                school_id=school_id
            )

        progress = StudentProgress(
            student_id=student_id,
            organization_id=organization_id,
            school_id=school_id
        )
        result = await collection.insert_one(progress.dict(by_alias=True, exclude={"id"}))
        progress.id = str(result.inserted_id)

        logger.info(f"Progress tracking initialized for student: {student_id}")
        return progress

    @staticmethod
    async def update_progress_after_session(session_id: str):
        """
        Update progress after a session ends.

        Increments session count, time, and updates streaks.

        Args:
            session_id: Study session ID
        """
        # Get session data
        sessions_collection = mongodb.get_collection(COLLECTION_SESSIONS)
        session_doc = await sessions_collection.find_one({"_id": ObjectId(session_id)})

        if not session_doc:
            logger.warning(f"Session not found for progress update: {session_id}")
            return

        student_id = session_doc["student_id"]
        organization_id = session_doc.get("organization_id")
        school_id = session_doc.get("school_id")
        duration = session_doc.get("duration_minutes", 0)
        subject = session_doc.get("subject", "")

        # Get progress with organization context
        progress = await ProgressService.get_or_create_progress(
            student_id,
            organization_id,
            school_id
        )

        # Update overall metrics
        progress.total_sessions += 1
        progress.total_time_minutes += duration

        # Update streak
        await ProgressService._update_streak(progress)

        # Update subject progress
        await ProgressService._update_subject_progress(
            progress,
            subject,
            duration_minutes=duration,
            session_completed=True
        )

        # Save progress
        await ProgressService._save_progress(progress)

        logger.info(
            f"Progress updated after session: {session_id} "
            f"(student: {student_id}, duration: {duration:.1f}m)"
        )

    @staticmethod
    async def update_progress_after_question(question_id: str):
        """
        Update progress after a question is answered.

        Increments question count and updates topic mastery.

        Args:
            question_id: Question ID
        """
        # Get question data
        questions_collection = mongodb.get_collection(COLLECTION_QUESTIONS)
        question_doc = await questions_collection.find_one({"_id": ObjectId(question_id)})

        if not question_doc:
            logger.warning(f"Question not found for progress update: {question_id}")
            return

        student_id = question_doc["student_id"]
        organization_id = question_doc.get("organization_id")
        school_id = question_doc.get("school_id")
        subject = question_doc.get("subject", "")
        topic = question_doc.get("topic", "")

        # Get progress with organization context
        progress = await ProgressService.get_or_create_progress(
            student_id,
            organization_id,
            school_id
        )

        # Update overall metrics
        progress.total_questions += 1

        # Update subject progress
        await ProgressService._update_subject_progress(
            progress,
            subject,
            question_asked=True
        )

        # Update topic mastery
        if topic:
            await ProgressService._update_topic_mastery(
                progress,
                subject,
                topic,
                question_asked=True
            )

        # Save progress
        await ProgressService._save_progress(progress)

        logger.debug(f"Progress updated after question: {question_id}")

    @staticmethod
    async def _update_streak(progress: StudentProgress):
        """
        Update learning streak based on activity.

        Args:
            progress: StudentProgress instance
        """
        today = datetime.utcnow().date()
        last_activity = progress.last_activity_date

        if last_activity:
            last_date = last_activity.date()
            days_diff = (today - last_date).days

            if days_diff == 0:
                # Same day - no change
                pass
            elif days_diff == 1:
                # Consecutive day - increment streak
                progress.current_streak_days += 1
                progress.longest_streak_days = max(
                    progress.longest_streak_days,
                    progress.current_streak_days
                )
            else:
                # Streak broken - reset
                progress.current_streak_days = 1
        else:
            # First activity
            progress.current_streak_days = 1
            progress.longest_streak_days = 1

        progress.last_activity_date = datetime.utcnow()

    @staticmethod
    async def _update_subject_progress(
        progress: StudentProgress,
        subject: str,
        duration_minutes: float = 0.0,
        session_completed: bool = False,
        question_asked: bool = False,
        exercise_completed: bool = False
    ):
        """
        Update progress for a specific subject.

        Args:
            progress: StudentProgress instance
            subject: Subject name
            duration_minutes: Time spent on subject
            session_completed: Whether session was completed
            question_asked: Whether question was asked
            exercise_completed: Whether exercise was completed
        """
        # Find or create subject progress
        subject_progress = None
        for sp in progress.subjects_progress:
            if sp.subject == subject:
                subject_progress = sp
                break

        if not subject_progress:
            subject_progress = SubjectProgress(subject=subject)
            progress.subjects_progress.append(subject_progress)

        # Update metrics
        subject_progress.total_time_minutes += duration_minutes
        if question_asked:
            subject_progress.questions_asked += 1
        if exercise_completed:
            subject_progress.exercises_completed += 1

        subject_progress.last_activity = datetime.utcnow()

    @staticmethod
    async def _update_topic_mastery(
        progress: StudentProgress,
        subject: str,
        topic: str,
        question_asked: bool = False,
        correct_answer: bool = False
    ):
        """
        Update mastery for a specific topic.

        Args:
            progress: StudentProgress instance
            subject: Subject name
            topic: Topic name
            question_asked: Whether question was asked
            correct_answer: Whether answer was correct (for exercises)
        """
        # Find or create topic mastery
        topic_mastery = None
        for tm in progress.topic_mastery:
            if tm.topic == topic:
                topic_mastery = tm
                break

        if not topic_mastery:
            topic_mastery = TopicMastery(topic=topic)
            progress.topic_mastery.append(topic_mastery)

        # Update metrics
        if question_asked:
            topic_mastery.questions_asked += 1

        if correct_answer:
            topic_mastery.correct_answers += 1
            topic_mastery.total_attempts += 1
        elif not question_asked:
            # Incorrect answer
            topic_mastery.total_attempts += 1

        # Calculate mastery score
        if topic_mastery.total_attempts > 0:
            accuracy = topic_mastery.correct_answers / topic_mastery.total_attempts
            engagement = min(topic_mastery.questions_asked / 10.0, 1.0)  # Max at 10 questions
            topic_mastery.mastery_score = (accuracy * 0.7 + engagement * 0.3) * 100

        topic_mastery.last_practiced = datetime.utcnow()

    @staticmethod
    async def _save_progress(progress: StudentProgress):
        """
        Save progress to database.

        Args:
            progress: StudentProgress instance
        """
        progress.updated_at = datetime.utcnow()

        collection = mongodb.get_collection(COLLECTION_PROGRESS)
        await collection.update_one(
            {"student_id": progress.student_id},
            {
                "$set": progress.dict(by_alias=True, exclude={"id"})
            },
            upsert=True
        )

    @staticmethod
    async def get_student_progress(
        student_id: str,
        organization_id: Optional[str] = None,
        school_id: Optional[str] = None
    ) -> Optional[StudentProgress]:
        """
        Get student progress by ID with organization filtering.

        Args:
            student_id: Student user ID
            organization_id: Organization ID for access control (optional)
            school_id: School ID (optional)

        Returns:
            StudentProgress if found, None otherwise
        """
        return await ProgressService.get_or_create_progress(
            student_id,
            organization_id,
            school_id
        )

    @staticmethod
    async def get_subject_progress(
        student_id: str,
        subject: str,
        organization_id: Optional[str] = None,
        school_id: Optional[str] = None
    ) -> Optional[SubjectProgress]:
        """
        Get progress for a specific subject with organization filtering.

        Args:
            student_id: Student user ID
            subject: Subject name
            organization_id: Organization ID for access control (optional)
            school_id: School ID (optional)

        Returns:
            SubjectProgress if found, None otherwise
        """
        progress = await ProgressService.get_or_create_progress(
            student_id,
            organization_id,
            school_id
        )

        for sp in progress.subjects_progress:
            if sp.subject == subject:
                return sp

        return None

    @staticmethod
    async def get_weekly_summary(
        student_id: str,
        organization_id: Optional[str] = None
    ) -> dict:
        """
        Generate weekly summary for student with organization filtering.

        Args:
            student_id: Student user ID
            organization_id: Organization ID for access control (optional)

        Returns:
            Dict with weekly statistics
        """
        # Get sessions from last 7 days
        week_ago = datetime.utcnow() - timedelta(days=7)
        sessions_collection = mongodb.get_collection(COLLECTION_SESSIONS)

        query = {
            "student_id": student_id,
            "started_at": {"$gte": week_ago}
        }
        if organization_id:
            query["organization_id"] = organization_id

        cursor = sessions_collection.find(query)

        sessions = []
        async for session_doc in cursor:
            sessions.append(session_doc)

        # Calculate weekly stats
        total_sessions = len(sessions)
        total_time = sum(s.get("duration_minutes", 0) for s in sessions)
        total_questions = sum(s.get("questions_asked", 0) for s in sessions)
        subjects_studied = list(set(s.get("subject", "") for s in sessions if s.get("subject")))

        # Get progress for streak info
        progress = await ProgressService.get_or_create_progress(student_id, organization_id)

        return {
            "week_start": week_ago.isoformat(),
            "week_end": datetime.utcnow().isoformat(),
            "total_sessions": total_sessions,
            "total_time_minutes": total_time,
            "total_questions": total_questions,
            "subjects_studied": subjects_studied,
            "current_streak_days": progress.current_streak_days,
            "avg_session_duration": total_time / total_sessions if total_sessions > 0 else 0
        }

    @staticmethod
    async def get_parent_dashboard(
        parent_id: str,
        student_ids: List[str],
        organization_id: Optional[str] = None
    ) -> dict:
        """
        Get dashboard data for parent with multiple students.

        Args:
            parent_id: Parent user ID
            student_ids: List of student IDs
            organization_id: Organization ID for access control (optional)

        Returns:
            Dict with all students' progress
        """
        students_progress = []

        for student_id in student_ids:
            progress = await ProgressService.get_or_create_progress(
                student_id,
                organization_id
            )
            weekly = await ProgressService.get_weekly_summary(
                student_id,
                organization_id
            )

            students_progress.append({
                "student_id": student_id,
                "total_sessions": progress.total_sessions,
                "total_time_minutes": progress.total_time_minutes,
                "current_streak_days": progress.current_streak_days,
                "weekly_summary": weekly,
                "subjects_progress": [sp.dict() for sp in progress.subjects_progress]
            })

        return {
            "parent_id": parent_id,
            "students": students_progress,
            "generated_at": datetime.utcnow().isoformat()
        }

    @staticmethod
    async def calculate_mastery_level(mastery_score: float) -> str:
        """
        Convert mastery score to level.

        Args:
            mastery_score: Score from 0-100

        Returns:
            Mastery level string
        """
        if mastery_score >= 80:
            return "mastered"
        elif mastery_score >= 60:
            return "proficient"
        elif mastery_score >= 40:
            return "learning"
        elif mastery_score >= 20:
            return "struggling"
        else:
            return "beginner"
