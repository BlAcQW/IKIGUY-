# Refined concept (product POV)

**One-tap Twi conversation anywhere.** A lightweight web widget (mic button) that lets users talk naturally in Twi and get instant Twi responses. The same core works for other Ghanaian and global languages later. North-star: **zero settings**—the agent detects what you’re speaking (Twi/English/… even mid-sentence), replies in-kind, and can also talk to you on the phone or call others.

Why it wins:

- **Twi-first experience** (rare, high demand), with high-quality ASR/TTS tuned for Ghanaian speech patterns.
- **Real-time feel** (low latency, barge-in) and **multi-turn memory**.
- **Easy embedding** (drop-in widget) and **phone connectivity** when you’re ready.

# MVP vs. Advanced phases

**MVP (4–6 weeks)**

- Web mic widget: press-to-talk, live waveform, streaming transcription, Twi replies (audio + text).
- Twi ASR: Whisper-based (server) or GhanaNLP API fallback; tune for Ghana accents.
- Twi TTS: MMS-TTS (Akan/`aka`) voice served from the backend; basic prosody controls.
- Basic dialog brain: prompt-based agent (OpenAI/Claude) with Twi in/out; configurable system prompt.
- Safety/quality: voice activity detection (VAD), basic latency budget, simple profanity filter, retries.
- Observability: session logs, latency & WER dashboard, downloadable transcripts.
- Config: switch **reply language** (Twi/English) via a toggle. WebSocket
  `language_changed` messages update the indicator and disable manual selection
  until the user hits a manual override button.

## Provider and Model Selection

`/voice/session/start` and `/voice/loop` accept `provider`, `model`, `voice`,
and `language` fields. The backend validates these against supported options to
ensure only known combinations are used.

**Advanced (post-MVP)**

- **Auto language detect & code-switching** (Twi↔English↔others) mid-utterance.
  - Includes token-level heuristics to split mixed sentences and guard translation.
- **Phone calling**: inbound/outbound via Vapi (bring your own number/Twilio import).
- **Barge-in** (interrupt TTS), **turn-taking** polish, and echo cancellation.
- **Custom voices** (cloned Ghanaian voices w/ opt-in consent), SSML style controls.
- **On-device/offline** path (mobile SDK or Electron) for kiosks/limited bandwidth.
- **Domain tools**: CRM lookups, calendar booking, payment links, knowledge base RAG.
- **Compliance**: consent beeps, PII redaction, data retention policies.

# System architecture (at a glance)

Frontend (Web)

- Mic capture (`getUserMedia`), WebAudio for VU meter, stream to backend (WebRTC or WS).
- WebRTC client (`client.ts`) adds microphone track before the offer, reports connection/ICE states, and retries dropped links.
- Play TTS audio chunks as they arrive.
- Session state (language, latency, connection), error toasts.

Backend (Edge API)

- Ingress (WebRTC SFU or WS), **VAD** gate → **ASR** (Twi model) → **NLU/Agent** → **TTS** → stream back audio.
- Optional **Realtime API** for speech-in/speech-out.
- Language-ID service (fastText) and code-switch controller.
- Language state tracker with hysteresis to avoid rapid switching.
- Persistence (Postgres/Supabase), cache (Redis).
- Analytics & traces (OpenTelemetry/Prometheus/Grafana).

Telephony (Advanced)

- Vapi for phone numbers, inbound IVR, outbound campaigns, recordings, webhooks.
- Demo 19 adds inbound PSTN webhook → WebSocket bridge with consent logging.
  Provider options (VAPI/Twilio/Vonage) are compared in [`PSTN_PROVIDERS.md`](./PSTN_PROVIDERS.md).

Docs for key parts: **getUserMedia** for mic capture (MDN) ([MDN Web Docs][1]); **WebRTC/MediaRecorder** for streaming/playback (MDN) ([MDN Web Docs][2]); **OpenAI Realtime** low-latency speech in/out (or Azure-hosted) ([OpenAI Platform][3], [Microsoft Learn][4]); **MMS-TTS** supports **Akan (`aka`)** (Twi macrolanguage) for Twi voices ([Hugging Face][5]); **Whisper** ASR + community Akan fine-tunes exist ([GitHub][6], [Hugging Face][7]); **Language-ID** via fastText lid.176 (176 langs) ([fastText][8]); **VAD** via Silero/WebRTC VAD ([GitHub][9]); **Vapi** for calls + web widget ([Vapi][10]).

---

# Components you’ll need (engineering view)

**Frontend**

- Mic capture & streaming: `navigator.mediaDevices.getUserMedia`, WebRTC `RTCPeerConnection` or WebSocket; MediaRecorder for chunking if you don’t use RTP. ([MDN Web Docs][1])
- Audio output: `<audio>` element fed incrementally (MSE) or WebAudio `AudioBufferSourceNode`.
- UI: status (listening/thinking/speaking), language toggle, waveform, latency.

**Edge/Backend**

- **Ingress**: WebRTC (SFU or simple peer) or WS. (Use OpenAI Realtime API or your own pipeline.) ([OpenAI Platform][3])
- **VAD**: Silero VAD (PyTorch/ONNX) or WebRTC VAD (CPU-light). ([GitHub][9])
- **ASR (Twi)**:
  - `faster-whisper`/`whisper.cpp` with multilingual model; test community Akan fine-tunes. ([GitHub][6], [Hugging Face][7])
  - Optional API fallback (GhanaNLP ASR) for resilience. ([translation.ghananlp.org][11])

- **Language ID / code-switch**: fastText `lid.176.bin` on sliding windows; switch routing when confidence crosses threshold. ([fastText][8])
  - Token-level heuristics split mixed-language segments before translation.
- **LLM / Dialog**: OpenAI (GPT-4o family) or Claude 3.5 Sonnet; prompt in Twi; adopt function/tool calls for actions.
- **TTS (Twi)**:
  - **Meta MMS-TTS (`facebook/mms-tts`)** for Akan (`aka`); stream PCM/Opus chunks. ([Hugging Face][5])
  - (Coqui XTTS-v2 is great but only 16 langs—not Twi—so use for other languages.) ([Coqui AI][12])

- **Telephony (later)**: Vapi: inbound call to web agent, simple outbound call.
- **Infra**: FastAPI/Node, Redis (queues/cache), Postgres/Supabase (sessions/analytics), S3 for audio.

## Demo 20 – Outbound Callbot

The prototype supports **Twilio Programmable Voice** and **Vonage Voice API** to dial whitelisted numbers and play a Twi message generated with existing TTS. Call records are stored in **MongoDB**, and a webhook updates status and opt‑outs.

### Configuration

Select the provider and credentials using environment variables:

```bash
export OUTBOUND_PROVIDER=twilio        # or "vonage"
export OUTBOUND_MONGO_URI=mongodb://localhost:27017

# Twilio
export TWILIO_ACCOUNT_SID=ACCT
export TWILIO_AUTH_TOKEN=TOKEN
export TWILIO_FROM_NUMBER=+15550001111

# Vonage
export VONAGE_API_KEY=KEY
export VONAGE_API_SECRET=SECRET
export VONAGE_FROM_NUMBER=+15550001111
```

Instantiate the manager from the environment:

```python
from apps.shared.voice_engine.outbound_call import create_manager_from_env

manager = create_manager_from_env()
manager.schedule_call("+233555000000", "Akwaaba! This is a demo call.")
```

Expose a webhook to record status changes and opt‑outs:

```python
from fastapi import FastAPI, Form

app = FastAPI()


@app.post("/voice/outbound/webhook")
def twilio_webhook(
    CallSid: str = Form(...),
    CallStatus: str = Form(...),
    Digits: str | None = Form(None),
) -> None:
    manager.handle_webhook(CallSid, CallStatus, digits=Digits)
```

**Libraries & SDKs**

- **ASR**: `openai-whisper`, `faster-whisper`, `whisper.cpp`; community Akan models. ([GitHub][6], [Hugging Face][7])
- **TTS**: `facebook/mms-tts` (HF Transformers/FAIRSEQ usage). ([Hugging Face][5])
- **VAD**: `silero-vad` / `pysilero-vad` / `py-webrtcvad`. ([GitHub][9], [PyPI][14])
- **Lang-ID**: `fasttext` + `lid.176.ftz`. ([fastText][8])
- **Realtime**: OpenAI Realtime API (browser WebRTC) or Azure-hosted equivalent. ([OpenAI Platform][3], [Microsoft Learn][4])
- **Telephony**: Vapi Web & Server SDKs. ([Vapi][15])
- **Browser**: WebRTC/MediaRecorder/WebAudio (MDN). ([MDN Web Docs][1])

---

# Sprints (example 6-week plan)

**Sprint 1 — Twi web pipeline (MVP skeleton)**

- Mic → backend stream; basic VAD gate.
- Whisper (server) for Twi; MMS-TTS voice out; play audio stream.
- Latency budget: <1.2s end-to-end.

**Sprint 2 — Dialog brain + UX**

- Twi prompts, tool-calling skeleton, error handling.
- UI polish: states, waveform, retry, session logs.

**Sprint 3 — Quality & stability**

- Barge-in, endpointing, audio chunking, retries.
- Metrics: WER, E2E latency, VAD precision/recall.

**Sprint 4 — Language toggle & early autodetect**

- Manual language switch + fastText background detection.
- Prepare router for future code-switching.

**Sprint 5 — Telephony preview (feature-flagged)**

- Vapi: inbound call to web agent, simple outbound call.
- Webhooks + call recordings in analytics. ([Vapi][10])

**Sprint 6 — Analytics & safeguards**

- Dashboards (latency, WER, drop rate), PII redaction, data retention policies.
- Beta pilot & feedback loop.

---

# PRD 1 — Twi Web Voice Agent (MVP)

**Goal**
Enable natural Twi conversations in the browser with sub-1.2s latency and ≥85% task success for scripted flows.

**Users / Jobs-to-be-Done**

- Ghanaian users who prefer speaking Twi to ask questions, get help, or practice.
- Businesses embedding a Twi assistant on their site.

\*\*In-

[1]: https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia?utm_source=chatgpt.com "MediaDevices: getUserMedia() method - MDN - Mozilla"
[2]: https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API?utm_source=chatgpt.com "WebRTC API - MDN - Mozilla"
[3]: https://platform.openai.com/docs/guides/realtime?utm_source=chatgpt.com "Realtime API - OpenAI Platform"
[4]: https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/realtime-audio-webrtc?utm_source=chatgpt.com "How to use the GPT-4o Realtime API via WebRTC (Preview) - Azure ..."
[5]: https://huggingface.co/facebook/mms-tts "facebook/mms-tts · Hugging Face"
[6]: https://github.com/openai/whisper "GitHub - openai/whisper: Robust Speech Recognition via Large-Scale Weak Supervision"
[7]: https://huggingface.co/GiftMark/akan-whisper-model?utm_source=chatgpt.com "GiftMark/akan-whisper-model"
[8]: https://fasttext.cc/docs/en/language-identification.html?utm_source=chatgpt.com "Language identification"
[9]: https://github.com/snakers4/silero-vad?utm_source=chatgpt.com "Silero VAD: pre-trained enterprise-grade Voice Activity ..."
[10]: https://docs.vapi.ai/quickstart/phone?utm_source=chatgpt.com "Phone calls"
[11]: https://translation.ghananlp.org/?utm_source=chatgpt.com "Home - GhanaNLP Translation API - developer portal"
[12]: https://docs.coqui.ai/en/latest/models/xtts.html?utm_source=chatgpt.com "TTS 0.22.0 documentation"
[13]: https://arxiv.org/pdf/2207.03546?utm_source=chatgpt.com "arXiv:2207.03546v1 [eess.AS] 7 Jul 2022"
[14]: https://pypi.org/project/pysilero-vad/?utm_source=chatgpt.com "pysilero-vad"
[15]: https://docs.vapi.ai/quickstart/web?utm_source=chatgpt.com "Web calls"

## Demo 1 – API Usage

The Core Backend provides a minimal endpoint for the mic permission and VU meter demo:

```
POST /voice/energy
```

Request body:

```json
{ "samples": [0, 1200, -900, ...] }
```

Response:

```json
{ "energy": 0.42 }
```

The endpoint delegates to `shared.voice_engine.calculate_energy` to compute a normalized RMS
value (0.0–1.0) that the frontend can display as a VU meter.

## Demo 2 – Echo Round Trip

To verify audio streaming, the Core Backend implements a simple echo service:

```
POST /voice/echo
```

Request body:

```json
{ "samples": [0, 1200, -900, ...] }
```

Response:

```json
{ "samples": [0, 1200, -900, ...] }
```

The frontend records a short clip, posts the PCM16 samples, and plays back the echoed audio.

## Demo 3 – VAD Auto Stop

Recording should end automatically once the speaker stops. The Core Backend exposes a
voice activity detection endpoint:

```
POST /voice/vad
```

Request body:

```json
{ "samples": [0, 1200, -900, ...] }
```

Response:

```json
{ "energy": 0.02, "voice": false }
```

The frontend streams audio chunks to this endpoint and stops capturing after consecutive
silent responses, enabling hands-free push‑to‑talk.

## Demo 4 – STT Partials in Twi

To illustrate streaming transcripts without heavy models, the Core Backend
provides a stubbed `/voice/stt` endpoint that decodes integer samples into text
and returns cumulative partials.

```
POST /voice/stt
```

Request body:

```json
{ "samples": [109, 101, 112, 97, 32, 119, 111, 32, 107, 121, 603, 119] }
```

Response:

```json
{
  "partials": ["mepa", "mepa wo", "mepa wo kyɛw"],
  "text": "mepa wo kyɛw",
  "language": "en",
  "confidence": 1.0
}
```

The frontend calls this route after recording to render partial and final
transcripts for Demo 4.

The endpoint now performs basic language detection. When the detected language
confidence meets the configured threshold, a `language.detected` event is
published on the session event bus. If detection is unavailable, the `language`
and `confidence` fields will be `null`.

## Demo 5 – STT Accuracy Check

To measure recognition quality, the Core Backend exposes a `/voice/wer` route
that returns the word error rate between a reference and hypothesis.

```
POST /voice/wer
```

Request body:

```json
{ "reference": "me din de kofi", "hypothesis": "me din de yaw" }
```

Response:

```json
{ "wer": 0.25 }
```

This enables Demo 5 to evaluate transcripts from a small Twi dataset.

## Demo 6 – Twi TTS Playback

The Core Backend exposes a `/voice/tts` endpoint that converts text into
synthetic PCM16 samples for lightweight playback. You can select from
several Ghanaian and Nigerian voices by passing a `voice` field in the request. If no
voice is specified, `akuapem_female` is used.

```
POST /voice/tts
```

Request body:

```json
{ "text": "akwaaba", "voice": "asante_male" }
```

Response:

```json
{ "samples": [97, 107, 119, 97, 97, 98, 97] }
```

### Available voices

| Language  | Voices                                           |
| --------- | ------------------------------------------------ |
| Twi       | `akuapem_female`, `asante_male`, `asante_female` |
| Ewe       | `ewe_female`, `ewe_male`                         |
| Ga        | `ga_male`, `ga_female`                           |
| Hausa     | `hausa_male`, `hausa_female`                     |
| Dagbani   | `dagbani_male`, `dagbani_female`                 |
| Yoruba    | `yoruba_male`, `yoruba_female`                   |
| Igbo      | `igbo_male`, `igbo_female`                       |
| Swahili   | `swahili_male`, `swahili_female`                 |
| Kikuyu    | `kikuyu_male`, `kikuyu_female`                   |
| Luo       | `luo_male`, `luo_female`                         |
| Zulu      | `zulu_male`, `zulu_female`                       |
| Xhosa     | `xhosa_male`, `xhosa_female`                     |
| Afrikaans | `afrikaans_male`, `afrikaans_female`             |

The frontend requests this endpoint and plays the returned samples to
demonstrate TTS without a heavy model.

### Demo 17 – Custom voices

Demo 17 adds a lightweight voice registry so you can switch Twi presets or plug
in your own synthesis routine. Register a voice with `register_voice` and then
refer to it in the `/voice/tts` request.

```python
from shared.voice_engine import register_voice

register_voice("custom_demo", lambda text: [1] * len(text))
```

```json
POST /voice/tts
{ "text": "ab", "voice": "custom_demo" }
```

```json
{ "samples": [1, 1] }
```

### Country language selection

To cover all African and emerging countries, a helper endpoint lists available languages by
country:

```
GET /voice/languages?country=Ghana
```

Response:

```json
{
  "country": "Ghana",
  "languages": ["English", "Akan", "Ewe", "Ga", "Dagbani", "Hausa"]
}
```

Clients can call this endpoint after a user selects a country to populate a
language picker before choosing a voice. For example:

```
GET /voice/languages?country=Brazil
```

Response:

```json
{ "country": "Brazil", "languages": ["Portuguese"] }
```

These responses allow clients to populate language pickers before choosing a voice.

## Demo 7 – E2E Voice Loop

To complete an end-to-end pipeline, the Core Backend exposes a `/voice/loop`
endpoint. It transcribes incoming PCM16 samples and returns both the text and
synthetic audio that speaks the transcript.

```
POST /voice/loop
```

Request body:

```json
{ "samples": [97, 98] }
```

Response:

```json
{
  "samples": [97, 98],
  "partials": ["a", "ab"],
  "text": "ab"
}
```

The frontend records audio, sends the samples to this route, then plays the
returned samples for a full speech-in/speech-out loop.

## Demo 8 – Interrupt / Barge-in

To simulate barge-in, the Core Backend exposes a `/voice/barge` endpoint. It
takes the TTS audio currently being played and new microphone input. If the
incoming audio has sufficient energy, the TTS playback is interrupted and no
samples are returned.

```
POST /voice/barge
```

Request body:

```json
{ "tts": [97, 98], "incoming": [1000, 1000] }
```

Response:

```json
{ "samples": [], "interrupted": true }
```

This allows clients to stop playback when a user speaks over the system.

## Demo 9 – Resilience: Retry & Fallback

To demonstrate basic resilience, the backend exposes a `/voice/retry`
endpoint. It attempts to synthesize text and will retry the primary path
before falling back to alternate text if all attempts fail.

```
POST /voice/retry
```

Request body:

```json
{ "text": "hi", "failures": 2 }
```

Response:

```json
{ "samples": [104, 105], "fallback": false }
```

If `failures` exceed the retry count, the response contains samples for the
`fallback_text` and `fallback` is set to `true`.

## Demo 10 – Manual Language Switcher


To switch between Twi and English mid-session, the backend exposes a
`/voice/language` route. The chosen language is stored in session state so
subsequent requests respond in the selected language.

```
POST /voice/language

To toggle between reply languages, the backend keeps a session-level language
setting:

```
GET /voice/language
POST /voice/language {"language": "English"}
```

Clients update this endpoint whenever a new language is chosen from a
dropdown. Subsequent requests can read the selection to route STT and TTS
correctly.


## Demo 21 – Consent + Redaction (Compliance)

The Core Backend exposes a `/voice/compliance` endpoint that masks phone numbers and email
addresses, detects consent phrases, and optionally returns raw audio when retention is
allowed.

```
POST /voice/compliance

```

Request body:

```json

{ "language": "English" }

{
  "text": "Call 123-456-7890 or email test@example.com. I agree.",
  "samples": [1, 2],
  "retain_audio": false
}

```

Response:

```json

{ "language": "English" }
```

Clients can toggle this endpoint during a conversation to update the
response language without restarting the session.

## Demo 11 – Prompt Persona & Tone

To demonstrate persona swaps, clients call `/voice/persona` with a desired
style such as `"customer_service"` or `"teacher"`. The selection updates the
system prompt template and is persisted per tenant.

```
POST /voice/persona
```

Request body:

```json
{ "persona": "teacher" }
```

Response:

```json
{ "persona": "teacher" }
```

Different personas produce noticeably different tones or formats, allowing
users to select the interaction style that best fits their needs.

{
  "redacted": "Call ***-***-**** or email ***@example.com. I agree.",
  "consent": true,
  "audio": []
}
```

## Demo 22 – Multi-Tenant Branding & Rate Limits

To showcase tenant-specific themes and quotas, the backend exposes helper
utilities:

* `tenant_branding.get_branding(tenant_id)` returns a logo URL and primary
  color for a given tenant.
* `rate_limiter.RateLimiter` enforces a requests-per-minute budget per tenant
  and raises a 429 when the quota is exceeded.

Example usage:

```python
from apps.shared.voice_engine.tenant_branding import get_branding
from apps.shared.voice_engine.rate_limiter import RateLimiter

limiter = RateLimiter(rpm=60)
branding = get_branding("acme")

if not limiter.allow("acme"):
    raise HTTPException(status_code=429, detail="Rate limit exceeded")

print(branding.logo_url, branding.primary_color)
```

Clients can switch the tenant identifier (e.g., via a JWT scope) to observe the
branding change and hit rate limits gracefully.


## Demo 15 – Auto Language Detect

This demo showcases automatic language detection between Twi and English. The
engine monitors each utterance, routes audio through the appropriate
translation pipeline, and flips languages only when confidence passes a
threshold with hysteresis to avoid rapid switching. Detection confidence is
exported via Prometheus metrics for accuracy tracking.


## Demo 16 – Code-Switch Handling

This demo shows how mixed Twi/English sentences are handled.  Tokens are
tagged with a quick heuristic that checks for Twi diacritics and treats most
capitalized words as proper nouns (so they pass through untouched).  Contiguous
English spans are routed through a translation step before the sentence is fed
to the LLM or TTS.

```python
from code_switch import tag_sentence, translate_and_merge

def translate_en_to_tw(phrase: str) -> str:
    mapping = {"appointment for Friday": "ahyɛde ma Fida"}
    return mapping.get(phrase, phrase)

tokens = tag_sentence("Mepɛ appointment for Friday anɔpa")
result = translate_and_merge(tokens, translate_en_to_tw)
assert result == "Mepɛ ahyɛde ma Fida anɔpa"
```

This ensures the agent understands the mixed utterance and responds in natural
Twi without mistranslating proper nouns like "Accra" while still translating
common day names such as "Friday".

## Demo 23 – Degraded/Offline Mode

Demo 23 showcases resilience when the backend is unreachable. The frontend
queues turns locally and retries delivery with exponential backoff until the
connection is restored.

The helper class `OfflineTurnQueue` stores turns and exposes a ``flush``
method that attempts to send queued items:

```python
from shared.voice_engine import OfflineTurnQueue

queue = OfflineTurnQueue()
queue.enqueue("turn data")

def sender(turn: str) -> None:
    ...  # deliver to backend

queue.flush(sender)
```

In production the queue would persist to IndexedDB; for the demo an in-memory
list is used. The UI should inform users when turns are queued and replay them
once connectivity returns.


