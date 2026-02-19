#!/bin/bash

###############################################################################
# Comprehensive TTS Services Health Check Script
#
# This script checks the health of all TTS services deployed locally and
# provides a detailed status report with color-coded output.
#
# Usage: ./comprehensive_health_check.sh [--json] [--verbose]
###############################################################################

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Flags
JSON_OUTPUT=false
VERBOSE=false

# Parse arguments
for arg in "$@"; do
    case $arg in
        --json)
            JSON_OUTPUT=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--json] [--verbose]"
            echo ""
            echo "Options:"
            echo "  --json      Output in JSON format"
            echo "  --verbose   Show detailed information"
            echo "  --help      Show this help message"
            exit 0
            ;;
    esac
done

# Service definitions
declare -A SERVICES=(
    ["Coqui XTTS v2"]="https://coqui.ailabsafrica.com"
    ["MeloTTS"]="https://melotts.ailabsafrica.com"
    ["OpenVoice"]="https://openvoice.ailabsafrica.com"
    ["Kokoro TTS"]="https://kokoro.ailabsafrica.com"
    ["Crawl4AI"]="https://crawl4ai.ailabsafrica.com"
)

declare -A LOCAL_SERVICES=(
    ["Coqui XTTS v2"]="http://localhost:8005"
    ["MeloTTS"]="http://localhost:8001"
    ["OpenVoice"]="http://localhost:8003"
    ["Kokoro TTS"]="http://localhost:8010"
    ["Crawl4AI"]="http://localhost:8009"
)

declare -A CONTAINERS=(
    ["Coqui XTTS v2"]="coqui"
    ["MeloTTS"]="melotts"
    ["OpenVoice"]="openvoice"
    ["Kokoro TTS"]="kokoro"
    ["Crawl4AI"]="crawl4ai"
)

# Initialize counters
total_services=0
healthy_services=0
unhealthy_services=0
offline_services=0

# JSON output array
declare -a json_results=()

###############################################################################
# Function: check_service_health
# Description: Check the health of a single service
# Arguments:
#   $1 - Service name
#   $2 - Service URL
#   $3 - Container name
###############################################################################
check_service_health() {
    local service_name="$1"
    local service_url="$2"
    local container_name="$3"
    local local_url="${LOCAL_SERVICES[$service_name]}"

    ((total_services++))

    # Check if container is running
    container_status=$(sudo docker ps --filter "name=$container_name" --format "{{.Status}}" 2>/dev/null)

    if [ -z "$container_status" ]; then
        if [ "$JSON_OUTPUT" = true ]; then
            json_results+=("{\"service\":\"$service_name\",\"status\":\"offline\",\"container\":\"not_running\",\"health\":\"N/A\",\"https\":\"N/A\"}")
        else
            printf "${RED}✗${NC} %-20s ${RED}OFFLINE${NC} (Container not running)\n" "$service_name"
        fi
        ((offline_services++))
        return 1
    fi

    # Check local health endpoint
    health_response=$(curl -s -w "\n%{http_code}" -m 5 "$local_url/health" 2>/dev/null)
    http_code=$(echo "$health_response" | tail -n1)
    health_body=$(echo "$health_response" | sed '$d')

    # Check HTTPS endpoint
    https_response=$(curl -s -w "\n%{http_code}" -m 5 "$service_url/health" 2>/dev/null)
    https_code=$(echo "$https_response" | tail -n1)

    # Determine overall status
    if [ "$http_code" = "200" ]; then
        if [ "$https_code" = "200" ]; then
            status_icon="${GREEN}✓${NC}"
            status_text="${GREEN}HEALTHY${NC}"
            https_status="${GREEN}SSL OK${NC}"
            ((healthy_services++))
            json_status="healthy"
        else
            status_icon="${YELLOW}⚠${NC}"
            status_text="${YELLOW}DEGRADED${NC}"
            https_status="${RED}SSL FAIL${NC}"
            ((unhealthy_services++))
            json_status="degraded"
        fi
    else
        status_icon="${RED}✗${NC}"
        status_text="${RED}UNHEALTHY${NC}"
        https_status="${RED}N/A${NC}"
        ((unhealthy_services++))
        json_status="unhealthy"
    fi

    # Output results
    if [ "$JSON_OUTPUT" = true ]; then
        json_results+=("{\"service\":\"$service_name\",\"status\":\"$json_status\",\"container\":\"running\",\"health\":$http_code,\"https\":$https_code,\"container_status\":\"$container_status\",\"response\":$(echo "$health_body" | jq -c . 2>/dev/null || echo '{}')}")
    else
        printf "%b %-20s %b" "$status_icon" "$service_name" "$status_text"
        printf " | HTTPS: %b" "$https_status"

        if [ "$VERBOSE" = true ]; then
            printf "\n    Container: %s\n" "$container_status"
            printf "    Local Health: HTTP %s\n" "$http_code"
            printf "    HTTPS Health: HTTP %s\n" "$https_code"
            if [ -n "$health_body" ]; then
                printf "    Response: %s\n" "$(echo "$health_body" | jq -c . 2>/dev/null || echo "$health_body")"
            fi
        fi
        printf "\n"
    fi
}

###############################################################################
# Function: check_docker_daemon
# Description: Check if Docker daemon is running
###############################################################################
check_docker_daemon() {
    if ! sudo docker info >/dev/null 2>&1; then
        if [ "$JSON_OUTPUT" = false ]; then
            echo -e "${RED}ERROR: Docker daemon is not running or not accessible${NC}"
        fi
        exit 1
    fi
}

###############################################################################
# Function: print_summary
# Description: Print summary statistics
###############################################################################
print_summary() {
    if [ "$JSON_OUTPUT" = false ]; then
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "Summary:"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        printf "Total Services:     %d\n" "$total_services"
        printf "${GREEN}Healthy:            %d${NC}\n" "$healthy_services"
        printf "${YELLOW}Degraded:           %d${NC}\n" "$unhealthy_services"
        printf "${RED}Offline:            %d${NC}\n" "$offline_services"

        # Calculate uptime percentage
        if [ "$total_services" -gt 0 ]; then
            uptime_pct=$((healthy_services * 100 / total_services))
            printf "\nUptime:             %d%%\n" "$uptime_pct"
        fi

        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    fi
}

###############################################################################
# Main execution
###############################################################################
main() {
    # Check Docker daemon
    check_docker_daemon

    if [ "$JSON_OUTPUT" = false ]; then
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "TTS Services Health Check"
        echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
    fi

    # Check each service
    for service_name in "${!SERVICES[@]}"; do
        check_service_health "$service_name" "${SERVICES[$service_name]}" "${CONTAINERS[$service_name]}"
    done

    # Output results
    if [ "$JSON_OUTPUT" = true ]; then
        printf '{"timestamp":"%s","services":[%s],"summary":{"total":%d,"healthy":%d,"degraded":%d,"offline":%d}}\n' \
            "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
            "$(IFS=,; echo "${json_results[*]}")" \
            "$total_services" \
            "$healthy_services" \
            "$unhealthy_services" \
            "$offline_services"
    else
        print_summary
    fi

    # Exit code based on health
    if [ "$offline_services" -gt 0 ] || [ "$unhealthy_services" -gt 0 ]; then
        exit 1
    else
        exit 0
    fi
}

# Run main function
main
