"""
Database initialization and connection management.

Author: AI Labs Africa
Date: 2025-11-10
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import logging
from apps.drive.backend.app.core.config import settings

logger = logging.getLogger(__name__)

# Global database client and instance
_mongo_client: AsyncIOMotorClient = None
_database: AsyncIOMotorDatabase = None


async def init_db():
    """Initialize MongoDB connection."""
    global _mongo_client, _database

    try:
        _mongo_client = AsyncIOMotorClient(settings.MONGODB_URL)
        _database = _mongo_client[settings.MONGODB_DB_NAME]

        # Test connection
        await _database.command("ping")
        logger.info(f"Connected to MongoDB database: {settings.MONGODB_DB_NAME}")

        # Create indexes
        await create_indexes()

    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def close_db():
    """Close MongoDB connection."""
    global _mongo_client

    if _mongo_client:
        _mongo_client.close()
        logger.info("MongoDB connection closed")


def get_database() -> AsyncIOMotorDatabase:
    """Get database instance."""
    if _database is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _database


async def create_indexes():
    """Create database indexes for efficient queries."""
    drive_items = _database.drive_items

    # Create indexes
    await drive_items.create_index([("organization_id", 1), ("parent_id", 1)])
    await drive_items.create_index([("organization_id", 1), ("owner_id", 1)])
    await drive_items.create_index([("path", 1)])
    await drive_items.create_index([("name", "text")])
    await drive_items.create_index([("is_deleted", 1), ("deleted_at", 1)])
    await drive_items.create_index([("share_link.token", 1)])
    await drive_items.create_index([("modified_at", -1)])
    await drive_items.create_index([("created_at", -1)])

    logger.info("Database indexes created successfully")
