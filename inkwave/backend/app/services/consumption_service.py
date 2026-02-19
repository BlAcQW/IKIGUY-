"""
Consumption tracking service.

Provides unified tracking for all book consumption events.
Single source of truth for both admin and user dashboards.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.consumption import (
    ConsumptionEvent,
    ConsumptionEventInDB,
    ConsumptionEventCreate,
    ConsumptionEventType,
    ConsumptionMode,
    ConsumptionSession,
    UserConsumptionStats,
    BookConsumptionStats,
    ProgressUpdateRequest,
    CompletionRequest,
)

logger = logging.getLogger(__name__)


class ConsumptionService:
    """
    Service for tracking book consumption.

    Handles:
    - Recording consumption events
    - Aggregating session data
    - Computing user and book statistics
    - Supporting both admin and user dashboard queries
    """

    COLLECTION_NAME = "consumption_events"

    async def record_event(
        self,
        user_id: str,
        event_data: ConsumptionEventCreate,
    ) -> ConsumptionEventInDB:
        """
        Record a consumption event.

        Args:
            user_id: User ID from authentication
            event_data: Event data from request

        Returns:
            Created consumption event
        """
        db = get_db()

        event = ConsumptionEvent(
            user_id=user_id,
            book_id=event_data.book_id,
            session_id=event_data.session_id,
            event_type=event_data.event_type,
            consumption_mode=event_data.consumption_mode,
            chunk_index=event_data.chunk_index,
            total_chunks=event_data.total_chunks,
            progress_percentage=event_data.progress_percentage,
            position_seconds=event_data.position_seconds,
            duration_seconds=event_data.duration_seconds,
            cumulative_time_seconds=event_data.cumulative_time_seconds,
            book_title=event_data.book_title,
            book_author=event_data.book_author,
            context=event_data.context,
            device_type=event_data.device_type,
            browser=event_data.browser,
            user_agent=event_data.user_agent,
        )

        result = await db[self.COLLECTION_NAME].insert_one(event.model_dump())

        logger.info(
            f"Recorded consumption event: user={user_id}, "
            f"book={event_data.book_id}, type={event_data.event_type.value}"
        )

        return ConsumptionEventInDB(**event.model_dump(), _id=str(result.inserted_id))

    async def record_progress_update(
        self,
        user_id: str,
        update: ProgressUpdateRequest,
    ) -> ConsumptionEventInDB:
        """
        Record a timer-based progress update.

        Called periodically by frontend (every 30 seconds or on pause).

        Args:
            user_id: User ID
            update: Progress update data

        Returns:
            Created progress event
        """
        # Calculate progress percentage
        progress = 0.0
        if update.total_chunks > 0:
            progress = ((update.chunk_index + 1) / update.total_chunks) * 100

        event_data = ConsumptionEventCreate(
            book_id=update.book_id,
            session_id=update.session_id,
            event_type=ConsumptionEventType.PROGRESS_UPDATE,
            consumption_mode=update.consumption_mode,
            chunk_index=update.chunk_index,
            total_chunks=update.total_chunks,
            progress_percentage=min(progress, 100.0),
            position_seconds=update.position_seconds,
            duration_seconds=update.duration_since_last_update,
            cumulative_time_seconds=update.cumulative_time_seconds,
        )

        return await self.record_event(user_id, event_data)

    async def record_completion(
        self,
        user_id: str,
        completion: CompletionRequest,
    ) -> ConsumptionEventInDB:
        """
        Record deterministic book completion.

        Called when user finishes the last chunk.

        Args:
            user_id: User ID
            completion: Completion data

        Returns:
            Created completion event
        """
        event_data = ConsumptionEventCreate(
            book_id=completion.book_id,
            session_id=completion.session_id,
            event_type=ConsumptionEventType.COMPLETED,
            consumption_mode=completion.consumption_mode,
            chunk_index=completion.final_chunk_index,
            total_chunks=completion.total_chunks,
            progress_percentage=100.0,
            cumulative_time_seconds=completion.total_time_seconds,
            context={
                "all_chunks_consumed": completion.all_chunks_consumed,
                "chunk_indices_consumed": completion.chunk_indices_consumed,
            },
        )

        return await self.record_event(user_id, event_data)

    async def get_user_sessions(
        self,
        user_id: str,
        book_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ConsumptionSession]:
        """
        Get aggregated consumption sessions for a user.

        Args:
            user_id: User ID
            book_id: Optional book filter
            limit: Max sessions to return
            offset: Pagination offset

        Returns:
            List of consumption sessions
        """
        db = get_db()

        # Build match stage
        match_stage: Dict[str, Any] = {"user_id": user_id}
        if book_id:
            match_stage["book_id"] = book_id

        # Aggregate sessions
        pipeline = [
            {"$match": match_stage},
            {"$sort": {"timestamp": 1}},
            {
                "$group": {
                    "_id": "$session_id",
                    "user_id": {"$first": "$user_id"},
                    "book_id": {"$first": "$book_id"},
                    "book_title": {"$first": "$book_title"},
                    "book_author": {"$first": "$book_author"},
                    "consumption_mode": {"$first": "$consumption_mode"},
                    "started_at": {"$min": "$timestamp"},
                    "ended_at": {"$max": "$timestamp"},
                    "start_chunk": {"$min": "$chunk_index"},
                    "end_chunk": {"$max": "$chunk_index"},
                    "progress_percentage": {"$max": "$progress_percentage"},
                    "total_duration_seconds": {"$sum": "$duration_seconds"},
                    "events": {"$push": "$event_type"},
                }
            },
            {"$sort": {"started_at": -1}},
            {"$skip": offset},
            {"$limit": limit},
        ]

        cursor = db[self.COLLECTION_NAME].aggregate(pipeline)
        sessions = []

        async for doc in cursor:
            is_completed = ConsumptionEventType.COMPLETED.value in doc.get("events", [])
            sessions.append(
                ConsumptionSession(
                    session_id=doc["_id"],
                    user_id=doc["user_id"],
                    book_id=doc["book_id"],
                    book_title=doc.get("book_title"),
                    book_author=doc.get("book_author"),
                    consumption_mode=doc["consumption_mode"],
                    started_at=doc["started_at"],
                    ended_at=doc.get("ended_at"),
                    start_chunk=doc.get("start_chunk", 0),
                    end_chunk=doc.get("end_chunk", 0),
                    progress_percentage=doc.get("progress_percentage", 0.0),
                    total_duration_seconds=doc.get("total_duration_seconds", 0.0),
                    is_completed=is_completed,
                )
            )

        return sessions

    async def get_user_stats(
        self,
        user_id: str,
        period_days: Optional[int] = None,
    ) -> UserConsumptionStats:
        """
        Get aggregated consumption stats for a user.

        Args:
            user_id: User ID
            period_days: Optional period filter (e.g., last 7 days)

        Returns:
            User consumption statistics
        """
        db = get_db()

        # Build match stage
        match_stage: Dict[str, Any] = {"user_id": user_id}
        if period_days:
            cutoff = datetime.utcnow() - timedelta(days=period_days)
            match_stage["timestamp"] = {"$gte": cutoff}

        # Count unique books
        books_pipeline = [
            {"$match": match_stage},
            {
                "$group": {
                    "_id": "$book_id",
                    "has_completed": {
                        "$max": {
                            "$cond": [
                                {"$eq": ["$event_type", ConsumptionEventType.COMPLETED.value]},
                                1,
                                0,
                            ]
                        }
                    },
                    "has_started": {
                        "$max": {
                            "$cond": [
                                {
                                    "$in": [
                                        "$event_type",
                                        [
                                            ConsumptionEventType.BOOK_OPENED.value,
                                            ConsumptionEventType.READING_STARTED.value,
                                            ConsumptionEventType.LISTENING_STARTED.value,
                                        ],
                                    ]
                                },
                                1,
                                0,
                            ]
                        }
                    },
                }
            },
        ]

        cursor = db[self.COLLECTION_NAME].aggregate(books_pipeline)
        books_data = [doc async for doc in cursor]

        total_books_opened = len(books_data)
        total_books_completed = sum(1 for b in books_data if b.get("has_completed"))
        total_books_in_progress = total_books_opened - total_books_completed

        # Time by mode
        time_pipeline = [
            {"$match": match_stage},
            {
                "$group": {
                    "_id": "$consumption_mode",
                    "total_seconds": {"$sum": "$duration_seconds"},
                }
            },
        ]

        cursor = db[self.COLLECTION_NAME].aggregate(time_pipeline)
        time_data = {doc["_id"]: doc["total_seconds"] async for doc in cursor}

        reading_time = time_data.get(ConsumptionMode.MANUAL_READING.value, 0.0)
        listening_time = time_data.get(ConsumptionMode.AUDIO_PLAYBACK.value, 0.0)
        ai_time = time_data.get(ConsumptionMode.AI_VOICE_NARRATION.value, 0.0)

        # Last activity
        last_event = await db[self.COLLECTION_NAME].find_one(
            {"user_id": user_id},
            sort=[("timestamp", -1)],
        )

        return UserConsumptionStats(
            user_id=user_id,
            total_books_opened=total_books_opened,
            total_books_in_progress=total_books_in_progress,
            total_books_completed=total_books_completed,
            total_reading_time_seconds=reading_time,
            total_listening_time_seconds=listening_time,
            total_ai_narration_time_seconds=ai_time,
            mode_breakdown={
                "manual_reading": reading_time,
                "audio_playback": listening_time,
                "ai_voice_narration": ai_time,
            },
            last_activity_at=last_event.get("timestamp") if last_event else None,
            stats_period_start=(
                datetime.utcnow() - timedelta(days=period_days) if period_days else None
            ),
            stats_period_end=datetime.utcnow() if period_days else None,
        )

    async def get_book_stats(
        self,
        book_id: str,
        period_days: Optional[int] = None,
    ) -> BookConsumptionStats:
        """
        Get aggregated consumption stats for a book.

        Args:
            book_id: Book ID
            period_days: Optional period filter

        Returns:
            Book consumption statistics
        """
        db = get_db()

        # Build match stage
        match_stage: Dict[str, Any] = {"book_id": book_id}
        if period_days:
            cutoff = datetime.utcnow() - timedelta(days=period_days)
            match_stage["timestamp"] = {"$gte": cutoff}

        # Get book title from first event
        first_event = await db[self.COLLECTION_NAME].find_one(
            {"book_id": book_id},
            {"book_title": 1},
        )
        book_title = first_event.get("book_title") if first_event else None

        # Count unique users and sessions
        users_sessions_pipeline = [
            {"$match": match_stage},
            {
                "$group": {
                    "_id": None,
                    "unique_users": {"$addToSet": "$user_id"},
                    "unique_sessions": {"$addToSet": "$session_id"},
                    "total_time": {"$sum": "$duration_seconds"},
                }
            },
        ]

        cursor = db[self.COLLECTION_NAME].aggregate(users_sessions_pipeline)
        result = await cursor.to_list(length=1)

        if result:
            total_users = len(result[0].get("unique_users", []))
            total_sessions = len(result[0].get("unique_sessions", []))
            total_time = result[0].get("total_time", 0.0)
        else:
            total_users = 0
            total_sessions = 0
            total_time = 0.0

        # Count completions
        completions = await db[self.COLLECTION_NAME].count_documents(
            {
                **match_stage,
                "event_type": ConsumptionEventType.COMPLETED.value,
            }
        )

        completion_rate = (completions / total_users * 100) if total_users > 0 else 0.0
        avg_completion_time = (total_time / completions) if completions > 0 else 0.0

        # Mode breakdown
        mode_pipeline = [
            {"$match": match_stage},
            {
                "$group": {
                    "_id": {"session": "$session_id", "mode": "$consumption_mode"},
                }
            },
            {
                "$group": {
                    "_id": "$_id.mode",
                    "count": {"$sum": 1},
                }
            },
        ]

        cursor = db[self.COLLECTION_NAME].aggregate(mode_pipeline)
        mode_data = {doc["_id"]: doc["count"] async for doc in cursor}

        return BookConsumptionStats(
            book_id=book_id,
            book_title=book_title,
            total_users=total_users,
            total_sessions=total_sessions,
            total_completions=completions,
            completion_rate=completion_rate,
            average_completion_time_seconds=avg_completion_time,
            total_consumption_time_seconds=total_time,
            mode_breakdown=mode_data,
        )

    async def get_recent_activity(
        self,
        user_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[ConsumptionEventInDB]:
        """
        Get recent consumption events.

        Args:
            user_id: Optional user filter (for user dashboard)
            limit: Max events to return

        Returns:
            List of recent events
        """
        db = get_db()

        query: Dict[str, Any] = {}
        if user_id:
            query["user_id"] = user_id

        cursor = (
            db[self.COLLECTION_NAME]
            .find(query)
            .sort("timestamp", -1)
            .limit(limit)
        )

        events = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            events.append(ConsumptionEventInDB(**doc))

        return events

    async def get_admin_dashboard_stats(
        self,
        period_days: int = 7,
    ) -> Dict[str, Any]:
        """
        Get admin dashboard statistics.

        Args:
            period_days: Period for stats

        Returns:
            Dashboard statistics
        """
        db = get_db()
        cutoff = datetime.utcnow() - timedelta(days=period_days)

        # Overall stats
        stats_pipeline = [
            {"$match": {"timestamp": {"$gte": cutoff}}},
            {
                "$group": {
                    "_id": None,
                    "total_events": {"$sum": 1},
                    "unique_users": {"$addToSet": "$user_id"},
                    "unique_books": {"$addToSet": "$book_id"},
                    "unique_sessions": {"$addToSet": "$session_id"},
                    "total_duration": {"$sum": "$duration_seconds"},
                    "completions": {
                        "$sum": {
                            "$cond": [
                                {"$eq": ["$event_type", ConsumptionEventType.COMPLETED.value]},
                                1,
                                0,
                            ]
                        }
                    },
                }
            },
        ]

        cursor = db[self.COLLECTION_NAME].aggregate(stats_pipeline)
        result = await cursor.to_list(length=1)

        if result:
            data = result[0]
            return {
                "period_days": period_days,
                "total_events": data.get("total_events", 0),
                "unique_users": len(data.get("unique_users", [])),
                "unique_books": len(data.get("unique_books", [])),
                "total_sessions": len(data.get("unique_sessions", [])),
                "total_duration_hours": data.get("total_duration", 0) / 3600,
                "total_completions": data.get("completions", 0),
            }
        else:
            return {
                "period_days": period_days,
                "total_events": 0,
                "unique_users": 0,
                "unique_books": 0,
                "total_sessions": 0,
                "total_duration_hours": 0,
                "total_completions": 0,
            }

    async def check_session_exists(
        self,
        session_id: str,
    ) -> bool:
        """
        Check if a session has any events.

        Args:
            session_id: Session ID to check

        Returns:
            True if session exists
        """
        db = get_db()
        count = await db[self.COLLECTION_NAME].count_documents(
            {"session_id": session_id},
            limit=1,
        )
        return count > 0

    async def get_session_latest_progress(
        self,
        session_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get latest progress for a session.

        Used to resume tracking after page refresh.

        Args:
            session_id: Session ID

        Returns:
            Latest progress data or None
        """
        db = get_db()
        latest = await db[self.COLLECTION_NAME].find_one(
            {"session_id": session_id},
            sort=[("timestamp", -1)],
        )

        if latest:
            return {
                "chunk_index": latest.get("chunk_index", 0),
                "position_seconds": latest.get("position_seconds", 0.0),
                "cumulative_time_seconds": latest.get("cumulative_time_seconds", 0.0),
                "progress_percentage": latest.get("progress_percentage", 0.0),
                "consumption_mode": latest.get("consumption_mode"),
                "last_event_type": latest.get("event_type"),
                "timestamp": latest.get("timestamp"),
            }
        return None


# Singleton instance
consumption_service = ConsumptionService()
