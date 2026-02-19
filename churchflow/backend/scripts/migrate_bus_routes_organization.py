"""
Database migration script to add organization_id to bus routes.

This script:
1. Finds bus routes linked to conferences
2. Adds organization_id from the conference to each bus route
3. Handles orphaned routes (conference doesn't exist)
4. Provides detailed reporting

Run: python apps/churchflow/backend/scripts/migrate_bus_routes_organization.py
"""

import asyncio
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB connection string (password properly URL-encoded)
MONGODB_URL = "mongodb://admin:aawwER4444%25@127.0.0.1:27017/churchflow?authSource=admin"


async def migrate_bus_routes():
    """Add organization_id to all bus routes based on their conference."""

    print("\n" + "=" * 80)
    print("BUS ROUTES ORGANIZATION MIGRATION")
    print("=" * 80)

    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.get_default_database()

    # Count total bus routes
    total_routes = await db.bus_routes.count_documents({})
    routes_with_org = await db.bus_routes.count_documents({"organization_id": {"$exists": True, "$ne": None}})
    routes_without_org = await db.bus_routes.count_documents({"organization_id": {"$exists": False}}) + \
                         await db.bus_routes.count_documents({"organization_id": None})

    print(f"\n📊 Current State:")
    print(f"   Total bus routes: {total_routes}")
    print(f"   ✅ With organization_id: {routes_with_org}")
    print(f"   ❌ Without organization_id: {routes_without_org}")

    if routes_without_org == 0:
        print("\n✅ All bus routes already have organization_id!")
        client.close()
        return

    # Get routes needing migration
    routes = await db.bus_routes.find({
        "$or": [
            {"organization_id": {"$exists": False}},
            {"organization_id": None}
        ]
    }).to_list(length=1000)

    print(f"\n🔄 Processing {len(routes)} bus routes...")

    updated_count = 0
    orphaned_count = 0
    error_count = 0

    for route in routes:
        route_id = route["_id"]
        route_name = route.get("route_name") or route.get("name") or "Unknown Route"
        conference_id = route.get("conference_id")

        try:
            if not conference_id:
                print(f"   ⚠️  Route '{route_name}' ({route_id}) has no conference_id - skipping")
                orphaned_count += 1
                continue

            # Get conference to find organization_id
            # Reason: Bus routes are tied to conferences, organization comes from conference
            conference = await db.conferences.find_one(
                {"_id": ObjectId(conference_id) if isinstance(conference_id, str) else conference_id},
                {"_id": 1, "name": 1, "organization_id": 1}
            )

            if not conference:
                print(f"   ⚠️  Route '{route_name}' references non-existent conference {conference_id}")
                orphaned_count += 1
                continue

            organization_id = conference.get("organization_id")

            if not organization_id:
                print(f"   ⚠️  Conference '{conference.get('name')}' has no organization_id")
                orphaned_count += 1
                continue

            # Update bus route with organization_id
            result = await db.bus_routes.update_one(
                {"_id": route_id},
                {
                    "$set": {
                        "organization_id": organization_id,
                        "updated_at": datetime.utcnow()
                    }
                }
            )

            if result.modified_count > 0:
                print(f"   ✅ Updated '{route_name}' → organization: {organization_id}")
                updated_count += 1
            else:
                print(f"   ℹ️  Route '{route_name}' already has organization_id")

        except Exception as e:
            print(f"   ❌ Error updating route '{route_name}': {str(e)}")
            error_count += 1

    # Final verification
    print(f"\n📊 Migration Results:")
    print(f"   ✅ Successfully updated: {updated_count}")
    print(f"   ⚠️  Orphaned routes (no valid conference): {orphaned_count}")
    print(f"   ❌ Errors: {error_count}")

    # Verify final state
    final_with_org = await db.bus_routes.count_documents({"organization_id": {"$exists": True, "$ne": None}})
    final_without_org = await db.bus_routes.count_documents({"organization_id": {"$exists": False}}) + \
                        await db.bus_routes.count_documents({"organization_id": None})

    print(f"\n📊 Final State:")
    print(f"   Total bus routes: {total_routes}")
    print(f"   ✅ With organization_id: {final_with_org}")
    print(f"   ❌ Without organization_id: {final_without_org}")

    # List orphaned routes that need manual attention
    if orphaned_count > 0:
        print(f"\n⚠️  ORPHANED ROUTES REQUIRING MANUAL ATTENTION:")
        orphaned_routes = await db.bus_routes.find({
            "$or": [
                {"organization_id": {"$exists": False}},
                {"organization_id": None}
            ]
        }).to_list(length=100)

        for route in orphaned_routes:
            route_name = route.get("route_name") or route.get("name") or "Unknown"
            print(f"   - {route_name} (ID: {route['_id']}, Conference: {route.get('conference_id', 'None')})")

        # Offer to assign orphaned routes to IMPACT 2025
        print(f"\n🔍 Checking for IMPACT 2025 conference...")
        impact_conf = await db.conferences.find_one({"name": {"$regex": "IMPACT 2025", "$options": "i"}})

        if impact_conf:
            print(f"   Found IMPACT 2025 (ID: {impact_conf['_id']})")
            print(f"   Organization: {impact_conf.get('organization_id')}")
            print(f"\n🔄 Assigning {len(orphaned_routes)} orphaned routes to IMPACT 2025...")

            reassigned_count = 0
            for route in orphaned_routes:
                route_id = route["_id"]
                route_name = route.get("route_name") or route.get("name") or "Unknown"

                result = await db.bus_routes.update_one(
                    {"_id": route_id},
                    {
                        "$set": {
                            "conference_id": impact_conf["_id"],
                            "organization_id": impact_conf.get("organization_id"),
                            "updated_at": datetime.utcnow()
                        }
                    }
                )

                if result.modified_count > 0:
                    print(f"   ✅ Reassigned '{route_name}' to IMPACT 2025")
                    reassigned_count += 1

            print(f"\n✅ Reassigned {reassigned_count} routes to IMPACT 2025")
        else:
            print(f"   ⚠️  No IMPACT 2025 conference found - orphaned routes need manual reassignment")

    print("\n" + "=" * 80)
    print("✅ Migration Complete!")
    print("=" * 80 + "\n")

    client.close()


if __name__ == "__main__":
    asyncio.run(migrate_bus_routes())
