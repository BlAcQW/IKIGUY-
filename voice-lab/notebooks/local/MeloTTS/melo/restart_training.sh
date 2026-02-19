#!/bin/bash
# Restart training script with optimized settings for Twi TTS

# Kill existing training process
echo "Stopping existing training processes..."
pkill -f "train.py --c data/twi_full/config.json"
sleep 5

# Set CUDA memory allocation settings
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

# Activate venv
source /opt/kasaai/apps/venv/bin/activate

# Change to melo directory
cd /opt/kasaai/apps/voice-lab/notebooks/local/MeloTTS/melo

# Use random port to avoid conflicts
PORT=$((RANDOM + 30000))

echo "========================================="
echo "Starting MeloTTS Training - Twi Full Dataset"
echo "Config: data/twi_full/config.json"
echo "GPU: 1"
echo "Port: $PORT"
echo "Memory optimization: enabled"
echo "========================================="

# Run training with optimized settings
nohup torchrun --nproc_per_node=1 \
    --master_port=$PORT \
    train.py --c data/twi_full/config.json --model twi_full \
    > train_optimized.log 2>&1 &

echo "Training started! PID: $!"
echo "Monitor with: tail -f train_optimized.log"
echo "Check training log: tail -f logs/twi_full/train.log"
