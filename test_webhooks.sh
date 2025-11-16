#!/bin/bash

# BridgeCore Webhooks Testing Script
# Usage: ./test_webhooks.sh

BASE_URL="https://bridgecore.geniura.com"
USERNAME="done"
PASSWORD=",,07Genius"
DATABASE="done"

echo "=== BridgeCore Webhooks Testing ==="
echo ""

# Step 1: Login to get token
echo "1. Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"$USERNAME\", \"password\": \"$PASSWORD\", \"database\": \"$DATABASE\"}" \
  -k)

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
USER_ID=$(echo $LOGIN_RESPONSE | grep -o '"id":[0-9]*' | cut -d':' -f2)

if [ -z "$TOKEN" ]; then
  echo "❌ Login failed!"
  echo "Response: $LOGIN_RESPONSE"
  exit 1
fi

echo "✅ Login successful!"
echo "Token: ${TOKEN:0:50}..."
echo "User ID: $USER_ID"
echo ""

# Step 2: Test Webhook Health Check
echo "2. Testing Webhook Health Check..."
curl -s -X GET "$BASE_URL/api/v1/webhooks/health" -k | jq .
echo ""

# Step 3: Test Smart Sync Health Check
echo "3. Testing Smart Sync Health Check..."
curl -s -X GET "$BASE_URL/api/v2/sync/health" -k | jq .
echo ""

# Step 4: Test List Events (v1)
echo "4. Testing List Events (v1)..."
curl -s -X GET "$BASE_URL/api/v1/webhooks/events?limit=10" \
  -H "Authorization: Bearer $TOKEN" \
  -k | jq .
echo ""

# Step 5: Test Check Updates (v1)
echo "5. Testing Check Updates (v1)..."
curl -s -X GET "$BASE_URL/api/v1/webhooks/check-updates?limit=50" \
  -H "Authorization: Bearer $TOKEN" \
  -k | jq .
echo ""

# Step 6: Test Smart Sync Pull (v2)
echo "6. Testing Smart Sync Pull (v2)..."
DEVICE_ID="test-device-$(date +%s)"
curl -s -X POST "$BASE_URL/api/v2/sync/pull" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\": $USER_ID, \"device_id\": \"$DEVICE_ID\", \"app_type\": \"sales_app\", \"limit\": 50}" \
  -k | jq .
echo ""

# Step 7: Test Get Sync State (v2)
echo "7. Testing Get Sync State (v2)..."
curl -s -X GET "$BASE_URL/api/v2/sync/state?user_id=$USER_ID&device_id=$DEVICE_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -k | jq .
echo ""

# Step 8: Test List Events with Filters
echo "8. Testing List Events with Filters (model=sale.order)..."
curl -s -X GET "$BASE_URL/api/v1/webhooks/events?model=sale.order&limit=5" \
  -H "Authorization: Bearer $TOKEN" \
  -k | jq .
echo ""

echo "=== Testing Complete ==="
