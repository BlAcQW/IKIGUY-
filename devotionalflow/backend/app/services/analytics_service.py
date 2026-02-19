"""
Analytics service for DevotionalFlow.
Provides comprehensive analytics and insights for platform engagement.
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from bson import ObjectId
from fastapi import HTTPException, status
import logging

from app.db.mongodb import get_database

logger = logging.getLogger(__name__)


async def get_dashboard_stats(
    days: int = 30,
    author_id: Optional[str] = None
) -> Dict:
    """
    Get dashboard statistics for analytics.

    Args:
        days: Number of days to look back (default: 30)
        author_id: Optional author ID to filter by

    Returns:
        Dictionary with dashboard statistics
    """
    db = get_database()
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    previous_start = start_date - timedelta(days=days)
    
    # Build query
    query = {
        "published_at": {"$gte": start_date, "$lte": end_date},
        "status": "published"
    }
    if author_id:
        query["author_id"] = ObjectId(author_id)
    
    previous_query = {
        "published_at": {"$gte": previous_start, "$lt": start_date},
        "status": "published"
    }
    if author_id:
        previous_query["author_id"] = ObjectId(author_id)
    
    # Get current period stats
    current_devotionals = await db.devotionals.find(query).to_list(length=None)
    previous_devotionals = await db.devotionals.find(previous_query).to_list(length=None)
    
    # Calculate totals
    total_views = sum(d.get("views_count", 0) for d in current_devotionals)
    total_likes = sum(d.get("likes_count", 0) for d in current_devotionals)
    total_comments = sum(d.get("comments_count", 0) for d in current_devotionals)
    total_shares = sum(d.get("shares_count", 0) for d in current_devotionals)
    total_bookmarks = sum(d.get("bookmarks_count", 0) for d in current_devotionals)
    
    # Previous period totals
    prev_views = sum(d.get("views_count", 0) for d in previous_devotionals)
    prev_likes = sum(d.get("likes_count", 0) for d in previous_devotionals)
    prev_comments = sum(d.get("comments_count", 0) for d in previous_devotionals)
    prev_shares = sum(d.get("shares_count", 0) for d in previous_devotionals)
    
    # Calculate changes
    views_change = ((total_views - prev_views) / prev_views * 100) if prev_views > 0 else 0
    likes_change = ((total_likes - prev_likes) / prev_likes * 100) if prev_likes > 0 else 0
    comments_change = ((total_comments - prev_comments) / prev_comments * 100) if prev_comments > 0 else 0
    shares_change = ((total_shares - prev_shares) / prev_shares * 100) if prev_shares > 0 else 0
    
    # Get unique readers
    unique_readers = await db.reading_history.distinct(
        "user_id",
        {"created_at": {"$gte": start_date, "$lte": end_date}}
    )
    total_readers = len(unique_readers)
    
    # Previous period readers
    prev_unique_readers = await db.reading_history.distinct(
        "user_id",
        {"created_at": {"$gte": previous_start, "$lt": start_date}}
    )
    prev_readers = len(prev_unique_readers)
    readers_change = ((total_readers - prev_readers) / prev_readers * 100) if prev_readers > 0 else 0
    
    # Calculate engagement rate
    total_interactions = total_likes + total_comments + total_shares
    engagement_rate = (total_interactions / total_views * 100) if total_views > 0 else 0
    
    # Get average reading time
    reading_history = await db.reading_history.find({
        "created_at": {"$gte": start_date, "$lte": end_date},
        "time_spent": {"$gt": 0}
    }).to_list(length=1000)
    
    avg_read_time = 0
    if reading_history:
        total_time = sum(r.get("time_spent", 0) for r in reading_history)
        avg_read_time = (total_time / len(reading_history)) / 60  # Convert to minutes
    
    # Devotionals published
    devotionals_published = len(current_devotionals)
    prev_published = len(previous_devotionals)
    published_change = ((devotionals_published - prev_published) / prev_published * 100) if prev_published > 0 else 0
    
    return {
        "total_readers": total_readers,
        "readers_change": readers_change,
        "devotionals_published": devotionals_published,
        "published_change": published_change,
        "engagement_rate": round(engagement_rate, 2),
        "total_views": total_views,
        "views_change": round(views_change, 2),
        "total_likes": total_likes,
        "likes_change": round(likes_change, 2),
        "total_comments": total_comments,
        "comments_change": round(comments_change, 2),
        "total_shares": total_shares,
        "shares_change": round(shares_change, 2),
        "total_bookmarks": total_bookmarks,
        "avg_read_time": round(avg_read_time, 2),
        "period_days": days,
    }


async def get_engagement_trends(
    days: int = 30,
    granularity: str = "daily",
    author_id: Optional[str] = None
) -> Dict:
    """
    Get engagement trends over time.

    Args:
        days: Number of days to look back
        granularity: "daily", "weekly", or "monthly"
        author_id: Optional author ID to filter by

    Returns:
        Dictionary with time series data
    """
    db = get_database()
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    query = {
        "published_at": {"$gte": start_date, "$lte": end_date},
        "status": "published"
    }
    if author_id:
        query["author_id"] = ObjectId(author_id)
    
    devotionals = await db.devotionals.find(query).to_list(length=None)
    
    # Group by time period
    trends = {}
    
    for dev in devotionals:
        published_at = dev.get("published_at")
        if not published_at:
            continue
        
        if isinstance(published_at, str):
            published_at = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
        
        # Determine time key based on granularity
        if granularity == "daily":
            time_key = published_at.strftime("%Y-%m-%d")
        elif granularity == "weekly":
            week_start = published_at - timedelta(days=published_at.weekday())
            time_key = week_start.strftime("%Y-%W")
        else:  # monthly
            time_key = published_at.strftime("%Y-%m")
        
        if time_key not in trends:
            trends[time_key] = {
                "views": 0,
                "likes": 0,
                "comments": 0,
                "shares": 0,
                "bookmarks": 0,
            }
        
        trends[time_key]["views"] += dev.get("views_count", 0)
        trends[time_key]["likes"] += dev.get("likes_count", 0)
        trends[time_key]["comments"] += dev.get("comments_count", 0)
        trends[time_key]["shares"] += dev.get("shares_count", 0)
        trends[time_key]["bookmarks"] += dev.get("bookmarks_count", 0)
    
    # Convert to sorted list
    trend_list = [
        {
            "date": key,
            "views": data["views"],
            "likes": data["likes"],
            "comments": data["comments"],
            "shares": data["shares"],
            "bookmarks": data["bookmarks"],
        }
        for key, data in sorted(trends.items())
    ]
    
    return {
        "trends": trend_list,
        "granularity": granularity,
        "period_days": days,
    }


async def get_top_devotionals(
    limit: int = 10,
    metric: str = "views",
    days: int = 30,
    author_id: Optional[str] = None
) -> List[Dict]:
    """
    Get top-performing devotionals.

    Args:
        limit: Number of devotionals to return
        metric: Sort by "views", "likes", "comments", "shares", or "engagement"
        days: Number of days to look back
        author_id: Optional author ID to filter by

    Returns:
        List of top devotionals
    """
    db = get_database()
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    query = {
        "published_at": {"$gte": start_date, "$lte": end_date},
        "status": "published"
    }
    if author_id:
        query["author_id"] = ObjectId(author_id)
    
    # Determine sort field
    sort_field = f"{metric}_count" if metric != "engagement" else None
    
    if sort_field:
        cursor = db.devotionals.find(query).sort(sort_field, -1).limit(limit)
    else:
        # For engagement, calculate and sort
        cursor = db.devotionals.find(query).limit(limit * 2)  # Get more to calculate engagement
    
    devotionals = await cursor.to_list(length=None)
    
    # Calculate engagement for each if needed
    if metric == "engagement":
        for dev in devotionals:
            views = dev.get("views_count", 0)
            interactions = (
                dev.get("likes_count", 0) +
                dev.get("comments_count", 0) +
                dev.get("shares_count", 0)
            )
            dev["_engagement"] = (interactions / views * 100) if views > 0 else 0
        devotionals.sort(key=lambda x: x.get("_engagement", 0), reverse=True)
        devotionals = devotionals[:limit]
    
    # Get author names
    author_ids = [ObjectId(d["author_id"]) for d in devotionals if d.get("author_id")]
    authors = {}
    if author_ids:
        author_cursor = db.users.find({"_id": {"$in": author_ids}})
        author_list = await author_cursor.to_list(length=None)
        authors = {str(a["_id"]): a.get("name", "Unknown") for a in author_list}
    
    result = []
    for dev in devotionals:
        engagement = (
            (dev.get("likes_count", 0) + dev.get("comments_count", 0) + dev.get("shares_count", 0)) /
            dev.get("views_count", 1) * 100
        ) if dev.get("views_count", 0) > 0 else 0
        
        result.append({
            "id": str(dev["_id"]),
            "title": dev.get("title", "Untitled"),
            "author_id": str(dev.get("author_id", "")),
            "author_name": authors.get(str(dev.get("author_id", "")), "Unknown"),
            "views": dev.get("views_count", 0),
            "likes": dev.get("likes_count", 0),
            "comments": dev.get("comments_count", 0),
            "shares": dev.get("shares_count", 0),
            "bookmarks": dev.get("bookmarks_count", 0),
            "engagement_rate": round(engagement, 2),
            "published_at": dev.get("published_at").isoformat() if dev.get("published_at") else None,
        })
    
    return result


async def get_reader_insights(
    days: int = 30,
    author_id: Optional[str] = None
) -> Dict:
    """
    Get reader insights including device breakdown, time of day, etc.

    Args:
        days: Number of days to look back
        author_id: Optional author ID to filter by

    Returns:
        Dictionary with reader insights
    """
    db = get_database()
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get reading history
    query = {"created_at": {"$gte": start_date, "$lte": end_date}}
    
    # If filtering by author, get their devotional IDs first
    if author_id:
        devotional_ids = await db.devotionals.distinct(
            "_id",
            {"author_id": ObjectId(author_id), "status": "published"}
        )
        query["devotional_id"] = {"$in": devotional_ids}
    
    reading_history = await db.reading_history.find(query).to_list(length=None)
    
    # Device breakdown
    device_breakdown = {}
    time_of_day = {}
    total_readers = set()
    returning_readers = set()
    reader_visits = {}
    
    for record in reading_history:
        user_id = str(record.get("user_id", ""))
        total_readers.add(user_id)
        
        # Track visits per user
        if user_id not in reader_visits:
            reader_visits[user_id] = 0
        reader_visits[user_id] += 1
        
        if reader_visits[user_id] >= 2:
            returning_readers.add(user_id)
        
        # Device (default to mobile if not specified)
        device = record.get("device_type", "mobile")
        if not device or device == "unknown":
            device = "mobile"  # Default assumption for mobile-first platform
        device_breakdown[device] = device_breakdown.get(device, 0) + 1
        
        # Time of day
        created_at = record.get("created_at")
        if created_at:
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            hour = created_at.hour
            time_slot = f"{hour:02d}:00"
            time_of_day[time_slot] = time_of_day.get(time_slot, 0) + 1
    
    # Calculate returning reader percentage
    returning_rate = (len(returning_readers) / len(total_readers) * 100) if total_readers else 0
    
    # Get referral sources from shares
    share_query = {"created_at": {"$gte": start_date, "$lte": end_date}}
    if author_id:
        devotional_ids = await db.devotionals.distinct(
            "_id",
            {"author_id": ObjectId(author_id), "status": "published"}
        )
        share_query["devotional_id"] = {"$in": devotional_ids}
    
    shares = await db.shares.find(share_query).to_list(length=None)
    referral_sources = {}
    for share in shares:
        platform = share.get("platform", "unknown")
        referral_sources[platform] = referral_sources.get(platform, 0) + 1
    
    # Geographic data (if available in reading history)
    geographic = {}
    for record in reading_history:
        country = record.get("country") or record.get("country_code") or "unknown"
        if country and country != "unknown":
            geographic[country] = geographic.get(country, 0) + 1
    
    return {
        "total_readers": len(total_readers),
        "returning_readers": len(returning_readers),
        "returning_rate": round(returning_rate, 2),
        "device_breakdown": device_breakdown,
        "time_of_day": dict(sorted(time_of_day.items())),
        "referral_sources": referral_sources,
        "geographic": geographic,
    }


async def get_audience_growth(
    days: int = 90,
    author_id: Optional[str] = None
) -> Dict:
    """
    Get audience growth and retention metrics.

    Args:
        days: Number of days to analyze
        author_id: Optional author ID to filter by

    Returns:
        Dictionary with growth and retention data
    """
    db = get_database()
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get new readers (first time reading)
    query = {"created_at": {"$gte": start_date, "$lte": end_date}}
    
    if author_id:
        devotional_ids = await db.devotionals.distinct(
            "_id",
            {"author_id": ObjectId(author_id), "status": "published"}
        )
        query["devotional_id"] = {"$in": devotional_ids}
    
    # Get all reading history in period
    all_readings = await db.reading_history.find(query).to_list(length=None)
    
    # Get first reading per user (ever)
    user_first_readings = {}
    for reading in all_readings:
        user_id = str(reading.get("user_id", ""))
        created_at = reading.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        
        if user_id not in user_first_readings or created_at < user_first_readings[user_id]:
            user_first_readings[user_id] = created_at
    
    # New readers (first reading in this period)
    new_readers = [
        uid for uid, first_date in user_first_readings.items()
        if first_date >= start_date
    ]
    
    # Retention: readers who read 30+ days ago and still reading
    thirty_days_ago = end_date - timedelta(days=30)
    old_readers = set()
    recent_readers = set()
    
    for reading in all_readings:
        user_id = str(reading.get("user_id", ""))
        created_at = reading.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        
        if created_at < thirty_days_ago:
            old_readers.add(user_id)
        if created_at >= thirty_days_ago:
            recent_readers.add(user_id)
    
    retained_readers = old_readers.intersection(recent_readers)
    retention_rate = (len(retained_readers) / len(old_readers) * 100) if old_readers else 0
    
    # Churn: readers who read 30+ days ago but not recently
    churned_readers = old_readers - recent_readers
    churn_rate = (len(churned_readers) / len(old_readers) * 100) if old_readers else 0
    
    return {
        "new_readers": len(new_readers),
        "total_readers": len(user_first_readings),
        "retained_readers": len(retained_readers),
        "retention_rate": round(retention_rate, 2),
        "churned_readers": len(churned_readers),
        "churn_rate": round(churn_rate, 2),
        "period_days": days,
    }

