#!/bin/bash

BASE_URL="https://bridgecore.geniura.com"
USERNAME="done"
PASSWORD=",,07Genius"
DATABASE="done"

echo "=== اختبار Webhook بعد الإصلاح ==="
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

# 2. Connect to Odoo
echo "2. الاتصال بـ Odoo..."
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

# 3. Test check-updates
echo "3. اختبار check-updates..."
RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/webhooks/check-updates?limit=50" \
  -H "Authorization: Bearer $TOKEN" \
  -k)

echo "$RESPONSE" | jq .
echo ""

if echo "$RESPONSE" | grep -q "session not found"; then
  echo "❌ المشكلة لا تزال موجودة"
  echo ""
  echo "حاول:"
  echo "1. تحقق من السجلات: docker-compose logs api --tail=50"
  echo "2. تأكد من أن Odoo URL صحيح: https://app.propanel.ma/odoo"
  echo "3. تأكد من credentials"
else
  echo "✅ نجح!"
fi
