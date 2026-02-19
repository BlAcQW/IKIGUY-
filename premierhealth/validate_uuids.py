#!/usr/bin/env python3
"""
Validate all UUIDs in squad configuration
"""

import json
import os
import re
import sys
import requests
from pathlib import Path

SQUAD_ID = "d9c801a1-34df-4496-bb90-7ac9e3f9e44e"
VAPI_BASE_URL = "https://api.vapi.ai"

# UUID v4 regex pattern
UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)

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

def is_valid_uuid(uuid_string):
    """Check if a string is a valid UUID."""
    if not uuid_string or not isinstance(uuid_string, str):
        return False
    return bool(UUID_PATTERN.match(uuid_string))

def get_squad(api_key):
    url = f"{VAPI_BASE_URL}/squad/{SQUAD_ID}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def validate_squad_uuids(squad):
    """Recursively validate all UUIDs in squad configuration."""
    invalid_uuids = []

    def check_value(obj, path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_path = f"{path}.{key}" if path else key

                # Check if this looks like it should be a UUID
                if 'id' in key.lower() or key in ['assistant', 'assistantId']:
                    if isinstance(value, str):
                        if not is_valid_uuid(value):
                            invalid_uuids.append({
                                'path': new_path,
                                'key': key,
                                'value': value,
                                'reason': 'Invalid UUID format'
                            })

                # Recurse
                check_value(value, new_path)

        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                new_path = f"{path}[{i}]"
                check_value(item, new_path)

    check_value(squad)
    return invalid_uuids

def main():
    print("="*80)
    print("🔍 UUID Validation - Squad Configuration")
    print("="*80)

    api_key = get_vapi_api_key()
    squad = get_squad(api_key)

    if "error" in squad:
        print(f"❌ Error getting squad: {squad['error']}")
        sys.exit(1)

    print(f"\n📊 Squad: {squad.get('name')}")
    print(f"   ID: {squad.get('id')}")

    # Validate squad ID itself
    print(f"\n🔍 Validating Squad ID...")
    if is_valid_uuid(squad.get('id')):
        print(f"   ✅ Squad ID is valid UUID")
    else:
        print(f"   ❌ Squad ID is INVALID: {squad.get('id')}")

    # Check all members
    print(f"\n🔍 Validating Member Assistant IDs...")
    members = squad.get('members', [])

    for i, member in enumerate(members, 1):
        assistant_id = member.get('assistantId') or member.get('assistant')
        if assistant_id:
            if is_valid_uuid(assistant_id):
                print(f"   ✅ [{i}] {assistant_id}")
            else:
                print(f"   ❌ [{i}] INVALID: {assistant_id}")

    # Check assistantDestinations
    print(f"\n🔍 Validating Assistant Destinations...")
    for i, member in enumerate(members, 1):
        if 'assistantDestinations' in member:
            destinations = member.get('assistantDestinations', [])
            print(f"   Member {i} has {len(destinations)} destinations:")

            for j, dest in enumerate(destinations, 1):
                dest_id = dest.get('assistantId')
                dest_name = dest.get('assistantName', 'N/A')

                if dest_id:
                    if is_valid_uuid(dest_id):
                        print(f"      ✅ [{j}] {dest_name}: {dest_id}")
                    else:
                        print(f"      ❌ [{j}] {dest_name}: INVALID UUID: {dest_id}")
                else:
                    print(f"      ⚠️  [{j}] {dest_name}: No assistantId")

    # Deep scan for any invalid UUIDs
    print(f"\n🔍 Deep Scanning Entire Configuration...")
    invalid_uuids = validate_squad_uuids(squad)

    print("\n" + "="*80)

    if not invalid_uuids:
        print("✅ ALL UUIDs ARE VALID!")
        print("="*80)
        print("\nEvery UUID in the squad configuration is properly formatted.")
        print("\n🤔 The 400 error might be caused by:")
        print("   1. VAPI's API is still propagating the updated config")
        print("   2. The Web SDK is sending additional data not in the config")
        print("   3. Browser is using cached old config")
        print("   4. VAPI validation error unrelated to squad config")
    else:
        print("❌ INVALID UUIDs FOUND!")
        print("="*80)
        print(f"\nFound {len(invalid_uuids)} invalid UUID(s):")

        for item in invalid_uuids:
            print(f"\n   Path: {item['path']}")
            print(f"   Key: {item['key']}")
            print(f"   Value: {item['value']}")
            print(f"   Reason: {item['reason']}")

        print("\n🔧 These need to be fixed in the squad configuration!")

    print("\n" + "="*80)

if __name__ == "__main__":
    main()
