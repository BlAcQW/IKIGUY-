#!/bin/bash

#
# Create an AI Voice Assistant using cURL
#
# This example demonstrates how to create a new voice assistant using the KasaAI API.
#

# Configuration
API_KEY="${KASAAI_API_KEY:-your_api_key_here}"
BASE_URL="https://developer.ailabsafrica.com"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if API key is set
if [ "$API_KEY" = "your_api_key_here" ]; then
    echo -e "${RED}❌ Error: KASAAI_API_KEY environment variable not set${NC}"
    echo "   Please set it with: export KASAAI_API_KEY=your_api_key"
    exit 1
fi

echo -e "${GREEN}🚀 Creating Voice Assistant...${NC}\n"

# Create assistant
response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/v1/assistants" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Customer Service Assistant",
    "system_prompt": "You are a friendly customer service assistant for TechCorp. Help customers with product inquiries, order status, and general support. Be professional, empathetic, and solution-oriented.",
    "voice": "alloy",
    "language": "en",
    "first_message": "Hello! I'\''m your TechCorp assistant. How can I help you today?",
    "model": "gpt-4o-mini",
    "provider": "openai"
  }')

# Split response and status code
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

# Check status
if [ "$http_code" -eq 201 ]; then
    echo -e "${GREEN}✅ Assistant created successfully!${NC}\n"
    echo "$body" | jq '.'

    # Extract and display key information
    assistant_id=$(echo "$body" | jq -r '.id')
    assistant_name=$(echo "$body" | jq -r '.name')
    assistant_status=$(echo "$body" | jq -r '.status')

    echo -e "\n${GREEN}Assistant Details:${NC}"
    echo "ID: $assistant_id"
    echo "Name: $assistant_name"
    echo "Status: $assistant_status"
else
    echo -e "${RED}❌ Error creating assistant${NC}"
    echo "HTTP Status: $http_code"
    echo "$body" | jq '.'
    exit 1
fi

echo -e "\n${YELLOW}---${NC}\n"
echo -e "${GREEN}Now let's create another assistant with custom configuration:${NC}\n"

# Create custom assistant
response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/v1/assistants" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sales Assistant",
    "system_prompt": "You are a persuasive sales assistant. Qualify leads and book appointments.",
    "voice": "nova",
    "language": "en",
    "first_message": "Hi! I'\''m calling about our premium services. Do you have a moment?",
    "model": "gpt-4o",
    "provider": "openai",
    "temperature": 0.7,
    "max_tokens": 500,
    "end_call_message": "Thank you for your time. Have a great day!"
  }')

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" -eq 201 ]; then
    echo -e "${GREEN}✅ Custom assistant created!${NC}\n"
    echo "$body" | jq '.'
else
    echo -e "${RED}❌ Error creating custom assistant${NC}"
    echo "HTTP Status: $http_code"
    echo "$body" | jq '.'
    exit 1
fi

echo -e "\n${GREEN}✨ Done!${NC}"
