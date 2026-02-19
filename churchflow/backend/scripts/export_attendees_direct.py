#!/usr/bin/env python3
"""
Export all conference registrations directly from MongoDB to CSV.

This script:
1. Queries MongoDB directly for all registrations
2. Converts them to a clean CSV format
3. Saves to a file ready for B2C portal audience import

Fields included:
- phone: Primary phone number (required)
- name: Full name of attendee
- email: Email address (if available)
- conference: Conference they registered for
- status: Registration status (confirmed/pending/cancelled)
- checked_in: Whether they checked in
- church: Their church name
- branch: Their branch name
"""

import os
import sys
import csv
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from pymongo import MongoClient
from bson import ObjectId

# Load environment variables
load_dotenv("/opt/kasaai/.env")

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://admin:aawwER4444%25@127.0.0.1:27017/")
MONGODB_DB_NAME = os.getenv("CHURCHFLOW_MONGODB_DB_NAME", "churchflow")


def normalize_phone(phone):
    """Normalize phone number to international format."""
    if not phone:
        return ""

    # Remove spaces, dashes, parentheses
    phone = str(phone).replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

    # If starts with 0, replace with +233 (Ghana)
    if phone.startswith("0"):
        phone = "+233" + phone[1:]

    # If doesn't start with +, assume Ghana and add +233
    if not phone.startswith("+"):
        phone = "+233" + phone

    return phone


def fetch_all_registrations():
    """Fetch all registrations directly from MongoDB."""
    print("\n📥 Connecting to MongoDB...")

    # Connect to MongoDB
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB_NAME]

    print(f"✅ Connected to database: {MONGODB_DB_NAME}")

    # Fetch all registrations
    print("\n📥 Fetching all registrations...")
    registrations = list(db.conference_registrations.find().sort("created_at", -1))
    print(f"✅ Found {len(registrations)} registrations")

    # Fetch related data for enrichment
    print("\n🔍 Enriching data with conference and branch names...")

    # Get unique conference and branch IDs
    conference_ids = set([r["conference_id"] for r in registrations])
    branch_ids = set([r.get("branch_id") for r in registrations if r.get("branch_id")])

    # Fetch conferences and branches
    conferences = {c["_id"]: c for c in db.conferences.find({"_id": {"$in": list(conference_ids)}})}
    branches = {b["_id"]: b for b in db.branches.find({"_id": {"$in": list(branch_ids)}})}

    print(f"   Loaded {len(conferences)} conferences")
    print(f"   Loaded {len(branches)} branches")

    # Enrich registrations with names
    enriched = []
    for reg in registrations:
        conference = conferences.get(reg["conference_id"])
        branch = branches.get(reg.get("branch_id"))

        enriched.append({
            "phone": reg.get("user_phone", ""),
            "name": reg.get("user_name", ""),
            "email": reg.get("user_email", ""),
            "conference": conference["name"] if conference else "Unknown",
            "status": reg.get("status", "confirmed"),
            "checked_in": reg.get("checked_in", False),
            "church": reg.get("church_name", ""),
            "branch": branch["name"] if branch else "",
            "registration_code": reg.get("registration_code", ""),
            "created_at": reg.get("created_at", "")
        })

    client.close()
    return enriched


def export_to_csv(registrations, output_file):
    """Export registrations to CSV file."""
    print(f"\n📝 Exporting to CSV: {output_file}")

    # Define CSV columns for B2C portal import
    fieldnames = [
        "phone",           # Primary identifier (required)
        "name",            # Full name
        "email",           # Email address
        "conference",      # Conference name
        "status",          # Registration status
        "checked_in",      # Check-in status
        "church",          # Church name
        "branch",          # Branch name
        "registration_code", # Unique registration code
        "created_at"       # Registration date
    ]

    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for reg in registrations:
            writer.writerow({
                "phone": normalize_phone(reg.get("phone", "")),
                "name": reg.get("name", ""),
                "email": reg.get("email", ""),
                "conference": reg.get("conference", ""),
                "status": reg.get("status", "confirmed"),
                "checked_in": "Yes" if reg.get("checked_in", False) else "No",
                "church": reg.get("church", ""),
                "branch": reg.get("branch", ""),
                "registration_code": reg.get("registration_code", ""),
                "created_at": str(reg.get("created_at", ""))
            })

    print(f"✅ Successfully exported {len(registrations)} records to CSV")

    # Print summary statistics
    print("\n📊 Export Summary:")
    print(f"   Total registrations: {len(registrations)}")

    checked_in = sum(1 for r in registrations if r.get("checked_in", False))
    print(f"   Checked in: {checked_in}")
    print(f"   Not checked in: {len(registrations) - checked_in}")

    conferences = set(r.get("conference") for r in registrations if r.get("conference"))
    print(f"   Unique conferences: {len(conferences)}")

    branches = set(r.get("branch") for r in registrations if r.get("branch"))
    print(f"   Unique branches: {len(branches)}")

    with_email = sum(1 for r in registrations if r.get("email"))
    print(f"   With email: {with_email}")
    print(f"   Without email: {len(registrations) - with_email}")

    # Show sample of phone numbers
    print("\n📞 Sample phone numbers (first 5):")
    for i, reg in enumerate(registrations[:5]):
        phone = normalize_phone(reg.get("phone", ""))
        name = reg.get("name", "Unknown")
        print(f"   {i+1}. {phone} - {name}")


def main():
    """Main execution function."""
    print("=" * 60)
    print("ChurchFlow - Export All Attendees to CSV (Direct MongoDB)")
    print("=" * 60)

    # Fetch all registrations
    registrations = fetch_all_registrations()

    if not registrations:
        print("\n⚠️  No registrations found in database!")
        return

    # Generate output filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"/opt/kasaai/apps/churchflow/backend/exports/all_attendees_{timestamp}.csv"

    # Create exports directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Export to CSV
    export_to_csv(registrations, output_file)

    print(f"\n🎉 Export complete!")
    print(f"📁 File saved: {output_file}")
    print(f"\n💡 You can now import this CSV into the B2C portal as an audience list.")
    print(f"\n📋 Import instructions:")
    print(f"   1. Go to B2C portal SMS Campaigns")
    print(f"   2. Create new campaign")
    print(f"   3. Select 'Upload CSV Audience'")
    print(f"   4. Upload this file: {output_file}")
    print("=" * 60)


if __name__ == "__main__":
    main()
