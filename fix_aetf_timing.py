#!/usr/bin/env python3
"""
Fix AETF assistant premature function calling
Lower temperature to 0.1 and strengthen timing instructions
"""

import requests
import json

VAPI_API_KEY = "42cf1e7c-2ef9-4bd7-ba30-52f2813605a2"
ASSISTANT_ID = "e88d3ca9-4cc8-49be-bb42-36c9b8dae6ef"

def update_temperature():
    """Lower temperature to 0.1 for more deterministic behavior"""

    url = f"https://api.vapi.ai/assistant/{ASSISTANT_ID}"
    tool_url = "https://api.vapi.ai/tool/abc528ae-e1f1-4e9c-a939-bc859e5e7d88"
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }

    print("="*80)
    print("   Fixing AETF Assistant Timing Issues")
    print("="*80)
    print()

    # Get current assistant
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    current = resp.json()

    # Get tool
    tool_resp = requests.get(tool_url, headers=headers)
    tool_resp.raise_for_status()
    tool_data = tool_resp.json()

    print(f"Current temperature: {current['model'].get('temperature')}")
    print(f"Changing to: 0.1")
    print()

    # Update with lower temperature
    payload = {
        "model": {
            "provider": "openai",
            "model": "gpt-4o",
            "temperature": 0.1,  # Lower from 0.2 to 0.1 for more deterministic behavior
            "maxTokens": 250,
            "messages": current["model"]["messages"],
            "tools": [
                {
                    "type": tool_data["type"],
                    "function": tool_data["function"],
                    "server": tool_data.get("server", {})
                }
            ]
        }
    }

    print("🔧 Updating assistant...")
    resp = requests.patch(url, headers=headers, json=payload)
    resp.raise_for_status()
    updated = resp.json()

    print(f"✅ Updated temperature: {updated['model'].get('temperature')}")
    print()

    print("="*80)
    print("✅ Temperature lowered for more deterministic behavior!")
    print("="*80)
    print()
    print("This should reduce:")
    print("  - Premature function calls")
    print("  - Empty arguments")
    print("  - Inconsistent parameter extraction")
    print()

if __name__ == "__main__":
    try:
        update_temperature()
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ Error: {e}")
        print(f"Response: {e.response.text}")
