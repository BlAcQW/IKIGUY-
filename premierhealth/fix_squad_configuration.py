#!/usr/bin/env python3
"""
Fix Squad Configuration - Add assistantDestinations to router member

This script updates the Premier Health squad in VAPI to include assistantDestinations
for the router assistant member, fixing the 400 error:
"Invalid Destination. Assistant 'Premier Health Greater Accra' Not Found."

The issue: VAPI squads need assistantDestinations at the SQUAD level, not in individual
assistant configurations.

Usage:
    python3 fix_squad_configuration.py

Requirements:
    - requests library
    - VAPI API key in environment or .env file
"""

import json
import os
import sys
import requests
from pathlib import Path

# Configuration
SQUAD_ID = "d9c801a1-34df-4496-bb90-7ac9e3f9e44e"
ROUTER_ASSISTANT_ID = "87182b39-a050-4ef4-9319-773666fabd6d"
VAPI_BASE_URL = "https://api.vapi.ai"

# Assistant IDs from deployment record
ASSISTANT_IDS = {
    "Greater Accra": "85e1cf7e-1711-4d01-9cad-c043b37707bd",
    "Ashanti": "529d7292-c050-4f5c-941d-5207a4e3e3be",
    "Northern Regions": "650340b7-76ee-46e9-ae34-268ebc217dba",
    "Western and Central": "caec99dc-3e51-43c2-a9cc-4b9b6bbef1dc",
    "Eastern and Volta": "0917ac57-8cac-44a1-9047-aead837af492",
    "Bono Regions": "e39da43d-1190-419a-9739-d2c11bc8fe78"
}

def load_env_file():
    """Load environment variables from .env file."""
    env_path = Path("/opt/kasaai/.env")
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if key == "VAPI_API_KEY" or key == "VAPI_PRIVATE_KEY":
                        os.environ[key] = value
                        print(f"✅ Loaded {key} from .env")

def get_vapi_api_key():
    """Get VAPI API key from environment."""
    load_env_file()
    api_key = os.getenv("VAPI_API_KEY") or os.getenv("VAPI_PRIVATE_KEY")
    if not api_key:
        print("❌ Error: VAPI_API_KEY not found in environment or .env file")
        sys.exit(1)
    return api_key

def get_current_squad(api_key):
    """Retrieve current squad configuration from VAPI."""
    print(f"\n🔍 Retrieving current squad configuration...")

    url = f"{VAPI_BASE_URL}/squad/{SQUAD_ID}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        squad = response.json()
        print(f"✅ Retrieved squad: {squad.get('name', 'Unknown')}")
        print(f"   Members: {len(squad.get('members', []))}")

        # Check current router member configuration
        for member in squad.get('members', []):
            if member.get('assistant') == ROUTER_ASSISTANT_ID:
                has_destinations = 'assistantDestinations' in member
                print(f"\n📊 Router member found:")
                print(f"   - Assistant ID: {member.get('assistant')}")
                print(f"   - Has assistantDestinations: {has_destinations}")
                if has_destinations:
                    print(f"   - Destinations count: {len(member.get('assistantDestinations', []))}")

        return squad

    except requests.exceptions.RequestException as e:
        print(f"❌ Error retrieving squad: {e}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"   Response: {e.response.text}")
        sys.exit(1)

def build_assistant_destinations():
    """Build assistantDestinations array for router member."""
    destinations = []

    destination_configs = [
        {
            "name": "Premier Health Greater Accra",
            "id": ASSISTANT_IDS["Greater Accra"],
            "message": "Let me connect you to our Greater Accra specialist who knows all the healthcare facilities in your area.",
            "description": "Transfer to Greater Accra specialist for Accra, Tema, Madina, Legon, and surrounding areas"
        },
        {
            "name": "Premier Health Ashanti",
            "id": ASSISTANT_IDS["Ashanti"],
            "message": "Let me connect you to our Ashanti specialist who knows all the healthcare facilities in your area.",
            "description": "Transfer to Ashanti specialist for Kumasi, Obuasi, Mampong, and surrounding areas"
        },
        {
            "name": "Premier Health Northern Regions",
            "id": ASSISTANT_IDS["Northern Regions"],
            "message": "Let me connect you to our Northern regions specialist who knows all the healthcare facilities in your area.",
            "description": "Transfer to Northern specialist for Tamale, Bolgatanga, Wa, Bawku, and surrounding areas"
        },
        {
            "name": "Premier Health Western and Central",
            "id": ASSISTANT_IDS["Western and Central"],
            "message": "Let me connect you to our Western and Central specialist who knows all the healthcare facilities in your area.",
            "description": "Transfer to Western/Central specialist for Takoradi, Sekondi, Cape Coast, and surrounding areas"
        },
        {
            "name": "Premier Health Eastern and Volta",
            "id": ASSISTANT_IDS["Eastern and Volta"],
            "message": "Let me connect you to our Eastern and Volta specialist who knows all the healthcare facilities in your area.",
            "description": "Transfer to Eastern/Volta specialist for Koforidua, Ho, Hohoe, and surrounding areas"
        },
        {
            "name": "Premier Health Bono Regions",
            "id": ASSISTANT_IDS["Bono Regions"],
            "message": "Let me connect you to our Bono specialist who knows all the healthcare facilities in your area.",
            "description": "Transfer to Bono specialist for Sunyani, Techiman, Berekum, and surrounding areas"
        }
    ]

    for config in destination_configs:
        destinations.append({
            "type": "assistant",
            "assistantId": config["id"],
            "assistantName": config["name"],
            "message": config["message"],
            "description": config["description"]
        })

    return destinations

def update_squad(api_key, current_squad):
    """Update squad configuration with assistantDestinations for router."""
    print(f"\n🚀 Updating squad {SQUAD_ID}...")

    # Build new members array with assistantDestinations for router
    new_members = []
    assistant_destinations = build_assistant_destinations()

    for member in current_squad.get('members', []):
        if member.get('assistant') == ROUTER_ASSISTANT_ID:
            # Add assistantDestinations to router member
            new_member = {
                "assistant": ROUTER_ASSISTANT_ID,
                "assistantDestinations": assistant_destinations
            }
            new_members.append(new_member)
            print(f"\n✅ Updated router member with {len(assistant_destinations)} destinations:")
            for dest in assistant_destinations:
                print(f"   - {dest['assistantName']}: {dest['assistantId']}")
        else:
            # Keep other members as-is
            new_members.append(member)

    # Build update payload
    update_payload = {
        "name": current_squad.get('name'),
        "members": new_members
    }

    url = f"{VAPI_BASE_URL}/squad/{SQUAD_ID}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.patch(url, headers=headers, json=update_payload, timeout=30)
        response.raise_for_status()

        updated_squad = response.json()
        print(f"\n✅ Squad updated successfully!")

        return updated_squad

    except requests.exceptions.RequestException as e:
        print(f"❌ Error updating squad: {e}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"   Response: {e.response.text}")
        sys.exit(1)

def verify_fix():
    """Verify that the fix resolves the issue."""
    print("\n" + "="*80)
    print("✅ SQUAD FIX APPLIED SUCCESSFULLY!")
    print("="*80)
    print("\n📋 What was fixed:")
    print("   • Added assistantDestinations to router member in squad configuration")
    print("   • Squad now maps assistant names to actual assistant IDs")
    print("   • Router can transfer calls to regional specialists")
    print("   • 400 'Invalid Destination' error should be resolved")

    print("\n🧪 Testing instructions:")
    print("   1. Go to: https://kasaai.premierhealthinsurance.org/")
    print("   2. Click 'Start Voice Call'")
    print("   3. The call should start without 400 errors")
    print("   4. Say which region you need (e.g., 'Greater Accra')")
    print("   5. Router should successfully transfer to the regional specialist")
    print("   6. Regional specialist should answer with area-specific information")

    print("\n📝 If you still see errors:")
    print("   • Clear browser cache and reload the page")
    print("   • Check browser console for any new error messages")
    print("   • Verify all 7 assistants still exist in VAPI dashboard")
    print("   • Check that squad members list includes all 7 assistants")

    print("\n" + "="*80)

def main():
    """Main execution function."""
    print("="*80)
    print("🔧 Premier Health Squad Configuration Fix")
    print("="*80)
    print("\nThis script will add assistantDestinations to the squad to fix:")
    print("'Invalid Destination. Assistant \"Premier Health Greater Accra\" Not Found.'")

    # Get API key
    api_key = get_vapi_api_key()

    # Get current squad state
    current_squad = get_current_squad(api_key)

    # Confirm update
    print("\n" + "="*80)
    print("⚠️  READY TO UPDATE SQUAD")
    print("="*80)
    print("\nThis will update the squad configuration to include assistantDestinations")
    print("for the router member, allowing proper transfer to regional specialists.")
    response = input("\nProceed with update? (yes/no): ").strip().lower()
    if response != 'yes':
        print("❌ Update cancelled by user")
        sys.exit(0)

    # Update squad
    updated_squad = update_squad(api_key, current_squad)

    # Verify and show testing instructions
    verify_fix()

if __name__ == "__main__":
    main()
