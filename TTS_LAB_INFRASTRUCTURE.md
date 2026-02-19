# TTS Lab Infrastructure Documentation

**Created:** 2025-11-09
**Status:** ✅ Production Ready - Unified TTS Research & Production Hub
**Domain:** https://ttslab.ailabsafrica.com
**Deployment:** Hybrid (RunPod GPU + Local Infrastructure)

---

## Overview

TTS Lab is a consolidated interface hub providing unified access to all Text-to-Speech services across both RunPod GPU infrastructure and local servers. This replaces fragmented provider-specific domains with a single, professional entry point for research, development, and production TTS workflows.

---

## Architecture

### Traffic Flow

```
User → ttslab.ailabsafrica.com (HTTPS)
     → nginx on 148.251.0.46
     → Serves landing page from /var/www/ttslab/index.html

User selects provider → Redirects to:
     ├─ RunPod Services (via RunPod Proxy)
     │   ├─ GPT-SoVITS: jzfmzviw26huka-8011.proxy.runpod.net
     │   ├─ Fish Speech: jzfmzviw26huka-8012.proxy.runpod.net
     │   ├─ Zonos TTS: jzfmzviw26huka-8013.proxy.runpod.net
     │   ├─ TTS-WebUI: jzfmzviw26huka-8014.proxy.runpod.net
     │   └─ F5-TTS: jzfmzviw26huka-8015.proxy.runpod.net
     │
     └─ Local Services (via nginx proxy)
         └─ MeloTTS: ttslab.ailabsafrica.com/melotts → localhost:8001
```

---

## Service Inventory

### RunPod GPU Services (194.68.245.121:22153)

| Provider | Port | Backend | Status | RunPod Proxy | Features |
|----------|------|---------|--------|--------------|----------|
| **GPT-SoVITS** | 8011 | 9880 (FastAPI) | ⚠️ Stopped | 8011.proxy.runpod.net | Zero-shot voice cloning, multilingual |
| **Fish Speech** | 8012 | 7860 (Gradio) | ✅ Active | 8012.proxy.runpod.net | Natural prosody, emotional control |
| **Zonos TTS** | 8013 | 7861 (Gradio) | ✅ Active | 8013.proxy.runpod.net | High-quality, production-ready |
| **TTS-WebUI (Outeai)** | 8014 | 8017 (Gradio) | ✅ Active | 8014.proxy.runpod.net | Multi-backend unified interface |
| **F5-TTS** | 8015 | 8003 (Gradio) | ✅ Active | 8015.proxy.runpod.net | Flow-matching, zero-shot, 335M params |

**Note:** Port 8010 hosts the old TTS Provider Hub (gptsovits.ailabsafrica.com). TTS Lab supersedes this with more comprehensive coverage.

### Local Infrastructure Services (148.251.0.46)

| Provider | Port | Status | Access Path | Features |
|----------|------|--------|-------------|----------|
| **MeloTTS** | 8001 | ✅ Active | /melotts | Low-latency, lightweight, API-first |

---

## RunPod Nginx Configuration

**Location:** `/etc/nginx/nginx.conf` on 194.68.245.121:22153

Each TTS service has a dedicated server block proxying to the backend service:

```nginx
# F5-TTS Gradio Interface (example)
server {
    listen 8015;
    server_name _;
    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:8003;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_connect_timeout 120s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
    }
}
```

**All configured ports:** 8010, 8011, 8012, 8013, 8014, 8015

---

## Local Server Configuration

**File:** `/etc/nginx/sites-available/ttslab.ailabsafrica.com.conf`

```nginx
server {
    listen 443 ssl http2;
    server_name ttslab.ailabsafrica.com;

    ssl_certificate /etc/letsencrypt/live/gptsovits-ui.ailabsafrica.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/gptsovits-ui.ailabsafrica.com/privkey.pem;

    # Landing page
    location = / {
        root /var/www/ttslab;
        try_files /index.html =404;
        add_header Cache-Control 'no-cache, no-store, must-revalidate';
    }

    # Proxy to MeloTTS
    location /melotts {
        rewrite ^/melotts(.*) $1 break;
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        # ... standard proxy headers ...
    }
}
```

**Landing Page:** `/var/www/ttslab/index.html`

---

## Endpoints

### Main Hub
- **URL:** https://ttslab.ailabsafrica.com
- **Status:** ✅ Working
- **Purpose:** Unified landing page with all TTS provider access

### RunPod Services (Direct Access)
| Service | URL | Status |
|---------|-----|--------|
| GPT-SoVITS | https://jzfmzviw26huka-8011.proxy.runpod.net | ⚠️ Backend Stopped |
| Fish Speech | https://jzfmzviw26huka-8012.proxy.runpod.net | ✅ Working |
| Zonos TTS | https://jzfmzviw26huka-8013.proxy.runpod.net | ✅ Working |
| TTS-WebUI | https://jzfmzviw26huka-8014.proxy.runpod.net | ✅ Working |
| F5-TTS | https://jzfmzviw26huka-8015.proxy.runpod.net | ✅ Working |

### Local Services
| Service | URL | Status |
|---------|-----|--------|
| MeloTTS | https://ttslab.ailabsafrica.com/melotts | ✅ Working |

---

## Features

### Landing Page Highlights
- **Responsive Design:** Modern gradient UI with card-based provider layout
- **Provider Categorization:** Separate sections for RunPod GPU and Local services
- **Real-time Status:** Visual indicators for service availability
- **Rich Metadata:** Each provider card includes:
  - Description and use cases
  - Key features list
  - Technology stack tags
  - Direct launch links
- **Statistics Dashboard:** Shows total models, infrastructures, and availability

### Infrastructure Benefits
1. **Unified Access:** Single domain for all TTS services
2. **Hybrid Deployment:** Leverages both GPU cloud and local infrastructure
3. **Flexibility:** Easy to add/remove providers without DNS changes
4. **Professional Presentation:** Clean, modern interface for clients and researchers
5. **Service Discovery:** Clear categorization and feature descriptions
6. **Zero Downtime:** No dependency on SSH tunnels
7. **SSL Security:** HTTPS for all services

---

## Service Status

### ✅ Working
- TTS Lab landing page at https://ttslab.ailabsafrica.com
- RunPod nginx listening on ports 8010-8015
- F5-TTS Gradio (port 8003 → 8015)
- Fish Speech Gradio (port 7860 → 8012)
- Zonos TTS Gradio (port 7861 → 8013)
- TTS-WebUI (port 8017 → 8014)
- MeloTTS local service (port 8001)
- All RunPod proxy URLs accessible
- Local nginx proxy to MeloTTS working

### ⚠️ Needs Attention
- GPT-SoVITS backend not currently running (can be started if needed)
- Fish Speech returns 405 on HEAD requests (normal for API-first services)
- DNS propagation for dedicated ttslab SSL cert (currently using shared cert)

---

## Troubleshooting

### Test All RunPod Services
```bash
# Check all nginx ports on RunPod
ssh -i ~/.ssh/id_ed25519 root@194.68.245.121 -p 22153 "ss -tlnp | grep -E ':(8010|8011|8012|8013|8014|8015)'"

# Test each RunPod proxy
curl -I https://jzfmzviw26huka-8011.proxy.runpod.net/  # GPT-SoVITS
curl -I https://jzfmzviw26huka-8012.proxy.runpod.net/  # Fish Speech
curl -I https://jzfmzviw26huka-8013.proxy.runpod.net/  # Zonos
curl -I https://jzfmzviw26huka-8014.proxy.runpod.net/  # TTS-WebUI
curl -I https://jzfmzviw26huka-8015.proxy.runpod.net/  # F5-TTS
```

### Test Local Services
```bash
# Test MeloTTS direct
curl -I http://localhost:8001

# Test MeloTTS through ttslab proxy
curl -I https://ttslab.ailabsafrica.com/melotts

# Test landing page
curl -I https://ttslab.ailabsafrica.com/
```

### Update Landing Page
```bash
# Edit and upload new version
vi /var/www/ttslab/index.html

# Or copy from backup
sudo cp /tmp/ttslab_index.html /var/www/ttslab/index.html
```

### Restart Services
```bash
# Reload nginx on local server
sudo systemctl reload nginx

# Reload nginx on RunPod
ssh -i ~/.ssh/id_ed25519 root@194.68.245.121 -p 22153 "nginx -s reload"

# Start GPT-SoVITS if needed
ssh -i ~/.ssh/id_ed25519 root@194.68.245.121 -p 22153 "cd /workspace/tts-deployment/docker/tts-webui/gptsovits && nohup python3 api.py > /tmp/gptsovits_api.log 2>&1 &"
```

---

## Future Enhancements

### Planned Additions
1. **More Local Services:** Add more TTS providers to local infrastructure
2. **API Gateway:** Unified API endpoint for programmatic access
3. **Model Comparison:** Side-by-side comparison tool
4. **Usage Analytics:** Track provider usage and performance
5. **User Authentication:** Secure access with user accounts
6. **Rate Limiting:** Prevent abuse and ensure fair usage
7. **Dedicated SSL:** Obtain dedicated cert once DNS fully propagates

### Potential New Providers
- StyleTTS2 (already running on RunPod, needs nginx config)
- Bark TTS
- Coqui TTS
- XTTS
- Piper TTS
- Edge TTS

---

## Relationship to Other Infrastructure

### Supersedes
- **Old TTS Provider Hub** (gptsovits.ailabsafrica.com on port 8010)
  - Now serves basic 4-provider hub
  - TTS Lab provides comprehensive coverage with better UX

### Complements
- **Voice Lab** (@apps/voice-lab/) - Research and development
- **Core Backend** (@apps/core_backend/) - Production TTS API integration
- **Vapi TTS Service** (@apps/vapi_service/) - Webhook integration for Vapi

### Related Documentation
- GPTSOVITS_INFRASTRUCTURE.md - Detailed GPT-SoVITS deployment
- TTS_PROVIDER_AUDIT.md - Provider capabilities and comparison
- @apps/voice-lab/API_INTEGRATION_GUIDE.md - Integration patterns

---

## Dependencies

### RunPod Services
All services use `/workspace/tts-venv/bin/python3` virtual environment with:
- PyTorch with CUDA support
- Gradio (various versions)
- Provider-specific dependencies

### Local Services
- MeloTTS: Docker container on port 8001
- Nginx 1.18.0
- Let's Encrypt SSL certificates

---

## Maintenance

### Regular Tasks
1. **Monitor Service Health:** Check all provider status weekly
2. **Update Landing Page:** Reflect new providers or status changes
3. **SSL Renewal:** Certbot handles auto-renewal (verify monthly)
4. **Log Rotation:** Monitor nginx access/error logs
5. **RunPod Instance:** Ensure pod doesn't terminate (check dashboard)

### Emergency Contacts
- **DNS Issues:** Cloudflare dashboard or DNS provider
- **SSL Issues:** Let's Encrypt logs at `/var/log/letsencrypt/`
- **RunPod Issues:** RunPod dashboard or support
- **Service Issues:** Check systemd logs and application logs

---

**Generated:** 2025-11-09
**Author:** Claude Code
**Version:** 1.0
**Related:** GPTSOVITS_INFRASTRUCTURE.md, TTS_PROVIDER_AUDIT.md
