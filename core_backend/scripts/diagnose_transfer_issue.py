#!/usr/bin/env python3
"""
Script to diagnose VAPI call transfer issues.
Checks provider support, configuration, and provides recommendations.
"""
import os
import sys
import requests
import json
from typing import Dict, Any, List

# VAPI Configuration
VAPI_API_KEY = "42cf1e7c-2ef9-4bd7-ba30-52f2813605a2"
ASSISTANT_ID = "1d9a82db-d70b-453b-9dd2-6844dc5af84c"
BASE_URL = "https://api.vapi.ai"

def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def get_assistant() -> Dict[str, Any]:
    """Fetch assistant configuration."""
    response = requests.get(
        f"{BASE_URL}/assistant/{ASSISTANT_ID}",
        headers={"Authorization": f"Bearer {VAPI_API_KEY}"}
    )
    response.raise_for_status()
    return response.json()

def get_phone_numbers() -> List[Dict[str, Any]]:
    """Fetch all phone numbers."""
    response = requests.get(
        f"{BASE_URL}/phone-number",
        headers={"Authorization": f"Bearer {VAPI_API_KEY}"}
    )
    response.raise_for_status()
    return response.json()

def get_recent_calls(limit: int = 5) -> List[Dict[str, Any]]:
    """Fetch recent calls."""
    response = requests.get(
        f"{BASE_URL}/call?limit={limit}",
        headers={"Authorization": f"Bearer {VAPI_API_KEY}"}
    )
    response.raise_for_status()
    return response.json()

def diagnose_transfer_support(assistant: Dict[str, Any], phone_numbers: List[Dict[str, Any]]):
    """Diagnose call transfer support based on provider."""
    print_section("📞 PHONE PROVIDER DIAGNOSIS")

    # Find the phone number linked to this assistant
    assistant_phone = None
    phone_number_id = assistant.get("phoneNumberId")

    if phone_number_id:
        assistant_phone = next((p for p in phone_numbers if p.get("id") == phone_number_id), None)

    if not assistant_phone:
        print("❌ No phone number linked to this assistant")
        print("\nRECOMMENDATION:")
        print("  1. Purchase a phone number from a provider that supports SIP REFER")
        print("  2. Link it to your assistant")
        return

    provider = assistant_phone.get("provider", "unknown")
    number = assistant_phone.get("number", "unknown")

    print(f"Phone Number: {number}")
    print(f"Provider: {provider}")
    print()

    # Check provider compatibility
    if provider == "vapi":
        print("⚠️  ISSUE IDENTIFIED: Using VAPI's free phone numbers")
        print()
        print("ROOT CAUSE:")
        print("  • VAPI free numbers DO NOT support outbound calls")
        print("  • Call transfers require outbound calling capability")
        print("  • VAPI uses SIP REFER protocol for transfers")
        print("  • When transfer is triggered, the call drops immediately")
        print()
        print("❌ TRANSFER SUPPORT: NOT SUPPORTED")
        print()
        print("SOLUTION:")
        print("  1. Purchase a phone number from Twilio (recommended)")
        print("  2. Configure Twilio to enable SIP REFER support")
        print("  3. Link the Twilio number to your assistant")
        print()
        print("TWILIO SETUP:")
        print("  • Create Twilio account: https://www.twilio.com/try-twilio")
        print("  • Purchase a phone number with voice capabilities")
        print("  • Get your Account SID and Auth Token")
        print("  • Add to VAPI: Settings → Phone Numbers → Import from Twilio")
        print()
        return False

    elif provider == "twilio":
        print("✅ PROVIDER: Twilio (SUPPORTS SIP REFER)")
        print()
        print("VERIFICATION CHECKLIST:")
        print("  ☐ Twilio account has outbound calling enabled")
        print("  ☐ Phone number has voice capabilities")
        print("  ☐ SIP REFER is enabled on your SIP trunk")
        print("  ☐ Destination number is formatted correctly (+[country][number])")
        print()
        return True

    elif provider == "telnyx":
        print("⚠️  PROVIDER: Telnyx")
        print()
        print("NOTE:")
        print("  • Standard Telnyx accounts DO NOT support SIP REFER")
        print("  • Enterprise/commercial accounts MAY have this feature")
        print("  • Contact Telnyx support to verify your account capabilities")
        print()
        print("RECOMMENDATION:")
        print("  • Consider switching to Twilio for guaranteed SIP REFER support")
        print()
        return None

    else:
        print(f"⚠️  PROVIDER: {provider} (Unknown compatibility)")
        print()
        print("VERIFICATION NEEDED:")
        print(f"  • Contact {provider} support")
        print("  • Ask if they support SIP REFER protocol")
        print("  • Verify outbound calling is enabled")
        print()
        return None

def check_transfer_configuration(assistant: Dict[str, Any]):
    """Check transferCall tool configuration."""
    print_section("🔧 TRANSFER TOOL CONFIGURATION")

    tools = assistant.get("model", {}).get("tools", [])
    transfer_tool = next((t for t in tools if t.get("type") == "transferCall"), None)

    if not transfer_tool:
        print("❌ No transferCall tool configured")
        return

    print("✅ transferCall tool found")
    print()

    # Check function parameters
    function = transfer_tool.get("function", {})
    parameters = function.get("parameters", {})
    properties = parameters.get("properties", {})

    destination = properties.get("destination", {})

    print("Configuration:")
    print(f"  • Description: {function.get('description', 'N/A')[:100]}")
    print()

    # Check for enum
    if "enum" in destination:
        print(f"  ✅ Destination enum: {destination['enum']}")
    else:
        print("  ⚠️  No destination enum (should have one for fixed destination)")

    # Check messages
    messages = transfer_tool.get("messages", [])
    if messages:
        print(f"  ✅ Transfer messages configured: {len(messages)} message(s)")
    else:
        print("  ⚠️  No transfer messages (recommended for better UX)")

def analyze_recent_calls(calls: List[Dict[str, Any]]):
    """Analyze recent call failures."""
    print_section("📊 RECENT CALL ANALYSIS")

    if not calls:
        print("No recent calls found")
        return

    for i, call in enumerate(calls[:5], 1):
        call_id = call.get("id", "unknown")
        status = call.get("status", "unknown")
        ended_reason = call.get("endedReason", "N/A")
        provider = call.get("phoneCallProvider", "unknown")

        print(f"Call {i}: {call_id}")
        print(f"  Status: {status}")
        print(f"  Ended Reason: {ended_reason}")
        print(f"  Provider: {provider}")

        # Check for transfer attempts
        messages = call.get("messages", [])
        transfer_messages = [m for m in messages if "transfer" in str(m).lower()]

        if transfer_messages:
            print(f"  ⚠️  Transfer attempted: {len(transfer_messages)} related message(s)")

        if ended_reason == "assistant-forwarded-call":
            print("  ✅ Call was successfully forwarded")
        elif status == "ended" and not ended_reason:
            print("  ⚠️  Call ended without clear reason")
        elif status == "queued":
            print("  ⚠️  Call stuck in queue - didn't connect")

        print()

def main():
    """Main diagnostic function."""
    print_section("🔍 VAPI CALL TRANSFER DIAGNOSTIC")

    try:
        # Fetch data
        print("Fetching data from VAPI...")
        assistant = get_assistant()
        phone_numbers = get_phone_numbers()
        recent_calls = get_recent_calls()
        print("✓ Data fetched successfully\n")

        # Run diagnostics
        provider_supported = diagnose_transfer_support(assistant, phone_numbers)
        check_transfer_configuration(assistant)
        analyze_recent_calls(recent_calls)

        # Final recommendations
        print_section("📋 SUMMARY & RECOMMENDATIONS")

        if provider_supported == False:
            print("🚨 ACTION REQUIRED:")
            print("  Your current phone provider (VAPI free numbers) DOES NOT support")
            print("  call transfers. You MUST switch to a compatible provider.")
            print()
            print("IMMEDIATE STEPS:")
            print("  1. Sign up for Twilio: https://www.twilio.com/try-twilio")
            print("  2. Purchase a phone number with voice capabilities ($1/month)")
            print("  3. In VAPI dashboard: Settings → Phone Numbers → Import from Twilio")
            print("  4. Link the new number to your 'Hey Papa Phone' assistant")
            print("  5. Test the transfer functionality again")
            print()
        elif provider_supported == True:
            print("✅ Provider supports transfers!")
            print()
            print("If transfers still fail, check:")
            print("  1. Destination number is reachable")
            print("  2. Destination number format includes country code")
            print("  3. Your Twilio account has sufficient balance")
            print("  4. SIP REFER is enabled on your Twilio SIP trunk")
            print()
        else:
            print("⚠️  Provider compatibility unknown")
            print()
            print("NEXT STEPS:")
            print("  1. Contact your provider to verify SIP REFER support")
            print("  2. Consider switching to Twilio for guaranteed compatibility")
            print()

    except Exception as e:
        print(f"\n❌ Error during diagnosis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
