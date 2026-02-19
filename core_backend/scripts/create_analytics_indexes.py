"""
Create MongoDB indexes for affiliate analytics performance.

This script creates indexes on the referral_clicks collection to optimize
query performance for analytics endpoints.

Run with: python scripts/create_analytics_indexes.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv(project_root / ".env")

MONGO_URI = os.getenv("MONGODB_URI", "mongodb://admin:aawwER4444%25@127.0.0.1:27017/kasaai_core?authSource=admin")
DATABASE_NAME = "kasaai_core"


async def create_indexes():
    """Create analytics indexes on referral_clicks collection."""
    print(f"🔗 Connecting to MongoDB: {DATABASE_NAME}")
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db["referral_clicks"]

    print("\n📊 Creating indexes for analytics performance...")

    # Index 1: For conversion analytics by affiliate and time
    print("\n1. Creating index: affiliate_id + clicked_at (descending)")
    await collection.create_index(
        [("affiliate_id", 1), ("clicked_at", -1)],
        name="idx_affiliate_clicks_time"
    )
    print("   ✅ Created: idx_affiliate_clicks_time")

    # Index 2: For conversion tracking
    print("\n2. Creating index: affiliate_id + converted")
    await collection.create_index(
        [("affiliate_id", 1), ("converted", 1)],
        name="idx_affiliate_conversions"
    )
    print("   ✅ Created: idx_affiliate_conversions")

    # Index 3: For referral code lookups (used in mark_click_converted)
    print("\n3. Creating index: referral_code + clicked_at (descending)")
    await collection.create_index(
        [("referral_code", 1), ("clicked_at", -1)],
        name="idx_referral_code_time"
    )
    print("   ✅ Created: idx_referral_code_time")

    # Index 4: For UTM campaign analytics
    print("\n4. Creating index: utm_campaign + clicked_at (descending)")
    await collection.create_index(
        [("utm_campaign", 1), ("clicked_at", -1)],
        name="idx_utm_campaign_time",
        sparse=True  # Only index documents with utm_campaign
    )
    print("   ✅ Created: idx_utm_campaign_time (sparse)")

    # Index 5: For UTM source analytics
    print("\n5. Creating index: utm_source + clicked_at (descending)")
    await collection.create_index(
        [("utm_source", 1), ("clicked_at", -1)],
        name="idx_utm_source_time",
        sparse=True  # Only index documents with utm_source
    )
    print("   ✅ Created: idx_utm_source_time (sparse)")

    # Index 6: For organization-level analytics
    print("\n6. Creating index: organization_id + affiliate_id + clicked_at")
    await collection.create_index(
        [("organization_id", 1), ("affiliate_id", 1), ("clicked_at", -1)],
        name="idx_org_affiliate_time"
    )
    print("   ✅ Created: idx_org_affiliate_time")

    # List all indexes
    print("\n📋 All indexes on referral_clicks collection:")
    indexes = await collection.list_indexes().to_list(None)
    for idx in indexes:
        print(f"   - {idx['name']}: {idx.get('key', {})}")

    # Get collection stats
    stats = await db.command("collStats", "referral_clicks")
    print(f"\n📊 Collection Stats:")
    print(f"   - Documents: {stats.get('count', 0):,}")
    print(f"   - Size: {stats.get('size', 0) / 1024:.2f} KB")
    print(f"   - Indexes: {stats.get('nindexes', 0)}")
    print(f"   - Total Index Size: {stats.get('totalIndexSize', 0) / 1024:.2f} KB")

    client.close()
    print("\n✅ All indexes created successfully!")


if __name__ == "__main__":
    print("=" * 70)
    print("Creating Analytics Indexes for Affiliate System")
    print("=" * 70)
    asyncio.run(create_indexes())
    print("\n" + "=" * 70)
    print("Done! Analytics queries will now be much faster.")
    print("=" * 70)
