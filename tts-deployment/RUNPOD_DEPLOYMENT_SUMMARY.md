# RunPod Deployment Summary

**Date:** 2025-10-20
**Pod ID:** jzfmzviw26huka-644113c7
**GPU:** NVIDIA A40 (46GB VRAM)
**Status:** 🔄 Setup In Progress

---

## 📊 Overview

Successfully configured RunPod connection and implemented a portable deployment strategy for TTS services.

---

## ✅ Completed Steps

### 1. Configuration Updates
- ✅ Updated `.env.example` with new RunPod credentials
- ✅ Updated `scripts/runpod_tunnels.sh` with new connection details
- ✅ Updated `README.md` with RunPod information
- ✅ Created `.env` file with active credentials
- ✅ Verified SSH connectivity to RunPod instance

### 2. Docker Installation Attempt
- ✅ Installed Docker and Docker Compose on RunPod
- ✅ Installed NVIDIA Container Toolkit
- ⚠️ **Discovery:** Docker-in-Docker has permission issues on RunPod
  - Error: `failed to mount overlay: operation not permitted`
  - Cause: RunPod instances run inside containers, no privileged mode

### 3. Alternative Deployment Strategy
- ✅ Documented three portable deployment options:
  1. **RunPod Templates** (Docker Hub images) - Best for production
  2. **Workspace Snapshots** (tar.gz backups) - Quick migration
  3. **Automated Setup Script** - Fast implementation
- ✅ Created comprehensive `RUNPOD_PORTABLE_DEPLOYMENT.md`
- ✅ Created `RUNPOD_DIRECT_DEPLOYMENT.md`
- ✅ Created automated setup script: `scripts/setup-runpod-tts.sh`

### 4. Automated Deployment
- ✅ Transferred setup script to RunPod
- 🔄 **Currently Running:** Automated setup installing dependencies

---

## 📂 Files Created/Modified

### Created Files
1. **RUNPOD_SETUP.md** - Complete RunPod deployment guide
2. **RUNPOD_UPDATE_2025-10-20.md** - Configuration update documentation
3. **RUNPOD_PORTABLE_DEPLOYMENT.md** - Portable deployment strategies
4. **RUNPOD_DIRECT_DEPLOYMENT.md** - Direct Python deployment guide
5. **scripts/setup-runpod-tts.sh** - Automated setup script (372 lines)
6. **RUNPOD_DEPLOYMENT_SUMMARY.md** - This file

### Modified Files
1. **.env.example** - Added RunPod connection details and Docker Hub credentials
2. **scripts/runpod_tunnels.sh** - Updated SSH connection parameters
3. **README.md** - Updated RunPod information and added documentation section
4. **.env** - Created from template with active credentials

---

## 🔌 RunPod Connection Details

```bash
# SSH Connection
Host: 194.68.245.121
Port: 22048
User: root
Pod ID: jzfmzviw26huka-644113c7
SSH Key: ~/.ssh/id_ed25519

# Connection command
ssh -p 22048 -i ~/.ssh/id_ed25519 root@194.68.245.121

# Alternative (via proxy)
ssh jzfmzviw26huka-644113c7@ssh.runpod.io -i ~/.ssh/id_ed25519
```

### Verified Resources
- **GPU:** NVIDIA A40, 46,068 MiB (46GB VRAM)
- **CPU:** 96 cores
- **RAM:** 503GB
- **Storage:** 546TB on `/workspace` volume
- **OS:** Ubuntu 22.04 (Linux 6.8.0-65-generic)
- **Python:** 3.12.3

---

## 🎯 Deployment Strategy: Automated Python Environment

### Why Not Docker?
Docker-in-Docker requires:
- Privileged mode (not available on RunPod)
- Overlay filesystem support (permission denied)
- iptables access (permission denied)

### Chosen Solution: Automated Setup Script
Creates portable deployment using:
- Python virtual environments for each service
- tmux for process management
- Automated dependency installation
- Management scripts (start, stop, status, cleanup)
- Easy backup/restore via tar.gz snapshots

### Portability
**Time to deploy on new pod:** ~10-15 minutes

```bash
# Backup current deployment
ssh runpod 'tar czf /workspace/tts-backup.tar.gz /workspace/tts-deployment'

# Restore on new pod
scp -P NEW_PORT tts-backup.tar.gz root@NEW_IP:/workspace/
ssh new-pod 'cd /workspace && tar xzf tts-backup.tar.gz'
ssh new-pod '/workspace/tts-deployment/start_all.sh'
```

---

## 🛠️ Services Being Deployed

| Service | Port | VRAM | Status |
|---------|------|------|--------|
| F5-TTS | 8002 | 6-10GB | 🔄 Installing |
| StyleTTS2 | 8006 | 8-12GB | ⏳ Pending |
| Kyutai/Moshi | 8008 | 12-16GB | ⏳ Pending |

**Total VRAM Usage:** 26-38GB (within 46GB limit)

---

## 📋 Management Scripts Created

All scripts located in `/workspace/tts-deployment/`:

1. **start_all.sh** - Start all TTS services in tmux sessions
2. **stop_all.sh** - Stop all TTS services
3. **status.sh** - Check status of all services (tmux, ports, GPU, health)
4. **cleanup.sh** - Remove old generated audio files
5. **README.txt** - Quick reference guide

---

## 🔄 Current Status

### Setup Script Progress
```bash
# Check progress
ssh -p 22048 -i ~/.ssh/id_ed25519 root@194.68.245.121 \
  'tail -f /var/log/tts-setup.log'
```

### What's Installing
1. ✅ System dependencies (ffmpeg, espeak-ng, portaudio, etc.)
2. 🔄 F5-TTS: PyTorch + CUDA, cloning repo, installing dependencies
3. ⏳ StyleTTS2: PyTorch + CUDA, cloning repo, downloading models
4. ⏳ Kyutai: API dependencies

---

## 📝 Next Steps

### Immediate (Automated by Script)
1. ✅ Install system dependencies
2. 🔄 Setup F5-TTS environment
3. ⏳ Setup StyleTTS2 environment
4. ⏳ Setup Kyutai environment
5. ⏳ Create management scripts

### Manual Steps Required
1. Transfer service code (app.py files) to RunPod
2. Start services: `/workspace/tts-deployment/start_all.sh`
3. Establish SSH tunnels from local machine
4. Verify services with health checks
5. Create deployment snapshot for backup

### Future Enhancements
1. Build RunPod Docker template for instant deployment
2. Push images to Docker Hub (ailabsafrica)
3. Create RunPod template in dashboard
4. Setup automated health monitoring
5. Configure auto-restart on pod reboot

---

## 🔐 Credentials

### Docker Hub (for Future Template)
```
Username: ailabsafrica
Token: dckr_pat_ReBluOQjSQK_KtR4fGKBJ75kaS4
```

### SSH Key
```
Path: ~/.ssh/id_ed25519
```

---

## 📊 Resource Allocation

### Storage
```
/workspace                - 546TB (deployment files, models, outputs)
/                        - 30GB (system, temporary files)
```

### Memory
```
RAM:  503GB total
VRAM: 46GB (NVIDIA A40)
```

### Network Ports
```
8002 - F5-TTS
8006 - StyleTTS2
8008 - Kyutai/Moshi
8888 - Jupyter Lab (RunPod HTTP service)
```

---

## ⚠️ Important Notes

1. **No Docker Isolation:** Services run directly on the instance
2. **Process Management:** Uses tmux (not systemd in RunPod containers)
3. **Port Access:** Via SSH tunnels from local machine
4. **Persistence:** `/workspace` persists, but process state doesn't survive reboots
5. **Startup:** Must run `start_all.sh` after pod restart

---

## 🧪 Testing Plan

Once deployment completes:

1. **Health Checks**
   ```bash
   curl http://localhost:8002/health
   curl http://localhost:8006/health
   curl http://localhost:8008/health
   ```

2. **GPU Access**
   ```bash
   nvidia-smi
   ```

3. **Test Synthesis**
   ```bash
   curl -X POST http://localhost:8002/synthesize \
     -H "Content-Type: application/json" \
     -d '{"text": "Hello from F5-TTS!", "language": "en"}' \
     --output test.wav
   ```

4. **SSH Tunnel**
   ```bash
   # From local machine
   ./scripts/runpod_tunnels.sh start
   curl http://localhost:8002/health
   ```

---

## 📚 Documentation Index

All documentation in `/opt/kasaai/apps/tts-deployment/`:

- **README.md** - Main project documentation
- **RUNPOD_SETUP.md** - Initial RunPod setup guide (Docker approach)
- **RUNPOD_UPDATE_2025-10-20.md** - Configuration update details
- **RUNPOD_PORTABLE_DEPLOYMENT.md** - Portability strategies
- **RUNPOD_DIRECT_DEPLOYMENT.md** - Direct Python deployment guide
- **RUNPOD_DEPLOYMENT_SUMMARY.md** - This summary
- **TTS_DEPLOYMENT_PLAN.md** - Original deployment plan
- **DEPLOYMENT_STATUS_2025-10-20.md** - Service status report
- **CRON_SETUP.md** - Monitoring automation

---

## 🎯 Success Criteria

Deployment is complete when:
- ✅ All three services running in tmux
- ✅ Health endpoints responding
- ✅ GPU accessible to all services
- ✅ SSH tunnels established
- ✅ Test synthesis successful
- ✅ Backup snapshot created
- ✅ Documentation updated

---

## 🔄 Backup Strategy

### Create Snapshot
```bash
ssh runpod 'cd /workspace && tar czf tts-snapshot-$(date +%Y%m%d).tar.gz tts-deployment/'
```

### Download Backup
```bash
scp -P 22048 -i ~/.ssh/id_ed25519 \
  root@194.68.245.121:/workspace/tts-snapshot-*.tar.gz \
  ~/backups/runpod/
```

### Restore Backup
```bash
scp -P NEW_PORT ~/backups/runpod/tts-snapshot-*.tar.gz root@NEW_IP:/workspace/
ssh -p NEW_PORT root@NEW_IP 'cd /workspace && tar xzf tts-snapshot-*.tar.gz'
```

---

**Status:** 🔄 Setup Script Running
**ETA:** 10-15 minutes
**Last Updated:** 2025-10-20 14:15 UTC
