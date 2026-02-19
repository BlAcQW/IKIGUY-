You are building the **KasaAI Core Backend (Control Plane)** for AI Labs Africa.

## Mission
Provide a secure, multi-tenant control plane that orchestrates assistants, knowledge, campaigns, telephony adapters, licensing, and analytics for **B2B Portal**, **B2C Portal**, **Developer Platform**, and optional **Edge/On-Prem Nodes**.

Core is **private** (not internet-facing). Only trusted first-party services call it over **mTLS**. The Developer Platform proxies any public traffic.

---

## Tech & Architecture
- **Language/Framework:** Python 3.11 + **FastAPI** (sync endpoints) + Uvicorn
- **DB:** **Supabase Postgres** (one project per env: dev/stage/prod); schemas: `core`, `integrations`, `analytics`, `admin` (Supabase `auth` managed by platform)
- **Cache/Queues:** Redis (job queues, rate control, idempotency)
- **Vector Search:** pgvector or external (e.g., Qdrant) via adapter
- **Storage:** Supabase Storage / S3 for KB files, audio, transcripts (signed URLs)
- **Messaging:** Redis streams (default) with clean interfaces so Kafka/NATS can be swapped later
- **Auth between services:** mTLS + short-lived **service JWTs** (aud=core, tenant_id claims)
- **Config:** 12-factor via env; feature flags in `admin.feature_flags`
- **Observability:** OpenTelemetry, structured logs (JSON), Prometheus metrics

---

## Data & Multi-Tenancy (Supabase)
- **One Supabase project per environment**; **shared** by Core, B2B, B2C, Developer Platform.
- Every table has `tenant_id UUID NOT NULL`. RLS policies enforce `tenant_id = auth.jwt()->>'tenant_id'` for any direct reads. Core uses **service role** but must **always** bind `tenant_id` server-side.
- Schemas:
  - `core`: assistants, prompts, guardrails, campaigns, audiences, call_logs, transcripts, usage_meters, kb_sources, kb_chunks, licenses
  - `integrations`: mcp_connectors, webhooks, oauth states
  - `analytics`: outcomes, sentiments, rollups, regions, qa_scores
  - `admin`: jobs, migrations, feature_flags, audit_logs

---

## Core Responsibilities
1. **Assistant Orchestration** – CRUD + config (prompt, guardrails, voice/lang), channel capabilities.
2. **Knowledge/RAG** – document ingest, parsing, chunking, embedding, retrieval policies.
3. **Campaign Engine** – schedule, pacing, retries, telephony vendor adapter selection, call session lifecycles.
4. **Telephony/Realtime Adapters** – pluggable: VAPI, Vonage, Telnyx, WebRTC/SIP, Edge.
5. **Licensing & Entitlements** – SaaS features + On-Prem license files/tokens, periodic revalidation.
6. **Usage Metering & Billing Feeds** – minutes/messages/STT/TTS/provider costs → daily rollups.
7. **Events/Webhooks** – emit normalized events; HMAC signing for downstream (via Developer Platform).
8. **Analytics & QA** – aggregates, funnels, drop-offs, sentiment, QA rubrics/scores.
9. **Edge/On-Prem Sync** – license activation, capability packs, offline usage export/import (air-gapped).

---

## Internal API (private, mTLS)
Base path: `/internal`

### Assistants
- `GET /assistants?tenantId=` → list
- `POST /assistants` { name, channel, voice, language, prompt, guardrails }
- `PATCH /assistants/{id}`
- `DELETE /assistants/{id}`
- `POST /assistants/{id}/test` → mock LLM turn + latency (no dial)

### Knowledge / RAG
- `GET /kb/sources?tenantId=`
- `POST /kb/upload` (multipart) → returns `sourceId`
- `POST /kb/{sourceId}/reindex`
- `DELETE /kb/{sourceId}`
- `GET /kb/{sourceId}/status` (parsed/chunked/embedded)

### Campaigns
- `GET /campaigns?tenantId=`
- `POST /campaigns` { assistantId, audienceRef|listId, schedule, pacing, retries }
- `POST /campaigns/{id}/start`
- `POST /campaigns/{id}/pause`
- `POST /campaigns/{id}/stop`
- `GET /campaigns/{id}/metrics` { totals, outcomes, dropoffs, sentiment, region }

### Telephony Adapters
- `GET /adapters` (registered providers + status)
- `POST /adapters/select` { campaignId, policy } → chosen route
- Webhook ingress endpoints per adapter (signed): `/telephony/{provider}/hook`

### Events & Webhooks
- `POST /events/ingest` (from adapters & workers)
- `POST /webhooks/deliver` (internal call to Dev Platform queue)

### Usage & Billing
- `GET /usage/summary?tenantId=&range=30d`
- `POST /usage/rollup/run?date=YYYY-MM-DD` (admin)
- `GET /costs/providers?tenantId=&range=30d`

### Licensing
- `GET /licenses/status?tenantId=`
- `POST /licenses/activate` (SaaS token or on-prem file)
- `POST /licenses/sync` (Edge pull)
- `POST /licenses/validate` (admin)

### QA & Analytics
- `GET /qa/samples?tenantId=&range=7d`
- `POST /qa/scores` { callId, rubricId, scores[], notes }
- `GET /analytics/top-questions?tenantId=&range=30d`
- `GET /analytics/regions?tenantId=&range=30d`

**All endpoints**: validate **service JWT** + **mTLS**, bind/verify `tenant_id`, log audit record, idempotency keys where relevant.

---

## Domain Models (simplified)
```ts
Assistant { id, tenant_id, name, channel, voice, language, prompt, guardrails, created_at }
Campaign  { id, tenant_id, name, assistant_id, status, schedule:{...}, pacing:{ccr,retries,delayMin}, audience_ref, created_at }
CallLog   { id, tenant_id, campaign_id, assistant_id, contact, start_at, end_at, duration_sec, outcome, cost_usd, region, sentiment }
KbSource  { id, tenant_id, type, uri, status, errors[], created_at }
UsageMeter{ id, tenant_id, date, minutes, messages, stt_secs, tts_chars, cost_usd }
License   { id, tenant_id, mode, features{}, issued_at, expires_at, last_check, status }
WebhookEvent { id, tenant_id, type, payload_json, created_at, delivered:boolean }
