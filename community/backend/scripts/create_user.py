"""
Create user account for voice-lab dataset management.

Usage:
    python scripts/create_user.py --email alfred.anyan@gmail.com
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv

load_dotenv()


def create_user(email: str, full_name: str = None, is_admin: bool = False):
    """
    Create a new user in the community platform.

    Args:
        email: User email address
        full_name: User's full name
        is_admin: Whether to grant admin permissions

    Returns:
        Created user document
    """
    # Connect to MongoDB
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://kasaai_user:6a6EfjQyaJKvPTLrfpZgCmPQQYUZIq@localhost:27017/ailabsafrica")
    client = MongoClient(mongo_uri)
    db = client.ailabsafrica
    users_collection = db.users

    # Check if user already exists
    existing_user = users_collection.find_one({"email": email})
    if existing_user:
        print(f"✅ User already exists: {email}")
        print(f"   User ID: {existing_user['_id']}")
        print(f"   Level: {existing_user.get('level', 'newcomer')}")
        return existing_user

    # Create new user
    user_level = "guardian" if is_admin else "contributor"
    user_doc = {
        "_id": ObjectId(),
        "email": email,
        "full_name": full_name or email.split("@")[0].replace(".", " ").title(),
        "username": email.split("@")[0].replace(".", "_"),
        "level": user_level,
        "total_points": 1000 if is_admin else 0,
        "level_points": 0,
        "achievements": [],
        "badges": ["early_adopter", "voice_lab_contributor"] if is_admin else [],
        "language_expertise": [],
        "validator_qualifications": [],
        "verified_languages": [],
        "permissions": ["manage_datasets", "upload_data", "create_proposals"] if is_admin else [],
        "can_validate": is_admin,
        "can_moderate": is_admin,
        "can_create_proposals": True,
        "contributions_count": 0,
        "validations_count": 0,
        "quality_rating": 0.0,
        "reputation_score": 100 if is_admin else 0,
        "is_active": True,
        "is_verified": is_admin,
        "email_verified": is_admin,
        "phone_verified": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "last_activity": datetime.utcnow(),
    }

    # Insert user
    result = users_collection.insert_one(user_doc)

    print(f"✅ User created successfully!")
    print(f"   Email: {email}")
    print(f"   User ID: {result.inserted_id}")
    print(f"   Level: {user_doc['level']}")
    print(f"   Permissions: {', '.join(user_doc['permissions']) if user_doc['permissions'] else 'None'}")

    client.close()
    return user_doc


def main():
    parser = argparse.ArgumentParser(description="Create user for community platform")
    parser.add_argument("--email", required=True, help="User email address")
    parser.add_argument("--name", help="User's full name")
    parser.add_argument("--admin", action="store_true", help="Grant admin permissions")

    args = parser.parse_args()

    create_user(args.email, args.name, args.admin)


if __name__ == "__main__":
    main()
