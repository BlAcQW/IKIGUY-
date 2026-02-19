#!/bin/bash

echo "=== KasaAI Developer Platform Python 3.12 Deployment ==="

# Stop the service first
echo "--- Stopping Developer Platform service ---"
sudo systemctl stop kasaai-dev-backend.service || true

# Navigate to developer platform backend directory
cd /opt/kasaai/apps/developer_platform/backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "--- Creating virtual environment ---"
    python3 -m venv venv
fi

# Activate virtual environment
echo "--- Activating virtual environment ---"
source venv/bin/activate

# Upgrade pip and setuptools first
echo "--- Upgrading pip and setuptools ---"
pip install --upgrade pip setuptools wheel

# Install distutils compatibility
echo "--- Installing distutils compatibility ---"
pip install distutils-compat

# Install Python 3.12 compatible requirements
echo "--- Installing Python 3.12 compatible requirements ---"
if [ -f "requirements-py312.txt" ]; then
    pip install -r requirements-py312.txt || {
        echo "Error: Failed to install Python 3.12 requirements"
        echo "Trying with updated standard requirements..."
        pip install -r requirements.txt
    }
else
    echo "Python 3.12 requirements file not found, using standard requirements"
    pip install -r requirements.txt
fi

# Deactivate virtual environment
deactivate

# Ensure consolidated environment file exists
if [ ! -f "/opt/kasaai/.env" ]; then
    echo "--- Creating consolidated environment file ---"
    sudo cp /opt/kasaai/env.example /opt/kasaai/.env
    echo "Environment file created. Please update the values in /opt/kasaai/.env"
fi

# Test database connection
echo "--- Testing database connection ---"
source venv/bin/activate

# Test MongoDB connection
echo "Testing MongoDB connection..."
python3 -c "
import os
from pymongo import MongoClient

# Load environment variables
env_file = '/opt/kasaai/.env'
if os.path.exists(env_file):
    with open(env_file, 'r') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                try:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
                except ValueError:
                    continue

# Get MongoDB URL and database name
mongo_url = os.getenv('MONGODB_URL', 'mongodb://localhost:27017')
mongo_db = os.getenv('MONGODB_DB', 'kasaai_dev')
print(f'Attempting to connect to: {mongo_url}/{mongo_db}')

try:
    client = MongoClient(mongo_url)
    client[mongo_db].command('ping')
    client.close()
    print('✅ MongoDB connection successful!')
except Exception as e:
    print(f'❌ MongoDB connection failed: {e}')
    print('Please ensure MongoDB is running and credentials are correct.')
"

deactivate

# Start the service
echo "--- Starting Developer Platform service ---"
sudo systemctl start kasaai-dev-backend.service

# Check service status
echo "--- Checking service status ---"
sudo systemctl status kasaai-dev-backend.service --no-pager

echo "=== Developer Platform deployment completed ==="
