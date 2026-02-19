"""
Fix VAPI Assistant Transcript Settings

This script adds the artifactPlan configuration to enable full transcripts
including both user and assistant messages in the end-of-call report.

Issue: Transcripts only showing user messages, not assistant responses
Fix: Add artifactPlan with proper configuration

Usage:
    python fix_vapi_transcript_settings.py
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


def update_vapi_assistant_transcript_settings(assistant_id: str) -> dict:
    """
    Update VAPI assistant with proper artifact plan for full transcripts.

    Args:
        assistant_id: VAPI assistant ID

    Returns:
        Update response from VAPI API
    """
    try:
        headers = {
            "Authorization": f"Bearer {VAPI_API_KEY}",
            "Content-Type": "application/json"
        }

        # Configuration to enable full transcripts
        update_payload = {
            "artifactPlan": {
                "recordingEnabled": True,
                "videoRecordingEnabled": False,
                "transcriptPlan": {
                    "enabled": True,
                    "assistantName": "Ama",
                    "userName": "Customer"
                }
            },
            "recordingEnabled": True  # Also enable recording at assistant level
        }

        print("=" * 80)
        print("VAPI Assistant Transcript Settings Fix")
        print("=" * 80)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Assistant ID: {assistant_id}")
        print(f"VAPI API: {VAPI_BASE_URL}")
        print()

        print("🔧 Configuration to apply:")
        print(json.dumps(update_payload, indent=2))
        print()

        print(f"📡 Updating assistant settings...")

        with httpx.Client(timeout=30.0) as client:
            response = client.patch(
                f"{VAPI_BASE_URL}/assistant/{assistant_id}",
                headers=headers,
                json=update_payload
            )

            if response.status_code in [200, 201]:
                result = response.json()
                print(f"✅ Success! Assistant updated")
                print()

                # Verify the settings were applied
                print("🔍 Verifying applied settings:")
                if "artifactPlan" in result:
                    print(f"  ✅ artifactPlan: {json.dumps(result['artifactPlan'], indent=4)}")
                else:
                    print(f"  ⚠️  artifactPlan not in response")

                if "recordingEnabled" in result:
                    print(f"  ✅ recordingEnabled: {result['recordingEnabled']}")
                else:
                    print(f"  ⚠️  recordingEnabled not in response")

                return result
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                return {"error": response.text, "status_code": response.status_code}

    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return {"error": str(e)}


def main():
    """Main function to fix transcript settings."""
    print()
    print("🔍 ISSUE IDENTIFIED:")
    print("   Transcripts only showing user messages, not assistant responses")
    print("   Root cause: artifactPlan not configured on assistant")
    print()
    print("🔧 FIX:")
    print("   Add artifactPlan with transcriptPlan enabled")
    print("   Enable recordingEnabled for full conversation capture")
    print()
    print("=" * 80)
    print()

    result = update_vapi_assistant_transcript_settings(ASSISTANT_ID)

    print()
    print("=" * 80)
    print("Update Summary")
    print("=" * 80)

    if "id" in result:
        print("✅ Status: SUCCESS")
        print(f"   Assistant ID: {result['id']}")
        print(f"   Updated at: {result.get('updatedAt')}")
        print()
        print("✅ Expected behavior after fix:")
        print("   - Full transcripts with both user AND assistant messages")
        print("   - Transcripts visible in VAPI dashboard during calls")
        print("   - Complete conversation history in end-of-call reports")
        print("   - Database will save full transcripts with both sides")
    else:
        print("❌ Status: FAILED")
        print(f"   Error: {result.get('error')}")

    print("=" * 80)


if __name__ == "__main__":
    main()
