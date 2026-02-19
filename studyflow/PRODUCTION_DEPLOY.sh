#!/bin/bash
# ONE-COMMAND PRODUCTION DEPLOYMENT
# Run this directly on production server: ssh root@148.251.0.46 'bash -s' < PRODUCTION_DEPLOY.sh

set -e

echo "================================================================"
echo "  StudyFlow Production Deployment - Universal Admin Fix"
echo "================================================================"
echo ""

# Navigate to app directory
cd /opt/kasaai/apps

echo "[1/5] Pulling latest changes from GitHub..."
git fetch origin
git checkout dev
git pull origin dev
echo "✓ Code updated"
echo ""

echo "[2/5] Checking changed files..."
git log -1 --stat | grep studyflow
echo ""

echo "[3/5] Restarting kasaai-studyflow service..."
sudo systemctl restart kasaai-studyflow
echo "✓ Service restarted"
echo ""

echo "[4/5] Waiting for service to start..."
sleep 5

echo "[5/5] Verifying service status..."
if sudo systemctl is-active --quiet kasaai-studyflow; then
    echo "✓ Service is running"
else
    echo "✗ Service failed to start!"
    sudo systemctl status kasaai-studyflow --no-pager -l | tail -20
    exit 1
fi
echo ""

echo "Testing API endpoint..."
if curl -f -s https://studyflow-api.ailabsafrica.com/health > /dev/null; then
    echo "✓ API is responding"
else
    echo "✗ API is not responding!"
    exit 1
fi
echo ""

echo "================================================================"
echo "  DEPLOYMENT SUCCESSFUL!"
echo "================================================================"
echo ""
echo "What was fixed:"
echo "  1. Universal admins now see ALL materials (not just their org)"
echo "  2. Supabase user metadata synced with MongoDB organizations"
echo ""
echo "USERS MUST LOG OUT AND LOG BACK IN to get fresh JWT tokens!"
echo ""
echo "Test at: https://studyflow.ailabsafrica.com"
echo "================================================================"
