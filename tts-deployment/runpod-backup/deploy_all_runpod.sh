#!/bin/bash
################################################################################
# RunPod Complete Deployment Script
# Deploys: F5-TTS, StyleTTS2, and Whisper Training
# Date: 2025-10-23
################################################################################

set -e  # Exit on error

echo "================================="
echo "🚀 RunPod Complete Deployment"
echo "================================="
echo ""

# Configuration
RUNPOD_HOST="194.68.245.121"
RUNPOD_PORT="22048"
RUNPOD_USER="root"
SSH_KEY="$HOME/.ssh/id_ed25519"
LOCAL_BACKUP_DIR="/opt/kasaai/apps/tts-deployment/runpod-backup"
REMOTE_WORKSPACE="/workspace"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_ssh() {
    log_info "Checking SSH connectivity..."
    if ssh -p $RUNPOD_PORT -i $SSH_KEY -o ConnectTimeout=10 $RUNPOD_USER@$RUNPOD_HOST "echo 'Connected'" &>/dev/null; then
        log_info "✅ SSH connection successful"
        return 0
    else
        log_error "❌ Cannot connect to RunPod. Is the pod running?"
        echo ""
        echo "Please start the pod from RunPod web dashboard:"
        echo "  Pod ID: jzfmzviw26huka-644113c7"
        echo "  GPU: A40 (46GB VRAM)"
        echo ""
        exit 1
    fi
}

deploy_tts_services() {
    log_info "Step 1: Deploying TTS Services (F5-TTS, StyleTTS2)"

    # Create workspace directories
    ssh -p $RUNPOD_PORT -i $SSH_KEY $RUNPOD_USER@$RUNPOD_HOST << 'EOF'
mkdir -p /workspace/tts-deployment
cd /workspace/tts-deployment
EOF

    # Copy docker-compose and service files
    log_info "Copying docker-compose configuration..."
    scp -P $RUNPOD_PORT -i $SSH_KEY \
        $LOCAL_BACKUP_DIR/backups/*/docker-compose.runpod.yml \
        $RUNPOD_USER@$RUNPOD_HOST:/workspace/tts-deployment/docker-compose.yml

    # Copy F5-TTS files
    log_info "Copying F5-TTS service files..."
    ssh -p $RUNPOD_PORT -i $SSH_KEY $RUNPOD_USER@$RUNPOD_HOST "mkdir -p /workspace/tts-deployment/docker/f5tts"
    scp -P $RUNPOD_PORT -i $SSH_KEY -r \
        /opt/kasaai/apps/tts-deployment/docker/f5tts/* \
        $RUNPOD_USER@$RUNPOD_HOST:/workspace/tts-deployment/docker/f5tts/

    # Copy StyleTTS2 files
    log_info "Copying StyleTTS2 service files..."
    ssh -p $RUNPOD_PORT -i $SSH_KEY $RUNPOD_USER@$RUNPOD_HOST "mkdir -p /workspace/tts-deployment/docker/styletts2"
    scp -P $RUNPOD_PORT -i $SSH_KEY -r \
        /opt/kasaai/apps/tts-deployment/docker/styletts2/* \
        $RUNPOD_USER@$RUNPOD_HOST:/workspace/tts-deployment/docker/styletts2/

    # Start services
    log_info "Starting TTS services with docker-compose..."
    ssh -p $RUNPOD_PORT -i $SSH_KEY $RUNPOD_USER@$RUNPOD_HOST << 'EOF'
cd /workspace/tts-deployment
docker compose up -d f5tts styletts2
echo ""
echo "Waiting for services to start..."
sleep 10
docker compose ps
EOF

    log_info "✅ TTS services deployed"
}

deploy_whisper_training() {
    log_info "Step 2: Deploying Whisper Training"

    # Create training directory
    ssh -p $RUNPOD_PORT -i $SSH_KEY $RUNPOD_USER@$RUNPOD_HOST << 'EOF'
mkdir -p /workspace/whisper-training
cd /workspace/whisper-training
EOF

    # Copy fixed training script
    log_info "Copying fixed Whisper training script..."
    scp -P $RUNPOD_PORT -i $SSH_KEY \
        $LOCAL_BACKUP_DIR/runpod_whisper_african_qlora_streaming_fixed.py \
        $RUNPOD_USER@$RUNPOD_HOST:/workspace/whisper-training/

    # Copy startup script
    scp -P $RUNPOD_PORT -i $SSH_KEY \
        $LOCAL_BACKUP_DIR/start_whisper_fixed.sh \
        $RUNPOD_USER@$RUNPOD_HOST:/workspace/whisper-training/

    # Make executable
    ssh -p $RUNPOD_PORT -i $SSH_KEY $RUNPOD_USER@$RUNPOD_HOST \
        "chmod +x /workspace/whisper-training/start_whisper_fixed.sh"

    # Install dependencies
    log_info "Installing Python dependencies..."
    ssh -p $RUNPOD_PORT -i $SSH_KEY $RUNPOD_USER@$RUNPOD_HOST << 'EOF'
pip install --quiet --upgrade pip
pip install --quiet transformers==4.43.0 peft==0.12.0 accelerate==0.34.0
pip install --quiet datasets==2.20.0 evaluate==0.4.2 jiwer
pip install --quiet librosa soundfile bitsandbytes wandb psutil pandas
EOF

    log_info "✅ Whisper training environment ready"
}

setup_authentication() {
    log_info "Step 3: Setting up authentication"

    # Check if HF token exists
    if [ -z "$HUGGING_FACE_HUB_TOKEN" ]; then
        log_warn "HUGGING_FACE_HUB_TOKEN not found in environment"
        log_warn "You'll need to run: huggingface-cli login --token YOUR_TOKEN"
    else
        log_info "Setting up HuggingFace authentication..."
        ssh -p $RUNPOD_PORT -i $SSH_KEY $RUNPOD_USER@$RUNPOD_HOST << EOF
echo "$HUGGING_FACE_HUB_TOKEN" | huggingface-cli login --token
EOF
    fi

    # Check if WandB key exists
    if [ -z "$WANDB_API_KEY" ]; then
        log_warn "WANDB_API_KEY not found (optional)"
    else
        log_info "Setting up Weights & Biases..."
        ssh -p $RUNPOD_PORT -i $SSH_KEY $RUNPOD_USER@$RUNPOD_HOST << EOF
wandb login $WANDB_API_KEY
EOF
    fi

    log_info "✅ Authentication setup complete"
}

start_training() {
    log_info "Step 4: Starting Whisper Training"

    ssh -p $RUNPOD_PORT -i $SSH_KEY $RUNPOD_USER@$RUNPOD_HOST << 'EOF'
cd /workspace/whisper-training

# Start training in background with nohup
nohup ./start_whisper_fixed.sh > whisper_training.log 2>&1 &

echo "Training started in background (PID: $!)"
echo ""
echo "Monitor with:"
echo "  ssh -p 22048 root@194.68.245.121 'tail -f /workspace/whisper-training/whisper_training.log'"
echo ""
echo "Or check WandB:"
echo "  https://wandb.ai/alfred-anyan-ai-labs/whisper-african-qlora"
EOF

    log_info "✅ Training started"
}

setup_ssh_tunnels() {
    log_info "Step 5: Setting up SSH tunnels for TTS services"

    # Kill existing tunnels
    pkill -f "ssh.*$RUNPOD_PORT.*8002" || true
    pkill -f "ssh.*$RUNPOD_PORT.*8006" || true

    # F5-TTS tunnel (port 8002)
    log_info "Creating F5-TTS tunnel (localhost:8002 -> RunPod:8002)"
    ssh -f -N -L 8002:localhost:8002 -p $RUNPOD_PORT -i $SSH_KEY $RUNPOD_USER@$RUNPOD_HOST

    # StyleTTS2 tunnel (port 8006)
    log_info "Creating StyleTTS2 tunnel (localhost:8006 -> RunPod:8006)"
    ssh -f -N -L 8006:localhost:8006 -p $RUNPOD_PORT -i $SSH_KEY $RUNPOD_USER@$RUNPOD_HOST

    log_info "✅ SSH tunnels established"
}

verify_deployment() {
    log_info "Step 6: Verifying deployment"

    echo ""
    echo "=== RunPod Services Status ==="
    ssh -p $RUNPOD_PORT -i $SSH_KEY $RUNPOD_USER@$RUNPOD_HOST << 'EOF'
# GPU status
echo "GPU Status:"
nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader
echo ""

# Docker services
echo "Docker Services:"
cd /workspace/tts-deployment
docker compose ps
echo ""

# Training process
echo "Training Process:"
ps aux | grep whisper | grep -v grep || echo "Not running yet"
echo ""
EOF

    # Test local endpoints
    echo "=== Local Endpoint Tests ==="

    # F5-TTS
    if curl -s --connect-timeout 5 http://localhost:8002/health | grep -q "healthy\|ok\|status"; then
        log_info "✅ F5-TTS: http://localhost:8002 (accessible)"
    else
        log_warn "⚠️  F5-TTS: Service may still be starting..."
    fi

    # StyleTTS2
    if curl -s --connect-timeout 5 http://localhost:8006/health | grep -q "healthy\|ok\|status"; then
        log_info "✅ StyleTTS2: http://localhost:8006 (accessible)"
    else
        log_warn "⚠️  StyleTTS2: Service may still be starting..."
    fi

    echo ""
    log_info "✅ Deployment verification complete"
}

# Main execution
main() {
    echo "Starting deployment process..."
    echo ""

    # Check SSH connectivity first
    check_ssh

    # Deploy services
    deploy_tts_services
    echo ""

    deploy_whisper_training
    echo ""

    setup_authentication
    echo ""

    start_training
    echo ""

    setup_ssh_tunnels
    echo ""

    verify_deployment
    echo ""

    echo "================================="
    echo "🎉 Deployment Complete!"
    echo "================================="
    echo ""
    echo "📊 Access Points:"
    echo "  - F5-TTS:     https://f5tts.ailabsafrica.com (via tunnel)"
    echo "  - StyleTTS2:  https://styletts.ailabsafrica.com (via tunnel)"
    echo "  - WandB:      https://wandb.ai/alfred-anyan-ai-labs/whisper-african-qlora"
    echo ""
    echo "📝 Next Steps:"
    echo "  1. Monitor training: ssh -p 22048 root@194.68.245.121 'tail -f /workspace/whisper-training/whisper_training.log'"
    echo "  2. Check GPU: ssh -p 22048 root@194.68.245.121 'nvidia-smi'"
    echo "  3. Test TTS: curl http://localhost:8002/health"
    echo ""
    echo "⏱️  Expected training time: 48-72 hours"
    echo ""
}

# Run main function
main
