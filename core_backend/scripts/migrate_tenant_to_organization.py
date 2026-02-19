#!/usr/bin/env python3
"""
Migrate tenant_id to organization_id across MongoDB collections.

This script resolves the organizational model conflict between legacy tenant_id
and the new standard organization_id used by the shared library.

Usage:
    python scripts/migrate_tenant_to_organization.py --dry-run    # Test first
    python scripts/migrate_tenant_to_organization.py --execute    # Run migration

Collections affected:
- campaigns (tenant_id → organization_id)
- voice_campaigns (tenant_id → organization_id)
- automation_configs (verify organization_id exists)
- call_logs (add organization_id if missing from tenant_id)
- vapi_calls (add organization_id if missing)
- assistants (add organization_id if missing)
- phone_numbers (add organization_id if missing)
- kb_documents (add organization_id if missing)

Author: Claude Code
Date: 2025-11-07
"""

import os
import sys
import asyncio
import argparse
from datetime import datetime
from typing import List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import BulkWriteError
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Configure logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TenantToOrganizationMigration:
    """
    Handles migration from tenant_id to organization_id.
    """

    def __init__(self, mongodb_url: str, database_name: str, dry_run: bool = True):
        """
        Initialize migration.

        Args:
            mongodb_url: MongoDB connection string
            database_name: Database to migrate
            dry_run: If True, only report what would be done
        """
        self.mongodb_url = mongodb_url
        self.database_name = database_name
        self.dry_run = dry_run
        self.client = None
        self.db = None
        self.migration_log = []

    async def connect(self):
        """Connect to MongoDB."""
        logger.info(f"Connecting to MongoDB database: {self.database_name}")
        self.client = AsyncIOMotorClient(self.mongodb_url)
        self.db = self.client[self.database_name]

        # Test connection
        await self.db.command("ping")
        logger.info("✅ Connected to MongoDB successfully")

    async def disconnect(self):
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
            logger.info("✅ Disconnected from MongoDB")

    def log_action(self, action: str, collection: str, details: Dict[str, Any]):
        """Log migration action."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "collection": collection,
            "details": details
        }
        self.migration_log.append(log_entry)
        logger.info(f"{'[DRY RUN] ' if self.dry_run else ''}[{collection}] {action}: {details}")

    async def backup_collection(self, collection_name: str) -> str:
        """
        Create backup of collection before migration.

        Args:
            collection_name: Name of collection to backup

        Returns:
            Backup collection name
        """
        backup_name = f"{collection_name}_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        if self.dry_run:
            logger.info(f"[DRY RUN] Would create backup: {backup_name}")
            return backup_name

        logger.info(f"Creating backup: {backup_name}")

        # Copy collection
        pipeline = [{"$match": {}}, {"$out": backup_name}]
        await self.db[collection_name].aggregate(pipeline).to_list(None)

        # Verify backup
        original_count = await self.db[collection_name].count_documents({})
        backup_count = await self.db[backup_name].count_documents({})

        if original_count != backup_count:
            raise Exception(f"Backup verification failed: {original_count} != {backup_count}")

        logger.info(f"✅ Backup created: {backup_name} ({backup_count} documents)")
        return backup_name

    async def migrate_tenant_id_field(self, collection_name: str):
        """
        Migrate collection from tenant_id to organization_id.

        Steps:
        1. Count documents with tenant_id
        2. Rename tenant_id → organization_id
        3. Verify migration
        4. Create index on organization_id

        Args:
            collection_name: Collection to migrate
        """
        collection = self.db[collection_name]

        logger.info(f"")
        logger.info(f"{'='*80}")
        logger.info(f"Migrating collection: {collection_name}")
        logger.info(f"{'='*80}")

        # Count documents with tenant_id
        tenant_id_count = await collection.count_documents({"tenant_id": {"$exists": True}})
        org_id_count = await collection.count_documents({"organization_id": {"$exists": True}})
        total_count = await collection.count_documents({})

        logger.info(f"📊 Current state:")
        logger.info(f"   Total documents: {total_count}")
        logger.info(f"   With tenant_id: {tenant_id_count}")
        logger.info(f"   With organization_id: {org_id_count}")

        if tenant_id_count == 0:
            logger.info(f"✅ No documents with tenant_id found. Skipping.")
            return

        # Create backup
        if not self.dry_run:
            backup_name = await self.backup_collection(collection_name)

        # Rename tenant_id to organization_id
        if self.dry_run:
            logger.info(f"[DRY RUN] Would rename tenant_id → organization_id for {tenant_id_count} documents")
        else:
            logger.info(f"Renaming tenant_id → organization_id...")

            result = await collection.update_many(
                {"tenant_id": {"$exists": True}},
                {"$rename": {"tenant_id": "organization_id"}}
            )

            logger.info(f"✅ Renamed field in {result.modified_count} documents")

            self.log_action(
                "rename_field",
                collection_name,
                {
                    "from": "tenant_id",
                    "to": "organization_id",
                    "documents_modified": result.modified_count
                }
            )

        # Verify migration
        if not self.dry_run:
            tenant_id_remaining = await collection.count_documents({"tenant_id": {"$exists": True}})
            org_id_after = await collection.count_documents({"organization_id": {"$exists": True}})

            logger.info(f"📊 After migration:")
            logger.info(f"   tenant_id remaining: {tenant_id_remaining}")
            logger.info(f"   organization_id now: {org_id_after}")

            if tenant_id_remaining > 0:
                raise Exception(f"Migration incomplete: {tenant_id_remaining} documents still have tenant_id")

        # Create index on organization_id
        if self.dry_run:
            logger.info(f"[DRY RUN] Would create index on organization_id")
        else:
            logger.info(f"Creating index on organization_id...")
            await collection.create_index("organization_id")
            logger.info(f"✅ Index created")

        logger.info(f"✅ Migration complete for {collection_name}")

    async def add_organization_id_from_tenant(self, collection_name: str):
        """
        Add organization_id field to documents that have tenant_id but no organization_id.

        Args:
            collection_name: Collection to update
        """
        collection = self.db[collection_name]

        logger.info(f"")
        logger.info(f"{'='*80}")
        logger.info(f"Adding organization_id to collection: {collection_name}")
        logger.info(f"{'='*80}")

        # Count documents that need updating
        needs_update = await collection.count_documents({
            "tenant_id": {"$exists": True},
            "organization_id": {"$exists": False}
        })

        logger.info(f"📊 Documents needing organization_id: {needs_update}")

        if needs_update == 0:
            logger.info(f"✅ All documents already have organization_id. Skipping.")
            return

        if self.dry_run:
            logger.info(f"[DRY RUN] Would copy tenant_id → organization_id for {needs_update} documents")
        else:
            logger.info(f"Copying tenant_id → organization_id...")

            result = await collection.update_many(
                {
                    "tenant_id": {"$exists": True},
                    "organization_id": {"$exists": False}
                },
                [{"$set": {"organization_id": "$tenant_id"}}]
            )

            logger.info(f"✅ Added organization_id to {result.modified_count} documents")

            self.log_action(
                "add_organization_id",
                collection_name,
                {
                    "source": "tenant_id",
                    "documents_modified": result.modified_count
                }
            )

    async def verify_collection(self, collection_name: str):
        """
        Verify collection has proper organization_id field.

        Args:
            collection_name: Collection to verify
        """
        collection = self.db[collection_name]

        total = await collection.count_documents({})
        with_org_id = await collection.count_documents({"organization_id": {"$exists": True}})
        with_tenant_id = await collection.count_documents({"tenant_id": {"$exists": True}})

        logger.info(f"")
        logger.info(f"Verification for {collection_name}:")
        logger.info(f"   Total documents: {total}")
        logger.info(f"   With organization_id: {with_org_id} ({100*with_org_id/total if total > 0 else 0:.1f}%)")
        logger.info(f"   With tenant_id: {with_tenant_id}")

        if with_tenant_id > 0:
            logger.warning(f"⚠️  {with_tenant_id} documents still have tenant_id")

        return {
            "collection": collection_name,
            "total": total,
            "with_organization_id": with_org_id,
            "with_tenant_id": with_tenant_id,
            "coverage": 100 * with_org_id / total if total > 0 else 0
        }

    async def run_migration(self):
        """Execute full migration process."""
        try:
            await self.connect()

            mode = "DRY RUN MODE" if self.dry_run else "LIVE MIGRATION MODE"
            logger.info(f"")
            logger.info(f"{'#'*80}")
            logger.info(f"# TENANT_ID → ORGANIZATION_ID MIGRATION")
            logger.info(f"# Mode: {mode}")
            logger.info(f"# Database: {self.database_name}")
            logger.info(f"# Time: {datetime.utcnow().isoformat()}")
            logger.info(f"{'#'*80}")
            logger.info(f"")

            # Phase 1: Collections that need tenant_id → organization_id rename
            rename_collections = [
                "campaigns",
                "voice_campaigns"
            ]

            for collection_name in rename_collections:
                # Check if collection exists
                collection_names = await self.db.list_collection_names()
                if collection_name in collection_names:
                    await self.migrate_tenant_id_field(collection_name)
                else:
                    logger.info(f"⏭️  Collection {collection_name} not found, skipping")

            # Phase 2: Collections that might need organization_id added
            add_org_id_collections = [
                "automation_configs",
                "call_logs",
                "vapi_calls",
                "assistants",
                "phone_numbers",
                "kb_documents",
                "kb_sources"
            ]

            for collection_name in add_org_id_collections:
                collection_names = await self.db.list_collection_names()
                if collection_name in collection_names:
                    await self.add_organization_id_from_tenant(collection_name)
                else:
                    logger.info(f"⏭️  Collection {collection_name} not found, skipping")

            # Phase 3: Verification
            logger.info(f"")
            logger.info(f"{'='*80}")
            logger.info(f"VERIFICATION PHASE")
            logger.info(f"{'='*80}")

            all_collections = rename_collections + add_org_id_collections
            verification_results = []

            for collection_name in all_collections:
                collection_names = await self.db.list_collection_names()
                if collection_name in collection_names:
                    result = await self.verify_collection(collection_name)
                    verification_results.append(result)

            # Final summary
            logger.info(f"")
            logger.info(f"{'='*80}")
            logger.info(f"MIGRATION SUMMARY")
            logger.info(f"{'='*80}")
            logger.info(f"Mode: {mode}")
            logger.info(f"Database: {self.database_name}")
            logger.info(f"Collections processed: {len(verification_results)}")

            total_docs = sum(r["total"] for r in verification_results)
            total_with_org_id = sum(r["with_organization_id"] for r in verification_results)
            total_with_tenant_id = sum(r["with_tenant_id"] for r in verification_results)

            logger.info(f"")
            logger.info(f"Overall statistics:")
            logger.info(f"   Total documents: {total_docs}")
            logger.info(f"   With organization_id: {total_with_org_id} ({100*total_with_org_id/total_docs if total_docs > 0 else 0:.1f}%)")
            logger.info(f"   With tenant_id: {total_with_tenant_id}")

            if not self.dry_run:
                # Save migration log
                log_file = f"/tmp/migration_log_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
                with open(log_file, "w") as f:
                    json.dump({
                        "timestamp": datetime.utcnow().isoformat(),
                        "database": self.database_name,
                        "dry_run": self.dry_run,
                        "actions": self.migration_log,
                        "verification": verification_results
                    }, f, indent=2)
                logger.info(f"")
                logger.info(f"📝 Migration log saved to: {log_file}")

            if total_with_tenant_id > 0:
                logger.warning(f"")
                logger.warning(f"⚠️  WARNING: {total_with_tenant_id} documents still have tenant_id")
                logger.warning(f"⚠️  Review and investigate before deploying")

            logger.info(f"")
            logger.info(f"{'='*80}")
            logger.info(f"✅ Migration complete")
            logger.info(f"{'='*80}")

        except Exception as e:
            logger.error(f"")
            logger.error(f"{'='*80}")
            logger.error(f"❌ MIGRATION FAILED")
            logger.error(f"{'='*80}")
            logger.error(f"Error: {str(e)}")
            raise

        finally:
            await self.disconnect()


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Migrate tenant_id to organization_id in MongoDB"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run in dry-run mode (no changes made)"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute the migration (makes actual changes)"
    )
    parser.add_argument(
        "--database",
        default=os.getenv("MONGO_CORE_DATABASE", "kasaai_core"),
        help="Database name to migrate (default: kasaai_core)"
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.dry_run and not args.execute:
        parser.error("Must specify either --dry-run or --execute")

    if args.dry_run and args.execute:
        parser.error("Cannot specify both --dry-run and --execute")

    # Get MongoDB URL from environment
    mongodb_url = os.getenv("MONGODB_URL")
    if not mongodb_url:
        logger.error("MONGODB_URL environment variable not set")
        sys.exit(1)

    # Run migration
    migration = TenantToOrganizationMigration(
        mongodb_url=mongodb_url,
        database_name=args.database,
        dry_run=args.dry_run
    )

    await migration.run_migration()


if __name__ == "__main__":
    asyncio.run(main())
