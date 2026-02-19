"""
Database utilities for the African Language Community Platform
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from core.config import get_settings

settings = get_settings()

# Global database client
client: AsyncIOMotorClient = None
database: AsyncIOMotorDatabase = None

async def connect_to_mongo():
    """Connect to MongoDB"""
    global client, database
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    database = client[settings.DATABASE_NAME]

async def close_mongo_connection():
    """Close MongoDB connection"""
    global client
    if client:
        client.close()

def get_database() -> AsyncIOMotorDatabase:
    """Get database instance"""
    return database