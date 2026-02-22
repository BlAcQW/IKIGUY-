# LOAD — Product Requirements Document

## 1. Product Vision

**LOAD** is a developer-first platform for building, testing, and deploying conversational voice AI agents. It enables developers and businesses to create AI-powered phone agents that can handle inbound and outbound calls with natural conversation capabilities.

### Mission
Democratize voice AI by providing a simple, powerful API and dashboard for building production-grade voice agents.

### Goals
- Provide a complete voice AI infrastructure (STT → LLM → TTS pipeline)
- Offer both API-first and dashboard-based workflows
- Enable real-time, low-latency voice conversations
- Support programmable telephony (Twilio) for real phone calls
- Allow custom tool/function execution during conversations
- Scale from prototyping to production workloads

---

## 2. Target Users

| Segment | Description | Primary Need |
|---------|-------------|--------------|
| **Developers** | Building voice AI into products | Simple API, SDKs, WebSocket streaming |
| **Businesses** | Customer service, sales, scheduling | Dashboard-driven assistant creation |
| **Enterprises** | Large-scale deployments | Multi-org, compliance, SLAs |

---

## 3. Core Features

### 3.1 Assistants
- Create and configure AI voice agents
- Define system prompt, personality, behavior
- Select AI model (LLM), voice (TTS), and transcriber (STT)
- Configure first message, end-of-call behavior
- JSONB-based flexible configuration storage
- Version history and cloning

### 3.2 Calls
- **Web Calls**: Browser-based via WebSocket audio streaming
- **Inbound Calls**: Receive calls on purchased phone numbers
- **Outbound Calls**: Initiate calls via API
- Real-time call monitoring and status
- Call recording and transcript storage
- Call cost tracking and duration metrics

### 3.3 Phone Numbers
- Purchase phone numbers via Twilio
- Assign assistants to phone numbers
- Manage number lifecycle (buy, configure, release)
- Support for toll-free and local numbers
- SIP trunking support (future)

### 3.4 Tools / Functions
- Define custom tools with JSON Schema
- Server URL webhooks for tool execution
- Tool invocation during live conversations
- Built-in tools (transfer call, end call, etc.)
- Async tool execution support

### 3.5 Squads
- Multi-assistant routing configurations
- Define transfer conditions between assistants
- Shared context across squad members
- Call handoff with context preservation

### 3.6 Campaigns
- Bulk outbound call management
- Contact list upload and management
- Campaign scheduling and throttling
- Progress tracking and analytics
- Retry logic for failed calls

### 3.7 Dashboard
- Real-time call activity overview
- Assistant management UI
- Call logs with search and filtering
- Phone number management
- Campaign monitoring
- Settings and API key management

### 3.8 Analytics
- Call volume and duration metrics
- Success/failure rates
- Cost breakdown by assistant/campaign
- Latency metrics (STT, LLM, TTS)
- Conversation quality insights

---

## 4. Voice Pipeline Architecture

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  Audio   │───▶│   STT   │───▶│   LLM   │───▶│   TTS   │
│  Input   │    │(Whisper)│    │ (GPT-4) │    │(OpenAI) │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
                                                   │
                                                   ▼
                                              ┌─────────┐
                                              │  Audio   │
                                              │  Output  │
                                              └─────────┘
```

### Pipeline Providers (Pluggable)
- **STT**: OpenAI Whisper (MVP), Deepgram, Google (future)
- **LLM**: OpenAI GPT-4 (MVP), Anthropic Claude, Google Gemini (future)
- **TTS**: OpenAI TTS (MVP), ElevenLabs, PlayHT (future)

---

## 5. Integration Ecosystem

### MVP Integrations
- OpenAI (STT + LLM + TTS)
- Twilio (telephony)
- Webhooks (tool execution, events)

### Future Integrations
- Deepgram (STT)
- ElevenLabs (TTS)
- Anthropic Claude (LLM)
- Make/Zapier (workflow automation)
- CRM systems (Salesforce, HubSpot)

---

## 6. Delivery Roadmap

### MVP (Phase 1-2)
- User auth (JWT + API keys)
- Assistant CRUD
- Voice pipeline (OpenAI all-in-one)
- Web-based calls via WebSocket
- Basic dashboard

### V1 (Phase 3-4)
- Twilio telephony (inbound/outbound)
- Call recording & transcripts
- Tool/function execution
- Squads & multi-assistant routing
- Full dashboard

### V2 (Phase 5+)
- Campaigns & bulk calling
- Analytics & insights
- Multi-provider support
- SDK & client libraries
- Usage metering & billing

---

## 7. Success Metrics

| Metric | Target |
|--------|--------|
| API response latency | < 200ms (non-voice) |
| Voice pipeline latency | < 500ms end-to-end |
| Call success rate | > 95% |
| System uptime | 99.9% |
| Dashboard page load | < 2s |
| API key creation to first call | < 5 minutes |
