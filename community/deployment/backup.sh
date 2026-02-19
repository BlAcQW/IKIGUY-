#!/bin/bash

# African Language Community Platform - Backup Script
# Automated backup for MongoDB, uploaded files, and configuration

set -e

# Configuration
BACKUP_DIR="/opt/kasaai/data/community/backups"
DATA_DIR="/opt/kasaai/data/community"
CONFIG_DIR="/opt/kasaai/apps/community"
S3_BUCKET="ailabs-community-backups"  # Optional S3 backup
RETENTION_DAYS=30
MAX_BACKUP_SIZE="10G"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✓${NC} $1"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ✗${NC} $1"
    exit 1
}

warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ⚠${NC} $1"
}

check_prerequisites() {
    log "Checking backup prerequisites..."

    # Check if backup directory exists
    mkdir -p "$BACKUP_DIR"

    # Check available disk space
    local available_space=$(df "$BACKUP_DIR" | awk 'NR==2 {print $4}')
    local required_space=10485760  # 10GB in KB

    if [ "$available_space" -lt "$required_space" ]; then
        warning "Low disk space for backups: $(($available_space/1024/1024))GB available"
    fi

    # Check MongoDB connection
    if ! mongosh --eval "db.adminCommand('ping')" >/dev/null 2>&1; then
        error "Cannot connect to MongoDB"
    fi

    success "Prerequisites check passed"
}

backup_mongodb() {
    log "Backing up MongoDB database..."

    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_path="$BACKUP_DIR/mongodb_$timestamp"

    # Create MongoDB dump
    mongodump --db language_community --out "$backup_path" --quiet

    if [ $? -eq 0 ]; then
        # Compress the backup
        tar -czf "${backup_path}.tar.gz" -C "$BACKUP_DIR" "mongodb_$timestamp"
        rm -rf "$backup_path"
        success "MongoDB backup completed: ${backup_path}.tar.gz"
    else
        error "MongoDB backup failed"
    fi
}

backup_uploaded_files() {
    log "Backing up uploaded files..."

    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_path="$BACKUP_DIR/uploads_$timestamp.tar.gz"

    if [ -d "$DATA_DIR/uploads" ]; then
        # Create compressed archive of uploads
        tar -czf "$backup_path" -C "$DATA_DIR" uploads

        if [ $? -eq 0 ]; then
            success "File uploads backup completed: $backup_path"
        else
            error "File uploads backup failed"
        fi
    else
        warning "No uploads directory found, skipping file backup"
    fi
}

backup_configuration() {
    log "Backing up configuration files..."

    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_path="$BACKUP_DIR/config_$timestamp.tar.gz"

    # Backup configuration files (excluding sensitive data)
    tar -czf "$backup_path" \
        --exclude="*.log" \
        --exclude="venv" \
        --exclude="node_modules" \
        --exclude="dist" \
        --exclude="*.pyc" \
        --exclude="__pycache__" \
        -C "/opt/kasaai/apps" community/deployment community/backend community/frontend-main/src

    if [ $? -eq 0 ]; then
        success "Configuration backup completed: $backup_path"
    else
        error "Configuration backup failed"
    fi
}

backup_nginx_config() {
    log "Backing up nginx configuration..."

    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_path="$BACKUP_DIR/nginx_$timestamp.tar.gz"

    # Backup nginx site configurations
    tar -czf "$backup_path" \
        -C /etc/nginx sites-available/language-community.ailabsafrica.conf \
        sites-available/language-community-api.ailabsafrica.conf 2>/dev/null || warning "Some nginx configs not found"

    success "Nginx configuration backup completed: $backup_path"
}

upload_to_s3() {
    if [ -z "$S3_BUCKET" ] || ! command -v aws &> /dev/null; then
        warning "S3 backup not configured or AWS CLI not available"
        return
    fi

    log "Uploading backups to S3..."

    local today=$(date +%Y%m%d)

    # Upload today's backups to S3
    aws s3 sync "$BACKUP_DIR" "s3://$S3_BUCKET/language-community/$today/" \
        --exclude "*" \
        --include "*$(date +%Y%m%d)*" \
        --quiet

    if [ $? -eq 0 ]; then
        success "S3 upload completed"
    else
        warning "S3 upload failed"
    fi
}

cleanup_old_backups() {
    log "Cleaning up old backups..."

    # Remove local backups older than retention period
    find "$BACKUP_DIR" -name "*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete

    # Remove empty directories
    find "$BACKUP_DIR" -type d -empty -delete

    success "Old backups cleaned up (kept last $RETENTION_DAYS days)"
}

generate_backup_report() {
    log "Generating backup report..."

    local report_file="$BACKUP_DIR/backup_report_$(date +%Y%m%d).txt"
    local today=$(date +%Y%m%d)

    cat > "$report_file" << EOF
African Language Community Platform - Backup Report
Generated: $(date)

=== BACKUP SUMMARY ===
Backup Directory: $BACKUP_DIR
Retention Period: $RETENTION_DAYS days

=== TODAY'S BACKUPS ===
$(ls -lh "$BACKUP_DIR"/*$today* 2>/dev/null || echo "No backups found for today")

=== DISK USAGE ===
$(df -h "$BACKUP_DIR")

=== BACKUP DIRECTORY SIZE ===
$(du -sh "$BACKUP_DIR")

=== MONGODB STATUS ===
$(mongosh --eval "db.serverStatus().connections" --quiet 2>/dev/null || echo "MongoDB connection failed")

=== SERVICE STATUS ===
$(systemctl is-active language-community-api)

=== RECENT BACKUPS ===
$(find "$BACKUP_DIR" -name "*.tar.gz" -type f -mtime -7 -exec ls -lh {} \; | head -10)
EOF

    success "Backup report generated: $report_file"
}

verify_backups() {
    log "Verifying backup integrity..."

    local today=$(date +%Y%m%d)
    local failed_backups=0

    # Test each backup archive
    for backup in "$BACKUP_DIR"/*$today*.tar.gz; do
        if [ -f "$backup" ]; then
            if tar -tzf "$backup" >/dev/null 2>&1; then
                success "Backup verified: $(basename "$backup")"
            else
                error "Corrupted backup: $(basename "$backup")"
                ((failed_backups++))
            fi
        fi
    done

    if [ $failed_backups -eq 0 ]; then
        success "All backups verified successfully"
    else
        error "$failed_backups backup(s) failed verification"
    fi
}

main() {
    log "Starting African Language Community Platform backup..."

    check_prerequisites
    backup_mongodb
    backup_uploaded_files
    backup_configuration
    backup_nginx_config
    verify_backups
    upload_to_s3
    cleanup_old_backups
    generate_backup_report

    success "Backup process completed successfully!"

    # Display summary
    echo
    echo "📊 Backup Summary:"
    echo "📁 Location: $BACKUP_DIR"
    echo "📈 Total size: $(du -sh "$BACKUP_DIR" | cut -f1)"
    echo "🗂️ Files: $(find "$BACKUP_DIR" -name "*.tar.gz" -type f | wc -l) backup archives"
    echo "⏰ Next cleanup: $(date -d "+$RETENTION_DAYS days" +%Y-%m-%d)"
}

# Parse command line arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [options]"
        echo "Options:"
        echo "  --help, -h      Show this help message"
        echo "  --verify-only   Only verify existing backups"
        echo "  --cleanup-only  Only cleanup old backups"
        echo "  --report-only   Only generate backup report"
        exit 0
        ;;
    --verify-only)
        verify_backups
        exit 0
        ;;
    --cleanup-only)
        cleanup_old_backups
        exit 0
        ;;
    --report-only)
        generate_backup_report
        exit 0
        ;;
    *)
        main
        ;;
esac