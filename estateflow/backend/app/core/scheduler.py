"""
Background Task Scheduler

Manages periodic background tasks using APScheduler.
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services.reminder_worker import get_reminder_worker

logger = logging.getLogger(__name__)


class BackgroundScheduler:
    """
    Manages background scheduled tasks for the application.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize the scheduler.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.scheduler = AsyncIOScheduler()
        self.reminder_worker = get_reminder_worker(db)

    def start(self):
        """
        Start the background scheduler and register all tasks.
        """
        logger.info("Starting background task scheduler...")

        try:
            # Task 1: Process pending reminders every minute
            self.scheduler.add_job(
                self.reminder_worker.process_pending_reminders,
                trigger=IntervalTrigger(minutes=1),
                id="process_reminders",
                name="Process Pending Reminders",
                replace_existing=True,
                max_instances=1  # Prevent overlapping executions
            )
            logger.info("✓ Registered task: Process Pending Reminders (every 1 minute)")

            # Task 2: Cleanup old failed reminders once per day at 3 AM
            self.scheduler.add_job(
                self.reminder_worker.cleanup_old_reminders,
                trigger=CronTrigger(hour=3, minute=0),
                id="cleanup_reminders",
                name="Cleanup Old Reminders",
                replace_existing=True,
                max_instances=1
            )
            logger.info("✓ Registered task: Cleanup Old Reminders (daily at 3 AM)")

            # Task 3: Log reminder statistics every hour
            self.scheduler.add_job(
                self._log_reminder_stats,
                trigger=IntervalTrigger(hours=1),
                id="log_reminder_stats",
                name="Log Reminder Statistics",
                replace_existing=True,
                max_instances=1
            )
            logger.info("✓ Registered task: Log Reminder Statistics (every 1 hour)")

            # Start the scheduler
            self.scheduler.start()
            logger.info("✓ Background scheduler started successfully")

        except Exception as e:
            logger.error(f"Failed to start background scheduler: {e}", exc_info=True)
            raise

    async def _log_reminder_stats(self):
        """
        Log reminder statistics for monitoring.
        """
        try:
            stats = await self.reminder_worker.get_reminder_stats()
            logger.info(
                f"Reminder Stats - Total: {stats.get('total', 0)}, "
                f"Pending: {stats.get('pending', 0)}, "
                f"Sent: {stats.get('sent', 0)}, "
                f"Failed: {stats.get('failed', 0)}, "
                f"Upcoming (next hour): {stats.get('upcoming_next_hour', 0)}"
            )
        except Exception as e:
            logger.error(f"Error logging reminder stats: {e}", exc_info=True)

    def shutdown(self):
        """
        Gracefully shut down the scheduler.
        """
        logger.info("Shutting down background scheduler...")
        try:
            self.scheduler.shutdown(wait=True)
            logger.info("✓ Background scheduler shut down successfully")
        except Exception as e:
            logger.error(f"Error shutting down scheduler: {e}", exc_info=True)

    def get_jobs(self):
        """
        Get list of all scheduled jobs.

        Returns:
            List of job information dictionaries
        """
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        return jobs


# Global scheduler instance
_scheduler_instance = None


def get_scheduler(db: AsyncIOMotorDatabase) -> BackgroundScheduler:
    """
    Get or create the global scheduler instance.

    Args:
        db: MongoDB database instance

    Returns:
        BackgroundScheduler instance
    """
    global _scheduler_instance

    if _scheduler_instance is None:
        _scheduler_instance = BackgroundScheduler(db)

    return _scheduler_instance
