#!/usr/bin/env python3
"""
Script to create 3 sample announcements for the landing page.

Usage:
    python3 create_sample_announcements.py [admin_token]
"""

import requests
import json
import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv("/opt/kasaai/.env")

API_BASE_URL = os.getenv("API_BASE_URL", "https://churchflow.ailabsafrica.com/api/v1")

def get_admin_token():
    """Get admin token from args or environment."""
    if len(sys.argv) > 1:
        return sys.argv[1]
    
    token = os.getenv("ADMIN_TOKEN")
    if token:
        return token
    
    print("Error: Admin token required")
    print("Usage: python3 create_sample_announcements.py [admin_token]")
    print("Or set ADMIN_TOKEN environment variable")
    sys.exit(1)

def create_sample_announcements(token):
    """Create 3 sample announcements."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Sample announcements
    announcements = [
        {
            "title": "Weekly Prayer Meeting",
            "description": "Join us every Wednesday evening for our powerful prayer meeting. Experience breakthrough, healing, and deliverance through corporate prayer and intercession.",
            "image_url": None,  # No image for this one
            "cta_text": "Learn More",
            "cta_link": "/events",
            "is_active": True,
            "is_hero": False,
            "display_order": 1,
            "start_date": datetime.now().isoformat(),
            "end_date": (datetime.now() + timedelta(days=30)).isoformat()
        },
        {
            "title": "Youth Revival Night",
            "description": "A special night designed for the youth! Come experience worship, testimonies, and powerful teaching that will ignite your passion for God and purpose.",
            "image_url": None,
            "cta_text": "Register Now",
            "cta_link": "/events",
            "is_active": True,
            "is_hero": False,
            "display_order": 2,
            "start_date": datetime.now().isoformat(),
            "end_date": (datetime.now() + timedelta(days=45)).isoformat()
        },
        {
            "title": "Monthly Communion Service",
            "description": "Join us for our monthly communion service as we remember the sacrifice of our Lord Jesus Christ. This is a time of reflection, worship, and receiving fresh grace.",
            "image_url": None,
            "cta_text": "Join Us",
            "cta_link": "/events",
            "is_active": True,
            "is_hero": False,
            "display_order": 3,
            "start_date": datetime.now().isoformat(),
            "end_date": (datetime.now() + timedelta(days=60)).isoformat()
        }
    ]
    
    created_count = 0
    for ann in announcements:
        try:
            response = requests.post(
                f"{API_BASE_URL}/announcements",
                headers=headers,
                json=ann
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                print(f"✅ Created: {result.get('title')}")
                created_count += 1
            else:
                print(f"❌ Failed to create '{ann['title']}': {response.status_code}")
                print(f"   Error: {response.text}")
        except Exception as e:
            print(f"❌ Error creating '{ann['title']}': {str(e)}")
    
    return created_count

def main():
    """Main function."""
    print("Creating 3 sample announcements...")
    print(f"API Base URL: {API_BASE_URL}\n")
    
    token = get_admin_token()
    
    created = create_sample_announcements(token)
    
    print(f"\n✅ Created {created} out of 3 sample announcements.")
    if created == 3:
        print("   All announcements are ready to display below the hero section on the landing page.")
    
    return 0 if created == 3 else 1

if __name__ == "__main__":
    sys.exit(main())

