# StyleTTS2 Docker Deployment Guide - Production Ready

**Date:** 2025-10-21
**Deployment Type:** Docker Compose (Production)
**Status:** ✅ Ready for deployment

---

## 🎯 Why Docker?

### Production Benefits
- ✅ **Reproducible** - Same environment every time
- ✅ **Portable** - Works on any RunPod instance
- ✅ **Isolated** - No dependency conflicts
- ✅ **Auto-restart** - Crashes are handled automatically
- ✅ **Easy updates** - Just rebuild and redeploy
- ✅ **Version controlled** - Images are tagged and versioned

### Operational Benefits
- ✅ **Easy scaling** - Add more instances with one command
- ✅ **Resource limits** - Control GPU/CPU/memory allocation
- ✅ **Monitoring** - Built-in health checks
- ✅ **Logging** - Centralized via Docker
- ✅ **Rollback** - Easy to revert to previous version

---

## 📦 Deployment Package

**Package:** `/opt/kasaai/apps/tts-deployment/runpod-styletts2-deploy.tar.gz`

**Contents:**
- `docker/styletts2/app.py` - FastAPI server
- `docker/styletts2/Dockerfile` - Build configuration
- `docker/styletts2/requirements.txt` - Python dependencies
- `docker-compose.runpod.yml` - Orchestration config

**Size:** ~3.6KB (compressed)

---

## 🚀 Step-by-Step Deployment

### Prerequisites

Verify these are installed on RunPod:
```bash
docker --version          # Should show Docker 20+
docker compose version    # Should show v2.x
nvidia-smi               # Should show NVIDIA A40
```

If Docker is not installed, see [Installation Steps](#docker-installation) below.

---

### Step 1: Transfer Deployment Package

From your **local machine**:

```bash
# Option A: Direct connection (preferred)
scp -P 22130 \
  /opt/kasaai/apps/tts-deployment/runpod-styletts2-deploy.tar.gz \
  root@194.68.245.121:/workspace/

# Option B: Via SSH proxy (if direct fails)
scp -o ControlPath=/home/dev/.ssh/controlmasters/jzfmzviw26huka-644113c7@ssh.runpod.io:22 \
  /opt/kasaai/apps/tts-deployment/runpod-styletts2-deploy.tar.gz \
  jzfmzviw26huka-644113c7@ssh.runpod.io:/workspace/
```

**Verify upload:**
```bash
ssh -p 22130 root@194.68.245.121 "ls -lh /workspace/runpod-styletts2-deploy.tar.gz"
```

---

### Step 2: Extract Files on RunPod

SSH into RunPod:
```bash
ssh -p 22130 root@194.68.245.121
```

Extract the deployment package:
```bash
cd /workspace
tar xzf runpod-styletts2-deploy.tar.gz

# Verify extraction
ls -la docker/styletts2/
ls -la docker-compose.runpod.yml
```

Expected output:
```
docker/styletts2/
├── app.py
├── Dockerfile
└── requirements.txt

docker-compose.runpod.yml
```

---

### Step 3: Build StyleTTS2 Docker Image

This will take **10-20 minutes** (downloads CUDA images, installs dependencies):

```bash
cd /workspace

# Build only StyleTTS2 (not F5-TTS or Kyutai)
docker compose -f docker-compose.runpod.yml build styletts

# Watch the build process
# You'll see:
# - CUDA base image download (~2GB)
# - System packages installation
# - PyTorch installation
# - StyleTTS2 package installation
```

**Monitor build progress:**
The build will show each Dockerfile step. Key steps:
1. `FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04` - Base image
2. `RUN apt-get install...` - System dependencies
3. `RUN pip3 install torch...` - PyTorch with CUDA
4. `RUN pip3 install -r requirements.txt` - StyleTTS2 and deps
5. `COPY app.py` - Application code

**Expected build time:** 10-20 minutes (first time)

---

### Step 4: Start StyleTTS2 Container

```bash
# Start StyleTTS2 in detached mode
docker compose -f docker-compose.runpod.yml up -d styletts

# Check status
docker compose -f docker-compose.runpod.yml ps

# Expected output:
# NAME       IMAGE              STATUS         PORTS
# styletts   styletts2:latest   Up X seconds   0.0.0.0:8006->8006/tcp
```

**View startup logs:**
```bash
docker compose -f docker-compose.runpod.yml logs -f styletts

# Watch for:
# "Loading StyleTTS2 model..."
# "StyleTTS2 model loaded successfully"
# "Application startup complete"
# "Uvicorn running on http://0.0.0.0:8006"
```

**Press Ctrl+C to stop watching logs** (container keeps running).

---

### Step 5: Verify Deployment

#### 5.1 Health Check
```bash
curl http://localhost:8006/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "device": "cuda",
  "model_loaded": true,
  "gpu_name": "NVIDIA A40",
  "gpu_memory_allocated_gb": "3.XX",
  "gpu_memory_total_gb": "45.XX"
}
```

#### 5.2 Languages Check
```bash
curl http://localhost:8006/languages
```

**Expected response:**
```json
{
  "languages": [
    {"code": "en", "name": "English"}
  ],
  "note": "StyleTTS2 is primarily trained on English..."
}
```

#### 5.3 GPU Stats
```bash
curl http://localhost:8006/gpu_stats
```

**Expected response:**
```json
{
  "device_count": 1,
  "current_device": 0,
  "device_name": "NVIDIA A40",
  "memory_allocated_gb": 3.XX,
  "memory_reserved_gb": 4.XX,
  "memory_total_gb": 45.XX
}
```

#### 5.4 Test Synthesis
```bash
curl -X POST http://localhost:8006/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, this is StyleTTS2 speaking from a Docker container",
    "alpha": 0.3,
    "beta": 0.7,
    "diffusion_steps": 5
  }' \
  --output test_docker.wav

# Check the file
ls -lh test_docker.wav
file test_docker.wav

# Expected: WAV audio file, ~100-500KB
```

---

### Step 6: Test Voice Cloning

You'll need a reference audio file. If you have access to the voice library:

```bash
# Example with a short test file (create a test file first)
curl -X POST http://localhost:8006/clone \
  -F "text=This is a test of voice cloning with StyleTTS2 in Docker" \
  -F "reference_audio=@/path/to/reference.wav" \
  -F "alpha=0.3" \
  -F "beta=0.7" \
  -F "diffusion_steps=5" \
  -F "embedding_scale=1.0" \
  --output cloned_docker.wav

# Verify output
ls -lh cloned_docker.wav
```

---

## 🔧 Container Management

### View Logs
```bash
# Follow logs in real-time
docker compose -f docker-compose.runpod.yml logs -f styletts

# View last 100 lines
docker compose -f docker-compose.runpod.yml logs --tail=100 styletts

# View logs since 1 hour ago
docker compose -f docker-compose.runpod.yml logs --since 1h styletts
```

### Restart Container
```bash
docker compose -f docker-compose.runpod.yml restart styletts
```

### Stop Container
```bash
docker compose -f docker-compose.runpod.yml stop styletts
```

### Start Container
```bash
docker compose -f docker-compose.runpod.yml start styletts
```

### Rebuild and Restart (after code changes)
```bash
docker compose -f docker-compose.runpod.yml build styletts
docker compose -f docker-compose.runpod.yml up -d styletts
```

### Remove Container and Volumes
```bash
# Stop and remove container
docker compose -f docker-compose.runpod.yml down styletts

# Remove with volumes (clears model cache)
docker compose -f docker-compose.runpod.yml down -v styletts
```

### Execute Commands Inside Container
```bash
# Get a shell inside the container
docker exec -it styletts bash

# Check Python version
docker exec styletts python3 --version

# Check installed packages
docker exec styletts pip3 list | grep styletts2

# Check GPU access
docker exec styletts python3 -c "import torch; print(torch.cuda.is_available())"
```

---

## 📊 Monitoring

### Container Stats
```bash
# Real-time stats
docker stats styletts

# Shows:
# - CPU usage
# - Memory usage
# - Network I/O
# - GPU usage (if nvidia-docker configured)
```

### Check GPU Usage
```bash
# On host
nvidia-smi

# Inside container
docker exec styletts nvidia-smi
```

### Disk Usage
```bash
# Check image size
docker images | grep styletts

# Check volume usage
docker volume ls
docker volume inspect styletts_models
```

---

## 🔄 Updates and Maintenance

### Update Code
```bash
# 1. Update app.py locally in /opt/kasaai/apps/tts-deployment/docker/styletts2/

# 2. Create new deployment package
cd /opt/kasaai/apps/tts-deployment
tar czf runpod-styletts2-deploy.tar.gz \
  docker/styletts2/app.py \
  docker/styletts2/Dockerfile \
  docker/styletts2/requirements.txt \
  docker-compose.runpod.yml

# 3. Transfer to RunPod
scp -P 22130 runpod-styletts2-deploy.tar.gz root@194.68.245.121:/workspace/

# 4. On RunPod: Extract and rebuild
cd /workspace
tar xzf runpod-styletts2-deploy.tar.gz
docker compose -f docker-compose.runpod.yml build styletts
docker compose -f docker-compose.runpod.yml up -d styletts
```

### Update Dependencies
```bash
# 1. Update requirements.txt locally

# 2. Follow the Update Code process above
```

---

## 🚨 Troubleshooting

### Container Won't Start
```bash
# Check logs for errors
docker compose -f docker-compose.runpod.yml logs styletts

# Common issues:
# 1. Port 8006 already in use
docker ps -a | grep 8006
lsof -i :8006

# 2. GPU not available
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# 3. Out of disk space
df -h
docker system df
```

### Model Loading Fails
```bash
# Check if model cache is corrupted
docker exec styletts ls -la /root/.cache/styletts2/

# Clear cache and restart
docker compose -f docker-compose.runpod.yml down -v styletts
docker compose -f docker-compose.runpod.yml up -d styletts
```

### API Returns Errors
```bash
# Check health endpoint first
curl http://localhost:8006/health

# View recent logs
docker compose -f docker-compose.runpod.yml logs --tail=50 styletts

# Check container is actually running
docker compose -f docker-compose.runpod.yml ps styletts
```

### Out of GPU Memory
```bash
# Check GPU usage
nvidia-smi

# If multiple services running, stop others
docker compose -f docker-compose.runpod.yml stop f5tts kyutai

# Restart StyleTTS2
docker compose -f docker-compose.runpod.yml restart styletts
```

---

## 🔐 Docker Installation (If Needed)

If Docker is not installed on your RunPod instance:

```bash
# Update system
apt-get update && apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt-get install -y docker-compose-plugin

# Verify installation
docker --version
docker compose version

# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  tee /etc/apt/sources.list.d/nvidia-docker.list

apt-get update
apt-get install -y nvidia-container-toolkit

# Configure Docker to use NVIDIA runtime
nvidia-ctk runtime configure --runtime=docker
systemctl restart docker

# Verify GPU access
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

---

## 📈 Expected Performance

| Metric | Value |
|--------|-------|
| **Container Size** | ~8-10GB (includes CUDA runtime, PyTorch, StyleTTS2) |
| **Startup Time** | 30-60 seconds (model loading) |
| **VRAM Usage** | ~4GB (during inference) |
| **Inference Time** | 3-8 seconds (depends on diffusion_steps) |
| **Max Concurrent Requests** | 1-2 (limited by GPU) |

---

## ✅ Post-Deployment Checklist

- [ ] Container builds successfully
- [ ] Container starts and stays running
- [ ] `/health` endpoint returns "healthy"
- [ ] GPU is accessible (check `/gpu_stats`)
- [ ] Basic synthesis works (`/synthesize`)
- [ ] Voice cloning works (`/clone`)
- [ ] Logs show no errors
- [ ] Container auto-restarts after crash
- [ ] Update frontend status to 'online'
- [ ] Test from TTS Lab UI

---

## 🎯 Next Steps After Deployment

1. **Update Frontend Status**
   ```typescript
   // apps/b2c-portal/src/config/tts-providers.ts
   styletts2: {
     status: 'online',  // Change from 'building'
   }
   ```

2. **Rebuild Frontend**
   ```bash
   cd /opt/kasaai/apps/b2c-portal
   npm run build
   ```

3. **Test from UI**
   - Go to https://kasaai.ailabsafrica.com/tts-lab
   - Select StyleTTS2
   - Test voice cloning with Ghanaian voices
   - Adjust style parameters
   - Generate and download audio

4. **Monitor Production**
   - Set up log monitoring
   - Configure alerts for container crashes
   - Monitor GPU usage
   - Track API response times

---

## 📝 Quick Reference

**Start:** `docker compose -f docker-compose.runpod.yml up -d styletts`
**Stop:** `docker compose -f docker-compose.runpod.yml stop styletts`
**Logs:** `docker compose -f docker-compose.runpod.yml logs -f styletts`
**Restart:** `docker compose -f docker-compose.runpod.yml restart styletts`
**Rebuild:** `docker compose -f docker-compose.runpod.yml build styletts`
**Health:** `curl http://localhost:8006/health`

---

**Deployment Time:** ~30-40 minutes total (including build)
**Production Ready:** ✅ Yes - with auto-restart, health checks, and GPU support
