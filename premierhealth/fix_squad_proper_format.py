#!/usr/bin/env python3
"""
Fix Squad - Use Proper VAPI Format for assistantDestinations

According to VAPI docs, assistantDestinations should have:
- type: "assistant"
- assistantName: "Name"  (references squad member by name)
- message: "Transfer message"
- description: "Transfer description"

NO assistantId in assistantDestinations! VAPI resolves names to squad members.
"""

import json
import os
import sys
import requests
from pathlib import Path

SQUAD_ID = "d9c801a1-34df-4496-bb90-7ac9e3f9e44e"
ROUTER_ASSISTANT_ID = "87182b39-a050-4ef4-9319-773666fabd6d"
VAPI_BASE_URL = "https://api.vapi.ai"

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
    url = f"{VAPI_BASE_URL}/squad/{SQUAD_ID}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()

def build_proper_assistant_destinations():
    """Build assistantDestinations with VAPI's proper format.

    Format: type, assistantName, message, description
    NO assistantId - VAPI resolves names to squad members
    """
    return [
        {
            "type": "assistant",
            "assistantName": "Premier Health Greater Accra",
            "message": "Let me connect you to our Greater Accra specialist who knows all the healthcare facilities in your area.",
            "description": "Transfer to Greater Accra specialist for Accra, Tema, Madina, Legon, and surrounding areas"
        },
        {
            "type": "assistant",
            "assistantName": "Premier Health Ashanti",
            "message": "Let me connect you to our Ashanti specialist who knows all the healthcare facilities in your area.",
            "description": "Transfer to Ashanti specialist for Kumasi, Obuasi, Mampong, and surrounding areas"
        },
        {
            "type": "assistant",
            "assistantName": "Premier Health Northern Regions",
            "message": "Let me connect you to our Northern regions specialist who knows all the healthcare facilities in your area.",
            "description": "Transfer to Northern specialist for Tamale, Bolgatanga, Wa, Bawku, and surrounding areas"
        },
        {
            "type": "assistant",
            "assistantName": "Premier Health Western and Central",
            "message": "Let me connect you to our Western and Central specialist who knows all the healthcare facilities in your area.",
            "description": "Transfer to Western/Central specialist for Takoradi, Sekondi, Cape Coast, and surrounding areas"
        },
        {
            "type": "assistant",
            "assistantName": "Premier Health Eastern and Volta",
            "message": "Let me connect you to our Eastern and Volta specialist who knows all the healthcare facilities in your area.",
            "description": "Transfer to Eastern/Volta specialist for Koforidua, Ho, Hohoe, and surrounding areas"
        },
        {
            "type": "assistant",
            "assistantName": "Premier Health Bono Regions",
            "message": "Let me connect you to our Bono specialist who knows all the healthcare facilities in your area.",
            "description": "Transfer to Bono specialist for Sunyani, Techiman, Berekum, and surrounding areas"
        }
    ]

def update_squad(api_key, current_squad):
    print("\n🚀 Updating squad with proper VAPI format...")

    destinations = build_proper_assistant_destinations()

    # Build members array
    new_members = [
        {
            "assistantId": ROUTER_ASSISTANT_ID,
            "assistantDestinations": destinations
        }
    ]

    # Add other squad members (regional assistants)
    for member in current_squad['members'][1:]:
        new_members.append(member)

    update_payload = {
        "name": current_squad['name'],
        "members": new_members
    }

    print("\n✅ New assistantDestinations format (per VAPI docs):")
    for dest in destinations:
        print(f"   - {dest['assistantName']}")
        print(f"     Fields: type={dest['type']}, message=YES, description=YES")
        print(f"     NO assistantId (VAPI resolves from squad members)")

    url = f"{VAPI_BASE_URL}/squad/{SQUAD_ID}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.patch(url, headers=headers, json=update_payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ Error: {e}")
        print(f"Status: {e.response.status_code}")
        print(f"Response: {e.response.text}")
        print(f"\nPayload sent:")
        print(json.dumps(update_payload, indent=2))
        sys.exit(1)

def main():
    print("="*80)
    print("🔧 Fix Squad - Use Proper VAPI Format")
    print("="*80)
    print("\nVAPI Docs say assistantDestinations should have:")
    print("  ✅ type, assistantName, message, description")
    print("  ❌ NO assistantId (VAPI resolves from squad members)\n")

    api_key = get_vapi_api_key()
    current_squad = get_current_squad(api_key)

    print(f"Squad: {current_squad['name']}")
    print(f"Members: {len(current_squad['members'])}")

    response = input("\nProceed? (yes/no): ").strip().lower()
    if response != 'yes':
        print("❌ Cancelled")
        sys.exit(0)

    updated = update_squad(api_key, current_squad)

    print("\n✅ Squad updated successfully!")
    print("\n" + "="*80)
    print("✅ DONE!")
    print("="*80)
    print("\n🧪 Test now:")
    print("   https://kasaai.premierhealthinsurance.org/")
    print("\n" + "="*80)

if __name__ == "__main__":
    main()
