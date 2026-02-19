You are building the **KasaAI B2C Self-Serve Portal** for AI Labs Africa.

## Goal
Deliver a polished, self-service web app where individuals and SMEs can:
- Create **AI assistants** (voice/chat/WhatsApp) from templates
- Import contacts and launch **one-time or recurring campaigns**
- View **simple analytics** (connect rate, outcomes, sentiment)
- Manage **usage & billing** (bundles, overage, invoices)
- Configure basic **integrations** via pre-built MCP connectors

## Tech & Standards
- **Framework:** Next.js 14 (App Router) + TypeScript
- **UI:** TailwindCSS + shadcn/ui; brand colors **Dark Blue `#0B1F3B`** and **Gold `#CFAE49`**
- **State/Data:** React Query (TanStack Query) + Zod for DTO validation
- **Auth:** Supabase Auth (email/password + magic link); email verification required
- **Billing:** Stripe (global) and Paystack (Africa) – toggle by region
- **Storage:** S3/MinIO for contact CSVs and light KB files
- **Charts:** Recharts
- **Env:** `NEXT_PUBLIC_API_BASE`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `STRIPE_PK`, `PAYSTACK_PK`, `S3_*`
- **API access:** use the **Core Backend private BFF** (HTTPS dev, mTLS prod) under `/internal/*`
- **Security:** reCAPTCHA on sign-up and campaign start; CSRF token on mutations; rate limits on public endpoints
- **Testing:** Vitest + Testing Library, Playwright smoke tests for sign-up → create campaign → checkout

## Information Architecture (routes)
- `/` – Landing (value prop, quick start)
- `/signup`, `/login`, `/logout`
- `/onboarding` – wizard (industry → template → channel → billing)
- `/dashboard` – usage, active campaign tiles, quick actions
- `/assistants`
  - List/Create/Edit assistant (template-first: Insurance, Banking, Real Estate, Retail, Church, Elections)
  - Prompt, guardrails (deny if not grounded), voice selection, language
- `/campaigns`
  - Create (assistant, audience upload, pacing, retries, schedule)
  - Monitor (status, connect rate, outcomes)
  - History (export CSV)
- `/audiences`
  - Import CSV, map fields (name, phone, region, tags)
  - DNC/suppression list upload
- `/billing`
  - Buy **one-time bundles** (1k / 5k / 10k / 20k / 50k minutes)
  - Show **overage rate**, **usage meter**, invoices/receipts
- `/integrations`
  - Simple MCP connectors (Google Sheets, HubSpot Lite, Webhook)
- `/settings`
  - Profile, workspace name, verified caller ID/WhatsApp (info/tutorial), consent text, time-window dialing
- `/help`
  - Quick docs, status page, contact support

## Key User Flows
1. **Onboarding Wizard**
   - Step 1: Choose industry + template
   - Step 2: Pick channel (Voice / WhatsApp / Web Chat)
   - Step 3: Configure voice/language, greeting, brand name
   - Step 4: Upload audience CSV (optional)
   - Step 5: Purchase minutes (bundle) → Stripe/Paystack checkout
   - Step 6: Launch first campaign (or save as draft)

2. **Run a One-Time Campaign**
   - Select assistant → upload audience → set schedule & pacing → preview call script → buy bundle if low balance → start
   - Live progress (connected, avg duration, outcomes) with 10s polling

3. **Upgrade/Top-Up**
   - If balance low, prompt top-up modal (bundle tiers + overage explained)
   - Show pro-rata overage estimate based on pacing and audience size

## Components
- `TemplateGallery` (industry cards with preview)
- `AssistantBuilder` (prompt, rules, voice picker)
- `AudienceUploader` (CSV dropzone + field mapper + DNC checker)
- `CampaignWizard` (steps, schedule, pacing, retries)
- `UsageMeter` (minutes left, overage projection)
- `BillingBundles` (1k/5k/10k/20k/50k tiers)
- `CheckoutButton` (Stripe/Paystack integration)
- `AnalyticsTiles` (KPI cards)
- `FunnelMini`, `SentimentMini`, `DropoffMini`
- `IntegrationCard` (Sheets, HubSpot Lite, Webhook only)
- `ConsentEditor` (text with tokens: {{brand}}, {{opt_out_code}})
- `CallPreview` (text-to-speech preview, not a live call)

## Data Models (simplified)
```ts
type Assistant = {
  id: string; name: string; channel: "voice"|"whatsapp"|"chat";
  template: string; prompt: string; language: string; voice: string;
  guardrails: { denyUngrounded: boolean };
  createdAt: string;
};

type Campaign = {
  id: string; name: string; assistantId: string;
  schedule: { startAt?: string; window: { start: string; end: string } };
  pacing: { ccr: number; retries: number; retryDelayMin: number };
  audienceRef: string; // S3 key or list id
  status: "draft"|"running"|"paused"|"completed"|"failed";
  createdAt: string;
};

type UsageSummary = {
  minutesIncluded: number;
  minutesUsed: number;
  overageRate: number; // USD per min
  projectedOverage?: number;
};

type BundlePurchase = {
  id: string; tier: "1k"|"5k"|"10k"|"20k"|"50k";
  minutes: number; priceUsd: number;
  provider: "stripe"|"paystack"; invoiceUrl: string; status: "paid"|"pending";
};
