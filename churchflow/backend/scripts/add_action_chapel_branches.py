#!/usr/bin/env python3
"""
Add additional branches for Action Chapel International.

This script adds multiple branch locations across Ghana.
"""

import sys
from pathlib import Path

# Add the parent directory to sys.path to import from app
sys.path.insert(0, str(Path(__file__).parent.parent))

from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def add_branches():
    """Add Action Chapel International branches."""

    # Connect to MongoDB
    mongodb_url = os.getenv(
        "MONGODB_URL",
        "mongodb://admin:aawwER4444%25@127.0.0.1:27017/churchflow?authSource=admin"
    )

    print("📡 Connecting to MongoDB...")
    client = MongoClient(mongodb_url)
    db = client.churchflow

    # Get Action Chapel organization
    org = db.organizations.find_one({"slug": "action-chapel-international"})
    if not org:
        print("❌ Action Chapel International organization not found!")
        print("   Run init_action_chapel.py first")
        sys.exit(1)

    org_id = org["_id"]
    print(f"✅ Found organization: {org['name']} ({org_id})")

    # Define branches
    branches = [
        {
            "name": "Action Chapel - Tema",
            "slug": "action-chapel-tema",
            "location": "Tema, Greater Accra Region, Ghana",
            "contact_info": {
                "phone": "+233303123456",
                "email": "tema@actionchapel.net",
                "address": "Tema Community 1, Ghana"
            },
            "capacity": 2000,
            "pastor_name": "Rev. Emmanuel Mensah",
            "service_times": [
                "Sunday First Service: 7:30 AM",
                "Sunday Second Service: 9:30 AM",
                "Wednesday Service: 6:00 PM"
            ]
        },
        {
            "name": "Action Chapel - Kumasi",
            "slug": "action-chapel-kumasi",
            "location": "Kumasi, Ashanti Region, Ghana",
            "contact_info": {
                "phone": "+233322234567",
                "email": "kumasi@actionchapel.net",
                "address": "Ahodwo, Kumasi, Ghana"
            },
            "capacity": 3000,
            "pastor_name": "Rev. Dr. Samuel Agyei",
            "service_times": [
                "Sunday First Service: 7:00 AM",
                "Sunday Second Service: 9:00 AM",
                "Sunday Third Service: 11:00 AM",
                "Friday Service: 6:00 PM"
            ]
        },
        {
            "name": "Action Chapel - Takoradi",
            "slug": "action-chapel-takoradi",
            "location": "Takoradi, Western Region, Ghana",
            "contact_info": {
                "phone": "+233312345678",
                "email": "takoradi@actionchapel.net",
                "address": "Market Circle, Takoradi, Ghana"
            },
            "capacity": 1500,
            "pastor_name": "Pastor Francis Mensah",
            "service_times": [
                "Sunday Service: 8:30 AM",
                "Wednesday Service: 6:00 PM"
            ]
        },
        {
            "name": "Action Chapel - Cape Coast",
            "slug": "action-chapel-cape-coast",
            "location": "Cape Coast, Central Region, Ghana",
            "contact_info": {
                "phone": "+233332456789",
                "email": "capecoast@actionchapel.net",
                "address": "University Road, Cape Coast, Ghana"
            },
            "capacity": 1200,
            "pastor_name": "Pastor Mary Acquah",
            "service_times": [
                "Sunday Service: 9:00 AM",
                "Thursday Service: 6:00 PM"
            ]
        },
        {
            "name": "Action Chapel - Tamale",
            "slug": "action-chapel-tamale",
            "location": "Tamale, Northern Region, Ghana",
            "contact_info": {
                "phone": "+233372567890",
                "email": "tamale@actionchapel.net",
                "address": "Central Tamale, Ghana"
            },
            "capacity": 1000,
            "pastor_name": "Pastor Ibrahim Mohammed",
            "service_times": [
                "Sunday Service: 8:00 AM",
                "Wednesday Service: 5:30 PM"
            ]
        },
        {
            "name": "Action Chapel - East Legon",
            "slug": "action-chapel-east-legon",
            "location": "East Legon, Accra, Ghana",
            "contact_info": {
                "phone": "+233302678901",
                "email": "eastlegon@actionchapel.net",
                "address": "East Legon, Accra, Ghana"
            },
            "capacity": 2500,
            "pastor_name": "Rev. Emmanuel Adjei",
            "service_times": [
                "Sunday First Service: 7:30 AM",
                "Sunday Second Service: 9:30 AM",
                "Sunday Third Service: 11:30 AM",
                "Wednesday Service: 6:00 PM"
            ]
        },
        {
            "name": "Action Chapel - Spintex",
            "slug": "action-chapel-spintex",
            "location": "Spintex, Accra, Ghana",
            "contact_info": {
                "phone": "+233302789012",
                "email": "spintex@actionchapel.net",
                "address": "Spintex Road, Accra, Ghana"
            },
            "capacity": 1800,
            "pastor_name": "Pastor Sarah Ofori",
            "service_times": [
                "Sunday First Service: 8:00 AM",
                "Sunday Second Service: 10:00 AM",
                "Friday Service: 6:00 PM"
            ]
        },
        {
            "name": "Action Chapel - Ho",
            "slug": "action-chapel-ho",
            "location": "Ho, Volta Region, Ghana",
            "contact_info": {
                "phone": "+233362890123",
                "email": "ho@actionchapel.net",
                "address": "Ho Central, Ghana"
            },
            "capacity": 800,
            "pastor_name": "Pastor Benjamin Agbeko",
            "service_times": [
                "Sunday Service: 9:00 AM",
                "Wednesday Service: 6:00 PM"
            ]
        }
    ]

    print(f"\n🏢 Adding {len(branches)} branches...")

    added_count = 0
    skipped_count = 0

    for branch_data in branches:
        # Check if branch already exists
        existing = db.branches.find_one({"slug": branch_data["slug"]})
        if existing:
            print(f"   ⏭️  {branch_data['name']} - Already exists")
            skipped_count += 1
            continue

        # Create branch
        branch = {
            "organization_id": org_id,
            "name": branch_data["name"],
            "slug": branch_data["slug"],
            "location": branch_data["location"],
            "contact_info": branch_data["contact_info"],
            "is_headquarters": False,
            "capacity": branch_data["capacity"],
            "pastor_name": branch_data["pastor_name"],
            "service_times": branch_data["service_times"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "metadata": {
                "type": "branch",
                "region": branch_data["location"].split(",")[-2].strip() if "," in branch_data["location"] else "Ghana"
            }
        }

        result = db.branches.insert_one(branch)
        print(f"   ✅ {branch_data['name']} - {result.inserted_id}")
        added_count += 1

    print(f"\n🎉 Branch setup complete!")
    print(f"   Added: {added_count}")
    print(f"   Skipped (existing): {skipped_count}")

    # Show total branches
    total_branches = db.branches.count_documents({"organization_id": org_id})
    print(f"   Total branches for {org['name']}: {total_branches}")

    # List all branches
    print(f"\n📋 All branches:")
    for branch in db.branches.find({"organization_id": org_id}).sort("name", 1):
        hq_marker = " [HQ]" if branch.get("is_headquarters") else ""
        print(f"   - {branch['name']}{hq_marker} ({branch.get('capacity', 0)} capacity)")

    return {
        "added": added_count,
        "skipped": skipped_count,
        "total": total_branches
    }


if __name__ == "__main__":
    try:
        result = add_branches()
        print("\n✅ All branches added successfully!")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
