# Kyutai Moshi Deployment Status

**Date:** 2025-11-02 (Updated)
**Model:** Moshiko-7B (Language Model) + Moshika (Mimi Audio Codec)
**Status:** ✅ **SUCCESSFULLY DEPLOYED ON RUNPOD**

---

## 🎉 UPDATE: Successfully Deployed (Nov 2, 2025)

**RESOLVED:** Moshi is now fully operational on RunPod!
- ✅ Models loaded successfully (Moshi LM + Mimi codec)
- ✅ Using 15GB GPU memory on NVIDIA A40 (46GB total)
- ✅ Service running on port 8008
- ✅ WebSocket endpoint ready at /ws/conversation
- ✅ See [MOSHI_RUNPOD_DEPLOYMENT_SUCCESS.md](./MOSHI_RUNPOD_DEPLOYMENT_SUCCESS.md) for details

## 📋 Original Issue Summary (Oct 20, 2025)

Kyutai Moshi deployment was initially blocked on RunPod GPU instance (194.68.245.121) due to critical disk space limitation. The issue has been resolved with expanded storage.

---

## ✅ Completed Steps

### 1. Package Installation
- ✅ Installed `moshi` package (v0.2.11) via pip
- ✅ Installed PyTorch 2.5.1+cu121 with CUDA support
- ✅ Installed `fastapi`, `uvicorn`, `pydantic`, `websockets`
- ✅ All dependencies successfully installed

### 2. API Implementation
- ✅ Created FastAPI server (`/workspace/tts-deployment/kyutai/app.py`)
- ✅ Implemented model loading functions
- ✅ Added health check endpoint (`/health`)
- ✅ Added GPU stats endpoint (`/gpu_stats`)
- ✅ Added service info endpoint (`/`)
- ✅ Implemented WebSocket endpoint for real-time conversation (`/ws/conversation`)

### 3. Model Configuration
- ✅ Configured HuggingFace model loading:
  - Moshi LM: `kyutai/moshiko-pytorch-bf16` (Language Model ~15GB)
  - Mimi: `kyutai/moshika-pytorch-bf16` (Audio Codec ~3GB)
- ✅ GPU device detection and memory tracking
- ✅ Error handling and logging

---

## ❌ Deployment Blocker

### Issue: Container Filesystem Full

**Error Message:**
```
RuntimeError: Data processing error: CAS service error : IO Error: No space left on device (os error 28)
```

**Root Cause:**
- RunPod container overlay filesystem: **30GB / 30GB (100% full)**
- Existing HuggingFace cache in `/root/.cache/huggingface`: **27GB**
- Moshi models require an additional **15-20GB** for download
- Total needed: ~45-50GB, but container has only 30GB capacity

**Filesystem Breakdown:**
```
Filesystem                         Size  Used Avail Use% Mounted on
overlay                             30G   30G  1.6M 100% /        <-- FULL
mfs#eu-se-1.runpod.net:9421        546T  448T   98T  83% /workspace  <-- Has space but quota issues
```

**What's Using the Space:**
```
/root/.cache/huggingface:  27GB  (F5-TTS, StyleTTS2, Whisper models)
/workspace (attempted):    24GB  (Hit disk quota before completion)
/tmp:                      12MB
```

---

## 🔍 Attempted Solutions

### 1. Move HuggingFace Cache to /workspace ❌
- Set `HF_HOME=/workspace/.cache/huggingface`
- Set `TRANSFORMERS_CACHE=/workspace/.cache/huggingface/transformers`
- Set `HF_DATASETS_CACHE=/workspace/.cache/huggingface/datasets`
- **Result:** Hit disk quota on /workspace filesystem ("Disk quota exceeded - os error 122")

### 2. Use Default Cache (/root) ❌
- Attempted to use existing models in `/root/.cache/huggingface`
- **Result:** Container overlay filesystem is 100% full, no room for downloads

### 3. Copy App to Different Location ❌
- Tried creating venv in `/root/tts-deployment/moshi`
- **Result:** Same disk space issues

---

## 💡 Resolution Options

### Option A: New RunPod Instance (Recommended)
**Approach:** Deploy Moshi on a fresh RunPod pod with larger container storage

**Pros:**
- Clean slate deployment
- Can configure larger container overlay filesystem (50GB+)
- Dedicated GPU resources for Moshi
- No interference with F5-TTS/StyleTTS2

**Cons:**
- Additional RunPod costs
- Requires new SSH tunnel setup
- New SSL certificate configuration

**Estimated Cost:** ~$0.39/hour for NVIDIA A40 (48GB)

---

### Option B: Clean Up Existing RunPod ⚠️
**Approach:** Remove F5-TTS and StyleTTS2 models to make room

**Pros:**
- No additional costs
- Same infrastructure

**Cons:**
- Loses F5-TTS and StyleTTS2 (which are production-ready and working)
- Only frees up ~15-20GB (might not be enough)
- High risk - may break existing services

**Recommendation:** ❌ Not recommended

---

### Option C: RunPod Storage Reconfiguration 🔧
**Approach:** Request RunPod support to increase container storage or reconfigure storage allocation

**Pros:**
- Keeps all services on one instance
- No code changes needed

**Cons:**
- May not be possible without recreating pod
- Potential downtime for F5-TTS/StyleTTS2
- Unclear if RunPod allows this

**Recommendation:** 🤔 Worth investigating

---

### Option D: Skip Moshi for Now ✅
**Approach:** Proceed with F5-TTS and StyleTTS2 as production services

**Pros:**
- F5-TTS and StyleTTS2 fully operational (100% test pass rate)
- Complete voice cloning capabilities already available
- No additional costs or complexity
- Can deploy Moshi later if specifically needed

**Cons:**
- No real-time bidirectional conversation capability
- Moshi's unique features unavailable

**Recommendation:** ✅ **Recommended** - F5-TTS and StyleTTS2 provide comprehensive TTS coverage

---

## 📊 Moshi vs F5-TTS/StyleTTS2

| Feature | Moshi | F5-TTS | StyleTTS2 |
|---------|-------|--------|-----------|
| Voice Cloning | ❌ No | ✅ Yes | ✅ Yes |
| Real-time Conversation | ✅ Yes | ❌ No | ❌ No |
| Bidirectional Audio | ✅ Yes | ❌ No | ❌ No |
| Interrupt Handling | ✅ Yes | ❌ No | ❌ No |
| Multi-language | ✅ Limited | ✅ 4 languages | ❌ English only |
| Deployment Status | ⏸️ Blocked | ✅ Operational | ✅ Operational |
| GPU Memory | ~15-20GB | ~2.2GB | ~0.7-1.0GB |
| Use Case | Conversational AI | Voice Cloning TTS | Expressive TTS |

---

## 📁 Implementation Details

### File Locations

**RunPod (194.68.245.121:22048):**
```
/workspace/tts-deployment/kyutai/
├── app.py                    # Moshi FastAPI server (ready)
├── venv/                     # Python virtual environment
│   └── lib/python3.12/site-packages/
│       └── moshi/            # Moshi package installed
└── logs/
    └── moshi.log             # Server logs

/root/.cache/huggingface/hub/
└── models--kyutai--moshiko-pytorch-bf16/  # Partial download (incomplete)
```

### API Endpoints (If Deployed)

**Base URL:** https://kyutai.ailabsafrica.com (not configured yet)

**Endpoints:**
- `GET /` - Service information
- `GET /health` - Health check with model status
- `GET /gpu_stats` - GPU memory and utilization
- `WS /ws/conversation` - WebSocket for real-time bidirectional conversation

### Sample Usage (When Deployed)

**WebSocket Connection:**
```python
import asyncio
import websockets

async def conversation():
    uri = "wss://kyutai.ailabsafrica.com/ws/conversation"
    async with websockets.connect(uri) as websocket:
        # Send audio chunk
        await websocket.send(audio_bytes)

        # Receive response
        response = await websocket.recv()
```

---

## 🔧 Technical Details

### Models

**Moshiko (Language Model):**
- Repository: `kyutai/moshiko-pytorch-bf16`
- Size: ~15GB
- Format: SafeTensors (BF16 precision)
- Purpose: Language understanding and generation

**Moshika (Mimi Audio Codec):**
- Repository: `kyutai/moshika-pytorch-bf16`
- Size: ~3GB
- Format: SafeTensors
- Purpose: Audio encoding/decoding for real-time streaming

### GPU Requirements

- NVIDIA GPU with 20GB+ VRAM
- CUDA 12.1+ support
- BFloat16 precision support

### Dependencies

```txt
moshi==0.2.11
torch==2.5.1+cu121
torchaudio==2.5.1+cu121
fastapi
uvicorn
pydantic
websockets
huggingface-hub
```

---

## 📝 Next Steps

### If Proceeding with Moshi Deployment:

1. **Create New RunPod Instance:**
   ```bash
   # Request pod with:
   - GPU: NVIDIA A40 (48GB) or similar
   - Container Storage: 50GB+ (not default 30GB)
   - Network Storage: /workspace (default)
   ```

2. **Deploy Moshi:**
   ```bash
   # On new pod:
   cd /workspace && git clone <repo>
   cd tts-deployment/kyutai
   python3 -m venv venv
   source venv/bin/activate
   pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
   pip install moshi fastapi uvicorn pydantic websockets
   python app.py
   ```

3. **Configure SSH Tunnel:**
   ```bash
   # On local server (148.251.0.46):
   ssh -f -N -L 8008:localhost:8008 root@<new-runpod-ip>:<new-port>
   ```

4. **Configure Nginx:**
   ```nginx
   # /etc/nginx/sites-available/kyutai.ailabsafrica.com.conf
   server {
       listen 443 ssl http2;
       server_name kyutai.ailabsafrica.com;

       location / {
           proxy_pass http://localhost:8008;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
       }
   }
   ```

5. **Test Deployment:**
   ```bash
   curl https://kyutai.ailabsafrica.com/health
   ```

### If Skipping Moshi:

1. ✅ Mark Moshi as "Future Enhancement"
2. ✅ Update frontend TTS providers list (keep status as "building")
3. ✅ Focus on F5-TTS and StyleTTS2 optimization and usage
4. ✅ Revisit Moshi deployment if real-time conversation becomes a priority

---

## 🎯 Recommendation

**Decision: Skip Moshi Deployment for Now** ✅

**Rationale:**
1. F5-TTS and StyleTTS2 are **fully operational** with 100% test pass rate
2. Both provide **high-quality voice cloning** capabilities
3. Moshi requires **dedicated infrastructure** due to space constraints
4. Real-time bidirectional conversation is a **niche use case** for current requirements
5. Moshi can be deployed later on a **dedicated RunPod instance** if needed

**Current Production Services:**
- ✅ **F5-TTS:** https://f5tts.ailabsafrica.com (4 languages, flow-matching TTS)
- ✅ **StyleTTS2:** https://styletts.ailabsafrica.com (expressive, style transfer)

**Future Deployment:**
- ⏸️ **Moshi:** Can be deployed on new RunPod instance when conversational AI is needed

---

## 📚 References

- **Moshi GitHub:** https://github.com/kyutai-labs/moshi
- **Moshi HuggingFace (LM):** https://huggingface.co/kyutai/moshiko-pytorch-bf16
- **Moshi HuggingFace (Codec):** https://huggingface.co/kyutai/moshika-pytorch-bf16
- **Moshi Paper:** https://kyutai.org/Moshi.pdf
- **RunPod Docs:** https://docs.runpod.io/

---

**Deployment Attempted:** 2025-10-20
**Status:** Blocked by disk space
**Resolution:** Skip for now, deploy on dedicated instance if needed
**Impact:** Low - F5-TTS and StyleTTS2 provide complete voice cloning coverage

