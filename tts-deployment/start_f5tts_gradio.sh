#!/bin/bash
###############################################################################
# F5-TTS Gradio Launcher for RunPod
#
# This script starts the official F5-TTS Gradio web interface on RunPod
#
# Usage (on RunPod):
#   bash start_f5tts_gradio.sh
#
# Or download and run directly:
#   curl -o /tmp/start_f5.sh https://f5tts.ailabsafrica.com/start_f5tts_gradio.sh
#   bash /tmp/start_f5.sh
###############################################################################

set -e

echo "=========================================="
echo "  F5-TTS Gradio Launcher"
echo "=========================================="
echo ""

# Configuration
PORT=8002
HOST="0.0.0.0"
WORKSPACE="/workspace"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if F5-TTS is installed
echo -e "${YELLOW}[1/4]${NC} Checking F5-TTS installation..."
if command -v f5-tts_infer-gradio &> /dev/null; then
    echo -e "${GREEN}✓${NC} F5-TTS is installed"
else
    echo -e "${RED}✗${NC} F5-TTS not found. Installing..."
    pip install f5-tts -q
fi

# Check if running processes exist
echo -e "${YELLOW}[2/4]${NC} Checking for existing F5-TTS processes..."
EXISTING_PID=$(pgrep -f "f5-tts_infer-gradio" || echo "")

if [ -n "$EXISTING_PID" ]; then
    echo -e "${YELLOW}⚠${NC} Found existing F5-TTS process (PID: $EXISTING_PID)"
    echo -e "${YELLOW}⚠${NC} Killing existing process..."
    kill $EXISTING_PID 2>/dev/null || true
    sleep 2
fi

# Check port availability
echo -e "${YELLOW}[3/4]${NC} Checking port $PORT..."
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠${NC} Port $PORT is in use. Killing process..."
    lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# Start F5-TTS Gradio
echo -e "${YELLOW}[4/4]${NC} Launching F5-TTS Gradio interface..."
echo -e "${GREEN}➜${NC} Command: f5-tts_infer-gradio --port $PORT --host $HOST"
echo ""

# Launch in background with log output
nohup f5-tts_infer-gradio --port $PORT --host $HOST > /tmp/f5tts_gradio.log 2>&1 &
GRADIO_PID=$!

echo -e "${GREEN}✓${NC} F5-TTS Gradio started (PID: $GRADIO_PID)"
echo ""
echo "=========================================="
echo "  Access Information"
echo "=========================================="
echo -e "${GREEN}Local (RunPod):${NC}   http://localhost:$PORT"
echo -e "${GREEN}Tunneled:${NC}         https://f5tts.ailabsafrica.com"
echo ""
echo -e "${YELLOW}Logs:${NC} tail -f /tmp/f5tts_gradio.log"
echo "=========================================="
echo ""

# Wait a bit and check if process is still running
sleep 5
if ps -p $GRADIO_PID > /dev/null; then
    echo -e "${GREEN}✓✓✓ F5-TTS Gradio is running successfully!${NC}"
    echo ""
    echo "The interface is now accessible via the SSH tunnel."
else
    echo -e "${RED}✗✗✗ F5-TTS Gradio failed to start${NC}"
    echo ""
    echo "Check logs: tail -f /tmp/f5tts_gradio.log"
    exit 1
fi
