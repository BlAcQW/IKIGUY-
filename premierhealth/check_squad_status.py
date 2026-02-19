#!/usr/bin/env python3
"""
Check Current Squad Status - Verify if assistantDestinations are configured
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

def get_vapi_api_key():
    """Get VAPI API key from environment."""
    load_env_file()
    api_key = os.getenv("VAPI_API_KEY") or os.getenv("VAPI_PRIVATE_KEY")
    if not api_key:
        print("❌ Error: VAPI_API_KEY not found")
        sys.exit(1)
    return api_key

def get_squad_config(api_key):
    """Retrieve current squad configuration from VAPI."""
    url = f"{VAPI_BASE_URL}/squad/{SQUAD_ID}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error retrieving squad: {e}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"   Response: {e.response.text}")
        sys.exit(1)

def main():
    print("="*80)
    print("🔍 Premier Health Squad - Current Configuration Status")
    print("="*80)

    api_key = get_vapi_api_key()
    print(f"\n✅ API Key loaded: {api_key[:10]}...{api_key[-4:]}")

    squad = get_squad_config(api_key)

    # Save full config for debugging first
    output_file = "/opt/kasaai/apps/premierhealth/squad_config_current.json"
    with open(output_file, 'w') as f:
        json.dump(squad, f, indent=2)
    print(f"\n💾 Full config saved to: {output_file}")

    print(f"\n📊 Squad Information:")
    print(f"   Name: {squad.get('name', 'N/A')}")
    print(f"   ID: {squad.get('id', 'N/A')}")
    print(f"   Total Members: {len(squad.get('members', []))}")

    # Debug: Print member structure
    print(f"\n🔍 Debug - Member Structure:")
    for i, member in enumerate(squad.get('members', [])):
        print(f"   Member {i+1}:")
        print(f"      Keys: {list(member.keys())}")
        print(f"      Full: {json.dumps(member, indent=8)[:200]}...")

    # Find router member
    router_member = None
    for member in squad.get('members', []):
        if member.get('assistant') == ROUTER_ASSISTANT_ID:
            router_member = member
            break
        # Also check if it's nested differently
        if member.get('assistantId') == ROUTER_ASSISTANT_ID:
            router_member = member
            break

    if not router_member:
        print(f"\n❌ CRITICAL: Router assistant not found in squad!")
        print(f"   Looking for: {ROUTER_ASSISTANT_ID}")
        print(f"\n   Available members:")
        for member in squad.get('members', []):
            print(f"   - assistant: {member.get('assistant', 'N/A')}")
            print(f"   - assistantId: {member.get('assistantId', 'N/A')}")
            print(f"   - id: {member.get('id', 'N/A')}")
        sys.exit(1)

    print(f"\n✅ Router Member Found:")
    print(f"   Assistant ID: {router_member.get('assistant')}")

    # Check for assistantDestinations
    has_destinations = 'assistantDestinations' in router_member
    destinations = router_member.get('assistantDestinations', [])

    print(f"\n🎯 Assistant Destinations:")
    print(f"   Configured: {'YES ✅' if has_destinations else 'NO ❌'}")
    print(f"   Count: {len(destinations)}")

    if destinations:
        print(f"\n📋 Destination Details:")
        for i, dest in enumerate(destinations, 1):
            print(f"\n   [{i}] {dest.get('assistantName', 'N/A')}")
            print(f"       ID: {dest.get('assistantId', 'N/A')}")
            print(f"       Type: {dest.get('type', 'N/A')}")
            if 'message' in dest:
                print(f"       Message: {dest['message'][:60]}...")

    # Final verdict
    print("\n" + "="*80)
    if has_destinations and len(destinations) >= 6:
        print("✅ SQUAD CONFIGURATION IS CORRECT!")
        print("="*80)
        print("\nThe squad has assistantDestinations configured properly.")
        print(f"All {len(destinations)} regional assistants are mapped.")
        print("\n🧪 Next Steps:")
        print("   1. Test voice call at: https://kasaai.premierhealthinsurance.org/")
        print("   2. If still getting 400 error, the issue may be:")
        print("      - Browser cache (clear and reload)")
        print("      - Assistant names don't match actual names in VAPI")
        print("      - One or more assistant IDs are invalid")
        print("\n   Run verify_assistants_exist.py to check assistant names")
    else:
        print("❌ SQUAD CONFIGURATION IS INCOMPLETE!")
        print("="*80)
        print(f"\nExpected: 6+ assistant destinations")
        print(f"Found: {len(destinations)}")
        print("\n🔧 Fix Required:")
        print("   Run: python3 fix_squad_configuration.py")

    print("\n" + "="*80)

    # Save full config for debugging
    output_file = "/opt/kasaai/apps/premierhealth/squad_config_current.json"
    with open(output_file, 'w') as f:
        json.dump(squad, f, indent=2)
    print(f"\n💾 Full config saved to: {output_file}")

if __name__ == "__main__":
    main()
