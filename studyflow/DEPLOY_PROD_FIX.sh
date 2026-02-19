#!/bin/bash
# Deployment script for production server (148.251.0.46)
# Run this on the PRODUCTION server to apply the universal admin fix

set -e

echo "=== StudyFlow Universal Admin Fix Deployment ==="
echo ""
echo "This script will:"
echo "1. Pull latest changes from GitHub (dev branch)"
echo "2. Restart the studyflow backend service"
echo ""

# Navigate to app directory
cd /opt/kasaai/apps

# Pull latest changes
echo "Pulling latest changes from GitHub..."
git fetch origin
git checkout dev
git pull origin dev

echo ""
echo "Changes pulled successfully!"
echo ""

# Restart service
echo "Restarting kasaai-studyflow service..."
sudo systemctl restart kasaai-studyflow

echo ""
echo "Waiting for service to start..."
sleep 3

# Check service status
sudo systemctl status kasaai-studyflow --no-pager -l | head -15

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Next steps:"
echo "1. Ask users to LOG OUT and LOG BACK IN to get fresh JWT tokens"
echo "2. Verify materials are now visible at https://studyflow.ailabsafrica.com"
echo ""
