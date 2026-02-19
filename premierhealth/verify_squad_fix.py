#!/usr/bin/env python3
"""
Verify Squad Configuration Fix

This script retrieves the current squad configuration from VAPI
to verify that assistantDestinations were properly added.
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

def verify_squad_configuration(api_key):
    """Retrieve and verify squad configuration."""
    print("="*80)
    print("🔍 Verifying Squad Configuration")
    print("="*80)

    url = f"{VAPI_BASE_URL}/squad/{SQUAD_ID}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        squad = response.json()
        print(f"\n✅ Squad Retrieved: {squad.get('name', 'Unknown')}")
        print(f"   Squad ID: {SQUAD_ID}")
        print(f"   Total Members: {len(squad.get('members', []))}")

        # Find router member
        router_member = None
        for member in squad.get('members', []):
            if member.get('assistant') == ROUTER_ASSISTANT_ID:
                router_member = member
                break

        if not router_member:
            print(f"\n❌ ERROR: Router member not found in squad")
            print(f"   Expected assistant ID: {ROUTER_ASSISTANT_ID}")
            return False

        print(f"\n✅ Router Member Found:")
        print(f"   Assistant ID: {router_member.get('assistant')}")

        # Check assistantDestinations
        destinations = router_member.get('assistantDestinations', [])

        if not destinations:
            print(f"\n❌ ERROR: NO assistantDestinations found!")
            print(f"   The fix was not applied or was reverted")
            print(f"\n   Current router member config:")
            print(json.dumps(router_member, indent=2))
            return False

        print(f"\n✅ assistantDestinations Found: {len(destinations)} destinations")
        print("\n📋 Destination Mappings:")
        for i, dest in enumerate(destinations, 1):
            name = dest.get('assistantName', 'Unknown')
            aid = dest.get('assistantId', 'MISSING')
            status = "✅" if aid != 'MISSING' else "❌"
            print(f"   {i}. {status} {name}")
            print(f"      ID: {aid}")

        # Verify all 6 regional specialists are mapped
        expected_count = 6
        if len(destinations) == expected_count:
            print(f"\n✅ All {expected_count} regional specialists are mapped correctly!")
            return True
        else:
            print(f"\n⚠️  WARNING: Expected {expected_count} destinations, found {len(destinations)}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error retrieving squad: {e}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"   Response: {e.response.text}")
        return False

def main():
    api_key = get_vapi_api_key()
    success = verify_squad_configuration(api_key)

    print("\n" + "="*80)
    if success:
        print("✅ VERIFICATION PASSED")
        print("="*80)
        print("\nThe squad configuration is correct. If you're still seeing 400 errors,")
        print("the issue may be elsewhere. Please share:")
        print("  1. The exact error message from browser console")
        print("  2. Any response body from the failed request")
        print("  3. Network tab details of the POST to api.vapi.ai/call/web")
    else:
        print("❌ VERIFICATION FAILED")
        print("="*80)
        print("\nThe squad configuration is missing assistantDestinations.")
        print("Try running the fix script again:")
        print("  python3 /opt/kasaai/apps/premierhealth/fix_squad_configuration.py")
    print()

if __name__ == "__main__":
    main()
