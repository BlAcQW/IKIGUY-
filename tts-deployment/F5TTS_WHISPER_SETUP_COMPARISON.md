# F5-TTS vs Whisper ASR Setup Comparison

**Date:** 2025-11-28

---

## 📊 Setup Pattern

Both services follow the same pattern:
- **Backend Service:** Python service on internal port
- **Nginx Proxy:** Exposed port that forwards to backend
- **Proxy Server:** Forwards domain to RunPod internal URL

---

## 🔵 F5-TTS Setup (Working ✅)

### RunPod Configuration

**Backend Service:**
- Port: **8002** (Python F5-TTS API)
- Status: ✅ Running
- Health: `http://localhost:8002/health`

**Nginx Proxy:**
- Port: **8012** (Exposed port)
- Forwards to: `http://localhost:8002`
- Health: `http://localhost:8012/health`

**Nginx Config (RunPod):**
```nginx
# F5-TTS API - Port 8002 backend, exposed on 8012
server {
    listen 8012;
    location / {
        proxy_pass http://localhost:8002;
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
    location /health {
        proxy_pass http://localhost:8002/health;
        access_log off;
    }
}
```

### Proxy Server Configuration (148.251.0.46)

**Domain:** `f5tts.ailabsafrica.com`
**Forwards to:** `http://jzfmzviw26huka.runpod.internal:8012`
**Status:** ✅ Working (HTTP 200)

---

## 🟢 Whisper ASR Setup (Needs Proxy Config ⚠️)

### RunPod Configuration

**Backend Service:**
- Port: **8021** (Python Whisper ASR)
- Status: ✅ Running
- Health: `http://localhost:8021/health`
- Models: `['base']` loaded

**Nginx Proxy:**
- Port: **8011** (Exposed port)
- Forwards to: `http://127.0.0.1:8021`
- Health: `http://localhost:8011/health`
- Status: ✅ Working

**Nginx Config (RunPod):**
```nginx
# Whisper ASR API - Port 8011
server {
    listen 8011;
    server_name _;
    client_max_body_size 100M;

    location /health {
        proxy_pass http://127.0.0.1:8021/health;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        access_log off;
    }

    location / {
        proxy_pass http://127.0.0.1:8021;
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
```

### Proxy Server Configuration (148.251.0.46) - NEEDED ⚠️

**Domain:** `whisper.ailabsafrica.com`
**Should forward to:** `http://jzfmzviw26huka.runpod.internal:8011`
**Current Status:** ❌ 502 Bad Gateway (not configured)

**Required Config:**
```nginx
server {
    listen 443 ssl http2;
    server_name whisper.ailabsafrica.com;

    ssl_certificate /etc/letsencrypt/live/whisper.ailabsafrica.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/whisper.ailabsafrica.com/privkey.pem;

    location / {
        proxy_pass http://jzfmzviw26huka.runpod.internal:8011;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_cache_bypass $http_upgrade;
        proxy_connect_timeout 120s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
    }
}
```

---

## 📋 Summary

| Service | Backend Port | Exposed Port | Domain | Status |
|---------|-------------|--------------|--------|--------|
| **F5-TTS** | 8002 | 8012 | f5tts.ailabsafrica.com | ✅ Working |
| **Whisper ASR** | 8021 | 8011 | whisper.ailabsafrica.com | ⚠️ Needs proxy config |

---

## ✅ Action Required

The RunPod setup for Whisper ASR is **correct and matches the F5-TTS pattern**. 

**Only missing:** Proxy server nginx configuration on 148.251.0.46 to forward `whisper.ailabsafrica.com` → `http://jzfmzviw26huka.runpod.internal:8011`

Once the proxy server is configured (following the F5-TTS pattern), the domain will work.

