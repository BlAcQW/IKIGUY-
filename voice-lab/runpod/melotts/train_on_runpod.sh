#!/bin/bash
# MeloTTS Training Script for RunPod
# Optimized for Twi-Fante Dataset

set -e  # Exit on error

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║          MeloTTS Training on RunPod - Twi-Fante              ║"
echo "╚═══════════════════════════════════════════════════════════════╝"

# Configuration
WORKSPACE="/workspace"
DATA_DIR="${WORKSPACE}/data/twi_full"
CONFIG_FILE="${DATA_DIR}/config.json"
CHECKPOINT_DIR="${WORKSPACE}/checkpoints/twi_melotts"
LOG_DIR="${WORKSPACE}/logs"
MODEL_NAME="twi_melotts"

# GPU Configuration
NUM_GPUS=$(nvidia-smi --query-gpu=count --format=csv,noheader | head -1)
MASTER_PORT=${MASTER_PORT:-29500}

# Create directories
mkdir -p "${CHECKPOINT_DIR}"
mkdir -p "${LOG_DIR}"

# Print system info
echo ""
echo "📊 System Information:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
echo "Number of GPUs: ${NUM_GPUS}"
echo "CUDA Version: $(nvcc --version | grep release | awk '{print $5}' | cut -c2-)"
echo "PyTorch Version: $(python -c 'import torch; print(torch.__version__)')"
echo "CUDA Available: $(python -c 'import torch; print(torch.cuda.is_available())')"
echo ""

# Check if data exists
if [ ! -f "${CONFIG_FILE}" ]; then
    echo "❌ Error: Config file not found at ${CONFIG_FILE}"
    echo "Please upload your Twi-Fante data to ${DATA_DIR}"
    exit 1
fi

if [ ! -f "${DATA_DIR}/train.list" ]; then
    echo "❌ Error: train.list not found at ${DATA_DIR}/train.list"
    exit 1
fi

# Print dataset info
echo "📁 Dataset Information:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
TRAIN_SAMPLES=$(wc -l < "${DATA_DIR}/train.list")
VAL_SAMPLES=$(wc -l < "${DATA_DIR}/val.list")
echo "Training samples: ${TRAIN_SAMPLES}"
echo "Validation samples: ${VAL_SAMPLES}"
echo "Config file: ${CONFIG_FILE}"
echo ""

# Extract training parameters from config
BATCH_SIZE=$(python -c "import json; print(json.load(open('${CONFIG_FILE}'))['train']['batch_size'])")
EPOCHS=$(python -c "import json; print(json.load(open('${CONFIG_FILE}'))['train']['epochs'])")
FP16=$(python -c "import json; print(json.load(open('${CONFIG_FILE}'))['train']['fp16_run'])")
LR=$(python -c "import json; print(json.load(open('${CONFIG_FILE}'))['train']['learning_rate'])")

echo "⚙️  Training Configuration:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Batch Size: ${BATCH_SIZE}"
echo "Epochs: ${EPOCHS}"
echo "FP16 Training: ${FP16}"
echo "Learning Rate: ${LR}"
echo "Checkpoint Dir: ${CHECKPOINT_DIR}"
echo ""

# Initialize WandB (optional)
if [ ! -z "${WANDB_API_KEY}" ]; then
    echo "🔗 Initializing Weights & Biases..."
    wandb login "${WANDB_API_KEY}"
    export WANDB_PROJECT="melotts-twi-fante"
    export WANDB_NAME="twi_melotts_$(date +%Y%m%d_%H%M%S)"
else
    echo "⚠️  WANDB_API_KEY not set, skipping W&B logging"
fi

# Start TensorBoard in background
echo "📈 Starting TensorBoard on port 6006..."
tensorboard --logdir="${LOG_DIR}" --port=6006 --bind_all &
TENSORBOARD_PID=$!
echo "TensorBoard PID: ${TENSORBOARD_PID}"
echo ""

# Change to MeloTTS directory
cd /workspace/MeloTTS/melo || exit 1

# Create symbolic link to data if needed
if [ ! -d "data/twi_full" ]; then
    ln -s "${DATA_DIR}" data/twi_full
fi

# Calculate total training time estimate
STEPS_PER_EPOCH=$((TRAIN_SAMPLES / BATCH_SIZE / NUM_GPUS))
TOTAL_STEPS=$((STEPS_PER_EPOCH * EPOCHS))
# Assume 0.5 seconds per step with FP16 on RTX 4090
ESTIMATED_HOURS=$((TOTAL_STEPS / 2 / 3600))

echo "📊 Training Estimates:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Steps per epoch: ${STEPS_PER_EPOCH}"
echo "Total training steps: ${TOTAL_STEPS}"
echo "Estimated time: ~${ESTIMATED_HOURS} hours ($(echo "scale=1; ${ESTIMATED_HOURS}/24" | bc) days)"
echo "Estimated cost (RTX 4090 @ \$0.34/hr): ~\$$(echo "scale=2; ${ESTIMATED_HOURS}*0.34" | bc)"
echo ""

echo "🚀 Starting Training..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Press Ctrl+C to stop training"
echo ""

# Run training with error handling
set +e  # Don't exit on error for training (allow graceful shutdown)

if [ "${NUM_GPUS}" -gt 1 ]; then
    echo "Training with ${NUM_GPUS} GPUs using torchrun..."
    torchrun \
        --nproc_per_node="${NUM_GPUS}" \
        --master_port="${MASTER_PORT}" \
        train.py \
        --c "data/twi_full/config.json" \
        --model "${MODEL_NAME}" \
        2>&1 | tee "${LOG_DIR}/training_$(date +%Y%m%d_%H%M%S).log"
else
    echo "Training with single GPU..."
    python train.py \
        --c "data/twi_full/config.json" \
        --model "${MODEL_NAME}" \
        2>&1 | tee "${LOG_DIR}/training_$(date +%Y%m%d_%H%M%S).log"
fi

TRAINING_EXIT_CODE=$?

# Stop TensorBoard
if [ ! -z "${TENSORBOARD_PID}" ]; then
    echo "Stopping TensorBoard..."
    kill "${TENSORBOARD_PID}" 2>/dev/null || true
fi

# Check training result
if [ ${TRAINING_EXIT_CODE} -eq 0 ]; then
    echo ""
    echo "✅ Training completed successfully!"
    echo ""
    echo "📦 Outputs:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Checkpoints: ${CHECKPOINT_DIR}"
    echo "Logs: ${LOG_DIR}"
    echo ""
    echo "Latest checkpoint:"
    ls -lht "${CHECKPOINT_DIR}" | head -5
    echo ""
    echo "🎉 Training Summary:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Model: ${MODEL_NAME}"
    echo "Dataset: Twi-Fante (${TRAIN_SAMPLES} training samples)"
    echo "Final checkpoint: $(ls -t ${CHECKPOINT_DIR}/*.pth 2>/dev/null | head -1)"
    echo ""
    echo "Next steps:"
    echo "1. Download checkpoints from ${CHECKPOINT_DIR}"
    echo "2. Test inference with: python inference.py --checkpoint <path> --text 'Akwaaba'"
    echo "3. Deploy to RunPod Serverless for production"
else
    echo ""
    echo "⚠️  Training exited with code ${TRAINING_EXIT_CODE}"
    echo "Check logs at: ${LOG_DIR}"
fi

exit ${TRAINING_EXIT_CODE}
