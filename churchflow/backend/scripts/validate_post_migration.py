"""
Post-Migration Validation Script

Validates data integrity after organization consolidation migration.

Usage:
    python validate_post_migration.py [--database=churchflow]
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


async def validate_post_migration(database_name: str = "churchflow"):
    """
    Validate data integrity after migration.

    Args:
        database_name: Name of database to validate

    Returns:
        Dictionary of validation results
    """

    logger.info("=" * 80)
    logger.info("POST-MIGRATION VALIDATION")
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

    # Collections to validate
    primary_collections = [
        "branches", "bus_routes", "conferences", "organization_memberships",
        "organization_users", "session_attendance", "sms_campaigns", "wallets",
        "conference_registrations", "conference_sessions", "bus_registrations",
        "donations", "donor_profiles", "journey_stages", "subscriptions", "usage_metrics"
    ]

    # Check 1: Verify no old org_id remains
    logger.info("\n[CHECK 1] Verifying no old org_id remains...")

    total_old_org_docs = 0

    for coll_name in primary_collections:
        old_count = await db[coll_name].count_documents({
            "$or": [
                {"organization_id": OLD_ORG_ID},
                {"org_id": OLD_ORG_ID}
            ]
        })

        if old_count > 0:
            total_old_org_docs += old_count
            results["errors"].append(f"{coll_name} has {old_count} documents with old org_id")
            logger.error(f"  ❌ {coll_name}: {old_count} documents still have old org_id")

    if total_old_org_docs == 0:
        results["checks"].append("No documents with old org_id found")
        logger.info(f"  ✓ No documents with old org_id ({OLD_ORG_ID})")
    else:
        results["valid"] = False
        logger.error(f"  ❌ FAILED: {total_old_org_docs} documents still have old org_id")

    # Check 2: Verify all have target org_id
    logger.info("\n[CHECK 2] Verifying all documents have target org_id...")

    for coll_name in primary_collections:
        target_count = await db[coll_name].count_documents({
            "organization_id": TARGET_ORG_ID
        })

        missing_count = await db[coll_name].count_documents({
            "$or": [
                {"organization_id": {"$exists": False}},
                {"organization_id": None},
                {"organization_id": {"$nin": [TARGET_ORG_ID]}}
            ]
        })

        if missing_count > 0:
            results["warnings"].append(f"{coll_name} has {missing_count} documents without target org_id")
            logger.warning(f"  ⚠ {coll_name}: {target_count} have target org_id, {missing_count} don't")
        else:
            logger.info(f"  ✓ {coll_name}: {target_count} documents have target org_id")

    # Check 3: Verify ObjectId types
    logger.info("\n[CHECK 3] Verifying organization_id is ObjectId type...")

    for coll_name in primary_collections:
        string_org_ids = await db[coll_name].count_documents({
            "organization_id": {"$type": "string"}
        })

        if string_org_ids > 0:
            results["errors"].append(f"{coll_name} has {string_org_ids} documents with string org_id")
            logger.error(f"  ❌ {coll_name}: {string_org_ids} documents have string org_id")
            results["valid"] = False
        else:
            objectid_count = await db[coll_name].count_documents({
                "organization_id": {"$type": "objectId"}
            })

            if objectid_count > 0:
                logger.info(f"  ✓ {coll_name}: All {objectid_count} org_ids are ObjectId type")

    # Check 4: Verify foreign key consistency
    logger.info("\n[CHECK 4] Verifying foreign key consistency...")

    # Check conference_registrations.organization_id matches conference.organization_id
    mismatched_pipeline = [
        {
            "$lookup": {
                "from": "conferences",
                "localField": "conference_id",
                "foreignField": "_id",
                "as": "conference"
            }
        },
        {"$unwind": {"path": "$conference", "preserveNullAndEmptyArrays": True}},
        {
            "$match": {
                "$expr": {
                    "$and": [
                        {"$ne": [{"$type": "$conference"}, "missing"]},
                        {"$ne": ["$organization_id", "$conference.organization_id"]}
                    ]
                }
            }
        },
        {"$count": "mismatches"}
    ]

    mismatches_result = await db.conference_registrations.aggregate(mismatched_pipeline).to_list(length=1)
    mismatches = mismatches_result[0]["mismatches"] if mismatches_result else 0

    if mismatches > 0:
        results["errors"].append(f"{mismatches} conference_registrations have org_id mismatch")
        logger.error(f"  ❌ {mismatches} conference_registrations have org_id != conference.org_id")
        results["valid"] = False
    else:
        logger.info("  ✓ conference_registrations.org_id matches conference.org_id")

    # Check session_attendance.organization_id matches conference.organization_id
    session_mismatches_pipeline = [
        {
            "$lookup": {
                "from": "conferences",
                "localField": "conference_id",
                "foreignField": "_id",
                "as": "conference"
            }
        },
        {"$unwind": {"path": "$conference", "preserveNullAndEmptyArrays": True}},
        {
            "$match": {
                "$expr": {
                    "$and": [
                        {"$ne": [{"$type": "$conference"}, "missing"]},
                        {"$ne": ["$organization_id", "$conference.organization_id"]}
                    ]
                }
            }
        },
        {"$count": "mismatches"}
    ]

    session_mismatches_result = await db.session_attendance.aggregate(session_mismatches_pipeline).to_list(length=1)
    session_mismatches = session_mismatches_result[0]["mismatches"] if session_mismatches_result else 0

    if session_mismatches > 0:
        results["errors"].append(f"{session_mismatches} session_attendance have org_id mismatch")
        logger.error(f"  ❌ {session_mismatches} session_attendance have org_id != conference.org_id")
        results["valid"] = False
    else:
        logger.info("  ✓ session_attendance.org_id matches conference.org_id")

    # Check 5: Verify document counts unchanged
    logger.info("\n[CHECK 5] Verifying no data loss...")

    collection_counts = {}

    for coll_name in primary_collections:
        count = await db[coll_name].count_documents({})
        collection_counts[coll_name] = count

    logger.info("  Document counts:")
    for coll_name, count in sorted(collection_counts.items()):
        logger.info(f"    {coll_name}: {count} documents")

    results["checks"].append("Document counts recorded (compare with pre-migration)")

    # Check 6: Verify indexes exist
    logger.info("\n[CHECK 6] Verifying migration indexes exist...")

    expected_indexes = {
        "session_attendance": ["conference_id_1_organization_id_1"],
        "conference_registrations": ["conference_id_1_organization_id_1"],
        "conference_sessions": ["conference_id_1_organization_id_1"],
        "bus_registrations": ["bus_route_id_1_organization_id_1"],
        "bus_routes": ["conference_id_1_organization_id_1"],
    }

    for coll_name, expected_index_names in expected_indexes.items():
        indexes = await db[coll_name].index_information()
        index_names = list(indexes.keys())

        for expected_index in expected_index_names:
            if expected_index in index_names:
                logger.info(f"  ✓ {coll_name}: index '{expected_index}' exists")
            else:
                results["warnings"].append(f"{coll_name} missing index '{expected_index}'")
                logger.warning(f"  ⚠ {coll_name}: index '{expected_index}' missing")

    # Check 7: Verify backup collections updated
    logger.info("\n[CHECK 7] Verifying backup collections updated...")

    backup_collections = [
        "branches_backup_20251114_113423",
        "branches_backup_20251114_114124",
        "wallets_backup_20251114_113423",
        "wallets_backup_20251114_114124"
    ]

    for backup_coll in backup_collections:
        # Check if collection exists
        all_colls = await db.list_collection_names()

        if backup_coll not in all_colls:
            logger.info(f"  ⊘ {backup_coll}: doesn't exist")
            continue

        old_count = await db[backup_coll].count_documents({
            "$or": [
                {"organization_id": OLD_ORG_ID},
                {"org_id": OLD_ORG_ID}
            ]
        })

        if old_count > 0:
            results["warnings"].append(f"{backup_coll} has {old_count} docs with old org_id")
            logger.warning(f"  ⚠ {backup_coll}: {old_count} documents still have old org_id")
        else:
            logger.info(f"  ✓ {backup_coll}: no old org_id found")

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
        logger.info("\n✅ Post-migration validation PASSED")
        logger.info("   Migration successful!")
    else:
        logger.error("\n❌ Post-migration validation FAILED")
        logger.error("   Migration has errors that need to be fixed")

    client.close()
    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ChurchFlow Post-Migration Validation")
    parser.add_argument("--database", default="churchflow", help="Database name (default: churchflow)")

    args = parser.parse_args()

    try:
        results = asyncio.run(validate_post_migration(database_name=args.database))

        # Exit with error code if validation failed
        sys.exit(0 if results["valid"] else 1)

    except Exception as e:
        logger.error(f"Validation failed with exception: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
