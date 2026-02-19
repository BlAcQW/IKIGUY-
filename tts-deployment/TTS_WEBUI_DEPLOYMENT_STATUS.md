# TTS-WebUI Deployment - Final Step! 🚀

**Date:** November 8, 2025
**Status:** ✅ Almost Ready - One Manual Step Remaining
**Domain:** https://tts-webui.ailabsafrica.com
**Pod ID:** jzfmzviw26huka-644113c7

---

## ✅ Completed Deployment Steps

### 1. TTS-WebUI Installation ✅
- **Location:** `/workspace/tts-deployment/docker/tts-webui/`
- **Extensions Installed:**
  - StyleTTS2 0.1.8 + extension 0.1.0
  - RVC 0.3.6 + extension 0.0.5
  - Bark, Tortoise, Demucs, MMS, Vocos, and more

### 2. React UI Built ✅
- Production build complete (42 static pages)
- All TTS models ready
- Extension manager available in UI

### 3. Services Running on RunPod ✅
- ✅ React UI: Port 3000
- ✅ Gradio Backend: Port 7770
- ✅ Nginx Proxy: Port 8013 → 3000

### 4. Nginx & SSL Configured ✅
- ✅ RunPod nginx: Listening on 0.0.0.0:8013
- ✅ Local nginx: `/etc/nginx/sites-enabled/tts-webui.ailabsafrica.com.conf`
- ✅ SSL Certificate: Valid until February 6, 2026
- ✅ DNS: tts-webui.ailabsafrica.com → 148.251.0.46

---

## ⏰ ONE REMAINING STEP: Expose Port 8013 on RunPod

### Instructions:

1. Go to: **https://www.runpod.io/console/pods**
2. Find pod: **jzfmzviw26huka**
3. Click **"Edit Pod"** or **"Edit Template"**
4. Find field: **"Expose HTTP Ports (Max 10)"**
5. **Current value:** `8010,8011,8012`
6. **Update to:** `8010,8011,8012,8013`
7. Click **Save**
8. Wait 1-2 minutes for changes to apply

### Verification:
```bash
# Test RunPod proxy (after exposing port)
curl -I https://jzfmzviw26huka-8013.proxy.runpod.net

# Should return HTTP 200 and see the TTS-WebUI React app
```

---

## 🌐 Access URLs

### After Port 8013 is Exposed:

**Production URL (Recommended):**
```
https://tts-webui.ailabsafrica.com
```

**RunPod Direct URL:**
```
https://jzfmzviw26huka-8013.proxy.runpod.net
```

---

## 🎨 Installing GPT-SoVITS Extension

Once you can access the TTS-WebUI:

1. Open **https://tts-webui.ailabsafrica.com**
2. Navigate to **Extensions** or **Tools** section
3. Find **GPT-SoVITS** in the extension manager
4. Click **Install**
5. Restart TTS-WebUI server after installation:
   ```bash
   ssh -p 22153 root@194.68.245.121
   pkill -f "python3 server.py"
   cd /workspace/tts-deployment/docker/tts-webui
   source venv/bin/activate
   nohup python3 server.py --docker > /tmp/tts-webui.log 2>&1 &
   ```

---

## 📊 Available TTS Models

### Currently Installed:
- **StyleTTS2** ✅ - High-quality voice cloning
- **RVC** ✅ - Voice conversion
- **Bark** ✅ - Multi-lingual, music, effects
- **Tortoise** ✅ - High-quality synthesis
- **MMS** ✅ - Meta's multilingual model
- **Demucs** ✅ - Audio separation
- **Vocos** ✅ - Neural vocoder

### Available to Install (via Extension Manager):
- **GPT-SoVITS** - High-quality voice cloning
- F5-TTS, XTTS v2, Parler TTS
- Kokoro TTS, MahaTTS, Valle-X
- Whisper, MusicGen, Stable Audio
- And many more...

---

## 🔧 Service Management

### Check Status on RunPod:
```bash
ssh -p 22153 root@194.68.245.121

# Check TTS-WebUI processes
ps aux | grep -E "(next start|python3 server.py)"

# Check ports
ss -tlnp | grep -E ':(3000|7770|8013)'

# View logs
tail -f /tmp/tts-webui.log
```

### Restart TTS-WebUI:
```bash
pkill -f "python3 server.py"
cd /workspace/tts-deployment/docker/tts-webui
source venv/bin/activate
nohup python3 server.py --docker > /tmp/tts-webui.log 2>&1 &
```

### Restart RunPod Nginx:
```bash
nginx -s reload
```

---

## 📋 Architecture

```
User Browser
    ↓
https://tts-webui.ailabsafrica.com
    ↓
Local Nginx (148.251.0.46) + SSL
    ↓
RunPod Proxy (jzfmzviw26huka-8013.proxy.runpod.net)
    ↓
RunPod Nginx (port 8013)
    ↓
TTS-WebUI React UI (port 3000)
    ├── Gradio Backend (port 7770)
    └── Extension Manager
```

---

## 🔌 API Access (Optional)

TTS-WebUI includes an OpenAI-compatible API on port 7778.

**To enable API access:**
1. Expose port 7778 on RunPod (add to HTTP ports list)
2. Update nginx to proxy API requests
3. Access at: `https://tts-webui-api.ailabsafrica.com/v1/audio/speech`

---

## 📦 Resource Usage

### RunPod (NVIDIA A40 - 44 GB VRAM)
- F5-TTS: ~4 GB
- StyleTTS2: ~2-4 GB
- Moshi: ~10 GB
- **Available for TTS-WebUI**: ~24-28 GB ✅

### Disk Space
- TTS-WebUI: ~15 GB
- With GPT-SoVITS: ~18-20 GB

---

## ✅ Quick Checklist

- [x] Install TTS-WebUI on RunPod
- [x] Install StyleTTS2 and RVC extensions
- [x] Build React UI
- [x] Start TTS-WebUI server
- [x] Configure RunPod nginx (port 8013)
- [x] Configure local nginx (tts-webui.ailabsafrica.com)
- [x] Get SSL certificate
- [ ] **Expose port 8013 on RunPod dashboard** ← DO THIS NOW
- [ ] Test: https://tts-webui.ailabsafrica.com
- [ ] Install GPT-SoVITS extension via WebUI
- [ ] Test voice generation

---

## 🎯 Next Steps

1. **Expose port 8013** on RunPod dashboard (see instructions above)
2. **Access TTS-WebUI**: https://tts-webui.ailabsafrica.com
3. **Install GPT-SoVITS**: Use the built-in extension manager
4. **Test TTS models**: Try StyleTTS2, RVC, and GPT-SoVITS
5. **Explore features**: Voice cloning, conversion, audio tools

---

**Almost there! Just expose port 8013 and you're ready to go! 🚀**

**Last Updated:** November 8, 2025, 15:15 UTC
