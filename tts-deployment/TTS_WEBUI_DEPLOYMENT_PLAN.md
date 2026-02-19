# TTS-WebUI Deployment Plan

**Date:** November 8, 2025
**Target:** styletts-ui.ailabsafrica.com
**RunPod Port:** 3000 (React UI) and 7770 (Gradio backend)

---

## What is TTS-WebUI?

**Comprehensive TTS Platform** - Single interface for 20+ TTS models:

### Text-to-Speech Models:
- ✅ **StyleTTS2** - High-quality expressive TTS with voice cloning
- Bark - Multi-lingual, music, sound effects
- Tortoise - High-quality, slow
- XTTS v2 - Multilingual voice cloning
- F5-TTS - Fast, expressive
- OpenVoice - Voice cloning
- Parler TTS - Controllable TTS
- Kokoro TTS - Japanese TTS
- MahaTTS, MMS, VALL-E X, SeamlessM4T, and more

### Audio Tools:
- RVC - Voice conversion
- Demucs - Audio separation
- Whisper - Speech recognition
- MusicGen/AudioCraft - Music generation
- Stable Audio - Audio generation

---

## Architecture

```
User Browser
    ↓
https://styletts-ui.ailabsafrica.com (Nginx + SSL)
    ↓
RunPod Proxy (jzfmzviw26huka-8015.proxy.runpod.net)
    ↓
TTS-WebUI on RunPod
    ├── Port 3000 → React UI (Modern web interface)
    ├── Port 7770 → Gradio Backend (API + Gradio UI)
    └── Models stored in /workspace/tts-deployment/docker/tts-webui/data/
```

---

## Installation Status

### ⏳ Current Step: Installing Dependencies

**Location:** `/workspace/tts-deployment/docker/tts-webui/`

**Installing:**
```bash
# Virtual environment created
python3 -m venv venv

# Installing requirements.txt:
- tts_webui_core
- gradio==5.49.1
- torch (PyTorch with CUDA support)
- accelerate
- safetensors
- Many TTS model extensions
```

**Installation Size:**
- Base: ~10.7 GB
- Each model: 2-8 GB additional
- Total (with StyleTTS2): ~15-20 GB

**Estimated Time:** 5-10 minutes

---

## Port Allocation

| Service | Port | Purpose | RunPod Proxy |
|---------|------|---------|--------------|
| **React UI** | 3000 | Modern web interface | Port 8015 (TBD) |
| **Gradio Backend** | 7770 | API + Gradio interface | Port 8016 (TBD) |

**Note:** We need to expose both ports through RunPod proxy or choose one interface.

---

## Deployment Steps

### 1. ✅ Clone Repository
```bash
cd /workspace/tts-deployment/docker
git clone https://github.com/rsxdalv/TTS-WebUI.git tts-webui
```

### 2. ⏳ Install Dependencies (In Progress)
```bash
cd tts-webui
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. ⏸️ Install StyleTTS2 Extension
```bash
pip install tts-webui-extension.styletts2>=0.1.0 \
    --extra-index-url https://tts-webui.github.io/extensions-index/
```

### 4. ⏸️ Start Server
```bash
# Option A: React UI (Port 3000) - Recommended
cd react-ui && npm install && npm run build
cd .. && python3 server.py --docker

# Option B: Gradio only (Port 7770)
python3 server.py --docker --gradio-only

# Background service
nohup python3 server.py --docker > /tmp/tts-webui.log 2>&1 &
```

### 5. ⏸️ Configure Nginx & SSL
```bash
# On local server (148.251.0.46)
sudo cp /tmp/styletts-ui.ailabsafrica.com.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/styletts-ui.ailabsafrica.com.conf \
    /etc/nginx/sites-enabled/

# Get SSL certificate
sudo certbot --nginx -d styletts-ui.ailabsafrica.com

# Test and reload
sudo nginx -t
sudo systemctl reload nginx
```

### 6. ⏸️ Test
```bash
# Check health
curl https://styletts-ui.ailabsafrica.com

# Access UI
open https://styletts-ui.ailabsafrica.com
```

---

## Configuration

### Environment Variables

Create `.env` file in `/workspace/tts-deployment/docker/tts-webui/`:

```bash
# Ports
TTS_PORT=7770
UI_PORT=3000
OPENAI_API_PORT=7778

# GPU
CUDA_VISIBLE_DEVICES=0

# Models (optional - downloads on demand)
# STYLETTS2_MODEL_PATH=/workspace/tts-deployment/docker/tts-webui/data/models/styletts2/
```

### Gradio Options

Edit `tts_webui/config/config.json`:

```json
{
  "gradio_interface_options": {
    "server_name": "0.0.0.0",
    "server_port": 7770,
    "share": false,
    "auth": null
  }
}
```

---

## Using StyleTTS2 in TTS-WebUI

Once deployed:

1. **Open UI:** https://styletts-ui.ailabsafrica.com
2. **Select Model:** Choose "StyleTTS2" from model dropdown
3. **Generate Speech:**
   - Enter text
   - Adjust alpha (timbre) and beta (prosody)
   - Click "Generate"
4. **Voice Cloning:**
   - Upload reference audio
   - Enter text
   - Generate with cloned voice

---

## Advantages of TTS-WebUI

### vs Our Custom StyleTTS2-UI:

| Feature | TTS-WebUI | Custom UI |
|---------|-----------|-----------|
| **Models** | 20+ models | StyleTTS2 only |
| **Interface** | React + Gradio | Gradio only |
| **Size** | 10-20 GB | <100 MB |
| **Setup** | Complex | Simple |
| **Maintenance** | Active community | We maintain |
| **Integration** | Standalone | Connects to our API |
| **Features** | Extensive | Focused |

### Pros:
- ✅ Multiple TTS models in one interface
- ✅ Modern React UI + Gradio fallback
- ✅ Active development and community
- ✅ Voice conversion, audio tools
- ✅ Extension ecosystem

### Cons:
- ❌ Heavy installation (10-20 GB)
- ❌ Complex setup
- ❌ Runs models internally (doesn't use our StyleTTS2 API)
- ❌ Higher GPU memory usage
- ❌ More dependencies to maintain

---

## Resource Requirements

### Disk Space:
- Base installation: 10.7 GB
- StyleTTS2 model: 3-5 GB
- Additional models (optional): 2-8 GB each
- **Total:** ~15-20 GB minimum

### GPU Memory:
- StyleTTS2: ~2-4 GB VRAM
- Multiple models loaded: 10-20 GB VRAM
- **Available:** 44.43 GB on NVIDIA A40 ✅

### CPU/RAM:
- RAM: 8-16 GB recommended
- CPU: Multi-core for React build

---

## Comparison with Current Setup

### Current Architecture:
```
StyleTTS2 API (port 8006) → Swagger UI
    - Lightweight
    - API-focused
    - No separate UI needed
```

### With TTS-WebUI:
```
TTS-WebUI (ports 3000/7770)
    - Standalone TTS platform
    - Doesn't use our StyleTTS2 API
    - Runs models internally
    - Full-featured UI
```

### Conflict/Duplication:
- ⚠️ **TTS-WebUI will run its own StyleTTS2 instance**
- ⚠️ **Won't use our existing API at port 8006**
- ⚠️ **Duplicate model loading (~4-6 GB VRAM)**

### Recommendation:
**Option A:** Use TTS-WebUI and deprecate standalone StyleTTS2 API
**Option B:** Keep both - TTS-WebUI for UI, StyleTTS2 API for programmatic access
**Option C:** Use our custom lightweight UI that connects to existing API

---

## Migration Path

If choosing TTS-WebUI:

1. ✅ Install TTS-WebUI on RunPod
2. ✅ Configure StyleTTS2 extension
3. ⚠️ Decide on standalone StyleTTS2 API:
   - Keep running (for API access)
   - OR stop to free VRAM
4. ✅ Update frontend to point to TTS-WebUI
5. ✅ Configure nginx for styletts-ui.ailabsafrica.com

---

## Next Steps (After Installation Completes)

1. ⏳ Wait for `pip install -r requirements.txt` to complete (~5 min)
2. ⏸️ Install StyleTTS2 extension
3. ⏸️ Build React UI (or use Gradio)
4. ⏸️ Start server on port 3000/7770
5. ⏸️ Obtain SSL certificate
6. ⏸️ Configure nginx proxy
7. ⏸️ Test StyleTTS2 in UI
8. ⏸️ Document usage

---

## Questions to Answer

1. **Interface Choice:**
   - React UI (port 3000) - Modern, fast
   - Gradio UI (port 7770) - Simple, auto-generated
   - Both (expose both ports)

2. **Existing StyleTTS2 API:**
   - Keep running (dual access)
   - Stop to save VRAM (~4-6 GB)

3. **Models to Enable:**
   - StyleTTS2 only
   - StyleTTS2 + F5-TTS + others?

4. **Frontend Integration:**
   - Update b2c-portal to use TTS-WebUI API
   - Keep using standalone APIs

---

**Current Status:** Installing dependencies on RunPod
**ETA to completion:** 5-10 minutes for full setup
**Ready for:** Configuration decisions

---

**Last Updated:** November 8, 2025, 3:35 PM
**Installation ID:** 97eca4 (background process)
