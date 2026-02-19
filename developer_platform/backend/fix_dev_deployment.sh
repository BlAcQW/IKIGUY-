#!/bin/bash

echo "=== KasaAI Developer Platform Deployment Fix ==="
echo "This script fixes Python 3.12 compatibility and database connection issues"

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "Error: requirements.txt not found. Please run this script from the developer_platform/backend directory."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
echo "Detected Python version: $PYTHON_VERSION"

# Stop the service first
echo "--- Stopping Developer Platform service ---"
sudo systemctl stop kasaai-dev-backend.service || true

if [[ "$PYTHON_VERSION" == "3.12" ]]; then
    echo "Python 3.12 detected. Applying compatibility fixes..."
    
    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        echo "--- Activating virtual environment ---"
        source venv/bin/activate
    else
        echo "--- Creating virtual environment ---"
        python3 -m venv venv
        source venv/bin/activate
    fi
    
    # Upgrade pip and setuptools
    echo "--- Upgrading pip and setuptools ---"
    pip install --upgrade pip setuptools wheel
    
    # Install distutils compatibility
    echo "--- Installing distutils compatibility ---"
    pip install distutils-compat
    
    # Install requirements with Python 3.12 compatible versions
    echo "--- Installing Python 3.12 compatible requirements ---"
    if [ -f "requirements-py312.txt" ]; then
        pip install -r requirements-py312.txt || {
            echo "Error: Failed to install Python 3.12 compatible requirements"
            echo "Falling back to original requirements with fixes..."
            pip install -r requirements.txt
        }
    else
        echo "Python 3.12 requirements file not found, using standard requirements"
        pip install -r requirements.txt
    fi
    
    echo "=== Installation completed successfully ==="
else
    echo "Python version $PYTHON_VERSION detected. Using standard installation..."
    
    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        echo "--- Activating virtual environment ---"
        source venv/bin/activate
    else
        echo "--- Creating virtual environment ---"
        python3 -m venv venv
        source venv/bin/activate
    fi
    
    # Install requirements
    echo "--- Installing requirements ---"
    pip install -r requirements.txt
fi

# Deactivate virtual environment
deactivate

# Check if the consolidated environment file exists
if [ ! -f "/opt/kasaai/.env" ]; then
    echo "--- Creating consolidated environment file ---"
    sudo cp /opt/kasaai/env.example /opt/kasaai/.env
    echo "Environment file created. Please update the values in /opt/kasaai/.env"
fi

# Test database connection
echo "--- Testing database connection ---"
cd /opt/kasaai/apps/developer_platform/backend
source venv/bin/activate

# Test MongoDB connection
echo "Testing MongoDB connection..."
python3 -c "
import os
from pymongo import MongoClient
from urllib.parse import urlparse

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

# Get MongoDB connection info
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
    print('Please ensure MongoDB is running and environment variables are correct.')
"

deactivate

# Start the service
echo "--- Starting Developer Platform service ---"
sudo systemctl start kasaai-dev-backend.service

# Check service status
echo "--- Checking service status ---"
sudo systemctl status kasaai-dev-backend.service --no-pager

echo "=== Developer Platform deployment fix completed ==="
