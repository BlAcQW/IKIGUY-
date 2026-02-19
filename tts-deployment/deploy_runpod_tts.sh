#!/bin/bash

###############################################################################
# RunPod TTS Deployment Script
# Deploys F5-TTS and StyleTTS2 to RunPod GPU instance
#
# Usage: ./deploy_runpod_tts.sh [service_name]
# Options:
#   - f5tts: Deploy only F5-TTS
#   - styletts2: Deploy only StyleTTS2
#   - all: Deploy both services (default)
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
RUNPOD_SSH="jzfmzviw26huka-644113c7@ssh.runpod.io"
RUNPOD_PORT="22"
WORKSPACE="/workspace"
LOCAL_DIR="/opt/kasaai/apps/tts-deployment"

# Functions
print_header() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check SSH connectivity
check_ssh_connection() {
    print_header "Checking SSH Connection to RunPod"

    if ssh -T -p "$RUNPOD_PORT" "$RUNPOD_SSH" "echo 'Connection successful'" 2>/dev/null | grep -q "Connection successful"; then
        print_success "SSH connection to RunPod verified"
        return 0
    else
        print_error "Cannot connect to RunPod via SSH"
        print_info "Please ensure your SSH key is configured and the RunPod instance is running"
        exit 1
    fi
}

# Deploy F5-TTS
deploy_f5tts() {
    print_header "Deploying F5-TTS"

    # Copy F5-TTS files
    print_info "Copying F5-TTS files to RunPod..."
    ssh -T -p "$RUNPOD_PORT" "$RUNPOD_SSH" "mkdir -p $WORKSPACE/tts-deployment/docker/f5tts"

    scp -P "$RUNPOD_PORT" \
        "$LOCAL_DIR/docker/f5tts/app.py" \
        "$LOCAL_DIR/docker/f5tts/Dockerfile" \
        "$RUNPOD_SSH:$WORKSPACE/tts-deployment/docker/f5tts/"

    print_success "F5-TTS files copied"

    # Check if F5-TTS is already running
    print_info "Checking if F5-TTS service is running..."
    if ssh -T -p "$RUNPOD_PORT" "$RUNPOD_SSH" "curl -s http://localhost:8002/health" &>/dev/null; then
        print_warning "F5-TTS is already running on port 8002"
        print_info "To restart, manually stop the existing service first"
    else
        print_info "F5-TTS is not running. Manual startup required."
        print_info "Command: cd $WORKSPACE/tts-deployment/docker/f5tts && python3 app.py"
    fi
}

# Deploy StyleTTS2
deploy_styletts2() {
    print_header "Deploying StyleTTS2"

    # Copy StyleTTS2 files
    print_info "Copying StyleTTS2 files to RunPod..."
    ssh -T -p "$RUNPOD_PORT" "$RUNPOD_SSH" "mkdir -p $WORKSPACE/tts-deployment/docker/styletts2"

    scp -P "$RUNPOD_PORT" \
        "$LOCAL_DIR/docker/styletts2/app.py" \
        "$LOCAL_DIR/docker/styletts2/Dockerfile" \
        "$LOCAL_DIR/docker/styletts2/requirements.txt" \
        "$RUNPOD_SSH:$WORKSPACE/tts-deployment/docker/styletts2/"

    print_success "StyleTTS2 files copied"

    # Install dependencies on RunPod
    print_info "Installing StyleTTS2 dependencies..."
    ssh -T -p "$RUNPOD_PORT" "$RUNPOD_SSH" << 'EOF'
cd /workspace/tts-deployment/docker/styletts2
pip3 install --no-cache-dir -r requirements.txt
EOF

    if [ $? -eq 0 ]; then
        print_success "StyleTTS2 dependencies installed"
    else
        print_error "Failed to install StyleTTS2 dependencies"
        exit 1
    fi

    # Check if StyleTTS2 is already running
    print_info "Checking if StyleTTS2 service is running..."
    if ssh -T -p "$RUNPOD_PORT" "$RUNPOD_SSH" "curl -s http://localhost:8006/health" &>/dev/null; then
        print_warning "StyleTTS2 is already running on port 8006"
        print_info "To restart, manually stop the existing service first"
    else
        print_info "StyleTTS2 is not running. Ready for manual startup."
        print_info "Command: cd $WORKSPACE/tts-deployment/docker/styletts2 && python3 app.py"
    fi
}

# Show service status
show_service_status() {
    print_header "Service Status"

    # Check F5-TTS
    if ssh -T -p "$RUNPOD_PORT" "$RUNPOD_SSH" "curl -s http://localhost:8002/health" &>/dev/null; then
        F5_STATUS=$(ssh -T -p "$RUNPOD_PORT" "$RUNPOD_SSH" "curl -s http://localhost:8002/health" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
        print_success "F5-TTS: Running (Port 8002) - Status: $F5_STATUS"
    else
        print_warning "F5-TTS: Not running"
    fi

    # Check StyleTTS2
    if ssh -T -p "$RUNPOD_PORT" "$RUNPOD_SSH" "curl -s http://localhost:8006/health" &>/dev/null; then
        STYLE_STATUS=$(ssh -T -p "$RUNPOD_PORT" "$RUNPOD_SSH" "curl -s http://localhost:8006/health" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
        print_success "StyleTTS2: Running (Port 8006) - Status: $STYLE_STATUS"
    else
        print_warning "StyleTTS2: Not running"
    fi
}

# Main execution
main() {
    local service="${1:-all}"

    print_header "RunPod TTS Deployment"
    print_info "Service to deploy: $service"
    echo ""

    # Check SSH connection
    check_ssh_connection
    echo ""

    # Deploy based on selection
    case "$service" in
        f5tts)
            deploy_f5tts
            ;;
        styletts2)
            deploy_styletts2
            ;;
        all)
            deploy_f5tts
            echo ""
            deploy_styletts2
            ;;
        *)
            print_error "Invalid service name: $service"
            print_info "Valid options: f5tts, styletts2, all"
            exit 1
            ;;
    esac

    echo ""
    show_service_status

    echo ""

    # Cleanup dangling images
    print_header "Cleaning Up Docker Images"
    print_info "Removing dangling Docker images to free up space..."
    ssh -T -p "$RUNPOD_PORT" "$RUNPOD_SSH" "docker image prune -f" 2>/dev/null
    if [ $? -eq 0 ]; then
        print_success "Docker cleanup completed"
    else
        print_warning "Docker cleanup skipped (may not have permission or docker not available)"
    fi

    echo ""
    print_header "Deployment Complete"
    print_info "To start services manually, SSH into RunPod and run:"
    print_info "  F5-TTS:    cd $WORKSPACE/tts-deployment/docker/f5tts && nohup python3 app.py &"
    print_info "  StyleTTS2: cd $WORKSPACE/tts-deployment/docker/styletts2 && nohup python3 app.py &"
    print_info ""
    print_info "To view logs:"
    print_info "  tail -f nohup.out"
}

# Run main function
main "$@"
