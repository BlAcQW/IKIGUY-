"""
Database initialization script for Affiliate Program.

Creates MongoDB collections and indexes for the affiliate system.

Usage:
    python scripts/init_affiliate_database.py

Author: KasaAI Team
Date: 2025-11-18
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path to import from backend
sys.path.insert(0, str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING, IndexModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def init_affiliate_collections():
    """
    Initialize affiliate program collections and indexes.

    Creates:
    - affiliate_profiles
    - referral_links
    - referral_attributions
    - commission_records
    - payout_requests

    With appropriate indexes for performance.
    """
    # Get MongoDB connection string
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://admin:aawwER4444%25@127.0.0.1:27017/kasaai_core?authSource=admin")

    # Extract database name from URI if present, otherwise use env var
    if "/" in mongo_uri.split("@")[-1]:
        uri_db = mongo_uri.split("/")[-1].split("?")[0]
        database_name = uri_db if uri_db else os.getenv("MONGODB_DATABASE", "kasaai_core")
    else:
        database_name = os.getenv("MONGODB_DATABASE", "kasaai_core")

    print(f"Connecting to MongoDB: {database_name}")

    # Connect to MongoDB
    client = AsyncIOMotorClient(mongo_uri)
    db = client[database_name]

    try:
        # ====================================================================
        # 1. AFFILIATE_PROFILES COLLECTION
        # ====================================================================
        print("\n1. Creating affiliate_profiles collection...")

        # Create collection if not exists
        collections = await db.list_collection_names()
        if "affiliate_profiles" not in collections:
            await db.create_collection("affiliate_profiles")
            print("   ✓ Collection created")
        else:
            print("   ✓ Collection already exists")

        # Create indexes
        affiliate_profiles_indexes = [
            IndexModel([("user_id", ASCENDING)], unique=True, name="user_id_unique"),
            IndexModel([("referral_code", ASCENDING)], unique=True, name="referral_code_unique"),
            IndexModel([("upline_id", ASCENDING)], name="upline_id_idx"),
            IndexModel([("organization_id", ASCENDING)], name="organization_id_idx"),
            IndexModel([("is_active", ASCENDING)], name="is_active_idx"),
            IndexModel([("created_at", DESCENDING)], name="created_at_idx"),
        ]

        await db.affiliate_profiles.create_indexes(affiliate_profiles_indexes)
        print("   ✓ Indexes created: user_id (unique), referral_code (unique), upline_id, organization_id, is_active, created_at")

        # ====================================================================
        # 2. REFERRAL_LINKS COLLECTION
        # ====================================================================
        print("\n2. Creating referral_links collection...")

        if "referral_links" not in collections:
            await db.create_collection("referral_links")
            print("   ✓ Collection created")
        else:
            print("   ✓ Collection already exists")

        referral_links_indexes = [
            IndexModel([("affiliate_id", ASCENDING)], name="affiliate_id_idx"),
            IndexModel([("referral_code", ASCENDING)], name="referral_code_idx"),
            IndexModel([("organization_id", ASCENDING)], name="organization_id_idx"),
            IndexModel([("created_at", DESCENDING)], name="created_at_idx"),
        ]

        await db.referral_links.create_indexes(referral_links_indexes)
        print("   ✓ Indexes created: affiliate_id, referral_code, organization_id, created_at")

        # ====================================================================
        # 3. REFERRAL_ATTRIBUTIONS COLLECTION
        # ====================================================================
        print("\n3. Creating referral_attributions collection...")

        if "referral_attributions" not in collections:
            await db.create_collection("referral_attributions")
            print("   ✓ Collection created")
        else:
            print("   ✓ Collection already exists")

        referral_attributions_indexes = [
            IndexModel([("referred_user_id", ASCENDING)], unique=True, name="referred_user_id_unique"),
            IndexModel([("affiliate_id", ASCENDING)], name="affiliate_id_idx"),
            IndexModel([("referral_code", ASCENDING)], name="referral_code_idx"),
            IndexModel([("organization_id", ASCENDING)], name="organization_id_idx"),
            IndexModel([("clicked_at", DESCENDING)], name="clicked_at_idx"),
            IndexModel([("signed_up_at", DESCENDING)], name="signed_up_at_idx"),
        ]

        await db.referral_attributions.create_indexes(referral_attributions_indexes)
        print("   ✓ Indexes created: referred_user_id (unique), affiliate_id, referral_code, organization_id, clicked_at, signed_up_at")

        # ====================================================================
        # 4. COMMISSION_RECORDS COLLECTION
        # ====================================================================
        print("\n4. Creating commission_records collection...")

        if "commission_records" not in collections:
            await db.create_collection("commission_records")
            print("   ✓ Collection created")
        else:
            print("   ✓ Collection already exists")

        commission_records_indexes = [
            IndexModel([("affiliate_id", ASCENDING)], name="affiliate_id_idx"),
            IndexModel([("referred_user_id", ASCENDING)], name="referred_user_id_idx"),
            IndexModel([("transaction_id", ASCENDING)], name="transaction_id_idx"),
            IndexModel([("organization_id", ASCENDING)], name="organization_id_idx"),
            IndexModel([("status", ASCENDING)], name="status_idx"),
            IndexModel([("tier_level", ASCENDING)], name="tier_level_idx"),
            IndexModel([("created_at", DESCENDING)], name="created_at_idx"),
            IndexModel([("affiliate_id", ASCENDING), ("status", ASCENDING)], name="affiliate_status_compound_idx"),
            IndexModel([("affiliate_id", ASCENDING), ("created_at", DESCENDING)], name="affiliate_created_compound_idx"),
        ]

        await db.commission_records.create_indexes(commission_records_indexes)
        print("   ✓ Indexes created: affiliate_id, referred_user_id, transaction_id, organization_id, status, tier_level, created_at")
        print("   ✓ Compound indexes: (affiliate_id, status), (affiliate_id, created_at)")

        # ====================================================================
        # 5. PAYOUT_REQUESTS COLLECTION
        # ====================================================================
        print("\n5. Creating payout_requests collection...")

        if "payout_requests" not in collections:
            await db.create_collection("payout_requests")
            print("   ✓ Collection created")
        else:
            print("   ✓ Collection already exists")

        payout_requests_indexes = [
            IndexModel([("affiliate_id", ASCENDING)], name="affiliate_id_idx"),
            IndexModel([("organization_id", ASCENDING)], name="organization_id_idx"),
            IndexModel([("status", ASCENDING)], name="status_idx"),
            IndexModel([("created_at", DESCENDING)], name="created_at_idx"),
            IndexModel([("processed_at", DESCENDING)], name="processed_at_idx"),
            IndexModel([("affiliate_id", ASCENDING), ("status", ASCENDING)], name="affiliate_status_compound_idx"),
            IndexModel([("affiliate_id", ASCENDING), ("created_at", DESCENDING)], name="affiliate_created_compound_idx"),
        ]

        await db.payout_requests.create_indexes(payout_requests_indexes)
        print("   ✓ Indexes created: affiliate_id, organization_id, status, created_at, processed_at")
        print("   ✓ Compound indexes: (affiliate_id, status), (affiliate_id, created_at)")

        # ====================================================================
        # 6. UPDATE USERS COLLECTION
        # ====================================================================
        print("\n6. Updating users collection...")

        # Check if users collection exists
        if "users" in collections:
            # Add is_affiliate field to existing users (default: false)
            result = await db.users.update_many(
                {"is_affiliate": {"$exists": False}},
                {"$set": {"is_affiliate": False}}
            )
            print(f"   ✓ Added is_affiliate field to {result.modified_count} existing users")

            # Create index on is_affiliate
            await db.users.create_indexes([
                IndexModel([("is_affiliate", ASCENDING)], name="is_affiliate_idx")
            ])
            print("   ✓ Index created: is_affiliate")
        else:
            print("   ⚠ Users collection not found - will be created on first user signup")

        # ====================================================================
        # 7. VERIFICATION
        # ====================================================================
        print("\n7. Verifying collections and indexes...")

        collections = await db.list_collection_names()
        affiliate_collections = [
            "affiliate_profiles",
            "referral_links",
            "referral_attributions",
            "commission_records",
            "payout_requests"
        ]

        all_created = all(col in collections for col in affiliate_collections)

        if all_created:
            print("   ✓ All affiliate collections created successfully")
        else:
            missing = [col for col in affiliate_collections if col not in collections]
            print(f"   ✗ Missing collections: {missing}")
            return False

        # Verify indexes
        for collection_name in affiliate_collections:
            collection = db[collection_name]
            indexes = await collection.index_information()
            index_count = len(indexes) - 1  # Exclude default _id index
            print(f"   ✓ {collection_name}: {index_count} indexes")

        print("\n" + "="*60)
        print("✅ Affiliate database initialization complete!")
        print("="*60)
        print("\nCollections created:")
        for col in affiliate_collections:
            print(f"  - {col}")

        print("\nNext steps:")
        print("  1. Restart core_backend service")
        print("  2. Test affiliate endpoints")
        print("  3. Implement frontend components")

        return True

    except Exception as e:
        print(f"\n❌ Error during initialization: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        client.close()


async def test_connection():
    """Test MongoDB connection before initialization."""
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://admin:aawwER4444%25@127.0.0.1:27017/kasaai_core?authSource=admin")

    # Extract database name from URI
    if "/" in mongo_uri.split("@")[-1]:
        uri_db = mongo_uri.split("/")[-1].split("?")[0]
        database_name = uri_db if uri_db else os.getenv("MONGODB_DATABASE", "kasaai_core")
    else:
        database_name = os.getenv("MONGODB_DATABASE", "kasaai_core")

    print("Testing MongoDB connection...")
    print(f"URI: {mongo_uri}")
    print(f"Database: {database_name}")

    try:
        client = AsyncIOMotorClient(mongo_uri, serverSelectionTimeoutMS=5000)
        # Test connection
        await client.admin.command('ping')
        print("✓ MongoDB connection successful\n")
        client.close()
        return True
    except Exception as e:
        print(f"✗ MongoDB connection failed: {str(e)}\n")
        return False


async def main():
    """Main function."""
    print("="*60)
    print("Affiliate Program - Database Initialization")
    print("="*60)
    print()

    # Test connection first
    if not await test_connection():
        print("Please check your MongoDB connection and try again.")
        sys.exit(1)

    # Initialize collections
    success = await init_affiliate_collections()

    if success:
        print("\n✅ Database initialization completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Database initialization failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
