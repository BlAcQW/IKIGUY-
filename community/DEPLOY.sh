#!/bin/bash

# African Language Community Platform Deployment Script
# Deploys both frontend and backend with SSL certificates

set -e

echo "🚀 Deploying African Language Community Platform..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root"
   exit 1
fi

# Change to community directory
cd /opt/kasaai/apps/community

print_status "Checking prerequisites..."

# Check if MongoDB is running
if ! systemctl is-active --quiet mongodb; then
    print_status "Starting MongoDB..."
    systemctl start mongodb
    systemctl enable mongodb
fi

# Check if Redis is running
if ! systemctl is-active --quiet redis; then
    print_status "Starting Redis..."
    systemctl start redis
    systemctl enable redis
fi

# Check if nginx is installed
if ! command -v nginx &> /dev/null; then
    print_error "Nginx is not installed. Please install nginx first."
    exit 1
fi

# Check if certbot is installed
if ! command -v certbot &> /dev/null; then
    print_warning "Certbot not found. Installing..."
    apt update
    apt install -y certbot python3-certbot-nginx
fi

print_status "Setting up backend..."

# Backend setup
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
source venv/bin/activate
pip install -r requirements.txt

# Initialize database if .env exists
if [ -f ".env" ]; then
    print_status "Initializing database..."
    python init_database.py
else
    print_warning "No .env file found. Please create one from .env.example before running."
fi

# Install backend systemd service
print_status "Installing backend service..."
cp ../language-community-api.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable language-community-api.service

# Setup frontend
cd ../frontend

print_status "Setting up frontend..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

# Check if npm is available
if ! command -v npm &> /dev/null; then
    print_error "npm is not installed. Please install npm first."
    exit 1
fi

# Install dependencies
print_status "Installing frontend dependencies..."
npm install

# Build frontend if .env.local exists
if [ -f ".env.local" ]; then
    print_status "Building frontend..."
    npm run build
else
    print_warning "No .env.local file found. Please create one from .env.example before building."
fi

# Install frontend systemd service
print_status "Installing frontend service..."
cp language-community-frontend.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable language-community-frontend.service

# Setup nginx configurations
cd ..

print_status "Setting up nginx configurations..."

# Install nginx configurations
cp language-community-api.ailabsafrica.conf /etc/nginx/sites-available/
cp language-community.ailabsafrica.conf /etc/nginx/sites-available/

# Enable sites
ln -sf /etc/nginx/sites-available/language-community-api.ailabsafrica.conf /etc/nginx/sites-enabled/
ln -sf /etc/nginx/sites-available/language-community.ailabsafrica.conf /etc/nginx/sites-enabled/

# Test nginx configuration
print_status "Testing nginx configuration..."
if ! nginx -t; then
    print_error "Nginx configuration test failed!"
    exit 1
fi

# Get SSL certificates
print_status "Obtaining SSL certificates..."

# Check if certificates already exist
if [ ! -f "/etc/letsencrypt/live/language-community-api.ailabsafrica.com/fullchain.pem" ]; then
    print_status "Getting SSL certificate for API domain..."
    certbot --nginx -d language-community-api.ailabsafrica.com --non-interactive --agree-tos --email admin@ailabsafrica.com
else
    print_success "API SSL certificate already exists"
fi

if [ ! -f "/etc/letsencrypt/live/language-community.ailabsafrica.com/fullchain.pem" ]; then
    print_status "Getting SSL certificate for frontend domain..."
    certbot --nginx -d language-community.ailabsafrica.com --non-interactive --agree-tos --email admin@ailabsafrica.com
else
    print_success "Frontend SSL certificate already exists"
fi

# Start services
print_status "Starting services..."

# Start backend
systemctl start language-community-api.service
print_success "Backend service started"

# Wait a moment for backend to start
sleep 5

# Start frontend
systemctl start language-community-frontend.service
print_success "Frontend service started"

# Reload nginx
systemctl reload nginx
print_success "Nginx reloaded"

# Check service status
print_status "Checking service status..."

if systemctl is-active --quiet language-community-api.service; then
    print_success "✅ Backend API is running"
else
    print_error "❌ Backend API failed to start"
    print_status "Backend logs:"
    journalctl -u language-community-api.service -n 20 --no-pager
fi

if systemctl is-active --quiet language-community-frontend.service; then
    print_success "✅ Frontend is running"
else
    print_error "❌ Frontend failed to start"
    print_status "Frontend logs:"
    journalctl -u language-community-frontend.service -n 20 --no-pager
fi

if systemctl is-active --quiet nginx; then
    print_success "✅ Nginx is running"
else
    print_error "❌ Nginx is not running"
fi

# Test endpoints
print_status "Testing endpoints..."

# Test backend API
if curl -f -s https://language-community-api.ailabsafrica.com/health > /dev/null; then
    print_success "✅ Backend API health check passed"
else
    print_warning "⚠️ Backend API health check failed"
fi

# Test frontend
if curl -f -s https://language-community.ailabsafrica.com/ > /dev/null; then
    print_success "✅ Frontend health check passed"
else
    print_warning "⚠️ Frontend health check failed"
fi

print_success "🎉 Deployment completed!"
echo ""
echo "🌐 Your African Language Community Platform is now live:"
echo "   Frontend: https://language-community.ailabsafrica.com"
echo "   Backend API: https://language-community-api.ailabsafrica.com"
echo "   API Docs: https://language-community-api.ailabsafrica.com/docs"
echo ""
echo "📋 Service Management Commands:"
echo "   Backend:  systemctl {start|stop|restart|status} language-community-api.service"
echo "   Frontend: systemctl {start|stop|restart|status} language-community-frontend.service"
echo "   Nginx:    systemctl {reload|restart|status} nginx"
echo ""
echo "📊 View Logs:"
echo "   Backend:  journalctl -u language-community-api.service -f"
echo "   Frontend: journalctl -u language-community-frontend.service -f"
echo "   Nginx:    tail -f /var/log/nginx/language-community*.log"
echo ""
echo "🔐 SSL certificates will auto-renew via certbot."
echo ""
print_success "African Language Community Platform is ready to collect language data! 🌍✨"