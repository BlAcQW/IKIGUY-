"""
Consumption Tracking API Routes.

Unified endpoints for tracking all book consumption activity:
- Book opened
- Reading/listening started
- Progress updates (WITH BILLING)
- Completion

Single source of truth for both admin and user dashboards.
BILLING: Progress updates now charge credits based on listening time.
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import get_current_user, get_current_admin_user
from app.core.config import settings
from app.models.consumption import (
    ConsumptionEventCreate,
    ConsumptionEventInDB,
    ConsumptionEventType,
    ConsumptionMode,
    ConsumptionSession,
    UserConsumptionStats,
    BookConsumptionStats,
    ProgressUpdateRequest,
    CompletionRequest,
)
from app.services.consumption_service import consumption_service
from app.services.wallet_service import wallet_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/consumption", tags=["consumption"])


# ============================================================================
# Event Recording Endpoints
# ============================================================================

@router.post("/events", status_code=status.HTTP_201_CREATED)
async def record_consumption_event(
    request: ConsumptionEventCreate,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Record a consumption event.

    Events: book_opened, reading_started, listening_started, paused, resumed, completed

    Args:
        request: Event data
        current_user: Authenticated user

    Returns:
        Created event with ID
    """
    try:
        event = await consumption_service.record_event(
            user_id=current_user.user_id,
            event_data=request,
        )

        logger.info(
            f"Consumption event recorded: user={current_user.user_id}, "
            f"book={request.book_id}, type={request.event_type.value}"
        )

        return {
            "message": "Event recorded successfully",
            "event_id": event.event_id,
            "event_type": event.event_type.value,
        }

    except Exception as e:
        logger.error(f"Failed to record consumption event: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record event: {str(e)}"
        )


@router.post("/progress", status_code=status.HTTP_201_CREATED)
async def update_progress(
    request: ProgressUpdateRequest,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Record a timer-based progress update WITH BILLING.

    Called periodically by frontend (every 30 seconds or on pause).
    NON-NEGOTIABLE: This endpoint tracks actual time spent AND charges credits.

    Billing: $0.10 per minute of listening/reading time.
    Every second counts - charges are calculated from duration_since_last_update.

    Args:
        request: Progress update data
        current_user: Authenticated user

    Returns:
        Updated progress confirmation with billing info
    """
    try:
        # 1. Record the progress event
        event = await consumption_service.record_progress_update(
            user_id=current_user.user_id,
            update=request,
        )

        # 2. BILLING: Charge for listening/reading time
        # Convert seconds to minutes for billing
        duration_minutes = request.duration_since_last_update / 60.0
        credits_charged = 0.0
        billing_success = False

        if duration_minutes > 0:
            try:
                transaction = await wallet_service.charge_listening_time(
                    user_id=current_user.user_id,
                    book_id=request.book_id,
                    duration_minutes=duration_minutes,
                    book_title=None,  # Could be added to request if needed
                )
                if transaction:
                    credits_charged = float(transaction.amount)
                    billing_success = True
                    logger.info(
                        f"Charged user {current_user.user_id}: ${credits_charged:.4f} "
                        f"for {duration_minutes:.2f} min on book {request.book_id}"
                    )
                else:
                    logger.warning(
                        f"Billing failed for user {current_user.user_id} - "
                        f"insufficient balance or wallet issue"
                    )
            except Exception as billing_error:
                # Log but don't fail the progress update - billing is secondary
                logger.error(f"Billing error (non-blocking): {billing_error}")

        return {
            "message": "Progress updated",
            "event_id": event.event_id,
            "progress_percentage": event.progress_percentage,
            "cumulative_time_seconds": event.cumulative_time_seconds,
            # Billing info for frontend display
            "billing": {
                "duration_seconds": request.duration_since_last_update,
                "duration_minutes": round(duration_minutes, 4),
                "credits_charged": round(credits_charged, 4),
                "billing_success": billing_success,
            },
        }

    except Exception as e:
        logger.error(f"Failed to update progress: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update progress: {str(e)}"
        )


@router.post("/complete", status_code=status.HTTP_201_CREATED)
async def record_completion(
    request: CompletionRequest,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Record deterministic book completion.

    NON-NEGOTIABLE: Completion is only recorded when user finishes the last chunk.
    This endpoint is called when:
    - Audio playback reaches the end of the final chunk
    - User explicitly marks book as complete after reaching 100%

    Args:
        request: Completion data with verification
        current_user: Authenticated user

    Returns:
        Completion confirmation
    """
    try:
        event = await consumption_service.record_completion(
            user_id=current_user.user_id,
            completion=request,
        )

        logger.info(
            f"Book completion recorded: user={current_user.user_id}, "
            f"book={request.book_id}, session={request.session_id}"
        )

        return {
            "message": "Book completed",
            "event_id": event.event_id,
            "total_time_seconds": request.total_time_seconds,
            "completed": True,
        }

    except Exception as e:
        logger.error(f"Failed to record completion: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record completion: {str(e)}"
        )


# ============================================================================
# Session Recovery Endpoints
# ============================================================================

@router.get("/sessions/{session_id}/latest")
async def get_session_latest_progress(
    session_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get latest progress for a session.

    Used to resume tracking after page refresh.
    Survives browser refreshes and reconnects.

    Args:
        session_id: Reading session ID
        current_user: Authenticated user

    Returns:
        Latest progress data or empty if no history
    """
    try:
        progress = await consumption_service.get_session_latest_progress(session_id)

        if progress:
            return {
                "found": True,
                **progress,
            }
        else:
            return {
                "found": False,
                "message": "No progress found for this session",
            }

    except Exception as e:
        logger.error(f"Failed to get session progress: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session progress: {str(e)}"
        )


# ============================================================================
# User Dashboard Endpoints
# ============================================================================

@router.get("/me/stats")
async def get_my_stats(
    period_days: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
) -> UserConsumptionStats:
    """
    Get my consumption statistics.

    Args:
        period_days: Optional filter (e.g., 7 for last week)
        current_user: Authenticated user

    Returns:
        User consumption statistics
    """
    try:
        stats = await consumption_service.get_user_stats(
            user_id=current_user.user_id,
            period_days=period_days,
        )
        return stats

    except Exception as e:
        logger.error(f"Failed to get user stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )


@router.get("/me/sessions")
async def get_my_sessions(
    book_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
) -> List[ConsumptionSession]:
    """
    Get my consumption sessions.

    Args:
        book_id: Optional book filter
        limit: Max sessions to return
        offset: Pagination offset
        current_user: Authenticated user

    Returns:
        List of consumption sessions
    """
    try:
        sessions = await consumption_service.get_user_sessions(
            user_id=current_user.user_id,
            book_id=book_id,
            limit=limit,
            offset=offset,
        )
        return sessions

    except Exception as e:
        logger.error(f"Failed to get user sessions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sessions: {str(e)}"
        )


@router.get("/me/recent")
async def get_my_recent_activity(
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
) -> List[ConsumptionEventInDB]:
    """
    Get my recent consumption events.

    Args:
        limit: Max events to return
        current_user: Authenticated user

    Returns:
        List of recent events
    """
    try:
        events = await consumption_service.get_recent_activity(
            user_id=current_user.user_id,
            limit=limit,
        )
        return events

    except Exception as e:
        logger.error(f"Failed to get recent activity: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get activity: {str(e)}"
        )


# ============================================================================
# Admin Dashboard Endpoints (same data source as user)
# ============================================================================

@router.get("/admin/dashboard")
async def get_admin_dashboard(
    period_days: int = 7,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get admin dashboard statistics.

    NON-NEGOTIABLE: This queries the same consumption_events collection
    as user dashboards. No separate data source.

    Args:
        period_days: Period for statistics
        current_user: Authenticated admin user

    Returns:
        Dashboard statistics
    """
    try:
        # Verify admin access
        await get_current_admin_user(current_user.user_id)

        stats = await consumption_service.get_admin_dashboard_stats(
            period_days=period_days,
        )
        return stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get admin dashboard: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard: {str(e)}"
        )


@router.get("/admin/users/{user_id}/stats")
async def get_user_stats_admin(
    user_id: str,
    period_days: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
) -> UserConsumptionStats:
    """
    Get consumption stats for any user (admin only).

    Same data source as user's own stats endpoint.

    Args:
        user_id: Target user ID
        period_days: Optional period filter
        current_user: Authenticated admin user

    Returns:
        User consumption statistics
    """
    try:
        # Verify admin access
        await get_current_admin_user(current_user.user_id)

        stats = await consumption_service.get_user_stats(
            user_id=user_id,
            period_days=period_days,
        )
        return stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user stats (admin): {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )


@router.get("/admin/books/{book_id}/stats")
async def get_book_stats_admin(
    book_id: str,
    period_days: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
) -> BookConsumptionStats:
    """
    Get consumption stats for a book (admin only).

    Args:
        book_id: Target book ID
        period_days: Optional period filter
        current_user: Authenticated admin user

    Returns:
        Book consumption statistics
    """
    try:
        # Verify admin access
        await get_current_admin_user(current_user.user_id)

        stats = await consumption_service.get_book_stats(
            book_id=book_id,
            period_days=period_days,
        )
        return stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get book stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )


@router.get("/admin/recent")
async def get_all_recent_activity(
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
) -> List[ConsumptionEventInDB]:
    """
    Get all recent consumption events (admin only).

    Args:
        limit: Max events to return
        current_user: Authenticated admin user

    Returns:
        List of recent events from all users
    """
    try:
        # Verify admin access
        await get_current_admin_user(current_user.user_id)

        events = await consumption_service.get_recent_activity(
            user_id=None,  # No user filter = all users
            limit=limit,
        )
        return events

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get all recent activity: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get activity: {str(e)}"
        )
