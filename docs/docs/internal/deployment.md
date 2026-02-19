# Deployment Guide

**Internal Documentation - AI Labs Africa Employees Only**

## Prerequisites

### Server Access

**Production Server (148.251.0.46)**
```bash
ssh root@148.251.0.46
# Or
ssh root@api.ailabsafrica.com
```

**Development Server (85.214.12.174)**
```bash
ssh root@85.214.12.174
# Or
ssh root@dev-api.ailabsafrica.com
```

### Repository

```bash
cd /opt/kasaai
git pull origin main
```

## Deploying a New Application

### 1. Create Backend Service

Create systemd service file:
```bash
sudo nano /etc/systemd/system/kasaai-yourapp-backend.service
```

Template:
```ini
[Unit]
Description=KasaAI YourApp Backend
After=network.target

[Service]
Type=simple
User=dev
Group=dev
WorkingDirectory=/opt/kasaai/apps/yourapp/backend
Environment="PATH=/opt/kasaai/apps/venv/bin"
EnvironmentFile=/opt/kasaai/.env
ExecStart=/opt/kasaai/apps/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 30036
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable kasaai-yourapp-backend
sudo systemctl start kasaai-yourapp-backend
sudo systemctl status kasaai-yourapp-backend
```

### 2. Configure Nginx

Create nginx configuration:
```bash
sudo nano /etc/nginx/sites-available/yourapp-api.ailabsafrica.com.conf
```

Template:
```nginx
server {
    listen 80;
    server_name yourapp-api.ailabsafrica.com;

    # CORS headers
    add_header Access-Control-Allow-Origin "*" always;
    add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
    add_header Access-Control-Allow-Headers "Authorization, Content-Type, X-Organization-ID" always;

    # Handle preflight requests
    if ($request_method = OPTIONS) {
        return 204;
    }

    location / {
        proxy_pass http://localhost:30036;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # Timeouts for long-running requests
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/yourapp-api.ailabsafrica.com.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 3. Set Up SSL

```bash
sudo certbot --nginx -d yourapp-api.ailabsafrica.com
```

### 4. Deploy Frontend

Build frontend:
```bash
cd /opt/kasaai/apps/yourapp/frontend
npm install
npm run build
```

Create nginx configuration:
```bash
sudo nano /etc/nginx/sites-available/yourapp.ailabsafrica.com.conf
```

Template:
```nginx
server {
    listen 80;
    server_name yourapp.ailabsafrica.com;

    root /opt/kasaai/apps/yourapp/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable and get SSL:
```bash
sudo ln -s /etc/nginx/sites-available/yourapp.ailabsafrica.com.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d yourapp.ailabsafrica.com
```

## Updating Existing Applications

### Backend Update

```bash
# Navigate to repo
cd /opt/kasaai

# Pull latest changes
git pull origin main

# Activate virtual environment
source apps/venv/bin/activate

# Install dependencies if requirements changed
pip install -r apps/yourapp/backend/requirements.txt

# Restart service
sudo systemctl restart kasaai-yourapp-backend

# Check status
sudo systemctl status kasaai-yourapp-backend

# View logs
sudo journalctl -u kasaai-yourapp-backend -f
```

### Frontend Update

```bash
# Navigate to frontend
cd /opt/kasaai/apps/yourapp/frontend

# Pull latest (if not already done)
git pull origin main

# Install dependencies
npm install

# Build
npm run build

# Nginx will serve the updated dist/ automatically
```

### Shared Library Update

When updating @apps/shared/:
```bash
cd /opt/kasaai/apps/shared

# Pull changes
git pull origin main

# Reinstall shared library
pip install -e .

# Restart all services that use shared library
sudo systemctl restart kasaai-core-backend
sudo systemctl restart kasaai-studyflow-backend
sudo systemctl restart kasaai-churchflow-backend
sudo systemctl restart kasaai-inkwave-backend
sudo systemctl restart kasaai-eventflow-backend
sudo systemctl restart kasaai-erp-backend
sudo systemctl restart kasaai-docs-backend
```

## Database Migrations

### MongoDB

No automatic migrations. Manual updates via mongosh:

```bash
mongosh "mongodb://admin:aawwER4444%@127.0.0.1:27017/"

use yourapp_db

# Example: Add new field to all documents
db.collection.updateMany(
  {},
  { $set: { new_field: "default_value" } }
)
```

### PostgreSQL (Supabase)

Access Supabase dashboard:
- Production: https://supabase.ailabsafrica.com
- Run migrations via SQL editor

## Rollback Procedure

If deployment fails:

```bash
# 1. Rollback git
cd /opt/kasaai
git log --oneline -5  # Find previous commit
git checkout <previous-commit-hash>

# 2. Rebuild (if needed)
# Backend: restart service
sudo systemctl restart kasaai-yourapp-backend

# Frontend: rebuild
cd apps/yourapp/frontend
npm run build

# 3. Return to main when ready
git checkout main
```

## Health Checks

### Check All Services

```bash
sudo systemctl list-units "kasaai-*.service" --all
```

### Check Individual Service

```bash
sudo systemctl status kasaai-yourapp-backend
```

### Check Nginx

```bash
sudo nginx -t  # Test configuration
sudo systemctl status nginx
```

### Check Logs

```bash
# Application logs
sudo journalctl -u kasaai-yourapp-backend -n 100

# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

## Environment Variables

Located in `/opt/kasaai/.env`:

```bash
# Edit environment variables
sudo nano /opt/kasaai/.env

# After editing, restart affected services
sudo systemctl restart kasaai-yourapp-backend
```

**Never commit .env file to git!**

## SSL Certificate Renewal

Certificates auto-renew via certbot. To manually renew:

```bash
sudo certbot renew
sudo systemctl reload nginx
```

Check expiration:
```bash
sudo certbot certificates
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs for errors
sudo journalctl -u kasaai-yourapp-backend -n 50

# Check port availability
sudo netstat -tulpn | grep 30036

# Check file permissions
ls -la /opt/kasaai/apps/yourapp/backend/
```

### Nginx Configuration Error

```bash
# Test configuration
sudo nginx -t

# Check syntax
sudo nginx -T | less
```

### Database Connection Issues

```bash
# Test MongoDB connection
mongosh "mongodb://admin:aawwER4444%@127.0.0.1:27017/"

# Check if MongoDB is running
sudo systemctl status mongod
```

## Security Best Practices

1. **Always use HTTPS** - Never deploy without SSL
2. **Restrict CORS** - Update CORS origins for production
3. **Environment Variables** - Never hardcode secrets
4. **Regular Updates** - Keep system packages updated
5. **Backup Database** - Regular MongoDB backups
6. **Monitor Logs** - Check for suspicious activity

---

## RunPod GPU Cloud Deployments

### RVC Voice Conversion Service

**Service:** RVC (Retrieval-based Voice Conversion)
**Endpoint:** https://rvc.ailabsafrica.com
**Port:** 8017
**Status:** ✅ Production

#### RunPod Configuration

**Pod Details:**
- **Pod ID:** jzfmzviw26huka
- **GPU:** NVIDIA A40 (44.43GB VRAM)
- **SSH Access:** `ssh -i ~/.ssh/id_ed25519 root@194.68.245.121 -p 22153`
- **Location:** `/workspace/rvc-webui/`
- **Python Version:** 3.10 (required for fairseq compatibility)

**Environment Setup:**
```bash
# SSH to RunPod
ssh -i ~/.ssh/id_ed25519 root@194.68.245.121 -p 22153

# Navigate to RVC directory
cd /workspace/rvc-webui

# Virtual environment (Python 3.10)
source venv/bin/activate
```

#### Installation Process

**1. Clone Repository:**
```bash
cd /workspace
git clone https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI.git rvc-webui
cd rvc-webui
```

**2. Create Python 3.10 Virtual Environment:**
```bash
# fairseq requires Python ≤ 3.10
python3.10 -m venv venv
source venv/bin/activate
```

**3. Install PyTorch with CUDA 12.1:**
```bash
pip install --upgrade pip
pip install torch==2.1.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cu121
```

**4. Install Dependencies:**
```bash
# IMPORTANT: pip must be < 24.1 for omegaconf compatibility
pip install 'pip<24.1'
pip install -r requirements.txt
```

**Dependencies Installed:**
- PyTorch 2.1.0 with CUDA 12.1
- fairseq 0.12.2 (requires Python ≤3.10)
- gradio 3.34.0 (for WebUI)
- librosa 0.9.1 (audio processing)
- scipy, numpy, numba (scientific computing)
- FastAPI + uvicorn (for REST API)

**5. Download Models (~3.2GB total):**
```bash
# Models are automatically downloaded on first use
# - HuBERT base model (181MB)
# - RMVPE model (173MB)
# - Pretrained G/D models
# - UVR5 weights
```

#### FastAPI Server Setup

**1. Create API Server:**
File: `/workspace/rvc-webui/app.py` (280 lines)
- Implements FastAPI REST endpoints
- VITS framework + HiFi-GAN vocoder
- GPU-accelerated inference on CUDA

**2. Start API Server:**
```bash
cd /workspace/rvc-webui
source venv/bin/activate
python app.py --port 8017 --host 0.0.0.0 > /tmp/rvc_api_8017.log 2>&1 &
```

**3. Verify Service:**
```bash
# Check if running
ps aux | grep app.py

# Test health endpoint
curl https://jzfmzviw26huka-8017.proxy.runpod.net/health
```

#### Nginx Reverse Proxy (Production Server)

**1. Create Nginx Config:**
File: `/tmp/rvc.ailabsafrica.com.conf`

```nginx
# HTTP redirect to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name rvc.ailabsafrica.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name rvc.ailabsafrica.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/rvc.ailabsafrica.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/rvc.ailabsafrica.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Large file upload support (100MB for audio files)
    client_max_body_size 100M;

    # Logging
    access_log /var/log/nginx/rvc.access.log;
    error_log /var/log/nginx/rvc.error.log;

    # Proxy to RunPod
    location / {
        proxy_pass https://jzfmzviw26huka-8017.proxy.runpod.net;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host jzfmzviw26huka-8017.proxy.runpod.net;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # Extended timeouts for voice conversion
        proxy_connect_timeout 120s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;

        # SSL verification
        proxy_ssl_server_name on;
        proxy_ssl_verify off;
    }
}
```

**2. Deploy Nginx Config:**
```bash
# On production server (148.251.0.46)
sudo cp /tmp/rvc.ailabsafrica.com.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/rvc.ailabsafrica.com.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

**3. Obtain SSL Certificate:**
```bash
sudo certbot --nginx -d rvc.ailabsafrica.com
```

#### Model Management

**Model Directory Structure:**
```
/workspace/rvc-webui/logs/
├── character_voice/
│   ├── model.pth (54MB trained model)
│   └── added_*.index (voice features)
├── neutral_voice/
│   ├── model.pth (54MB)
│   └── added_*.index
└── clear_voice/
    ├── model.pth (54MB)
    └── added_*.index
```

**Training New Models (via Gradio WebUI):**
```bash
cd /workspace/rvc-webui
source venv/bin/activate
python infer-web.py

# Access at http://localhost:7865 via SSH tunnel
# Or use RunPod's public endpoint
```

**Training Process:**
1. Upload 5-30 minutes of clean audio from target speaker
2. Process audio (extract features with ContentVec + RMVPE)
3. Train model (2-4 hours on A40 GPU)
4. Generate index file for retrieval
5. Model automatically available via API at `logs/<model_name>/model.pth`

#### Service Management

**Check Service Status:**
```bash
# SSH to RunPod
ssh -i ~/.ssh/id_ed25519 root@194.68.245.121 -p 22153

# Check if running
ps aux | grep app.py | grep 8017

# View logs
tail -f /tmp/rvc_api_8017.log
```

**Restart Service:**
```bash
# Kill existing process
pkill -f "app.py --port 8017"

# Start new instance
cd /workspace/rvc-webui
source venv/bin/activate
nohup python app.py --port 8017 --host 0.0.0.0 > /tmp/rvc_api_8017.log 2>&1 &
```

**Monitor GPU Usage:**
```bash
# Check GPU utilization
nvidia-smi

# Watch GPU in real-time
watch -n 1 nvidia-smi
```

#### API Endpoints

**Health Check:**
```bash
curl https://rvc.ailabsafrica.com/health

# Expected response:
# {"status": "healthy", "device": "cuda:0", "current_model": null}
```

**List Models:**
```bash
curl https://rvc.ailabsafrica.com/models

# Response includes all available models in logs/ directory
```

**Convert Voice:**
```bash
curl -X POST https://rvc.ailabsafrica.com/convert \
  -F "audio=@input.wav" \
  -F "model_path=logs/character_voice/model.pth" \
  -F "pitch_shift=0" \
  -F "index_rate=0.75" \
  -F "f0_method=rmvpe" \
  --output converted.wav
```

#### Performance Monitoring

**Inference Benchmarks:**
- Short Audio (5s): ~1-2 seconds
- Medium Audio (30s): ~6-8 seconds
- Long Audio (2min): ~25-30 seconds
- GPU Memory: ~2GB VRAM during inference
- Pitch Accuracy: >95% with RMVPE

**Resource Usage:**
```bash
# Check disk usage
du -sh /workspace/rvc-webui/

# Check model sizes
du -sh /workspace/rvc-webui/logs/*/
```

#### Troubleshooting

**Service Won't Start:**
```bash
# Check Python version
python --version  # Should be 3.10.x

# Check dependencies
pip list | grep -E "torch|fairseq|gradio"

# Check port availability
netstat -tulpn | grep 8017

# Check logs
cat /tmp/rvc_api_8017.log
```

**Model Not Found:**
```bash
# List available models
ls -la /workspace/rvc-webui/logs/

# Verify model file exists
ls -lh /workspace/rvc-webui/logs/*/model.pth
```

**CUDA Out of Memory:**
```bash
# Check GPU memory
nvidia-smi

# Kill existing processes using GPU
# (Be careful not to kill other services!)
pkill -f "app.py --port 8017"

# Restart service
cd /workspace/rvc-webui && source venv/bin/activate
python app.py --port 8017 --host 0.0.0.0 > /tmp/rvc_api_8017.log 2>&1 &
```

**Poor Conversion Quality:**
1. Adjust `index_rate` parameter (0.5-0.9)
2. Try different `f0_method` (rmvpe, harvest, fcpe)
3. Increase `filter_radius` for smoothing
4. Retrain model with more/better quality data

#### Backup and Recovery

**Backup Models:**
```bash
# On RunPod
tar -czf rvc_models_backup.tar.gz /workspace/rvc-webui/logs/

# Download to local machine
scp -P 22153 -i ~/.ssh/id_ed25519 \
  root@194.68.245.121:/workspace/rvc-webui/rvc_models_backup.tar.gz \
  ./backups/
```

**Restore Models:**
```bash
# Upload to RunPod
scp -P 22153 -i ~/.ssh/id_ed25519 \
  ./backups/rvc_models_backup.tar.gz \
  root@194.68.245.121:/workspace/rvc-webui/

# Extract
cd /workspace/rvc-webui
tar -xzf rvc_models_backup.tar.gz
```

#### SSL Certificate

**Certificate Details:**
- Domain: rvc.ailabsafrica.com
- Provider: Let's Encrypt
- Expires: February 6, 2026
- Auto-renewal: Configured via certbot

**Manual Renewal:**
```bash
# On production server
sudo certbot renew
sudo systemctl reload nginx
```

#### Documentation References

- **Service Docs:** `/opt/kasaai/apps/shared/voice_engine/RVC_VOICE_CONVERSION.md`
- **Infrastructure:** `/opt/kasaai/apps/architecture/TTS_INFRASTRUCTURE.md`
- **API Docs:** `/opt/kasaai/apps/developer_platform/API_DOCUMENTATION.md`
- **Use Cases:** `/opt/kasaai/apps/docs/docs/use-cases/rvc-voice-conversion.md`
- **GitHub:** https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI

---

**Last Updated**: November 8, 2025
