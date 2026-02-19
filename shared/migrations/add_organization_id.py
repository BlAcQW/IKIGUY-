"""
Migration Script: Add organization_id to existing documents.

This script adds organization_id field to existing documents across all applications.
For now, it sets organization_id to null, allowing admins to manually assign organizations later.

Usage:
    python add_organization_id.py --database churchflow --dry-run
    python add_organization_id.py --database churchflow --execute
    python add_organization_id.py --all --execute
"""

import asyncio
import os
import sys
from typing import List, Dict
import argparse
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

# Database configurations
DATABASES = {
    "churchflow": {
        "name": "churchflow",
        "collections": [
            "branches",
            "registrations",
            "conferences",
            "speakers",
            "conference_registrations",
            "bus_routes",
            "bus_registrations",
            "bus_updates",
            "users",
            "notification_logs",
        ]
    },
    "eventflow": {
        "name": "eventflow",
        "collections": [
            "events",
            "tasks",
            "responsible_persons",
        ]
    },
    "inkwave": {
        "name": "inkwave",
        "collections": [
            "books",
            "book_chunks",
            "reading_sessions",
            "interactions",
            "users",
            "usage_logs",
            "provider_configs",
        ]
    },
    "studyflow": {
        "name": "studyflow",
        "collections": [
            "users",
            "materials",
            "learning_materials",
            "schools",
            "study_sessions",
            "questions",
        ]
    }
}


class OrganizationMigration:
    """Handle migration of organization_id field."""

    def __init__(self, mongodb_url: str):
        """
        Initialize migration.

        Args:
            mongodb_url: MongoDB connection URL
        """
        self.client = AsyncIOMotorClient(mongodb_url)
        self.stats: Dict[str, Dict] = {}

    async def migrate_collection(
        self,
        database_name: str,
        collection_name: str,
        dry_run: bool = True
    ) -> Dict:
        """
        Migrate a single collection.

        Args:
            database_name: Name of the database
            collection_name: Name of the collection
            dry_run: If True, only count documents without updating

        Returns:
            Statistics about the migration
        """
        db = self.client[database_name]
        collection = db[collection_name]

        # Count documents without organization_id
        query = {
            "$or": [
                {"organization_id": {"$exists": False}},
                {"organization_id": None}
            ]
        }

        count = await collection.count_documents(query)

        result = {
            "collection": collection_name,
            "documents_to_update": count,
            "updated": 0,
            "errors": 0
        }

        if not dry_run and count > 0:
            try:
                # Update documents to have organization_id: null
                update_result = await collection.update_many(
                    query,
                    {
                        "$set": {
                            "organization_id": None,
                            "migration_timestamp": datetime.utcnow()
                        }
                    }
                )
                result["updated"] = update_result.modified_count
            except Exception as e:
                result["errors"] = 1
                result["error_message"] = str(e)

        return result

    async def migrate_database(
        self,
        database_key: str,
        dry_run: bool = True
    ) -> Dict:
        """
        Migrate all collections in a database.

        Args:
            database_key: Key from DATABASES dict
            dry_run: If True, only count documents without updating

        Returns:
            Statistics about the migration
        """
        if database_key not in DATABASES:
            raise ValueError(f"Unknown database: {database_key}")

        db_config = DATABASES[database_key]
        database_name = db_config["name"]
        collections = db_config["collections"]

        print(f"\n{'='*60}")
        print(f"{'DRY RUN - ' if dry_run else ''}Migrating database: {database_name}")
        print(f"{'='*60}")

        stats = {
            "database": database_name,
            "collections": [],
            "total_documents": 0,
            "total_updated": 0,
            "total_errors": 0
        }

        for collection_name in collections:
            print(f"\nProcessing collection: {collection_name}...")
            result = await self.migrate_collection(
                database_name,
                collection_name,
                dry_run
            )

            stats["collections"].append(result)
            stats["total_documents"] += result["documents_to_update"]
            stats["total_updated"] += result["updated"]
            stats["total_errors"] += result["errors"]

            if result["documents_to_update"] > 0:
                print(f"  ✓ Found {result['documents_to_update']} documents")
                if not dry_run:
                    print(f"  ✓ Updated {result['updated']} documents")
                if result["errors"] > 0:
                    print(f"  ✗ Errors: {result.get('error_message', 'Unknown')}")
            else:
                print(f"  - No documents to update")

        return stats

    async def migrate_all(self, dry_run: bool = True) -> Dict:
        """
        Migrate all databases.

        Args:
            dry_run: If True, only count documents without updating

        Returns:
            Overall statistics
        """
        overall_stats = {
            "databases": [],
            "total_documents": 0,
            "total_updated": 0,
            "total_errors": 0
        }

        for db_key in DATABASES.keys():
            stats = await self.migrate_database(db_key, dry_run)
            overall_stats["databases"].append(stats)
            overall_stats["total_documents"] += stats["total_documents"]
            overall_stats["total_updated"] += stats["total_updated"]
            overall_stats["total_errors"] += stats["total_errors"]

        return overall_stats

    def print_summary(self, stats: Dict, dry_run: bool = True):
        """
        Print migration summary.

        Args:
            stats: Migration statistics
            dry_run: Whether this was a dry run
        """
        print(f"\n{'='*60}")
        print(f"Migration Summary {'(DRY RUN)' if dry_run else '(EXECUTED)'}")
        print(f"{'='*60}")

        if "databases" in stats:
            # Overall summary
            for db_stats in stats["databases"]:
                print(f"\n{db_stats['database'].upper()}:")
                print(f"  Total documents: {db_stats['total_documents']}")
                if not dry_run:
                    print(f"  Updated: {db_stats['total_updated']}")
                    print(f"  Errors: {db_stats['total_errors']}")

            print(f"\nOVERALL TOTALS:")
            print(f"  Total documents: {stats['total_documents']}")
            if not dry_run:
                print(f"  Updated: {stats['total_updated']}")
                print(f"  Errors: {stats['total_errors']}")
        else:
            # Single database summary
            print(f"\n{stats['database'].upper()}:")
            print(f"  Total documents: {stats['total_documents']}")
            if not dry_run:
                print(f"  Updated: {stats['total_updated']}")
                print(f"  Errors: {stats['total_errors']}")

        print(f"\n{'='*60}\n")

    async def close(self):
        """Close database connection."""
        self.client.close()


async def main():
    """Main migration function."""
    parser = argparse.ArgumentParser(
        description="Add organization_id field to existing documents"
    )
    parser.add_argument(
        "--database",
        choices=list(DATABASES.keys()),
        help="Specific database to migrate"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Migrate all databases"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Perform dry run without updating (default)"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually execute the migration"
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.database and not args.all:
        parser.error("Either --database or --all must be specified")

    # Get MongoDB URL from environment
    mongodb_url = os.getenv("MONGODB_URL")
    if not mongodb_url:
        print("❌ Error: MONGODB_URL environment variable not set")
        sys.exit(1)

    # Determine if this is a dry run
    dry_run = not args.execute

    # Create migrator
    migrator = OrganizationMigration(mongodb_url)

    try:
        if args.all:
            print("\n🔄 Migrating ALL databases...")
            stats = await migrator.migrate_all(dry_run=dry_run)
        else:
            print(f"\n🔄 Migrating database: {args.database}")
            stats = await migrator.migrate_database(args.database, dry_run=dry_run)

        migrator.print_summary(stats, dry_run=dry_run)

        if dry_run:
            print("💡 This was a DRY RUN. Use --execute to actually perform the migration.")
        else:
            print("✅ Migration completed successfully!")

    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await migrator.close()


if __name__ == "__main__":
    asyncio.run(main())
