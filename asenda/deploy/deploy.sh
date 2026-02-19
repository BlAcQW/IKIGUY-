#!/bin/bash
# Deployment script for Asenda.ai
# Run as root on the target server

set -e

echo "🚀 Deploying Asenda.ai..."

# Navigate to project directory
cd /opt/kasaai/apps/asenda

# Pull latest changes (if using git)
# git pull origin main

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Build the application
echo "🔨 Building application..."
npm run build

# Copy static files to standalone
echo "📁 Copying static files..."
cp -r public .next/standalone/
cp -r .next/static .next/standalone/.next/

# Copy systemd service file
echo "⚙️ Setting up systemd service..."
sudo cp deploy/kasaai-asenda.service /etc/systemd/system/
sudo systemctl daemon-reload

# Enable and start the service
sudo systemctl enable kasaai-asenda
sudo systemctl restart kasaai-asenda

# Check service status
echo "✅ Checking service status..."
sleep 3
sudo systemctl status kasaai-asenda --no-pager

# Copy nginx configuration
echo "🌐 Setting up Nginx..."
sudo cp deploy/asenda.ai.nginx.conf /etc/nginx/sites-available/asenda.ai.conf
sudo ln -sf /etc/nginx/sites-available/asenda.ai.conf /etc/nginx/sites-enabled/

# Test nginx configuration
sudo nginx -t

# Obtain SSL certificate (first time only)
# sudo certbot --nginx -d asenda.ai -d www.asenda.ai

# Reload nginx
sudo systemctl reload nginx

echo "✅ Deployment complete!"
echo "🌐 Site should be available at https://asenda.ai"
