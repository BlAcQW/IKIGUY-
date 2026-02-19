"""
Author/Pastor service for managing devotionals and dashboard.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from bson import ObjectId
from app.db.mongodb import get_database


class AuthorService:
    """Service for author/pastor operations."""

    def __init__(self):
        self.db = get_database()
        self.users_collection = self.db.users
        self.devotionals_collection = self.db.devotionals
        self.comments_collection = self.db.comments
        self.likes_collection = self.db.likes
        self.readings_collection = self.db.readings

    async def get_author_statistics(self, author_id: str) -> Dict[str, Any]:
        """
        Get personal statistics for author dashboard.

        Args:
            author_id: ID of the author/pastor

        Returns:
            Dict[str, Any]: Author statistics including readers, devotionals, engagement
        """
        # Count total devotionals published
        total_devotionals = await self.devotionals_collection.count_documents(
            {"author_id": author_id, "status": "published"}
        )

        # Count total likes on author's devotionals
        devotionals = await self.devotionals_collection.find(
            {"author_id": author_id}
        ).to_list(length=None)

        devotional_ids = [str(d["_id"]) for d in devotionals]

        total_likes = await self.likes_collection.count_documents(
            {"devotional_id": {"$in": devotional_ids}}
        )

        # Count total comments on author's devotionals
        total_comments = await self.comments_collection.count_documents(
            {"devotional_id": {"$in": devotional_ids}}
        )

        # Calculate total engagement
        total_engagement = total_likes + total_comments

        # Get total views/reads (if tracking)
        total_reads = 0
        if await self.readings_collection.count_documents({}) > 0:
            total_reads = await self.readings_collection.count_documents(
                {"devotional_id": {"$in": devotional_ids}}
            )

        # Calculate engagement rate (if we have reads)
        engagement_rate = 0
        if total_reads > 0:
            engagement_rate = (total_engagement / total_reads) * 100

        # Get unique readers (users who liked or commented on devotionals)
        # Note: This is an approximation - you might want to track actual readers differently
        unique_likers = await self.likes_collection.distinct(
            "user_id", {"devotional_id": {"$in": devotional_ids}}
        )
        unique_commenters = await self.comments_collection.distinct(
            "user_id", {"devotional_id": {"$in": devotional_ids}}
        )
        total_readers = len(set(unique_likers + unique_commenters))

        # Get this week's stats
        week_ago = datetime.utcnow() - timedelta(days=7)

        this_week_devotionals = await self.devotionals_collection.count_documents(
            {"author_id": author_id, "created_at": {"$gte": week_ago}}
        )

        this_week_likes = await self.likes_collection.count_documents(
            {"devotional_id": {"$in": devotional_ids}, "created_at": {"$gte": week_ago}}
        )

        this_week_comments = await self.comments_collection.count_documents(
            {"devotional_id": {"$in": devotional_ids}, "created_at": {"$gte": week_ago}}
        )

        this_week_engagement = this_week_likes + this_week_comments

        # Get this week's views/reads
        this_week_reads = 0
        if await self.readings_collection.count_documents({}) > 0:
            this_week_reads = await self.readings_collection.count_documents(
                {"devotional_id": {"$in": devotional_ids}, "created_at": {"$gte": week_ago}}
            )

        return {
            "total_readers": total_readers,
            "total_devotionals": total_devotionals,
            "total_likes": total_likes,
            "total_comments": total_comments,
            "total_engagement": total_engagement,
            "total_reads": total_reads,
            "engagement_rate": round(engagement_rate, 2),
            "this_week": {
                "devotionals": this_week_devotionals,
                "likes": this_week_likes,
                "comments": this_week_comments,
                "engagement": this_week_engagement,
                "reads": this_week_reads,
            },
        }

    async def get_recent_devotionals(
        self, author_id: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get recent devotionals for author dashboard.

        Args:
            author_id: ID of the author/pastor
            limit: Maximum number of devotionals to return

        Returns:
            List[Dict[str, Any]]: List of recent devotionals with engagement metrics
        """
        # Get recent devotionals
        devotionals = (
            await self.devotionals_collection.find({"author_id": author_id})
            .sort("created_at", -1)
            .limit(limit)
            .to_list(length=limit)
        )

        # Enrich with engagement metrics
        enriched_devotionals = []
        for devotional in devotionals:
            devotional_id = str(devotional["_id"])

            # Get likes count
            likes_count = await self.likes_collection.count_documents(
                {"devotional_id": devotional_id}
            )

            # Get comments count
            comments_count = await self.comments_collection.count_documents(
                {"devotional_id": devotional_id}
            )

            # Get reads count (if tracking)
            reads_count = 0
            if await self.readings_collection.count_documents({}) > 0:
                reads_count = await self.readings_collection.count_documents(
                    {"devotional_id": devotional_id}
                )

            enriched_devotionals.append(
                {
                    "id": devotional_id,
                    "title": devotional.get("title"),
                    "status": devotional.get("status"),
                    "category": devotional.get("category"),
                    "created_at": devotional.get("created_at"),
                    "scheduled_for": devotional.get("scheduled_for"),
                    "likes": likes_count,
                    "comments": comments_count,
                    "reads": reads_count,
                }
            )

        return enriched_devotionals

    async def get_devotionals_list(
        self,
        author_id: str,
        status: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        Get paginated list of devotionals for author.

        Args:
            author_id: ID of the author/pastor
            status: Filter by status (published, scheduled, draft)
            search: Search by title
            page: Page number
            page_size: Items per page

        Returns:
            Dict[str, Any]: Paginated list of devotionals with metrics
        """
        # Build query filter
        query = {"author_id": author_id}

        if status:
            query["status"] = status

        if search:
            query["title"] = {"$regex": search, "$options": "i"}

        # Count total matching documents
        total = await self.devotionals_collection.count_documents(query)

        # Calculate pagination
        skip = (page - 1) * page_size
        total_pages = (total + page_size - 1) // page_size

        # Get devotionals with pagination
        devotionals_cursor = (
            self.devotionals_collection.find(query)
            .sort("created_at", -1)
            .skip(skip)
            .limit(page_size)
        )

        devotionals = await devotionals_cursor.to_list(length=page_size)

        # Enrich with engagement metrics
        enriched_devotionals = []
        for devotional in devotionals:
            devotional_id = str(devotional["_id"])

            # Get likes count
            likes_count = await self.likes_collection.count_documents(
                {"devotional_id": devotional_id}
            )

            # Get comments count
            comments_count = await self.comments_collection.count_documents(
                {"devotional_id": devotional_id}
            )

            # Get reads count (if tracking)
            reads_count = 0
            if await self.readings_collection.count_documents({}) > 0:
                reads_count = await self.readings_collection.count_documents(
                    {"devotional_id": devotional_id}
                )

            enriched_devotionals.append(
                {
                    "id": devotional_id,
                    "title": devotional.get("title"),
                    "content": devotional.get("content"),
                    "scripture_reference": devotional.get("scripture_reference"),
                    "scripture_text": devotional.get("scripture_text"),
                    "status": devotional.get("status"),
                    "category": devotional.get("category"),
                    "created_at": devotional.get("created_at"),
                    "updated_at": devotional.get("updated_at"),
                    "scheduled_for": devotional.get("scheduled_for"),
                    "published_at": devotional.get("published_at"),
                    "likes": likes_count,
                    "comments": comments_count,
                    "reads": reads_count,
                }
            )

        return {
            "devotionals": enriched_devotionals,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    async def get_engagement_analytics(
        self, author_id: str, period: str = "30d"
    ) -> Dict[str, Any]:
        """
        Get detailed engagement analytics for author.

        Args:
            author_id: ID of the author/pastor
            period: Time period (7d, 30d, 90d, 1y)

        Returns:
            Dict[str, Any]: Detailed engagement analytics
        """
        # Calculate period start date
        period_map = {
            "7d": 7,
            "30d": 30,
            "90d": 90,
            "1y": 365,
        }
        days = period_map.get(period, 30)
        period_start = datetime.utcnow() - timedelta(days=days)

        # Get author's devotionals
        devotionals = await self.devotionals_collection.find(
            {"author_id": author_id}
        ).to_list(length=None)

        devotional_ids = [str(d["_id"]) for d in devotionals]

        # Get engagement over time (daily breakdown)
        daily_engagement = []
        for i in range(days):
            day_start = period_start + timedelta(days=i)
            day_end = day_start + timedelta(days=1)

            day_likes = await self.likes_collection.count_documents(
                {
                    "devotional_id": {"$in": devotional_ids},
                    "created_at": {"$gte": day_start, "$lt": day_end},
                }
            )

            day_comments = await self.comments_collection.count_documents(
                {
                    "devotional_id": {"$in": devotional_ids},
                    "created_at": {"$gte": day_start, "$lt": day_end},
                }
            )

            day_reads = 0
            if await self.readings_collection.count_documents({}) > 0:
                day_reads = await self.readings_collection.count_documents(
                    {
                        "devotional_id": {"$in": devotional_ids},
                        "created_at": {"$gte": day_start, "$lt": day_end},
                    }
                )

            daily_engagement.append(
                {
                    "date": day_start.strftime("%Y-%m-%d"),
                    "likes": day_likes,
                    "comments": day_comments,
                    "reads": day_reads,
                    "total_engagement": day_likes + day_comments,
                }
            )

        # Get top performing devotionals in period
        top_devotionals = []
        for devotional in devotionals[:10]:  # Limit to 10 most recent
            devotional_id = str(devotional["_id"])

            likes_count = await self.likes_collection.count_documents(
                {
                    "devotional_id": devotional_id,
                    "created_at": {"$gte": period_start},
                }
            )

            comments_count = await self.comments_collection.count_documents(
                {
                    "devotional_id": devotional_id,
                    "created_at": {"$gte": period_start},
                }
            )

            reads_count = 0
            if await self.readings_collection.count_documents({}) > 0:
                reads_count = await self.readings_collection.count_documents(
                    {
                        "devotional_id": devotional_id,
                        "created_at": {"$gte": period_start},
                    }
                )

            top_devotionals.append(
                {
                    "id": devotional_id,
                    "title": devotional.get("title"),
                    "likes": likes_count,
                    "comments": comments_count,
                    "reads": reads_count,
                    "total_engagement": likes_count + comments_count,
                }
            )

        # Sort by total engagement
        top_devotionals.sort(key=lambda x: x["total_engagement"], reverse=True)

        return {
            "period": period,
            "period_start": period_start.isoformat(),
            "period_end": datetime.utcnow().isoformat(),
            "daily_engagement": daily_engagement,
            "top_devotionals": top_devotionals[:5],  # Top 5
        }
