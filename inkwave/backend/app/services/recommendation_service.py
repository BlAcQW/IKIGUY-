"""
Recommendation Service for InkWave - Church Content Platform.

Provides personalized sermon and teaching recommendations based on:
- Spiritual topics (Prayer, Faith, Deliverance, etc.)
- User listening history
- Popular series from Archbishop Duncan-Williams
- Seasonal content (Easter, Christmas, etc.)
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import Counter

from app.core.database import get_db

logger = logging.getLogger(__name__)


# Church content categories for Archbishop Duncan-Williams
CHURCH_CATEGORIES = {
    "prayer": "Prayer & Intercession",
    "faith": "Faith & Breakthrough",
    "deliverance": "Deliverance & Spiritual Warfare",
    "prosperity": "Prosperity & Abundance",
    "healing": "Healing & Restoration",
    "leadership": "Leadership & Ministry",
    "family": "Marriage & Family",
    "youth": "Youth & Young Adults",
    "praise": "Praise & Worship",
    "prophecy": "Prophetic Messages"
}


class RecommendationService:
    """Service for generating sermon and teaching recommendations."""

    def __init__(self):
        """Initialize recommendation service."""
        self.db = None

    def _ensure_db(self):
        """Ensure database is initialized."""
        if self.db is None:
            self.db = get_db()

    async def get_recommendations(
        self,
        user_id: str,
        limit: int = 10,
        exclude_completed: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get personalized sermon recommendations for a user.

        Args:
            user_id: User ID
            limit: Maximum number of recommendations
            exclude_completed: Exclude sermons user has completed

        Returns:
            List of recommended sermons with scores
        """
        self._ensure_db()
        try:
            # Get user's listening history
            user_history = await self._get_user_listening_history(user_id)

            # Get user's preferred topics
            preferred_topics = await self._get_preferred_topics(user_id)

            # Get sermons user has already listened to
            listened_book_ids = [book["book_id"] for book in user_history]

            # Build recommendation query
            query = {
                "processing_status": "ready",
                "processed": True
            }

            if exclude_completed:
                # Exclude sermons user has finished (progress >= 95%)
                completed_book_ids = [
                    book["book_id"]
                    for book in user_history
                    if book.get("progress", 0) >= 95
                ]
                if completed_book_ids:
                    query["book_id"] = {"$nin": completed_book_ids}

            # Fetch candidate sermons
            books_cursor = self.db.books.find(query).limit(limit * 3)
            candidate_books = await books_cursor.to_list(length=limit * 3)

            if not candidate_books:
                # No sermons available, return empty list
                return []

            # Score and rank sermons
            scored_books = []
            for book in candidate_books:
                score = await self._calculate_recommendation_score(
                    book,
                    user_id,
                    user_history,
                    preferred_topics,
                    listened_book_ids
                )
                scored_books.append({
                    **book,
                    "recommendation_score": score,
                    "recommendation_reason": self._get_recommendation_reason(
                        book, preferred_topics, user_history
                    )
                })

            # Sort by score and return top N
            scored_books.sort(key=lambda x: x["recommendation_score"], reverse=True)
            recommendations = scored_books[:limit]

            # Format response
            return [self._format_book_response(book) for book in recommendations]

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}", exc_info=True)
            # Fallback to recent sermons
            return await self._get_recent_books(limit)

    async def get_by_category(
        self,
        category: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get sermons by spiritual category.

        Args:
            category: Category key (prayer, faith, deliverance, etc.)
            limit: Maximum number of sermons

        Returns:
            List of sermons in category
        """
        self._ensure_db()
        try:
            query = {
                "processing_status": "ready",
                "processed": True,
                "metadata.genre": category
            }

            books_cursor = self.db.books.find(query).sort(
                "created_at", -1
            ).limit(limit)
            books = await books_cursor.to_list(length=limit)

            return [self._format_book_response(book) for book in books]

        except Exception as e:
            logger.error(f"Error getting sermons by category: {e}", exc_info=True)
            return []

    async def get_latest_sermons(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get latest sermons from Archbishop Duncan-Williams.

        Args:
            limit: Maximum number of sermons

        Returns:
            List of latest sermons
        """
        self._ensure_db()
        return await self._get_recent_books(limit)

    async def get_popular_series(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get popular sermon series.

        Args:
            limit: Maximum number of series

        Returns:
            List of popular series
        """
        self._ensure_db()
        try:
            # Group by series and count listeners
            pipeline = [
                {
                    "$match": {
                        "processing_status": "ready",
                        "processed": True
                    }
                },
                {
                    "$group": {
                        "_id": "$metadata.themes",
                        "count": {"$sum": 1},
                        "first_book": {"$first": "$$ROOT"}
                    }
                },
                {
                    "$sort": {"count": -1}
                },
                {
                    "$limit": limit
                }
            ]

            series = []
            async for doc in self.db.books.aggregate(pipeline):
                series.append(self._format_book_response(doc["first_book"]))

            return series

        except Exception as e:
            logger.error(f"Error getting popular series: {e}", exc_info=True)
            return await self._get_recent_books(limit)

    async def get_series_with_metadata(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get sermon series grouped by common themes/topics.

        Returns series information including:
        - Series name
        - Number of sermons
        - Representative sermon
        - Topics covered

        Args:
            limit: Maximum number of series

        Returns:
            List of series with metadata
        """
        self._ensure_db()
        try:
            # Group by first theme (primary topic)
            pipeline = [
                {
                    "$match": {
                        "processing_status": "ready",
                        "processed": True,
                        "metadata.themes": {"$exists": True, "$ne": []}
                    }
                },
                {
                    "$addFields": {
                        "primary_theme": {"$arrayElemAt": ["$metadata.themes", 0]}
                    }
                },
                {
                    "$group": {
                        "_id": "$primary_theme",
                        "sermon_count": {"$sum": 1},
                        "representative_sermon": {"$first": "$$ROOT"},
                        "all_topics": {"$push": "$metadata.genre"}
                    }
                },
                {
                    "$project": {
                        "series_name": "$_id",
                        "sermon_count": 1,
                        "representative_sermon": 1,
                        "topics": {
                            "$reduce": {
                                "input": "$all_topics",
                                "initialValue": [],
                                "in": {"$setUnion": ["$$value", "$$this"]}
                            }
                        }
                    }
                },
                {
                    "$sort": {"sermon_count": -1}
                },
                {
                    "$limit": limit
                }
            ]

            series_list = []
            async for doc in self.db.books.aggregate(pipeline):
                series_info = {
                    "series_name": doc.get("series_name", "Untitled Series"),
                    "sermon_count": doc.get("sermon_count", 0),
                    "topics": doc.get("topics", []),
                    "representative_sermon": self._format_book_response(doc["representative_sermon"])
                }
                series_list.append(series_info)

            return series_list

        except Exception as e:
            logger.error(f"Error getting series with metadata: {e}", exc_info=True)
            return []

    async def get_similar_sermons(
        self,
        book_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get sermons similar to a specific sermon.

        Args:
            book_id: Target sermon ID
            limit: Maximum number of similar sermons

        Returns:
            List of similar sermons
        """
        self._ensure_db()
        try:
            # Get target sermon
            target_book = await self.db.books.find_one({"book_id": book_id})
            if not target_book:
                return []

            # Get target sermon topics
            target_genres = target_book.get("metadata", {}).get("genre", [])
            if not target_genres:
                # No topics, return recent sermons
                return await self._get_recent_books(limit)

            # Find sermons with overlapping topics
            query = {
                "book_id": {"$ne": book_id},  # Exclude target sermon
                "processing_status": "ready",
                "processed": True,
                "metadata.genre": {"$in": target_genres}
            }

            similar_cursor = self.db.books.find(query).limit(limit)
            similar_books = await similar_cursor.to_list(length=limit)

            return [self._format_book_response(book) for book in similar_books]

        except Exception as e:
            logger.error(f"Error finding similar sermons: {e}", exc_info=True)
            return []

    async def get_featured_content(self) -> Dict[str, Any]:
        """
        Get featured sermon for hero banner.

        Returns:
            Featured sermon details
        """
        self._ensure_db()
        try:
            # Get most recent sermon as featured
            book = await self.db.books.find_one(
                {"processing_status": "ready", "processed": True},
                sort=[("created_at", -1)]
            )

            if book:
                return self._format_book_response(book)
            return None

        except Exception as e:
            logger.error(f"Error getting featured content: {e}", exc_info=True)
            return None

    # Private helper methods

    async def _get_user_listening_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's listening history."""
        try:
            sessions_cursor = self.db.reading_sessions.find(
                {"user_id": user_id}
            ).sort("updated_at", -1).limit(50)
            sessions = await sessions_cursor.to_list(length=50)
            return sessions
        except Exception as e:
            logger.error(f"Error getting listening history: {e}")
            return []

    async def _get_preferred_topics(self, user_id: str) -> List[str]:
        """Extract user's preferred spiritual topics from listening history."""
        try:
            # Get user's listening sessions
            history = await self._get_user_listening_history(user_id)
            book_ids = [session["book_id"] for session in history]

            if not book_ids:
                return []

            # Get topics from listened sermons
            books_cursor = self.db.books.find({"book_id": {"$in": book_ids}})
            books = await books_cursor.to_list(length=len(book_ids))

            # Count topic occurrences
            topic_counter = Counter()
            for book in books:
                genres = book.get("metadata", {}).get("genre", [])
                topic_counter.update(genres)

            # Return top 3 topics
            return [topic for topic, _ in topic_counter.most_common(3)]

        except Exception as e:
            logger.error(f"Error getting preferred topics: {e}")
            return []

    async def _calculate_recommendation_score(
        self,
        book: Dict[str, Any],
        user_id: str,
        user_history: List[Dict[str, Any]],
        preferred_topics: List[str],
        listened_book_ids: List[str]
    ) -> float:
        """
        Calculate recommendation score for a sermon.

        Scoring factors:
        - Topic match: +10 per matching topic
        - Recency: +5 for sermons added in last 30 days
        - Popular: +3 for highly listened sermons
        - Not started: +2 (encourage discovery)
        - Already started: -5 (user already knows about it)
        """
        score = 0.0

        # Topic match
        book_genres = book.get("metadata", {}).get("genre", [])
        for genre in book_genres:
            if genre in preferred_topics:
                score += 10

        # Recency boost for new sermons
        created_at = book.get("created_at")
        if created_at:
            days_old = (datetime.utcnow() - created_at).days
            if days_old <= 30:
                score += 5
            elif days_old <= 90:
                score += 2

        # Penalize if user has already started
        if book["book_id"] in listened_book_ids:
            score -= 5
        else:
            # Boost for new discoveries
            score += 2

        return score

    def _get_recommendation_reason(
        self,
        book: Dict[str, Any],
        preferred_topics: List[str],
        user_history: List[Dict[str, Any]]
    ) -> str:
        """Generate human-readable recommendation reason."""
        book_genres = book.get("metadata", {}).get("genre", [])

        # Check for topic match
        matching_topics = [g for g in book_genres if g in preferred_topics]
        if matching_topics:
            topic_name = CHURCH_CATEGORIES.get(matching_topics[0], matching_topics[0])
            return f"Based on your interest in {topic_name}"

        # Check if it's new
        created_at = book.get("created_at")
        if created_at and (datetime.utcnow() - created_at).days <= 7:
            return "Latest message"

        # Default
        return "Popular in the church"

    async def _get_recent_books(self, limit: int) -> List[Dict[str, Any]]:
        """Get recently added sermons as fallback."""
        try:
            books_cursor = self.db.books.find({
                "processing_status": "ready",
                "processed": True
            }).sort("created_at", -1).limit(limit)
            books = await books_cursor.to_list(length=limit)

            return [self._format_book_response(book) for book in books]

        except Exception as e:
            logger.error(f"Error getting recent sermons: {e}")
            return []

    def _format_book_response(self, book: Dict[str, Any]) -> Dict[str, Any]:
        """Format sermon for API response."""
        metadata = book.get("metadata", {})

        return {
            "id": book.get("book_id"),
            "title": book.get("title"),
            "author": book.get("author", "Archbishop Nicholas Duncan-Williams"),
            "cover_url": book.get("cover_url"),
            "duration": metadata.get("estimated_reading_time_minutes", 0),
            "genre": metadata.get("genre", []),
            "description": metadata.get("summary", ""),
            "themes": metadata.get("themes", []),
            "difficulty_level": metadata.get("difficulty_level", "intermediate"),
            "recommendation_score": book.get("recommendation_score", 0),
            "recommendation_reason": book.get("recommendation_reason", "")
        }


# Singleton instance
recommendation_service = RecommendationService()
