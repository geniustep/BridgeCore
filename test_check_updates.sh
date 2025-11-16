#!/bin/bash

# مثال عملي لاختبار check-updates

BASE_URL="https://bridgecore.geniura.com"
USERNAME="done"
PASSWORD=",,07Genius"
DATABASE="done"

echo "=== اختبار check-updates ==="
echo ""

# 1. تسجيل الدخول
echo "1. تسجيل الدخول..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"$USERNAME\", \"password\": \"$PASSWORD\", \"database\": \"$DATABASE\"}" \
  -k)

# 2. استخراج التوكن
TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
  echo "❌ فشل تسجيل الدخول!"
  echo "$LOGIN_RESPONSE" | jq .
  exit 1
fi

echo "✅ تم الحصول على التوكن: ${TOKEN:0:50}..."
echo ""

# 3. الاتصال بـ Odoo (اختياري - إذا لم يكن متصل)
echo "2. الاتصال بـ Odoo..."
SYSTEM_ID=$(echo $LOGIN_RESPONSE | jq -r '.system_id')
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

# 4. اختبار check-updates مع التوكن في Header
echo "3. اختبار check-updates..."
echo "   URL: $BASE_URL/api/v1/webhooks/check-updates?limit=50"
echo "   Header: Authorization: Bearer $TOKEN"
echo ""

RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/webhooks/check-updates?limit=50" \
  -H "Authorization: Bearer $TOKEN" \
  -k)

echo "النتيجة:"
echo "$RESPONSE" | jq .
echo ""

# 5. عرض التوكن للاستخدام اليدوي
echo "=========================================="
echo "للاستخدام اليدوي، استخدم هذا الأمر:"
echo "=========================================="
echo ""
echo "curl -X GET '$BASE_URL/api/v1/webhooks/check-updates?limit=50' \\"
echo "  -H 'Authorization: Bearer $TOKEN' \\"
echo "  -k"
echo ""
