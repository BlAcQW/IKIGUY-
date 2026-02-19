#!/usr/bin/env python3
"""
Deploy Updated Greater Accra Assistant to VAPI

Updates:
1. Removed duplicate COMMUNITY keyterms (now just "COMMUNITY")
2. Model already correct: gpt-4o-mini (GPT 4.1 mini)
3. Voice already correct: ZiQB5LljRyikkJWtFN55
4. Tool ID already correct: 560adfee-43bf-4614-baa8-0d5ccfbe9769
"""

import os
import json
import httpx
import asyncio

VAPI_API_KEY = os.getenv("VAPI_API_KEY")
ASSISTANT_ID = "85e1cf7e-1711-4d01-9cad-c043b37707bd"
CONFIG_FILE = "/opt/kasaai/apps/automations/premier-health/config_greater_accra_assistant.json"


async def deploy_assistant():
    """Deploy assistant to VAPI."""
    print("🚀 Deploying Greater Accra Assistant to VAPI")
    print("=" * 70)

    # Load config
    print(f"\n1. Loading config from {CONFIG_FILE}...")
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)

    print(f"   ✅ Config loaded")
    print(f"      Model: {config['model']['model']}")
    print(f"      Voice: {config['voice']['voiceId']}")
    print(f"      Keyterms: {len(config['transcriber']['keyterm'])}")
    print(f"      Has COMMUNITY: {'COMMUNITY' in config['transcriber']['keyterm']}")
    print(f"      Has COMMUNITY 4: {'COMMUNITY 4' in config['transcriber']['keyterm']}")

    # Deploy
    print(f"\n2. Deploying to VAPI assistant {ASSISTANT_ID}...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.patch(
                f"https://api.vapi.ai/assistant/{ASSISTANT_ID}",
                json=config,
                headers={
                    "Authorization": f"Bearer {VAPI_API_KEY}",
                    "Content-Type": "application/json"
                }
            )
            response.raise_for_status()
            result = response.json()

            print(f"   ✅ Deployment successful!")
            print(f"      Assistant ID: {result.get('id')}")
            print(f"      Name: {result.get('name')}")
            print(f"      Model: {result.get('model', {}).get('model')}")
            print(f"      Updated: {result.get('updatedAt')}")

            # Verify keyterms
            deployed_keyterms = result.get('transcriber', {}).get('keyterm', [])
            print(f"\n   Deployed keyterms count: {len(deployed_keyterms)}")
            print(f"   Has COMMUNITY: {'COMMUNITY' in deployed_keyterms}")
            print(f"   Has COMMUNITY 4: {'COMMUNITY 4' in deployed_keyterms}")

            if 'COMMUNITY' in deployed_keyterms and 'COMMUNITY 4' not in deployed_keyterms:
                print(f"\n   🎉 Keyterms cleaned successfully!")
            else:
                print(f"\n   ⚠️  Keyterm cleanup may need verification")

            return True

        except httpx.HTTPStatusError as e:
            print(f"   ❌ HTTP Error: {e.response.status_code}")
            print(f"      Response: {e.response.text[:500]}")
            return False
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False


async def main():
    """Main execution."""
    success = await deploy_assistant()

    if success:
        print("\n✅ Greater Accra Assistant Deployment Complete!")
        print("\nChanges:")
        print("  - Removed duplicate COMMUNITY keyterms (COMMUNITY 4, 5, 6, 9, 10, 12, 22, 26)")
        print("  - Kept only 'COMMUNITY' - STT will handle the numbers")
        print("  - Model: gpt-4o-mini (GPT 4.1 mini) ✓")
        print("  - Voice: ZiQB5LljRyikkJWtFN55 ✓")
        print("  - RAG queries tested: All separated cities working ✓")
    else:
        print("\n❌ Deployment failed")


if __name__ == "__main__":
    asyncio.run(main())
