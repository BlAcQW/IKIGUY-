# RunPod Portable Deployment Strategy

**Created:** 2025-10-20
**Problem:** Virtual environments aren't portable between pods
**Solution:** Use RunPod's Docker template system or create deployment snapshots

---

## 🎯 The Problem

Using virtual environments directly on RunPod has a major limitation:
- **Not portable:** If you need to switch pods, you'd have to reinstall everything
- **Time-consuming:** Each new pod requires full setup (30-60 minutes)
- **Error-prone:** Manual steps can be forgotten or misconfigured

---

## ✅ Solution Options

### Option 1: Use RunPod Templates (RECOMMENDED)

RunPod supports custom Docker templates that can be reused across pods.

#### How It Works:
1. Build Docker images locally or on CI/CD
2. Push images to Docker Hub or GitHub Container Registry
3. Create RunPod template pointing to your images
4. New pods start instantly with your services pre-installed

#### Implementation:

**Step 1: Build and Push Images Locally**

```bash
# On your local machine (or CI/CD)
cd /opt/kasaai/apps/tts-deployment

# Build images
docker build -t yourusername/f5tts:latest docker/f5tts/
docker build -t yourusername/styletts2:latest docker/styletts2/
docker build -t yourusername/kyutai:latest docker/kyutai/

# Push to Docker Hub
docker login
docker push yourusername/f5tts:latest
docker push yourusername/styletts2:latest
docker push yourusername/kyutai:latest
```

**Step 2: Create RunPod Template**

Create a custom Dockerfile for RunPod:

```dockerfile
# runpod-tts-template.dockerfile
FROM runpod/pytorch:2.1.0-py3.10-cuda12.1.0-devel

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    portaudio19-dev \
    espeak-ng \
    tmux \
    && rm -rf /var/lib/apt/lists/*

# Copy service applications
COPY docker/f5tts/app.py /workspace/f5tts/app.py
COPY docker/styletts2/app.py /workspace/styletts2/app.py
COPY docker/kyutai/app.py /workspace/kyutai/app.py

# Install Python dependencies
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    pydantic \
    torch \
    torchaudio \
    transformers \
    && pip install git+https://github.com/SWivid/F5-TTS.git

# Create startup script
COPY runpod-startup.sh /workspace/startup.sh
RUN chmod +x /workspace/startup.sh

# Expose ports
EXPOSE 8002 8006 8008

# Set working directory
WORKDIR /workspace

CMD ["/workspace/startup.sh"]
```

**Step 3: Build and Push Template**

```bash
docker build -f runpod-tts-template.dockerfile -t yourusername/runpod-tts:latest .
docker push yourusername/runpod-tts:latest
```

**Step 4: Use in RunPod**

In RunPod dashboard:
1. Go to "Templates"
2. Create new template
3. Set Docker image: `yourusername/runpod-tts:latest`
4. Configure ports: 8002, 8006, 8008
5. Set disk space: 50GB
6. Save template

Now you can spin up new pods instantly with all services pre-configured!

---

### Option 2: Workspace Snapshots (Quick Backup/Restore)

RunPod's `/workspace` volume persists and can be backed up.

```bash
# Create deployment snapshot
ssh -p 22048 -i ~/.ssh/id_ed25519 root@194.68.245.121 \
  'cd /workspace && tar czf tts-deployment-snapshot.tar.gz tts-deployment/'

# Download snapshot
scp -P 22048 -i ~/.ssh/id_ed25519 \
  root@194.68.245.121:/workspace/tts-deployment-snapshot.tar.gz \
  ~/backups/

# On new pod: Upload and extract
scp -P NEW_PORT -i ~/.ssh/id_ed25519 \
  ~/backups/tts-deployment-snapshot.tar.gz \
  root@NEW_IP:/workspace/

ssh -p NEW_PORT -i ~/.ssh/id_ed25519 root@NEW_IP \
  'cd /workspace && tar xzf tts-deployment-snapshot.tar.gz'
```

---

### Option 3: Automated Setup Script (Fastest to Implement)

Create a comprehensive setup script that can provision a new pod in minutes.

```bash
#!/bin/bash
# setup-runpod-tts.sh - Automated RunPod TTS Setup

set -e

echo "🚀 Starting RunPod TTS Setup..."

# Install system dependencies
echo "📦 Installing system dependencies..."
apt-get update && apt-get install -y \
  ffmpeg libsndfile1 portaudio19-dev espeak-ng tmux git \
  || echo "Some packages might already be installed"

# Create directory structure
echo "📁 Creating directory structure..."
mkdir -p /workspace/tts-deployment/{f5tts,styletts2,kyutai,outputs}

# Setup F5-TTS
echo "🎵 Setting up F5-TTS..."
cd /workspace/tts-deployment/f5tts
python3 -m venv venv
source venv/bin/activate
pip install --quiet torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
git clone --quiet https://github.com/SWivid/F5-TTS.git || echo "Already cloned"
cd F5-TTS
pip install --quiet -e .
pip install --quiet fastapi uvicorn pydantic
deactivate

# Setup StyleTTS2
echo "🎤 Setting up StyleTTS2..."
cd /workspace/tts-deployment/styletts2
python3 -m venv venv
source venv/bin/activate
pip install --quiet torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
git clone --quiet https://github.com/yl4579/StyleTTS2.git || echo "Already cloned"
cd StyleTTS2
pip install --quiet -r requirements.txt
pip install --quiet fastapi uvicorn pydantic
# Download models
mkdir -p Models/LibriTTS
wget -q https://huggingface.co/yl4579/StyleTTS2-LibriTTS/resolve/main/Models/LibriTTS/epochs_2nd_00020.pth \
  -O Models/LibriTTS/epochs_2nd_00020.pth || echo "Model already downloaded"
deactivate

# Setup Kyutai
echo "🗣️ Setting up Kyutai..."
cd /workspace/tts-deployment/kyutai
python3 -m venv venv
source venv/bin/activate
pip install --quiet fastapi uvicorn pydantic
deactivate

# Create startup script
echo "🔧 Creating startup script..."
cat > /workspace/tts-deployment/start_all.sh <<'SCRIPT'
#!/bin/bash
cd /workspace/tts-deployment/f5tts/F5-TTS
tmux new -d -s f5tts "source ../venv/bin/activate && uvicorn app:app --host 0.0.0.0 --port 8002"

cd /workspace/tts-deployment/styletts2/StyleTTS2
tmux new -d -s styletts2 "source ../venv/bin/activate && uvicorn app:app --host 0.0.0.0 --port 8006"

cd /workspace/tts-deployment/kyutai
tmux new -d -s kyutai "source venv/bin/activate && uvicorn app:app --host 0.0.0.0 --port 8008"

echo "✅ All TTS services started in tmux sessions"
echo "📋 List sessions: tmux ls"
echo "🔗 Attach to session: tmux attach -t f5tts"
SCRIPT

chmod +x /workspace/tts-deployment/start_all.sh

echo "✅ Setup complete!"
echo "📝 Next steps:"
echo "   1. Copy service code (app.py files) to respective directories"
echo "   2. Run: /workspace/tts-deployment/start_all.sh"
echo "   3. Check: tmux ls"
```

**Usage:**

```bash
# Save script locally
nano /opt/kasaai/apps/tts-deployment/scripts/setup-runpod-tts.sh
# Paste script above
chmod +x /opt/kasaai/apps/tts-deployment/scripts/setup-runpod-tts.sh

# Transfer to new RunPod instance
scp -P PORT -i ~/.ssh/id_ed25519 \
  /opt/kasaai/apps/tts-deployment/scripts/setup-runpod-tts.sh \
  root@IP:/workspace/

# Run on RunPod
ssh -p PORT -i ~/.ssh/id_ed25519 root@IP \
  'bash /workspace/setup-runpod-tts.sh'
```

**Time to deploy on new pod:** ~10-15 minutes (mostly downloading models)

---

## 📊 Comparison of Options

| Option | Portability | Setup Time | Maintenance | Best For |
|--------|-------------|------------|-------------|----------|
| **RunPod Template** | ⭐⭐⭐⭐⭐ | Instant | Low | Production |
| **Workspace Snapshot** | ⭐⭐⭐⭐ | ~5 min | Medium | Quick migration |
| **Setup Script** | ⭐⭐⭐ | ~15 min | High | Development |
| **Manual venv** | ⭐ | ~60 min | Very High | Testing |

---

## 🎯 Recommended Approach: Hybrid Strategy

**For Now (Development):**
1. Use automated setup script for quick deployment
2. Create workspace snapshots as backup

**For Production:**
1. Build RunPod template with all services
2. Use template for all new pods
3. Keep workspace snapshots for disaster recovery

---

## 📝 Implementation Plan

### Phase 1: Create Automated Setup Script ✅
Create `setup-runpod-tts.sh` for quick pod provisioning

### Phase 2: Build RunPod Template
1. Create `runpod-tts-template.dockerfile`
2. Build and push to Docker Hub
3. Create RunPod template
4. Test on new pod

### Phase 3: Documentation
1. Document template usage
2. Create troubleshooting guide
3. Setup monitoring

---

## 🔄 Migration Process (Pod to Pod)

### Quick Migration (Workspace Snapshot)
```bash
# On old pod
tar czf /workspace/tts-snapshot.tar.gz /workspace/tts-deployment

# Download
scp -P OLD_PORT -i ~/.ssh/id_ed25519 root@OLD_IP:/workspace/tts-snapshot.tar.gz ./

# Upload to new pod
scp -P NEW_PORT -i ~/.ssh/id_ed25519 ./tts-snapshot.tar.gz root@NEW_IP:/workspace/

# On new pod
cd /workspace && tar xzf tts-snapshot.tar.gz
./tts-deployment/start_all.sh
```

**Time:** 5-10 minutes

### Template-Based Migration
```bash
# Simply start new pod from template
# All services are pre-installed and configured
```

**Time:** <1 minute

---

**Next Action:** Would you like me to:
1. Create the automated setup script now?
2. Build the RunPod Docker template?
3. Or proceed with direct deployment on current pod first?
