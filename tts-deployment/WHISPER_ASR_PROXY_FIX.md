# Whisper ASR Proxy Server Fix Required

**Date:** 2025-11-28
**Status:** ⚠️ **502 Bad Gateway** - Proxy server needs configuration

---

## 🔴 Current Issue

**Domain:** https://whisper.ailabsafrica.com
**Status:** HTTP 502 Bad Gateway
**Error:** Proxy server (148.251.0.46) cannot connect to RunPod backend

---

## ✅ RunPod Service Status

**Service is working correctly:**
- ✅ Port 8021: Python Whisper ASR service (healthy)
- ✅ Port 8011: Nginx proxy (healthy, forwarding to 8021)
- ✅ Internal URL: `http://jzfmzviw26huka.runpod.internal:8011` (working)
- ✅ Direct IP: `http://194.68.245.121:8011` (should work)

---

## 🔧 Fix Required on Proxy Server (148.251.0.46)

### Option 1: Use RunPod Internal URL (Recommended)

**File:** `/etc/nginx/sites-available/whisper.ailabsafrica.com`

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name whisper.ailabsafrica.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name whisper.ailabsafrica.com;

    ssl_certificate /etc/letsencrypt/live/whisper.ailabsafrica.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/whisper.ailabsafrica.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    client_max_body_size 100M;

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
        proxy_buffering off;
    }

    location /ws/ {
        proxy_pass http://jzfmzviw26huka.runpod.internal:8011/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }
}
```

### Option 2: Use Direct IP (If internal URL doesn't work)

If `jzfmzviw26huka.runpod.internal` doesn't resolve, use direct IP:

```nginx
proxy_pass http://194.68.245.121:8011;
```

---

## 📋 Setup Steps

1. **Create/Update nginx config:**
   ```bash
   sudo nano /etc/nginx/sites-available/whisper.ailabsafrica.com
   # Paste the config above
   ```

2. **Enable the site:**
   ```bash
   sudo ln -sf /etc/nginx/sites-available/whisper.ailabsafrica.com /etc/nginx/sites-enabled/
   ```

3. **Test configuration:**
   ```bash
   sudo nginx -t
   ```

4. **Reload nginx:**
   ```bash
   sudo systemctl reload nginx
   ```

5. **Test the domain:**
   ```bash
   curl https://whisper.ailabsafrica.com/health
   ```

---

## 🧪 Verification

After fixing, test:

```bash
# Health check
curl https://whisper.ailabsafrica.com/health

# Expected response:
# {"status":"healthy","models_loaded":["base"],"gpu_available":true,"device":"cuda"}

# List models
curl https://whisper.ailabsafrica.com/v1/models
```

---

## 🔍 Troubleshooting

**If 502 persists:**

1. **Check if internal URL resolves:**
   ```bash
   ping jzfmzviw26huka.runpod.internal
   # Or
   curl http://jzfmzviw26huka.runpod.internal:8011/health
   ```

2. **Try direct IP instead:**
   ```bash
   curl http://194.68.245.121:8011/health
   ```

3. **Check nginx error logs:**
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```

4. **Verify RunPod service is accessible:**
   ```bash
   # From RunPod itself
   curl http://localhost:8011/health
   ```

---

## 📝 Notes

- The RunPod service is fully functional
- The issue is only with the proxy server configuration
- Follow the same pattern as other services (f5-tts, etc.)
- Internal URL should work if proxy server is on same RunPod network

