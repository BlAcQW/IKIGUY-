"""
Migration script to convert bus route times from string format to datetime.

Converts departure_time and arrival_time fields from "07:00 AM" format
to proper datetime objects using the conference start date.

Date: 2025-10-28
"""

import os
import sys
from datetime import datetime, timedelta
from pymongo import MongoClient
from bson import ObjectId

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings


def parse_time_string(time_str: str, base_date: datetime) -> datetime:
    """
    Parse time string like "07:00 AM" and combine with base date.

    Args:
        time_str: Time string in format "HH:MM AM/PM"
        base_date: Base date to use for the datetime

    Returns:
        datetime: Parsed datetime object
    """
    if not time_str or not isinstance(time_str, str):
        return None

    try:
        # Parse time (handles "07:00 AM" or "7:00 AM" format)
        time_obj = datetime.strptime(time_str.strip(), "%I:%M %p")

        # Combine with base date
        result = base_date.replace(
            hour=time_obj.hour,
            minute=time_obj.minute,
            second=0,
            microsecond=0
        )

        return result

    except ValueError as e:
        print(f"  ⚠️  Failed to parse time '{time_str}': {e}")
        return None


def migrate_bus_route_times():
    """
    Migrate bus route times from string to datetime format.

    Uses the conference start date as the base date for all bus times.
    Assumes buses run on the first day of the conference.
    """
    print("=" * 60)
    print("Bus Route Time Migration")
    print("=" * 60)
    print(f"MongoDB URL: {settings.mongodb_url}")
    print(f"Database: {settings.mongodb_db_name}")
    print()

    # Connect to MongoDB
    client = MongoClient(settings.mongodb_url)
    db = client[settings.mongodb_db_name]

    try:
        # Get conference info for base date
        conference = db.conferences.find_one()
        if not conference:
            print("❌ No conference found. Cannot determine base date.")
            return False

        base_date = conference.get("start_date")
        if not base_date:
            print("❌ Conference has no start_date. Cannot migrate.")
            return False

        print(f"Conference: {conference['name']}")
        print(f"Base date: {base_date}")
        print()

        # Get all bus routes
        routes = list(db.bus_routes.find())
        total_routes = len(routes)

        print(f"Found {total_routes} bus routes to migrate")
        print()

        migrated_count = 0
        skipped_count = 0
        error_count = 0

        for route in routes:
            route_id = route["_id"]
            route_name = route.get("name") or route.get("route_name", "Unnamed")

            print(f"Processing: {route_name} ({route_id})")

            # Check current time format
            departure_time = route.get("departure_time")
            arrival_time = route.get("arrival_time")

            # Skip if already datetime
            if isinstance(departure_time, datetime):
                print("  ℹ️  Already migrated (departure_time is datetime)")
                skipped_count += 1
                continue

            # Parse and convert times
            updates = {}

            if departure_time:
                parsed_departure = parse_time_string(departure_time, base_date)
                if parsed_departure:
                    updates["departure_time"] = parsed_departure
                    print(f"  ✅ departure_time: '{departure_time}' → {parsed_departure}")
                else:
                    error_count += 1

            if arrival_time:
                parsed_arrival = parse_time_string(arrival_time, base_date)
                if parsed_arrival:
                    updates["arrival_time"] = parsed_arrival
                    print(f"  ✅ arrival_time: '{arrival_time}' → {parsed_arrival}")
                else:
                    error_count += 1

            # Update in database
            if updates:
                updates["updated_at"] = datetime.utcnow()

                result = db.bus_routes.update_one(
                    {"_id": route_id},
                    {"$set": updates}
                )

                if result.modified_count > 0:
                    migrated_count += 1
                    print(f"  ✅ Updated in database")
                else:
                    print(f"  ⚠️  No changes made")
            else:
                skipped_count += 1
                print(f"  ℹ️  No time fields to migrate")

            print()

        # Summary
        print("=" * 60)
        print("Migration Summary")
        print("=" * 60)
        print(f"Total routes: {total_routes}")
        print(f"✅ Migrated: {migrated_count}")
        print(f"ℹ️  Skipped: {skipped_count}")
        print(f"❌ Errors: {error_count}")
        print()

        if migrated_count > 0:
            print("✅ Migration completed successfully!")
        else:
            print("ℹ️  No routes needed migration.")

        return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        client.close()


if __name__ == "__main__":
    print()
    success = migrate_bus_route_times()
    print()

    if not success:
        sys.exit(1)
