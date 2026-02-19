#!/bin/bash
###############################################################################
# Auto-Restart Script for Local TTS Services
#
# This script automatically detects and restarts unhealthy local TTS Docker
# containers. It can be called manually or integrated with health monitoring.
#
# Usage:
#   ./auto_restart_local_tts.sh [service_name]
#
# Examples:
#   ./auto_restart_local_tts.sh              # Check and restart all services
#   ./auto_restart_local_tts.sh coqui        # Restart only Coqui
#   ./auto_restart_local_tts.sh --dry-run    # Show what would be restarted
#
###############################################################################

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
LOG_FILE="/var/log/tts/auto_restart.log"
MAX_RESTART_ATTEMPTS=3
HEALTH_CHECK_TIMEOUT=10
RESTART_WAIT_TIME=30
DRY_RUN=false

# Service definitions (matches comprehensive_health_check.sh)
declare -A SERVICES=(
    ["coqui"]="8005"
    ["melotts"]="8001"
    ["openvoice"]="8003"
    ["kokoro"]="8010"
    ["crawl4ai"]="8009"
)

declare -A SERVICE_NAMES=(
    ["coqui"]="Coqui XTTS v2"
    ["melotts"]="MeloTTS"
    ["openvoice"]="OpenVoice"
    ["kokoro"]="Kokoro TTS"
    ["crawl4ai"]="Crawl4AI"
)

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
            echo "Services: ${!SERVICES[@]}"
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
    sudo mkdir -p "$(dirname "$LOG_FILE")"
    sudo touch "$LOG_FILE"

    # Log to file
    echo "[$timestamp] [$level] $message" | sudo tee -a "$LOG_FILE" > /dev/null

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
# Function: check_docker_daemon
# Description: Check if Docker daemon is running
###############################################################################
check_docker_daemon() {
    if ! sudo docker info >/dev/null 2>&1; then
        log_message "ERROR" "Docker daemon is not running or not accessible"
        exit 1
    fi
}

###############################################################################
# Function: is_service_healthy
# Description: Check if a service is healthy via health endpoint
# Arguments:
#   $1 - Container name
#   $2 - Port number
# Returns:
#   0 if healthy, 1 if unhealthy
###############################################################################
is_service_healthy() {
    local container_name="$1"
    local port="$2"

    # Check if container is running
    if ! sudo docker ps --filter "name=$container_name" --format "{{.Names}}" | grep -q "^$container_name$"; then
        log_message "WARN" "$container_name container is not running"
        return 1
    fi

    # Check health endpoint
    local health_url="http://localhost:$port/health"
    local http_code=$(curl -s -w "%{http_code}" -o /dev/null -m "$HEALTH_CHECK_TIMEOUT" "$health_url" 2>/dev/null)

    if [ "$http_code" = "200" ]; then
        return 0
    else
        log_message "WARN" "$container_name health check failed (HTTP $http_code)"
        return 1
    fi
}

###############################################################################
# Function: restart_service
# Description: Restart a Docker container and verify it comes back healthy
# Arguments:
#   $1 - Container name
#   $2 - Port number
# Returns:
#   0 if restart successful, 1 if failed
###############################################################################
restart_service() {
    local container_name="$1"
    local port="$2"
    local service_display_name="${SERVICE_NAMES[$container_name]}"

    log_message "INFO" "Attempting to restart $service_display_name ($container_name)..."

    # Check if container exists
    if ! sudo docker ps -a --filter "name=$container_name" --format "{{.Names}}" | grep -q "^$container_name$"; then
        log_message "ERROR" "Container $container_name does not exist"
        return 1
    fi

    if [ "$DRY_RUN" = true ]; then
        log_message "INFO" "[DRY RUN] Would restart: sudo docker restart $container_name"
        return 0
    fi

    # Restart the container
    if sudo docker restart "$container_name" > /dev/null 2>&1; then
        log_message "INFO" "Container $container_name restarted, waiting ${RESTART_WAIT_TIME}s for service to initialize..."
        sleep "$RESTART_WAIT_TIME"

        # Verify service is healthy
        local attempt=1
        while [ $attempt -le "$MAX_RESTART_ATTEMPTS" ]; do
            log_message "INFO" "Health check attempt $attempt/$MAX_RESTART_ATTEMPTS for $container_name..."

            if is_service_healthy "$container_name" "$port"; then
                log_message "SUCCESS" "$service_display_name is now healthy!"

                # Send success notification (optional - can be integrated with email service)
                # notify_restart_success "$container_name"

                return 0
            fi

            if [ $attempt -lt "$MAX_RESTART_ATTEMPTS" ]; then
                log_message "WARN" "Health check failed, waiting 10s before retry..."
                sleep 10
            fi

            ((attempt++))
        done

        log_message "ERROR" "$service_display_name failed to become healthy after restart"

        # Send failure notification (optional)
        # notify_restart_failure "$container_name"

        return 1
    else
        log_message "ERROR" "Failed to restart container $container_name"
        return 1
    fi
}

###############################################################################
# Function: process_service
# Description: Check and restart a single service if needed
# Arguments:
#   $1 - Container name
#   $2 - Port number
###############################################################################
process_service() {
    local container_name="$1"
    local port="$2"
    local service_display_name="${SERVICE_NAMES[$container_name]}"

    log_message "INFO" "Checking $service_display_name ($container_name)..."

    if is_service_healthy "$container_name" "$port"; then
        log_message "INFO" "$service_display_name is healthy, no action needed"
        return 0
    else
        log_message "WARN" "$service_display_name is unhealthy, initiating restart..."
        restart_service "$container_name" "$port"
        return $?
    fi
}

###############################################################################
# Function: send_summary_email
# Description: Send summary email of all restart actions (placeholder)
###############################################################################
send_summary_email() {
    local summary="$1"

    # This can be integrated with the unified email service
    # For now, just log it
    log_message "INFO" "Restart Summary:\n$summary"

    # TODO: Integrate with shared/services/unified_email_service.py
    # python3 -c "
    # import asyncio
    # from apps.shared.services.unified_email_service import get_email_service
    # async def send():
    #     service = get_email_service()
    #     await service.send_email(
    #         to='admin@ailabsafrica.com',
    #         subject='TTS Auto-Restart Summary',
    #         body='$summary'
    #     )
    # asyncio.run(send())
    # "
}

###############################################################################
# Main execution
###############################################################################
main() {
    log_message "INFO" "=========================================="
    log_message "INFO" "TTS Auto-Restart Script Started"
    log_message "INFO" "=========================================="

    if [ "$DRY_RUN" = true ]; then
        log_message "INFO" "Running in DRY RUN mode - no actual restarts will be performed"
    fi

    # Check Docker daemon
    check_docker_daemon

    # Track results
    declare -A results
    local total=0
    local restarted=0
    local failed=0
    local healthy=0

    # Process services
    if [ -n "$TARGET_SERVICE" ]; then
        # Single service mode
        if [ -z "${SERVICES[$TARGET_SERVICE]}" ]; then
            log_message "ERROR" "Unknown service: $TARGET_SERVICE"
            log_message "INFO" "Available services: ${!SERVICES[@]}"
            exit 1
        fi

        process_service "$TARGET_SERVICE" "${SERVICES[$TARGET_SERVICE]}"
        exit $?
    else
        # All services mode
        for container_name in "${!SERVICES[@]}"; do
            port="${SERVICES[$container_name]}"
            ((total++))

            if is_service_healthy "$container_name" "$port"; then
                results[$container_name]="healthy"
                ((healthy++))
            else
                log_message "WARN" "${SERVICE_NAMES[$container_name]} is unhealthy, initiating restart..."

                if restart_service "$container_name" "$port"; then
                    results[$container_name]="restarted_success"
                    ((restarted++))
                else
                    results[$container_name]="restarted_failed"
                    ((failed++))
                fi
            fi
        done
    fi

    # Print summary
    log_message "INFO" "=========================================="
    log_message "INFO" "Auto-Restart Summary"
    log_message "INFO" "=========================================="
    log_message "INFO" "Total services checked: $total"
    log_message "INFO" "Healthy (no action): $healthy"
    log_message "INFO" "Successfully restarted: $restarted"
    log_message "INFO" "Failed to restart: $failed"
    log_message "INFO" "=========================================="

    # Detailed results
    for container_name in "${!results[@]}"; do
        local status="${results[$container_name]}"
        local service_display_name="${SERVICE_NAMES[$container_name]}"

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
