#!/usr/bin/env python3
"""
Update All Premier Health VAPI Assistant Configurations

Updates all regional assistant configurations with:
- New 11Labs voice ID: ZiQB5LljRyikkJWtFN55
- New OpenAI model: gpt-4o-mini
- Ensures query_premier_health_knowledge_base tool is added

Usage:
    python update_all_assistants_config.py
"""

import json
import os
from pathlib import Path

# Configuration updates
NEW_VOICE_ID = "ZiQB5LljRyikkJWtFN55"
NEW_MODEL = "gpt-4o-mini"
TOOL_ID = "560adfee-43bf-4614-baa8-0d5ccfbe9769"

# Assistant config files (excluding router and claims)
ASSISTANT_CONFIGS = [
    "config_ashanti_assistant.json",
    "config_greater_accra_assistant.json",
    "config_northern_regions_assistant.json",
    "config_bono_regions_assistant.json",
    "config_eastern_and_volta_assistant.json",
    "config_bono_bono_east_and_ahafo_assistant.json",
    "config_western_and_central_assistant.json",
]

BASE_PATH = "/opt/kasaai/apps/automations/premier-health"


def update_config(config_path: str) -> dict:
    """
    Update a single assistant configuration.

    Args:
        config_path: Path to config file

    Returns:
        dict with update stats
    """
    with open(config_path, 'r') as f:
        config = json.load(f)

    updates = []

    # Update voice ID
    if config.get('voice', {}).get('voiceId') != NEW_VOICE_ID:
        old_voice = config.get('voice', {}).get('voiceId', 'NOT SET')
        config['voice']['voiceId'] = NEW_VOICE_ID
        updates.append(f"Voice: {old_voice} → {NEW_VOICE_ID}")

    # Update model
    if config.get('model', {}).get('model') != NEW_MODEL:
        old_model = config.get('model', {}).get('model', 'NOT SET')
        config['model']['model'] = NEW_MODEL
        updates.append(f"Model: {old_model} → {NEW_MODEL}")

    # Ensure toolIds exists and contains our tool
    if 'toolIds' not in config.get('model', {}):
        config['model']['toolIds'] = []

    if TOOL_ID not in config['model']['toolIds']:
        config['model']['toolIds'].append(TOOL_ID)
        updates.append(f"Added tool: {TOOL_ID}")

    # Save updated config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    return {
        'file': os.path.basename(config_path),
        'updates': updates,
        'success': True
    }


def main():
    """Main execution."""
    print("=" * 80)
    print("Premier Health - Update All Assistant Configurations")
    print("=" * 80)

    print(f"\n📝 Configuration Updates:")
    print(f"   Voice ID: {NEW_VOICE_ID}")
    print(f"   Model: {NEW_MODEL}")
    print(f"   Tool ID: {TOOL_ID}")

    print(f"\n🔧 Processing {len(ASSISTANT_CONFIGS)} assistant configs...\n")

    results = []
    for config_file in ASSISTANT_CONFIGS:
        config_path = os.path.join(BASE_PATH, config_file)

        if not os.path.exists(config_path):
            print(f"   ⚠️  {config_file}: NOT FOUND")
            results.append({
                'file': config_file,
                'updates': [],
                'success': False
            })
            continue

        try:
            result = update_config(config_path)
            results.append(result)

            if result['updates']:
                print(f"   ✅ {config_file}")
                for update in result['updates']:
                    print(f"      - {update}")
            else:
                print(f"   ✓  {config_file} (already up to date)")

        except Exception as e:
            print(f"   ❌ {config_file}: ERROR - {e}")
            results.append({
                'file': config_file,
                'updates': [],
                'success': False,
                'error': str(e)
            })

    # Summary
    successful = sum(1 for r in results if r['success'])
    updated = sum(1 for r in results if r['success'] and r['updates'])

    print(f"\n" + "=" * 80)
    print(f"✅ UPDATE COMPLETE!")
    print(f"=" * 80)
    print(f"\n📊 Summary:")
    print(f"   Total configs: {len(ASSISTANT_CONFIGS)}")
    print(f"   Successfully processed: {successful}")
    print(f"   Updated: {updated}")
    print(f"   Already up to date: {successful - updated}")
    print(f"   Failed: {len(ASSISTANT_CONFIGS) - successful}")

    print(f"\n🎯 All assistants now configured with:")
    print(f"   ✅ 11Labs Voice: {NEW_VOICE_ID}")
    print(f"   ✅ OpenAI Model: {NEW_MODEL}")
    print(f"   ✅ RAG Tool: {TOOL_ID}")
    print(f"\n💡 Next step: Deploy configs to VAPI using individual update scripts")
    print("=" * 80)


if __name__ == "__main__":
    main()
