"""
Tracking API Routes.

Endpoints for error tracking, analytics events, and usage logging.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.database import Database
from app.core.auth import get_current_user
from app.models.analytics import (
    ErrorLog,
    ErrorLogInDB,
    ErrorType,
    AnalyticsEvent,
    AnalyticsEventInDB,
    EventType,
    UsageLog,
    UsageLogInDB,
    PlaybackMetrics,
    PlaybackMetricsInDB
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tracking", tags=["tracking"])


# Request Models
class ErrorLogRequest(BaseModel):
    """Request to log an error."""
    error_type: str
    error_message: str
    stack_trace: Optional[str] = None
    context: dict = Field(default_factory=dict)
    user_agent: Optional[str] = None
    browser: Optional[str] = None
    device_type: Optional[str] = None


class EventTrackRequest(BaseModel):
    """Request to track an analytics event."""
    event_type: str
    event_name: str
    properties: dict = Field(default_factory=dict)
    page_url: Optional[str] = None
    referrer: Optional[str] = None


class UsageLogRequest(BaseModel):
    """Request to log usage/cost."""
    service: str
    action: str
    cost_credits: int
    metadata: dict = Field(default_factory=dict)


class PlaybackMetricsRequest(BaseModel):
    """Request to log playback metrics."""
    session_id: str
    book_id: str
    chunk_index: int
    buffer_start_ms: int
    buffer_end_ms: Optional[int] = None
    buffer_duration_ms: Optional[int] = None
    stall_count: int = 0
    total_stall_duration_ms: int = 0
    audio_format: Optional[str] = None
    audio_bitrate: Optional[int] = None
    audio_size_bytes: Optional[int] = None
    download_time_ms: Optional[int] = None
    cache_hit: bool = False


# Endpoints

@router.post("/errors", status_code=status.HTTP_201_CREATED)
async def log_error(
    request: ErrorLogRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Log an error for tracking and debugging.

    Args:
        request: Error details
        current_user: Authenticated user (optional for some errors)

    Returns:
        Created error log
    """
    try:
        db = Database.get_database()

        # Validate error type
        try:
            error_type_enum = ErrorType(request.error_type)
        except ValueError:
            error_type_enum = ErrorType.UNKNOWN

        error_log = ErrorLog(
            user_id=current_user.user_id if current_user else None,
            error_type=error_type_enum,
            error_message=request.error_message,
            stack_trace=request.stack_trace,
            context=request.context,
            user_agent=request.user_agent,
            browser=request.browser,
            device_type=request.device_type
        )

        result = await db.errors.insert_one(error_log.model_dump())

        logger.warning(
            f"Error logged: {error_type_enum.value} - {request.error_message[:100]} "
            f"(User: {current_user.user_id if current_user else 'anonymous'})"
        )

        return {
            "message": "Error logged successfully",
            "error_id": error_log.error_id
        }

    except Exception as e:
        logger.error(f"Failed to log error: {e}", exc_info=True)
        # Don't fail the request if error logging fails
        return {
            "message": "Error logging failed (non-critical)",
            "error": str(e)
        }


@router.post("/events", status_code=status.HTTP_201_CREATED)
async def track_event(
    request: EventTrackRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Track an analytics event.

    Args:
        request: Event details
        current_user: Authenticated user (optional for some events)

    Returns:
        Confirmation
    """
    try:
        db = Database.get_database()

        # Validate event type
        try:
            event_type_enum = EventType(request.event_type)
        except ValueError:
            logger.warning(f"Unknown event type: {request.event_type}")
            # Still track it with the raw string
            event_type_enum = request.event_type

        # Add session_id from context if available
        session_id = request.properties.get('session_id')

        event = AnalyticsEvent(
            user_id=current_user.user_id if current_user else None,
            session_id=session_id,
            event_type=event_type_enum,
            event_name=request.event_name,
            properties=request.properties,
            page_url=request.page_url,
            referrer=request.referrer
        )

        await db.analytics_events.insert_one(event.model_dump())

        return {
            "message": "Event tracked successfully",
            "event_id": event.event_id
        }

    except Exception as e:
        logger.error(f"Failed to track event: {e}", exc_info=True)
        # Don't fail the request if event tracking fails
        return {
            "message": "Event tracking failed (non-critical)",
            "error": str(e)
        }


@router.post("/usage", status_code=status.HTTP_201_CREATED)
async def log_usage(
    request: UsageLogRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Log usage for cost tracking.

    Args:
        request: Usage details
        current_user: Authenticated user

    Returns:
        Confirmation
    """
    try:
        db = Database.get_database()

        session_id = request.metadata.get('session_id')

        usage_log = UsageLog(
            user_id=current_user.user_id,
            session_id=session_id,
            service=request.service,
            action=request.action,
            cost_credits=request.cost_credits,
            metadata=request.metadata
        )

        await db.usage_logs.insert_one(usage_log.model_dump())

        logger.info(
            f"Usage logged: {request.service}/{request.action} "
            f"- {request.cost_credits} credits (User: {current_user.user_id})"
        )

        return {
            "message": "Usage logged successfully",
            "log_id": usage_log.log_id
        }

    except Exception as e:
        logger.error(f"Failed to log usage: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to log usage: {str(e)}"
        )


@router.post("/playback-metrics", status_code=status.HTTP_201_CREATED)
async def log_playback_metrics(
    request: PlaybackMetricsRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Log audio playback quality metrics.

    Args:
        request: Playback metrics
        current_user: Authenticated user

    Returns:
        Confirmation
    """
    try:
        db = Database.get_database()

        metrics = PlaybackMetrics(
            user_id=current_user.user_id,
            session_id=request.session_id,
            book_id=request.book_id,
            chunk_index=request.chunk_index,
            buffer_start_ms=request.buffer_start_ms,
            buffer_end_ms=request.buffer_end_ms,
            buffer_duration_ms=request.buffer_duration_ms,
            stall_count=request.stall_count,
            total_stall_duration_ms=request.total_stall_duration_ms,
            audio_format=request.audio_format,
            audio_bitrate=request.audio_bitrate,
            audio_size_bytes=request.audio_size_bytes,
            download_time_ms=request.download_time_ms,
            cache_hit=request.cache_hit
        )

        await db.playback_metrics.insert_one(metrics.model_dump())

        return {
            "message": "Playback metrics logged successfully",
            "metrics_id": metrics.metrics_id
        }

    except Exception as e:
        logger.error(f"Failed to log playback metrics: {e}", exc_info=True)
        # Don't fail the request if metrics logging fails
        return {
            "message": "Metrics logging failed (non-critical)",
            "error": str(e)
        }


@router.get("/errors/recent", response_model=List[ErrorLogInDB])
async def get_recent_errors(
    limit: int = 100,
    error_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get recent errors (admin only).

    Args:
        limit: Maximum number of errors to return
        error_type: Filter by error type
        current_user: Authenticated admin user

    Returns:
        List of recent errors
    """
    try:
        from app.core.auth import get_current_admin_user

        # Check if user is admin
        await get_current_admin_user(current_user.user_id)

        db = Database.get_database()

        query = {}
        if error_type:
            query["error_type"] = error_type

        cursor = db.errors.find(query).sort("timestamp", -1).limit(limit)
        errors = await cursor.to_list(length=limit)

        return errors

    except Exception as e:
        logger.error(f"Failed to get errors: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve errors: {str(e)}"
        )


@router.get("/errors/stats")
async def get_error_stats(
    current_user: dict = Depends(get_current_user)
):
    """
    Get error statistics (admin only).

    Args:
        current_user: Authenticated admin user

    Returns:
        Error statistics
    """
    try:
        from app.core.auth import get_current_admin_user

        # Check if user is admin
        await get_current_admin_user(current_user.user_id)

        db = Database.get_database()

        # Get error counts by type
        pipeline = [
            {
                "$group": {
                    "_id": "$error_type",
                    "count": {"$sum": 1}
                }
            },
            {
                "$sort": {"count": -1}
            }
        ]

        cursor = db.errors.aggregate(pipeline)
        error_counts = await cursor.to_list(length=None)

        # Get total errors
        total_errors = sum(item["count"] for item in error_counts)

        # Get unresolved errors
        unresolved = await db.errors.count_documents({"resolved": False})

        return {
            "total_errors": total_errors,
            "unresolved_errors": unresolved,
            "errors_by_type": error_counts
        }

    except Exception as e:
        logger.error(f"Failed to get error stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve error stats: {str(e)}"
        )
