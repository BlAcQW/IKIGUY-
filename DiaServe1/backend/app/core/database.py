"""
Database connection and initialization.

Handles MongoDB connections and database operations.
"""

import logging
import ssl
import certifi
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


class MongoDB:
    """MongoDB database connection manager."""

    client: Optional[AsyncIOMotorClient] = None
    db = None
    gridfs_bucket: Optional[AsyncIOMotorGridFSBucket] = None

    @classmethod
    async def connect(cls):
        """
        Connect to MongoDB.

        Establishes connection to MongoDB database and creates necessary indexes.
        """
        try:
            # Use Python's built-in ssl module with certifi CA bundle
            # to avoid pyOpenSSL compatibility issues
            tls_ctx = ssl.create_default_context(cafile=certifi.where())
            cls.client = AsyncIOMotorClient(settings.MONGODB_URL, tls=True, tlsCAFile=certifi.where())
            cls.db = cls.client[settings.MONGODB_DB_NAME]
            # Test connection
            await cls.client.admin.command('ping')
            logger.info(f"Connected to MongoDB database: {settings.MONGODB_DB_NAME}")

            # Create text index on properties collection
            properties_collection = cls.db["properties"]

            # Check if text index exists
            indexes = await properties_collection.list_indexes().to_list(length=100)
            has_text_index = any(
                idx.get("key", {}).get("_fts") == "text"
                for idx in indexes
            )

            if not has_text_index:
                # Create text index on name and description
                await properties_collection.create_index([
                    ("name", "text"),
                    ("description", "text")
                ], name="property_text_search")
                logger.info("Created text index on properties.name and properties.description")
            else:
                logger.info("Text index already exists on properties collection")

            # Initialize GridFS bucket
            cls.gridfs_bucket = AsyncIOMotorGridFSBucket(cls.db)
            logger.info("GridFS bucket initialized")

            # Create indexes for property_images collection
            await cls._create_image_indexes()

        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise

    @classmethod
    async def _create_image_indexes(cls):
        """
        Create indexes for property_images collection.

        Creates indexes for efficient querying of image metadata.
        """
        images_collection = cls.db["property_images"]

        # Index for querying images by property_id and order
        await images_collection.create_index([("property_id", 1), ("order", 1)])
        logger.info("Created index on property_images.property_id and order")

        # Unique index for file_id
        await images_collection.create_index([("file_id", 1)], unique=True)
        logger.info("Created unique index on property_images.file_id")

        # Index for organization filtering
        await images_collection.create_index([("organization_id", 1)])
        logger.info("Created index on property_images.organization_id")

    @classmethod
    async def disconnect(cls):
        """
        Disconnect from MongoDB.

        Closes MongoDB connection.
        """
        if cls.client:
            cls.client.close()
            logger.info("Disconnected from MongoDB")

    @classmethod
    def get_db(cls):
        """
        Get database instance.

        Returns:
            Database instance

        Raises:
            RuntimeError: If database not connected
        """
        if cls.db is None:
            raise RuntimeError("Database not connected")
        return cls.db

    @classmethod
    def get_gridfs_bucket(cls) -> AsyncIOMotorGridFSBucket:
        """
        Get GridFS bucket instance.

        Returns:
            AsyncIOMotorGridFSBucket: GridFS bucket for file storage

        Raises:
            RuntimeError: If GridFS bucket not initialized
        """
        if cls.gridfs_bucket is None:
            raise RuntimeError("GridFS bucket not initialized")
        return cls.gridfs_bucket


async def connect_databases():
    """
    Connect to all databases.

    Initializes database connections.
    """
    await MongoDB.connect()


async def disconnect_databases():
    """
    Disconnect from all databases.

    Closes all database connections.
    """
    await MongoDB.disconnect()


async def get_database():
    """
    Get database instance for dependency injection.

    Returns:
        Database instance

    Raises:
        RuntimeError: If database not connected
    """
    return MongoDB.get_db()

