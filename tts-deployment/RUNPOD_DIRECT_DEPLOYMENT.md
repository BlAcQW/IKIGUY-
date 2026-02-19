# RunPod Direct Python Deployment Guide

**Date:** 2025-10-20
**Pod ID:** jzfmzviw26huka-644113c7
**GPU:** NVIDIA A40 (46GB VRAM)
**Status:** ⚠️ Docker-in-Docker Not Supported - Using Direct Python Deployment

---

## 🔴 Important Discovery

RunPod instances run inside Docker containers themselves, which means Docker-in-Docker requires privileged mode and special configuration that's not available by default. The standard approach of deploying via Docker Compose doesn't work on RunPod.

### Error Encountered
```
failed to mount overlay: operation not permitted
iptables v1.8.10 (nf_tables): Could not fetch rule set generation id: Permission denied
```

---

## ✅ Alternative Approach: Direct Python Deployment

Since RunPod provides direct GPU access and Python 3.12, we can deploy TTS services directly using Python virtual environments.

### Advantages
- Direct GPU access (no Docker overhead)
- Faster deployment (no image building)
- Better performance (native execution)
- Simpler troubleshooting

### Disadvantages
- Manual dependency management
- No container isolation
- Requires process management (systemd/supervisor/tmux)

---

## 📋 Deployment Steps

### 1. Verify Environment

```bash
# SSH into RunPod
ssh -p 22048 -i ~/.ssh/id_ed25519 root@194.68.245.121

# Check resources
python3 --version    # Python 3.12.3
nvidia-smi           # NVIDIA A40, 46GB VRAM
df -h /workspace     # 546TB storage available
```

### 2. Install System Dependencies

```bash
# Update system
apt-get update

# Install build tools and libraries
apt-get install -y \
  build-essential \
  python3-dev \
  python3-venv \
  git \
  ffmpeg \
  libsndfile1 \
  portaudio19-dev \
  espeak-ng

# Install PyTorch with CUDA support
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### 3. Deploy F5-TTS

```bash
cd /workspace/tts-deployment/f5tts

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Clone F5-TTS repository
git clone https://github.com/SWivid/F5-TTS.git
cd F5-TTS

# Install dependencies
pip install -e .
pip install fastapi uvicorn pydantic

# Copy and modify app.py
cp /workspace/tts-deployment/docker/f5tts/app.py ./

# Run service (in tmux/screen)
tmux new -s f5tts
uvicorn app:app --host 0.0.0.0 --port 8002
# Ctrl+B, D to detach
```

### 4. Deploy StyleTTS2

```bash
cd /workspace/tts-deployment/styletts2

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Clone StyleTTS2 repository
git clone https://github.com/yl4579/StyleTTS2.git
cd StyleTTS2

# Install dependencies
pip install -r requirements.txt
pip install fastapi uvicorn pydantic

# Download models
wget https://huggingface.co/yl4579/StyleTTS2-LibriTTS/resolve/main/Models/LibriTTS/epochs_2nd_00020.pth \
  -O Models/LibriTTS/epochs_2nd_00020.pth

# Copy and modify app.py
cp /workspace/tts-deployment/docker/styletts2/app.py ./

# Run service
tmux new -s styletts2
uvicorn app:app --host 0.0.0.0 --port 8006
# Ctrl+B, D to detach
```

### 5. Deploy Kyutai/Moshi

```bash
cd /workspace/tts-deployment/kyutai

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Moshi (when available)
# pip install moshi

# For now, run placeholder API
cp /workspace/tts-deployment/docker/kyutai/app.py ./
pip install fastapi uvicorn pydantic

# Run service
tmux new -s kyutai
uvicorn app:app --host 0.0.0.0 --port 8008
# Ctrl+B, D to detach
```

---

## 🔧 Process Management

### Using tmux (Recommended)

```bash
# List running sessions
tmux ls

# Attach to session
tmux attach -t f5tts

# Kill session
tmux kill-session -t f5tts

# Create startup script
cat > /workspace/tts-deployment/start_all.sh <<'EOF'
#!/bin/bash
cd /workspace/tts-deployment/f5tts/F5-TTS
tmux new -d -s f5tts "source ../venv/bin/activate && uvicorn app:app --host 0.0.0.0 --port 8002"

cd /workspace/tts-deployment/styletts2/StyleTTS2
tmux new -d -s styletts2 "source ../venv/bin/activate && uvicorn app:app --host 0.0.0.0 --port 8006"

cd /workspace/tts-deployment/kyutai
tmux new -d -s kyutai "source venv/bin/activate && uvicorn app:app --host 0.0.0.0 --port 8008"
EOF

chmod +x /workspace/tts-deployment/start_all.sh
```

### Using systemd (If Available)

Create service files in `/etc/systemd/system/`:

```ini
# /etc/systemd/system/f5tts.service
[Unit]
Description=F5-TTS Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/workspace/tts-deployment/f5tts/F5-TTS
Environment="PATH=/workspace/tts-deployment/f5tts/venv/bin"
ExecStart=/workspace/tts-deployment/f5tts/venv/bin/uvicorn app:app --host 0.0.0.0 --port 8002
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start services
systemctl enable f5tts styletts2 kyutai
systemctl start f5tts styletts2 kyutai

# Check status
systemctl status f5tts
```

---

## 🌐 SSH Tunnel Setup

From your local machine, establish SSH tunnels to access the services:

```bash
# Start tunnels (on local machine)
cd /opt/kasaai/apps/tts-deployment
./scripts/runpod_tunnels.sh start

# Test services
curl http://localhost:8002/health  # F5-TTS
curl http://localhost:8006/health  # StyleTTS2
curl http://localhost:8008/health  # Kyutai
```

---

## 📊 Monitoring

### Check Running Services

```bash
# List tmux sessions
tmux ls

# Check ports
netstat -tulpn | grep -E '8002|8006|8008'

# Check GPU usage
watch -n 1 nvidia-smi
```

### View Logs

```bash
# Attach to tmux session to see logs
tmux attach -t f5tts

# Or check service logs (if using systemd)
journalctl -u f5tts -f
```

---

## 🧪 Testing

### Health Checks

```bash
# From RunPod
curl http://localhost:8002/health
curl http://localhost:8006/health
curl http://localhost:8008/health

# From local machine (via tunnel)
curl http://localhost:8002/health
```

### Test Speech Synthesis

```bash
# F5-TTS
curl -X POST http://localhost:8002/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello from F5-TTS!", "language": "en"}' \
  --output /workspace/tts-deployment/outputs/test_f5.wav

# Check output
ls -lh /workspace/tts-deployment/outputs/test_f5.wav
```

---

## 💾 Storage Management

### Output Files

All generated audio files are stored in:
```
/workspace/tts-deployment/outputs/
```

### Cleanup Script

```bash
# Create cleanup script
cat > /workspace/tts-deployment/cleanup.sh <<'EOF'
#!/bin/bash
# Clean up audio files older than 24 hours
find /workspace/tts-deployment/outputs -name "*.wav" -mtime +1 -delete
echo "Cleaned up old audio files"
EOF

chmod +x /workspace/tts-deployment/cleanup.sh

# Add to crontab
echo "0 2 * * * /workspace/tts-deployment/cleanup.sh" | crontab -
```

---

## ⚠️ Limitations

1. **No Container Isolation:** All services run in the same environment
2. **Manual Management:** Requires manual process management
3. **Port Conflicts:** Ensure ports don't conflict with RunPod's internal services
4. **Persistence:** Services will stop if RunPod instance restarts (use startup scripts)

---

## 🔄 Startup Script for RunPod

Create `/workspace/startup.sh` to auto-start services on pod restart:

```bash
#!/bin/bash
# RunPod startup script

echo "Starting TTS services..."

# Start all TTS services in tmux
/workspace/tts-deployment/start_all.sh

echo "TTS services started"
echo "Check status with: tmux ls"
```

Make it executable:
```bash
chmod +x /workspace/startup.sh
```

---

## 📚 Service-Specific Notes

### F5-TTS
- Model size: ~2-4GB
- VRAM usage: 6-10GB
- First run downloads models to `~/.cache/huggingface`

### StyleTTS2
- Model size: ~1-2GB
- VRAM usage: 8-12GB
- Models stored in `Models/LibriTTS/`

### Kyutai/Moshi
- Currently placeholder API
- Awaiting official Python package
- VRAM usage: ~12-16GB (estimated)

---

## 🐛 Troubleshooting

### Service Won't Start

```bash
# Check if port is in use
netstat -tulpn | grep 8002

# Check Python dependencies
source /workspace/tts-deployment/f5tts/venv/bin/activate
python -c "import torch; print(torch.cuda.is_available())"

# Check GPU access
nvidia-smi
```

### Out of VRAM

```bash
# Stop services to free VRAM
tmux kill-session -t kyutai  # Stop least critical service first

# Check GPU memory
nvidia-smi
```

### tmux Sessions Lost

```bash
# Check if sessions exist
tmux ls

# Restart all services
/workspace/tts-deployment/start_all.sh
```

---

## 📖 Next Steps

1. **Complete Manual Deployment:**
   - Deploy F5-TTS with actual implementation
   - Deploy StyleTTS2 with models
   - Wait for Kyutai/Moshi Python package

2. **Automate Startup:**
   - Create robust startup scripts
   - Configure RunPod to run startup.sh on pod start

3. **Setup Monitoring:**
   - Health check endpoints
   - GPU usage monitoring
   - Disk space monitoring

4. **Document APIs:**
   - API schemas for each service
   - Example requests/responses
   - Integration guide

---

**Status:** 📝 Documentation Complete - Ready for Manual Deployment
**Last Updated:** 2025-10-20
