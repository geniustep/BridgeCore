#!/bin/bash

# Simple Webhook Testing - Step by Step
BASE_URL="https://bridgecore.geniura.com"
USERNAME="done"
PASSWORD=",,07Genius"
DATABASE="done"

echo "=== Simple Webhook Testing ==="
echo ""

# Step 1: Login
echo "1. Login..."
LOGIN=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"$USERNAME\", \"password\": \"$PASSWORD\", \"database\": \"$DATABASE\"}" \
  -k)

TOKEN=$(echo $LOGIN | jq -r '.access_token // empty')
if [ -z "$TOKEN" ]; then
  echo "❌ Login failed: $LOGIN"
  exit 1
fi
echo "✅ Login OK"
echo ""

# Step 2: Test Health (no auth needed)
echo "2. Health Check..."
curl -s "$BASE_URL/api/v1/webhooks/health" -k | jq .
echo ""

# Step 3: Test List Events (needs Odoo session)
echo "3. List Events (needs Odoo connection)..."
RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/webhooks/events?limit=5" \
  -H "Authorization: Bearer $TOKEN" \
  -k)
echo "$RESPONSE" | jq .
echo ""

# Step 4: Check what the error says
if echo "$RESPONSE" | grep -q "Odoo session"; then
  echo "⚠️  Need to connect to Odoo first via /api/v1/systems/{system_id}/connect"
  echo ""
  echo "To fix:"
  echo "1. Login (done ✅)"
  echo "2. Connect to Odoo system using:"
  echo "   POST $BASE_URL/api/v1/systems/odoo-$DATABASE/connect"
  echo "   Authorization: Bearer $TOKEN"
  echo "   Body: { \"url\": \"https://app.propanel.ma/odoo\", \"database\": \"$DATABASE\", \"username\": \"$USERNAME\", \"password\": \"$PASSWORD\" }"
fi
