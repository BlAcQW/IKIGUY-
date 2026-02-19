#!/usr/bin/env python3
"""
Deploy VAPI Squad with Router and Regional Assistants
Creates all assistants and squad configuration in VAPI
"""

import json
import requests
import time
from pathlib import Path

# VAPI Configuration
VAPI_API_KEY = "42cf1e7c-2ef9-4bd7-ba30-52f2813605a2"
VAPI_BASE_URL = "https://api.vapi.ai"

# New assistant ID to use as base (per user request)
BASE_ASSISTANT_ID = "d9cc5399-14b8-49b0-8e6b-e541dd9703b6"

# Region names in order
REGIONS = [
    "Greater Accra",
    "Ashanti",
    "Northern Regions",
    "Western and Central",
    "Eastern and Volta",
    "Bono Regions"
]


def load_json_config(filename):
    """Load JSON configuration file"""
    filepath = Path(__file__).parent / filename
    with open(filepath, 'r') as f:
        return json.load(f)


def create_assistant(config, assistant_name):
    """
    Create an assistant in VAPI

    Args:
        config (dict): Assistant configuration
        assistant_name (str): Name for logging

    Returns:
        str: Assistant ID if successful, None otherwise
    """
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }

    url = f"{VAPI_BASE_URL}/assistant"

    print(f"\n📤 Creating {assistant_name}...")
    print(f"   Name: {config['name']}")
    print(f"   Model: {config['model']['provider']} - {config['model']['model']}")

    if 'keywords' in config.get('transcriber', {}):
        keywords_count = len(config['transcriber']['keywords'])
        print(f"   Keywords: {keywords_count} cities")

    try:
        response = requests.post(url, headers=headers, json=config)

        if response.status_code == 201:
            assistant_data = response.json()
            assistant_id = assistant_data['id']
            print(f"✅ Created successfully! ID: {assistant_id}")
            return assistant_id
        else:
            print(f"❌ Failed to create {assistant_name}")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return None

    except Exception as e:
        print(f"❌ Error creating {assistant_name}: {str(e)}")
        return None


def update_assistant(assistant_id, config, assistant_name):
    """
    Update an existing assistant in VAPI

    Args:
        assistant_id (str): ID of assistant to update
        config (dict): New configuration
        assistant_name (str): Name for logging

    Returns:
        bool: True if successful
    """
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }

    url = f"{VAPI_BASE_URL}/assistant/{assistant_id}"

    print(f"\n📝 Updating {assistant_name} (ID: {assistant_id})...")

    try:
        response = requests.patch(url, headers=headers, json=config)

        if response.status_code == 200:
            print(f"✅ Updated successfully!")
            return True
        else:
            print(f"❌ Failed to update {assistant_name}")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return False

    except Exception as e:
        print(f"❌ Error updating {assistant_name}: {str(e)}")
        return False


def create_squad(config):
    """
    Create a squad in VAPI

    Args:
        config (dict): Squad configuration

    Returns:
        str: Squad ID if successful, None otherwise
    """
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }

    url = f"{VAPI_BASE_URL}/squad"

    print(f"\n🔗 Creating Squad: {config['name']}...")
    print(f"   Members: {len(config['members'])} assistants")

    try:
        response = requests.post(url, headers=headers, json=config)

        if response.status_code == 201:
            squad_data = response.json()
            squad_id = squad_data['id']
            print(f"✅ Squad created successfully! ID: {squad_id}")
            return squad_id
        else:
            print(f"❌ Failed to create squad")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return None

    except Exception as e:
        print(f"❌ Error creating squad: {str(e)}")
        return None


def deploy_full_squad():
    """
    Deploy complete squad with router and all regional assistants

    Returns:
        dict: Deployment results with all IDs
    """
    print("=" * 80)
    print("VAPI SQUAD DEPLOYMENT - PREMIER HEALTH NAVIGATOR")
    print("=" * 80)
    print("\nDeploying router + 6 regional assistants + squad configuration...")

    results = {
        "router_id": None,
        "regional_ids": {},
        "squad_id": None,
        "success": False
    }

    # Step 1: Create Router Assistant
    print("\n" + "=" * 80)
    print("STEP 1: Create Router Assistant")
    print("=" * 80)

    router_config = load_json_config("config_router_assistant.json")
    router_id = create_assistant(router_config, "Router Assistant")

    if not router_id:
        print("\n❌ Failed to create router. Aborting deployment.")
        return results

    results["router_id"] = router_id
    time.sleep(2)  # Rate limiting

    # Step 2: Create Regional Assistants
    print("\n" + "=" * 80)
    print("STEP 2: Create Regional Assistants")
    print("=" * 80)

    regional_ids = {}

    for region in REGIONS:
        safe_filename = region.replace(" ", "_").replace(",", "").lower()
        config_file = f"config_{safe_filename}_assistant.json"

        regional_config = load_json_config(config_file)
        assistant_id = create_assistant(regional_config, f"{region} Assistant")

        if not assistant_id:
            print(f"\n⚠️  Failed to create {region} assistant. Continuing with others...")
            continue

        regional_ids[region] = assistant_id
        time.sleep(2)  # Rate limiting

    if len(regional_ids) != len(REGIONS):
        print(f"\n⚠️  Warning: Only created {len(regional_ids)}/{len(REGIONS)} regional assistants")

    results["regional_ids"] = regional_ids

    # Step 3: Create Squad Configuration
    print("\n" + "=" * 80)
    print("STEP 3: Create Squad")
    print("=" * 80)

    # Build squad config with actual IDs and assistant destinations
    # assistantDestinations allow VAPI to handle transcriber handoff automatically
    assistant_destinations = []
    for region, assistant_id in regional_ids.items():
        assistant_destinations.append({
            "type": "assistant",
            "assistantId": assistant_id,
            "assistantName": f"Premier Health {region}",
            "message": f"Let me connect you to our {region} specialist who knows all the healthcare facilities in your area.",
            "description": f"Transfer to {region} specialist"
        })

    # Router member with assistant destinations
    router_member = {
        "assistant": router_id,
        "assistantDestinations": assistant_destinations
    }

    # Regional members (no destinations needed)
    regional_members = [{"assistant": assistant_id} for assistant_id in regional_ids.values()]

    # Complete squad configuration
    squad_config = {
        "name": "Premier Health Navigator Squad",
        "members": [router_member] + regional_members
    }

    squad_id = create_squad(squad_config)

    if not squad_id:
        print("\n❌ Failed to create squad")
        return results

    results["squad_id"] = squad_id
    results["success"] = True

    # Save deployment results
    deployment_record = {
        "deployed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "router_assistant_id": router_id,
        "regional_assistants": regional_ids,
        "squad_id": squad_id,
        "total_assistants": 1 + len(regional_ids),
        "regions": list(regional_ids.keys())
    }

    with open('/opt/kasaai/apps/automations/premier-health/deployment_record.json', 'w') as f:
        json.dump(deployment_record, f, indent=2)

    # Print summary
    print("\n" + "=" * 80)
    print("DEPLOYMENT COMPLETE ✅")
    print("=" * 80)
    print(f"\n✅ Router Assistant: {router_id}")
    print(f"\n✅ Regional Assistants ({len(regional_ids)}):")
    for region, aid in regional_ids.items():
        print(f"   • {region}: {aid}")
    print(f"\n✅ Squad: {squad_id}")
    print(f"\n📝 Deployment record saved to: deployment_record.json")
    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print("1. Test the squad with sample calls")
    print("2. Monitor call transcripts for accuracy")
    print("3. Update knowledge base with regional filtering if needed")
    print("4. Run test_squad.py to verify all transfers work correctly")
    print("\n✅ Squad is ready for testing!")

    return results


def deploy_update_base_assistant():
    """
    Alternative: Update the existing base assistant instead of creating new ones
    """
    print("=" * 80)
    print("UPDATE BASE ASSISTANT - PREMIER HEALTH NAVIGATOR")
    print("=" * 80)
    print(f"\nUpdating assistant {BASE_ASSISTANT_ID} with router configuration...")

    router_config = load_json_config("config_router_assistant.json")
    success = update_assistant(BASE_ASSISTANT_ID, router_config, "Base Assistant")

    if success:
        print("\n✅ Base assistant updated successfully!")
        print(f"   Assistant ID: {BASE_ASSISTANT_ID}")
        print("\nNote: You still need to create the 6 regional assistants separately.")
        print("Run deploy_full_squad() to create complete squad setup.")
    else:
        print("\n❌ Failed to update base assistant")

    return success


if __name__ == "__main__":
    import sys

    print("\nVAPI Squad Deployment Script")
    print("=" * 80)
    print("\nOptions:")
    print("1. Deploy complete squad (router + 6 regional assistants + squad)")
    print("2. Update existing base assistant only")
    print()

    choice = input("Enter choice (1 or 2): ").strip()

    if choice == "1":
        results = deploy_full_squad()
        if results["success"]:
            sys.exit(0)
        else:
            sys.exit(1)
    elif choice == "2":
        success = deploy_update_base_assistant()
        sys.exit(0 if success else 1)
    else:
        print("Invalid choice. Exiting.")
        sys.exit(1)
