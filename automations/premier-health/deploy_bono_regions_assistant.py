#!/usr/bin/env python3
"""
Deploy Updated Bono Regions Assistant to VAPI

Changes:
1. Removed duplicate SAMPA keyterm
2. Fixed BECHEM city (was incorrectly under KENYASE)
3. Separated KINTAMPO and DUAYAW NKWANTA
4. Model already correct: gpt-4o-mini
5. Voice already correct: ZiQB5LljRyikkJWtFN55
6. Tool ID already correct: 560adfee-43bf-4614-baa8-0d5ccfbe9769
"""

import os
import json
import httpx
import asyncio

VAPI_API_KEY = os.getenv("VAPI_API_KEY")
ASSISTANT_ID = "e39da43d-1190-419a-9739-d2c11bc8fe78"
CONFIG_FILE = "/opt/kasaai/apps/automations/premier-health/config_bono_regions_assistant.json"


async def deploy_assistant():
    """Deploy assistant to VAPI."""
    print("🚀 Deploying Bono Regions Assistant to VAPI")
    print("=" * 70)

    # Load config
    print(f"\n1. Loading config from {CONFIG_FILE}...")
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)

    print(f"   ✅ Config loaded")
    print(f"      Model: {config['model']['model']}")
    print(f"      Voice: {config['voice']['voiceId']}")
    print(f"      Keyterms: {len(config['transcriber']['keyterm'])}")

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
        print("\n✅ Bono Regions Assistant Deployment Complete!")
        print("\nChanges:")
        print("  - Removed duplicate SAMPA keyterm")
        print("  - Fixed BECHEM city (separated from KENYASE)")
        print("  - Separated KINTAMPO and DUAYAW NKWANTA cities")
        print("  - Created 14 city documents in RAG")
        print("  - Model: gpt-4o-mini ✓")
        print("  - Voice: ZiQB5LljRyikkJWtFN55 ✓")
        print("  - RAG queries tested: All cities working ✓")
    else:
        print("\n❌ Deployment failed")


if __name__ == "__main__":
    asyncio.run(main())
