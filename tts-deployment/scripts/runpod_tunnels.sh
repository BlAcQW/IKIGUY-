#!/bin/bash
###############################################################################
# SSH Tunnel Manager for RunPod GPU Services
#
# This script establishes persistent SSH tunnels for F5-TTS, StyleTTS2, and
# Kyutai/Moshi services running on RunPod.
#
# Features:
# - Uses stable proxied SSH connection (survives pod restarts)
# - Automatic fallback to direct TCP if proxy fails
# - Health checking for tunnel validation
# - PID management for tunnel lifecycle
#
# Usage:
#   ./runpod_tunnels.sh start   # Start SSH tunnels
#   ./runpod_tunnels.sh stop    # Stop SSH tunnels
#   ./runpod_tunnels.sh status  # Check tunnel status
#   ./runpod_tunnels.sh restart # Restart tunnels
###############################################################################

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/../runpod.config.sh"

# Load RunPod configuration
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
else
    echo "ERROR: Configuration file not found: $CONFIG_FILE"
    echo "Please ensure runpod.config.sh exists in the tts-deployment directory"
    exit 1
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

###############################################################################
# Logging functions
###############################################################################
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_header() {
    echo -e "${CYAN}$1${NC}"
}

###############################################################################
# Function: check_ssh_key
# Description: Verify SSH key exists
###############################################################################
check_ssh_key() {
    if [ ! -f "$SSH_KEY" ]; then
        log_error "SSH key not found at $SSH_KEY"
        log_info "Generate one with: ssh-keygen -t ed25519 -f $SSH_KEY"
        exit 1
    fi
}

###############################################################################
# Function: get_ssh_connection_string
# Description: Build SSH connection string based on configuration
# Returns: SSH connection string
###############################################################################
get_ssh_connection_string() {
    local ssh_opts="-o ConnectTimeout=$SSH_CONNECT_TIMEOUT"
    ssh_opts="$ssh_opts -o ServerAliveInterval=$SSH_SERVER_ALIVE_INTERVAL"
    ssh_opts="$ssh_opts -o ServerAliveCountMax=$SSH_SERVER_ALIVE_COUNT_MAX"
    ssh_opts="$ssh_opts -o StrictHostKeyChecking=no"
    ssh_opts="$ssh_opts -o UserKnownHostsFile=/dev/null"
    ssh_opts="$ssh_opts -o LogLevel=ERROR"
    ssh_opts="$ssh_opts -i $SSH_KEY"

    case "$RUNPOD_CONNECTION_METHOD" in
        proxy)
            echo "$ssh_opts $RUNPOD_PROXY_USER@$RUNPOD_PROXY_HOST"
            ;;
        direct)
            echo "$ssh_opts -p $RUNPOD_DIRECT_PORT $RUNPOD_DIRECT_USER@$RUNPOD_DIRECT_HOST"
            ;;
        auto)
            # Try proxy first, fallback to direct
            if ssh -o BatchMode=yes -o ConnectTimeout=5 $ssh_opts "$RUNPOD_PROXY_USER@$RUNPOD_PROXY_HOST" "exit" 2>/dev/null; then
                echo "$ssh_opts $RUNPOD_PROXY_USER@$RUNPOD_PROXY_HOST"
            else
                log_warn "Proxy connection failed, falling back to direct TCP"
                echo "$ssh_opts -p $RUNPOD_DIRECT_PORT $RUNPOD_DIRECT_USER@$RUNPOD_DIRECT_HOST"
            fi
            ;;
        *)
            log_error "Invalid RUNPOD_CONNECTION_METHOD: $RUNPOD_CONNECTION_METHOD"
            log_info "Valid options: proxy, direct, auto"
            exit 1
            ;;
    esac
}

###############################################################################
# Function: test_connection
# Description: Test if we can connect to RunPod
# Returns: 0 if successful, 1 if failed
###############################################################################
test_connection() {
    local ssh_opts=$(get_ssh_connection_string)

    log_info "Testing connection to RunPod..."

    # Test with -T (no PTY), -o BatchMode=yes (no password prompt), and a simple command
    if ssh -T -o BatchMode=yes $ssh_opts "exit 0" >/dev/null 2>&1; then
        log_info "✓ Connection test passed"
        return 0
    else
        log_error "✗ Connection test failed"
        return 1
    fi
}

###############################################################################
# Function: start_tunnels
# Description: Start SSH tunnels in background
###############################################################################
start_tunnels() {
    log_header "=================================================="
    log_header "  Starting RunPod SSH Tunnels"
    log_header "=================================================="

    # Check prerequisites
    check_ssh_key

    # Check if tunnels are already running
    if [ -f "$TUNNEL_PID_FILE" ]; then
        OLD_PID=$(cat "$TUNNEL_PID_FILE")
        if ps -p "$OLD_PID" > /dev/null 2>&1; then
            log_warn "Tunnels already running with PID $OLD_PID"
            log_info "Run '$0 stop' to stop existing tunnels first"
            return 0
        else
            log_warn "Stale PID file found, removing..."
            rm -f "$TUNNEL_PID_FILE"
        fi
    fi

    # Note: We skip connection test because RunPod proxy SSH doesn't support
    # command execution (returns "Your SSH client doesn't support PTY" error).
    # The tunnel will fail immediately if connection doesn't work anyway.
    log_info "Connecting to RunPod (Note: PTY warning from RunPod is normal)..."

    # Build SSH command
    local ssh_opts=$(get_ssh_connection_string)

    # Build port forwarding arguments
    local port_forwards=""
    for service_key in "${!RUNPOD_SERVICES[@]}"; do
        local port="${RUNPOD_SERVICES[$service_key]}"
        port_forwards="$port_forwards -L $port:localhost:$port"
    done

    # Ensure log directory exists
    mkdir -p "$(dirname "$TUNNEL_LOG_FILE")" 2>/dev/null || sudo mkdir -p "$(dirname "$TUNNEL_LOG_FILE")"

    log_info ""
    log_info "Connection method: $RUNPOD_CONNECTION_METHOD"
    log_info "Pod ID: $RUNPOD_POD_ID"
    log_info "Forwarding ports: ${RUNPOD_SERVICES[*]}"
    log_info ""

    # Start tunnel using nohup instead of -f (RunPod proxy doesn't support -f)
    # -T flag disables PTY allocation for RunPod proxy compatibility
    # Note: SSH will use control master (ControlMaster=auto), so the initial process exits quickly
    nohup ssh -N -T \
        $port_forwards \
        -o ExitOnForwardFailure=yes \
        $ssh_opts > "$TUNNEL_LOG_FILE" 2>&1 &

    # Wait for tunnel to establish
    sleep 3

    # Verify ports are actually forwarding (more reliable than checking process)
    local all_forwarding=true
    for service_key in "${!RUNPOD_SERVICES[@]}"; do
        local port="${RUNPOD_SERVICES[$service_key]}"
        if ! nc -z localhost "$port" 2>/dev/null; then
            log_error "Port $port is not forwarding"
            all_forwarding=false
        fi
    done

    if [ "$all_forwarding" = false ]; then
        log_error "Some ports failed to forward"
        log_error "Check log: $TUNNEL_LOG_FILE"
        tail -10 "$TUNNEL_LOG_FILE" >&2
        exit 1
    fi

    # Get PID of SSH tunnel process (could be control master or direct process)
    TUNNEL_PID=$(pgrep -f "ssh.*-N.*-T.*$RUNPOD_POD_ID@$RUNPOD_PROXY_HOST" | head -1)

    # Fallback: try to find control master if direct process not found
    if [ -z "$TUNNEL_PID" ]; then
        TUNNEL_PID=$(pgrep -f "ssh:.*controlmasters.*$RUNPOD_POD_ID@$RUNPOD_PROXY_HOST" | head -1)
    fi

    if [ -z "$TUNNEL_PID" ]; then
        log_error "Could not find SSH control master process"
        exit 1
    fi

    # Ensure PID directory exists (try sudo first, then fallback to user)
    mkdir -p "$(dirname "$TUNNEL_PID_FILE")" 2>/dev/null || sudo mkdir -p "$(dirname "$TUNNEL_PID_FILE")"

    # Write PID file
    echo "$TUNNEL_PID" > "$TUNNEL_PID_FILE" 2>/dev/null || echo "$TUNNEL_PID" | sudo tee "$TUNNEL_PID_FILE" > /dev/null

    log_info "✓ SSH tunnels established successfully"
    log_info "✓ PID: $TUNNEL_PID"
    log_info ""
    log_header "Tunneled Services:"

    for service_key in "${!RUNPOD_SERVICES[@]}"; do
        local port="${RUNPOD_SERVICES[$service_key]}"
        local name="${RUNPOD_SERVICE_NAMES[$service_key]}"
        log_info "  • Port $port: $name"
    done

    log_header "=================================================="
}

###############################################################################
# Function: stop_tunnels
# Description: Stop running SSH tunnels
###############################################################################
stop_tunnels() {
    log_header "=================================================="
    log_header "  Stopping RunPod SSH Tunnels"
    log_header "=================================================="

    if [ -f "$TUNNEL_PID_FILE" ]; then
        TUNNEL_PID=$(cat "$TUNNEL_PID_FILE")
        if ps -p "$TUNNEL_PID" > /dev/null 2>&1; then
            log_info "Stopping SSH tunnels (PID: $TUNNEL_PID)..."
            kill "$TUNNEL_PID"
            rm -f "$TUNNEL_PID_FILE"
            log_info "✓ Tunnels stopped"
        else
            log_warn "No running tunnels found for PID $TUNNEL_PID"
            rm -f "$TUNNEL_PID_FILE"
        fi
    else
        log_warn "No tunnel PID file found"
    fi

    log_header "=================================================="
}

###############################################################################
# Function: check_status
# Description: Check status of SSH tunnels and port forwarding
###############################################################################
check_status() {
    log_header "=================================================="
    log_header "  RunPod SSH Tunnel Status"
    log_header "=================================================="

    log_info "Pod ID: $RUNPOD_POD_ID"
    log_info "Connection method: $RUNPOD_CONNECTION_METHOD"
    log_info ""

    if [ -f "$TUNNEL_PID_FILE" ]; then
        TUNNEL_PID=$(cat "$TUNNEL_PID_FILE")
        if ps -p "$TUNNEL_PID" > /dev/null 2>&1; then
            log_info "✓ SSH tunnels are running (PID: $TUNNEL_PID)"
            log_info ""

            # Check if ports are actually listening and responding
            local all_healthy=true
            for service_key in "${!RUNPOD_SERVICES[@]}"; do
                local port="${RUNPOD_SERVICES[$service_key]}"
                local name="${RUNPOD_SERVICE_NAMES[$service_key]}"

                # Check if port is listening
                if nc -z localhost "$port" 2>/dev/null; then
                    # Try health check
                    local http_code=$(curl -s -w "%{http_code}" -o /dev/null -m 2 "http://localhost:$port/health" 2>/dev/null)
                    if [ "$http_code" = "200" ]; then
                        echo -e "  ${GREEN}✓${NC} Port $port ($name): Forwarding + Healthy"
                    else
                        echo -e "  ${YELLOW}⚠${NC} Port $port ($name): Forwarding (Service not responding: HTTP $http_code)"
                        all_healthy=false
                    fi
                else
                    echo -e "  ${RED}✗${NC} Port $port ($name): NOT forwarding"
                    all_healthy=false
                fi
            done

            log_info ""
            if [ "$all_healthy" = true ]; then
                log_info "✓ All services are healthy"
            else
                log_warn "Some services are not healthy (this may be normal if services are starting)"
            fi
        else
            log_error "SSH tunnels are NOT running (stale PID file)"
            rm -f "$TUNNEL_PID_FILE"
        fi
    else
        log_warn "No tunnels running"
        log_info ""
        log_info "Start tunnels with: $0 start"
    fi

    log_header "=================================================="
}

###############################################################################
# Main execution
###############################################################################
case "${1:-status}" in
    start)
        start_tunnels
        ;;
    stop)
        stop_tunnels
        ;;
    status)
        check_status
        ;;
    restart)
        stop_tunnels
        sleep 2
        start_tunnels
        ;;
    *)
        echo "Usage: $0 {start|stop|status|restart}"
        echo ""
        echo "Commands:"
        echo "  start   - Start SSH tunnels to RunPod"
        echo "  stop    - Stop running SSH tunnels"
        echo "  status  - Check tunnel and service status"
        echo "  restart - Restart SSH tunnels"
        exit 1
        ;;
esac
