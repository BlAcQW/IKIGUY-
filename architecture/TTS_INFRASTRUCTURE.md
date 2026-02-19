# TTS Infrastructure Architecture

**Last Updated:** November 3, 2025
**Status:** Production Operational
**Maintainer:** AI Labs Africa Infrastructure Team

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Provider Ecosystem](#provider-ecosystem)
4. [Deployment Models](#deployment-models)
5. [Network Architecture](#network-architecture)
6. [Integration Patterns](#integration-patterns)
7. [Monitoring & Health Checks](#monitoring--health-checks)
8. [Scaling & Resource Management](#scaling--resource-management)
9. [Security & Access Control](#security--access-control)
10. [Development vs Production](#development-vs-production)
11. [Troubleshooting](#troubleshooting)

---

## Overview

The KasaAI TTS (Text-to-Speech) infrastructure provides a unified, multi-provider synthesis platform supporting 8 different TTS engines with varying capabilities, languages, and specializations.

### Design Principles

1. **Provider Abstraction** - Single API for all TTS providers
2. **High Availability** - Multiple providers for failover and redundancy
3. **Resource Optimization** - GPU allocation across local and cloud instances
4. **Language Diversity** - Support for 17+ languages including Ghanaian Twi
5. **Voice Cloning** - Advanced voice replication across multiple providers

### Key Metrics

- **Providers:** 10 total (6 production, 2 specialty, 1 comprehensive platform, 1 voice conversion)
- **Availability:** 100% (8/8 active providers online)
- **Languages:** 17+ languages supported (TTS), Language-agnostic (RVC)
- **Response Time:** <150ms for health checks
- **GPU Utilization:** ~20% local, ~20% RunPod (including TTS-WebUI and RVC)

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Applications                       │
│  (ChurchFlow, StudyFlow, InkWave, EventFlow, Core Backend)     │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│              Shared Services Layer (@shared)                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │         TTSProviderService (tts_provider_service.py)      │  │
│  │  - Unified API for all providers                          │  │
│  │  - Automatic billing & cost tracking                      │  │
│  │  - Health monitoring & failover                           │  │
│  │  - Voice cloning support                                  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│  ┌───────────────────────────┴──────────────────────────────┐  │
│  │            AIProviderRegistry (provider_registry.py)      │  │
│  │  - Provider discovery & configuration                     │  │
│  │  - Capability-based provider selection                    │  │
│  │  - Status tracking & updates                              │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────┬───────────────────────────────────────────┘
                      │
         ┌────────────┴──────────────┐
         ▼                           ▼
┌─────────────────────┐    ┌──────────────────────┐
│  Production Server  │    │   RunPod GPU Cloud   │
│  (148.251.0.46)     │    │  (194.68.245.121)    │
│                     │    │                      │
│  Local Providers:   │    │  Cloud Providers:    │
│  - Coqui XTTS      │    │  - F5-TTS           │
│  - MeloTTS         │    │  - StyleTTS2        │
│  - OpenVoice       │    │  - RVC (Port 8017)  │
│  - Kokoro TTS      │    │                      │
│                     │    │  GPU: NVIDIA A40     │
│  GPU: 20GB VRAM     │    │  VRAM: 46GB          │
└─────────────────────┘    └──────────────────────┘
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│   Nginx Reverse     │
│      Proxy          │
│  - SSL/TLS          │
│  - Load Balancing   │
│  - CORS Handling    │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│   HTTPS Endpoints   │
│  *.ailabsafrica.com │
└─────────────────────┘
```

---

## Provider Ecosystem

### Production Providers (6)

#### 1. Coqui XTTS v2
**API Endpoint:** `https://coqui.ailabsafrica.com`
**UI Endpoint:** `https://coqui-ui.ailabsafrica.com` (Gradio Interface)
**Port:** API: 8005, UI: localhost:8015
**Deployment:** Local Docker (Production Server)

**Capabilities:**
- ✅ Voice Cloning
- ✅ 17 Languages
- ✅ Multi-speaker
- ✅ Speed Control

**Languages:** en, es, fr, de, it, pt, pl, tr, ru, nl, cs, ar, zh-cn, hu, ko, ja, hi

**Use Cases:**
- Multilingual content generation
- Voice cloning for brand consistency
- High-quality audiobook narration
- Default provider for most applications

**GPU Requirements:** ~2GB VRAM

---

#### 2. MeloTTS
**API Endpoint:** `https://melotts.ailabsafrica.com`
**UI Endpoint:** `https://melotts-ui.ailabsafrica.com` (Gradio Interface)
**Port:** API: 8001, UI: localhost:8011
**Deployment:** Local Docker (Production Server)

**Capabilities:**
- ❌ No Voice Cloning
- ✅ 6 Languages
- ✅ Multi-speaker
- ✅ Speed Control
- ✅ Pitch Control

**Languages:** EN, ES, FR, ZH, JP, KR

**Use Cases:**
- Fast synthesis for real-time applications
- Multi-speaker dialogues
- Low-latency requirements
- Mobile applications

**GPU Requirements:** ~1GB VRAM

---

#### 3. OpenVoice
**API Endpoint:** `https://openvoice.ailabsafrica.com`
**UI Endpoint:** `https://openvoice-ui.ailabsafrica.com` (Gradio Interface)
**Port:** API: 8003, UI: localhost:8013
**Deployment:** Local Docker (Production Server)

**Capabilities:**
- ✅ Voice Cloning
- ✅ Emotion Control
- ✅ Tone Conversion
- ✅ 2 Languages (EN, ZH)

**Special Features:**
- 11 Target Speakers
- Advanced emotion control
- Tone converter for voice transformation

**Use Cases:**
- Emotional content (storytelling, entertainment)
- Voice transformation
- Character voices for games/media
- English-Chinese bilingual content

**GPU Requirements:** ~1GB VRAM

---

#### 4. Kokoro TTS
**API Endpoint:** `https://kokoro.ailabsafrica.com`
**UI Endpoint:** `https://kokoro-ui.ailabsafrica.com` (Gradio Interface)
**Port:** API: 8010, UI: localhost:8021
**Deployment:** Local Docker (Production Server)

**Capabilities:**
- ❌ No Voice Cloning
- ✅ English Only
- ✅ 11 Voicepacks
- ✅ Speed Control

**Use Cases:**
- High-quality English narration
- Podcast generation
- English-only applications
- Professional voiceovers

**GPU Requirements:** Minimal (~500MB VRAM)

---

#### 5. F5-TTS
**API Endpoint:** `https://f5tts.ailabsafrica.com`
**UI Endpoint:** `https://f5tts-ui.ailabsafrica.com` (Gradio Interface)
**Port:** API: 8002 (RunPod), UI: 8011 (RunPod)
**Deployment:** RunPod GPU Cloud (NVIDIA A40)

**Capabilities:**
- ✅ Voice Cloning
- ✅ Flow-Matching TTS
- ✅ 4 Languages (en, zh, ja, ko)
- ✅ High Quality

**Special Features:**
- Flow-matching based synthesis
- Excellent voice cloning quality
- Requires reference audio

**Use Cases:**
- Premium voice cloning
- Asian language content (Japanese, Korean, Chinese)
- High-fidelity synthesis
- Character voice creation

**GPU Requirements:** ~1.5GB VRAM (A40)

---

#### 6. StyleTTS2
**API Endpoint:** `https://styletts.ailabsafrica.com`
**UI Endpoint:** `https://styletts-ui.ailabsafrica.com` (TTS-WebUI Gradio Interface)
**Port:** API: 8006 (RunPod), UI: 8013 (RunPod)
**Deployment:** RunPod GPU Cloud (NVIDIA A40)

**Capabilities:**
- ✅ Voice Cloning
- ✅ Style Transfer
- ✅ Emotion Control
- ✅ English Only

**Special Features:**
- Highly expressive synthesis
- Style transfer capabilities
- Emotional voice generation

**Use Cases:**
- Expressive storytelling
- Audiobook narration with emotion
- Character voices with personality
- Premium English content

**GPU Requirements:** ~1.5GB VRAM (A40)

---

### Specialty Providers (2)

#### 7. Kyutai Moshi
**Endpoint:** `http://localhost:8011` (Local only)
**Port:** 8011
**Deployment:** Local Docker (when running)

**Capabilities:**
- ❌ No Voice Cloning
- ✅ Real-time Conversation
- ✅ Full-duplex Dialogue
- ✅ Ultra-low Latency

**Special Features:**
- Real-time conversational AI
- Bidirectional spoken dialogue
- Streaming audio processing

**Use Cases:**
- Real-time voice assistants
- Interactive voice systems
- Live customer service bots
- Voice-based games

**GPU Requirements:** ~15GB VRAM
**Status:** Not exposed publicly (resource-intensive, specialty use)

---

#### 8. AKAN MMS (Twi)
**Endpoint:** `https://flow-api.ailabsafrica.com/api/voice-lab`
**Deployment:** Voice Lab Service

**Capabilities:**
- ❌ No Voice Cloning
- ✅ Twi Language (Asante, Akuapem, Fante)
- ✅ 6 Native Speaker Voices (3 male, 3 female)
- ✅ Speed Control
- ✅ Pitch Control

**Use Cases:**
- Ghanaian language content
- Local educational applications
- Cultural preservation
- Vernacular radio/media

**Integration:** Uses Voice Lab service architecture (different API pattern)

---

#### 9. TTS-WebUI (Comprehensive Platform)
**Endpoint:** `https://tts-webui.ailabsafrica.com`
**Ports:**
- React UI: 3000
- Gradio Backend: 7770
- OpenAI API: 7778
- Nginx Proxy: 8016
**Deployment:** RunPod GPU Cloud (NVIDIA A40)

**Capabilities:**
- ✅ 20+ TTS Models
- ✅ Voice Cloning (multiple providers)
- ✅ Multi-language (depends on selected model)
- ✅ Extension Manager
- ✅ React UI + Gradio Backend
- ✅ OpenAI-compatible API

**Included Models:**
- **Core**: StyleTTS2, RVC, Bark, Tortoise, MeloTTS, MMS, Demucs, Vocos
- **Advanced**: F5-TTS, XTTS v2, OpenVoice, Kokoro, Parler TTS
- **Specialty**: Whisper (ASR), MusicGen, Stable Audio
- **Experimental**: GPT-SoVITS, Chatterbox, MahaTTS, VALL-E X

**Special Features:**
- Unified interface for all models
- Extension system for easy model installation
- React-based web UI (Next.js)
- Gradio backend for model management
- OpenAI-compatible API for programmatic access
- Voice cloning across multiple providers
- Audio processing tools (Demucs for separation)
- ASR integration (Whisper)
- Music generation (MusicGen, Stable Audio)

**Use Cases:**
- Centralized TTS platform for all models
- Voice cloning experimentation
- Multi-model comparison
- Extension-based model management
- API-based programmatic synthesis
- Audio research and development
- Music and sound generation

**GPU Requirements:** ~15-20GB VRAM (varies by active models)

**Architecture:**
```
User Browser / API Client
    ↓
https://tts-webui.ailabsafrica.com
    ↓
Local Nginx (148.251.0.46) + SSL
    ↓
RunPod Proxy (jzfmzviw26huka-8016.proxy.runpod.net)
    ↓
RunPod Nginx (port 8016)
    ↓
TTS-WebUI React UI (port 3000)
    ├── Gradio Backend (port 7770)
    └── OpenAI API (port 7778)
        ↓
    20+ TTS Models
```

**Programmatic Access:**
```python
from apps.shared.services.tts_webui_service import (
    TTSWebUIService,
    TTSWebUISynthesisRequest,
    TTSWebUIProvider
)

# Initialize service
service = TTSWebUIService()

# Synthesize with StyleTTS2
request = TTSWebUISynthesisRequest(
    text="Hello from TTS-WebUI",
    provider_id=TTSWebUIProvider.STYLETTS2,
    language="en"
)
response = await service.synthesize(request)

# Voice cloning with F5-TTS
from apps.shared.services.tts_webui_service import TTSWebUIVoiceCloneRequest

clone_request = TTSWebUIVoiceCloneRequest(
    text="Cloned voice speaking",
    provider_id=TTSWebUIProvider.F5_TTS,
    reference_audio_base64=audio_b64
)
clone_response = await service.synthesize_with_voice_cloning(clone_request)
```

**RunPod Configuration:**
- **Pod ID:** jzfmzviw26huka-644113c7
- **GPU:** NVIDIA A40 (44GB VRAM)
- **SSH Access:** `ssh -p 22153 root@194.68.245.121`
- **Container Location:** `/workspace/tts-deployment/docker/tts-webui/`
- **Python Environment:** `/workspace/tts-deployment/docker/tts-webui/venv`

**Service Management:**
```bash
# SSH to RunPod
ssh -p 22153 root@194.68.245.121

# Check services
ps aux | grep -E "(next start|python3 server.py)"
ss -tlnp | grep -E ':(3000|7770|7778|8016)'

# Restart TTS-WebUI
pkill -f "python3 server.py"
cd /workspace/tts-deployment/docker/tts-webui
source venv/bin/activate
nohup python3 server.py --docker > /tmp/tts-webui.log 2>&1 &

# Restart Nginx
nginx -s reload

# View logs
tail -f /tmp/tts-webui.log
```

**Extension Management:**
- Extensions can be installed via WebUI interface
- Navigate to Extensions tab
- Search for desired model (e.g., "GPT-SoVITS")
- Click Install
- Restart server after installation

**Status:** Production Ready ✅

---

#### 10. RVC Voice Conversion

**Type:** Voice Conversion & Transformation
**Endpoint:** `https://rvc.ailabsafrica.com`
**Port:** 8017
**GPU:** NVIDIA A40 (44.43GB VRAM) on RunPod
**Status:** Production ✅

**Capabilities:**
- **Voice Conversion** - Transform voice characteristics while preserving speech content
- **Multiple Pitch Extraction Methods** - RMVPE (recommended), Harvest, PM, FCPE, CREPE
- **Index-based Retrieval** - High-quality voice feature matching
- **Real-time Processing** - Suitable for near-real-time applications
- **Model Training Support** - Via Gradio WebUI interface
- **GPU Acceleration** - CUDA-accelerated inference

**Architecture:**
- **Framework:** VITS (Variational Inference with adversarial learning)
- **Vocoder:** HiFi-GAN for natural audio generation
- **Feature Extractor:** ContentVec for voice features
- **Speech Model:** HuBERT base model (181MB)
- **Pitch Detector:** RMVPE model (173MB)
- **Python:** 3.10 (required for fairseq compatibility)
- **Dependencies:** PyTorch 2.1.0, fairseq 0.12.2, gradio 3.34.0

**Use Cases:**
```python
# 1. Voice Character Transformation
response = requests.post(
    "https://rvc.ailabsafrica.com/convert",
    files={"audio": ("input.wav", audio_data, "audio/wav")},
    data={
        "model_path": "logs/character_voice/model.pth",
        "pitch_shift": 2,
        "index_rate": 0.8,
        "f0_method": "rmvpe"
    }
)

# 2. Voice Anonymization
response = requests.post(
    "https://rvc.ailabsafrica.com/convert",
    files={"audio": ("interview.wav", audio_data, "audio/wav")},
    data={
        "model_path": "logs/neutral_voice/model.pth",
        "protect": 0.5,
        "rms_mix_rate": 0.3,
        "f0_method": "rmvpe"
    }
)

# 3. Voice Restoration
response = requests.post(
    "https://rvc.ailabsafrica.com/convert",
    files={"audio": ("poor_quality.wav", audio_data, "audio/wav")},
    data={
        "model_path": "logs/clear_voice/model.pth",
        "filter_radius": 5,
        "index_rate": 0.7,
        "f0_method": "rmvpe"
    }
)
```

**API Endpoints:**
- `GET /health` - Health check and status
- `GET /models` - List available RVC models
- `POST /convert` - Convert voice using RVC model
- `GET /docs` - FastAPI interactive documentation

**Performance Benchmarks:**
- **Short Audio (5s):** ~1-2 seconds
- **Medium Audio (30s):** ~6-8 seconds
- **Long Audio (2min):** ~25-30 seconds
- **GPU Memory:** ~2GB VRAM during inference
- **Audio Quality:** 24kHz, 16-bit WAV output
- **Pitch Accuracy:** >95% with RMVPE

**RunPod Configuration:**
```bash
# SSH Access
ssh -p 22153 root@194.68.245.121

# Location
cd /workspace/rvc-webui

# Virtual Environment (Python 3.10)
source venv/bin/activate

# Start API Server
python app.py --port 8017 --host 0.0.0.0

# Start Gradio WebUI (for model training)
python infer-web.py
# Access at http://localhost:7865
```

**Model Management:**
```bash
# List available models
curl https://rvc.ailabsafrica.com/models

# Models are stored in logs/ directory
# Example structure:
# logs/
# ├── character_voice/
# │   ├── model.pth (54MB)
# │   └── added_*.index (voice features)
# └── neutral_voice/
#     ├── model.pth (54MB)
#     └── added_*.index
```

**Service Management:**
```bash
# Check if RVC is running
curl https://rvc.ailabsafrica.com/health

# Expected response:
# {
#   "status": "healthy",
#   "device": "cuda:0",
#   "current_model": null,
#   "timestamp": 1762625858.296
# }

# View API logs on RunPod
ssh -p 22153 root@194.68.245.121
tail -f /tmp/rvc_api_8017.log
```

**Model Training (via Gradio WebUI):**
1. **Prepare Training Data** - 5-30 minutes of clean audio from target speaker
2. **Upload Audio** - Via Gradio interface at port 7865
3. **Process Audio** - Extract features (ContentVec + RMVPE)
4. **Train Model** - 2-4 hours on A40 GPU
5. **Generate Index** - Create voice feature index for retrieval
6. **Deploy** - Models automatically available via API

**Extension Management:**
- Model training via Gradio WebUI interface
- Upload training audio through web interface
- Monitor training progress with tensorboard
- Export trained models to logs/ directory
- Models immediately available via API after training

**Parameters:**
- `pitch_shift` - Pitch shift in semitones (-12 to +12)
- `index_rate` - Voice similarity (0.0-1.0, recommend 0.75)
- `filter_radius` - Smoothing radius (1-7, recommend 3)
- `rms_mix_rate` - Volume matching (0.0-1.0, recommend 0.25)
- `protect` - Consonant protection (0.0-0.5, recommend 0.33)
- `f0_method` - Pitch extraction method (rmvpe, harvest, pm, fcpe, crepe)

**Nginx Configuration:**
```nginx
# /tmp/rvc.ailabsafrica.com.conf
server {
    listen 443 ssl http2;
    server_name rvc.ailabsafrica.com;

    ssl_certificate /etc/letsencrypt/live/rvc.ailabsafrica.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/rvc.ailabsafrica.com/privkey.pem;

    client_max_body_size 100M;

    location / {
        proxy_pass https://jzfmzviw26huka-8017.proxy.runpod.net;
        proxy_http_version 1.1;
        proxy_set_header Host jzfmzviw26huka-8017.proxy.runpod.net;
        proxy_connect_timeout 120s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
        proxy_ssl_server_name on;
        proxy_ssl_verify off;
    }
}
```

**SSL Certificate:**
- Provider: Let's Encrypt
- Domain: rvc.ailabsafrica.com
- Expires: February 6, 2026
- Auto-renewal: Configured via certbot

**Documentation:**
- **Service Documentation:** `@shared/voice_engine/RVC_VOICE_CONVERSION.md`
- **API Docs:** https://rvc.ailabsafrica.com/docs
- **Health Check:** https://rvc.ailabsafrica.com/health
- **GitHub:** https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI

**Status:** Production Ready ✅

---

## Deployment Models

### Local Docker Deployment (Production Server)

**Server:** 148.251.0.46
**GPU:** NVIDIA GPU (20GB VRAM)
**OS:** Ubuntu Server

**Services:**
```yaml
# docker-compose.local.yml
services:
  coqui:
    image: ghcr.io/coqui-ai/tts
    ports: ["8005:8005"]
    deploy:
      resources:
        reservations:
          devices: [driver: nvidia, count: 1, capabilities: [gpu]]

  melotts:
    ports: ["8001:8001"]
    deploy:
      resources:
        reservations:
          devices: [driver: nvidia, count: 1, capabilities: [gpu]]

  openvoice:
    ports: ["8003:8003"]
    deploy:
      resources:
        reservations:
          devices: [driver: nvidia, count: 1, capabilities: [gpu]]

  kokoro:
    ports: ["8010:8010"]
    deploy:
      resources:
        reservations:
          devices: [driver: nvidia, count: 1, capabilities: [gpu]]
```

**Management Commands:**
```bash
# Start all services
cd /opt/kasaai/apps/tts-deployment
docker-compose -f docker-compose.local.yml up -d

# Check status
docker ps | grep -E "(coqui|melo|openvoice|kokoro)"

# View logs
docker logs <service-name>

# Restart specific service
docker restart <service-name>
```

---

### RunPod Cloud Deployment

**Instance:** 194.68.245.121
**GPU:** NVIDIA A40 (46GB VRAM)
**SSH Port:** 22130

**Services:**
```yaml
# docker-compose.runpod.yml
services:
  f5tts:
    ports: ["8002:8002"]
    deploy:
      resources:
        reservations:
          devices: [driver: nvidia, count: 1, capabilities: [gpu]]

  styletts2:
    ports: ["8004:8004"]
    deploy:
      resources:
        reservations:
          devices: [driver: nvidia, count: 1, capabilities: [gpu]]
```

**Access & Management:**
```bash
# SSH to RunPod
ssh root@194.68.245.121 -p 22130

# Once connected
cd /workspace/tts-deployment
docker-compose up -d

# Check GPU usage
nvidia-smi

# View services
docker ps
```

**Port Tunneling:**
RunPod services are tunneled back to production server via SSH reverse tunnels or similar mechanism, making them accessible through production Nginx proxy.

---

## Network Architecture

### DNS Configuration

All TTS provider domains are CNAMEs or A records pointing to production server:

```
coqui.ailabsafrica.com       A    148.251.0.46
melotts.ailabsafrica.com     A    148.251.0.46
openvoice.ailabsafrica.com   A    148.251.0.46
kokoro.ailabsafrica.com      A    148.251.0.46
f5tts.ailabsafrica.com       A    148.251.0.46
styletts.ailabsafrica.com    A    148.251.0.46
tts-webui.ailabsafrica.com   A    148.251.0.46
```

### Nginx Reverse Proxy

**Configuration Pattern:**
```nginx
# Example: /etc/nginx/sites-available/coqui.ailabsafrica.com.conf
server {
    listen 443 ssl http2;
    server_name coqui.ailabsafrica.com;

    ssl_certificate /etc/letsencrypt/live/coqui.ailabsafrica.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/coqui.ailabsafrica.com/privkey.pem;

    client_max_body_size 50M;

    location / {
        proxy_pass http://localhost:8005;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;

        # CORS headers
        add_header 'Access-Control-Allow-Origin' 'https://flow.ailabsafrica.com' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
    }

    location /health {
        proxy_pass http://localhost:8005/health;
        access_log off;
    }
}
```

**SSL/TLS:**
- Certificate Authority: Let's Encrypt
- Auto-renewal: Configured via certbot
- Protocols: TLS 1.2, TLS 1.3
- Ciphers: Strong cipher suites only

**CORS:**
- Origin: `https://flow.ailabsafrica.com` and app-specific domains
- Methods: GET, POST, OPTIONS
- Headers: Content-Type, Authorization
- Preflight: OPTIONS requests handled

---

## Integration Patterns

### Provider Registry Pattern

**File:** `apps/shared/integration/ai_services/provider_registry.py`

```python
# Provider configuration
def get_default_tts_providers_config() -> Dict[str, Dict[str, Any]]:
    return {
        "coqui_xtts": {
            "name": "Coqui XTTS v2",
            "endpoint": os.getenv("COQUI_ENDPOINT", "https://coqui.ailabsafrica.com"),
            "provider_type": "tts",
            "languages": 17,
            "capabilities": {
                "voiceCloning": True,
                "multiLanguage": True,
                "speedControl": True,
            }
        },
        # ... other providers
    }

# Usage in applications
registry = AIProviderRegistry()
registry.register_providers_from_config(
    get_default_tts_providers_config(),
    provider_type=ProviderType.TTS
)

# Get provider by capability
voice_cloning_providers = registry.get_providers_by_capability("voiceCloning")

# Get specific provider
coqui = registry.get_provider("coqui_xtts")
```

### TTS Provider Service Pattern

**File:** `apps/shared/services/tts_provider_service.py`

```python
from apps.shared.services.tts_provider_service import (
    TTSProviderService,
    SynthesisRequest
)

# Initialize service
tts_service = TTSProviderService(enable_billing=False)  # Skip billing for internal use
await tts_service.initialize()

# Simple synthesis
result = await tts_service.synthesize(
    user_id="user_123",
    request=SynthesisRequest(
        provider_id="coqui_xtts",
        text="Welcome to ChurchFlow!",
        language="en",
        voice_id="nova"
    )
)

# Voice cloning synthesis
from apps.shared.services.tts_provider_service import VoiceCloneRequest

clone_result = await tts_service.synthesize_with_voice_cloning(
    user_id="user_123",
    request=VoiceCloneRequest(
        provider_id="f5tts",
        text="This is cloned voice",
        reference_audio_base64=audio_b64,
        language="en"
    )
)
```

### Health Monitoring Pattern

```python
# Check provider health
providers_health = await tts_service.get_all_providers_health(force_refresh=True)

for provider_health in providers_health:
    print(f"{provider_health.provider_id}: {provider_health.status}")
    if not provider_health.healthy:
        print(f"  Error: {provider_health.error_message}")
```

### Application Integration (ChurchFlow Example)

**File:** `apps/churchflow/backend/app/api/routes/registrations.py`

```python
from app.services.voice_greeting_service import VoiceGreetingService

# During conference check-in
if conference.get("voice_greeting", {}).get("enabled", False):
    voice_greeting_service = VoiceGreetingService()

    greeting_response = await voice_greeting_service.generate_greeting(
        user_data={"user_name": "John Doe", "phone": "+233241234567"},
        event_data={"event_name": "IMPACT 2025"},
        config=voice_config,
        user_id=user_id
    )

    if greeting_response:
        # greeting_response.audio_url contains the audio file URL
        # greeting_response.text contains the personalized text
        # greeting_response.provider_used shows which provider was used
```

---

## Monitoring & Health Checks

### Health Endpoint Standard

All providers expose a `/health` endpoint:

**Request:**
```bash
curl https://coqui.ailabsafrica.com/health
```

**Response Format:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "device": "cuda",
  "gpu_memory_allocated": "2.1 GB",
  "gpu_memory_total": "20.0 GB"
}
```

### Automated Health Monitoring

**HealthMonitor Service:**
```python
# apps/shared/integration/ai_services/health_monitor.py

from apps.shared.integration.ai_services import HealthMonitor

monitor = HealthMonitor()

provider_urls = {
    "coqui_xtts": "https://coqui.ailabsafrica.com",
    "melotts": "https://melotts.ailabsafrica.com",
    # ... other providers
}

await monitor.start_monitoring(provider_urls, interval_seconds=60)

# Get current health status
health = await monitor.get_provider_health("coqui_xtts")
print(f"Coqui XTTS: {health.status}")
```

### Metrics to Monitor

1. **Availability**
   - Health endpoint response time
   - HTTP status codes
   - Service uptime percentage

2. **Performance**
   - Synthesis request latency
   - Queue depth
   - Throughput (requests/second)

3. **Resources**
   - GPU memory utilization
   - CPU usage
   - Disk space (for audio file storage)

4. **Errors**
   - Failed synthesis attempts
   - Timeout errors
   - Model loading failures

---

## Scaling & Resource Management

### GPU Allocation Strategy

**Local Server (20GB VRAM):**
- Lightweight providers (MeloTTS, OpenVoice, Kokoro): ~3-4GB total
- Medium provider (Coqui XTTS): ~2GB
- **Total: ~5-6GB used, ~14GB available for scaling**

**RunPod A40 (46GB VRAM):**
- F5-TTS: ~0.7GB
- StyleTTS2: ~0.7GB
- **Total: ~1.4GB used, ~44.5GB available**

### Scaling Considerations

**Horizontal Scaling:**
- Deploy additional Docker containers on same server
- Nginx load balancing across multiple instances
- Limited by GPU memory on single server

**Vertical Scaling:**
- Upgrade GPU on local server (20GB → 40GB+ VRAM)
- Add additional GPUs
- Use GPU partitioning (MIG for NVIDIA A100)

**Cloud Scaling:**
- Deploy more RunPod instances for heavy providers
- Use spot instances for cost optimization
- Auto-scaling based on queue depth

### Current Capacity

**Estimated Concurrent Synthesis Capacity:**
- Coqui XTTS: ~10 concurrent requests
- MeloTTS: ~20 concurrent (faster synthesis)
- OpenVoice: ~15 concurrent
- Kokoro: ~25 concurrent
- F5-TTS: ~5 concurrent (higher quality, slower)
- StyleTTS2: ~5 concurrent (expressive, slower)

**Total Capacity:** ~80 concurrent synthesis requests across all providers

---

## Security & Access Control

### Authentication

**API Keys:**
- Providers do not currently require API keys for internal access
- Access control enforced at Nginx level via IP whitelisting (if configured)
- Applications use internal service-to-service authentication

**JWT Tokens:**
- Frontend applications use JWT tokens from Supabase
- Backend services validate tokens before calling TTS providers
- User-specific billing tracked via user_id from token

### SSL/TLS

**Certificate Management:**
```bash
# Let's Encrypt certificates
sudo certbot certonly --nginx -d coqui.ailabsafrica.com
sudo certbot certonly --nginx -d melotts.ailabsafrica.com
# etc.

# Auto-renewal
sudo certbot renew --dry-run
```

**Certificate Expiration Monitoring:**
- Certificates expire every 90 days
- Auto-renewal configured via cron job
- Alert if renewal fails

### CORS Configuration

**Allowed Origins:**
- `https://flow.ailabsafrica.com`
- `https://churchflow.ailabsafrica.com`
- `https://studyflow.ailabsafrica.com`
- `https://inkwave.ailabsafrica.com`
- `https://eventflow.ailabsafrica.com`
- `https://kasaai.ailabsafrica.com`
- Development: `http://localhost:*`

### Data Privacy

**Audio File Storage:**
- Generated audio files stored locally on server
- Temporary files deleted after 24 hours
- User data (reference audio) stored securely with access controls

**Logging:**
- Request logging at Nginx level (access logs)
- Error logging for debugging
- PII (personally identifiable information) not logged

---

## Development vs Production

### Development Server (85.214.12.174)

**Purpose:** Testing, development, staging

**Configuration:**
- Same Docker images as production
- No public DNS (access via localhost only)
- Used for integration testing
- Lower resource allocation

**Running Services:**
- Coqui XTTS (port 8005)
- MeloTTS (port 8001)
- OpenVoice (port 8003)
- Kokoro TTS (port 8010)

**Testing:**
```bash
# Test local services on dev server
curl http://localhost:8005/health

# Test without HTTPS
curl -X POST http://localhost:8005/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Test synthesis", "language": "en"}'
```

### Production Server (148.251.0.46)

**Purpose:** Live production traffic

**Configuration:**
- Public HTTPS endpoints
- SSL certificates
- Production-grade monitoring
- Full resource allocation

**Access:**
```bash
# Test production services
curl https://coqui.ailabsafrica.com/health

# Production synthesis (requires authentication)
curl -X POST https://coqui.ailabsafrica.com/synthesize \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{"text": "Production synthesis", "language": "en"}'
```

### Environment Variables

**Production `.env`:**
```bash
COQUI_ENDPOINT=https://coqui.ailabsafrica.com
MELOTTS_ENDPOINT=https://melotts.ailabsafrica.com
OPENVOICE_ENDPOINT=https://openvoice.ailabsafrica.com
KOKORO_ENDPOINT=https://kokoro.ailabsafrica.com
F5TTS_ENDPOINT=https://f5tts.ailabsafrica.com
STYLETTS_ENDPOINT=https://styletts.ailabsafrica.com
MOSHI_ENDPOINT=http://localhost:8011
AKAN_MMS_ENDPOINT=https://flow-api.ailabsafrica.com/api/voice-lab
TTSWEBUI_WEBUI_ENDPOINT=https://tts-webui.ailabsafrica.com
TTSWEBUI_API_ENDPOINT=https://tts-webui.ailabsafrica.com/api
```

**Development `.env`:**
```bash
COQUI_ENDPOINT=http://localhost:8005
MELOTTS_ENDPOINT=http://localhost:8001
OPENVOICE_ENDPOINT=http://localhost:8003
KOKORO_ENDPOINT=http://localhost:8010
F5TTS_ENDPOINT=http://localhost:8002
STYLETTS_ENDPOINT=http://localhost:8004
MOSHI_ENDPOINT=http://localhost:8011
AKAN_MMS_ENDPOINT=http://localhost:8012
TTSWEBUI_WEBUI_ENDPOINT=http://localhost:3000
TTSWEBUI_API_ENDPOINT=http://localhost:7778
```

---

## Troubleshooting

### Common Issues & Solutions

#### Issue: Provider Returns 502 Bad Gateway

**Symptoms:**
```bash
curl https://melotts.ailabsafrica.com/health
# Output: <html><body>502 Bad Gateway</body></html>
```

**Diagnosis:**
```bash
# Check if Docker container is running
docker ps | grep melotts
# No output = container stopped

# Check Nginx logs
sudo tail -f /var/log/nginx/melotts.error.log
```

**Solution:**
```bash
# Restart Docker container
docker start melotts

# Wait for initialization
sleep 10

# Verify
curl https://melotts.ailabsafrica.com/health
# Should return: {"status":"healthy",...}
```

---

#### Issue: GPU Out of Memory

**Symptoms:**
```bash
# Health endpoint returns error
{"status":"error","message":"CUDA out of memory"}
```

**Diagnosis:**
```bash
# Check GPU memory usage
nvidia-smi

# Check which containers are using GPU
docker ps --format "{{.Names}}" | xargs -I {} sh -c 'echo {}; docker exec {} nvidia-smi 2>/dev/null || echo "No GPU access"'
```

**Solution:**
```bash
# Option 1: Restart specific service
docker restart <high-memory-service>

# Option 2: Stop non-essential services
docker stop moshi  # If not needed

# Option 3: Reduce concurrent requests
# Edit docker-compose.yml to limit replicas
```

---

#### Issue: Synthesis Timeout

**Symptoms:**
- Request takes >30 seconds
- No response returned

**Diagnosis:**
```bash
# Check service logs
docker logs coqui --tail 50

# Check Nginx timeout settings
grep timeout /etc/nginx/sites-available/coqui.ailabsafrica.com.conf
```

**Solution:**
```bash
# Increase Nginx timeout (if needed)
sudo nano /etc/nginx/sites-available/coqui.ailabsafrica.com.conf
# Update: proxy_read_timeout 300s;

# Reload Nginx
sudo systemctl reload nginx

# Or optimize synthesis request (reduce text length, use faster provider)
```

---

#### Issue: RunPod Service Unreachable

**Symptoms:**
- F5-TTS or StyleTTS2 returns timeout
- Connection refused

**Diagnosis:**
```bash
# SSH to RunPod
ssh root@194.68.245.121 -p 22130

# Check services
docker ps
nvidia-smi

# Check port listening
netstat -tuln | grep -E "(8002|8004)"
```

**Solution:**
```bash
# On RunPod instance
cd /workspace/tts-deployment
docker-compose up -d

# Verify health
curl http://localhost:8002/health
curl http://localhost:8004/health

# Check SSH tunnel on production server
# (Implementation depends on tunneling method used)
```

---

#### Issue: Voice Cloning Fails

**Symptoms:**
- Synthesis succeeds but doesn't match reference voice
- "Invalid reference audio" error

**Diagnosis:**
```bash
# Check reference audio file format
file /opt/kasaai/apps/voice-lab/voices/nana_aba.wav
# Should be: WAVE audio, 16 bit, mono or stereo

# Check file size
ls -lh /opt/kasaai/apps/voice-lab/voices/
# Should be: 5-30 seconds of audio (~500KB-3MB)
```

**Solution:**
```bash
# Convert audio to correct format if needed
ffmpeg -i input.mp3 -ar 22050 -ac 1 -sample_fmt s16 output.wav

# Ensure reference audio is base64 encoded for API
base64 -w 0 /opt/kasaai/apps/voice-lab/voices/nana_aba.wav

# Test with different provider (F5-TTS vs StyleTTS2)
```

---

### Health Check Commands

**Quick Health Check (All Providers):**
```bash
#!/bin/bash
# /opt/kasaai/apps/tts-deployment/scripts/health_check.sh

echo "=== TTS Provider Health Check ==="
echo ""

providers=(
  "https://coqui.ailabsafrica.com/health:Coqui XTTS"
  "https://melotts.ailabsafrica.com/health:MeloTTS"
  "https://openvoice.ailabsafrica.com/health:OpenVoice"
  "https://kokoro.ailabsafrica.com/health:Kokoro TTS"
  "https://f5tts.ailabsafrica.com/health:F5-TTS"
  "https://styletts.ailabsafrica.com/health:StyleTTS2"
  "https://tts-webui.ailabsafrica.com/health:TTS-WebUI"
)

for provider in "${providers[@]}"; do
  IFS=':' read -r url name <<< "$provider"
  response=$(curl -s -w "\n%{http_code}" --max-time 5 "$url" 2>/dev/null)
  http_code=$(echo "$response" | tail -n1)
  body=$(echo "$response" | sed '$d')

  if [ "$http_code" = "200" ]; then
    status=$(echo "$body" | jq -r '.status // "unknown"')
    echo "✅ $name: $status"
  else
    echo "❌ $name: HTTP $http_code (offline)"
  fi
done
```

---

## Best Practices

### Provider Selection

1. **For Multilingual Content:** Use Coqui XTTS (17 languages) or TTS-WebUI with appropriate model
2. **For Speed:** Use MeloTTS (fast synthesis) or TTS-WebUI Kokoro
3. **For Voice Cloning:** Use F5-TTS, StyleTTS2, or TTS-WebUI (multiple models available)
4. **For Emotion:** Use OpenVoice, StyleTTS2, or TTS-WebUI StyleTTS2/OpenVoice
5. **For Ghanaian Languages:** Use AKAN MMS
6. **For Real-time Conversation:** Use Moshi (if running)
7. **For Multi-Model Access:** Use TTS-WebUI (20+ models in one platform)
8. **For Research/Experimentation:** Use TTS-WebUI (extension manager for easy model testing)

### Audio File Management

**Storage Location:**
```bash
/opt/kasaai/apps/<app-name>/backend/storage/greetings/
/opt/kasaai/apps/<app-name>/backend/storage/tts_outputs/
```

**Cleanup Strategy:**
```bash
# Delete audio files older than 24 hours
find /opt/kasaai/apps/*/backend/storage/ -name "*.wav" -type f -mtime +1 -delete
find /opt/kasaai/apps/*/backend/storage/ -name "*.mp3" -type f -mtime +1 -delete
```

**Backup:**
```bash
# Backup important reference audio files
rsync -av /opt/kasaai/apps/voice-lab/voices/ /backup/voice-lab-voices/
```

### Performance Optimization

1. **Cache Common Phrases:** Store frequently used greetings
2. **Use Appropriate Provider:** Don't use F5-TTS for simple text
3. **Batch Requests:** Process multiple synthesis requests together
4. **Preload Models:** Keep containers running to avoid cold start
5. **Monitor GPU Memory:** Restart services if memory leaks occur

---

## Additional Resources

**Documentation:**
- [TTS Deployment Verification Report](/opt/kasaai/apps/tts-deployment/TTS_DEPLOYMENT_VERIFICATION_2025-11-03.md)
- [TTS Provider Service README](/opt/kasaai/apps/shared/services/README.md)
- [Voice Greeting Implementation](/opt/kasaai/apps/churchflow/VOICE_GREETING_CONFERENCE_CHECKIN.md)

**Code References:**
- Provider Registry: `/opt/kasaai/apps/shared/integration/ai_services/provider_registry.py`
- TTS Provider Service: `/opt/kasaai/apps/shared/services/tts_provider_service.py`
- Health Monitor: `/opt/kasaai/apps/shared/integration/ai_services/health_monitor.py`

**Deployment:**
- Local Docker Compose: `/opt/kasaai/apps/tts-deployment/docker-compose.local.yml`
- RunPod Docker Compose: `/opt/kasaai/apps/tts-deployment/docker-compose.runpod.yml`
- Nginx Configs: `/etc/nginx/sites-available/*tts*.conf`

---

**Document Maintained By:** AI Labs Africa Infrastructure Team
**Last Verification:** November 3, 2025
**Next Review:** December 1, 2025
