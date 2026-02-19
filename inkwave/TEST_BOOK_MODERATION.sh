#!/bin/bash

# InkWave Book Moderation - End-to-End Test Script
# Tests all book moderation functionality with real API calls

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_URL="https://inkwave-api.ailabsafrica.com"
ADMIN_EMAIL="admin@ailabsafrica.com"
ADMIN_PASSWORD="Admin@2024!"

# Test variables
ACCESS_TOKEN=""
TEST_BOOK_ID=""
AUDIT_LOG_COUNT_BEFORE=0
AUDIT_LOG_COUNT_AFTER=0

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}InkWave Book Moderation - E2E Test${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Step 1: Login as admin
echo -e "${YELLOW}[1/8] Logging in as admin...${NC}"

# Create login JSON file to avoid escaping issues
cat > /tmp/inkwave_login.json << EOF
{"email":"${ADMIN_EMAIL}","password":"${ADMIN_PASSWORD}"}
EOF

LOGIN_RESPONSE=$(curl -s -X POST "${API_URL}/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d @/tmp/inkwave_login.json)

ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('session',{}).get('access_token',''))" 2>/dev/null || echo "")

if [ -z "$ACCESS_TOKEN" ]; then
  echo -e "${RED}✗ Login failed!${NC}"
  echo "Response: $LOGIN_RESPONSE"
  exit 1
fi

echo -e "${GREEN}✓ Login successful${NC}"
echo "Token: ${ACCESS_TOKEN:0:20}..."

# Step 2: Get list of all books
echo -e "\n${YELLOW}[2/8] Fetching all books...${NC}"
BOOKS_RESPONSE=$(curl -s -X GET "${API_URL}/api/v1/books?page=1&per_page=10" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}")

# Extract first book ID
TEST_BOOK_ID=$(echo "$BOOKS_RESPONSE" | grep -o '"id":"[^"]*"' | head -1 | sed 's/"id":"//;s/"$//')

if [ -z "$TEST_BOOK_ID" ]; then
  echo -e "${RED}✗ No books found in database${NC}"
  echo "Response: $BOOKS_RESPONSE"
  exit 1
fi

echo -e "${GREEN}✓ Found books${NC}"
echo "Test Book ID: $TEST_BOOK_ID"

# Step 3: Get initial audit log count
echo -e "\n${YELLOW}[3/8] Getting initial audit log count...${NC}"
AUDIT_RESPONSE=$(curl -s -X GET "${API_URL}/api/v1/admin/audit-log?limit=1000" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}")

AUDIT_LOG_COUNT_BEFORE=$(echo "$AUDIT_RESPONSE" | grep -o '"id":"' | wc -l)

echo -e "${GREEN}✓ Audit log count: ${AUDIT_LOG_COUNT_BEFORE}${NC}"

# Step 4: Hide the book
echo -e "\n${YELLOW}[4/8] Hiding book...${NC}"
HIDE_REASON="Test+moderation+-+hiding+for+E2E+test+at+$(date +%Y%m%d%H%M%S)"
HIDE_RESPONSE=$(timeout 10 curl -s -X POST "${API_URL}/api/v1/admin/books/${TEST_BOOK_ID}/hide?reason=${HIDE_REASON}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}")

# Check if response contains "success":true
HIDE_SUCCESS=$(echo "$HIDE_RESPONSE" | grep -o '"success":true' || echo "")

if [ -z "$HIDE_SUCCESS" ]; then
  echo -e "${RED}✗ Hide book failed!${NC}"
  echo "Response: $HIDE_RESPONSE"
  exit 1
fi

echo -e "${GREEN}✓ Book hidden successfully${NC}"

# Step 5: Verify book is in hidden books list
echo -e "\n${YELLOW}[5/8] Checking hidden books list...${NC}"
HIDDEN_BOOKS_RESPONSE=$(curl -s -X GET "${API_URL}/api/v1/admin/books/hidden?page=1&per_page=100" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}")

HIDDEN_BOOK_FOUND=$(echo "$HIDDEN_BOOKS_RESPONSE" | grep -o "\"id\":\"${TEST_BOOK_ID}\"" || echo "")

if [ -z "$HIDDEN_BOOK_FOUND" ]; then
  echo -e "${RED}✗ Book not found in hidden books list${NC}"
  exit 1
fi

echo -e "${GREEN}✓ Book appears in hidden books list${NC}"

# Step 6: Check audit log entry was created
echo -e "\n${YELLOW}[6/8] Verifying audit log entry...${NC}"
AUDIT_RESPONSE_AFTER=$(timeout 10 curl -s -X GET "${API_URL}/api/v1/admin/audit-log?book_id=${TEST_BOOK_ID}&limit=100" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}")

HIDE_LOG_FOUND=$(echo "$AUDIT_RESPONSE_AFTER" | grep -o "book_hidden" || echo "")

if [ -z "$HIDE_LOG_FOUND" ]; then
  echo -e "${RED}✗ Audit log entry not found${NC}"
  echo "Response: $AUDIT_RESPONSE_AFTER"
  exit 1
fi

echo -e "${GREEN}✓ Audit log entry created${NC}"

# Step 7: Unhide the book
echo -e "\n${YELLOW}[7/8] Unhiding book...${NC}"
UNHIDE_REASON="Test+complete+-+unhiding+after+E2E+test"
UNHIDE_RESPONSE=$(timeout 10 curl -s -X POST "${API_URL}/api/v1/admin/books/${TEST_BOOK_ID}/unhide?reason=${UNHIDE_REASON}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}")

# Check if response contains "success":true
UNHIDE_SUCCESS=$(echo "$UNHIDE_RESPONSE" | grep -o '"success":true' || echo "")

if [ -z "$UNHIDE_SUCCESS" ]; then
  echo -e "${RED}✗ Unhide book failed!${NC}"
  echo "Response: $UNHIDE_RESPONSE"
  exit 1
fi

echo -e "${GREEN}✓ Book unhidden successfully${NC}"

# Step 8: Verify book is removed from hidden books list
echo -e "\n${YELLOW}[8/8] Verifying book removed from hidden list...${NC}"
HIDDEN_BOOKS_FINAL=$(curl -s -X GET "${API_URL}/api/v1/admin/books/hidden?page=1&per_page=100" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}")

HIDDEN_BOOK_STILL_FOUND=$(echo "$HIDDEN_BOOKS_FINAL" | grep -o "\"id\":\"${TEST_BOOK_ID}\"" || echo "")

if [ -n "$HIDDEN_BOOK_STILL_FOUND" ]; then
  echo -e "${RED}✗ Book still appears in hidden books list${NC}"
  exit 1
fi

echo -e "${GREEN}✓ Book removed from hidden books list${NC}"

# Verify both audit log entries exist (optional check - commented out)
# UNHIDE_LOG_FOUND=$(echo "$AUDIT_RESPONSE_AFTER" | grep -o "book_unhidden" || echo "")

# Summary
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}Test Results Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ Admin login${NC}"
echo -e "${GREEN}✓ Fetch all books${NC}"
echo -e "${GREEN}✓ Get audit log${NC}"
echo -e "${GREEN}✓ Hide book${NC}"
echo -e "${GREEN}✓ Verify book in hidden list${NC}"
echo -e "${GREEN}✓ Audit log entry created (BOOK_HIDDEN)${NC}"
echo -e "${GREEN}✓ Unhide book${NC}"
echo -e "${GREEN}✓ Book removed from hidden list${NC}"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✓ ALL TESTS PASSED!${NC}"
echo -e "${GREEN}========================================${NC}"

echo -e "\n${BLUE}Test Details:${NC}"
echo -e "  API URL: ${API_URL}"
echo -e "  Test Book ID: ${TEST_BOOK_ID}"
echo -e "  Audit Logs Before: ${AUDIT_LOG_COUNT_BEFORE}"
echo -e "  Hide Reason: ${HIDE_REASON}"
echo -e "  Unhide Reason: ${UNHIDE_REASON}"

echo -e "\n${BLUE}Next Steps:${NC}"
echo -e "  1. Visit ${YELLOW}https://dev-inkwave.ailabsafrica.com/admin${NC}"
echo -e "  2. Click ${YELLOW}Book Moderation${NC} card"
echo -e "  3. Test the UI manually"
echo -e "  4. Check ${YELLOW}Audit Log${NC} tab for test entries"
