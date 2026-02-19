# Workers & Jobs

    RAG Indexer: parse → chunk → embed → store vectors

    Dialer/Orchestrator: schedule calls, retries, pacing, pick adapter

    Event Normalizer: adapter → unified event → DB + webhook emit

    Billing Rollups: provider CDRs + internal logs → usage_meters daily

    QA Sampler: select calls for scoring based on rules

    License Validator: periodic checks; handle grace periods/offline

# Adapters (ports)

    TelephonyPort: dial(), hangup(), subscribeEvents(), signed webhook ingress

    ASR/TTSPort: cloud vs edge selection; language packs feature-gated

    VectorPort: pgvector/Qdrant interchangeable

    MCPPort: call registered tools (CRM/helpdesk/payments) via Dev Platform

# Security

    Network: Core is private; only allow B2B, B2C, Dev Platform IPs/certs.

    AuthZ: service JWT contains tenant_id, svc claim; RBAC for admin routes.

    PII: redaction pipeline; retention windows configurable per tenant.

    Secrets: KMS/Vault; never persist third-party creds (Dev Platform manages MCP).

    Audit: every write with actor, tenant, path, payload hash.

# Licensing Flow

    SaaS: feature flags by plan; entitlements: channels, max assistants, analytics tier, language packs.

    On-Prem/Edge: signed license file or token; periodic revalidation; air-gapped: offline usage export/import with signed manifests; grace windows.

# Analytics & Funnels

# Track:

    Connect rate, avg duration, drop-offs (intro/price/handover), conversion, sentiment, regions.

    Top questions/confusions, QA scores.

    Export endpoints for CSV/PDF (rendering done in portals).
	
	
#	Testing & CI

    Unit: services, adapters, licensing checks, RAG indexer.

    Contract: run against Developer Platform staging proxy with fake tenant.

    E2E (smoke): create assistant → upload KB → create campaign → start → ingest mock events → metrics populated.

    Load: campaign engine under 10k concurrent call intents (mock).

# Acceptance Criteria

    Assistants/KG: Create assistant; upload a PDF; status flows parsed→chunked→embedded; retrieval works in test call.

    Campaigns: Create/run campaign with pacing & retries; dialer chooses adapter; events ingested and normalized.

    Usage/Billing: Minutes and costs roll up daily; /usage/summary returns correct aggregates.

    Licensing: SaaS feature gates enforced; on-prem activation works; license expiry blocks gated features; offline usage export available.

    Security: All internal endpoints enforce mTLS + service JWT; tenant binding verified; audit logs present.

    Resilience: If telephony provider webhook is delayed, system retries and remains idempotent.

# Deliverables

    FastAPI app with /internal/* routes + Pydantic schemas

    Workers (RAG indexer, dialer, billing rollups, license validator)

    Redis + DB migrations (SQL) and seed scripts

    Observability setup (OpenTelemetry, metrics, health checks)

    README (env, run, tests) + OpenAPI for internal consumers
## Running

```bash
uvicorn apps.core_backend.backend.main:app --reload
# Uses the same Supabase database as the B2C and Developer Platform apps.
# Set `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` (or `CORE_DB_URL`).
# Bootstrap a service account in the DB and pass its token via
# `X-Service-Token` header when calling private endpoints.
# Stream sessions over WebSocket: `ws://localhost:8000/internal/sessions/{session_id}`.
# Request a human handover via `POST /internal/sessions/{session_id}/handover`.
# Upload knowledge with `POST /internal/kb` (fields: `tenant_id`, `content` or `url`).
# Query knowledge with `POST /internal/kb/search` to retrieve chunks using hybrid retrieval with cross-encoder reranking.
# The session WebSocket uses this search with a grounding threshold and responds with a clarification when ungrounded.
# Schedule outbound work with `POST /internal/campaigns` (fields: `cron`, `pacing_per_minute`, `max_attempts`, `backoff_minutes`).
# Campaigns use an in-memory dialer that maps outcomes (answered, busy, failed)
# to success or retry states.
# Usage metrics are recorded for each tenant; query totals with `GET /internal/usage` or
# submit custom records via `POST /internal/usage` (fields: minutes, messages,
# stt_calls, tts_calls, telephony_cost, stt_cost, tts_cost plus provider names).
# Aggregate daily totals with `POST /internal/usage/rollup?day=YYYY-MM-DD`,
# export them for billing via `GET /internal/usage/invoice`, and retrieve
# per-provider cost attribution with `GET /internal/usage/costs`.
# Mirror usage on edge nodes with `GET /internal/usage/export` and
# `POST /internal/usage/import`, and fetch license/capability info using
# `GET /internal/edge/sync`.
# Submit QA scores with `POST /internal/qa/score`; session and campaign events
# are stored on an in-memory event bus for analytics.
# Persist events into the warehouse table by calling
# `POST /internal/events/etl` and drain webhook events for delivery via
# `GET /internal/events/webhooks`.
# Activate licenses with `POST /internal/licenses/activate`, check status via
# `GET /internal/licenses/status/{tenant_id}`, and verify feature availability
# (agents, channels, minutes) using `POST /internal/licenses/verify`. Assistant
# and campaign creation as well as session usage recording enforce these limits.
# TLS is handled at the proxy in dev, but the API verifies the token.
```


