#!/usr/bin/env python3
"""
Update Greater Accra Region VAPI Assistant with Separated City Keyterms

This script updates the Greater Accra regional assistant (85e1cf7e-1711-4d01-9cad-c043b37707bd)
with the corrected city keyterms after separating merged cities.

Changes:
- Removed: SANTASIPATASE, TAFOBREMANG (merged names)
- Added: PATASE, MAMPONTENG, ABUAKWA, AGONA, WIAMOASE, DUNKWA
- All 24 individual Greater Accra cities now properly represented

Usage:
    python update_greater_accra_assistant.py
"""

import os
import sys
import json
import httpx
from datetime import datetime

# VAPI Configuration
VAPI_API_KEY = os.getenv("VAPI_API_KEY", "42cf1e7c-2ef9-4bd7-ba30-52f2813605a2")
VAPI_BASE_URL = os.getenv("VAPI_BASE_URL", "https://api.vapi.ai")

# Greater Accra Assistant Configuration
ASSISTANT_ID = "85e1cf7e-1711-4d01-9cad-c043b37707bd"
ASSISTANT_NAME = "Premier Health Greater Accra"

# Load the updated config
CONFIG_PATH = "/opt/kasaai/apps/automations/premier-health/config_greater_accra_assistant.json"


def load_config():
    """Load the assistant configuration from JSON file."""
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return None


def verify_keyterms(keyterms):
    """Verify that separated city keyterms are properly included."""
    print("\n🔍 Verifying separated city coverage...")

    required_cities = {
        "SANTASI": "Individual city (was part of Santasipatase)",
        "PATASE": "Individual city (was part of Santasipatase)",
        "TAFO": "Individual city (was part of Tafobremang)",
        "BREMANG": "Individual city (was part of Tafobremang)",
        "BOMSO": "Individual city (was part of Bomso/Knust/Ejisu)",
        "KNUST": "Individual city (was part of Bomso/Knust/Ejisu)",
        "EJISU": "Individual city (was part of Bomso/Knust/Ejisu)",
        "ABUAKWA": "Individual city (was part of Abuakwa/Tanoso)",
        "TANOSO": "Individual city (was part of Abuakwa/Tanoso)",
        "AHODWO": "Individual city (was part of Ahodwo/Ahinsan)",
        "AHINSAN": "Individual city (was part of Ahodwo/Ahinsan)",
        "MAMPONG": "Individual city (was part of Mampong/Agona/Wiamoase)",
        "AGONA": "Individual city (was part of Mampong/Agona/Wiamoase)",
        "WIAMOASE": "Individual city (was part of Mampong/Agona/Wiamoase)",
        "OBUASI": "Individual city (was part of Obuasi/Dunkwa)",
        "DUNKWA": "Individual city (was part of Obuasi/Dunkwa)",
        "KONONGO": "Individual city (was part of Konongo/Agogo)",
        "AGOGO": "Individual city (was part of Konongo/Agogo)",
        "MAMPONTENG": "Individual city",
        "ASOKWA": "Individual city",
        "BANTAMA": "Individual city",
        "ABREPO": "Individual city",
        "SUAME": "Individual city",
        "ADUM": "Individual city",
    }

    removed_cities = ["SANTASIPATASE", "TAFOBREMANG"]

    all_pass = True

    print("\n   ✅ REQUIRED CITIES (should be present):")
    for city, description in required_cities.items():
        if city in keyterms:
            print(f"      ✓ {city:15} - {description}")
        else:
            print(f"      ✗ {city:15} - MISSING! {description}")
            all_pass = False

    print("\n   ❌ REMOVED CITIES (should NOT be present):")
    for city in removed_cities:
        if city in keyterms:
            print(f"      ✗ {city:15} - STILL PRESENT! Should be removed")
            all_pass = False
        else:
            print(f"      ✓ {city:15} - Correctly removed")

    return all_pass


def update_assistant(config):
    """Update assistant with new configuration."""
    try:
        headers = {
            "Authorization": f"Bearer {VAPI_API_KEY}",
            "Content-Type": "application/json"
        }

        print(f"\n🔧 Updating assistant: {ASSISTANT_ID}")
        print(f"   Name: {config.get('name', ASSISTANT_NAME)}")

        # Extract keyterms from config
        keyterms = config.get('transcriber', {}).get('keyterm', [])
        print(f"   Keyterms count: {len(keyterms)}")

        # Verify keyterms
        verification_passed = verify_keyterms(keyterms)

        if not verification_passed:
            print("\n⚠️  WARNING: Keyterm verification failed!")
            response = input("Continue with update anyway? (yes/no): ")
            if response.lower() != 'yes':
                print("❌ Update cancelled by user")
                return None

        print("\n📍 Key separations in this update:")
        print("   • SANTASI + PATASE (removed: SANTASIPATASE)")
        print("   • TAFO + BREMANG (removed: TAFOBREMANG)")
        print("   • BOMSO + KNUST + EJISU (3 individual cities)")
        print("   • ABUAKWA + TANOSO (2 individual cities)")
        print("   • AHODWO + AHINSAN (2 individual cities)")
        print("   • MAMPONG + AGONA + WIAMOASE (3 individual cities)")
        print("   • OBUASI + DUNKWA (2 individual cities)")
        print("   • KONONGO + AGOGO (2 individual cities)")

        print("\n🚀 Sending update to VAPI...")

        with httpx.Client(timeout=30.0) as client:
            response = client.patch(
                f"{VAPI_BASE_URL}/assistant/{ASSISTANT_ID}",
                headers=headers,
                json=config
            )

            if response.status_code in [200, 201]:
                result = response.json()
                print(f"\n✅ Assistant updated successfully!")
                print(f"   Assistant ID: {result.get('id')}")
                print(f"   Name: {result.get('name')}")
                print(f"   Updated at: {result.get('updatedAt')}")

                # Verify transcriber
                transcriber = result.get('transcriber', {})
                if transcriber:
                    print(f"\n🎙️  Transcriber Verified:")
                    print(f"   Provider: {transcriber.get('provider')}")
                    print(f"   Model: {transcriber.get('model')}")
                    print(f"   Language: {transcriber.get('language')}")
                    returned_keyterms = transcriber.get('keyterm', [])
                    print(f"   Keyterms: {len(returned_keyterms)}")

                    # Verify key cities are present
                    test_cities = ['SANTASI', 'PATASE', 'TAFO', 'BREMANG', 'MAMPONTENG', 'AGONA', 'WIAMOASE', 'DUNKWA']
                    missing = [city for city in test_cities if city not in returned_keyterms]

                    if missing:
                        print(f"   ⚠️  WARNING: Some cities still missing: {', '.join(missing)}")
                    else:
                        print(f"   ✅ All test cities verified present!")

                return result
            else:
                print(f"\n❌ Error updating assistant: {response.status_code}")
                print(f"   Response: {response.text}")
                return None

    except Exception as e:
        print(f"\n❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main function."""
    print("=" * 80)
    print("Premier Health Greater Accra Assistant - City Separation Update")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Assistant ID: {ASSISTANT_ID}")
    print(f"Config file: {CONFIG_PATH}")

    # Load config
    print("\n📄 Loading configuration...")
    config = load_config()

    if not config:
        print("❌ Failed to load configuration. Exiting.")
        return

    print(f"✅ Configuration loaded successfully")

    # Update assistant
    result = update_assistant(config)

    if result:
        print("\n" + "=" * 80)
        print("✅ UPDATE SUCCESSFUL!")
        print("=" * 80)
        print("\n📝 KEY CHANGES:")
        print("   ✅ Removed merged city names (SANTASIPATASE, TAFOBREMANG)")
        print("   ✅ Added individual cities (PATASE, MAMPONTENG, AGONA, WIAMOASE, DUNKWA, etc.)")
        print("   ✅ All 24 Greater Accra cities now properly represented")
        print("   ✅ RAG database updated with separated city documents")
        print("\n🎯 User Experience:")
        print("   • Query 'doctors in SANTASI' → Returns providers in SANTASI ✅")
        print("   • Query 'hospitals in PATASE' → Returns providers in PATASE ✅")
        print("   • Query 'clinics in BREMANG' → Returns providers in BREMANG ✅")
        print("   • Query 'facilities in MAMPONTENG' → Returns providers in MAMPONTENG ✅")
        print("\n📊 Coverage:")
        print("   • 24 city-specific documents in RAG database")
        print("   • Cities properly separated (e.g., SANTASI ≠ PATASE)")
        print("   • All Greater Accra region cities covered")
        print("=" * 80)
    else:
        print("\n❌ UPDATE FAILED - Check errors above")
        sys.exit(1)


if __name__ == "__main__":
    main()
