# F5-TTS RunPod Deployment - Complete ✅

**Date:** 2025-11-08  
**Status:** Production Ready  
**Pod ID:** jzfmzviw26huka-644113c7

## 🎉 Deployment Summary

Successfully deployed F5-TTS API and Gradio UI on RunPod with public access via nginx reverse proxy and RunPod's HTTP proxy service.

## 🌐 Public URLs

### Your Domains (SSL Enabled)
- **F5-TTS API:** https://f5tts.ailabsafrica.com
- **F5-TTS Gradio UI:** https://f5tts-ui.ailabsafrica.com

### RunPod Direct URLs
- **API:** https://jzfmzviw26huka-8010.proxy.runpod.net
- **Gradio UI:** https://jzfmzviw26huka-8011.proxy.runpod.net

## 📋 Architecture

```
User Request
    ↓
Your Domain (SSL termination on your server 148.251.0.46)
    ↓
Your Nginx (proxy to RunPod)
    ↓
RunPod Proxy (jzfmzviw26huka-8010.proxy.runpod.net)
    ↓
RunPod Nginx (port 8010/8011)
    ↓
F5-TTS Service (port 8002/8003)
```

## 🔧 RunPod Configuration

### SSH Access
```bash
ssh root@194.68.245.121 -p 22153 -i ~/.ssh/id_ed25519
```

### Services Running
- **F5-TTS FastAPI:** Port 8002 → Exposed via nginx on port 8010
- **F5-TTS Gradio UI:** Port 8003 → Exposed via nginx on port 8011

### HTTP Ports Exposed on RunPod Dashboard
- Port 8010 ✅ (F5-TTS API)
- Port 8011 ✅ (F5-TTS Gradio UI)
- Port 8012 ✅ (Reserved for Moshi)
- Ports 8013-8017, 8019 ✅ (Available for other services)

### Nginx Configuration on RunPod
Location: `/etc/nginx/nginx.conf`  
Listens on: `0.0.0.0:8010`, `0.0.0.0:8011`

## 🚀 Starting Services on RunPod

**Automatic Startup Script:**
```bash
/workspace/start_f5tts_services.sh
```

**Manual Start:**
```bash
# Start F5-TTS API
cd /workspace/tts-deployment/docker/f5tts
source /workspace/tts-venv/bin/activate
nohup python3 app.py > /tmp/f5tts_api.log 2>&1 &

# Start F5-TTS Gradio UI
cd /workspace
source /workspace/tts-venv/bin/activate
nohup f5-tts_infer-gradio --port 8003 --host 0.0.0.0 > /tmp/f5tts_gradio.log 2>&1 &
```

## 📊 Monitoring

**Check Services:**
```bash
# On RunPod
ss -tlnp | grep -E '8002|8003|8010|8011'

# Check logs
tail -f /tmp/f5tts_api.log
tail -f /tmp/f5tts_gradio.log
```

**Health Check:**
```bash
# API health
curl https://f5tts.ailabsafrica.com/health

# Expected response:
{
    "status": "healthy",
    "device": "cuda",
    "model_loaded": true,
    "gpu_name": "NVIDIA A40"
}
```

## 🔐 SSL Certificates

- **f5tts.ailabsafrica.com:** Valid until 2026-02-06
- **f5tts-ui.ailabsafrica.com:** Valid until 2026-02-06
- **Auto-renewal:** Configured via certbot

## 📁 File Locations

### On RunPod
- F5-TTS API: `/workspace/tts-deployment/docker/f5tts/app.py`
- Gradio UI: Via `f5-tts_infer-gradio` command
- Nginx Config: `/etc/nginx/nginx.conf`
- Startup Script: `/workspace/start_f5tts_services.sh`
- Virtual Env: `/workspace/tts-venv/`

### On Your Server
- Nginx Configs:
  - `/etc/nginx/sites-available/f5tts.ailabsafrica.com.conf`
  - `/etc/nginx/sites-available/f5tts-ui.ailabsafrica.com.conf`
- RunPod Config: `/opt/kasaai/apps/tts-deployment/runpod.config.sh`

## ⚡ Performance

- **GPU:** NVIDIA A40 (44.43 GB VRAM)
- **Memory Used:** ~0.68 GB for F5-TTS model
- **Latency:** Direct HTTPS connection (no SSH tunnel overhead)
- **Timeout:** 100 seconds (Cloudflare limit on RunPod proxy)

## 🔄 Restart Procedure

If RunPod pod restarts:
1. Services will stop (not persistent)
2. SSH port may change (update runpod.config.sh)
3. Nginx config persists (no action needed)
4. Restart services: `/workspace/start_f5tts_services.sh`

## 🎯 Next Steps

- ☐ Set up Moshi/Kyutai on port 8012
- ☐ Add auto-start script for RunPod services
- ☐ Monitor and optimize performance
- ☐ Consider adding health monitoring/alerts

## 📝 Notes

- RunPod HTTP proxy has 100-second timeout (Cloudflare)
- Services must bind to `0.0.0.0` (not `127.0.0.1`)
- Max 10 HTTP ports can be exposed per pod
- SSL termination happens on your server, not RunPod

---

**Deployment completed:** 2025-11-08 13:10 UTC  
**Deployed by:** Claude Code  
**Status:** ✅ Production Ready
