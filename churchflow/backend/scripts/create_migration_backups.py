"""
Create Migration Backups

Creates backups of all critical collections before migration.

Usage:
    python create_migration_backups.py [--database=churchflow]
"""

import asyncio
import logging
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Configuration
MONGODB_URL = "mongodb://admin:aawwER4444%25@127.0.0.1:27017/{database}?authSource=admin"

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


async def create_migration_backups(database_name: str = "churchflow"):
    """
    Create backups of all critical collections before migration.

    Args:
        database_name: Name of database to backup

    Returns:
        Dictionary of backup results
    """

    logger.info("=" * 80)
    logger.info("CREATING MIGRATION BACKUPS")
    logger.info("=" * 80)

    # Connect to MongoDB
    mongo_url = MONGODB_URL.format(database=database_name)
    client = AsyncIOMotorClient(mongo_url)
    db = client.get_default_database()

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    collections_to_backup = [
        "branches",
        "bus_routes",
        "conferences",
        "organization_memberships",
        "organization_users",
        "session_attendance",
        "sms_campaigns",
        "wallets",
        "conference_registrations",
        "conference_sessions",
        "bus_registrations",
        "donations",
        "donor_profiles",
        "journey_stages",
        "subscriptions",
        "usage_metrics"
    ]

    results = {
        "backups_created": 0,
        "failed": [],
        "timestamp": timestamp
    }

    for coll_name in collections_to_backup:
        backup_name = f"{coll_name}_backup_org_migration_{timestamp}"

        try:
            # Check if collection exists
            all_collections = await db.list_collection_names()
            if coll_name not in all_collections:
                logger.info(f"  ⊘ {coll_name}: collection doesn't exist, skipping")
                continue

            # Get document count
            doc_count = await db[coll_name].count_documents({})

            if doc_count == 0:
                logger.info(f"  ⊘ {coll_name}: empty collection, skipping")
                continue

            logger.info(f"  Backing up {coll_name} ({doc_count} documents)...")

            # Drop existing backup if present
            if backup_name in all_collections:
                await db[backup_name].drop()
                logger.info(f"    Dropped existing backup: {backup_name}")

            # Copy collection using aggregation
            await db[coll_name].aggregate([
                {"$match": {}},
                {"$out": backup_name}
            ]).to_list(length=None)

            # Verify backup
            backup_count = await db[backup_name].count_documents({})

            if backup_count == doc_count:
                logger.info(f"  ✓ {backup_name}: {backup_count} documents backed up")
                results["backups_created"] += 1
            else:
                logger.error(f"  ❌ {backup_name}: backup verification failed ({backup_count}/{doc_count})")
                results["failed"].append(f"{coll_name}: count mismatch")

        except Exception as e:
            logger.error(f"  ❌ {coll_name}: backup failed - {str(e)}")
            results["failed"].append(f"{coll_name}: {str(e)}")

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("BACKUP SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Backups Created: {results['backups_created']}/{len(collections_to_backup)}")
    logger.info(f"Timestamp: {timestamp}")

    if results["failed"]:
        logger.error(f"\nFailed Backups: {len(results['failed'])}")
        for failure in results["failed"]:
            logger.error(f"  ❌ {failure}")

    if results["backups_created"] == len(collections_to_backup):
        logger.info("\n✅ All backups created successfully")
    elif results["backups_created"] > 0:
        logger.warning(f"\n⚠ Partial success: {results['backups_created']} backups created")
    else:
        logger.error("\n❌ No backups created")

    client.close()
    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create ChurchFlow Migration Backups")
    parser.add_argument("--database", default="churchflow", help="Database name (default: churchflow)")

    args = parser.parse_args()

    try:
        results = asyncio.run(create_migration_backups(database_name=args.database))

        # Exit with error code if no backups created
        sys.exit(0 if results["backups_created"] > 0 else 1)

    except Exception as e:
        logger.error(f"Backup creation failed with exception: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
