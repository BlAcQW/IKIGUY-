#!/bin/bash
#
# Run MeloTTS Training with Monitoring - MEMORY EFFICIENT v2.1
#
# This script:
# - Runs the memory-efficient training script
# - Logs output to file
# - Monitors GPU and RAM usage
# - Can be run in background with nohup
#
# IMPORTANT: Consider stopping K3s first to free RAM:
#   sudo systemctl stop k3s
#

# Configuration
SCRIPT_PATH="/home/dev/local/021_melo_tts_twi_memory_efficient.py"
LOG_FILE="/home/dev/training_logs/twi_tts_v2.1_$(date +%Y%m%d_%H%M%S).log"
GPU_MONITOR_LOG="/home/dev/training_logs/gpu_monitor_$(date +%Y%m%d_%H%M%S).log"
RAM_MONITOR_LOG="/home/dev/training_logs/ram_monitor_$(date +%Y%m%d_%H%M%S).log"

# Create log directory
mkdir -p /home/dev/training_logs

echo "================================================================================================"
echo "MeloTTS Twi Training - MEMORY EFFICIENT VERSION v2.1"
echo "================================================================================================"
echo "Training script: $SCRIPT_PATH"
echo "Training log:    $LOG_FILE"
echo "GPU monitor log: $GPU_MONITOR_LOG"
echo "RAM monitor log: $RAM_MONITOR_LOG"
echo "================================================================================================"
echo ""
echo "CRITICAL FIXES IN THIS VERSION:"
echo "  ✓ Lazy dataset loading (processes on-the-fly - no RAM cache!)"
echo "  ✓ Using 16kHz audio (no resampling - 20x faster evaluation!)"
echo "  ✓ 50k training samples (reduced for memory safety)"
echo "  ✓ 2k validation samples (faster evaluation)"
echo "  ✓ Loss modules properly initialized on GPU"
echo "  ✓ Memory cleanup after each evaluation"
echo ""
echo "MEMORY USAGE:"
echo "  - v2.0 (failed): ~63GB RAM (OOM crash during preprocessing)"
echo "  - v2.1 (this):   ~10-15GB RAM (lazy loading, stable)"
echo ""
echo "ESTIMATED RUNTIME:"
echo "  - Total steps: ~15,625 (50k samples, 10 epochs)"
echo "  - Evaluation: Every 2000 steps (fast - no slowdown!)"
echo "  - Expected duration: ~30-40 hours (may early stop at ~epoch 3-5)"
echo ""
echo "RECOMMENDATION:"
echo "  Stop K3s first to free ~30GB RAM:"
echo "    sudo systemctl stop k3s"
echo ""
echo "================================================================================================"
echo ""

# Check if K3s is running
if systemctl is-active --quiet k3s; then
    echo "⚠️  WARNING: K3s is still running and consuming RAM!"
    echo "   Consider stopping it first: sudo systemctl stop k3s"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted. Stop K3s first, then re-run this script."
        exit 1
    fi
fi

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

# Start RAM monitoring in background
(
    echo "Time,Used_GB,Available_GB,Total_GB,Used_Percent" > "$RAM_MONITOR_LOG"
    while true; do
        timestamp=$(date "+%Y-%m-%d %H:%M:%S")
        ram_stats=$(free -g | awk 'NR==2 {printf "%d,%d,%d,%.1f", $3, $7, $2, ($3/$2)*100}')
        echo "$timestamp,$ram_stats" >> "$RAM_MONITOR_LOG"
        sleep 30  # Monitor every 30 seconds
    done
) &
RAM_MONITOR_PID=$!

echo "Monitoring started:"
echo "  GPU monitor PID: $GPU_MONITOR_PID"
echo "  RAM monitor PID: $RAM_MONITOR_PID"
echo "  GPU log: $GPU_MONITOR_LOG"
echo "  RAM log: $RAM_MONITOR_LOG"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "================================================================================================"
    echo "Training stopped. Cleaning up..."
    echo "================================================================================================"
    kill $GPU_MONITOR_PID 2>/dev/null
    kill $RAM_MONITOR_PID 2>/dev/null
    echo "Monitoring stopped"
    echo "Training log: $LOG_FILE"
    echo "GPU monitor log: $GPU_MONITOR_LOG"
    echo "RAM monitor log: $RAM_MONITOR_LOG"
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
echo "RAM monitor saved to: $RAM_MONITOR_LOG"
echo ""

if [ $exit_code -eq 0 ]; then
    echo "✓ Training completed successfully!"
    echo "Model saved to: /opt/kasaai/apps/voice-lab/models/melo_tts_twi_v2_memory_efficient"
else
    echo "✗ Training failed. Check logs for errors."
fi

echo ""
echo "If you stopped K3s, restart it now:"
echo "  sudo systemctl start k3s"
echo ""

exit $exit_code
