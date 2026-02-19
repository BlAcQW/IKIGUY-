#!/usr/bin/env python3
"""
Safe branch update script that preserves existing registrations.

This script:
1. Maps existing branches by name to preserve ObjectIds
2. Only creates new branches for names that don't exist
3. Updates existing branches with new data (location, region, etc.)
4. Preserves all branch_id references in registrations

This is safer than seed_fixed_branches.py which deletes all branches.
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


def safe_update_branches():
    """
    Safely update branches while preserving existing registrations.

    This function:
    1. Maps existing branches by name
    2. Updates existing branches with new data
    3. Creates new branches only for new names
    4. Preserves all ObjectIds for existing branches
    """
    print("=" * 70)
    print("ChurchFlow Safe Branch Update Script")
    print("=" * 70)
    print()
    print("This script will:")
    print("  • Preserve existing branch ObjectIds (keeps registrations intact)")
    print("  • Update existing branches with new data")
    print("  • Add only new branches (the 3 training programs)")
    print("  • Keep all existing registrations linked correctly")
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

        # Get all existing branches and create name-to-id mapping
        print("→ Loading existing branches...")
        existing_branches = list(db.branches.find({}))
        existing_by_name = {b["name"].lower(): b for b in existing_branches}
        print(f"✓ Found {len(existing_branches)} existing branches")
        print()

        # Statistics
        updated_count = 0
        created_count = 0
        unchanged_count = 0

        # Process each branch from FIXED_BRANCHES
        print(f"→ Processing {len(FIXED_BRANCHES)} branches from constants...")
        print()

        for branch_data in FIXED_BRANCHES:
            branch_name = branch_data["name"]
            branch_name_lower = branch_name.lower()

            # Check if branch already exists
            if branch_name_lower in existing_by_name:
                # Update existing branch
                existing_branch = existing_by_name[branch_name_lower]
                branch_id = existing_branch["_id"]

                # Prepare update data
                update_data = {
                    "name": branch_data["name"],
                    "location": branch_data["location"],
                    "address": branch_data.get("location"),
                    "region": branch_data.get("region"),
                    "organization_id": org_id,
                    "updated_at": datetime.utcnow(),
                }

                # Only update if something changed
                needs_update = False
                for key, value in update_data.items():
                    if key != "updated_at" and existing_branch.get(key) != value:
                        needs_update = True
                        break

                if needs_update:
                    db.branches.update_one(
                        {"_id": branch_id},
                        {"$set": update_data}
                    )
                    updated_count += 1
                    print(f"  ✓ Updated: {branch_name}")
                else:
                    unchanged_count += 1
            else:
                # Create new branch
                new_branch = {
                    "name": branch_data["name"],
                    "location": branch_data["location"],
                    "address": branch_data.get("location"),
                    "contact_person": None,
                    "contact_phone": None,
                    "capacity": 100,
                    "status": "active",
                    "region": branch_data.get("region"),
                    "organization_id": org_id,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
                result = db.branches.insert_one(new_branch)
                created_count += 1
                print(f"  + Created: {branch_name} (ID: {result.inserted_id})")

        print()
        print("=" * 70)
        print("✓ Branch update completed successfully!")
        print("=" * 70)
        print()
        print("Summary:")
        print(f"  • Updated branches: {updated_count}")
        print(f"  • Created branches: {created_count}")
        print(f"  • Unchanged branches: {unchanged_count}")
        print(f"  • Total branches in database: {db.branches.count_documents({})}")
        print()

        # Verify registrations are still linked
        print("→ Verifying registration links...")
        registrations_with_branches = db.conference_registrations.count_documents({
            "branch_id": {"$exists": True, "$ne": None}
        })
        
        if registrations_with_branches > 0:
            # Check how many have valid branch references
            pipeline = [
                {"$match": {"branch_id": {"$exists": True, "$ne": None}}},
                {"$group": {"_id": "$branch_id"}},
                {"$lookup": {
                    "from": "branches",
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "branch"
                }},
                {"$match": {"branch": {"$ne": []}}},
                {"$count": "valid_references"}
            ]
            result = list(db.conference_registrations.aggregate(pipeline))
            valid_count = result[0]["valid_references"] if result else 0
            
            print(f"  • Registrations with branch_id: {registrations_with_branches}")
            print(f"  • Valid branch references: {valid_count}")
            
            if valid_count == registrations_with_branches:
                print("  ✓ All registration branch references are valid!")
            else:
                print(f"  ⚠ Warning: {registrations_with_branches - valid_count} registrations have invalid branch references")
        else:
            print("  • No registrations with branch references found")
        
        print()

        # Show new training program branches
        training_branches = list(db.branches.find({"region": "Training Programs"}))
        if training_branches:
            print("→ New Training Program Branches:")
            for branch in training_branches:
                print(f"  • {branch['name']} (ID: {branch['_id']})")
            print()

        print("=" * 70)
        print("✓ All done! Existing registrations are preserved.")
        print("=" * 70)
        print()

    except Exception as e:
        print(f"✗ Error during update: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    safe_update_branches()

