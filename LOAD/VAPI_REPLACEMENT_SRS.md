# LOAD as VAPI Replacement — Software Requirements Specification

## 1. Overview

This SRS details the exact technical implementation needed to make LOAD replace VAPI as the voice AI engine for DiaServe1. It covers every file to create/modify, every API contract, and step-by-step implementation instructions.

---

## 2. System Context

### 2.1 Existing Infrastructure

| Component | Location | Status |
|-----------|----------|--------|
| LOAD Backend | `/root/home/LOAD/backend` | Phases 1-2 complete, build broken |
| LOAD Frontend | `/root/home/LOAD/frontend` | Working, build broken (minor) |
| DiaServe1 Backend | `/root/home/DiaServe1/backend` | Running, uses VAPI |
| DiaServe1 Frontend | `/root/home/DiaServe1/frontend` | Running |
| Asterisk Proxy | `148.251.0.46` (Docker: kasaai-asterisk-proxy) | Running, registered with Ant Cellular |
| PostgreSQL | Docker, port 5432 | Running |
| Redis | Docker, port 6379 | Running |
| MongoDB | DiaServe1 uses this | Running |

### 2.2 Network Topology

```
Internet
  │
  ├── 148.251.0.46:5060 (Asterisk SIP proxy)
  │     ├── Registered with vitalpbx.antcellular.com
  │     ├── Extension: 308249843
  │     └── Handles SIP signaling + media
  │
  ├── 148.251.0.46:3000 (LOAD backend — to be configured)
  │     └── Fastify API + WebSocket
  │
  ├── 148.251.0.46:5173 (LOAD frontend)
  │     └── React dashboard
  │
  ├── 148.251.0.46:8000 (DiaServe1 backend)
  │     └── FastAPI
  │
  └── 148.251.0.46:3001 (DiaServe1 frontend — if separate port)
        └── React dashboard
```

---

## 3. Implementation: Phase A — Fix Build Errors

### 3.1 Backend: Fix Twilio SDK Types

**File:** `LOAD/backend/src/telephony/twilio.ts`

The Twilio SDK v4.x has different property names than what's currently coded. Fix the following:

```typescript
// WRONG (current code):
const call = await this.client.calls.create({
  phoneNumber: to,                    // ← invalid
  from: from,
  statusCallbackUrl: callbackUrl,     // ← invalid
  url: twimlUrl,
});

// CORRECT:
const call = await this.client.calls.create({
  to: to,
  from: from,
  statusCallback: callbackUrl,
  url: twimlUrl,
});
```

For phone number purchase:

```typescript
// WRONG:
const number = await this.client.incomingPhoneNumbers.create({
  phoneNumber: numberToBuy,
  voiceUrl: voiceWebhookUrl,
  statusCallbackUrl: statusWebhookUrl,
});

// CORRECT:
const number = await this.client.incomingPhoneNumbers.create({
  phoneNumber: numberToBuy,
  voiceUrl: voiceWebhookUrl,
  statusCallback: statusWebhookUrl,
});
```

### 3.2 Frontend: Fix Unused Imports

**Files to fix:**
- `LOAD/frontend/src/pages/Dashboard.tsx` — Remove `import React from 'react'` (or use it)
- `LOAD/frontend/src/pages/PhoneNumbers.tsx` — Same
- `LOAD/frontend/src/pages/WebCall.tsx` — Same

Since React 17+ with the JSX transform doesn't need the import, just remove the unused import lines.

### 3.3 Verification

```bash
# Backend
cd /root/home/LOAD/backend
npm run build    # Should succeed with 0 errors
npm test         # Should show 138 passing

# Frontend
cd /root/home/LOAD/frontend
npm run build    # Should succeed
```

---

## 4. Implementation: Phase B — Asterisk ARI Integration

### 4.1 New Dependencies

```bash
cd /root/home/LOAD/backend
npm install ari-client ws     # Asterisk ARI client + WebSocket
npm install -D @types/ws      # Already installed, verify
```

### 4.2 New File: `src/telephony/asterisk-ari.ts`

This is the core integration between LOAD and the existing Asterisk proxy.

```typescript
// src/telephony/asterisk-ari.ts

import Ari from 'ari-client';
import { config } from '@/config/index.js';
import { logger } from '@/utils/logger.js';

interface AriConfig {
  url: string;
  username: string;
  password: string;
  appName: string;
}

interface CallSession {
  channelId: string;
  bridgeId: string;
  externalMediaId: string;
  callerNumber: string;
  calledNumber: string;
  direction: 'inbound' | 'outbound';
  startedAt: Date;
}

class AsteriskAriClient {
  private client: any = null;
  private config: AriConfig;
  private activeSessions: Map<string, CallSession> = new Map();
  private onInboundCall: ((session: CallSession) => void) | null = null;
  private onCallEnd: ((channelId: string, reason: string) => void) | null = null;
  private onAudioData: ((channelId: string, audio: Buffer) => void) | null = null;

  constructor() {
    this.config = {
      url: process.env.ASTERISK_ARI_URL || 'http://148.251.0.46:8088',
      username: process.env.ASTERISK_ARI_USERNAME || 'load',
      password: process.env.ASTERISK_ARI_PASSWORD || '',
      appName: process.env.ASTERISK_ARI_APP || 'load',
    };
  }

  async connect(): Promise<void> {
    // Connect to Asterisk ARI
    // Register StasisStart handler for inbound calls
    // Register StasisEnd handler for call cleanup
    // Set up ExternalMedia channels for audio streaming
  }

  async originateCall(
    to: string,
    from: string,
    variables?: Record<string, string>
  ): Promise<string> {
    // Create outbound call via ARI
    // 1. Create a bridge
    // 2. Originate a channel to the destination via Ant Cellular trunk
    // 3. Create ExternalMedia channel for audio I/O
    // 4. Bridge all channels together
    // 5. Return channel ID as call reference
  }

  async hangup(channelId: string): Promise<void> {
    // Hang up call via ARI
    // Destroy bridge
    // Clean up session
  }

  async sendAudio(channelId: string, audio: Buffer): Promise<void> {
    // Send audio to the ExternalMedia channel
    // Audio format: PCM 16-bit, 8kHz (Asterisk standard) or 16kHz (ulaw/alaw)
  }

  // Event handlers
  onInbound(handler: (session: CallSession) => void): void {
    this.onInboundCall = handler;
  }

  onEnd(handler: (channelId: string, reason: string) => void): void {
    this.onCallEnd = handler;
  }

  onAudio(handler: (channelId: string, audio: Buffer) => void): void {
    this.onAudioData = handler;
  }
}

export const asteriskClient = new AsteriskAriClient();
```

### 4.3 New File: `src/telephony/call-bridge.ts`

Bridges Asterisk audio with LOAD's voice pipeline:

```typescript
// src/telephony/call-bridge.ts

import { asteriskClient } from './asterisk-ari.js';
import { processPipelineTurn } from '@/voice-pipeline/pipeline.js';
import { createSession, getSession, endSession } from '@/voice-pipeline/session.js';
import { callService } from '@/modules/calls/service.js';
import { webhookDelivery } from '@/modules/webhooks/delivery.js';

class CallBridge {
  // Maps Asterisk channel IDs to LOAD call session IDs
  private channelToSession: Map<string, string> = new Map();

  async initialize(): Promise<void> {
    // Register handlers with Asterisk client

    asteriskClient.onInbound(async (ariSession) => {
      // 1. Look up phone number in database
      // 2. Find assigned assistant
      // 3. Create call record (type: INBOUND, status: RINGING)
      // 4. Create voice pipeline session
      // 5. Update call status to IN_PROGRESS
      // 6. If assistant has firstMessage, synthesize and send via TTS
      // 7. Fire call.started webhook
    });

    asteriskClient.onAudio(async (channelId, audioBuffer) => {
      // 1. Get session ID from channel mapping
      // 2. Accumulate audio in session buffer
      // 3. On silence detection (or VAD trigger):
      //    - Run processPipelineTurn(sessionId, audioBuffer, config)
      //    - Send response audio back via asteriskClient.sendAudio()
      //    - Send transcript update via webhook
    });

    asteriskClient.onEnd(async (channelId, reason) => {
      // 1. Get session ID
      // 2. End voice pipeline session
      // 3. Update call record (status: ENDED, endReason, duration, transcript)
      // 4. Fire call.ended webhook with full transcript
      // 5. Clean up mappings
    });
  }

  async initiateOutbound(
    assistantId: string,
    customerNumber: string,
    callerNumber: string,
    metadata?: Record<string, unknown>
  ): Promise<string> {
    // 1. Create call record (type: OUTBOUND, status: QUEUED)
    // 2. Create voice pipeline session
    // 3. asteriskClient.originateCall(customerNumber, callerNumber)
    // 4. Map channel to session
    // 5. On answer: update status, play firstMessage
    // 6. Return call ID
  }
}

export const callBridge = new CallBridge();
```

### 4.4 Asterisk Configuration Updates

**File to create on Asterisk server:** Update existing config at `/opt/kasaai/asterisk/`

#### Enable ARI — `ari.conf`

```ini
[general]
enabled = yes
pretty = yes
allowed_origins = *

[load]
type = user
read_only = no
password = changeme-secure-password
```

#### Enable HTTP — `http.conf`

```ini
[general]
enabled = yes
bindaddr = 0.0.0.0
bindport = 8088
```

#### Update Dialplan — `extensions.conf`

```ini
; Inbound calls from Ant Cellular → hand to LOAD via ARI
[from-ant-cellular]
exten => _X.,1,NoOp(=== Inbound Call: ${CALLERID(num)} -> ${EXTEN} ===)
same  => n,Answer()
same  => n,Stasis(load,inbound,${EXTEN},${CALLERID(num)})
same  => n,Hangup()

; Outbound calls from LOAD → route via Ant Cellular trunk
[to-ant-cellular]
exten => _X.,1,NoOp(=== Outbound Call: ${CALLERID(num)} -> ${EXTEN} ===)
same  => n,Dial(PJSIP/${EXTEN}@ant-cellular-trunk,60,g)
same  => n,Hangup()

; External media for audio bridging
[load-media]
exten => s,1,NoOp(External media channel)
same  => n,Answer()
same  => n,Stasis(load,media)
same  => n,Hangup()
```

### 4.5 Audio Format Bridging

Asterisk uses 8kHz mono audio (ulaw/alaw). LOAD's pipeline uses:
- STT input: PCM 16-bit, 16kHz
- TTS output: PCM 16-bit, 24kHz

**Resampling needed:**

```typescript
// src/telephony/audio-resample.ts

// Asterisk (8kHz) → LOAD STT (16kHz): upsample 2x
export function upsample8kTo16k(input: Buffer): Buffer {
  const output = Buffer.alloc(input.length * 2);
  for (let i = 0; i < input.length; i += 2) {
    const sample = input.readInt16LE(i);
    const outIdx = i * 2;
    output.writeInt16LE(sample, outIdx);
    output.writeInt16LE(sample, outIdx + 2); // duplicate sample
  }
  return output;
}

// LOAD TTS (24kHz) → Asterisk (8kHz): downsample 3x
export function downsample24kTo8k(input: Buffer): Buffer {
  const ratio = 3;
  const output = Buffer.alloc(Math.floor(input.length / ratio));
  for (let i = 0, o = 0; i < input.length - 2 * ratio; i += 2 * ratio, o += 2) {
    output.writeInt16LE(input.readInt16LE(i), o);
  }
  return output;
}
```

**Better approach:** Configure Asterisk ExternalMedia to use 16kHz:

```ini
; In Asterisk ExternalMedia channel creation:
; format=slin16 (signed linear 16kHz)
```

This way only TTS output needs downsampling (24kHz → 16kHz).

---

## 5. Implementation: Phase C — LOAD Telephony Endpoints

### 5.1 Update Call Routes

**File:** `LOAD/backend/src/modules/calls/routes.ts`

Add outbound call creation and inbound webhook:

```typescript
// New route: POST /api/calls (outbound)
app.post('/api/calls', {
  preHandler: [authMiddleware],
  schema: {
    body: createCallSchema,
    response: { 201: callResponseSchema }
  }
}, async (request, reply) => {
  const { type, assistantId, customerNumber, phoneNumberId, metadata } = request.body;

  if (type === 'OUTBOUND') {
    // Validate assistant exists and belongs to org
    // Validate phone number if provided
    // Initiate call via callBridge.initiateOutbound()
    // Return call record
  }
});

// New route: POST /api/calls/:id/end (force end call)
app.post('/api/calls/:id/end', {
  preHandler: [authMiddleware],
}, async (request, reply) => {
  // Look up call
  // If active: hangup via callBridge
  // Update call record
});
```

### 5.2 Update Call Service

**File:** `LOAD/backend/src/modules/calls/service.ts`

Add methods for telephony calls:

```typescript
// New methods needed:

async createOutboundCall(data: {
  organizationId: string;
  assistantId: string;
  customerNumber: string;
  phoneNumberId?: string;
  metadata?: Record<string, unknown>;
}): Promise<Call> {
  // 1. Create call record with status QUEUED
  // 2. Initiate call via callBridge
  // 3. Return call record
}

async handleInboundCall(data: {
  phoneNumber: string;
  callerNumber: string;
  callerName?: string;
}): Promise<Call> {
  // 1. Look up phone number → find org + assistant
  // 2. Create call record with type INBOUND, status RINGING
  // 3. Return call record with assistant config
}

async updateCallTranscript(callId: string, transcript: TranscriptEntry[]): Promise<void> {
  // Persist transcript to database
}

async setCallRecording(callId: string, recordingUrl: string): Promise<void> {
  // Set recording URL on call record
}
```

### 5.3 Update Phone Number Service

**File:** `LOAD/backend/src/modules/phone-numbers/service.ts`

Add SIP trunk phone number support (in addition to Twilio):

```typescript
// Support both Twilio and SIP trunk numbers
async createSipNumber(data: {
  organizationId: string;
  number: string;      // e.g., +233308249843
  provider: 'SIP_TRUNK';
  sipDomain?: string;   // e.g., vitalpbx.antcellular.com
  assistantId?: string;
  name?: string;
}): Promise<PhoneNumber> {
  // Create phone number record with provider = SIP_TRUNK
  // No Twilio API call needed
  // Just register in database for routing
}

async findByNumber(number: string): Promise<PhoneNumber | null> {
  // Look up by E.164 number
  // Used by inbound call handler to find assigned assistant
}
```

### 5.4 New Prisma Schema Updates

**File:** `LOAD/backend/prisma/schema.prisma`

```prisma
// Update PhoneNumber model to support SIP trunk
model PhoneNumber {
  id             String   @id @default(uuid())
  organizationId String
  number         String   @unique
  twilioSid      String?  @unique  // nullable for SIP trunk numbers
  assistantId    String?
  name           String?
  provider       String   // "TWILIO" or "SIP_TRUNK"
  sipDomain      String?  // e.g., "vitalpbx.antcellular.com"
  status         String   @default("ACTIVE")
  createdAt      DateTime @default(now())
  updatedAt      DateTime @updatedAt

  organization Organization @relation(fields: [organizationId], references: [id])
  assistant    Assistant?   @relation(fields: [assistantId], references: [id])
  calls        Call[]

  @@index([organizationId])
  @@index([number])
}

// Update Call model to support telephony metadata
model Call {
  // ... existing fields ...
  externalCallId  String?  // Asterisk channel ID or Twilio SID
  callerNumber    String?  // Who initiated the call (for inbound)

  // ... existing relations ...
}
```

---

## 6. Implementation: Phase D — DiaServe1 Integration

### 6.1 New File: `DiaServe1/backend/app/integration/load_client.py`

```python
"""
LOAD Voice AI Platform Client
Replaces VapiClient for voice call management
"""
import os
import httpx
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class LoadClient:
    """Async client for LOAD voice AI platform API"""

    def __init__(self):
        self.base_url = os.getenv("LOAD_API_URL", "http://localhost:3000")
        self.api_key = os.getenv("LOAD_API_KEY", "")
        self.timeout = 30.0

    @property
    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.startswith("load_"))

    async def create_assistant(
        self,
        name: str,
        system_prompt: str,
        first_message: str = None,
        voice_id: str = "alloy",
        model: str = "gpt-4",
    ) -> Dict[str, Any]:
        """Create a voice assistant in LOAD"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/assistants",
                headers=self._headers,
                json={
                    "name": name,
                    "model": {
                        "provider": "openai",
                        "model": model,
                        "temperature": 0.7,
                        "maxTokens": 1000,
                        "systemPrompt": system_prompt,
                    },
                    "voice": {
                        "provider": "openai",
                        "voiceId": voice_id,
                        "speed": 1.0,
                    },
                    "transcriber": {
                        "provider": "openai",
                        "model": "whisper-1",
                        "language": "en",
                    },
                    "firstMessage": first_message,
                },
            )
            response.raise_for_status()
            return response.json()["data"]

    async def make_call(
        self,
        phone_number: str,
        assistant_id: str,
        customer_name: str = None,
        metadata: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Initiate a single outbound voice call"""
        if not self.is_configured():
            logger.warning("LOAD API key not configured, skipping call")
            return {"error": "not_configured"}

        payload = {
            "type": "OUTBOUND",
            "assistantId": assistant_id,
            "customerNumber": phone_number,
            "metadata": {
                **(metadata or {}),
                "customerName": customer_name,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/calls",
                    headers=self._headers,
                    json=payload,
                )
                response.raise_for_status()
                result = response.json()
                logger.info(f"LOAD call initiated: {result['data']['id']}")
                return result["data"]
        except httpx.HTTPError as e:
            logger.error(f"LOAD call failed: {e}")
            return {"error": str(e)}

    async def make_bulk_calls(
        self,
        recipients: List[Dict[str, Any]],
        assistant_id: str,
    ) -> Dict[str, Any]:
        """Initiate bulk calls via LOAD campaign"""
        if not self.is_configured():
            logger.warning("LOAD API key not configured, skipping bulk calls")
            return {"initiated": 0, "failed": len(recipients)}

        contacts = [
            {
                "name": r.get("name", ""),
                "number": r["phone"],
                "metadata": r.get("data", {}),
            }
            for r in recipients
        ]

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Create campaign
                response = await client.post(
                    f"{self.base_url}/api/campaigns",
                    headers=self._headers,
                    json={
                        "name": f"DiaServe Campaign {len(contacts)} contacts",
                        "assistantId": assistant_id,
                        "contacts": contacts,
                        "schedule": {"maxConcurrent": 5},
                    },
                )
                response.raise_for_status()
                campaign = response.json()["data"]

                # Start campaign
                await client.post(
                    f"{self.base_url}/api/campaigns/{campaign['id']}/start",
                    headers=self._headers,
                )

                return {
                    "campaignId": campaign["id"],
                    "initiated": len(contacts),
                    "failed": 0,
                }
        except httpx.HTTPError as e:
            logger.error(f"LOAD bulk calls failed: {e}")
            return {"initiated": 0, "failed": len(recipients), "error": str(e)}

    async def get_call(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Get call details including transcript"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/calls/{call_id}",
                    headers=self._headers,
                )
                response.raise_for_status()
                return response.json()["data"]
        except httpx.HTTPError as e:
            logger.error(f"LOAD get call failed: {e}")
            return None

    async def list_calls(
        self,
        status: str = None,
        call_type: str = None,
        page: int = 1,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """List calls with filtering"""
        params = {"page": page, "limit": limit}
        if status:
            params["status"] = status
        if call_type:
            params["type"] = call_type

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/calls",
                    headers=self._headers,
                    params=params,
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"LOAD list calls failed: {e}")
            return {"data": [], "meta": {"total": 0}}
```

### 6.2 Update Webhook Handler

**File:** `DiaServe1/backend/app/api/voice/router.py`

Add new endpoint for LOAD webhooks alongside existing VAPI webhook:

```python
@router.post("/webhook/load")
async def load_webhook(
    request: Request,
    payload: Dict[str, Any],
):
    """Receive webhook events from LOAD platform"""
    # Verify HMAC signature
    signature = request.headers.get("X-Load-Signature", "")
    # TODO: Verify signature with WEBHOOK_SECRET

    event_type = payload.get("event", "")
    data = payload.get("data", {})
    org_id = data.get("metadata", {}).get("organization_id", "")

    if event_type == "call.started":
        logger.info(f"LOAD call started: {data.get('callId')}")
        # Could update real-time UI

    elif event_type == "call.ended":
        # Create voice call record in MongoDB
        call_record = {
            "organization_id": org_id,
            "caller_name": data.get("metadata", {}).get("customerName", "Unknown"),
            "caller_phone": data.get("customerNumber", ""),
            "direction": "outbound" if data.get("type") == "OUTBOUND" else "inbound",
            "status": "completed",
            "outcome": _map_outcome(data.get("endReason", "")),
            "duration_seconds": data.get("duration", 0),
            "assistant_id": data.get("assistantId", ""),
            "transcript": data.get("transcript", []),
            "recording_url": data.get("recordingUrl", ""),
            "metadata": data.get("metadata", {}),
        }
        await voice_service.create_call(call_record)

        # Auto-create/escalate lead if applicable
        if data.get("customerNumber"):
            await _maybe_create_lead(call_record, org_id)

    elif event_type == "transcript.update":
        # Real-time transcript update (for live monitoring)
        pass

    elif event_type == "campaign.completed":
        # Campaign finished
        logger.info(f"LOAD campaign completed: {data.get('campaignId')}")

    return {"status": "ok"}


def _map_outcome(end_reason: str) -> str:
    """Map LOAD end reasons to DiaServe1 outcomes"""
    mapping = {
        "completed": "information_provided",
        "customer_hangup": "information_provided",
        "assistant_hangup": "information_provided",
        "transfer": "transferred",
        "voicemail": "voicemail",
        "no_answer": "no_outcome",
        "busy": "no_outcome",
        "failed": "no_outcome",
    }
    return mapping.get(end_reason, "no_outcome")
```

### 6.3 Update Campaign Service

**File:** `DiaServe1/backend/app/services/campaign_service.py`

Replace VAPI calls with LOAD calls:

```python
# At top of file, add:
from app.integration.load_client import LoadClient

# In __init__:
self.load_client = LoadClient()

# Replace _launch_voice_campaign method:
async def _launch_voice_campaign(
    self, campaign, contacts, organization_id: str
):
    """Launch voice campaign via LOAD platform"""
    assistant_id = campaign.message_template.voice_id  # LOAD assistant ID

    recipients = [
        {
            "phone": contact.phone,
            "name": contact.name or "Customer",
            "data": {
                "contact_id": str(contact.id),
                "organization_id": organization_id,
                "property_type_preferences": getattr(
                    contact, "property_type_preferences", []
                ),
                "location_preferences": getattr(
                    contact, "location_preferences", []
                ),
            },
        }
        for contact in contacts
        if contact.phone
    ]

    if not recipients:
        logger.warning(f"Campaign {campaign.id}: No valid phone numbers")
        return

    result = await self.load_client.make_bulk_calls(recipients, assistant_id)

    # Update campaign stats
    campaign.stats = {
        "total": len(recipients),
        "initiated": result.get("initiated", 0),
        "failed": result.get("failed", 0),
        "campaign_id_load": result.get("campaignId", ""),
    }
```

### 6.4 Update DiaServe1 Environment

**File:** `DiaServe1/backend/.env` — add:

```bash
# LOAD Voice AI Platform (replaces VAPI)
LOAD_API_URL=http://localhost:3000
LOAD_API_KEY=load_your-generated-api-key
```

---

## 7. Implementation: Phase E — Webhook Delivery System

### 7.1 New File: `LOAD/backend/src/modules/webhooks/delivery.ts`

```typescript
// src/modules/webhooks/delivery.ts

import { Queue, Worker, Job } from 'bullmq';
import { createHmac } from 'crypto';
import { prisma } from '@/database/client.js';
import { config } from '@/config/index.js';
import { logger } from '@/utils/logger.js';

interface WebhookJob {
  webhookId: string;
  url: string;
  secret: string;
  event: string;
  payload: Record<string, unknown>;
  attempt: number;
}

const QUEUE_NAME = 'webhook-delivery';

// Queue for webhook delivery jobs
const webhookQueue = new Queue(QUEUE_NAME, {
  connection: { url: config.redisUrl },
  defaultJobOptions: {
    attempts: 3,
    backoff: {
      type: 'exponential',
      delay: 1000, // 1s, 5s, 25s
    },
    removeOnComplete: 1000,
    removeOnFail: 5000,
  },
});

// Worker processes webhook deliveries
const webhookWorker = new Worker(
  QUEUE_NAME,
  async (job: Job<WebhookJob>) => {
    const { url, secret, event, payload } = job.data;

    const body = JSON.stringify({ event, data: payload, timestamp: new Date().toISOString() });
    const signature = createHmac('sha256', secret).update(body).digest('hex');

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Load-Signature': signature,
        'X-Load-Event': event,
      },
      body,
      signal: AbortSignal.timeout(30000), // 30s timeout
    });

    if (!response.ok) {
      throw new Error(`Webhook delivery failed: ${response.status} ${response.statusText}`);
    }

    logger.info(`Webhook delivered: ${event} → ${url} (${response.status})`);
  },
  { connection: { url: config.redisUrl } }
);

// Fire webhook event to all registered webhooks for an organization
export async function fireWebhookEvent(
  organizationId: string,
  event: string,
  payload: Record<string, unknown>
): Promise<void> {
  const webhooks = await prisma.webhook.findMany({
    where: {
      organizationId,
      active: true,
      events: { has: event },
    },
  });

  for (const webhook of webhooks) {
    await webhookQueue.add(`${event}-${webhook.id}`, {
      webhookId: webhook.id,
      url: webhook.url,
      secret: webhook.secret,
      event,
      payload,
      attempt: 1,
    });
  }
}

export { webhookQueue, webhookWorker };
```

### 7.2 Integrate Webhook Firing into Call Lifecycle

**File:** `LOAD/backend/src/telephony/call-bridge.ts`

At each call lifecycle event, fire the webhook:

```typescript
import { fireWebhookEvent } from '@/modules/webhooks/delivery.js';

// When call starts:
await fireWebhookEvent(call.organizationId, 'call.started', {
  callId: call.id,
  type: call.type,
  assistantId: call.assistantId,
  customerNumber: call.customerNumber,
  startedAt: new Date().toISOString(),
});

// When transcript updates:
await fireWebhookEvent(call.organizationId, 'transcript.update', {
  callId: call.id,
  role: 'user', // or 'assistant'
  text: transcriptText,
  timestamp: new Date().toISOString(),
});

// When call ends:
await fireWebhookEvent(call.organizationId, 'call.ended', {
  callId: call.id,
  type: call.type,
  assistantId: call.assistantId,
  customerNumber: call.customerNumber,
  duration: durationSeconds,
  endReason: reason,
  transcript: fullTranscript,
  recordingUrl: recordingUrl || null,
  metadata: call.metadata,
});
```

---

## 8. Implementation: Phase F — Campaign Execution Engine

### 8.1 New File: `LOAD/backend/src/modules/campaigns/engine.ts`

```typescript
// src/modules/campaigns/engine.ts

import { Queue, Worker, Job } from 'bullmq';
import { prisma } from '@/database/client.js';
import { callBridge } from '@/telephony/call-bridge.js';
import { fireWebhookEvent } from '@/modules/webhooks/delivery.js';
import { config } from '@/config/index.js';
import { logger } from '@/utils/logger.js';

interface CampaignJob {
  campaignId: string;
  organizationId: string;
}

interface CallJob {
  campaignId: string;
  organizationId: string;
  assistantId: string;
  contact: { name: string; number: string; metadata?: Record<string, unknown> };
  phoneNumberId?: string;
}

const CAMPAIGN_QUEUE = 'campaign-execute';
const CALL_QUEUE = 'campaign-calls';

const campaignQueue = new Queue(CAMPAIGN_QUEUE, {
  connection: { url: config.redisUrl },
});

const callQueue = new Queue(CALL_QUEUE, {
  connection: { url: config.redisUrl },
  defaultJobOptions: {
    attempts: 2,
    backoff: { type: 'fixed', delay: 60000 }, // retry after 1 min
  },
});

// Campaign orchestrator worker
const campaignWorker = new Worker(
  CAMPAIGN_QUEUE,
  async (job: Job<CampaignJob>) => {
    const { campaignId, organizationId } = job.data;

    const campaign = await prisma.campaign.findUnique({
      where: { id: campaignId },
    });

    if (!campaign || campaign.status !== 'RUNNING') return;

    const contacts = campaign.contacts as any[];
    const maxConcurrent = (campaign.schedule as any)?.maxConcurrent || 5;

    // Queue individual calls
    for (const contact of contacts) {
      await callQueue.add(`call-${contact.number}`, {
        campaignId,
        organizationId,
        assistantId: campaign.assistantId,
        contact,
        phoneNumberId: campaign.phoneNumberId,
      });
    }

    // Rate limit: process maxConcurrent at a time
    // BullMQ handles this via concurrency setting on worker
  },
  { connection: { url: config.redisUrl } }
);

// Individual call worker
const callWorker = new Worker(
  CALL_QUEUE,
  async (job: Job<CallJob>) => {
    const { campaignId, organizationId, assistantId, contact } = job.data;

    try {
      const callId = await callBridge.initiateOutbound(
        assistantId,
        contact.number,
        '+233308249843', // caller ID
        {
          campaignId,
          organization_id: organizationId,
          customerName: contact.name,
          ...contact.metadata,
        }
      );

      // Update campaign stats
      await updateCampaignStats(campaignId, 'completed');

      logger.info(`Campaign call completed: ${contact.number} → ${callId}`);
    } catch (error) {
      await updateCampaignStats(campaignId, 'failed');
      throw error; // Let BullMQ handle retry
    }
  },
  {
    connection: { url: config.redisUrl },
    concurrency: 5, // max concurrent calls
  }
);

async function updateCampaignStats(
  campaignId: string,
  result: 'completed' | 'failed'
): Promise<void> {
  // Atomic update campaign stats
  const campaign = await prisma.campaign.findUnique({
    where: { id: campaignId },
  });

  if (!campaign) return;

  const stats = (campaign.stats as any) || { total: 0, completed: 0, failed: 0, inProgress: 0 };
  const updatedStats = {
    ...stats,
    [result]: stats[result] + 1,
    inProgress: Math.max(0, stats.inProgress - 1),
  };

  await prisma.campaign.update({
    where: { id: campaignId },
    data: { stats: updatedStats },
  });

  // Check if campaign is done
  if (updatedStats.completed + updatedStats.failed >= updatedStats.total) {
    await prisma.campaign.update({
      where: { id: campaignId },
      data: { status: 'COMPLETED' },
    });

    await fireWebhookEvent(campaign.organizationId, 'campaign.completed', {
      campaignId,
      stats: updatedStats,
    });
  }
}

// Start campaign
export async function startCampaign(campaignId: string): Promise<void> {
  const campaign = await prisma.campaign.findUnique({
    where: { id: campaignId },
  });

  if (!campaign) throw new Error('Campaign not found');

  const contacts = campaign.contacts as any[];

  await prisma.campaign.update({
    where: { id: campaignId },
    data: {
      status: 'RUNNING',
      stats: { total: contacts.length, completed: 0, failed: 0, inProgress: 0 },
    },
  });

  await campaignQueue.add(`campaign-${campaignId}`, {
    campaignId,
    organizationId: campaign.organizationId,
  });
}

export { campaignQueue, callQueue, campaignWorker, callWorker };
```

---

## 9. LOAD Startup Sequence Update

**File:** `LOAD/backend/src/app.ts`

Add telephony initialization to the startup sequence:

```typescript
// After existing setup (database, routes, middleware):

// Initialize telephony
import { asteriskClient } from '@/telephony/asterisk-ari.js';
import { callBridge } from '@/telephony/call-bridge.js';
import { webhookWorker } from '@/modules/webhooks/delivery.js';
import { campaignWorker, callWorker } from '@/modules/campaigns/engine.js';

// Connect to Asterisk ARI (if configured)
if (process.env.ASTERISK_ARI_URL) {
  await asteriskClient.connect();
  await callBridge.initialize();
  logger.info('Asterisk ARI connected, telephony ready');
} else {
  logger.warn('ASTERISK_ARI_URL not set, telephony disabled (web calls only)');
}

// Start BullMQ workers
webhookWorker.on('completed', (job) => {
  logger.debug(`Webhook delivered: ${job.name}`);
});

campaignWorker.on('failed', (job, err) => {
  logger.error(`Campaign job failed: ${job?.name}`, err);
});

callWorker.on('failed', (job, err) => {
  logger.error(`Campaign call failed: ${job?.name}`, err);
});
```

---

## 10. Testing Requirements

### 10.1 New Test Files Needed

| File | Tests |
|------|-------|
| `src/telephony/asterisk-ari.test.ts` | ARI connection, originate, hangup, event handling |
| `src/telephony/call-bridge.test.ts` | Inbound routing, outbound initiation, audio bridging |
| `src/telephony/audio-resample.test.ts` | Upsample/downsample correctness |
| `src/modules/webhooks/delivery.test.ts` | Queue, delivery, HMAC signing, retry |
| `src/modules/campaigns/engine.test.ts` | Campaign start, call queuing, stats, completion |
| `src/modules/calls/routes.test.ts` | Outbound call creation, validation |
| `src/modules/phone-numbers/service.test.ts` | SIP trunk number creation, lookup |

### 10.2 Integration Tests

```bash
# Test Asterisk ARI connection (requires running Asterisk)
ASTERISK_ARI_URL=http://148.251.0.46:8088 npx vitest run src/telephony/

# Test webhook delivery (requires Redis)
npx vitest run src/modules/webhooks/

# Test campaign engine (requires Redis)
npx vitest run src/modules/campaigns/
```

### 10.3 End-to-End Test Scenario

1. Create assistant via API
2. Register SIP trunk phone number (+233308249843)
3. Assign assistant to phone number
4. Register webhook URL
5. Simulate inbound call (via Asterisk test)
6. Verify: call record created, voice pipeline engaged, transcript generated
7. Verify: webhook delivered with call.started and call.ended events
8. Create outbound call via API
9. Verify: call placed through Asterisk, conversation happens, webhook delivered
10. Create campaign with 3 contacts
11. Start campaign
12. Verify: 3 calls placed, stats updated, campaign.completed webhook fired

---

## 11. Monitoring & Debugging

### 11.1 LOAD Logs

```bash
# Backend logs (Fastify/Pino)
docker logs -f load-backend

# Specific log filtering
docker logs load-backend 2>&1 | grep "telephony"
docker logs load-backend 2>&1 | grep "webhook"
docker logs load-backend 2>&1 | grep "campaign"
```

### 11.2 Asterisk Monitoring

```bash
# Check registration with Ant Cellular
docker exec kasaai-asterisk-proxy asterisk -rx "pjsip show registrations"

# Check active channels
docker exec kasaai-asterisk-proxy asterisk -rx "core show channels"

# Check ARI connections
docker exec kasaai-asterisk-proxy asterisk -rx "ari show apps"

# Live call debug
docker exec kasaai-asterisk-proxy asterisk -rx "core set verbose 5"
docker logs -f kasaai-asterisk-proxy
```

### 11.3 Redis / BullMQ Monitoring

```bash
# Check queues
redis-cli KEYS "bull:*"
redis-cli LLEN "bull:webhook-delivery:wait"
redis-cli LLEN "bull:campaign-calls:wait"
```

---

## 12. File Inventory

### New Files to Create in LOAD

| File | Purpose |
|------|---------|
| `backend/src/telephony/asterisk-ari.ts` | Asterisk ARI client |
| `backend/src/telephony/call-bridge.ts` | Bridges Asterisk audio ↔ voice pipeline |
| `backend/src/telephony/audio-resample.ts` | Audio format conversion |
| `backend/src/modules/webhooks/delivery.ts` | BullMQ webhook delivery |
| `backend/src/modules/campaigns/engine.ts` | BullMQ campaign execution |
| Tests for all above | Unit + integration tests |

### Files to Modify in LOAD

| File | Changes |
|------|---------|
| `backend/src/telephony/twilio.ts` | Fix SDK property names |
| `backend/src/telephony/sip.ts` | Replace placeholder with real implementation |
| `backend/src/modules/calls/routes.ts` | Add outbound call endpoint |
| `backend/src/modules/calls/service.ts` | Add telephony call methods |
| `backend/src/modules/phone-numbers/service.ts` | Add SIP trunk support |
| `backend/prisma/schema.prisma` | Add SIP fields to PhoneNumber |
| `backend/src/app.ts` | Initialize telephony + workers on startup |
| `backend/src/config/index.ts` | Add Asterisk env vars to config |
| `frontend/src/pages/Dashboard.tsx` | Remove unused import |
| `frontend/src/pages/PhoneNumbers.tsx` | Remove unused import |
| `frontend/src/pages/WebCall.tsx` | Remove unused import |

### New Files to Create in DiaServe1

| File | Purpose |
|------|---------|
| `backend/app/integration/load_client.py` | LOAD API client (replaces VapiClient) |

### Files to Modify in DiaServe1

| File | Changes |
|------|---------|
| `backend/app/api/voice/router.py` | Add `/webhook/load` endpoint |
| `backend/app/services/campaign_service.py` | Use LoadClient instead of VapiClient |
| `backend/.env` | Add LOAD_API_URL, LOAD_API_KEY |

### Files to Modify on Asterisk Server

| File | Changes |
|------|---------|
| `/etc/asterisk/ari.conf` | Enable ARI with credentials |
| `/etc/asterisk/http.conf` | Enable HTTP for ARI |
| `/etc/asterisk/extensions.conf` | Route inbound to Stasis app |
