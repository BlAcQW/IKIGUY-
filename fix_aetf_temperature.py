#!/usr/bin/env python3
"""
Fix AETF assistant with optimal temperature for parameter extraction
Based on VAPI community recommendations: temperature 0-0.3
"""

import requests
import json

VAPI_API_KEY = "42cf1e7c-2ef9-4bd7-ba30-52f2813605a2"
ASSISTANT_ID = "e88d3ca9-4cc8-49be-bb42-36c9b8dae6ef"

def update_assistant_temperature():
    """Update assistant with optimal temperature for function calling"""
    url = f"https://api.vapi.ai/assistant/{ASSISTANT_ID}"
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }

    print("="*80)
    print("   Optimizing AETF Assistant for Parameter Extraction")
    print("="*80)
    print()

    # Get current assistant
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    current = response.json()

    print(f"✅ Assistant: {current['name']}")
    print(f"📊 Current model: {current['model'].get('model')}")
    print(f"🌡️  Current temperature: {current['model'].get('temperature', 'NOT SET')}")
    print()

    # Update with optimal settings
    payload = {
        "model": {
            "provider": "openai",
            "model": "gpt-4o",
            "temperature": 0.2,  # Optimal for parameter extraction per VAPI community
            "maxTokens": 250  # Reasonable limit for responses
        }
    }

    print("🔧 Updating assistant with optimal settings...")
    print("   - Temperature: 0.2 (recommended for parameter extraction)")
    print("   - Max tokens: 250 (keeps responses concise)")
    print()

    response = requests.patch(url, headers=headers, json=payload)
    response.raise_for_status()
    updated = response.json()

    print(f"✅ Updated temperature: {updated['model'].get('temperature')}")
    print(f"✅ Updated max tokens: {updated['model'].get('maxTokens')}")
    print()

    print("="*80)
    print("✅ Assistant optimized successfully!")
    print("="*80)
    print()
    print("Changes based on VAPI community recommendations:")
    print("  ✓ Temperature set to 0.2 (improves parameter extraction)")
    print("  ✓ Max tokens set to 250 (keeps responses focused)")
    print()
    print("This should significantly improve parameter extraction from conversation.")
    print()

if __name__ == "__main__":
    update_assistant_temperature()
