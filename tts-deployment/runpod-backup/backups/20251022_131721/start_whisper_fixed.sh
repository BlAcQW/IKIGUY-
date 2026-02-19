#!/bin/bash
cd /workspace

# Disable torchcodec in datasets
export DATASETS_AUDIO_BACKEND=soundfile

python3 runpod_whisper_african_qlora_streaming.py > whisper_training.log 2>&1 &
echo $! > whisper_training.pid
echo "Training started with PID: $(cat whisper_training.pid)"
