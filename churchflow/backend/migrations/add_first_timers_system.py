"""
Database Migration: Add First Timers System

Creates the first_timers collection with appropriate indexes
for the First Timer Management system.

Migration Date: December 15, 2025
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Load environment variables
load_dotenv()


async def migrate():
    """
    Execute migration for First Timers system.

    Creates:
    - first_timers collection indexes
    - Compound indexes for efficient queries
    """
    # MongoDB connection
    username = "admin"
    password = quote_plus(os.getenv("MONGO_PASSWORD", "aawwER4444%"))
    mongo_uri = f"mongodb://{username}:{password}@127.0.0.1:27017/"

    client = AsyncIOMotorClient(mongo_uri)
    db = client["churchflow"]

    print("=" * 60)
    print("🚀 Starting First Timers System Migration")
    print("=" * 60)

    try:
        # 1. Create indexes for first_timers collection
        print("\n📊 Creating indexes for first_timers collection...")

        # Organization and active status index (most common query)
        await db.first_timers.create_index(
            [("organization_id", 1), ("is_active", 1)],
            name="org_active_idx"
        )
        print("   ✅ Created: org_active_idx (organization_id + is_active)")

        # Interest type index (for dashboard stats)
        await db.first_timers.create_index(
            [("organization_id", 1), ("interest_type", 1), ("is_active", 1)],
            name="org_interest_active_idx"
        )
        print("   ✅ Created: org_interest_active_idx (organization + interest_type + active)")

        # Follow-up status index (for dashboard stats)
        await db.first_timers.create_index(
            [("organization_id", 1), ("follow_up_status", 1), ("is_active", 1)],
            name="org_followup_active_idx"
        )
        print("   ✅ Created: org_followup_active_idx (organization + follow_up_status + active)")

        # Conversion tracking index
        await db.first_timers.create_index(
            [("organization_id", 1), ("converted_to_member", 1), ("is_active", 1)],
            name="org_converted_active_idx"
        )
        print("   ✅ Created: org_converted_active_idx (organization + converted + active)")

        # Visit date index (for time-based queries)
        await db.first_timers.create_index(
            [("organization_id", 1), ("visit_date", -1), ("is_active", 1)],
            name="org_visit_date_idx"
        )
        print("   ✅ Created: org_visit_date_idx (organization + visit_date DESC + active)")

        # Branch filter index
        await db.first_timers.create_index(
            [("branch_id", 1), ("is_active", 1)],
            name="branch_active_idx"
        )
        print("   ✅ Created: branch_active_idx (branch_id + is_active)")

        # Phone and email indexes for uniqueness checks
        await db.first_timers.create_index(
            [("phone", 1), ("organization_id", 1)],
            name="phone_org_idx"
        )
        print("   ✅ Created: phone_org_idx (phone + organization_id)")

        await db.first_timers.create_index(
            [("email", 1), ("organization_id", 1)],
            name="email_org_idx",
            sparse=True  # Sparse index since email is optional
        )
        print("   ✅ Created: email_org_idx (email + organization_id) - SPARSE")

        # Assigned user index (for follow-up queries)
        await db.first_timers.create_index(
            [("assigned_to_user_id", 1), ("follow_up_status", 1)],
            name="assigned_followup_idx",
            sparse=True  # Sparse since assignment is optional
        )
        print("   ✅ Created: assigned_followup_idx (assigned_to + follow_up_status) - SPARSE")

        # Next follow-up date index (for reminder queries)
        await db.first_timers.create_index(
            [("next_follow_up_date", 1), ("follow_up_status", 1)],
            name="next_followup_date_idx",
            sparse=True  # Sparse since date is optional
        )
        print("   ✅ Created: next_followup_date_idx (next_follow_up_date + status) - SPARSE")

        # Member ID index (for reverse lookups after conversion)
        await db.first_timers.create_index(
            [("member_id", 1)],
            name="member_id_idx",
            sparse=True  # Sparse since only converted records have member_id
        )
        print("   ✅ Created: member_id_idx (member_id) - SPARSE")

        # Created by user index
        await db.first_timers.create_index(
            [("created_by_user_id", 1), ("created_at", -1)],
            name="created_by_date_idx"
        )
        print("   ✅ Created: created_by_date_idx (created_by + created_at DESC)")

        print("\n✅ All indexes created successfully!")

        # 2. Verify collection exists and check document count
        print("\n📊 Verifying first_timers collection...")
        count = await db.first_timers.count_documents({})
        print(f"   📈 Current document count: {count}")

        if count == 0:
            print("   ℹ️  Collection is empty (expected for new installation)")
        else:
            print(f"   ✅ Found {count} existing first timer records")

        # 3. List all indexes for verification
        print("\n📋 Listing all indexes on first_timers collection:")
        indexes = await db.first_timers.list_indexes().to_list(length=None)
        for idx in indexes:
            print(f"   - {idx['name']}: {idx.get('key', {})}")

        print("\n" + "=" * 60)
        print("✅ First Timers System Migration Complete!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Restart the backend service: sudo systemctl restart kasaai-churchflow-backend")
        print("2. Test the /api/v1/first-timers endpoints")
        print("3. Create frontend components for First Timer Dashboard")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        raise

    finally:
        client.close()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("First Timers System Database Migration")
    print("=" * 60)
    asyncio.run(migrate())
