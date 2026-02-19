"""
URL Shortening Service.

A centralized service for creating and managing short URLs across all applications.
Provides collision-free short code generation, analytics tracking, and expiration handling.

Used by:
- InkWave: Book sharing and invitation links
- ChurchFlow: Conference material sharing
- Any other app needing URL shortening
"""

import logging
import string
import random
from typing import Optional, Dict, Any, List
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class URLShorteningService:
    """Service for URL shortening and management."""

    # Characters for short codes (excluding ambiguous ones)
    CODE_CHARS = string.ascii_letters + string.digits
    # Remove ambiguous characters
    CODE_CHARS = CODE_CHARS.replace('0', '').replace('O', '').replace('l', '').replace('I', '')

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize the URL shortening service.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.collection = db.short_urls

    async def initialize_indexes(self):
        """Create database indexes for optimal query performance."""
        try:
            # Unique index on short_code for fast lookups and collision prevention
            await self.collection.create_index("short_code", unique=True)

            # Index for finding URLs by target
            await self.collection.create_index("target_url")

            # Index for finding expired URLs
            await self.collection.create_index("expires_at")

            # Index for analytics queries
            await self.collection.create_index([("created_at", -1)])

            logger.info("URL shortening service indexes created")
        except Exception as e:
            logger.warning(f"Failed to create URL shortening indexes: {e}")

    def generate_short_code(self, length: int = 6) -> str:
        """
        Generate a random short code.

        Args:
            length: Length of the short code (default 6)

        Returns:
            Random alphanumeric string without ambiguous characters
        """
        return ''.join(random.choices(self.CODE_CHARS, k=length))

    async def create_short_url(
        self,
        target_url: str,
        custom_code: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
        app_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a short URL.

        Args:
            target_url: The full URL to shorten
            custom_code: Optional custom short code (must be unique)
            expires_at: Optional expiration datetime
            metadata: Optional metadata dict (e.g., {"type": "invitation", "invitation_id": "abc"})
            app_name: Optional app identifier (e.g., "inkwave", "churchflow")

        Returns:
            Dict with short_code, short_url, target_url, and metadata

        Raises:
            ValueError: If custom code is already in use or generation fails
        """
        # Determine short code
        if custom_code:
            # Check if custom code is available
            existing = await self.collection.find_one({"short_code": custom_code})
            if existing:
                raise ValueError(f"Short code '{custom_code}' is already in use")
            short_code = custom_code
        else:
            # Generate unique short code with collision avoidance
            max_attempts = 10
            short_code = None
            for _ in range(max_attempts):
                candidate = self.generate_short_code()
                existing = await self.collection.find_one({"short_code": candidate})
                if not existing:
                    short_code = candidate
                    break

            if not short_code:
                raise ValueError("Failed to generate unique short code after 10 attempts")

        # Create short URL document
        short_url_doc = {
            "short_code": short_code,
            "target_url": target_url,
            "created_at": datetime.now(),
            "expires_at": expires_at,
            "clicks": 0,
            "click_details": [],
            "app_name": app_name,
            **(metadata or {})
        }

        await self.collection.insert_one(short_url_doc)

        logger.info(
            f"Created short URL {short_code} -> {target_url[:50]}... "
            f"(app: {app_name or 'unknown'})"
        )

        return {
            "short_code": short_code,
            "target_url": target_url,
            "created_at": short_url_doc["created_at"],
            "expires_at": expires_at,
            "clicks": 0
        }

    async def get_target_url(self, short_code: str) -> Optional[Dict[str, Any]]:
        """
        Get the target URL and metadata for a short code.

        Args:
            short_code: The short code to look up

        Returns:
            Dict with target_url and metadata, or None if not found/expired
        """
        doc = await self.collection.find_one({"short_code": short_code})

        if not doc:
            return None

        # Check expiration
        if doc.get("expires_at") and datetime.now() > doc["expires_at"]:
            logger.warning(f"Short code {short_code} has expired")
            return None

        return doc

    async def record_click(
        self,
        short_code: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Record a click/visit to a short URL.

        Args:
            short_code: The short code that was clicked
            metadata: Optional click metadata (e.g., user_agent, ip, referrer)

        Returns:
            True if recorded successfully, False if short code not found
        """
        click_detail = {
            "timestamp": datetime.now(),
            **(metadata or {})
        }

        result = await self.collection.update_one(
            {"short_code": short_code},
            {
                "$inc": {"clicks": 1},
                "$push": {"click_details": click_detail}
            }
        )

        return result.modified_count > 0

    async def get_stats(self, short_code: str) -> Optional[Dict[str, Any]]:
        """
        Get analytics for a short URL.

        Args:
            short_code: The short code to get stats for

        Returns:
            Dict with stats including clicks, recent activity, etc.
        """
        doc = await self.collection.find_one({"short_code": short_code})

        if not doc:
            return None

        return {
            "short_code": short_code,
            "target_url": doc["target_url"],
            "created_at": doc["created_at"],
            "expires_at": doc.get("expires_at"),
            "clicks": doc.get("clicks", 0),
            "recent_clicks": doc.get("click_details", [])[-10:],  # Last 10 clicks
            "app_name": doc.get("app_name")
        }

    async def delete_short_url(self, short_code: str) -> bool:
        """
        Delete a short URL.

        Args:
            short_code: The short code to delete

        Returns:
            True if deleted, False if not found
        """
        result = await self.collection.delete_one({"short_code": short_code})

        if result.deleted_count > 0:
            logger.info(f"Deleted short URL {short_code}")
            return True

        return False

    async def cleanup_expired(self) -> int:
        """
        Clean up expired short URLs.

        Returns:
            Number of URLs deleted
        """
        result = await self.collection.delete_many({
            "expires_at": {"$lt": datetime.now()}
        })

        if result.deleted_count > 0:
            logger.info(f"Cleaned up {result.deleted_count} expired short URLs")

        return result.deleted_count

    async def get_app_stats(self, app_name: str) -> Dict[str, Any]:
        """
        Get statistics for a specific app.

        Args:
            app_name: App identifier (e.g., "inkwave", "churchflow")

        Returns:
            Dict with aggregate stats for the app
        """
        total = await self.collection.count_documents({"app_name": app_name})

        # Get total clicks for this app
        pipeline = [
            {"$match": {"app_name": app_name}},
            {"$group": {"_id": None, "total_clicks": {"$sum": "$clicks"}}}
        ]
        result = await self.collection.aggregate(pipeline).to_list(1)
        total_clicks = result[0]["total_clicks"] if result else 0

        # Get most clicked URLs
        pipeline = [
            {"$match": {"app_name": app_name}},
            {"$sort": {"clicks": -1}},
            {"$limit": 10},
            {"$project": {
                "short_code": 1,
                "target_url": 1,
                "clicks": 1,
                "created_at": 1
            }}
        ]
        top_urls = await self.collection.aggregate(pipeline).to_list(10)

        return {
            "app_name": app_name,
            "total_urls": total,
            "total_clicks": total_clicks,
            "top_urls": top_urls
        }


def get_url_shortening_service(db: AsyncIOMotorDatabase) -> URLShorteningService:
    """
    Get a URL shortening service instance.

    Args:
        db: MongoDB database instance

    Returns:
        URLShorteningService instance
    """
    return URLShorteningService(db)
