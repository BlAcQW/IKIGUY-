"""
Initiate an Outbound Call

This example demonstrates how to initiate an outbound call using your voice assistant.
"""

import os
import requests
import time
from typing import Dict


# Configuration
API_KEY = os.getenv("KASAAI_API_KEY", "your_api_key_here")
BASE_URL = "https://developer.ailabsafrica.com"


def initiate_call(
    assistant_id: str,
    phone_number: str,
    task: str = "outbound"
) -> Dict:
    """
    Initiate an outbound call.

    Args:
        assistant_id: The assistant ID to use for the call
        phone_number: Phone number in E.164 format (e.g., +14155552671)
        task: Call type (default: "outbound")

    Returns:
        Dict: Call object with status and details

    Raises:
        requests.HTTPError: If the API request fails
    """
    endpoint = f"{BASE_URL}/api/v1/calls"

    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "assistant_id": assistant_id,
        "phone_number": phone_number,
        "task": task
    }

    response = requests.post(endpoint, headers=headers, json=payload)
    response.raise_for_status()

    return response.json()


def get_call_status(call_id: str) -> Dict:
    """
    Get the status of a call.

    Args:
        call_id: The call ID

    Returns:
        Dict: Call status object

    Raises:
        requests.HTTPError: If the API request fails
    """
    endpoint = f"{BASE_URL}/api/v1/calls/{call_id}"

    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }

    response = requests.get(endpoint, headers=headers)
    response.raise_for_status()

    return response.json()


def monitor_call(call_id: str, max_wait: int = 60):
    """
    Monitor a call until it completes or times out.

    Args:
        call_id: The call ID to monitor
        max_wait: Maximum seconds to wait (default: 60)
    """
    print(f"\n📞 Monitoring call: {call_id}")
    start_time = time.time()

    while time.time() - start_time < max_wait:
        try:
            status = get_call_status(call_id)
            current_status = status['status']

            print(f"   Status: {current_status}")

            if current_status in ['completed', 'failed', 'busy', 'no-answer']:
                print(f"\n✅ Call ended with status: {current_status}")
                if 'duration' in status:
                    print(f"   Duration: {status['duration']} seconds")
                break

            time.sleep(3)  # Wait 3 seconds before checking again

        except requests.HTTPError as e:
            print(f"❌ Error checking call status: {e}")
            break


def main():
    """Main function to demonstrate initiating a call."""
    # Get assistant ID from command line or environment
    assistant_id = os.getenv("ASSISTANT_ID")
    phone_number = os.getenv("PHONE_NUMBER")

    if not assistant_id:
        print("❌ Error: ASSISTANT_ID environment variable not set")
        print("   Set it with: export ASSISTANT_ID=your_assistant_id")
        exit(1)

    if not phone_number:
        print("❌ Error: PHONE_NUMBER environment variable not set")
        print("   Set it with: export PHONE_NUMBER=+1234567890")
        exit(1)

    try:
        # Initiate the call
        print(f"📞 Initiating call to {phone_number}...")
        call = initiate_call(
            assistant_id=assistant_id,
            phone_number=phone_number
        )

        print("✅ Call initiated successfully!")
        print(f"   Call ID: {call['id']}")
        print(f"   Status: {call['status']}")
        print(f"   Phone: {call['phone_number']}")
        print(f"   Type: {call['type']}")

        # Monitor the call
        monitor_call(call['id'], max_wait=120)

    except requests.HTTPError as e:
        print(f"❌ Error initiating call: {e}")
        if hasattr(e.response, 'json'):
            error_detail = e.response.json()
            print(f"   Details: {error_detail}")

            # Provide helpful error messages
            if e.response.status_code == 400:
                print("\n💡 Common issues:")
                print("   - Phone number must be in E.164 format (+country_code + number)")
                print("   - Check that your assistant_id is correct")
            elif e.response.status_code == 402:
                print("\n💡 Insufficient credits. Add credits at:")
                print("   https://developer.ailabsafrica.com/billing")
            elif e.response.status_code == 429:
                print("\n💡 Rate limit exceeded. Wait a moment and try again.")
        exit(1)


if __name__ == "__main__":
    main()
