#!/usr/bin/env python3
"""
Script to create sample announcements via the API.

Usage:
    python3 create_announcements.py
"""

import requests
import json
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:30030/api/v1"
# You'll need to set this to a valid admin token
ADMIN_TOKEN = "YOUR_ADMIN_TOKEN_HERE"

def create_announcement(title, description, cta_text, cta_link, start_date=None, end_date=None, display_order=0):
    """Create an announcement via the API."""
    url = f"{API_BASE_URL}/announcements"
    headers = {
        "Authorization": f"Bearer {ADMIN_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "title": title,
        "description": description,
        "cta_text": cta_text,
        "cta_link": cta_link,
        "is_active": True,
        "display_order": display_order
    }
    
    if start_date:
        payload["start_date"] = start_date.isoformat()
    if end_date:
        payload["end_date"] = end_date.isoformat()
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 201:
        print(f"✅ Created: {title}")
        return response.json()
    else:
        print(f"❌ Failed to create '{title}': {response.status_code} - {response.text}")
        return None

def main():
    """Create sample announcements."""
    print("Creating announcements...")
    print(f"API Base URL: {API_BASE_URL}\n")
    
    # 31st December Crossover Service
    create_announcement(
        title="31st December Crossover Service",
        description="Join us for a powerful night of worship, prayer, and prophecy as we cross over into the new year. This is a special service to give thanks for the past year and receive direction for the year ahead. Experience a night of breakthrough, celebration, and divine encounters.",
        cta_text="Register Now",
        cta_link="/events",
        start_date=datetime(2024, 12, 1),
        end_date=datetime(2024, 12, 31, 23, 59, 59),
        display_order=1
    )
    
    # Additional sample announcements
    create_announcement(
        title="New Year Prayer & Fasting",
        description="Start the new year with 21 days of prayer and fasting. Join us as we seek God's face and direction for the year ahead. Daily prayer meetings and guidance materials provided.",
        cta_text="Learn More",
        cta_link="/events",
        start_date=datetime(2024, 12, 15),
        end_date=datetime(2025, 1, 21, 23, 59, 59),
        display_order=2
    )
    
    create_announcement(
        title="Welcome New Members",
        description="If you're new to Action Chapel International, we'd love to connect with you! Join our new member orientation and get connected to small groups and ministries.",
        cta_text="Get Started",
        cta_link="/portal",
        display_order=3
    )
    
    print("\n✅ Announcement creation complete!")
    print("\nNote: To use this script, set ADMIN_TOKEN to a valid admin authentication token.")

if __name__ == "__main__":
    main()

