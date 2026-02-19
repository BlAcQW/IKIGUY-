I put a complete diagram + pipeline plan on the canvas for you. Want me to tailor it to your exact stack (cloud vs on-prem, GPU type, expected concurrency) or generate infra-as-code (K8s manifests / Dockerfiles) next?
# Multilingual Faster‑Whisper with LoRA (Twi / Hausa / Ga)

A practical, bootstrap‑friendly blueprint to fine‑tune one Whisper backbone for multiple African languages using **LoRA adapters**, and to deploy low‑latency **faster‑whisper (CTranslate2)** streaming inference.

---

## 1) High‑Level System Design (Streaming Inference)

```
+-------------------+        WebRTC / gRPC / WS        +---------------------+
|  Client (App/IVR) |  ───────────────────────────────▶ |  API Gateway        |
+-------------------+                                    +---------------------+
                                                             │
                                                             │ PCM/Opus stream
                                                             ▼
                                                     +---------------------+
                                                     |  Ingress / Chunker  |
                                                     |  (VAD + Overlap)    |
                                                     +---------------------+
                                                             │ frames
                                                             ▼
                                             +-----------------------------+
                                             |  Language Detector (fast)   |
                                             |  (Whisper LD or fastText)   |
                                             +-----------------------------+
                                                       │ lang code {twi|ha|ga}
                                                       ▼
                                      +-------------------------------------------+
                                      |  Router / Orchestrator                    |
                                      |  - Picks LoRA adapter by language         |
                                      |  - Batches streams per GPU                |
                                      |  - Backpressure / QoS                     |
                                      +-------------------------------------------+
                                      │                     │                      │
                                      ▼                     ▼                      ▼
                         +-------------------+   +-------------------+   +-------------------+
                         |  Inference Pod A  |   |  Inference Pod B  |   |  Inference Pod C  |
                         |  faster-whisper   |   |  faster-whisper   |   |  faster-whisper   |
                         |  backbone (FP16)  |   |  backbone (FP16)  |   |  backbone (FP16)  |
                         |  + LoRA cache     |   |  + LoRA cache     |   |  + LoRA cache     |
                         +-------------------+   +-------------------+   +-------------------+
                                     │                     │                      │
                                     └──────────────┬──────┴──────────────┬───────┘
                                                    ▼                     ▼
                                           +-----------------+   +-----------------+
                                           |  Post‑Processor |   |  Metrics/Logs   |
                                           |  (punct, detok) |   |  + Traces       |
                                           +-----------------+   +-----------------+
                                                    │
                                                    ▼
                                           +-----------------+
                                           |   API Gateway   |
                                           +-----------------+
                                                    │
                                                    ▼
                                           +-----------------+
                                           |  Client Output  |
                                           +-----------------+
```

**Key ideas**

* Single **Whisper backbone** on GPU with **per‑language LoRA adapters** (Twi/Hausa/Ga). Adapters are tiny; hot‑swap per stream.
* **VAD + chunking with overlap** for pseudo‑streaming; batching across streams for throughput.
* **Language detection** early → selects adapter + decoding settings.
* **Autoscale** inference pods; keep a **LoRA adapter cache** on each GPU worker.

---

## 2) Data Strategy & Dataset Prep

### 2.1 Sources & Ingestion

* Public corpora: Common Voice, African speech datasets, local radio archives (with rights), podcasts, call‑center (consented), YouTube (respect ToS/rights).
* Private corpora: enterprise call recordings (DPA in place), IVR logs, agent hand‑offs.

### 2.2 Ground‑Truth & Alignment

* Prefer **exact transcripts**. If you only have subtitles, align via **forced alignment** (e.g., aeneas, Gentle) and manual spot checks.
* Normalize: lowercasing (where appropriate), remove markup, expand numerals (for TTS parity), keep diacritics where meaningful.

### 2.3 Cleaning & QA

* VAD to trim long silences; remove music/noise‑only clips.
* Language ID filter (remove non‑target language or route to the right bucket).
* Length bounds (e.g., 1–30s clips for stable batching); balance speech rates.

### 2.4 Metadata Schema (HF‑style)

```json
{
  "audio": {"path": "...", "sampling_rate": 16000, "duration": 7.2},
  "text": "ɛte sɛn?",               
  "lang": "twi",                    
  "split": "train|valid|test",
  "speaker_id": "spk_0123",
  "domain": "callcenter|news|street|ivr",
  "accent": "ashanti|akuapem|...",
  "quality": 0.0,                    
  "source": "cv|internal|yt|...",
  "license": "CC-BY-4.0|internal",
  "created_at": "2025-09-01"
}
```

### 2.5 Balancing (Key for Multi‑lingual)

* **Per‑epoch sampling weights**: oversample Ga (low hours), moderate Twi, undersample Hausa if dominant.
* Optionally **temperature sampling** across languages.

---

## 3) Training Approach (LoRA / PEFT)

### 3.1 Model Choice

* Start from **Whisper‑small / medium** multilingual checkpoint (good quality vs compute trade‑off).
* Use **PEFT/LoRA** for parameter‑efficient fine‑tuning; freeze backbone weights.

### 3.2 Tokenization & Prompts

* Keep Whisper’s text tokenizer.
* Prefix **language tokens** (e.g., `<|twi|>`, `<|hausa|>`, `<|ga|>`) or use Whisper’s language detection to set language in the decoder prompt.

### 3.3 Loss & Decoding

* Cross‑entropy on decoder outputs; label‑smoothing 0.1.
* Decoding during eval: beam size 1–4; temperature 0.0–0.3; no‑repeat‑ngram.

### 3.4 Hyperparameters (starting points)

* Batch size: effective 128–256 samples (with gradient accumulation).
* LR: 1e‑4 for LoRA adapters; cosine decay; warmup 3–5% steps.
* LoRA: r=8–16, alpha=16–32, dropout=0.05; target modules: attention projections and MLPs in the decoder/encoder.
* FP16/BF16 mixed precision; gradient checkpointing enabled.

### 3.5 Multi‑Language Strategies

* **Joint adapters**: single LoRA trained on mixed Twi/Hausa/Ga (simple to deploy).
* **Per‑language adapters**: separate LoRA per language; swap at inference (best isolation; avoids forgetting).
* **Sequential curriculum**: if datasets arrive over time, rehearse earlier languages each epoch to avoid forgetting.

### 3.6 Evaluation

* Split test by **domain** and **speaker** (unseen).
* Metrics: WER/CER per language, latency (RTF), memory use.
* Error tagging: spelling variants, code‑switching, numbers, names.

---

## 4) Training Pipeline (Orchestration)

```
[Data Lake] ──▶ [Ingest] ─▶ [Clean/VAD/LD] ─▶ [Shard + Balance] ─▶ [HF Datasets]
                                                      │
                                                      ▼
                                           [Trainer (PyTorch + PEFT)]
                                                      │
                                  ┌───────────────┬───────────────┬───────────────┐
                                  ▼               ▼               ▼
                           LoRA (twi).safetensors  LoRA (ha).safetensors  LoRA (ga).safetensors
                                                      │
                                                      ▼
                             [Eval / Regression / Drift checks per language]
                                                      │
                                                      ▼
                              [Model Registry]  (backbone ver + adapter vers)
```

**Tooling**

* **PyTorch + Hugging Face Transformers** for training; **PEFT** for LoRA.
* **Weights & Biases** or MLflow for experiment tracking.
* **DVC** or LakeFS for dataset versioning.
* **Prefect/Airflow** to orchestrate ingest → train → eval → register.

---

## 5) Packaging for Inference (CTranslate2 / faster‑whisper)

1. Export Whisper backbone to **CTranslate2** format (FP16 for GPU, INT8 for CPU variants).
2. Save LoRA adapters as small **safetensors**; keep a JSON map:

```json
{
  "backbone": "whisper-small-ct2-fp16/",
  "adapters": {
    "twi": "lora-twi.safetensors",
    "hausa": "lora-ha.safetensors",
    "ga": "lora-ga.safetensors"
  },
  "decode_defaults": {
    "beam_size": 1,
    "temperature": 0.0,
    "vad": true,
    "chunk_sec": 5.0,
    "overlap_sec": 0.5
  }
}
```

3. Validate numerical parity vs PyTorch during a **golden set** inference check.

---

## 6) Deployment Blueprint (Kubernetes‑friendly)

**Services**

* **api‑gateway**: HTTP/gRPC/WebSocket; auth (JWT), rate limiting.
* **stream‑ingress**: WebRTC/WS termination, resampling → 16kHz mono.
* **asr‑router**: language detect + route to an **inference‑worker** with the right adapter; micro‑batches chunks.
* **inference‑worker**: faster‑whisper (CT2) + adapter cache on **GPU**; expose gRPC for batched decode.
* **post‑processor**: punctuation, de‑tokenization, casing; optional NER for numbers/names.
* **metrics**: Prometheus + Grafana; **tracing**: OpenTelemetry; **logs**: Loki/ELK.

**Performance knobs**

* GPU: FP16; set `num_streams` per worker; pin CPU threads for I/O.
* Batching: accumulate up to N chunks or T milliseconds.
* VAD: drop silence to reduce load.
* Adapter cache: keep hot adapters in VRAM; LRU evict cold ones.

**Autoscaling**

* HPA on queue depth / p95 latency / GPU util.
* Scale out inference‑workers first; keep short cold‑start by preloading backbone.

**Fallbacks**

* If GPU pool saturated → route to CPU tier with **INT8** CT2 for small models.
* Circuit breaker to shed low‑priority traffic during spikes.

---

## 7) Inference Flow (Pseudocode)

```python
# gateway receives audio frames -> sends to router
lang = detect_language(frame_batch)  # fast detector or Whisper LD on a small pre-roll
adapter = adapter_map[lang]

# choose a worker with the adapter cached (or load it)
worker = pick_worker(lang, adapter)

# micro-batch chunks for throughput
chunks = make_chunks(frames, chunk_sec=5.0, overlap=0.5)

for batch in micro_batch(chunks, max_items=8, timeout_ms=20):
    result = worker.transcribe(
        batch,
        adapter=adapter,
        beam_size=1,
        vad=True,
        return_timestamps=True,
    )
    stream_out(result)
```

---

## 8) Training Script Sketch (LoRA, multi‑lang)

```python
from peft import LoraConfig, get_peft_model
from transformers import WhisperForConditionalGeneration, WhisperProcessor
from datasets import load_dataset, interleave_datasets

langs = ["twi", "ha", "ga"]
sets = [load_dataset("my_corpus", lang) for lang in langs]
# Balance: oversample low-resource languages
dataset = interleave_datasets(
    [s["train"] for s in sets],
    probabilities=[0.4, 0.4, 0.2],  # example: give Ga more weight if smaller
    seed=42,
)

proc = WhisperProcessor.from_pretrained("openai/whisper-small")
model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-small")

peft_cfg = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05,
                      target_modules=["q_proj","k_proj","v_proj","o_proj","fc1","fc2"])
model = get_peft_model(model, peft_cfg)

# ... training loop with mixed precision, grad accumulation, label smoothing ...
# log WER/CER per language; save separate adapters or a joint one
```

---

## 9) Testing & QA

* **Per‑language test suites** (Twi/Hausa/Ga) with domain slices (news, phone, street).
* **Latency tests**: end‑to‑text p50/p95; measure real‑time factor (RTF).
* **Robustness**: background noise, code‑switching, low SNR.
* **Drift monitors**: rolling WER on sampled production calls; alert on regressions.

---

## 10) Ops, Cost & Growth

* Start with **1× GPU node** (e.g., 24–48GB VRAM) + CPU fallback tier; add nodes as traffic grows.
* Use **spot GPUs** for batch training; keep a small on‑demand pool for steady inference.
* Store raw audio in object storage; retain transcripts + timestamps; anonymize PII.
* Monthly cost model: GPU hours (training/inference) + storage + egress; set budgets & alerts.

---

## 11) Security & Compliance

* Consent management, data minimization; redact PII (names/numbers) if required.
* Encrypt at rest (SSE‑S3 or KMS) and in transit (mTLS).
* Access controls for model registry, datasets, and adapters per customer/tenant.

---

## 12) What to Build First (MVP)

1. Ingest + clean small Twi/Hausa/Ga corpus (100–300 hrs total).
2. Train **per‑language LoRA** adapters on Whisper‑small.
3. Export backbone -> **CTranslate2**, serve with **faster‑whisper**.
4. Deploy **one GPU inference worker** + CPU fallback; measure latency & WER.
5. Add autoscaling, adapter cache, and domain‑specific post‑processing.

---

**You can iterate on this doc as we lock in your exact stack (cloud vs on‑prem, GPU type, provider).**
