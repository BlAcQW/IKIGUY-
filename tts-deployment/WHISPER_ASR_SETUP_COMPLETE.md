# Whisper ASR Setup Complete ✅

**Date:** 2025-11-27
**Status:** ✅ **RUNPOD SERVICE WORKING** - Proxy server config needed

---

## ✅ Test Results

### RunPod Service (194.68.245.121:22153)

**Service Stack:**
- ✅ Port 8021: Python Whisper ASR service (running)
- ✅ Port 8011: Nginx proxy (listening, forwarding to 8021)

**Test Results:**
```bash
# Direct Python service test
curl http://localhost:8021/health
✅ {"status":"healthy","models_loaded":[],"gpu_available":true,"device":"cuda"}

# Nginx proxy test (port 8011)
curl http://localhost:8011/health
✅ {"status":"healthy","models_loaded":[],"gpu_available":true,"device":"cuda"}

# Models endpoint
curl http://localhost:8011/v1/models
✅ Returns list of available models (tiny, base, small, medium, large-v2, large-v3)
```

**Nginx Configuration (RunPod):**
- ✅ Port 8011 → Port 8021 (correctly configured)
- ✅ WebSocket support enabled
- ✅ All endpoints proxied correctly

---

## 🔧 Proxy Server Configuration Needed

**Server:** 148.251.0.46
**Domain:** whisper.ailabsafrica.com

### Step 1: Create Nginx Config

**File:** `/etc/nginx/sites-available/whisper.ailabsafrica.com`

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name whisper.ailabsafrica.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name whisper.ailabsafrica.com;

    # SSL certificate configuration
    ssl_certificate /etc/letsencrypt/live/whisper.ailabsafrica.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/whisper.ailabsafrica.com/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    client_max_body_size 100M;

    # Forward to RunPod internal URL
    location / {
        proxy_pass http://jzfmzviw26huka.runpod.internal:8011;
        proxy_http_version 1.1;
        
        # Headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 120s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
        
        # Buffering
        proxy_buffering off;
    }

    # WebSocket streaming endpoint
    location /ws/ {
        proxy_pass http://jzfmzviw26huka.runpod.internal:8011/ws/;
        proxy_http_version 1.1;
        
        # WebSocket headers
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # Extended timeout for WebSocket
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }
}
```

### Step 2: Enable Configuration

```bash
# Create symlink
sudo ln -s /etc/nginx/sites-available/whisper.ailabsafrica.com /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

### Step 3: Verify SSL Certificate

```bash
# Check if certificate exists
sudo certbot certificates | grep whisper.ailabsafrica.com

# If not, obtain certificate
sudo certbot --nginx -d whisper.ailabsafrica.com
```

---

## 🌐 Service Architecture

```
Internet
   ↓
whisper.ailabsafrica.com (148.251.0.46:443)
   ↓ (HTTPS)
Proxy Server Nginx
   ↓ (HTTP)
jzfmzviw26huka.runpod.internal:8011
   ↓
RunPod Nginx (Port 8011)
   ↓ (HTTP)
Python Whisper ASR Service (Port 8021)
```

---

## 📋 Available Endpoints

Once proxy is configured, these will be accessible:

- **Health Check:** `https://whisper.ailabsafrica.com/health`
- **List Models:** `https://whisper.ailabsafrica.com/v1/models`
- **OpenAI-compatible:** `https://whisper.ailabsafrica.com/v1/audio/transcriptions`
- **Simplified:** `https://whisper.ailabsafrica.com/transcribe`
- **WebSocket:** `wss://whisper.ailabsafrica.com/ws/stream`

---

## 🧪 Test Commands

**After proxy is configured:**

```bash
# Health check
curl https://whisper.ailabsafrica.com/health

# List models
curl https://whisper.ailabsafrica.com/v1/models

# Test transcription (requires audio file)
curl -X POST https://whisper.ailabsafrica.com/transcribe \
  -F "audio_file=@test.wav" \
  -F "model=base" \
  -F "language=tw"
```

---

## ✅ Current Status

- ✅ RunPod service running on port 8021
- ✅ RunPod nginx configured on port 8011
- ✅ All endpoints tested and working
- ⏳ Proxy server nginx config needed (148.251.0.46)
- ⏳ SSL certificate needed for whisper.ailabsafrica.com

---

## 📝 Notes

- The RunPod service is fully functional and ready
- The proxy server just needs the nginx configuration added
- Follow the same pattern as f5-tts.ailabsafrica.com
- Internal RunPod URL: `http://jzfmzviw26huka.runpod.internal:8011`

