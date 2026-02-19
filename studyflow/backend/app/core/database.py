"""
Database connection management for StudyFlow.

Manages connections to MongoDB (main database) and PostgreSQL (pgvector for RAG).
"""

import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import asynccontextmanager

from app.config import settings

logger = logging.getLogger(__name__)


class MongoDB:
    """
    MongoDB connection manager.

    Handles async connections to MongoDB for user data, sessions, etc.
    """

    client: Optional[AsyncIOMotorClient] = None
    database: Optional[AsyncIOMotorDatabase] = None

    @classmethod
    async def connect(cls):
        """
        Connect to MongoDB.

        Establishes connection and creates database instance.
        """
        try:
            cls.client = AsyncIOMotorClient(settings.MONGODB_URL)
            cls.database = cls.client[settings.MONGODB_DATABASE]

            # Test connection
            await cls.client.admin.command('ping')
            logger.info(f"✓ Connected to MongoDB: {settings.MONGODB_DATABASE}")

        except Exception as e:
            logger.error(f"✗ Failed to connect to MongoDB: {str(e)}")
            raise

    @classmethod
    async def disconnect(cls):
        """Disconnect from MongoDB."""
        if cls.client:
            cls.client.close()
            logger.info("✓ Disconnected from MongoDB")

    @classmethod
    def get_database(cls) -> AsyncIOMotorDatabase:
        """
        Get MongoDB database instance.

        Returns:
            AsyncIOMotorDatabase instance

        Raises:
            RuntimeError: If database is not connected
        """
        if cls.database is None:
            raise RuntimeError("MongoDB not connected. Call connect() first.")
        return cls.database

    @classmethod
    def get_collection(cls, collection_name: str):
        """
        Get a MongoDB collection.

        Args:
            collection_name: Name of the collection

        Returns:
            Collection instance
        """
        db = cls.get_database()
        return db[collection_name]


class PostgreSQL:
    """
    PostgreSQL connection manager.

    Handles connections to PostgreSQL with pgvector for RAG embeddings.
    """

    connection_string: Optional[str] = None

    @classmethod
    def initialize(cls):
        """Initialize PostgreSQL connection string."""
        cls.connection_string = settings.postgres_connection_string
        logger.info(f"✓ PostgreSQL connection configured: {settings.POSTGRES_HOST}")

    @classmethod
    def get_connection(cls):
        """
        Get a PostgreSQL connection.

        Returns:
            psycopg2 connection

        Raises:
            RuntimeError: If connection string is not initialized
        """
        if cls.connection_string is None:
            raise RuntimeError("PostgreSQL not initialized. Call initialize() first.")

        try:
            conn = psycopg2.connect(
                cls.connection_string,
                cursor_factory=RealDictCursor
            )
            return conn
        except Exception as e:
            logger.error(f"✗ Failed to connect to PostgreSQL: {str(e)}")
            raise

    @classmethod
    @asynccontextmanager
    async def get_async_connection(cls):
        """
        Get an async PostgreSQL connection context.

        Usage:
            async with PostgreSQL.get_async_connection() as conn:
                # Use conn
        """
        conn = cls.get_connection()
        try:
            yield conn
        finally:
            conn.close()


# Global database instances
mongodb = MongoDB()
postgresql = PostgreSQL()


async def connect_databases():
    """
    Connect to all databases.

    Called during application startup.
    """
    logger.info("Connecting to databases...")

    # Connect MongoDB
    await mongodb.connect()

    # Initialize PostgreSQL
    postgresql.initialize()

    # Test PostgreSQL connection
    try:
        conn = postgresql.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        logger.info("✓ PostgreSQL connection test successful")
    except Exception as e:
        logger.warning(f"⚠ PostgreSQL connection test failed: {str(e)}")
        logger.warning("RAG features may not work without PostgreSQL/pgvector")

    logger.info("✓ All databases connected")


async def disconnect_databases():
    """
    Disconnect from all databases.

    Called during application shutdown.
    """
    logger.info("Disconnecting from databases...")
    await mongodb.disconnect()
    logger.info("✓ All databases disconnected")


# Collection names (constants)
COLLECTION_USERS = "users"
COLLECTION_SESSIONS = "sessions"
COLLECTION_QUESTIONS = "questions"
COLLECTION_PROGRESS = "progress"
COLLECTION_WALLETS = "wallets"
COLLECTION_TRANSACTIONS = "transactions"
COLLECTION_MATERIALS = "materials"
COLLECTION_EXERCISES = "exercises"
