# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is LOAD?

LOAD is a developer-first platform for building, testing, and deploying conversational voice AI agents. It provides an API and dashboard for creating AI-powered phone agents that handle inbound/outbound calls using a pluggable STT → LLM → TTS voice pipeline.

**Current state:** Phases 1-2 complete (auth, assistants, voice pipeline, web calls). Phases 3-5 (telephony, tools/squads, campaigns/analytics) are scaffolded but not yet implemented.

## Commands

### Backend (`/root/home/LOAD/backend`)

```bash
npm run dev              # Start dev server (tsx watch, port 3000)
npm run build            # TypeScript compile
npm test                 # Run all tests (vitest run)
npm run test:watch       # Run tests in watch mode
npm run test:coverage    # Run tests with v8 coverage (80% threshold)
npm run lint             # ESLint on src/

# Database
npm run db:generate      # prisma generate (after schema changes)
npm run db:migrate       # prisma migrate dev (create/apply migrations)
npm run db:push          # prisma db push (sync schema without migration)
npm run db:studio        # prisma studio (visual DB editor)
```

Run a single test file:
```bash
npx vitest run src/modules/auth/service.test.ts
```

### Frontend (`/root/home/LOAD/frontend`)

```bash
npm run dev              # Vite dev server (port 5173)
npm run build            # tsc -b && vite build
npm run lint             # ESLint on src/
```

### Infrastructure

```bash
docker compose up -d             # Start postgres + redis + app
docker compose up postgres redis # Start only databases for local dev
```

API docs available at `http://localhost:3000/docs` (Swagger UI).

## Architecture

### Backend (Fastify + TypeScript)

Modular monolith. Each domain module follows the same structure:

```
src/modules/<domain>/
  routes.ts          # Fastify route registration, calls authMiddleware, validates with Zod
  schemas.ts         # Zod schemas for request validation
  service.ts         # Business logic, uses prisma client directly
  *.test.ts          # Co-located unit tests
```

**Key architectural patterns:**

- **Auth middleware** (`src/middleware/auth.ts`): Dual auth — detects `Bearer load_...` for API key auth (bcrypt-compared against DB) vs standard JWT. Sets `request.userId`, `request.organizationId`, `request.userRole` on the Fastify request.
- **All resources are organization-scoped**: Every query filters by `organizationId` from the authenticated request.
- **API response envelope**: All endpoints return `{ success, data, meta?, error? }` format.
- **Config validation** (`src/config/index.ts`): Environment variables validated at startup with Zod. App will fail fast on missing required vars.
- **Path alias**: `@/*` maps to `./src/*` (configured in both tsconfig.json and vitest.config.ts).

### Voice Pipeline (`src/voice-pipeline/`, `src/providers/`)

The pipeline orchestrates Audio → STT → LLM → TTS → Audio:

- **Provider adapters** implement typed interfaces (`STTProvider`, `LLMProvider`, `TTSProvider`) in `src/providers/{stt,llm,tts}/types.ts`. Currently only OpenAI implementations exist. New providers must implement the same interface.
- **Pipeline orchestrator** (`src/voice-pipeline/pipeline.ts`): `processPipelineTurn()` takes a session ID + audio buffer, runs through all three providers sequentially, and maintains conversation history in the session.
- **Session management** (`src/voice-pipeline/session.ts`): In-memory Map of `CallSession` objects. Sessions hold conversation history, call metadata, and status. Immutable update pattern — sessions are replaced, not mutated.
- **WebSocket handler** (`src/websocket/handler.ts`): Handles real-time bidirectional audio streaming at `WS /api/calls/web`. Receives binary PCM audio from clients, runs the pipeline, sends back audio + transcript JSON messages.

### Frontend (React + Vite + Tailwind)

- React Router with `ProtectedRoute` wrapper checking `useAuth()` hook state
- API client (`src/lib/api.ts`): Thin `fetch` wrapper using `/api` base path with JWT from `localStorage`
- Auth state (`src/lib/auth.ts` + `src/hooks/useAuth.ts`): Token stored as `load_token` in localStorage
- No state management library — local state and prop drilling

### Database (PostgreSQL + Prisma)

- Schema at `backend/prisma/schema.prisma`
- All entities use UUID primary keys
- Assistant `model`, `voice`, `transcriber` fields are JSONB (flexible provider config)
- Campaign `contacts`, `schedule`, `stats` are also JSONB

## Testing

Tests are co-located with source in `src/**/*.test.ts`. Setup file at `tests/setup.ts` sets environment variables and clears mocks between tests.

Test helpers in `tests/helpers/`:
- `prisma-mock.ts`: Creates a mock PrismaClient with vi.fn() stubs for all models
- `factories.ts`: Factory functions (`buildUser`, `buildOrganization`, `buildAssistant`, `buildApiKey`) for test data
- `app.ts`: Builds a Fastify test app instance

Tests mock the Prisma client via `vi.mock('@/database/client.js')` — they do not hit a real database.

## Screenshots

Puppeteer-based tool for capturing frontend page screenshots during development.

### Setup

```bash
npm install   # from repo root — installs puppeteer
```

### Usage

```bash
# Single page (no auth needed for public pages)
node scripts/screenshot.mjs --no-auth /login

# Protected page (auto-registers/logs in a test user)
node scripts/screenshot.mjs /

# Multiple pages
node scripts/screenshot.mjs / /assistants /settings

# All 13 pages
node scripts/screenshot.mjs all

# Custom base URL
node scripts/screenshot.mjs --base-url http://localhost:5173 /
```

### Available Pages

`/login`, `/register`, `/` (dashboard), `/assistants`, `/web-call`, `/calls`, `/phone-numbers`, `/tools`, `/squads`, `/campaigns`, `/webhooks`, `/analytics`, `/settings`

### Visual Analysis with Claude Code

Screenshots are saved to `.claude/screenshots/<slug>-<timestamp>.png`. Use the `Read` tool on a PNG to have Claude visually analyze the page. This enables a screenshot loop: make changes, take screenshot, analyze, iterate.

## Environment

Copy `.env.example` to `.env`. Required variables: `DATABASE_URL`, `JWT_SECRET` (min 16 chars). Optional: `OPENAI_API_KEY` (needed for voice pipeline), `TWILIO_ACCOUNT_SID`/`TWILIO_AUTH_TOKEN` (needed for telephony).
