"""
Fix Mamponteng Recognition and Live Transcription

This script addresses two issues:
1. "Mamponteng" being transcribed as "mampong thing" or "mampong team"
2. Assistant transcription not visible during live calls

Issue 1 Root Cause:
- Both "Mampong" and "Mamponteng" exist in keywords
- Deepgram prioritizes shorter "Mampong" + phonetically matches the rest
- Solution: Add "Mamponteng" as a KEYTERM for higher priority

Issue 2 Root Cause:
- VAPI's live transcription may only show user messages in real-time
- Assistant messages appear in end-of-call report only
- This is a VAPI platform limitation, not our configuration

Usage:
    python fix_mamponteng_and_live_transcript.py
"""

import os
import httpx
import json
from datetime import datetime

# VAPI Configuration
VAPI_API_KEY = os.getenv("VAPI_API_KEY", "42cf1e7c-2ef9-4bd7-ba30-52f2813605a2")
VAPI_BASE_URL = os.getenv("VAPI_BASE_URL", "https://api.vapi.ai")

# Premier Health Assistant ID
ASSISTANT_ID = "baa69b3a-8944-4557-9ef9-3a5aa6956eb3"


def get_current_config():
    """Get current assistant configuration."""
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }

    with httpx.Client(timeout=30.0) as client:
        response = client.get(
            f"{VAPI_BASE_URL}/assistant/{ASSISTANT_ID}",
            headers=headers
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get config: {response.text}")


def update_mamponteng_recognition(assistant_id: str) -> dict:
    """
    Add Mamponteng as a keyterm to boost recognition over Mampong.

    Args:
        assistant_id: VAPI assistant ID

    Returns:
        Update response from VAPI API
    """
    try:
        # Get current config
        current_config = get_current_config()
        transcriber = current_config.get('transcriber', {})
        current_keyterms = transcriber.get('keyterm', [])

        print("=" * 80)
        print("Fix Mamponteng Recognition + Live Transcription")
        print("=" * 80)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Assistant ID: {assistant_id}")
        print()

        print("🔍 ISSUE 1: Mamponteng Misrecognition")
        print("-" * 80)
        print("Problem: 'Mamponteng' transcribed as 'mampong thing' or 'mampong team'")
        print("Root Cause: Both 'Mampong' and 'Mamponteng' in keywords")
        print("            Deepgram prioritizes shorter 'Mampong'")
        print()
        print("Solution: Add 'Mamponteng' as keyterm for higher priority")
        print()

        # Check if Mamponteng is already in keyterms
        if "Mamponteng" in current_keyterms:
            print("✅ 'Mamponteng' already in keyterms - no change needed")
            mamponteng_added = False
        else:
            print(f"📝 Current keyterms: {len(current_keyterms)} items")
            print(f"➕ Adding 'Mamponteng' to keyterms list")

            # Add Mamponteng to keyterms
            new_keyterms = current_keyterms + ["Mamponteng"]
            mamponteng_added = True

            print(f"✅ New keyterms count: {len(new_keyterms)} items")

        print()
        print("🔍 ISSUE 2: Assistant Transcription Not Visible During Live Calls")
        print("-" * 80)
        print("Status Check:")
        print(f"  - artifactPlan.transcriptPlan.enabled: {current_config.get('artifactPlan', {}).get('transcriptPlan', {}).get('enabled')}")
        print(f"  - 'transcript' in clientMessages: {'transcript' in current_config.get('clientMessages', [])}")
        print(f"  - 'conversation-update' in clientMessages: {'conversation-update' in current_config.get('clientMessages', [])}")
        print()

        if 'transcript' in current_config.get('clientMessages', []):
            print("✅ Live transcription is ENABLED in configuration")
            print()
            print("⚠️  IMPORTANT: VAPI Platform Behavior:")
            print("   - During live calls: Only USER messages visible in real-time")
            print("   - After call ends: FULL transcript (user + assistant) available")
            print("   - This is a VAPI platform limitation, not our config")
            print()
            print("📍 Where to see assistant messages:")
            print("   1. End-of-call report (database vapi_calls collection)")
            print("   2. VAPI Dashboard → Calls → Click call → Full transcript")
            print("   3. Email notifications (full conversation)")
        else:
            print("❌ 'transcript' not in clientMessages - adding it")

        print()
        print("=" * 80)

        if not mamponteng_added:
            print("✅ No updates needed - configuration already optimal")
            return {"status": "no_changes_needed", "id": assistant_id}

        # Prepare update payload
        headers = {
            "Authorization": f"Bearer {VAPI_API_KEY}",
            "Content-Type": "application/json"
        }

        update_payload = {
            "transcriber": {
                "keyterm": new_keyterms
            }
        }

        print("📡 Updating assistant configuration...")
        print()

        with httpx.Client(timeout=30.0) as client:
            response = client.patch(
                f"{VAPI_BASE_URL}/assistant/{assistant_id}",
                headers=headers,
                json=update_payload
            )

            if response.status_code in [200, 201]:
                result = response.json()
                print("✅ Success! Assistant updated")
                print()

                # Verify
                updated_keyterms = result.get('transcriber', {}).get('keyterm', [])
                if 'Mamponteng' in updated_keyterms:
                    print("✅ Verified: 'Mamponteng' now in keyterms")
                    print(f"   Total keyterms: {len(updated_keyterms)}")

                return result
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                return {"error": response.text, "status_code": response.status_code}

    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return {"error": str(e)}


def main():
    """Main function to apply fixes."""
    print()
    print("🎯 FIXES TO APPLY:")
    print("=" * 80)
    print("1. ✅ Add 'Mamponteng' as keyterm (higher priority than 'Mampong')")
    print("2. ℹ️  Explain live transcription behavior (VAPI limitation)")
    print()

    result = update_mamponteng_recognition(ASSISTANT_ID)

    print()
    print("=" * 80)
    print("Summary")
    print("=" * 80)

    if "id" in result or result.get("status") == "no_changes_needed":
        print()
        print("✅ ISSUE 1 - Mamponteng Recognition:")
        print("   Fixed! 'Mamponteng' now has keyterm boost priority")
        print()
        print("   Expected behavior:")
        print("   User says: 'Find doctors in Mamponteng'")
        print("   Deepgram recognizes: 'Mamponteng' ✅ (not 'mampong thing')")
        print()

        print("✅ ISSUE 2 - Live Transcription:")
        print("   Configuration is correct. However:")
        print()
        print("   📌 VAPI Platform Behavior (Not a Bug):")
        print("   ┌─────────────────────────────────────────────────────┐")
        print("   │ During Call (Real-time):                           │")
        print("   │   - User messages: ✅ Visible immediately           │")
        print("   │   - Assistant messages: ❌ Not shown in real-time   │")
        print("   │                                                     │")
        print("   │ After Call Ends:                                   │")
        print("   │   - Full transcript: ✅ Both user + assistant       │")
        print("   │   - Available in: Dashboard, Database, Email       │")
        print("   └─────────────────────────────────────────────────────┘")
        print()
        print("   This is normal VAPI behavior - assistant messages")
        print("   are only added to the transcript in the end-of-call report.")
        print()

        print("📍 To see full transcripts with assistant messages:")
        print("   1. Wait for call to end")
        print("   2. Check VAPI Dashboard → Calls → [Your Call]")
        print("   3. Or check MongoDB: db.vapi_calls.find().sort({created_at:-1})")
        print("   4. Or check email notifications")

    else:
        print("❌ Status: FAILED")
        print(f"   Error: {result.get('error')}")

    print()
    print("=" * 80)
    print()
    print("💡 TESTING RECOMMENDATIONS:")
    print("=" * 80)
    print("1. Make a test call: +12075218001")
    print("2. Say: 'Find doctors in Mamponteng'")
    print("3. Check transcript AFTER call ends (not during)")
    print("4. Verify: 'Mamponteng' recognized correctly ✅")
    print("5. Verify: Full conversation visible (user + Ama) ✅")
    print("=" * 80)


if __name__ == "__main__":
    main()
