#!/usr/bin/env python3
"""
Enable strict mode on send_notification_email tool
This should enforce parameter extraction per VAPI docs
"""

import requests
import json

VAPI_API_KEY = "42cf1e7c-2ef9-4bd7-ba30-52f2813605a2"
TOOL_ID = "abc528ae-e1f1-4e9c-a939-bc859e5e7d88"

def enable_strict_mode():
    """Enable strict mode on the email tool"""
    url = f"https://api.vapi.ai/tool/{TOOL_ID}"
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }

    print("="*80)
    print("   Enabling Strict Mode on Email Tool")
    print("="*80)
    print()

    # Get current tool configuration
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    current = response.json()

    print(f"✅ Tool: {current['function']['name']}")
    print(f"📋 Current required params: {current['function']['parameters'].get('required', [])}")
    print(f"🔒 Strict mode: {current['function'].get('strict', 'NOT SET')}")
    print()

    # Create updated configuration with strict mode
    updated_tool = {
        "type": "function",
        "function": {
            "name": "send_notification_email",
            "description": "Send email notification using local SMTP server with advanced formatting and delivery tracking. Extract ALL parameters from the conversation.",
            "strict": True,  # KEY FIX: Enable strict mode
            "parameters": {
                "type": "object",
                "properties": {
                    "to_email": {
                        "type": "string",
                        "description": "Recipient email address that the user spelled out in the conversation"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject line. For conference summaries use 'AETF AI 2025 Conference Summary'"
                    },
                    "message": {
                        "type": "string",
                        "description": "Full email content with conference details, schedule, speakers, and contact information"
                    },
                    "customer_name": {
                        "type": "string",
                        "description": "Customer name for personalization if mentioned, otherwise use 'Guest'"
                    }
                },
                "required": ["to_email", "subject", "message"],
                "additionalProperties": False  # Strict mode requirement
            }
        },
        "server": {
            "url": "https://api.ailabsafrica.com/integrations/vapi-webhook"
        }
    }

    print("🔧 Updating tool with strict mode enabled...")
    print("   - Setting strict: true")
    print("   - Setting additionalProperties: false")
    print("   - Maintaining required: [to_email, subject, message]")
    print()

    # Use PUT to replace entire tool configuration
    response = requests.put(url, headers=headers, json=updated_tool)
    response.raise_for_status()
    result = response.json()

    print(f"✅ Updated strict mode: {result['function'].get('strict')}")
    print(f"✅ Required params: {result['function']['parameters'].get('required')}")
    print()

    print("="*80)
    print("✅ Strict mode enabled successfully!")
    print("="*80)
    print()
    print("Per VAPI docs, this should now:")
    print("  ✓ Enforce all required parameters are present")
    print("  ✓ Only allow properties defined in schema")
    print("  ✓ Prevent empty arguments {}")
    print()

if __name__ == "__main__":
    try:
        enable_strict_mode()
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ Error: {e}")
        print(f"Response: {e.response.text}")
