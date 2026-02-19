"""
Analytics Service.

Tracks usage, costs, and performance metrics across all AI services.

Usage:
    analytics = AnalyticsService(mongodb_uri="...")
    await analytics.track_voice_qa(user_id, book_id, costs, duration)
    stats = await analytics.get_usage_stats(user_id, period="month")
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Analytics event types."""
    VOICE_QA = "voice_qa"  # Voice Q&A interaction
    STT = "stt"  # Speech-to-text
    TTS = "tts"  # Text-to-speech
    RAG = "rag"  # RAG query
    NARRATION = "narration"  # Audio narration playback
    BOOK_VIEW = "book_view"  # Book detail view
    BOOK_PLAY = "book_play"  # Start playing audiobook
    TOP_UP = "top_up"  # Wallet top-up
    SIGN_UP = "sign_up"  # User signup
    LOGIN = "login"  # User login


class UsageEvent(BaseModel):
    """Usage event model."""
    event_type: EventType
    user_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Identifiers
    book_id: Optional[str] = None
    session_id: Optional[str] = None
    interaction_id: Optional[str] = None

    # Costs & usage
    cost_credits: int = 0
    duration_seconds: Optional[float] = None
    tokens_input: Optional[int] = None
    tokens_output: Optional[int] = None

    # Providers
    stt_provider: Optional[str] = None
    tts_provider: Optional[str] = None
    llm_provider: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UsageStats(BaseModel):
    """Usage statistics."""
    user_id: str
    period_start: datetime
    period_end: datetime

    # Event counts
    total_events: int = 0
    voice_qa_count: int = 0
    narration_minutes: float = 0.0
    books_viewed: int = 0
    books_played: int = 0

    # Costs
    total_cost_credits: int = 0
    stt_cost: int = 0
    tts_cost: int = 0
    rag_cost: int = 0
    narration_cost: int = 0

    # Top books
    top_books: List[Dict[str, Any]] = Field(default_factory=list)

    # Provider usage
    provider_stats: Dict[str, Any] = Field(default_factory=dict)


class AnalyticsService:
    """
    Analytics service for tracking usage and generating insights.

    Stores events in MongoDB and provides aggregation queries.
    """

    def __init__(self, mongodb_uri: Optional[str] = None):
        """
        Initialize analytics service.

        Args:
            mongodb_uri: MongoDB connection string
        """
        self.mongodb_uri = mongodb_uri
        self.db = None  # Will be initialized when MongoDB is connected

        logger.info("Initialized AnalyticsService")

    async def connect(self):
        """Connect to MongoDB."""
        if not self.mongodb_uri:
            logger.warning("No MongoDB URI provided, analytics will not be persisted")
            return

        # TODO: Connect to MongoDB
        # from motor.motor_asyncio import AsyncIOMotorClient
        # self.client = AsyncIOMotorClient(self.mongodb_uri)
        # self.db = self.client.analytics
        pass

    async def track_event(self, event: UsageEvent) -> str:
        """
        Track a usage event.

        Args:
            event: Usage event to track

        Returns:
            Event ID
        """
        event_id = f"event_{datetime.utcnow().timestamp()}"

        # TODO: Store in MongoDB
        # await self.db.events.insert_one({
        #     "event_id": event_id,
        #     **event.dict()
        # })

        logger.info(f"Tracked event: {event.event_type} for user={event.user_id}, cost={event.cost_credits}")
        return event_id

    async def track_voice_qa(
        self,
        user_id: str,
        book_id: str,
        costs: Dict[str, int],
        duration: float,
        stt_provider: str = "openai",
        tts_provider: str = "openai",
        llm_provider: str = "gemini"
    ) -> str:
        """
        Track voice Q&A interaction.

        Args:
            user_id: User identifier
            book_id: Book identifier
            costs: Cost breakdown (stt, rag, tts, total)
            duration: Duration in seconds
            stt_provider: STT provider used
            tts_provider: TTS provider used
            llm_provider: LLM provider used

        Returns:
            Event ID
        """
        event = UsageEvent(
            event_type=EventType.VOICE_QA,
            user_id=user_id,
            book_id=book_id,
            cost_credits=costs.get("total", 0),
            duration_seconds=duration,
            stt_provider=stt_provider,
            tts_provider=tts_provider,
            llm_provider=llm_provider,
            metadata={
                "stt_cost": costs.get("stt", 0),
                "rag_cost": costs.get("rag", 0),
                "tts_cost": costs.get("tts", 0),
            }
        )
        return await self.track_event(event)

    async def track_narration(
        self,
        user_id: str,
        book_id: str,
        duration_minutes: float,
        cost_credits: int
    ) -> str:
        """
        Track narration playback.

        Args:
            user_id: User identifier
            book_id: Book identifier
            duration_minutes: Playback duration in minutes
            cost_credits: Credits spent

        Returns:
            Event ID
        """
        event = UsageEvent(
            event_type=EventType.NARRATION,
            user_id=user_id,
            book_id=book_id,
            cost_credits=cost_credits,
            duration_seconds=duration_minutes * 60,
            metadata={"duration_minutes": duration_minutes}
        )
        return await self.track_event(event)

    async def get_usage_stats(
        self,
        user_id: str,
        period: str = "month"
    ) -> UsageStats:
        """
        Get usage statistics for a user.

        Args:
            user_id: User identifier
            period: Period (day, week, month, year, all)

        Returns:
            Usage statistics
        """
        # Calculate period boundaries
        now = datetime.utcnow()
        if period == "day":
            period_start = now - timedelta(days=1)
        elif period == "week":
            period_start = now - timedelta(weeks=1)
        elif period == "month":
            period_start = now - timedelta(days=30)
        elif period == "year":
            period_start = now - timedelta(days=365)
        else:  # all
            period_start = datetime(2020, 1, 1)

        # TODO: Aggregate from MongoDB
        # events = await self.db.events.find({
        #     "user_id": user_id,
        #     "timestamp": {"$gte": period_start, "$lte": now}
        # }).to_list()

        # Mock stats for development
        stats = UsageStats(
            user_id=user_id,
            period_start=period_start,
            period_end=now,
            total_events=45,
            voice_qa_count=15,
            narration_minutes=120.0,
            books_viewed=8,
            books_played=3,
            total_cost_credits=300,
            stt_cost=60,
            tts_cost=150,
            rag_cost=30,
            narration_cost=60,
            top_books=[
                {"book_id": "1", "title": "The Midnight Library", "plays": 5},
                {"book_id": "2", "title": "Atomic Habits", "plays": 3},
            ],
            provider_stats={
                "stt": {"openai": 15},
                "tts": {"openai": 12, "elevenlabs": 3},
                "llm": {"gemini": 15}
            }
        )

        logger.info(f"Retrieved usage stats for user={user_id}, period={period}")
        return stats

    async def get_admin_analytics(
        self,
        period: str = "month"
    ) -> Dict[str, Any]:
        """
        Get admin-level analytics (all users).

        Args:
            period: Period (day, week, month, year, all)

        Returns:
            Admin analytics data
        """
        # Calculate period boundaries
        now = datetime.utcnow()
        if period == "day":
            period_start = now - timedelta(days=1)
        elif period == "week":
            period_start = now - timedelta(weeks=1)
        elif period == "month":
            period_start = now - timedelta(days=30)
        elif period == "year":
            period_start = now - timedelta(days=365)
        else:  # all
            period_start = datetime(2020, 1, 1)

        # TODO: Aggregate from MongoDB
        # Mock data for development
        analytics = {
            "period_start": period_start.isoformat(),
            "period_end": now.isoformat(),

            # User metrics
            "total_users": 150,
            "active_users": 85,
            "new_users": 12,

            # Usage metrics
            "total_events": 2450,
            "voice_qa_count": 850,
            "narration_minutes": 12500.0,
            "books_viewed": 420,
            "books_played": 180,

            # Cost metrics
            "total_cost_credits": 45000,
            "total_revenue_usd": 450.00,
            "avg_cost_per_user": 300,

            # Top books
            "top_books": [
                {"book_id": "1", "title": "The Midnight Library", "plays": 85, "revenue": 170.00},
                {"book_id": "2", "title": "Atomic Habits", "plays": 62, "revenue": 124.00},
                {"book_id": "3", "title": "Sapiens", "plays": 48, "revenue": 96.00},
            ],

            # Provider usage
            "provider_stats": {
                "stt": {
                    "openai": {"count": 850, "cost": 12750},
                    "google": {"count": 0, "cost": 0},
                },
                "tts": {
                    "openai": {"count": 720, "cost": 21600},
                    "elevenlabs": {"count": 130, "cost": 6500},
                },
                "llm": {
                    "gemini": {"count": 850, "cost": 4250},
                }
            },

            # Time series data (daily)
            "time_series": [
                {"date": "2025-10-18", "events": 95, "cost": 1500, "revenue": 15.00},
                {"date": "2025-10-19", "events": 102, "cost": 1620, "revenue": 16.20},
                {"date": "2025-10-20", "events": 88, "cost": 1400, "revenue": 14.00},
                {"date": "2025-10-21", "events": 110, "cost": 1750, "revenue": 17.50},
                {"date": "2025-10-22", "events": 98, "cost": 1560, "revenue": 15.60},
                {"date": "2025-10-23", "events": 105, "cost": 1670, "revenue": 16.70},
                {"date": "2025-10-24", "events": 92, "cost": 1500, "revenue": 15.00},
            ]
        }

        logger.info(f"Retrieved admin analytics for period={period}")
        return analytics

    async def get_provider_comparison(self) -> Dict[str, Any]:
        """
        Get provider performance comparison.

        Returns:
            Provider comparison data
        """
        # Mock data for development
        comparison = {
            "stt_providers": [
                {
                    "provider": "openai",
                    "name": "OpenAI Whisper",
                    "usage_count": 850,
                    "total_cost": 12750,
                    "avg_cost_per_request": 15,
                    "avg_duration_ms": 2500,
                    "success_rate": 0.98
                },
                {
                    "provider": "google",
                    "name": "Google STT",
                    "usage_count": 0,
                    "total_cost": 0,
                    "avg_cost_per_request": 0,
                    "avg_duration_ms": 0,
                    "success_rate": 0
                },
            ],
            "tts_providers": [
                {
                    "provider": "openai",
                    "name": "OpenAI TTS",
                    "usage_count": 720,
                    "total_cost": 21600,
                    "avg_cost_per_request": 30,
                    "avg_duration_ms": 1800,
                    "success_rate": 0.99
                },
                {
                    "provider": "elevenlabs",
                    "name": "ElevenLabs",
                    "usage_count": 130,
                    "total_cost": 6500,
                    "avg_cost_per_request": 50,
                    "avg_duration_ms": 2200,
                    "success_rate": 0.97
                },
            ],
            "llm_providers": [
                {
                    "provider": "gemini",
                    "name": "Gemini 2.5 Flash",
                    "usage_count": 850,
                    "total_cost": 4250,
                    "avg_cost_per_request": 5,
                    "avg_duration_ms": 1500,
                    "success_rate": 0.99
                },
            ]
        }

        logger.info("Retrieved provider comparison")
        return comparison


# Singleton instance
_analytics_service: Optional[AnalyticsService] = None


def get_analytics_service(mongodb_uri: Optional[str] = None) -> AnalyticsService:
    """
    Get global analytics service instance.

    Args:
        mongodb_uri: MongoDB connection string

    Returns:
        Analytics service instance
    """
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService(mongodb_uri)
    return _analytics_service
