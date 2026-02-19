# Premier Health Squad Deployment Guide

## Overview

This guide covers the deployment of the Premier Health VAPI squad configuration to fix the Deepgram transcriber failure during call transfers.

## Problem Summary

**Error**: `call.in-progress.error-vapifault-deepgram-transcriber-failed`

**Root Cause**:
- Call transfers between router and regional assistants failed because they weren't in a VAPI squad
- Deepgram transcriber session couldn't handoff properly between assistants
- Agent-to-agent transfers only work within VAPI squads
- Missing webhook event handlers for transfer tracking and debugging

## Solution Implemented

### 1. Squad Architecture

Created a VAPI squad with:
- 1 **Router Assistant** (handles region identification and routing)
- 6 **Regional Assistants** (specialized knowledge for each region):
  - Greater Accra
  - Ashanti
  - Northern Regions
  - Western and Central
  - Eastern and Volta
  - Bono Regions

**Key Feature**: Squad automatically handles Deepgram transcriber handoff during transfers, eliminating the transcriber failure error.

### 2. Configuration Changes

#### A. Webhook Secrets (`/opt/kasaai/.env`)
Generated secure HMAC SHA256 secrets for all assistants:
```bash
PREMIER_HEALTH_WEBHOOK_SECRET_ROUTER=kHsYrRrbb66u3C5rNGk9iljyVhy06KYDyB7zaNBHnsY
PREMIER_HEALTH_WEBHOOK_SECRET_GREATER_ACCRA=O4XHJLouHwFdBUPyJedZGQI_mJWbYFroQGyuzyhe9Wo
PREMIER_HEALTH_WEBHOOK_SECRET_ASHANTI=yjNnmiIni2Qkhh8AATJ35dKgLqOdsUx1yNi1jBteT9U
PREMIER_HEALTH_WEBHOOK_SECRET_NORTHERN_REGIONS=YABTUOK21vInqTVvE9SPq1fzkIe6p3mwJ0p-rHFkB2Y
PREMIER_HEALTH_WEBHOOK_SECRET_WESTERN_AND_CENTRAL=dOZAxf5jGGABdRsqyHa-XRNfn7ybGNUe9y8asKxidYE
PREMIER_HEALTH_WEBHOOK_SECRET_EASTERN_AND_VOLTA=C6fIoRJg5TqH3MlJlsTNqcWgHCw6yBvJCjlQ9PCC37k
PREMIER_HEALTH_WEBHOOK_SECRET_BONO_REGIONS=sXhVzxC2G0YlNtDduRk5qy7ML-HBtjJ17JeR3Ky_Yqc
```

#### B. Assistant Configurations
Updated all 7 assistant configs with:
- Enhanced `serverMessages` array including:
  - `"transfer-update"` - Track transfer progress
  - `"transfer-destination-request"` - Dynamic routing support
  - `"transcript"` - Full call transcripts
- Corrected `serverUrl`: `https://api.ailabsafrica.com/premier-health/vapi-server-messages`
- Real webhook secrets (replaced placeholders)

#### C. Squad Configuration (`config_squad.json`)
Template with placeholders for assistant IDs. The deployment script fills these automatically.

### 3. Backend Enhancements

#### A. Transfer Event Handler (`premier_health_transfers.py`)
New FastAPI router handling:
- **Webhook signature validation** using HMAC SHA256
- **Transfer event tracking**:
  - `transfer-update`: Log transfer status (completed/failed)
  - `transfer-destination-request`: Dynamic routing support
  - `transcript`: Call transcript logging
  - `end-of-call-report`: Call completion analytics
- **MongoDB logging**: All transfer events stored in `premier_health_transfers` collection

#### B. Transfer Statistics Endpoint
`GET /premier-health/transfer-statistics`

Returns:
- Total transfers
- Success/failure counts
- Success rate percentage
- Recent transfer history

### 4. Deployment Script Enhancements (`deploy_squad.py`)
Updated to:
- Deploy all 7 assistants (router + 6 regional)
- Create squad with **assistantDestinations** in router member
- Save deployment record with all IDs
- Support both new deployment and updates

---

## Deployment Instructions

### Prerequisites
```bash
# 1. Ensure you're in the correct directory
cd /opt/kasaai/apps/automations/premier-health

# 2. Set VAPI API key
export VAPI_API_KEY="42cf1e7c-2ef9-4bd7-ba30-52f2813605a2"

# 3. Verify webhook secrets are in .env
grep "PREMIER_HEALTH_WEBHOOK_SECRET" /opt/kasaai/.env
```

### Step 1: Deploy Squad

```bash
# Run the deployment script
python3 deploy_squad.py
```

When prompted, select:
- **Option 1**: Deploy complete squad (router + 6 regional assistants + squad)

**Expected Output**:
```
================================================================================
VAPI SQUAD DEPLOYMENT - PREMIER HEALTH NAVIGATOR
================================================================================

Deploying router + 6 regional assistants + squad configuration...

================================================================================
STEP 1: Create Router Assistant
================================================================================
📤 Creating Router Assistant...
✅ Created successfully! ID: abc123...

================================================================================
STEP 2: Create Regional Assistants
================================================================================
📤 Creating Greater Accra Assistant...
✅ Created successfully! ID: def456...
...

================================================================================
STEP 3: Create Squad
================================================================================
🔗 Creating Squad: Premier Health Navigator Squad...
✅ Squad created successfully! ID: xyz789...

================================================================================
DEPLOYMENT COMPLETE ✅
================================================================================

✅ Router Assistant: abc123...
✅ Regional Assistants (6):
   • Greater Accra: def456...
   ...
✅ Squad: xyz789...
```

**Important Files Created**:
- `deployment_record.json` - Contains all assistant and squad IDs
- `squad_id.txt` - Squad ID for future updates

### Step 2: Restart Core Backend

```bash
# Restart the service to load new routes
sudo systemctl restart kasaai-core-backend

# Check logs
sudo journalctl -u kasaai-core-backend -f
```

### Step 3: Update VAPI Phone Number

In VAPI dashboard:
1. Go to Phone Numbers
2. Select your Premier Health phone number
3. Update "Assistant" to use **Squad ID** (from `squad_id.txt`) instead of individual assistant ID
4. Save changes

---

## Testing

### Test 1: Basic Call Transfer

```bash
# Make a test call to your VAPI phone number
# Say: "I need a doctor in Madina"

# Expected flow:
# 1. Router answers
# 2. Identifies "Madina" is in Greater Accra
# 3. Transfers to Greater Accra specialist
# 4. No Deepgram error occurs
# 5. Transcriber continues working after transfer
```

### Test 2: Webhook Events

```bash
# Check transfer logs in MongoDB
mongosh mongodb://admin:aawwER4444%25@127.0.0.1:27017/kasaai_core

# Query transfer events
db.premier_health_transfers.find().sort({timestamp: -1}).limit(5).pretty()
```

### Test 3: Transfer Statistics

```bash
# Get transfer statistics via API
curl https://api.ailabsafrica.com/premier-health/transfer-statistics
```

Expected response:
```json
{
  "success": true,
  "statistics": {
    "total_transfers": 15,
    "successful_transfers": 14,
    "failed_transfers": 1,
    "success_rate": 93.33
  },
  "recent_transfers": [...]
}
```

---

## Monitoring

### Check Transfer Success Rate

```bash
# Via API
curl https://api.ailabsafrica.com/premier-health/transfer-statistics | jq '.statistics.success_rate'
```

### View Recent Transfer Events

```bash
# MongoDB query
mongosh mongodb://admin:aawwER4444%25@127.0.0.1:27017/kasaai_core --eval '
db.premier_health_transfers.find(
  {event_type: "transfer_update"},
  {call_id: 1, "event_data.status": 1, timestamp: 1}
).sort({timestamp: -1}).limit(10)
'
```

### Check Backend Logs

```bash
# Filter for transfer events
sudo journalctl -u kasaai-core-backend -f | grep -i transfer
```

---

## Troubleshooting

### Issue: Transfer Still Fails with Deepgram Error

**Check**:
1. Verify squad was created successfully:
   ```bash
   cat squad_id.txt
   ```

2. Verify phone number uses squad ID (not individual assistant ID)

3. Check assistant configs have matching keyterms:
   ```bash
   # All should have similar keyterm counts
   jq '.transcriber.keyterm | length' config_*.json
   ```

### Issue: Webhook Signature Validation Fails

**Check**:
1. Webhook secrets in .env match those in assistant configs
2. Correct webhook URL: `https://api.ailabsafrica.com/premier-health/vapi-server-messages`
3. Backend has restarted after adding secrets

**Debug**:
```bash
# Check backend logs for validation errors
sudo journalctl -u kasaai-core-backend -f | grep "webhook signature"
```

### Issue: No Transfer Events Logged

**Check**:
1. Assistant `serverMessages` include transfer events:
   ```bash
   jq '.serverMessages' config_greater_accra_assistant.json
   ```
   Should include: `"transfer-update"`, `"transfer-destination-request"`

2. Backend endpoint is reachable:
   ```bash
   curl https://api.ailabsafrica.com/premier-health/transfer-statistics
   ```

---

## Architecture Diagram

```
┌─────────────────────┐
│   VAPI Phone Call   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────────────────┐
│          Premier Health Squad                   │
│                                                 │
│  ┌─────────────────┐                           │
│  │ Router          │                           │
│  │ Assistant       │──┐                        │
│  └─────────────────┘  │                        │
│           │            │ assistantDestinations  │
│     Identifies         │                        │
│       Region           ▼                        │
│           │     ┌──────────────────┐           │
│           └────▶│ Regional         │           │
│                 │ Assistants (6)   │           │
│                 │ - Greater Accra  │           │
│                 │ - Ashanti        │           │
│                 │ - Northern       │           │
│                 │ - Western/Central│           │
│                 │ - Eastern/Volta  │           │
│                 │ - Bono           │           │
│                 └──────────────────┘           │
│                                                 │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
     ┌──────────────────────────┐
     │  Webhook Events          │
     │  (transfer-update, etc)  │
     └──────────┬───────────────┘
                │
                ▼
     ┌──────────────────────────┐
     │  Core Backend            │
     │  /premier-health/        │
     │  vapi-server-messages    │
     └──────────┬───────────────┘
                │
                ▼
     ┌──────────────────────────┐
     │  MongoDB Collection      │
     │  premier_health_transfers│
     └──────────────────────────┘
```

---

## Key Benefits

1. **✅ Eliminates Deepgram Transcriber Errors**
   - Squad automatically handles transcriber handoff
   - No manual session management needed

2. **✅ Full Transfer Tracking**
   - All transfers logged to MongoDB
   - Success/failure monitoring
   - Transfer statistics API

3. **✅ Secure Webhook Validation**
   - HMAC SHA256 signature verification
   - Individual secrets per assistant
   - Protection against unauthorized requests

4. **✅ Scalable Architecture**
   - Easy to add new regional assistants
   - Dynamic transfer routing support
   - Centralized monitoring

---

## Next Steps

1. **Monitor Initial Performance**
   - Check transfer success rate after deployment
   - Review MongoDB logs for any issues
   - Verify Deepgram error no longer occurs

2. **Optional Enhancements**
   - Add transfer retry logic with exponential backoff
   - Implement custom transfer routing based on business hours
   - Add alerting for failed transfers
   - Create dashboard for real-time monitoring

3. **Documentation**
   - Share transfer statistics with team
   - Document any regional routing adjustments
   - Update runbooks with squad ID

---

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review MongoDB transfer logs
3. Check backend logs: `sudo journalctl -u kasaai-core-backend -f`
4. Contact development team with:
   - Squad ID (from `squad_id.txt`)
   - Call ID showing the error
   - Relevant logs

---

**Last Updated**: 2025-11-06
**Version**: 1.0
**Status**: ✅ Ready for Deployment
