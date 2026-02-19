#!/usr/bin/env python3
"""
Export all conference registrations to CSV for import into B2C portal.

This script:
1. Fetches all registrations from the ChurchFlow API
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
import json
import requests
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment variables
load_dotenv("/opt/kasaai/.env")

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "https://churchflow-api.ailabsafrica.com/api/v1")
SUPABASE_URL = os.getenv("CHURCHFLOW_SUPABASE_URL", "https://supabase.ailabsafrica.com")
SUPABASE_ANON_KEY = os.getenv("CHURCHFLOW_SUPABASE_ANON_KEY")

# Default admin credentials
ADMIN_EMAIL = "admin@ailabsafrica.com"
ADMIN_PASSWORD = "Passw0rd!"  # Default password from setup


def get_admin_token():
    """Get JWT token by logging in as admin."""
    print("🔐 Logging in as admin...")

    # Login via Supabase
    login_url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }

    response = requests.post(login_url, headers=headers, json=data)

    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✅ Successfully logged in as {ADMIN_EMAIL}")
        return token
    else:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        sys.exit(1)


def fetch_all_registrations(token):
    """Fetch all registrations from the API."""
    print("\n📥 Fetching all registrations from API...")

    url = f"{API_BASE_URL}/registrations/export"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        registrations = response.json()
        print(f"✅ Successfully fetched {len(registrations)} registrations")
        return registrations
    else:
        print(f"❌ Failed to fetch registrations: {response.status_code} - {response.text}")
        sys.exit(1)


def normalize_phone(phone):
    """Normalize phone number to international format."""
    if not phone:
        return ""

    # Remove spaces, dashes, parentheses
    phone = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

    # If starts with 0, replace with +233 (Ghana)
    if phone.startswith("0"):
        phone = "+233" + phone[1:]

    # If doesn't start with +, assume Ghana and add +233
    if not phone.startswith("+"):
        phone = "+233" + phone

    return phone


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
                "phone": normalize_phone(reg.get("user_phone", "")),
                "name": reg.get("user_name", ""),
                "email": reg.get("user_email", ""),
                "conference": reg.get("conference_name", ""),
                "status": reg.get("status", "confirmed"),
                "checked_in": "Yes" if reg.get("checked_in", False) else "No",
                "church": reg.get("church_name", ""),
                "branch": reg.get("branch_name", ""),
                "registration_code": reg.get("registration_code", ""),
                "created_at": reg.get("created_at", "")
            })

    print(f"✅ Successfully exported {len(registrations)} records to CSV")

    # Print summary statistics
    print("\n📊 Export Summary:")
    print(f"   Total registrations: {len(registrations)}")

    checked_in = sum(1 for r in registrations if r.get("checked_in", False))
    print(f"   Checked in: {checked_in}")
    print(f"   Not checked in: {len(registrations) - checked_in}")

    conferences = set(r.get("conference_name") for r in registrations if r.get("conference_name"))
    print(f"   Conferences: {len(conferences)}")

    branches = set(r.get("branch_name") for r in registrations if r.get("branch_name"))
    print(f"   Branches: {len(branches)}")

    with_email = sum(1 for r in registrations if r.get("user_email"))
    print(f"   With email: {with_email}")
    print(f"   Without email: {len(registrations) - with_email}")


def main():
    """Main execution function."""
    print("=" * 60)
    print("ChurchFlow - Export All Attendees to CSV")
    print("=" * 60)

    # Get authentication token
    token = get_admin_token()

    # Fetch all registrations
    registrations = fetch_all_registrations(token)

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
    print("=" * 60)


if __name__ == "__main__":
    main()
