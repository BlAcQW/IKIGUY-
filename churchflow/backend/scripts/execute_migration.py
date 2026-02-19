"""
Execute conference registrant migration.

This script migrates all conference registrants to member/visitor profiles.
Run preview first with test_migration_preview.py to see what changes will be made.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.core.database import connect_to_mongodb, get_database
from app.services.member_migration_service import MemberMigrationService


async def execute_migration():
    """Execute migration."""
    print("=" * 80)
    print("CONFERENCE REGISTRANT MIGRATION")
    print("=" * 80)
    print("\nWARNING: This will modify the users collection!")
    print("Press Ctrl+C now if you want to cancel.")
    print("\nConnecting to MongoDB...")
    await connect_to_mongodb()

    print("\nInitializing migration service...")
    migration_service = MemberMigrationService()

    print("\nExecuting migration...\n")
    print("=" * 80)

    stats = await migration_service.migrate_conference_registrants_to_profiles(
        dry_run=False
    )

    print("\n" + "=" * 80)
    print("\nMIGRATION EXECUTION RESULTS:")
    print("=" * 80)
    print(f"Total Registrations:           {stats['total_registrations']}")
    print(f"Members Created:               {stats['members_created']}")
    print(f"Members Updated:               {stats['members_updated']}")
    print(f"Visitors Created:              {stats['visitors_created']}")
    print(f"Visitors Updated:              {stats['visitors_updated']}")
    print(f"Placeholder Phones Generated:  {stats['placeholder_phones']}")
    print(f"Errors:                        {stats['errors']}")

    if stats['error_details']:
        print("\nError Details:")
        for error in stats['error_details']:
            print(f"  - {error}")

    print("\n" + "=" * 80)
    print("\nMIGRATION COMPLETED SUCCESSFULLY!")
    print(f"Total users created: {stats['members_created'] + stats['visitors_created']}")
    print(f"Total users updated: {stats['members_updated'] + stats['visitors_updated']}")
    print("=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(execute_migration())
    except KeyboardInterrupt:
        print("\n\nMigration cancelled by user.")
        sys.exit(1)
