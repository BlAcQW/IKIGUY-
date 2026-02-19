#!/usr/bin/env python3
"""
Script to fix the Hey Papa Phone assistant transfer configuration.

This script updates the assistant with proper transferCall tool configuration
based on VAPI documentation best practices.
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv("/opt/kasaai/.env")

VAPI_API_KEY = os.getenv("VAPI_API_KEY")
ASSISTANT_ID = "1d9a82db-d70b-453b-9dd2-6844dc5af84c"
TRANSFER_NUMBER = "+233504796858"


def fix_assistant_transfer():
    """
    Fix the assistant's transferCall tool configuration.

    Returns:
        dict: Updated assistant configuration
    """
    url = f"https://api.vapi.ai/assistant/{ASSISTANT_ID}"

    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }

    # Updated configuration with proper transferCall tool
    update_payload = {
        "model": {
            "model": "gpt-4o",
            "provider": "openai",
            "maxTokens": 500,  # Increased from 150 to allow proper reasoning
            "messages": [
                {
                    "role": "system",
                    "content": """## ✅ **SYSTEM PROMPT FOR "PAPA" – ACTION CHAPEL INTERNATIONAL**

You are **Papa**, the official AI voice assistant for **Action Chapel International**. Your role is to warmly assist members, visitors, and first-timers by helping them with church-related needs and guiding them to the right support.

### **ABOUT THE CHURCH**

* Action Chapel International is a Christian charismatic church founded by **Archbishop Nicholas Duncan-Williams**.
* The ministry emphasizes prayer, spiritual growth, family, worship, covenant, and kingdom impact.

### **YOUR CORE PURPOSE**

Help callers with:

* Paying **tithes**
* Giving or **sowing seed offerings**
* Making **first fruit**, **prophetic**, and **thanksgiving** offerings
* Making a complaint
* Booking:
  * **Counselling**
  * **Weddings**
  * **Funerals**
  * **Baby dedications**
  * **House blessings**
  * **Deliverance sessions**
* Finding service times and locations
* Connecting to the right church representative

### **CONVERSATION STYLE**

* Warm, pastoral, fatherly, reassuring
* Calm and respectful tone
* Use simple, clear English (Grade 4 level)
* Keep responses short and conversational
* Never preach, argue doctrine, or offer spiritual interpretations
* No bullet points when speaking — conversational language only

### **DATA HANDLING**

* Only collect **first name**
* Never request last name, email, ID numbers, or sensitive information
* Phone number should be auto-captured from caller ID

### **WHEN TO TRANSFER**

You must **transfer the caller** when:

* They want to pay tithe or give an offering
* They request help with a financial transaction
* They want to book counselling, weddings, funerals, dedications, or other pastoral services
* They ask to speak to a church representative
* They express distress, grief, or urgent spiritual need
* They want to make a complaint

### **TRANSFER INSTRUCTIONS**

When you need to transfer:

1. Say: "I will connect you now so someone can assist you properly. Please hold on a moment."
2. Immediately use the transferCall function with destination = "+233504796858"

Example:
User: "I want to pay my tithe"
You: "I will connect you now so someone can assist you properly. Please hold on a moment."
[Use transferCall function]

### **THINGS YOU MUST NOT DO**

* Do not collect money or process payments yourself
* Do not pray, prophesy, or offer spiritual direction
* Do not give medical, legal, or financial advice
* Do not schedule events yourself
* Do not acknowledge controversy or rumors

### **GOAL OF EVERY CALL**

* Be warm and supportive
* Understand what the caller needs
* Transfer them smoothly to the responsible person
* Leave them feeling appreciated, valued, and at home
"""
                }
            ],
            "tools": [
                {
                    "type": "transferCall",
                    "destinations": [
                        {
                            "type": "number",
                            "number": TRANSFER_NUMBER,
                            "message": "Connecting you to a church representative who can help you."
                        }
                    ],
                    "function": {
                        "name": "transferCall",
                        "description": f"Use this function to transfer the call to a church representative at {TRANSFER_NUMBER}. Call this when the user needs assistance with tithes, offerings, bookings, complaints, or wants to speak to someone.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "destination": {
                                    "type": "string",
                                    "enum": [TRANSFER_NUMBER],  # FIXED: Added enum
                                    "description": f"The destination to transfer to. Must be '{TRANSFER_NUMBER}'"
                                }
                            },
                            "required": ["destination"]
                        }
                    },
                    "messages": [
                        {
                            "type": "request-start",
                            "content": "I will connect you now so someone can assist you properly. Please hold on a moment."
                        }
                    ]
                }
            ]
        },
        "firstMessage": "Hello, this is Papa's assistant. I can help you with any inquiry such as how to pay your tithe, how to book counselling sessions, how to schedule an event like a wedding, funeral, baby dedication or answer any enquiries you have. Feel free to ask me anything. This is your family church and Papa is here for you.",
        "endCallMessage": "Thank you for calling Action Chapel International. May God bless you. Goodbye."
    }

    print(f"🔧 Updating assistant {ASSISTANT_ID}...")
    print(f"   Transfer number: {TRANSFER_NUMBER}")
    print(f"   Changes:")
    print(f"   - Added enum to destination parameter")
    print(f"   - Increased maxTokens from 150 to 500")
    print(f"   - Added transfer messages for better UX")
    print(f"   - Enhanced transfer instructions in system prompt")
    print("-" * 80)

    response = requests.patch(url, headers=headers, json=update_payload)
    response.raise_for_status()

    return response.json()


def main():
    """Main execution function."""
    try:
        result = fix_assistant_transfer()

        print("\n✅ Assistant updated successfully!")
        print("\n📋 Updated Configuration:")
        print(json.dumps(result, indent=2))

        print("\n" + "=" * 80)
        print("✅ FIXES APPLIED:")
        print("=" * 80)
        print("1. ✅ Added enum array to destination parameter")
        print(f"      enum: ['{TRANSFER_NUMBER}']")
        print("2. ✅ Increased maxTokens from 150 to 500")
        print("      Allows better reasoning about when to transfer")
        print("3. ✅ Added transfer messages")
        print("      Better UX with request-start message")
        print("4. ✅ Enhanced system prompt")
        print("      Clear examples of when to use transferCall")
        print("=" * 80)

        print("\n🧪 Test the fix:")
        print(f"   Run: python3 scripts/test_call_transfer_live.py")
        print(f"   Or use curl to initiate a test call")
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
