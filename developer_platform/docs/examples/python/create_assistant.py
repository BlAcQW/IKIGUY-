"""
Create an AI Voice Assistant

This example demonstrates how to create a new voice assistant using the KasaAI API.
The assistant can be configured with custom personality, voice, and language.
"""

import os
import requests
from typing import Optional


# Configuration
API_KEY = os.getenv("KASAAI_API_KEY", "your_api_key_here")
BASE_URL = "https://developer.ailabsafrica.com"


def create_assistant(
    name: str,
    system_prompt: str,
    voice: str = "alloy",
    language: str = "en",
    first_message: Optional[str] = None
) -> dict:
    """
    Create a new voice assistant.

    Args:
        name: Name of the assistant
        system_prompt: System prompt that defines assistant behavior
        voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
        language: Language code (en, es, fr, etc.)
        first_message: Optional greeting message

    Returns:
        dict: Created assistant data

    Raises:
        requests.HTTPError: If the API request fails
    """
    endpoint = f"{BASE_URL}/api/v1/assistants"

    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "name": name,
        "system_prompt": system_prompt,
        "voice": voice,
        "language": language
    }

    if first_message:
        payload["first_message"] = first_message

    response = requests.post(endpoint, headers=headers, json=payload)
    response.raise_for_status()

    return response.json()


def main():
    """Main function to demonstrate assistant creation."""
    try:
        # Create a customer support assistant
        assistant = create_assistant(
            name="Customer Support Bot",
            system_prompt=(
                "You are a helpful customer support assistant for TechCorp. "
                "Be friendly, professional, and solve customer issues efficiently. "
                "If you cannot solve an issue, escalate to a human agent."
            ),
            voice="alloy",
            language="en",
            first_message="Hello! I'm here to help with any questions or issues you have. How can I assist you today?"
        )

        print("✅ Successfully created assistant!")
        print(f"   ID: {assistant['id']}")
        print(f"   Name: {assistant['name']}")
        print(f"   Status: {assistant['status']}")
        print(f"   Voice: {assistant['voice']}")
        print(f"   Language: {assistant['language']}")
        print(f"   Created: {assistant['created_at']}")

    except requests.HTTPError as e:
        print(f"❌ Error creating assistant: {e}")
        if hasattr(e.response, 'json'):
            print(f"   Details: {e.response.json()}")
        exit(1)


if __name__ == "__main__":
    main()
