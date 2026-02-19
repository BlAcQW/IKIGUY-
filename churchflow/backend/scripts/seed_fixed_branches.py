#!/usr/bin/env python3
"""
Database seeding script for fixed church branches.

This script:
1. Deletes all existing branches from the database
2. Populates the database with the predefined fixed branch list
3. Handles organization linking and proper data formatting

Run this script to initialize or reset the branches collection.
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId

# Add parent directory to path to import from app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.constants.branches import FIXED_BRANCHES


def get_db():
    """
    Get MongoDB database connection.

    Returns:
        Database connection object.
    """
    mongodb_url = os.getenv(
        "MONGODB_URL",
        "mongodb://admin:aawwER4444%25@127.0.0.1:27017/churchflow?authSource=admin"
    )
    client = MongoClient(mongodb_url)
    return client.churchflow


def get_or_create_default_organization(db):
    """
    Get or create a default organization for branches.

    Args:
        db: Database connection.

    Returns:
        ObjectId: Organization ID.
    """
    # Check if default organization exists
    org = db.organizations.find_one({"name": "Default Church Organization"})

    if not org:
        # Create default organization
        org_data = {
            "name": "Default Church Organization",
            "description": "Default organization for church branches",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "status": "active"
        }
        result = db.organizations.insert_one(org_data)
        print(f"✓ Created default organization with ID: {result.inserted_id}")
        return result.inserted_id
    else:
        print(f"✓ Using existing organization with ID: {org['_id']}")
        return org["_id"]


def seed_branches():
    """
    Seed the database with fixed branches.

    This function:
    1. Connects to MongoDB
    2. Deletes all existing branches
    3. Inserts the fixed branch list from constants
    4. Provides progress feedback
    """
    print("=" * 60)
    print("ChurchFlow Branch Database Seeding Script")
    print("=" * 60)
    print()

    try:
        # Connect to database
        print("→ Connecting to MongoDB...")
        db = get_db()
        print("✓ Connected successfully")
        print()

        # Get or create default organization
        print("→ Setting up organization...")
        org_id = get_or_create_default_organization(db)
        print()

        # Count existing branches
        existing_count = db.branches.count_documents({})
        print(f"→ Found {existing_count} existing branches in database")

        if existing_count > 0:
            # Delete all existing branches
            print("→ Deleting existing branches...")
            result = db.branches.delete_many({})
            print(f"✓ Deleted {result.deleted_count} branches")
        print()

        # Prepare branch documents
        print(f"→ Preparing {len(FIXED_BRANCHES)} branches for insertion...")
        branch_documents = []

        for branch_data in FIXED_BRANCHES:
            document = {
                "name": branch_data["name"],
                "location": branch_data["location"],
                "address": branch_data.get("location"),  # Use location as default address
                "contact_person": None,
                "contact_phone": None,
                "capacity": 100,  # Default capacity
                "status": "active",
                "region": branch_data.get("region"),
                "organization_id": org_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
            branch_documents.append(document)

        print(f"✓ Prepared {len(branch_documents)} branch documents")
        print()

        # Insert branches
        print("→ Inserting branches into database...")
        result = db.branches.insert_many(branch_documents)
        print(f"✓ Successfully inserted {len(result.inserted_ids)} branches")
        print()

        # Verify insertion
        print("→ Verifying insertion...")
        final_count = db.branches.count_documents({})
        print(f"✓ Database now contains {final_count} branches")
        print()

        # Show sample of inserted branches
        print("→ Sample of inserted branches:")
        sample_branches = list(db.branches.find().limit(5))
        for i, branch in enumerate(sample_branches, 1):
            print(f"  {i}. {branch['name']} - {branch['location']}")
        print(f"  ... and {final_count - 5} more")
        print()

        # Show branch count by region
        print("→ Branch distribution by region:")
        pipeline = [
            {"$group": {"_id": "$region", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        region_stats = list(db.branches.aggregate(pipeline))
        for stat in region_stats:
            print(f"  {stat['_id']}: {stat['count']} branches")
        print()

        print("=" * 60)
        print("✓ Database seeding completed successfully!")
        print("=" * 60)
        print()
        print("Summary:")
        print(f"  • Organization ID: {org_id}")
        print(f"  • Total Branches: {final_count}")
        print(f"  • Regions Covered: {len(region_stats)}")
        print()

    except Exception as e:
        print(f"✗ Error during seeding: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    seed_branches()
