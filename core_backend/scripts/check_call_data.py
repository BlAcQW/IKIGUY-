#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.mongo import get_collection

async def main():
    vapi_calls = get_collection("vapi_calls")

    # Find one call with the phone number
    call = await vapi_calls.find_one({"from_phone": "+233244868395"})

    if call:
        print("Found call:")
        print(f"  call_id: {call.get('call_id')}")
        print(f"  from_phone: {call.get('from_phone')}")
        print(f"  to_phone: {call.get('to_phone')}")
        print(f"  assistant_id: {call.get('assistant_id')}")
        print(f"  duration: {call.get('duration')}")
        print(f"  call_duration: {call.get('call_duration')}")
        print(f"  cost: {call.get('cost')}")
        print(f"  status: {call.get('status')}")
        print(f"  ended_reason: {call.get('ended_reason')}")
        print(f"  start_time: {call.get('start_time')}")
        print(f"  created_at: {call.get('created_at')}")
    else:
        print("No call found with that phone number")

    # Also check total counts
    total = await vapi_calls.count_documents({})
    with_duration = await vapi_calls.count_documents({"duration": {"$gt": 0}})
    with_call_duration = await vapi_calls.count_documents({"call_duration": {"$gt": 0}})
    with_cost = await vapi_calls.count_documents({"cost": {"$gt": 0}})

    print(f"\nTotal vapi_calls: {total}")
    print(f"With duration > 0: {with_duration}")
    print(f"With call_duration > 0: {with_call_duration}")
    print(f"With cost > 0: {with_cost}")

if __name__ == "__main__":
    asyncio.run(main())
