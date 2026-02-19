#!/bin/bash
# Whisper Small Training Script for RunPod
# Optimized for Twi-Fante ASR

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║        Whisper Small Training on RunPod - Twi-Fante          ║"
echo "╚═══════════════════════════════════════════════════════════════╝"

# Configuration
WORKSPACE="/workspace"
DATA_DIR="${WORKSPACE}/data/twi_asr"
CHECKPOINT_DIR="${WORKSPACE}/checkpoints/whisper_twi"
LOG_DIR="${WORKSPACE}/logs"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create directories
mkdir -p "${CHECKPOINT_DIR}"
mkdir -p "${LOG_DIR}"

# Print system info
echo ""
echo "📊 System Information:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
NUM_GPUS=$(nvidia-smi --query-gpu=count --format=csv,noheader | head -1)
echo "Number of GPUs: ${NUM_GPUS}"
echo "CUDA Version: $(nvcc --version | grep release | awk '{print $5}' | cut -c2-)"
echo "PyTorch Version: $(python -c 'import torch; print(torch.__version__)')"
echo "Transformers Version: $(python -c 'import transformers; print(transformers.__version__)')"
echo ""

# Check if data exists
if [ ! -d "${DATA_DIR}" ]; then
    echo "⚠️  Local data directory not found: ${DATA_DIR}"
    echo "Will download Mozilla Common Voice Twi dataset automatically"
    echo ""
fi

# Check WandB
if [ ! -z "${WANDB_API_KEY}" ]; then
    echo "🔗 Weights & Biases configured"
    wandb login "${WANDB_API_KEY}"
else
    echo "ℹ️  WANDB_API_KEY not set, using TensorBoard only"
fi

# Start TensorBoard
echo "📈 Starting TensorBoard on port 6006..."
tensorboard --logdir="${CHECKPOINT_DIR}" --port=6006 --bind_all &
TENSORBOARD_PID=$!
echo "TensorBoard PID: ${TENSORBOARD_PID}"
echo "Access TensorBoard at: http://<POD_IP>:6006"
echo ""

# Estimate training time
echo "📊 Training Estimates (Whisper Small):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Model: openai/whisper-small (244M parameters)"
echo "Estimated time: ~200 hours (8 days)"
echo "Estimated cost (RTX 4090 @ \$0.34/hr): ~\$68"
echo "Batch size: 16 (FP16 enabled)"
echo "Epochs: 10"
echo ""

echo "🚀 Starting Training..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Press Ctrl+C to stop training (will save checkpoint)"
echo ""

# Run training
python "${SCRIPT_DIR}/train_whisper.py" 2>&1 | tee "${LOG_DIR}/whisper_training_$(date +%Y%m%d_%H%M%S).log"

TRAINING_EXIT_CODE=$?

# Stop TensorBoard
if [ ! -z "${TENSORBOARD_PID}" ]; then
    kill "${TENSORBOARD_PID}" 2>/dev/null || true
fi

# Check result
if [ ${TRAINING_EXIT_CODE} -eq 0 ]; then
    echo ""
    echo "✅ Training completed successfully!"
    echo ""
    echo "📦 Outputs:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Checkpoints: ${CHECKPOINT_DIR}"
    echo "Final model: ${CHECKPOINT_DIR}/final_model"
    echo "Logs: ${LOG_DIR}"
    echo ""
    echo "🎉 Next Steps:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "1. Test inference: python test_inference.py --model ${CHECKPOINT_DIR}/final_model"
    echo "2. Download checkpoint: scp -r root@<POD_IP>:${CHECKPOINT_DIR}/final_model ./"
    echo "3. Deploy to RunPod Serverless"
    echo "4. Integrate with your backend"
else
    echo ""
    echo "⚠️  Training exited with code ${TRAINING_EXIT_CODE}"
    echo "Check logs at: ${LOG_DIR}"
fi

exit ${TRAINING_EXIT_CODE}
