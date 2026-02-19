#!/bin/bash

# KasaAI Drive - Deployment Script
# This script deploys the Drive backend and frontend to production

set -e

echo "========================================="
echo "KasaAI Drive - Deployment Script"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ==================== BACKEND DEPLOYMENT ====================

echo -e "${YELLOW}[1/6] Installing backend dependencies...${NC}"
cd /opt/kasaai/apps/drive/backend
/opt/kasaai/apps/venv/bin/pip install -r requirements.txt

echo -e "${GREEN}✓ Backend dependencies installed${NC}"
echo ""

# ==================== SYSTEMD SERVICE ====================

echo -e "${YELLOW}[2/6] Setting up systemd service...${NC}"
sudo cp /opt/kasaai/apps/drive/kasaai-drive-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable kasaai-drive-backend

echo -e "${GREEN}✓ Systemd service configured${NC}"
echo ""

# ==================== NGINX CONFIGURATION ====================

echo -e "${YELLOW}[3/6] Configuring Nginx...${NC}"

# Copy nginx configs
sudo cp /opt/kasaai/apps/drive/drive-api.ailabsafrica.com.conf /etc/nginx/sites-available/
sudo cp /opt/kasaai/apps/drive/drive.ailabsafrica.com.conf /etc/nginx/sites-available/

# Enable sites
sudo ln -sf /etc/nginx/sites-available/drive-api.ailabsafrica.com.conf /etc/nginx/sites-enabled/
sudo ln -sf /etc/nginx/sites-available/drive.ailabsafrica.com.conf /etc/nginx/sites-enabled/

# Test nginx configuration
sudo nginx -t

echo -e "${GREEN}✓ Nginx configured${NC}"
echo ""

# ==================== SSL CERTIFICATES ====================

echo -e "${YELLOW}[4/6] Obtaining SSL certificates...${NC}"

# Check if certificates already exist
if [ ! -f /etc/letsencrypt/live/drive-api.ailabsafrica.com/fullchain.pem ]; then
    echo "Obtaining SSL certificate for drive-api.ailabsafrica.com..."
    sudo certbot --nginx -d drive-api.ailabsafrica.com --non-interactive --agree-tos -m admin@ailabsafrica.com
else
    echo "SSL certificate for drive-api.ailabsafrica.com already exists"
fi

if [ ! -f /etc/letsencrypt/live/drive.ailabsafrica.com/fullchain.pem ]; then
    echo "Obtaining SSL certificate for drive.ailabsafrica.com..."
    sudo certbot --nginx -d drive.ailabsafrica.com --non-interactive --agree-tos -m admin@ailabsafrica.com
else
    echo "SSL certificate for drive.ailabsafrica.com already exists"
fi

echo -e "${GREEN}✓ SSL certificates configured${NC}"
echo ""

# ==================== FRONTEND DEPLOYMENT ====================

echo -e "${YELLOW}[5/6] Building frontend...${NC}"
cd /opt/kasaai/apps/drive/frontend

# Copy environment file if it doesn't exist
if [ ! -f .env.local ]; then
    cp .env.local.example .env.local
    echo "⚠️  .env.local created from example. Please update with production values."
fi

# Install dependencies and build
npm install
npm run build

echo -e "${GREEN}✓ Frontend built${NC}"
echo ""

# ==================== START SERVICES ====================

echo -e "${YELLOW}[6/6] Starting services...${NC}"

# Reload nginx
sudo systemctl reload nginx

# Start backend service
sudo systemctl restart kasaai-drive-backend

# Check service status
sleep 2
sudo systemctl status kasaai-drive-backend --no-pager

echo -e "${GREEN}✓ Services started${NC}"
echo ""

# ==================== SUMMARY ====================

echo "========================================="
echo -e "${GREEN}Deployment Complete!${NC}"
echo "========================================="
echo ""
echo "Backend API: https://drive-api.ailabsafrica.com"
echo "Frontend: https://drive.ailabsafrica.com"
echo ""
echo "To view backend logs:"
echo "  sudo journalctl -u kasaai-drive-backend -f"
echo ""
echo "To start frontend in production:"
echo "  cd /opt/kasaai/apps/drive/frontend && npm start"
echo ""
echo "To restart backend:"
echo "  sudo systemctl restart kasaai-drive-backend"
echo ""
