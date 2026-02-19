# RunPod Setup Guide

**Created:** 2025-10-20
**Last Updated:** 2025-10-21
**Pod ID:** jzfmzviw26huka-644113c7
**GPU:** NVIDIA A40 (46GB VRAM)
**Status:** ⚠️ Services need setup/reinstallation

---

## 🔌 Connection Details

### SSH over Direct TCP (Primary Method)
```bash
# Current connection (port updated from 22048 to 22130)
ssh root@194.68.245.121 -p 22130 -i ~/.ssh/id_ed25519
```

### SSH via Proxy (Alternative)
```bash
# If direct TCP connection fails
ssh jzfmzviw26huka-644113c7@ssh.runpod.io -i ~/.ssh/id_ed25519
```

### HTTP Services
- **Jupyter Lab:** Port 8888
- **Status:** Ready

---

## 🚀 Initial Setup

### 1. Verify Connection and GPU

```bash
# Test SSH connection (using current port 22130)
ssh -p 22130 -i ~/.ssh/id_ed25519 root@194.68.245.121 "echo 'Connected!' && nvidia-smi"

# Expected output: NVIDIA A40, 46068 MiB
```

### 2. Install Docker and Docker Compose

SSH into the RunPod instance and run:

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
systemctl restart docker

# Verify GPU access in Docker
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

### 3. Create Deployment Directory

```bash
# Create directory structure
mkdir -p /opt/kasaai/apps/tts-deployment
cd /opt/kasaai/apps/tts-deployment
```

### 4. Transfer Files to RunPod

From your local machine:

```bash
# Create archive of necessary files
cd /opt/kasaai/apps/tts-deployment
tar czf runpod-deploy.tar.gz \
  docker/f5tts/ \
  docker/styletts2/ \
  docker/kyutai/ \
  docker-compose.runpod.yml \
  .env

# Transfer to RunPod
scp -P 22130 -i ~/.ssh/id_ed25519 \
  runpod-deploy.tar.gz \
  root@194.68.245.121:/workspace/tts-deployment/

# SSH into RunPod and extract
ssh -p 22130 -i ~/.ssh/id_ed25519 root@194.68.245.121
cd /workspace/tts-deployment
tar xzf runpod-deploy.tar.gz
```

### 5. Build and Deploy Services

On the RunPod instance:

```bash
cd /opt/kasaai/apps/tts-deployment

# Build all images (this will take 20-40 minutes)
docker compose -f docker-compose.runpod.yml build

# Start services
docker compose -f docker-compose.runpod.yml up -d

# Check status
docker compose -f docker-compose.runpod.yml ps

# View logs
docker compose -f docker-compose.runpod.yml logs -f
```

---

## 🔧 Services on RunPod

| Service | Port | VRAM Usage | Status |
|---------|------|------------|--------|
| F5-TTS | 8002 | 6-10GB | Pending |
| StyleTTS2 | 8006 | 8-12GB | Pending |
| Kyutai/Moshi | 8008 | 12-16GB | Pending |

**Total Estimated VRAM:** 26-38GB (fits within 46GB A40)

---

## 🌐 SSH Tunnel Setup

From your local machine, establish SSH tunnels to access RunPod services:

```bash
# Start tunnels
cd /opt/kasaai/apps/tts-deployment
./scripts/runpod_tunnels.sh start

# Check status
./scripts/runpod_tunnels.sh status

# Test service access
curl http://localhost:8002/health  # F5-TTS
curl http://localhost:8006/health  # StyleTTS2
curl http://localhost:8008/health  # Kyutai/Moshi

# Stop tunnels
./scripts/runpod_tunnels.sh stop
```

---

## 📊 Monitoring

### GPU Usage
```bash
# From local machine (via SSH)
ssh -p 22130 -i ~/.ssh/id_ed25519 root@194.68.245.121 'watch -n 1 nvidia-smi'

# On RunPod instance
watch -n 1 nvidia-smi
```

### Docker Container Stats
```bash
# On RunPod instance
docker stats

# Specific service
docker stats f5tts styletts kyutai
```

### Service Logs
```bash
# All services
docker compose -f docker-compose.runpod.yml logs -f

# Specific service
docker compose -f docker-compose.runpod.yml logs -f f5tts
```

---

## 🔄 Management Commands

### Restart Services
```bash
# Restart all services
docker compose -f docker-compose.runpod.yml restart

# Restart specific service
docker compose -f docker-compose.runpod.yml restart f5tts
```

### Stop Services
```bash
# Stop all services
docker compose -f docker-compose.runpod.yml down

# Stop specific service
docker compose -f docker-compose.runpod.yml stop f5tts
```

### Rebuild Services
```bash
# Rebuild and restart specific service
docker compose -f docker-compose.runpod.yml up -d --build f5tts

# Rebuild from scratch (no cache)
docker compose -f docker-compose.runpod.yml build --no-cache f5tts
docker compose -f docker-compose.runpod.yml up -d f5tts
```

### Clean Up
```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove all stopped containers
docker container prune
```

---

## 🧪 Testing Services

### Health Checks
```bash
# Via SSH tunnel (from local machine)
curl http://localhost:8002/health
curl http://localhost:8006/health
curl http://localhost:8008/health

# Or directly on RunPod
ssh -p 22130 -i ~/.ssh/id_ed25519 root@194.68.245.121 \
  "curl http://localhost:8002/health"
```

### Test Speech Synthesis
```bash
# F5-TTS test
curl -X POST http://localhost:8002/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello from F5-TTS!", "language": "en"}' \
  --output test_f5.wav

# StyleTTS2 test
curl -X POST http://localhost:8006/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello from StyleTTS2!", "language": "en"}' \
  --output test_style.wav
```

---

## 🔒 Security Considerations

### SSH Key Management
```bash
# Ensure SSH key has correct permissions
chmod 600 ~/.ssh/id_ed25519

# Add host key to known_hosts (if not already done)
ssh-keyscan -p 22048 194.68.245.121 >> ~/.ssh/known_hosts
```

### Firewall Rules
The RunPod instance should have:
- Port 22048 open for SSH
- Port 8888 open for Jupyter Lab
- Internal ports 8002, 8006, 8008 for Docker services (accessed via SSH tunnel)

### Container Security
```bash
# Run containers as non-root user (recommended)
# Update Dockerfiles to include:
# USER nonroot

# Scan images for vulnerabilities
docker scan f5tts:latest
```

---

## 💾 Storage Management

### Check Disk Usage
```bash
# Overall disk usage
df -h

# Docker storage usage
docker system df -v

# Volume sizes
docker volume ls | grep tts-deployment
```

### Backup Volumes
```bash
# Backup F5-TTS checkpoints
docker run --rm -v tts-deployment_f5tts_ckpts:/data \
  -v $(pwd):/backup ubuntu tar czf /backup/f5tts_ckpts_backup.tar.gz /data

# Backup generated outputs
docker run --rm -v tts-deployment_f5tts_outputs:/data \
  -v $(pwd):/backup ubuntu tar czf /backup/f5tts_outputs_backup.tar.gz /data
```

---

## ⚠️ Troubleshooting

### Connection Issues

**Problem:** "Connection refused" or "Host key verification failed"
```bash
# Remove old host key (use current port 22130)
ssh-keygen -R "[194.68.245.121]:22130"

# Add new host key
ssh-keyscan -p 22130 194.68.245.121 >> ~/.ssh/known_hosts

# Test connection
ssh -v -p 22130 -i ~/.ssh/id_ed25519 root@194.68.245.121 "echo OK"
```

### Docker Issues

**Problem:** GPU not available in container
```bash
# Verify NVIDIA runtime
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# Check Docker daemon config
cat /etc/docker/daemon.json
# Should contain nvidia runtime configuration

# Restart Docker
systemctl restart docker
```

**Problem:** Container won't start
```bash
# Check logs
docker compose -f docker-compose.runpod.yml logs f5tts

# Check if port is in use
netstat -tulpn | grep 8002

# Rebuild from scratch
docker compose -f docker-compose.runpod.yml down
docker compose -f docker-compose.runpod.yml build --no-cache f5tts
docker compose -f docker-compose.runpod.yml up -d f5tts
```

### Out of VRAM
```bash
# Check GPU memory
nvidia-smi

# Stop services to free VRAM
docker compose -f docker-compose.runpod.yml stop kyutai

# Adjust model parameters in docker/*/app.py if needed
```

### SSH Tunnel Issues

**Problem:** Tunnel disconnects frequently
```bash
# Use autossh for persistent tunnels
apt-get install autossh

# Modified tunnel command with autossh
autossh -M 0 -N \
  -o ServerAliveInterval=60 \
  -o ServerAliveCountMax=3 \
  -L 8002:localhost:8002 \
  -L 8006:localhost:8006 \
  -L 8008:localhost:8008 \
  -p 22130 -i ~/.ssh/id_ed25519 \
  root@194.68.245.121
```

---

## 📝 Environment Variables

The `.env` file on RunPod should contain:

```bash
# GPU Configuration
CUDA_VISIBLE_DEVICES=0
NVIDIA_VISIBLE_DEVICES=all

# Storage
STORAGE_TYPE=local
STORAGE_BASE_PATH=/app/outputs

# Logging
LOG_LEVEL=info

# Performance
MAX_CONCURRENT_REQUESTS=5
REQUEST_TIMEOUT_SECONDS=300
```

---

## 🔄 Updates and Maintenance

### Update Services
```bash
# On local machine: create updated archive
cd /opt/kasaai/apps/tts-deployment
tar czf runpod-update.tar.gz docker/ docker-compose.runpod.yml

# Transfer to RunPod
scp -P 22130 -i ~/.ssh/id_ed25519 \
  runpod-update.tar.gz \
  root@194.68.245.121:/workspace/tts-deployment/

# On RunPod: extract and rebuild
cd /workspace/tts-deployment
tar xzf runpod-update.tar.gz
docker compose -f docker-compose.runpod.yml build
docker compose -f docker-compose.runpod.yml up -d
```

### Scheduled Cleanup
```bash
# Add to crontab on RunPod
crontab -e

# Add line to clean up old files daily at 2 AM
0 2 * * * cd /opt/kasaai/apps/tts-deployment && docker exec f5tts curl -X DELETE http://localhost:8002/cleanup
0 2 * * * cd /opt/kasaai/apps/tts-deployment && docker exec styletts curl -X DELETE http://localhost:8006/cleanup
0 2 * * * cd /opt/kasaai/apps/tts-deployment && docker exec kyutai curl -X DELETE http://localhost:8008/cleanup
```

---

## 📞 Quick Reference

### Connection String
```bash
ssh root@194.68.245.121 -p 22130 -i ~/.ssh/id_ed25519
```

### Pod Information
- **Pod ID:** jzfmzviw26huka-644113c7
- **GPU:** NVIDIA A40 (46GB VRAM)
- **OS:** Ubuntu 22.04
- **Location:** RunPod Cloud
- **SSH Port:** 22130 (updated from 22048)

### Service Ports
- F5-TTS: 8002
- StyleTTS2: 8006
- Kyutai/Moshi: 8008
- Jupyter Lab: 8888

### Deployment Path
```
/workspace/tts-deployment/
```

### Current Status (2025-10-21)
- ✅ SSH connection active
- ⚠️ Docker not found in PATH
- ⚠️ Services need proper setup/reinstallation
- ℹ️ Workspace directory exists at /workspace/tts-deployment/
- ℹ️ Only F5-TTS docker files present, StyleTTS2 missing

---

**Last Updated:** 2025-10-21
**Status:** ⚠️ Requires service setup - Docker/services not properly configured
