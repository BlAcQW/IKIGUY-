#!/bin/bash
# Whisper Training with Environment Configuration

# Set all environment variables
export TMPDIR=/workspace/tmp
export TEMP=/workspace/tmp
export TMP=/workspace/tmp
export HF_HOME=/workspace/.cache/huggingface
export WANDB_DIR=/workspace/.cache/wandb
export TRANSFORMERS_CACHE=/workspace/.cache/huggingface/transformers
export HF_DATASETS_CACHE=/workspace/.cache/huggingface/datasets
export HF_TOKEN=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
export WANDB_API_KEY=4945245393f4e0b9997521b6bbfa8800e05ded8f

# Activate venv
source /workspace/venv/bin/activate

# Run training
cd /workspace/whisper-african-training
nohup python /workspace/whisper-african-training/runpod_whisper_african_qlora.py \
  --output_dir /workspace/whisper-african-training/outputs/whisper-small-african \
  --use_wandb \
  --wandb_project whisper-african-qlora \
  --wandb_run_name phase1-hausa-yoruba-igbo-$(date +%Y%m%d-%H%M%S) \
  --push_to_hub \
  --hub_model_id ailabsafrica/whisper-small-african \
  > /workspace/whisper-african-training/training.log 2>&1 &

echo $! > /workspace/whisper-african-training/training.pid
echo "Training started with PID: $(cat /workspace/whisper-african-training/training.pid)"
echo ""
echo "Monitor with: tail -f /workspace/whisper-african-training/training.log"
