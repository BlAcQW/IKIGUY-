#!/bin/bash
# Monitoring script for Whisper training

echo '=================================================='
echo '📊 Whisper Training Monitor'
echo '=================================================='
echo ''

# Check if training is running
if [ -f /workspace/whisper-african-training/training.pid ]; then
    PID=$(cat /workspace/whisper-african-training/training.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo '✅ Training is running (PID: '$PID')'
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
