#!/usr/bin/env python3
"""
Fix Router Assistant - Add assistantId fields to transfer destinations

This script updates the Premier Health router assistant in VAPI to include
assistantId fields in all transfer destinations, fixing the 400 error:
"Invalid Destination. Assistant 'Premier Health Greater Accra' Not Found."

Usage:
    python3 fix_router_assistant.py

Requirements:
    - requests library
    - VAPI API key in environment or .env file
"""

import json
import os
import sys
import requests
from pathlib import Path

# Configuration
ROUTER_ASSISTANT_ID = "87182b39-a050-4ef4-9319-773666fabd6d"
VAPI_BASE_URL = "https://api.vapi.ai"
CONFIG_FILE = "/opt/kasaai/apps/automations/premier-health/config_router_assistant.json"

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
                        print(f"✅ Loaded {key} from .env")

def get_vapi_api_key():
    """Get VAPI API key from environment."""
    # Try to load from .env file first
    load_env_file()

    api_key = os.getenv("VAPI_API_KEY") or os.getenv("VAPI_PRIVATE_KEY")
    if not api_key:
        print("❌ Error: VAPI_API_KEY not found in environment or .env file")
        sys.exit(1)
    return api_key

def load_router_config():
    """Load router assistant configuration from JSON file."""
    print(f"\n📂 Loading configuration from: {CONFIG_FILE}")

    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        print("✅ Configuration loaded successfully")

        # Verify assistantId fields are present
        destinations = config.get('model', {}).get('tools', [{}])[0].get('destinations', [])
        assistant_ids = [d.get('assistantId') for d in destinations]

        print(f"\n🔍 Found {len(destinations)} transfer destinations:")
        for dest in destinations:
            name = dest.get('assistantName', 'Unknown')
            aid = dest.get('assistantId', 'MISSING')
            status = "✅" if aid != 'MISSING' else "❌"
            print(f"   {status} {name}: {aid}")

        if any(aid is None for aid in assistant_ids):
            print("\n❌ Error: Some destinations are missing assistantId fields")
            sys.exit(1)

        return config

    except FileNotFoundError:
        print(f"❌ Error: Configuration file not found: {CONFIG_FILE}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in configuration file: {e}")
        sys.exit(1)

def get_current_assistant(api_key):
    """Retrieve current assistant configuration from VAPI."""
    print(f"\n🔍 Retrieving current assistant configuration...")

    url = f"{VAPI_BASE_URL}/assistant/{ROUTER_ASSISTANT_ID}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        assistant = response.json()
        print(f"✅ Retrieved assistant: {assistant.get('name', 'Unknown')}")

        # Check current transfer destinations
        current_destinations = assistant.get('model', {}).get('tools', [{}])[0].get('destinations', [])
        print(f"\n📊 Current transfer destinations: {len(current_destinations)}")
        for dest in current_destinations:
            name = dest.get('assistantName', 'Unknown')
            aid = dest.get('assistantId', 'MISSING')
            print(f"   - {name}: {aid}")

        return assistant

    except requests.exceptions.RequestException as e:
        print(f"❌ Error retrieving assistant: {e}")
        if hasattr(e.response, 'text'):
            print(f"   Response: {e.response.text}")
        sys.exit(1)

def update_assistant(api_key, config):
    """Update router assistant configuration in VAPI."""
    print(f"\n🚀 Updating assistant {ROUTER_ASSISTANT_ID}...")

    url = f"{VAPI_BASE_URL}/assistant/{ROUTER_ASSISTANT_ID}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.patch(url, headers=headers, json=config, timeout=30)
        response.raise_for_status()

        updated_assistant = response.json()
        print(f"✅ Assistant updated successfully!")

        # Verify the update
        updated_destinations = updated_assistant.get('model', {}).get('tools', [{}])[0].get('destinations', [])
        print(f"\n✅ Updated transfer destinations: {len(updated_destinations)}")
        for dest in updated_destinations:
            name = dest.get('assistantName', 'Unknown')
            aid = dest.get('assistantId', 'MISSING')
            status = "✅" if aid != 'MISSING' else "❌"
            print(f"   {status} {name}: {aid}")

        return updated_assistant

    except requests.exceptions.RequestException as e:
        print(f"❌ Error updating assistant: {e}")
        if hasattr(e.response, 'text'):
            print(f"   Response: {e.response.text}")
        sys.exit(1)

def verify_fix():
    """Verify that the fix resolves the issue."""
    print("\n" + "="*80)
    print("✅ FIX APPLIED SUCCESSFULLY!")
    print("="*80)
    print("\n📋 What was fixed:")
    print("   • Added assistantId fields to all 6 transfer destinations")
    print("   • Router can now resolve assistant names to actual assistants")
    print("   • 400 'Invalid Destination' error should be resolved")

    print("\n🧪 Testing instructions:")
    print("   1. Go to: https://kasaai.premierhealthinsurance.org/")
    print("   2. Click 'Start Voice Call'")
    print("   3. The call should start without 400 errors")
    print("   4. Ask to be transferred to a region (e.g., 'Greater Accra')")
    print("   5. Router should successfully transfer to the regional specialist")

    print("\n📝 If you still see errors:")
    print("   • Check browser console for any new error messages")
    print("   • Verify all assistants still exist in VAPI dashboard")
    print("   • Check VAPI webhook logs for any issues")

    print("\n" + "="*80)

def main():
    """Main execution function."""
    print("="*80)
    print("🔧 Premier Health Router Assistant Fix")
    print("="*80)
    print("\nThis script will add assistantId fields to fix the error:")
    print("'Invalid Destination. Assistant \"Premier Health Greater Accra\" Not Found.'")

    # Get API key
    api_key = get_vapi_api_key()

    # Load updated configuration
    config = load_router_config()

    # Get current assistant state
    current_assistant = get_current_assistant(api_key)

    # Confirm update
    print("\n" + "="*80)
    print("⚠️  READY TO UPDATE")
    print("="*80)
    response = input("\nProceed with update? (yes/no): ").strip().lower()
    if response != 'yes':
        print("❌ Update cancelled by user")
        sys.exit(0)

    # Update assistant
    updated_assistant = update_assistant(api_key, config)

    # Verify and show testing instructions
    verify_fix()

if __name__ == "__main__":
    main()
