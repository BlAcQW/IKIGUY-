"""
List All Voice Assistants

This example demonstrates how to retrieve a list of all your voice assistants.
"""

import os
import requests
from typing import List, Dict


# Configuration
API_KEY = os.getenv("KASAAI_API_KEY", "your_api_key_here")
BASE_URL = "https://developer.ailabsafrica.com"


def list_assistants(limit: int = 10, offset: int = 0) -> List[Dict]:
    """
    List all voice assistants.

    Args:
        limit: Maximum number of assistants to return (default: 10)
        offset: Number of assistants to skip (default: 0)

    Returns:
        List[Dict]: List of assistant objects

    Raises:
        requests.HTTPError: If the API request fails
    """
    endpoint = f"{BASE_URL}/api/v1/assistants"

    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }

    params = {
        "limit": limit,
        "offset": offset
    }

    response = requests.get(endpoint, headers=headers, params=params)
    response.raise_for_status()

    return response.json()


def get_assistant(assistant_id: str) -> Dict:
    """
    Get a specific assistant by ID.

    Args:
        assistant_id: The assistant ID

    Returns:
        Dict: Assistant object

    Raises:
        requests.HTTPError: If the API request fails
    """
    endpoint = f"{BASE_URL}/api/v1/assistants/{assistant_id}"

    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }

    response = requests.get(endpoint, headers=headers)
    response.raise_for_status()

    return response.json()


def main():
    """Main function to demonstrate listing assistants."""
    try:
        # List all assistants
        print("Fetching assistants...")
        assistants = list_assistants(limit=20)

        if not assistants:
            print("No assistants found. Create one first using create_assistant.py")
            return

        print(f"\n✅ Found {len(assistants)} assistant(s):\n")

        for assistant in assistants:
            print(f"📱 {assistant['name']}")
            print(f"   ID: {assistant['id']}")
            print(f"   Status: {assistant['status']}")
            print(f"   Voice: {assistant['voice']}")
            print(f"   Language: {assistant['language']}")
            print(f"   Created: {assistant['created_at']}")
            print()

        # Example: Get a specific assistant
        if assistants:
            first_id = assistants[0]['id']
            print(f"Getting details for assistant: {first_id}")
            assistant = get_assistant(first_id)
            print(f"✅ Retrieved assistant: {assistant['name']}")

    except requests.HTTPError as e:
        print(f"❌ Error fetching assistants: {e}")
        if hasattr(e.response, 'json'):
            print(f"   Details: {e.response.json()}")
        exit(1)


if __name__ == "__main__":
    main()
