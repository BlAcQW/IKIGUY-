#!/usr/bin/env python3
"""
Create default users for DevotionalFlow (FreshManna) platform.

Creates:
- admin@ailabsafrica.com (Universal Admin) - password: Admin@2024!
- user@ailabsafrica.com (Regular User) - password: User@123
- admin@freshmanna.com (Platform Admin) - password: Admin@123

These users are consistent across all KasaAI applications.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from app.utils.auth import get_password_hash
from datetime import datetime


async def create_default_users():
    """Create default users if they don't exist."""

    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.DATABASE_NAME]

    # Default users configuration
    default_users = [
        {
            "email": "admin@ailabsafrica.com",
            "password": "Admin@2024!",
            "name": "KasaAI Admin",
            "role": "pastor",
            "ministry_name": "Fresh Manna",
            "bio": "Universal admin account for all KasaAI platforms",
        },
        {
            "email": "user@ailabsafrica.com",
            "password": "User@123",
            "name": "Test User",
            "role": "reader",
            "bio": "Test user account for all KasaAI platforms",
        },
        {
            "email": "admin@freshmanna.com",
            "password": "Admin@123",
            "name": "FreshManna Admin",
            "role": "admin",
            "bio": "Platform administrator for FreshManna",
        },
        {
            "email": "pastor@freshmanna.com",
            "password": "Pastor@123",
            "name": "Test Pastor",
            "role": "pastor",
            "ministry_name": "Test Ministry",
            "bio": "Test pastor account for FreshManna",
        },
    ]

    print("=" * 60)
    print("Creating Default Users for DevotionalFlow (FreshManna)")
    print("=" * 60)
    print()

    for user_data in default_users:
        email = user_data["email"]

        # Check if user exists
        existing_user = await db.users.find_one({"email": email})

        if existing_user:
            print(f"✓ User already exists: {email}")
            continue

        # Create user document
        password_hash = get_password_hash(user_data["password"])

        user_doc = {
            "email": user_data["email"],
            "name": user_data["name"],
            "role": user_data["role"],
            "password_hash": password_hash,
            "bio": user_data.get("bio"),
            "avatar_url": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True,
            "is_suspended": False,
            "last_active": None,
        }

        # Add role-specific fields
        if user_data["role"] == "pastor":
            user_doc["ministry_name"] = user_data.get("ministry_name")
            user_doc["ministry_website"] = None
            user_doc["subscription_plan"] = "free"
            user_doc["subscription_expires_at"] = None
        elif user_data["role"] == "reader":
            user_doc["reading_streak"] = 0
            user_doc["reading_preferences"] = {
                "font_size": "medium",
                "theme": "light",
                "notification_time": "08:00",
            }
        elif user_data["role"] == "admin":
            # Admins can have both pastor and reader fields for testing
            user_doc["reading_streak"] = 0
            user_doc["reading_preferences"] = {
                "font_size": "medium",
                "theme": "light",
                "notification_time": "08:00",
            }

        # Insert user
        result = await db.users.insert_one(user_doc)
        print(f"✓ Created user: {email} (ID: {result.inserted_id})")
        print(f"  - Name: {user_data['name']}")
        print(f"  - Role: {user_data['role']}")
        print(f"  - Password: {user_data['password']}")
        print()

    print("=" * 60)
    print("Default Users Summary")
    print("=" * 60)
    print()
    print("Login Credentials:")
    print("-" * 60)
    for user_data in default_users:
        print(f"Email:    {user_data['email']}")
        print(f"Password: {user_data['password']}")
        print(f"Role:     {user_data['role']}")
        print()

    print("=" * 60)
    print("✓ Default users setup complete!")
    print("=" * 60)

    # Close connection
    client.close()


if __name__ == "__main__":
    asyncio.run(create_default_users())
