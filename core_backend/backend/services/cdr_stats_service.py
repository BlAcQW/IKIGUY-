"""
CDR Statistics Service

Handles call detail record statistics with:
- Optimized MongoDB aggregation using $facet
- Proper index management
- Redis caching for performance
- Direction-aware call tracking

Author: KasaAI
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
import hashlib
import json

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import IndexModel, ASCENDING, DESCENDING

from ..schemas.cdr import (
    CallDirection,
    CallSummary,
    CallBreakdown,
    DailyUsage,
    RecentCall,
    CDRStatsResponse,
)

logger = logging.getLogger(__name__)


class CDRStatsService:
    """
    Service for computing and caching CDR statistics.

    Features:
    - Single $facet aggregation for all stats
    - Automatic index creation
    - Redis caching with TTL
    - Pagination support
    """

    # Collection names
    CALLS_COLLECTION = "asterisk_calls"
    PHONES_COLLECTION = "managed_phone_numbers"

    # Cache settings
    CACHE_TTL_SECONDS = 300  # 5 minutes for recent data
    CACHE_PREFIX = "cdr_stats:"

    # Required indexes for optimal query performance
    REQUIRED_INDEXES = [
        IndexModel(
            [("phone_id", ASCENDING), ("created_at", DESCENDING)],
            name="phone_id_created_at_idx"
        ),
        IndexModel(
            [("phone_id", ASCENDING), ("direction", ASCENDING), ("created_at", DESCENDING)],
            name="phone_direction_created_idx"
        ),
        IndexModel(
            [("phone_id", ASCENDING), ("disposition", ASCENDING), ("created_at", DESCENDING)],
            name="phone_disposition_created_idx"
        ),
        IndexModel(
            [("src", ASCENDING), ("created_at", DESCENDING)],
            name="src_created_idx"
        ),
        IndexModel(
            [("dst", ASCENDING), ("created_at", DESCENDING)],
            name="dst_created_idx"
        ),
    ]

    def __init__(self, db: AsyncIOMotorDatabase, redis_client=None):
        """
        Initialize CDR Stats Service.

        Args:
            db: MongoDB database instance
            redis_client: Optional Redis client for caching
        """
        self.db = db
        self.redis = redis_client
        self._indexes_ensured = False

    async def ensure_indexes(self) -> None:
        """
        Create required indexes if they don't exist.

        Should be called once at application startup.
        """
        if self._indexes_ensured:
            return

        try:
            collection = self.db[self.CALLS_COLLECTION]

            # Get existing indexes
            existing = await collection.index_information()
            existing_names = set(existing.keys())

            # Create missing indexes
            for index in self.REQUIRED_INDEXES:
                if index.document.get("name") not in existing_names:
                    await collection.create_indexes([index])
                    logger.info(f"Created index: {index.document.get('name')}")

            self._indexes_ensured = True
            logger.info("CDR indexes verified/created successfully")

        except Exception as e:
            logger.error(f"Error ensuring CDR indexes: {e}")
            # Don't fail - queries will still work, just slower

    async def find_phone_by_number(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """
        Find a phone record by number with flexible matching.

        Args:
            phone_number: Phone number (with or without country code)

        Returns:
            Phone document or None
        """
        collection = self.db[self.PHONES_COLLECTION]

        # Normalize the number
        clean_number = phone_number.replace("+", "").replace(" ", "").replace("-", "")

        # Try exact match first
        phone = await collection.find_one({"number": phone_number})
        if phone:
            return phone

        # Try with +233 prefix
        if not phone_number.startswith("+"):
            phone = await collection.find_one({"number": f"+233{phone_number}"})
            if phone:
                return phone

            # Try with +2330 prefix (some numbers stored this way)
            phone = await collection.find_one({"number": f"+2330{phone_number}"})
            if phone:
                return phone

        # Fallback: match by last 9 digits
        if len(clean_number) >= 9:
            last_digits = clean_number[-9:]
            cursor = collection.find({})
            async for p in cursor:
                stored = p.get("number", "").replace("+", "").replace(" ", "")
                if stored.endswith(last_digits):
                    return p

        return None

    def _get_cache_key(self, phone_id: str, days: int, page: int, per_page: int) -> str:
        """Generate cache key for stats request."""
        params = f"{phone_id}:{days}:{page}:{per_page}"
        return f"{self.CACHE_PREFIX}{hashlib.md5(params.encode()).hexdigest()}"

    async def _get_cached_stats(self, cache_key: str) -> Optional[Dict]:
        """Get stats from cache if available."""
        if not self.redis:
            return None

        try:
            cached = await self.redis.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache read error: {e}")

        return None

    async def _set_cached_stats(self, cache_key: str, stats: Dict) -> None:
        """Store stats in cache."""
        if not self.redis:
            return

        try:
            await self.redis.setex(
                cache_key,
                self.CACHE_TTL_SECONDS,
                json.dumps(stats, default=str)
            )
        except Exception as e:
            logger.warning(f"Cache write error: {e}")

    async def get_stats(
        self,
        phone_number: str,
        days: int = 30,
        page: int = 1,
        per_page: int = 20,
        include_unanswered: bool = False,
    ) -> CDRStatsResponse:
        """
        Get comprehensive CDR statistics for a phone number.

        Uses a single $facet aggregation for optimal performance.

        Args:
            phone_number: Phone number to get stats for
            days: Number of days to include (1-365)
            page: Page number for recent calls
            per_page: Results per page (1-100)
            include_unanswered: Include unanswered calls in stats

        Returns:
            CDRStatsResponse with all statistics

        Raises:
            ValueError: If phone number not found
        """
        # Ensure indexes exist
        await self.ensure_indexes()

        # Find phone record
        phone_record = await self.find_phone_by_number(phone_number)
        if not phone_record:
            raise ValueError(f"Phone number {phone_number} not found")

        phone_id = phone_record.get("id")
        phone_num = phone_record.get("number")

        # Check cache
        cache_key = self._get_cache_key(phone_id, days, page, per_page)
        cached = await self._get_cached_stats(cache_key)
        if cached:
            logger.debug(f"Cache hit for {phone_id}")
            return CDRStatsResponse(**cached)

        # Build aggregation pipeline
        from_date = datetime.utcnow() - timedelta(days=days)
        skip = (page - 1) * per_page

        # Base match conditions
        base_match = {
            "phone_id": phone_id,
            "created_at": {"$gte": from_date}
        }

        # For stats, typically only count answered calls
        stats_match = base_match.copy()
        if not include_unanswered:
            stats_match["disposition"] = "ANSWERED"

        collection = self.db[self.CALLS_COLLECTION]

        # Single $facet aggregation for all stats
        pipeline = [
            {"$match": base_match},
            {
                "$facet": {
                    # Total count for pagination
                    "total_count": [
                        {"$count": "count"}
                    ],

                    # Summary statistics (answered calls only for billing)
                    "summary": [
                        {"$match": {"disposition": "ANSWERED"} if not include_unanswered else {}},
                        {
                            "$group": {
                                "_id": None,
                                "total_calls": {"$sum": 1},
                                "total_minutes": {
                                    "$sum": {"$divide": [{"$ifNull": ["$billsec_seconds", 0]}, 60]}
                                },
                                "total_cost": {"$sum": {"$ifNull": ["$cost_ghc", 0]}}
                            }
                        }
                    ],

                    # Outbound calls breakdown (calls made FROM this phone)
                    "outbound": [
                        {"$match": {"direction": "outbound", "disposition": "ANSWERED"}},
                        {
                            "$group": {
                                "_id": "$dst",
                                "call_count": {"$sum": 1},
                                "total_minutes": {
                                    "$sum": {"$divide": [{"$ifNull": ["$billsec_seconds", 0]}, 60]}
                                },
                                "total_cost": {"$sum": {"$ifNull": ["$cost_ghc", 0]}},
                                "last_call": {"$max": "$created_at"}
                            }
                        },
                        {"$sort": {"total_minutes": -1}},
                        {"$limit": 50}
                    ],

                    # Inbound calls breakdown (calls made TO this phone)
                    "inbound": [
                        {"$match": {"direction": "inbound", "disposition": "ANSWERED"}},
                        {
                            "$group": {
                                "_id": "$src",
                                "call_count": {"$sum": 1},
                                "total_minutes": {
                                    "$sum": {"$divide": [{"$ifNull": ["$billsec_seconds", 0]}, 60]}
                                },
                                "total_cost": {"$sum": {"$ifNull": ["$cost_ghc", 0]}},
                                "last_call": {"$max": "$created_at"}
                            }
                        },
                        {"$sort": {"total_minutes": -1}},
                        {"$limit": 50}
                    ],

                    # Daily usage
                    "daily": [
                        {"$match": {"disposition": "ANSWERED"} if not include_unanswered else {}},
                        {
                            "$group": {
                                "_id": {
                                    "$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}
                                },
                                "call_count": {"$sum": 1},
                                "total_minutes": {
                                    "$sum": {"$divide": [{"$ifNull": ["$billsec_seconds", 0]}, 60]}
                                },
                                "total_cost": {"$sum": {"$ifNull": ["$cost_ghc", 0]}}
                            }
                        },
                        {"$sort": {"_id": -1}},
                        {"$limit": days}
                    ],

                    # Recent calls with pagination
                    "recent": [
                        {"$sort": {"created_at": -1}},
                        {"$skip": skip},
                        {"$limit": per_page},
                        {
                            "$project": {
                                "call_id": {"$ifNull": ["$uniqueid", "$_id"]},
                                "source": "$src",
                                "destination": "$dst",
                                "direction": {"$ifNull": ["$direction", "unknown"]},
                                "duration_seconds": {"$ifNull": ["$billsec_seconds", "$duration"]},
                                "disposition": 1,
                                "cost": {"$ifNull": ["$cost_ghc", 0]},
                                "timestamp": "$created_at"
                            }
                        }
                    ]
                }
            }
        ]

        # Execute aggregation
        results = None
        async for doc in collection.aggregate(pipeline):
            results = doc
            break

        if not results:
            results = {
                "total_count": [],
                "summary": [],
                "outbound": [],
                "inbound": [],
                "daily": [],
                "recent": []
            }

        # Parse results
        total_count = results["total_count"][0]["count"] if results["total_count"] else 0

        summary_data = results["summary"][0] if results["summary"] else {}
        summary = CallSummary(
            total_calls=summary_data.get("total_calls", 0),
            total_minutes=round(summary_data.get("total_minutes", 0), 2),
            total_cost=round(summary_data.get("total_cost", 0), 2)
        )

        outbound_calls = [
            CallBreakdown(
                number=r.get("_id", "Unknown"),
                direction=CallDirection.OUTBOUND,
                call_count=r.get("call_count", 0),
                total_minutes=round(r.get("total_minutes", 0), 2),
                total_cost=round(r.get("total_cost", 0), 2),
                last_call=r.get("last_call")
            )
            for r in results["outbound"]
        ]

        inbound_calls = [
            CallBreakdown(
                number=r.get("_id", "Unknown"),
                direction=CallDirection.INBOUND,
                call_count=r.get("call_count", 0),
                total_minutes=round(r.get("total_minutes", 0), 2),
                total_cost=round(r.get("total_cost", 0), 2),
                last_call=r.get("last_call")
            )
            for r in results["inbound"]
        ]

        daily_usage = [
            DailyUsage(
                date=r.get("_id", ""),
                call_count=r.get("call_count", 0),
                total_minutes=round(r.get("total_minutes", 0), 2),
                total_cost=round(r.get("total_cost", 0), 2)
            )
            for r in results["daily"]
        ]

        recent_calls = [
            RecentCall(
                call_id=str(r.get("call_id", "")),
                source=r.get("source", ""),
                destination=r.get("destination", ""),
                direction=CallDirection(r.get("direction", "outbound")) if r.get("direction") in ["inbound", "outbound"] else CallDirection.OUTBOUND,
                duration_seconds=r.get("duration_seconds", 0) or 0,
                disposition=r.get("disposition", "UNKNOWN"),
                cost=round(r.get("cost", 0), 2),
                timestamp=r.get("timestamp", datetime.utcnow())
            )
            for r in results["recent"]
        ]

        # Calculate remaining minutes
        credit_balance = phone_record.get("credit_balance", 0)
        cost_per_minute = phone_record.get("cost_per_minute", 0.15)
        remaining_minutes = round(credit_balance / cost_per_minute, 2) if cost_per_minute > 0 else 0

        # Build response
        response = CDRStatsResponse(
            success=True,
            phone_number=phone_num,
            phone_id=phone_id,
            period_days=days,
            summary=summary,
            outbound_calls=outbound_calls,
            inbound_calls=inbound_calls,
            daily_usage=daily_usage,
            recent_calls=recent_calls,
            recent_calls_total=total_count,
            recent_calls_page=page,
            recent_calls_per_page=per_page,
            credit_balance=credit_balance,
            remaining_minutes=remaining_minutes
        )

        # Cache the response
        await self._set_cached_stats(cache_key, response.model_dump())

        return response

    async def invalidate_cache(self, phone_id: str) -> None:
        """
        Invalidate all cached stats for a phone.

        Call this when new CDR records are added.

        Args:
            phone_id: Phone ID to invalidate cache for
        """
        if not self.redis:
            return

        try:
            # Use pattern matching to delete all keys for this phone
            pattern = f"{self.CACHE_PREFIX}*{phone_id}*"
            cursor = 0
            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
                if keys:
                    await self.redis.delete(*keys)
                if cursor == 0:
                    break
            logger.info(f"Invalidated cache for phone {phone_id}")
        except Exception as e:
            logger.warning(f"Cache invalidation error: {e}")


# Singleton instance (will be initialized with DB connection)
_cdr_service: Optional[CDRStatsService] = None


def get_cdr_stats_service(db: AsyncIOMotorDatabase, redis_client=None) -> CDRStatsService:
    """
    Get or create CDR Stats Service instance.

    Args:
        db: MongoDB database
        redis_client: Optional Redis client

    Returns:
        CDRStatsService instance
    """
    global _cdr_service
    if _cdr_service is None:
        _cdr_service = CDRStatsService(db, redis_client)
    return _cdr_service
