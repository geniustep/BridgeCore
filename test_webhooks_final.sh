#!/bin/bash

# Final Webhook Testing Script
BASE_URL="https://bridgecore.geniura.com"
USERNAME="done"
PASSWORD=",,07Genius"
DATABASE="done"

echo "=== BridgeCore Webhooks Testing ==="
echo ""

# Login
echo "1. Login..."
LOGIN=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"$USERNAME\", \"password\": \"$PASSWORD\", \"database\": \"$DATABASE\"}" \
  -k)

TOKEN=$(echo $LOGIN | jq -r '.access_token')
USER_ID=$(echo $LOGIN | jq -r '.user.id')
SYSTEM_ID=$(echo $LOGIN | jq -r '.system_id')

echo "✅ Logged in as User ID: $USER_ID, System: $SYSTEM_ID"
echo ""

# Connect to Odoo
echo "2. Connecting to Odoo..."
CONNECT=$(curl -s -X POST "$BASE_URL/systems/$SYSTEM_ID/connect" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"url\": \"https://app.propanel.ma/odoo\",
    \"database\": \"$DATABASE\",
    \"username\": \"$USERNAME\",
    \"password\": \"$PASSWORD\",
    \"system_type\": \"odoo\"
  }" \
  -k)

echo "$CONNECT" | jq .
echo ""

sleep 2

# Test Webhooks
echo "3. Testing Webhook Endpoints..."
echo "3.1 List Events:"
curl -s -X GET "$BASE_URL/api/v1/webhooks/events?limit=5" \
  -H "Authorization: Bearer $TOKEN" \
  -k | jq . | head -15
echo ""

echo "3.2 Smart Sync Pull:"
curl -s -X POST "$BASE_URL/api/v2/sync/pull" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": $USER_ID,
    \"device_id\": \"test-device-$(date +%s)\",
    \"app_type\": \"sales_app\",
    \"limit\": 10
  }" \
  -k | jq .
echo ""

echo "✅ Testing Complete!"
