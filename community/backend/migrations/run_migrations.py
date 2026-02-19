"""
Migration Runner for African Language Community Platform

Runs all pending migrations in order and tracks migration history.

Usage:
    python run_migrations.py                    # Run all pending migrations
    python run_migrations.py --migration 001    # Run specific migration
    python run_migrations.py --status           # Show migration status
    python run_migrations.py --rollback 001     # Rollback specific migration
"""

import os
import sys
import argparse
import importlib
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()


# List of all migrations in order
MIGRATIONS = [
    "001_add_mlops_collections",
]


async def get_executed_migrations(db):
    """Get list of already executed migrations."""
    migrations = []
    async for doc in db.migrations.find({"status": "completed"}):
        migrations.append(doc["migration_id"])
    return migrations


async def show_migration_status(db):
    """Show status of all migrations."""
    executed = await get_executed_migrations(db)

    print("\n" + "="*60)
    print("MIGRATION STATUS")
    print("="*60)

    for migration_id in MIGRATIONS:
        status = "✅ EXECUTED" if migration_id in executed else "⏳ PENDING"
        print(f"{migration_id}: {status}")

        # Show execution details if executed
        if migration_id in executed:
            doc = await db.migrations.find_one({"migration_id": migration_id})
            if doc:
                print(f"  Executed at: {doc['executed_at']}")
                if doc.get("rolled_back_at"):
                    print(f"  ⚠️  Rolled back at: {doc['rolled_back_at']}")

    print("="*60 + "\n")


async def run_migration(db, migration_id):
    """Run a specific migration."""

    # Check if already executed
    executed = await get_executed_migrations(db)
    if migration_id in executed:
        print(f"⚠️  Migration {migration_id} already executed")
        return False

    print(f"\n{'='*60}")
    print(f"Running migration: {migration_id}")
    print(f"{'='*60}\n")

    # Import and run migration
    try:
        module = importlib.import_module(migration_id)
        await module.run_migration()
        return True
    except Exception as e:
        print(f"\n❌ Migration {migration_id} failed: {e}")
        raise


async def run_rollback(db, migration_id):
    """Rollback a specific migration."""

    # Check if executed
    executed = await get_executed_migrations(db)
    if migration_id not in executed:
        print(f"⚠️  Migration {migration_id} not executed, nothing to rollback")
        return False

    print(f"\n{'='*60}")
    print(f"Rolling back migration: {migration_id}")
    print(f"{'='*60}\n")

    # Import and run rollback
    try:
        rollback_module = f"{migration_id.split('_')[0]}_rollback_{'_'.join(migration_id.split('_')[1:])}"
        module = importlib.import_module(rollback_module)
        await module.run_rollback()
        return True
    except Exception as e:
        print(f"\n❌ Rollback {migration_id} failed: {e}")
        raise


async def run_all_pending(db):
    """Run all pending migrations."""

    executed = await get_executed_migrations(db)
    pending = [m for m in MIGRATIONS if m not in executed]

    if not pending:
        print("\n✅ No pending migrations")
        return

    print(f"\n{'='*60}")
    print(f"Found {len(pending)} pending migration(s)")
    print(f"{'='*60}\n")

    for migration_id in pending:
        success = await run_migration(db, migration_id)
        if not success:
            print(f"\n❌ Stopping at failed migration: {migration_id}")
            break


async def main():
    """Main entry point."""

    parser = argparse.ArgumentParser(description="Database migration runner")
    parser.add_argument("--migration", help="Run specific migration by ID")
    parser.add_argument("--rollback", help="Rollback specific migration by ID")
    parser.add_argument("--status", action="store_true", help="Show migration status")
    args = parser.parse_args()

    # Get MongoDB connection from environment
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://admin:aawwER444444@127.0.0.1:27017/")
    db_name = os.getenv("MONGODB_DATABASE", "african_language_community")

    print(f"\n🔗 Connecting to MongoDB: {db_name}")
    client = AsyncIOMotorClient(mongodb_url)
    db = client[db_name]

    try:
        # Test connection
        await db.command("ping")
        print("✅ Connected to MongoDB")

        # Execute based on arguments
        if args.status:
            await show_migration_status(db)
        elif args.migration:
            await run_migration(db, args.migration)
        elif args.rollback:
            await run_rollback(db, args.rollback)
        else:
            await run_all_pending(db)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())
