#!/bin/bash

#
# Initiate an Outbound Call using cURL
#
# This example demonstrates how to initiate an outbound call using your voice assistant.
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

# Check for assistant ID argument
ASSISTANT_ID="$1"
PHONE_NUMBER="$2"

if [ -z "$ASSISTANT_ID" ] || [ -z "$PHONE_NUMBER" ]; then
    echo -e "${YELLOW}Usage: $0 <assistant_id> <phone_number>${NC}"
    echo ""
    echo "Example:"
    echo "  $0 asst_123abc +1234567890"
    echo ""
    echo "To get your assistant IDs, run: ./list_assistants.sh"
    exit 1
fi

echo -e "${GREEN}📞 Initiating Outbound Call...${NC}\n"
echo "Assistant ID: $ASSISTANT_ID"
echo "Phone Number: $PHONE_NUMBER"
echo ""

# Initiate call
response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/v1/calls" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"assistant_id\": \"$ASSISTANT_ID\",
    \"phone_number\": \"$PHONE_NUMBER\",
    \"task\": \"Make a friendly call to check customer satisfaction with recent purchase\"
  }")

# Split response and status code
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

# Check status
if [ "$http_code" -eq 201 ]; then
    echo -e "${GREEN}✅ Call initiated successfully!${NC}\n"
    echo "$body" | jq '.'

    # Extract call ID
    call_id=$(echo "$body" | jq -r '.id')
    call_status=$(echo "$body" | jq -r '.status')

    echo -e "\n${BLUE}Call Details:${NC}"
    echo "Call ID: $call_id"
    echo "Status: $call_status"
    echo "Phone: $PHONE_NUMBER"

    # Monitor call status
    echo -e "\n${YELLOW}Monitoring call status (polling every 3 seconds)...${NC}"

    for i in {1..10}; do
        sleep 3

        # Get call status
        status_response=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/api/v1/calls/$call_id" \
          -H "X-API-Key: $API_KEY")

        status_http_code=$(echo "$status_response" | tail -n1)
        status_body=$(echo "$status_response" | sed '$d')

        if [ "$status_http_code" -eq 200 ]; then
            current_status=$(echo "$status_body" | jq -r '.status')
            duration=$(echo "$status_body" | jq -r '.duration // 0')

            echo -e "${BLUE}[$i]${NC} Status: $current_status | Duration: ${duration}s"

            # Break if call is completed or failed
            if [ "$current_status" = "completed" ] || [ "$current_status" = "failed" ] || [ "$current_status" = "no-answer" ]; then
                echo -e "\n${GREEN}Call finished with status: $current_status${NC}"

                # Display final details
                echo -e "\n${BLUE}Final Call Details:${NC}"
                echo "$status_body" | jq '.'
                break
            fi
        else
            echo -e "${RED}Error checking call status${NC}"
            break
        fi

        if [ $i -eq 10 ]; then
            echo -e "\n${YELLOW}ℹ️  Call still in progress. Check later with:${NC}"
            echo "  curl -H \"X-API-Key: \$KASAAI_API_KEY\" $BASE_URL/api/v1/calls/$call_id"
        fi
    done

else
    echo -e "${RED}❌ Error initiating call${NC}"
    echo "HTTP Status: $http_code"
    echo "$body" | jq '.'
    exit 1
fi

echo -e "\n${YELLOW}---${NC}\n"
echo -e "${BLUE}You can also list all calls:${NC}"
echo "  curl -H \"X-API-Key: \$KASAAI_API_KEY\" $BASE_URL/api/v1/calls"

echo -e "\n${GREEN}✨ Done!${NC}"
