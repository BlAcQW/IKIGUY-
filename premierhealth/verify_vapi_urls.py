#!/usr/bin/env python3
"""
VAPI Configuration Verification Script
Checks if all Premier Health assistants have correct webhook URLs
"""

import os
import requests
import json
from typing import Dict, List

# Load VAPI API key from environment
VAPI_API_KEY = os.getenv('VAPI_API_KEY', '42cf1e7c-2ef9-4bd7-ba30-52f2813605a2')
VAPI_BASE_URL = "https://api.vapi.ai"

# Expected configuration
CORRECT_WEBHOOK_URL = "https://api.ailabsafrica.com/premier-health/vapi-webhook"

# All 7 assistants in the squad
ASSISTANTS = [
    {
        "id": "87182b39-a050-4ef4-9319-773666fabd6d",
        "name": "Router Assistant",
        "expected_region": None
    },
    {
        "id": "85e1cf7e-1711-4d01-9cad-c043b37707bd",
        "name": "Greater Accra Specialist",
        "expected_region": "GREATER ACCRA"
    },
    {
        "id": "529d7292-c050-4f5c-941d-5207a4e3e3be",
        "name": "Ashanti Specialist",
        "expected_region": "ASHANTI"
    },
    {
        "id": "650340b7-76ee-46e9-ae34-268ebc217dba",
        "name": "Northern Regions Specialist",
        "expected_region": "NORTHERN"
    },
    {
        "id": "caec99dc-3e51-43c2-a9cc-4b9b6bbef1dc",
        "name": "Western and Central Specialist",
        "expected_region": "WESTERN"
    },
    {
        "id": "0917ac57-8cac-44a1-9047-aead837af492",
        "name": "Eastern and Volta Specialist",
        "expected_region": "EASTERN"
    },
    {
        "id": "e39da43d-1190-419a-9739-d2c11bc8fe78",
        "name": "Bono Regions Specialist",
        "expected_region": "BONO"
    }
]


def get_assistant_config(assistant_id: str) -> Dict:
    """Get assistant configuration from VAPI API"""
    url = f"{VAPI_BASE_URL}/assistant/{assistant_id}"
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def check_assistant(assistant: Dict) -> Dict:
    """Check if assistant has correct configuration"""
    try:
        config = get_assistant_config(assistant['id'])

        # Extract URLs
        server_url = config.get('server', {}).get('url', 'NOT SET')
        server_url_alt = config.get('serverUrl', 'NOT SET')

        # Check if correct
        server_url_correct = server_url == CORRECT_WEBHOOK_URL
        server_url_alt_correct = server_url_alt == CORRECT_WEBHOOK_URL

        # Check tool configuration
        tools = config.get('model', {}).get('tools', [])
        has_kb_tool = False
        region_param = None

        for tool in tools:
            if tool.get('type') == 'function':
                func = tool.get('function', {})
                if func.get('name') == 'query_premier_health_knowledge_base':
                    has_kb_tool = True
                    params = func.get('parameters', {})
                    props = params.get('properties', {})
                    region_prop = props.get('region', {})
                    region_param = region_prop.get('default')

        return {
            "assistant_id": assistant['id'],
            "name": assistant['name'],
            "server_url": server_url,
            "server_url_correct": server_url_correct,
            "serverUrl": server_url_alt,
            "serverUrl_correct": server_url_alt_correct,
            "has_kb_tool": has_kb_tool,
            "region_parameter": region_param,
            "expected_region": assistant.get('expected_region'),
            "region_correct": region_param == assistant.get('expected_region') if assistant.get('expected_region') else True,
            "status": "✅ CORRECT" if (server_url_correct and has_kb_tool) else "❌ NEEDS FIX"
        }

    except Exception as e:
        return {
            "assistant_id": assistant['id'],
            "name": assistant['name'],
            "error": str(e),
            "status": "❌ ERROR"
        }


def main():
    """Main verification function"""
    print("=" * 80)
    print("VAPI CONFIGURATION VERIFICATION")
    print("Premier Health Navigator Squad")
    print("=" * 80)
    print()

    results = []
    all_correct = True

    for assistant in ASSISTANTS:
        print(f"Checking: {assistant['name']} ({assistant['id'][:8]}...)")
        result = check_assistant(assistant)
        results.append(result)

        if result['status'] != "✅ CORRECT":
            all_correct = False

        print(f"  Status: {result['status']}")
        if 'error' not in result:
            print(f"  server.url: {result['server_url']}")
            print(f"    ✅ Correct" if result['server_url_correct'] else f"    ❌ WRONG (should be: {CORRECT_WEBHOOK_URL})")
            print(f"  serverUrl: {result['serverUrl']}")
            print(f"    ✅ Correct" if result['serverUrl_correct'] else f"    ❌ WRONG")
            print(f"  Knowledge Base Tool: {'✅ Present' if result['has_kb_tool'] else '❌ Missing'}")
            if result['expected_region']:
                print(f"  Region Parameter: {result['region_parameter']} (expected: {result['expected_region']})")
                print(f"    {'✅ Correct' if result['region_correct'] else '❌ Wrong'}")
        else:
            print(f"  Error: {result['error']}")
        print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    correct_count = sum(1 for r in results if r['status'] == "✅ CORRECT")
    total_count = len(results)

    print(f"Total Assistants: {total_count}")
    print(f"Correctly Configured: {correct_count}")
    print(f"Need Fixes: {total_count - correct_count}")
    print()

    if all_correct:
        print("🎉 ALL ASSISTANTS CORRECTLY CONFIGURED!")
        print()
        print("Next steps:")
        print("1. Test with a phone call: +233 24 242 6051")
        print("2. Monitor backend logs: sudo journalctl -u kasaai-core-backend -f")
        print("3. Verify no 404 errors in logs")
    else:
        print("⚠️  SOME ASSISTANTS NEED CONFIGURATION UPDATES")
        print()
        print("To fix:")
        print("1. Login to https://vapi.ai")
        print("2. Update the 'server.url' field for each assistant marked ❌")
        print("3. Set to:", CORRECT_WEBHOOK_URL)
        print("4. Run this script again to verify")
        print()
        print("See VAPI_SERVER_URL_FIX.md for detailed instructions")

    print("=" * 80)

    # Save results to JSON
    with open('/tmp/vapi_verification_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print()
    print("Detailed results saved to: /tmp/vapi_verification_results.json")

    return 0 if all_correct else 1


if __name__ == "__main__":
    exit(main())
