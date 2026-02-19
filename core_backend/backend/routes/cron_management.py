"""
Cron Management API Routes

Provides endpoints for managing scheduled cron jobs.
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import logging

from ..services.cron_management_service import cron_management_service
from ..auth import get_current_user_mongo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cron-management", tags=["cron-management"])


class JobMetadataRequest(BaseModel):
    name: str
    description: str
    job_type: str = "custom"
    metadata: Optional[Dict[str, Any]] = None


class CreateCronJobRequest(BaseModel):
    name: str
    description: str
    cron_expression: str  # e.g., "0 */6 * * *" (every 6 hours)
    job_type: str = "custom"
    webhook_url: Optional[str] = None  # URL to call when job runs
    script_path: Optional[str] = None  # Path to script to execute
    metadata: Optional[Dict[str, Any]] = None


@router.get("/jobs")
async def list_cron_jobs(
    status: Optional[str] = None,
    job_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    List all scheduled cron jobs.

    Query params:
        status: Filter by status (active, paused, all)
        job_type: Filter by job type (system, custom, campaign, etc.)
    """
    try:
        if not cron_management_service:
            raise HTTPException(
                status_code=500,
                detail="Cron management service not initialized"
            )

        jobs = await cron_management_service.list_all_jobs(
            status=status,
            job_type=job_type
        )

        return {
            "success": True,
            "jobs": jobs,
            "total": len(jobs)
        }

    except Exception as e:
        logger.error(f"Error listing cron jobs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list cron jobs: {str(e)}"
        )


@router.get("/jobs/{job_id}")
async def get_cron_job(
    job_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """Get details of a specific cron job."""
    try:
        if not cron_management_service:
            raise HTTPException(
                status_code=500,
                detail="Cron management service not initialized"
            )

        job = await cron_management_service.get_job_by_id(job_id)

        if not job:
            raise HTTPException(
                status_code=404,
                detail=f"Job {job_id} not found"
            )

        return {
            "success": True,
            "job": job
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cron job {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get cron job: {str(e)}"
        )


@router.post("/jobs/{job_id}/pause")
async def pause_cron_job(
    job_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """Pause a scheduled cron job."""
    try:
        if not cron_management_service:
            raise HTTPException(
                status_code=500,
                detail="Cron management service not initialized"
            )

        result = await cron_management_service.pause_job(job_id)

        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Failed to pause job")
            )

        return {
            "success": True,
            "message": result["message"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing cron job {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to pause cron job: {str(e)}"
        )


@router.post("/jobs/{job_id}/resume")
async def resume_cron_job(
    job_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """Resume a paused cron job."""
    try:
        if not cron_management_service:
            raise HTTPException(
                status_code=500,
                detail="Cron management service not initialized"
            )

        result = await cron_management_service.resume_job(job_id)

        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Failed to resume job")
            )

        return {
            "success": True,
            "message": result["message"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming cron job {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to resume cron job: {str(e)}"
        )


@router.delete("/jobs/{job_id}")
async def delete_cron_job(
    job_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """Delete/remove a scheduled cron job."""
    try:
        if not cron_management_service:
            raise HTTPException(
                status_code=500,
                detail="Cron management service not initialized"
            )

        result = await cron_management_service.remove_job(job_id)

        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Failed to delete job")
            )

        return {
            "success": True,
            "message": result["message"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting cron job {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete cron job: {str(e)}"
        )


@router.get("/logs")
async def get_execution_logs(
    job_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get execution logs for cron jobs.

    Query params:
        job_id: Filter by specific job ID
        status: Filter by execution status (success, error)
        limit: Maximum number of logs to return (default 100)
    """
    try:
        if not cron_management_service:
            raise HTTPException(
                status_code=500,
                detail="Cron management service not initialized"
            )

        logs = await cron_management_service.get_execution_logs(
            job_id=job_id,
            status=status,
            limit=limit
        )

        return {
            "success": True,
            "logs": logs,
            "total": len(logs)
        }

    except Exception as e:
        logger.error(f"Error getting execution logs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get execution logs: {str(e)}"
        )


@router.post("/jobs/{job_id}/metadata")
async def register_job_metadata(
    job_id: str,
    request: JobMetadataRequest,
    current_user: dict = Depends(get_current_user_mongo)
):
    """Register or update metadata for a cron job."""
    try:
        if not cron_management_service:
            raise HTTPException(
                status_code=500,
                detail="Cron management service not initialized"
            )

        result = await cron_management_service.register_job_metadata(
            job_id=job_id,
            name=request.name,
            description=request.description,
            job_type=request.job_type,
            created_by=current_user.get("user_id"),
            metadata=request.metadata
        )

        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Failed to register metadata")
            )

        return {
            "success": True,
            "job_id": result["job_id"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering job metadata: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to register job metadata: {str(e)}"
        )


@router.get("/stats")
async def get_cron_stats(
    current_user: dict = Depends(get_current_user_mongo)
):
    """Get statistics about cron jobs."""
    try:
        if not cron_management_service:
            raise HTTPException(
                status_code=500,
                detail="Cron management service not initialized"
            )

        # Get all jobs
        all_jobs = await cron_management_service.list_all_jobs()

        # Calculate stats
        total_jobs = len(all_jobs)
        active_jobs = sum(1 for job in all_jobs if not job["is_paused"])
        paused_jobs = sum(1 for job in all_jobs if job["is_paused"])

        # Group by type
        jobs_by_type = {}
        for job in all_jobs:
            job_type = job["job_type"]
            jobs_by_type[job_type] = jobs_by_type.get(job_type, 0) + 1

        # Get recent logs
        recent_logs = await cron_management_service.get_execution_logs(limit=10)

        # Calculate success rate from recent logs
        if recent_logs:
            success_count = sum(1 for log in recent_logs if log["status"] == "success")
            success_rate = (success_count / len(recent_logs)) * 100
        else:
            success_rate = 0

        return {
            "success": True,
            "stats": {
                "total_jobs": total_jobs,
                "active_jobs": active_jobs,
                "paused_jobs": paused_jobs,
                "jobs_by_type": jobs_by_type,
                "recent_success_rate": round(success_rate, 2),
                "recent_executions": len(recent_logs)
            }
        }

    except Exception as e:
        logger.error(f"Error getting cron stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get cron stats: {str(e)}"
        )


@router.post("/demo/initialize")
async def initialize_demo_jobs_endpoint(
    current_user: dict = Depends(get_current_user_mongo)
):
    """Initialize demo cron jobs for testing."""
    try:
        if not cron_management_service:
            raise HTTPException(
                status_code=500,
                detail="Cron management service not initialized"
            )

        # Import scheduler from main
        from ..main import scheduler
        from ..services.demo_cron_jobs import initialize_demo_jobs

        await initialize_demo_jobs(scheduler, cron_management_service)

        return {
            "success": True,
            "message": "Demo cron jobs initialized successfully"
        }

    except Exception as e:
        logger.error(f"Error initializing demo jobs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize demo jobs: {str(e)}"
        )


@router.post("/demo/cleanup")
async def cleanup_demo_jobs_endpoint(
    current_user: dict = Depends(get_current_user_mongo)
):
    """Remove all demo cron jobs."""
    try:
        # Import scheduler from main
        from ..main import scheduler
        from ..services.demo_cron_jobs import cleanup_demo_jobs

        await cleanup_demo_jobs(scheduler)

        return {
            "success": True,
            "message": "Demo cron jobs removed successfully"
        }

    except Exception as e:
        logger.error(f"Error cleaning up demo jobs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cleanup demo jobs: {str(e)}"
        )


@router.post("/jobs/create")
async def create_custom_cron_job(
    job_request: CreateCronJobRequest,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Create a custom cron job.

    The job can either call a webhook URL or execute a script.
    """
    try:
        if not cron_management_service:
            raise HTTPException(
                status_code=500,
                detail="Cron management service not initialized"
            )

        # Validate that either webhook_url or script_path is provided
        if not job_request.webhook_url and not job_request.script_path:
            raise HTTPException(
                status_code=400,
                detail="Either webhook_url or script_path must be provided"
            )

        # Parse cron expression (validate format)
        from apscheduler.triggers.cron import CronTrigger
        try:
            # Parse the cron expression to validate it
            parts = job_request.cron_expression.strip().split()
            if len(parts) == 5:
                # Standard cron: minute hour day month day_of_week
                trigger = CronTrigger(
                    minute=parts[0],
                    hour=parts[1],
                    day=parts[2],
                    month=parts[3],
                    day_of_week=parts[4]
                )
            elif len(parts) == 6:
                # With seconds: second minute hour day month day_of_week
                trigger = CronTrigger(
                    second=parts[0],
                    minute=parts[1],
                    hour=parts[2],
                    day=parts[3],
                    month=parts[4],
                    day_of_week=parts[5]
                )
            else:
                raise ValueError("Cron expression must have 5 or 6 fields")
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid cron expression: {str(e)}"
            )

        # Create job function
        import subprocess
        import requests
        from uuid import uuid4

        job_id = f"custom_{uuid4().hex[:12]}"

        def custom_job_executor():
            """Execute the custom job."""
            logger.info(f"🔄 Executing custom job: {job_request.name}")

            result = {}

            try:
                if job_request.webhook_url:
                    # Call webhook
                    logger.info(f"Calling webhook: {job_request.webhook_url}")
                    response = requests.post(
                        job_request.webhook_url,
                        json={
                            "job_id": job_id,
                            "job_name": job_request.name,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        },
                        timeout=30
                    )
                    response.raise_for_status()
                    result = {
                        "status": "success",
                        "webhook_status": response.status_code,
                        "response": response.text[:500]  # Limit response size
                    }

                elif job_request.script_path:
                    # Execute script
                    logger.info(f"Executing script: {job_request.script_path}")
                    proc = subprocess.run(
                        [job_request.script_path],
                        capture_output=True,
                        text=True,
                        timeout=300  # 5 minute timeout
                    )
                    result = {
                        "status": "success" if proc.returncode == 0 else "error",
                        "exit_code": proc.returncode,
                        "stdout": proc.stdout[:500],  # Limit output size
                        "stderr": proc.stderr[:500]
                    }

                logger.info(f"✅ Custom job completed: {job_request.name}")
                return result

            except Exception as e:
                logger.error(f"❌ Custom job failed: {job_request.name} - {str(e)}")
                return {
                    "status": "error",
                    "error": str(e)
                }

        # Add job to scheduler
        from ..main import scheduler

        scheduler.add_job(
            custom_job_executor,
            trigger,
            id=job_id,
            name=job_request.name,
            replace_existing=False
        )

        # Register metadata
        await cron_management_service.register_job_metadata(
            job_id=job_id,
            name=job_request.name,
            description=job_request.description,
            job_type=job_request.job_type,
            created_by=current_user.get("user_id", "unknown"),
            metadata={
                **(job_request.metadata or {}),
                "cron_expression": job_request.cron_expression,
                "webhook_url": job_request.webhook_url,
                "script_path": job_request.script_path
            }
        )

        logger.info(f"✅ Created custom cron job: {job_id} - {job_request.name}")

        return {
            "success": True,
            "job_id": job_id,
            "message": f"Custom cron job '{job_request.name}' created successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating custom cron job: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create custom cron job: {str(e)}"
        )
