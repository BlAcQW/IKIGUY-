#!/bin/bash
#
# Deployment script for Asterisk REST API Service
# Deploys to production server (148.251.0.46)
#
# Usage: ./deploy.sh [--local|--production]
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="kasaai-asterisk-api"
SERVICE_DIR="/opt/kasaai/apps/shared/asterisk-api"
VENV_DIR="/opt/kasaai/apps/venv"
ENV_FILE="/opt/kasaai/.env"
NGINX_CONF="/etc/nginx/sites-available/asterisk-api.ailabsafrica.com.conf"
DOMAIN="asterisk-api.ailabsafrica.com"

# Parse arguments
MODE="${1:-local}"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Asterisk REST API Deployment Script${NC}"
echo -e "${BLUE}================================================${NC}"
echo -e "${GREEN}Mode: ${MODE}${NC}"
echo ""

# Function: Print step
print_step() {
    echo -e "${YELLOW}▶ $1${NC}"
}

# Function: Print success
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function: Print error
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function: Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Step 1: Check prerequisites
print_step "Step 1: Checking prerequisites..."

if [ ! -d "$VENV_DIR" ]; then
    print_error "Virtual environment not found at $VENV_DIR"
    exit 1
fi
print_success "Virtual environment found"

if [ ! -f "$ENV_FILE" ]; then
    print_error "Environment file not found at $ENV_FILE"
    echo "Please create $ENV_FILE with required variables"
    exit 1
fi
print_success "Environment file found"

# Step 2: Install Python dependencies
print_step "Step 2: Installing Python dependencies..."
cd "$SERVICE_DIR"
$VENV_DIR/bin/pip install -q -r requirements.txt
print_success "Dependencies installed"

# Step 3: Check if Asterisk is installed
print_step "Step 3: Checking Asterisk installation..."
if command_exists asterisk; then
    ASTERISK_VERSION=$(asterisk -V 2>/dev/null || echo "unknown")
    print_success "Asterisk installed: $ASTERISK_VERSION"
else
    print_error "Asterisk not installed - service will run in SIMULATION MODE"
    echo "  To install Asterisk: sudo apt install asterisk asterisk-modules"
fi

# Step 4: Test API locally
print_step "Step 4: Testing API locally..."

# Start API in background
echo "  Starting API on port 30040..."
$VENV_DIR/bin/python main.py > /tmp/asterisk-api-test.log 2>&1 &
API_PID=$!

# Wait for startup
sleep 3

# Test health endpoint
if curl -s http://localhost:30040/health > /dev/null 2>&1; then
    print_success "API health check passed"
else
    print_error "API health check failed"
    echo "  Check logs: cat /tmp/asterisk-api-test.log"
    kill $API_PID 2>/dev/null || true
    exit 1
fi

# Test root endpoint
if curl -s http://localhost:30040/ | grep -q "Asterisk REST API"; then
    print_success "API root endpoint working"
else
    print_error "API root endpoint failed"
    kill $API_PID 2>/dev/null || true
    exit 1
fi

# Stop test API
kill $API_PID 2>/dev/null || true
print_success "Local tests passed"

# If local mode, stop here
if [ "$MODE" = "local" ]; then
    echo ""
    echo -e "${GREEN}Local testing complete!${NC}"
    echo "  Logs: /tmp/asterisk-api-test.log"
    echo ""
    echo "To run in development:"
    echo "  cd $SERVICE_DIR"
    echo "  $VENV_DIR/bin/python main.py"
    echo ""
    echo "To deploy to production:"
    echo "  ./deploy.sh --production"
    exit 0
fi

# Production deployment
echo ""
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Production Deployment${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Step 5: Install systemd service
print_step "Step 5: Installing systemd service..."

if [ -f "kasaai-asterisk-api.service" ]; then
    sudo cp kasaai-asterisk-api.service /etc/systemd/system/
    sudo systemctl daemon-reload
    print_success "Service file installed"
else
    print_error "Service file not found"
    exit 1
fi

# Step 6: Configure nginx
print_step "Step 6: Configuring nginx..."

# Check if nginx is installed
if ! command_exists nginx; then
    print_error "Nginx not installed"
    echo "  Install with: sudo apt install nginx"
    exit 1
fi

# Copy nginx config
if [ -f "asterisk-api.ailabsafrica.com.conf" ]; then
    sudo cp asterisk-api.ailabsafrica.com.conf /etc/nginx/sites-available/

    # Enable site
    if [ ! -L "/etc/nginx/sites-enabled/asterisk-api.ailabsafrica.com.conf" ]; then
        sudo ln -s /etc/nginx/sites-available/asterisk-api.ailabsafrica.com.conf \
                    /etc/nginx/sites-enabled/
    fi

    # Test nginx config
    if sudo nginx -t > /dev/null 2>&1; then
        print_success "Nginx configuration valid"
    else
        print_error "Nginx configuration invalid"
        sudo nginx -t
        exit 1
    fi
else
    print_error "Nginx config file not found"
    exit 1
fi

# Step 7: Get SSL certificate
print_step "Step 7: Configuring SSL..."

if command_exists certbot; then
    # Check if certificate already exists
    if sudo certbot certificates 2>/dev/null | grep -q "$DOMAIN"; then
        print_success "SSL certificate already exists for $DOMAIN"
    else
        echo "  Obtaining SSL certificate..."
        sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email dev@ailabsafrica.com || {
            print_error "Failed to obtain SSL certificate"
            echo "  You can manually run: sudo certbot --nginx -d $DOMAIN"
        }
    fi
else
    print_error "Certbot not installed"
    echo "  Install with: sudo apt install certbot python3-certbot-nginx"
    echo "  Then run: sudo certbot --nginx -d $DOMAIN"
fi

# Step 8: Start service
print_step "Step 8: Starting service..."

sudo systemctl enable $SERVICE_NAME
sudo systemctl restart $SERVICE_NAME

# Wait for service to start
sleep 2

if sudo systemctl is-active --quiet $SERVICE_NAME; then
    print_success "Service started successfully"
else
    print_error "Service failed to start"
    echo "  Check logs: sudo journalctl -u $SERVICE_NAME -n 50"
    exit 1
fi

# Step 9: Reload nginx
print_step "Step 9: Reloading nginx..."
sudo systemctl reload nginx
print_success "Nginx reloaded"

# Step 10: Test deployment
print_step "Step 10: Testing deployment..."

# Test health endpoint
sleep 2
if curl -k -s https://$DOMAIN/health | grep -q "asterisk_connected"; then
    print_success "HTTPS health check passed"
else
    print_error "HTTPS health check failed"
    echo "  Try: curl -k https://$DOMAIN/health"
fi

# Final summary
echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  Deployment Complete!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Service Status:"
echo "  Status: $(sudo systemctl is-active $SERVICE_NAME)"
echo "  URL: https://$DOMAIN"
echo ""
echo "Useful Commands:"
echo "  View logs:    sudo journalctl -u $SERVICE_NAME -f"
echo "  Restart:      sudo systemctl restart $SERVICE_NAME"
echo "  Stop:         sudo systemctl stop $SERVICE_NAME"
echo "  Status:       sudo systemctl status $SERVICE_NAME"
echo ""
echo "API Documentation:"
echo "  Swagger UI:   https://$DOMAIN/docs"
echo "  ReDoc:        https://$DOMAIN/redoc"
echo "  Health:       https://$DOMAIN/health"
echo ""
echo "Test the API:"
echo "  curl https://$DOMAIN/health"
echo "  curl https://$DOMAIN/asterisk/status"
echo ""
