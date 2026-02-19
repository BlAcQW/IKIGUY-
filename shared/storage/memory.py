"""
In-Memory Storage Backend

This module provides in-memory storage backend implementation for testing and development.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from collections import defaultdict

from .interfaces import StorageBackend, StorageConfig


class MemoryStorageBackend(StorageBackend):
    """In-memory storage backend implementation for testing and development"""
    
    def __init__(self, config: StorageConfig):
        super().__init__(config)
        self._tables: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(dict)
        self._schemas: Dict[str, Dict[str, str]] = {}
        self._connected = True  # Always connected for in-memory
    
    async def connect(self) -> bool:
        """
        Connect to in-memory storage (always succeeds)
        
        Returns:
            bool: True if connection successful
        """
        self._connected = True
        return True
    
    async def disconnect(self) -> bool:
        """
        Disconnect from in-memory storage
        
        Returns:
            bool: True if disconnection successful
        """
        self._connected = False
        return True
    
    async def is_connected(self) -> bool:
        """
        Check if connected to in-memory storage
        
        Returns:
            bool: True if connected
        """
        return self._connected
    
    async def create_table(self, table_name: str, schema: Dict[str, str]) -> bool:
        """
        Create table with schema
        
        Args:
            table_name: Name of table to create
            schema: Column definitions (name: type)
            
        Returns:
            bool: True if table created successfully
        """
        try:
            self._schemas[table_name] = schema
            self._tables[table_name] = {}
            return True
        except Exception as e:
            print(f"Failed to create table {table_name}: {e}")
            return False
    
    async def drop_table(self, table_name: str) -> bool:
        """
        Drop table
        
        Args:
            table_name: Name of table to drop
            
        Returns:
            bool: True if table dropped successfully
        """
        try:
            if table_name in self._tables:
                del self._tables[table_name]
            if table_name in self._schemas:
                del self._schemas[table_name]
            return True
        except Exception as e:
            print(f"Failed to drop table {table_name}: {e}")
            return False
    
    async def table_exists(self, table_name: str) -> bool:
        """
        Check if table exists
        
        Args:
            table_name: Name of table to check
            
        Returns:
            bool: True if table exists
        """
        return table_name in self._tables
    
    async def insert(self, table_name: str, data: Dict[str, Any]) -> str:
        """
        Insert data into table
        
        Args:
            table_name: Name of table
            data: Data to insert
            
        Returns:
            str: ID of inserted record
        """
        try:
            # Generate ID if not provided
            if "id" not in data:
                data["id"] = str(uuid.uuid4())
            
            # Add timestamp if not provided
            if "created_at" not in data:
                data["created_at"] = datetime.utcnow()
            
            record_id = data["id"]
            
            # Create table if it doesn't exist
            if table_name not in self._tables:
                self._tables[table_name] = {}
            
            # Store the record
            self._tables[table_name][record_id] = data.copy()
            
            return record_id
            
        except Exception as e:
            print(f"Failed to insert into table {table_name}: {e}")
            raise
    
    async def update(self, table_name: str, record_id: str, data: Dict[str, Any]) -> bool:
        """
        Update record in table
        
        Args:
            table_name: Name of table
            record_id: ID of record to update
            data: Data to update
            
        Returns:
            bool: True if update successful
        """
        try:
            if table_name not in self._tables or record_id not in self._tables[table_name]:
                return False
            
            # Add updated timestamp
            data["updated_at"] = datetime.utcnow()
            
            # Update the record
            self._tables[table_name][record_id].update(data)
            
            return True
            
        except Exception as e:
            print(f"Failed to update record {record_id} in table {table_name}: {e}")
            return False
    
    async def delete(self, table_name: str, record_id: str) -> bool:
        """
        Delete record from table
        
        Args:
            table_name: Name of table
            record_id: ID of record to delete
            
        Returns:
            bool: True if delete successful
        """
        try:
            if table_name in self._tables and record_id in self._tables[table_name]:
                del self._tables[table_name][record_id]
                return True
            return False
        except Exception as e:
            print(f"Failed to delete record {record_id} from table {table_name}: {e}")
            return False
    
    async def get_by_id(self, table_name: str, record_id: str) -> Optional[Dict[str, Any]]:
        """
        Get record by ID
        
        Args:
            table_name: Name of table
            record_id: ID of record
            
        Returns:
            Optional[Dict[str, Any]]: Record data if found
        """
        try:
            if table_name in self._tables and record_id in self._tables[table_name]:
                return self._tables[table_name][record_id].copy()
            return None
        except Exception as e:
            print(f"Failed to get record {record_id} from table {table_name}: {e}")
            return None
    
    async def query(self, table_name: str, filters: Dict[str, Any] = None, 
                   order_by: str = None, limit: int = None, offset: int = None) -> List[Dict[str, Any]]:
        """
        Query records from table
        
        Args:
            table_name: Name of table
            filters: Filter conditions
            order_by: Order by clause
            limit: Maximum number of records
            offset: Number of records to skip
            
        Returns:
            List[Dict[str, Any]]: List of records
        """
        try:
            if table_name not in self._tables:
                return []
            
            records = list(self._tables[table_name].values())
            
            # Apply filters
            if filters:
                filtered_records = []
                for record in records:
                    matches = True
                    for key, value in filters.items():
                        if key not in record or record[key] != value:
                            matches = False
                            break
                    if matches:
                        filtered_records.append(record)
                records = filtered_records
            
            # Apply ordering
            if order_by:
                try:
                    # Simple ordering by field name
                    reverse = False
                    if order_by.startswith("-"):
                        order_by = order_by[1:]
                        reverse = True
                    records.sort(key=lambda x: x.get(order_by, ""), reverse=reverse)
                except Exception:
                    # If ordering fails, keep original order
                    pass
            
            # Apply offset and limit
            if offset:
                records = records[offset:]
            if limit:
                records = records[:limit]
            
            return [record.copy() for record in records]
            
        except Exception as e:
            print(f"Failed to query table {table_name}: {e}")
            return []
    
    async def count(self, table_name: str, filters: Dict[str, Any] = None) -> int:
        """
        Count records in table
        
        Args:
            table_name: Name of table
            filters: Filter conditions
            
        Returns:
            int: Number of records
        """
        try:
            if filters:
                # Use query method and count results
                records = await self.query(table_name, filters)
                return len(records)
            else:
                # Return total count
                return len(self._tables.get(table_name, {}))
                
        except Exception as e:
            print(f"Failed to count records in table {table_name}: {e}")
            return 0
    
    async def execute_raw(self, query: str, params: Dict[str, Any] = None) -> Any:
        """
        Execute raw query (not supported in memory backend)
        
        Args:
            query: Raw query string
            params: Query parameters
            
        Returns:
            Any: Query result
        """
        raise NotImplementedError("Raw queries not supported in memory backend")
    
    async def begin_transaction(self) -> Any:
        """
        Begin transaction (not supported in memory backend)
        
        Returns:
            Any: Transaction object
        """
        # For memory backend, we'll use a simple transaction wrapper
        return MemoryTransaction(self)
    
    async def commit_transaction(self, transaction: Any) -> bool:
        """
        Commit transaction
        
        Args:
            transaction: Transaction object
            
        Returns:
            bool: True if commit successful
        """
        try:
            if hasattr(transaction, 'commit'):
                await transaction.commit()
            return True
        except Exception as e:
            print(f"Failed to commit transaction: {e}")
            return False
    
    async def rollback_transaction(self, transaction: Any) -> bool:
        """
        Rollback transaction
        
        Args:
            transaction: Transaction object
            
        Returns:
            bool: True if rollback successful
        """
        try:
            if hasattr(transaction, 'rollback'):
                await transaction.rollback()
            return True
        except Exception as e:
            print(f"Failed to rollback transaction: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check
        
        Returns:
            Dict[str, Any]: Health check results
        """
        try:
            return {
                "status": "healthy",
                "connected": self._connected,
                "tables_count": len(self._tables),
                "total_records": sum(len(table) for table in self._tables.values()),
                "backend_type": "memory",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e),
                "backend_type": "memory",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    # Memory-specific methods for testing and debugging
    
    def clear_all(self) -> None:
        """Clear all data (useful for testing)"""
        self._tables.clear()
        self._schemas.clear()
    
    def get_table_data(self, table_name: str) -> Dict[str, Dict[str, Any]]:
        """Get all data from a table (useful for testing)"""
        return self._tables.get(table_name, {}).copy()
    
    def set_table_data(self, table_name: str, data: Dict[str, Dict[str, Any]]) -> None:
        """Set all data for a table (useful for testing)"""
        self._tables[table_name] = data.copy()


class MemoryTransaction:
    """Simple transaction wrapper for memory backend"""
    
    def __init__(self, backend: MemoryStorageBackend):
        self.backend = backend
        self._snapshot = {}
        self._operations = []
        self._committed = False
        self._rolled_back = False
    
    async def commit(self) -> None:
        """Commit transaction (no-op for memory backend)"""
        if not self._committed and not self._rolled_back:
            self._committed = True
    
    async def rollback(self) -> None:
        """Rollback transaction (no-op for memory backend)"""
        if not self._committed and not self._rolled_back:
            self._rolled_back = True
