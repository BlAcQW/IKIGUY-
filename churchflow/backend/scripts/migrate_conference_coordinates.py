"""
Migration script to add default GPS coordinates to existing conferences.

This script updates all conferences that don't have GPS coordinates set,
adding the default Action Chapel Spintex location coordinates.

Default coordinates: Action Chapel International Prayer Cathedral, Spintex Road, Accra
- Latitude: 5.62564
- Longitude: -0.164432
- Check-in radius: 1000 meters (1km)

Usage:
    python -m scripts.migrate_conference_coordinates
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Default coordinates for Action Chapel Spintex
DEFAULT_LATITUDE = 5.62564
DEFAULT_LONGITUDE = -0.164432
DEFAULT_CHECKIN_RADIUS = 1000  # 1km in meters


async def migrate_conference_coordinates():
    """
    Update existing conferences without GPS coordinates with default values.

    Returns:
        tuple: (total_conferences, updated_count, already_had_coords)
    """
    # Get MongoDB connection details from environment
    mongodb_url = os.getenv("MONGODB_URL")
    if not mongodb_url:
        raise ValueError("MONGODB_URL not found in environment variables")

    # Connect to MongoDB
    client = AsyncIOMotorClient(mongodb_url)
    db = client.churchflow
    conferences_collection = db.conferences

    try:
        # Count total conferences
        total_conferences = await conferences_collection.count_documents({})
        print(f"\n📊 Total conferences in database: {total_conferences}")

        # Find conferences without GPS coordinates
        query = {
            "$or": [
                {"venue_latitude": {"$exists": False}},
                {"venue_longitude": {"$exists": False}},
                {"venue_latitude": None},
                {"venue_longitude": None}
            ]
        }

        conferences_to_update = await conferences_collection.find(query).to_list(length=None)
        conferences_without_coords = len(conferences_to_update)

        print(f"🔍 Found {conferences_without_coords} conferences without GPS coordinates")

        if conferences_without_coords == 0:
            print("✅ All conferences already have GPS coordinates!")
            return total_conferences, 0, total_conferences

        # Update conferences with default coordinates
        update_data = {
            "$set": {
                "venue_latitude": DEFAULT_LATITUDE,
                "venue_longitude": DEFAULT_LONGITUDE,
                "venue_checkin_radius": DEFAULT_CHECKIN_RADIUS,
                "self_checkin_enabled": True,
                "allow_repeat_checkin": True,
                "updated_at": datetime.utcnow()
            }
        }

        result = await conferences_collection.update_many(query, update_data)
        updated_count = result.modified_count

        print(f"\n✅ Migration completed successfully!")
        print(f"   - Updated conferences: {updated_count}")
        print(f"   - Default coordinates: ({DEFAULT_LATITUDE}, {DEFAULT_LONGITUDE})")
        print(f"   - Check-in radius: {DEFAULT_CHECKIN_RADIUS}m (1km)")
        print(f"   - Self check-in enabled: True")
        print(f"   - Allow repeat check-in: True")

        # Display sample of updated conferences
        if updated_count > 0:
            print(f"\n📝 Sample of updated conferences:")
            sample_conferences = await conferences_collection.find(
                {"venue_latitude": DEFAULT_LATITUDE}
            ).limit(5).to_list(length=5)

            for conf in sample_conferences:
                print(f"   - {conf.get('name', 'Unnamed')} ({conf.get('venue', 'No venue')})")

        already_had_coords = total_conferences - conferences_without_coords
        return total_conferences, updated_count, already_had_coords

    except Exception as e:
        print(f"\n❌ Error during migration: {str(e)}")
        raise
    finally:
        client.close()


async def verify_migration():
    """
    Verify that all conferences now have GPS coordinates.

    Returns:
        bool: True if all conferences have coordinates, False otherwise
    """
    mongodb_url = os.getenv("MONGODB_URL")
    client = AsyncIOMotorClient(mongodb_url)
    db = client.churchflow
    conferences_collection = db.conferences

    try:
        # Check for any conferences still missing coordinates
        query = {
            "$or": [
                {"venue_latitude": {"$exists": False}},
                {"venue_longitude": {"$exists": False}},
                {"venue_latitude": None},
                {"venue_longitude": None}
            ]
        }

        missing_coords = await conferences_collection.count_documents(query)

        print(f"\n🔍 Verification:")
        if missing_coords == 0:
            print("   ✅ All conferences have GPS coordinates!")
            return True
        else:
            print(f"   ⚠️  {missing_coords} conferences still missing coordinates")
            return False

    finally:
        client.close()


async def main():
    """Main migration execution."""
    print("\n" + "="*60)
    print("📍 Conference GPS Coordinates Migration")
    print("="*60)

    try:
        # Run migration
        total, updated, already_had = await migrate_conference_coordinates()

        # Verify migration
        success = await verify_migration()

        # Summary
        print("\n" + "="*60)
        print("📊 Migration Summary")
        print("="*60)
        print(f"Total conferences: {total}")
        print(f"Already had coordinates: {already_had}")
        print(f"Updated with default coordinates: {updated}")
        print(f"Migration status: {'✅ SUCCESS' if success else '⚠️  INCOMPLETE'}")
        print("="*60 + "\n")

        if success:
            print("💡 Next steps:")
            print("   1. Review conferences in the admin panel")
            print("   2. Update coordinates for specific venues as needed")
            print("   3. Test location-based check-in functionality")
            print()

    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
