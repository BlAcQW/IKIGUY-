#!/usr/bin/env python3
"""
Check specific assistant configuration for issues
"""

import json
import os
import sys
import requests
from pathlib import Path

ASSISTANT_ID = "85e1cf7e-1711-4d01-9cad-c043b37707bd"  # Greater Accra
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

def get_assistant(api_key):
    url = f"{VAPI_BASE_URL}/assistant/{ASSISTANT_ID}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

def main():
    print("="*80)
    print("🔍 Greater Accra Assistant Configuration Check")
    print("="*80)

    api_key = get_vapi_api_key()
    assistant = get_assistant(api_key)

    print(f"\n📊 Assistant: {assistant.get('name')}")
    print(f"   ID: {assistant.get('id')}")

    # Check critical fields
    critical_fields = {
        'serverUrl': assistant.get('serverUrl') or assistant.get('server', {}).get('url'),
        'voice': assistant.get('voice', {}).get('provider'),
        'voiceId': assistant.get('voice', {}).get('voiceId'),
        'model': assistant.get('model', {}).get('provider'),
        'firstMessage': assistant.get('firstMessage'),
        'transcriber': assistant.get('transcriber', {}).get('provider')
    }

    print(f"\n🔍 Critical Configuration:")
    issues = []

    for field, value in critical_fields.items():
        status = "✅" if value else "❌"
        print(f"   {status} {field}: {value or 'MISSING'}")
        if not value:
            issues.append(f"Missing {field}")

    # Check tools
    tools = assistant.get('model', {}).get('tools', [])
    print(f"\n🔧 Tools: {len(tools)}")
    for i, tool in enumerate(tools, 1):
        tool_type = tool.get('type')
        print(f"   [{i}] {tool_type}")

        if tool_type == 'transferCall':
            print(f"      ⚠️  WARNING: Regional assistant shouldn't have transferCall")
            issues.append("Has transferCall tool (should only be in router)")

    # Check server URL specifically
    server_url = assistant.get('serverUrl') or assistant.get('server', {}).get('url')
    if server_url:
        print(f"\n🌐 Testing Server URL:")
        print(f"   URL: {server_url}")

        try:
            test_response = requests.head(server_url, timeout=5)
            print(f"   Status: {test_response.status_code}")
            if test_response.status_code in [200, 405]:  # 405 is OK (POST only)
                print(f"   ✅ Endpoint is reachable")
            else:
                print(f"   ❌ Unexpected status code")
                issues.append(f"Server URL returns {test_response.status_code}")
        except Exception as e:
            print(f"   ❌ Cannot reach endpoint: {e}")
            issues.append(f"Server URL unreachable: {e}")

    print("\n" + "="*80)

    if issues:
        print("⚠️  ISSUES FOUND:")
        print("="*80)
        for issue in issues:
            print(f"   • {issue}")

        print("\n💡 Possible causes of 'Meeting has ended' error:")
        print("   1. Server URL is unreachable from VAPI's servers")
        print("   2. Webhook is timing out (>10 seconds)")
        print("   3. Webhook is returning an error")
        print("   4. Missing required configuration fields")
    else:
        print("✅ CONFIGURATION LOOKS GOOD")
        print("="*80)
        print("\nIf still getting 'Meeting has ended':")
        print("   1. Check backend logs for webhook errors")
        print("   2. VAPI might be experiencing issues")
        print("   3. Try using a different assistant")

    # Save full config
    with open("/opt/kasaai/apps/premierhealth/greater_accra_assistant.json", 'w') as f:
        json.dump(assistant, f, indent=2)

    print(f"\n💾 Full config saved to: greater_accra_assistant.json")
    print("="*80)

if __name__ == "__main__":
    main()
