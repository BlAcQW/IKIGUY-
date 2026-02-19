#!/bin/bash
###############################################################################
# RunPod Configuration File
#
# This file contains RunPod connection details and is sourced by all scripts
# that need to connect to RunPod services.
#
# IMPORTANT: Update only RUNPOD_POD_ID when you create a new pod.
#            The proxy hostname is automatically constructed from the pod ID.
###############################################################################

# RunPod Pod Identifier (stable across restarts, changes only if you delete the pod)
# Format: {random-id}-{8-char-hash}
# Example: jzfmzviw26huka-644113c7
export RUNPOD_POD_ID="${RUNPOD_POD_ID:-jzfmzviw26huka-644113c7}"

# Connection Method Priority (1=highest)
# 1. Proxied SSH (most stable, survives port changes)
# 2. Direct TCP (faster, but port may change)
# 3. RunPod API (fallback for auto-discovery)

# Proxied SSH Configuration (RECOMMENDED - most stable)
# This hostname format is stable and doesn't change when pod restarts
export RUNPOD_PROXY_HOST="ssh.runpod.io"
export RUNPOD_PROXY_USER="$RUNPOD_POD_ID"

# Direct TCP Configuration (will change if pod restarts)
# Only use if you need lowest latency and can handle port changes
export RUNPOD_DIRECT_HOST="${RUNPOD_DIRECT_HOST:-194.68.245.121}"
export RUNPOD_DIRECT_PORT="${RUNPOD_DIRECT_PORT:-22153}"
export RUNPOD_DIRECT_USER="${RUNPOD_DIRECT_USER:-root}"

# SSH Key Configuration
export SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_ed25519}"

# Connection Method (proxy|direct|auto)
# - proxy: Always use proxied SSH (recommended)
# - direct: Always use direct TCP
# - auto: Try proxy first, fallback to direct
export RUNPOD_CONNECTION_METHOD="${RUNPOD_CONNECTION_METHOD:-proxy}"

# RunPod API Configuration (for auto-discovery)
# Get your API key from: https://www.runpod.io/console/user/settings
export RUNPOD_API_KEY="${RUNPOD_API_KEY:-rpa_0AGD99DG0R237PDY5XPGVA887USJWOVCWCUFMSF91g3y2o}"
export RUNPOD_API_ENDPOINT="https://api.runpod.io/graphql"

# Service Port Mappings (RunPod internal port -> Local tunnel port)
declare -gA RUNPOD_SERVICES=(
    ["f5tts"]="8002"
    ["styletts2"]="8006"
    ["moshi"]="8008"
)

# Service Display Names
declare -gA RUNPOD_SERVICE_NAMES=(
    ["f5tts"]="F5-TTS"
    ["styletts2"]="StyleTTS2"
    ["moshi"]="Kyutai/Moshi"
)

# Docker Compose Service Names (on RunPod)
declare -gA RUNPOD_COMPOSE_SERVICES=(
    ["f5tts"]="f5tts"
    ["styletts2"]="styletts"
    ["moshi"]="moshi"
)

# Tunnel Configuration
export TUNNEL_PID_FILE="${HOME}/.cache/runpod_tunnels.pid"
export TUNNEL_LOG_FILE="/var/log/tts/runpod_tunnels.log"

# Health Check Configuration
export HEALTH_CHECK_TIMEOUT=10
export HEALTH_CHECK_RETRIES=3

# Connection Timeouts
export SSH_CONNECT_TIMEOUT=10
export SSH_SERVER_ALIVE_INTERVAL=60
export SSH_SERVER_ALIVE_COUNT_MAX=3

###############################################################################
# Function: get_runpod_ssh_command
# Description: Returns the appropriate SSH command based on connection method
# Returns: SSH command string
###############################################################################
get_runpod_ssh_command() {
    local ssh_opts="-o ConnectTimeout=$SSH_CONNECT_TIMEOUT"
    ssh_opts="$ssh_opts -o ServerAliveInterval=$SSH_SERVER_ALIVE_INTERVAL"
    ssh_opts="$ssh_opts -o ServerAliveCountMax=$SSH_SERVER_ALIVE_COUNT_MAX"
    ssh_opts="$ssh_opts -o StrictHostKeyChecking=no"
    ssh_opts="$ssh_opts -i $SSH_KEY"

    case "$RUNPOD_CONNECTION_METHOD" in
        proxy)
            echo "ssh $ssh_opts $RUNPOD_PROXY_USER@$RUNPOD_PROXY_HOST"
            ;;
        direct)
            echo "ssh $ssh_opts -p $RUNPOD_DIRECT_PORT $RUNPOD_DIRECT_USER@$RUNPOD_DIRECT_HOST"
            ;;
        auto)
            # Try proxy first
            if ssh -o ConnectTimeout=5 -o BatchMode=yes $ssh_opts "$RUNPOD_PROXY_USER@$RUNPOD_PROXY_HOST" "exit" 2>/dev/null; then
                echo "ssh $ssh_opts $RUNPOD_PROXY_USER@$RUNPOD_PROXY_HOST"
            else
                echo "ssh $ssh_opts -p $RUNPOD_DIRECT_PORT $RUNPOD_DIRECT_USER@$RUNPOD_DIRECT_HOST"
            fi
            ;;
        *)
            echo "ssh $ssh_opts $RUNPOD_PROXY_USER@$RUNPOD_PROXY_HOST"
            ;;
    esac
}

###############################################################################
# Function: test_runpod_connection
# Description: Test if we can connect to RunPod
# Returns: 0 if successful, 1 if failed
###############################################################################
test_runpod_connection() {
    local ssh_cmd=$(get_runpod_ssh_command)

    # Use -T flag to disable PTY for RunPod proxy compatibility
    if $ssh_cmd -T "echo 'Connection successful'" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

###############################################################################
# Function: get_runpod_info_via_api
# Description: Query RunPod API for pod connection details (requires API key)
# Returns: JSON with pod details or empty if failed
###############################################################################
get_runpod_info_via_api() {
    if [ -z "$RUNPOD_API_KEY" ]; then
        echo "ERROR: RUNPOD_API_KEY not set" >&2
        return 1
    fi

    local query='{"query": "query { pod(input: {podId: \"'$RUNPOD_POD_ID'\"}) { id name runtime { ports { ip publicPort privatePort } } } }"}'

    curl -s -X POST "$RUNPOD_API_ENDPOINT" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $RUNPOD_API_KEY" \
        -d "$query"
}

###############################################################################
# Function: update_direct_connection_from_api
# Description: Update RUNPOD_DIRECT_* vars from API response
# Returns: 0 if successful, 1 if failed
###############################################################################
update_direct_connection_from_api() {
    local api_response=$(get_runpod_info_via_api)

    if [ -z "$api_response" ]; then
        return 1
    fi

    # Parse SSH port from API response (looking for port 22)
    local ssh_port=$(echo "$api_response" | grep -o '"privatePort":22,"publicPort":[0-9]*' | grep -o '[0-9]*$')
    local host_ip=$(echo "$api_response" | grep -o '"ip":"[^"]*"' | head -1 | cut -d'"' -f4)

    if [ -n "$ssh_port" ] && [ -n "$host_ip" ]; then
        export RUNPOD_DIRECT_HOST="$host_ip"
        export RUNPOD_DIRECT_PORT="$ssh_port"
        echo "Updated direct connection: $host_ip:$ssh_port" >&2
        return 0
    else
        return 1
    fi
}

# Export functions so they can be used by scripts that source this file
export -f get_runpod_ssh_command
export -f test_runpod_connection
export -f get_runpod_info_via_api
export -f update_direct_connection_from_api

# Validation on source
if [ ! -f "$SSH_KEY" ]; then
    echo "WARNING: SSH key not found at $SSH_KEY" >&2
fi
