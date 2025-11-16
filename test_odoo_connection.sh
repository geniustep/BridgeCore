#!/bin/bash

echo "=== اختبار الاتصال بـ Odoo ==="
echo ""

# 1. اختبار URL مباشرة
echo "1. اختبار URL مباشرة..."
curl -s -I "https://app.propanel.ma/odoo/web/session/authenticate" -k | head -5
echo ""

# 2. اختبار المصادقة مباشرة
echo "2. اختبار المصادقة مباشرة..."
RESPONSE=$(curl -s -X POST "https://app.propanel.ma/odoo/web/session/authenticate" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
      "db": "done",
      "login": "done",
      "password": ",,07Genius"
    }
  }' \
  -k)

echo "$RESPONSE" | jq . 2>/dev/null || echo "$RESPONSE" | head -20
echo ""

# 3. اختبار بدون /odoo
echo "3. اختبار بدون /odoo..."
RESPONSE2=$(curl -s -X POST "https://app.propanel.ma/web/session/authenticate" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
      "db": "done",
      "login": "done",
      "password": ",,07Genius"
    }
  }' \
  -k)

echo "$RESPONSE2" | head -20
echo ""
