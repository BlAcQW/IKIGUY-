# RunPod Setup Summary

**Date:** November 8, 2025
**Server:** 194.68.245.121:22153
**Pod ID:** jzfmzviw26huka-644113c7

---

## ✅ Setup Complete

### 1. StyleTTS2 Deployment

**Location:**
- **Local (Dev):** `/opt/kasaai/apps/tts-deployment/docker/styletts2/` (source code only)
- **RunPod (Production):** `/workspace/tts-deployment/docker/styletts2/` (running service)

**Status:**
```
✅ Running on RunPod only
✅ Accessible at https://styletts.ailabsafrica.com
✅ GPU: NVIDIA A40 (44.43GB total)
✅ Process running on port 8006
```

**Architecture:**
```
User Request
    ↓
https://styletts.ailabsafrica.com (Nginx on 148.251.0.46)
    ↓
jzfmzviw26huka-8013.proxy.runpod.net (RunPod proxy)
    ↓
Port 8006 on RunPod GPU (194.68.245.121)
    ↓
StyleTTS2 FastAPI (app.py)
```

**Key Difference:**
- ❌ **NOT running locally** on 148.251.0.46
- ✅ **Only on RunPod** GPU instance
- Local files are just source code/reference

---

### 2. Node.js & NPM Installation

**Installed on RunPod:** ✅

```bash
Node.js: v20.19.5
NPM:     v10.8.2
Location: /usr/bin/node, /usr/bin/npm
```

**Installation Command Used:**
```bash
ssh -p 22153 root@194.68.245.121
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs
```

---

### 3. Claude Code CLI Installation

**Installed globally on RunPod:** ✅

```bash
Package:  @anthropic-ai/claude-code
Version:  2.0.36
Location: /usr/bin/claude
```

**Installation Command Used:**
```bash
ssh -p 22153 root@194.68.245.121
cd /workspace
npm install -g @anthropic-ai/claude-code
```

**Usage:**
```bash
# SSH to RunPod
ssh -p 22153 root@194.68.245.121

# Navigate to workspace
cd /workspace

# Use Claude Code
claude
```

---

## All TTS Services on RunPod

| Service | Port | Local (148.251.0.46) | RunPod (194.68.245.121) | Public URL |
|---------|------|---------------------|------------------------|------------|
| **F5-TTS** | 8002 | ❌ No | ✅ Yes | https://f5tts.ailabsafrica.com |
| **StyleTTS2** | 8006 | ❌ No | ✅ Yes | https://styletts.ailabsafrica.com |
| **Moshi** | 8008 | ❌ No | ✅ Yes | https://kyutai.ailabsafrica.com |

**Summary:** All TTS services run exclusively on RunPod GPU, proxied through the local server.

---

## RunPod /workspace Directory Structure

```
/workspace/
├── tts-deployment/
│   ├── docker/
│   │   ├── f5tts/          # F5-TTS API (port 8002)
│   │   ├── styletts2/      # StyleTTS2 API (port 8006) ✅
│   │   ├── moshi/          # Moshi API (port 8008)
│   │   ├── melotts/        # MeloTTS
│   │   ├── openvoice/      # OpenVoice
│   │   └── kokoro/         # Kokoro
│   └── ...
├── F5-TTS/                 # F5-TTS source repo
├── StyleTTS2/              # StyleTTS2 source repo
├── moshi/                  # Moshi source
├── gptsovits/              # GPT-SoVITS
└── .claude/                # Claude Code config ✅
```

---

## SSH Access

**Connection:**
```bash
ssh -p 22153 root@194.68.245.121
```

**Key:** `~/.ssh/id_ed25519` (already configured)

**Available Commands:**
```bash
# Check running services
ps aux | grep -E "f5tts|styletts|moshi"

# Check GPU usage
nvidia-smi

# View logs
tail -f /tmp/styletts2_api.log

# Use Claude Code
claude

# Check Node.js/npm
node --version
npm --version
```

---

## Verification

### 1. StyleTTS2 Health Check
```bash
curl https://styletts.ailabsafrica.com/health
```

**Response:**
```json
{
    "status": "healthy",
    "device": "cuda",
    "model_loaded": false,
    "gpu_name": "NVIDIA A40",
    "gpu_memory_allocated_gb": "0.00",
    "gpu_memory_total_gb": "44.43"
}
```

### 2. Node.js Verification
```bash
ssh -p 22153 root@194.68.245.121 "node --version && npm --version"
```

**Output:**
```
v20.19.5
10.8.2
```

### 3. Claude Code Verification
```bash
ssh -p 22153 root@194.68.245.121 "claude --version"
```

**Output:**
```
2.0.36 (Claude Code)
```

---

## Next Steps

### Using Claude Code on RunPod

1. **SSH to RunPod:**
   ```bash
   ssh -p 22153 root@194.68.245.121
   ```

2. **Navigate to workspace:**
   ```bash
   cd /workspace
   ```

3. **Start Claude Code:**
   ```bash
   claude
   ```

4. **Work on TTS deployment:**
   ```bash
   cd /workspace/tts-deployment/docker/styletts2
   claude
   ```

### Common Tasks

**Update StyleTTS2 code:**
```bash
# Edit locally
vim /opt/kasaai/apps/tts-deployment/docker/styletts2/app.py

# Copy to RunPod
scp -P 22153 /opt/kasaai/apps/tts-deployment/docker/styletts2/app.py \
    root@194.68.245.121:/workspace/tts-deployment/docker/styletts2/

# Restart service on RunPod
ssh -p 22153 root@194.68.245.121 \
    "pkill -f styletts2 && cd /workspace/tts-deployment/docker/styletts2 && \
     source /workspace/tts-venv/bin/activate && \
     nohup python3 app.py > /tmp/styletts2_api.log 2>&1 &"
```

**Use Claude Code to modify files:**
```bash
ssh -p 22153 root@194.68.245.121
cd /workspace/tts-deployment/docker/styletts2
claude  # Opens Claude Code in current directory
```

---

## Important Notes

### Why No Local StyleTTS2?

**GPU Requirement:**
- StyleTTS2 needs GPU for model inference
- Local server (148.251.0.46) has no GPU
- RunPod provides NVIDIA A40 (44GB VRAM)

**Current Architecture:**
```
Local Server (148.251.0.46)
├── Nginx reverse proxy ✅
├── SSL certificates ✅
└── No GPU ❌

RunPod GPU (194.68.245.121)
├── NVIDIA A40 GPU ✅
├── TTS services running ✅
├── Node.js + Claude Code ✅
└── /workspace for development ✅
```

### File Synchronization

**Important:** Local and RunPod files can diverge!

**Recommendation:**
1. Edit files on local machine
2. Use `scp` or `rsync` to sync to RunPod
3. Restart services on RunPod
4. OR use Claude Code directly on RunPod via SSH

**Git Sync (Best Practice):**
```bash
# On local machine
git commit -m "Update StyleTTS2"
git push

# On RunPod
ssh -p 22153 root@194.68.245.121
cd /workspace/tts-deployment
git pull
```

---

## Troubleshooting

### StyleTTS2 Not Responding

**Check if running:**
```bash
ssh -p 22153 root@194.68.245.121 "ps aux | grep styletts"
```

**Restart service:**
```bash
ssh -p 22153 root@194.68.245.121 << 'EOF'
pkill -f styletts2
cd /workspace/tts-deployment/docker/styletts2
source /workspace/tts-venv/bin/activate
nohup python3 app.py > /tmp/styletts2_api.log 2>&1 &
echo "PID: $!"
EOF
```

**Check logs:**
```bash
ssh -p 22153 root@194.68.245.121 "tail -100 /tmp/styletts2_api.log"
```

### Claude Code Issues

**Verify installation:**
```bash
ssh -p 22153 root@194.68.245.121 "which claude && claude --version"
```

**Reinstall if needed:**
```bash
ssh -p 22153 root@194.68.245.121 "npm install -g @anthropic-ai/claude-code"
```

---

## Summary

✅ **StyleTTS2:** Running on RunPod only (GPU required)
✅ **Node.js:** v20.19.5 installed on RunPod
✅ **NPM:** v10.8.2 installed on RunPod
✅ **Claude Code:** v2.0.36 installed globally on RunPod at /usr/bin/claude
✅ **Workspace:** /workspace ready for development
✅ **SSH Access:** Confirmed working on port 22153

**Ready to use Claude Code on RunPod!** 🚀

---

**Last Updated:** November 8, 2025
**Status:** Production Ready
