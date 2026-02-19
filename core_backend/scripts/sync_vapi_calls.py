#!/usr/bin/env python3
"""
Sync VAPI Call Logs Script

This script:
1. Removes duplicate call logs from vapi_calls collection (keeps latest)
2. Iterates campaign_calls and fetches call data from VAPI API
3. Upserts the data into vapi_calls collection

Usage:
    python scripts/sync_vapi_calls.py
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from pymongo import MongoClient
from dateutil import parser as date_parser

# Configuration
VAPI_API_KEY = "42cf1e7c-2ef9-4bd7-ba30-52f2813605a2"
MONGODB_URL = "mongodb://admin:aawwER4444%25@127.0.0.1:27017/kasaai_core?authSource=admin"
BATCH_SIZE = 100
RATE_LIMIT_DELAY = 0.5  # seconds between API calls (increased for rate limiting)
MAX_RETRIES = 5  # max retries on rate limit
BACKOFF_MULTIPLIER = 2  # exponential backoff multiplier


def get_mongodb_connection():
    """Connect to MongoDB."""
    client = MongoClient(MONGODB_URL)
    db = client["kasaai_core"]
    return db


def remove_duplicates(db):
    """
    Remove duplicate call logs from vapi_calls collection.
    Keeps the latest record for each call_id.
    """
    print("\n=== Step 1: Removing duplicates from vapi_calls ===")

    vapi_calls = db["vapi_calls"]

    # Find duplicates
    pipeline = [
        {"$group": {
            "_id": "$call_id",
            "count": {"$sum": 1},
            "ids": {"$push": "$_id"},
            "dates": {"$push": "$created_at"}
        }},
        {"$match": {"count": {"$gt": 1}}}
    ]

    duplicates = list(vapi_calls.aggregate(pipeline))
    print(f"Found {len(duplicates)} call_ids with duplicates")

    total_removed = 0
    for dup in duplicates:
        call_id = dup["_id"]
        ids = dup["ids"]

        # Get all records for this call_id with their timestamps
        records = list(vapi_calls.find({"call_id": call_id}).sort("updated_at", -1))

        if len(records) > 1:
            # Keep the first one (most recent), delete the rest
            ids_to_delete = [r["_id"] for r in records[1:]]
            result = vapi_calls.delete_many({"_id": {"$in": ids_to_delete}})
            total_removed += result.deleted_count

    print(f"Removed {total_removed} duplicate records")

    # Verify
    total_after = vapi_calls.count_documents({})
    print(f"Total records in vapi_calls after cleanup: {total_after}")

    return total_removed


def fetch_vapi_call(call_id: str) -> dict:
    """Fetch a single call from VAPI API with retry logic for rate limits."""
    url = f"https://api.vapi.ai/call/{call_id}"
    headers = {"Authorization": f"Bearer {VAPI_API_KEY}"}

    retry_delay = RATE_LIMIT_DELAY
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                return json.loads(response.text, strict=False)
            elif response.status_code == 404:
                return None
            elif response.status_code == 429:
                # Rate limited - exponential backoff
                retry_delay = min(retry_delay * BACKOFF_MULTIPLIER, 60)  # Max 60s
                if attempt < MAX_RETRIES - 1:
                    print(f"  Rate limited on {call_id}, waiting {retry_delay:.1f}s (attempt {attempt + 1}/{MAX_RETRIES})")
                    time.sleep(retry_delay)
                    continue
                else:
                    print(f"  Max retries exceeded for {call_id}")
                    return None
            else:
                print(f"  Error fetching {call_id}: {response.status_code}")
                return None
        except Exception as e:
            print(f"  Exception fetching {call_id}: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(retry_delay)
                continue
            return None
    return None


def transform_vapi_to_local(vapi_data: dict, campaign_call: dict = None) -> dict:
    """Transform VAPI API response to local vapi_calls schema."""

    # Extract metadata
    metadata = vapi_data.get("metadata", {})

    # Calculate duration from timestamps
    duration = 0
    started_at = vapi_data.get("startedAt")
    ended_at = vapi_data.get("endedAt")
    if started_at and ended_at:
        try:
            start = date_parser.parse(started_at)
            end = date_parser.parse(ended_at)
            duration = int((end - start).total_seconds())
        except:
            pass

    # Determine status
    ended_reason = vapi_data.get("endedReason", "")
    status = "completed"
    if ended_reason in ["customer-did-not-answer", "customer-busy", "voicemail",
                        "voicemail-reached", "no-answer", "silence-timed-out"]:
        status = "no_answer"
    elif "error" in ended_reason.lower() or ended_reason in ["error", "failed", "assistant-error"]:
        status = "failed"

    # Get customer phone
    customer = vapi_data.get("customer", {})
    customer_phone = customer.get("number", "")

    # Get artifact data
    artifact = vapi_data.get("artifact", {})

    # Build local record
    record = {
        "call_id": vapi_data.get("id"),
        "organization_id": metadata.get("organization_id") or (campaign_call.get("organization_id") if campaign_call else None),
        "automation_id": metadata.get("automation_id") or (campaign_call.get("automation_id") if campaign_call else None),
        "campaign_id": metadata.get("campaign_id") or (campaign_call.get("campaign_id") if campaign_call else None),
        "assistant_id": vapi_data.get("assistantId"),
        "phone_id": vapi_data.get("phoneNumberId"),
        "customer_phone": customer_phone,
        "status": status,
        "ended_reason": ended_reason,
        "duration": duration,
        "cost": vapi_data.get("cost", 0),
        "transcript": vapi_data.get("transcript", ""),
        "summary": vapi_data.get("summary") or (vapi_data.get("analysis", {}).get("summary", "")),
        "recording_url": vapi_data.get("recordingUrl") or artifact.get("recordingUrl"),
        "stereo_recording_url": vapi_data.get("stereoRecordingUrl") or artifact.get("stereoRecordingUrl"),
        "messages": vapi_data.get("messages", [])[:50],  # Limit messages
        "started_at": started_at,
        "ended_at": ended_at,
        "cost_breakdown": vapi_data.get("costBreakdown", {}),
        "metadata": metadata,
        "vapi_status": vapi_data.get("status"),
        "vapi_type": vapi_data.get("type"),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "synced_from_vapi": True,
        "synced_at": datetime.utcnow()
    }

    return record


def sync_from_campaign_calls(db):
    """
    Iterate campaign_calls and sync missing calls from VAPI.
    """
    print("\n=== Step 2: Syncing calls from VAPI API ===")

    campaign_calls = db["campaign_calls"]
    vapi_calls = db["vapi_calls"]

    # Get all unique call_ids from campaign_calls
    all_campaign_call_ids = campaign_calls.distinct("call_id")
    print(f"Total unique call_ids in campaign_calls: {len(all_campaign_call_ids)}")

    # Get existing call_ids in vapi_calls
    existing_call_ids = set(vapi_calls.distinct("call_id"))
    print(f"Existing call_ids in vapi_calls: {len(existing_call_ids)}")

    # Find missing call_ids
    missing_call_ids = [cid for cid in all_campaign_call_ids if cid and cid not in existing_call_ids]
    print(f"Missing call_ids to sync: {len(missing_call_ids)}")

    # Also get call_ids that exist but may need updating (have no cost or duration)
    incomplete_calls = list(vapi_calls.find({
        "$or": [
            {"cost": {"$in": [None, 0]}},
            {"duration": {"$in": [None, 0]}},
            {"transcript": {"$in": [None, ""]}}
        ],
        "call_id": {"$in": all_campaign_call_ids}
    }, {"call_id": 1}))
    incomplete_call_ids = [c["call_id"] for c in incomplete_calls]
    print(f"Incomplete call_ids to update: {len(incomplete_call_ids)}")

    # Combine missing and incomplete
    call_ids_to_sync = list(set(missing_call_ids + incomplete_call_ids))
    print(f"Total call_ids to sync/update: {len(call_ids_to_sync)}")

    if not call_ids_to_sync:
        print("Nothing to sync!")
        return 0, 0

    # Process in batches
    synced = 0
    failed = 0
    consecutive_rate_limits = 0
    current_delay = RATE_LIMIT_DELAY

    for i, call_id in enumerate(call_ids_to_sync):
        if i > 0 and i % 50 == 0:
            print(f"Progress: {i}/{len(call_ids_to_sync)} ({synced} synced, {failed} failed, delay={current_delay:.1f}s)")
            # Save progress periodically
            sys.stdout.flush()

        # Fetch from VAPI
        vapi_data = fetch_vapi_call(call_id)

        if vapi_data:
            # Get campaign_call data for additional context
            campaign_call = campaign_calls.find_one({"call_id": call_id})

            # Transform and upsert
            record = transform_vapi_to_local(vapi_data, campaign_call)

            vapi_calls.update_one(
                {"call_id": call_id},
                {"$set": record},
                upsert=True
            )
            synced += 1
            consecutive_rate_limits = 0
            # Gradually decrease delay on success (min 0.5s)
            current_delay = max(RATE_LIMIT_DELAY, current_delay * 0.95)
        else:
            failed += 1
            consecutive_rate_limits += 1
            # Increase delay on failure
            if consecutive_rate_limits >= 3:
                current_delay = min(current_delay * 1.5, 30)
                print(f"  Increasing delay to {current_delay:.1f}s after {consecutive_rate_limits} consecutive failures")
                consecutive_rate_limits = 0

        # Rate limiting
        time.sleep(current_delay)

    print(f"\nSync complete: {synced} synced, {failed} failed")
    return synced, failed


def main():
    print("=" * 60)
    print("VAPI Call Logs Sync Script")
    print("=" * 60)

    # Connect to MongoDB
    db = get_mongodb_connection()

    # Step 1: Remove duplicates
    duplicates_removed = remove_duplicates(db)

    # Step 2: Sync from VAPI
    synced, failed = sync_from_campaign_calls(db)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Duplicates removed: {duplicates_removed}")
    print(f"Calls synced from VAPI: {synced}")
    print(f"Calls failed to sync: {failed}")

    # Final counts
    vapi_calls = db["vapi_calls"]
    campaign_calls = db["campaign_calls"]
    print(f"\nFinal counts:")
    print(f"  vapi_calls: {vapi_calls.count_documents({})}")
    print(f"  campaign_calls: {campaign_calls.count_documents({})}")


if __name__ == "__main__":
    main()
