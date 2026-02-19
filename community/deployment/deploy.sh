#!/bin/bash

# African Language Community Platform - Production Deployment Script
# This script deploys the language community platform to production

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="language-community"
API_SERVICE="language-community-api"
FRONTEND_DIR="/opt/kasaai/apps/community/frontend-main"
BACKEND_DIR="/opt/kasaai/apps/community/backend"
DATA_DIR="/opt/kasaai/data/community"
NGINX_SITES="/etc/nginx/sites-available"
NGINX_ENABLED="/etc/nginx/sites-enabled"
SYSTEMD_DIR="/etc/systemd/system"

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✓${NC} $1"
}

warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ⚠${NC} $1"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ✗${NC} $1"
    exit 1
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root (use sudo)"
    fi
}

check_dependencies() {
    log "Checking system dependencies..."

    local deps=("nginx" "python3" "python3-pip" "python3-venv" "nodejs" "npm" "mongodb" "git" "certbot")
    for dep in "${deps[@]}"; do
        if ! command -v $dep &> /dev/null; then
            error "Required dependency '$dep' is not installed"
        fi
    done

    success "All dependencies are installed"
}

setup_directories() {
    log "Setting up directory structure..."

    # Create data directories
    mkdir -p "$DATA_DIR"/{uploads,datasets,logs,backups}
    mkdir -p /var/log/nginx
    mkdir -p /var/www/certbot

    # Set proper ownership
    chown -R www-data:www-data "$DATA_DIR"
    chown -R www-data:www-data "$BACKEND_DIR"

    success "Directories created and configured"
}

setup_python_environment() {
    log "Setting up Python virtual environment..."

    cd "$BACKEND_DIR"

    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi

    # Activate and install dependencies
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt

    success "Python environment configured"
}

build_frontend() {
    log "Building frontend application..."

    cd "$FRONTEND_DIR"

    # Install dependencies and build
    npm ci --production
    npm run build

    # Set proper ownership
    chown -R www-data:www-data dist/

    success "Frontend built successfully"
}

install_systemd_service() {
    log "Installing systemd service..."

    # Copy service file
    cp "/opt/kasaai/apps/community/deployment/${API_SERVICE}.service" "$SYSTEMD_DIR/"

    # Reload systemd and enable service
    systemctl daemon-reload
    systemctl enable "$API_SERVICE"

    success "Systemd service installed and enabled"
}

configure_nginx() {
    log "Configuring nginx..."

    # Copy nginx configurations
    cp "/opt/kasaai/apps/community/deployment/language-community.ailabsafrica.conf" "$NGINX_SITES/"
    cp "/opt/kasaai/apps/community/deployment/language-community-api.ailabsafrica.conf" "$NGINX_SITES/"

    # Enable sites
    ln -sf "$NGINX_SITES/language-community.ailabsafrica.conf" "$NGINX_ENABLED/"
    ln -sf "$NGINX_SITES/language-community-api.ailabsafrica.conf" "$NGINX_ENABLED/"

    # Test nginx configuration
    nginx -t || error "Nginx configuration test failed"

    success "Nginx configured successfully"
}

setup_ssl_certificates() {
    log "Setting up SSL certificates..."

    # Check if certificates already exist
    if [ -f "/etc/letsencrypt/live/language-community.ailabsafrica.com/fullchain.pem" ]; then
        warning "SSL certificates already exist, skipping certificate generation"
        return
    fi

    # Get certificates for both domains
    certbot certonly --webroot \
        -w /var/www/certbot \
        -d language-community.ailabsafrica.com \
        -d language-community-api.ailabsafrica.com \
        --agree-tos \
        --no-eff-email \
        --email admin@ailabsafrica.com || warning "SSL certificate generation failed - please run manually"

    # Set up auto-renewal
    (crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet --post-hook 'systemctl reload nginx'") | crontab -

    success "SSL certificates configured"
}

setup_mongodb() {
    log "Configuring MongoDB..."

    # Enable and start MongoDB
    systemctl enable mongod
    systemctl start mongod

    # Create database and user (if needed)
    mongo <<EOF || warning "MongoDB setup might need manual configuration"
use language_community
db.createUser({
    user: "language_community_user",
    pwd: "secure_password_change_this",
    roles: [
        { role: "readWrite", db: "language_community" }
    ]
})
EOF

    success "MongoDB configured"
}

setup_logrotate() {
    log "Setting up log rotation..."

    cat > /etc/logrotate.d/language-community << EOF
/var/log/nginx/language-community*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload nginx
    endscript
}

$DATA_DIR/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
}
EOF

    success "Log rotation configured"
}

setup_monitoring() {
    log "Setting up basic monitoring..."

    # Create monitoring script
    cat > /usr/local/bin/language-community-health-check << 'EOF'
#!/bin/bash

# Health check script for Language Community Platform

API_URL="http://127.0.0.1:8001/health"
LOG_FILE="/var/log/language-community-health.log"

timestamp() {
    date '+%Y-%m-%d %H:%M:%S'
}

# Check API health
if curl -sf "$API_URL" > /dev/null; then
    echo "$(timestamp) - API: OK" >> "$LOG_FILE"
else
    echo "$(timestamp) - API: FAILED" >> "$LOG_FILE"
    # Restart service if it's not responding
    systemctl restart language-community-api
    echo "$(timestamp) - API: RESTARTED" >> "$LOG_FILE"
fi

# Check disk space
DISK_USAGE=$(df /opt/kasaai/data/community | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 80 ]; then
    echo "$(timestamp) - DISK: WARNING - ${DISK_USAGE}% used" >> "$LOG_FILE"
fi

# Check MongoDB
if systemctl is-active --quiet mongod; then
    echo "$(timestamp) - MongoDB: OK" >> "$LOG_FILE"
else
    echo "$(timestamp) - MongoDB: FAILED" >> "$LOG_FILE"
    systemctl restart mongod
fi

# Cleanup old logs (keep last 1000 lines)
tail -1000 "$LOG_FILE" > "${LOG_FILE}.tmp" && mv "${LOG_FILE}.tmp" "$LOG_FILE"
EOF

    chmod +x /usr/local/bin/language-community-health-check

    # Add to crontab (run every 5 minutes)
    (crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/language-community-health-check") | crontab -

    success "Basic monitoring configured"
}

start_services() {
    log "Starting services..."

    # Start API service
    systemctl start "$API_SERVICE"
    systemctl status "$API_SERVICE" --no-pager -l

    # Reload nginx
    systemctl reload nginx
    systemctl status nginx --no-pager -l

    success "Services started successfully"
}

run_tests() {
    log "Running deployment tests..."

    sleep 5  # Wait for services to fully start

    # Test API health
    if curl -sf "http://127.0.0.1:8001/health" > /dev/null; then
        success "API health check passed"
    else
        error "API health check failed"
    fi

    # Test nginx configuration
    if curl -sf "http://127.0.0.1" > /dev/null; then
        success "Frontend serving test passed"
    else
        warning "Frontend serving test failed - check nginx configuration"
    fi

    success "Deployment tests completed"
}

main() {
    log "Starting African Language Community Platform deployment..."

    check_root
    check_dependencies
    setup_directories
    setup_python_environment
    build_frontend
    install_systemd_service
    configure_nginx
    setup_ssl_certificates
    setup_mongodb
    setup_logrotate
    setup_monitoring
    start_services
    run_tests

    success "Deployment completed successfully!"

    echo
    echo "🌍 African Language Community Platform is now running!"
    echo "📱 Frontend: https://language-community.ailabsafrica.com"
    echo "🔌 API: https://language-community-api.ailabsafrica.com"
    echo "📊 API Docs: https://language-community-api.ailabsafrica.com/docs"
    echo
    echo "Next steps:"
    echo "1. Update environment variables in /etc/systemd/system/${API_SERVICE}.service"
    echo "2. Configure Supabase credentials"
    echo "3. Set up proper backup procedures"
    echo "4. Configure monitoring alerts"
    echo "5. Review security settings"
}

# Parse command line arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [options]"
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --test-only    Run deployment tests only"
        exit 0
        ;;
    --test-only)
        run_tests
        exit 0
        ;;
    *)
        main
        ;;
esac