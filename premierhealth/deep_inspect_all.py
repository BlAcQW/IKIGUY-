#!/usr/bin/env python3
"""
Deep Inspect All - Check squad and all assistant configurations for issues
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

def get_assistant(api_key, assistant_id):
    url = f"{VAPI_BASE_URL}/assistant/{assistant_id}"
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
    print("🔍 Premier Health Squad - Deep Inspection")
    print("="*80)

    api_key = get_vapi_api_key()
    squad = get_squad(api_key)

    if "error" in squad:
        print(f"❌ Error getting squad: {squad['error']}")
        sys.exit(1)

    print(f"\n📊 Squad: {squad.get('name')}")
    print(f"   ID: {squad.get('id')}")
    print(f"   Members: {len(squad.get('members', []))}")

    # Get all member assistant IDs
    member_ids = []
    for member in squad.get('members', []):
        assistant_id = member.get('assistantId') or member.get('assistant')
        if assistant_id:
            member_ids.append(assistant_id)

    print(f"\n🔍 Inspecting all {len(member_ids)} assistants...")

    all_good = True
    issues_found = []

    for i, assistant_id in enumerate(member_ids, 1):
        assistant = get_assistant(api_key, assistant_id)

        if "error" in assistant:
            print(f"\n❌ [{i}] ERROR: {assistant['error']}")
            all_good = False
            continue

        name = assistant.get('name', 'N/A')
        server_url = assistant.get('serverUrl', assistant.get('server', {}).get('url', 'N/A'))

        print(f"\n✅ [{i}] {name}")
        print(f"      ID: {assistant_id}")
        print(f"      serverUrl: {server_url}")

        # Check for issues
        if server_url and server_url != 'N/A':
            if 'ailabsafrica.com' not in server_url:
                print(f"      ⚠️  WARNING: server URL doesn't contain ailabsafrica.com")
                issues_found.append(f"{name}: server URL looks suspicious")
                all_good = False
            elif 'premier-health' not in server_url:
                print(f"      ⚠️  WARNING: server URL doesn't contain 'premier-health'")
                issues_found.append(f"{name}: server URL may be incorrect")
                all_good = False
        else:
            print(f"      ⚠️  WARNING: No serverUrl configured")
            issues_found.append(f"{name}: Missing serverUrl")
            all_good = False

        # Check for transfer tools (should NOT be in regional assistants)
        tools = assistant.get('model', {}).get('tools', [])
        has_transfer = any(t.get('type') == 'transferCall' for t in tools)

        if has_transfer and i > 1:  # Skip router (first member)
            print(f"      ⚠️  WARNING: Regional assistant has transferCall tool")
            issues_found.append(f"{name}: Has transferCall tool (should only be in router)")

    print("\n" + "="*80)

    if all_good and not issues_found:
        print("✅ ALL ASSISTANTS CONFIGURED CORRECTLY!")
        print("="*80)
        print("\nSquad and all assistants are properly configured.")
        print("\n🤔 If you're still getting 400 errors:")
        print("   1. Clear browser cache completely")
        print("   2. Try in incognito/private mode")
        print("   3. Check if the error message changed")
        print("   4. Wait 5-10 minutes (VAPI API might be caching)")
        print("   5. Check VAPI dashboard for any service issues")
    else:
        print("⚠️  CONFIGURATION ISSUES FOUND:")
        print("="*80)
        for issue in issues_found:
            print(f"   - {issue}")

        print("\n🔧 Recommended actions:")
        print("   1. Review assistant configurations in VAPI dashboard")
        print("   2. Ensure all serverUrl values are correct")
        print("   3. Remove transferCall tools from regional assistants")

    print("\n" + "="*80)

if __name__ == "__main__":
    main()
