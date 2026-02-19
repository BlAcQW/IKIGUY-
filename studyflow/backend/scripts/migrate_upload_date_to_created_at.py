"""
Migration script: Rename upload_date field to created_at

This script migrates the materials collection from the old schema
(using 'upload_date') to the new schema (using 'created_at').

Date: 2025-11-18
Reason: Frontend was showing today's date for all materials because
        the Pydantic model expected 'created_at' but database had
        'upload_date', causing default factory to create current date.
"""

import asyncio
from pymongo import MongoClient
from urllib.parse import quote_plus
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv("/opt/kasaai/.env")


async def migrate_upload_date_to_created_at():
    """Migrate upload_date field to created_at in materials collection."""

    # Connect to MongoDB
    username = os.getenv("MONGODB_USERNAME", "admin")
    password = os.getenv("MONGODB_PASSWORD")
    escaped_password = quote_plus(password)

    client = MongoClient(f'mongodb://{username}:{escaped_password}@127.0.0.1:27017/')
    db = client['studyflow']

    print("Migrating materials collection...")
    print("=" * 50)

    # Count materials needing migration
    count = db.materials.count_documents({
        "upload_date": {"$exists": True},
        "created_at": {"$exists": False}
    })

    print(f"Found {count} materials to migrate")

    if count == 0:
        print("No materials need migration. Exiting.")
        return

    # Perform migration
    result = db.materials.update_many(
        {
            "upload_date": {"$exists": True},
            "created_at": {"$exists": False}
        },
        [
            {
                "$set": {
                    "created_at": "$upload_date",
                    "updated_at": "$upload_date"
                }
            },
            {
                "$unset": "upload_date"
            }
        ]
    )

    print(f"Migrated {result.modified_count} materials")

    # Verify migration
    print("\nVerification:")
    print("-" * 50)

    remaining = db.materials.count_documents({"upload_date": {"$exists": True}})
    print(f"Materials still with upload_date: {remaining}")

    migrated = db.materials.count_documents({"created_at": {"$exists": True}})
    print(f"Materials with created_at: {migrated}")

    # Show sample
    print("\nSample migrated materials:")
    materials = list(db.materials.find({}).limit(3))
    for m in materials:
        print(f"  - {m.get('title', 'N/A')[:50]}")
        print(f"    created_at: {m.get('created_at')}")
        print(f"    upload_date: {m.get('upload_date', 'REMOVED')}")

    print("\n✓ Migration completed successfully!")

    client.close()


if __name__ == "__main__":
    asyncio.run(migrate_upload_date_to_created_at())
