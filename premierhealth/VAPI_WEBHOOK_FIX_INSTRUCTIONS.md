# VAPI Webhook URL Fix Instructions

**Date:** November 7, 2025
**Issue:** query_premier_health_knowledge_base tool not working - assistants can't find providers
**Root Cause:** Incorrect webhook URL in VAPI assistant configurations (404 errors)

## Problem Summary

The VAPI assistants are calling the wrong webhook URL:
- ❌ **Current (WRONG):** `https://api.ailabsafrica.com/vapi/webhooks/premier-health`
- ✅ **Correct:** `https://api.ailabsafrica.com/premier-health/vapi-webhook`

This causes ALL function calls to fail with 404, including `query_premier_health_knowledge_base`, which is why assistants report "cannot find providers" even though 885 providers exist in the database.

## Evidence from Logs

```
Nov 07 14:55:18 ... "POST /vapi/webhooks/premier-health HTTP/1.1" 404 Not Found
Nov 07 14:55:39 ... "POST /vapi/webhooks/premier-health HTTP/1.1" 404 Not Found
```

## Step-by-Step Fix Instructions

### Step 1: Access VAPI Dashboard
1. Go to https://vapi.ai
2. Log in with your Premier Health VAPI account
3. Navigate to "Assistants" section

### Step 2: Update Each Assistant's Server URL

You need to update **7 regional assistants**:

1. **Greater Accra Assistant**
2. **Ashanti Assistant**
3. **Western & Central Assistant**
4. **Eastern & Volta Assistant**
5. **Northern Regions Assistant**
6. **Bono Regions Assistant**
7. **Bono/Bono East/Ahafo Assistant**

For **EACH** assistant, follow these steps:

#### A. Open Assistant Settings
- Click on the assistant name
- Go to "Server" or "Webhook" settings
- Look for "Server URL" or "Webhook URL" field

#### B. Update the URL
**Current value (WRONG):**
```
https://api.ailabsafrica.com/vapi/webhooks/premier-health
```

**Change to (CORRECT):**
```
https://api.ailabsafrica.com/premier-health/vapi-webhook
```

#### C. Verify Function Configuration
While in the assistant settings, also verify that the function `query_premier_health_knowledge_base` is properly configured:

**Function Name:** `query_premier_health_knowledge_base`

**Parameters:**
- `query` (string, required): The search query
- `region` (string, optional): Geographic region filter (e.g., "GREATER ACCRA", "ASHANTI")

**Server URL:** `https://api.ailabsafrica.com/premier-health/vapi-webhook`

#### D. Save Changes
- Click "Save" or "Update"
- Confirm the changes are applied

### Step 3: Verify the Fix

After updating all 7 assistants, test each one:

#### Test 1: Simple Provider Search
Call the assistant and ask:
```
"I need a doctor in Madina"
```

**Expected Response:**
- Assistant should provide specific provider names and locations
- NOT "I cannot find providers"

#### Test 2: Regional Query
Call the assistant and ask:
```
"Show me hospitals in Kumasi"
```

**Expected Response:**
- List of hospitals in Kumasi (Ashanti region)
- Specific addresses and contact information

#### Test 3: Check Backend Logs
On the server, check that RAG queries are now being logged:

```bash
sudo journalctl -u kasaai-core-backend -f | grep "KNOWLEDGE BASE QUERY"
```

**Expected output:**
```
🔧 Function call received: query_premier_health_knowledge_base
🔍 KNOWLEDGE BASE QUERY: query='doctor in Madina', region='GREATER ACCRA'
📥 RAG QUERY START: company=premier_health_production
✅ RAG QUERY COMPLETE
```

**If you see these logs, the fix is working!**

## Alternative: Update via Configuration Files

If you have access to the assistant configuration JSON files, you can update them directly:

### Files to Update:
```
/opt/kasaai/apps/automations/premier-health/
├── config_greater_accra_assistant.json
├── config_ashanti_assistant.json
├── config_western_and_central_assistant.json
├── config_eastern_and_volta_assistant.json
├── config_northern_regions_assistant.json
├── config_bono_regions_assistant.json
└── config_bono_bono_east_and_ahafo_assistant.json
```

### Update Steps:
1. Open each JSON file
2. Find the `server` or `serverUrl` field
3. Change from:
   ```json
   "serverUrl": "https://api.ailabsafrica.com/vapi/webhooks/premier-health"
   ```
   To:
   ```json
   "serverUrl": "https://api.ailabsafrica.com/premier-health/vapi-webhook"
   ```
4. Save the file
5. Re-deploy the assistant using VAPI API or dashboard

## Technical Details

### Why This Happened
The endpoint structure follows FastAPI routing:
- Route: `/premier-health/vapi-webhook`
- NOT: `/vapi/webhooks/*`

The `/vapi/webhooks/` prefix doesn't exist in our FastAPI application, causing 404 errors.

### What Was Fixed on Backend
1. ✅ Cleared Python bytecode cache
2. ✅ Backend restarted successfully
3. ✅ Webhook endpoint `/premier-health/vapi-webhook` is active and ready
4. ✅ RAG knowledge base is loaded (176 chunks, 885 providers)
5. ✅ Test suite shows 100% pass rate

### Backend Status
```bash
# Check backend status
sudo systemctl status kasaai-core-backend

# Check if endpoint is accessible
curl -X POST https://api.ailabsafrica.com/premier-health/vapi-webhook \
  -H "Content-Type: application/json" \
  -d '{"message": {"type": "function-call", "function_call": {"name": "query_premier_health_knowledge_base", "parameters": {"query": "test"}}}, "call": {}}'
```

## Troubleshooting

### Issue: Still Getting "Cannot Find Providers"
**Check:**
1. Webhook URL is correct in VAPI dashboard
2. Backend is running: `sudo systemctl status kasaai-core-backend`
3. Logs show function calls arriving: `sudo journalctl -u kasaai-core-backend -f`

### Issue: 404 Errors Still Appearing
**Check:**
1. URL is exactly: `https://api.ailabsafrica.com/premier-health/vapi-webhook`
2. No typos (no trailing slash, correct path)
3. Assistant settings were saved after changes

### Issue: No Response from Assistant
**Check:**
1. VAPI phone number is active
2. Assistant is published/deployed in VAPI
3. Backend logs for errors: `sudo journalctl -u kasaai-core-backend --since "1 hour ago" | grep -i error`

## Success Criteria

After applying the fix, you should observe:

✅ No more 404 errors in backend logs for `/vapi/webhooks/premier-health`
✅ Function calls arrive at `/premier-health/vapi-webhook` with 200 status
✅ RAG queries appear in logs with "KNOWLEDGE BASE QUERY"
✅ Assistants provide specific provider names and locations
✅ Regional filtering works correctly

## Contact

If you encounter issues after following these instructions:
- Check backend logs: `sudo journalctl -u kasaai-core-backend -f`
- Review VAPI dashboard for any error messages
- Verify all 7 assistants have been updated

---

**Status:** Backend is ready ✅
**Action Required:** Update VAPI webhook URLs in dashboard
**Estimated Time:** 15-20 minutes for all 7 assistants
