"""
Database connection and operations for KasaAI Documentation
"""

import os
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import logging
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

# MongoDB connection
_mongo_client: Optional[AsyncIOMotorClient] = None
_mongo_db = None


def get_mongo_client() -> AsyncIOMotorClient:
    """Get MongoDB client instance."""
    global _mongo_client

    if _mongo_client is None:
        # Get credentials from environment or use defaults
        mongo_user = os.getenv("MONGO_USER", "admin")
        mongo_password = os.getenv("MONGO_PASSWORD", "aawwER4444%")
        mongo_host = os.getenv("MONGO_HOST", "127.0.0.1")
        mongo_port = os.getenv("MONGO_PORT", "27017")

        # URL encode credentials
        encoded_user = quote_plus(mongo_user)
        encoded_password = quote_plus(mongo_password)

        # Construct MongoDB URL
        mongo_url = f"mongodb://{encoded_user}:{encoded_password}@{mongo_host}:{mongo_port}/"

        _mongo_client = AsyncIOMotorClient(mongo_url)
        logger.info(f"Connected to MongoDB at {mongo_host}:{mongo_port}")

    return _mongo_client


def get_database():
    """Get documentation database instance."""
    global _mongo_db

    if _mongo_db is None:
        client = get_mongo_client()
        _mongo_db = client["kasaai_docs"]
        logger.info("Using kasaai_docs database")

    return _mongo_db


async def init_database():
    """Initialize database collections and indexes."""
    db = get_database()

    # Create collections if they don't exist
    collections = await db.list_collection_names()

    if "users" not in collections:
        await db.create_collection("users")
        # Create indexes
        await db.users.create_index("email", unique=True)
        await db.users.create_index("supabase_id", unique=True)
        logger.info("Created users collection with indexes")

    if "document_metadata" not in collections:
        await db.create_collection("document_metadata")
        # Create indexes
        await db.document_metadata.create_index("path", unique=True)
        logger.info("Created document_metadata collection with indexes")

    # Initialize default internal documents
    default_internal_docs = [
        {
            "path": "internal/introduction",
            "visibility": "internal",
            "title": "Internal Documentation Introduction",
            "description": "Overview of internal documentation"
        },
        {
            "path": "internal/onboarding",
            "visibility": "internal",
            "title": "Developer Intern Onboarding",
            "description": "Complete onboarding guide for new developers"
        },
        {
            "path": "internal/architecture",
            "visibility": "internal",
            "title": "System Architecture",
            "description": "Detailed technical architecture"
        },
        {
            "path": "internal/deployment",
            "visibility": "internal",
            "title": "Deployment Guide",
            "description": "Server deployment procedures"
        },
        {
            "path": "internal/maintenance",
            "visibility": "internal",
            "title": "Maintenance & Operations",
            "description": "Operational procedures and troubleshooting"
        }
    ]

    for doc in default_internal_docs:
        existing = await db.document_metadata.find_one({"path": doc["path"]})
        if not existing:
            from datetime import datetime
            doc["created_at"] = datetime.utcnow()
            doc["updated_at"] = datetime.utcnow()
            await db.document_metadata.insert_one(doc)
            logger.info(f"Initialized metadata for {doc['path']}")


# User operations
async def get_user_by_id(user_id: str):
    """Get user by Supabase ID."""
    db = get_database()
    return await db.users.find_one({"supabase_id": user_id})


async def get_user_by_email(email: str):
    """Get user by email."""
    db = get_database()
    return await db.users.find_one({"email": email})


async def create_user(user_data: dict):
    """Create a new user."""
    db = get_database()
    from datetime import datetime
    user_data["created_at"] = datetime.utcnow()
    user_data["updated_at"] = datetime.utcnow()
    result = await db.users.insert_one(user_data)
    return await db.users.find_one({"_id": result.inserted_id})


async def update_user(user_id: str, update_data: dict):
    """Update user information."""
    db = get_database()
    from datetime import datetime
    update_data["updated_at"] = datetime.utcnow()
    await db.users.update_one(
        {"supabase_id": user_id},
        {"$set": update_data}
    )
    return await get_user_by_id(user_id)


async def list_users(skip: int = 0, limit: int = 100):
    """List all users."""
    db = get_database()
    cursor = db.users.find().skip(skip).limit(limit)
    return await cursor.to_list(length=limit)


async def delete_user(user_id: str):
    """Delete a user."""
    db = get_database()
    result = await db.users.delete_one({"supabase_id": user_id})
    return result.deleted_count > 0


# Document metadata operations
async def get_document_metadata(path: str):
    """Get document metadata by path."""
    db = get_database()
    return await db.document_metadata.find_one({"path": path})


async def create_document_metadata(metadata: dict):
    """Create document metadata."""
    db = get_database()
    from datetime import datetime
    metadata["created_at"] = datetime.utcnow()
    metadata["updated_at"] = datetime.utcnow()
    result = await db.document_metadata.insert_one(metadata)
    return await db.document_metadata.find_one({"_id": result.inserted_id})


async def update_document_metadata(path: str, update_data: dict):
    """Update document metadata."""
    db = get_database()
    from datetime import datetime
    update_data["updated_at"] = datetime.utcnow()
    await db.document_metadata.update_one(
        {"path": path},
        {"$set": update_data}
    )
    return await get_document_metadata(path)


async def list_document_metadata(skip: int = 0, limit: int = 100):
    """List all document metadata."""
    db = get_database()
    cursor = db.document_metadata.find().skip(skip).limit(limit)
    return await cursor.to_list(length=limit)


async def delete_document_metadata(path: str):
    """Delete document metadata."""
    db = get_database()
    result = await db.document_metadata.delete_one({"path": path})
    return result.deleted_count > 0
