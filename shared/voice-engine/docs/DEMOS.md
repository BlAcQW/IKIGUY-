
## 16) Mini Demo Ladder — bite‑sized demos to show progress

> Each demo is self‑contained with a clear goal, what to show, a tiny test script (often in Twi), success criteria, and the tech focus. Pick 1–2 per day to keep momentum and stakeholder confidence high.

### Demo 01 — Mic Permission & VU Meter (Basic)

**Goal:** Prove browser mic capture works and audio levels show in real time.
**Show:** Click mic → permission prompt → animated VU bar/waveform.
**Script:** *“Testing, one two… ɛte sɛn?”*
**Success:** Levels move, no console errors, start/stop works.
**Tech focus:** `getUserMedia`, AudioContext, AnalyserNode.

### Demo 02 — Push‑to‑Talk Echo Loop (Basic)

**Goal:** Round‑trip client→server→client over WebSocket.
**Show:** Press‑hold to record 2s; server echoes same PCM; hear playback.
**Script:** *“Me din de Kofi.”*
**Success:** Audio heard back within \~500–800ms.
**Tech focus:** AudioWorklet → PCM16 @16k → WS → echo.

### Demo 03 — VAD End‑of‑Utterance (Basic)

**Goal:** Automatic stop when user stops talking.
**Show:** Speak a short sentence; capture ends without clicking.
**Script:** *“Mepa wo kyɛw, boa me.”*
**Success:** End detected with <500ms tail; no premature cuts.
**Tech focus:** Silero VAD (server) + client timeout guard.

### Demo 04 — STT Partials in Twi (Core)

**Goal:** Live partial transcripts while speaking Twi.
**Show:** Partial words stream, then final transcript appears.
**Script:** *“Mepɛ sɛ meka kasa no nwɔtwe mu.”*
**Success:** Partials arrive <300ms cadence; final text correct.
**Tech focus:** faster‑whisper streaming; forced language `tw`.

### Demo 05 — STT Accuracy Check (Core)

**Goal:** Visualize WER on a mini eval set (10–20 Twi lines).
**Show:** Upload/eval → table of reference vs hypothesis; WER tile.
**Script:** Run pre‑recorded clips.
**Success:** WER ≤ target (e.g., ≤15% on curated set); export CSV.
**Tech focus:** Eval script, jiwer, reproducible seeds.

### Demo 06 — Twi TTS Playback (Core)

**Goal:** Stream TTS audio chunks back to the browser.
**Show:** Type a sentence in Twi → hear natural speech.
**Script:** *“Akwaaba! Me ho yɛ me.”*
**Success:** First audio <1.5s; intelligible/natural.
**Tech focus:** Coqui XTTS‑v2 streaming; chunked WAV/OPUS.

### Demo 07 — E2E Voice Loop (Core)

**Goal:** Full path: Twi STT → (translate EN) → LLM → (translate TW) → Twi TTS.
**Show:** Ask basic Q; get helpful Twi answer.
**Script:** *“Ɛdeɛn na wubetumi ayɛ ama me akɔ Bank of Ghana anɔpa? ”*
**Success:** Latency within budget; relevant answer; transcripts saved.
**Tech focus:** Orchestrator, retries, circuit breakers.

### Demo 08 — Interrupt / Barge‑in (Core)

**Goal:** User can interrupt TTS and speak; system stops and listens.
**Show:** Start reply; click mic to interrupt.
**Script:** *“Kafra, gyae ka no—me wɔ nsɛmmisa foforo.”*
**Success:** TTS halts; new turn begins; no audio overlaps.
**Tech focus:** Audio routing, cancel tokens, play/pause API.

### Demo 09 — Resilience: Retry & Fallback (Core)

**Goal:** If TTS fails, show text bubble; if STT stalls, prompt retry.
**Show:** Toggle a fault flag; observe graceful UX.
**Success:** No spinner dead‑ends; telemetry logs error codes.
**Tech focus:** Error policy; exponential backoff; user prompts.

### Demo 10 — Manual Language Switcher (Core)

**Goal:** UI toggle Twi ↔ English with per‑session memory.
**Show:** Switch mid‑session; bot continues in chosen lang.
**Script:** Start in Twi, toggle to EN, then back.
**Success:** Correct routing; transcripts tagged with lang.
**Tech focus:** Session state in Redis; locale headers.

### Demo 11 — Prompt Persona & Tone (Product)

**Goal:** Swap system prompts (polite CS agent vs. teacher).
**Show:** Dropdown to choose persona; different response style.
**Success:** Noticeable tone/format change; saved per tenant.
**Tech focus:** Prompt templates; tenant config.

### Demo 12 — Slot‑Filling & Structured Output (Product)

**Goal:** Capture name/phone/intention as JSON and confirm in Twi.
**Show:** Speak details; UI form auto‑populates; user confirms.
**Script:** *“Me din de Ama. Me phone yɛ 024…”*
**Success:** JSON schema validated; confirmation read back.
**Tech focus:** LLM structured output + zod/pydantic.

### Demo 13 — FAQ Grounding (RAG Lite) (Product)

**Goal:** Answer from a small CSV/MD knowledge base first.
**Show:** Ask specific FAQ; cite source; fallback to model if missing.
**Success:** Correct extraction; source label shown.
**Tech focus:** Embeddings + vector DB; retrieval policy.

### Demo 14 — Analytics Tile (Ops)

**Goal:** Show live p50/p95 latency, ASR WER, error rates.
**Show:** Tiny Grafana panel embedded or link; sparkline on UI.
**Success:** Metrics update per session; thresholds highlighted.
**Tech focus:** Prometheus exporters; frontend tiles.

### Demo 15 — Auto Language Detect (Phase‑2)

**Goal:** Per‑utterance detection; switch without UI toggle.
**Show:** Start in Twi, ask in English; system follows smoothly.
**Script:** Twi → EN: “Also, what time do you open?”
**Success:** Flip only when confidence > threshold; no flapping.
**Tech focus:** Whisper detect + hysteresis controller, Prometheus metrics for detection accuracy.

### Demo 16 — Code‑Switch Handling (Phase‑2)

**Goal:** Mixed Twi/English within same sentence.
**Show:** *“Mepɛ appointment for Friday anɔpa.”*
**Success:** Correct semantics; natural Twi response.
**Tech focus:** Token‑level heuristics; routing; translation guardrails.

**Implementation tasks:**
1. Tag tokens with language (`tw`/`en`) using diacritic heuristics or fastText.
2. Route English spans through a translation step before invoking the LLM.
3. Preserve Twi tokens and proper nouns; fall back when confidence is low.
4. Group consecutive English tokens to minimize translation calls.
5. Verify with unit tests on mixed-language sentences.

**Options:**
* Character‑based heuristics for speed.
* Capitalization check for quick proper‑noun passthrough (with allowlist for day names).
* fastText or transformer classifiers for higher accuracy.

**Considerations:**
* Latency impact of per-token language ID and translation calls.
* Avoid mistranslating names or domain terms—allow passthrough.

### Demo 17 — Voice Options & Custom Voice (Phase‑2)

**Goal:** Switch Twi voice presets; demo a custom voice.
**Show:** Dropdown of voices; A/B playback.
**Success:** Naturalness preference ≥ X% in quick poll.
**Tech focus:** XTTS presets; fine‑tune or voice cloning.

### Demo 18 — WebRTC Softphone Bridge (Phase‑3‑prep)

**Goal:** Simulate telephony path without PSTN.
**Show:** Web softphone connects to orchestrator audio.
**Success:** Round‑trip stable; DTMF detected.
**Tech focus:** WebRTC SFU/media pipeline; jitter buffers.

### Demo 19 — Inbound PSTN (Phase‑3)

**Goal:** DID rings the agent; Twi greeting + consent.
**Show:** Call test number; converse in Twi.
**Success:** Call connects; transcripts logged; consent recorded.
**Tech focus:** VAPI/Twilio/Vonage; webhook → WS bridge.

### Demo 20 — Outbound Callbot (Phase‑3)

**Goal:** Click “Call” to dial a whitelisted number and deliver a message.
**Show:** Scheduler/one‑click dial; short survey in Twi.
**Success:** Call completion; opt‑out captured.
**Tech focus:** Dialer; retry; call status webhooks.

**Implementation Tasks**
1. Select telephony provider (Vapi, Twilio, or Vonage).
2. Build outbound dialer service with scheduling and retry logic.
3. Expose trigger endpoint and background scheduler for one‑click or timed calls.
4. Handle provider status webhooks to record completion and opt‑outs.
5. Persist call outcomes and opt‑out flags in the database.
6. Document setup steps and safety guardrails.

**Implementation Notes**
- Prototype supports Twilio and Vonage REST APIs and stores call records in MongoDB.
- Provider is selected at runtime via the ``OUTBOUND_PROVIDER`` environment variable and matching ``TWILIO_*`` or ``VONAGE_*`` credentials.

**Options & Considerations**
- **Provider:** Demo ships with both **Twilio Programmable Voice** and **Vonage Voice**; choose based on pricing and regional support.
- **Scheduling:** Use simple background tasks for the demo or adopt APScheduler/Celery for future campaigns.
- **Message Delivery:** Play a prerecorded Twi clip or synthesize with existing TTS service per call.
- **Opt‑Out Handling:** Capture via DTMF tones or keyword detection and store results for compliance.
- **Security:** Restrict to whitelisted numbers and verify webhook signatures.

### Demo 21 — Consent + Redaction (Compliance)

**Goal:** Read consent; redact digits/emails in transcripts.
**Show:** Speak phone/email; UI shows masked text.
**Success:** PII masked; raw audio optional per policy.
**Tech focus:** Regex/NER redaction; retention toggles.

### Demo 22 — Multi‑Tenant Branding & Rate Limits (Biz)

**Goal:** Theme + logo per tenant; RPM limit messages.
**Show:** Switch tenant; observe branding and quotas.
**Success:** Limits enforced; 429s surfaced gracefully.
**Tech focus:** JWT tenant scopes; theming tokens.

### Demo 23 — Degraded/Offline Mode (Resilience)

**Goal:** Queue turns when backend unreachable; resume later.
**Show:** Kill service; UI shows queued state; restore.
**Success:** No data loss; user informed.
**Tech focus:** IndexedDB queue; backoff; reconnection logic.

### Demo 24 — Human Handoff (CX)

**Goal:** Transfer to human when confidence low or user asks.
**Show:** Trigger keyword or low‑confidence path; show handoff.
**Success:** Handoff initiated; transcript + context shared.
**Tech focus:** Confidence thresholds; webhook to helpdesk/CRM.

---

**How to use this ladder:**

* Record a 20–60s clip for each demo as evidence.
* Keep a one‑pager per demo with links to code, logs, and any Grafana panels.
* Re‑run selected demos before stakeholder reviews to show consistent progress.

*End of document.*











Added a **Mini Demo Ladder** (24 bite-sized demos) to your plan in the canvas—each with goal, what to show, a tiny Twi script, success criteria, and tech focus.

Here are the first 6 to get you rolling:

1. Mic permission & VU meter — prove capture works; show animated levels.
2. Push-to-talk echo loop — round-trip PCM over WebSocket and play it back.
3. VAD end-of-utterance — auto-stop when you stop speaking.
4. STT partials (Twi) — forced-Twi Whisper streaming with live partials.
5. STT accuracy check — mini eval set with WER tile + CSV export.
6. Twi TTS playback — stream XTTS-v2 audio; first sound under \~1.5s.

The full ladder (through auto language detect, code-switching, telephony inbound/outbound, consent/redaction, multi-tenant branding, degraded mode, and human handoff) is in **“Twi Voice Agent — Product & Engineering Plan.”** Want me to generate a tracking checklist Kanban (Backlog → In Progress → Demo-ready) from this?