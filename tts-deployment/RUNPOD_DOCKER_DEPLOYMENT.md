# F5-TTS & StyleTTS2 Docker Deployment on RunPod

**Date:** 2025-10-21
**Status:** ✅ Both services ready for Docker deployment
**Deployment Method:** Docker Compose (Production)

---

## 📊 Service Comparison

| Feature | F5-TTS | StyleTTS2 |
|---------|---------|-----------|
| **Port** | 8002 | 8006 |
| **VRAM** | ~0.7GB | ~4GB |
| **Docker Image Size** | ~8GB | ~8-10GB |
| **Build Time** | 15-20 min | 10-20 min |
| **Startup Time** | 30-60s | 30-60s |
| **Status** | ⚠️ Running via Python | ✅ Ready for Docker |
| **Dockerfile** | ✅ Complete | ✅ Complete |
| **app.py** | ✅ Complete | ✅ Complete |

---

## 🎯 Deployment Strategy

### Current State
- **F5-TTS**: Running directly via Python on RunPod (not using Docker)
- **StyleTTS2**: Code ready, not yet deployed

### Recommended Approach
Deploy **both services via Docker Compose** for:
- ✅ Consistency (same deployment method)
- ✅ Portability (easy pod migration)
- ✅ Reliability (auto-restart on crash)
- ✅ Isolation (no dependency conflicts)
- ✅ Easy management (single docker-compose command)

---

## 🚀 Complete Deployment Guide

### Prerequisites

Verify Docker is installed on RunPod:
```bash
ssh -p 22130 root@194.68.245.121

# Check Docker
docker --version          # Need 20+
docker compose version    # Need v2.x
nvidia-smi               # Verify GPU

# If Docker not installed, see installation section below
```

---

### Step 1: Prepare Deployment Package

On your **local machine**:

```bash
cd /opt/kasaai/apps/tts-deployment

# Create complete deployment package with both services
tar czf runpod-tts-complete.tar.gz \
  docker/f5tts/app.py \
  docker/f5tts/Dockerfile \
  docker/styletts2/app.py \
  docker/styletts2/Dockerfile \
  docker/styletts2/requirements.txt \
  docker-compose.runpod.yml

# Verify package
ls -lh runpod-tts-complete.tar.gz
```

---

### Step 2: Transfer to RunPod

```bash
# Transfer deployment package
scp -P 22130 runpod-tts-complete.tar.gz root@194.68.245.121:/workspace/

# Verify transfer
ssh -p 22130 root@194.68.245.121 "ls -lh /workspace/runpod-tts-complete.tar.gz"
```

---

### Step 3: Extract on RunPod

```bash
# SSH to RunPod
ssh -p 22130 root@194.68.245.121

# Extract files
cd /workspace
tar xzf runpod-tts-complete.tar.gz

# Verify structure
ls -la docker/f5tts/
ls -la docker/styletts2/
ls -la docker-compose.runpod.yml
```

Expected structure:
```
/workspace/
├── docker/
│   ├── f5tts/
│   │   ├── app.py
│   │   └── Dockerfile
│   └── styletts2/
│       ├── app.py
│       ├── Dockerfile
│       └── requirements.txt
└── docker-compose.runpod.yml
```

---

### Step 4: Build Docker Images

This will take **20-40 minutes** for both services:

```bash
cd /workspace

# Option A: Build both services (recommended)
docker compose -f docker-compose.runpod.yml build f5tts styletts

# Option B: Build individually
docker compose -f docker-compose.runpod.yml build f5tts
docker compose -f docker-compose.runpod.yml build styletts

# Watch build progress
# F5-TTS: ~15-20 minutes (clones repo, installs deps)
# StyleTTS2: ~10-20 minutes (installs styletts2 package)
```

**Build Process:**
- Downloads CUDA base image (~2GB)
- Installs system dependencies
- Installs PyTorch with CUDA support
- Installs service-specific dependencies
- Copies application code

---

### Step 5: Stop Existing Services (If Running)

If F5-TTS is running via direct Python:

```bash
# Find F5-TTS process
ps aux | grep "python.*app.py" | grep f5

# Stop it (replace PID with actual process ID)
kill <PID>

# Or if running via nohup
pkill -f "python.*f5.*app.py"
```

---

### Step 6: Start Services via Docker

```bash
cd /workspace

# Option A: Start both services
docker compose -f docker-compose.runpod.yml up -d f5tts styletts

# Option B: Start individually
docker compose -f docker-compose.runpod.yml up -d f5tts
docker compose -f docker-compose.runpod.yml up -d styletts

# Check status
docker compose -f docker-compose.runpod.yml ps

# Expected output:
# NAME      IMAGE              STATUS         PORTS
# f5tts     f5tts:latest       Up X seconds   0.0.0.0:8002->8002/tcp
# styletts  styletts2:latest   Up X seconds   0.0.0.0:8006->8006/tcp
```

---

### Step 7: Monitor Startup

```bash
# Watch logs for both services
docker compose -f docker-compose.runpod.yml logs -f

# Or watch individually
docker compose -f docker-compose.runpod.yml logs -f f5tts
docker compose -f docker-compose.runpod.yml logs -f styletts

# Wait for startup messages:
# F5-TTS: "F5-TTS model loaded successfully"
# StyleTTS2: "StyleTTS2 model loaded successfully"
# Both: "Uvicorn running on http://0.0.0.0:XXXX"
```

Press **Ctrl+C** to stop watching logs (containers keep running).

---

### Step 8: Verify Deployment

#### Test F5-TTS
```bash
# Health check
curl http://localhost:8002/health

# Expected response:
{
  "status": "healthy",
  "device": "cuda",
  "model_loaded": true,
  "gpu_name": "NVIDIA A40"
}

# Test synthesis
curl -X POST http://localhost:8002/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Testing F5-TTS Docker deployment"}' \
  --output f5_test.wav
```

#### Test StyleTTS2
```bash
# Health check
curl http://localhost:8006/health

# Expected response:
{
  "status": "healthy",
  "device": "cuda",
  "model_loaded": true,
  "gpu_name": "NVIDIA A40"
}

# Test synthesis
curl -X POST http://localhost:8006/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Testing StyleTTS2 Docker deployment"}' \
  --output styletts2_test.wav
```

#### Check GPU Usage
```bash
nvidia-smi

# Should show both containers using GPU memory:
# - F5-TTS: ~700MB
# - StyleTTS2: ~4GB
# - Total: ~4.7GB / 46GB
```

---

## 🔧 Container Management

### View Status
```bash
# All services
docker compose -f docker-compose.runpod.yml ps

# Detailed info
docker ps
```

### View Logs
```bash
# Both services
docker compose -f docker-compose.runpod.yml logs -f

# F5-TTS only
docker compose -f docker-compose.runpod.yml logs -f f5tts

# StyleTTS2 only
docker compose -f docker-compose.runpod.yml logs -f styletts

# Last 100 lines
docker compose -f docker-compose.runpod.yml logs --tail=100
```

### Restart Services
```bash
# Restart both
docker compose -f docker-compose.runpod.yml restart

# Restart individually
docker compose -f docker-compose.runpod.yml restart f5tts
docker compose -f docker-compose.runpod.yml restart styletts
```

### Stop Services
```bash
# Stop both
docker compose -f docker-compose.runpod.yml stop

# Stop individually
docker compose -f docker-compose.runpod.yml stop f5tts
docker compose -f docker-compose.runpod.yml stop styletts
```

### Start Services
```bash
# Start both
docker compose -f docker-compose.runpod.yml start

# Start individually
docker compose -f docker-compose.runpod.yml start f5tts
docker compose -f docker-compose.runpod.yml start styletts
```

### Remove Containers
```bash
# Stop and remove
docker compose -f docker-compose.runpod.yml down

# Remove with volumes (clears model cache)
docker compose -f docker-compose.runpod.yml down -v
```

---

## 🔄 Updates and Maintenance

### Update Code

When you update app.py locally:

```bash
# 1. On local machine - update files
cd /opt/kasaai/apps/tts-deployment
# Edit docker/f5tts/app.py or docker/styletts2/app.py

# 2. Create new package
tar czf runpod-tts-complete.tar.gz \
  docker/f5tts/ \
  docker/styletts2/ \
  docker-compose.runpod.yml

# 3. Transfer to RunPod
scp -P 22130 runpod-tts-complete.tar.gz root@194.68.245.121:/workspace/

# 4. On RunPod - extract and rebuild
cd /workspace
tar xzf runpod-tts-complete.tar.gz
docker compose -f docker-compose.runpod.yml build f5tts styletts
docker compose -f docker-compose.runpod.yml up -d
```

### Update Dependencies

```bash
# Update requirements.txt locally, then follow Update Code process
```

---

## 📊 Resource Usage

### Expected VRAM Usage
```
F5-TTS:      ~0.7GB
StyleTTS2:   ~4.0GB
------------------
Total:       ~4.7GB / 46GB (10% utilization)
```

### Disk Space
```
CUDA base image:     ~2GB
F5-TTS image:        ~8GB
StyleTTS2 image:     ~8-10GB
Model caches:        ~2-3GB
------------------
Total:               ~20-23GB
```

### Monitor Resources
```bash
# GPU usage
nvidia-smi

# Container stats
docker stats

# Disk usage
docker system df
du -sh /var/lib/docker
```

---

## 🚨 Troubleshooting

### Containers Won't Start

```bash
# Check logs
docker compose -f docker-compose.runpod.yml logs

# Common issues:
# 1. Port already in use
lsof -i :8002
lsof -i :8006

# 2. GPU not accessible
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# 3. Out of disk space
df -h
docker system prune -a
```

### Model Loading Fails

```bash
# Clear cache and restart
docker compose -f docker-compose.runpod.yml down -v
docker compose -f docker-compose.runpod.yml up -d

# Check logs for specific errors
docker compose -f docker-compose.runpod.yml logs -f
```

### API Errors

```bash
# Test health endpoints
curl http://localhost:8002/health
curl http://localhost:8006/health

# Check container status
docker compose -f docker-compose.runpod.yml ps

# Restart if needed
docker compose -f docker-compose.runpod.yml restart
```

---

## 🔐 Docker Installation (If Needed)

If Docker is not installed on RunPod:

```bash
# Update system
apt-get update && apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt-get install -y docker-compose-plugin

# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  tee /etc/apt/sources.list.d/nvidia-docker.list

apt-get update
apt-get install -y nvidia-container-toolkit

# Configure Docker runtime
nvidia-ctk runtime configure --runtime=docker
systemctl restart docker

# Verify GPU access
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

---

## ✅ Post-Deployment Checklist

### F5-TTS
- [ ] Container builds successfully
- [ ] Container starts and runs
- [ ] Health endpoint returns healthy
- [ ] GPU accessible
- [ ] Synthesis works
- [ ] Voice cloning works
- [ ] Auto-restart configured

### StyleTTS2
- [ ] Container builds successfully
- [ ] Container starts and runs
- [ ] Health endpoint returns healthy
- [ ] GPU accessible
- [ ] Synthesis works
- [ ] Voice cloning works
- [ ] Style parameters work
- [ ] Auto-restart configured

### Frontend
- [ ] Update F5-TTS status to 'online'
- [ ] Update StyleTTS2 status to 'online'
- [ ] Rebuild b2c-portal
- [ ] Test from TTS Lab UI
- [ ] Test all style controls

---

## 📝 Quick Reference

### Both Services
```bash
# Start both
docker compose -f docker-compose.runpod.yml up -d

# Stop both
docker compose -f docker-compose.runpod.yml stop

# Restart both
docker compose -f docker-compose.runpod.yml restart

# Logs for both
docker compose -f docker-compose.runpod.yml logs -f

# Status
docker compose -f docker-compose.runpod.yml ps
```

### Individual Services
```bash
# F5-TTS
docker compose -f docker-compose.runpod.yml up -d f5tts
docker compose -f docker-compose.runpod.yml logs -f f5tts
curl http://localhost:8002/health

# StyleTTS2
docker compose -f docker-compose.runpod.yml up -d styletts
docker compose -f docker-compose.runpod.yml logs -f styletts
curl http://localhost:8006/health
```

---

## 🎯 Migration from Direct Python to Docker

If F5-TTS is currently running via direct Python:

### 1. Stop Python Process
```bash
pkill -f "python.*f5.*app.py"
```

### 2. Deploy via Docker
```bash
docker compose -f docker-compose.runpod.yml up -d f5tts
```

### 3. Verify Works
```bash
curl http://localhost:8002/health
```

### Benefits of Migration
- ✅ Auto-restart on crash
- ✅ Easy updates
- ✅ Consistent with StyleTTS2
- ✅ Production-ready
- ✅ Pod migration ready

---

## 🎊 Summary

**Both F5-TTS and StyleTTS2 are ready for Docker deployment!**

### Current State
- ✅ F5-TTS: Dockerfile ready, running via Python
- ✅ StyleTTS2: Dockerfile ready, not deployed yet

### Recommended Next Steps
1. Deploy both via Docker Compose
2. Migrate F5-TTS from Python to Docker
3. Deploy StyleTTS2 via Docker
4. Test both services
5. Update frontend status
6. Monitor production

**Total Deployment Time:** ~45-60 minutes (including builds)
**Production Ready:** ✅ Yes - with full Docker benefits
