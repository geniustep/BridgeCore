# اختبار Moodle API Endpoints

دليل شامل لاختبار تكامل Moodle مع BridgeCore

## المتطلبات

1. **خادم Moodle** يعمل ومتاح
2. **Web Services Token** من Moodle
3. **Tenant** موجود في BridgeCore
4. **Tenant User** للاختبار

---

## إعداد Moodle

### 1. تفعيل Web Services في Moodle

```
Site Administration → Advanced Features
→ Enable web services ✓
```

### 2. تفعيل REST Protocol

```
Site Administration → Plugins → Web Services → Manage Protocols
→ Enable REST protocol ✓
```

### 3. إنشاء مستخدم للـ API

```
Site Administration → Users → Add New User
→ Username: bridgecore_api
→ Email: api@yourdomain.com
→ Assign system role: Manager
```

### 4. إنشاء Token

```
Site Administration → Plugins → Web Services → Manage Tokens
→ Add Token
→ User: bridgecore_api
→ Service: moodle_mobile_app
→ Save
→ Copy generated token
```

---

## إعداد BridgeCore

### 1. إضافة Moodle System إلى Catalog

```bash
# استخدام Admin API
POST /admin/systems
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "system_type": "moodle",
  "name": "Moodle LMS",
  "description": "Learning Management System",
  "status": "active",
  "is_enabled": true,
  "capabilities": {
    "courses": true,
    "users": true,
    "enrolments": true
  }
}
```

### 2. إضافة اتصال Moodle للـ Tenant

```bash
# استخدام Admin API
POST /admin/systems/tenant-connections
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "tenant_id": "YOUR_TENANT_UUID",
  "system_id": "MOODLE_SYSTEM_UUID",
  "connection_config": {
    "url": "https://lms.example.com",
    "token": "YOUR_MOODLE_TOKEN",
    "service": "moodle_mobile_app"
  },
  "is_active": true,
  "is_primary": false
}
```

---

## استخدام سكريبت الاختبار

### الطريقة 1: اختبار مباشر (مع Token)

```bash
python3 scripts/test_moodle_api.py \
  --base-url http://localhost:8001 \
  --moodle-url https://lms.example.com \
  --token YOUR_MOODLE_TOKEN \
  --tenant-token YOUR_TENANT_TOKEN
```

### الطريقة 2: اختبار مع Login

```bash
python3 scripts/test_moodle_api.py \
  --base-url http://localhost:8001 \
  --moodle-url https://lms.example.com \
  --token YOUR_MOODLE_TOKEN \
  --tenant-email user@example.com \
  --tenant-password password123
```

### الطريقة 3: اختبار كامل مع Setup

```bash
python3 scripts/test_moodle_api.py \
  --base-url http://localhost:8001 \
  --moodle-url https://lms.example.com \
  --token YOUR_MOODLE_TOKEN \
  --tenant-id YOUR_TENANT_UUID \
  --tenant-email user@example.com \
  --tenant-password password123 \
  --admin-token YOUR_ADMIN_TOKEN
```

---

## اختبار يدوي باستخدام curl

### 1. الحصول على Token

```bash
curl -X POST http://localhost:8001/api/v1/auth/tenant/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

### 2. اختبار Site Info

```bash
curl -X GET http://localhost:8001/api/v1/moodle/site-info \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. اختبار Health

```bash
curl -X GET http://localhost:8001/api/v1/moodle/health \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. الحصول على الكورسات

```bash
curl -X GET http://localhost:8001/api/v1/moodle/courses \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 5. الحصول على المستخدمين

```bash
curl -X GET http://localhost:8001/api/v1/moodle/users \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 6. استدعاء دالة Moodle

```bash
curl -X POST "http://localhost:8001/api/v1/moodle/call?function_name=core_webservice_get_site_info" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

## Endpoints المتاحة

### System Endpoints

- `GET /api/v1/moodle/site-info` - معلومات الموقع
- `GET /api/v1/moodle/health` - فحص الاتصال
- `POST /api/v1/moodle/call` - استدعاء دالة Moodle

### Course Endpoints

- `GET /api/v1/moodle/courses` - جميع الكورسات
- `GET /api/v1/moodle/courses/{course_id}` - كورس محدد
- `POST /api/v1/moodle/courses` - إنشاء كورس
- `PUT /api/v1/moodle/courses/{course_id}` - تحديث كورس
- `DELETE /api/v1/moodle/courses/{course_id}` - حذف كورس
- `GET /api/v1/moodle/courses/{course_id}/users` - مستخدمو الكورس
- `POST /api/v1/moodle/courses/{course_id}/enrol` - تسجيل مستخدم

### User Endpoints

- `GET /api/v1/moodle/users` - جميع المستخدمين
- `GET /api/v1/moodle/users/{user_id}` - مستخدم محدد
- `POST /api/v1/moodle/users` - إنشاء مستخدم
- `PUT /api/v1/moodle/users/{user_id}` - تحديث مستخدم
- `DELETE /api/v1/moodle/users/{user_id}` - حذف مستخدم

---

## استكشاف الأخطاء

### خطأ: "Moodle is not configured for this tenant"

**الحل:**
1. تأكد من إضافة اتصال Moodle للـ tenant
2. تحقق من أن `is_active = true`
3. استخدم Admin API لإضافة الاتصال

### خطأ: "Connection timeout"

**الحل:**
1. تحقق من أن URL Moodle صحيح
2. تأكد من أن Moodle متاح من السيرفر
3. تحقق من إعدادات Firewall

### خطأ: "Invalid token"

**الحل:**
1. تحقق من أن Token صحيح
2. تأكد من أن Token لم ينتهِ صلاحيته
3. أنشئ Token جديد من Moodle

### خطأ: "Web services not enabled"

**الحل:**
1. فعل Web Services في Moodle
2. فعل REST Protocol
3. تحقق من صلاحيات المستخدم

---

## أمثلة متقدمة

### إنشاء كورس جديد

```bash
curl -X POST http://localhost:8001/api/v1/moodle/courses \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "fullname": "Introduction to Python",
    "shortname": "PYTHON101",
    "categoryid": 1,
    "summary": "Learn Python programming"
  }'
```

### تسجيل مستخدم في كورس

```bash
curl -X POST http://localhost:8001/api/v1/moodle/courses/1/enrol \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 5,
    "role_id": 5
  }'
```

---

## ملاحظات

- جميع الـ endpoints تتطلب مصادقة Tenant User
- الـ responses تكون بصيغة JSON
- في حالة الخطأ، يتم إرجاع رسالة خطأ واضحة
- يمكن استخدام `/docs` لرؤية جميع الـ endpoints وتجربتها

