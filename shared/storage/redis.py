"""
Redis Storage Backend

This module provides Redis storage backend implementation for caching and session management.
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import redis.asyncio as redis
from pydantic import BaseModel

from .interfaces import StorageBackend, StorageConfig


class RedisStorageBackend(StorageBackend):
    """Redis storage backend implementation for caching and session management"""
    
    def __init__(self, config: StorageConfig):
        super().__init__(config)
        self.client = None
        self._prefix = "kasaai"
    
    async def connect(self) -> bool:
        """
        Connect to Redis server
        
        Returns:
            bool: True if connection successful
        """
        try:
            # Build connection parameters
            if self.config.connection_string:
                # Parse connection string
                self.client = redis.from_url(
                    self.config.connection_string,
                    decode_responses=True,
                    socket_connect_timeout=self.config.timeout,
                    socket_timeout=self.config.timeout,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
            else:
                # Use individual parameters
                self.client = redis.Redis(
                    host=self.config.host or "localhost",
                    port=self.config.port or 6379,
                    password=self.config.password,
                    db=0,
                    decode_responses=True,
                    socket_connect_timeout=self.config.timeout,
                    socket_timeout=self.config.timeout,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
            
            # Test connection
            await self.client.ping()
            self._connected = True
            return True
            
        except Exception as e:
            print(f"Failed to connect to Redis: {e}")
            self._connected = False
            return False
    
    async def disconnect(self) -> bool:
        """
        Disconnect from Redis server
        
        Returns:
            bool: True if disconnection successful
        """
        try:
            if self.client:
                await self.client.close()
            self._connected = False
            return True
        except Exception as e:
            print(f"Failed to disconnect from Redis: {e}")
            return False
    
    async def is_connected(self) -> bool:
        """
        Check if connected to Redis server
        
        Returns:
            bool: True if connected
        """
        if not self._connected or not self.client:
            return False
        
        try:
            await self.client.ping()
            return True
        except Exception:
            self._connected = False
            return False
    
    def _get_key(self, table_name: str, record_id: str = None) -> str:
        """Generate Redis key with prefix"""
        if record_id:
            return f"{self._prefix}:{table_name}:{record_id}"
        return f"{self._prefix}:{table_name}"
    
    def _serialize_data(self, data: Dict[str, Any]) -> str:
        """Serialize data to JSON string"""
        serialized = {}
        for key, value in data.items():
            if isinstance(value, datetime):
                serialized[key] = value.isoformat()
            else:
                serialized[key] = value
        return json.dumps(serialized)
    
    def _deserialize_data(self, data: str) -> Dict[str, Any]:
        """Deserialize data from JSON string"""
        return json.loads(data)
    
    async def create_table(self, table_name: str, schema: Dict[str, str]) -> bool:
        """
        Create table with schema (Redis doesn't need table creation)
        
        Args:
            table_name: Name of table to create
            schema: Column definitions (name: type)
            
        Returns:
            bool: True if table created successfully
        """
        # Redis doesn't require table creation
        # Just store the schema for reference
        schema_key = self._get_key(f"{table_name}_schema")
        await self.client.set(schema_key, json.dumps(schema))
        return True
    
    async def drop_table(self, table_name: str) -> bool:
        """
        Drop table (delete all keys with table prefix)
        
        Args:
            table_name: Name of table to drop
            
        Returns:
            bool: True if table dropped successfully
        """
        try:
            pattern = self._get_key(table_name) + "*"
            keys = await self.client.keys(pattern)
            if keys:
                await self.client.delete(*keys)
            return True
        except Exception as e:
            print(f"Failed to drop table {table_name}: {e}")
            return False
    
    async def table_exists(self, table_name: str) -> bool:
        """
        Check if table exists (check if schema exists)
        
        Args:
            table_name: Name of table to check
            
        Returns:
            bool: True if table exists
        """
        try:
            schema_key = self._get_key(f"{table_name}_schema")
            return await self.client.exists(schema_key) > 0
        except Exception as e:
            print(f"Failed to check if table {table_name} exists: {e}")
            return False
    
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
            key = self._get_key(table_name, record_id)
            serialized_data = self._serialize_data(data)
            
            # Store the record
            await self.client.set(key, serialized_data)
            
            # Add to table index
            index_key = self._get_key(f"{table_name}_index")
            await self.client.sadd(index_key, record_id)
            
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
            # Add updated timestamp
            data["updated_at"] = datetime.utcnow()
            
            key = self._get_key(table_name, record_id)
            
            # Get existing data
            existing_data = await self.client.get(key)
            if not existing_data:
                return False
            
            # Merge with existing data
            existing_dict = self._deserialize_data(existing_data)
            existing_dict.update(data)
            
            # Store updated data
            serialized_data = self._serialize_data(existing_dict)
            await self.client.set(key, serialized_data)
            
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
            key = self._get_key(table_name, record_id)
            
            # Delete the record
            deleted = await self.client.delete(key)
            
            # Remove from table index
            index_key = self._get_key(f"{table_name}_index")
            await self.client.srem(index_key, record_id)
            
            return deleted > 0
            
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
            key = self._get_key(table_name, record_id)
            data = await self.client.get(key)
            
            if data:
                return self._deserialize_data(data)
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
            order_by: Order by clause (not supported in Redis)
            limit: Maximum number of records
            offset: Number of records to skip
            
        Returns:
            List[Dict[str, Any]]: List of records
        """
        try:
            # Get all record IDs for the table
            index_key = self._get_key(f"{table_name}_index")
            record_ids = await self.client.smembers(index_key)
            
            # Get all records
            records = []
            for record_id in record_ids:
                record = await self.get_by_id(table_name, record_id)
                if record:
                    records.append(record)
            
            # Apply filters (simple in-memory filtering)
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
            
            # Apply offset and limit
            if offset:
                records = records[offset:]
            if limit:
                records = records[:limit]
            
            return records
            
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
                # Use set cardinality for faster counting
                index_key = self._get_key(f"{table_name}_index")
                return await self.client.scard(index_key)
                
        except Exception as e:
            print(f"Failed to count records in table {table_name}: {e}")
            return 0
    
    async def execute_raw(self, query: str, params: Dict[str, Any] = None) -> Any:
        """
        Execute raw Redis command
        
        Args:
            query: Redis command
            params: Command parameters
            
        Returns:
            Any: Command result
        """
        try:
            # Parse Redis command
            parts = query.split()
            command = parts[0].upper()
            args = parts[1:]
            
            # Execute command
            method = getattr(self.client, command.lower())
            if params:
                # Replace placeholders with parameters
                for i, arg in enumerate(args):
                    if arg.startswith(":") and arg[1:] in params:
                        args[i] = str(params[arg[1:]])
            
            return await method(*args)
            
        except Exception as e:
            print(f"Failed to execute raw Redis command: {e}")
            raise
    
    async def begin_transaction(self) -> Any:
        """
        Begin Redis transaction
        
        Returns:
            Any: Transaction object
        """
        try:
            return self.client.pipeline()
        except Exception as e:
            print(f"Failed to begin Redis transaction: {e}")
            raise
    
    async def commit_transaction(self, transaction: Any) -> bool:
        """
        Commit Redis transaction
        
        Args:
            transaction: Transaction object
            
        Returns:
            bool: True if commit successful
        """
        try:
            await transaction.execute()
            return True
        except Exception as e:
            print(f"Failed to commit Redis transaction: {e}")
            return False
    
    async def rollback_transaction(self, transaction: Any) -> bool:
        """
        Rollback Redis transaction (Redis doesn't support rollback)
        
        Args:
            transaction: Transaction object
            
        Returns:
            bool: True if rollback successful
        """
        # Redis doesn't support rollback, just discard the pipeline
        try:
            transaction.reset()
            return True
        except Exception as e:
            print(f"Failed to rollback Redis transaction: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check
        
        Returns:
            Dict[str, Any]: Health check results
        """
        try:
            start_time = datetime.utcnow()
            await self.client.ping()
            end_time = datetime.utcnow()
            
            return {
                "status": "healthy",
                "connected": True,
                "response_time_ms": (end_time - start_time).total_seconds() * 1000,
                "backend_type": "redis",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e),
                "backend_type": "redis",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    # Redis-specific methods for caching and session management
    
    async def set_cache(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        Set cache value with TTL
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            bool: True if successful
        """
        try:
            cache_key = f"{self._prefix}:cache:{key}"
            serialized_value = self._serialize_data({"value": value})
            await self.client.setex(cache_key, ttl, serialized_value)
            return True
        except Exception as e:
            print(f"Failed to set cache: {e}")
            return False
    
    async def get_cache(self, key: str) -> Optional[Any]:
        """
        Get cache value
        
        Args:
            key: Cache key
            
        Returns:
            Optional[Any]: Cached value if found
        """
        try:
            cache_key = f"{self._prefix}:cache:{key}"
            data = await self.client.get(cache_key)
            if data:
                return self._deserialize_data(data)["value"]
            return None
        except Exception as e:
            print(f"Failed to get cache: {e}")
            return None
    
    async def delete_cache(self, key: str) -> bool:
        """
        Delete cache value
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if successful
        """
        try:
            cache_key = f"{self._prefix}:cache:{key}"
            return await self.client.delete(cache_key) > 0
        except Exception as e:
            print(f"Failed to delete cache: {e}")
            return False
    
    async def set_session(self, session_id: str, data: Dict[str, Any], ttl: int = 86400) -> bool:
        """
        Set session data
        
        Args:
            session_id: Session ID
            data: Session data
            ttl: Time to live in seconds
            
        Returns:
            bool: True if successful
        """
        try:
            session_key = f"{self._prefix}:session:{session_id}"
            serialized_data = self._serialize_data(data)
            await self.client.setex(session_key, ttl, serialized_data)
            return True
        except Exception as e:
            print(f"Failed to set session: {e}")
            return False
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data
        
        Args:
            session_id: Session ID
            
        Returns:
            Optional[Dict[str, Any]]: Session data if found
        """
        try:
            session_key = f"{self._prefix}:session:{session_id}"
            data = await self.client.get(session_key)
            if data:
                return self._deserialize_data(data)
            return None
        except Exception as e:
            print(f"Failed to get session: {e}")
            return None
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete session data
        
        Args:
            session_id: Session ID
            
        Returns:
            bool: True if successful
        """
        try:
            session_key = f"{self._prefix}:session:{session_id}"
            return await self.client.delete(session_key) > 0
        except Exception as e:
            print(f"Failed to delete session: {e}")
            return False
