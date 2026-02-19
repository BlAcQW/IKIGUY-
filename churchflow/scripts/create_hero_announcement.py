#!/usr/bin/env python3
"""
Script to create/update the 31st December Crossover Service announcement as a hero announcement.

Usage:
    python3 create_hero_announcement.py [admin_token]
"""

import requests
import json
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv("/opt/kasaai/.env")

API_BASE_URL = os.getenv("API_BASE_URL", "https://churchflow.ailabsafrica.com/api/v1")
HERO_IMAGE_URL = "https://actionchapel.net/wp-content/uploads/2025/07/WhatsApp-Image-2025-07-20-at-10.27.46.jpeg"

def get_admin_token():
    """Get admin token from args or environment."""
    if len(sys.argv) > 1:
        return sys.argv[1]
    
    token = os.getenv("ADMIN_TOKEN")
    if token:
        return token
    
    print("Error: Admin token required")
    print("Usage: python3 create_hero_announcement.py [admin_token]")
    print("Or set ADMIN_TOKEN environment variable")
    sys.exit(1)

def get_organization_id(token):
    """Get organization ID."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(f"{API_BASE_URL}/users/me", headers=headers)
    if response.status_code == 200:
        user_data = response.json()
        branch_id = user_data.get("branch_id")
        if branch_id:
            return branch_id
    
    # Fallback: try organizations endpoint
    response = requests.get(f"{API_BASE_URL}/organizations", headers=headers)
    if response.status_code == 200:
        orgs = response.json()
        if orgs and len(orgs) > 0:
            org_data = orgs[0].get("organization", orgs[0])
            # Note: JSON serialization might corrupt ObjectId, but we'll try
            return org_data.get("id")
    
    return None

def create_or_update_hero_announcement(token, org_id):
    """Create or update the 31st December Crossover announcement as hero."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # First, check if announcement already exists
    response = requests.get(f"{API_BASE_URL}/announcements", headers=headers, params={"page": 1, "page_size": 100})
    
    announcement_id = None
    if response.status_code == 200:
        data = response.json()
        announcements = data.get("announcements", data.get("items", []))
        
        # Find existing "31st December" or "Crossover" announcement
        for ann in announcements:
            title_lower = ann.get("title", "").lower()
            if "31st" in title_lower and "december" in title_lower and "crossover" in title_lower:
                announcement_id = ann.get("id") or ann.get("_id")
                print(f"Found existing announcement: {ann.get('title')} (ID: {announcement_id})")
                break
    
    announcement_data = {
        "title": "31st December Crossover Service",
        "description": "Join us for a powerful night of worship, prayer, and prophecy as we cross over into the new year. This is a special service to give thanks for the past year and receive direction for the year ahead. Experience a night of breakthrough, celebration, and divine encounters.",
        "image_url": HERO_IMAGE_URL,
        "cta_text": "Register Now",
        "cta_link": "/events",
        "is_active": True,
        "is_hero": True,
        "display_order": 0,
        "start_date": datetime(2024, 12, 1).isoformat(),
        "end_date": datetime(2024, 12, 31, 23, 59, 59).isoformat()
    }
    
    if announcement_id:
        # Update existing announcement
        print(f"Updating announcement {announcement_id}...")
        response = requests.put(
            f"{API_BASE_URL}/announcements/{announcement_id}",
            headers=headers,
            json=announcement_data
        )
        action = "updated"
    else:
        # Create new announcement
        print("Creating new hero announcement...")
        response = requests.post(
            f"{API_BASE_URL}/announcements",
            headers=headers,
            json=announcement_data
        )
        action = "created"
    
    if response.status_code in [200, 201]:
        result = response.json()
        print(f"✅ Successfully {action} hero announcement!")
        print(f"   Title: {result.get('title')}")
        print(f"   Hero: {result.get('is_hero')}")
        print(f"   Active: {result.get('is_active')}")
        return True
    else:
        print(f"❌ Failed to {action} announcement: {response.status_code}")
        print(f"   Error: {response.text}")
        return False

def main():
    """Main function."""
    print("Creating/updating 31st December Crossover Service as hero announcement...")
    print(f"API Base URL: {API_BASE_URL}\n")
    
    token = get_admin_token()
    
    org_id = get_organization_id(token)
    if not org_id:
        print("❌ Could not get organization ID")
        sys.exit(1)
    
    print(f"Organization ID: {org_id}\n")
    
    success = create_or_update_hero_announcement(token, org_id)
    
    if success:
        print("\n✅ Done! The announcement is now set as a hero announcement.")
        print("   It will appear on the left side of the hero section on the landing page.")
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())

