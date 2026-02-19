#!/usr/bin/env python3
"""
Deploy All Premier Health VAPI Assistant Updates

Deploys updated configurations to VAPI for all regional assistants.

Usage:
    export VAPI_API_KEY=your-key
    python deploy_all_assistants.py
"""

import json
import os
import sys
import httpx
from datetime import datetime

# VAPI Configuration
VAPI_API_KEY = os.getenv("VAPI_API_KEY", "42cf1e7c-2ef9-4bd7-ba30-52f2813605a2")
VAPI_BASE_URL = "https://api.vapi.ai"

# Assistant mappings: config_file → assistant_id
ASSISTANTS = {
    "config_ashanti_assistant.json": "529d7292-c050-4f5c-941d-5207a4e3e3be",
    "config_greater_accra_assistant.json": "85e1cf7e-1711-4d01-9cad-c043b37707bd",
    "config_northern_regions_assistant.json": "ASSISTANT_ID_NEEDED",  # TODO: Add actual ID
    "config_bono_regions_assistant.json": "ASSISTANT_ID_NEEDED",  # TODO: Add actual ID
    "config_eastern_and_volta_assistant.json": "ASSISTANT_ID_NEEDED",  # TODO: Add actual ID
    "config_bono_bono_east_and_ahafo_assistant.json": "ASSISTANT_ID_NEEDED",  # TODO: Add actual ID
    "config_western_and_central_assistant.json": "ASSISTANT_ID_NEEDED",  # TODO: Add actual ID
}

BASE_PATH = "/opt/kasaai/apps/automations/premier-health"


def deploy_assistant(config_file: str, assistant_id: str) -> dict:
    """
    Deploy configuration to VAPI assistant.

    Args:
        config_file: Config filename
        assistant_id: VAPI assistant ID

    Returns:
        dict with deployment result
    """
    if assistant_id == "ASSISTANT_ID_NEEDED":
        return {
            'config': config_file,
            'success': False,
            'message': 'Assistant ID not configured'
        }

    config_path = os.path.join(BASE_PATH, config_file)

    try:
        # Load config
        with open(config_path, 'r') as f:
            config = json.load(f)

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
                return {
                    'config': config_file,
                    'assistant_id': assistant_id,
                    'success': True,
                    'updated_at': result.get('updatedAt'),
                    'voice_id': result.get('voice', {}).get('voiceId'),
                    'model': result.get('model', {}).get('model'),
                    'tool_count': len(result.get('model', {}).get('toolIds', []))
                }
            else:
                return {
                    'config': config_file,
                    'assistant_id': assistant_id,
                    'success': False,
                    'message': f"HTTP {response.status_code}: {response.text[:200]}"
                }

    except Exception as e:
        return {
            'config': config_file,
            'assistant_id': assistant_id,
            'success': False,
            'message': str(e)
        }


def main():
    """Main execution."""
    print("=" * 80)
    print("Premier Health - Deploy All Assistant Updates to VAPI")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Assistants to deploy: {len(ASSISTANTS)}")

    print("\n🚀 Deploying configurations...\n")

    results = []
    for config_file, assistant_id in ASSISTANTS.items():
        print(f"📤 {config_file}")
        print(f"   Assistant ID: {assistant_id}")

        result = deploy_assistant(config_file, assistant_id)
        results.append(result)

        if result['success']:
            print(f"   ✅ SUCCESS")
            print(f"      Updated: {result.get('updated_at')}")
            print(f"      Voice: {result.get('voice_id')}")
            print(f"      Model: {result.get('model')}")
            print(f"      Tools: {result.get('tool_count')}")
        else:
            print(f"   ❌ FAILED: {result.get('message')}")
        print()

    # Summary
    successful = sum(1 for r in results if r['success'])
    failed = sum(1 for r in results if not r['success'])

    print("=" * 80)
    if successful == len(ASSISTANTS):
        print("✅ ALL DEPLOYMENTS SUCCESSFUL!")
    else:
        print(f"⚠️  DEPLOYMENT COMPLETED WITH ISSUES")
    print("=" * 80)

    print(f"\n📊 Summary:")
    print(f"   Total: {len(ASSISTANTS)}")
    print(f"   Successful: {successful}")
    print(f"   Failed: {failed}")

    if failed > 0:
        print(f"\n❌ Failed deployments:")
        for r in results:
            if not r['success']:
                print(f"   - {r['config']}: {r.get('message', 'Unknown error')}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
