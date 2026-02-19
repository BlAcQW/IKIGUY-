#!/bin/bash

# Download Base LLM Models to Ollama
# Models for fine-tuning Ghanaian language AI

set -e

echo "📥 Downloading Base LLM Models to Ollama"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Ollama is running
if ! sudo docker ps | grep -q ollama; then
    echo -e "${YELLOW}⚠ Ollama container is not running${NC}"
    echo "Starting Ollama..."
    cd /opt/kasaai/apps/tts-deployment
    sudo docker-compose -f docker-compose.local.yml up -d ollama
    sleep 10
fi

echo -e "${GREEN}✓ Ollama is running${NC}"
echo ""

# Function to download a model
download_model() {
    local model=$1
    local size=$2
    local description=$3

    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}📥 Downloading: $model${NC}"
    echo -e "${BLUE}Size: $size | $description${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    sudo docker exec ollama ollama pull $model

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Successfully downloaded: $model${NC}"
    else
        echo -e "${YELLOW}⚠ Failed to download: $model${NC}"
    fi
    echo ""
}

# Download recommended models for Ghanaian AI
echo -e "${YELLOW}Phase 1: Essential Models for Fine-tuning${NC}"
echo "These are the base models we'll fine-tune for Ghanaian languages"
echo ""

download_model "llama3.2:3b" "2.0GB" "Fast, general-purpose (will fine-tune for Twi)"
download_model "aya:8b" "4.8GB" "Multilingual including African languages"
download_model "mistral:7b" "4.1GB" "High-quality reasoning"

echo ""
echo -e "${YELLOW}Phase 2: Optional Testing Model${NC}"
echo ""

# Ask if user wants to download the small test model
read -p "Download Llama 3.2 1B for quick testing? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    download_model "llama3.2:1b" "1.3GB" "Smallest, fastest (for testing)"
fi

echo ""
echo -e "${YELLOW}Phase 3: Additional Models (Optional)${NC}"
echo ""

# Ask if user wants additional models
read -p "Download additional models (Qwen, DeepSeek Coder)? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    download_model "qwen2.5:7b" "4.7GB" "Alternative multilingual model"
    download_model "deepseek-coder:6.7b" "3.8GB" "Code generation specialist"
fi

# Summary
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓ Download Complete!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# List downloaded models
echo "📦 Downloaded Models:"
echo ""
sudo docker exec ollama ollama list

echo ""
echo "💾 Disk Usage:"
df -h / | grep -E "Filesystem|/$"

echo ""
echo "🌐 Access Models:"
echo "  - Open WebUI: https://openwebui.ailabsafrica.com"
echo "  - LLM Lab:    https://kasaai.ailabsafrica.com/llm-lab"
echo "  - Ollama API: https://ollama.ailabsafrica.com"
echo ""
echo "🧪 Test a model:"
echo "  sudo docker exec ollama ollama run llama3.2:3b 'What is Ghana known for?'"
echo ""
echo "📚 Next Steps:"
echo "  1. Test models in Open WebUI"
echo "  2. Collect Ghanaian training data (1,500+ samples)"
echo "  3. Rent RunPod GPU for fine-tuning"
echo "  4. See: LLM_FINETUNING_PLAN.md"
echo ""
