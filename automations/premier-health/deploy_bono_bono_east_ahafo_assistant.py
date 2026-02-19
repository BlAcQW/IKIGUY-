#!/usr/bin/env python3
"""
Deploy Bono/Bono East/Ahafo Assistant Configuration to VAPI

This script deploys the updated serverUrl configuration for the
Bono/Bono East/Ahafo regional assistant.

Usage:
    python deploy_bono_bono_east_ahafo_assistant.py
"""

import json
import os
import httpx
from datetime import datetime

# VAPI Configuration
VAPI_API_KEY = os.getenv("VAPI_API_KEY", "42cf1e7c-2ef9-4bd7-ba30-52f2813605a2")
VAPI_BASE_URL = "https://api.vapi.ai"

# Configuration file and assistant ID
CONFIG_FILE = "/opt/kasaai/apps/automations/premier-health/config_bono_bono_east_and_ahafo_assistant.json"

# Note: We need to find the assistant ID for Bono/Bono East/Ahafo
# Options:
# 1. Create a new assistant (POST /assistant)
# 2. Get the ID from VAPI dashboard
# 3. List all assistants and find it (GET /assistant)
ASSISTANT_ID = None  # Will be determined by listing assistants


def list_assistants():
    """List all VAPI assistants to find the Bono/Bono East/Ahafo assistant."""
    try:
        headers = {
            "Authorization": f"Bearer {VAPI_API_KEY}",
            "Content-Type": "application/json"
        }

        with httpx.Client(timeout=30.0) as client:
            response = client.get(
                f"{VAPI_BASE_URL}/assistant",
                headers=headers
            )

            if response.status_code == 200:
                assistants = response.json()
                print(f"\n📋 Found {len(assistants)} assistants:\n")

                for assistant in assistants:
                    name = assistant.get('name', 'Unnamed')
                    assistant_id = assistant.get('id')
                    server_url = assistant.get('serverUrl', 'Not set')
                    print(f"  - {name}")
                    print(f"    ID: {assistant_id}")
                    print(f"    Server URL: {server_url}")

                    # Check if this is the Bono/Bono East/Ahafo assistant
                    if "bono" in name.lower() and ("east" in name.lower() or "ahafo" in name.lower()):
                        print(f"    ⭐ This is the Bono/Bono East/Ahafo assistant!")
                        return assistant_id
                    print()

                return None
            else:
                print(f"❌ Error listing assistants: {response.status_code}")
                print(f"Response: {response.text}")
                return None

    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return None


def deploy_assistant(assistant_id: str):
    """Deploy configuration to VAPI assistant."""
    try:
        # Load config
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)

        print(f"\n📤 Deploying configuration...")
        print(f"   Config file: {CONFIG_FILE}")
        print(f"   Assistant ID: {assistant_id}")
        print(f"   Server URL: {config.get('serverUrl')}")

        # Deploy to VAPI
        headers = {
            "Authorization": f"Bearer {VAPI_API_KEY}",
            "Content-Type": "application/json"
        }

        with httpx.Client(timeout=30.0) as client:
            response = client.patch(
                f"{VAPI_BASE_URL}/assistant/{assistant_id}",
                headers=headers,
                json=config
            )

            if response.status_code in [200, 201]:
                result = response.json()
                print(f"\n✅ Deployment successful!")
                print(f"   Assistant name: {result.get('name')}")
                print(f"   Updated at: {result.get('updatedAt')}")
                print(f"   Server URL: {result.get('serverUrl')}")
                print(f"   Voice ID: {result.get('voice', {}).get('voiceId')}")
                print(f"   Model: {result.get('model', {}).get('model')}")
                return True
            else:
                print(f"\n❌ Deployment failed: HTTP {response.status_code}")
                print(f"   Response: {response.text[:500]}")
                return False

    except Exception as e:
        print(f"\n❌ Exception during deployment: {str(e)}")
        return False


def main():
    """Main execution."""
    print("=" * 80)
    print("Deploy Bono/Bono East/Ahafo Assistant - Server URL Fix")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Config file: {CONFIG_FILE}")

    # Step 1: Find the assistant ID
    print("\n🔍 Step 1: Finding Bono/Bono East/Ahafo assistant ID...")
    assistant_id = list_assistants()

    if not assistant_id:
        print("\n⚠️  Could not find Bono/Bono East/Ahafo assistant!")
        print("\nOptions:")
        print("  1. Check the VAPI dashboard for the assistant ID")
        print("  2. Create a new assistant if it doesn't exist")
        print("  3. Verify the assistant name matches the search criteria")
        print("\n" + "=" * 80)
        return

    # Step 2: Deploy the configuration
    print(f"\n🚀 Step 2: Deploying configuration to assistant {assistant_id}...")
    success = deploy_assistant(assistant_id)

    # Summary
    print("\n" + "=" * 80)
    if success:
        print("✅ DEPLOYMENT SUCCESSFUL!")
        print("\nServer URL has been updated to:")
        print("  https://api.ailabsafrica.com/premier-health/vapi-webhook")
        print("\nThe knowledge base queries should now work correctly.")
    else:
        print("❌ DEPLOYMENT FAILED")
        print("\nPlease check the error messages above and try again.")
    print("=" * 80)


if __name__ == "__main__":
    main()
