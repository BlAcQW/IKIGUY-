"""
Migrate hardcoded branches from constants to MongoDB.

This script migrates the 150+ hardcoded branches in app/constants/branches.py
to the branches MongoDB collection for full CRUD support.

Usage:
    python scripts/migrate_branches_to_db.py --organization-id <id> [--geocode] [--dry-run]
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.constants.branches import FIXED_BRANCHES
from app.config import get_settings

settings = get_settings()


async def migrate_branches(
    db,
    organization_id: str,
    geocode: bool = False,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Migrate branches from constants to MongoDB.

    Args:
        db: MongoDB database instance
        organization_id: Organization ID to assign branches to
        geocode: If True, runs geocoding for branches without coordinates
        dry_run: If True, shows what would be done without making changes

    Returns:
        Dictionary with migration results
    """
    collection = db.branches
    org_id = ObjectId(organization_id)

    inserted_count = 0
    updated_count = 0
    skipped_count = 0
    geocode_needed_count = 0

    print("\n" + "="*80)
    print("  Branch Migration: Constants → MongoDB")
    print("="*80)
    print(f"\n📊 Total branches to migrate: {len(FIXED_BRANCHES)}")
    print(f"🏢 Target organization: {organization_id}")
    print(f"🗺️  Geocoding: {'Enabled' if geocode else 'Disabled'}")
    print(f"🔍 Mode: {'DRY RUN (no changes)' if dry_run else 'LIVE MIGRATION'}")
    print()

    for i, branch_const in enumerate(FIXED_BRANCHES, 1):
        branch_name = branch_const["name"]
        print(f"\n[{i}/{len(FIXED_BRANCHES)}] Processing: {branch_name}")

        # Check if branch already exists in database
        existing_branch = await collection.find_one({
            "organization_id": org_id,
            "name": branch_name
        })

        # Prepare branch document
        branch_doc = {
            "organization_id": org_id,
            "name": branch_const["name"],
            "location": branch_const["location"],
            "region": branch_const["region"],
            "latitude": branch_const.get("latitude"),
            "longitude": branch_const.get("longitude"),
            "checkin_radius": branch_const.get("checkin_radius", 500),
            "auto_checkin_enabled": branch_const.get("auto_checkin_enabled", False),
            "geocoding_accuracy": branch_const.get("geocoding_accuracy"),
            "service_times": [],  # Will be configured later by admin
            "is_active": True,
            "updated_at": datetime.utcnow()
        }

        # Add created_at only for new branches
        if not existing_branch:
            branch_doc["created_at"] = datetime.utcnow()

        # Check if geocoding is needed
        needs_geocoding = (
            geocode and
            branch_doc["latitude"] is None and
            branch_doc["longitude"] is None
        )

        if needs_geocoding:
            geocode_needed_count += 1
            print("  ⚠️  Needs geocoding (coordinates missing)")

        if existing_branch:
            # Update existing branch
            if not dry_run:
                result = await collection.update_one(
                    {"_id": existing_branch["_id"]},
                    {"$set": branch_doc}
                )

                if result.modified_count > 0:
                    print(f"  ✏️  Updated: {branch_name}")
                    print(f"     GPS: {branch_doc.get('latitude', 'None')}, {branch_doc.get('longitude', 'None')}")
                    updated_count += 1
                else:
                    print(f"  ⏭️  Skipped (unchanged): {branch_name}")
                    skipped_count += 1
            else:
                print(f"  [DRY RUN] Would update: {branch_name}")
                updated_count += 1

        else:
            # Insert new branch
            if not dry_run:
                await collection.insert_one(branch_doc)
                print(f"  ✅ Inserted: {branch_name}")
                print(f"     Location: {branch_doc['location']}")
                print(f"     Region: {branch_doc['region']}")
                print(f"     GPS: {branch_doc.get('latitude', 'None')}, {branch_doc.get('longitude', 'None')}")
                inserted_count += 1
            else:
                print(f"  [DRY RUN] Would insert: {branch_name}")
                inserted_count += 1

    # Create indexes
    if not dry_run:
        print("\n📊 Creating database indexes...")
        await collection.create_index([("organization_id", 1), ("name", 1)], unique=True)
        await collection.create_index([("organization_id", 1), ("is_active", 1)])
        await collection.create_index([("organization_id", 1), ("region", 1)])
        await collection.create_index([("organization_id", 1), ("auto_checkin_enabled", 1)])
        await collection.create_index([
            ("organization_id", 1),
            ("latitude", 1),
            ("longitude", 1)
        ])
        print("  ✅ Indexes created")
    else:
        print("\n[DRY RUN] Would create database indexes")

    # Summary
    print("\n" + "="*80)
    print("📈 MIGRATION SUMMARY")
    print("="*80)
    print(f"  Inserted: {inserted_count}")
    print(f"  Updated:  {updated_count}")
    print(f"  Skipped:  {skipped_count}")
    print(f"  Total:    {len(FIXED_BRANCHES)}")
    print()

    if geocode_needed_count > 0:
        print(f"⚠️  {geocode_needed_count} branches need geocoding")
        print("   Run: python scripts/geocode_branches.py")
        print()

    if dry_run:
        print("🔍 This was a DRY RUN - no changes were made to the database")
        print("   Remove --dry-run flag to perform actual migration")
    else:
        print("✅ Migration complete!")

    print("="*80)

    return {
        "inserted": inserted_count,
        "updated": updated_count,
        "skipped": skipped_count,
        "total": len(FIXED_BRANCHES),
        "geocode_needed": geocode_needed_count,
        "dry_run": dry_run
    }


async def verify_migration(db, organization_id: str):
    """
    Verify migration by checking database state.

    Args:
        db: MongoDB database instance
        organization_id: Organization ID
    """
    collection = db.branches
    org_id = ObjectId(organization_id)

    print("\n" + "="*80)
    print("  Migration Verification")
    print("="*80)

    # Count total branches
    total_count = await collection.count_documents({"organization_id": org_id})
    print(f"\n📊 Total branches in database: {total_count}")

    # Count by status
    active_count = await collection.count_documents({
        "organization_id": org_id,
        "is_active": True
    })
    inactive_count = total_count - active_count
    print(f"   Active: {active_count}")
    print(f"   Inactive: {inactive_count}")

    # Count with/without coordinates
    with_coords = await collection.count_documents({
        "organization_id": org_id,
        "latitude": {"$ne": None},
        "longitude": {"$ne": None}
    })
    without_coords = total_count - with_coords
    print(f"\n🗺️  Geolocation status:")
    print(f"   With coordinates: {with_coords} ({with_coords/total_count*100:.1f}%)")
    print(f"   Without coordinates: {without_coords} ({without_coords/total_count*100:.1f}%)")

    # Count auto check-in enabled
    auto_checkin_count = await collection.count_documents({
        "organization_id": org_id,
        "auto_checkin_enabled": True
    })
    print(f"\n✅ Auto check-in enabled: {auto_checkin_count} ({auto_checkin_count/total_count*100:.1f}%)")

    # Region breakdown
    pipeline = [
        {"$match": {"organization_id": org_id}},
        {"$group": {"_id": "$region", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]

    regions = await collection.aggregate(pipeline).to_list(length=10)

    print(f"\n📍 Top regions:")
    for region in regions:
        print(f"   {region['_id']}: {region['count']} branches")

    print("\n" + "="*80)


async def list_branches_without_coordinates(db, organization_id: str):
    """
    List branches that still need geocoding.

    Args:
        db: MongoDB database instance
        organization_id: Organization ID
    """
    collection = db.branches
    org_id = ObjectId(organization_id)

    cursor = collection.find({
        "organization_id": org_id,
        "$or": [
            {"latitude": None},
            {"longitude": None}
        ]
    }).sort("name", 1)

    branches = await cursor.to_list(length=None)

    if not branches:
        print("\n✅ All branches have GPS coordinates!")
        return

    print("\n" + "="*80)
    print(f"  Branches Without GPS Coordinates ({len(branches)})")
    print("="*80)

    for i, branch in enumerate(branches, 1):
        print(f"\n{i}. {branch['name']}")
        print(f"   Location: {branch['location']}")
        print(f"   Region: {branch['region']}")

    print("\n💡 To add coordinates:")
    print("   1. Run: python scripts/geocode_branches.py")
    print("   2. Or manually add via admin UI")
    print("="*80)


async def main():
    """Main execution function."""
    import argparse

    parser = argparse.ArgumentParser(description="Migrate branches to MongoDB")
    parser.add_argument(
        "--organization-id",
        required=True,
        help="Organization ID to assign branches to"
    )
    parser.add_argument(
        "--geocode",
        action="store_true",
        help="Run geocoding for branches without coordinates"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify migration status without migrating"
    )
    parser.add_argument(
        "--list-missing-coords",
        action="store_true",
        help="List branches without GPS coordinates"
    )

    args = parser.parse_args()

    # Validate organization ID format
    try:
        ObjectId(args.organization_id)
    except Exception:
        print(f"\n❌ Error: Invalid organization ID format: {args.organization_id}")
        print("   Must be a valid MongoDB ObjectId (24-character hex string)")
        return

    # Connect to database
    print("\n🔌 Connecting to MongoDB...")
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client.churchflow
    print("  ✅ Connected")

    try:
        if args.verify:
            # Verify migration
            await verify_migration(db, args.organization_id)
        elif args.list_missing_coords:
            # List branches without coordinates
            await list_branches_without_coordinates(db, args.organization_id)
        else:
            # Perform migration
            results = await migrate_branches(
                db,
                args.organization_id,
                geocode=args.geocode,
                dry_run=args.dry_run
            )

            if not args.dry_run and results["inserted"] + results["updated"] > 0:
                print("\n💡 Next steps:")
                print("1. Verify migration: python scripts/migrate_branches_to_db.py --organization-id <id> --verify")

                if results["geocode_needed"] > 0:
                    print("2. Geocode branches: python scripts/geocode_branches.py")

                print("3. Configure service times via admin UI")
                print("4. Enable auto check-in for desired branches")

    finally:
        client.close()
        print("\n👋 Database connection closed.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏸️  Migration interrupted by user.")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
