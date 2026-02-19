#!/usr/bin/env python3
"""
Automated Database Backup Cron Script.

Runs daily backups of all MongoDB and PostgreSQL databases.
Designed to be run as a cron job.

Usage:
    python backup_cron.py [--backup-type {daily,weekly,monthly}]

Example crontab entries:
    # Daily backups at 2 AM
    0 2 * * * cd /opt/kasaai && /opt/kasaai/apps/venv/bin/python /opt/kasaai/apps/shared/backup/backup_cron.py --backup-type daily

    # Weekly backups on Sunday at 3 AM
    0 3 * * 0 cd /opt/kasaai && /opt/kasaai/apps/venv/bin/python /opt/kasaai/apps/shared/backup/backup_cron.py --backup-type weekly

    # Monthly backups on 1st of month at 4 AM
    0 4 1 * * cd /opt/kasaai && /opt/kasaai/apps/venv/bin/python /opt/kasaai/apps/shared/backup/backup_cron.py --backup-type monthly

    # Cleanup old backups daily at 5 AM
    0 5 * * * cd /opt/kasaai && /opt/kasaai/apps/venv/bin/python /opt/kasaai/apps/shared/backup/backup_cron.py --cleanup-only
"""

import asyncio
import argparse
import logging
import os
import sys
import subprocess
from datetime import datetime
from typing import List

# Add apps directory to Python path
sys.path.insert(0, '/opt/kasaai')

from apps.shared.backup import (
    DatabaseBackupService,
    DatabaseType,
    BackupType,
    DatabaseBackupError,
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/kasaai_backups.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class BackupCronJob:
    """Automated backup cron job."""

    def __init__(self, backup_type: BackupType = BackupType.DAILY):
        """
        Initialize backup cron job.

        Args:
            backup_type: Type of backup to perform
        """
        self.backup_type = backup_type
        self.backup_service = DatabaseBackupService()
        self.organization_id = os.getenv("DEFAULT_ORGANIZATION_ID", "default")

    async def get_mongodb_databases(self) -> List[str]:
        """
        Get list of MongoDB databases to backup.

        Returns:
            List of database names
        """
        try:
            mongodb_uri = os.getenv("MONGODB_URL")
            if not mongodb_uri:
                logger.warning("MONGODB_URL not set, skipping MongoDB backups")
                return []

            # List MongoDB databases
            cmd = [
                "mongosh",
                mongodb_uri,
                "--quiet",
                "--eval",
                "db.adminCommand('listDatabases').databases.map(d => d.name).join('\\n')"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                logger.error(f"Failed to list MongoDB databases: {result.stderr}")
                return []

            databases = [
                line.strip()
                for line in result.stdout.strip().split('\n')
                if line.strip() and line.strip() not in ["admin", "config", "local"]
            ]

            logger.info(f"Found {len(databases)} MongoDB databases to backup")
            return databases

        except Exception as e:
            logger.error(f"Error listing MongoDB databases: {e}")
            return []

    async def get_postgresql_databases(self) -> List[str]:
        """
        Get list of PostgreSQL databases to backup.

        Returns:
            List of database names
        """
        try:
            postgres_host = os.getenv("POSTGRES_SERVER", "localhost")
            postgres_user = os.getenv("POSTGRES_USER", "postgres")
            postgres_password = os.getenv("POSTGRES_PASSWORD")

            if not postgres_password:
                logger.warning("POSTGRES_PASSWORD not set, skipping PostgreSQL backups")
                return []

            # Set PGPASSWORD
            env = os.environ.copy()
            env["PGPASSWORD"] = postgres_password

            # List PostgreSQL databases
            cmd = [
                "psql",
                "-h", postgres_host,
                "-U", postgres_user,
                "-t",
                "-c", "SELECT datname FROM pg_database WHERE datistemplate = false AND datname NOT IN ('postgres');"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=30)

            if result.returncode != 0:
                logger.error(f"Failed to list PostgreSQL databases: {result.stderr}")
                return []

            databases = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]

            logger.info(f"Found {len(databases)} PostgreSQL databases to backup")
            return databases

        except Exception as e:
            logger.error(f"Error listing PostgreSQL databases: {e}")
            return []

    async def backup_database(
        self,
        database_name: str,
        database_type: DatabaseType
    ) -> bool:
        """
        Backup a single database.

        Args:
            database_name: Database name
            database_type: Database type

        Returns:
            True if backup successful
        """
        try:
            logger.info(f"Starting backup: {database_name} ({database_type.value})")

            metadata = await self.backup_service.backup_database(
                database_name=database_name,
                database_type=database_type,
                organization_id=self.organization_id,
                backup_type=self.backup_type
            )

            logger.info(
                f"Backup completed: {database_name} -> {metadata.backup_path} "
                f"({metadata.compressed_size / (1024 * 1024):.2f} MB)"
            )

            return True

        except DatabaseBackupError as e:
            logger.error(f"Backup failed for {database_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error backing up {database_name}: {e}")
            return False

    async def run_backups(self):
        """
        Run backups for all databases.

        Returns:
            Tuple of (success_count, failure_count)
        """
        logger.info(f"Starting {self.backup_type.value} backup run")
        start_time = datetime.utcnow()

        success_count = 0
        failure_count = 0

        # Backup MongoDB databases
        mongodb_databases = await self.get_mongodb_databases()
        for db_name in mongodb_databases:
            success = await self.backup_database(db_name, DatabaseType.MONGODB)
            if success:
                success_count += 1
            else:
                failure_count += 1

        # Backup PostgreSQL databases
        postgresql_databases = await self.get_postgresql_databases()
        for db_name in postgresql_databases:
            success = await self.backup_database(db_name, DatabaseType.POSTGRESQL)
            if success:
                success_count += 1
            else:
                failure_count += 1

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        logger.info(
            f"Backup run completed in {duration:.2f} seconds: "
            f"{success_count} successful, {failure_count} failed"
        )

        return success_count, failure_count

    async def run_cleanup(self):
        """
        Clean up old backups based on retention policy.

        Returns:
            True if cleanup successful
        """
        try:
            logger.info("Starting backup cleanup")

            await self.backup_service.cleanup_old_backups()

            logger.info("Backup cleanup completed successfully")
            return True

        except DatabaseBackupError as e:
            logger.error(f"Backup cleanup failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during cleanup: {e}")
            return False

    async def close(self):
        """Close backup service connection."""
        await self.backup_service.close()


async def main():
    """Main entry point for cron job."""
    parser = argparse.ArgumentParser(
        description='Automated database backup cron job'
    )
    parser.add_argument(
        '--backup-type',
        choices=['daily', 'weekly', 'monthly'],
        default='daily',
        help='Type of backup to perform (default: daily)'
    )
    parser.add_argument(
        '--cleanup-only',
        action='store_true',
        help='Only run cleanup, skip backups'
    )
    parser.add_argument(
        '--no-cleanup',
        action='store_true',
        help='Skip cleanup after backups'
    )

    args = parser.parse_args()

    # Convert backup type string to enum
    backup_type = BackupType(args.backup_type)

    # Create backup job
    backup_job = BackupCronJob(backup_type=backup_type)

    try:
        if args.cleanup_only:
            # Only run cleanup
            logger.info("Running cleanup only (--cleanup-only flag set)")
            await backup_job.run_cleanup()
        else:
            # Run backups
            success_count, failure_count = await backup_job.run_backups()

            # Run cleanup after backups (unless --no-cleanup is set)
            if not args.no_cleanup:
                await backup_job.run_cleanup()

            # Exit with error code if any backups failed
            if failure_count > 0:
                logger.error(f"Some backups failed: {failure_count} failures")
                sys.exit(1)

        logger.info("Backup cron job completed successfully")

    except Exception as e:
        logger.error(f"Backup cron job failed: {e}")
        sys.exit(1)

    finally:
        await backup_job.close()


if __name__ == "__main__":
    asyncio.run(main())
