"""
Storage service that integrates shared storage management library.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import logging
import json

from apps.shared.storage import MemoryStorageBackend, PostgresStorageBackend, RedisStorageBackend
from apps.shared.storage.interfaces import StorageConfig, StorageBackend

logger = logging.getLogger(__name__)


class StorageService:
    """Service for managing data storage using shared libraries."""

    def __init__(self, storage_type: str = "memory", connection_string: str = None):
        """
        Initialize the storage service.

        Args:
            storage_type: Type of storage backend (memory, postgresql, redis)
            connection_string: Connection string for the storage backend
        """
        self.storage_type = storage_type
        self.storage_backend = self._initialize_storage_backend(storage_type, connection_string)

    def _initialize_storage_backend(self, storage_type: str, connection_string: str) -> StorageBackend:
        """
        Initialize the appropriate storage backend.

        Args:
            storage_type: Type of storage backend
            connection_string: Connection string for the storage backend

        Returns:
            StorageBackend: Initialized storage backend
        """
        if storage_type == "postgresql":
            if not connection_string:
                connection_string = "postgresql://localhost:5432/kasaai_core"
            config = StorageConfig(backend_type="postgresql", connection_string=connection_string)
            return PostgresStorageBackend(config)
        elif storage_type == "redis":
            if not connection_string:
                connection_string = "redis://localhost:6379/0"
            config = StorageConfig(backend_type="redis", connection_string=connection_string)
            return RedisStorageBackend(config)
        else:  # memory
            config = StorageConfig(backend_type="memory", connection_string="memory://")
            return MemoryStorageBackend(config)

    async def _ensure_initialized(self):
        """Ensure the storage backend is initialized."""
        try:
            # Test connection by creating a test table
            await self.storage_backend.create_table("test_connection", {
                "id": "TEXT PRIMARY KEY",
                "data": "TEXT"
            })
            await self.storage_backend.delete_table("test_connection")
        except Exception as e:
            logger.warning(f"Storage backend initialization test failed: {e}")

    async def create_table(
        self,
        table_name: str,
        schema: Dict[str, str]
    ) -> bool:
        """
        Create a new table.

        Args:
            table_name: Name of the table to create
            schema: Table schema definition

        Returns:
            bool: True if table was created successfully
        """
        try:
            await self._ensure_initialized()
            await self.storage_backend.create_table(table_name, schema)
            logger.info(f"Created table {table_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create table {table_name}: {e}")
            return False

    async def delete_table(self, table_name: str) -> bool:
        """
        Delete a table.

        Args:
            table_name: Name of the table to delete

        Returns:
            bool: True if table was deleted successfully
        """
        try:
            await self._ensure_initialized()
            await self.storage_backend.delete_table(table_name)
            logger.info(f"Deleted table {table_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete table {table_name}: {e}")
            return False

    async def insert(
        self,
        table_name: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        Insert data into a table.

        Args:
            table_name: Name of the table
            data: Data to insert

        Returns:
            bool: True if data was inserted successfully
        """
        try:
            await self._ensure_initialized()
            await self.storage_backend.insert(table_name, data)
            logger.debug(f"Inserted data into {table_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to insert data into {table_name}: {e}")
            return False

    async def select(
        self,
        table_name: str,
        conditions: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Select data from a table.

        Args:
            table_name: Name of the table
            conditions: Query conditions
            limit: Maximum number of results
            offset: Number of results to skip
            order_by: Order by clause

        Returns:
            List[Dict[str, Any]]: Query results
        """
        try:
            await self._ensure_initialized()
            results = await self.storage_backend.select(
                table_name, conditions, limit, offset, order_by
            )
            return results
        except Exception as e:
            logger.error(f"Failed to select data from {table_name}: {e}")
            return []

    async def select_one(
        self,
        table_name: str,
        conditions: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Select a single record from a table.

        Args:
            table_name: Name of the table
            conditions: Query conditions

        Returns:
            Optional[Dict[str, Any]]: Single record or None
        """
        try:
            await self._ensure_initialized()
            result = await self.storage_backend.select_one(table_name, conditions)
            return result
        except Exception as e:
            logger.error(f"Failed to select one record from {table_name}: {e}")
            return None

    async def update(
        self,
        table_name: str,
        data: Dict[str, Any],
        conditions: Dict[str, Any]
    ) -> int:
        """
        Update data in a table.

        Args:
            table_name: Name of the table
            data: Data to update
            conditions: Update conditions

        Returns:
            int: Number of records updated
        """
        try:
            await self._ensure_initialized()
            result = await self.storage_backend.update(table_name, data, conditions)
            logger.debug(f"Updated {result} records in {table_name}")
            return result
        except Exception as e:
            logger.error(f"Failed to update data in {table_name}: {e}")
            return 0

    async def delete(
        self,
        table_name: str,
        conditions: Dict[str, Any]
    ) -> int:
        """
        Delete data from a table.

        Args:
            table_name: Name of the table
            conditions: Delete conditions

        Returns:
            int: Number of records deleted
        """
        try:
            await self._ensure_initialized()
            result = await self.storage_backend.delete(table_name, conditions)
            logger.debug(f"Deleted {result} records from {table_name}")
            return result
        except Exception as e:
            logger.error(f"Failed to delete data from {table_name}: {e}")
            return 0

    async def upsert(
        self,
        table_name: str,
        data: Dict[str, Any],
        unique_columns: List[str]
    ) -> int:
        """
        Upsert data in a table.

        Args:
            table_name: Name of the table
            data: Data to upsert
            unique_columns: Columns that determine uniqueness

        Returns:
            int: Number of records affected
        """
        try:
            await self._ensure_initialized()
            result = await self.storage_backend.upsert(table_name, data, unique_columns)
            logger.debug(f"Upserted data in {table_name}")
            return result
        except Exception as e:
            logger.error(f"Failed to upsert data in {table_name}: {e}")
            return 0

    async def get_table_info(self, table_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a table.

        Args:
            table_name: Name of the table

        Returns:
            Optional[Dict[str, Any]]: Table information
        """
        try:
            await self._ensure_initialized()
            info = await self.storage_backend.get_table_info(table_name)
            return info
        except Exception as e:
            logger.error(f"Failed to get table info for {table_name}: {e}")
            return None

    async def list_tables(self) -> List[str]:
        """
        List all tables.

        Returns:
            List[str]: List of table names
        """
        try:
            await self._ensure_initialized()
            tables = await self.storage_backend.list_tables()
            return tables
        except Exception as e:
            logger.error(f"Failed to list tables: {e}")
            return []

    async def backup_table(
        self,
        table_name: str,
        backup_name: str
    ) -> bool:
        """
        Create a backup of a table.

        Args:
            table_name: Name of the table to backup
            backup_name: Name of the backup

        Returns:
            bool: True if backup was created successfully
        """
        try:
            await self._ensure_initialized()
            # Get all data from the table
            data = await self.select(table_name)
            
            # Create backup table
            backup_table_name = f"{table_name}_backup_{backup_name}"
            table_info = await self.get_table_info(table_name)
            if table_info:
                await self.create_table(backup_table_name, table_info.get("schema", {}))
                
                # Insert backup data
                for record in data:
                    await self.insert(backup_table_name, record)
                
                logger.info(f"Created backup {backup_name} for table {table_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to backup table {table_name}: {e}")
            return False

    async def restore_table(
        self,
        table_name: str,
        backup_name: str
    ) -> bool:
        """
        Restore a table from backup.

        Args:
            table_name: Name of the table to restore
            backup_name: Name of the backup to restore from

        Returns:
            bool: True if restore was successful
        """
        try:
            await self._ensure_initialized()
            backup_table_name = f"{table_name}_backup_{backup_name}"
            
            # Check if backup exists
            backup_data = await self.select(backup_table_name)
            if not backup_data:
                logger.error(f"Backup {backup_name} not found for table {table_name}")
                return False
            
            # Clear existing table
            await self.delete(table_name, {})
            
            # Restore data
            for record in backup_data:
                await self.insert(table_name, record)
            
            logger.info(f"Restored table {table_name} from backup {backup_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to restore table {table_name}: {e}")
            return False

    async def export_table(
        self,
        table_name: str,
        format: str = "json"
    ) -> str:
        """
        Export table data.

        Args:
            table_name: Name of the table to export
            format: Export format (json, csv)

        Returns:
            str: Exported data
        """
        try:
            await self._ensure_initialized()
            data = await self.select(table_name)
            
            if format.lower() == "json":
                return json.dumps(data, indent=2, default=str)
            elif format.lower() == "csv":
                if not data:
                    return ""
                
                import csv
                import io
                
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
                
                return output.getvalue()
            else:
                raise ValueError(f"Unsupported export format: {format}")
        except Exception as e:
            logger.error(f"Failed to export table {table_name}: {e}")
            return ""

    async def import_table(
        self,
        table_name: str,
        data: str,
        format: str = "json"
    ) -> bool:
        """
        Import data into a table.

        Args:
            table_name: Name of the table to import into
            data: Data to import
            format: Import format (json, csv)

        Returns:
            bool: True if import was successful
        """
        try:
            await self._ensure_initialized()
            
            if format.lower() == "json":
                import_data = json.loads(data)
            elif format.lower() == "csv":
                import csv
                import io
                
                input_data = io.StringIO(data)
                reader = csv.DictReader(input_data)
                import_data = list(reader)
            else:
                raise ValueError(f"Unsupported import format: {format}")
            
            # Insert data
            for record in import_data:
                await self.insert(table_name, record)
            
            logger.info(f"Imported {len(import_data)} records into {table_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to import data into {table_name}: {e}")
            return False

    async def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.

        Returns:
            Dict[str, Any]: Storage statistics
        """
        try:
            await self._ensure_initialized()
            tables = await self.list_tables()
            
            stats = {
                "storage_type": self.storage_type,
                "total_tables": len(tables),
                "tables": {}
            }
            
            for table_name in tables:
                table_info = await self.get_table_info(table_name)
                if table_info:
                    stats["tables"][table_name] = {
                        "record_count": table_info.get("record_count", 0),
                        "size_bytes": table_info.get("size_bytes", 0)
                    }
            
            return stats
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {}

    async def cleanup_old_data(
        self,
        table_name: str,
        date_column: str,
        days_to_keep: int
    ) -> int:
        """
        Clean up old data from a table.

        Args:
            table_name: Name of the table
            date_column: Name of the date column
            days_to_keep: Number of days to keep

        Returns:
            int: Number of records deleted
        """
        try:
            await self._ensure_initialized()
            from datetime import datetime, timedelta
            
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            # Delete old records
            result = await self.delete(table_name, {
                date_column: {"$lt": cutoff_date.isoformat()}
            })
            
            logger.info(f"Cleaned up {result} old records from {table_name}")
            return result
        except Exception as e:
            logger.error(f"Failed to cleanup old data from {table_name}: {e}")
            return 0

    # File-specific storage methods for voice creation
    async def save_file(self, file_path: str, data: bytes) -> bool:
        """
        Save binary data to a file path.

        Args:
            file_path: Virtual file path
            data: Binary data to save

        Returns:
            bool: True if file was saved successfully
        """
        try:
            import os
            import base64
            
            await self._ensure_initialized()
            
            # Create files table if it doesn't exist
            await self.create_table("files", {
                "path": "TEXT PRIMARY KEY",
                "data": "TEXT",
                "size": "INTEGER",
                "mime_type": "TEXT",
                "created_at": "TEXT"
            })
            
            # Encode data as base64 for storage
            encoded_data = base64.b64encode(data).decode('utf-8')
            
            # Guess mime type from file extension
            _, ext = os.path.splitext(file_path)
            mime_type = {
                '.wav': 'audio/wav',
                '.mp3': 'audio/mpeg',
                '.m4a': 'audio/mp4',
                '.json': 'application/json',
                '.txt': 'text/plain'
            }.get(ext.lower(), 'application/octet-stream')
            
            file_record = {
                "path": file_path,
                "data": encoded_data,
                "size": len(data),
                "mime_type": mime_type,
                "created_at": datetime.utcnow().isoformat()
            }
            
            await self.upsert("files", file_record, ["path"])
            logger.debug(f"Saved file {file_path} ({len(data)} bytes)")
            return True
        except Exception as e:
            logger.error(f"Failed to save file {file_path}: {e}")
            return False

    async def get_file(self, file_path: str) -> bytes:
        """
        Get binary data from a file path.

        Args:
            file_path: Virtual file path

        Returns:
            bytes: File data

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        try:
            import base64
            
            await self._ensure_initialized()
            
            file_record = await self.select_one("files", {"path": file_path})
            if not file_record:
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Decode base64 data
            data = base64.b64decode(file_record["data"].encode('utf-8'))
            logger.debug(f"Retrieved file {file_path} ({len(data)} bytes)")
            return data
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get file {file_path}: {e}")
            raise FileNotFoundError(f"File not found: {file_path}")

    async def delete_folder(self, folder_path: str) -> bool:
        """
        Delete all files in a folder path.

        Args:
            folder_path: Virtual folder path

        Returns:
            bool: True if folder was deleted successfully
        """
        try:
            await self._ensure_initialized()
            
            # Find all files in the folder
            # Using a simple prefix match since we don't have complex query operators
            all_files = await self.select("files")
            folder_files = [f for f in all_files if f["path"].startswith(folder_path)]
            
            # Delete each file
            deleted_count = 0
            for file_record in folder_files:
                await self.delete("files", {"path": file_record["path"]})
                deleted_count += 1
            
            logger.info(f"Deleted folder {folder_path} with {deleted_count} files")
            return True
        except Exception as e:
            logger.error(f"Failed to delete folder {folder_path}: {e}")
            return False

    async def list_files(self, folder_path: str = "") -> List[str]:
        """
        List all files in a folder path.

        Args:
            folder_path: Virtual folder path

        Returns:
            List[str]: List of file paths
        """
        try:
            await self._ensure_initialized()
            
            all_files = await self.select("files")
            if folder_path:
                folder_files = [f["path"] for f in all_files if f["path"].startswith(folder_path)]
            else:
                folder_files = [f["path"] for f in all_files]
            
            return sorted(folder_files)
        except Exception as e:
            logger.error(f"Failed to list files in {folder_path}: {e}")
            return []

    async def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists.

        Args:
            file_path: Virtual file path

        Returns:
            bool: True if file exists
        """
        try:
            await self._ensure_initialized()
            file_record = await self.select_one("files", {"path": file_path})
            return file_record is not None
        except Exception as e:
            logger.error(f"Failed to check if file exists {file_path}: {e}")
            return False

    async def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get file information.

        Args:
            file_path: Virtual file path

        Returns:
            Optional[Dict[str, Any]]: File information
        """
        try:
            await self._ensure_initialized()
            file_record = await self.select_one("files", {"path": file_path})
            if file_record:
                return {
                    "path": file_record["path"],
                    "size": file_record["size"],
                    "mime_type": file_record["mime_type"],
                    "created_at": file_record["created_at"]
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get file info {file_path}: {e}")
            return None
