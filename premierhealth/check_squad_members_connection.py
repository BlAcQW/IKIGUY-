#!/usr/bin/env python3
"""
Check Squad Members Connection - Verify how members are connected in the squad
"""

import json
import os
import sys
import requests
from pathlib import Path

SQUAD_ID = "d9c801a1-34df-4496-bb90-7ac9e3f9e44e"
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

def main():
    print("="*80)
    print("🔍 Squad Member Connections Analysis")
    print("="*80)

    api_key = get_vapi_api_key()
    squad = get_squad(api_key)

    if "error" in squad:
        print(f"❌ Error getting squad: {squad['error']}")
        sys.exit(1)

    # Save full squad for reference
    with open("/opt/kasaai/apps/premierhealth/squad_full_analysis.json", 'w') as f:
        json.dump(squad, f, indent=2)

    print(f"\n📊 Squad: {squad.get('name')}")
    print(f"   ID: {squad.get('id')}")

    # Check for all fields that might affect validation
    print(f"\n🔍 Squad-Level Configuration:")

    important_fields = [
        'members', 'name', 'id', 'orgId', 'createdAt', 'updatedAt'
    ]

    for field in squad.keys():
        if field not in important_fields:
            print(f"   • {field}: {squad[field]}")

    # Analyze members structure
    print(f"\n🔍 Members Analysis:")
    members = squad.get('members', [])
    print(f"   Total members: {len(members)}")

    for i, member in enumerate(members, 1):
        print(f"\n   Member {i}:")

        # Show all fields
        for key, value in member.items():
            if key == 'assistantDestinations':
                print(f"      {key}: [{len(value)} destinations]")
                for j, dest in enumerate(value, 1):
                    print(f"         [{j}] {dest.get('assistantName')}")
                    print(f"             Type: {dest.get('type')}")
                    print(f"             AssistantId: {dest.get('assistantId')}")

                    # Check for any unexpected fields
                    expected_dest_keys = {'type', 'assistantId', 'assistantName', 'message', 'description'}
                    actual_keys = set(dest.keys())
                    unexpected = actual_keys - expected_dest_keys
                    if unexpected:
                        print(f"             ⚠️  Unexpected fields: {unexpected}")
            else:
                print(f"      {key}: {value}")

        # Check for unexpected fields in member
        expected_member_keys = {'assistantId', 'assistant', 'assistantDestinations'}
        actual_member_keys = set(member.keys())
        unexpected_member_fields = actual_member_keys - expected_member_keys

        if unexpected_member_fields:
            print(f"      ⚠️  Unexpected member fields: {unexpected_member_fields}")

    # Check if members are properly linked
    print(f"\n🔍 Member Linkage Check:")

    # Get all member IDs
    member_ids = set()
    for member in members:
        aid = member.get('assistantId') or member.get('assistant')
        if aid:
            member_ids.add(aid)

    print(f"   Total unique assistant IDs in members: {len(member_ids)}")

    # Get all destination IDs
    dest_ids = set()
    for member in members:
        if 'assistantDestinations' in member:
            for dest in member['assistantDestinations']:
                dest_id = dest.get('assistantId')
                if dest_id:
                    dest_ids.add(dest_id)

    print(f"   Total unique assistant IDs in destinations: {len(dest_ids)}")

    # Check if destination assistants are in the squad
    print(f"\n🔍 Destination → Member Mapping:")
    missing_in_squad = dest_ids - member_ids

    if missing_in_squad:
        print(f"   ❌ ERROR: Destinations reference assistants NOT in squad members!")
        print(f"   Missing assistants: {len(missing_in_squad)}")
        for missing_id in missing_in_squad:
            print(f"      - {missing_id}")
        print(f"\n   This will cause 400 errors!")
    else:
        print(f"   ✅ All destination assistants are members of the squad")

    # Check the reverse - are all members reachable?
    print(f"\n🔍 Reachability Check:")

    # Find which member has destinations (should be router)
    router_member = None
    for member in members:
        if 'assistantDestinations' in member:
            router_member = member
            router_id = member.get('assistantId') or member.get('assistant')
            print(f"   Router assistant: {router_id}")
            print(f"   Can reach: {len(dest_ids)} assistants")
            break

    if not router_member:
        print(f"   ❌ NO ROUTER FOUND! No member has assistantDestinations")
    else:
        unreachable = member_ids - dest_ids - {router_id}
        if unreachable:
            print(f"   ⚠️  Unreachable assistants (not in destinations): {len(unreachable)}")
            for unreach_id in unreachable:
                print(f"      - {unreach_id}")
        else:
            print(f"   ✅ All non-router members are reachable via router")

    print("\n" + "="*80)
    print("💾 Full squad saved to: squad_full_analysis.json")
    print("="*80)

if __name__ == "__main__":
    main()
