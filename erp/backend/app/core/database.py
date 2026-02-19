"""
Database connection and management.
"""

import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings

logger = logging.getLogger(__name__)


class MongoDB:
    """MongoDB singleton connection manager."""

    client: AsyncIOMotorClient = None
    database: AsyncIOMotorDatabase = None

    @classmethod
    def get_database(cls) -> AsyncIOMotorDatabase:
        """
        Get MongoDB database instance.

        Returns:
            AsyncIOMotorDatabase: Database instance

        Raises:
            RuntimeError: If database is not initialized
        """
        if cls.database is None:
            raise RuntimeError(
                "Database not initialized. Call connect_databases() first."
            )
        return cls.database


async def connect_databases():
    """
    Connect to MongoDB.

    Initializes the MongoDB connection and creates database indexes.
    """
    logger.info("Connecting to MongoDB...")
    try:
        MongoDB.client = AsyncIOMotorClient(settings.MONGODB_URL)
        MongoDB.database = MongoDB.client[settings.MONGODB_DATABASE]

        # Verify connection
        await MongoDB.client.admin.command("ping")
        logger.info(f"✅ Connected to MongoDB database: {settings.MONGODB_DATABASE}")
    except Exception as e:
        logger.error(f"✗ Failed to connect to MongoDB: {e}")
        raise


async def disconnect_databases():
    """Disconnect from MongoDB."""
    if MongoDB.client:
        MongoDB.client.close()
        logger.info("Disconnected from MongoDB")
