# TTS-WebUI Deployment Guide - Almost Complete! ✅

**Date:** November 8, 2025
**Status:** Awaiting DNS and RunPod Port Exposure
**Pod ID:** jzfmzviw26huka-644113c7

## 🎉 Deployment Progress

### ✅ Completed Steps

1. **TTS-WebUI Installation** - Fully installed on RunPod
   - Location: `/workspace/tts-deployment/docker/tts-webui/`
   - Python venv created with all dependencies
   - Extensions installed: StyleTTS2 0.1.0, RVC 0.0.5

2. **React UI Built** - Production build complete
   - Next.js build successful
   - All 42 static pages generated
   - Supports 20+ TTS models

3. **Services Running on RunPod**
   - ✅ React UI: Port 3000 (Next.js frontend)
   - ✅ Gradio Backend: Port 7770 (Python API)
   - ✅ Nginx Proxy: Port 8013 → 3000 (RunPod internal)

4. **Nginx Configuration**
   - ✅ RunPod nginx: Listening on 0.0.0.0:8013
   - ✅ Local nginx config: Prepared at `/tmp/styletts-ui.ailabsafrica.com.conf`

---

## ⏳ Remaining Manual Steps

### Step 1: Add DNS A Record

**Domain:** styletts-ui.ailabsafrica.com
**Type:** A
**Value:** 148.251.0.46
**TTL:** 3600 (or default)

Go to your DNS provider (same place where you configured f5tts-ui.ailabsafrica.com) and add this record.

**Verification:**
```bash
nslookup styletts-ui.ailabsafrica.com
# Should return: 148.251.0.46
```

---

### Step 2: Expose Port 8013 on RunPod

1. Go to: https://www.runpod.io/console/pods
2. Find pod: **jzfmzviw26huka**
3. Click **"Edit Pod"**
4. Find field: **"Expose HTTP Ports (Max 10)"**
5. **Current:** `8010,8011,8012` (F5-TTS, F5-TTS UI, Moshi)
6. **Update to:** `8010,8011,8012,8013`
7. Click **Save**
8. Wait 1-2 minutes for proxy to update

**Verification:**
```bash
curl -I https://jzfmzviw26huka-8013.proxy.runpod.net
# Should return HTTP 200 or see the React UI
```

---

### Step 3: Get SSL Certificate (After DNS Propagates)

Once DNS propagates (5-15 minutes), run:

```bash
# Install the full nginx config with SSL
sudo cp /tmp/styletts-ui.ailabsafrica.com.conf /etc/nginx/sites-available/
sudo ln -sf /etc/nginx/sites-available/styletts-ui.ailabsafrica.com.conf /etc/nginx/sites-enabled/

# Get SSL certificate
sudo certbot --nginx -d styletts-ui.ailabsafrica.com --non-interactive --agree-tos --email admin@ailabsafrica.com

# Reload nginx
sudo systemctl reload nginx
```

---

## 🌐 URLs After Completion

### Production URLs (SSL Enabled)
- **TTS-WebUI:** https://styletts-ui.ailabsafrica.com

### RunPod Direct URL
- **TTS-WebUI:** https://jzfmzviw26huka-8013.proxy.runpod.net

---

## 📋 Architecture

```
User Browser
    ↓
https://styletts-ui.ailabsafrica.com (nginx + SSL on 148.251.0.46)
    ↓
RunPod Proxy (jzfmzviw26huka-8013.proxy.runpod.net)
    ↓
RunPod Nginx (port 8013)
    ↓
TTS-WebUI React UI (port 3000)
    └── Gradio Backend (port 7770)
```

---

## 🎯 Available TTS Models

TTS-WebUI includes these models (extensions installed):

### Text-to-Speech
- **StyleTTS2** ✅ - High-quality expressive TTS with voice cloning
- **Bark** ✅ - Multi-lingual, music, sound effects
- **Tortoise** ✅ - High-quality, slow generation
- **MMS** ✅ - Multilingual model from Meta
- MahaTTS, Kokoro, Valle-X, Chatterbox

### Audio Tools
- **RVC** ✅ - Retrieval-based Voice Conversion
- **Demucs** ✅ - Audio source separation
- **Vocos** ✅ - Neural vocoder

### Music Generation
- MusicGen, Stable Audio, ACE, Magnet

---

## 🔧 Service Management

### On RunPod (SSH: `ssh root@194.68.245.121 -p 22153`)

**Check TTS-WebUI status:**
```bash
# Check if React UI is running
ps aux | grep "next start"

# Check if Gradio backend is running
ps aux | grep "python3 server.py"

# Check ports
ss -tlnp | grep -E ':(3000|7770|8013)'
```

**View logs:**
```bash
tail -f /tmp/tts-webui.log
```

**Restart TTS-WebUI:**
```bash
pkill -f "python3 server.py"
cd /workspace/tts-deployment/docker/tts-webui
source venv/bin/activate
nohup python3 server.py --docker > /tmp/tts-webui.log 2>&1 &
```

**Restart nginx:**
```bash
nginx -s reload
```

---

## 🔌 API Access

TTS-WebUI includes an OpenAI-compatible API:

**Endpoint:** Port 7778 (needs to be exposed separately if needed)
**Documentation:** http://localhost:7778/docs (when exposed)

The OpenAI TTS API extension is already installed (`tts_webui_extension.openai_tts_api-0.16.0`).

---

## 📊 Resource Usage

### Disk Space
- TTS-WebUI: ~15 GB (base + StyleTTS2 + RVC)
- React UI build: ~2 GB

### GPU Memory (NVIDIA A40 - 44 GB VRAM)
- F5-TTS: ~4 GB
- StyleTTS2: ~2-4 GB
- Moshi: ~10 GB
- **Available for TTS-WebUI**: ~24-28 GB ✅

### Current RunPod Services
- Port 8010: F5-TTS API
- Port 8011: F5-TTS Gradio UI
- Port 8012: Moshi/Kyutai
- **Port 8013: TTS-WebUI** (to be exposed)

---

## 🐛 Troubleshooting

### React UI not loading
```bash
ssh -p 22153 root@194.68.245.121
cd /workspace/tts-deployment/docker/tts-webui/react-ui
npm run build  # Rebuild if needed
```

### Port 8013 not accessible
```bash
# On RunPod
ss -tlnp | grep 8013  # Should show nginx listening

# Check nginx config
nginx -t
nginx -s reload
```

### Gradio backend issues
```bash
# Check Python process
ps aux | grep server.py

# Check logs
tail -100 /tmp/tts-webui.log
```

---

## ✅ Quick Completion Checklist

- [ ] Add DNS A record: styletts-ui.ailabsafrica.com → 148.251.0.46
- [ ] Wait 5-15 minutes for DNS propagation
- [ ] Expose port 8013 on RunPod dashboard
- [ ] Verify RunPod proxy works: `curl https://jzfmzviw26huka-8013.proxy.runpod.net`
- [ ] Install final nginx config with SSL
- [ ] Get SSL certificate with certbot
- [ ] Test: https://styletts-ui.ailabsafrica.com
- [ ] Test StyleTTS2 voice generation
- [ ] Test RVC voice conversion

---

## 🎨 TTS-WebUI Features

Once deployed, you can:

1. **Generate Speech**
   - Select from 20+ TTS models
   - Adjust voice parameters
   - Download audio files

2. **Voice Cloning (StyleTTS2)**
   - Upload reference audio
   - Clone voices with high quality
   - Adjust timbre and prosody

3. **Voice Conversion (RVC)**
   - Transform voices between speakers
   - Real-time voice changing
   - Multi-format support

4. **Audio Tools**
   - Separate audio sources (Demucs)
   - Generate music (MusicGen)
   - Enhance audio quality

---

**Next:** Complete the 2 manual steps above, then enjoy your comprehensive TTS platform! 🚀

**Last Updated:** November 8, 2025, 15:10 UTC
