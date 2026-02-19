#!/bin/bash
# Modified training script for Twi - no auto-restart loop
CONFIG=$1
GPUS=$2
MODEL_NAME=$(basename "$(dirname $CONFIG)")

# Activate venv
source /opt/kasaai/apps/venv/bin/activate

# Use random port to avoid conflicts
PORT=$((RANDOM + 30000))

echo "Starting training with:"
echo "  Config: $CONFIG"
echo "  GPUs: $GPUS"
echo "  Model: $MODEL_NAME"
echo "  Port: $PORT"

torchrun --nproc_per_node=$GPUS \
        --master_port=$PORT \
    train.py --c $CONFIG --model $MODEL_NAME
