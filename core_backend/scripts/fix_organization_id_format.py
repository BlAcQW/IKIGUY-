"""
Fix organization_id Format in Collections

This script fixes organization_id fields that were incorrectly set to MongoDB _id
instead of the UUID id field. Affects:
- automation_configs
- vapi_calls
- automation_calls
- campaign_calls (already correct)

Run with: python scripts/fix_organization_id_format.py
"""

import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MongoDB connection
MONGO_URI = os.getenv("MONGODB_URI", "mongodb://admin:aawwER4444%25@127.0.0.1:27017/kasaai_core?authSource=admin")


async def main():
    """Main migration function."""
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGO_URI)
    db = client.kasaai_core

    logger.info("=" * 80)
    logger.info("Starting Organization ID Format Fix")
    logger.info("=" * 80)

    # Step 1: Build mapping of MongoDB _id to UUID id
    logger.info("\n📊 Step 1: Building organization ID mapping...")
    orgs_collection = db.organizations
    org_mapping = {}  # MongoDB _id -> UUID id

    async for org in orgs_collection.find({}):
        mongo_id = str(org["_id"])
        uuid_id = org.get("id")
        if uuid_id:
            org_mapping[mongo_id] = uuid_id
            logger.info(f"  - {org.get('name', 'Unknown')}: {mongo_id} -> {uuid_id}")

    logger.info(f"\n✅ Found {len(org_mapping)} organizations")

    # Step 2: Fix automation_configs
    logger.info("\n📝 Step 2: Fixing automation_configs...")
    configs_collection = db.automation_configs
    fixed_configs = 0
    skipped_configs = 0

    async for config in configs_collection.find({"organization_id": {"$exists": True}}):
        org_id = config.get("organization_id")
        if org_id in org_mapping:
            # This is a MongoDB _id, needs to be converted to UUID
            uuid_id = org_mapping[org_id]
            result = await configs_collection.update_one(
                {"_id": config["_id"]},
                {"$set": {"organization_id": uuid_id}}
            )
            if result.modified_count > 0:
                fixed_configs += 1
                logger.info(f"  ✅ Fixed config {config.get('automation_name')}: {org_id} -> {uuid_id}")
        else:
            # Already correct UUID or not in mapping
            skipped_configs += 1

    logger.info(f"\n📊 Automation Configs: {fixed_configs} fixed, {skipped_configs} skipped")

    # Step 3: Fix vapi_calls
    logger.info("\n📞 Step 3: Fixing vapi_calls...")
    vapi_calls_collection = db.vapi_calls
    fixed_calls = 0
    skipped_calls = 0

    async for call in vapi_calls_collection.find({"organization_id": {"$exists": True}}):
        org_id = call.get("organization_id")
        if org_id in org_mapping:
            # This is a MongoDB _id, needs to be converted to UUID
            uuid_id = org_mapping[org_id]
            result = await vapi_calls_collection.update_one(
                {"_id": call["_id"]},
                {"$set": {"organization_id": uuid_id}}
            )
            if result.modified_count > 0:
                fixed_calls += 1
                if fixed_calls <= 10:  # Only log first 10
                    logger.info(f"  ✅ Fixed call {call.get('call_id')}: {org_id} -> {uuid_id}")
        else:
            skipped_calls += 1

    logger.info(f"\n📊 VAPI Calls: {fixed_calls} fixed, {skipped_calls} skipped")

    # Step 4: Fix automation_calls
    logger.info("\n🤖 Step 4: Fixing automation_calls...")
    automation_calls_collection = db.automation_calls
    fixed_auto_calls = 0
    skipped_auto_calls = 0

    async for call in automation_calls_collection.find({"organization_id": {"$exists": True}}):
        org_id = call.get("organization_id")
        if org_id in org_mapping:
            # This is a MongoDB _id, needs to be converted to UUID
            uuid_id = org_mapping[org_id]
            result = await automation_calls_collection.update_one(
                {"_id": call["_id"]},
                {"$set": {"organization_id": uuid_id}}
            )
            if result.modified_count > 0:
                fixed_auto_calls += 1
                if fixed_auto_calls <= 10:  # Only log first 10
                    logger.info(f"  ✅ Fixed automation call {call.get('call_id')}: {org_id} -> {uuid_id}")
        else:
            skipped_auto_calls += 1

    logger.info(f"\n📊 Automation Calls: {fixed_auto_calls} fixed, {skipped_auto_calls} skipped")

    # Step 5: Fix campaign_calls
    logger.info("\n📋 Step 5: Fixing campaign_calls...")
    campaign_calls_collection = db.campaign_calls
    fixed_campaign_calls = 0
    skipped_campaign_calls = 0

    async for call in campaign_calls_collection.find({"organization_id": {"$exists": True}}):
        org_id = call.get("organization_id")
        if org_id in org_mapping:
            # This is a MongoDB _id, needs to be converted to UUID
            uuid_id = org_mapping[org_id]
            result = await campaign_calls_collection.update_one(
                {"_id": call["_id"]},
                {"$set": {"organization_id": uuid_id}}
            )
            if result.modified_count > 0:
                fixed_campaign_calls += 1
                if fixed_campaign_calls <= 10:  # Only log first 10
                    logger.info(f"  ✅ Fixed campaign call {call.get('_id')}: {org_id} -> {uuid_id}")
        else:
            skipped_campaign_calls += 1

    logger.info(f"\n📊 Campaign Calls: {fixed_campaign_calls} fixed, {skipped_campaign_calls} skipped")

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("MIGRATION SUMMARY")
    logger.info("=" * 80)
    logger.info(f"✅ Automation Configs Fixed: {fixed_configs}")
    logger.info(f"✅ VAPI Calls Fixed: {fixed_calls}")
    logger.info(f"✅ Automation Calls Fixed: {fixed_auto_calls}")
    logger.info(f"✅ Campaign Calls Fixed: {fixed_campaign_calls}")
    logger.info("=" * 80)

    # Close connection
    client.close()
    logger.info("\n✅ Migration completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
