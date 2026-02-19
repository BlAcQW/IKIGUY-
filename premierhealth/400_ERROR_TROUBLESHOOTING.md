# 400 Bad Request Error - Troubleshooting Guide

## Error Symptoms

When users click "Start Voice Call" on https://kasaai.premierhealthinsurance.org/, they see:
```
POST https://api.vapi.ai/call/web 400 (Bad Request)
widget.umd.js:78 Vapi error:
{type: 'start-method-error', stage: 'unknown', error: Response, totalDuration: 867, timestamp: '2025-11-11T12:03:37.893Z', …}
```

## Root Cause

The Premier Health Navigator Squad was **missing `assistantDestinations`** in the router member configuration.

### The Issue
When a VAPI squad uses transfer functionality, the **squad configuration** (not individual assistants) must define `assistantDestinations` that map assistant names to their IDs. This was missing from the router member configuration.

### Error Message
```
"Invalid Destination. Assistant 'Premier Health Greater Accra' Not Found."
statusCode: 400
```

## Why This Causes 400 Errors

1. User clicks "Start Voice Call" → Browser calls `window.vapiWebInstance.start(null, null, squadId)`
2. Vapi Web SDK sends POST to `https://api.vapi.ai/call/web`
3. **Vapi validates the squad configuration**
4. Vapi checks router's transfer destinations (Greater Accra, Ashanti, etc.)
5. **Router member has NO `assistantDestinations` mapping**
6. Vapi cannot resolve assistant names to IDs
7. **Vapi returns 400 Bad Request: "Invalid Destination"**

## The Fix (APPLIED ✅)

### What Was Done

Updated the squad configuration to include `assistantDestinations` for the router member using the VAPI API.

**Squad ID:** `d9c801a1-34df-4496-bb90-7ac9e3f9e44e`
**Router Assistant ID:** `87182b39-a050-4ef4-9319-773666fabd6d`

### Assistant Destinations Added

The following mappings were added to the squad configuration:

1. **Greater Accra Specialist** - ID: `85e1cf7e-1711-4d01-9cad-c043b37707bd`
2. **Ashanti Specialist** - ID: `529d7292-c050-4f5c-941d-5207a4e3e3be`
3. **Northern Regions Specialist** - ID: `650340b7-76ee-46e9-ae34-268ebc217dba`
4. **Western and Central Specialist** - ID: `caec99dc-3e51-43c2-a9cc-4b9b6bbef1dc`
5. **Eastern and Volta Specialist** - ID: `0917ac57-8cac-44a1-9047-aead837af492`
6. **Bono Regions Specialist** - ID: `e39da43d-1190-419a-9739-d2c11bc8fe78`

### Fix Script

Location: `/opt/kasaai/apps/premierhealth/fix_squad_configuration.py`

The script:
- Retrieved current squad configuration
- Added `assistantDestinations` to the router member
- Updated the squad via VAPI API
- Verified the fix was applied successfully

⏱️ **Applied:** 2025-11-11

## What's Been Fixed (In This Commit)

### Enhanced Error Handling ✅

Now when 400 errors occur, users see:
```
🔧 Voice assistant is being configured

The voice call feature is temporarily unavailable. Please try:

✅ Click "Start Chat" button below for text chat
✅ Call us directly at +233 24 242 6051

For technical support: api.ailabsafrica.com/premier-health
```

### Enhanced Debugging ✅

Console now shows detailed diagnostics:
```
=== VAPI VOICE CALL TRIGGERED ===
Timestamp: 2025-11-11T12:03:37.893Z
✓ Vapi Web SDK detected
Starting squad call...
▶ Starting squad call with ID: d9c801a1-34df-4496-bb90-7ac9e3f9e44e
Calling: vapiWebInstance.start(null, null, squadId)
❌ Error starting squad call: [Error object]
Error type: Error
Error details: {message: "...", response: {...}, status: 400}
⚠ 400 Bad Request - This typically means:
  • Assistant server.url is incorrect or unreachable
  • Squad configuration is invalid
  • Expected server.url: https://api.ailabsafrica.com/premier-health/vapi-webhook
```

## Verification After Fix

### 1. Run Verification Script
```bash
cd /opt/kasaai/apps/premierhealth
python3 verify_vapi_urls.py
```

**Expected output:**
```
✅ ALL ASSISTANTS CORRECTLY CONFIGURED!
```

### 2. Test Web Call
1. Visit https://kasaai.premierhealthinsurance.org/
2. Click "Start Voice Call"
3. Should connect without 400 error
4. Voice call should start successfully

### 3. Monitor Backend Logs
```bash
sudo journalctl -u kasaai-core-backend -f | grep "premier-health"
```

**Expected to see:**
```
INFO: POST /vapi/webhooks/premier-health - 200 OK
✅ KNOWLEDGE BASE QUERY successful
```

## Alternative Options (Working Now)

While voice calls are down, users can:

### ✅ Chat Widget
- Click "Start Chat" button
- Uses different assistant (baa69b3a-8944-4557-9ef9-3a5aa6956eb3)
- Works without server.url validation

### ✅ Direct Phone Call
- Phone: +233 24 242 6051
- Bypasses web validation
- Connects directly to VAPI

### ✅ Widget-based Voice
- The embedded `<vapi-widget>` might still work
- Uses different initialization path
- Less user control

## Why Backend is NOT the Problem

Backend logs show successful webhook processing:
```
✅ Successfully forwarded and processed webhook
✅ RAG query successful: confidence=1.0
✅ Provider search returning results
```

The issue is:
- ❌ NOT the backend
- ❌ NOT the knowledge base
- ❌ NOT the RAG system
- ✅ ONLY the VAPI assistant configuration

## Technical Details

### Error Flow
```
User → "Start Voice Call" button
  ↓
JavaScript → window.vapiWebInstance.start(null, null, squadId)
  ↓
Vapi SDK → POST https://api.vapi.ai/call/web
  ↓
VAPI → Validates squad configuration
  ↓
VAPI → Checks all 7 assistant server.url values
  ↓
VAPI → Detects unreachable URLs
  ↓
VAPI → Returns 400 Bad Request ❌
  ↓
Enhanced error handling → Shows user-friendly message ✅
```

### Configuration in index.html

```javascript
// Squad ID
const squadId = "d9c801a1-34df-4496-bb90-7ac9e3f9e44e";

// Public Key
const vapiPublicKey = "0c22dcea-0d6c-4fc0-8fb2-93292d8575e8";

// Call start (line 731)
await window.vapiWebInstance.start(null, null, squadId);
```

## Next Steps

1. ✅ **Squad configuration updated:** Added assistantDestinations via API
2. ✅ **Code changes done:** Enhanced error handling committed
3. 🧪 **Testing Required:** Test voice calls on https://kasaai.premierhealthinsurance.org/
4. ✅ **Documentation Updated:** Reflects actual root cause and fix

## Support

- **Fix Script:** `/opt/kasaai/apps/premierhealth/fix_squad_configuration.py`
- **Configuration:** `/opt/kasaai/apps/automations/premier-health/config_squad.json`
- **Deployment Record:** `/opt/kasaai/apps/automations/premier-health/deployment_record.json`
- **Backend:** https://api.ailabsafrica.com/premier-health/vapi-webhook
- **Frontend:** https://kasaai.premierhealthinsurance.org/

## Key Learnings

### VAPI Squad Architecture
- ✅ **Squad-level configuration:** `assistantDestinations` must be in squad members, not individual assistants
- ❌ **Individual assistant tools:** Cannot include `assistantId` in transfer destinations
- ✅ **Proper structure:** Squad maps assistant names → IDs, assistants use names only

### Configuration Hierarchy
```
Squad Configuration (squad.members[0])
├── assistant: "router-id"
└── assistantDestinations: [
    ├── {assistantId: "accra-id", assistantName: "Greater Accra", ...}
    ├── {assistantId: "ashanti-id", assistantName: "Ashanti", ...}
    └── ...
]

Router Assistant (individual assistant config)
└── model.tools[0].destinations: [
    ├── {type: "assistant", assistantName: "Greater Accra", ...}  ← NO assistantId
    ├── {type: "assistant", assistantName: "Ashanti", ...}  ← NO assistantId
    └── ...
]
```

---

**Status:** ✅ Fix Applied - Ready for Testing

**Last Updated:** 2025-11-11
