#!/bin/bash

echo "=== KasaAI Platform Deployment Script ==="

# Stop all services first
echo "--- Stopping all KasaAI services ---"
sudo systemctl stop kasaai-core-backend.service || true
sudo systemctl stop kasaai-dev-backend.service || true
sudo systemctl stop kasaai-edge-node.service || true

echo "--- Navigating to project directory ---"
cd /opt/kasaai/ || { echo "Error: Directory not found. Exiting."; exit 1; }

echo "--- Pulling latest code from Git ---"
git pull origin main || { echo "Error: Git pull failed. Exiting."; exit 1; }

# =============================================================================
# CORE BACKEND DEPLOYMENT
# =============================================================================
echo "--- Deploying Core Backend ---"
cd /opt/kasaai/apps/core_backend || { echo "Error: Core backend directory not found. Exiting."; exit 1; }

echo "--- Activating Core Backend virtual environment ---"
source /opt/kasaai/apps/core_backend/venv/bin/activate || { echo "Error: Core backend virtual environment not found or failed to activate. Exiting."; exit 1; }

echo "--- Installing/Updating Core Backend Python dependencies ---"
pip install -r requirements.txt || { echo "Error: Core backend pip install failed. Exiting."; exit 1; }

echo "--- Deactivating Core Backend virtual environment ---"
deactivate

echo "--- Starting Core Backend service ---"
sudo systemctl start kasaai-core-backend.service || { echo "Error: Failed to start Core Backend service. Check logs. Exiting."; exit 1; }

echo "--- Core Backend deployment completed. Checking service status... ---"
sudo systemctl status kasaai-core-backend.service --no-pager
sudo journalctl -u kasaai-core-backend.service --since "1 minute ago" --no-pager

# =============================================================================
# DEVELOPER BACKEND DEPLOYMENT
# =============================================================================
echo "--- Deploying Developer Backend ---"
cd /opt/kasaai/apps/developer_platform/backend || { echo "Error: Developer backend directory not found. Exiting."; exit 1; }

echo "--- Activating Developer Backend virtual environment ---"
source /opt/kasaai/apps/developer_platform/venv/bin/activate || { echo "Error: Developer backend virtual environment not found or failed to activate. Exiting."; exit 1; }

echo "--- Installing/Updating Developer Backend Python dependencies ---"
pip install -r requirements.txt || { echo "Error: Developer backend pip install failed. Exiting."; exit 1; }

echo "--- Deactivating Developer Backend virtual environment ---"
deactivate

echo "--- Starting Developer Backend service ---"
sudo systemctl start kasaai-dev-backend.service || { echo "Error: Failed to start Developer Backend service. Check logs. Exiting."; exit 1; }

echo "--- Developer Backend deployment completed. Checking service status... ---"
sudo systemctl status kasaai-dev-backend.service --no-pager
sudo journalctl -u kasaai-dev-backend.service --since "1 minute ago" --no-pager

# =============================================================================
# EDGE NODE DEPLOYMENT
# =============================================================================
echo "--- Deploying Edge Node ---"
cd /opt/kasaai/apps/edge || { echo "Error: Edge node directory not found. Exiting."; exit 1; }

echo "--- Activating Edge Node virtual environment ---"
source /opt/kasaai/apps/edge/venv/bin/activate || { echo "Error: Edge node virtual environment not found or failed to activate. Exiting."; exit 1; }

echo "--- Fixing Python 3.12 compatibility issues ---"
pip install --upgrade pip setuptools wheel || { echo "Error: Failed to upgrade pip/setuptools. Exiting."; exit 1; }

echo "--- Installing/Updating Edge Node Python dependencies ---"
pip install -r requirements.txt || { echo "Error: Edge node pip install failed. Exiting."; exit 1; }

echo "--- Deactivating Edge Node virtual environment ---"
deactivate

echo "--- Starting Edge Node service ---"
sudo systemctl start kasaai-edge-node.service || { echo "Error: Failed to start Edge Node service. Check logs. Exiting."; exit 1; }

echo "--- Edge Node deployment completed. Checking service status... ---"
sudo systemctl status kasaai-edge-node.service --no-pager
sudo journalctl -u kasaai-edge-node.service --since "1 minute ago" --no-pager

# =============================================================================
# FINAL STATUS CHECK
# =============================================================================
echo "=== Final Service Status Check ==="
echo "--- Core Backend Status ---"
sudo systemctl is-active kasaai-core-backend.service
sudo systemctl is-enabled kasaai-core-backend.service

echo "--- Developer Backend Status ---"
sudo systemctl is-active kasaai-dev-backend.service
sudo systemctl is-enabled kasaai-dev-backend.service

echo "--- Edge Node Status ---"
sudo systemctl is-active kasaai-edge-node.service
sudo systemctl is-enabled kasaai-edge-node.service

echo "=== Deployment completed successfully! ==="
echo "Services are now running:"
echo "- Core Backend: http://localhost:30027"
echo "- Developer Backend: http://localhost:30028"
echo "- Edge Node: http://localhost:30029"
