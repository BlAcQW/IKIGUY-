"""
Demo Cron Jobs

Provides example/demo cron jobs for testing the cron management system.
These jobs demonstrate different trigger types and use cases.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


def demo_system_health_check():
    """
    Demo job: System health check.

    Simulates a system health monitoring task that runs every 5 minutes.
    """
    logger.info("🏥 Demo: Running system health check")
    # In a real implementation, this would check system metrics
    # For demo purposes, we just log
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {
            "database": "ok",
            "memory": "ok",
            "disk": "ok"
        }
    }


def demo_cleanup_temp_files():
    """
    Demo job: Cleanup temporary files.

    Simulates a cleanup task that runs daily at 2 AM.
    """
    logger.info("🧹 Demo: Cleaning up temporary files")
    # In a real implementation, this would delete old temp files
    return {
        "status": "completed",
        "files_cleaned": 0,  # Demo value
        "space_freed": "0 MB",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def demo_backup_database():
    """
    Demo job: Database backup.

    Simulates a database backup task that runs every 6 hours.
    """
    logger.info("💾 Demo: Running database backup")
    # In a real implementation, this would backup the database
    return {
        "status": "completed",
        "backup_size": "0 MB",  # Demo value
        "backup_location": "/backups/demo.sql",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def demo_send_daily_report():
    """
    Demo job: Send daily report.

    Simulates sending a daily report at 9 AM.
    """
    logger.info("📊 Demo: Sending daily report")
    # In a real implementation, this would generate and send a report
    return {
        "status": "sent",
        "recipients": ["admin@example.com"],
        "report_type": "daily_summary",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def demo_check_api_endpoints():
    """
    Demo job: Check API endpoints.

    Simulates checking if all API endpoints are responsive.
    """
    logger.info("🔍 Demo: Checking API endpoints")
    # In a real implementation, this would ping all endpoints
    return {
        "status": "completed",
        "endpoints_checked": 0,  # Demo value
        "all_healthy": True,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


async def initialize_demo_jobs(scheduler, cron_service):
    """
    Initialize demo cron jobs.

    Args:
        scheduler: APScheduler BackgroundScheduler instance
        cron_service: CronManagementService instance
    """
    logger.info("Initializing demo cron jobs...")

    demo_jobs = [
        {
            "id": "demo_health_check",
            "func": demo_system_health_check,
            "trigger": "cron",
            "trigger_args": {"minute": "*/5"},  # Every 5 minutes
            "name": "System Health Check (Demo)",
            "description": "Monitors system health metrics every 5 minutes",
            "job_type": "system"
        },
        {
            "id": "demo_cleanup",
            "func": demo_cleanup_temp_files,
            "trigger": "cron",
            "trigger_args": {"hour": 2, "minute": 0},  # Daily at 2 AM
            "name": "Cleanup Temporary Files (Demo)",
            "description": "Cleans up temporary files daily at 2 AM",
            "job_type": "system"
        },
        {
            "id": "demo_backup",
            "func": demo_backup_database,
            "trigger": "cron",
            "trigger_args": {"hour": "*/6"},  # Every 6 hours
            "name": "Database Backup (Demo)",
            "description": "Creates database backups every 6 hours",
            "job_type": "system"
        },
        {
            "id": "demo_daily_report",
            "func": demo_send_daily_report,
            "trigger": "cron",
            "trigger_args": {"hour": 9, "minute": 0},  # Daily at 9 AM
            "name": "Daily Report (Demo)",
            "description": "Sends daily summary report at 9 AM",
            "job_type": "custom"
        },
        {
            "id": "demo_api_check",
            "func": demo_check_api_endpoints,
            "trigger": "cron",
            "trigger_args": {"minute": "*/15"},  # Every 15 minutes
            "name": "API Endpoints Check (Demo)",
            "description": "Checks API endpoint health every 15 minutes",
            "job_type": "system"
        }
    ]

    for job_config in demo_jobs:
        try:
            # Check if job already exists
            existing_job = scheduler.get_job(job_config["id"])
            if existing_job:
                logger.info(f"Demo job already exists: {job_config['id']}")
                continue

            # Add job to scheduler
            scheduler.add_job(
                job_config["func"],
                job_config["trigger"],
                **job_config["trigger_args"],
                id=job_config["id"],
                name=job_config["name"],
                replace_existing=True
            )

            # Register metadata in database
            await cron_service.register_job_metadata(
                job_id=job_config["id"],
                name=job_config["name"],
                description=job_config["description"],
                job_type=job_config["job_type"],
                created_by="system",
                metadata={"demo": True}
            )

            logger.info(f"✅ Registered demo job: {job_config['name']}")

        except Exception as e:
            logger.error(f"Error registering demo job {job_config['id']}: {e}")

    logger.info("Demo cron jobs initialization completed")


async def cleanup_demo_jobs(scheduler):
    """
    Remove all demo cron jobs.

    Args:
        scheduler: APScheduler BackgroundScheduler instance
    """
    logger.info("Removing demo cron jobs...")

    demo_job_ids = [
        "demo_health_check",
        "demo_cleanup",
        "demo_backup",
        "demo_daily_report",
        "demo_api_check"
    ]

    for job_id in demo_job_ids:
        try:
            job = scheduler.get_job(job_id)
            if job:
                scheduler.remove_job(job_id)
                logger.info(f"✅ Removed demo job: {job_id}")
        except Exception as e:
            logger.error(f"Error removing demo job {job_id}: {e}")

    logger.info("Demo cron jobs cleanup completed")
