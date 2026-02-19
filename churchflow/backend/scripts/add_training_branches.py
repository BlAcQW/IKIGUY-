#!/usr/bin/env python3
"""
Simple script to add only the 3 new training program branches.

This script:
1. Checks if branches already exist (by name)
2. Only adds the 3 new training program branches
3. Does not modify or delete any existing branches
4. Safe to run multiple times (idempotent)
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
    # Check for default organization (try both possible names)
    org = db.organizations.find_one({
        "$or": [
            {"name": "Default Church Organization"},
            {"is_default": True}
        ]
    })

    if not org:
        # Create default organization
        org_data = {
            "name": "Default Church Organization",
            "description": "Default organization for church branches",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "status": "active",
            "is_default": True
        }
        result = db.organizations.insert_one(org_data)
        print(f"✓ Created default organization with ID: {result.inserted_id}")
        return result.inserted_id
    else:
        print(f"✓ Using existing organization with ID: {org['_id']}")
        return org["_id"]


def add_training_branches():
    """
    Add only the 3 new training program branches.
    
    This is safe to run multiple times - it checks if branches exist first.
    """
    print("=" * 70)
    print("Add Training Program Branches")
    print("=" * 70)
    print()
    print("This script will add only the 3 new training program branches:")
    print("  • SUCCESSFUL MINISTERS ACADEMY")
    print("  • DTS Alumni")
    print("  • DTS Students")
    print()
    print("Existing branches will NOT be modified or deleted.")
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

        # Define the 3 new training program branches
        new_branches = [
            {
                "name": "SUCCESSFUL MINISTERS ACADEMY",
                "location": "Action Chapel International, Accra, Ghana",
                "region": "Training Programs"
            },
            {
                "name": "DTS Alumni",
                "location": "Action Chapel International, Accra, Ghana",
                "region": "Training Programs"
            },
            {
                "name": "DTS Students",
                "location": "Action Chapel International, Accra, Ghana",
                "region": "Training Programs"
            }
        ]

        # Check existing branches
        existing_branch_names = {b["name"].lower() for b in db.branches.find({}, {"name": 1})}
        print(f"→ Found {len(existing_branch_names)} existing branches")
        print()

        # Add new branches
        added_count = 0
        skipped_count = 0

        print("→ Processing new branches...")
        for branch_data in new_branches:
            branch_name = branch_data["name"]
            branch_name_lower = branch_name.lower()

            # Check if branch already exists
            if branch_name_lower in existing_branch_names:
                print(f"  ⊘ Skipped: {branch_name} (already exists)")
                skipped_count += 1
            else:
                # Create new branch
                new_branch = {
                    "name": branch_data["name"],
                    "location": branch_data["location"],
                    "address": branch_data["location"],
                    "contact_person": None,
                    "contact_phone": None,
                    "capacity": 100,
                    "status": "active",
                    "region": branch_data["region"],
                    "organization_id": org_id,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
                result = db.branches.insert_one(new_branch)
                print(f"  ✓ Added: {branch_name} (ID: {result.inserted_id})")
                added_count += 1
                # Update existing names set for next iteration
                existing_branch_names.add(branch_name_lower)

        print()
        print("=" * 70)
        print("✓ Branch addition completed!")
        print("=" * 70)
        print()
        print("Summary:")
        print(f"  • Branches added: {added_count}")
        print(f"  • Branches skipped (already exist): {skipped_count}")
        print(f"  • Total branches in database: {db.branches.count_documents({})}")
        print()

        # Verify the new branches
        training_branches = list(db.branches.find({"region": "Training Programs"}))
        if training_branches:
            print("→ Training Program Branches:")
            for branch in sorted(training_branches, key=lambda x: x["name"]):
                print(f"  • {branch['name']} (ID: {branch['_id']})")
            print()

        print("=" * 70)
        print("✓ All done! Existing branches and registrations are untouched.")
        print("=" * 70)
        print()

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    add_training_branches()

