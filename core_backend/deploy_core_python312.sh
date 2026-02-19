#!/bin/bash

echo "=== KasaAI Core Backend Python 3.12 Deployment ==="

# Stop the service first
echo "--- Stopping Core Backend service ---"
sudo systemctl stop kasaai-core-backend.service || true

# Navigate to core backend directory
cd /opt/kasaai/apps/core_backend

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

# Test PostgreSQL connection
echo "Testing PostgreSQL connection..."
python3 -c "
import os
import psycopg2

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

# Get database URL
db_url = os.getenv('CORE_DB_URL', 'postgresql://postgres:aawwER444444@localhost:5432/kasaai_core')
print(f'Attempting to connect to: {db_url}')

try:
    conn = psycopg2.connect(db_url)
    print('✅ PostgreSQL connection successful!')
    conn.close()
except Exception as e:
    print(f'❌ PostgreSQL connection failed: {e}')
    print('Please check:')
    print('1. PostgreSQL is running on localhost:5433')
    print('2. Database kasaai_core exists')
    print('3. User postgres has access')
    print('4. Environment variables are correct')
"

deactivate

# Start the service
echo "--- Starting Core Backend service ---"
sudo systemctl start kasaai-core-backend.service

# Check service status
echo "--- Checking service status ---"
sudo systemctl status kasaai-core-backend.service --no-pager

echo "=== Core Backend deployment completed ==="
