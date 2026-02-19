"""
Storage Backend Interfaces

This module defines the core storage backend interfaces used by all shared libraries.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field


class StorageConfig(BaseModel):
    """Storage configuration"""
    backend_type: str = Field(..., description="Storage backend type")
    connection_string: Optional[str] = Field(None, description="Connection string")
    host: Optional[str] = Field(None, description="Host address")
    port: Optional[int] = Field(None, description="Port number")
    database: Optional[str] = Field(None, description="Database name")
    username: Optional[str] = Field(None, description="Username")
    password: Optional[str] = Field(None, description="Password")
    ssl_mode: Optional[str] = Field("prefer", description="SSL mode")
    pool_size: int = Field(10, description="Connection pool size")
    max_overflow: int = Field(20, description="Maximum overflow connections")
    timeout: int = Field(30, description="Connection timeout in seconds")
    retry_attempts: int = Field(3, description="Number of retry attempts")
    retry_delay: float = Field(1.0, description="Delay between retries in seconds")


class StorageBackend(ABC):
    """Abstract storage backend interface"""
    
    def __init__(self, config: StorageConfig):
        self.config = config
        self._connected = False
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Connect to storage backend
        
        Returns:
            bool: True if connection successful
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Disconnect from storage backend
        
        Returns:
            bool: True if disconnection successful
        """
        pass
    
    @abstractmethod
    async def is_connected(self) -> bool:
        """
        Check if connected to storage backend
        
        Returns:
            bool: True if connected
        """
        pass
    
    @abstractmethod
    async def create_table(self, table_name: str, schema: Dict[str, str]) -> bool:
        """
        Create table with schema
        
        Args:
            table_name: Name of table to create
            schema: Column definitions (name: type)
            
        Returns:
            bool: True if table created successfully
        """
        pass
    
    @abstractmethod
    async def drop_table(self, table_name: str) -> bool:
        """
        Drop table
        
        Args:
            table_name: Name of table to drop
            
        Returns:
            bool: True if table dropped successfully
        """
        pass
    
    @abstractmethod
    async def table_exists(self, table_name: str) -> bool:
        """
        Check if table exists
        
        Args:
            table_name: Name of table to check
            
        Returns:
            bool: True if table exists
        """
        pass
    
    @abstractmethod
    async def insert(self, table_name: str, data: Dict[str, Any]) -> str:
        """
        Insert data into table
        
        Args:
            table_name: Name of table
            data: Data to insert
            
        Returns:
            str: ID of inserted record
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def delete(self, table_name: str, record_id: str) -> bool:
        """
        Delete record from table
        
        Args:
            table_name: Name of table
            record_id: ID of record to delete
            
        Returns:
            bool: True if delete successful
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, table_name: str, record_id: str) -> Optional[Dict[str, Any]]:
        """
        Get record by ID
        
        Args:
            table_name: Name of table
            record_id: ID of record
            
        Returns:
            Optional[Dict[str, Any]]: Record data if found
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def count(self, table_name: str, filters: Dict[str, Any] = None) -> int:
        """
        Count records in table
        
        Args:
            table_name: Name of table
            filters: Filter conditions
            
        Returns:
            int: Number of records
        """
        pass
    
    @abstractmethod
    async def execute_raw(self, query: str, params: Dict[str, Any] = None) -> Any:
        """
        Execute raw query
        
        Args:
            query: Raw query string
            params: Query parameters
            
        Returns:
            Any: Query result
        """
        pass
    
    @abstractmethod
    async def begin_transaction(self) -> Any:
        """
        Begin database transaction
        
        Returns:
            Any: Transaction object
        """
        pass
    
    @abstractmethod
    async def commit_transaction(self, transaction: Any) -> bool:
        """
        Commit transaction
        
        Args:
            transaction: Transaction object
            
        Returns:
            bool: True if commit successful
        """
        pass
    
    @abstractmethod
    async def rollback_transaction(self, transaction: Any) -> bool:
        """
        Rollback transaction
        
        Args:
            transaction: Transaction object
            
        Returns:
            bool: True if rollback successful
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check
        
        Returns:
            Dict[str, Any]: Health check results
        """
        pass
