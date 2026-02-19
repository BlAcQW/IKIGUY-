#!/bin/bash
# Automated Storage Cleanup for TTS Services
# Calls cleanup endpoint for all running TTS services

set -e

# Configuration
MAX_AGE_HOURS=${MAX_AGE_HOURS:-48}
LOG_FILE="/var/log/tts_cleanup.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] [WARN]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] [ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] [INFO]${NC} $1" | tee -a "$LOG_FILE"
}

# Service endpoints (local)
LOCAL_SERVICES=(
    "melotts:8001"
    "openvoice:8003"
    "chatterbox:8004"
    "coqui:8005"
    "kokoro:8010"
)

# Service endpoints (RunPod via tunnels)
RUNPOD_SERVICES=(
    "f5tts:8002"
    "styletts:8006"
    "kyutai:8008"
)

cleanup_service() {
    local service_name=$1
    local port=$2
    local url="http://localhost:${port}/cleanup"

    log_info "Cleaning up ${service_name}..."

    # Check if service is running
    if ! nc -z localhost "$port" 2>/dev/null; then
        log_warn "${service_name} (port ${port}) is not reachable, skipping..."
        return 1
    fi

    # Call cleanup endpoint
    response=$(curl -s -X DELETE "$url" -w "\n%{http_code}" 2>&1)
    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" -eq 200 ]; then
        # Try to parse JSON response
        if command -v jq &> /dev/null; then
            deleted=$(echo "$body" | jq -r '.deleted // "unknown"')
            message=$(echo "$body" | jq -r '.message // ""')
            log "${service_name}: ✓ ${message} (${deleted} files)"
        else
            log "${service_name}: ✓ Cleanup successful"
        fi
    else
        log_error "${service_name}: Failed (HTTP ${http_code})"
        return 1
    fi
}

# Main execution
log "========================================="
log "Starting TTS Storage Cleanup"
log "Max file age: ${MAX_AGE_HOURS} hours"
log "========================================="

total_services=0
successful_cleanups=0
failed_cleanups=0

# Clean local services
log_info "Cleaning local GPU services..."
for service in "${LOCAL_SERVICES[@]}"; do
    IFS=':' read -r name port <<< "$service"
    ((total_services++))
    if cleanup_service "$name" "$port"; then
        ((successful_cleanups++))
    else
        ((failed_cleanups++))
    fi
done

# Clean RunPod services (if tunnels are active)
log_info "Cleaning RunPod GPU services (via SSH tunnels)..."
for service in "${RUNPOD_SERVICES[@]}"; do
    IFS=':' read -r name port <<< "$service"
    ((total_services++))
    if cleanup_service "$name" "$port"; then
        ((successful_cleanups++))
    else
        ((failed_cleanups++))
    fi
done

# Summary
log "========================================="
log "Cleanup Summary:"
log "  Total services: ${total_services}"
log "  Successful: ${successful_cleanups}"
log "  Failed/Skipped: ${failed_cleanups}"
log "========================================="

# Check Docker volume usage
if command -v docker &> /dev/null; then
    log_info "Docker volume usage:"
    docker system df -v 2>/dev/null | grep "tts-deployment" || log_warn "No TTS volumes found"
fi

# Exit with error if any cleanups failed
if [ "$failed_cleanups" -gt 0 ]; then
    exit 1
fi

exit 0
