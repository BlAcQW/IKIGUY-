"""
Database Backup Routes.

Provides API endpoints for database backup management.
Universal admin only.
"""

import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field

from apps.shared.backup import (
    DatabaseBackupService,
    DatabaseType,
    BackupType,
    BackupMetadata,
    DatabaseBackupError,
)
from ..auth import get_current_user_mongo
from apps.shared.services.organization_service import OrganizationService


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/backups", tags=["backups"])


# Pydantic Models for API

class BackupRequest(BaseModel):
    """Request model for creating a backup."""
    database_name: str = Field(..., description="Database name to backup")
    database_type: str = Field(..., description="Database type: mongodb or postgresql")
    organization_id: str = Field(..., description="Organization ID")
    backup_type: str = Field(default="manual", description="Backup type: daily, weekly, monthly, manual")


class RestoreRequest(BaseModel):
    """Request model for restoring a backup."""
    backup_path: str = Field(..., description="Remote backup path")
    target_database_name: Optional[str] = Field(None, description="Target database name (optional)")


class BackupResponse(BaseModel):
    """Response model for backup metadata."""
    database_name: str
    database_type: str
    backup_type: str
    organization_id: str
    timestamp: str
    file_size: int
    compressed_size: int
    backup_path: str
    status: str
    error: Optional[str] = None


class BackupStatsResponse(BaseModel):
    """Response model for backup statistics."""
    total_backups: int
    total_size_bytes: int
    total_size_mb: float
    by_type: dict
    by_database: dict
    latest_backup: Optional[BackupResponse] = None


# Dependency to check universal admin
def check_universal_admin(user: dict = Depends(get_current_user_mongo)):
    """Check if user is universal admin."""
    user_id = user.get("tenant_id") or user.get("account_id") or user.get("sub", "default-account")
    user_email = user.get("email", "")

    org_service = OrganizationService()
    if not org_service.is_universal_admin(user_id, user_email):
        raise HTTPException(
            status_code=403,
            detail="Only universal administrators can manage backups"
        )

    return user


# Initialize backup service
backup_service = DatabaseBackupService()


@router.post("/", response_model=BackupResponse)
async def create_backup(
    request: BackupRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(check_universal_admin)
):
    """
    Create a database backup.

    Universal admin only.

    Args:
        request: Backup request with database details
        background_tasks: FastAPI background tasks
        user: Current user (universal admin)

    Returns:
        Backup metadata

    Example:
        ```bash
        POST /backups/
        {
            "database_name": "kasaai_core",
            "database_type": "mongodb",
            "organization_id": "org_123",
            "backup_type": "manual"
        }
        ```
    """
    try:
        # Validate database type
        try:
            db_type = DatabaseType(request.database_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid database type. Must be: {', '.join([t.value for t in DatabaseType])}"
            )

        # Validate backup type
        try:
            bk_type = BackupType(request.backup_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid backup type. Must be: {', '.join([t.value for t in BackupType])}"
            )

        # Perform backup
        logger.info(f"Creating backup for {request.database_name} ({request.database_type})")

        metadata = await backup_service.backup_database(
            database_name=request.database_name,
            database_type=db_type,
            organization_id=request.organization_id,
            backup_type=bk_type
        )

        logger.info(f"Backup created successfully: {metadata.backup_path}")

        return BackupResponse(
            database_name=metadata.database_name,
            database_type=metadata.database_type.value,
            backup_type=metadata.backup_type.value,
            organization_id=metadata.organization_id,
            timestamp=metadata.timestamp.isoformat(),
            file_size=metadata.file_size,
            compressed_size=metadata.compressed_size,
            backup_path=metadata.backup_path,
            status=metadata.status,
            error=metadata.error
        )

    except DatabaseBackupError as e:
        logger.error(f"Backup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during backup: {e}")
        raise HTTPException(status_code=500, detail=f"Backup failed: {e}")


@router.get("/", response_model=List[BackupResponse])
async def list_backups(
    organization_id: Optional[str] = Query(None, description="Filter by organization ID"),
    database_name: Optional[str] = Query(None, description="Filter by database name"),
    database_type: Optional[str] = Query(None, description="Filter by database type"),
    backup_type: Optional[str] = Query(None, description="Filter by backup type"),
    user: dict = Depends(check_universal_admin)
):
    """
    List available backups.

    Universal admin only.

    Args:
        organization_id: Filter by organization ID
        database_name: Filter by database name
        database_type: Filter by database type (mongodb, postgresql)
        backup_type: Filter by backup type (daily, weekly, monthly, manual)
        user: Current user (universal admin)

    Returns:
        List of backup metadata

    Example:
        ```bash
        GET /backups/?organization_id=org_123&database_type=mongodb
        ```
    """
    try:
        # Validate filters
        db_type = None
        if database_type:
            try:
                db_type = DatabaseType(database_type.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid database type. Must be: {', '.join([t.value for t in DatabaseType])}"
                )

        bk_type = None
        if backup_type:
            try:
                bk_type = BackupType(backup_type.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid backup type. Must be: {', '.join([t.value for t in BackupType])}"
                )

        # List backups
        backups = await backup_service.list_backups(
            organization_id=organization_id,
            database_name=database_name,
            database_type=db_type,
            backup_type=bk_type
        )

        return [
            BackupResponse(
                database_name=b.database_name,
                database_type=b.database_type.value,
                backup_type=b.backup_type.value,
                organization_id=b.organization_id,
                timestamp=b.timestamp.isoformat(),
                file_size=b.file_size,
                compressed_size=b.compressed_size,
                backup_path=b.backup_path,
                status=b.status,
                error=b.error
            )
            for b in backups
        ]

    except DatabaseBackupError as e:
        logger.error(f"Failed to list backups: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error listing backups: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list backups: {e}")


@router.post("/restore", response_model=dict)
async def restore_backup(
    request: RestoreRequest,
    user: dict = Depends(check_universal_admin)
):
    """
    Restore database from backup.

    Universal admin only.

    CAUTION: This will drop all existing data in the target database!

    Args:
        request: Restore request with backup path
        user: Current user (universal admin)

    Returns:
        Success status

    Example:
        ```bash
        POST /backups/restore
        {
            "backup_path": "org_123/mongodb/kasaai_core/daily/backup_2025-10-26_12-00-00.tar.gz",
            "target_database_name": "kasaai_core_restored"
        }
        ```
    """
    try:
        logger.info(f"Restoring backup from {request.backup_path}")

        success = await backup_service.restore_database(
            backup_path=request.backup_path,
            target_database_name=request.target_database_name
        )

        if success:
            logger.info(f"Backup restored successfully from {request.backup_path}")
            return {
                "success": True,
                "message": "Database restored successfully",
                "backup_path": request.backup_path,
                "target_database": request.target_database_name
            }
        else:
            raise HTTPException(status_code=500, detail="Restore failed")

    except DatabaseBackupError as e:
        logger.error(f"Restore failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during restore: {e}")
        raise HTTPException(status_code=500, detail=f"Restore failed: {e}")


@router.delete("/cleanup", response_model=dict)
async def cleanup_old_backups(
    user: dict = Depends(check_universal_admin)
):
    """
    Clean up old backups based on retention policy.

    Universal admin only.

    Retention policy:
    - Daily backups: Keep last 7 days
    - Weekly backups: Keep last 4 weeks
    - Monthly backups: Keep last 12 months
    - Manual backups: Keep forever

    Args:
        user: Current user (universal admin)

    Returns:
        Success status

    Example:
        ```bash
        DELETE /backups/cleanup
        ```
    """
    try:
        logger.info("Starting backup cleanup")

        await backup_service.cleanup_old_backups()

        logger.info("Backup cleanup completed")

        return {
            "success": True,
            "message": "Backup cleanup completed successfully"
        }

    except DatabaseBackupError as e:
        logger.error(f"Cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during cleanup: {e}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {e}")


@router.get("/stats", response_model=BackupStatsResponse)
async def get_backup_stats(
    organization_id: Optional[str] = Query(None, description="Filter by organization ID"),
    user: dict = Depends(check_universal_admin)
):
    """
    Get backup statistics.

    Universal admin only.

    Args:
        organization_id: Filter by organization ID
        user: Current user (universal admin)

    Returns:
        Backup statistics

    Example:
        ```bash
        GET /backups/stats?organization_id=org_123
        ```
    """
    try:
        stats = await backup_service.get_backup_stats(organization_id=organization_id)

        latest_backup = None
        if stats.get("latest_backup"):
            lb = stats["latest_backup"]
            latest_backup = BackupResponse(
                database_name=lb["database_name"],
                database_type=lb["database_type"],
                backup_type=lb["backup_type"],
                organization_id=lb["organization_id"],
                timestamp=lb["timestamp"],
                file_size=lb["file_size"],
                compressed_size=lb["compressed_size"],
                backup_path=lb["backup_path"],
                status=lb["status"],
                error=lb.get("error")
            )

        return BackupStatsResponse(
            total_backups=stats["total_backups"],
            total_size_bytes=stats["total_size_bytes"],
            total_size_mb=stats["total_size_mb"],
            by_type=stats["by_type"],
            by_database=stats["by_database"],
            latest_backup=latest_backup
        )

    except DatabaseBackupError as e:
        logger.error(f"Failed to get backup stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting backup stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get backup stats: {e}")


@router.get("/databases", response_model=dict)
async def list_databases(
    user: dict = Depends(check_universal_admin)
):
    """
    List available databases for backup.

    Universal admin only.

    Args:
        user: Current user (universal admin)

    Returns:
        Dictionary with MongoDB and PostgreSQL databases

    Example:
        ```bash
        GET /backups/databases
        ```
    """
    try:
        import subprocess
        import os

        result = {
            "mongodb": [],
            "postgresql": []
        }

        # List MongoDB databases
        try:
            mongodb_uri = os.getenv("MONGODB_URL")
            if mongodb_uri:
                cmd = ["mongosh", mongodb_uri, "--quiet", "--eval", "db.adminCommand('listDatabases').databases.map(d => d.name).join('\\n')"]
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if proc.returncode == 0:
                    databases = [line.strip() for line in proc.stdout.strip().split('\n') if line.strip()]
                    # Filter out system databases
                    result["mongodb"] = [
                        db for db in databases
                        if db not in ["admin", "config", "local"]
                    ]
        except Exception as e:
            logger.warning(f"Failed to list MongoDB databases: {e}")

        # List PostgreSQL databases
        try:
            postgres_host = os.getenv("POSTGRES_SERVER", "localhost")
            postgres_user = os.getenv("POSTGRES_USER", "postgres")
            postgres_password = os.getenv("POSTGRES_PASSWORD")

            env = os.environ.copy()
            env["PGPASSWORD"] = postgres_password

            cmd = [
                "psql",
                "-h", postgres_host,
                "-U", postgres_user,
                "-t",  # Tuples only
                "-c", "SELECT datname FROM pg_database WHERE datistemplate = false AND datname NOT IN ('postgres');"
            ]

            proc = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=10)
            if proc.returncode == 0:
                databases = [line.strip() for line in proc.stdout.strip().split('\n') if line.strip()]
                result["postgresql"] = databases
        except Exception as e:
            logger.warning(f"Failed to list PostgreSQL databases: {e}")

        return result

    except Exception as e:
        logger.error(f"Failed to list databases: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list databases: {e}")
