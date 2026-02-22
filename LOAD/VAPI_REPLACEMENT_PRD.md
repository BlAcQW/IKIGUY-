# LOAD as VAPI Replacement — Product Requirements Document

## Executive Summary

Replace VAPI (external SaaS) with LOAD (self-hosted) as the voice AI engine for DiaServe1's property management platform. This eliminates the VAPI dependency, gives full control over the voice pipeline, removes the Ant Cellular SIP registration issue, and reduces per-call costs.

---

## 1. Current State Analysis

### What VAPI Does for DiaServe1 Today

| Capability | VAPI Status | LOAD Status |
|-----------|-------------|-------------|
| Outbound voice calls to leads | Working | Not implemented |
| Bulk campaign calls | Working (via API) | Not implemented |
| Inbound call handling (+233308249843) | BROKEN (SIP registration issue) | Not implemented |
| STT (Speech-to-Text) | Working | Working (OpenAI Whisper) |
| LLM conversation | Working | Working (OpenAI GPT-4) |
| TTS (Text-to-Speech) | Working | Working (OpenAI TTS) |
| Web-based calls (browser) | Working | Working (WebSocket) |
| Call recording | Working | Not implemented |
| Webhook delivery (call.ended) | Working | Not implemented |
| Phone number management | Working | Scaffolded, broken build |
| Real-time transcripts | Working | Working (WebSocket only) |

### Why Replace VAPI?

1. **Inbound calls are broken** — VAPI can't SIP REGISTER with Ant Cellular's VitalPBX
2. **Cost** — VAPI charges per-minute; LOAD only costs OpenAI API fees
3. **Control** — Full control over voice pipeline, latency, and provider selection
4. **Data sovereignty** — Call recordings and transcripts stay on your server
5. **Customization** — Custom tools, routing, and business logic without VAPI's limitations

---

## 2. Target Architecture

```
                    ┌─────────────────────────────────────┐
                    │           DiaServe1 App              │
                    │      (Python/FastAPI Backend)        │
                    │      (React/Vite Frontend)           │
                    └──────────┬──────────────────────────┘
                               │ HTTP API + Webhooks
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                        LOAD Platform                          │
│                  (Node.js/Fastify Backend)                    │
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐ │
│  │  Auth &   │  │Assistant │  │  Call     │  │  Campaign    │ │
│  │  API Keys │  │  Mgmt    │  │  Engine   │  │  Engine      │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘ │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              Voice Pipeline Engine                      │  │
│  │         Audio → STT → LLM → TTS → Audio                │  │
│  │    (OpenAI Whisper → GPT-4 → OpenAI TTS)               │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              Telephony Layer                             │  │
│  │  ┌──────────┐  ┌──────────────┐  ┌──────────────────┐  │  │
│  │  │  Twilio   │  │  SIP Trunk   │  │  Asterisk Proxy  │  │  │
│  │  │ (backup)  │  │ (Ant Cell.)  │  │  (148.251.0.46)  │  │  │
│  │  └──────────┘  └──────────────┘  └──────────────────┘  │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────────┐   │
│  │PostgreSQL│  │  Redis   │  │  BullMQ (Job Queue)      │   │
│  └──────────┘  └──────────┘  └──────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
                               │
                    SIP/RTP    │    SIP/RTP
              ┌────────────────┼────────────────┐
              ▼                ▼                 ▼
      ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
      │ Ant Cellular  │ │   Twilio     │ │  Web Browser │
      │  VitalPBX     │ │  (optional)  │ │  (WebSocket) │
      │+233308249843  │ │              │ │              │
      └──────────────┘ └──────────────┘ └──────────────┘
```

---

## 3. What Needs to Be Built

### Phase A: Fix LOAD Build Issues (Day 1)

**Priority: CRITICAL — blocks everything**

| Task | File | Issue |
|------|------|-------|
| Fix Twilio SDK types | `backend/src/telephony/twilio.ts` | Invalid properties: `phoneNumber`, `statusCallbackUrl` |
| Fix unused React imports | `frontend/src/pages/Dashboard.tsx` | Unused `React` import |
| Fix unused React imports | `frontend/src/pages/PhoneNumbers.tsx` | Unused `React` import |
| Fix unused React imports | `frontend/src/pages/WebCall.tsx` | Unused `React` import |

### Phase B: SIP Trunk Integration (Days 2-5)

**Priority: HIGH — this is what makes LOAD replace VAPI for Ant Cellular**

LOAD needs a SIP integration layer to connect with the existing Asterisk proxy at `148.251.0.46` which is already registered with Ant Cellular's VitalPBX.

#### B.1 SIP/Asterisk Integration Architecture

```
Inbound Call Flow:
  Caller → Ant Cellular → Asterisk Proxy (148.251.0.46)
    → SIP INVITE to LOAD backend
    → LOAD creates call session
    → Voice pipeline handles conversation

Outbound Call Flow:
  LOAD API request → LOAD creates call
    → SIP INVITE to Asterisk Proxy
    → Asterisk routes to Ant Cellular
    → Ant Cellular connects to recipient
    → Voice pipeline handles conversation
```

#### B.2 Implementation Options for SIP in LOAD

**Option 1: WebSocket Bridge via Asterisk (Recommended)**
- Asterisk handles all SIP signaling
- LOAD connects to Asterisk via ARI (Asterisk REST Interface) or WebSocket
- Audio flows: Asterisk ↔ LOAD via RTP/WebSocket
- LOAD only needs to handle audio streams, not SIP protocol

**Option 2: Native SIP in Node.js**
- Use `drachtio-srf` or `jssip` Node.js SIP library
- LOAD directly handles SIP INVITE/BYE/etc.
- More complex but eliminates Asterisk dependency for future

**Option 3: Twilio as SIP-to-WebSocket Bridge**
- Buy a Twilio number
- Configure Twilio to bridge calls to LOAD's WebSocket endpoint
- Use Twilio's `<Stream>` TwiML to send audio to LOAD
- Simplest to implement, but adds Twilio cost

#### B.3 Recommended: Option 1 (Asterisk ARI + WebSocket)

The Asterisk proxy at `148.251.0.46` is already running and registered with Ant Cellular. We extend it:

```
Asterisk (148.251.0.46)
  ├── pjsip.conf: Registered with Ant Cellular VitalPBX
  ├── ARI enabled: HTTP API for call control
  ├── extensions.conf: Route inbound → ARI app "load"
  └── WebSocket: Stream audio to LOAD backend

LOAD Backend
  ├── src/telephony/asterisk-ari.ts: ARI client
  ├── src/telephony/sip-audio-stream.ts: WebSocket audio bridge
  └── src/websocket/handler.ts: Extended for SIP audio sessions
```

### Phase C: Telephony Implementation in LOAD (Days 3-8)

#### C.1 Inbound Call Handler

```typescript
// New: src/telephony/asterisk-ari.ts
// Connects to Asterisk ARI, listens for StasisStart events
// When call arrives:
//   1. Look up phone number → find assigned assistant
//   2. Create call record (type: INBOUND)
//   3. Answer the call via ARI
//   4. Create external media channel (WebSocket audio)
//   5. Bridge caller channel + media channel
//   6. Start voice pipeline session
//   7. Process audio: STT → LLM → TTS loop
//   8. On hangup: end session, persist transcript, fire webhook
```

#### C.2 Outbound Call Handler

```typescript
// New: src/telephony/asterisk-outbound.ts
// When API receives POST /api/calls (type: OUTBOUND):
//   1. Validate assistant exists
//   2. Create call record (status: QUEUED)
//   3. Via ARI: originate call through Asterisk
//   4. Asterisk routes via Ant Cellular trunk
//   5. On answer: create media channel + bridge
//   6. Start voice pipeline session
//   7. Play first message via TTS
//   8. Process conversation loop
//   9. On hangup/end: persist transcript, fire webhook
```

#### C.3 Call Recording

```typescript
// New: src/telephony/recording.ts
// During call:
//   1. ARI record the bridge (mixed audio)
//   2. Store recording to local filesystem or S3
//   3. Update call record with recording URL
//   4. Access control: only org members can download
```

### Phase D: DiaServe1 Integration (Days 5-10)

#### D.1 Replace VapiClient with LoadClient

Create a new Python client in DiaServe1 that talks to LOAD's API instead of VAPI's:

```python
# DiaServe1/backend/app/integration/load_client.py

class LoadClient:
    """Client for LOAD voice AI platform (replaces VapiClient)"""

    def __init__(self):
        self.base_url = os.getenv("LOAD_API_URL", "http://localhost:3000")
        self.api_key = os.getenv("LOAD_API_KEY", "")  # load_xxxx format

    async def make_call(
        self,
        phone_number: str,
        assistant_id: str,
        customer_name: str = None,
        metadata: dict = None
    ) -> dict:
        """Initiate a single outbound call"""
        # POST /api/calls
        # { type: "OUTBOUND", assistantId, customerNumber, metadata }

    async def make_bulk_calls(
        self,
        recipients: list,
        assistant_id: str
    ) -> dict:
        """Initiate bulk outbound calls (campaign)"""
        # POST /api/campaigns
        # { assistantId, contacts: [...], status: "RUNNING" }

    async def get_call(self, call_id: str) -> dict:
        """Get call details including transcript"""
        # GET /api/calls/:id

    async def list_calls(self, **filters) -> dict:
        """List calls with filtering"""
        # GET /api/calls?status=...&type=...
```

#### D.2 Update Webhook Handler

```python
# DiaServe1/backend/app/api/voice/router.py
# Update webhook to handle LOAD's format instead of VAPI's

@router.post("/webhook/load")
async def load_webhook(payload: Dict[str, Any]):
    """Receive webhook events from LOAD platform"""
    event_type = payload.get("event")  # call.started, call.ended, etc.
    call_data = payload.get("data", {})

    if event_type == "call.ended":
        # Extract: duration, transcript, recording_url, outcome
        # Create voice_calls record in MongoDB
        # Trigger lead creation/escalation if applicable

    elif event_type == "call.started":
        # Update call status in real-time

    elif event_type == "transcript.update":
        # Store live transcript updates
```

#### D.3 Update Campaign Service

```python
# DiaServe1/backend/app/services/campaign_service.py
# Replace vapi_service calls with load_client calls

async def _launch_voice_campaign(self, campaign, contacts, org_id):
    # Instead of: self.vapi_service.make_bulk_calls(...)
    # Use: self.load_client.create_campaign(...)

    # Create campaign in LOAD with:
    #   - assistant_id from campaign.message_template.voice_id
    #   - contacts list with phone numbers and metadata
    #   - webhook URL for DiaServe1 to receive updates
```

### Phase E: Webhook Delivery System in LOAD (Days 6-9)

#### E.1 BullMQ Webhook Queue

```typescript
// New: src/modules/webhooks/delivery.ts
//
// When call events occur:
//   1. Create BullMQ job with: { webhookId, event, payload }
//   2. Worker processes job:
//      a. POST payload to webhook URL
//      b. Sign with HMAC-SHA256 (X-Load-Signature header)
//      c. If fails: retry 3x with exponential backoff (1s, 5s, 30s)
//      d. Log delivery status
```

#### E.2 Events to Deliver

| Event | When | Payload |
|-------|------|---------|
| `call.started` | Call connects | `{ callId, type, assistantId, customerNumber, startedAt }` |
| `call.ended` | Call ends | `{ callId, duration, endReason, transcript, recordingUrl }` |
| `call.failed` | Call fails | `{ callId, error, failReason }` |
| `transcript.update` | Each turn | `{ callId, role, text, timestamp }` |
| `campaign.progress` | Batch update | `{ campaignId, completed, failed, remaining }` |
| `campaign.completed` | Campaign done | `{ campaignId, stats }` |

### Phase F: Campaign Execution Engine (Days 8-12)

```typescript
// New: src/modules/campaigns/engine.ts
//
// Campaign execution via BullMQ:
//   1. POST /api/campaigns/:id/start → creates "campaign:execute" job
//   2. Worker picks up job:
//      a. Load campaign contacts
//      b. For each contact (respecting maxConcurrent):
//         - Create outbound call via telephony layer
//         - Track call status
//         - Update campaign stats
//      c. Handle retries for failed calls
//      d. Fire campaign.progress webhooks
//      e. On completion: fire campaign.completed webhook
```

---

## 4. Environment Configuration

### LOAD .env Additions

```bash
# Existing (already in .env)
DATABASE_URL=postgresql://load:load_password@localhost:5432/load_db
REDIS_URL=redis://localhost:6379
JWT_SECRET=dev-jwt-secret-minimum-16-chars
OPENAI_API_KEY=sk-your-openai-api-key
PORT=3000

# New: Asterisk ARI Connection
ASTERISK_ARI_URL=http://148.251.0.46:8088
ASTERISK_ARI_USERNAME=load
ASTERISK_ARI_PASSWORD=your-ari-password
ASTERISK_ARI_APP=load

# New: SIP Configuration
SIP_DOMAIN=148.251.0.46
SIP_PORT=5060
SIP_CALLER_ID=+233308249843

# New: Webhook signing
WEBHOOK_SECRET=your-webhook-signing-secret

# Optional: Twilio (fallback/alternative)
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token

# Optional: Call Recording Storage
RECORDING_STORAGE=local  # or "s3"
RECORDING_PATH=/var/lib/load/recordings
# S3_BUCKET=your-bucket
# S3_REGION=us-east-1
# S3_ACCESS_KEY=...
# S3_SECRET_KEY=...
```

### DiaServe1 .env Additions

```bash
# Replace VAPI_API_KEY with:
LOAD_API_URL=http://localhost:3000    # or https://load.yourdomain.com
LOAD_API_KEY=load_your-api-key-here   # Generated from LOAD dashboard

# Webhook URL that LOAD will POST to:
LOAD_WEBHOOK_URL=http://localhost:8000/api/v1/voice/webhook/load
```

### Asterisk Configuration Updates

The existing Asterisk proxy at `148.251.0.46` needs ARI enabled:

```ini
; /etc/asterisk/ari.conf (add to existing config)
[general]
enabled = yes
pretty = yes

[load]
type = user
read_only = no
password = your-ari-password

; /etc/asterisk/http.conf
[general]
enabled = yes
bindaddr = 0.0.0.0
bindport = 8088

; /etc/asterisk/extensions.conf (update existing dialplan)
[from-ant-cellular]
; When Ant Cellular sends an inbound call:
exten => _X.,1,NoOp(Inbound call from Ant Cellular: ${EXTEN})
same => n,Stasis(load,inbound,${EXTEN})  ; Hand to ARI app "load"
same => n,Hangup()

[to-ant-cellular]
; For outbound calls via Ant Cellular trunk:
exten => _X.,1,NoOp(Outbound call to: ${EXTEN})
same => n,Dial(PJSIP/${EXTEN}@ant-cellular-trunk,60)
same => n,Hangup()
```

---

## 5. API Mapping: VAPI → LOAD

| VAPI Endpoint | LOAD Equivalent | Notes |
|--------------|-----------------|-------|
| `POST /call` | `POST /api/calls` | Same concept, different payload |
| `GET /call/:id` | `GET /api/calls/:id` | Direct mapping |
| `GET /call?phoneNumberId=X` | `GET /api/calls?phoneNumberId=X` | Same filtering |
| `POST /assistant` | `POST /api/assistants` | Similar schema |
| `GET /assistant/:id` | `GET /api/assistants/:id` | Direct mapping |
| `POST /phone-number` | `POST /api/phone-numbers` | Via Twilio or SIP trunk |
| Webhook: `call.ended` | Webhook: `call.ended` | Different payload format |
| Webhook: `call-ended` | Webhook: `call.ended` | LOAD normalizes event names |
| SIP trunk credential | Asterisk ARI config | SIP handled by Asterisk, not LOAD directly |

### Payload Mapping

**VAPI Outbound Call:**
```json
{
  "assistantId": "cde22a1e-...",
  "customer": {
    "number": "+233XXXXXXXXX",
    "numberE164CheckEnabled": false
  },
  "phoneNumberId": "6d828206-..."
}
```

**LOAD Outbound Call:**
```json
{
  "assistantId": "uuid-here",
  "type": "OUTBOUND",
  "customerNumber": "+233XXXXXXXXX",
  "phoneNumberId": "uuid-here",
  "metadata": {
    "organization_id": "org-123",
    "contact_id": "contact-456"
  }
}
```

**VAPI Webhook (call.ended):**
```json
{
  "type": "call.ended",
  "call": {
    "customer": { "name": "John", "number": "+233..." },
    "duration": 120,
    "metadata": { "organization_id": "org-123" }
  }
}
```

**LOAD Webhook (call.ended):**
```json
{
  "event": "call.ended",
  "timestamp": "2026-02-21T10:30:00Z",
  "data": {
    "callId": "uuid",
    "type": "OUTBOUND",
    "assistantId": "uuid",
    "customerNumber": "+233...",
    "duration": 120,
    "endReason": "completed",
    "transcript": [
      { "role": "assistant", "text": "Hello...", "timestamp": "..." },
      { "role": "user", "text": "Hi...", "timestamp": "..." }
    ],
    "recordingUrl": "/api/calls/uuid/recording",
    "metadata": { "organization_id": "org-123" }
  },
  "signature": "hmac-sha256-signature"
}
```

---

## 6. Migration Checklist

### Pre-Migration

- [ ] Fix LOAD build errors (backend TypeScript + frontend React imports)
- [ ] Verify LOAD backend starts and tests pass
- [ ] Verify LOAD frontend builds and renders
- [ ] Set up LOAD `.env` with OpenAI API key
- [ ] Create LOAD user account and API key via dashboard
- [ ] Create assistant in LOAD matching current VAPI assistant config

### Asterisk Setup

- [ ] Enable ARI on existing Asterisk proxy (148.251.0.46)
- [ ] Configure ARI user credentials
- [ ] Update Asterisk dialplan to route inbound calls to ARI app
- [ ] Test ARI connection from LOAD backend
- [ ] Verify Asterisk is still registered with Ant Cellular

### LOAD Telephony Implementation

- [ ] Implement Asterisk ARI client in LOAD (`src/telephony/asterisk-ari.ts`)
- [ ] Implement audio bridge (Asterisk ↔ LOAD voice pipeline)
- [ ] Implement inbound call handler
- [ ] Implement outbound call handler
- [ ] Implement call recording
- [ ] Implement webhook delivery (BullMQ)
- [ ] Implement campaign execution engine
- [ ] Write tests for all new modules

### DiaServe1 Integration

- [ ] Create `LoadClient` in DiaServe1 (replaces `VapiClient`)
- [ ] Add LOAD webhook endpoint to DiaServe1
- [ ] Update campaign service to use LoadClient
- [ ] Update voice service to handle LOAD webhook format
- [ ] Update frontend API calls if needed
- [ ] Test outbound call via LOAD
- [ ] Test inbound call via Asterisk → LOAD
- [ ] Test bulk campaign via LOAD

### Cutover

- [ ] Run parallel: both VAPI and LOAD handling calls for 1 week
- [ ] Compare call quality, latency, transcript accuracy
- [ ] Disable VAPI integration in DiaServe1
- [ ] Remove VAPI_API_KEY from environment
- [ ] Monitor LOAD for 72 hours post-cutover

---

## 7. Cost Comparison

### VAPI Costs (Current)

| Item | Cost |
|------|------|
| Per-minute (inbound/outbound) | ~$0.05/min |
| STT included | $0 |
| LLM included | $0 |
| TTS included | $0 |
| Phone number | $2/month |
| **100 calls/month @ 3 min avg** | **~$15/month + $2** |

### LOAD Costs (Self-Hosted)

| Item | Cost |
|------|------|
| Server hosting (already running) | $0 incremental |
| OpenAI Whisper STT | ~$0.006/min |
| OpenAI GPT-4 | ~$0.03-0.06/call (depends on tokens) |
| OpenAI TTS | ~$0.015/1K chars (~$0.03/call) |
| Ant Cellular SIP (already paid) | $0 incremental |
| **100 calls/month @ 3 min avg** | **~$6-9/month** |

**Savings: ~50-60% reduction in voice AI costs**

---

## 8. Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Asterisk proxy goes down | Docker health check + auto-restart; Twilio as fallback |
| Higher latency than VAPI | LOAD runs on same server, should be lower; tune audio chunk size |
| OpenAI API outage | Add Deepgram (STT) and ElevenLabs (TTS) as fallback providers |
| Ant Cellular still doesn't route inbound | Already have Asterisk registered; issue is DID routing on their end |
| LOAD bugs in production | Run parallel with VAPI for 1 week before full cutover |
| Audio quality issues | Test with PCM 16kHz/24kHz; adjust buffer sizes if needed |

---

## 9. Success Criteria

| Metric | Target |
|--------|--------|
| Outbound call success rate | >= 95% |
| Inbound call answer rate | >= 99% (when Ant Cellular routes correctly) |
| Voice pipeline latency (STT+LLM+TTS) | < 500ms |
| Call recording availability | 100% of completed calls |
| Transcript accuracy | >= VAPI quality (same Whisper model) |
| Webhook delivery success | >= 99% (with retries) |
| Campaign execution throughput | 10 concurrent calls |
| System uptime | 99.9% |

---

## 10. Timeline

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| A: Fix build errors | 1 day | None |
| B: SIP/Asterisk integration | 4 days | Phase A |
| C: Telephony in LOAD | 6 days | Phase A, B |
| D: DiaServe1 integration | 5 days | Phase C |
| E: Webhook delivery | 3 days | Phase C |
| F: Campaign engine | 4 days | Phase C, E |
| Testing & parallel run | 7 days | All phases |
| **Total** | **~4 weeks** | |

Phases B, C, D, E can partially overlap. Realistic delivery: **3-4 weeks**.
