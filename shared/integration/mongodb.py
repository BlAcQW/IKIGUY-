"""
MongoDB Integration Module

This module provides integration with MongoDB for document database operations,
data management, and NoSQL database capabilities.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

try:
    import pymongo
    from pymongo import MongoClient, ASCENDING, DESCENDING
    from pymongo.errors import PyMongoError
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    logging.warning("MongoDB APIs not available. Install pymongo")

logger = logging.getLogger(__name__)


class MongoDBOperationType(Enum):
    """MongoDB operation types."""
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    FIND = "find"
    AGGREGATE = "aggregate"
    CREATE_INDEX = "create_index"
    DROP_INDEX = "drop_index"


class MongoDBIndexType(Enum):
    """MongoDB index types."""
    SINGLE = "single"
    COMPOUND = "compound"
    TEXT = "text"
    GEOSPATIAL = "geospatial"
    HASHED = "hashed"


@dataclass
class MongoDBConfig:
    """Configuration for MongoDB integration."""
    
    connection_string: str
    """MongoDB connection string."""
    
    database_name: str
    """Database name."""
    
    username: Optional[str] = None
    """Database username."""
    
    password: Optional[str] = None
    """Database password."""
    
    auth_source: str = "admin"
    """Authentication source."""
    
    auth_mechanism: str = "SCRAM-SHA-256"
    """Authentication mechanism."""
    
    max_pool_size: int = 100
    """Maximum connection pool size."""
    
    min_pool_size: int = 0
    """Minimum connection pool size."""
    
    max_idle_time_ms: int = 30000
    """Maximum idle time in milliseconds."""
    
    server_selection_timeout_ms: int = 5000
    """Server selection timeout in milliseconds."""
    
    socket_timeout_ms: int = 20000
    """Socket timeout in milliseconds."""
    
    connect_timeout_ms: int = 20000
    """Connection timeout in milliseconds."""
    
    retry_writes: bool = True
    """Enable retry writes."""
    
    retry_reads: bool = True
    """Enable retry reads."""
    
    ssl: bool = False
    """Enable SSL/TLS."""
    
    ssl_cert_reqs: str = "CERT_NONE"
    """SSL certificate requirements."""


@dataclass
class MongoDBDocument:
    """MongoDB document data structure."""
    
    _id: Optional[str] = None
    """Document ID."""
    
    data: Dict[str, Any] = field(default_factory=dict)
    """Document data."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""
    
    updated_at: Optional[datetime] = None
    """Last update timestamp."""
    
    version: int = 1
    """Document version."""
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    """Document metadata."""


@dataclass
class MongoDBQuery:
    """MongoDB query data structure."""
    
    filter: Dict[str, Any] = field(default_factory=dict)
    """Query filter."""
    
    projection: Optional[Dict[str, Any]] = None
    """Query projection."""
    
    sort: Optional[List[tuple]] = None
    """Sort criteria."""
    
    limit: Optional[int] = None
    """Result limit."""
    
    skip: Optional[int] = None
    """Skip count."""
    
    hint: Optional[Dict[str, Any]] = None
    """Query hint."""


@dataclass
class MongoDBIndex:
    """MongoDB index data structure."""
    
    name: str
    """Index name."""
    
    fields: List[tuple]
    """Index fields."""
    
    index_type: MongoDBIndexType
    """Index type."""
    
    unique: bool = False
    """Unique index."""
    
    sparse: bool = False
    """Sparse index."""
    
    background: bool = True
    """Background index creation."""
    
    expire_after_seconds: Optional[int] = None
    """TTL expiration in seconds."""


@dataclass
class MongoDBStats:
    """MongoDB statistics data structure."""
    
    database_name: str
    """Database name."""
    
    collections_count: int
    """Number of collections."""
    
    data_size: int
    """Data size in bytes."""
    
    storage_size: int
    """Storage size in bytes."""
    
    indexes_size: int
    """Indexes size in bytes."""
    
    objects_count: int
    """Number of objects."""
    
    avg_obj_size: float
    """Average object size."""
    
    last_updated: Optional[datetime] = None
    """Last update timestamp."""


class MongoDBIntegration:
    """MongoDB integration for document database operations."""
    
    def __init__(self, config: MongoDBConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Build connection options
        connection_options = {
            "maxPoolSize": config.max_pool_size,
            "minPoolSize": config.min_pool_size,
            "maxIdleTimeMS": config.max_idle_time_ms,
            "serverSelectionTimeoutMS": config.server_selection_timeout_ms,
            "socketTimeoutMS": config.socket_timeout_ms,
            "connectTimeoutMS": config.connect_timeout_ms,
            "retryWrites": config.retry_writes,
            "retryReads": config.retry_reads,
            "ssl": config.ssl,
            "ssl_cert_reqs": getattr(pymongo.ssl_support, config.ssl_cert_reqs) if config.ssl else None
        }
        
        # Add authentication if provided
        if config.username and config.password:
            connection_options.update({
                "username": config.username,
                "password": config.password,
                "authSource": config.auth_source,
                "authMechanism": config.auth_mechanism
            })
        
        # Initialize MongoDB client
        self.client = MongoClient(config.connection_string, **connection_options)
        self.database = self.client[config.database_name]
        
        self.logger.info(f"Connected to MongoDB database: {config.database_name}")
    
    def get_collection(self, collection_name: str):
        """Get a MongoDB collection."""
        return self.database[collection_name]
    
    async def insert_document(
        self,
        collection_name: str,
        document: MongoDBDocument
    ) -> str:
        """
        Insert a document into a collection.
        
        Args:
            collection_name: Collection name
            document: Document to insert
            
        Returns:
            Inserted document ID
        """
        try:
            collection = self.get_collection(collection_name)
            
            # Prepare document data
            doc_data = document.data.copy()
            doc_data["created_at"] = datetime.now()
            doc_data["updated_at"] = datetime.now()
            doc_data["version"] = document.version
            doc_data["metadata"] = document.metadata
            
            if document._id:
                doc_data["_id"] = document._id
            
            result = collection.insert_one(doc_data)
            
            self.logger.info(f"Inserted document into {collection_name}: {result.inserted_id}")
            return str(result.inserted_id)
            
        except PyMongoError as e:
            self.logger.error(f"Failed to insert document into {collection_name}: {e}")
            raise
    
    async def insert_many_documents(
        self,
        collection_name: str,
        documents: List[MongoDBDocument]
    ) -> List[str]:
        """
        Insert multiple documents into a collection.
        
        Args:
            collection_name: Collection name
            documents: List of documents to insert
            
        Returns:
            List of inserted document IDs
        """
        try:
            collection = self.get_collection(collection_name)
            
            # Prepare documents data
            docs_data = []
            for document in documents:
                doc_data = document.data.copy()
                doc_data["created_at"] = datetime.now()
                doc_data["updated_at"] = datetime.now()
                doc_data["version"] = document.version
                doc_data["metadata"] = document.metadata
                
                if document._id:
                    doc_data["_id"] = document._id
                
                docs_data.append(doc_data)
            
            result = collection.insert_many(docs_data)
            
            self.logger.info(f"Inserted {len(result.inserted_ids)} documents into {collection_name}")
            return [str(doc_id) for doc_id in result.inserted_ids]
            
        except PyMongoError as e:
            self.logger.error(f"Failed to insert documents into {collection_name}: {e}")
            raise
    
    async def find_documents(
        self,
        collection_name: str,
        query: MongoDBQuery
    ) -> List[MongoDBDocument]:
        """
        Find documents in a collection.
        
        Args:
            collection_name: Collection name
            query: Query configuration
            
        Returns:
            List of found documents
        """
        try:
            collection = self.get_collection(collection_name)
            
            # Build cursor
            cursor = collection.find(
                filter=query.filter,
                projection=query.projection
            )
            
            # Apply sort
            if query.sort:
                cursor = cursor.sort(query.sort)
            
            # Apply skip and limit
            if query.skip:
                cursor = cursor.skip(query.skip)
            if query.limit:
                cursor = cursor.limit(query.limit)
            
            # Apply hint
            if query.hint:
                cursor = cursor.hint(query.hint)
            
            # Convert to documents
            documents = []
            for doc in cursor:
                document = MongoDBDocument(
                    _id=str(doc.get("_id")),
                    data={k: v for k, v in doc.items() if k not in ["_id", "created_at", "updated_at", "version", "metadata"]},
                    created_at=doc.get("created_at"),
                    updated_at=doc.get("updated_at"),
                    version=doc.get("version", 1),
                    metadata=doc.get("metadata", {})
                )
                documents.append(document)
            
            self.logger.info(f"Found {len(documents)} documents in {collection_name}")
            return documents
            
        except PyMongoError as e:
            self.logger.error(f"Failed to find documents in {collection_name}: {e}")
            raise
    
    async def find_one_document(
        self,
        collection_name: str,
        query: MongoDBQuery
    ) -> Optional[MongoDBDocument]:
        """
        Find one document in a collection.
        
        Args:
            collection_name: Collection name
            query: Query configuration
            
        Returns:
            Found document or None
        """
        try:
            collection = self.get_collection(collection_name)
            
            # Build query
            doc = collection.find_one(
                filter=query.filter,
                projection=query.projection,
                sort=query.sort,
                hint=query.hint
            )
            
            if doc:
                document = MongoDBDocument(
                    _id=str(doc.get("_id")),
                    data={k: v for k, v in doc.items() if k not in ["_id", "created_at", "updated_at", "version", "metadata"]},
                    created_at=doc.get("created_at"),
                    updated_at=doc.get("updated_at"),
                    version=doc.get("version", 1),
                    metadata=doc.get("metadata", {})
                )
                return document
            
            return None
            
        except PyMongoError as e:
            self.logger.error(f"Failed to find document in {collection_name}: {e}")
            raise
    
    async def update_document(
        self,
        collection_name: str,
        filter_query: Dict[str, Any],
        update_data: Dict[str, Any],
        upsert: bool = False
    ) -> int:
        """
        Update documents in a collection.
        
        Args:
            collection_name: Collection name
            filter_query: Filter query
            update_data: Update data
            upsert: Enable upsert
            
        Returns:
            Number of modified documents
        """
        try:
            collection = self.get_collection(collection_name)
            
            # Prepare update data
            update_data["updated_at"] = datetime.now()
            update_data["$inc"] = {"version": 1}
            
            result = collection.update_many(
                filter=filter_query,
                update={"$set": update_data},
                upsert=upsert
            )
            
            self.logger.info(f"Updated {result.modified_count} documents in {collection_name}")
            return result.modified_count
            
        except PyMongoError as e:
            self.logger.error(f"Failed to update documents in {collection_name}: {e}")
            raise
    
    async def delete_documents(
        self,
        collection_name: str,
        filter_query: Dict[str, Any]
    ) -> int:
        """
        Delete documents from a collection.
        
        Args:
            collection_name: Collection name
            filter_query: Filter query
            
        Returns:
            Number of deleted documents
        """
        try:
            collection = self.get_collection(collection_name)
            
            result = collection.delete_many(filter=filter_query)
            
            self.logger.info(f"Deleted {result.deleted_count} documents from {collection_name}")
            return result.deleted_count
            
        except PyMongoError as e:
            self.logger.error(f"Failed to delete documents from {collection_name}: {e}")
            raise
    
    async def aggregate_documents(
        self,
        collection_name: str,
        pipeline: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Aggregate documents in a collection.
        
        Args:
            collection_name: Collection name
            pipeline: Aggregation pipeline
            
        Returns:
            Aggregation results
        """
        try:
            collection = self.get_collection(collection_name)
            
            result = list(collection.aggregate(pipeline))
            
            self.logger.info(f"Aggregated {len(result)} results from {collection_name}")
            return result
            
        except PyMongoError as e:
            self.logger.error(f"Failed to aggregate documents in {collection_name}: {e}")
            raise
    
    async def create_index(
        self,
        collection_name: str,
        index: MongoDBIndex
    ) -> str:
        """
        Create an index on a collection.
        
        Args:
            collection_name: Collection name
            index: Index configuration
            
        Returns:
            Created index name
        """
        try:
            collection = self.get_collection(collection_name)
            
            # Build index specification
            index_spec = []
            for field, direction in index.fields:
                if index.index_type == MongoDBIndexType.TEXT:
                    index_spec.append((field, "text"))
                elif index.index_type == MongoDBIndexType.GEOSPATIAL:
                    index_spec.append((field, "2dsphere"))
                elif index.index_type == MongoDBIndexType.HASHED:
                    index_spec.append((field, "hashed"))
                else:
                    index_spec.append((field, ASCENDING if direction == 1 else DESCENDING))
            
            # Build index options
            index_options = {
                "unique": index.unique,
                "sparse": index.sparse,
                "background": index.background
            }
            
            if index.expire_after_seconds:
                index_options["expireAfterSeconds"] = index.expire_after_seconds
            
            result = collection.create_index(index_spec, **index_options)
            
            self.logger.info(f"Created index {result} on {collection_name}")
            return result
            
        except PyMongoError as e:
            self.logger.error(f"Failed to create index on {collection_name}: {e}")
            raise
    
    async def drop_index(
        self,
        collection_name: str,
        index_name: str
    ) -> bool:
        """
        Drop an index from a collection.
        
        Args:
            collection_name: Collection name
            index_name: Index name
            
        Returns:
            Success status
        """
        try:
            collection = self.get_collection(collection_name)
            
            collection.drop_index(index_name)
            
            self.logger.info(f"Dropped index {index_name} from {collection_name}")
            return True
            
        except PyMongoError as e:
            self.logger.error(f"Failed to drop index {index_name} from {collection_name}: {e}")
            raise
    
    async def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        Get collection statistics.
        
        Args:
            collection_name: Collection name
            
        Returns:
            Collection statistics
        """
        try:
            collection = self.get_collection(collection_name)
            
            stats = collection.stats()
            
            return {
                "collection_name": collection_name,
                "count": stats.get("count", 0),
                "size": stats.get("size", 0),
                "avg_obj_size": stats.get("avgObjSize", 0),
                "storage_size": stats.get("storageSize", 0),
                "indexes": stats.get("nindexes", 0),
                "index_size": stats.get("totalIndexSize", 0)
            }
            
        except PyMongoError as e:
            self.logger.error(f"Failed to get stats for {collection_name}: {e}")
            raise
    
    async def get_database_stats(self) -> MongoDBStats:
        """
        Get database statistics.
        
        Returns:
            Database statistics
        """
        try:
            stats = self.database.command("dbStats")
            
            return MongoDBStats(
                database_name=self.config.database_name,
                collections_count=stats.get("collections", 0),
                data_size=stats.get("dataSize", 0),
                storage_size=stats.get("storageSize", 0),
                indexes_size=stats.get("indexSize", 0),
                objects_count=stats.get("objects", 0),
                avg_obj_size=stats.get("avgObjSize", 0),
                last_updated=datetime.now()
            )
            
        except PyMongoError as e:
            self.logger.error(f"Failed to get database stats: {e}")
            raise
    
    async def list_collections(self) -> List[str]:
        """
        List all collections in the database.
        
        Returns:
            List of collection names
        """
        try:
            collections = self.database.list_collection_names()
            
            self.logger.info(f"Found {len(collections)} collections in database")
            return collections
            
        except PyMongoError as e:
            self.logger.error(f"Failed to list collections: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the MongoDB integration.
        
        Returns:
            Health check results
        """
        try:
            # Test connection by running a simple command
            result = self.database.command("ping")
            
            # Get database stats
            stats = await self.get_database_stats()
            
            return {
                "status": "healthy",
                "database_name": self.config.database_name,
                "connection": "successful",
                "collections_count": stats.collections_count,
                "data_size": stats.data_size,
                "objects_count": stats.objects_count,
                "last_checked": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_checked": datetime.now().isoformat()
            }

