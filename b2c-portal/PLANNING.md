# KasaAI – B2C Self-Serve Portal — Planning

## 1) Purpose
Self-service portal for individuals and SMEs to create assistants, launch simple campaigns, and view usage/billing—consuming **Core private APIs** (not public Developer APIs).

---

## 2) Target Users
- Solo operators, micro-businesses, SMEs.
- Early adopters testing voice/chat assistants and outbound campaigns.

---

## 3) Features
- **Onboarding**: email/Google signup; workspace creation; quick templates.
- **Assistant Builder**: choose template (sales/FAQ/reminder); set channel & language; attach KB.
- **Campaign Manager**: upload contacts, schedule, set limits; view live stats.
- **Analytics**: calls/minutes, outcomes, drop-offs, sentiment (simplified views).
- **Billing**: plan & balance; invoice history; recharge; overage alerts.
- **Support**: help center, in-app chat, ticket form.

---

## 4) Architecture
- Next.js frontend; talks to **Core private BFF** via mTLS proxy.
- Stripe/Paystack for payments; invoices mirror Core usage rollups.
- CSP allowlists for embedded WebRTC voice tests.

---

## 5) Compliance & Safety
- Consent prompts baked into templates; default PII redaction on transcripts.
- DNC checks by default; per-workspace retention settings.

---

## 6) Roadmap
- **P1**: Templates, assistant builder, basic campaigns, simple analytics.
- **P2**: Billing & invoices, usage alerts, export CSVs, WhatsApp channel.
- **P3**: Community template gallery, marketplace upsells (integrations via Developer Platform).

## 7) WebRTC Integration
- **Library Choice**: evaluate native `RTCPeerConnection` against lightweight wrappers like `simple-peer`.
  - Native API provides full control over tracks, renegotiation, and ICE handling without extra dependencies.
  - `simple-peer` offers rapid setup and simpler signaling but hides low-level events and increases bundle size.
- **Chosen Approach**: adopt native `RTCPeerConnection` in the Next.js client for voice tests to keep dependencies minimal and configuration explicit.
- **STUN/TURN**:
  - Development uses public STUN servers (e.g., `stun:stun.l.google.com:19302`).
  - Production runs a self-hosted TURN service (`turns:turn.kasa.ai:5349`) via `coturn`, enforcing TLS and issuing short-lived credentials from the Core BFF.
- **Security**: STUN reveals client IPs; TURN credentials must be ephemeral and delivered over HTTPS. Enforce rate limiting and logging on TURN, and rely on WebRTC's end-to-end encryption for media streams.
