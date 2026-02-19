#!/bin/bash
###############################################################################
# Unified Auto-Restart Script for All TTS Services
#
# This script automatically detects and restarts unhealthy TTS services
# from both local Docker and RunPod deployments.
#
# Usage:
#   ./auto_restart_all_tts.sh [--local-only|--runpod-only] [--dry-run]
#
# Examples:
#   ./auto_restart_all_tts.sh                  # Check and restart all services
#   ./auto_restart_all_tts.sh --local-only     # Only check local services
#   ./auto_restart_all_tts.sh --runpod-only    # Only check RunPod services
#   ./auto_restart_all_tts.sh --dry-run        # Show what would be restarted
#
###############################################################################

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Configuration
LOG_FILE="/var/log/tts/auto_restart_all.log"
LOCAL_ONLY=false
RUNPOD_ONLY=false
DRY_RUN_FLAG=""

# Parse arguments
for arg in "$@"; do
    case $arg in
        --local-only)
            LOCAL_ONLY=true
            shift
            ;;
        --runpod-only)
            RUNPOD_ONLY=true
            shift
            ;;
        --dry-run)
            DRY_RUN_FLAG="--dry-run"
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--local-only|--runpod-only] [--dry-run]"
            echo ""
            echo "Options:"
            echo "  --local-only    Only restart local Docker services"
            echo "  --runpod-only   Only restart RunPod services"
            echo "  --dry-run       Show what would be restarted without doing it"
            echo "  --help          Show this help message"
            echo ""
            echo "Local Services:"
            echo "  - Coqui XTTS v2 (port 8005)"
            echo "  - MeloTTS (port 8001)"
            echo "  - OpenVoice (port 8003)"
            echo "  - Kokoro TTS (port 8010)"
            echo "  - Crawl4AI (port 8009)"
            echo ""
            echo "RunPod Services:"
            echo "  - F5-TTS (port 8002)"
            echo "  - StyleTTS2 (port 8006)"
            echo "  - Kyutai/Moshi (port 8008)"
            exit 0
            ;;
    esac
done

###############################################################################
# Function: log_message
# Description: Log a message to both console and log file
###############################################################################
log_message() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    # Ensure log directory exists
    sudo mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || mkdir -p "$(dirname "$LOG_FILE")"
    sudo touch "$LOG_FILE" 2>/dev/null || touch "$LOG_FILE"

    # Log to file
    echo "[$timestamp] [$level] $message" | sudo tee -a "$LOG_FILE" 2>/dev/null || echo "[$timestamp] [$level] $message" >> "$LOG_FILE"

    # Log to console with colors
    case "$level" in
        INFO)
            echo -e "${GREEN}[INFO]${NC} $message"
            ;;
        WARN)
            echo -e "${YELLOW}[WARN]${NC} $message"
            ;;
        ERROR)
            echo -e "${RED}[ERROR]${NC} $message"
            ;;
        SUCCESS)
            echo -e "${GREEN}[SUCCESS]${NC} $message"
            ;;
        HEADER)
            echo -e "${CYAN}$message${NC}"
            ;;
        *)
            echo -e "${BLUE}[$level]${NC} $message"
            ;;
    esac
}

###############################################################################
# Main execution
###############################################################################
main() {
    log_message "HEADER" "==========================================================================="
    log_message "HEADER" "       TTS UNIFIED AUTO-RESTART SCRIPT"
    log_message "HEADER" "==========================================================================="
    log_message "INFO" "Started at: $(date '+%Y-%m-%d %H:%M:%S')"

    if [ -n "$DRY_RUN_FLAG" ]; then
        log_message "INFO" "Running in DRY RUN mode - no actual restarts will be performed"
    fi

    local local_exit_code=0
    local runpod_exit_code=0

    # Check local services
    if [ "$RUNPOD_ONLY" = false ]; then
        log_message "HEADER" ""
        log_message "HEADER" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        log_message "HEADER" "  CHECKING LOCAL DOCKER SERVICES"
        log_message "HEADER" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

        if [ -f "$SCRIPT_DIR/auto_restart_local_tts.sh" ]; then
            "$SCRIPT_DIR/auto_restart_local_tts.sh" $DRY_RUN_FLAG || local_exit_code=$?
        else
            log_message "ERROR" "Local restart script not found: $SCRIPT_DIR/auto_restart_local_tts.sh"
            local_exit_code=1
        fi
    fi

    # Check RunPod services
    if [ "$LOCAL_ONLY" = false ]; then
        log_message "HEADER" ""
        log_message "HEADER" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        log_message "HEADER" "  CHECKING RUNPOD SERVICES"
        log_message "HEADER" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

        if [ -f "$SCRIPT_DIR/auto_restart_runpod_tts.sh" ]; then
            "$SCRIPT_DIR/auto_restart_runpod_tts.sh" $DRY_RUN_FLAG || runpod_exit_code=$?
        else
            log_message "WARN" "RunPod restart script not found: $SCRIPT_DIR/auto_restart_runpod_tts.sh"
            log_message "WARN" "Skipping RunPod services..."
        fi
    fi

    # Final summary
    log_message "HEADER" ""
    log_message "HEADER" "==========================================================================="
    log_message "HEADER" "  UNIFIED AUTO-RESTART SUMMARY"
    log_message "HEADER" "==========================================================================="

    if [ "$RUNPOD_ONLY" = false ]; then
        if [ $local_exit_code -eq 0 ]; then
            log_message "SUCCESS" "✓ Local Services: All healthy or successfully restarted"
        else
            log_message "ERROR" "✗ Local Services: Some services failed to restart"
        fi
    fi

    if [ "$LOCAL_ONLY" = false ]; then
        if [ $runpod_exit_code -eq 0 ]; then
            log_message "SUCCESS" "✓ RunPod Services: All healthy or successfully restarted"
        else
            log_message "ERROR" "✗ RunPod Services: Some services failed to restart or pod is offline"
        fi
    fi

    log_message "HEADER" "==========================================================================="
    log_message "INFO" "Completed at: $(date '+%Y-%m-%d %H:%M:%S')"
    log_message "INFO" "Full logs: $LOG_FILE"
    log_message "HEADER" "==========================================================================="

    # Exit with error if either script failed
    if [ $local_exit_code -ne 0 ] || [ $runpod_exit_code -ne 0 ]; then
        exit 1
    else
        exit 0
    fi
}

# Run main function
main
