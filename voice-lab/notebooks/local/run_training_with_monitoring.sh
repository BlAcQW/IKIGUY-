#!/bin/bash
#
# Run MeloTTS Training with Monitoring - FIXED VERSION v2.0
#
# This script:
# - Runs the fixed training script
# - Logs output to file
# - Monitors GPU memory
# - Can be run in background with nohup
#

# Configuration
SCRIPT_PATH="/home/dev/local/020_melo_tts_twi_fixed.py"
LOG_FILE="/home/dev/training_logs/twi_tts_v2_fixed_$(date +%Y%m%d_%H%M%S).log"
GPU_MONITOR_LOG="/home/dev/training_logs/gpu_monitor_$(date +%Y%m%d_%H%M%S).log"

# Create log directory
mkdir -p /home/dev/training_logs

echo "================================================================================================"
echo "MeloTTS Twi Training - FIXED VERSION v2.0"
echo "================================================================================================"
echo "Training script: $SCRIPT_PATH"
echo "Training log:    $LOG_FILE"
echo "GPU monitor log: $GPU_MONITOR_LOG"
echo "================================================================================================"
echo ""
echo "CRITICAL FIXES IN THIS VERSION:"
echo "  ✓ Using 16kHz audio (no resampling - 20x faster evaluation!)"
echo "  ✓ Increased to 100k training samples (from 50k)"
echo "  ✓ Reduced to 2k validation samples (faster evaluation)"
echo "  ✓ Loss modules properly initialized on GPU"
echo "  ✓ Memory cleanup after each evaluation"
echo ""
echo "ESTIMATED RUNTIME:"
echo "  - Total steps: ~31,250 (100k samples, 10 epochs)"
echo "  - Evaluation: Every 2000 steps (fast - no slowdown!)"
echo "  - Expected duration: ~50-60 hours (may early stop at ~epoch 3)"
echo ""
echo "================================================================================================"
echo ""

# Start GPU monitoring in background
(
    echo "Time,GPU_Util%,Memory_Used_MB,Memory_Total_MB,Temperature_C" > "$GPU_MONITOR_LOG"
    while true; do
        timestamp=$(date "+%Y-%m-%d %H:%M:%S")
        gpu_stats=$(nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits 2>/dev/null)
        if [ $? -eq 0 ]; then
            echo "$timestamp,$gpu_stats" >> "$GPU_MONITOR_LOG"
        fi
        sleep 30  # Monitor every 30 seconds
    done
) &
GPU_MONITOR_PID=$!

echo "GPU monitoring started (PID: $GPU_MONITOR_PID)"
echo "Logs will be written to: $GPU_MONITOR_LOG"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "================================================================================================"
    echo "Training stopped. Cleaning up..."
    echo "================================================================================================"
    kill $GPU_MONITOR_PID 2>/dev/null
    echo "GPU monitoring stopped"
    echo "Training log: $LOG_FILE"
    echo "GPU monitor log: $GPU_MONITOR_LOG"
}

trap cleanup EXIT INT TERM

# Run training with logging
echo "Starting training..."
echo "Press Ctrl+C to stop"
echo "Logs are being written to: $LOG_FILE"
echo ""

python3 "$SCRIPT_PATH" 2>&1 | tee "$LOG_FILE"

exit_code=$?

echo ""
echo "================================================================================================"
echo "Training finished with exit code: $exit_code"
echo "================================================================================================"
echo "Logs saved to: $LOG_FILE"
echo "GPU monitor saved to: $GPU_MONITOR_LOG"
echo ""

if [ $exit_code -eq 0 ]; then
    echo "✓ Training completed successfully!"
    echo "Model saved to: /opt/kasaai/apps/voice-lab/models/melo_tts_twi_v2_fixed"
else
    echo "✗ Training failed. Check logs for errors."
fi

exit $exit_code
