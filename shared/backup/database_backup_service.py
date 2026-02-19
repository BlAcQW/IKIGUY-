"""
Database Backup Service.

Provides centralized database backup functionality for all KasaAI applications.
Supports MongoDB and PostgreSQL with automatic backup to Hetzner Storage Box.

Features:
- MongoDB backup using mongodump
- PostgreSQL backup using pg_dump
- Automatic compression (gzip)
- Upload to Hetzner Storage Box
- Organization-scoped backups
- Retention policy management (daily, weekly, monthly)
- Manual and automated backup support
- Metadata tracking

Retention Policy:
- Daily backups: Keep last 7 days
- Weekly backups: Keep last 4 weeks
- Monthly backups: Keep last 12 months

Storage Structure:
/backups/{organization_id}/{database_type}/{database_name}/{backup_type}/
  - backup_YYYY-MM-DD_HH-MM-SS.tar.gz
  - backup_YYYY-MM-DD_HH-MM-SS.metadata.json
"""

import os
import logging
import subprocess
import tempfile
import shutil
import json
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime, timedelta
from enum import Enum
import asyncio

from apps.shared.storage.hetzner_storage_box import HetznerStorageBox, HetznerStorageBoxError


logger = logging.getLogger(__name__)


class DatabaseType(Enum):
    """Supported database types."""
    MONGODB = "mongodb"
    POSTGRESQL = "postgresql"


class BackupType(Enum):
    """Backup frequency types."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    MANUAL = "manual"


class BackupMetadata:
    """Backup metadata."""
    def __init__(
        self,
        database_name: str,
        database_type: DatabaseType,
        backup_type: BackupType,
        organization_id: str,
        timestamp: datetime,
        file_size: int,
        compressed_size: int,
        backup_path: str,
        status: str = "completed",
        error: Optional[str] = None
    ):
        self.database_name = database_name
        self.database_type = database_type
        self.backup_type = backup_type
        self.organization_id = organization_id
        self.timestamp = timestamp
        self.file_size = file_size
        self.compressed_size = compressed_size
        self.backup_path = backup_path
        self.status = status
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "database_name": self.database_name,
            "database_type": self.database_type.value,
            "backup_type": self.backup_type.value,
            "organization_id": self.organization_id,
            "timestamp": self.timestamp.isoformat(),
            "file_size": self.file_size,
            "compressed_size": self.compressed_size,
            "backup_path": self.backup_path,
            "status": self.status,
            "error": self.error
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BackupMetadata":
        """Create from dictionary."""
        return cls(
            database_name=data["database_name"],
            database_type=DatabaseType(data["database_type"]),
            backup_type=BackupType(data["backup_type"]),
            organization_id=data["organization_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            file_size=data["file_size"],
            compressed_size=data["compressed_size"],
            backup_path=data["backup_path"],
            status=data.get("status", "completed"),
            error=data.get("error")
        )


class DatabaseBackupError(Exception):
    """Base exception for database backup errors."""
    pass


class DatabaseBackupService:
    """
    Centralized database backup service for all KasaAI applications.

    Example:
        ```python
        backup_service = DatabaseBackupService()

        # Backup MongoDB database
        metadata = await backup_service.backup_database(
            database_name="kasaai_core",
            database_type=DatabaseType.MONGODB,
            organization_id="org_123",
            backup_type=BackupType.DAILY
        )

        # Backup PostgreSQL database
        metadata = await backup_service.backup_database(
            database_name="kasaai_core",
            database_type=DatabaseType.POSTGRESQL,
            organization_id="org_123",
            backup_type=BackupType.MANUAL
        )

        # Clean up old backups
        await backup_service.cleanup_old_backups()
        ```
    """

    def __init__(
        self,
        mongodb_uri: Optional[str] = None,
        postgres_host: Optional[str] = None,
        postgres_port: int = 5432,
        postgres_user: Optional[str] = None,
        postgres_password: Optional[str] = None,
        storage_base_path: str = "backups"
    ):
        """
        Initialize database backup service.

        Args:
            mongodb_uri: MongoDB connection URI
            postgres_host: PostgreSQL host
            postgres_port: PostgreSQL port
            postgres_user: PostgreSQL username
            postgres_password: PostgreSQL password
            storage_base_path: Base path in Hetzner Storage Box for backups
        """
        self.mongodb_uri = mongodb_uri or os.getenv("MONGODB_URL")
        self.postgres_host = postgres_host or os.getenv("POSTGRES_SERVER", "localhost")
        self.postgres_port = postgres_port
        self.postgres_user = postgres_user or os.getenv("POSTGRES_USER", "postgres")
        self.postgres_password = postgres_password or os.getenv("POSTGRES_PASSWORD")
        self.storage_base_path = storage_base_path

        self.logger = logging.getLogger(__name__)
        self.storage: Optional[HetznerStorageBox] = None

    async def _init_storage(self):
        """Initialize Hetzner Storage Box connection."""
        if self.storage and self.storage.connected:
            return

        try:
            self.storage = HetznerStorageBox(base_path=self.storage_base_path)
            await self.storage.connect()
            self.logger.info("Connected to Hetzner Storage Box for backups")
        except Exception as e:
            raise DatabaseBackupError(f"Failed to connect to storage: {e}")

    def _get_backup_path(
        self,
        organization_id: str,
        database_type: DatabaseType,
        database_name: str,
        backup_type: BackupType,
        timestamp: datetime
    ) -> str:
        """
        Get remote backup path in storage.

        Format: {org_id}/{db_type}/{db_name}/{backup_type}/backup_YYYY-MM-DD_HH-MM-SS.tar.gz

        Args:
            organization_id: Organization ID
            database_type: Database type
            database_name: Database name
            backup_type: Backup type
            timestamp: Backup timestamp

        Returns:
            Remote backup path
        """
        timestamp_str = timestamp.strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"backup_{timestamp_str}.tar.gz"

        return f"{organization_id}/{database_type.value}/{database_name}/{backup_type.value}/{filename}"

    def _get_metadata_path(self, backup_path: str) -> str:
        """Get metadata file path for backup."""
        return backup_path.replace(".tar.gz", ".metadata.json")

    async def _backup_mongodb(
        self,
        database_name: str,
        output_dir: str
    ) -> int:
        """
        Backup MongoDB database using mongodump.

        Args:
            database_name: Database name
            output_dir: Output directory for backup

        Returns:
            Backup size in bytes

        Raises:
            DatabaseBackupError: If backup fails
        """
        try:
            # Run mongodump
            cmd = [
                "mongodump",
                "--uri", self.mongodb_uri,
                "--db", database_name,
                "--out", output_dir,
                "--gzip"
            ]

            self.logger.info(f"Running mongodump for {database_name}...")

            result = await asyncio.to_thread(
                subprocess.run,
                cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )

            if result.returncode != 0:
                raise DatabaseBackupError(f"mongodump failed: {result.stderr}")

            self.logger.info(f"mongodump completed for {database_name}")

            # Calculate backup size
            backup_size = 0
            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    backup_size += os.path.getsize(file_path)

            return backup_size

        except subprocess.TimeoutExpired:
            raise DatabaseBackupError(f"mongodump timed out after 1 hour")
        except Exception as e:
            raise DatabaseBackupError(f"MongoDB backup failed: {e}")

    async def _backup_postgresql(
        self,
        database_name: str,
        output_file: str
    ) -> int:
        """
        Backup PostgreSQL database using pg_dump.

        Args:
            database_name: Database name
            output_file: Output file path

        Returns:
            Backup size in bytes

        Raises:
            DatabaseBackupError: If backup fails
        """
        try:
            # Set PGPASSWORD environment variable
            env = os.environ.copy()
            env["PGPASSWORD"] = self.postgres_password

            # Run pg_dump
            cmd = [
                "pg_dump",
                "-h", self.postgres_host,
                "-p", str(self.postgres_port),
                "-U", self.postgres_user,
                "-d", database_name,
                "-F", "c",  # Custom format (compressed)
                "-f", output_file
            ]

            self.logger.info(f"Running pg_dump for {database_name}...")

            result = await asyncio.to_thread(
                subprocess.run,
                cmd,
                capture_output=True,
                text=True,
                env=env,
                timeout=3600  # 1 hour timeout
            )

            if result.returncode != 0:
                raise DatabaseBackupError(f"pg_dump failed: {result.stderr}")

            self.logger.info(f"pg_dump completed for {database_name}")

            # Get backup size
            backup_size = os.path.getsize(output_file)
            return backup_size

        except subprocess.TimeoutExpired:
            raise DatabaseBackupError(f"pg_dump timed out after 1 hour")
        except Exception as e:
            raise DatabaseBackupError(f"PostgreSQL backup failed: {e}")

    async def _compress_backup(
        self,
        source_path: str,
        output_file: str
    ) -> int:
        """
        Compress backup directory to tar.gz.

        Args:
            source_path: Source directory or file
            output_file: Output tar.gz file

        Returns:
            Compressed size in bytes
        """
        try:
            self.logger.info(f"Compressing backup to {output_file}...")

            def _compress():
                shutil.make_archive(
                    output_file.replace(".tar.gz", ""),
                    "gztar",
                    source_path
                )

            await asyncio.to_thread(_compress)

            compressed_size = os.path.getsize(output_file)
            self.logger.info(f"Compression complete: {compressed_size} bytes")

            return compressed_size

        except Exception as e:
            raise DatabaseBackupError(f"Compression failed: {e}")

    async def backup_database(
        self,
        database_name: str,
        database_type: DatabaseType,
        organization_id: str,
        backup_type: BackupType = BackupType.MANUAL
    ) -> BackupMetadata:
        """
        Backup database and upload to Hetzner Storage Box.

        Args:
            database_name: Database name
            database_type: Database type (MongoDB or PostgreSQL)
            organization_id: Organization ID
            backup_type: Backup type (daily, weekly, monthly, manual)

        Returns:
            BackupMetadata with backup information

        Raises:
            DatabaseBackupError: If backup fails
        """
        timestamp = datetime.utcnow()
        temp_dir = None

        try:
            # Initialize storage connection
            await self._init_storage()

            # Create temporary directory for backup
            temp_dir = tempfile.mkdtemp(prefix=f"backup_{database_name}_")
            self.logger.info(f"Created temporary directory: {temp_dir}")

            # Perform database-specific backup
            if database_type == DatabaseType.MONGODB:
                backup_size = await self._backup_mongodb(database_name, temp_dir)

                # MongoDB backup creates a directory, need to compress it
                compressed_file = os.path.join(temp_dir, f"{database_name}.tar.gz")
                compressed_size = await self._compress_backup(
                    os.path.join(temp_dir, database_name),
                    compressed_file
                )

            elif database_type == DatabaseType.POSTGRESQL:
                # pg_dump with custom format is already compressed
                backup_file = os.path.join(temp_dir, f"{database_name}.dump")
                backup_size = await self._backup_postgresql(database_name, backup_file)

                # Create tar.gz for consistency
                compressed_file = os.path.join(temp_dir, f"{database_name}.tar.gz")
                compressed_size = await self._compress_backup(backup_file, compressed_file)

            else:
                raise DatabaseBackupError(f"Unsupported database type: {database_type}")

            # Get remote backup path
            backup_path = self._get_backup_path(
                organization_id,
                database_type,
                database_name,
                backup_type,
                timestamp
            )

            # Upload to storage
            self.logger.info(f"Uploading backup to {backup_path}...")
            await self.storage.upload_file(
                local_path=compressed_file,
                remote_path=backup_path,
                overwrite=True
            )
            self.logger.info(f"Backup uploaded successfully")

            # Create metadata
            metadata = BackupMetadata(
                database_name=database_name,
                database_type=database_type,
                backup_type=backup_type,
                organization_id=organization_id,
                timestamp=timestamp,
                file_size=backup_size,
                compressed_size=compressed_size,
                backup_path=backup_path,
                status="completed"
            )

            # Upload metadata
            metadata_path = self._get_metadata_path(backup_path)
            metadata_file = os.path.join(temp_dir, "metadata.json")
            with open(metadata_file, "w") as f:
                json.dump(metadata.to_dict(), f, indent=2)

            await self.storage.upload_file(
                local_path=metadata_file,
                remote_path=metadata_path,
                overwrite=True
            )

            self.logger.info(f"Backup completed: {database_name} -> {backup_path}")
            return metadata

        except Exception as e:
            self.logger.error(f"Backup failed for {database_name}: {e}")

            # Create failed metadata
            metadata = BackupMetadata(
                database_name=database_name,
                database_type=database_type,
                backup_type=backup_type,
                organization_id=organization_id,
                timestamp=timestamp,
                file_size=0,
                compressed_size=0,
                backup_path="",
                status="failed",
                error=str(e)
            )

            raise DatabaseBackupError(f"Backup failed: {e}")

        finally:
            # Clean up temporary directory
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                self.logger.info(f"Cleaned up temporary directory: {temp_dir}")

    async def list_backups(
        self,
        organization_id: Optional[str] = None,
        database_name: Optional[str] = None,
        database_type: Optional[DatabaseType] = None,
        backup_type: Optional[BackupType] = None
    ) -> List[BackupMetadata]:
        """
        List available backups.

        Args:
            organization_id: Filter by organization ID
            database_name: Filter by database name
            database_type: Filter by database type
            backup_type: Filter by backup type

        Returns:
            List of backup metadata

        Raises:
            DatabaseBackupError: If listing fails
        """
        try:
            await self._init_storage()

            # Build search path
            search_path = ""
            if organization_id:
                search_path += f"{organization_id}/"
            if database_type:
                search_path += f"{database_type.value}/"
            if database_name:
                search_path += f"{database_name}/"
            if backup_type:
                search_path += f"{backup_type.value}/"

            # List all .metadata.json files
            files = await self.storage.list_files(search_path)

            metadata_files = [f for f in files if f.endswith(".metadata.json")]

            backups = []
            for metadata_file in metadata_files:
                try:
                    # Download metadata
                    temp_file = tempfile.mktemp(suffix=".json")
                    await self.storage.download_file(metadata_file, temp_file)

                    with open(temp_file, "r") as f:
                        metadata_dict = json.load(f)

                    metadata = BackupMetadata.from_dict(metadata_dict)
                    backups.append(metadata)

                    os.remove(temp_file)
                except Exception as e:
                    self.logger.warning(f"Failed to read metadata {metadata_file}: {e}")

            # Sort by timestamp (newest first)
            backups.sort(key=lambda x: x.timestamp, reverse=True)

            return backups

        except Exception as e:
            raise DatabaseBackupError(f"Failed to list backups: {e}")

    async def restore_database(
        self,
        backup_path: str,
        target_database_name: Optional[str] = None
    ) -> bool:
        """
        Restore database from backup.

        Args:
            backup_path: Remote backup path
            target_database_name: Target database name (defaults to original name)

        Returns:
            True if restore successful

        Raises:
            DatabaseBackupError: If restore fails
        """
        temp_dir = None

        try:
            await self._init_storage()

            # Download metadata
            metadata_path = self._get_metadata_path(backup_path)
            temp_metadata = tempfile.mktemp(suffix=".json")

            await self.storage.download_file(metadata_path, temp_metadata)

            with open(temp_metadata, "r") as f:
                metadata_dict = json.load(f)

            metadata = BackupMetadata.from_dict(metadata_dict)
            os.remove(temp_metadata)

            # Use target database name or original
            db_name = target_database_name or metadata.database_name

            # Create temporary directory
            temp_dir = tempfile.mkdtemp(prefix=f"restore_{db_name}_")

            # Download backup file
            backup_file = os.path.join(temp_dir, "backup.tar.gz")
            await self.storage.download_file(backup_path, backup_file)

            # Extract backup
            shutil.unpack_archive(backup_file, temp_dir)

            # Restore based on database type
            if metadata.database_type == DatabaseType.MONGODB:
                # Find mongodump directory
                dump_dir = os.path.join(temp_dir, metadata.database_name)

                # Run mongorestore
                cmd = [
                    "mongorestore",
                    "--uri", self.mongodb_uri,
                    "--db", db_name,
                    "--drop",  # Drop existing collections
                    dump_dir
                ]

                result = await asyncio.to_thread(
                    subprocess.run,
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=3600
                )

                if result.returncode != 0:
                    raise DatabaseBackupError(f"mongorestore failed: {result.stderr}")

            elif metadata.database_type == DatabaseType.POSTGRESQL:
                # Find dump file
                dump_file = os.path.join(temp_dir, f"{metadata.database_name}.dump")

                # Set PGPASSWORD
                env = os.environ.copy()
                env["PGPASSWORD"] = self.postgres_password

                # Run pg_restore
                cmd = [
                    "pg_restore",
                    "-h", self.postgres_host,
                    "-p", str(self.postgres_port),
                    "-U", self.postgres_user,
                    "-d", db_name,
                    "--clean",  # Drop existing objects
                    "-F", "c",  # Custom format
                    dump_file
                ]

                result = await asyncio.to_thread(
                    subprocess.run,
                    cmd,
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=3600
                )

                if result.returncode != 0:
                    raise DatabaseBackupError(f"pg_restore failed: {result.stderr}")

            self.logger.info(f"Database restored successfully: {db_name}")
            return True

        except Exception as e:
            raise DatabaseBackupError(f"Restore failed: {e}")

        finally:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    async def cleanup_old_backups(self):
        """
        Clean up old backups based on retention policy.

        Retention:
        - Daily: Keep last 7 days
        - Weekly: Keep last 4 weeks
        - Monthly: Keep last 12 months
        - Manual: Keep forever
        """
        try:
            await self._init_storage()

            now = datetime.utcnow()

            # Get all backups
            all_backups = await self.list_backups()

            for backup in all_backups:
                should_delete = False
                age = now - backup.timestamp

                if backup.backup_type == BackupType.DAILY:
                    # Keep last 7 days
                    if age > timedelta(days=7):
                        should_delete = True

                elif backup.backup_type == BackupType.WEEKLY:
                    # Keep last 4 weeks
                    if age > timedelta(weeks=4):
                        should_delete = True

                elif backup.backup_type == BackupType.MONTHLY:
                    # Keep last 12 months
                    if age > timedelta(days=365):
                        should_delete = True

                # Manual backups are kept forever

                if should_delete:
                    try:
                        # Delete backup file
                        await self.storage.delete_file(backup.backup_path)

                        # Delete metadata file
                        metadata_path = self._get_metadata_path(backup.backup_path)
                        await self.storage.delete_file(metadata_path)

                        self.logger.info(f"Deleted old backup: {backup.backup_path}")
                    except Exception as e:
                        self.logger.warning(f"Failed to delete {backup.backup_path}: {e}")

            self.logger.info("Backup cleanup completed")

        except Exception as e:
            self.logger.error(f"Backup cleanup failed: {e}")
            raise DatabaseBackupError(f"Cleanup failed: {e}")

    async def get_backup_stats(
        self,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get backup statistics.

        Args:
            organization_id: Filter by organization ID

        Returns:
            Dictionary with backup statistics
        """
        try:
            backups = await self.list_backups(organization_id=organization_id)

            total_backups = len(backups)
            total_size = sum(b.compressed_size for b in backups)

            by_type = {}
            for backup_type in BackupType:
                count = len([b for b in backups if b.backup_type == backup_type])
                by_type[backup_type.value] = count

            by_database = {}
            for backup in backups:
                db_key = f"{backup.database_type.value}:{backup.database_name}"
                if db_key not in by_database:
                    by_database[db_key] = 0
                by_database[db_key] += 1

            latest_backup = backups[0] if backups else None

            return {
                "total_backups": total_backups,
                "total_size_bytes": total_size,
                "total_size_mb": total_size / (1024 * 1024),
                "by_type": by_type,
                "by_database": by_database,
                "latest_backup": latest_backup.to_dict() if latest_backup else None
            }

        except Exception as e:
            raise DatabaseBackupError(f"Failed to get backup stats: {e}")

    async def close(self):
        """Close storage connection."""
        if self.storage:
            await self.storage.disconnect()
