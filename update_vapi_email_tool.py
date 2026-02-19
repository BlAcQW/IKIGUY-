#!/usr/bin/env python3
"""
Update VAPI email tool with more explicit parameter descriptions
to help GPT-4o extract them from conversation
"""

import requests
import json

VAPI_API_KEY = "42cf1e7c-2ef9-4bd7-ba30-52f2813605a2"
TOOL_ID = "abc528ae-e1f1-4e9c-a939-bc859e5e7d88"

# Enhanced function definition with very explicit parameter extraction hints
enhanced_function = {
    "type": "function",
    "function": {
        "name": "send_notification_email",
        "description": "Send email notification with conference summary or requested information. CRITICAL: Extract ALL parameters from the conversation - the recipient's email address, a descriptive subject, and the full message content.",
        "parameters": {
            "type": "object",
            "properties": {
                "to_email": {
                    "type": "string",
                    "description": "REQUIRED: The recipient's email address that they spelled out in the conversation (e.g., 'alfred.anyan@gmail.com'). Extract this from when the user spelled their email letter by letter."
                },
                "subject": {
                    "type": "string",
                    "description": "REQUIRED: A clear subject line for the email. For conference summaries, use 'AETF AI 2025 Conference Summary'. For other requests, create an appropriate subject based on what the user requested."
                },
                "message": {
                    "type": "string",
                    "description": "REQUIRED: The full email message content. For conference summaries, include: event details, schedule, speakers, AETF mission, and contact info. For other requests, provide the information the user asked for in a well-formatted message."
                },
                "customer_name": {
                    "type": "string",
                    "description": "OPTIONAL: The user's first name if they mentioned it in the conversation. Use 'Guest' if name was not provided.",
                    "default": "Guest"
                }
            },
            "required": ["to_email", "subject", "message"]
        }
    },
    "server": {
        "url": "https://api.ailabsafrica.com/integrations/vapi-webhook"
    }
}

def update_tool():
    """Update VAPI tool with enhanced function definition"""
    url = f"https://api.vapi.ai/tool/{TOOL_ID}"
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }

    print("="*80)
    print("   Updating VAPI Email Tool")
    print("="*80)
    print()

    # Get current tool
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    current = response.json()

    print(f"✅ Current tool: {current['function']['name']}")
    print(f"📝 Current description length: {len(current['function']['description'])}")
    print()

    # Update tool
    print("🔧 Updating tool with enhanced parameter descriptions...")
    response = requests.patch(url, headers=headers, json=enhanced_function)
    response.raise_for_status()
    updated = response.json()

    print(f"✅ Updated description length: {len(updated['function']['description'])}")
    print()

    print("="*80)
    print("✅ Tool updated successfully!")
    print("="*80)
    print()
    print("Enhanced parameter descriptions now include:")
    print("  - Explicit extraction hints (e.g., 'Extract from when user spelled...')")
    print("  - Example values in descriptions")
    print("  - Context about what content to include")
    print("  - Clear marking of REQUIRED vs OPTIONAL")
    print()
    print("The tool should now be better at extracting parameters from conversation.")
    print()

if __name__ == "__main__":
    update_tool()
