#!/usr/bin/env python3
"""
Script to fix VAPI assistant transfer configuration.

This script updates the assistant to include the transferCall tool
which is required for call transfers to work properly.
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv("/opt/kasaai/.env")

VAPI_API_KEY = os.getenv("VAPI_API_KEY")
ASSISTANT_ID = "c2854d74-dafe-445c-8c34-1326c2310cb7"
TRANSFER_NUMBER = "+233548480355"  # Final transfer destination (tested and verified)

def update_assistant_with_transfer_tool():
    """
    Update the VAPI assistant to include transferCall tool.

    Returns:
        dict: Updated assistant configuration
    """
    url = f"https://api.vapi.ai/assistant/{ASSISTANT_ID}"

    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }

    # Configuration with transferCall tool
    update_payload = {
        "model": {
            "model": "gpt-4o",
            "provider": "openai",
            "maxTokens": 150,
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

You must **transfer the caller** by calling the transferCall function when:

* They want to pay tithe or give an offering
* They request help with a financial transaction
* They want to book counselling, weddings, funerals, dedications, or other pastoral services
* They ask to speak to a church representative
* They express distress, grief, or urgent spiritual need
* They want to make a complaint

### **TRANSFER INSTRUCTIONS**

When transferring, say:

> I will connect you now so someone can assist you properly. Please hold on a moment.

Then immediately call the **transferCall** function with the destination parameter.

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
                    "messages": [
                        {
                            "type": "request-start",
                            "content": "I will connect you now so someone can assist you properly. Please hold on a moment."
                        }
                    ],
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
                                    "description": f"The destination to transfer to. Must be '{TRANSFER_NUMBER}'"
                                }
                            },
                            "required": ["destination"]
                        }
                    }
                }
            ]
        }
    }

    response = requests.patch(url, headers=headers, json=update_payload)
    response.raise_for_status()

    return response.json()

def main():
    """Main execution function."""
    print(f"Updating VAPI assistant {ASSISTANT_ID}...")
    print(f"Adding transferCall tool with destination: {TRANSFER_NUMBER}")

    try:
        result = update_assistant_with_transfer_tool()
        print("\n✅ Assistant updated successfully!")
        print("\nUpdated configuration:")
        print(json.dumps(result, indent=2))

        print("\n📋 Summary of changes:")
        print("- Added transferCall tool to model.tools")
        print(f"- Configured transfer destination: {TRANSFER_NUMBER}")
        print("- Updated system prompt to use transferCall function")
        print("- Added transfer messages for better UX")

    except requests.exceptions.HTTPError as e:
        print(f"\n❌ Error updating assistant: {e}")
        print(f"Response: {e.response.text}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
