#!/bin/bash

# Voice Lab API Startup Script

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Voice Lab API...${NC}"

# Check if .env exists, if not copy from example
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file from .env.example...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}Please update .env with your configuration${NC}"
fi

# Create necessary directories
echo -e "${GREEN}Creating necessary directories...${NC}"
mkdir -p models data/uploads data/processed data/synthetic logs

# Check if running with Docker or locally
if [ "$1" == "docker" ]; then
    echo -e "${GREEN}Starting with Docker...${NC}"
    docker-compose up -d
    echo -e "${GREEN}Voice Lab API is running at http://localhost:8000${NC}"
    echo -e "${GREEN}View logs: docker-compose logs -f voice-lab-api${NC}"
else
    echo -e "${GREEN}Starting locally...${NC}"
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}Creating virtual environment...${NC}"
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    echo -e "${GREEN}Installing dependencies...${NC}"
    pip install -r api/requirements.txt
    
    # Start the API
    echo -e "${GREEN}Starting API server...${NC}"
    uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
fi