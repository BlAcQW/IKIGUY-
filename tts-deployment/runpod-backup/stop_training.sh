#!/bin/bash
# Stop Whisper training

if [ -f /workspace/whisper-african-training/training.pid ]; then
    PID=$(cat /workspace/whisper-african-training/training.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "Stopping training (PID: $PID)..."
        kill $PID
        echo "✅ Training stopped"
        rm /workspace/whisper-african-training/training.pid
    else
        echo "⚠️ Training process not running"
    fi
else
    echo "⚠️ No training.pid file found"
fi
