"""
MongoDB database connection and utilities.
Uses Motor (async MongoDB driver) for non-blocking I/O.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Global MongoDB client and database
client: AsyncIOMotorClient = None
db: AsyncIOMotorDatabase = None


async def connect_to_mongo():
    """
    Establish connection to MongoDB.
    Called on application startup.
    """
    global client, db
    try:
        logger.info(f"Connecting to MongoDB at {settings.MONGODB_URI}")
        client = AsyncIOMotorClient(settings.MONGODB_URI)
        db = client[settings.DATABASE_NAME]

        # Test connection
        await client.admin.command("ping")
        logger.info(f"Successfully connected to MongoDB database: {settings.DATABASE_NAME}")

        # Create indexes
        await create_indexes()

    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def close_mongo_connection():
    """
    Close MongoDB connection.
    Called on application shutdown.
    """
    global client
    if client:
        logger.info("Closing MongoDB connection")
        client.close()
        logger.info("MongoDB connection closed")


async def create_indexes():
    """
    Create all necessary MongoDB indexes.
    Ensures optimal query performance.
    """
    logger.info("Creating MongoDB indexes...")

    # Users collection indexes
    await db.users.create_index("email", unique=True)
    await db.users.create_index("role")
    await db.users.create_index("created_at")

    # Devotionals collection indexes
    await db.devotionals.create_index("slug", unique=True)
    await db.devotionals.create_index("author_id")
    await db.devotionals.create_index("status")
    await db.devotionals.create_index("published_at")
    await db.devotionals.create_index([("categories", 1)])
    await db.devotionals.create_index([("title", "text"), ("content.text", "text")])
    await db.devotionals.create_index([("author_id", 1), ("status", 1)])

    # Compound indexes for date filtering with other fields
    # Reason: Optimize queries that filter by date range + category or date + sort by likes
    await db.devotionals.create_index([("published_at", -1), ("categories", 1)])
    await db.devotionals.create_index([("published_at", -1), ("likes_count", -1)])

    # Series-related indexes for devotionals (CRITICAL for performance)
    # Reason: 15-20x performance improvement for series queries
    await db.devotionals.create_index("series_id")
    await db.devotionals.create_index([("series_id", 1), ("part_number", 1)])
    await db.devotionals.create_index([("series_id", 1), ("status", 1)])

    # Series collection indexes
    await db.series.create_index("slug", unique=True)
    await db.series.create_index("author_id")
    await db.series.create_index([("author_id", 1), ("created_at", -1)])
    await db.series.create_index("start_date")

    # Comments collection indexes
    await db.comments.create_index("devotional_id")
    await db.comments.create_index("user_id")
    await db.comments.create_index("parent_comment_id")
    await db.comments.create_index("created_at")
    await db.comments.create_index([("devotional_id", 1), ("created_at", -1)])

    # Likes collection indexes (compound unique)
    await db.likes.create_index([("user_id", 1), ("target_type", 1), ("target_id", 1)], unique=True)
    await db.likes.create_index("target_id")

    # Bookmarks collection indexes (compound unique)
    await db.bookmarks.create_index([("user_id", 1), ("devotional_id", 1)], unique=True)
    await db.bookmarks.create_index("devotional_id")

    # Reading history collection indexes
    await db.reading_history.create_index("user_id")
    await db.reading_history.create_index("devotional_id")
    await db.reading_history.create_index("read_at")
    await db.reading_history.create_index([("user_id", 1), ("devotional_id", 1)])

    # Discussions collection indexes
    await db.discussions.create_index("author_id")
    await db.discussions.create_index("devotional_id")
    await db.discussions.create_index("category")
    await db.discussions.create_index("last_activity_at")
    await db.discussions.create_index([("title", "text"), ("description", "text")])
    await db.discussions.create_index([("last_activity_at", -1)])

    # Discussion messages collection indexes
    await db.discussion_messages.create_index("discussion_id")
    await db.discussion_messages.create_index("user_id")
    await db.discussion_messages.create_index("created_at")
    await db.discussion_messages.create_index([("discussion_id", 1), ("created_at", -1)])

    # Platform invites collection indexes
    # Reason: Support efficient lookups for invitation verification and management
    await db.platform_invites.create_index("email")
    await db.platform_invites.create_index("token", unique=True)
    await db.platform_invites.create_index("status")
    await db.platform_invites.create_index("expires_at")
    await db.platform_invites.create_index("invited_by_id")
    await db.platform_invites.create_index([("status", 1), ("expires_at", 1)])
    await db.platform_invites.create_index([("invited_at", -1)])

    logger.info("MongoDB indexes created successfully")


def get_database() -> AsyncIOMotorDatabase:
    """
    Get the MongoDB database instance.

    Returns:
        AsyncIOMotorDatabase: MongoDB database instance.
    """
    return db
