#!/bin/bash

# Load environment variables from core_backend
# Using Gemini instead of OpenAI (2x cheaper, better for education)
export GEMINI_API_KEY="AIzaSyAACjmMMYIVH2Pq8Ns8KbOud-X8oCQMny4"
export MONGODB_URL="mongodb://admin:aawwER4444%25@127.0.0.1:27017/kasaai?authSource=admin"
export POSTGRES_PASSWORD="aawwER444444"
export POSTGRES_HOST="localhost"
export POSTGRES_PORT="5432"
export POSTGRES_USER="postgres"
export POSTGRES_DB="kasaai_core"

# Run the tests
cd /opt/kasaai/apps/studyflow/backend
python3 test_shared_services.py
