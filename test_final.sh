#!/bin/bash

BASE_URL="https://bridgecore.geniura.com"
USERNAME="done"
PASSWORD=",,07Genius"
DATABASE="done"

echo "=== اختبار نهائي ==="
echo ""

# 1. Login
TOKEN=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"$USERNAME\", \"password\": \"$PASSWORD\", \"database\": \"$DATABASE\"}" \
  -k | jq -r '.access_token')

SYSTEM_ID="odoo-done"

echo "✅ Token obtained"
echo ""

# 2. Connect with correct URL (without /odoo)
echo "2. الاتصال بـ Odoo (URL بدون /odoo)..."
CONNECT=$(curl -s -X POST "$BASE_URL/systems/$SYSTEM_ID/connect" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"url\": \"https://app.propanel.ma\",
    \"database\": \"$DATABASE\",
    \"username\": \"$USERNAME\",
    \"password\": \"$PASSWORD\",
    \"system_type\": \"odoo\"
  }" \
  -k)

echo "$CONNECT" | jq .
echo ""

sleep 3

# 3. Test webhook
echo "3. اختبار webhook..."
RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/webhooks/check-updates?limit=50" \
  -H "Authorization: Bearer $TOKEN" \
  -k)

echo "$RESPONSE" | jq . | head -30
echo ""

if echo "$RESPONSE" | grep -q "has_update\|summary\|events"; then
  echo "✅ ✅ ✅ نجح! ✅ ✅ ✅"
else
  echo "❌ لا يزال هناك مشكلة"
fi
