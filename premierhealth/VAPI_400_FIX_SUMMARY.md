# VAPI 400 Error Fix - Summary Report

## Date: 2025-11-11

## Problem Statement

Users clicking "Start Voice Call" on https://kasaai.premierhealthinsurance.org/ were getting:
```
POST https://api.vapi.ai/call/web 400 (Bad Request)
Error: "Invalid Destination. Assistant 'Premier Health Greater Accra' Not Found."
```

## Root Cause Analysis

### Initial Hypothesis ❌
We initially thought the issue was incorrect `server.url` configurations in individual assistants.

### Actual Root Cause ✅
The **squad configuration** was missing `assistantDestinations` for the router member.

VAPI squads require `assistantDestinations` at the **squad level** to map assistant names to IDs for transfer functionality. Without this mapping, VAPI couldn't resolve assistant names (like "Premier Health Greater Accra") when the router tried to transfer calls.

### Key Insight
- ✅ **Squad members need:** `assistantDestinations` with full assistant details
- ❌ **Individual assistants should NOT have:** `assistantId` in their tool destinations
- ✅ **Proper architecture:** Squad handles name→ID mapping, assistants use names only

## Solution Implemented

### 1. Updated Squad Configuration
- **Script:** `/opt/kasaai/apps/premierhealth/fix_squad_configuration.py`
- **Squad ID:** `d9c801a1-34df-4496-bb90-7ac9e3f9e44e`
- **Action:** Added `assistantDestinations` array to router member with all 6 regional specialists

### 2. Assistant Destinations Mapping
```json
{
  "assistant": "87182b39-a050-4ef4-9319-773666fabd6d",
  "assistantDestinations": [
    {
      "type": "assistant",
      "assistantId": "85e1cf7e-1711-4d01-9cad-c043b37707bd",
      "assistantName": "Premier Health Greater Accra",
      "message": "Let me connect you to our Greater Accra specialist...",
      "description": "Transfer to Greater Accra specialist..."
    },
    // ... 5 more regional specialists
  ]
}
```

### 3. Regional Specialists Mapped
1. **Greater Accra** → `85e1cf7e-1711-4d01-9cad-c043b37707bd`
2. **Ashanti** → `529d7292-c050-4f5c-941d-5207a4e3e3be`
3. **Northern Regions** → `650340b7-76ee-46e9-ae34-268ebc217dba`
4. **Western and Central** → `caec99dc-3e51-43c2-a9cc-4b9b6bbef1dc`
5. **Eastern and Volta** → `0917ac57-8cac-44a1-9047-aead837af492`
6. **Bono Regions** → `e39da43d-1190-419a-9739-d2c11bc8fe78`

## Files Modified

### Configuration Files
- ✅ `/opt/kasaai/apps/automations/premier-health/config_router_assistant.json` - Added assistantId fields for documentation
- ✅ Squad configuration updated via VAPI API

### Scripts Created
- ✅ `/opt/kasaai/apps/premierhealth/fix_squad_configuration.py` - Main fix script
- ✅ `/opt/kasaai/apps/premierhealth/fix_router_assistant.py` - Initial attempt (revealed VAPI architecture)

### Documentation Updated
- ✅ `/opt/kasaai/apps/premierhealth/400_ERROR_TROUBLESHOOTING.md` - Updated with actual root cause and fix
- ✅ `/opt/kasaai/apps/premierhealth/VAPI_400_FIX_SUMMARY.md` - This summary

## Testing Instructions

### 1. Test Voice Call Start
```
1. Go to: https://kasaai.premierhealthinsurance.org/
2. Click "Start Voice Call"
3. Expected: Call starts without 400 error
4. Expected: Router greets you and asks for your region
```

### 2. Test Regional Transfer
```
1. Start voice call
2. Say: "I'm in Greater Accra" (or any region)
3. Expected: Router transfers to regional specialist
4. Expected: Regional specialist answers with area-specific info
```

### 3. Monitor Backend
```bash
sudo journalctl -u kasaai-core-backend -f | grep "premier-health"
```
Expected: Webhook calls processed successfully

## Verification

### Before Fix
```
❌ POST https://api.vapi.ai/call/web 400 (Bad Request)
❌ Error: "Invalid Destination. Assistant 'Premier Health Greater Accra' Not Found."
❌ Calls fail to start
```

### After Fix
```
✅ Squad configuration includes assistantDestinations
✅ Router can resolve assistant names to IDs
✅ Calls should start successfully
✅ Transfers should work to all 6 regional specialists
```

## VAPI Squad Architecture Lessons

### Correct Structure
```
Squad (d9c801a1-34df-4496-bb90-7ac9e3f9e44e)
└── members[]
    ├── [0] Router Member
    │   ├── assistant: "87182b39..."
    │   └── assistantDestinations: [
    │       ├── {assistantId: "85e1cf...", assistantName: "Greater Accra"}
    │       ├── {assistantId: "529d72...", assistantName: "Ashanti"}
    │       └── ... (4 more)
    │   ]
    ├── [1] Greater Accra Assistant {assistant: "85e1cf..."}
    ├── [2] Ashanti Assistant {assistant: "529d72..."}
    └── ... (4 more regional assistants)
```

### Why This Architecture?
1. **Centralized mapping:** Squad controls which assistants can be reached
2. **Security:** Squad validates transfers before allowing them
3. **Flexibility:** Easy to add/remove assistants from routing
4. **Clarity:** Squad configuration is single source of truth

## API Credentials Used
- **VAPI API Key:** From `/opt/kasaai/.env` → `VAPI_API_KEY`
- **Squad ID:** `d9c801a1-34df-4496-bb90-7ac9e3f9e44e`
- **Update Method:** PATCH request to `https://api.vapi.ai/squad/{squad_id}`

## Status

✅ **Fix Applied:** Squad configuration updated successfully via VAPI API
✅ **Documentation Updated:** All files reflect actual root cause and solution
🧪 **Testing Required:** User should test voice calls to confirm fix works
📝 **Commit Ready:** Changes ready to be committed to git

## Next Steps for User

1. **Test the Fix**
   - Visit https://kasaai.premierhealthinsurance.org/
   - Click "Start Voice Call"
   - Verify call starts without errors
   - Test transfer to a regional specialist

2. **If It Works ✅**
   - No further action needed
   - Fix is complete and documented

3. **If It Still Fails ❌**
   - Check browser console for new error messages
   - Share the error details
   - We'll investigate further

## Support Files

- **Main Fix Script:** `/opt/kasaai/apps/premierhealth/fix_squad_configuration.py`
- **Troubleshooting:** `/opt/kasaai/apps/premierhealth/400_ERROR_TROUBLESHOOTING.md`
- **Squad Config:** `/opt/kasaai/apps/automations/premier-health/config_squad.json`
- **Deployment Record:** `/opt/kasaai/apps/automations/premier-health/deployment_record.json`

---

**Engineer:** Claude Code
**Date:** 2025-11-11
**Status:** ✅ Fix Applied - Ready for Testing
