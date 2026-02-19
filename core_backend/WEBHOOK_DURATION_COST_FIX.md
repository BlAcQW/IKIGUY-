# VAPI Webhook Duration & Cost Extraction Fix

## Issue
The end-of-call-report webhook was not properly extracting call duration and cost from VAPI webhooks, resulting in `duration=0s, cost=$0` for all calls in campaign statistics.

## Root Causes

### 1. Incorrect Call Data Extraction
**Problem:** Code was looking for call data in `message.call` but VAPI sends it at the top level in `request.call` for end-of-call-report events.

**Original code:**
```python
call_data = message_data.get("call", {}) if message_data else (request.call or {})
```

**Fixed code:**
```python
call_data = request.call or {}  # Call data is at top level for end-of-call-report
```

**File:** `core_backend/backend/routes/integration_webhooks.py:1224`

### 2. Incorrect Duration Field Names
**Problem:** Code was looking for non-existent fields `duration` or `durationSeconds`.

**According to VAPI docs (2025):**
- Duration is NOT provided as a direct field
- Must be calculated from `startedAt` and `endedAt` timestamps
- Timestamps are ISO 8601 format strings

**Original code:**
```python
duration = call_data.get("duration") or call_data.get("durationSeconds") or 0
cost = call_data.get("cost") or call_data.get("costUsd") or 0
```

**Fixed code:**
```python
started_at = call_data.get("startedAt")
ended_at = call_data.get("endedAt")

duration = 0
if started_at and ended_at:
    try:
        from dateutil import parser
        start_time = parser.parse(started_at)
        end_time = parser.parse(ended_at)
        duration = int((end_time - start_time).total_seconds())
    except Exception as e:
        logger.warning(f"⚠️ Could not calculate duration from timestamps: {e}")

# Cost uses the correct field name
cost = call_data.get("cost", 0)
cost_breakdown = call_data.get("costBreakdown", {})
```

**File:** `core_backend/backend/routes/integration_webhooks.py:1437-1461`

## VAPI Webhook Field Reference

### Call Object Fields (2025)
Based on official VAPI documentation:

**Timestamps:**
- `createdAt` - When call was created
- `updatedAt` - When call was last updated
- `startedAt` - When call actually started (may be `null` if call never connected)
- `endedAt` - When call ended (may be `null` if call never connected)

**Cost Fields:**
- `cost` - Total cost in USD (number)
- `costBreakdown` - Detailed breakdown object with:
  - `transport` - Telephony costs
  - `stt` - Speech-to-text costs
  - `llm` - Language model costs
  - `tts` - Text-to-speech costs
  - `vapi` - Platform fees
  - `total` - Total cost
  - `llmPromptTokens`, `llmCompletionTokens`, `ttsCharacters`
  - `analysisCostBreakdown` - Analysis costs

**Status Fields:**
- `status` - Call status (queued, ringing, in-progress, forwarding, ended)
- `endedReason` - Why call ended (customer-busy, customer-did-not-answer, assistant-error, etc.)

## Organization ID Format
**Confirmed:** We correctly use the UUID `id` field (not MongoDB `_id`) for `organization_id` in:
- Call metadata
- Campaign calls collection
- Automation calls collection

**Example:**
- MongoDB `_id`: `ObjectId('68fe1506328a480434807cb0')` ❌ NOT used
- UUID `id`: `'5f0d1b87-2d41-469c-9e73-207d2328bb0f'` ✅ Used correctly

This ensures cross-system compatibility with Supabase and other services.

## Testing Results

### Test Call 1 (ID: 019aa9a8-58f6-7557-a1ba-bb35a95ffcac)
- **Status:** customer-busy (call never connected)
- **Expected behavior:** `startedAt=None`, `endedAt=None`, `duration=0`, `cost=0`
- **Actual result:** ✅ Correctly logged with `duration=0s, cost=$0`
- **Debug logs showed:**
  ```
  ⚠️ Timestamps: startedAt=None, endedAt=None
  ⚠️ Cost breakdown: None
  ⚠️ Call 019aa9a8-58f6-7557-a1ba-bb35a95ffcac has duration=0s, cost=$0 - webhook may not have complete data
  ```

### What This Means
For calls that never connect (customer-busy, no-answer), VAPI correctly does NOT populate `startedAt`/`endedAt` timestamps since the call never actually started. These calls have `cost=0` which is expected.

For successful calls that do connect, VAPI will populate:
- `startedAt` - When recipient answered
- `endedAt` - When call disconnected
- `cost` - Actual cost based on duration and services used

## Next Steps

To fully verify the fix works for successful calls:

1. **Make a successful test call** that actually connects and has a conversation
2. **Verify the webhook captures:**
   - Non-zero `startedAt` and `endedAt` timestamps
   - Calculated `duration` in seconds
   - Non-zero `cost` value
   - Properly saved to `campaign_calls` collection

3. **Check frontend campaign summary** shows correct:
   - Total calls
   - Average duration
   - Total cost
   - Cost breakdown

## Files Modified

1. `/opt/kasaai/apps/core_backend/backend/routes/integration_webhooks.py`
   - Line 1224: Fixed call data extraction for end-of-call-report
   - Lines 1437-1461: Fixed duration and cost extraction using correct VAPI field names
   - Added comprehensive debug logging for troubleshooting

## Sources
- [VAPI Get Call API](https://docs.vapi.ai/api-reference/calls/get) - Call object schema
- [VAPI Server Events](https://docs.vapi.ai/server-url/events) - Webhook event types
- [VAPI Call Duration Discussion](https://vapi.ai/community/m/1377970440441692293) - Community thread on duration fields
- [VAPI Create Call API](https://docs.vapi.ai/api-reference/calls/create) - Call creation and response format

## Date
2025-11-22 04:43 CET

## Status
✅ **Fixed and deployed** - Webhook correctly extracts duration and cost when available
⏳ **Pending verification** - Needs successful call test to verify non-zero values are captured correctly
