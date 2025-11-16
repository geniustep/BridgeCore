#!/bin/bash

# Complete Webhook Testing Guide
# This script demonstrates how to test the BridgeCore Webhook system

BASE_URL="https://bridgecore.geniura.com"
USERNAME="done"
PASSWORD=",,07Genius"
DATABASE="done"

echo "=========================================="
echo "BridgeCore Webhooks - Complete Test Guide"
echo "=========================================="
echo ""

# Step 1: Login
echo "📝 Step 1: Login to get JWT token"
echo "-----------------------------------"
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"$USERNAME\", \"password\": \"$PASSWORD\", \"database\": \"$DATABASE\"}" \
  -k)

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token // empty')
USER_ID=$(echo $LOGIN_RESPONSE | jq -r '.user.id // empty')
SYSTEM_ID=$(echo $LOGIN_RESPONSE | jq -r '.system_id // empty')

if [ -z "$TOKEN" ]; then
  echo "❌ Login failed!"
  echo "$LOGIN_RESPONSE" | jq .
  exit 1
fi

echo "✅ Login successful!"
echo "   User ID: $USER_ID"
echo "   System ID: $SYSTEM_ID"
echo "   Token: ${TOKEN:0:50}..."
echo ""

# Step 2: Health Checks (no auth needed)
echo "📝 Step 2: Health Checks"
echo "-----------------------------------"
echo "Webhook Health:"
curl -s "$BASE_URL/api/v1/webhooks/health" -k | jq .
echo ""
echo "Smart Sync Health:"
curl -s "$BASE_URL/api/v2/sync/health" -k | jq .
echo ""

# Step 3: Connect to Odoo (if needed)
echo "📝 Step 3: Connect to Odoo System"
echo "-----------------------------------"
echo "Connecting to Odoo..."
CONNECT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/systems/$SYSTEM_ID/connect" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"url\": \"https://app.propanel.ma/odoo\",
    \"database\": \"$DATABASE\",
    \"username\": \"$USERNAME\",
    \"password\": \"$PASSWORD\"
  }" \
  -k)

echo "$CONNECT_RESPONSE" | jq .
echo ""

# Wait a bit for connection to establish
sleep 2

# Step 4: Test Webhook Endpoints
echo "📝 Step 4: Test Webhook Endpoints (v1)"
echo "-----------------------------------"

echo "4.1 List Events:"
curl -s -X GET "$BASE_URL/api/v1/webhooks/events?limit=5" \
  -H "Authorization: Bearer $TOKEN" \
  -k | jq . | head -20
echo ""

echo "4.2 Check Updates:"
curl -s -X GET "$BASE_URL/api/v1/webhooks/check-updates?limit=50" \
  -H "Authorization: Bearer $TOKEN" \
  -k | jq .
echo ""

echo "4.3 List Events with Filter (sale.order):"
curl -s -X GET "$BASE_URL/api/v1/webhooks/events?model=sale.order&limit=5" \
  -H "Authorization: Bearer $TOKEN" \
  -k | jq . | head -20
echo ""

# Step 5: Test Smart Sync (v2)
echo "📝 Step 5: Test Smart Sync Endpoints (v2)"
echo "-----------------------------------"

DEVICE_ID="test-device-$(date +%s)"
echo "Device ID: $DEVICE_ID"
echo ""

echo "5.1 Smart Sync Pull:"
SYNC_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v2/sync/pull" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": $USER_ID,
    \"device_id\": \"$DEVICE_ID\",
    \"app_type\": \"sales_app\",
    \"limit\": 50
  }" \
  -k)

echo "$SYNC_RESPONSE" | jq .
echo ""

echo "5.2 Get Sync State:"
curl -s -X GET "$BASE_URL/api/v2/sync/state?user_id=$USER_ID&device_id=$DEVICE_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -k | jq .
echo ""

echo "=========================================="
echo "✅ Testing Complete!"
echo "=========================================="
echo ""
echo "📚 Available Endpoints:"
echo "  - GET  /api/v1/webhooks/health"
echo "  - GET  /api/v1/webhooks/events"
echo "  - GET  /api/v1/webhooks/check-updates"
echo "  - POST /api/v2/sync/pull"
echo "  - GET  /api/v2/sync/state"
echo "  - GET  /api/v2/sync/health"
echo ""
echo "📖 Full documentation: /docs"
