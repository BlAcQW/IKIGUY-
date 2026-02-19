#!/usr/bin/env python3
"""
Verify Assistants Exist - Check if all assistants exist in VAPI and have correct names
"""

import json
import os
import sys
import requests
from pathlib import Path

VAPI_BASE_URL = "https://api.vapi.ai"

EXPECTED_ASSISTANTS = {
    "87182b39-a050-4ef4-9319-773666fabd6d": "Premier Health Router",
    "85e1cf7e-1711-4d01-9cad-c043b37707bd": "Premier Health Greater Accra",
    "529d7292-c050-4f5c-941d-5207a4e3e3be": "Premier Health Ashanti",
    "650340b7-76ee-46e9-ae34-268ebc217dba": "Premier Health Northern Regions",
    "caec99dc-3e51-43c2-a9cc-4b9b6bbef1dc": "Premier Health Western and Central",
    "0917ac57-8cac-44a1-9047-aead837af492": "Premier Health Eastern and Volta",
    "e39da43d-1190-419a-9739-d2c11bc8fe78": "Premier Health Bono Regions"
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

def check_assistant(api_key, assistant_id, expected_name):
    """Check if an assistant exists and get its actual name."""
    url = f"{VAPI_BASE_URL}/assistant/{assistant_id}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        assistant = response.json()
        actual_name = assistant.get('name', 'UNKNOWN')

        return {
            "exists": True,
            "actual_name": actual_name,
            "expected_name": expected_name,
            "name_match": actual_name == expected_name,
            "id": assistant.get('id'),
            "orgId": assistant.get('orgId')
        }
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return {
                "exists": False,
                "actual_name": None,
                "expected_name": expected_name,
                "name_match": False,
                "error": "404 Not Found"
            }
        else:
            return {
                "exists": False,
                "actual_name": None,
                "expected_name": expected_name,
                "name_match": False,
                "error": f"{e.response.status_code} - {e.response.text}"
            }

def main():
    print("="*80)
    print("🔍 Verifying All Assistants Exist in VAPI")
    print("="*80)

    api_key = get_vapi_api_key()

    all_good = True
    name_mismatches = []

    for assistant_id, expected_name in EXPECTED_ASSISTANTS.items():
        print(f"\n📋 Checking: {expected_name}")
        print(f"   ID: {assistant_id}")

        result = check_assistant(api_key, assistant_id, expected_name)

        if not result["exists"]:
            print(f"   ❌ DOES NOT EXIST!")
            if "error" in result:
                print(f"   Error: {result['error']}")
            all_good = False
        elif not result["name_match"]:
            print(f"   ⚠️  NAME MISMATCH!")
            print(f"   Expected: '{expected_name}'")
            print(f"   Actual:   '{result['actual_name']}'")
            name_mismatches.append({
                "id": assistant_id,
                "expected": expected_name,
                "actual": result['actual_name']
            })
            all_good = False
        else:
            print(f"   ✅ EXISTS with correct name")
            print(f"   Org ID: {result.get('orgId', 'N/A')}")

    print("\n" + "="*80)

    if all_good:
        print("✅ ALL ASSISTANTS EXIST WITH CORRECT NAMES")
        print("="*80)
        print("\nThe assistants are configured correctly.")
        print("The issue may be elsewhere. Let's check:")
        print("  1. Are you testing on the correct website?")
        print("  2. Have you cleared browser cache?")
        print("  3. Is the squad ID correct in index.html?")
    elif name_mismatches:
        print("⚠️  NAME MISMATCHES FOUND")
        print("="*80)
        print("\nThe squad is looking for assistants with these names:")
        for mismatch in name_mismatches:
            print(f"\n  Looking for: '{mismatch['expected']}'")
            print(f"  But found:   '{mismatch['actual']}'")
            print(f"  Assistant ID: {mismatch['id']}")

        print("\n📝 SOLUTION:")
        print("Update the squad's assistantDestinations to use the ACTUAL assistant names.")
        print("Run the fix script with corrected names.")
    else:
        print("❌ SOME ASSISTANTS DO NOT EXIST")
        print("="*80)
        print("\nSome assistant IDs are invalid or deleted.")
        print("You may need to recreate missing assistants.")

    print("\n" + "="*80)

if __name__ == "__main__":
    main()
