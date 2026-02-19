#!/usr/bin/env python3
"""
Remove transferCall Tool from Router Assistant

When using VAPI squads, the squad's assistantDestinations handles routing.
The individual assistant should NOT have its own transferCall tool.
"""

import json
import os
import sys
import requests
from pathlib import Path

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

def get_router_assistant(api_key):
    url = f"{VAPI_BASE_URL}/assistant/{ROUTER_ASSISTANT_ID}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()

def update_router_assistant(api_key, config):
    url = f"{VAPI_BASE_URL}/assistant/{ROUTER_ASSISTANT_ID}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.patch(url, headers=headers, json=config, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ Error updating assistant: {e}")
        print(f"Response Status: {e.response.status_code}")
        print(f"Response Body: {e.response.text}")
        sys.exit(1)

def main():
    print("="*80)
    print("🔧 Remove transferCall Tool from Router Assistant")
    print("="*80)
    print("\nWhen using squads, the squad's assistantDestinations handles routing.")
    print("The router assistant should NOT have its own transferCall tool.\n")

    api_key = get_vapi_api_key()

    print("📥 Retrieving current router configuration...")
    router = get_router_assistant(api_key)

    tools = router.get('model', {}).get('tools', [])
    print(f"   Current tools: {len(tools)}")

    if not tools:
        print("\n✅ Router already has no tools. No changes needed.")
        return

    for tool in tools:
        if tool.get('type') == 'transferCall':
            print(f"   Found transferCall tool with {len(tool.get('destinations', []))} destinations")

    print("\n⚠️  This will REMOVE the transferCall tool from the router assistant.")
    print("The squad's assistantDestinations will handle all transfers.")

    response = input("\nProceed? (yes/no): ").strip().lower()
    if response != 'yes':
        print("❌ Cancelled")
        sys.exit(0)

    # Update router to remove tools
    update_config = {
        "model": {
            "provider": router['model']['provider'],
            "model": router['model']['model'],
            "temperature": router['model'].get('temperature', 0.7),
            "messages": router['model']['messages'],
            "tools": []  # Remove all tools
        }
    }

    print("\n🚀 Updating router assistant...")
    updated = update_router_assistant(api_key, update_config)

    print("✅ Router assistant updated!")
    print(f"   Tools: {len(updated.get('model', {}).get('tools', []))}")

    print("\n" + "="*80)
    print("✅ DONE!")
    print("="*80)
    print("\n🧪 Test now:")
    print("   1. Go to: https://kasaai.premierhealthinsurance.org/")
    print("   2. Click 'Start Voice Call'")
    print("   3. Squad's assistantDestinations will handle routing")
    print("\n" + "="*80)

if __name__ == "__main__":
    main()
