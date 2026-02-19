#!/bin/bash
# Deploy Whisper ASR to RunPod
# This script deploys the Whisper ASR service to RunPod GPU instance

set -e

echo "🚀 Deploying Whisper ASR to RunPod..."

# RunPod connection details
RUNPOD_SSH="root@194.68.245.121"
RUNPOD_SSH_PORT="22153"
RUNPOD_SSH_KEY="$HOME/.ssh/id_ed25519"

# Check if SSH key exists
if [ ! -f "$RUNPOD_SSH_KEY" ]; then
    echo "❌ SSH key not found at $RUNPOD_SSH_KEY"
    echo "Please ensure your SSH key is set up for RunPod access"
    exit 1
fi

echo "📦 Building Whisper ASR Docker image..."
cd /opt/kasaai/apps/tts-deployment
docker build -t whisper-asr:latest ./docker/whisper-asr

echo "📤 Copying files to RunPod..."
# Copy docker-compose and app files
scp -P $RUNPOD_SSH_PORT -i $RUNPOD_SSH_KEY \
    docker-compose.runpod.yml \
    $RUNPOD_SSH:/workspace/tts-deployment/

# Copy whisper-asr directory
scp -P $RUNPOD_SSH_PORT -i $RUNPOD_SSH_KEY \
    -r docker/whisper-asr \
    $RUNPOD_SSH:/workspace/tts-deployment/docker/

echo "🔧 Deploying on RunPod..."
ssh -p $RUNPOD_SSH_PORT -i $RUNPOD_SSH_KEY $RUNPOD_SSH << 'EOF'
cd /workspace/tts-deployment

# Stop existing whisper-asr if running
docker-compose -f docker-compose.runpod.yml stop whisper-asr 2>/dev/null || true
docker-compose -f docker-compose.runpod.yml rm -f whisper-asr 2>/dev/null || true

# Build and start whisper-asr
docker-compose -f docker-compose.runpod.yml build whisper-asr
docker-compose -f docker-compose.runpod.yml up -d whisper-asr

# Wait for service to start
sleep 5

# Check logs
echo "📋 Checking logs..."
docker logs whisper-asr --tail 20

# Test health endpoint
echo "🏥 Testing health endpoint..."
curl -s http://localhost:8020/health | jq . || echo "Health check failed"
EOF

echo ""
echo "✅ Whisper ASR deployment complete!"
echo ""
echo "📝 Next steps:"
echo "1. Expose port 8020 on RunPod dashboard: https://www.runpod.io/console/pods"
echo "2. Update nginx config (already done)"
echo "3. Reload nginx: sudo systemctl reload nginx"
echo "4. Stop old whisper-api service: sudo systemctl stop kasaai-whisper-api"
echo ""
echo "🌐 RunPod Proxy URL: https://jzfmzviw26huka-8020.proxy.runpod.net"
echo "🌐 Public URL: https://whisper.ailabsafrica.com"

