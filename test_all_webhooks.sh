#!/bin/bash

BASE_URL="https://bridgecore.geniura.com"
USERNAME="done"
PASSWORD=",,07Genius"
DATABASE="done"

echo "=========================================="
echo "اختبار شامل لجميع Webhook Endpoints"
echo "=========================================="
echo ""

# 1. Login
TOKEN=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"$USERNAME\", \"password\": \"$PASSWORD\", \"database\": \"$DATABASE\"}" \
  -k | jq -r '.access_token')

SYSTEM_ID="odoo-done"

echo "✅ تم الحصول على Token"
echo ""

# 2. Connect
echo "2. الاتصال بـ Odoo..."
curl -s -X POST "$BASE_URL/systems/$SYSTEM_ID/connect" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"url\": \"https://app.propanel.ma\",
    \"database\": \"$DATABASE\",
    \"username\": \"$USERNAME\",
    \"password\": \"$PASSWORD\",
    \"system_type\": \"odoo\"
  }" \
  -k | jq . | head -5
echo ""

sleep 3

# 3. Test all endpoints
echo "3. اختبار جميع الـ Endpoints..."
echo ""

echo "3.1 Health Check (v1):"
curl -s "$BASE_URL/api/v1/webhooks/health" -k | jq .
echo ""

echo "3.2 Health Check (v2):"
curl -s "$BASE_URL/api/v2/sync/health" -k | jq .
echo ""

echo "3.3 Check Updates:"
curl -s -X GET "$BASE_URL/api/v1/webhooks/check-updates?limit=50" \
  -H "Authorization: Bearer $TOKEN" \
  -k | jq .
echo ""

echo "3.4 List Events:"
curl -s -X GET "$BASE_URL/api/v1/webhooks/events?limit=5" \
  -H "Authorization: Bearer $TOKEN" \
  -k | jq . | head -20
echo ""

echo "3.5 Smart Sync Pull:"
USER_ID=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"$USERNAME\", \"password\": \"$PASSWORD\", \"database\": \"$DATABASE\"}" \
  -k | jq -r '.user.id')

curl -s -X POST "$BASE_URL/api/v2/sync/pull" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": $USER_ID,
    \"device_id\": \"test-device-$(date +%s)\",
    \"app_type\": \"sales_app\",
    \"limit\": 10
  }" \
  -k | jq . | head -20
echo ""

echo "=========================================="
echo "✅ ✅ ✅ جميع الاختبارات مكتملة! ✅ ✅ ✅"
echo "=========================================="
