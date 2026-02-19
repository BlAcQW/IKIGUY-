#!/bin/bash
# RunPod TTS Automated Setup Script
# Creates portable TTS deployment that can be quickly replicated on new pods

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE} $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

# Check if running on RunPod
if [ ! -d "/workspace" ]; then
    log_error "This script is designed to run on RunPod instances with /workspace directory"
    exit 1
fi

log_step "🚀 Starting RunPod TTS Deployment"

# Install system dependencies
log_step "📦 Installing System Dependencies"
apt-get update -qq
apt-get install -y -qq \
  ffmpeg \
  libsndfile1 \
  portaudio19-dev \
  espeak-ng \
  tmux \
  git \
  wget \
  curl \
  || log_warn "Some packages might already be installed"

# Create directory structure
log_step "📁 Creating Directory Structure"
mkdir -p /workspace/tts-deployment/{f5tts,styletts2,kyutai,outputs,logs}
cd /workspace/tts-deployment
log_info "Created: /workspace/tts-deployment/"

# Setup F5-TTS
log_step "🎵 Setting up F5-TTS"
cd /workspace/tts-deployment/f5tts
if [ ! -d "venv" ]; then
    log_info "Creating virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate
log_info "Installing PyTorch with CUDA support..."
pip install -q torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

if [ ! -d "F5-TTS" ]; then
    log_info "Cloning F5-TTS repository..."
    git clone -q https://github.com/SWivid/F5-TTS.git
fi
cd F5-TTS
log_info "Installing F5-TTS dependencies..."
pip install -q -e .
pip install -q fastapi uvicorn pydantic python-multipart
deactivate
log_info "✅ F5-TTS setup complete"

# Setup StyleTTS2
log_step "🎤 Setting up StyleTTS2"
cd /workspace/tts-deployment/styletts2
if [ ! -d "venv" ]; then
    log_info "Creating virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate
log_info "Installing PyTorch with CUDA support..."
pip install -q torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

if [ ! -d "StyleTTS2" ]; then
    log_info "Cloning StyleTTS2 repository..."
    git clone -q https://github.com/yl4579/StyleTTS2.git
fi
cd StyleTTS2
log_info "Installing StyleTTS2 dependencies..."
pip install -q -r requirements.txt
pip install -q fastapi uvicorn pydantic python-multipart

# Download models
mkdir -p Models/LibriTTS
if [ ! -f "Models/LibriTTS/epochs_2nd_00020.pth" ]; then
    log_info "Downloading StyleTTS2 models (this may take a few minutes)..."
    wget -q --show-progress https://huggingface.co/yl4579/StyleTTS2-LibriTTS/resolve/main/Models/LibriTTS/epochs_2nd_00020.pth \
      -O Models/LibriTTS/epochs_2nd_00020.pth
else
    log_info "Model already downloaded"
fi
deactivate
log_info "✅ StyleTTS2 setup complete"

# Setup Kyutai/Moshi
log_step "🗣️ Setting up Kyutai/Moshi"
cd /workspace/tts-deployment/kyutai
if [ ! -d "venv" ]; then
    log_info "Creating virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate
log_info "Installing API dependencies..."
pip install -q fastapi uvicorn pydantic python-multipart
# Note: Kyutai/Moshi Python package not yet available, using placeholder
deactivate
log_info "✅ Kyutai placeholder setup complete"

# Copy app.py files if they exist
log_step "📋 Checking for Service Code"
if [ -f "/workspace/tts-deployment/docker/f5tts/app.py" ]; then
    log_info "Copying F5-TTS app.py..."
    cp /workspace/tts-deployment/docker/f5tts/app.py /workspace/tts-deployment/f5tts/F5-TTS/
fi

if [ -f "/workspace/tts-deployment/docker/styletts2/app.py" ]; then
    log_info "Copying StyleTTS2 app.py..."
    cp /workspace/tts-deployment/docker/styletts2/app.py /workspace/tts-deployment/styletts2/StyleTTS2/
fi

if [ -f "/workspace/tts-deployment/docker/kyutai/app.py" ]; then
    log_info "Copying Kyutai app.py..."
    cp /workspace/tts-deployment/docker/kyutai/app.py /workspace/tts-deployment/kyutai/
fi

# Create startup script
log_step "🔧 Creating Startup Scripts"
cat > /workspace/tts-deployment/start_all.sh <<'SCRIPT'
#!/bin/bash
# Start all TTS services in tmux sessions

echo "Starting TTS services..."

# Kill existing sessions if any
tmux kill-session -t f5tts 2>/dev/null || true
tmux kill-session -t styletts2 2>/dev/null || true
tmux kill-session -t kyutai 2>/dev/null || true

# Start F5-TTS
cd /workspace/tts-deployment/f5tts/F5-TTS
if [ -f "app.py" ]; then
    tmux new -d -s f5tts "source ../venv/bin/activate && uvicorn app:app --host 0.0.0.0 --port 8002 2>&1 | tee /workspace/tts-deployment/logs/f5tts.log"
    echo "✅ F5-TTS started on port 8002"
else
    echo "⚠️  F5-TTS app.py not found, skipping"
fi

# Start StyleTTS2
cd /workspace/tts-deployment/styletts2/StyleTTS2
if [ -f "app.py" ]; then
    tmux new -d -s styletts2 "source ../venv/bin/activate && uvicorn app:app --host 0.0.0.0 --port 8006 2>&1 | tee /workspace/tts-deployment/logs/styletts2.log"
    echo "✅ StyleTTS2 started on port 8006"
else
    echo "⚠️  StyleTTS2 app.py not found, skipping"
fi

# Start Kyutai
cd /workspace/tts-deployment/kyutai
if [ -f "app.py" ]; then
    tmux new -d -s kyutai "source venv/bin/activate && uvicorn app:app --host 0.0.0.0 --port 8008 2>&1 | tee /workspace/tts-deployment/logs/kyutai.log"
    echo "✅ Kyutai started on port 8008"
else
    echo "⚠️  Kyutai app.py not found, skipping"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ TTS Services Started"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Management commands:"
echo "   tmux ls                     - List all sessions"
echo "   tmux attach -t f5tts        - Attach to F5-TTS"
echo "   tmux attach -t styletts2    - Attach to StyleTTS2"
echo "   tmux attach -t kyutai       - Attach to Kyutai"
echo "   Ctrl+B, D                   - Detach from session"
echo ""
echo "🔍 Check services:"
echo "   curl http://localhost:8002/health"
echo "   curl http://localhost:8006/health"
echo "   curl http://localhost:8008/health"
echo ""
echo "📊 View logs:"
echo "   tail -f /workspace/tts-deployment/logs/f5tts.log"
echo "   tail -f /workspace/tts-deployment/logs/styletts2.log"
echo "   tail -f /workspace/tts-deployment/logs/kyutai.log"
echo ""
SCRIPT

chmod +x /workspace/tts-deployment/start_all.sh

# Create stop script
cat > /workspace/tts-deployment/stop_all.sh <<'SCRIPT'
#!/bin/bash
# Stop all TTS services

echo "Stopping TTS services..."
tmux kill-session -t f5tts 2>/dev/null && echo "✅ Stopped F5-TTS" || echo "⚠️  F5-TTS not running"
tmux kill-session -t styletts2 2>/dev/null && echo "✅ Stopped StyleTTS2" || echo "⚠️  StyleTTS2 not running"
tmux kill-session -t kyutai 2>/dev/null && echo "✅ Stopped Kyutai" || echo "⚠️  Kyutai not running"
echo "Done"
SCRIPT

chmod +x /workspace/tts-deployment/stop_all.sh

# Create status script
cat > /workspace/tts-deployment/status.sh <<'SCRIPT'
#!/bin/bash
# Check status of TTS services

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TTS Services Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check tmux sessions
echo "📋 Running Sessions:"
tmux ls 2>/dev/null || echo "   No tmux sessions running"
echo ""

# Check ports
echo "🌐 Listening Ports:"
netstat -tulpn 2>/dev/null | grep -E '8002|8006|8008' || echo "   No services listening on ports 8002, 8006, 8008"
echo ""

# Check GPU
echo "🎮 GPU Status:"
nvidia-smi --query-gpu=index,name,memory.used,memory.total --format=csv,noheader 2>/dev/null || echo "   Unable to query GPU"
echo ""

# Health checks
echo "🏥 Health Checks:"
for port in 8002 8006 8008; do
    if curl -s http://localhost:$port/health > /dev/null 2>&1; then
        echo "   ✅ Port $port: Healthy"
    else
        echo "   ❌ Port $port: Not responding"
    fi
done
echo ""
SCRIPT

chmod +x /workspace/tts-deployment/status.sh

# Create cleanup script
cat > /workspace/tts-deployment/cleanup.sh <<'SCRIPT'
#!/bin/bash
# Cleanup old generated audio files

echo "Cleaning up audio files older than 24 hours..."
find /workspace/tts-deployment/outputs -name "*.wav" -mtime +1 -delete
echo "✅ Cleanup complete"
SCRIPT

chmod +x /workspace/tts-deployment/cleanup.sh

# Create README
cat > /workspace/tts-deployment/README.txt <<'README'
TTS Deployment on RunPod
========================

Quick Start
-----------
1. Start all services:   ./start_all.sh
2. Check status:         ./status.sh
3. Stop all services:    ./stop_all.sh
4. Cleanup old files:    ./cleanup.sh

Service Endpoints
-----------------
- F5-TTS:     http://localhost:8002
- StyleTTS2:  http://localhost:8006
- Kyutai:     http://localhost:8008

Health Checks
-------------
curl http://localhost:8002/health
curl http://localhost:8006/health
curl http://localhost:8008/health

Logs
----
tail -f logs/f5tts.log
tail -f logs/styletts2.log
tail -f logs/kyutai.log

Tmux Management
---------------
tmux ls                  # List sessions
tmux attach -t f5tts     # Attach to session
Ctrl+B, D                # Detach from session

Backup This Deployment
----------------------
cd /workspace
tar czf tts-backup.tar.gz tts-deployment/
scp -P PORT tts-backup.tar.gz user@host:/backup/

Restore on New Pod
------------------
scp -P PORT user@host:/backup/tts-backup.tar.gz /workspace/
cd /workspace && tar xzf tts-backup.tar.gz
./tts-deployment/start_all.sh
README

log_step "✨ Setup Complete!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ RunPod TTS Deployment Ready"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📍 Location: /workspace/tts-deployment/"
echo ""
echo "📝 Next Steps:"
echo "   1. Transfer service code (app.py files) if not already present"
echo "   2. Start services: ./start_all.sh"
echo "   3. Check status: ./status.sh"
echo ""
echo "📖 Full documentation: cat /workspace/tts-deployment/README.txt"
echo ""
echo "💾 To backup this deployment:"
echo "   tar czf /workspace/tts-backup.tar.gz /workspace/tts-deployment/"
echo ""
log_info "Deployment timestamp: $(date)"
