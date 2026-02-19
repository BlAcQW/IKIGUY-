"""
Analytics models for DevotionalFlow.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime


class DashboardStatsResponse(BaseModel):
    """Dashboard statistics response."""
    total_readers: int
    readers_change: float
    devotionals_published: int
    published_change: float
    engagement_rate: float
    total_views: int
    views_change: float
    total_likes: int
    likes_change: float
    total_comments: int
    comments_change: float
    total_shares: int
    shares_change: float
    total_bookmarks: int
    avg_read_time: float
    period_days: int


class EngagementTrendPoint(BaseModel):
    """Single point in engagement trend."""
    date: str
    views: int
    likes: int
    comments: int
    shares: int
    bookmarks: int


class EngagementTrendsResponse(BaseModel):
    """Engagement trends response."""
    trends: List[EngagementTrendPoint]
    granularity: str
    period_days: int


class TopDevotionalResponse(BaseModel):
    """Top devotional response."""
    id: str
    title: str
    author_id: str
    author_name: str
    views: int
    likes: int
    comments: int
    shares: int
    bookmarks: int
    engagement_rate: float
    published_at: Optional[str] = None


class ReaderInsightsResponse(BaseModel):
    """Reader insights response."""
    total_readers: int
    returning_readers: int
    returning_rate: float
    device_breakdown: Dict[str, int]
    time_of_day: Dict[str, int]
    referral_sources: Dict[str, int]
    geographic: Dict[str, int]


class AudienceGrowthResponse(BaseModel):
    """Audience growth and retention response."""
    new_readers: int
    total_readers: int
    retained_readers: int
    retention_rate: float
    churned_readers: int
    churn_rate: float
    period_days: int

