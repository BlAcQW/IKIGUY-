#!/bin/bash
#
# Test script for Asterisk REST API
#

BASE_URL="https://asterisk-api.ailabsafrica.com"

echo "============================================"
echo "Asterisk REST API Test Script"
echo "============================================"
echo ""

# Test 1: Health Check
echo "[1] Testing health endpoint..."
curl -s "$BASE_URL/health" | python3 -m json.tool
echo ""

# Test 2: Asterisk Status
echo "[2] Testing Asterisk status..."
curl -s "$BASE_URL/asterisk/status" | python3 -m json.tool
echo ""

# Test 3: Create SIP Peer
echo "[3] Creating test SIP peer..."
PHONE_NUMBER="+1555$(date +%s | tail -c 8)"
SIP_USERNAME="test_$(date +%s)"
curl -X POST "$BASE_URL/sip/peer" \
  -H "Content-Type: application/json" \
  -d "{
    \"number\": \"$PHONE_NUMBER\",
    \"sip_username\": \"$SIP_USERNAME\",
    \"sip_password\": \"test_password_123\",
    \"webhook_url\": \"https://api.ailabsafrica.com/voice/webhook/test\"
  }" | python3 -m json.tool
echo ""

# Test 4: Wait for reload
echo "[4] Waiting for Asterisk to reload..."
sleep 3
docker exec kasaai-asterisk-proxy asterisk -rx "module reload res_pjsip.so" >/dev/null 2>&1
sleep 2
echo ""

# Test 5: Query Created Peer
echo "[5] Querying created peer in Asterisk..."
docker exec kasaai-asterisk-proxy asterisk -rx "pjsip show endpoint $SIP_USERNAME" 2>/dev/null | head -15
echo ""

# Test 6: List All Peers
echo "[6] Listing all SIP peers..."
curl -s "$BASE_URL/sip/peers" | python3 -m json.tool
echo ""

echo "============================================"
echo "Test complete!"
echo "============================================"
