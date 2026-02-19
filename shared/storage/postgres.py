"""
PostgreSQL Storage Backend

This module provides PostgreSQL storage backend implementation.
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import asyncpg
from sqlalchemy import create_engine, text, MetaData, Table, Column, String, Integer, DateTime, JSON, Boolean
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from .interfaces import StorageBackend, StorageConfig


class PostgresStorageBackend(StorageBackend):
    """PostgreSQL storage backend implementation"""
    
    def __init__(self, config: StorageConfig):
        super().__init__(config)
        self.engine = None
        self.session_factory = None
        self.metadata = MetaData()
        self._connection_pool = None
    
    async def connect(self) -> bool:
        """
        Connect to PostgreSQL database
        
        Returns:
            bool: True if connection successful
        """
        try:
            # Build connection string
            if self.config.connection_string:
                connection_string = self.config.connection_string
            else:
                connection_string = (
                    f"postgresql+asyncpg://{self.config.username}:{self.config.password}"
                    f"@{self.config.host}:{self.config.port}/{self.config.database}"
                )
                if self.config.ssl_mode:
                    connection_string += f"?sslmode={self.config.ssl_mode}"
            
            # Create async engine
            self.engine = create_async_engine(
                connection_string,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.timeout,
                echo=False
            )
            
            # Create session factory
            self.session_factory = sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )
            
            # Test connection
            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            
            self._connected = True
            return True
            
        except Exception as e:
            print(f"Failed to connect to PostgreSQL: {e}")
            self._connected = False
            return False
    
    async def disconnect(self) -> bool:
        """
        Disconnect from PostgreSQL database
        
        Returns:
            bool: True if disconnection successful
        """
        try:
            if self.engine:
                await self.engine.dispose()
            self._connected = False
            return True
        except Exception as e:
            print(f"Failed to disconnect from PostgreSQL: {e}")
            return False
    
    async def is_connected(self) -> bool:
        """
        Check if connected to PostgreSQL database
        
        Returns:
            bool: True if connected
        """
        if not self._connected or not self.engine:
            return False
        
        try:
            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception:
            self._connected = False
            return False
    
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
            # Convert schema to SQLAlchemy columns
            columns = []
            for column_name, column_type in schema.items():
                if column_type.lower() == "string":
                    columns.append(Column(column_name, String))
                elif column_type.lower() == "integer":
                    columns.append(Column(column_name, Integer))
                elif column_type.lower() == "datetime":
                    columns.append(Column(column_name, DateTime))
                elif column_type.lower() == "json":
                    columns.append(Column(column_name, JSON))
                elif column_type.lower() == "boolean":
                    columns.append(Column(column_name, Boolean))
                else:
                    columns.append(Column(column_name, String))
            
            # Create table
            table = Table(table_name, self.metadata, *columns)
            async with self.engine.begin() as conn:
                await conn.run_sync(self.metadata.create_all, tables=[table])
            
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
            async with self.engine.begin() as conn:
                await conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
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
        try:
            async with self.engine.begin() as conn:
                result = await conn.execute(
                    text("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = :table_name)"),
                    {"table_name": table_name}
                )
                return result.scalar()
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
            
            # Convert data to JSON-serializable format
            serialized_data = {}
            for key, value in data.items():
                if isinstance(value, datetime):
                    serialized_data[key] = value.isoformat()
                elif isinstance(value, dict):
                    serialized_data[key] = json.dumps(value)
                else:
                    serialized_data[key] = value
            
            # Build INSERT query
            columns = ", ".join(serialized_data.keys())
            placeholders = ", ".join([f":{key}" for key in serialized_data.keys()])
            query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders}) RETURNING id"
            
            async with self.engine.begin() as conn:
                result = await conn.execute(text(query), serialized_data)
                record_id = result.scalar()
                return str(record_id)
                
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
            
            # Convert data to JSON-serializable format
            serialized_data = {}
            for key, value in data.items():
                if isinstance(value, datetime):
                    serialized_data[key] = value.isoformat()
                elif isinstance(value, dict):
                    serialized_data[key] = json.dumps(value)
                else:
                    serialized_data[key] = value
            
            # Build UPDATE query
            set_clause = ", ".join([f"{key} = :{key}" for key in serialized_data.keys()])
            query = f"UPDATE {table_name} SET {set_clause} WHERE id = :record_id"
            serialized_data["record_id"] = record_id
            
            async with self.engine.begin() as conn:
                result = await conn.execute(text(query), serialized_data)
                return result.rowcount > 0
                
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
            query = f"DELETE FROM {table_name} WHERE id = :record_id"
            async with self.engine.begin() as conn:
                result = await conn.execute(text(query), {"record_id": record_id})
                return result.rowcount > 0
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
            query = f"SELECT * FROM {table_name} WHERE id = :record_id"
            async with self.engine.begin() as conn:
                result = await conn.execute(text(query), {"record_id": record_id})
                row = result.fetchone()
                if row:
                    return dict(row._mapping)
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
            # Build query
            query = f"SELECT * FROM {table_name}"
            params = {}
            
            # Add WHERE clause
            if filters:
                where_conditions = []
                for key, value in filters.items():
                    if isinstance(value, (list, tuple)):
                        placeholders = ", ".join([f":{key}_{i}" for i in range(len(value))])
                        where_conditions.append(f"{key} IN ({placeholders})")
                        for i, v in enumerate(value):
                            params[f"{key}_{i}"] = v
                    else:
                        where_conditions.append(f"{key} = :{key}")
                        params[key] = value
                
                if where_conditions:
                    query += " WHERE " + " AND ".join(where_conditions)
            
            # Add ORDER BY
            if order_by:
                query += f" ORDER BY {order_by}"
            
            # Add LIMIT and OFFSET
            if limit:
                query += f" LIMIT {limit}"
            if offset:
                query += f" OFFSET {offset}"
            
            async with self.engine.begin() as conn:
                result = await conn.execute(text(query), params)
                rows = result.fetchall()
                return [dict(row._mapping) for row in rows]
                
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
            query = f"SELECT COUNT(*) FROM {table_name}"
            params = {}
            
            if filters:
                where_conditions = []
                for key, value in filters.items():
                    if isinstance(value, (list, tuple)):
                        placeholders = ", ".join([f":{key}_{i}" for i in range(len(value))])
                        where_conditions.append(f"{key} IN ({placeholders})")
                        for i, v in enumerate(value):
                            params[f"{key}_{i}"] = v
                    else:
                        where_conditions.append(f"{key} = :{key}")
                        params[key] = value
                
                if where_conditions:
                    query += " WHERE " + " AND ".join(where_conditions)
            
            async with self.engine.begin() as conn:
                result = await conn.execute(text(query), params)
                return result.scalar()
                
        except Exception as e:
            print(f"Failed to count records in table {table_name}: {e}")
            return 0
    
    async def execute_raw(self, query: str, params: Dict[str, Any] = None) -> Any:
        """
        Execute raw query
        
        Args:
            query: Raw query string
            params: Query parameters
            
        Returns:
            Any: Query result
        """
        try:
            async with self.engine.begin() as conn:
                result = await conn.execute(text(query), params or {})
                return result
        except Exception as e:
            print(f"Failed to execute raw query: {e}")
            raise
    
    async def begin_transaction(self) -> Any:
        """
        Begin database transaction
        
        Returns:
            Any: Transaction object
        """
        try:
            return await self.engine.begin()
        except Exception as e:
            print(f"Failed to begin transaction: {e}")
            raise
    
    async def commit_transaction(self, transaction: Any) -> bool:
        """
        Commit transaction
        
        Args:
            transaction: Transaction object
            
        Returns:
            bool: True if commit successful
        """
        try:
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
            start_time = datetime.utcnow()
            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            end_time = datetime.utcnow()
            
            return {
                "status": "healthy",
                "connected": True,
                "response_time_ms": (end_time - start_time).total_seconds() * 1000,
                "backend_type": "postgresql",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e),
                "backend_type": "postgresql",
                "timestamp": datetime.utcnow().isoformat()
            }
