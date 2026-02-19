#!/usr/bin/env python3
"""
Fix AETF Assistant email function usage
Updates the system prompt to include clear instructions on how to use send_notification_email
"""

import requests
import json

VAPI_API_KEY = "42cf1e7c-2ef9-4bd7-ba30-52f2813605a2"
ASSISTANT_ID = "e88d3ca9-4cc8-49be-bb42-36c9b8dae6ef"

# Enhanced tool instructions
TOOL_INSTRUCTIONS = """

📧 **Email Tool Usage (IMPORTANT)**

Function: send_notification_email

**When to use**: When a user requests information to be sent to their email.

**Required Steps**:
1. Ask user for their email address
2. Ask them to spell it letter by letter to ensure accuracy
3. Confirm the email address back to them
4. After confirmation, prepare a comprehensive summary/message
5. Call the function with ALL required parameters

**Function Parameters** (ALL REQUIRED):
- `to_email`: The user's confirmed email address (e.g., "alfred.anyan@gmail.com")
- `subject`: A clear, descriptive subject line (e.g., "AETF AI 2025 Conference Summary")
- `message`: The full content to send (conference details, summary, etc.)
- `customer_name`: User's name if provided, otherwise "Guest"

**Example Usage**:
```
User: "Send me a summary to alfred.anyan@gmail.com"

Assistant should:
1. Confirm: "Let me confirm - alfred dot anyan at gmail dot com, is that correct?"
2. After confirmation, call function with:
   {
     "to_email": "alfred.anyan@gmail.com",
     "subject": "AETF AI 2025 Conference Summary",
     "message": "Dear Guest,\\n\\nHere's your requested summary of the AETF AI 2025 Conference:\\n\\n[Include full conference details, schedule, speakers, etc.]",
     "customer_name": "Alfred"  // if name was mentioned
   }
```

**CRITICAL**: Always include the actual email address, subject, and message content when calling the function. Never call it with empty parameters.

**What to include in email message**:
- Conference overview (name, date, venue, theme)
- Key speakers and dignitaries
- Session schedule with times
- AETF mission and goals
- Contact information
- Any specific details the user requested

**After sending**: Confirm to user that the email has been sent successfully."""

def get_current_assistant():
    """Get current assistant configuration"""
    url = f"https://api.vapi.ai/assistant/{ASSISTANT_ID}"
    headers = {"Authorization": f"Bearer {VAPI_API_KEY}"}

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def update_assistant_prompt(current_system_prompt):
    """Update assistant with enhanced email tool instructions"""

    # Find where to insert the tool instructions
    # Insert before "💡 Behavior Rules" section
    if "💡 Behavior Rules" in current_system_prompt:
        parts = current_system_prompt.split("💡 Behavior Rules")
        enhanced_prompt = parts[0] + TOOL_INSTRUCTIONS + "\n\n💡 Behavior Rules" + parts[1]
    else:
        # If section not found, append at the end
        enhanced_prompt = current_system_prompt + "\n\n" + TOOL_INSTRUCTIONS

    # Update assistant
    url = f"https://api.vapi.ai/assistant/{ASSISTANT_ID}"
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": {
            "provider": "openai",
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "system",
                    "content": enhanced_prompt
                }
            ]
        }
    }

    response = requests.patch(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()

def main():
    print("="*80)
    print("   AETF Assistant Email Function Fix")
    print("="*80)
    print()

    print("📥 Getting current assistant configuration...")
    assistant = get_current_assistant()
    current_prompt = assistant["model"]["messages"][0]["content"]

    print(f"✅ Assistant: {assistant['name']}")
    print(f"📝 Current prompt length: {len(current_prompt)} characters")
    print()

    print("🔧 Updating system prompt with enhanced email tool instructions...")
    updated = update_assistant_prompt(current_prompt)

    new_prompt = updated["model"]["messages"][0]["content"]
    print(f"✅ Updated prompt length: {len(new_prompt)} characters")
    print(f"📊 Added: {len(new_prompt) - len(current_prompt)} characters")
    print()

    print("="*80)
    print("✅ AETF Assistant updated successfully!")
    print("="*80)
    print()
    print("The assistant now has clear instructions on how to:")
    print("  1. Collect email addresses properly")
    print("  2. Extract parameters from conversation")
    print("  3. Call send_notification_email with ALL required parameters")
    print()
    print("Test it by asking:")
    print('  "Send me a summary of the conference to alfred.anyan@gmail.com"')
    print()

if __name__ == "__main__":
    main()
