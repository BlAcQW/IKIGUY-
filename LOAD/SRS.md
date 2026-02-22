# LOAD — Software Requirements Specification

## 1. System Architecture

### Architecture Style
Modular monolith with clear module boundaries, designed for future microservice extraction.

```
┌──────────────────────────────────────────────────────────┐
│                      API Gateway                          │
│              (Fastify + Auth Middleware)                   │
├──────────┬──────────┬──────────┬──────────┬──────────────┤
│   Auth   │Assistants│  Calls   │  Tools   │  Campaigns   │
│  Module  │  Module  │  Module  │  Module  │   Module     │
├──────────┴──────────┴──────────┴──────────┴──────────────┤
│                   Service Layer                           │
├──────────────────────────────────────────────────────────┤
│              Voice Pipeline Engine                        │
│         (STT → LLM → TTS Orchestrator)                   │
├──────────────────────────────────────────────────────────┤
│            Provider Adapters (Pluggable)                  │
│        OpenAI Whisper │ OpenAI GPT │ OpenAI TTS          │
├──────────────────────────────────────────────────────────┤
│           Telephony Layer (Twilio)                        │
├──────────────────────────────────────────────────────────┤
│     PostgreSQL     │     Redis      │     BullMQ         │
└──────────────────────────────────────────────────────────┘
```

---

## 2. Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Runtime | Node.js | 20 LTS |
| Language | TypeScript | 5.x |
| Backend Framework | Fastify | 4.x |
| Frontend | React + Vite | React 18, Vite 5 |
| Database | PostgreSQL | 16 |
| ORM | Prisma | 5.x |
| Cache | Redis | 7.x |
| Task Queue | BullMQ | 5.x |
| Auth | JWT (jsonwebtoken) + bcrypt | - |
| AI Provider | OpenAI SDK | 4.x |
| Telephony | Twilio SDK | 4.x |
| WebSocket | ws + @fastify/websocket | - |
| Validation | Zod | 3.x |
| Testing | Vitest + Playwright | - |
| Containers | Docker + Docker Compose | - |

---

## 3. Core Entities & Data Models

### 3.1 User
```
User {
  id            String    @id @default(uuid)
  email         String    @unique
  passwordHash  String
  name          String
  organizationId String   @references Organization
  role          Role      (OWNER, ADMIN, MEMBER)
  createdAt     DateTime
  updatedAt     DateTime
}
```

### 3.2 Organization
```
Organization {
  id            String    @id @default(uuid)
  name          String
  slug          String    @unique
  plan          Plan      (FREE, PRO, ENTERPRISE)
  createdAt     DateTime
  updatedAt     DateTime
}
```

### 3.3 ApiKey
```
ApiKey {
  id            String    @id @default(uuid)
  key           String    @unique (hashed)
  prefix        String    (first 8 chars, for display)
  name          String
  organizationId String   @references Organization
  createdById   String    @references User
  lastUsedAt    DateTime?
  expiresAt     DateTime?
  createdAt     DateTime
}
```

### 3.4 Assistant
```
Assistant {
  id              String    @id @default(uuid)
  organizationId  String    @references Organization
  name            String
  model           Json      { provider, model, temperature, maxTokens, systemPrompt }
  voice           Json      { provider, voiceId, speed, stability }
  transcriber     Json      { provider, model, language }
  firstMessage    String?
  endCallMessage  String?
  endCallPhrases  String[]
  metadata        Json?
  createdAt       DateTime
  updatedAt       DateTime
}
```

### 3.5 Call
```
Call {
  id              String      @id @default(uuid)
  organizationId  String      @references Organization
  assistantId     String      @references Assistant
  type            CallType    (WEB, INBOUND, OUTBOUND)
  status          CallStatus  (QUEUED, RINGING, IN_PROGRESS, ENDED, FAILED)
  phoneNumberId   String?     @references PhoneNumber
  customerNumber  String?
  startedAt       DateTime?
  endedAt         DateTime?
  duration        Int?        (seconds)
  endReason       String?
  transcript      Json?
  recordingUrl    String?
  cost            Decimal?
  metadata        Json?
  createdAt       DateTime
}
```

### 3.6 PhoneNumber
```
PhoneNumber {
  id              String    @id @default(uuid)
  organizationId  String    @references Organization
  number          String    @unique
  twilioSid       String    @unique
  assistantId     String?   @references Assistant
  name            String?
  provider        String    (TWILIO)
  status          String    (ACTIVE, RELEASED)
  createdAt       DateTime
}
```

### 3.7 Tool
```
Tool {
  id              String    @id @default(uuid)
  organizationId  String    @references Organization
  type            ToolType  (FUNCTION, TRANSFER_CALL, END_CALL)
  name            String
  description     String?
  function        Json?     { name, description, parameters (JSON Schema) }
  serverUrl       String?
  serverSecret    String?
  metadata        Json?
  createdAt       DateTime
  updatedAt       DateTime
}
```

### 3.8 Squad
```
Squad {
  id              String    @id @default(uuid)
  organizationId  String    @references Organization
  name            String
  members         Json      [{ assistantId, transferConditions }]
  metadata        Json?
  createdAt       DateTime
  updatedAt       DateTime
}
```

### 3.9 Campaign
```
Campaign {
  id              String          @id @default(uuid)
  organizationId  String          @references Organization
  name            String
  assistantId     String          @references Assistant
  phoneNumberId   String          @references PhoneNumber
  status          CampaignStatus  (DRAFT, RUNNING, PAUSED, COMPLETED)
  contacts        Json            [{ name, number, metadata }]
  schedule        Json?           { startTime, endTime, timezone, maxConcurrent }
  stats           Json?           { total, completed, failed, inProgress }
  createdAt       DateTime
  updatedAt       DateTime
}
```

### 3.10 Webhook
```
Webhook {
  id              String    @id @default(uuid)
  organizationId  String    @references Organization
  url             String
  events          String[]  (call.started, call.ended, etc.)
  secret          String
  active          Boolean   @default(true)
  createdAt       DateTime
}
```

---

## 4. API Specification

### 4.1 Authentication

#### Register
```
POST /api/auth/register
Body: { email, password, name, organizationName }
Response: { user, organization, token }
```

#### Login
```
POST /api/auth/login
Body: { email, password }
Response: { user, token }
```

#### API Keys
```
POST   /api/api-keys          — Create API key
GET    /api/api-keys          — List API keys
DELETE /api/api-keys/:id      — Revoke API key
```

### 4.2 Assistants

```
POST   /api/assistants        — Create assistant
GET    /api/assistants        — List assistants (paginated)
GET    /api/assistants/:id    — Get assistant
PATCH  /api/assistants/:id    — Update assistant
DELETE /api/assistants/:id    — Delete assistant
```

**Create Assistant Request:**
```json
{
  "name": "Sales Agent",
  "model": {
    "provider": "openai",
    "model": "gpt-4",
    "temperature": 0.7,
    "maxTokens": 1000,
    "systemPrompt": "You are a helpful sales agent..."
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
  "firstMessage": "Hello! How can I help you today?"
}
```

### 4.3 Calls

```
POST   /api/calls             — Create call (outbound)
GET    /api/calls             — List calls (paginated, filtered)
GET    /api/calls/:id         — Get call details
DELETE /api/calls/:id         — End active call
```

**WebSocket: Web Call**
```
WS /api/calls/web
→ Client sends: { type: "start", assistantId: "..." }
→ Client sends: binary audio frames (PCM 16-bit, 16kHz)
← Server sends: binary audio frames (PCM 16-bit, 24kHz)
← Server sends: { type: "transcript", role: "user"|"assistant", text: "..." }
← Server sends: { type: "status", status: "..." }
```

### 4.4 Phone Numbers

```
POST   /api/phone-numbers           — Buy phone number
GET    /api/phone-numbers           — List phone numbers
GET    /api/phone-numbers/:id       — Get phone number
PATCH  /api/phone-numbers/:id       — Update (assign assistant)
DELETE /api/phone-numbers/:id       — Release phone number
```

### 4.5 Tools

```
POST   /api/tools             — Create tool
GET    /api/tools             — List tools
GET    /api/tools/:id         — Get tool
PATCH  /api/tools/:id         — Update tool
DELETE /api/tools/:id         — Delete tool
```

### 4.6 Squads

```
POST   /api/squads            — Create squad
GET    /api/squads            — List squads
GET    /api/squads/:id        — Get squad
PATCH  /api/squads/:id        — Update squad
DELETE /api/squads/:id        — Delete squad
```

### 4.7 Campaigns

```
POST   /api/campaigns              — Create campaign
GET    /api/campaigns              — List campaigns
GET    /api/campaigns/:id          — Get campaign
PATCH  /api/campaigns/:id          — Update campaign
POST   /api/campaigns/:id/start    — Start campaign
POST   /api/campaigns/:id/pause    — Pause campaign
DELETE /api/campaigns/:id          — Delete campaign
```

### 4.8 Webhooks

```
POST   /api/webhooks          — Create webhook
GET    /api/webhooks          — List webhooks
GET    /api/webhooks/:id      — Get webhook
PATCH  /api/webhooks/:id      — Update webhook
DELETE /api/webhooks/:id      — Delete webhook
```

---

## 5. Voice Pipeline Technical Design

### 5.1 Provider Adapter Interface

```typescript
// STT Provider
interface STTProvider {
  transcribe(audioBuffer: Buffer, options: STTOptions): Promise<string>;
  createStream(options: STTOptions): STTStream;
}

// LLM Provider
interface LLMProvider {
  chat(messages: Message[], options: LLMOptions): Promise<string>;
  chatStream(messages: Message[], options: LLMOptions): AsyncIterable<string>;
}

// TTS Provider
interface TTSProvider {
  synthesize(text: string, options: TTSOptions): Promise<Buffer>;
  synthesizeStream(text: string, options: TTSOptions): AsyncIterable<Buffer>;
}
```

### 5.2 Pipeline Flow

1. **Audio Input** → WebSocket binary frame received
2. **STT** → Audio buffer sent to Whisper, returns text
3. **LLM** → User text + conversation history sent to GPT-4, streams response
4. **TTS** → LLM response chunks sent to TTS, streams audio
5. **Audio Output** → Audio chunks sent back via WebSocket

### 5.3 Session Management

Each active call maintains a session:
```typescript
interface CallSession {
  id: string;
  callId: string;
  assistantId: string;
  conversationHistory: Message[];
  audioBuffer: Buffer[];
  status: 'active' | 'paused' | 'ended';
  startedAt: Date;
  metadata: Record<string, unknown>;
}
```

---

## 6. Authentication & Authorization

### 6.1 JWT Authentication (Dashboard)
- Access token: 15-minute expiry
- Refresh token: 7-day expiry, stored as httpOnly cookie
- Token payload: `{ userId, organizationId, role }`

### 6.2 API Key Authentication (Programmatic)
- Format: `load_` + 32 random characters
- Stored as bcrypt hash in database
- Prefix (first 8 chars) stored for identification
- Scoped to organization
- Rate limited per key

### 6.3 Authorization
- All resources scoped to organization
- Role-based access: OWNER > ADMIN > MEMBER
- OWNER: full access, billing, delete org
- ADMIN: manage resources, invite users
- MEMBER: read/write resources

---

## 7. Twilio Telephony Integration

### 7.1 Inbound Calls
1. Twilio receives call on purchased number
2. Twilio sends webhook to LOAD backend
3. Backend looks up assigned assistant
4. Backend responds with TwiML to connect via WebSocket
5. Voice pipeline handles the conversation

### 7.2 Outbound Calls
1. API request to create outbound call
2. Backend uses Twilio REST API to initiate call
3. Twilio connects call, sends webhook
4. Backend connects to voice pipeline via WebSocket

### 7.3 Phone Number Management
- Buy numbers via Twilio API
- Configure webhooks on Twilio side
- Release numbers when deleted

---

## 8. Webhook / Event System

### 8.1 Events
| Event | Trigger |
|-------|---------|
| `call.started` | Call begins |
| `call.ended` | Call ends |
| `call.failed` | Call fails |
| `transcript.update` | New transcript segment |
| `tool.call` | Tool invoked during call |
| `campaign.completed` | Campaign finishes |

### 8.2 Delivery
- POST to registered webhook URL
- Include HMAC-SHA256 signature header
- Retry: 3 attempts with exponential backoff
- Timeout: 30 seconds per attempt
- Delivered via BullMQ job queue

---

## 9. Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| API Response Time | < 200ms (p95) |
| Voice Pipeline Latency | < 500ms (STT + LLM first token + TTS) |
| Concurrent Calls | 100+ per instance |
| Database Query Time | < 50ms (p95) |
| System Uptime | 99.9% |
| Data Encryption | AES-256 at rest, TLS 1.3 in transit |
| Auth Token Expiry | 15 min access, 7 day refresh |
| Rate Limiting | 100 req/min per API key (default) |
| Max Call Duration | 60 minutes |
| Recording Storage | S3-compatible object storage |

---

## 10. Error Handling

### API Error Format
```json
{
  "success": false,
  "error": {
    "code": "ASSISTANT_NOT_FOUND",
    "message": "Assistant with id 'abc' not found",
    "statusCode": 404
  }
}
```

### Success Response Format
```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "total": 100,
    "page": 1,
    "limit": 20
  }
}
```
