#!/bin/bash
#
# Pre-compute Top Queries Cron Job
# Runs daily at 2 AM to pre-compute responses for common RAG queries
#
# Author: AI Labs Africa
# Schedule: Daily at 2:00 AM
#

set -e  # Exit on error

# Configuration
VENV_PATH="/opt/kasaai/apps/venv"
PYTHON_BIN="$VENV_PATH/bin/python"
LOG_DIR="/var/log/kasaai"
LOG_FILE="$LOG_DIR/precompute-queries.log"
COMPANY_NAMES=("premier_health_production" "ghana_tourism_production")

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=========================================="
log "Starting query pre-computation job"
log "=========================================="

# Activate virtual environment
source "$VENV_PATH/bin/activate"

# Pre-compute for each company
for COMPANY_NAME in "${COMPANY_NAMES[@]}"; do
    log "Pre-computing queries for: $COMPANY_NAME"

    # Call the pre-compute endpoint via curl
    API_URL="https://flow-api.ailabsafrica.com/knowledge-base/${COMPANY_NAME}/precompute"

    RESPONSE=$(curl -s -X POST "$API_URL?days=7&force=false" \
        -H "Content-Type: application/json" \
        -w "\nHTTP_STATUS:%{http_code}" 2>&1)

    HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
    BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d')

    if [ "$HTTP_STATUS" = "200" ]; then
        log "✅ Success for $COMPANY_NAME"
        log "Response: $BODY"
    else
        log "❌ Failed for $COMPANY_NAME (HTTP $HTTP_STATUS)"
        log "Response: $BODY"
    fi

    # Small delay between companies
    sleep 2
done

log "=========================================="
log "Query pre-computation job completed"
log "=========================================="

# Optional: Clean up old logs (keep last 30 days)
find "$LOG_DIR" -name "precompute-queries-*.log" -mtime +30 -delete 2>/dev/null || true

exit 0
