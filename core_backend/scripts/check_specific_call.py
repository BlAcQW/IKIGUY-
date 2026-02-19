#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.mongo import get_collection

async def main():
    vapi_calls = get_collection("vapi_calls")

    # Find calls with this assistant_id that are showing N/A
    calls = await vapi_calls.find(
        {"assistant_id": "cde22a1e-1247-42bb-8c15-1df608c28798"}
    ).limit(3).to_list(3)

    if calls:
        print(f"Found {len(calls)} calls with assistant_id cde22a1e-1247-42bb-8c15-1df608c28798")
        for i, call in enumerate(calls, 1):
            print(f"\nCall {i}:")
            print(f"  _id: {call.get('_id')}")
            print(f"  call_id: {call.get('call_id')}")
            print(f"  from_phone: {call.get('from_phone')}")
            print(f"  to_phone: {call.get('to_phone')}")
            print(f"  assistant_id: {call.get('assistant_id')}")
            print(f"  duration: {call.get('duration')}")
            print(f"  call_duration: {call.get('call_duration')}")
            print(f"  cost: {call.get('cost')}")
            print(f"  status: {call.get('status')}")
            print(f"  ended_reason: {call.get('ended_reason')}")
            print(f"  created_at: {call.get('created_at')}")

        # Check if these exist in automation_calls
        automation_calls = get_collection("automation_calls")
        first_call_id = calls[0].get('call_id')
        if first_call_id:
            auto_call = await automation_calls.find_one({"call_id": first_call_id})
            if auto_call:
                print(f"\n✅ Found in automation_calls:")
                print(f"  duration: {auto_call.get('duration')}")
                print(f"  vapi_cost: {auto_call.get('vapi_cost')}")
                print(f"  status: {auto_call.get('status')}")
                print(f"  ended_reason: {auto_call.get('ended_reason')}")
            else:
                print(f"\n❌ NOT found in automation_calls")
    else:
        print("No calls found with that assistant_id")

if __name__ == "__main__":
    asyncio.run(main())
