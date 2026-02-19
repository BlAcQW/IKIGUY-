"""
Database connection and management for African Language Community Platform.

Handles MongoDB connection, collections, and database operations using Motor async driver.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ServerSelectionTimeoutError
import logging
from typing import Optional

from core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Global database instances
mongodb_client: Optional[AsyncIOMotorClient] = None
mongodb: Optional[AsyncIOMotorDatabase] = None


async def connect_to_mongo():
    """
    Create database connection and initialize collections.

    Establishes connection to MongoDB and sets up required indexes.
    """
    global mongodb_client, mongodb

    try:
        # Create MongoDB client
        mongodb_client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            serverSelectionTimeoutMS=5000
        )

        # Test the connection
        await mongodb_client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")

        # Get database
        mongodb = mongodb_client[settings.DATABASE_NAME]

        # Initialize collections and indexes
        await initialize_database()
        logger.info("Database initialization completed")

    except ServerSelectionTimeoutError:
        logger.error("Failed to connect to MongoDB - timeout")
        raise
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise


async def close_mongo_connection():
    """
    Close database connection.

    Properly closes MongoDB connection when application shuts down.
    """
    global mongodb_client, mongodb

    if mongodb_client:
        mongodb_client.close()
        logger.info("Disconnected from MongoDB")


async def initialize_database():
    """
    Initialize database collections and create indexes for performance.

    Creates required indexes for efficient querying and ensures database schema.
    """
    if mongodb is None:
        raise RuntimeError("Database not connected")

    # Language families collection indexes
    await mongodb.language_families.create_index([("name", 1)], unique=True)
    await mongodb.language_families.create_index([("created_at", -1)])

    # Language subfamilies collection indexes
    await mongodb.language_subfamilies.create_index([("family_id", 1), ("name", 1)])
    await mongodb.language_subfamilies.create_index([("created_at", -1)])

    # Languages collection indexes
    await mongodb.languages.create_index([("code", 1)], unique=True)
    await mongodb.languages.create_index([("subfamily_id", 1)])
    await mongodb.languages.create_index([("name", 1)])

    # Users collection indexes
    await mongodb.users.create_index([("email", 1)], unique=True)
    await mongodb.users.create_index([("supabase_id", 1)], unique=True)
    await mongodb.users.create_index([("username", 1)], unique=True, sparse=True)
    await mongodb.users.create_index([("language_expertise", 1)])
    await mongodb.users.create_index([("level", 1)])
    await mongodb.users.create_index([("total_points", -1)])

    # Submissions collection indexes
    await mongodb.submissions.create_index([("contributor_id", 1)])
    await mongodb.submissions.create_index([("language_code", 1)])
    await mongodb.submissions.create_index([("tier", 1)])
    await mongodb.submissions.create_index([("validation_status", 1)])
    await mongodb.submissions.create_index([("type", 1)])
    await mongodb.submissions.create_index([("created_at", -1)])
    await mongodb.submissions.create_index([
        ("language_code", 1), ("tier", 1), ("validation_status", 1)
    ])

    # Validations collection indexes
    await mongodb.validations.create_index([("submission_id", 1)])
    await mongodb.validations.create_index([("validator_id", 1)])
    await mongodb.validations.create_index([("created_at", -1)])
    await mongodb.validations.create_index([
        ("submission_id", 1), ("validator_id", 1)
    ], unique=True)

    # User achievements collection indexes
    await mongodb.user_achievements.create_index([("user_id", 1)])
    await mongodb.user_achievements.create_index([("achievement_type", 1)])
    await mongodb.user_achievements.create_index([("awarded_at", -1)])

    # Community proposals collection indexes
    await mongodb.community_proposals.create_index([("proposer_id", 1)])
    await mongodb.community_proposals.create_index([("status", 1)])
    await mongodb.community_proposals.create_index([("voting_deadline", 1)])
    await mongodb.community_proposals.create_index([("created_at", -1)])

    # Community votes collection indexes
    await mongodb.community_votes.create_index([("proposal_id", 1)])
    await mongodb.community_votes.create_index([("voter_id", 1)])
    await mongodb.community_votes.create_index([
        ("proposal_id", 1), ("voter_id", 1)
    ], unique=True)

    # Family shared resources collection indexes
    await mongodb.family_shared_resources.create_index([("family_id", 1)])
    await mongodb.family_shared_resources.create_index([("resource_type", 1)])
    await mongodb.family_shared_resources.create_index([("contributors", 1)])

    logger.info("Database indexes created successfully")


def get_database() -> AsyncIOMotorDatabase:
    """
    Get the current database instance.

    Returns:
        AsyncIOMotorDatabase: The MongoDB database instance

    Raises:
        RuntimeError: If database is not connected
    """
    if mongodb is None:
        raise RuntimeError("Database not connected")
    return mongodb


# Collection getters for easy access
async def get_collection(name: str):
    """
    Get a specific collection from the database.

    Args:
        name (str): Collection name

    Returns:
        Collection: MongoDB collection instance

    Raises:
        RuntimeError: If database is not connected
    """
    db = get_database()
    return db[name]