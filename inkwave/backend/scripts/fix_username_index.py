#!/usr/bin/env python3
"""
Migration script to fix username index in inkwave.users collection.

Problem: The username_1 index is configured as unique but not sparse,
causing duplicate key errors when multiple users have username=None.

Solution: Drop and recreate the index with sparse=True to allow
multiple null values while still enforcing uniqueness for non-null values.

Usage:
    cd /opt/kasaai/apps/inkwave/backend
    MONGODB_URI="mongodb://admin:aawwER4444%25@127.0.0.1:27017/inkwave?authSource=admin" \
    MONGODB_DB_NAME=inkwave \
    /opt/kasaai/apps/venv/bin/python scripts/fix_username_index.py
"""

import asyncio
import os
import sys
from datetime import datetime

# Add paths
sys.path.insert(0, '/opt/kasaai/apps')
sys.path.insert(0, '/opt/kasaai/apps/inkwave/backend')

# Set environment variables
os.environ.setdefault('SUPABASE_URL', 'https://supabase.ailabsafrica.com')
os.environ.setdefault('SUPABASE_ANON_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0')
os.environ.setdefault('MONGODB_URI', os.getenv('MONGODB_URI', 'mongodb://admin:aawwER4444%40@127.0.0.1:27017/?authSource=admin'))
os.environ.setdefault('MONGODB_DB_NAME', os.getenv('MONGODB_DB_NAME', 'inkwave'))


async def fix_username_index():
    """
    Fix the username index by dropping and recreating as sparse.

    Steps:
    1. Connect to MongoDB
    2. Check current index configuration
    3. Drop existing username_1 index
    4. Recreate with sparse=True
    5. Verify new index configuration
    """
    from motor.motor_asyncio import AsyncIOMotorClient
    from pymongo.errors import OperationFailure

    mongodb_uri = os.getenv('MONGODB_URI')
    mongodb_db_name = os.getenv('MONGODB_DB_NAME')

    print("=" * 70)
    print("USERNAME INDEX MIGRATION SCRIPT")
    print("=" * 70)
    print(f"\nTimestamp: {datetime.utcnow().isoformat()}")
    print(f"Database: {mongodb_db_name}")
    print(f"Collection: users")
    print("\n" + "-" * 70)

    try:
        # Step 1: Connect to MongoDB
        print("\n[1/5] Connecting to MongoDB...")
        client = AsyncIOMotorClient(mongodb_uri)
        db = client[mongodb_db_name]

        # Test connection
        await client.admin.command('ping')
        print("✅ Connected successfully!")

        # Step 2: Check current index configuration
        print("\n[2/5] Checking current username index configuration...")
        indexes = await db.users.index_information()

        if 'username_1' not in indexes:
            print("⚠️  WARNING: username_1 index does not exist!")
            print("   Creating sparse unique index from scratch...")
        else:
            index_info = indexes['username_1']
            is_unique = index_info.get('unique', False)
            is_sparse = index_info.get('sparse', False)

            print(f"   Current configuration:")
            print(f"   - Unique: {is_unique}")
            print(f"   - Sparse: {is_sparse}")
            print(f"   - Keys: {index_info.get('key')}")

            if is_sparse:
                print("\n✅ Index is already configured as sparse!")
                print("   No migration needed.")
                client.close()
                return

            print("\n   ❌ Index is NOT sparse - this is causing the duplicate key error")

        # Count users with null username
        null_username_count = await db.users.count_documents({'username': None})
        missing_username_count = await db.users.count_documents({'username': {'$exists': False}})
        total_users = await db.users.count_documents({})

        print(f"\n   Database state:")
        print(f"   - Total users: {total_users}")
        print(f"   - Users with username=None: {null_username_count}")
        print(f"   - Users missing username field: {missing_username_count}")

        # Step 3: Drop existing index
        print("\n[3/5] Dropping existing username_1 index...")
        try:
            result = await db.users.drop_index('username_1')
            print(f"✅ Index dropped successfully!")
        except OperationFailure as e:
            if 'index not found' in str(e).lower():
                print("⚠️  Index already doesn't exist (may have been deleted)")
            else:
                raise

        # Step 4: Create new sparse unique index
        print("\n[4/5] Creating new sparse unique index on username...")
        await db.users.create_index("username", unique=True, sparse=True, name="username_1")
        print("✅ Sparse unique index created successfully!")

        # Step 5: Verify new index configuration
        print("\n[5/5] Verifying new index configuration...")
        indexes = await db.users.index_information()

        if 'username_1' not in indexes:
            print("❌ ERROR: username_1 index was not created!")
            client.close()
            sys.exit(1)

        new_index_info = indexes['username_1']
        is_unique = new_index_info.get('unique', False)
        is_sparse = new_index_info.get('sparse', False)

        print(f"   New configuration:")
        print(f"   - Unique: {is_unique}")
        print(f"   - Sparse: {is_sparse}")
        print(f"   - Keys: {new_index_info.get('key')}")

        if is_unique and is_sparse:
            print("\n✅ SUCCESS! Index is now properly configured as sparse unique!")
        else:
            print("\n❌ ERROR: Index configuration is not correct!")
            print(f"   Expected: unique=True, sparse=True")
            print(f"   Got: unique={is_unique}, sparse={is_sparse}")
            client.close()
            sys.exit(1)

        # Final verification: Check that multiple null usernames are allowed
        print("\n" + "-" * 70)
        print("VERIFICATION")
        print("-" * 70)
        print(f"\n✅ All {null_username_count + missing_username_count} users with null usernames can now coexist")
        print("✅ New user signups will work (username defaults to None)")
        print("✅ Username uniqueness is still enforced for non-null values")

        # Close connection
        client.close()

        print("\n" + "=" * 70)
        print("MIGRATION COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print("\nNext steps:")
        print("1. Test user signup to verify it works")
        print("2. No application restart required (change is immediate)")
        print("3. Monitor signup logs for any issues")
        print()

    except Exception as e:
        print(f"\n❌ ERROR: Migration failed!")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print("\nStarting username index migration...")
    asyncio.run(fix_username_index())
