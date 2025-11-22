# 📋 الخطوات التالية - BridgeCore Smart Sync

## ✅ ما تم إنجازه

- ✅ تم دمج Smart Sync enhancements من الفرع البعيد
- ✅ تم إضافة Odoo module (`user_sync_state`)
- ✅ تم تحسين WebSocket و OdooClient
- ✅ تم إضافة Custom Exceptions
- ✅ تم إضافة أمثلة Flutter
- ✅ تم إضافة التوثيق الشامل

---

## 🎯 الخطوات التالية

### 1️⃣ تثبيت Odoo Module (مهم!)

**ملاحظة:** BridgeCore لا يحتوي على `odoo_addons` بعد الآن. استخدم **auto-webhook-odoo** الذي يحتوي على `user.sync.state`.

#### الخطوة 1: تثبيت auto-webhook-odoo

```bash
# نسخ auto-webhook-odoo إلى Odoo
cp -r /opt/auto-webhook-odoo /path/to/odoo/addons/auto_webhook

# أو إذا كان Odoo في Docker:
docker cp /opt/auto-webhook-odoo odoo_container:/mnt/extra-addons/auto_webhook
```

#### الخطوة 2: تثبيت في Odoo

1. افتح Odoo → Apps
2. اضغط "Update Apps List"
3. ابحث عن "Auto Webhook - Enterprise Grade"
4. اضغط "Install"

**auto-webhook-odoo يحتوي على:**
- ✅ `webhook.event` (للـ Push)
- ✅ `update.webhook` (للـ Pull)
- ✅ `user.sync.state` (للـ Smart Sync)

#### الخطوة 3: التحقق

```bash
# من BridgeCore، اختبر الاتصال:
curl -X GET 'https://bridgecore.geniura.com/api/v2/sync/state?user_id=1&device_id=test-device' \
  -H 'Authorization: Bearer YOUR_TOKEN'
```

---

### 2️⃣ اختبار Smart Sync

#### اختبار Smart Sync Pull

```bash
# 1. الحصول على Token
TOKEN=$(curl -s -X POST 'https://bridgecore.geniura.com/api/v1/auth/login' \
  -H 'Content-Type: application/json' \
  -d '{"username": "done", "password": ",,07Genius", "database": "done"}' \
  -k | jq -r '.access_token')

# 2. الاتصال بـ Odoo
curl -X POST 'https://bridgecore.geniura.com/systems/odoo-done/connect' \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "url": "https://app.propanel.ma",
    "database": "done",
    "username": "done",
    "password": ",,07Genius",
    "system_type": "odoo"
  }' \
  -k

# 3. اختبار Smart Sync
curl -X POST 'https://bridgecore.geniura.com/api/v2/sync/pull' \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": 1,
    "device_id": "test-device-001",
    "app_type": "sales_app",
    "limit": 50
  }' \
  -k | jq .
```

---

### 3️⃣ تحديث Flutter Apps

#### استخدام Flutter Example

```dart
// انسخ الملف:
// examples/flutter/smart_sync_service.dart

// استخدمه في تطبيقك:
final syncService = SmartSyncService(
  baseUrl: 'https://bridgecore.geniura.com',
  appType: 'sales_app',
  onEventsReceived: (events) async {
    // معالجة الأحداث
  },
);

await syncService.initialize();
syncService.startBackgroundSync();
```

---

### 4️⃣ مراقبة النظام

#### فحص Sync States في Odoo

1. افتح Odoo → Sync States → User Sync States
2. تحقق من وجود sync states
3. راجع الإحصائيات

#### فحص Logs

```bash
# BridgeCore logs
docker-compose logs -f api | grep -i sync

# Odoo logs (إذا كان في Docker)
docker logs odoo_container | grep -i sync
```

---

### 5️⃣ تحديث التوثيق (اختياري)

- ✅ README.md محدث
- ✅ docs/SYNC_ARCHITECTURE.md موجود
- ✅ examples/README.md موجود

---

## 🔍 Checklist

- [ ] تثبيت `auto-webhook-odoo` module في Odoo (يحتوي على `user.sync.state`)
- [ ] اختبار Smart Sync Pull
- [ ] اختبار Get Sync State
- [ ] اختبار Reset Sync State
- [ ] تحديث Flutter Apps لاستخدام Smart Sync
- [ ] مراقبة Logs للتأكد من عدم وجود أخطاء
- [ ] اختبار مع عدة أجهزة/مستخدمين

---

## 🐛 Troubleshooting

### مشكلة: Sync State غير موجود

**الحل:**
- تأكد من تثبيت `auto-webhook-odoo` module (يحتوي على `user.sync.state`)
- تحقق من الصلاحيات في Odoo
- جرب Reset Sync State

### مشكلة: لا توجد أحداث جديدة

**الحل:**
- تحقق من وجود أحداث في `update.webhook`
- تحقق من `last_event_id` في sync state
- جرب Reset Sync State لإعادة المزامنة الكاملة

### مشكلة: أخطاء في Odoo Client

**الحل:**
- تحقق من الاتصال بـ Odoo
- تحقق من session_id
- جرب إعادة الاتصال

---

## 📚 المراجع

- `docs/SYNC_ARCHITECTURE.md` - معمارية النظام
- `examples/README.md` - أمثلة الاستخدام
- `AUTO_WEBHOOK_ODOO_UPDATE.md` - دليل auto-webhook-odoo (يحتوي على `user.sync.state`)
- `SMART_SYNC_IMPLEMENTATION.md` - ملخص التنفيذ

---

## 🎯 الأولوية

1. **عاجل**: تثبيت Odoo module
2. **مهم**: اختبار Smart Sync
3. **مهم**: تحديث Flutter Apps
4. **اختياري**: مراقبة وتحسين

