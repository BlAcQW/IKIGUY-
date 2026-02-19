#!/usr/bin/env python3
"""Check VAPI call status and details."""
import sys
import json
import requests

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 check_call_status.py <call_id>")
        sys.exit(1)

    call_id = sys.argv[1]

    # Fetch call data from VAPI
    response = requests.get(
        f"https://api.vapi.ai/call/{call_id}",
        headers={"Authorization": "Bearer 42cf1e7c-2ef9-4bd7-ba30-52f2813605a2"}
    )

    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        sys.exit(1)

    data = response.json()

    # Print call details
    print(f"Status: {data.get('status', 'N/A')}")
    print(f"End Reason: {data.get('endedReason', 'N/A')}")
    print(f"Duration: {data.get('duration', 'N/A')}s")
    print(f"Cost: ${data.get('cost', 0)}")
    print(f"Started: {data.get('startedAt', 'N/A')}")
    print(f"Ended: {data.get('endedAt', 'N/A')}")

    print("\nTranscript:")
    messages = data.get("messages", [])
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("message", msg.get("content", ""))
        if content and role != "system":
            print(f"  {role}: {content}")

    print("\nTool Calls:")
    tool_calls = data.get("artifact", {}).get("toolCalls", [])
    if tool_calls:
        for tc in tool_calls:
            name = tc.get("function", {}).get("name", "N/A")
            result = tc.get("result", "N/A")
            print(f"  - {name}: {result}")
    else:
        print("  No tool calls found")

    print(f"\nSummary: {data.get('analysis', {}).get('summary', 'N/A')}")

    # Print full artifact for debugging
    artifact = data.get("artifact", {})
    if artifact:
        print("\nFull Artifact:")
        print(json.dumps(artifact, indent=2))

if __name__ == "__main__":
    main()
