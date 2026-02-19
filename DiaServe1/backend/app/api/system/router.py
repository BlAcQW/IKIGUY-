"""
System API Routes

Endpoints for system monitoring, health checks, and scheduler status.
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.services.reminder_worker import get_reminder_worker
from app.core.auth import get_current_user

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/scheduler/status")
async def get_scheduler_status(
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get scheduler and reminder system status.

    Requires authentication.

    Returns:
        Scheduler status and reminder statistics
    """
    reminder_worker = get_reminder_worker(database)

    # Get reminder stats
    stats = await reminder_worker.get_reminder_stats()

    # Get scheduler jobs info (if scheduler is available from app state)
    from app.main import scheduler as app_scheduler

    jobs = []
    if app_scheduler:
        jobs = app_scheduler.get_jobs()

    return {
        "scheduler": {
            "running": app_scheduler is not None,
            "jobs": jobs
        },
        "reminders": stats
    }


@router.post("/reminders/process")
async def trigger_reminder_processing(
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Manually trigger reminder processing cycle.

    Useful for testing and debugging.
    Requires authentication.

    Returns:
        Success status
    """
    reminder_worker = get_reminder_worker(database)

    # Process reminders
    await reminder_worker.process_pending_reminders()

    return {
        "success": True,
        "message": "Reminder processing cycle completed"
    }
