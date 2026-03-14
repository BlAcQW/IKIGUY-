# CHANGELOG

All notable changes to the LOAD platform are documented in this file.

---

## [Unreleased] — 2026-02-24

Branch: `feat/leads-system-and-load-project`

### WebRTC Real-Time Voice System (New Feature)

Replaced the turn-based WebSocket "hold to talk" system with continuous bidirectional audio streaming via WebRTC. Users speak naturally — the server detects when speech ends (VAD), runs the STT-LLM-TTS pipeline, and streams audio back. No buttons needed.

**Library choice:** `werift` (pure TypeScript WebRTC, no native deps) + `@discordjs/opus` (Opus codec).

**New files created:**

| File | Description |
|------|-------------|
| `backend/src/webrtc/audio-bridge.ts` | Opus codec bridge (decode/encode), PCM resampling wrappers, WAV header construction |
| `backend/src/webrtc/handler.ts` | `WebRTCCallHandler` class — manages one WebRTC call session (peer connection, VAD, pipeline turns, RTP audio) |
| `backend/src/webrtc/schemas.ts` | Zod schemas for WebRTC signaling endpoints |
| `backend/src/webrtc/routes.ts` | HTTP signaling endpoints: `POST /api/calls/webrtc/offer`, `POST /api/calls/webrtc/ice`, `POST /api/calls/webrtc/:callId/end` |
| `backend/src/webrtc/audio-bridge.test.ts` | Tests for Opus round-trip, WAV header generation, resampling |
| `backend/src/webrtc/handler.test.ts` | Tests for offer handling, VAD integration, pipeline invocation |
| `backend/src/webrtc/routes.test.ts` | Tests for HTTP signaling endpoints |
| `frontend/src/hooks/useWebRTC.ts` | React hook encapsulating WebRTC peer connection lifecycle |
| `frontend/src/hooks/useWebSocketCall.ts` | React hook extracting existing WebSocket call logic from WebCall.tsx |

**Files modified:**

| File | Change |
|------|--------|
| `backend/package.json` | Added `werift`, `@discordjs/opus` dependencies |
| `backend/src/index.ts` | Registered `webrtcRoutes` |
| `backend/src/config/index.ts` | Added `STUN_SERVERS`, `TURN_URL`, `TURN_USERNAME`, `TURN_CREDENTIAL` env vars |
| `frontend/src/pages/WebCall.tsx` | Added WebRTC mode toggle, mute button, mode selector (WebRTC vs Classic) |

**Audio flow:**
```
Browser mic (Opus 48kHz) → WebRTC RTP → Server decode → downsample 16kHz →
  VAD → on speechComplete → WAV wrap → processPipelineTurn() →
  STT → LLM → TTS (24kHz PCM) → upsample 48kHz → Opus encode → RTP → Browser speakers
```

**DataChannel protocol:** Same JSON messages as existing WebSocket protocol (`call_started`, `user_transcript`, `assistant_message`, `processing`, `call_ended`, `error`, `transfer`). Audio flows over RTP track automatically — no binary WebSocket messages needed.

---

### Security Audit & Fixes

Full-stack quality audit performed via `/audit` command. Identified and fixed all CRITICAL and HIGH severity issues.

#### CRITICAL Fixes

**CRIT-1: Hardcoded WEBHOOK_SECRET default** (`backend/src/config/index.ts`)
- **Before:** `WEBHOOK_SECRET: z.string().default('default-webhook-secret')` — any deployment forgetting to set the env var would use a known secret.
- **After:** `WEBHOOK_SECRET: z.string().min(16)` — app fails fast if not configured. No default.

**CRIT-2: WebSocket auth bypass** (`backend/src/websocket/handler.ts`)
- **Before:** Token extracted from URL query parameter `?token=`. If no token provided, connection continued unauthenticated — the `if (token)` block was optional.
- **After:** Complete rewrite to message-based auth:
  - 10-second auth timeout — unauthenticated connections are force-closed
  - First message MUST be `{ type: 'auth', token: '...' }` — token verified via `app.jwt.verify()`
  - `authenticatedSockets` Map tracks auth state per connection
  - All subsequent messages require authentication check
  - Cleanup on close/error removes from auth map
- **Frontend updated:** `WebCall.tsx` sends auth message on `ws.onopen`, waits for `status: ready` before sending `start`.

**CRIT-3: SSRF via tool serverUrl** (`backend/src/voice-pipeline/tool-executor.ts`)
- **Before:** User-supplied `serverUrl` on tool definitions was fetched directly — internal network scanning possible.
- **After:** Added comprehensive SSRF protection:
  - DNS pre-resolution of hostnames before connecting
  - CIDR block checking against: loopback (`127.0.0.0/8`), link-local (`169.254.0.0/16`), RFC-1918 private ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), IPv6 loopback (`::1`), IPv4-mapped IPv6 equivalents
  - Protocol restriction (http/https only)
  - `validateServerUrl()` called before every outbound tool fetch

#### HIGH Fixes

**HIGH-1: Missing org ownership checks on WebRTC endpoints** (`backend/src/webrtc/routes.ts`, `backend/src/webrtc/handler.ts`)
- ICE and end-call endpoints now verify `handler.organizationId === request.organizationId`
- Returns 404 (not 403) to avoid leaking resource existence
- Made `organizationId` public on handler (was `private readonly`)
- Added `data: null` to success responses for API envelope compliance

**HIGH-2: Unsafe `as any` casts and data passthrough**
- `backend/src/modules/tools/routes.ts`: Replaced `body as any` in PATCH handler with explicit field-by-field spread: `...(body.name !== undefined && { name: body.name })` for each field
- `backend/src/modules/phone-numbers/service.ts`: Replaced raw `data` passthrough to Prisma with explicit field destructuring (`assistantId`, `name`)

**HIGH-3: Swagger UI exposed in production** (`backend/src/index.ts`)
- Wrapped `swaggerUi` registration in `if (config.NODE_ENV !== 'production')` guard

**HIGH-4: WebSocket JWT in URL query parameter** (merged with CRIT-2 fix)
- JWT moved from URL query string to message body — prevents token leakage in server logs, proxy logs, browser history

**HIGH-5: WebRTC handler memory leak** (`backend/src/webrtc/routes.ts`, `backend/src/webrtc/handler.ts`)
- Added TTL sweep: `HANDLER_TTL_MS = 30 * 60 * 1000` (30 min), sweep every 60 seconds
- Added `pc.connectionStateChange.subscribe()` for auto-close on `failed`/`disconnected`/`closed`
- Added `handler.onClose(callback)` for auto-removal from `activeHandlers` map
- Sweep timer uses `.unref()` to not block process exit

**HIGH-6: Duplicated pipeline code across 3 transport handlers** (`backend/src/voice-pipeline/pipeline-helpers.ts` — NEW)
- Created shared helper with `extractAssistantConfig()` and `loadToolsForPipeline()`
- Updated `websocket/handler.ts`, `webrtc/handler.ts`, and `telephony/call-bridge.ts` to use shared helpers
- Eliminated ~80 lines of duplicated tool-loading/config-extraction code

**HIGH-7: templates.ts oversized (1586 lines)** (`backend/src/modules/tools/templates/` — NEW directory)
- Split monolithic `templates.ts` into 11 files organized by category:
  - `types.ts`, `scheduling.ts`, `sales.ts`, `finance.ts`, `retention.ts`, `survey.ts`, `marketing.ts`, `insurance.ts`, `healthcare.ts`, `common.ts`, `index.ts`
- Public API unchanged (same 6 exports from `index.ts`)
- Original `templates.ts` deleted
- Import paths updated in `routes.ts` and `templates.test.ts`

**HIGH-8: WebCall.tsx dual state machine / broken handleNewCall** (`frontend/src/pages/WebCall.tsx`, `frontend/src/hooks/useWebSocketCall.ts` — NEW)
- Extracted all inline WebSocket state/refs/functions (~280 lines) into `useWebSocketCall` hook
- Component now uses two clean hooks: `useWebRTC()` and `useWebSocketCall()`
- Removed 10 state variables, 8 refs, and 6 inline functions from the component
- Added `reset()` method to both `useWebRTC` and `useWebSocketCall` hooks
- `handleNewCall` now correctly resets the active hook's state via `reset()`
- Fixed stale closure bug in `ws.onclose` (functional state updater in hook)

---

### Test Infrastructure

- Updated werift mocks in `handler.test.ts` and `routes.test.ts` to include `connectionStateChange.subscribe` (required after TTL/auto-close feature)
- All 297 tests pass across 28 test files
- Backend build: 0 TypeScript errors
- Frontend types: 0 non-test errors (902 pre-existing test-only type errors from vitest mock types)

---

### Audit Summary (for reference)

| Severity | Found | Fixed | Remaining |
|----------|-------|-------|-----------|
| CRITICAL | 3 | 3 | 0 |
| HIGH | 8 | 8 | 0 |
| MEDIUM | 5 | 0 | 5 |
| LOW | 4 | 0 | 4 |

**Remaining MEDIUM issues (not yet addressed):**
- MED-1: No rate limiting on WebRTC signaling endpoints
- MED-2: No input length limits on SDP offer strings
- MED-3: `console.log` used for logging instead of structured logger
- MED-4: Missing `index.ts` barrel exports in some module directories
- MED-5: Voice pipeline session store is in-memory only (no Redis persistence)

**Remaining LOW issues (not yet addressed):**
- LOW-1: Some test files use `any` type assertions
- LOW-2: No request ID propagation for distributed tracing
- LOW-3: Missing JSDoc on some public interfaces
- LOW-4: Frontend test type errors (vitest mock type mismatches)

**Coverage:** 67.12% statements (below 80% threshold — needs more tests for telephony, campaigns, analytics modules)

---

### Files Changed Summary

| Category | Files Created | Files Modified |
|----------|--------------|----------------|
| WebRTC system | 9 | 4 |
| Security fixes | 1 (pipeline-helpers.ts) | 7 |
| Code quality | 12 (templates split + hooks) | 6 |
| Test fixes | 0 | 2 |
| **Total** | **22** | **19** |
