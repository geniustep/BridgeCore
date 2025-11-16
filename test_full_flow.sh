#!/bin/bash

BASE_URL="https://bridgecore.geniura.com"
USERNAME="done"
PASSWORD=",,07Genius"
DATABASE="done"

echo "=== اختبار كامل للتدفق ==="
echo ""

# 1. Login
echo "1. تسجيل الدخول..."
LOGIN=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"$USERNAME\", \"password\": \"$PASSWORD\", \"database\": \"$DATABASE\"}" \
  -k)

TOKEN=$(echo $LOGIN | jq -r '.access_token')
SYSTEM_ID=$(echo $LOGIN | jq -r '.system_id')
USER_ID=$(echo $LOGIN | jq -r '.user.id')

echo "✅ Token: ${TOKEN:0:50}..."
echo "✅ System ID: $SYSTEM_ID"
echo ""

# 2. Connect with correct URL
echo "2. الاتصال بـ Odoo مع URL صحيح..."
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

sleep 3

# 3. Test webhook
echo "3. اختبار webhook check-updates..."
RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/webhooks/check-updates?limit=50" \
  -H "Authorization: Bearer $TOKEN" \
  -k)

echo "$RESPONSE" | jq .
echo ""

# 4. Check logs
echo "4. فحص السجلات..."
cd /opt/BridgeCore/docker && docker-compose logs api --tail=20 | grep -E "(session|authenticate|Odoo|webhook)" | tail -10
