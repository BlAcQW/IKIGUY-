#!/bin/bash

#
# List All Voice Assistants using cURL
#
# This example demonstrates how to retrieve a list of all your voice assistants.
#

# Configuration
API_KEY="${KASAAI_API_KEY:-your_api_key_here}"
BASE_URL="https://developer.ailabsafrica.com"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if API key is set
if [ "$API_KEY" = "your_api_key_here" ]; then
    echo -e "${RED}❌ Error: KASAAI_API_KEY environment variable not set${NC}"
    echo "   Please set it with: export KASAAI_API_KEY=your_api_key"
    exit 1
fi

echo -e "${GREEN}📋 Listing Voice Assistants...${NC}\n"

# List all assistants
response=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/api/v1/assistants" \
  -H "X-API-Key: $API_KEY")

# Split response and status code
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

# Check status
if [ "$http_code" -eq 200 ]; then
    echo -e "${GREEN}✅ Assistants retrieved successfully!${NC}\n"

    # Display full JSON (pretty printed)
    echo "$body" | jq '.'

    # Extract and display summary
    total=$(echo "$body" | jq -r '.total')
    count=$(echo "$body" | jq -r '.assistants | length')

    echo -e "\n${BLUE}Summary:${NC}"
    echo "Total assistants: $total"
    echo "Displayed: $count"

    # Display each assistant
    echo -e "\n${BLUE}Assistants:${NC}"
    echo "$body" | jq -r '.assistants[] | "• \(.name) (ID: \(.id)) - Status: \(.status)"'
else
    echo -e "${RED}❌ Error listing assistants${NC}"
    echo "HTTP Status: $http_code"
    echo "$body" | jq '.'
    exit 1
fi

echo -e "\n${YELLOW}---${NC}\n"
echo -e "${GREEN}Now let's get details for a specific assistant...${NC}\n"

# Get first assistant ID
first_id=$(echo "$body" | jq -r '.assistants[0].id')

if [ "$first_id" != "null" ] && [ -n "$first_id" ]; then
    # Get specific assistant
    response=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/api/v1/assistants/$first_id" \
      -H "X-API-Key: $API_KEY")

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" -eq 200 ]; then
        echo -e "${GREEN}✅ Assistant details retrieved!${NC}\n"
        echo "$body" | jq '.'
    else
        echo -e "${RED}❌ Error getting assistant details${NC}"
        echo "HTTP Status: $http_code"
        echo "$body" | jq '.'
    fi
else
    echo -e "${YELLOW}ℹ️  No assistants found to display details${NC}"
fi

echo -e "\n${YELLOW}---${NC}\n"
echo -e "${BLUE}Pagination Example:${NC}\n"

# List with pagination
response=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/api/v1/assistants?limit=5&offset=0" \
  -H "X-API-Key: $API_KEY")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" -eq 200 ]; then
    echo -e "${GREEN}✅ First page (limit=5) retrieved!${NC}\n"
    count=$(echo "$body" | jq -r '.assistants | length')
    echo "Displaying $count assistants"
    echo "$body" | jq -r '.assistants[] | "• \(.name)"'
else
    echo -e "${RED}❌ Error with pagination${NC}"
    echo "HTTP Status: $http_code"
fi

echo -e "\n${GREEN}✨ Done!${NC}"
