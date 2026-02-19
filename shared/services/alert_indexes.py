"""
MongoDB Indexes for Alert Collections

Creates optimized indexes for alert_history and alert_configs collections.
"""

import logging
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


async def create_alert_indexes(db: AsyncIOMotorDatabase):
    """
    Create indexes for alert collections.

    Args:
        db: MongoDB database instance
    """
    try:
        # Alert History Collection Indexes
        alert_history = db.alert_history

        # 1. Index for cooldown checks (provider + tenant_id + sent_at)
        await alert_history.create_index(
            [("provider", 1), ("tenant_id", 1), ("sent_at", -1)],
            name="idx_cooldown_check"
        )

        # 2. Index for history queries (tenant_id + sent_at)
        await alert_history.create_index(
            [("tenant_id", 1), ("sent_at", -1)],
            name="idx_history_query"
        )

        # 3. Index for provider-specific queries
        await alert_history.create_index(
            [("provider", 1), ("sent_at", -1)],
            name="idx_provider_history"
        )

        # 4. Index for severity queries
        await alert_history.create_index(
            [("severity", 1), ("sent_at", -1)],
            name="idx_severity_history"
        )

        # 5. Index for acknowledgment queries
        await alert_history.create_index(
            [("acknowledged", 1), ("sent_at", -1)],
            name="idx_acknowledgment"
        )

        # 6. TTL index to auto-delete old alerts (after 90 days)
        await alert_history.create_index(
            [("sent_at", 1)],
            name="idx_ttl_cleanup",
            expireAfterSeconds=7776000  # 90 days
        )

        logger.info("✅ Alert history indexes created")

        # Alert Configs Collection Indexes
        alert_configs = db.alert_configs

        # 1. Index for tenant lookups
        await alert_configs.create_index(
            [("tenant_id", 1)],
            name="idx_tenant_config",
            unique=True
        )

        # 2. Index for updated_at queries
        await alert_configs.create_index(
            [("updated_at", -1)],
            name="idx_config_updates"
        )

        logger.info("✅ Alert configs indexes created")

        return {
            "success": True,
            "alert_history_indexes": 6,
            "alert_configs_indexes": 2
        }

    except Exception as e:
        logger.error(f"Failed to create alert indexes: {e}")
        return {
            "success": False,
            "error": str(e)
        }
