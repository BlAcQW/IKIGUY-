"""
Cron Management Service

Provides centralized management for scheduled cron jobs using APScheduler.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.job import Job
import logging
from bson import ObjectId

from ..mongo import get_database

logger = logging.getLogger(__name__)


class CronManagementService:
    """Service for managing scheduled cron jobs."""

    def __init__(self, scheduler):
        """
        Initialize the cron management service.

        Args:
            scheduler: APScheduler BackgroundScheduler instance
        """
        self.scheduler = scheduler
        self.db = get_database()
        self.cron_collection = self.db["cron_jobs"]
        self.execution_logs_collection = self.db["cron_execution_logs"]

    async def list_all_jobs(
        self,
        status: Optional[str] = None,
        job_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all scheduled cron jobs.

        Args:
            status: Filter by status (active, paused, all)
            job_type: Filter by job type

        Returns:
            List of cron jobs with their details
        """
        try:
            # Get all jobs from scheduler
            scheduler_jobs = self.scheduler.get_jobs()

            # Get metadata from database
            db_jobs = {}
            cursor = self.cron_collection.find({})
            async for job_data in cursor:
                db_jobs[job_data["job_id"]] = job_data

            jobs_list = []
            for job in scheduler_jobs:
                job_id = str(job.id)

                # Get metadata from database
                job_metadata = db_jobs.get(job_id, {})

                # Determine trigger type
                trigger_type = "unknown"
                trigger_details = {}
                if isinstance(job.trigger, CronTrigger):
                    trigger_type = "cron"
                    trigger_details = {
                        "expression": str(job.trigger),
                        "fields": job.trigger.fields
                    }
                elif isinstance(job.trigger, IntervalTrigger):
                    trigger_type = "interval"
                    trigger_details = {
                        "interval": str(job.trigger.interval)
                    }
                elif isinstance(job.trigger, DateTrigger):
                    trigger_type = "date"
                    trigger_details = {
                        "run_date": job.trigger.run_date.isoformat()
                    }

                job_info = {
                    "id": job_id,
                    "name": job.name or job_metadata.get("name", job_id),
                    "description": job_metadata.get("description", ""),
                    "func_name": job.func.__name__ if job.func else "unknown",
                    "trigger_type": trigger_type,
                    "trigger_details": trigger_details,
                    "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                    "is_paused": job.next_run_time is None,
                    "job_type": job_metadata.get("job_type", "system"),
                    "created_at": job_metadata.get("created_at"),
                    "created_by": job_metadata.get("created_by"),
                    "metadata": job_metadata.get("metadata", {})
                }

                # Apply filters
                if status == "active" and job_info["is_paused"]:
                    continue
                if status == "paused" and not job_info["is_paused"]:
                    continue
                if job_type and job_info["job_type"] != job_type:
                    continue

                jobs_list.append(job_info)

            return jobs_list

        except Exception as e:
            logger.error(f"Error listing cron jobs: {e}")
            raise

    async def get_job_by_id(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get details of a specific cron job.

        Args:
            job_id: ID of the job

        Returns:
            Job details or None if not found
        """
        try:
            job = self.scheduler.get_job(job_id)
            if not job:
                return None

            # Get metadata from database
            job_metadata = await self.cron_collection.find_one({"job_id": job_id}) or {}

            # Get recent execution logs
            logs_cursor = self.execution_logs_collection.find(
                {"job_id": job_id}
            ).sort("executed_at", -1).limit(10)
            recent_logs = []
            async for log in logs_cursor:
                log["_id"] = str(log["_id"])
                recent_logs.append(log)

            return {
                "id": job_id,
                "name": job.name or job_metadata.get("name", job_id),
                "description": job_metadata.get("description", ""),
                "func_name": job.func.__name__ if job.func else "unknown",
                "trigger": str(job.trigger),
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "is_paused": job.next_run_time is None,
                "job_type": job_metadata.get("job_type", "system"),
                "created_at": job_metadata.get("created_at"),
                "created_by": job_metadata.get("created_by"),
                "metadata": job_metadata.get("metadata", {}),
                "recent_logs": recent_logs
            }

        except Exception as e:
            logger.error(f"Error getting job {job_id}: {e}")
            raise

    async def pause_job(self, job_id: str) -> Dict[str, Any]:
        """
        Pause a scheduled job.

        Args:
            job_id: ID of the job to pause

        Returns:
            Result of the operation
        """
        try:
            job = self.scheduler.get_job(job_id)
            if not job:
                return {"success": False, "error": f"Job {job_id} not found"}

            job.pause()

            # Update metadata
            await self.cron_collection.update_one(
                {"job_id": job_id},
                {
                    "$set": {
                        "paused_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )

            logger.info(f"Paused job: {job_id}")
            return {"success": True, "message": f"Job {job_id} paused successfully"}

        except Exception as e:
            logger.error(f"Error pausing job {job_id}: {e}")
            return {"success": False, "error": str(e)}

    async def resume_job(self, job_id: str) -> Dict[str, Any]:
        """
        Resume a paused job.

        Args:
            job_id: ID of the job to resume

        Returns:
            Result of the operation
        """
        try:
            job = self.scheduler.get_job(job_id)
            if not job:
                return {"success": False, "error": f"Job {job_id} not found"}

            job.resume()

            # Update metadata
            await self.cron_collection.update_one(
                {"job_id": job_id},
                {
                    "$set": {
                        "resumed_at": datetime.now(timezone.utc).isoformat()
                    },
                    "$unset": {
                        "paused_at": ""
                    }
                }
            )

            logger.info(f"Resumed job: {job_id}")
            return {"success": True, "message": f"Job {job_id} resumed successfully"}

        except Exception as e:
            logger.error(f"Error resuming job {job_id}: {e}")
            return {"success": False, "error": str(e)}

    async def remove_job(self, job_id: str) -> Dict[str, Any]:
        """
        Remove a scheduled job.

        Args:
            job_id: ID of the job to remove

        Returns:
            Result of the operation
        """
        try:
            job = self.scheduler.get_job(job_id)
            if not job:
                return {"success": False, "error": f"Job {job_id} not found"}

            self.scheduler.remove_job(job_id)

            # Remove from database (soft delete)
            await self.cron_collection.update_one(
                {"job_id": job_id},
                {
                    "$set": {
                        "deleted_at": datetime.now(timezone.utc).isoformat(),
                        "is_deleted": True
                    }
                }
            )

            logger.info(f"Removed job: {job_id}")
            return {"success": True, "message": f"Job {job_id} removed successfully"}

        except Exception as e:
            logger.error(f"Error removing job {job_id}: {e}")
            return {"success": False, "error": str(e)}

    async def get_execution_logs(
        self,
        job_id: Optional[str] = None,
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get execution logs for cron jobs.

        Args:
            job_id: Filter by specific job ID
            limit: Maximum number of logs to return
            status: Filter by execution status (success, error)

        Returns:
            List of execution logs
        """
        try:
            query = {}
            if job_id:
                query["job_id"] = job_id
            if status:
                query["status"] = status

            cursor = self.execution_logs_collection.find(query).sort("executed_at", -1).limit(limit)

            logs = []
            async for log in cursor:
                log["_id"] = str(log["_id"])
                logs.append(log)

            return logs

        except Exception as e:
            logger.error(f"Error getting execution logs: {e}")
            raise

    async def log_execution(
        self,
        job_id: str,
        job_name: str,
        status: str,
        duration_ms: float,
        error_message: Optional[str] = None,
        result: Optional[Any] = None
    ) -> None:
        """
        Log a cron job execution.

        Args:
            job_id: ID of the job
            job_name: Name of the job
            status: Execution status (success, error)
            duration_ms: Execution duration in milliseconds
            error_message: Error message if failed
            result: Execution result
        """
        try:
            log_entry = {
                "job_id": job_id,
                "job_name": job_name,
                "status": status,
                "duration_ms": duration_ms,
                "executed_at": datetime.now(timezone.utc).isoformat(),
                "error_message": error_message,
                "result": result
            }

            await self.execution_logs_collection.insert_one(log_entry)
            logger.info(f"Logged execution for job {job_id}: {status}")

        except Exception as e:
            logger.error(f"Error logging execution for job {job_id}: {e}")

    async def register_job_metadata(
        self,
        job_id: str,
        name: str,
        description: str,
        job_type: str = "custom",
        created_by: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Register metadata for a cron job in the database.

        Args:
            job_id: ID of the job
            name: Human-readable name
            description: Job description
            job_type: Type of job (system, custom, campaign, etc.)
            created_by: User ID who created the job
            metadata: Additional metadata

        Returns:
            Result of the operation
        """
        try:
            job_data = {
                "job_id": job_id,
                "name": name,
                "description": description,
                "job_type": job_type,
                "created_by": created_by,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "metadata": metadata or {},
                "is_deleted": False
            }

            await self.cron_collection.update_one(
                {"job_id": job_id},
                {"$set": job_data},
                upsert=True
            )

            logger.info(f"Registered metadata for job: {job_id}")
            return {"success": True, "job_id": job_id}

        except Exception as e:
            logger.error(f"Error registering job metadata: {e}")
            return {"success": False, "error": str(e)}


# Create a singleton instance (will be initialized with scheduler from main.py)
cron_management_service: Optional[CronManagementService] = None


def init_cron_management_service(scheduler):
    """Initialize the cron management service with the scheduler instance."""
    global cron_management_service
    cron_management_service = CronManagementService(scheduler)
    return cron_management_service
