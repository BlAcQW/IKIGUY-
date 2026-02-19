#!/usr/bin/env python3
"""
Fix Squad Configuration - Add assistantId to assistantDestinations

The squad has assistantDestinations but they're missing the assistantId field!
This script adds the assistantId to each destination.
"""

import json
import os
import sys
import requests
from pathlib import Path

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
    env_path = Path("/opt/kasaai/.env")
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if key == "VAPI_API_KEY" or key == "VAPI_PRIVATE_KEY":
                        os.environ[key] = value

def get_vapi_api_key():
    load_env_file()
    api_key = os.getenv("VAPI_API_KEY") or os.getenv("VAPI_PRIVATE_KEY")
    if not api_key:
        print("❌ Error: VAPI_API_KEY not found")
        sys.exit(1)
    return api_key

def get_current_squad(api_key):
    print(f"\n🔍 Retrieving current squad configuration...")

    url = f"{VAPI_BASE_URL}/squad/{SQUAD_ID}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    squad = response.json()
    print(f"✅ Retrieved squad: {squad.get('name')}")

    # Check current router member
    router_member = squad['members'][0]
    destinations = router_member.get('assistantDestinations', [])

    print(f"\n📊 Current Router Destinations: {len(destinations)}")
    for dest in destinations:
        name = dest.get('assistantName', 'Unknown')
        has_id = 'assistantId' in dest
        aid = dest.get('assistantId', 'MISSING')
        status = "✅" if has_id else "❌"
        print(f"   {status} {name}: {aid}")

    return squad

def fix_assistant_destinations():
    """Build assistantDestinations with ONLY type, assistantId, and assistantName.

    NOTE: Squad-level destinations should NOT have 'message' or 'description'.
    Those belong in the individual assistant's transfer tool configuration.
    """
    destinations = [
        {
            "type": "assistant",
            "assistantId": ASSISTANT_IDS["Greater Accra"],
            "assistantName": "Premier Health Greater Accra"
        },
        {
            "type": "assistant",
            "assistantId": ASSISTANT_IDS["Ashanti"],
            "assistantName": "Premier Health Ashanti"
        },
        {
            "type": "assistant",
            "assistantId": ASSISTANT_IDS["Northern Regions"],
            "assistantName": "Premier Health Northern Regions"
        },
        {
            "type": "assistant",
            "assistantId": ASSISTANT_IDS["Western and Central"],
            "assistantName": "Premier Health Western and Central"
        },
        {
            "type": "assistant",
            "assistantId": ASSISTANT_IDS["Eastern and Volta"],
            "assistantName": "Premier Health Eastern and Volta"
        },
        {
            "type": "assistant",
            "assistantId": ASSISTANT_IDS["Bono Regions"],
            "assistantName": "Premier Health Bono Regions"
        }
    ]
    return destinations

def update_squad(api_key, current_squad):
    print(f"\n🚀 Updating squad with assistantId in all destinations...")

    # Build new members array with corrected assistantDestinations
    assistant_destinations = fix_assistant_destinations()

    new_members = [
        {
            "assistantId": ROUTER_ASSISTANT_ID,
            "assistantDestinations": assistant_destinations
        }
    ]

    # Add other members (keep as-is)
    for member in current_squad['members'][1:]:
        new_members.append(member)

    update_payload = {
        "name": current_squad.get('name'),
        "members": new_members
    }

    print(f"\n✅ New Router Destinations (with assistantId):")
    for dest in assistant_destinations:
        print(f"   ✅ {dest['assistantName']}: {dest['assistantId']}")

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
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ Error updating squad: {e}")
        print(f"\nResponse Status: {e.response.status_code}")
        print(f"Response Body: {e.response.text}")
        print(f"\nPayload sent:")
        print(json.dumps(update_payload, indent=2))
        sys.exit(1)

def main():
    print("="*80)
    print("🔧 Fix Squad - Add assistantId to assistantDestinations")
    print("="*80)
    print("\nThe squad has destinations but they're missing assistantId fields!")
    print("This script will add the assistantId to each destination.")

    api_key = get_vapi_api_key()
    current_squad = get_current_squad(api_key)

    print("\n" + "="*80)
    print("⚠️  READY TO UPDATE")
    print("="*80)
    response = input("\nProceed with update? (yes/no): ").strip().lower()
    if response != 'yes':
        print("❌ Update cancelled")
        sys.exit(0)

    updated_squad = update_squad(api_key, current_squad)

    print("\n" + "="*80)
    print("✅ FIX APPLIED!")
    print("="*80)
    print("\n🧪 Test now:")
    print("   1. Go to: https://kasaai.premierhealthinsurance.org/")
    print("   2. Click 'Start Voice Call'")
    print("   3. Should start without 400 errors")
    print("\n" + "="*80)

if __name__ == "__main__":
    main()
