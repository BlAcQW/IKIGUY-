#!/bin/bash
###############################################################################
# Auto-Restart Script for RunPod TTS Services
#
# This script automatically detects and restarts unhealthy RunPod-hosted TTS
# services via SSH. It can be called manually or integrated with health monitoring.
#
# Usage:
#   ./auto_restart_runpod_tts.sh [service_name]
#
# Examples:
#   ./auto_restart_runpod_tts.sh              # Check and restart all services
#   ./auto_restart_runpod_tts.sh f5tts        # Restart only F5-TTS
#   ./auto_restart_runpod_tts.sh --dry-run    # Show what would be restarted
#
###############################################################################

set -e

# Get script directory and load configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/../runpod.config.sh"

# Load RunPod configuration
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
else
    echo "ERROR: Configuration file not found: $CONFIG_FILE"
    exit 1
fi

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script-specific configuration
LOG_FILE="/var/log/tts/auto_restart_runpod.log"
MAX_RESTART_ATTEMPTS=3
RESTART_WAIT_TIME=60  # RunPod services need more time to initialize
DRY_RUN=false

# Service definitions come from runpod.config.sh
# Using RUNPOD_SERVICES, RUNPOD_SERVICE_NAMES, RUNPOD_COMPOSE_SERVICES

# Parse arguments
TARGET_SERVICE=""
for arg in "$@"; do
    case $arg in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [service_name] [--dry-run]"
            echo ""
            echo "Services: ${!RUNPOD_SERVICES[@]}"
            echo ""
            echo "Options:"
            echo "  --dry-run   Show what would be restarted without doing it"
            echo "  --help      Show this help message"
            exit 0
            ;;
        *)
            TARGET_SERVICE="$arg"
            shift
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
        *)
            echo -e "${BLUE}[$level]${NC} $message"
            ;;
    esac
}

###############################################################################
# Function: check_ssh_connection
# Description: Check if SSH connection to RunPod is available
###############################################################################
check_ssh_connection() {
    if [ ! -f "$SSH_KEY" ]; then
        log_message "ERROR" "SSH key not found at $SSH_KEY"
        exit 1
    fi

    log_message "INFO" "Testing SSH connection to RunPod ($RUNPOD_POD_ID)..."

    # Use the test function from runpod.config.sh
    if test_runpod_connection; then
        log_message "INFO" "SSH connection successful"
        return 0
    else
        log_message "ERROR" "Cannot connect to RunPod via SSH"
        log_message "ERROR" "Please check:"
        log_message "ERROR" "  - RunPod pod is running"
        log_message "ERROR" "  - SSH key is correct: $SSH_KEY"
        log_message "ERROR" "  - Pod ID is correct: $RUNPOD_POD_ID"
        log_message "ERROR" "  - Connection method: $RUNPOD_CONNECTION_METHOD"
        exit 1
    fi
}

###############################################################################
# Function: run_remote_command
# Description: Execute a command on RunPod via SSH
# Arguments:
#   $@ - Command to execute
###############################################################################
run_remote_command() {
    local ssh_cmd=$(get_runpod_ssh_command)
    $ssh_cmd "$@"
}

###############################################################################
# Function: is_service_healthy_remote
# Description: Check if a RunPod service is healthy via SSH
# Arguments:
#   $1 - Service name
#   $2 - Port number
# Returns:
#   0 if healthy, 1 if unhealthy
###############################################################################
is_service_healthy_remote() {
    local service_name="$1"
    local port="$2"

    # Check health endpoint on RunPod
    local health_url="http://localhost:$port/health"
    local http_code=$(run_remote_command "curl -s -w '%{http_code}' -o /dev/null -m $HEALTH_CHECK_TIMEOUT '$health_url' 2>/dev/null" || echo "000")

    if [ "$http_code" = "200" ]; then
        return 0
    else
        log_message "WARN" "$service_name health check failed on RunPod (HTTP $http_code)"
        return 1
    fi
}

###############################################################################
# Function: restart_service_remote
# Description: Restart a RunPod service via docker-compose over SSH
# Arguments:
#   $1 - Service name
#   $2 - Port number
# Returns:
#   0 if restart successful, 1 if failed
###############################################################################
restart_service_remote() {
    local service_name="$1"
    local port="$2"
    local service_display_name="${RUNPOD_SERVICE_NAMES[$service_name]}"
    local compose_service="${RUNPOD_COMPOSE_SERVICES[$service_name]}"

    log_message "INFO" "Attempting to restart $service_display_name on RunPod..."

    if [ "$DRY_RUN" = true ]; then
        log_message "INFO" "[DRY RUN] Would restart: cd /workspace/tts-deployment && docker compose restart $compose_service"
        return 0
    fi

    # Restart via docker-compose
    local restart_cmd="cd /workspace/tts-deployment && docker compose restart $compose_service"

    if run_remote_command "$restart_cmd" > /dev/null 2>&1; then
        log_message "INFO" "$service_display_name restarted on RunPod, waiting ${RESTART_WAIT_TIME}s for service to initialize..."
        sleep "$RESTART_WAIT_TIME"

        # Verify service is healthy
        local attempt=1
        while [ $attempt -le "$MAX_RESTART_ATTEMPTS" ]; do
            log_message "INFO" "Health check attempt $attempt/$MAX_RESTART_ATTEMPTS for $service_display_name..."

            if is_service_healthy_remote "$service_name" "$port"; then
                log_message "SUCCESS" "$service_display_name is now healthy on RunPod!"

                # Also restart SSH tunnel if it exists
                restart_ssh_tunnel "$port"

                return 0
            fi

            if [ $attempt -lt "$MAX_RESTART_ATTEMPTS" ]; then
                log_message "WARN" "Health check failed, waiting 10s before retry..."
                sleep 10
            fi

            ((attempt++))
        done

        log_message "ERROR" "$service_display_name failed to become healthy after restart"
        return 1
    else
        log_message "ERROR" "Failed to restart $service_display_name on RunPod"
        return 1
    fi
}

###############################################################################
# Function: restart_ssh_tunnel
# Description: Check SSH tunnel for a specific port and restart all tunnels if needed
# Arguments:
#   $1 - Port number
###############################################################################
restart_ssh_tunnel() {
    local port="$1"

    log_message "INFO" "Checking SSH tunnel for port $port..."

    # Check if tunnel exists and is forwarding
    if nc -z localhost "$port" 2>/dev/null; then
        log_message "INFO" "SSH tunnel for port $port is active"
        return 0
    else
        log_message "WARN" "SSH tunnel for port $port is down, attempting to restart all tunnels..."

        # Use the tunnel manager script to restart all tunnels
        if [ -f "$SCRIPT_DIR/runpod_tunnels.sh" ]; then
            "$SCRIPT_DIR/runpod_tunnels.sh" restart >/dev/null 2>&1

            # Wait for tunnel to come up
            sleep 3

            if nc -z localhost "$port" 2>/dev/null; then
                log_message "SUCCESS" "SSH tunnels restarted, port $port is now active"
                return 0
            else
                log_message "ERROR" "Failed to restart SSH tunnel for port $port"
                return 1
            fi
        else
            log_message "ERROR" "runpod_tunnels.sh not found, cannot restart tunnels"
            return 1
        fi
    fi
}

###############################################################################
# Function: process_service
# Description: Check and restart a single service if needed
# Arguments:
#   $1 - Service name
#   $2 - Port number
###############################################################################
process_service() {
    local service_name="$1"
    local port="$2"
    local service_display_name="${RUNPOD_SERVICE_NAMES[$service_name]}"

    log_message "INFO" "Checking $service_display_name on RunPod..."

    if is_service_healthy_remote "$service_name" "$port"; then
        log_message "INFO" "$service_display_name is healthy, no action needed"
        return 0
    else
        log_message "WARN" "$service_display_name is unhealthy, initiating restart..."
        restart_service_remote "$service_name" "$port"
        return $?
    fi
}

###############################################################################
# Main execution
###############################################################################
main() {
    log_message "INFO" "=========================================="
    log_message "INFO" "RunPod TTS Auto-Restart Script Started"
    log_message "INFO" "=========================================="

    if [ "$DRY_RUN" = true ]; then
        log_message "INFO" "Running in DRY RUN mode - no actual restarts will be performed"
    fi

    # Check SSH connection
    check_ssh_connection

    # Track results
    declare -A results
    local total=0
    local restarted=0
    local failed=0
    local healthy=0

    # Process services
    if [ -n "$TARGET_SERVICE" ]; then
        # Single service mode
        if [ -z "${RUNPOD_SERVICES[$TARGET_SERVICE]}" ]; then
            log_message "ERROR" "Unknown service: $TARGET_SERVICE"
            log_message "INFO" "Available services: ${!RUNPOD_SERVICES[@]}"
            exit 1
        fi

        process_service "$TARGET_SERVICE" "${RUNPOD_SERVICES[$TARGET_SERVICE]}"
        exit $?
    else
        # All services mode
        for service_name in "${!RUNPOD_SERVICES[@]}"; do
            port="${RUNPOD_SERVICES[$service_name]}"
            ((total++))

            if is_service_healthy_remote "$service_name" "$port"; then
                results[$service_name]="healthy"
                ((healthy++))
            else
                log_message "WARN" "${RUNPOD_SERVICE_NAMES[$service_name]} is unhealthy, initiating restart..."

                if restart_service_remote "$service_name" "$port"; then
                    results[$service_name]="restarted_success"
                    ((restarted++))
                else
                    results[$service_name]="restarted_failed"
                    ((failed++))
                fi
            fi
        done
    fi

    # Print summary
    log_message "INFO" "=========================================="
    log_message "INFO" "RunPod Auto-Restart Summary"
    log_message "INFO" "=========================================="
    log_message "INFO" "Total services checked: $total"
    log_message "INFO" "Healthy (no action): $healthy"
    log_message "INFO" "Successfully restarted: $restarted"
    log_message "INFO" "Failed to restart: $failed"
    log_message "INFO" "=========================================="

    # Detailed results
    for service_name in "${!results[@]}"; do
        local status="${results[$service_name]}"
        local service_display_name="${RUNPOD_SERVICE_NAMES[$service_name]}"

        case "$status" in
            healthy)
                log_message "INFO" "  ✓ $service_display_name: Healthy"
                ;;
            restarted_success)
                log_message "SUCCESS" "  ↻ $service_display_name: Restarted successfully"
                ;;
            restarted_failed)
                log_message "ERROR" "  ✗ $service_display_name: Restart failed"
                ;;
        esac
    done

    log_message "INFO" "=========================================="
    log_message "INFO" "Log file: $LOG_FILE"
    log_message "INFO" "=========================================="

    # Exit with appropriate code
    if [ "$failed" -gt 0 ]; then
        exit 1
    else
        exit 0
    fi
}

# Run main function
main
