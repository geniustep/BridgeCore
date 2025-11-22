# 🔗 دليل التكامل: auto-webhook-odoo مع BridgeCore

## 📋 نظرة عامة

نظام **auto-webhook-odoo** هو نظام webhook متقدم لـ Odoo يقوم بـ:
1. ✅ تتبع التغييرات تلقائياً في Odoo
2. ✅ إنشاء `webhook.event` records
3. ✅ إرسال الأحداث إلى BridgeCore (أو أي endpoint آخر)

---

## 🎯 كيف يعمل النظام

### التدفق الكامل:

```
1. المستخدم يعدل sale.order في Odoo
   ↓
2. webhook.mixin يلتقط التغيير (ORM hook)
   ↓
3. يتم إنشاء webhook.event في Odoo:
   {
     "model": "sale.order",
     "record_id": 456,
     "event": "write",
     "status": "pending",
     "subscriber_id": 1  # BridgeCore endpoint
   }
   ↓
4. Cron Job (كل 30 ثانية) يرسل الأحداث:
   - يقرأ webhook.event WHERE status='pending'
   - يرسل POST إلى BridgeCore endpoint
   - يحدث status إلى 'sent' أو 'failed'
   ↓
5. BridgeCore يستقبل webhook (إذا كان endpoint موجود)
   أو
   BridgeCore يسحب من update.webhook (النظام الحالي)
```

---

## 🔄 التكامل مع BridgeCore

### الخيار 1: Push (إرسال من Odoo)

**auto-webhook-odoo** يمكنه إرسال webhooks مباشرة إلى BridgeCore:

#### الإعداد:

1. **في Odoo - Subscriber:**
   - URL: `https://bridgecore.geniura.com/api/v1/webhooks/receive` (يحتاج endpoint)
   - Auth Type: Bearer Token
   - Auth Token: YOUR_BRIDGECORE_TOKEN

2. **في BridgeCore - يحتاج endpoint:**
   ```python
   POST /api/v1/webhooks/receive
   ```

#### المزايا:
- ✅ Real-time فوري
- ✅ Odoo يتحكم بالإرسال
- ✅ Retry mechanism في Odoo

#### العيوب:
- ❌ يحتاج endpoint في BridgeCore
- ❌ قد يفقد الأحداث إذا BridgeCore غير متاح

---

### الخيار 2: Pull (سحب من BridgeCore) - الحالي

**BridgeCore يسحب من `update.webhook`:**

#### الإعداد:

1. **auto-webhook-odoo** ينشئ `webhook.event`
2. **BridgeCore** يقرأ من `update.webhook` (أو `webhook.event`)

#### المزايا:
- ✅ لا فقدان للأحداث
- ✅ BridgeCore يتحكم بالوقت
- ✅ أسهل في الإدارة

---

## 📊 Models في auto-webhook-odoo

### 1. `webhook.event` (الجديد - متقدم)

```python
{
  "id": 123,
  "model": "sale.order",
  "record_id": 456,
  "event": "write",
  "status": "pending",  # pending/processing/sent/failed/dead
  "priority": "high",   # high/medium/low
  "category": "business",
  "retry_count": 0,
  "max_retries": 5,
  "subscriber_id": 1,  # BridgeCore endpoint
  "payload": {...},     # JSON data
  "timestamp": "2025-11-16T10:30:00Z"
}
```

### 2. `update.webhook` (قديم - للتوافق)

```python
{
  "id": 123,
  "model": "sale.order",
  "record_id": 456,
  "event": "write",
  "timestamp": "2025-11-16T10:30:00Z"
}
```

### 3. `webhook.subscriber` (نقاط النهاية)

```python
{
  "id": 1,
  "name": "BridgeCore Default Endpoint",
  "endpoint_url": "https://api.bridgecore.ma/webhook",
  "auth_type": "bearer",
  "auth_token": "...",
  "enabled": True
}
```

### 4. `webhook.config` (إعدادات لكل model)

```python
{
  "id": 1,
  "model_id": "sale.order",
  "enabled": True,
  "priority": "high",
  "events": "create,write",
  "subscriber_ids": [1]  # BridgeCore
}
```

---

## 🚀 الخطوات التالية

### 1. تثبيت auto-webhook-odoo في Odoo

```bash
# نسخ إلى Odoo addons
cp -r /opt/auto-webhook-odoo /path/to/odoo/addons/auto_webhook

# في Odoo:
# Apps → Update Apps List → Install "Auto Webhook - Enterprise Grade"
```

### 2. تحديث BridgeCore لاستخدام webhook.event

**الخيار A: استخدام webhook.event (الجديد)**

```python
# في app/utils/odoo_client.py
# تغيير من:
self.search_read("update.webhook", ...)

# إلى:
self.search_read("webhook.event", ...)
```

**الخيار B: إضافة endpoint لاستقبال webhooks**

```python
# في app/modules/webhook/router.py
@router.post("/receive")
async def receive_webhook(...):
    # استقبال webhook من Odoo
```

### 3. اختبار التكامل

```bash
# 1. تعديل sale.order في Odoo
# 2. تحقق من webhook.event في Odoo
# 3. BridgeCore يسحب أو يستقبل
```

---

## 📝 ملاحظات مهمة

1. **auto-webhook-odoo** يستخدم `webhook.event` (الجديد)
2. **BridgeCore** حالياً يستخدم `update.webhook` (القديم)
3. **يجب التحديث** لاستخدام `webhook.event` للحصول على الميزات المتقدمة

---

## 🔗 المراجع

- **auto-webhook-odoo**: https://github.com/geniustep/auto-webhook-odoo
- **BridgeCore**: https://github.com/geniustep/BridgeCore
