# TTS Provider Hub Infrastructure Documentation

**Created:** 2025-11-09
**Updated:** 2025-11-09
**Status:** ✅ Production Ready - Consolidated UI with Multiple TTS Providers
**Deployment:** RunPod GPU via Proxy (Unified Hub Approach)

---

## Overview

The TTS Provider Hub consolidates all TTS provider UIs into a single landing page for easy access. This replaces the previous individual provider access pattern with a unified hub that routes to multiple TTS services.

---

## Infrastructure Architecture

### Traffic Flow

```
User → gptsovits.ailabsafrica.com (HTTPS)
     → nginx on 148.251.0.46
     → jzfmzviw26huka-8010.proxy.runpod.net (RunPod Proxy)
     → nginx on RunPod:8010
     → TTS Provider Hub (Landing Page at /workspace/tts-ui-hub/index.html)
         ├─ Link → Port 8011 (GPT-SoVITS via nginx → FastAPI:9880)
         ├─ Link → Port 8012 (Fish Speech via nginx → F5-TTS API)
         ├─ Link → Port 8013 (Zonos via nginx → Gradio)
         └─ Link → Port 8014 (Outeai via nginx → Gradio)
```

### Hub Architecture

The hub uses a path-based routing approach where each TTS provider is accessible through a separate RunPod proxy port, all linked from a central landing page.

---

## RunPod Configuration (194.68.245.121:22153)

### Nginx Configuration

Added to `/etc/nginx/nginx.conf` (inside http block, before closing brace):

```nginx
# TTS Provider Hub - Consolidated UI
server {
    listen 8010;
    server_name _;
    client_max_body_size 100M;

    # Landing page
    location / {
        root /workspace/tts-ui-hub;
        try_files $uri $uri/ /index.html;
        add_header Cache-Control 'no-cache, no-store, must-revalidate';
    }
}

# GPT-SoVITS API
server {
    listen 8011;
    server_name _;
    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:9880;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_connect_timeout 120s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
    }
}

# Fish Speech (F5-TTS)
server {
    listen 8012;
    server_name _;
    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:7860;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}

# Zonos TTS
server {
    listen 8013;
    server_name _;
    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:7861;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}

# Outeai TTS
server {
    listen 8014;
    server_name _;
    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:7862;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### Running Services

| Port | Service | Status | Backend Port | Process |
|------|---------|--------|--------------|---------|
| 8010 | TTS Provider Hub (Landing Page) | ✅ Running | Static HTML | nginx |
| 8011 | GPT-SoVITS API | ⚠️ Stopped | 9880 | python3 api.py (when running) |
| 8012 | Fish Speech (F5-TTS) | ✅ Running | 7860 | F5-TTS API |
| 8013 | Zonos TTS | ✅ Running | 7861 | Gradio |
| 8014 | Outeai TTS | ✅ Running | 7862 | Gradio |

### Start Commands

```bash
# Create TTS Hub directory (if not exists)
mkdir -p /workspace/tts-ui-hub

# Upload landing page HTML to /workspace/tts-ui-hub/index.html

# Start GPT-SoVITS API (if not running)
cd /workspace/tts-deployment/docker/tts-webui/gptsovits
nohup python3 api.py > /tmp/gptsovits_api.log 2>&1 &

# All other TTS providers are started via separate processes:
# - Fish Speech (F5-TTS) on port 7860
# - Zonos TTS on port 7861
# - Outeai TTS on port 7862

# Reload nginx
nginx -s reload
```

---

## Local Server Configuration (148.251.0.46)

### Nginx Config

**File:** `/etc/nginx/sites-available/gptsovits.ailabsafrica.com.conf`

```nginx
# TTS Provider Hub - Consolidated UI for all TTS Providers via RunPod Proxy
server {
    listen 80;
    listen [::]:80;
    server_name gptsovits.ailabsafrica.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name gptsovits.ailabsafrica.com;

    ssl_certificate /etc/letsencrypt/live/gptsovits-ui.ailabsafrica.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/gptsovits-ui.ailabsafrica.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    client_max_body_size 100M;
    access_log /var/log/nginx/gptsovits.access.log;
    error_log /var/log/nginx/gptsovits.error.log;

    location / {
        proxy_pass https://jzfmzviw26huka-8010.proxy.runpod.net;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host jzfmzviw26huka-8010.proxy.runpod.net;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_connect_timeout 120s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
        proxy_ssl_server_name on;
        proxy_ssl_verify off;
    }
}
```

**Note:** The domain `gptsovits.ailabsafrica.com` now serves the TTS Provider Hub landing page instead of a single provider interface.

---

## Endpoints

| Endpoint | Status | RunPod Proxy | Purpose |
|----------|--------|--------------|---------|
| https://gptsovits.ailabsafrica.com | ✅ Working | jzfmzviw26huka-8010.proxy.runpod.net | TTS Provider Hub (Landing Page) |

### TTS Provider Access

Access individual providers through the hub landing page, which provides links to:

| Provider | RunPod Proxy | Status |
|----------|--------------|--------|
| GPT-SoVITS | jzfmzviw26huka-8011.proxy.runpod.net | ⚠️ Service Stopped |
| Fish Speech (F5-TTS) | jzfmzviw26huka-8012.proxy.runpod.net | ✅ Working |
| Zonos TTS | jzfmzviw26huka-8013.proxy.runpod.net | ✅ Working |
| Outeai TTS | jzfmzviw26huka-8014.proxy.runpod.net | ✅ Working |

---

## Status

### ✅ Working
- TTS Provider Hub landing page deployed at `/workspace/tts-ui-hub/index.html`
- RunPod nginx listening on ports 8010 (hub), 8011 (GPT-SoVITS), 8012 (Fish Speech), 8013 (Zonos), 8014 (Outeai)
- Fish Speech (F5-TTS) running on port 7860
- Zonos TTS running on port 7861
- Outeai TTS running on port 7862
- Hub accessible via https://gptsovits.ailabsafrica.com
- RunPod proxy working for all ports (8010-8014)
- Full migration from SSH tunnels to RunPod proxy complete
- Consolidated UI architecture replacing individual provider domains

### ⚠️ Needs Attention
- GPT-SoVITS API service (port 9880) not currently running - start if needed

### ❌ Deprecated
- Individual provider domains (gptsovits-ui.ailabsafrica.com) - Replaced by unified hub
- SSH tunnels (localhost:19874 and localhost:19880) - No longer needed
- Previous SSH-tunnel based approach replaced with RunPod proxy
- Separate port 8010 for GPT-SoVITS WebUI - Now consolidated landing page

---

## Benefits of Consolidated Hub Architecture

1. **Unified Access**: Single entry point for all TTS providers
2. **User Experience**: Clean landing page with provider descriptions and links
3. **Reliability**: No need to maintain persistent SSH connections
4. **Consistency**: Standardized access pattern across all providers
5. **Simplicity**: RunPod handles SSL and routing
6. **Scalability**: Easy to add new providers by updating the landing page
7. **Resource Efficiency**: Nginx serves static HTML instead of proxying to separate domains
8. **Automatic**: RunPod proxy is managed by their infrastructure

---

## Troubleshooting

### Check if all TTS services are running on RunPod
```bash
ssh -i ~/.ssh/id_ed25519 root@194.68.245.121 -p 22153 "ss -tlnp | grep -E ':(7860|7861|7862|9880|8010|8011|8012|8013|8014)'"
```

### Test local nginx proxies on RunPod
```bash
# Test hub landing page
ssh -i ~/.ssh/id_ed25519 root@194.68.245.121 -p 22153 "curl -I http://localhost:8010/"

# Test all TTS providers
ssh -i ~/.ssh/id_ed25519 root@194.68.245.121 -p 22153 "curl -I http://localhost:8011/ && curl -I http://localhost:8012/ && curl -I http://localhost:8013/ && curl -I http://localhost:8014/"
```

### Test RunPod proxy access
```bash
# Test hub
curl -I https://jzfmzviw26huka-8010.proxy.runpod.net/

# Test individual providers
curl -I https://jzfmzviw26huka-8011.proxy.runpod.net/  # GPT-SoVITS
curl -I https://jzfmzviw26huka-8012.proxy.runpod.net/  # Fish Speech
curl -I https://jzfmzviw26huka-8013.proxy.runpod.net/  # Zonos
curl -I https://jzfmzviw26huka-8014.proxy.runpod.net/  # Outeai
```

### Restart nginx on RunPod
```bash
ssh -i ~/.ssh/id_ed25519 root@194.68.245.121 -p 22153 "nginx -s reload"
```

### Update landing page on RunPod
```bash
# Upload new version of index.html
scp -i ~/.ssh/id_ed25519 -P 22153 /path/to/index.html root@194.68.245.121:/workspace/tts-ui-hub/index.html
```

---

## Dependencies

Installed on RunPod (2025-11-09):
- ffmpeg-python
- pytorch-lightning
- gradio<5
- funasr
- transformers
- fastapi[standard]
- All requirements from requirements.txt

---

## Migration Notes

**Phase 1 - SSH Tunnels (Deprecated):**
- SSH tunnels: localhost:19874 → RunPod:9874, localhost:19880 → RunPod:9880
- Nginx proxied to localhost:19874 and localhost:19880
- Required maintaining SSH processes
- Separate domain for each service

**Phase 2 - Individual RunPod Proxies (Deprecated):**
- RunPod nginx on ports 8010 (WebUI) and 8011 (API)
- Separate domains: gptsovits.ailabsafrica.com and gptsovits-ui.ailabsafrica.com
- RunPod proxy: jzfmzviw26huka-8010/8011.proxy.runpod.net
- No SSH tunnel maintenance needed

**Phase 3 - Consolidated Hub (Current):**
- Single domain: gptsovits.ailabsafrica.com serves landing page
- Landing page at /workspace/tts-ui-hub/index.html on port 8010
- Multiple TTS providers accessible through one hub:
  - Port 8011: GPT-SoVITS
  - Port 8012: Fish Speech (F5-TTS)
  - Port 8013: Zonos TTS
  - Port 8014: Outeai TTS
- Unified user experience with provider descriptions
- Easier to add new providers without DNS changes

**Port Selection Notes:**
- Initial attempt used ports 8018/8019 but these weren't exposed by RunPod
- Port 8010 was available and marked "Ready" in RunPod dashboard
- Ports 8011-8014 assigned for individual TTS providers
- Port 8010 repurposed from GPT-SoVITS WebUI to consolidated hub landing page

---

**Generated:** 2025-11-09
**Author:** Claude Code
**Related:** TTS_PROVIDER_AUDIT.md, tts-deployment/README.md
