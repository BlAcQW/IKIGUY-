#!/bin/bash
# Deploy Whisper African QLoRA Training to Existing RunPod
# RunPod Pod: jzfmzviw26huka-644113c7 (A40 46GB VRAM)

set -e

# Configuration
RUNPOD_HOST="194.68.245.121"
RUNPOD_PORT="22048"
RUNPOD_USER="root"
SSH_KEY="$HOME/.ssh/id_ed25519"
REMOTE_DIR="/workspace/whisper-african-training"
LOCAL_VOICE_LAB="/opt/kasaai/apps/voice-lab"

echo "=================================================="
echo "🚀 Whisper African QLoRA - RunPod Deployment"
echo "=================================================="
echo ""
echo "Pod: jzfmzviw26huka-644113c7"
echo "GPU: NVIDIA A40 (46GB VRAM)"
echo "Host: $RUNPOD_HOST:$RUNPOD_PORT"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to run SSH command
run_ssh() {
    ssh -p "$RUNPOD_PORT" -i "$SSH_KEY" "$RUNPOD_USER@$RUNPOD_HOST" "$@"
}

# Function to copy files
copy_file() {
    scp -P "$RUNPOD_PORT" -i "$SSH_KEY" "$1" "$RUNPOD_USER@$RUNPOD_HOST:$2"
}

# Step 1: Test connection
echo -e "${BLUE}Step 1: Testing connection...${NC}"
if run_ssh "echo 'Connection successful!'"; then
    echo -e "${GREEN}✅ Connection verified${NC}"
else
    echo -e "${YELLOW}❌ Connection failed. Check SSH configuration.${NC}"
    exit 1
fi
echo ""

# Step 2: Check GPU
echo -e "${BLUE}Step 2: Checking GPU...${NC}"
run_ssh "nvidia-smi --query-gpu=name,memory.total --format=csv,noheader"
echo ""

# Step 3: Create remote directory
echo -e "${BLUE}Step 3: Creating remote directory...${NC}"
run_ssh "mkdir -p $REMOTE_DIR"
echo -e "${GREEN}✅ Created $REMOTE_DIR${NC}"
echo ""

# Step 4: Copy training script
echo -e "${BLUE}Step 4: Copying training script...${NC}"
copy_file "$LOCAL_VOICE_LAB/runpod_whisper_african_qlora.py" "$REMOTE_DIR/"
echo -e "${GREEN}✅ Copied training script${NC}"
echo ""

# Step 5: Copy documentation
echo -e "${BLUE}Step 5: Copying documentation...${NC}"
copy_file "$LOCAL_VOICE_LAB/01_WHISPER_QLORA_RUNPOD_SETUP.md" "$REMOTE_DIR/"
copy_file "$LOCAL_VOICE_LAB/02_RUNPOD_QUICK_START.md" "$REMOTE_DIR/"
copy_file "$LOCAL_VOICE_LAB/03_CONFIRMED_TRAINING_DATA_INVENTORY.md" "$REMOTE_DIR/"
echo -e "${GREEN}✅ Copied documentation${NC}"
echo ""

# Step 6: Create virtual environment and install dependencies
echo -e "${BLUE}Step 6: Creating virtual environment in /workspace...${NC}"
run_ssh "cd /workspace && python3 -m venv venv"
echo -e "${GREEN}✅ Virtual environment created${NC}"
echo ""

echo -e "${BLUE}Step 7: Installing Python dependencies...${NC}"
run_ssh "cd /workspace && source venv/bin/activate && pip install --no-cache-dir transformers datasets accelerate bitsandbytes peft evaluate jiwer librosa soundfile wandb tqdm psutil pandas huggingface-hub"
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Step 8: Create start script
echo -e "${BLUE}Step 8: Creating start script...${NC}"
run_ssh "cat > $REMOTE_DIR/start_training.sh << 'EOF'
#!/bin/bash
# Whisper African Training Start Script

echo '=================================================='
echo '🎙️ Starting Whisper African QLoRA Training'
echo '=================================================='
echo ''

# Activate virtual environment
source /workspace/venv/bin/activate

# Login to Hugging Face (required for dataset downloads)
echo 'Please enter your Hugging Face token:'
read -s HF_TOKEN
huggingface-cli login --token \$HF_TOKEN

# Login to Weights & Biases (optional, for monitoring)
echo ''
echo 'Please enter your WandB API key (or press Enter to skip):'
read -s WANDB_KEY
if [ -n \"\$WANDB_KEY\" ]; then
    wandb login \$WANDB_KEY
fi

echo ''
echo '✅ Authentication complete'
echo ''
echo 'Starting training in 5 seconds...'
sleep 5

# Start training with nohup (using venv python)
nohup /workspace/venv/bin/python /workspace/whisper-african-training/runpod_whisper_african_qlora.py \
  --output_dir /workspace/whisper-african-training/outputs/whisper-small-african \
  --use_wandb \
  --wandb_project whisper-african-qlora \
  --wandb_run_name phase1-hausa-yoruba-igbo-twi-\$(date +%Y%m%d-%H%M%S) \
  --push_to_hub \
  --hub_model_id ailabsafrica/whisper-small-african \
  > /workspace/whisper-african-training/training.log 2>&1 &

TRAIN_PID=\$!
echo \"Training started with PID: \$TRAIN_PID\"
echo \$TRAIN_PID > /workspace/whisper-african-training/training.pid

echo ''
echo '📊 Monitor training:'
echo '  - WandB: https://wandb.ai/yourname/whisper-african-qlora'
echo '  - Logs: tail -f /workspace/whisper-african-training/training.log'
echo '  - GPU: watch -n 1 nvidia-smi'
echo ''
echo '🛑 Stop training:'
echo '  kill \$(cat /workspace/whisper-african-training/training.pid)'
echo ''
EOF"

run_ssh "chmod +x $REMOTE_DIR/start_training.sh"
echo -e "${GREEN}✅ Start script created${NC}"
echo ""

# Step 9: Create monitoring script
echo -e "${BLUE}Step 9: Creating monitoring script...${NC}"
run_ssh "cat > $REMOTE_DIR/monitor.sh << 'EOF'
#!/bin/bash
# Monitoring script for Whisper training

echo '=================================================='
echo '📊 Whisper Training Monitor'
echo '=================================================='
echo ''

# Check if training is running
if [ -f /workspace/whisper-african-training/training.pid ]; then
    PID=\$(cat /workspace/whisper-african-training/training.pid)
    if ps -p \$PID > /dev/null 2>&1; then
        echo '✅ Training is running (PID: '\$PID')'
    else
        echo '⚠️ Training process not found'
    fi
else
    echo '⚠️ No training.pid file found'
fi

echo ''
echo '=== GPU Status ==='
nvidia-smi --query-gpu=name,temperature.gpu,utilization.gpu,utilization.memory,memory.used,memory.total --format=csv,noheader

echo ''
echo '=== Last 20 lines of training log ==='
if [ -f /workspace/whisper-african-training/training.log ]; then
    tail -n 20 /workspace/whisper-african-training/training.log
else
    echo 'No training.log found'
fi

echo ''
echo '=== Disk Usage ==='
df -h /workspace

echo ''
echo '=== Training Checkpoints ==='
if [ -d /workspace/whisper-african-training/outputs ]; then
    ls -lh /workspace/whisper-african-training/outputs/whisper-small-african/checkpoint-* 2>/dev/null || echo 'No checkpoints yet'
else
    echo 'Output directory not created yet'
fi
EOF"

run_ssh "chmod +x $REMOTE_DIR/monitor.sh"
echo -e "${GREEN}✅ Monitor script created${NC}"
echo ""

# Step 10: Create stop script
echo -e "${BLUE}Step 10: Creating stop script...${NC}"
run_ssh "cat > $REMOTE_DIR/stop_training.sh << 'EOF'
#!/bin/bash
# Stop Whisper training

if [ -f /workspace/whisper-african-training/training.pid ]; then
    PID=\$(cat /workspace/whisper-african-training/training.pid)
    if ps -p \$PID > /dev/null 2>&1; then
        echo \"Stopping training (PID: \$PID)...\"
        kill \$PID
        echo \"✅ Training stopped\"
        rm /workspace/whisper-african-training/training.pid
    else
        echo \"⚠️ Training process not running\"
    fi
else
    echo \"⚠️ No training.pid file found\"
fi
EOF"

run_ssh "chmod +x $REMOTE_DIR/stop_training.sh"
echo -e "${GREEN}✅ Stop script created${NC}"
echo ""

# Step 11: Summary
echo ""
echo "=================================================="
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo "=================================================="
echo ""
echo "📂 Remote directory: $REMOTE_DIR"
echo ""
echo "🚀 To start training:"
echo "   ssh -p $RUNPOD_PORT -i $SSH_KEY $RUNPOD_USER@$RUNPOD_HOST"
echo "   cd $REMOTE_DIR"
echo "   ./start_training.sh"
echo ""
echo "📊 To monitor training:"
echo "   ssh -p $RUNPOD_PORT -i $SSH_KEY $RUNPOD_USER@$RUNPOD_HOST"
echo "   cd $REMOTE_DIR"
echo "   ./monitor.sh"
echo ""
echo "Or continuously monitor:"
echo "   watch -n 30 './monitor.sh'"
echo ""
echo "🛑 To stop training:"
echo "   ssh -p $RUNPOD_PORT -i $SSH_KEY $RUNPOD_USER@$RUNPOD_HOST"
echo "   cd $REMOTE_DIR"
echo "   ./stop_training.sh"
echo ""
echo "💾 To download trained model:"
echo "   scp -r -P $RUNPOD_PORT -i $SSH_KEY \\"
echo "     $RUNPOD_USER@$RUNPOD_HOST:$REMOTE_DIR/outputs/whisper-small-african/final \\"
echo "     /opt/kasaai/apps/voice-lab/models/whisper-small-african"
echo ""
echo "=================================================="
echo ""
