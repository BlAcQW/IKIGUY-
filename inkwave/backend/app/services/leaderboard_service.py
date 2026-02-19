"""
Leaderboard service for tracking and displaying top listeners.

Handles:
- Get top listeners by period (week, month, all-time)
- Calculate user listening hours
- Get user rank
- Respect privacy settings (opt-out, anonymous mode)
- Leaderboard caching for performance
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class LeaderboardService:
    """Service for leaderboard functionality."""

    # Cache duration (15 minutes)
    CACHE_DURATION_MINUTES = 15

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize leaderboard service.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.users_collection = db.users
        self.wallet_transactions_collection = db.wallet_transactions
        self.cache: Dict[str, Dict[str, Any]] = {}

    async def get_top_listeners(
        self, period: str = "all_time", limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get top listeners for a period.

        Args:
            period: Time period (week, month, all_time)
            limit: Number of results to return

        Returns:
            List of users with listening stats
        """
        # Check cache
        cache_key = f"{period}_{limit}"
        cached = self.cache.get(cache_key)
        if cached and cached["expires_at"] > datetime.utcnow():
            logger.debug(f"Returning cached leaderboard for {period}")
            return cached["data"]

        # Calculate date filter based on period
        date_filter = self._get_date_filter(period)

        # Get users who opted into leaderboard
        users_filter = {
            "privacy_settings.appear_in_leaderboard": True,
            "privacy_settings.leaderboard_display_mode": {"$ne": "opt_out"}
        }

        users = await self.users_collection.find(users_filter).to_list(length=None)

        if not users:
            return []

        # Calculate listening hours for each user
        leaderboard = []
        for user in users:
            hours = await self.calculate_listening_hours(
                user["user_id"], period
            )

            # Only include users with listening time
            if hours > 0:
                display_mode = user.get("privacy_settings", {}).get(
                    "leaderboard_display_mode", "full_profile"
                )

                entry = {
                    "user_id": user["user_id"],
                    "listening_hours": round(hours, 1),
                    "display_mode": display_mode
                }

                # Include profile info based on display mode
                if display_mode == "full_profile":
                    entry.update({
                        "username": user.get("username"),
                        "display_name": user.get("display_name"),
                        "avatar_url": user.get("avatar_url")
                    })
                elif display_mode == "anonymous":
                    # Generate nature-inspired username if user doesn't have one
                    from app.services.username_generator import get_display_username
                    display_username = get_display_username(user)

                    entry.update({
                        "username": display_username,
                        "display_name": display_username,
                        "avatar_url": None
                    })

                leaderboard.append(entry)

        # Sort by listening hours (descending)
        leaderboard.sort(key=lambda x: x["listening_hours"], reverse=True)

        # Limit results
        leaderboard = leaderboard[:limit]

        # Add ranks
        for i, entry in enumerate(leaderboard, start=1):
            entry["rank"] = i

        # Cache results
        self.cache[cache_key] = {
            "data": leaderboard,
            "expires_at": datetime.utcnow() + timedelta(minutes=self.CACHE_DURATION_MINUTES)
        }

        logger.info(f"Generated leaderboard for {period} with {len(leaderboard)} entries")

        return leaderboard

    async def search_leaderboard(
        self, period: str = "all_time", query: str = "", limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search leaderboard by username or display name.

        Args:
            period: Time period (week, month, all_time)
            query: Search query for username/display name
            limit: Number of results to return

        Returns:
            List of matching leaderboard entries
        """
        if not query or len(query.strip()) < 2:
            # Too short query, return empty results
            return []

        query_lower = query.strip().lower()

        # Get full leaderboard (up to 1000 users)
        all_entries = await self.get_top_listeners(period=period, limit=1000)

        # Filter by search query (case-insensitive partial match)
        matching_entries = []
        for entry in all_entries:
            username = entry.get("username", "").lower()
            display_name = entry.get("display_name", "").lower()

            # Check if query matches username or display name
            if query_lower in username or query_lower in display_name:
                matching_entries.append(entry)

        # Limit results
        matching_entries = matching_entries[:limit]

        logger.info(f"Search '{query}' returned {len(matching_entries)} results")

        return matching_entries

    async def get_user_rank(
        self, user_id: str, period: str = "all_time"
    ) -> Optional[int]:
        """
        Get user's rank on the leaderboard.

        Args:
            user_id: User ID to get rank for
            period: Time period (week, month, all_time)

        Returns:
            Rank (1-indexed) or None if not on leaderboard
        """
        # Get full leaderboard
        leaderboard = await self.get_top_listeners(period=period, limit=1000)

        # Find user
        for entry in leaderboard:
            if entry["user_id"] == user_id:
                return entry["rank"]

        return None

    async def calculate_listening_hours(
        self, user_id: str, period: str = "all_time"
    ) -> float:
        """
        Calculate total listening hours for a user.

        Sums up duration_minutes from wallet transactions.

        Args:
            user_id: User ID
            period: Time period (week, month, all_time)

        Returns:
            Total hours listened
        """
        # Build filter
        filter_query: Dict[str, Any] = {
            "user_id": user_id,
            "metadata.duration_minutes": {"$exists": True}
        }

        # Add date filter
        date_filter = self._get_date_filter(period)
        if date_filter:
            filter_query.update(date_filter)

        logger.debug(f"Leaderboard calculation for user_id={user_id}, period={period}, filter={filter_query}")

        # Aggregate total minutes
        pipeline = [
            {"$match": filter_query},
            {
                "$group": {
                    "_id": None,
                    "total_minutes": {"$sum": "$metadata.duration_minutes"},
                    "count": {"$sum": 1}
                }
            }
        ]

        result = await self.wallet_transactions_collection.aggregate(pipeline).to_list(length=1)

        if not result:
            logger.debug(f"No transactions found for user_id={user_id}, period={period}")
            return 0.0

        total_minutes = result[0].get("total_minutes", 0)
        tx_count = result[0].get("count", 0)
        total_hours = total_minutes / 60.0

        logger.debug(f"Leaderboard result for user_id={user_id}: {tx_count} transactions, {total_minutes:.1f} minutes, {total_hours:.2f} hours")

        return total_hours

    async def refresh_leaderboard_cache(self, period: str) -> None:
        """
        Manually refresh leaderboard cache.

        Args:
            period: Time period to refresh
        """
        cache_key = f"{period}_20"
        if cache_key in self.cache:
            del self.cache[cache_key]

        await self.get_top_listeners(period=period, limit=20)
        logger.info(f"Refreshed leaderboard cache for {period}")

    async def update_user_listening_stats(self, user_id: str) -> None:
        """
        Update user's denormalized listening stats.

        Updates:
        - total_listening_hours
        - books_completed

        Args:
            user_id: User ID to update stats for
        """
        # Calculate all-time listening hours
        total_hours = await self.calculate_listening_hours(user_id, "all_time")

        # Count completed books (reading sessions with 100% progress)
        books_completed = await self.db.reading_sessions.count_documents({
            "user_id": user_id,
            "progress_percentage": 100
        })

        # Update user document
        await self.users_collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "social_stats.total_listening_hours": total_hours,
                    "social_stats.books_completed": books_completed,
                    "social_stats.last_stats_update": datetime.utcnow()
                }
            }
        )

        logger.debug(
            f"Updated listening stats for {user_id}: "
            f"{total_hours:.1f} hours, {books_completed} books"
        )

    def _get_date_filter(self, period: str) -> Optional[Dict[str, Any]]:
        """
        Get MongoDB date filter for a period.

        Args:
            period: Time period (week, month, all_time)

        Returns:
            Date filter dict or None for all_time
        """
        now = datetime.utcnow()

        if period == "week":
            start_date = now - timedelta(days=7)
            return {"created_at": {"$gte": start_date}}
        elif period == "month":
            start_date = now - timedelta(days=30)
            return {"created_at": {"$gte": start_date}}
        elif period == "all_time":
            return None
        else:
            # Default to all_time
            return None


def get_leaderboard_service(db: AsyncIOMotorDatabase) -> LeaderboardService:
    """
    Get leaderboard service instance.

    Args:
        db: MongoDB database instance

    Returns:
        LeaderboardService instance
    """
    return LeaderboardService(db)
