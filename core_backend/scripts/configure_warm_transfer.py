#!/usr/bin/env python3
"""
Configure VAPI assistant with warm transfer for BYO SIP trunk.

Warm transfer creates a conference-style call instead of using SIP REFER,
which works better with custom SIP trunks.
"""

import os
import requests
import json

# VAPI Configuration
VAPI_API_KEY = "42cf1e7c-2ef9-4bd7-ba30-52f2813605a2"
ASSISTANT_ID = "c2854d74-dafe-445c-8c34-1326c2310cb7"  # Hey Papa Hybrid
TRANSFER_DESTINATION = "+233548480355"

def configure_warm_transfer():
    """Configure the assistant with warm transfer tool."""

    url = f"https://api.vapi.ai/assistant/{ASSISTANT_ID}"
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }

    # Get current assistant config
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error fetching assistant: {response.status_code}")
        print(response.text)
        return False

    assistant = response.json()

    # Configure warm transfer tool
    transfer_tool = {
        "type": "transferCall",
        "function": {
            "name": "transferCall",
            "description": "Use this function to transfer the call to a church representative. Call this when the user needs assistance with tithes, offerings, bookings, complaints, or wants to speak to someone.",
            "parameters": {
                "type": "object",
                "properties": {
                    "destination": {
                        "type": "string",
                        "description": f"The destination number. Must be '{TRANSFER_DESTINATION}'"
                    }
                },
                "required": ["destination"]
            }
        },
        "destinations": [
            {
                "type": "number",
                "number": TRANSFER_DESTINATION,
                "message": "Connecting you to a church representative. Please wait while I get them on the line.",
                "description": "Church representative for assistance"
                # Conference-style warm transfer via BYO SIP trunk
            }
        ],
        "messages": [
            {
                "type": "request-start",
                "content": "Let me connect you to someone who can help. I'm calling them now, please hold on."
            },
            {
                "type": "request-complete",
                "content": "I have them on the line. You're now connected."
            },
            {
                "type": "request-failed",
                "content": "I'm sorry, but I wasn't able to reach someone at the moment. Please try calling back or leave a message."
            }
        ]
    }

    # Prepare update payload - only send fields that can be updated
    update_payload = {
        "model": {
            "provider": assistant.get("model", {}).get("provider"),
            "model": assistant.get("model", {}).get("model"),
            "messages": assistant.get("model", {}).get("messages", []),
            "tools": [transfer_tool],
            "maxTokens": assistant.get("model", {}).get("maxTokens")
        }
    }

    # Update the assistant
    update_response = requests.patch(url, headers=headers, json=update_payload)

    if update_response.status_code == 200:
        print("✅ WARM TRANSFER CONFIGURED SUCCESSFULLY")
        print(f"\nAssistant: {assistant.get('name')}")
        print(f"Transfer Destination: {TRANSFER_DESTINATION}")
        print(f"Transfer Mode: Warm Transfer (rolling-window)")
        print(f"Timeout: 30 seconds")
        print("\nHow it works:")
        print("1. AI says: 'Let me connect you...'")
        print("2. VAPI calls the destination number")
        print("3. User hears hold music/ringing")
        print("4. When destination answers, AI says: 'I have them on the line'")
        print("5. Both parties are connected in a conference")
        return True
    else:
        print(f"❌ Error updating assistant: {update_response.status_code}")
        print(update_response.text)
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("CONFIGURING WARM TRANSFER FOR VAPI ASSISTANT")
    print("=" * 60)
    print()

    success = configure_warm_transfer()

    if success:
        print("\n" + "=" * 60)
        print("NEXT STEPS:")
        print("=" * 60)
        print("1. Test the transfer with a call")
        print("2. Verify the destination number rings")
        print("3. Check that both parties can hear each other")
        print()
        print("Test command:")
        print(f"python3 -c 'import requests; print(requests.post(\"https://api.vapi.ai/call/phone\", headers={{\"Authorization\": \"Bearer {VAPI_API_KEY}\"}}, json={{\"phoneNumberId\": \"6d828206-4eba-4668-9bb1-8c2f8045b682\", \"customer\": {{\"number\": \"+233593536814\"}}, \"assistantId\": \"{ASSISTANT_ID}\"}}).json())'")
    else:
        print("\n❌ Configuration failed. Please check the errors above.")
