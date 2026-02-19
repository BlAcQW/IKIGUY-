# KasaAI Developer Platform – Planning

## 1. Purpose

Provide a **public, versioned API surface** for partners and third-party developers to build on KasaAI without touching private Core services. It owns **API keys & scopes**, **rate limits**, **webhooks** (HMAC), **MCP registry/marketplace**, **SDKs**, and **developer docs**.

## 2. Core Responsibilities

- **Public API Gateway:** REST/GraphQL endpoints, validation, throttling, quotas.
- **Authn/Authz:** API keys (tenant/workspace scoped), OAuth apps (optional).
- **Webhooks:** Registration, signing (HMAC-SHA256), retries, DLQ, replay.
- **MCP Registry:** Register connectors (CRM, email, payments), health checks, secret management via vault.
- **Docs & SDKs:** TypeScript & Python SDKs, quickstarts, code samples.
- **Sandbox:** Test resources (mock ASR/TTS, fake numbers), usage caps.
- **Versioning & Deprecation:** v1 lifecycle, changelogs, migration guides.
- **Observability:** Per-key request logs, latency/error SLOs, abuse detection.

## 3. Non-Responsibilities

- No orchestration, campaigns, KB/RAG, licensing, or telephony routing. These live in **Core**. The Platform **proxies** validated calls to Core via mTLS.

## 4. Architecture

- **API Gateway Service** (Node/Nest or Go Fiber) in a DMZ.
- **Private mTLS** to Core (OpenAPI/gRPC contracts).
- **Secrets Vault** for MCP connector credentials (no secrets in Core).
- **Event Worker** to sign & deliver webhooks with retries.
- **Docs Site** (Docusaurus/Next) with codegen from OpenAPI.

## 5. Data Model (top-level)

- `api_keys(id, tenant_id, workspace_id, scopes[], rate_limit, status)`
- `webhooks(id, tenant_id, url, secret, events[], enabled)`
- `mcp_servers(id, tenant_id, url, tool_names[], status, created_by)`
- `api_request_logs(id, api_key_id, route, status, latency_ms, ts)`
- `quotas(id, api_key_id, period, limit, used)`
- `changelogs(version, date, notes)`

## 6. Security & Compliance

- mTLS to Core; HMAC-signed webhooks; per-key/tenant RLS.
- Audit trail on key issuance, scope grants, and connector secrets.
- Abuse controls: burst limiters, IP reputation, request entropy filters.

## 7. Versioning Strategy

- **/v1** stable; non-breaking additive only.
- Deprecation policy: 90-day notice, dual-run v1/v2, migration guides.
- SDKs pinned by API version; code-gen + semantic releases.

## 8. Roadmap

- **MVP (3–4 wks):** Keys/scopes, Assistants/Campaigns/Webhooks endpoints, mTLS proxy to Core, TS SDK, docs alpha.
- **v1 GA (6–8 wks):** MCP registry, quotas, Python SDK, Sandbox resources, signed webhooks & retries, per-key analytics.
- **v1.1+:** OAuth app registry, GraphQL, marketplace UI for MCP connectors.

## 9. Component Boundaries

### Developer Platform Owns:

- Public API endpoints and documentation
- API key management and authentication
- Webhook delivery and management
- MCP registry and marketplace
- SDK development and distribution
- Developer documentation and guides
- Sandbox environment for testing

### Developer Platform Does NOT Own:

- Assistant configuration (Core Backend)
- Session orchestration (Core Backend)
- Telephony operations (Edge Node)
- Tenant configuration (B2B/B2C portals)
- Provider management (Edge Node)
- Usage tracking and billing (Core Backend)

### Integration Points:

- **Core Backend**: Proxies API calls via mTLS
- **Edge Node**: Telephony APIs for developers
- **B2B/B2C Portals**: Provides APIs for portal operations
- **External Developers**: Public API surface and SDKs

## 10. API Surface Design

### Core APIs (Proxied to Core Backend)

- `/v1/assistants` - Assistant management
- `/v1/campaigns` - Campaign management
- `/v1/kb` - Knowledge base management
- `/v1/usage` - Usage and analytics

### Telephony APIs (Proxied to Edge Node)

- `/v1/calls` - Call control and monitoring
- `/v1/providers` - Provider management
- `/v1/dids` - DID management
- `/v1/analytics` - Telephony analytics

### Platform APIs (Internal)

- `/v1/keys` - API key management
- `/v1/webhooks` - Webhook management
- `/v1/mcp` - MCP server management
- `/v1/sandbox` - Sandbox resources

## 11. SDK Strategy

### TypeScript/JavaScript SDK

- Full API coverage with type safety
- Webhook handling utilities
- Authentication helpers
- Error handling and retries

### Python SDK

- Full API coverage with async support
- Integration with popular frameworks
- CLI tools for automation
- Testing utilities

### Mobile SDKs (Future)

- iOS SDK for mobile apps
- Android SDK for mobile apps
- React Native wrapper
- Flutter wrapper

## 12. Developer Experience

### Documentation

- Interactive API documentation
- Code examples and tutorials
- Best practices and guidelines
- Migration guides and changelogs

### Sandbox Environment

- Mock telephony endpoints
- Test API keys and webhooks
- Sample data and scenarios
- Integration testing tools

### Developer Portal

- Self-service API key management
- Usage analytics and monitoring
- Webhook testing and debugging
- Community forums and support
