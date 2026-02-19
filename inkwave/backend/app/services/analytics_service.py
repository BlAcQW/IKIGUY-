"""
Analytics Service for InkWave (Interactive Audiobook Platform).

Tracks usage metrics and costs for audiobook listening, AI interactions,
and TTS generation.
"""

import logging
import os
import sys
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta, timezone
from decimal import Decimal

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class InkWaveAnalyticsService:
    """
    Analytics service for InkWave.

    Provides book-specific analytics for listening time, AI interactions,
    and cost tracking.
    """

    def __init__(self):
        """Initialize InkWave analytics service."""
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.logger = logging.getLogger(__name__)
        self.initialized = False

    async def initialize(self, mongodb_uri: str, database_name: str = "kasaai_core") -> bool:
        """
        Initialize analytics service with database connection.

        Args:
            mongodb_uri: MongoDB connection URI
            database_name: Database name

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            client = AsyncIOMotorClient(mongodb_uri)
            self.db = client[database_name]
            self.initialized = True
            self.logger.info("Analytics service initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize analytics service: {e}")
            return False

    async def get_book_analytics(
        self,
        book_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive analytics for a book.

        Tracks listening time, AI interactions, and costs.

        Args:
            book_id: Book ID
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Dictionary with book analytics
        """
        if not self.initialized:
            self.logger.warning("Analytics service not initialized")
            return {
                "book_id": book_id,
                "error": "Analytics service not initialized"
            }

        try:
            # Set date range if not provided
            if not start_date:
                start_date = datetime.now(timezone.utc) - timedelta(days=30)
            if not end_date:
                end_date = datetime.now(timezone.utc)

            # Query wallet transactions for this book
            wallet_transactions = self.db["wallet_transactions"]

            # Get listening metrics
            listening_pipeline = [
                {
                    "$match": {
                        "metadata.book_id": book_id,
                        "metadata.service": "inkwave_listening",
                        "created_at": {"$gte": start_date, "$lte": end_date}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_cost": {"$sum": "$amount"},
                        "total_minutes": {"$sum": "$metadata.duration_minutes"},
                        "listening_sessions": {"$sum": 1}
                    }
                }
            ]

            listening_result = await wallet_transactions.aggregate(listening_pipeline).to_list(length=1)
            listening_data = listening_result[0] if listening_result else {}

            # Get AI interaction metrics
            ai_pipeline = [
                {
                    "$match": {
                        "metadata.book_id": book_id,
                        "metadata.service": "inkwave_ai",
                        "created_at": {"$gte": start_date, "$lte": end_date}
                    }
                },
                {
                    "$group": {
                        "_id": "$metadata.interaction_type",
                        "total_cost": {"$sum": "$amount"},
                        "interaction_count": {"$sum": 1}
                    }
                }
            ]

            ai_results = await wallet_transactions.aggregate(ai_pipeline).to_list(length=100)

            # Format AI interactions
            ai_interactions = {}
            total_ai_cost = 0.0
            total_ai_count = 0

            for result in ai_results:
                interaction_type = result["_id"] or "other"
                cost = abs(float(result["total_cost"]))
                count = result["interaction_count"]

                ai_interactions[interaction_type] = {
                    "cost": cost,
                    "count": count,
                    "average_cost": cost / count if count > 0 else 0.0
                }

                total_ai_cost += cost
                total_ai_count += count

            # Calculate totals
            listening_cost = abs(float(listening_data.get("total_cost", 0.0)))
            listening_minutes = float(listening_data.get("total_minutes", 0.0))
            listening_sessions = listening_data.get("listening_sessions", 0)

            total_cost = listening_cost + total_ai_cost

            return {
                "book_id": book_id,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "total_cost": total_cost,
                "listening": {
                    "cost": listening_cost,
                    "total_minutes": listening_minutes,
                    "sessions": listening_sessions,
                    "average_session_minutes": listening_minutes / listening_sessions if listening_sessions > 0 else 0.0
                },
                "ai_interactions": {
                    "total_cost": total_ai_cost,
                    "total_count": total_ai_count,
                    "by_type": ai_interactions
                },
                "cost_distribution": {
                    "listening_percent": (listening_cost / total_cost * 100) if total_cost > 0 else 0.0,
                    "ai_percent": (total_ai_cost / total_cost * 100) if total_cost > 0 else 0.0
                }
            }

        except Exception as e:
            self.logger.error(f"Failed to get book analytics: {e}")
            return {
                "book_id": book_id,
                "error": str(e)
            }

    async def get_user_listening_stats(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get listening statistics for a user.

        Args:
            user_id: User ID
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Dictionary with user listening stats
        """
        if not self.initialized:
            self.logger.warning("Analytics service not initialized")
            return {
                "user_id": user_id,
                "error": "Analytics service not initialized"
            }

        try:
            # Set date range if not provided
            if not start_date:
                start_date = datetime.now(timezone.utc) - timedelta(days=30)
            if not end_date:
                end_date = datetime.now(timezone.utc)

            # Query wallet transactions
            wallet_transactions = self.db["wallet_transactions"]

            pipeline = [
                {
                    "$match": {
                        "user_id": user_id,
                        "metadata.service": {"$in": ["inkwave_listening", "inkwave_ai"]},
                        "created_at": {"$gte": start_date, "$lte": end_date}
                    }
                },
                {
                    "$group": {
                        "_id": "$metadata.service",
                        "total_cost": {"$sum": "$amount"},
                        "activity_count": {"$sum": 1}
                    }
                }
            ]

            results = await wallet_transactions.aggregate(pipeline).to_list(length=100)

            # Format results
            listening_cost = 0.0
            listening_sessions = 0
            ai_cost = 0.0
            ai_interactions = 0

            for result in results:
                service = result["_id"]
                cost = abs(float(result["total_cost"]))
                count = result["activity_count"]

                if service == "inkwave_listening":
                    listening_cost = cost
                    listening_sessions = count
                elif service == "inkwave_ai":
                    ai_cost = cost
                    ai_interactions = count

            # Get detailed listening metrics
            listening_pipeline = [
                {
                    "$match": {
                        "user_id": user_id,
                        "metadata.service": "inkwave_listening",
                        "created_at": {"$gte": start_date, "$lte": end_date}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_minutes": {"$sum": "$metadata.duration_minutes"}
                    }
                }
            ]

            listening_result = await wallet_transactions.aggregate(listening_pipeline).to_list(length=1)
            total_minutes = float(listening_result[0].get("total_minutes", 0.0)) if listening_result else 0.0

            # Get books listened to
            books_pipeline = [
                {
                    "$match": {
                        "user_id": user_id,
                        "metadata.service": "inkwave_listening",
                        "created_at": {"$gte": start_date, "$lte": end_date}
                    }
                },
                {
                    "$group": {
                        "_id": "$metadata.book_id",
                        "minutes": {"$sum": "$metadata.duration_minutes"}
                    }
                }
            ]

            books_results = await wallet_transactions.aggregate(books_pipeline).to_list(length=100)
            unique_books = len(books_results)

            total_cost = listening_cost + ai_cost

            return {
                "user_id": user_id,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "total_cost": total_cost,
                "listening": {
                    "cost": listening_cost,
                    "total_minutes": total_minutes,
                    "sessions": listening_sessions,
                    "unique_books": unique_books,
                    "average_session_minutes": total_minutes / listening_sessions if listening_sessions > 0 else 0.0
                },
                "ai_interactions": {
                    "cost": ai_cost,
                    "count": ai_interactions
                }
            }

        except Exception as e:
            self.logger.error(f"Failed to get user listening stats: {e}")
            return {
                "user_id": user_id,
                "error": str(e)
            }

    async def get_popular_books(
        self,
        limit: int = 10,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get most popular books by listening time.

        Args:
            limit: Number of books to return
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Dictionary with popular books
        """
        if not self.initialized:
            self.logger.warning("Analytics service not initialized")
            return {
                "error": "Analytics service not initialized"
            }

        try:
            # Set date range if not provided
            if not start_date:
                start_date = datetime.now(timezone.utc) - timedelta(days=30)
            if not end_date:
                end_date = datetime.now(timezone.utc)

            # Query wallet transactions
            wallet_transactions = self.db["wallet_transactions"]

            pipeline = [
                {
                    "$match": {
                        "metadata.service": "inkwave_listening",
                        "created_at": {"$gte": start_date, "$lte": end_date}
                    }
                },
                {
                    "$group": {
                        "_id": "$metadata.book_id",
                        "total_minutes": {"$sum": "$metadata.duration_minutes"},
                        "unique_listeners": {"$addToSet": "$user_id"},
                        "sessions": {"$sum": 1}
                    }
                },
                {
                    "$project": {
                        "book_id": "$_id",
                        "total_minutes": 1,
                        "unique_listeners": {"$size": "$unique_listeners"},
                        "sessions": 1
                    }
                },
                {
                    "$sort": {"total_minutes": -1}
                },
                {
                    "$limit": limit
                }
            ]

            results = await wallet_transactions.aggregate(pipeline).to_list(length=limit)

            # Format results
            books = []
            for result in results:
                books.append({
                    "book_id": result["book_id"],
                    "total_minutes": float(result["total_minutes"]),
                    "unique_listeners": result["unique_listeners"],
                    "sessions": result["sessions"],
                    "average_session_minutes": float(result["total_minutes"]) / result["sessions"]
                })

            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "books": books,
                "count": len(books)
            }

        except Exception as e:
            self.logger.error(f"Failed to get popular books: {e}")
            return {
                "error": str(e)
            }


# Global service instance
_analytics_service: Optional[InkWaveAnalyticsService] = None


async def get_analytics_service() -> InkWaveAnalyticsService:
    """
    Get or create the global analytics service instance.

    Returns:
        InkWaveAnalyticsService instance
    """
    global _analytics_service

    if _analytics_service is None:
        _analytics_service = InkWaveAnalyticsService()

        # Initialize with environment variables
        mongodb_uri = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        await _analytics_service.initialize(mongodb_uri, database_name="kasaai_core")

    return _analytics_service
