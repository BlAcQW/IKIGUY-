#!/bin/bash
# Check status of all TTS services

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

check_port() {
    local port=$1
    local name=$2

    if nc -z localhost "$port" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $name (port $port) - Running"

        # Try to get health status if endpoint exists
        if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$port/health" 2>/dev/null | grep -q "200"; then
            echo -e "  ${GREEN}└─${NC} Health check: OK"
        fi
    else
        echo -e "${RED}✗${NC} $name (port $port) - Not running"
    fi
}

echo "=== TTS Services Status ==="
echo ""

echo "Local GPU Services:"
check_port 8001 "MeloTTS"
check_port 8003 "OpenVoice"
check_port 8004 "Chatterbox"
check_port 8005 "Coqui TTS"
check_port 8010 "Kokoro TTS"

echo ""
echo "RunPod GPU Services (via SSH tunnel):"
check_port 8002 "F5-TTS"
check_port 8006 "StyleTTS2"
check_port 8008 "Kyutai/Moshi"

echo ""
echo "Other Services:"
check_port 8007 "Open WebUI"
check_port 8009 "Crawl4AI"

echo ""
echo "=== GPU Status ==="
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits | \
    while IFS=, read -r idx name util mem_used mem_total; do
        echo -e "GPU $idx: $name"
        echo -e "  Utilization: ${util}%"
        echo -e "  Memory: ${mem_used}MB / ${mem_total}MB"
    done
else
    echo "nvidia-smi not found"
fi

echo ""
echo "=== Docker Containers ==="
if command -v docker &> /dev/null; then
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "tts|crawl|webui" || echo "No TTS containers running"
else
    echo "Docker not found"
fi
