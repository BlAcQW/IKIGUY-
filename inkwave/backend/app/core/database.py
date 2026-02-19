"""
Database connection and utilities.

Manages MongoDB connection for InkWave application.
"""

import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings

logger = logging.getLogger(__name__)


class Database:
    """
    MongoDB database connection manager.

    Singleton pattern for managing database connections.
    """

    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

    @classmethod
    async def connect(cls):
        """
        Connect to MongoDB database.

        Raises:
            Exception: If connection fails
        """
        try:
            logger.info(f"Connecting to MongoDB: {settings.MONGODB_URI}")
            logger.info(f"Database name: {settings.MONGODB_DB_NAME}")

            # Optimized connection pool for high concurrency (5000+ users)
            cls.client = AsyncIOMotorClient(
                settings.MONGODB_URI,
                maxPoolSize=200,           # Max connections per worker (16 workers × 200 = 3200 total)
                minPoolSize=20,            # Keep 20 connections warm per worker
                maxIdleTimeMS=45000,       # Close idle connections after 45 seconds
                serverSelectionTimeoutMS=10000,  # 10s timeout for server selection
                connectTimeoutMS=10000,    # 10s timeout for initial connection
                socketTimeoutMS=45000,     # 45s socket timeout
                retryWrites=True,          # Auto-retry failed writes
                retryReads=True,           # Auto-retry failed reads
                w='majority',              # Write concern: wait for majority
                journal=True,              # Wait for journal sync (durability)
            )
            logger.info("✅ Client created with optimized connection pool (maxPoolSize=200, minPoolSize=20)")

            cls.db = cls.client[settings.MONGODB_DB_NAME]
            logger.info(f"✅ Database object created: {type(cls.db)}")

            # Test connection
            await cls.client.admin.command("ping")
            logger.info(f"✅ Connected to MongoDB database: {settings.MONGODB_DB_NAME}")

            # Create indexes
            await cls.create_indexes()

        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise

    @classmethod
    async def disconnect(cls):
        """Close MongoDB connection."""
        if cls.client is not None:
            cls.client.close()
            logger.info("MongoDB connection closed")

    @classmethod
    async def create_indexes(cls):
        """
        Create database indexes for optimal performance.

        Indexes:
        - books: book_id (unique), title, author
        - users: user_id (unique), email, username (unique), text search
        - provider_configs: provider_type, provider_id (compound unique)
        - book_chunks: book_id, chunk_index (compound)
        - reading_sessions: user_id, book_id (compound)
        - interactions: user_id, session_id
        - usage_logs: user_id, timestamp
        - user_follows: follower/following (compound unique), status
        - reading_activity: user_id, created_at, book_id
        - user_blocks: blocker/blocked (compound unique)
        - user_reports: reported_user_id, status, created_at
        """
        if cls.db is None:
            logger.warning("Cannot create indexes: database not connected")
            return

        try:
            # Books collection
            await cls.db.books.create_index("book_id", unique=True)
            await cls.db.books.create_index("title")
            await cls.db.books.create_index("author")
            await cls.db.books.create_index("processing_status")
            await cls.db.books.create_index("created_at")

            # Book chunks collection
            await cls.db.book_chunks.create_index([("book_id", 1), ("chunk_index", 1)], unique=True)
            await cls.db.book_chunks.create_index("book_id")

            # Users collection
            await cls.db.users.create_index("user_id", unique=True)
            await cls.db.users.create_index("email", unique=True)
            # Social features indexes for users
            # Safety check: Drop username index if it exists but is not sparse
            # This prevents E11000 duplicate key errors when multiple users have no username
            try:
                existing_indexes = await cls.db.users.index_information()
                if 'username_1' in existing_indexes:
                    if not existing_indexes['username_1'].get('sparse', False):
                        logger.warning("⚠️ Found non-sparse username index, dropping and recreating...")
                        await cls.db.users.drop_index('username_1')
                        logger.info("✅ Dropped non-sparse username index")
            except Exception as e:
                logger.warning(f"⚠️ Could not check/fix username index: {e}")

            await cls.db.users.create_index("username", unique=True, sparse=True)  # Sparse to allow nulls
            await cls.db.users.create_index([("display_name", "text"), ("username", "text")])  # Text search

            # User follows collection (social features)
            await cls.db.user_follows.create_index(
                [("follower_user_id", 1), ("following_user_id", 1)], unique=True
            )
            await cls.db.user_follows.create_index("following_user_id")
            await cls.db.user_follows.create_index("follower_user_id")
            await cls.db.user_follows.create_index("status")

            # Reading activity collection (social features)
            await cls.db.reading_activity.create_index([("user_id", 1), ("created_at", -1)])
            await cls.db.reading_activity.create_index([("created_at", -1)])
            await cls.db.reading_activity.create_index("book_id")
            await cls.db.reading_activity.create_index("visibility")

            # User blocks collection (social features)
            await cls.db.user_blocks.create_index(
                [("blocker_user_id", 1), ("blocked_user_id", 1)], unique=True
            )
            await cls.db.user_blocks.create_index("blocked_user_id")

            # User reports collection (social features)
            await cls.db.user_reports.create_index([("reported_user_id", 1), ("status", 1)])
            await cls.db.user_reports.create_index("status")
            await cls.db.user_reports.create_index([("created_at", -1)])

            # Book clubs collection (social features)
            await cls.db.book_clubs.create_index("club_id", unique=True)
            await cls.db.book_clubs.create_index("book_id")
            await cls.db.book_clubs.create_index("creator_user_id")
            await cls.db.book_clubs.create_index("visibility")
            await cls.db.book_clubs.create_index([("archived", 1), ("created_at", -1)])
            await cls.db.book_clubs.create_index([("name", "text"), ("description", "text")])  # Text search

            # Club members collection
            await cls.db.club_members.create_index("membership_id", unique=True)
            await cls.db.club_members.create_index([("club_id", 1), ("user_id", 1), ("status", 1)])
            await cls.db.club_members.create_index("user_id")
            await cls.db.club_members.create_index("club_id")
            await cls.db.club_members.create_index("status")
            await cls.db.club_members.create_index([("club_id", 1), ("joined_at", -1)])

            # Club invitations collection
            await cls.db.club_invitations.create_index("invitation_id", unique=True)
            await cls.db.club_invitations.create_index("invitation_token", unique=True)
            await cls.db.club_invitations.create_index([("club_id", 1), ("status", 1)])
            await cls.db.club_invitations.create_index("invited_user_id")
            await cls.db.club_invitations.create_index("invited_email")
            await cls.db.club_invitations.create_index("status")
            await cls.db.club_invitations.create_index("expires_at")

            # Club discussions collection
            await cls.db.club_discussions.create_index("discussion_id", unique=True)
            await cls.db.club_discussions.create_index([("club_id", 1), ("created_at", -1)])
            await cls.db.club_discussions.create_index("user_id")
            await cls.db.club_discussions.create_index("reply_to_discussion_id")
            await cls.db.club_discussions.create_index([("club_id", 1), ("chapter_reference", 1)])
            await cls.db.club_discussions.create_index("deleted_at")

            # Provider configs collection
            await cls.db.provider_configs.create_index(
                [("provider_type", 1), ("provider_id", 1)], unique=True
            )
            await cls.db.provider_configs.create_index("provider_type")
            await cls.db.provider_configs.create_index("enabled")

            # Reading sessions collection
            await cls.db.reading_sessions.create_index([("user_id", 1), ("book_id", 1)])
            await cls.db.reading_sessions.create_index("user_id")
            await cls.db.reading_sessions.create_index("last_accessed")
            await cls.db.reading_sessions.create_index([("user_id", 1), ("completed", 1)])  # For active session queries
            await cls.db.reading_sessions.create_index([("updated_at", -1)])  # For recent activity

            # Interactions collection
            await cls.db.interactions.create_index("user_id")
            await cls.db.interactions.create_index("session_id")
            await cls.db.interactions.create_index("created_at")

            # Usage logs collection
            await cls.db.usage_logs.create_index("user_id")
            await cls.db.usage_logs.create_index("timestamp")
            await cls.db.usage_logs.create_index([("user_id", 1), ("timestamp", -1)])

            # Consumption events collection (unified activity tracking)
            await cls.db.consumption_events.create_index("event_id", unique=True)
            await cls.db.consumption_events.create_index([("user_id", 1), ("timestamp", -1)])
            await cls.db.consumption_events.create_index([("book_id", 1), ("timestamp", -1)])
            await cls.db.consumption_events.create_index([("session_id", 1), ("timestamp", 1)])
            await cls.db.consumption_events.create_index("event_type")
            await cls.db.consumption_events.create_index("consumption_mode")
            await cls.db.consumption_events.create_index([("user_id", 1), ("book_id", 1)])
            await cls.db.consumption_events.create_index([("timestamp", -1)])

            logger.info("✅ Database indexes created successfully")

        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            # Don't raise - indexes are optimization, not critical

    @classmethod
    def get_database(cls) -> AsyncIOMotorDatabase:
        """
        Get database instance.

        Returns:
            MongoDB database instance

        Raises:
            RuntimeError: If database not connected
        """
        if cls.db is None:
            raise RuntimeError("Database not connected. Call Database.connect() first.")
        return cls.db


# Convenience function
def get_db() -> AsyncIOMotorDatabase:
    """
    Get database instance for dependency injection.

    Returns:
        MongoDB database instance
    """
    return Database.get_database()
