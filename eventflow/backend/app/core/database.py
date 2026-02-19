"""
Database connection and utilities.

Provides async MongoDB client and database instance.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
from .config import settings


class Database:
    """MongoDB database connection manager."""

    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None


db_instance = Database()


async def connect_to_mongodb():
    """Connect to MongoDB."""
    try:
        db_instance.client = AsyncIOMotorClient(settings.mongodb_url)
        db_instance.db = db_instance.client[settings.mongodb_database]

        # Test connection
        await db_instance.client.admin.command("ping")
        print(f"✅ Connected to MongoDB: {settings.mongodb_database}")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        raise


async def close_mongodb_connection():
    """Close MongoDB connection."""
    if db_instance.client:
        db_instance.client.close()
        print("✅ Closed MongoDB connection")


def get_database() -> AsyncIOMotorDatabase:
    """Get database instance."""
    if db_instance.db is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongodb() first.")
    return db_instance.db
