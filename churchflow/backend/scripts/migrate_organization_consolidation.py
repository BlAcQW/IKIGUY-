"""
ChurchFlow Organization Consolidation Migration

Consolidates all data under Action Chapel International organization
and standardizes organization_id to ObjectId type.

Usage:
    python migrate_organization_consolidation.py [--dry-run] [--database=churchflow]
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Configuration
class MigrationConfig:
    MONGODB_URL = "mongodb://admin:aawwER4444%25@127.0.0.1:27017/{database}?authSource=admin"
    TARGET_ORG_ID = ObjectId("68fbb1cf8b6890654df914ca")
    OLD_ORG_ID = "8eac859d-9459-4bd2-a690-041ad2ba573d"
    BATCH_SIZE = 500

    @staticmethod
    def get_log_file():
        log_dir = "/opt/kasaai/logs"
        os.makedirs(log_dir, exist_ok=True)
        return f"{log_dir}/org_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Logging setup
def setup_logging():
    log_file = MigrationConfig.get_log_file()
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    logger.info(f"Logging to: {log_file}")
    return logger

logger = setup_logging()


class MigrationStats:
    """Track migration statistics."""

    def __init__(self):
        self.collections_processed = 0
        self.documents_updated = 0
        self.errors = []
        self.start_time = datetime.utcnow()

    def add_collection(self, collection_name: str, docs_updated: int):
        """Record collection processing."""
        self.collections_processed += 1
        self.documents_updated += docs_updated

        elapsed = (datetime.utcnow() - self.start_time).total_seconds()
        logger.info(f"""
        ========================================
        Collection: {collection_name}
        Documents Updated: {docs_updated}
        Progress: {self.collections_processed} collections
        Elapsed Time: {elapsed:.1f}s
        ========================================
        """)

    def add_error(self, collection_name: str, error: str):
        """Record error."""
        self.errors.append(f"{collection_name}: {error}")
        logger.error(f"ERROR in {collection_name}: {error}")

    def summary(self):
        """Print final summary."""
        elapsed = (datetime.utcnow() - self.start_time).total_seconds()

        logger.info("=" * 80)
        logger.info("MIGRATION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Collections Processed: {self.collections_processed}")
        logger.info(f"Documents Updated: {self.documents_updated}")
        logger.info(f"Errors: {len(self.errors)}")
        logger.info(f"Total Time: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")

        if self.errors:
            logger.error("ERRORS:")
            for error in self.errors:
                logger.error(f"  - {error}")
        else:
            logger.info("✅ Migration completed successfully!")


async def create_indexes(db):
    """Create indexes to speed up migration and queries."""

    logger.info("Creating migration indexes...")

    indexes = [
        ("session_attendance", [("conference_id", 1), ("organization_id", 1)]),
        ("conference_registrations", [("conference_id", 1), ("organization_id", 1)]),
        ("conference_sessions", [("conference_id", 1), ("organization_id", 1)]),
        ("bus_registrations", [("bus_route_id", 1), ("organization_id", 1)]),
        ("bus_routes", [("conference_id", 1), ("organization_id", 1)]),
    ]

    for collection_name, index_spec in indexes:
        try:
            await db[collection_name].create_index(index_spec)
            logger.info(f"  ✓ Created index on {collection_name}: {index_spec}")
        except Exception as e:
            logger.warning(f"  ⚠ Index creation failed for {collection_name}: {str(e)}")


async def update_all_org_ids(db, collection_name: str, dry_run: bool) -> int:
    """
    Update ALL organization_id values to target org_id.

    Args:
        db: Database connection
        collection_name: Collection to update
        dry_run: If True, only count documents

    Returns:
        Number of documents updated
    """

    # Update ALL org_ids that aren't already the target (as ObjectId)
    filter_query = {
        "$or": [
            {"organization_id": {"$ne": MigrationConfig.TARGET_ORG_ID}},
            {"organization_id": {"$exists": False}},
            {"organization_id": None}
        ]
    }

    if dry_run:
        count = await db[collection_name].count_documents(filter_query)
        logger.info(f"[DRY RUN] {collection_name}: would update {count} documents")
        return count

    result = await db[collection_name].update_many(
        filter_query,
        {
            "$set": {
                "organization_id": MigrationConfig.TARGET_ORG_ID,
                "updated_at": datetime.utcnow()
            },
            "$unset": {"org_id": ""}  # Remove legacy field if present
        }
    )

    logger.info(f"  {collection_name}: Updated {result.modified_count} documents")
    return result.modified_count


async def update_session_attendance_batch(db, dry_run: bool) -> int:
    """
    Update session_attendance with batch processing.

    Args:
        db: Database connection
        dry_run: If True, only count documents

    Returns:
        Number of documents updated
    """

    logger.info("Processing session_attendance with batch processing...")

    # Update ALL session_attendance records that don't have target org_id
    filter_query = {
        "$or": [
            {"organization_id": {"$ne": MigrationConfig.TARGET_ORG_ID}},
            {"organization_id": {"$exists": False}},
            {"organization_id": None}
        ]
    }

    total_docs = await db.session_attendance.count_documents(filter_query)

    if total_docs == 0:
        logger.info("  No session_attendance documents to update")
        return 0

    if dry_run:
        logger.info(f"[DRY RUN] session_attendance: would update {total_docs} documents")
        return total_docs

    # Get unique conference IDs and their org_ids
    conference_to_org = {}
    conferences = await db.conferences.find({}, {"_id": 1, "organization_id": 1}).to_list(length=None)

    for conf in conferences:
        org_id = conf.get("organization_id", MigrationConfig.TARGET_ORG_ID)

        # Ensure ObjectId type
        if isinstance(org_id, str) and ObjectId.is_valid(org_id):
            org_id = ObjectId(org_id)
        elif org_id == MigrationConfig.OLD_ORG_ID:
            org_id = MigrationConfig.TARGET_ORG_ID

        conference_to_org[conf["_id"]] = org_id

    # Process in batches
    batch_size = MigrationConfig.BATCH_SIZE
    batches = (total_docs // batch_size) + 1
    total_updated = 0

    for batch_num in range(batches):
        # Don't use skip() - just query the filter again to get next batch
        # Since we update docs, they won't match the filter on next iteration
        docs = await db.session_attendance.find(filter_query).limit(batch_size).to_list(length=batch_size)

        if not docs:
            break

        for doc in docs:
            conference_id = doc.get("conference_id")

            # Determine org_id
            if conference_id and conference_id in conference_to_org:
                org_id = conference_to_org[conference_id]
            else:
                org_id = MigrationConfig.TARGET_ORG_ID

            # Update document
            result = await db.session_attendance.update_one(
                {"_id": doc["_id"]},
                {
                    "$set": {
                        "organization_id": org_id,
                        "updated_at": datetime.utcnow()
                    }
                }
            )

            if result.modified_count > 0:
                total_updated += 1

        progress = ((batch_num + 1) / batches) * 100
        logger.info(f"  Batch {batch_num + 1}/{batches} ({progress:.1f}%): {len(docs)} processed, {total_updated} updated")

        # Small delay to avoid overwhelming database
        await asyncio.sleep(0.1)

    logger.info(f"  ✓ session_attendance: {total_updated} documents updated")
    return total_updated


async def add_org_id_from_foreign_key(db, collection_name: str, fk_field: str, dry_run: bool) -> int:
    """
    Add/update organization_id to target org_id.

    Args:
        db: Database connection
        collection_name: Collection to update
        fk_field: Foreign key field name
        dry_run: If True, only count documents

    Returns:
        Number of documents updated
    """

    logger.info(f"Updating organization_id in {collection_name} to target org_id...")

    # Update ALL that aren't already the target org_id
    filter_query = {
        "$or": [
            {"organization_id": {"$ne": MigrationConfig.TARGET_ORG_ID}},
            {"organization_id": {"$exists": False}},
            {"organization_id": None}
        ]
    }

    total_docs = await db[collection_name].count_documents(filter_query)

    if total_docs == 0:
        logger.info(f"  No {collection_name} documents to update")
        return 0

    if dry_run:
        logger.info(f"[DRY RUN] {collection_name}: would update {total_docs} documents")
        return total_docs

    # Get distinct foreign key values
    pipeline = [
        {"$match": filter_query},
        {"$group": {"_id": f"${fk_field}"}}
    ]

    fk_values = await db[collection_name].aggregate(pipeline).to_list(length=10000)
    total_updated = 0

    # Simply set all to target org_id (since user wants ALL data under one org)
    result = await db[collection_name].update_many(
        filter_query,
        {
            "$set": {
                "organization_id": MigrationConfig.TARGET_ORG_ID,
                "updated_at": datetime.utcnow()
            }
        }
    )

    total_updated = result.modified_count

    logger.info(f"  ✓ {collection_name}: {total_updated} documents updated")
    return total_updated


async def convert_org_id_to_objectid(db, collection_name: str, dry_run: bool) -> int:
    """
    Convert string organization_id to ObjectId type.

    Args:
        db: Database connection
        collection_name: Collection to update
        dry_run: If True, only count documents

    Returns:
        Number of documents updated
    """

    logger.info(f"Converting {collection_name}.organization_id from string to ObjectId...")

    filter_query = {
        "organization_id": {"$type": "string"}
    }

    total_docs = await db[collection_name].count_documents(filter_query)

    if total_docs == 0:
        logger.info(f"  No {collection_name} documents to convert")
        return 0

    if dry_run:
        logger.info(f"[DRY RUN] {collection_name}: would convert {total_docs} documents")
        return total_docs

    # Get documents with string org_id
    cursor = db[collection_name].find(filter_query)
    total_updated = 0

    async for doc in cursor:
        org_id_str = doc["organization_id"]

        # Convert to ObjectId
        if ObjectId.is_valid(org_id_str):
            org_id = ObjectId(org_id_str)
        else:
            # Invalid ObjectId string, use target org
            logger.warning(f"  Invalid ObjectId string '{org_id_str}' in {collection_name}, using target org")
            org_id = MigrationConfig.TARGET_ORG_ID

        # Update document
        result = await db[collection_name].update_one(
            {"_id": doc["_id"]},
            {
                "$set": {
                    "organization_id": org_id,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        if result.modified_count > 0:
            total_updated += 1

    logger.info(f"  ✓ {collection_name}: {total_updated} documents converted")
    return total_updated


async def migrate_organization_consolidation(database_name: str = "churchflow", dry_run: bool = False):
    """
    Main migration function.

    Args:
        database_name: Name of database to migrate
        dry_run: If True, only count documents without making changes
    """

    logger.info("=" * 80)
    logger.info("CHURCHFLOW ORGANIZATION CONSOLIDATION MIGRATION")
    logger.info("=" * 80)

    # Connect to MongoDB
    mongo_url = MigrationConfig.MONGODB_URL.format(database=database_name)
    client = AsyncIOMotorClient(mongo_url)
    db = client.get_default_database()

    if dry_run:
        logger.warning("⚠️  DRY RUN MODE - No changes will be committed")

    # Verify target organization exists
    target_org = await db.organizations.find_one({"_id": MigrationConfig.TARGET_ORG_ID})
    if not target_org:
        raise ValueError("Target organization not found!")

    logger.info(f"Target Organization: {target_org['name']}")
    logger.info(f"Target ID: {MigrationConfig.TARGET_ORG_ID}")
    logger.info(f"Old ID: {MigrationConfig.OLD_ORG_ID}")
    logger.info("")

    # Initialize stats
    stats = MigrationStats()

    # Create indexes (even in dry-run mode)
    if not dry_run:
        await create_indexes(db)
        logger.info("")

    # Phase 1: Update collections with old org_id
    logger.info("=" * 80)
    logger.info("PHASE 1: Update Collections with Old Org ID")
    logger.info("=" * 80)

    phase1_collections = [
        "branches",
        "conferences",
        "bus_routes",
        "sms_campaigns",
        "wallets",
        "organization_users",
        "organization_memberships"
    ]

    for collection in phase1_collections:
        try:
            count = await update_all_org_ids(db, collection, dry_run)
            stats.add_collection(collection, count)
        except Exception as e:
            stats.add_error(collection, str(e))

    # Phase 2: Large collections (batch processing)
    logger.info("")
    logger.info("=" * 80)
    logger.info("PHASE 2: Batch Process Large Collections")
    logger.info("=" * 80)

    try:
        count = await update_session_attendance_batch(db, dry_run)
        stats.add_collection("session_attendance", count)
    except Exception as e:
        stats.add_error("session_attendance", str(e))

    # Phase 3: Foreign key derivations
    logger.info("")
    logger.info("=" * 80)
    logger.info("PHASE 3: Add Org ID via Foreign Key Lookup")
    logger.info("=" * 80)

    fk_collections = [
        ("conference_registrations", "conference_id"),
        ("conference_sessions", "conference_id"),
        ("bus_registrations", "bus_route_id")
    ]

    for collection, fk_field in fk_collections:
        try:
            count = await add_org_id_from_foreign_key(db, collection, fk_field, dry_run)
            stats.add_collection(collection, count)
        except Exception as e:
            stats.add_error(collection, str(e))

    # Phase 4: Type conversions
    logger.info("")
    logger.info("=" * 80)
    logger.info("PHASE 4: Convert String to ObjectId")
    logger.info("=" * 80)

    type_conversion_collections = [
        "donations",
        "donor_profiles",
        "journey_stages",
        "subscriptions",
        "usage_metrics"
    ]

    for collection in type_conversion_collections:
        try:
            count = await convert_org_id_to_objectid(db, collection, dry_run)
            stats.add_collection(collection, count)
        except Exception as e:
            stats.add_error(collection, str(e))

    # Phase 5: Backup collections
    logger.info("")
    logger.info("=" * 80)
    logger.info("PHASE 5: Update Backup Collections")
    logger.info("=" * 80)

    backup_collections = [
        "branches_backup_20251114_113423",
        "branches_backup_20251114_114124",
        "conference_registrations_backup_20251114_113422",
        "conference_registrations_backup_20251114_114124",
        "conferences_backup_20251114_113422",
        "conferences_backup_20251114_114124",
        "users_backup_20251114_113422",
        "users_backup_20251114_114124",
        "wallets_backup_20251114_113423",
        "wallets_backup_20251114_114124"
    ]

    for collection in backup_collections:
        try:
            count = await update_all_org_ids(db, collection, dry_run)
            stats.add_collection(collection, count)
        except Exception as e:
            stats.add_error(collection, str(e))

    # Summary
    logger.info("")
    stats.summary()

    client.close()
    return stats


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ChurchFlow Organization Migration")
    parser.add_argument("--dry-run", action="store_true", help="Run without making changes")
    parser.add_argument("--database", default="churchflow", help="Database name (default: churchflow)")

    args = parser.parse_args()

    try:
        stats = asyncio.run(migrate_organization_consolidation(
            database_name=args.database,
            dry_run=args.dry_run
        ))

        # Exit with error code if there were errors
        sys.exit(1 if stats.errors else 0)

    except Exception as e:
        logger.error(f"Migration failed with exception: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
