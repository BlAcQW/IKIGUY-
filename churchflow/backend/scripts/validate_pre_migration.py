"""
Pre-Migration Validation Script

Validates data integrity before organization consolidation migration.

Usage:
    python validate_pre_migration.py [--database=churchflow]
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
TARGET_ORG_ID = ObjectId("68fbb1cf8b6890654df914ca")
OLD_ORG_ID = "8eac859d-9459-4bd2-a690-041ad2ba573d"

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


async def validate_pre_migration(database_name: str = "churchflow"):
    """
    Validate data integrity before migration.

    Args:
        database_name: Name of database to validate

    Returns:
        Dictionary of validation results
    """

    logger.info("=" * 80)
    logger.info("PRE-MIGRATION VALIDATION")
    logger.info("=" * 80)

    # Connect to MongoDB
    mongo_url = MONGODB_URL.format(database=database_name)
    client = AsyncIOMotorClient(mongo_url)
    db = client.get_default_database()

    results = {
        "valid": True,
        "checks": [],
        "warnings": [],
        "errors": []
    }

    # Check 1: Verify target organization exists
    logger.info("\n[CHECK 1] Verifying target organization exists...")

    target_org = await db.organizations.find_one({"_id": TARGET_ORG_ID})

    if not target_org:
        results["valid"] = False
        results["errors"].append("Target organization not found!")
        logger.error("  ❌ Target organization not found!")
    else:
        results["checks"].append(f"Target organization found: {target_org['name']}")
        logger.info(f"  ✓ Target organization: {target_org['name']}")
        logger.info(f"    ID: {TARGET_ORG_ID}")

    # Check 2: Count documents by org_id type
    logger.info("\n[CHECK 2] Counting documents by organization_id type...")

    collections_to_check = [
        "branches", "bus_routes", "conferences", "organization_memberships",
        "organization_users", "session_attendance", "sms_campaigns", "wallets",
        "conference_registrations", "conference_sessions", "bus_registrations",
        "donations", "donor_profiles", "journey_stages", "subscriptions", "usage_metrics"
    ]

    stats = {
        "old_org_id": 0,
        "target_org_id_string": 0,
        "target_org_id_objectid": 0,
        "missing_org_id": 0,
        "other_org_id": 0
    }

    for coll_name in collections_to_check:
        # Count old org_id
        old_count = await db[coll_name].count_documents({
            "$or": [
                {"organization_id": OLD_ORG_ID},
                {"org_id": OLD_ORG_ID}
            ]
        })

        # Count target org_id (string)
        target_str_count = await db[coll_name].count_documents({
            "organization_id": str(TARGET_ORG_ID)
        })

        # Count target org_id (ObjectId)
        target_oid_count = await db[coll_name].count_documents({
            "organization_id": TARGET_ORG_ID
        })

        # Count missing org_id
        missing_count = await db[coll_name].count_documents({
            "$or": [
                {"organization_id": {"$exists": False}},
                {"organization_id": None}
            ]
        })

        if old_count > 0 or target_str_count > 0 or target_oid_count > 0 or missing_count > 0:
            logger.info(f"\n  {coll_name}:")
            if old_count > 0:
                logger.info(f"    OLD org_id (string): {old_count}")
                stats["old_org_id"] += old_count
            if target_str_count > 0:
                logger.info(f"    TARGET org_id (string): {target_str_count}")
                stats["target_org_id_string"] += target_str_count
            if target_oid_count > 0:
                logger.info(f"    TARGET org_id (ObjectId): {target_oid_count}")
                stats["target_org_id_objectid"] += target_oid_count
            if missing_count > 0:
                logger.info(f"    MISSING org_id: {missing_count}")
                stats["missing_org_id"] += missing_count

    logger.info("\n  Summary:")
    logger.info(f"    Documents with old org_id: {stats['old_org_id']}")
    logger.info(f"    Documents with target org_id (string): {stats['target_org_id_string']}")
    logger.info(f"    Documents with target org_id (ObjectId): {stats['target_org_id_objectid']}")
    logger.info(f"    Documents missing org_id: {stats['missing_org_id']}")

    results["checks"].append(f"Found {stats['old_org_id']} documents to migrate from old org_id")
    results["checks"].append(f"Found {stats['target_org_id_string']} documents to convert from string to ObjectId")
    results["checks"].append(f"Found {stats['missing_org_id']} documents missing org_id")

    # Check 3: Verify foreign key relationships
    logger.info("\n[CHECK 3] Verifying foreign key relationships...")

    # Check conference_registrations have valid conference_id
    invalid_conf_regs = await db.conference_registrations.count_documents({
        "conference_id": {"$exists": True},
        "$expr": {"$not": {"$in": ["$conference_id", await get_conference_ids(db)]}}
    })

    if invalid_conf_regs > 0:
        results["warnings"].append(f"{invalid_conf_regs} conference_registrations with invalid conference_id")
        logger.warning(f"  ⚠ {invalid_conf_regs} conference_registrations with invalid conference_id")
    else:
        logger.info("  ✓ All conference_registrations have valid conference_id")

    # Check bus_registrations have valid bus_route_id
    bus_route_ids = await db.bus_routes.distinct("_id")
    invalid_bus_regs = await db.bus_registrations.count_documents({
        "bus_route_id": {"$exists": True, "$nin": bus_route_ids}
    })

    if invalid_bus_regs > 0:
        results["warnings"].append(f"{invalid_bus_regs} bus_registrations with invalid bus_route_id")
        logger.warning(f"  ⚠ {invalid_bus_regs} bus_registrations with invalid bus_route_id")
    else:
        logger.info("  ✓ All bus_registrations have valid bus_route_id")

    # Check 4: Check for data anomalies
    logger.info("\n[CHECK 4] Checking for data anomalies...")

    # Check for duplicate QR codes in conference_registrations
    duplicate_qrs_pipeline = [
        {"$group": {"_id": "$qr_code", "count": {"$sum": 1}}},
        {"$match": {"count": {"$gt": 1}}}
    ]

    duplicate_qrs = await db.conference_registrations.aggregate(duplicate_qrs_pipeline).to_list(length=100)

    if duplicate_qrs:
        results["warnings"].append(f"{len(duplicate_qrs)} duplicate QR codes in conference_registrations")
        logger.warning(f"  ⚠ {len(duplicate_qrs)} duplicate QR codes in conference_registrations")
    else:
        logger.info("  ✓ No duplicate QR codes")

    # Check 5: Verify collections exist
    logger.info("\n[CHECK 5] Verifying all expected collections exist...")

    all_collections = await db.list_collection_names()

    expected_collections = [
        "organizations", "branches", "conferences", "users",
        "conference_registrations", "conference_sessions", "session_attendance",
        "bus_routes", "bus_registrations"
    ]

    missing_collections = [c for c in expected_collections if c not in all_collections]

    if missing_collections:
        results["warnings"].append(f"Missing collections: {missing_collections}")
        logger.warning(f"  ⚠ Missing collections: {missing_collections}")
    else:
        logger.info(f"  ✓ All {len(expected_collections)} expected collections exist")

    # Check 6: Estimate migration time
    logger.info("\n[CHECK 6] Estimating migration time...")

    total_docs_to_update = stats["old_org_id"] + stats["target_org_id_string"] + stats["missing_org_id"]

    # Rough estimate: 100 docs/second for simple updates, 50 docs/second for lookups
    simple_updates = stats["old_org_id"] + stats["target_org_id_string"]
    complex_updates = stats["missing_org_id"]

    estimated_seconds = (simple_updates / 100) + (complex_updates / 50)
    estimated_minutes = estimated_seconds / 60

    logger.info(f"  Total documents to update: {total_docs_to_update}")
    logger.info(f"  Estimated time: {estimated_minutes:.1f} minutes")

    results["checks"].append(f"Estimated migration time: {estimated_minutes:.1f} minutes")

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 80)

    logger.info("\nChecks Passed:")
    for check in results["checks"]:
        logger.info(f"  ✓ {check}")

    if results["warnings"]:
        logger.info("\nWarnings:")
        for warning in results["warnings"]:
            logger.warning(f"  ⚠ {warning}")

    if results["errors"]:
        logger.info("\nErrors:")
        for error in results["errors"]:
            logger.error(f"  ❌ {error}")

    if results["valid"]:
        logger.info("\n✅ Pre-migration validation PASSED")
        logger.info("   Safe to proceed with migration")
    else:
        logger.error("\n❌ Pre-migration validation FAILED")
        logger.error("   Fix errors before proceeding")

    client.close()
    return results


async def get_conference_ids(db):
    """Get all valid conference IDs."""
    return await db.conferences.distinct("_id")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ChurchFlow Pre-Migration Validation")
    parser.add_argument("--database", default="churchflow", help="Database name (default: churchflow)")

    args = parser.parse_args()

    try:
        results = asyncio.run(validate_pre_migration(database_name=args.database))

        # Exit with error code if validation failed
        sys.exit(0 if results["valid"] else 1)

    except Exception as e:
        logger.error(f"Validation failed with exception: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
