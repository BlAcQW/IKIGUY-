"""
Bulk registration script for Archbishop Ministerial Network pastors to IMPACT 2025.

This script:
1. Parses the Excel file with pastor data
2. Checks for duplicates against existing registrations
3. Supports multiple phone numbers per registration (stored in metadata)
4. Registers new pastors to the Archbishop Ministerial Network branch
"""

import re
import pandas as pd
from datetime import datetime
from bson import ObjectId
from pymongo import MongoClient
import secrets


# MongoDB connection
MONGODB_URL = "mongodb://admin:aawwER4444%25@127.0.0.1:27017/churchflow?authSource=admin"

# IDs from database
CONFERENCE_ID = ObjectId("68fbc116ca541168d5ea195e")  # IMPACT 2025
BRANCH_ID = ObjectId("692ab5f9876fdce3adce5f47")  # Archbishop Ministerial Network


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
    if pd.isna(phone) or not phone:
        return None

    # Convert to string
    phone = str(phone).strip()

    # Remove all non-digit characters except +
    phone = re.sub(r'[^\d+]', '', phone)

    # Remove country code prefix if present
    if phone.startswith('+233'):
        phone = '0' + phone[4:]
    elif phone.startswith('233') and len(phone) > 10:
        phone = '0' + phone[3:]
    elif phone.startswith('+234'):  # Nigeria
        phone = phone  # Keep as is

    # Ensure Ghana numbers start with 0
    if len(phone) == 9 and phone[0] in '2345':
        phone = '0' + phone

    # Validate length
    if len(phone) < 9 or len(phone) > 15:
        return None

    return phone


def extract_multiple_phones(phone_str: str) -> list:
    """
    Extract multiple phone numbers from a string.

    Handles formats like:
    - "0241234567"
    - "0241234567/0551234567"
    - "024 123 4567 / 055 123 4567"
    - "0241234567, 0551234567"

    Args:
        phone_str: Raw phone string potentially containing multiple numbers

    Returns:
        List of normalized phone numbers
    """
    if pd.isna(phone_str) or not phone_str:
        return []

    phone_str = str(phone_str).strip()

    # Split by common separators
    parts = re.split(r'[/,;]', phone_str)

    phones = []
    for part in parts:
        normalized = normalize_phone(part.strip())
        if normalized and normalized not in phones:
            phones.append(normalized)

    return phones


def parse_excel_file(file_path: str) -> list:
    """
    Parse the Excel file and extract pastor data.

    Args:
        file_path: Path to the Excel file

    Returns:
        List of dicts with pastor data
    """
    df = pd.read_excel(file_path)

    pastors = []
    seen_phones = set()  # Track phones within this file to avoid duplicates

    for idx, row in df.iterrows():
        # Extract name
        title = str(row.get('TITLE', '')).strip() if pd.notna(row.get('TITLE')) else ''
        surname = str(row.get('SURNAME', '')).strip() if pd.notna(row.get('SURNAME')) else ''
        first_name = str(row.get('FIRST NAME', '')).strip() if pd.notna(row.get('FIRST NAME')) else ''

        # Build full name
        name_parts = []
        if title and title.lower() not in ['mr', 'mrs', 'ms', 'miss']:
            name_parts.append(title)
        if first_name:
            name_parts.append(first_name)
        if surname:
            name_parts.append(surname)

        full_name = ' '.join(name_parts).strip()
        if not full_name:
            print(f"  Warning: Skipping row {idx + 2} - no name found")
            continue

        # Extract phone numbers (support multiple)
        phones = extract_multiple_phones(row.get('TEL'))
        if not phones:
            print(f"  Warning: Skipping row {idx + 2} ({full_name}) - no valid phone found")
            continue

        # Check for duplicates within this file
        primary_phone = phones[0]
        if primary_phone in seen_phones:
            print(f"  Warning: Skipping duplicate in file - {full_name} ({primary_phone})")
            continue

        # Mark all phones as seen
        for p in phones:
            seen_phones.add(p)

        # Extract other fields
        email = str(row.get('EMAIL', '')).strip() if pd.notna(row.get('EMAIL')) else None
        if email and not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            email = None  # Invalid email format

        church_name = str(row.get('NAME OF CHURCH', '')).strip() if pd.notna(row.get('NAME OF CHURCH')) else None
        position = str(row.get('POSITION IN CHURCH', '')).strip() if pd.notna(row.get('POSITION IN CHURCH')) else None

        pastors.append({
            'name': full_name,
            'phones': phones,  # List of phone numbers
            'primary_phone': primary_phone,
            'email': email,
            'church_name': church_name,
            'position': position,
            'title': title
        })

    return pastors


def check_existing_registrations(db, phones: list) -> dict:
    """
    Check if any phone numbers are already registered.

    Args:
        db: MongoDB database connection
        phones: List of phone numbers to check

    Returns:
        Dict with phone as key and registration doc as value (if exists)
    """
    existing = {}

    for phone in phones:
        # Check primary phone field
        reg = db.conference_registrations.find_one({
            "conference_id": CONFERENCE_ID,
            "user_phone": phone,
            "status": {"$ne": "cancelled"}
        })
        if reg:
            existing[phone] = reg
            continue

        # Check alternate_phones in metadata
        reg = db.conference_registrations.find_one({
            "conference_id": CONFERENCE_ID,
            "metadata.alternate_phones": phone,
            "status": {"$ne": "cancelled"}
        })
        if reg:
            existing[phone] = reg

    return existing


def register_pastors(pastors: list, db):
    """
    Register all pastors to the conference.

    Args:
        pastors: List of pastor dicts
        db: MongoDB database connection
    """
    registered = 0
    skipped_duplicate = 0
    updated = 0
    errors = []

    for pastor in pastors:
        try:
            # Check for existing registrations using any of the phone numbers
            existing = check_existing_registrations(db, pastor['phones'])

            if existing:
                # Already registered - check if we need to add alternate phones
                first_existing = list(existing.values())[0]
                existing_phones = [first_existing['user_phone']]
                existing_phones.extend(first_existing.get('metadata', {}).get('alternate_phones', []))

                # Check if any new phones to add
                new_phones = [p for p in pastor['phones'] if p not in existing_phones]

                if new_phones:
                    # Update with new alternate phones
                    current_alternates = first_existing.get('metadata', {}).get('alternate_phones', [])
                    updated_alternates = list(set(current_alternates + new_phones))

                    db.conference_registrations.update_one(
                        {"_id": first_existing["_id"]},
                        {
                            "$set": {
                                "metadata.alternate_phones": updated_alternates,
                                "updated_at": datetime.utcnow()
                            }
                        }
                    )
                    print(f"  Updated: {pastor['name']} - added phones: {new_phones}")
                    updated += 1
                else:
                    existing_phone = list(existing.keys())[0]
                    print(f"  Skipped (already registered): {pastor['name']} - {existing_phone}")
                    skipped_duplicate += 1
                continue

            # Generate unique registration code
            registration_code = generate_registration_code()
            while db.conference_registrations.find_one({"registration_code": registration_code}):
                registration_code = generate_registration_code()

            # Prepare alternate phones (all phones except primary)
            alternate_phones = pastor['phones'][1:] if len(pastor['phones']) > 1 else []

            # Create registration document
            registration = {
                "conference_id": CONFERENCE_ID,
                "user_phone": pastor['primary_phone'],
                "user_name": pastor['name'],
                "user_email": pastor['email'],
                "branch_id": BRANCH_ID,
                "church_name": pastor.get('church_name'),
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
                    "import_batch": "archbishop_network_excel_2025_11_29",
                    "alternate_phones": alternate_phones,
                    "title": pastor.get('title'),
                    "position": pastor.get('position'),
                    "original_church_name": pastor.get('church_name')
                }
            }

            db.conference_registrations.insert_one(registration)
            phones_str = ', '.join(pastor['phones'])
            print(f"  Registered: {pastor['name']} - {phones_str} - {registration_code}")
            registered += 1

        except Exception as e:
            error_msg = f"Error registering {pastor['name']}: {str(e)}"
            print(f"  ERROR: {error_msg}")
            errors.append(error_msg)

    return registered, skipped_duplicate, updated, errors


def main():
    """Main function to run the bulk registration."""
    print("=" * 70)
    print("IMPACT 2025 - Bulk Registration Script")
    print("Archbishop Ministerial Network - Excel Import")
    print("=" * 70)

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

    # Parse Excel file
    print("\nParsing Excel file...")
    excel_file = "/opt/kasaai/apps/churchflow/PASTORS & LEADERS LIST ARCHBISHOP.xlsx"
    pastors = parse_excel_file(excel_file)
    print(f"Found {len(pastors)} valid pastor entries")

    # Show sample
    print("\nSample entries:")
    for p in pastors[:3]:
        phones_str = ', '.join(p['phones'])
        print(f"  - {p['name']}: {phones_str}")
    print("  ...")

    # Get current registration count
    current_count = db.conference_registrations.count_documents({
        "conference_id": CONFERENCE_ID,
        "branch_id": BRANCH_ID,
        "status": {"$ne": "cancelled"}
    })
    print(f"\nCurrent Archbishop Ministerial Network registrations: {current_count}")

    # Register all pastors
    print("\nProcessing registrations...")
    print("-" * 70)
    registered, skipped, updated, errors = register_pastors(pastors, db)
    print("-" * 70)

    # Summary
    print("\n" + "=" * 70)
    print("REGISTRATION SUMMARY")
    print("=" * 70)
    print(f"Total entries in Excel: {len(pastors)}")
    print(f"Successfully registered (new): {registered}")
    print(f"Updated (added phones): {updated}")
    print(f"Skipped (already registered): {skipped}")
    print(f"Errors: {len(errors)}")

    # Final count
    final_count = db.conference_registrations.count_documents({
        "conference_id": CONFERENCE_ID,
        "branch_id": BRANCH_ID,
        "status": {"$ne": "cancelled"}
    })
    print(f"\nTotal Archbishop Ministerial Network registrations: {final_count}")

    # Show registrations with multiple phones
    multi_phone_count = db.conference_registrations.count_documents({
        "conference_id": CONFERENCE_ID,
        "branch_id": BRANCH_ID,
        "metadata.alternate_phones.0": {"$exists": True}
    })
    print(f"Registrations with multiple phones: {multi_phone_count}")

    if errors:
        print("\nErrors encountered:")
        for e in errors:
            print(f"  - {e}")

    print("\nDone!")
    client.close()


if __name__ == "__main__":
    main()
