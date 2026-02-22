# LOAD VAPI Replacement — Step-by-Step Implementation Guide

## Quick Reference: What to Do (in order)

---

## Step 1: Fix LOAD Build Errors (30 min)

### 1a. Fix Backend TypeScript Errors

```bash
cd /root/home/LOAD/backend
```

Open `src/telephony/twilio.ts` and fix Twilio SDK property names:
- `phoneNumber` → `to` (in calls.create)
- `statusCallbackUrl` → `statusCallback` (in calls.create and incomingPhoneNumbers.create)
- `voiceUrl` property name check against Twilio SDK 4.x types

### 1b. Fix Frontend Unused Imports

```bash
cd /root/home/LOAD/frontend
```

Remove `import React from 'react'` from:
- `src/pages/Dashboard.tsx`
- `src/pages/PhoneNumbers.tsx`
- `src/pages/WebCall.tsx`

### 1c. Verify Builds Pass

```bash
cd /root/home/LOAD/backend && npm run build
cd /root/home/LOAD/frontend && npm run build
```

---

## Step 2: Start LOAD Services (15 min)

```bash
cd /root/home/LOAD

# Start databases
docker compose up -d postgres redis

# Wait for healthy
docker compose ps  # both should show "healthy"

# Run database migrations
cd backend
npm run db:migrate

# Start backend
npm run dev  # Port 3000

# In another terminal: start frontend
cd /root/home/LOAD/frontend
npm run dev  # Port 5173
```

### 2a. Verify LOAD is Running

- API Health: `curl http://localhost:3000/api/health`
- API Docs: Open `http://localhost:3000/docs`
- Dashboard: Open `http://localhost:5173`

### 2b. Create Account & API Key

1. Open `http://localhost:5173/register`
2. Create account (e.g., email: admin@kasaai.com, org: KasaAI)
3. Go to Settings → Create API Key
4. Save the key (format: `load_xxxxxxxxxxxx`)

### 2c. Create Your First Assistant

Via API (or dashboard):

```bash
curl -X POST http://localhost:3000/api/assistants \
  -H "Authorization: Bearer load_YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "KasaAI Property Agent",
    "model": {
      "provider": "openai",
      "model": "gpt-4",
      "temperature": 0.7,
      "maxTokens": 1000,
      "systemPrompt": "You are a helpful property agent for KasaAI. You help callers learn about available properties, schedule tours, and answer questions about listings. Be professional, friendly, and helpful. If the caller wants to schedule a tour, collect their name, preferred date/time, and the property they are interested in."
    },
    "voice": {
      "provider": "openai",
      "voiceId": "alloy",
      "speed": 1.0
    },
    "transcriber": {
      "provider": "openai",
      "model": "whisper-1",
      "language": "en"
    },
    "firstMessage": "Hello! Welcome to KasaAI. How can I help you with your property search today?"
  }'
```

Save the returned `id` — this is your assistant ID.

### 2d. Test Web Call

1. Open `http://localhost:5173/web-call`
2. Select your assistant
3. Click "Start Call"
4. Speak and verify the voice pipeline works

---

## Step 3: Enable Asterisk ARI (1 hour)

### 3a. SSH into the Asterisk Server

```bash
ssh root@148.251.0.46
# or if running locally:
docker exec -it kasaai-asterisk-proxy /bin/bash
```

### 3b. Enable ARI

Create/edit `/etc/asterisk/ari.conf`:

```ini
[general]
enabled = yes
pretty = yes
allowed_origins = *

[load]
type = user
read_only = no
password = your-secure-ari-password
```

### 3c. Enable HTTP

Create/edit `/etc/asterisk/http.conf`:

```ini
[general]
enabled = yes
bindaddr = 0.0.0.0
bindport = 8088
```

### 3d. Update Dialplan

Edit `/etc/asterisk/extensions.conf` — add/update:

```ini
[from-ant-cellular]
exten => _X.,1,NoOp(=== Inbound from Ant Cellular: ${CALLERID(num)} -> ${EXTEN} ===)
same  => n,Answer()
same  => n,Stasis(load,inbound,${EXTEN},${CALLERID(num)})
same  => n,Hangup()

[to-ant-cellular]
exten => _X.,1,NoOp(=== Outbound via Ant Cellular: -> ${EXTEN} ===)
same  => n,Dial(PJSIP/${EXTEN}@ant-cellular-trunk,60,g)
same  => n,Hangup()
```

### 3e. Reload Asterisk

```bash
# Inside container:
asterisk -rx "core reload"
asterisk -rx "ari show apps"
asterisk -rx "http show status"
```

### 3f. Test ARI Connection

```bash
# From LOAD server:
curl -u load:your-secure-ari-password \
  http://148.251.0.46:8088/ari/asterisk/info
```

Should return Asterisk system info JSON.

---

## Step 4: Implement Asterisk ARI Client in LOAD (2-3 days)

### 4a. Install Dependencies

```bash
cd /root/home/LOAD/backend
npm install ari-client
```

### 4b. Create Files

Create these files (full code in VAPI_REPLACEMENT_SRS.md Section 4):

1. `src/telephony/asterisk-ari.ts` — ARI connection, call control
2. `src/telephony/call-bridge.ts` — Bridges ARI audio ↔ voice pipeline
3. `src/telephony/audio-resample.ts` — Audio format conversion

### 4c. Add Config Variables

Update `src/config/index.ts` to include:

```typescript
// Asterisk ARI
ASTERISK_ARI_URL: z.string().optional(),
ASTERISK_ARI_USERNAME: z.string().optional(),
ASTERISK_ARI_PASSWORD: z.string().optional(),
ASTERISK_ARI_APP: z.string().default('load'),
```

Update `.env`:

```bash
ASTERISK_ARI_URL=http://148.251.0.46:8088
ASTERISK_ARI_USERNAME=load
ASTERISK_ARI_PASSWORD=your-secure-ari-password
ASTERISK_ARI_APP=load
```

### 4d. Wire Into App Startup

Update `src/app.ts` to initialize ARI on startup (see SRS Section 9).

### 4e. Test

```bash
npm test  # All existing + new tests pass
npm run build  # No TypeScript errors
```

---

## Step 5: Implement Telephony Endpoints (2 days)

### 5a. Update Call Routes

Add to `src/modules/calls/routes.ts`:
- `POST /api/calls` — Create outbound call
- `POST /api/calls/:id/end` — Force end call

### 5b. Update Call Service

Add to `src/modules/calls/service.ts`:
- `createOutboundCall()` — Initiates call via ARI
- `handleInboundCall()` — Routes inbound to assistant
- `updateCallTranscript()` — Persists transcript
- `setCallRecording()` — Stores recording URL

### 5c. Add SIP Phone Number Support

Update `src/modules/phone-numbers/service.ts`:
- `createSipNumber()` — Register SIP trunk number (no Twilio needed)
- `findByNumber()` — Lookup by E.164 for inbound routing

### 5d. Register Phone Number

```bash
# Register the Ant Cellular number in LOAD
curl -X POST http://localhost:3000/api/phone-numbers \
  -H "Authorization: Bearer load_YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "number": "+233308249843",
    "provider": "SIP_TRUNK",
    "sipDomain": "vitalpbx.antcellular.com",
    "name": "Ant Cellular Main Line",
    "assistantId": "YOUR_ASSISTANT_ID"
  }'
```

---

## Step 6: Implement Webhook Delivery (1 day)

### 6a. Create Webhook Delivery Service

Create `src/modules/webhooks/delivery.ts` (see SRS Section 7).

### 6b. Register DiaServe1 Webhook

```bash
# In LOAD, register DiaServe1 as webhook receiver
curl -X POST http://localhost:3000/api/webhooks \
  -H "Authorization: Bearer load_YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://localhost:8000/api/v1/voice/webhook/load",
    "events": ["call.started", "call.ended", "transcript.update", "campaign.completed"],
    "secret": "your-webhook-signing-secret"
  }'
```

---

## Step 7: Implement Campaign Engine (2 days)

Create `src/modules/campaigns/engine.ts` (see SRS Section 8).

Wire into campaign routes:
- `POST /api/campaigns/:id/start` → calls `startCampaign()`
- `POST /api/campaigns/:id/pause` → pauses BullMQ queue

---

## Step 8: Integrate DiaServe1 with LOAD (2 days)

### 8a. Create LOAD Client

Create `DiaServe1/backend/app/integration/load_client.py` (see SRS Section 6.1).

### 8b. Add Webhook Endpoint

Add to `DiaServe1/backend/app/api/voice/router.py`:
- `POST /webhook/load` — Receives LOAD webhook events

### 8c. Update Campaign Service

Update `DiaServe1/backend/app/services/campaign_service.py`:
- Replace `self.vapi_service.make_bulk_calls()` with `self.load_client.make_bulk_calls()`

### 8d. Update DiaServe1 .env

```bash
# Add to DiaServe1 backend .env:
LOAD_API_URL=http://localhost:3000
LOAD_API_KEY=load_your-generated-api-key
```

---

## Step 9: End-to-End Testing (2 days)

### Test 1: Web Call

1. Open LOAD dashboard → Web Call page
2. Select assistant, click Start
3. Speak and verify conversation works
4. Check call appears in Calls page with transcript

### Test 2: Outbound Call via API

```bash
curl -X POST http://localhost:3000/api/calls \
  -H "Authorization: Bearer load_YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "OUTBOUND",
    "assistantId": "YOUR_ASSISTANT_ID",
    "customerNumber": "+233XXXXXXXXX",
    "metadata": { "organization_id": "diaserve-org-id" }
  }'
```

Verify:
- [ ] Phone rings
- [ ] AI assistant speaks first message
- [ ] Conversation works
- [ ] Call record created with transcript
- [ ] Webhook fired to DiaServe1

### Test 3: Inbound Call

1. Call +233308249843 from external phone
2. Verify:
   - [ ] Asterisk receives call (check `docker logs kasaai-asterisk-proxy`)
   - [ ] ARI routes to LOAD
   - [ ] AI assistant answers
   - [ ] Conversation works
   - [ ] Call record created
   - [ ] Webhook fired

### Test 4: Campaign

```bash
# Create campaign via DiaServe1
# Use voice campaign with LOAD assistant ID
# Start campaign
# Verify all contacts called
# Verify webhooks received
# Verify DiaServe1 has call records
```

### Test 5: DiaServe1 Integration

1. Create voice campaign in DiaServe1
2. Verify it uses LOAD (not VAPI)
3. Check call records appear in DiaServe1 voice dashboard
4. Check leads are auto-created from calls

---

## Step 10: Cutover from VAPI (1 week parallel run)

### Day 1-3: Parallel Operation

- Keep VAPI configured but disabled for new campaigns
- Route all new campaigns through LOAD
- Monitor both systems

### Day 4-5: Compare Quality

- Compare call success rates
- Compare transcript quality
- Compare latency
- Compare webhook reliability

### Day 6-7: Full Cutover

1. Remove VAPI_API_KEY from DiaServe1 .env
2. Remove VapiClient import from campaign service
3. Update voice config in DiaServe1 to reference LOAD assistant IDs
4. Monitor for 48 hours

### Post-Cutover Cleanup

- [ ] Delete VAPI account (or keep as backup)
- [ ] Remove `DiaServe1/backend/app/integration/vapi_client.py`
- [ ] Remove VAPI webhook endpoint from DiaServe1
- [ ] Update DiaServe1 documentation

---

## Troubleshooting

### LOAD Backend Won't Start

```bash
# Check database
docker compose ps  # postgres should be "healthy"
# Check migrations
cd backend && npm run db:push
# Check env
cat .env  # Verify DATABASE_URL, JWT_SECRET
```

### Asterisk ARI Connection Failed

```bash
# Test ARI from LOAD server
curl -u load:password http://148.251.0.46:8088/ari/asterisk/info

# If timeout: check firewall
iptables -L -n | grep 8088

# If auth error: check ari.conf credentials
docker exec kasaai-asterisk-proxy cat /etc/asterisk/ari.conf
```

### Calls Not Routing Through Asterisk

```bash
# Check Asterisk registration with Ant Cellular
docker exec kasaai-asterisk-proxy asterisk -rx "pjsip show registrations"

# Check active channels during call
docker exec kasaai-asterisk-proxy asterisk -rx "core show channels"

# Check dialplan loaded
docker exec kasaai-asterisk-proxy asterisk -rx "dialplan show from-ant-cellular"
```

### No Audio During Call

- Check audio resampling (8kHz ↔ 16kHz conversion)
- Check ExternalMedia channel format in ARI
- Check firewall allows RTP ports (10000-20000 UDP)
- Try setting Asterisk ExternalMedia to `format=slin16`

### Webhooks Not Delivered

```bash
# Check Redis queue
redis-cli LLEN "bull:webhook-delivery:wait"
redis-cli LLEN "bull:webhook-delivery:failed"

# Check LOAD logs for delivery errors
docker logs load-backend 2>&1 | grep "webhook"

# Test webhook endpoint manually
curl -X POST http://localhost:8000/api/v1/voice/webhook/load \
  -H "Content-Type: application/json" \
  -d '{"event": "call.ended", "data": {"callId": "test"}}'
```

---

## Architecture Decision Records

### ADR-1: Why Asterisk ARI (not native SIP in Node.js)?

**Decision:** Use Asterisk ARI as the telephony bridge.

**Rationale:**
- Asterisk is already deployed and registered with Ant Cellular
- ARI provides a clean REST/WebSocket API for call control
- Asterisk handles SIP complexity (REGISTER, NAT traversal, codec negotiation)
- LOAD stays focused on voice AI, not SIP protocol
- If we later want native SIP, we can add `drachtio-srf` without breaking ARI

### ADR-2: Why BullMQ for webhooks and campaigns?

**Decision:** Use BullMQ (Redis-backed) for async job processing.

**Rationale:**
- Already in the tech stack (Redis running)
- Retry logic with exponential backoff built-in
- Rate limiting / concurrency control built-in
- Dead letter queue for failed jobs
- Dashboard available (Bull Board) for monitoring

### ADR-3: Why not Twilio for telephony?

**Decision:** Use Asterisk + Ant Cellular instead of Twilio.

**Rationale:**
- Ant Cellular number (+233308249843) is already provisioned
- Asterisk proxy is already running and registered
- No additional per-minute cost from Twilio
- Full control over call routing
- Twilio support remains as fallback option
