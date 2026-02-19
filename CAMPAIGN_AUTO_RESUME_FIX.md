# Campaign Auto-Resume Fix - December 6, 2025

## Issue
Campaigns with time windows (start_time/pause_time) were being auto-resumed even when `auto_start` was set to `false`. This meant that campaigns would automatically restart at the start_time regardless of user preference.

## Root Cause
The `check_and_resume_paused_campaigns()` function in `campaign_execution_service.py` was checking for paused campaigns with time windows but **not verifying the `auto_start` setting** before auto-resuming them.

## Solution Implemented

### 1. **Updated MongoDB Query** (Lines 2226-2232)
Changed the query to filter paused campaigns by `auto_start=True` at the database level:

```python
# Before:
paused_campaigns = await service.campaigns_collection.find({
    "status": "paused",
    "config.start_time": {"$exists": True, "$ne": None}
}).to_list(length=None)

# After:
paused_campaigns = await service.campaigns_collection.find({
    "status": "paused",
    "config.auto_start": True,  # ← Added this filter
    "config.start_time": {"$exists": True, "$ne": None}
}).to_list(length=None)
```

### 2. **Updated Log Messages** (Line 2266)
Enhanced logging to confirm auto_start is enabled:

```python
logger.info(f"Auto-resuming campaign {campaign_id} - start_time ({start_time_str}) reached and auto_start=True")
```

## Behavior After Fix

### ✅ With `auto_start: True`
- **Pending campaigns**: Will automatically start when `start_time` is reached
- **Paused campaigns** (due to time window): Will automatically resume when `start_time` is reached

### ❌ With `auto_start: False`
- **Pending campaigns**: Will remain pending, requiring manual start
- **Paused campaigns** (due to time window): Will remain paused, requiring manual resume
- **Manually paused campaigns**: Will never auto-resume (correct existing behavior)

## Files Modified
- `/opt/kasaai/apps/core_backend/backend/services/campaign_execution_service.py`
  - Lines 2226-2232: Updated paused campaigns query
  - Line 2241: Updated comment
  - Line 2266: Enhanced logging

## Testing Recommendations

1. **Test auto_start=True with time window:**
   - Create campaign with `auto_start: true`, `start_time: "14:00"`, `pause_time: "18:00"`
   - Verify it auto-starts at 14:00 UTC
   - Verify it auto-pauses at 18:00 UTC
   - Verify it auto-resumes at 14:00 UTC the next day

2. **Test auto_start=False with time window:**
   - Create campaign with `auto_start: false`, `start_time: "14:00"`, `pause_time: "18:00"`
   - Manually start at 15:00 UTC
   - Verify it auto-pauses at 18:00 UTC (outside calling window)
   - Verify it does NOT auto-resume at 14:00 UTC the next day
   - Verify it requires manual resume

3. **Test manual pause:**
   - Start a campaign with `auto_start: true`
   - Manually pause it via the UI
   - Verify it does NOT auto-resume at `start_time`

## Deployment Status
- ✅ Code updated: `campaign_execution_service.py`
- ✅ Service restarted: `kasaai-core-backend.service`
- ✅ Scheduler job running: "Campaign Auto-Resume" (runs every minute)
- ✅ Server: Live production (148.251.0.46)

## Related Documentation
- Frontend UI: `@b2c-portal/src/components/CampaignManagementModal.tsx`
- Auto-start checkbox: Lines 1017-1031 (create), Lines 1257-1273 (edit)
- Backend scheduler: `@core_backend/backend/main.py` Lines 285-292
