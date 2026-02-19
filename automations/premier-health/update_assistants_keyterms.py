#!/usr/bin/env python3
"""
Update all deployed assistants to ensure keyterms are properly configured
"""

import json
import requests
import time

# VAPI Configuration
VAPI_API_KEY = "42cf1e7c-2ef9-4bd7-ba30-52f2813605a2"
VAPI_BASE_URL = "https://api.vapi.ai"

# Load deployment record
with open('deployment_record.json', 'r') as f:
    deployment = json.load(f)

def update_assistant_keyterms(assistant_id, config_file, name):
    """Update an assistant with keyterms from config file"""

    # Load config
    with open(config_file, 'r') as f:
        config = json.load(f)

    transcriber = config.get('transcriber', {})
    keyterms = transcriber.get('keyterm', [])

    print(f"\n🔄 Updating {name}...")
    print(f"   ID: {assistant_id}")
    print(f"   Keyterms: {len(keyterms)} cities")

    if keyterms:
        print(f"   Sample: {', '.join(keyterms[:5])}...")

    # Update only transcriber to add keyterms
    update_payload = {
        "transcriber": transcriber
    }

    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }

    url = f"{VAPI_BASE_URL}/assistant/{assistant_id}"

    try:
        response = requests.patch(url, headers=headers, json=update_payload)

        if response.status_code == 200:
            print(f"   ✅ Updated successfully!")
            return True
        else:
            print(f"   ❌ Failed to update")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False


def main():
    print("=" * 80)
    print("UPDATING ASSISTANTS WITH KEYTERMS")
    print("=" * 80)

    success_count = 0
    total_count = 0

    # Update router
    print("\n" + "=" * 80)
    print("ROUTER ASSISTANT")
    print("=" * 80)

    router_id = deployment['router_assistant_id']
    if update_assistant_keyterms(router_id, 'config_router_assistant.json', 'Router'):
        success_count += 1
    total_count += 1
    time.sleep(1)

    # Update regional assistants
    print("\n" + "=" * 80)
    print("REGIONAL ASSISTANTS")
    print("=" * 80)

    regional_assistants = deployment['regional_assistants']

    config_mapping = {
        "Greater Accra": "config_greater_accra_assistant.json",
        "Ashanti": "config_ashanti_assistant.json",
        "Northern Regions": "config_northern_regions_assistant.json",
        "Western and Central": "config_western_and_central_assistant.json",
        "Eastern and Volta": "config_eastern_and_volta_assistant.json",
        "Bono Regions": "config_bono_regions_assistant.json"
    }

    for region, assistant_id in regional_assistants.items():
        config_file = config_mapping.get(region)
        if config_file:
            if update_assistant_keyterms(assistant_id, config_file, f"{region} Assistant"):
                success_count += 1
            total_count += 1
            time.sleep(1)

    # Summary
    print("\n" + "=" * 80)
    print("UPDATE SUMMARY")
    print("=" * 80)
    print(f"\n✅ Updated: {success_count}/{total_count} assistants")

    if success_count == total_count:
        print("\n🎉 All assistants updated successfully!")
        print("\nKeyterms are now configured:")
        print("  • Router: 33 region-level keywords")
        print("  • Greater Accra: 96 cities")
        print("  • Ashanti: 70 cities")
        print("  • Northern Regions: 30 cities")
        print("  • Western and Central: 51 cities")
        print("  • Eastern and Volta: 41 cities")
        print("  • Bono Regions: 36 cities")
        print("\n📝 Note: Keyterms work during transcription but may not show in API responses")
        print("    Test with actual calls to verify city name transcription accuracy")
    else:
        print(f"\n⚠️  Some updates failed. Check errors above.")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
