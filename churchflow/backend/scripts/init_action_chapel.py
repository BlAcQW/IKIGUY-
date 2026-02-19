#!/usr/bin/env python3
"""
Initialize Action Chapel International as the default church organization.

This script sets up:
1. Action Chapel International organization
2. Headquarters branch in Accra
3. Impact Conference event
"""

import sys
from pathlib import Path

# Add the parent directory to sys.path to import from app
sys.path.insert(0, str(Path(__file__).parent.parent))

from pymongo import MongoClient
from datetime import datetime, timedelta
from bson import ObjectId
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def init_action_chapel():
    """Initialize Action Chapel International in the database."""

    # Connect to MongoDB
    mongodb_url = os.getenv(
        "MONGODB_URL",
        "mongodb://admin:aawwER4444%25@127.0.0.1:27017/churchflow?authSource=admin"
    )

    print("📡 Connecting to MongoDB...")
    client = MongoClient(mongodb_url)
    db = client.churchflow

    # Check if organization already exists
    existing_org = db.organizations.find_one({"slug": "action-chapel-international"})
    if existing_org:
        print("✅ Action Chapel International already exists")
        return existing_org

    print("🏛️  Creating Action Chapel International organization...")

    # Create organization
    organization = {
        "name": "Action Chapel International",
        "slug": "action-chapel-international",
        "description": "Action Chapel International (ACI) is a vibrant, multi-cultural church family with a passion for reaching the world with the Gospel of Jesus Christ. Founded by Archbishop Nicholas Duncan-Williams, ACI has grown to become one of Africa's leading churches with branches worldwide.",
        "logo_url": "https://actionchapel.net/wp-content/uploads/2024/01/aci-logo.png",
        "contact_info": {
            "phone": "+233302764505",
            "email": "info@actionchapel.net",
            "address": "Action Chapel International, P.O. Box CT 8644, Cantonments, Accra, Ghana",
            "website": "https://actionchapel.net"
        },
        "is_default": True,
        "settings": {
            "enable_bus_management": True,
            "enable_qr_checkin": True,
            "enable_conference_registration": True,
            "enable_notifications": True
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "metadata": {
            "founder": "Archbishop Nicholas Duncan-Williams",
            "established": 1979,
            "tagline": "Raising Champions"
        }
    }

    org_result = db.organizations.insert_one(organization)
    org_id = org_result.inserted_id
    print(f"✅ Organization created with ID: {org_id}")

    # Create headquarters branch
    print("🏢 Creating headquarters branch...")

    branch = {
        "organization_id": org_id,
        "name": "Action Chapel International - Headquarters",
        "slug": "action-chapel-hq-accra",
        "location": "Cantonments, Accra, Ghana",
        "contact_info": {
            "phone": "+233302764505",
            "email": "hq@actionchapel.net",
            "address": "P.O. Box CT 8644, Cantonments, Accra, Ghana"
        },
        "is_headquarters": True,
        "capacity": 5000,
        "pastor_name": "Archbishop Nicholas Duncan-Williams",
        "service_times": [
            "Sunday First Service: 7:00 AM",
            "Sunday Second Service: 9:00 AM",
            "Sunday Third Service: 11:00 AM",
            "Wednesday Service: 6:00 PM",
            "Friday Service: 6:00 PM"
        ],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "metadata": {
            "type": "headquarters",
            "facilities": ["Auditorium", "Parking", "Children's Church", "Bookstore"]
        }
    }

    branch_result = db.branches.insert_one(branch)
    branch_id = branch_result.inserted_id
    print(f"✅ Branch created with ID: {branch_id}")

    # Update organization with headquarters reference
    db.organizations.update_one(
        {"_id": org_id},
        {"$set": {"headquarters_branch_id": branch_id}}
    )

    # Create Impact Conference
    print("🎤 Creating Impact Conference...")

    # Calculate conference dates (upcoming conference)
    # Typically held in October/November
    today = datetime.utcnow()
    if today.month <= 10:
        # If before October, set for this year
        start_date = datetime(today.year, 10, 25)
    else:
        # If after October, set for next year
        start_date = datetime(today.year + 1, 10, 25)

    end_date = start_date + timedelta(days=3)  # 4-day conference

    conference = {
        "name": "IMPACT Conference",
        "slug": "impact-conference",
        "description": "Join us for IMPACT, the annual conference of Action Chapel International. Experience powerful worship, dynamic preaching, and life-transforming encounters with God. This conference brings together thousands of believers from across the world for four days of intense spiritual awakening and empowerment.",
        "organization_id": org_id,
        "branch_id": branch_id,
        "start_date": start_date,
        "end_date": end_date,
        "venue": "Action Chapel International Headquarters, Accra",
        "expected_attendance": 10000,
        "registration_open": True,
        "registration_deadline": start_date - timedelta(days=7),
        "theme": "Raising Champions",
        "speakers": [
            {
                "name": "Archbishop Nicholas Duncan-Williams",
                "title": "Presiding Archbishop",
                "bio": "Founder and Presiding Archbishop of Action Chapel International",
                "image_url": None
            }
        ],
        "schedule": [
            {
                "day": 1,
                "date": start_date,
                "sessions": [
                    {
                        "time": "9:00 AM - 12:00 PM",
                        "title": "Opening Session",
                        "speaker": "Archbishop Nicholas Duncan-Williams"
                    },
                    {
                        "time": "6:00 PM - 9:00 PM",
                        "title": "Evening Session",
                        "speaker": "Special Guest"
                    }
                ]
            }
        ],
        "website_url": "https://actionchapel.net/impact/",
        "registration_link": "https://actionchapel.net/impact-registration/",
        "contact_info": {
            "email": "impact@actionchapel.net",
            "phone": "+233302764505"
        },
        "settings": {
            "enable_online_registration": True,
            "enable_bus_transport": True,
            "enable_accommodation_booking": False,
            "enable_live_stream": True
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "metadata": {
            "type": "annual_conference",
            "recurring": True,
            "featured": True,
            "highlight_on_home": True
        }
    }

    conf_result = db.conferences.insert_one(conference)
    conf_id = conf_result.inserted_id
    print(f"✅ Conference created with ID: {conf_id}")

    print("\n🎉 Action Chapel International setup complete!")
    print(f"\n📊 Summary:")
    print(f"   - Organization: {organization['name']}")
    print(f"   - Branch: {branch['name']}")
    print(f"   - Conference: {conference['name']}")
    print(f"   - Conference Dates: {start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}")
    print(f"   - Website: {organization['contact_info']['website']}")
    print(f"   - Impact Conference: https://actionchapel.net/impact/")

    return {
        "organization_id": str(org_id),
        "branch_id": str(branch_id),
        "conference_id": str(conf_id)
    }


if __name__ == "__main__":
    try:
        result = init_action_chapel()
        print("\n✅ Initialization successful!")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
