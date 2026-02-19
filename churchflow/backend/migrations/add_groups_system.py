"""
Database Migration: Add Groups System.

Adds support for groups and subgroups with:
- Create groups and subgroups collections with indexes
- Add subgroup_memberships field to users collection
- Create indexes for efficient querying

Run this migration to enable the Group Management feature.
"""

import asyncio
import sys
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING
from urllib.parse import quote_plus

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))


async def run_migration():
    """
    Run the migration to add groups system.

    Steps:
    1. Create indexes for groups collection
    2. Create indexes for subgroups collection
    3. Add subgroup_memberships field to users (if missing)
    4. Create indexes on users collection for group queries
    """
    # Connect to MongoDB
    mongo_uri = os.getenv("MONGODB_URI")
    if not mongo_uri:
        # Build URI with URL-encoded password
        username = "admin"
        password = quote_plus("aawwER4444%")
        mongo_uri = f"mongodb://{username}:{password}@127.0.0.1:27017/"

    client = AsyncIOMotorClient(mongo_uri)
    db = client.churchflow

    print("=" * 80)
    print("GROUP MANAGEMENT SYSTEM MIGRATION")
    print("=" * 80)
    print()

    # ========================================================================
    # Step 1: Create indexes for groups collection
    # ========================================================================
    print("📊 Step 1: Creating indexes for 'groups' collection...")

    try:
        await db.groups.create_index(
            [("organization_id", ASCENDING), ("is_active", ASCENDING)],
            name="org_active_idx"
        )
        print("   ✅ Created index: org_active_idx on groups collection")
    except Exception as e:
        print(f"   ⚠️  Index may already exist: {e}")

    try:
        await db.groups.create_index([("name", ASCENDING)], name="name_idx")
        print("   ✅ Created index: name_idx on groups collection")
    except Exception as e:
        print(f"   ⚠️  Index may already exist: {e}")

    print()

    # ========================================================================
    # Step 2: Create indexes for subgroups collection
    # ========================================================================
    print("📊 Step 2: Creating indexes for 'subgroups' collection...")

    try:
        await db.subgroups.create_index(
            [("group_id", ASCENDING), ("is_active", ASCENDING)],
            name="group_active_idx"
        )
        print("   ✅ Created index: group_active_idx on subgroups collection")
    except Exception as e:
        print(f"   ⚠️  Index may already exist: {e}")

    try:
        await db.subgroups.create_index(
            [("organization_id", ASCENDING)],
            name="org_idx"
        )
        print("   ✅ Created index: org_idx on subgroups collection")
    except Exception as e:
        print(f"   ⚠️  Index may already exist: {e}")

    try:
        await db.subgroups.create_index([("name", ASCENDING)], name="name_idx")
        print("   ✅ Created index: name_idx on subgroups collection")
    except Exception as e:
        print(f"   ⚠️  Index may already exist: {e}")

    print()

    # ========================================================================
    # Step 3: Add subgroup_memberships field to users
    # ========================================================================
    print("👥 Step 3: Adding 'subgroup_memberships' field to users...")

    result = await db.users.update_many(
        {"subgroup_memberships": {"$exists": False}},
        {"$set": {"subgroup_memberships": []}}
    )

    print(f"   ✅ Updated {result.modified_count} user documents")
    print()

    # ========================================================================
    # Step 4: Create indexes on users collection for group queries
    # ========================================================================
    print("📊 Step 4: Creating indexes on 'users' collection for group queries...")

    try:
        await db.users.create_index(
            "subgroup_memberships.subgroup_id",
            name="subgroup_id_idx"
        )
        print("   ✅ Created index: subgroup_id_idx on users collection")
    except Exception as e:
        print(f"   ⚠️  Index may already exist: {e}")

    try:
        await db.users.create_index(
            "subgroup_memberships.group_id",
            name="group_id_idx"
        )
        print("   ✅ Created index: group_id_idx on users collection")
    except Exception as e:
        print(f"   ⚠️  Index may already exist: {e}")

    print()

    # ========================================================================
    # Migration Summary
    # ========================================================================
    print("=" * 80)
    print("MIGRATION SUMMARY")
    print("=" * 80)
    print()

    # Count existing groups and subgroups
    groups_count = await db.groups.count_documents({})
    subgroups_count = await db.subgroups.count_documents({})
    users_with_memberships = await db.users.count_documents({
        "subgroup_memberships": {"$exists": True, "$ne": []}
    })

    print(f"📁 Groups collection:")
    print(f"   - Total groups: {groups_count}")
    print(f"   - Indexes: 2 (org_active_idx, name_idx)")
    print()

    print(f"📁 Subgroups collection:")
    print(f"   - Total subgroups: {subgroups_count}")
    print(f"   - Indexes: 3 (group_active_idx, org_idx, name_idx)")
    print()

    print(f"👥 Users collection:")
    print(f"   - Users with subgroup memberships: {users_with_memberships}")
    print(f"   - New indexes: 2 (subgroup_id_idx, group_id_idx)")
    print()

    print("=" * 80)
    print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Restart the ChurchFlow backend service")
    print("2. Access the admin dashboard at /groups to create groups and subgroups")
    print("3. Assign members to subgroups from the subgroup management page")
    print()

    # Close connection
    client.close()


async def rollback_migration():
    """
    Rollback the migration (optional - for development/testing).

    WARNING: This will remove all groups, subgroups, and member assignments!
    Use only for testing or if you need to completely remove the feature.
    """
    mongo_uri = os.getenv("MONGODB_URI")
    if not mongo_uri:
        # Build URI with URL-encoded password
        username = "admin"
        password = quote_plus("aawwER4444%")
        mongo_uri = f"mongodb://{username}:{password}@127.0.0.1:27017/"

    client = AsyncIOMotorClient(mongo_uri)
    db = client.churchflow

    print("=" * 80)
    print("⚠️  ROLLBACK: REMOVING GROUPS SYSTEM")
    print("=" * 80)
    print()

    # Remove subgroup_memberships from users
    print("👥 Removing subgroup_memberships from users...")
    result = await db.users.update_many(
        {},
        {"$unset": {"subgroup_memberships": ""}}
    )
    print(f"   ✅ Removed from {result.modified_count} users")

    # Drop groups collection
    print("🗑️  Dropping groups collection...")
    await db.groups.drop()
    print("   ✅ Dropped groups collection")

    # Drop subgroups collection
    print("🗑️  Dropping subgroups collection...")
    await db.subgroups.drop()
    print("   ✅ Dropped subgroups collection")

    print()
    print("✅ ROLLBACK COMPLETED")
    print()

    client.close()


if __name__ == "__main__":
    print()
    if len(sys.argv) > 1 and sys.argv[1] == "--rollback":
        print("⚠️  WARNING: This will delete all groups, subgroups, and member assignments!")
        confirm = input("Type 'ROLLBACK' to confirm: ")
        if confirm == "ROLLBACK":
            asyncio.run(rollback_migration())
        else:
            print("Rollback cancelled.")
    else:
        asyncio.run(run_migration())
    print()
