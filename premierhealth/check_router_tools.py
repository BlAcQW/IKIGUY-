#!/usr/bin/env python3
"""
Check Router Assistant Tools Configuration
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

api_key = get_vapi_api_key()
router = get_router_assistant(api_key)

print("="*80)
print("ROUTER ASSISTANT FULL CONFIGURATION")
print("="*80)
print(json.dumps(router, indent=2))

print("\n" + "="*80)
print("ROUTER TRANSFER TOOL CONFIGURATION")
print("="*80)

tools = router.get('model', {}).get('tools', [])
print(f"\nTotal tools: {len(tools)}")

for i, tool in enumerate(tools, 1):
    print(f"\nTool {i}:")
    print(f"  Type: {tool.get('type')}")

    if tool.get('type') == 'transferCall':
        destinations = tool.get('destinations', [])
        print(f"  Destinations: {len(destinations)}")

        for j, dest in enumerate(destinations, 1):
            print(f"\n  Destination {j}:")
            print(f"    Type: {dest.get('type')}")
            print(f"    Assistant Name: {dest.get('assistantName', 'MISSING')}")
            print(f"    Assistant ID: {dest.get('assistantId', 'MISSING')}")
            print(f"    Message: {dest.get('message', 'N/A')[:50]}...")
            print(f"    Description: {dest.get('description', 'N/A')[:50]}...")
