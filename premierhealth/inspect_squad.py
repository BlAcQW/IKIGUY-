#!/usr/bin/env python3
"""Inspect current squad configuration"""

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

def get_squad(api_key):
    url = f"{VAPI_BASE_URL}/squad/{SQUAD_ID}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()

load_env_file()
api_key = os.getenv("VAPI_API_KEY") or os.getenv("VAPI_PRIVATE_KEY")

squad = get_squad(api_key)

print("="*80)
print("FULL SQUAD CONFIGURATION")
print("="*80)
print(json.dumps(squad, indent=2))

print("\n" + "="*80)
print("SQUAD MEMBERS")
print("="*80)
for i, member in enumerate(squad.get('members', []), 1):
    print(f"\nMember {i}:")
    print(f"  Type: {type(member)}")
    print(f"  Keys: {list(member.keys())}")
    if isinstance(member, dict):
        if 'assistant' in member:
            print(f"  Assistant ID: {member.get('assistant')}")
        if 'assistantDestinations' in member:
            print(f"  Has assistantDestinations: YES ({len(member['assistantDestinations'])} destinations)")
        else:
            print(f"  Has assistantDestinations: NO")
    elif isinstance(member, str):
        print(f"  Assistant ID (string): {member}")
