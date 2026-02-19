# Campaign Organization Filtering Fix - Verification Guide

## Summary
Fixed issue where campaign calls were not appearing in campaign summary and `/call-logs` page due to missing `organization_id` filtering.

## Changes Made

### 1. Campaign Call Records (`campaign_execution_service.py`)
- **Added `organization_id` parameter** to `_create_campaign_call_record()`
- **Store `organization_id`** when creating campaign call records
- **Pass `campaign.organization_id`** when creating calls during campaign execution

### 2. Campaign Calls Retrieval (`campaign_execution_service.py`)
- **Added `organization_id` parameter** to `get_campaign_calls()`
- **Filter campaign calls by `organization_id`** for proper multi-tenant isolation

### 3. Endpoint Update (`automation_configs.py`)
- **Extract `organization_id`** from automation config or request context
- **Pass `organization_id`** to service method for filtering

### 4. Webhook Error Handling (`campaign_execution_service.py`)
- **Added fallback lookup** in `update_call_outcome()` if primary lookup fails
- **Improved logging** for debugging webhook processing

## Testing Steps

### 1. Restart Core Backend Service
```bash
sudo systemctl restart kasaai-core-backend.service
sudo systemctl status kasaai-core-backend.service
```

### 2. Verify Campaign Calls Have organization_id
```bash
# Connect to MongoDB
mongosh

# Check campaign calls collection
use kasaai
db.campaign_calls.find({campaign_id: "YOUR_CAMPAIGN_ID"}).pretty()
# Should see "organization_id" field in recent records
```

### 3. Test Campaign Summary Endpoint
```bash
# Replace with actual values
AUTOMATION_ID="your_automation_id"
CAMPAIGN_ID="your_campaign_id"
ORG_ID="action-chapel-international"  # or your org ID
TOKEN="your_auth_token"

curl -X GET \
  "http://localhost:30027/api/automation-configs/${AUTOMATION_ID}/campaigns/${CAMPAIGN_ID}/calls?page=1&limit=100" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "X-Organization-ID: ${ORG_ID}" \
  | jq '.'
```

### 4. Test Call Logs Endpoint
```bash
curl -X GET \
  "http://localhost:30027/api/call-logs?page=1&per_page=20" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "X-Organization-ID: ${ORG_ID}" \
  | jq '.'
```

### 5. Verify Frontend Display
1. Open b2c-portal in browser
2. Navigate to campaign management
3. Open campaign summary for "hetty_test" campaign
4. Verify calls appear in the summary
5. Navigate to `/call-logs` page
6. Verify calls appear filtered by organization

## Expected Results

### Before Fix
- ❌ Campaign summary shows no calls
- ❌ `/call-logs` page shows no calls (or shows calls from wrong organization)
- ❌ Campaign call records missing `organization_id` field

### After Fix
- ✅ Campaign summary shows all calls for the campaign
- ✅ `/call-logs` page shows calls filtered by organization
- ✅ Campaign call records include `organization_id` field
- ✅ Proper multi-tenant isolation

## Debugging

### Check Campaign Call Records
```javascript
// MongoDB query
db.campaign_calls.find({
  campaign_id: "YOUR_CAMPAIGN_ID",
  organization_id: { $exists: true }
}).count()
```

### Check VAPI Calls Collection
```javascript
db.vapi_calls.find({
  "metadata.campaign_id": "YOUR_CAMPAIGN_ID",
  organization_id: "YOUR_ORG_ID"
}).pretty()
```

### Check Backend Logs
```bash
sudo journalctl -u kasaai-core-backend.service -f
# Look for:
# - "Campaign call record created" with organization_id
# - "Getting campaign calls for organization:"
# - Webhook processing logs
```

## Rollback Instructions

If issues occur, revert the changes:
```bash
cd /opt/kasaai
git revert HEAD
sudo systemctl restart kasaai-core-backend.service
```

## Files Modified
1. `apps/core_backend/backend/services/campaign_execution_service.py`
2. `apps/core_backend/backend/routes/automation_configs.py`


