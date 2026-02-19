# KasaAI – Core Backend (Control Plane) — Planning

## 1) Purpose

The Core Backend is the private control plane that orchestrates assistants, sessions, campaigns, knowledge (RAG), usage metering, and licensing. It exposes **private, mTLS-protected** APIs to internal first-party apps (B2B & B2C portals) and the Developer Platform (public façade), and drives the data plane (telephony, ASR/TTS, LLM, KB store).

> **Non-goal:** No public endpoints, no API key issuance, no webhook delivery. These live in the **Developer Platform**.

---

## 2) Core Responsibilities

- **Assistant lifecycle**: create/update config (voice/chat/WhatsApp), languages, guardrails.
- **Sessions & orchestration**: route audio, manage ASR → NLU → RAG → TTS loops; human handover.
- **Campaign engine**: schedule pacing, retries, throttling; outbound dialing.
- **Knowledge & RAG**: doc ingestion, chunking/embedding, hybrid retrieval, reranking, grounding checks.
- **Usage & billing meters**: per-tenant minute/message counters; cost attribution (telephony, STT, TTS).
- **Licensing**: SaaS entitlements + on-prem license verification; feature gates.
- **Event emission**: normalized events to warehouse/analytics; event feed for Developer Platform webhooks.
- **On-prem/Edge sync**: license + capability sync; usage export/import for air-gapped deployments.

---

## 3) Private Interface Contracts (internal)

- `POST/GET/PATCH/DELETE /internal/assistants`
- `POST/GET/PATCH/DELETE /internal/campaigns` + `/internal/campaigns/{id}:start|stop|pause|resume`
- `POST/GET/PATCH /internal/kb` (documents, versions, reindex)
- `GET /internal/usage` (org/workspace/period) + **daily rollups**
- `POST /internal/licenses/verify` | `POST /internal/licenses/activate`
- `POST /internal/events/ingest` (from data plane) | **publishes** to bus for warehouse + Developer Platform

> Transport: HTTP/2 + mTLS (or gRPC).  
> Auth: service account JWT with audience/claims; strict RBAC/ABAC.

---

## 4) Data Plane Contracts

- **Telephony**: WebRTC/SIP adapters; call start/stop, media stream hooks.
- **ASR/TTS**: model selection, lexicon biasing, pace; streaming APIs.
- **LLM**: planner/guardrail prompts; temperature and safety controls.
- **KB Store**: embeddings (pgvector), BM25 index, cross-encoder rerank.

---

## 5) Event Model (to warehouse & Dev Platform)

- `call.started`, `assistant.turn`, `call.ended`
- `outcome.converted` (interested, converted, needs_follow_up, not_interested, invalid_number, transferred)
- `qa.score.created`
- Error/latency counters per stage (ASR, RAG, TTS, MCP tool call)

Events are **tenant-scoped**, HMAC-signable payloads with correlation IDs.

---

## 6) Security & Compliance

- mTLS between Core and internal clients; short-lived JWTs; least-privilege scopes.
- PII redaction policy; configurable retention windows (per tenant).
- Consent & DNC enforcement; per-region telephony allowlists.
- Secrets in KMS/Vault; audit trails for admin actions.

---

## 7) Environments & Deployments

- **SaaS**: HA cluster in your VPC; autoscale workers; dedicated DB.
- **On-prem Edge Node**: Docker bundle (ASR/TTS/RAG + SIP adapters), license file, offline usage export.
- **Hybrid**: Edge for audio; Core for control & analytics.

---

## 8) SLOs & Performance

- P95 turn latency (ASR→TTS): ≤ 1.5s cloud; ≤ 900ms edge.
- RAG retrieval + rerank: ≤ 250ms for 5–10 passages.
- Event delivery to warehouse: ≤ 60s; to Developer Platform queue: ≤ 5s.

---

## 9) Roadmap

- **P1**: Private APIs, session orchestration, RAG, usage meters, event bus.
- **P2**: Campaign engine, licensing + on-prem sync, MCP routing via Dev Platform.
- **P3**: Advanced QA scoring, multilingual packs, model capability registry.

---

## 10) Component Boundaries

### Core Backend Owns:

- Assistant configuration and lifecycle
- Session orchestration and state management
- Campaign scheduling and execution
- Knowledge base management and RAG
- Usage metering and billing aggregation
- License verification and feature gates
- Event emission and analytics

### Core Backend Does NOT Own:

- Public API endpoints (Developer Platform)
- Telephony provider management (Edge Node)
- Tenant configuration UI (B2B/B2C portals)
- SDK development (Developer Platform)
- Provider switching logic (Edge Node)
- Custom workflow automation (Edge Node + n8n)

### Integration Points:

- **Edge Node**: Receives telephony events, sends campaign instructions
- **Developer Platform**: Provides private APIs for public façade
- **B2B/B2C Portals**: Provides internal APIs for UI operations
- **On-premise**: License sync, usage export/import, capability discovery
