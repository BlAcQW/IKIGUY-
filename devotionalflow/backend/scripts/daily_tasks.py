#!/usr/bin/env python3
"""
Fresh Manna Daily Maintenance Tasks
Run this script daily via cron to perform maintenance tasks.

Tasks:
- Check for devotionals that should be published today
- Send daily notifications (if configured)
- Update statistics
- Cleanup tasks
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def check_todays_devotional():
    """Check if today's devotional exists."""
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.DATABASE_NAME]

    today = datetime.utcnow().date()
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = datetime.combine(today, datetime.max.time())

    devotional = await db.devotionals.find_one({
        "status": "published",
        "published_at": {
            "$gte": start_of_day,
            "$lte": end_of_day
        }
    })

    if devotional:
        logger.info(f"✓ Today's devotional found: {devotional['title']}")
    else:
        logger.warning(f"⚠ No devotional found for today ({today.isoformat()})")

    client.close()
    return devotional is not None


async def update_daily_statistics():
    """Update daily statistics."""
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.DATABASE_NAME]

    # Count total devotionals
    total_devotionals = await db.devotionals.count_documents({"status": "published"})

    # Count total views
    pipeline = [
        {"$group": {"_id": None, "total_views": {"$sum": "$views_count"}}}
    ]
    result = await db.devotionals.aggregate(pipeline).to_list(length=1)
    total_views = result[0]["total_views"] if result else 0

    # Count total users
    total_users = await db.users.count_documents({})

    logger.info(f"Daily Statistics:")
    logger.info(f"  - Total Devotionals: {total_devotionals}")
    logger.info(f"  - Total Views: {total_views}")
    logger.info(f"  - Total Users: {total_users}")

    client.close()


async def check_upcoming_gaps():
    """Check for gaps in upcoming devotional schedule."""
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.DATABASE_NAME]

    # Check next 7 days
    today = datetime.utcnow().date()
    gaps = []

    for day_offset in range(1, 8):
        check_date = today + timedelta(days=day_offset)
        start_of_day = datetime.combine(check_date, datetime.min.time())
        end_of_day = datetime.combine(check_date, datetime.max.time())

        devotional = await db.devotionals.find_one({
            "status": "published",
            "published_at": {
                "$gte": start_of_day,
                "$lte": end_of_day
            }
        })

        if not devotional:
            gaps.append(check_date.isoformat())

    if gaps:
        logger.warning(f"⚠ Schedule gaps found in next 7 days: {', '.join(gaps)}")
    else:
        logger.info("✓ No schedule gaps in next 7 days")

    client.close()
    return gaps


async def main():
    """Run all daily tasks."""
    logger.info("=" * 60)
    logger.info("Fresh Manna - Daily Maintenance Tasks")
    logger.info("=" * 60)
    logger.info(f"Run time: {datetime.utcnow().isoformat()}")
    logger.info("")

    try:
        # Check today's devotional
        logger.info("Checking today's devotional...")
        await check_todays_devotional()
        logger.info("")

        # Update statistics
        logger.info("Updating daily statistics...")
        await update_daily_statistics()
        logger.info("")

        # Check for gaps
        logger.info("Checking schedule for gaps...")
        await check_upcoming_gaps()
        logger.info("")

        logger.info("=" * 60)
        logger.info("✓ Daily tasks completed successfully")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error running daily tasks: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
