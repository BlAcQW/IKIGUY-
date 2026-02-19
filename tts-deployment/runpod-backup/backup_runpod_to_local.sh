#!/bin/bash
################################################################################
# Backup RunPod Data to Local Machine
#
# Purpose: Sync all important files from RunPod back to local machine for:
#   - Git version control
#   - Disaster recovery (in case RunPod instance is deleted)
#   - Local development
#
# Author: AI Labs Africa
# Date: 2025-10-22
################################################################################

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
RUNPOD_HOST="194.68.245.121"
RUNPOD_PORT="22130"
RUNPOD_USER="root"
RUNPOD_KEY="$HOME/.ssh/id_ed25519"
LOCAL_BACKUP_DIR="/opt/kasaai/apps/tts-deployment/runpod-backup"

# Files/directories to backup from RunPod
BACKUP_ITEMS=(
    # Training scripts
    "/workspace/runpod_whisper_african_qlora_streaming.py"
    "/workspace/run_training.sh"
    "/workspace/start_whisper.sh"
    "/workspace/start_whisper_fixed.sh"

    # Setup scripts
    "/workspace/setup-runpod-tts.sh"
    "/workspace/setup_multi_language_training.sh"

    # Configuration files
    "/workspace/docker-compose.runpod.yml"

    # Important outputs (checkpoints, models)
    "/workspace/outputs"

    # Training logs
    "/workspace/*.log"
)

print_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

################################################################################
# Main Backup Function
################################################################################

backup_runpod_data() {
    print_header "Backing Up RunPod Data to Local Machine"

    # Create backup directory with timestamp
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_DIR="${LOCAL_BACKUP_DIR}/backups/${TIMESTAMP}"
    mkdir -p "$BACKUP_DIR"

    print_info "Backup location: $BACKUP_DIR"
    print_info "RunPod instance: ${RUNPOD_USER}@${RUNPOD_HOST}:${RUNPOD_PORT}"
    echo ""

    # Backup each item
    for item in "${BACKUP_ITEMS[@]}"; do
        item_name=$(basename "$item")
        print_info "Backing up: $item_name"

        # Check if it's a directory or file pattern
        if [[ "$item" == *"*"* ]]; then
            # Pattern (like *.log)
            rsync -avz --ignore-missing-args \
                -e "ssh -p ${RUNPOD_PORT} -i ${RUNPOD_KEY}" \
                "${RUNPOD_USER}@${RUNPOD_HOST}:${item}" \
                "${BACKUP_DIR}/" 2>/dev/null || print_info "  No files matching $item_name"
        else
            # Regular file or directory
            rsync -avz --ignore-missing-args \
                -e "ssh -p ${RUNPOD_PORT} -i ${RUNPOD_KEY}" \
                "${RUNPOD_USER}@${RUNPOD_HOST}:${item}" \
                "${BACKUP_DIR}/" 2>/dev/null || print_info "  $item_name not found (skipped)"
        fi
    done

    print_success "Backup completed!"
    echo ""

    # Show backup summary
    backup_size=$(du -sh "$BACKUP_DIR" | cut -f1)
    file_count=$(find "$BACKUP_DIR" -type f | wc -l)

    echo "📊 Backup Summary:"
    echo "  Location: $BACKUP_DIR"
    echo "  Size: $backup_size"
    echo "  Files: $file_count"
    echo ""

    # Create a latest symlink
    rm -f "${LOCAL_BACKUP_DIR}/backups/latest"
    ln -s "$BACKUP_DIR" "${LOCAL_BACKUP_DIR}/backups/latest"
    print_success "Latest backup link updated"
}

################################################################################
# Backup Training Data Manifests (not actual audio files - too large)
################################################################################

backup_data_manifests() {
    print_header "Backing Up Training Data Manifests"

    print_info "Backing up CSV manifests only (not audio files)"

    MANIFEST_DIR="${LOCAL_BACKUP_DIR}/backups/latest/manifests"
    mkdir -p "$MANIFEST_DIR"

    # Backup manifest/CSV files from training data
    rsync -avz --include='*/' --include='*.csv' --include='*.txt' --include='*.json' \
        --include='DATASET_SUMMARY.txt' --exclude='*' \
        -e "ssh -p ${RUNPOD_PORT} -i ${RUNPOD_KEY}" \
        "${RUNPOD_USER}@${RUNPOD_HOST}:/workspace/training-data/" \
        "${MANIFEST_DIR}/" 2>/dev/null || print_info "  No manifests found"

    print_success "Data manifests backed up"
}

################################################################################
# Create Git-friendly Structure
################################################################################

create_git_structure() {
    print_header "Creating Git-Friendly Structure"

    # Copy important files to runpod-backup for Git
    LATEST_BACKUP="${LOCAL_BACKUP_DIR}/backups/latest"

    if [ -d "$LATEST_BACKUP" ]; then
        # Copy Python scripts
        find "$LATEST_BACKUP" -name "*.py" -exec cp {} "${LOCAL_BACKUP_DIR}/" \; 2>/dev/null || true

        # Copy shell scripts
        find "$LATEST_BACKUP" -name "*.sh" -exec cp {} "${LOCAL_BACKUP_DIR}/" \; 2>/dev/null || true

        # Copy YAML files
        find "$LATEST_BACKUP" -name "*.yml" -o -name "*.yaml" -exec cp {} "${LOCAL_BACKUP_DIR}/" \; 2>/dev/null || true

        print_success "Files copied to runpod-backup directory for Git"
    fi
}

################################################################################
# Main Execution
################################################################################

main() {
    print_header "RunPod → Local Backup"

    # Check SSH key exists
    if [ ! -f "$RUNPOD_KEY" ]; then
        echo "❌ SSH key not found: $RUNPOD_KEY"
        exit 1
    fi

    # Test connection
    print_info "Testing connection to RunPod..."
    if ! ssh -p ${RUNPOD_PORT} -i ${RUNPOD_KEY} -o ConnectTimeout=10 \
        ${RUNPOD_USER}@${RUNPOD_HOST} "echo 'Connected'" &>/dev/null; then
        echo "❌ Cannot connect to RunPod"
        exit 1
    fi
    print_success "Connection successful"

    # Run backups
    backup_runpod_data
    backup_data_manifests
    create_git_structure

    print_header "✨ Backup Complete!"
    print_success "All RunPod files backed up to: ${LOCAL_BACKUP_DIR}/backups/"
    print_info "Latest backup: ${LOCAL_BACKUP_DIR}/backups/latest"
    echo ""
    print_info "💡 Next steps:"
    echo "   1. cd /opt/kasaai/apps/tts-deployment/runpod-backup"
    echo "   2. git add ."
    echo "   3. git commit -m 'Backup RunPod training files'"
    echo ""
}

main "$@"
