#!/usr/bin/env python3
"""Diagnose transfer issues in VAPI calls."""
import sys
import json
import requests

def diagnose_call(call_id, api_key):
    """Diagnose call transfer."""

    response = requests.get(
        f"https://api.vapi.ai/call/{call_id}",
        headers={"Authorization": f"Bearer {api_key}"}
    )

    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return

    data = response.json()

    print("=" * 70)
    print("TRANSFER DIAGNOSTICS")
    print("=" * 70)
    print()

    print(f"Call ID: {data.get('id')}")
    print(f"Status: {data.get('status')}")
    print(f"End Reason: {data.get('endedReason')}")
    print(f"Duration: {data.get('duration')} seconds")
    print(f"Cost: ${data.get('cost')}")
    print()

    # Check for transfers
    artifact = data.get("artifact", {})
    transfers = artifact.get("transfers", [])
    print(f"Transfers in Artifact: {len(transfers)}")

    if transfers:
        for i, transfer in enumerate(transfers, 1):
            print(f"\n  Transfer #{i}:")
            print(f"    To: {transfer.get('toNumber', transfer.get('destination', 'Unknown'))}")
            print(f"    Status: {transfer.get('status', 'Unknown')}")
    else:
        print("  ❌ No transfers recorded")

    print()

    # Look for tool calls in messages
    messages = data.get("messages", [])
    tool_call_found = False

    print("Message Flow:")
    for msg in messages:
        role = msg.get("role")

        if role == "tool_calls":
            tool_call_found = True
            print(f"\n  ✅ TOOL CALL DETECTED:")
            tool_calls = msg.get("toolCalls", [])
            for tc in tool_calls:
                func = tc.get("function", {})
                print(f"    Function: {func.get('name')}")
                print(f"    Arguments: {func.get('arguments')}")

        elif role == "tool_call_result":
            print(f"\n  📋 TOOL RESULT:")
            print(f"    Name: {msg.get('name')}")
            print(f"    Result: {msg.get('result')}")

        elif role in ["bot", "user"]:
            content = msg.get("message", "")[:80]
            print(f"    {role}: {content}...")

    if not tool_call_found:
        print("\n  ❌ NO TOOL CALLS FOUND - Transfer function was not invoked by AI")
        print("     This means the AI didn't recognize the need to transfer")

    print()
    print("=" * 70)
    print("DIAGNOSIS:")
    print("=" * 70)

    # Diagnosis
    if data.get("endedReason") == "assistant-forwarded-call":
        if not tool_call_found:
            print("❌ Issue: Call ended as 'forwarded' but no tool call was made")
            print("   Possible causes:")
            print("   1. AI model didn't invoke transferCall function")
            print("   2. Tool configuration may not be properly set")
            print("   3. System prompt may need adjustment")
        elif len(transfers) == 0:
            print("❌ Issue: Tool call was made but transfer didn't complete")
            print("   Possible causes:")
            print("   1. Destination number didn't answer")
            print("   2. VAPI couldn't route the call")
            print("   3. Network/carrier issue")
        else:
            print("✅ Transfer was attempted and recorded")
            print(f"   Status: {transfers[0].get('status', 'Unknown')}")

    print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 diagnose_transfer.py <call_id>")
        sys.exit(1)

    CALL_ID = sys.argv[1]
    API_KEY = "42cf1e7c-2ef9-4bd7-ba30-52f2813605a2"

    diagnose_call(CALL_ID, API_KEY)
