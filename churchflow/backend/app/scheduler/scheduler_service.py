"""
Scheduler Service.

Background task scheduling using APScheduler with MongoDB persistence.
Handles scheduling and processing of automated communications.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from bson import ObjectId
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from pymongo import MongoClient

from app.core.database import get_database
from app.models.scheduled_communication import ScheduledCommunication
from app.core.config import settings

logger = logging.getLogger(__name__)


# Standalone function for recurring job (to avoid serialization issues)
async def process_pending_communications_job():
    """
    Process pending scheduled communications.

    Recurring job that runs every 5 minutes to find and process
    communications that are due to be sent.

    This serves as a backup to the individual scheduled jobs,
    ensuring no communications are missed.
    """
    db = get_database()
    logger.info("Processing pending scheduled communications")

    try:
        # Find communications due to be sent
        now = datetime.utcnow()

        # Query for pending communications or retries
        query = {
            "$or": [
                {
                    "status": "pending",
                    "scheduled_for": {"$lte": now}
                },
                {
                    "status": "pending",
                    "retry_count": {"$gt": 0},
                    "next_retry_at": {"$lte": now}
                }
            ]
        }

        cursor = db.scheduled_communications.find(query).limit(100)

        processed_count = 0
        async for comm_doc in cursor:
            try:
                # Process each communication
                from app.services.communication_orchestration_service import communication_orchestration_service
                scheduled_comm = ScheduledCommunication(**comm_doc)

                result = await communication_orchestration_service.send_scheduled_communication(
                    scheduled_comm=scheduled_comm
                )

                # Update status
                if result.get("status") == "success":
                    await db.scheduled_communications.update_one(
                        {"_id": comm_doc["_id"]},
                        {
                            "$set": {
                                "status": "sent",
                                "sent_at": datetime.utcnow(),
                                "campaign_ids": result.get("campaign_ids", {})
                            }
                        }
                    )

                processed_count += 1
            except Exception as e:
                logger.error(f"Error processing communication {comm_doc['_id']}: {e}")
                continue

        if processed_count > 0:
            logger.info(f"Processed {processed_count} pending communications")

    except Exception as e:
        logger.error(f"Error in process_pending_communications_job: {e}")


class SchedulerService:
    """
    Service for background task scheduling.

    Uses APScheduler with MongoDB job store for persistence across restarts.
    Handles scheduling and processing of automated communications.

    Features:
    - Persistent job storage in MongoDB
    - Automatic recovery after server restart
    - Scheduled communications processing
    - Retry logic for failed communications
    """

    def __init__(self, mongo_client=None):
        """
        Initialize the scheduler service.

        Args:
            mongo_client: MongoDB client for job store (optional, will use default if not provided)
        """
        self.scheduler = None
        self.mongo_client = mongo_client
        self.sync_mongo_client = None  # Separate synchronous client for APScheduler
        self.db = None
        self._initialized = False

    async def initialize(self):
        """
        Initialize APScheduler with MongoDB job store.

        Sets up the scheduler with:
        - MongoDB job store for persistence (synchronous pymongo client)
        - Async executor for non-blocking jobs
        - Configured timezone and job defaults
        """
        if self._initialized:
            logger.warning("Scheduler already initialized")
            return

        try:
            # Get async database for job execution
            if not self.db:
                self.db = get_database()

            # Create separate synchronous MongoDB client for APScheduler's job store
            # APScheduler's MongoDBJobStore requires pymongo (synchronous), not Motor (async)
            if not self.sync_mongo_client:
                mongo_uri = settings.mongodb_url
                self.sync_mongo_client = MongoClient(mongo_uri)
                logger.info("Created synchronous MongoDB client for APScheduler")

            # Configure job stores with synchronous client
            jobstores = {
                'default': MongoDBJobStore(
                    database='churchflow',
                    collection='apscheduler_jobs',
                    client=self.sync_mongo_client
                )
            }

            # Configure executors
            executors = {
                'default': AsyncIOExecutor()
            }

            # Job defaults
            job_defaults = {
                'coalesce': True,  # Combine multiple missed executions into one
                'max_instances': 3,  # Max concurrent instances of a job
                'misfire_grace_time': 300  # 5 minutes grace period for missed jobs
            }

            # Create scheduler
            self.scheduler = AsyncIOScheduler(
                jobstores=jobstores,
                executors=executors,
                job_defaults=job_defaults,
                timezone='UTC'
            )

            # Add recurring job to process pending communications
            self.scheduler.add_job(
                func=process_pending_communications_job,
                trigger=IntervalTrigger(minutes=5),
                id='process_scheduled_comms',
                name='Process Pending Scheduled Communications',
                replace_existing=True
            )

            logger.info("Scheduler initialized successfully")
            self._initialized = True

        except Exception as e:
            logger.error(f"Failed to initialize scheduler: {e}")
            raise

    async def start(self):
        """
        Start the scheduler.

        Begins processing scheduled jobs. Should be called during
        application startup.
        """
        if not self._initialized:
            await self.initialize()

        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")
        else:
            logger.warning("Scheduler already running")

    async def shutdown(self):
        """
        Shutdown the scheduler gracefully.

        Waits for all running jobs to complete before shutting down.
        Should be called during application shutdown.
        """
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("Scheduler shut down")
        else:
            logger.warning("Scheduler not running")

        # Close synchronous MongoDB client
        if self.sync_mongo_client:
            self.sync_mongo_client.close()
            logger.info("Closed synchronous MongoDB client")
            self.sync_mongo_client = None

    async def schedule_communication(
        self,
        scheduled_comm_id: str,
        scheduled_for: datetime
    ):
        """
        Schedule a communication to be sent at a specific time.

        Creates a scheduled job that will process the communication
        at the specified datetime.

        Args:
            scheduled_comm_id: ID of scheduled_communication document
            scheduled_for: When to send the communication

        Returns:
            str: Job ID
        """
        if not self.scheduler:
            raise RuntimeError("Scheduler not initialized")

        logger.info(f"Scheduling communication {scheduled_comm_id} for {scheduled_for}")

        # Create job ID
        job_id = f"comm_{scheduled_comm_id}"

        # Schedule job
        job = self.scheduler.add_job(
            func=self._send_scheduled_communication,
            trigger=DateTrigger(run_date=scheduled_for),
            args=[scheduled_comm_id],
            id=job_id,
            name=f"Send Communication {scheduled_comm_id}",
            replace_existing=True
        )

        logger.info(f"Scheduled job {job.id} for {scheduled_for}")

        return job.id

    async def cancel_scheduled_communication(self, scheduled_comm_id: str):
        """
        Cancel a scheduled communication.

        Removes the scheduled job if it hasn't been executed yet.

        Args:
            scheduled_comm_id: ID of scheduled_communication document

        Returns:
            bool: True if cancelled, False if job not found
        """
        if not self.scheduler:
            raise RuntimeError("Scheduler not initialized")

        job_id = f"comm_{scheduled_comm_id}"

        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Cancelled scheduled communication {scheduled_comm_id}")
            return True
        except Exception as e:
            logger.warning(f"Failed to cancel job {job_id}: {e}")
            return False

    async def reschedule_communication(
        self,
        scheduled_comm_id: str,
        new_scheduled_for: datetime
    ):
        """
        Reschedule a communication to a different time.

        Args:
            scheduled_comm_id: ID of scheduled_communication document
            new_scheduled_for: New datetime to send the communication

        Returns:
            str: Job ID
        """
        # Cancel existing job
        await self.cancel_scheduled_communication(scheduled_comm_id)

        # Schedule new job
        return await self.schedule_communication(scheduled_comm_id, new_scheduled_for)

    async def _send_scheduled_communication(self, scheduled_comm_id: str):
        """
        Send a scheduled communication.

        Background job that sends a communication via the appropriate channels
        (SMS, WhatsApp, Voice) based on the scheduled_communication configuration.

        Args:
            scheduled_comm_id: ID of scheduled_communication document
        """
        if not self.db:
            self.db = get_database()

        logger.info(f"Processing scheduled communication {scheduled_comm_id}")

        try:
            # Fetch scheduled communication
            comm_doc = await self.db.scheduled_communications.find_one({
                "_id": ObjectId(scheduled_comm_id)
            })

            if not comm_doc:
                logger.error(f"Scheduled communication {scheduled_comm_id} not found")
                return

            # Check if already sent
            if comm_doc.get("status") == "sent":
                logger.info(f"Communication {scheduled_comm_id} already sent")
                return

            # Check if cancelled
            if comm_doc.get("status") == "cancelled":
                logger.info(f"Communication {scheduled_comm_id} was cancelled")
                return

            scheduled_comm = ScheduledCommunication(**comm_doc)

            # Import CommunicationOrchestrationService here to avoid circular imports
            from app.services.communication_orchestration_service import communication_orchestration_service

            # Send via communication orchestration service
            result = await communication_orchestration_service.send_scheduled_communication(
                scheduled_comm=scheduled_comm
            )

            # Update status based on result
            if result.get("status") == "success":
                await self.db.scheduled_communications.update_one(
                    {"_id": ObjectId(scheduled_comm_id)},
                    {
                        "$set": {
                            "status": "sent",
                            "sent_at": datetime.utcnow(),
                            "campaign_ids": result.get("campaign_ids", {})
                        }
                    }
                )
                logger.info(f"Successfully sent communication {scheduled_comm_id}")
            else:
                # Failed - check if we should retry
                await self._handle_failed_communication(scheduled_comm_id, result.get("error"))

        except Exception as e:
            logger.error(f"Error sending scheduled communication {scheduled_comm_id}: {e}")
            await self._handle_failed_communication(scheduled_comm_id, str(e))

    async def _handle_failed_communication(self, scheduled_comm_id: str, error_message: str):
        """
        Handle failed communication with retry logic.

        Args:
            scheduled_comm_id: ID of scheduled_communication document
            error_message: Error description
        """
        if not self.db:
            self.db = get_database()

        logger.info(f"Handling failed communication {scheduled_comm_id}")

        # Fetch communication
        comm_doc = await self.db.scheduled_communications.find_one({
            "_id": ObjectId(scheduled_comm_id)
        })

        if not comm_doc:
            return

        retry_count = comm_doc.get("retry_count", 0)
        max_retries = comm_doc.get("max_retries", 3)

        if retry_count < max_retries:
            # Schedule retry
            retry_count += 1
            next_retry_at = datetime.utcnow() + timedelta(minutes=15 * retry_count)  # Exponential backoff

            await self.db.scheduled_communications.update_one(
                {"_id": ObjectId(scheduled_comm_id)},
                {
                    "$set": {
                        "retry_count": retry_count,
                        "next_retry_at": next_retry_at,
                        "error_message": error_message
                    }
                }
            )

            # Schedule retry job
            await self.schedule_communication(scheduled_comm_id, next_retry_at)

            logger.info(f"Scheduled retry {retry_count}/{max_retries} for {next_retry_at}")
        else:
            # Max retries reached - mark as failed
            await self.db.scheduled_communications.update_one(
                {"_id": ObjectId(scheduled_comm_id)},
                {
                    "$set": {
                        "status": "failed",
                        "error_message": error_message
                    }
                }
            )

            logger.error(f"Communication {scheduled_comm_id} failed after {max_retries} retries")

    async def _process_pending_communications(self):
        """
        Process pending scheduled communications.

        Recurring job that runs every 5 minutes to find and process
        communications that are due to be sent.

        This serves as a backup to the individual scheduled jobs,
        ensuring no communications are missed.
        """
        if not self.db:
            self.db = get_database()

        logger.info("Processing pending scheduled communications")

        try:
            # Find communications due to be sent
            now = datetime.utcnow()

            # Query for pending communications or retries
            query = {
                "$or": [
                    {
                        "status": "pending",
                        "scheduled_for": {"$lte": now}
                    },
                    {
                        "status": "pending",
                        "retry_count": {"$gt": 0},
                        "next_retry_at": {"$lte": now}
                    }
                ]
            }

            cursor = self.db.scheduled_communications.find(query).limit(100)

            processed_count = 0
            async for comm_doc in cursor:
                try:
                    await self._send_scheduled_communication(str(comm_doc["_id"]))
                    processed_count += 1
                except Exception as e:
                    logger.error(f"Error processing communication {comm_doc['_id']}: {e}")
                    continue

            if processed_count > 0:
                logger.info(f"Processed {processed_count} pending communications")

        except Exception as e:
            logger.error(f"Error in _process_pending_communications: {e}")

    def get_scheduled_jobs_count(self) -> int:
        """
        Get count of scheduled jobs.

        Returns:
            int: Number of jobs in the scheduler
        """
        if not self.scheduler:
            return 0

        return len(self.scheduler.get_jobs())

    def get_job_status(self, job_id: str) -> Optional[dict]:
        """
        Get status of a specific job.

        Args:
            job_id: Job ID

        Returns:
            dict: Job details or None if not found
        """
        if not self.scheduler:
            return None

        job = self.scheduler.get_job(job_id)

        if not job:
            return None

        return {
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger)
        }


# Global instance
scheduler_service = SchedulerService()
