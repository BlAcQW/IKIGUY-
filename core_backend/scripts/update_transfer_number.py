#!/usr/bin/env python3
"""
Script to update Hey Papa Phone assistant transfer number.

This script updates the assistant's transferCall tool with a new destination number
and adds warm transfer configuration.
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv("/opt/kasaai/.env")

VAPI_API_KEY = os.getenv("VAPI_API_KEY")
ASSISTANT_ID = "c2854d74-dafe-445c-8c34-1326c2310cb7"  # Hey Papa Hybrid
NEW_TRANSFER_NUMBER = "+233548480355"


def update_transfer_number():
    """
    Update the assistant's transfer number.

    Returns:
        dict: Updated assistant configuration
    """
    url = f"https://api.vapi.ai/assistant/{ASSISTANT_ID}"

    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }

    # Get current assistant configuration
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    assistant = response.json()

    # Updated configuration with new transfer number and warm transfer
    update_payload = {
        "model": {
            "provider": assistant.get("model", {}).get("provider"),
            "model": assistant.get("model", {}).get("model"),
            "messages": assistant.get("model", {}).get("messages", []),
            "maxTokens": assistant.get("model", {}).get("maxTokens"),
            "tools": [
                {
                    "type": "transferCall",
                    "destinations": [
                        {
                            "type": "number",
                            "number": NEW_TRANSFER_NUMBER,
                            "message": "Connecting you to a church representative who can help you."
                        }
                    ],
                    "function": {
                        "name": "transferCall",
                        "description": f"Use this function to transfer the call to a church representative at {NEW_TRANSFER_NUMBER}. Call this when the user needs assistance with tithes, offerings, bookings, complaints, or wants to speak to someone.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "destination": {
                                    "type": "string",
                                    "enum": [NEW_TRANSFER_NUMBER],
                                    "description": f"The destination to transfer to. Must be '{NEW_TRANSFER_NUMBER}'"
                                }
                            },
                            "required": ["destination"]
                        }
                    },
                    "messages": [
                        {
                            "type": "request-start",
                            "content": "I will connect you now so someone can assist you properly. Please hold on a moment."
                        },
                        {
                            "type": "request-complete",
                            "content": "Connecting you now."
                        }
                    ]
                }
            ]
        }
    }

    print(f"🔧 Updating transfer number for assistant {ASSISTANT_ID}...")
    print(f"   Old transfer number: +233504796858")
    print(f"   New transfer number: {NEW_TRANSFER_NUMBER}")
    print("-" * 80)

    response = requests.patch(url, headers=headers, json=update_payload)
    response.raise_for_status()

    return response.json()


def main():
    """Main execution function."""
    try:
        result = update_transfer_number()

        print("\n✅ Transfer number updated successfully!")
        print(f"\n📞 New transfer destination: {NEW_TRANSFER_NUMBER}")
        print(f"   Updated at: {result.get('updatedAt')}")

        print("\n" + "=" * 80)
        print("✅ CONFIGURATION UPDATED")
        print("=" * 80)
        print(f"Transfer Number: {NEW_TRANSFER_NUMBER}")
        print("Transfer Type: Blind transfer (default)")
        print("Messages: Request-start and request-complete messages configured")
        print("=" * 80)

        print("\n🧪 Test the new configuration:")
        print("   curl -X POST https://api.vapi.ai/call \\")
        print("     -H \"Authorization: Bearer $VAPI_API_KEY\" \\")
        print("     -H \"Content-Type: application/json\" \\")
        print("     -d '{")
        print(f"       \"assistantId\": \"{ASSISTANT_ID}\",")
        print("       \"phoneNumberId\": \"6d828206-4eba-4668-9bb1-8c2f8045b682\",")
        print("       \"customer\": {\"number\": \"+233548139291\"}")
        print("     }'")
        print("=" * 80)

    except requests.exceptions.HTTPError as e:
        print(f"\n❌ Error updating assistant: {e}")
        print(f"Response: {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
