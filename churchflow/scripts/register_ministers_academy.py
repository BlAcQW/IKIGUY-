"""
Bulk registration script for Successful Ministers Academy pastors to IMPACT 2025.

This script parses the pastor list and registers all 200 members to the
IMPACT 2025 conference under the Successful Ministers Academy branch.
"""

import re
from datetime import datetime
from bson import ObjectId
from pymongo import MongoClient
import secrets


# MongoDB connection
MONGODB_URL = "mongodb://admin:aawwER4444%25@127.0.0.1:27017/churchflow?authSource=admin"

# IDs from database
CONFERENCE_ID = ObjectId("68fbc116ca541168d5ea195e")  # IMPACT 2025
BRANCH_ID = ObjectId("691f84c430e9ccc62718174a")  # SUCCESSFUL MINISTERS ACADEMY


def generate_registration_code() -> str:
    """Generate a unique registration code."""
    return f"REG-{secrets.token_urlsafe(8).upper()}"


def normalize_phone(phone: str) -> str:
    """
    Normalize phone number to consistent format.

    Args:
        phone: Raw phone number string

    Returns:
        Normalized phone number (digits only, with leading 0 if Ghana number)
    """
    # Remove all non-digit characters except +
    phone = re.sub(r'[^\d+]', '', phone)

    # Handle multiple numbers (take first one)
    if '/' in phone:
        phone = phone.split('/')[0].strip()

    # Remove country code prefix if present
    if phone.startswith('+233'):
        phone = '0' + phone[4:]
    elif phone.startswith('233'):
        phone = '0' + phone[3:]
    elif phone.startswith('+234'):  # Nigeria
        phone = phone  # Keep as is

    # Ensure Ghana numbers start with 0
    if len(phone) == 9 and phone[0] in '2345':
        phone = '0' + phone

    return phone


def parse_pastor_list(file_path: str) -> list:
    """
    Parse the pastor list file and extract names and phone numbers.

    Args:
        file_path: Path to the pastor list file

    Returns:
        List of dicts with 'name' and 'phone' keys
    """
    pastors = []

    with open(file_path, 'r') as f:
        content = f.read()

    # Split by numbered entries - entries start with "number." or "number. "
    # Use regex to split on entry numbers
    entries = re.split(r'\n(?=\d+\.)', content)

    for entry in entries:
        entry = entry.strip()
        if not entry:
            continue

        # Join all lines of the entry (handles multi-line entries)
        entry = ' '.join(line.strip() for line in entry.split('\n') if line.strip())

        parsed = parse_entry(entry)
        if parsed:
            pastors.append(parsed)

    return pastors


def parse_entry(entry: str) -> dict:
    """
    Parse a single entry to extract name and phone.

    Args:
        entry: Raw entry string

    Returns:
        Dict with 'name' and 'phone' or None
    """
    # Remove leading number and dot
    entry = re.sub(r'^\d+\.?\s*', '', entry)

    # Find all phone number patterns - match various Ghana formats
    # Patterns: 0xxxxxxxxx, +233xxxxxxxxx, 233xxxxxxxxx, or with spaces/dashes
    # Also matches numbers like "024 871 4097" (with spaces)
    phone_patterns = [
        r'\+?\d{10,12}',                           # Standard: 0244123456 or +233244123456
        r'\+?233\s?\d{2,3}\s?\d{3}\s?\d{3,4}',     # +233 24 123 4567
        r'0\d{2}\s?\d{3}\s?\d{4}',                 # 024 123 4567
        r'0\d{2}\s\d{3}\s\d{3,4}',                 # 024 123 456
        r'\d{3}\s\d{3}\s\d{4}',                    # 024 871 4097 (without leading 0)
    ]

    phone = None
    phone_start = len(entry)

    for pattern in phone_patterns:
        match = re.search(pattern, entry)
        if match:
            # Take the earliest phone number found
            if match.start() < phone_start:
                phone = match.group(0)
                phone_start = match.start()

    if not phone:
        print(f"Warning: No phone found in entry: {entry}")
        return None

    # Get name (everything before the phone number)
    name_part = entry[:phone_start].strip()

    # Clean up name - remove trailing punctuation
    name = re.sub(r'[-–—:,\.]+$', '', name_part).strip()
    name = re.sub(r'\s+', ' ', name)  # Normalize spaces

    # Remove common prefixes that shouldn't be in the name
    if name.lower().startswith('name:'):
        name = name[5:].strip()

    if not name:
        print(f"Warning: No name found in entry: {entry}")
        return None

    return {
        'name': name,
        'phone': normalize_phone(phone)
    }


def register_pastors(pastors: list, db):
    """
    Register all pastors to the conference.

    Args:
        pastors: List of pastor dicts with name and phone
        db: MongoDB database connection
    """
    registered = 0
    skipped = 0
    errors = []

    for pastor in pastors:
        try:
            # Check if already registered
            existing = db.conference_registrations.find_one({
                "conference_id": CONFERENCE_ID,
                "user_phone": pastor['phone'],
                "status": {"$ne": "cancelled"}
            })

            if existing:
                print(f"  Skipped (already registered): {pastor['name']} - {pastor['phone']}")
                skipped += 1
                continue

            # Generate unique registration code
            registration_code = generate_registration_code()
            while db.conference_registrations.find_one({"registration_code": registration_code}):
                registration_code = generate_registration_code()

            # Create registration document
            registration = {
                "conference_id": CONFERENCE_ID,
                "user_phone": pastor['phone'],
                "user_name": pastor['name'],
                "user_email": None,
                "branch_id": BRANCH_ID,
                "church_name": None,
                "registration_code": registration_code,
                "requires_bus": False,
                "bus_route_id": None,
                "special_needs": None,
                "emergency_contact": None,
                "checked_in": False,
                "checked_in_at": None,
                "status": "confirmed",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "metadata": {
                    "source": "bulk_import",
                    "import_batch": "ministers_academy_2025_11_29"
                }
            }

            db.conference_registrations.insert_one(registration)
            print(f"  Registered: {pastor['name']} - {pastor['phone']} - {registration_code}")
            registered += 1

        except Exception as e:
            error_msg = f"Error registering {pastor['name']}: {str(e)}"
            print(f"  ERROR: {error_msg}")
            errors.append(error_msg)

    return registered, skipped, errors


def main():
    """Main function to run the bulk registration."""
    print("=" * 60)
    print("IMPACT 2025 - Bulk Registration Script")
    print("Successful Ministers Academy Pastors")
    print("=" * 60)

    # Connect to MongoDB
    print("\nConnecting to MongoDB...")
    client = MongoClient(MONGODB_URL)
    db = client.churchflow

    # Verify conference exists
    conference = db.conferences.find_one({"_id": CONFERENCE_ID})
    if not conference:
        print("ERROR: Conference not found!")
        return
    print(f"Conference: {conference['name']}")

    # Verify branch exists
    branch = db.branches.find_one({"_id": BRANCH_ID})
    if not branch:
        print("ERROR: Branch not found!")
        return
    print(f"Branch: {branch['name']}")

    # Parse pastor list
    print("\nParsing pastor list...")
    pastor_file = "/opt/kasaai/apps/churchflow/successful_ministers_academy_pastors_action"
    pastors = parse_pastor_list(pastor_file)
    print(f"Found {len(pastors)} pastors to register")

    # Show sample
    print("\nSample entries:")
    for p in pastors[:3]:
        print(f"  - {p['name']}: {p['phone']}")
    print("  ...")

    # Get current registration count
    current_count = db.conference_registrations.count_documents({
        "conference_id": CONFERENCE_ID,
        "status": {"$ne": "cancelled"}
    })
    print(f"\nCurrent registrations for conference: {current_count}")

    # Register all pastors
    print("\nRegistering pastors...")
    print("-" * 60)
    registered, skipped, errors = register_pastors(pastors, db)
    print("-" * 60)

    # Summary
    print("\n" + "=" * 60)
    print("REGISTRATION SUMMARY")
    print("=" * 60)
    print(f"Total pastors in list: {len(pastors)}")
    print(f"Successfully registered: {registered}")
    print(f"Skipped (already registered): {skipped}")
    print(f"Errors: {len(errors)}")

    # Final count
    final_count = db.conference_registrations.count_documents({
        "conference_id": CONFERENCE_ID,
        "status": {"$ne": "cancelled"}
    })
    print(f"\nTotal conference registrations: {final_count}")

    # Show registrations from Ministers Academy
    academy_count = db.conference_registrations.count_documents({
        "conference_id": CONFERENCE_ID,
        "branch_id": BRANCH_ID,
        "status": {"$ne": "cancelled"}
    })
    print(f"Registrations from Successful Ministers Academy: {academy_count}")

    if errors:
        print("\nErrors encountered:")
        for e in errors:
            print(f"  - {e}")

    print("\nDone!")
    client.close()


if __name__ == "__main__":
    main()
