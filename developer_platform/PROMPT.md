You are building the **KasaAI Developer Platform** for AI Labs Africa — a public-facing layer that lets external developers safely integrate with KasaAI via **REST APIs, SDKs, webhooks, and MCP connectors**. It includes:
1) A **public API backend** that proxies to Core Backend using service-to-service auth/mTLS, enforcing **API keys, scopes, quotas, and rate limits**.
2) A lightweight **Developer Console (frontend)** for key management, usage, webhooks, and MCP registry.

## Goals
- Issue & rotate **API keys** (hashed-at-rest), define **scopes** (assistants:read/write, campaigns:write, kb:write, webhooks:manage, mcp:manage), enforce **rate limits/quotas** per tenant.
- Provide stable **/v1** REST endpoints that proxy to **Core Internal** APIs (assistants, campaigns, KB, analytics) with audit trails.
- Deliver **webhooks** (HMAC-signed) with retries + DLQ; webhook test utility.
- Host an **MCP registry** (configure external connectors: CRM/helpdesk/payments) and a **tool-call proxy** to Core.
- Offer a **Developer Console**: keys, usage, webhooks, MCP connectors, docs, API explorer, sandbox.
- Ship **OpenAPI** + **TypeScript SDK** and auto-generated **Postman** collection.

## Tech & Architecture
- **Backend:** Node.js + TypeScript; choose **NestJS** (modules/guards/interceptors) + **Fastify** adapter.
- **Auth:** Console login via Supabase Auth; public API via **API keys** (prefix `kas_pk_`), HMAC for webhooks.
- **Data:** Supabase (schema `devplat`) for keys, scopes, apps, webhooks, deliveries, quotas; Redis for **rate limiting** (sliding window), **queue** (BullMQ) for webhook delivery.
- **Security:** 
  - Core communication: **mTLS** with client certs; requests signed and tenant-scoped.
  - Keys: **bcrypt/argon2** hash; show only prefixes to users; rotation + revocation.
  - Webhooks: HMAC-SHA256 signature header (`x-kasa-signature`, `x-kasa-timestamp`).
  - CORS restricted; IP allowlists optional; full **audit logs**.
- **Docs:** OpenAPI (Swagger), Redoc; codegen TS SDK.
- **Branding:** Dark Blue `#0B1F3B`, Gold `#CFAE49`.

## Public API (v1) – Contracts (proxy to Core)
Base path: `/v1`
Headers: `Authorization: Bearer <api_key>`, `X-Kasa-Tenant: <tenant_id>`

### Assistants
- `POST /assistants` → { id, name, channel, language, voice, prompt, guardrails }
- `GET /assistants` → Assistant[]
- `PATCH /assistants/:id`
- `DELETE /assistants/:id`

### Campaigns
- `POST /campaigns` → { id, status }
- `POST /campaigns/:id/start`
- `POST /campaigns/:id/stop`
- `GET /campaigns/:id/metrics` → { totals, outcomes, dropoffs, sentiment }

### Knowledge Base
- `POST /kb/sources` (multipart) file + metadata
- `POST /kb/sources/:id/reindex`
- `DELETE /kb/sources/:id`

### Analytics (read-only)
- `GET /analytics/summary?range=30d`
- `GET /analytics/top-questions?range=30d`
- `GET /analytics/regions?range=30d`

### Webhooks
- `POST /webhooks` (url, events[], secret auto-gen)
- `GET /webhooks` / `DELETE /webhooks/:id`
- `POST /webhooks/test` (fires sample signed payload)
- Delivery logs: `GET /webhooks/:id/deliveries?status=failed`

### API Keys & Usage
- `POST /keys` (scopes[], label, expiry?) → masked key once
- `GET /keys` (prefix + metadata only) / `DELETE /keys/:id`
- `GET /usage` → minutes/messages by day; remaining quota

### MCP Registry
- `GET /mcp/connectors`
- `POST /mcp/connectors` (type, config)  // e.g., HubSpot, Freshdesk, Paystack
- `POST /mcp/connectors/:id/test`
- `DELETE /mcp/connectors/:id`

> All endpoints: validate scopes, apply rate limits, attach tenant, audit log action, and **proxy** to Core as needed.

## Developer Console (Frontend)
**Stack:** Next.js 14 (App Router) + TypeScript + Tailwind + shadcn/ui + TanStack Query + Zod  
**Routes & Features**
- `/login` `/logout`
- `/dashboard` – usage tiles, latest webhook deliveries, API status
- `/keys` – create/rotate/revoke; show prefix + last 4; copy-once full key modal
- `/webhooks` – create (select events), show secret, test delivery, delivery logs, pause/resume
- `/mcp` – list connectors (cards), add/edit config, “Test Tool” button
- `/docs` – embedded Redoc + code samples (curl, Node, Python); **API Explorer** (OAuth device flow optional)
- `/usage` – charts (minutes/messages, rate limit hits, 4xx/5xx)
- `/settings` – tenant profile, IP allowlist, audit log viewer (read-only)

**Components**
- `KeyCard`, `KeyCreateDialog`, `WebhookForm`, `DeliveryTable`, `McpConnectorCard`, `UsageCharts`, `AuditLogTable`, `ApiExplorer`

**UX**
- Empty states, skeletons, toasts. Strong copy with examples. Guard dangerous actions with confirms.

## Rate Limiting & Quotas
- Redis sliding window per key + path + tenant.
- Defaults: 300 req/min burst; adjustable in `devplat.quotas`.
- Return `429` with `Retry-After` + docs link; log metric.

## Webhook Delivery
- Queue with backoff (1s, 10s, 60s, 5m, 30m; max 10 tries).
- Sign with HMAC; include timestamp; receivers verify `x-kasa-signature`.
- DLQ + redrive from console.

## OpenAPI & SDK
- Keep `openapi.yaml` in repo; CI publishes to CDN.
- Generate **TypeScript SDK** (`/sdks/js`) via openapi-typescript + hand-written client.
- Auto-export **Postman collection** per release.

## Security & Compliance
- Keys stored hashed; only show once. Rotation without downtime.
- mTLS to Core; Core service tokens are short-lived.
- Full audit: who did what, when, IP, user-agent.
- PII minimization; GDPR delete for console accounts.
- CSP strict; no wildcard `connect-src` in console.

## Testing & CI
- Unit: guards, quotas, signing utils; e2e: key issuance → API call → webhook test.
- Contract tests against Core’s staging with fake tenant.
- GitHub Actions: lint, typecheck, unit/e2e, build Docker, publish OpenAPI & SDK.

## Acceptance Criteria
1. Create API key (scoped), use it to create an assistant via `/v1/assistants`.
2. Rate limit kicks in with 429 under load; headers show limit/remaining/reset.
3. Webhook test sends signed payload; console shows success; failure retried & logged.
4. MCP connector added and “Test Tool” returns OK.
5. OpenAPI available at `/docs/openapi.yaml`; Postman JSON downloadable; TS SDK published.
6. All proxied calls include tenant context and are audit-logged.

## Env Vars (examples)
- `CORE_BASE_URL`, `CORE_MTLS_CERT`, `CORE_MTLS_KEY`, `CORE_CA`
- `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE`
- `REDIS_URL`
- `JWT_SECRET` (console)
- `WEB_BASE_URL` (console), `PUBLIC_DOCS_CDN`
- `HMAC_DEFAULT_SECRET` (fallback for tests)

Build the Developer Platform backend and Console with the above contracts, ensuring **public API stability**, **strict security**, and **excellent DX** (docs, SDK, Postman, examples).
