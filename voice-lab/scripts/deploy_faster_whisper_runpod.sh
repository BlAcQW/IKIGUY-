#!/bin/bash
#
# Deploy Faster Whisper Training to RunPod with Hetzner SSH Mount
# This script sets up remote data access without downloading everything
#

set -e

echo "================================================================"
echo "FASTER WHISPER TRAINING - RUNPOD DEPLOYMENT"
echo "================================================================"

# Configuration
HETZNER_HOST="u408824.your-storagebox.de"
HETZNER_USER="u408824"
HETZNER_PASS="your_storage_password"  # Replace with actual password
MOUNT_POINT="/mnt/hetzner_storage"
SCRIPT_DIR="/workspace/whisper-ghanaian"

echo "📋 Configuration:"
echo "  - Hetzner host: $HETZNER_HOST"
echo "  - Mount point: $MOUNT_POINT"
echo "  - Script directory: $SCRIPT_DIR"
echo ""

# Step 1: Install dependencies
echo "📦 Step 1: Installing dependencies..."
pip install -q --upgrade pip
pip install -q \
    transformers[torch] \
    datasets \
    evaluate \
    jiwer \
    librosa \
    soundfile \
    tensorboard \
    accelerate \
    bitsandbytes \
    peft \
    sshfs

echo "✅ Dependencies installed"
echo ""

# Step 2: Setup SSH mount for Hetzner storage
echo "🔗 Step 2: Setting up SSH mount to Hetzner..."

# Create mount point
mkdir -p $MOUNT_POINT

# Check if already mounted
if mountpoint -q $MOUNT_POINT; then
    echo "⚠️  Already mounted at $MOUNT_POINT"
else
    # Mount using sshfs (no download, streaming access)
    echo "Mounting Hetzner storage via SSH..."
    echo "$HETZNER_PASS" | sshfs \
        -o password_stdin \
        -o reconnect \
        -o ServerAliveInterval=15 \
        -o ServerAliveCountMax=3 \
        -o cache=yes \
        -o kernel_cache \
        -o compression=no \
        -o Ciphers=aes128-gcm@openssh.com \
        $HETZNER_USER@$HETZNER_HOST:/ \
        $MOUNT_POINT

    if [ $? -eq 0 ]; then
        echo "✅ Hetzner storage mounted successfully"
    else
        echo "❌ Failed to mount Hetzner storage"
        exit 1
    fi
fi

# Verify mount
echo "Verifying mount..."
if [ -d "$MOUNT_POINT/voice-lab" ]; then
    echo "✅ Mount verified - voice-lab directory found"
    du -sh $MOUNT_POINT/voice-lab/data/twi-akan-fante/manifests 2>/dev/null || echo "  (Calculating size...)"
else
    echo "❌ Mount verification failed"
    exit 1
fi
echo ""

# Step 3: Copy training script
echo "📝 Step 3: Setting up training environment..."
mkdir -p $SCRIPT_DIR
cd $SCRIPT_DIR

# Copy script from local (you'll need to upload it first)
cat > train_faster_whisper_ghanaian.py << 'SCRIPT_EOF'
# The Python training script will be inserted here
# For now, this is a placeholder - upload the actual script
echo "Upload train_faster_whisper_ghanaian.py to $SCRIPT_DIR"
SCRIPT_EOF

echo "✅ Training environment ready"
echo ""

# Step 4: Verify data accessibility
echo "🔍 Step 4: Verifying data accessibility..."

MANIFEST_DIR="$MOUNT_POINT/voice-lab/data/twi-akan-fante/manifests"
TRAIN_MANIFEST="$MANIFEST_DIR/faster_whisper_train.csv"
VAL_MANIFEST="$MANIFEST_DIR/faster_whisper_val.csv"

if [ -f "$TRAIN_MANIFEST" ]; then
    TRAIN_SAMPLES=$(wc -l < $TRAIN_MANIFEST)
    echo "✅ Training manifest: $TRAIN_SAMPLES samples"
else
    echo "❌ Training manifest not found: $TRAIN_MANIFEST"
    exit 1
fi

if [ -f "$VAL_MANIFEST" ]; then
    VAL_SAMPLES=$(wc -l < $VAL_MANIFEST)
    echo "✅ Validation manifest: $VAL_SAMPLES samples"
else
    echo "❌ Validation manifest not found: $VAL_MANIFEST"
    exit 1
fi

echo ""

# Step 5: Check GPU
echo "🎮 Step 5: Checking GPU..."
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader
echo ""

# Step 6: Ready to train
echo "================================================================"
echo "✅ SETUP COMPLETE - READY TO TRAIN"
echo "================================================================"
echo ""
echo "To start training, run:"
echo ""
echo "  cd $SCRIPT_DIR"
echo "  python train_faster_whisper_ghanaian.py \\"
echo "    --model openai/whisper-small \\"
echo "    --epochs 3 \\"
echo "    --batch-size 16 \\"
echo "    --lr 1e-5 \\"
echo "    --output-dir /workspace/outputs/faster-whisper-ghanaian"
echo ""
echo "Training will stream data from Hetzner (no full download needed!)"
echo ""
echo "Monitor training:"
echo "  - TensorBoard: tensorboard --logdir /workspace/outputs/faster-whisper-ghanaian"
echo "  - GPU: nvidia-smi"
echo ""
echo "================================================================"
