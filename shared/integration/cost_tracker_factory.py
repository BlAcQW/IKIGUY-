"""
Cost Tracker Factory

Factory for creating InternalCostTracker instances with database persistence.

Author: KasaAI Team
Date: 2025-10-30
"""

import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)


def create_cost_tracker_with_db(mongodb_client: Optional[AsyncIOMotorClient] = None, database_name: str = "kasaai_core"):
    """
    Create an InternalCostTracker with database persistence enabled.

    Args:
        mongodb_client: MongoDB async client. If None, creates tracker without persistence.
        database_name: Database name for cost records

    Returns:
        InternalCostTracker instance with optional database persistence
    """
    from .internal_cost_tracker import InternalCostTracker

    if mongodb_client:
        try:
            # Import here to avoid circular dependencies
            from apps.core_backend.backend.services.cost_record_service import CostRecordService

            cost_record_service = CostRecordService(mongodb_client, database_name)
            logger.info("✅ Cost tracker initialized with database persistence")
            return InternalCostTracker(cost_record_service=cost_record_service)
        except ImportError as e:
            logger.warning(f"⚠️  Could not import CostRecordService: {e}. Cost tracking will work but not persist to database.")
            return InternalCostTracker()
    else:
        logger.info("ℹ️  Cost tracker initialized without database persistence (in-memory only)")
        return InternalCostTracker()


async def flush_cost_tracker(cost_tracker):
    """
    Flush pending cost records to database.

    Args:
        cost_tracker: InternalCostTracker instance

    Returns:
        Number of records saved
    """
    if hasattr(cost_tracker, 'flush_pending_saves'):
        try:
            saved_count = await cost_tracker.flush_pending_saves()
            if saved_count > 0:
                logger.info(f"💾 Flushed {saved_count} cost records to database")
            return saved_count
        except Exception as e:
            logger.error(f"❌ Error flushing cost records: {e}")
            return 0
    return 0
