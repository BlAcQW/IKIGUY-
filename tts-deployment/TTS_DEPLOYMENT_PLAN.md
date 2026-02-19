# TTS Systems Deployment Plan
**Created:** 2025-10-19
**Infrastructure:** RunPod GPU (48GB VRAM) + Local GPU (20GB VRAM)

## System Overview

### Systems to Deploy
1. **MeloTTS** - Fast multilingual TTS
2. **F5-TTS** - Flow-matching based TTS
3. **OpenVoice** - Voice cloning TTS
4. **Chatterbox** - TTS system (needs clarification on specific version)
5. **Coqui TTS** - Production-ready TTS with multiple models
6. **StyleTTS2** - High-quality expressive TTS
7. **WebUI** - Gradio/Web interface (needs clarification)
8. **Kyutai (Moshi)** - Real-time conversational AI
9. **Crawl4AI** - Web scraping tool (non-TTS)

---

## GPU Allocation Strategy

### RunPod GPU (48GB VRAM) - Primary for Heavy Workloads
**Use for:**
- **Kyutai/Moshi** (12-16GB VRAM) - Real-time conversational model
- **StyleTTS2** (8-12GB VRAM) - Training and high-quality inference
- **F5-TTS** (6-10GB VRAM) - Flow-matching inference
- **Training tasks** for any model

**Rationale:** These are the most VRAM-intensive systems requiring substantial GPU memory.

### Local GPU (20GB VRAM) - For Lighter Inference
**Use for:**
- **MeloTTS** (2-4GB VRAM) - Fast inference
- **OpenVoice** (4-6GB VRAM) - Voice cloning
- **Coqui TTS** (3-6GB VRAM) - Production inference
- **Chatterbox** (3-5GB VRAM) - Lightweight inference
- **Crawl4AI** (CPU-based, minimal GPU)

**Rationale:** These systems have lower VRAM requirements and can run efficiently on 20GB GPU.

---

## Deployment Architecture

### Option A: Docker-Based (Recommended)
**Advantages:**
- Easy deployment and updates
- Isolated environments
- Port management
- Resource limits

**Systems with Docker Support:**
- ✅ Coqui TTS (official Docker images)
- ✅ Crawl4AI (Docker support available)
- ✅ Custom containers for others (PyTorch base)

### Option B: /opt Installation (Fallback)
**For systems without Docker or requiring custom setup:**
- Direct installation in `/opt/<system-name>`
- Virtual environments per system
- Systemd service files for auto-start

---

## Detailed Deployment Plan

### 1. MeloTTS
**Location:** Local GPU (20GB)
**Deployment:** Docker
**VRAM:** ~3GB
**Port:** 8001
**Domain:** melotts.ailabsafrica.com

**Docker Setup:**
```dockerfile
# Base: pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime
# Install MeloTTS from GitHub
# Expose port 8001
# FastAPI/Gradio endpoint
```

**Nginx Config:**
```nginx
server {
    listen 80;
    server_name melotts.ailabsafrica.com;

    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

### 2. F5-TTS
**Location:** RunPod GPU (48GB)
**Deployment:** Docker
**VRAM:** ~8GB
**Port:** 8002
**Domain:** f5tts.ailabsafrica.com

**Access:** SSH tunnel from local to RunPod
```bash
ssh -L 8002:localhost:8002 root@63.141.33.46 -p 22082 -i ~/.ssh/id_ed25519
```

**Nginx Config (Local):**
```nginx
server {
    listen 80;
    server_name f5tts.ailabsafrica.com;

    location / {
        proxy_pass http://localhost:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 300s;
    }
}
```

---

### 3. OpenVoice
**Location:** Local GPU (20GB)
**Deployment:** Docker
**VRAM:** ~5GB
**Port:** 8003
**Domain:** openvoice.ailabsafrica.com

**Docker Setup:**
```dockerfile
# Base: pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime
# Clone myshell-ai/OpenVoice
# Install dependencies
# Expose port 8003
```

---

### 4. Chatterbox
**Location:** Local GPU (20GB)
**Deployment:** /opt (pending clarification on specific version)
**VRAM:** ~4GB
**Port:** 8004
**Domain:** chatterbox.ailabsafrica.com

**Note:** Need clarification on which Chatterbox implementation

---

### 5. Coqui TTS
**Location:** Local GPU (20GB)
**Deployment:** Docker (official image available)
**VRAM:** ~4GB
**Port:** 8005
**Domain:** coqui.ailabsafrica.com

**Docker Command:**
```bash
docker run -d \
  --name coqui-tts \
  --gpus all \
  -p 8005:5002 \
  ghcr.io/coqui-ai/tts-cpu
```

---

### 6. StyleTTS2
**Location:** RunPod GPU (48GB)
**Deployment:** Docker
**VRAM:** ~10GB
**Port:** 8006
**Domain:** styletts.ailabsafrica.com

**High VRAM needed for quality synthesis**

---

### 7. WebUI
**Location:** TBD (needs clarification)
**Deployment:** Docker
**Port:** 8007
**Domain:** tts-webui.ailabsafrica.com

**Note:** Need clarification on which WebUI (all-in-one interface?)

---

### 8. Kyutai (Moshi)
**Location:** RunPod GPU (48GB)
**Deployment:** Docker
**VRAM:** ~14GB
**Port:** 8008
**Domain:** kyutai.ailabsafrica.com

**Real-time conversational AI - very GPU intensive**

---

### 9. Crawl4AI
**Location:** Local (CPU-based)
**Deployment:** Docker
**Port:** 8009
**Domain:** crawl4ai.ailabsafrica.com

**Docker Command:**
```bash
docker run -d \
  --name crawl4ai \
  -p 8009:8000 \
  unclecode/crawl4ai:latest
```

---

## Network Configuration

### Local Machine Setup
- All services on local GPU expose ports 8001, 8003-8005, 8009
- Nginx reverse proxy handles domain routing
- SSL/TLS via Let's Encrypt (certbot)

### RunPod Setup
- Services on RunPod expose ports 8002, 8006, 8008
- SSH tunnels forward ports to local machine
- Local nginx proxies to tunneled ports

### SSH Tunnel Script
```bash
#!/bin/bash
# /opt/scripts/runpod_tunnels.sh

ssh -N -L 8002:localhost:8002 \
       -L 8006:localhost:8006 \
       -L 8008:localhost:8008 \
       root@63.141.33.46 -p 22082 -i ~/.ssh/id_ed25519 &

echo "RunPod tunnels established"
```

---

## Resource Management

### Docker Compose - Local GPU
```yaml
version: '3.8'

services:
  melotts:
    build: ./melotts
    ports:
      - "8001:8001"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    environment:
      - CUDA_VISIBLE_DEVICES=0
    restart: unless-stopped

  openvoice:
    build: ./openvoice
    ports:
      - "8003:8003"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped

  coqui:
    image: ghcr.io/coqui-ai/tts
    ports:
      - "8005:5002"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped

  crawl4ai:
    image: unclecode/crawl4ai:latest
    ports:
      - "8009:8000"
    restart: unless-stopped
```

### Docker Compose - RunPod GPU
```yaml
version: '3.8'

services:
  f5tts:
    build: ./f5tts
    ports:
      - "8002:8002"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    environment:
      - CUDA_VISIBLE_DEVICES=0
    restart: unless-stopped

  styletts:
    build: ./styletts2
    ports:
      - "8006:8006"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped

  kyutai:
    build: ./kyutai
    ports:
      - "8008:8008"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped
```

---

## Implementation Phases

### Phase 1: Foundation (Week 1)
- [ ] Set up base Docker environment on both GPUs
- [ ] Configure nginx on local machine
- [ ] Test SSH tunnels to RunPod
- [ ] Deploy Crawl4AI (simplest, non-GPU)
- [ ] Deploy Coqui TTS (has official Docker support)

### Phase 2: Lightweight TTS (Week 2)
- [ ] Deploy MeloTTS on local GPU
- [ ] Deploy OpenVoice on local GPU
- [ ] Configure SSL certificates for all domains
- [ ] Test inference performance

### Phase 3: Heavy TTS (Week 3)
- [ ] Deploy F5-TTS on RunPod
- [ ] Deploy StyleTTS2 on RunPod
- [ ] Optimize VRAM usage and batching
- [ ] Performance benchmarking

### Phase 4: Advanced Systems (Week 4)
- [ ] Deploy Kyutai/Moshi on RunPod
- [ ] Clarify and deploy Chatterbox
- [ ] Clarify and deploy WebUI
- [ ] Load balancing and failover setup

---

## Monitoring & Maintenance

### GPU Monitoring
```bash
# Local GPU
watch -n 1 nvidia-smi

# RunPod GPU
ssh root@63.141.33.46 -p 22082 -i ~/.ssh/id_ed25519 'watch -n 1 nvidia-smi'
```

### Docker Monitoring
```bash
docker stats
docker compose logs -f <service>
```

### Health Checks
- Endpoint monitoring via uptime tools
- Prometheus + Grafana for metrics
- Alert on GPU memory >90%

---

## Backup & Disaster Recovery

### Model Checkpoints
- Store on shared cloud storage (S3/GCS)
- Sync between RunPod and local

### Configuration Backup
- Git repository for all configs
- Automated daily backups

### Failover Strategy
- If RunPod fails: redirect heavy models to local (reduced performance)
- If local fails: SSH tunnel to RunPod for all services

---

## Cost Optimization

### RunPod
- Use Spot instances when possible for training
- On-demand for production inference
- Shut down unused containers

### Local
- Keep running 24/7 for low-latency inference
- Power management for idle periods

---

## Security Considerations

1. **SSH Key Management**
   - Rotate keys regularly
   - Use ssh-agent for tunnel management

2. **API Authentication**
   - Add API keys to all endpoints
   - Rate limiting via nginx

3. **Network Security**
   - Firewall rules (UFW)
   - Fail2ban for SSH protection
   - HTTPS only (redirect HTTP)

4. **Docker Security**
   - Non-root containers where possible
   - Regular image updates
   - Security scanning (Trivy)

---

## Questions Requiring Clarification

1. **Chatterbox**: Which specific implementation? (GitHub repo/source?)
2. **WebUI**: Is this an all-in-one interface for all TTS systems, or a specific project?
3. **Training**: Will you be training models, or only inference?
4. **API Style**: REST API, gRPC, or WebSocket preference?
5. **Authentication**: Shared auth system or per-service?
6. **Storage**: Where to store generated audio files? (Local, S3, etc.)
7. **Scaling**: Expected concurrent requests per service?

---

## Next Steps

1. **Clarify the questions above**
2. **Create base Docker images** for each system
3. **Set up nginx configurations** with SSL
4. **Deploy Phase 1 systems** (Crawl4AI, Coqui)
5. **Test SSH tunnels and monitoring**
6. **Document API endpoints** for each service
7. **Create systemd services** for auto-start
8. **Set up monitoring dashboards**

