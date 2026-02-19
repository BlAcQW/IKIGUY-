# VAPI Server URL Fix Guide - Premier Health Navigator Squad

## 🚨 CRITICAL ISSUE IDENTIFIED

All 7 assistants in the Premier Health Navigator Squad have the **WRONG `server.url`** configured, causing function calls to fail with 404 errors.

---

## Problem Summary

**What's Wrong:**
- VAPI assistants have TWO URL fields: `server.url` and `serverUrl`
- `server.url` is used for server-to-server communication and tool function calls
- Current `server.url` values point to non-existent endpoints
- This causes all function calls to get 404 errors
- Backend never receives the queries
- Users experience repeated function calls with no results

**Evidence from Logs:**
```
Nov 07 14:55:18 ... "POST /vapi/webhooks/premier-health HTTP/1.1" 404 Not Found
Nov 07 14:55:39 ... "POST /vapi/webhooks/premier-health HTTP/1.1" 404 Not Found
```

---

## Fix Instructions

### Step 1: Login to VAPI Dashboard

1. Go to https://vapi.ai
2. Login with your credentials
3. Navigate to "Assistants" section

### Step 2: Update Each Assistant

You need to update **ALL 7 assistants** in the squad. For each assistant:

#### Assistant 1: Router Assistant
- **ID**: `87182b39-a050-4ef4-9319-773666fabd6d`
- **Name**: Premier Health Router
- **Action**:
  1. Open assistant settings
  2. Find "Server" section
  3. Change "Server URL" to: `https://api.ailabsafrica.com/premier-health/vapi-webhook`
  4. Save

#### Assistant 2: Greater Accra Specialist
- **ID**: `85e1cf7e-1711-4d01-9cad-c043b37707bd`
- **Name**: Premier Health Greater Accra
- **Current (WRONG)**: `https://flow-api.ailabsafrica.com/call-management/vapi/webhook`
- **Change to**: `https://api.ailabsafrica.com/premier-health/vapi-webhook`

#### Assistant 3: Ashanti Specialist
- **ID**: `529d7292-c050-4f5c-941d-5207a4e3e3be`
- **Name**: Premier Health Ashanti
- **Current (WRONG)**: `https://api.ailabsafrica.com/vapi/webhooks/premier-health`
- **Change to**: `https://api.ailabsafrica.com/premier-health/vapi-webhook`

#### Assistant 4: Northern Regions Specialist
- **ID**: `650340b7-76ee-46e9-ae34-268ebc217dba`
- **Name**: Premier Health Northern Regions
- **Change to**: `https://api.ailabsafrica.com/premier-health/vapi-webhook`

#### Assistant 5: Western and Central Specialist
- **ID**: `caec99dc-3e51-43c2-a9cc-4b9b6bbef1dc`
- **Name**: Premier Health Western and Central
- **Change to**: `https://api.ailabsafrica.com/premier-health/vapi-webhook`

#### Assistant 6: Eastern and Volta Specialist
- **ID**: `0917ac57-8cac-44a1-9047-aead837af492`
- **Name**: Premier Health Eastern and Volta
- **Change to**: `https://api.ailabsafrica.com/premier-health/vapi-webhook`

#### Assistant 7: Bono Regions Specialist
- **ID**: `e39da43d-1190-419a-9739-d2c11bc8fe78`
- **Name**: Premier Health Bono Regions
- **Change to**: `https://api.ailabsafrica.com/premier-health/vapi-webhook`

---

## Important Notes

### What NOT to Change
- ❌ **Do NOT change** the `serverUrl` field (if it shows separately)
- ❌ **Do NOT change** tool configurations
- ❌ **Do NOT change** model settings
- ✅ **ONLY change** the "Server URL" field in the Server section

### Field Names in VAPI Dashboard
Depending on the VAPI dashboard version, the field might be labeled as:
- "Server URL"
- "Server Endpoint"
- "Webhook URL" (in the Server section)

### Correct URL Format
```
https://api.ailabsafrica.com/premier-health/vapi-webhook
```

Make sure there are:
- ✅ No trailing slashes
- ✅ HTTPS (not HTTP)
- ✅ Correct domain: `api.ailabsafrica.com`
- ✅ Correct path: `/premier-health/vapi-webhook`

---

## Verification

### After Making Changes

1. **Wait 1-2 minutes** for VAPI to propagate changes

2. **Test with a call**:
   - Call: +233 24 242 6051
   - Ask: "I need a doctor in Madina"
   - Expected: List of providers in Madina

3. **Check backend logs**:
   ```bash
   sudo journalctl -u kasaai-core-backend -f | grep "KNOWLEDGE BASE QUERY"
   ```

   You should see:
   ```
   🔧 Function call received: query_premier_health_knowledge_base
   🔍 KNOWLEDGE BASE QUERY: query='doctor in Madina', region='GREATER ACCRA'
   ✅ RAG QUERY COMPLETE
   ```

4. **Verify no 404 errors**:
   ```bash
   sudo journalctl -u kasaai-core-backend --since "5 minutes ago" | grep "404"
   ```

   Should NOT see:
   ```
   "POST /vapi/webhooks/premier-health HTTP/1.1" 404 Not Found
   ```

5. **Run verification script**:
   ```bash
   cd /opt/kasaai/apps/premierhealth
   python3 verify_vapi_urls.py
   ```

---

## Troubleshooting

### Issue: Still getting 404 errors after update

**Possible causes:**
1. Changes not saved properly in VAPI dashboard
2. Need to wait longer for propagation (try 5 minutes)
3. Updated wrong field (make sure it's the Server URL, not tool serverUrl)

**Solution:**
- Re-check each assistant configuration in VAPI
- Verify the URL exactly matches (no extra slashes, correct domain)
- Try updating one assistant first and testing before updating all

### Issue: Function calls not reaching backend

**Check:**
1. Backend service is running: `sudo systemctl status kasaai-core-backend`
2. Endpoint is accessible: `curl -X POST https://api.ailabsafrica.com/premier-health/vapi-webhook -d '{}'`
3. VAPI logs in dashboard show successful calls

### Issue: Ashanti queries still return no providers

**Expected behavior:**
- This is CORRECT after the fix
- Database has NO Ashanti providers
- Backend returns helpful message:
  ```
  "I apologize, but Premier Health Insurance network providers in Ashanti region
  are not yet available in our digital system..."
  ```

**To add Ashanti data:**
- Import provider data into database
- Update RAG knowledge base
- See separate guide: `ADDING_REGIONAL_PROVIDERS.md`

---

## Timeline

- **Immediate** (30 min): Update all 7 assistant URLs in VAPI dashboard
- **Short-term** (1 hour): Test and verify all regions working correctly
- **Long-term** (varies): Add provider data for Ashanti and other regions

---

## Contact

If you encounter issues:
1. Check backend logs: `sudo journalctl -u kasaai-core-backend -f`
2. Check VAPI dashboard logs
3. Review this guide's troubleshooting section

---

## Version History

- **2025-11-07**: Initial guide created after identifying wrong server.url configuration
